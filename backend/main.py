"""Saving REST API. Run: uvicorn main:app --host 127.0.0.1 --port 4000."""

from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
import csv
import hmac
import io
import logging
import re
import secrets
import sqlite3
from eth_account import Account
from eth_account.messages import encode_defunct
from fastapi import FastAPI, HTTPException, Request, Response, Depends, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException as StarletteHTTPException
from web3 import Web3
from config import Settings
from database import Database
from security import now_ms, token_hash, password_hash, verify_password, RateLimiter
from chain import ChainReader, CHAIN_ID, EVENT_NAMES
from rpc_errors import rpc_message

log = logging.getLogger("saving.api")
READERS = ("admin", "auditor")


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=12, max_length=128)
    adminCode: str = Field(default="", max_length=256)
    auditorCode: str = Field(default="", max_length=256)


class WalletProof(BaseModel):
    signature: str = Field(min_length=130, max_length=132)


class ReceiptInput(BaseModel):
    hash: str = Field(pattern=r"^0x[0-9a-fA-F]{64}$")


def create_app(settings=None, chain=None):
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app):
        app.state.db = Database(settings.db_path)
        app.state.chain = chain if chain is not None else ChainReader(settings)
        yield

    app = FastAPI(
        title="Saving API",
        version="2.1.0",
        lifespan=lifespan,
        docs_url="/api/docs" if not settings.production else None,
        openapi_url="/api/openapi.json" if not settings.production else None,
        redoc_url=None,
    )
    app.state.settings = settings
    limiter = RateLimiter(settings.auth_limit)

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request, exc):
        return JSONResponse({"error": exc.detail}, status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        # Do not echo passwords, signatures or raw request values in errors.
        return JSONResponse(
            {
                "error": "Invalid request. Check field formats and password length (12–128 characters)."
            },
            status_code=422,
        )

    @app.exception_handler(Exception)
    async def unexpected_error(request, exc):
        # Log type and route only; RPC errors can contain credential-bearing URLs.
        log.error("Request failed: %s %s", request.url.path, type(exc).__name__)
        return JSONResponse(
            {
                "error": rpc_message(exc)
                or "Service unavailable. Check RPC configuration or try again later."
            },
            status_code=503,
        )

    @app.middleware("http")
    async def request_guard(request, call_next):
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            origin = request.headers.get("origin")
            host = request.headers.get("host", "")
            # API binds loopback in Docker; trust the local Next proxy only.
            if request.client and request.client.host in ("127.0.0.1", "::1"):
                host = request.headers.get("x-forwarded-host", host)
            allowed = (
                {settings.public_origin}
                if settings.public_origin
                else {f"http://{host}", f"https://{host}"}
            )
            if origin and origin not in allowed:
                return JSONResponse({"error": "Origin rejected."}, status_code=403)
            length = request.headers.get("content-length")
            if length and (not length.isdigit() or int(length) > 16384):
                return JSONResponse({"error": "Request too large."}, status_code=413)
            if (
                request.headers.get("content-type", "").split(";")[0]
                != "application/json"
            ):
                return JSONResponse({"error": "Use application/json."}, status_code=415)
            # Bound streamed requests too; Starlette caches the verified body.
            chunks, size = [], 0
            async for chunk in request.stream():
                size += len(chunk)
                if size > 16384:
                    return JSONResponse(
                        {"error": "Request too large."}, status_code=413
                    )
                chunks.append(chunk)
            request._body = b"".join(chunks)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    def current_user(request: Request):
        token = request.cookies.get("session", "")
        with app.state.db.connect() as db:
            user = (
                db.execute(
                    """SELECT u.id,u.email,u.role,u.wallet FROM users u JOIN sessions s ON s.user_id=u.id
                                 WHERE s.token=? AND s.expires>?""",
                    (token_hash(token), now_ms()),
                ).fetchone()
                if token
                else None
            )
        if not user:
            raise HTTPException(401, "Please sign in.")
        return dict(user)

    def reader(user=Depends(current_user)):
        if user["role"] not in READERS:
            raise HTTPException(403, "Administrator or auditor access required.")
        return user

    def writer(user=Depends(current_user)):
        if user["role"] == "auditor":
            raise HTTPException(403, "Auditor access is read-only.")
        return user

    def auth(body, request, response, register=False):
        email = body.email.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            raise HTTPException(422, "Use a valid email address.")
        # Account+peer throttling avoids treating every proxied user as one IP.
        limiter.check(("account", email))
        limiter.check(("peer", request.client.host if request.client else "unknown"))
        with app.state.db.connect() as db:
            if register:
                if body.adminCode and body.auditorCode:
                    raise HTTPException(422, "Use one invitation code only.")
                role = "user"
                for supplied, expected, requested in (
                    (body.adminCode, settings.admin_code, "admin"),
                    (body.auditorCode, settings.auditor_code, "auditor"),
                ):
                    if supplied:
                        if not expected or not hmac.compare_digest(
                            supplied.encode(), expected.encode()
                        ):
                            raise HTTPException(403, "Invalid role invitation.")
                        role = requested
                try:
                    result = db.execute(
                        "INSERT INTO users(email,password,role) VALUES(?,?,?)",
                        (email, password_hash(body.password), role),
                    )
                    Database.audit(db, result.lastrowid, "account_registered", role)
                except sqlite3.IntegrityError:
                    raise HTTPException(409, "Email already registered.") from None
            account = db.execute(
                "SELECT * FROM users WHERE email=?", (email,)
            ).fetchone()
            encoded = account["password"] if account else "0000:" + "00" * 64
            if not verify_password(body.password, encoded) or not account:
                raise HTTPException(401, "Invalid email or password.")
            session = secrets.token_hex(32)
            db.execute("DELETE FROM sessions WHERE expires<?", (now_ms(),))
            db.execute(
                "INSERT INTO sessions VALUES(?,?,?)",
                (token_hash(session), account["id"], now_ms() + 86400000),
            )
            Database.audit(db, account["id"], "signed_in")
        response.set_cookie(
            "session",
            session,
            max_age=86400,
            httponly=True,
            samesite="lax",
            secure=settings.production,
            path="/",
        )
        return {"ok": True}

    @app.get("/api/health")
    def health():
        with app.state.db.connect() as db:
            db.execute("SELECT 1").fetchone()
        return {"ok": True, "service": "saving-python", "version": "2.1.0"}

    @app.get("/api/config")
    def config():
        return {"contract": settings.contract_address or None, "chainId": CHAIN_ID}

    @app.post("/api/register")
    def register(body: Credentials, request: Request, response: Response):
        return auth(body, request, response, True)

    @app.post("/api/login")
    def login(body: Credentials, request: Request, response: Response):
        return auth(body, request, response)

    @app.get("/api/me")
    def me(user=Depends(current_user)):
        return user

    @app.post("/api/logout")
    def logout(request: Request, response: Response, user=Depends(current_user)):
        with app.state.db.connect() as db:
            db.execute(
                "DELETE FROM sessions WHERE token=?",
                (token_hash(request.cookies["session"]),),
            )
            Database.audit(db, user["id"], "signed_out")
        response.delete_cookie(
            "session",
            path="/",
            secure=settings.production,
            httponly=True,
            samesite="lax",
        )
        return {"ok": True}

    @app.post("/api/challenge")
    def challenge(request: Request, user=Depends(current_user)):
        domain = settings.public_origin or str(request.base_url).rstrip("/")
        message = f"Saving wallet verification\nOrigin: {domain}\nChain: {CHAIN_ID}\nAccount: {user['id']}\nNonce: {secrets.token_hex(32)}\nExpires in 5 minutes"
        with app.state.db.connect() as db:
            db.execute(
                "INSERT OR REPLACE INTO challenges VALUES(?,?,?)",
                (user["id"], message, now_ms() + 300000),
            )
        return {"message": message}

    @app.post("/api/wallet")
    def wallet(body: WalletProof, user=Depends(current_user)):
        with app.state.db.connect() as db:
            # Check, link and consume under one writer transaction to prevent replay races.
            db.execute("BEGIN IMMEDIATE")
            proof = db.execute(
                "SELECT * FROM challenges WHERE user_id=?", (user["id"],)
            ).fetchone()
            if not proof or proof["expires"] < now_ms():
                raise HTTPException(400, "Request a new wallet challenge.")
            try:
                address = Web3.to_checksum_address(
                    Account.recover_message(
                        encode_defunct(text=proof["message"]), signature=body.signature
                    )
                )
            except Exception:
                raise HTTPException(400, "Invalid signature.") from None
            existing = db.execute(
                "SELECT wallet FROM users WHERE id=?", (user["id"],)
            ).fetchone()["wallet"]
            if existing and existing.lower() != address.lower():
                raise HTTPException(409, "This account already has a different wallet.")
            try:
                db.execute(
                    "UPDATE users SET wallet=? WHERE id=?", (address, user["id"])
                )
            except sqlite3.IntegrityError:
                raise HTTPException(409, "Wallet belongs to another account.") from None
            db.execute("DELETE FROM challenges WHERE user_id=?", (user["id"],))
            Database.audit(db, user["id"], "wallet_verified", address)
        return {"wallet": address}

    def scope(user, alias="t"):
        return (
            ("1=1", [])
            if user["role"] in READERS
            else (f"{alias}.user_id=?", [user["id"]])
        )

    def selection(user, kind=""):
        condition, params = scope(user)
        if kind:
            if kind not in EVENT_NAMES:
                raise HTTPException(422, "Unknown event type.")
            condition += " AND t.kind=?"
            params.append(kind)
        return condition, params

    def activity_rows(db, user, kind="", limit=20, offset=0):
        condition, params = selection(user, kind)
        # Auditor does not need email addresses to reconcile wallet activity.
        private = "u.email," if user["role"] == "admin" else ""
        return [
            dict(r)
            for r in db.execute(
                f"""SELECT t.*,{private}u.wallet FROM transactions t
                    JOIN users u ON u.id=t.user_id WHERE {condition}
                    ORDER BY t.block DESC,t.log_index DESC LIMIT ? OFFSET ?""",
                [*params, limit, offset],
            )
        ]

    @app.get("/api/transactions")
    def legacy_transactions(
        limit: int = Query(500, ge=1, le=500), user=Depends(current_user)
    ):
        with app.state.db.connect() as db:
            return activity_rows(db, user, limit=limit)

    @app.get("/api/activity")
    def activity(
        page: int = Query(1, ge=1, le=1000000),
        pageSize: int = Query(20, ge=1, le=100),
        kind: str = "",
        user=Depends(current_user),
    ):
        condition, params = selection(user, kind)
        with app.state.db.connect() as db:
            total = db.execute(
                f"SELECT count(*) FROM transactions t WHERE {condition}", params
            ).fetchone()[0]
            return {
                "items": activity_rows(db, user, kind, pageSize, (page - 1) * pageSize),
                "total": total,
                "page": page,
                "pageSize": pageSize,
            }

    @app.get("/api/analytics")
    def analytics(user=Depends(current_user)):
        condition, params = scope(user)
        start = (datetime.now(timezone.utc).date() - timedelta(days=13)).isoformat()
        with app.state.db.connect() as db:
            rows = db.execute(
                f"""SELECT kind,amount,created FROM transactions t
                                WHERE {condition} AND created>=? ORDER BY created""",
                [*params, start],
            ).fetchall()
        days = {
            str(datetime.now(timezone.utc).date() - timedelta(days=n)): {
                "deposits": 0,
                "withdrawals": 0,
                "interest": 0,
                "funding": 0,
                "count": 0,
            }
            for n in reversed(range(14))
        }
        keys = {
            "Deposited": "deposits",
            "Withdrawn": "withdrawals",
            "InterestPaid": "interest",
            "Funded": "funding",
        }
        for row in rows:
            day = row["created"][:10]
            if day in days and row["kind"] in keys:
                days[day][keys[row["kind"]]] += int(row["amount"])
                days[day]["count"] += 1
        return {
            "basis": "recorded_at",
            "scope": "all_accounts" if user["role"] in READERS else "your_account",
            "days": [
                {
                    "date": day,
                    **{k: (v if k == "count" else str(v)) for k, v in values.items()},
                }
                for day, values in days.items()
            ],
        }

    @app.get("/api/transactions/export")
    def export_csv(user=Depends(current_user)):
        # Bounded export is explicit; paginate the API for larger journals.
        with app.state.db.connect() as db:
            rows = activity_rows(db, user, limit=10000)
        columns = [
            "hash",
            "log_index",
            "kind",
            "amount",
            "block",
            "block_time",
            "created",
            "wallet",
        ]
        if user["role"] == "admin":
            columns.append("email")
        output = io.StringIO()
        writer_csv = csv.writer(output)
        writer_csv.writerow(columns)
        for row in rows:
            # Spreadsheet formula protection, including malicious email local-parts.
            writer_csv.writerow(
                [
                    (
                        "'" + str(row[c])
                        if str(row.get(c) or "").startswith(
                            ("=", "+", "-", "@", "\t", "\r")
                        )
                        else row.get(c, "")
                    )
                    for c in columns
                ]
            )
        return Response(
            output.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": 'attachment; filename="saving-transactions.csv"',
                "X-Export-Limit": "10000",
            },
        )

    @app.get("/api/audit")
    def audit(page: int = Query(1, ge=1), user=Depends(reader)):
        with app.state.db.connect() as db:
            total = db.execute("SELECT count(*) FROM audit_log").fetchone()[0]
            rows = [
                dict(r)
                for r in db.execute(
                    "SELECT id,user_id,action,detail,created FROM audit_log ORDER BY id DESC LIMIT 20 OFFSET ?",
                    ((page - 1) * 20,),
                )
            ]
        return {"items": rows, "total": total, "page": page, "pageSize": 20}

    @app.get("/api/chain-status")
    def chain_status(user=Depends(current_user)):
        return app.state.chain.diagnostics()

    @app.get("/api/balance")
    def balance(user=Depends(current_user)):
        return app.state.chain.balance(user["wallet"])

    @app.post("/api/transactions")
    def import_receipt(body: ReceiptInput, user=Depends(writer)):
        if user["role"] != "admin" and not user["wallet"]:
            raise HTTPException(400, "Connect and verify a wallet first.")
        # Admins may recover confirmed receipts for already-linked customers.
        # Ownership always comes from decoded contract events, never request input.
        events = app.state.chain.verify_receipt(
            body.hash, None if user["role"] == "admin" else user["wallet"]
        )
        inserted = 0
        with app.state.db.connect() as db:
            matched = 0
            for event in events:
                owner = db.execute(
                    "SELECT id FROM users WHERE lower(wallet)=lower(?)",
                    (event["wallet"],),
                ).fetchone()
                if not owner or (user["role"] != "admin" and owner["id"] != user["id"]):
                    continue
                matched += 1
                result = db.execute(
                    """INSERT OR IGNORE INTO transactions(hash,log_index,user_id,kind,amount,block,block_hash,block_time)
                                     VALUES(?,?,?,?,?,?,?,?)""",
                    (
                        event["hash"],
                        event["log_index"],
                        owner["id"],
                        event["kind"],
                        event["amount"],
                        event["block"],
                        event["block_hash"],
                        event["block_time"],
                    ),
                )
                inserted += result.rowcount
            if not matched:
                raise HTTPException(
                    400,
                    "No matching registered wallet. The wallet that made the transaction must be linked to a customer account first.",
                )
            if inserted:
                Database.audit(db, user["id"], "receipt_imported", body.hash)
        return {"ok": True, "inserted": inserted}

    return app


app = create_app()
