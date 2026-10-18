"""Integration tests use temporary SQLite files and real Ethereum signatures."""

import csv
import io
import sqlite3
import subprocess
from types import SimpleNamespace
import pytest
from eth_account import Account
from eth_account.messages import encode_defunct
from fastapi import HTTPException
from fastapi.testclient import TestClient
from hexbytes import HexBytes
from web3 import Web3
from config import Settings
from main import create_app
from chain import ChainReader, ABI

PASSWORD = "a secure password 123"
HASH = "0x" + "ab" * 32


class FakeChain:
    def balance(self, wallet):
        return {
            "principal": "0",
            "interest": "0",
            "rateBps": "500",
            "reserve": "0",
            "totalPrincipal": "0",
            "owner": "0x" + "11" * 20,
            "block": 42,
        }

    def verify_receipt(self, tx_hash, wallet):
        return [
            {
                "hash": tx_hash,
                "log_index": 0,
                "kind": "Deposited",
                "amount": "1000000000000000001",
                "block": 42,
                "block_hash": "0x" + "cd" * 32,
                "block_time": "2026-10-18 00:00:00",
            }
        ]


@pytest.fixture
def setup(tmp_path):
    settings = Settings(
        db_path=str(tmp_path / "saving.sqlite"),
        admin_code="admin-secret",
        auditor_code="audit-secret",
        auth_limit=100,
    )
    app = create_app(settings, FakeChain())
    with TestClient(app) as client:
        yield app, client, settings


def register(client, email="member@example.com", **extra):
    return client.post(
        "/api/register", json={"email": email, "password": PASSWORD, **extra}
    )


def link(client, wallet=None):
    wallet = wallet or Account.create()
    challenge = client.post("/api/challenge", json={}).json()["message"]
    signature = Account.sign_message(
        encode_defunct(text=challenge), wallet.key
    ).signature.to_0x_hex()
    result = client.post("/api/wallet", json={"signature": signature})
    assert result.status_code == 200, result.text
    return wallet, signature


def test_accounts_and_legacy_password_compatibility(setup):
    app, client, settings = setup
    assert client.get("/api/me").status_code == 401
    assert register(client, adminCode="wrong").status_code == 403
    assert register(client).status_code == 200
    assert client.get("/api/me").json()["role"] == "user"
    assert register(client).status_code == 409
    assert (
        client.post(
            "/api/login",
            json={"email": "member@example.com", "password": "wrong but long password"},
        ).status_code
        == 401
    )
    assert client.post("/api/logout", json={}).status_code == 200
    assert client.get("/api/me").status_code == 401
    assert (
        client.post(
            "/api/login", json={"email": "MEMBER@example.com", "password": PASSWORD}
        ).status_code
        == 200
    )
    # Use actual Node output rather than a Python hash masquerading as Node data.
    encoded = subprocess.check_output(
        [
            "node",
            "-e",
            "const c=require('node:crypto');console.log('abcd:'+c.scryptSync('a secure password 123','abcd',64).toString('hex'))",
        ],
        text=True,
    ).strip()
    with app.state.db.connect() as db:
        db.execute(
            "UPDATE users SET password=? WHERE email=?", (encoded, "member@example.com")
        )
    assert (
        client.post(
            "/api/login", json={"email": "member@example.com", "password": PASSWORD}
        ).status_code
        == 200
    )


def test_wallet_proofs_expiry_replay_unique_and_immutable(setup):
    app, client, _ = setup
    register(client)
    wallet, signature = link(client)
    assert client.post("/api/wallet", json={"signature": signature}).status_code == 400
    proof = client.post("/api/challenge", json={}).json()["message"]
    wrong = Account.create()
    signed = Account.sign_message(
        encode_defunct(text=proof), wrong.key
    ).signature.to_0x_hex()
    assert client.post("/api/wallet", json={"signature": signed}).status_code == 409
    with app.state.db.connect() as db:
        db.execute("UPDATE challenges SET expires=0")
    assert client.post("/api/wallet", json={"signature": signed}).status_code == 400
    register(client, "second@example.com")
    proof = client.post("/api/challenge", json={}).json()["message"]
    signed = Account.sign_message(
        encode_defunct(text=proof), wallet.key
    ).signature.to_0x_hex()
    assert client.post("/api/wallet", json={"signature": signed}).status_code == 409


def test_history_isolation_pagination_exact_amounts_and_idempotency(setup):
    app, client, _ = setup
    register(client)
    link(client)
    assert client.post("/api/transactions", json={"hash": HASH}).json()["inserted"] == 1
    assert client.post("/api/transactions", json={"hash": HASH}).json()["inserted"] == 0
    history = client.get("/api/activity?pageSize=1").json()
    assert history["total"] == 1 and len(history["items"]) == 1
    assert history["items"][0]["amount"] == "1000000000000000001"
    assert client.get("/api/activity?page=2&pageSize=1").json()["items"] == []
    assert client.get("/api/activity?kind=Funded").json()["total"] == 0
    assert client.get("/api/activity?kind=made-up").status_code == 422
    assert client.get("/api/activity?pageSize=10000").status_code == 422
    register(client, "other@example.com")
    assert client.get("/api/activity").json()["total"] == 0
    assert HASH not in client.get("/api/transactions/export").text
    assert client.get("/api/audit").status_code == 403
    register(client, "admin@example.com", adminCode="admin-secret")
    assert client.get("/api/activity").json()["total"] == 1
    assert "email" in client.get("/api/activity").json()["items"][0]
    assert client.get("/api/audit").json()["total"] > 0
    register(client, "reviewer@example.com", auditorCode="audit-secret")
    assert client.get("/api/me").json()["role"] == "auditor"
    item = client.get("/api/activity").json()["items"][0]
    assert "email" not in item
    assert "email" not in next(
        csv.reader(io.StringIO(client.get("/api/transactions/export").text))
    )
    assert client.post("/api/transactions", json={"hash": HASH}).status_code == 403
    assert client.get("/api/audit").status_code == 200


def test_security_validation_origin_and_invitation_escalation(setup):
    _, client, _ = setup
    assert (
        client.post(
            "/api/register",
            json={"email": "a@example.com", "password": PASSWORD},
            headers={"Origin": "https://evil.example"},
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/register",
            content="x" * 17000,
            headers={"Content-Type": "application/json"},
        ).status_code
        == 413
    )
    assert (
        client.post(
            "/api/login", json={"email": "a@example.com", "password": "short"}
        ).status_code
        == 422
    )
    assert register(client, role="admin").status_code == 422
    assert (
        register(
            client, adminCode="admin-secret", auditorCode="audit-secret"
        ).status_code
        == 422
    )
    assert client.get("/api/login").status_code == 405
    assert (
        client.post(
            "/api/register",
            content="{broken",
            headers={"Content-Type": "application/json"},
        ).status_code
        == 422
    )
    assert client.get("/api/unknown").status_code == 404


def test_analytics_scope_and_integer_precision(setup):
    app, client, _ = setup
    register(client)
    with app.state.db.connect() as db:
        db.execute(
            "INSERT INTO transactions(hash,log_index,user_id,kind,amount,block) VALUES(?,0,1,'Deposited',?,1)",
            (HASH, "1000000000000000001"),
        )
        db.execute(
            "INSERT INTO transactions(hash,log_index,user_id,kind,amount,block) VALUES(?,1,1,'Deposited',?,1)",
            (HASH, "2"),
        )
    data = client.get("/api/analytics").json()
    assert len(data["days"]) == 14
    assert data["days"][-1]["deposits"] == "1000000000000000003"
    register(client, "another@example.com")
    assert client.get("/api/analytics").json()["days"][-1]["deposits"] == "0"
    register(client, "auditor@example.com", auditorCode="audit-secret")
    assert (
        client.get("/api/analytics").json()["days"][-1]["deposits"]
        == "1000000000000000003"
    )


def test_csv_formula_safety(setup):
    _, client, _ = setup
    register(client, "=formula@example.com")
    link(client)
    client.post("/api/transactions", json={"hash": HASH})
    register(client, "admin@example.com", adminCode="admin-secret")
    rows = list(
        csv.DictReader(io.StringIO(client.get("/api/transactions/export").text))
    )
    assert rows[0]["email"] == "'=formula@example.com"


def test_expired_session_and_persistence_after_restart(setup):
    app, client, settings = setup
    register(client)
    wallet, _ = link(client)
    cookie = client.cookies.get("session")
    with TestClient(create_app(settings, FakeChain())) as restarted:
        restarted.cookies.set("session", cookie)
        assert restarted.get("/api/me").json()["wallet"] == wallet.address
    with app.state.db.connect() as db:
        db.execute("UPDATE sessions SET expires=0")
    assert client.get("/api/me").status_code == 401


def test_migrate_original_node_schema(tmp_path):
    path = tmp_path / "legacy.sqlite"
    with sqlite3.connect(path) as db:
        db.executescript("""CREATE TABLE users(id INTEGER PRIMARY KEY,email TEXT UNIQUE,password TEXT,role TEXT,wallet TEXT UNIQUE);
        CREATE TABLE transactions(hash TEXT,log_index INTEGER,user_id INTEGER REFERENCES users(id),kind TEXT,amount TEXT,block INTEGER,created TEXT DEFAULT CURRENT_TIMESTAMP,PRIMARY KEY(hash,log_index));
        INSERT INTO users VALUES(1,'legacy@example.com','not-a-real-hash','user',NULL);
        INSERT INTO transactions(hash,log_index,user_id,kind,amount,block) VALUES('legacy',0,1,'Deposited','123',1);""")
    from database import Database

    Database(str(path))
    Database(str(path))
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT amount FROM transactions").fetchone()[0] == "123"
        assert {r[1] for r in db.execute("PRAGMA table_info(transactions)")} >= {
            "block_time",
            "block_hash",
        }


def test_secure_cookie_and_rate_limit(tmp_path):
    app = create_app(
        Settings(
            db_path=str(tmp_path / "secure.sqlite"),
            production=True,
            public_origin="https://saving.example",
            auth_limit=1,
        ),
        FakeChain(),
    )
    with TestClient(app, base_url="https://saving.example") as c:
        result = register(c)
        assert (
            "Secure" in result.headers["set-cookie"]
            and "HttpOnly" in result.headers["set-cookie"]
        )
        assert register(c, "second@example.com").status_code == 429
        assert (
            c.post(
                "/api/logout", json={}, headers={"origin": "http://saving.example"}
            ).status_code
            == 403
        )
        assert c.get("/api/docs").status_code == 404


def raw_reader():
    wallet = Account.create().address
    vault = Web3().eth.contract(
        address=Web3.to_checksum_address("0x" + "12" * 20), abi=ABI
    )
    block_hash = HexBytes("0x" + "cd" * 32)
    log = {
        "address": vault.address,
        "topics": [
            Web3.keccak(text="Deposited(address,uint256)"),
            HexBytes("0x" + wallet[2:].zfill(64)),
        ],
        "data": HexBytes((123).to_bytes(32, "big")),
        "logIndex": 0,
        "transactionHash": HexBytes(HASH),
        "transactionIndex": 0,
        "blockHash": block_hash,
        "blockNumber": 42,
        "removed": False,
    }
    receipt = {
        "status": 1,
        "to": vault.address,
        "blockNumber": 42,
        "blockHash": block_hash,
        "transactionHash": HexBytes(HASH),
        "logs": [log],
    }
    eth = SimpleNamespace(
        chain_id=11155111,
        block_number=43,
        get_transaction_receipt=lambda h: receipt,
        get_block=lambda n: {"hash": block_hash, "timestamp": 1792281600},
    )
    chain = ChainReader(Settings())
    chain.web3 = SimpleNamespace(eth=eth)
    chain.vault = vault
    return chain, wallet, receipt, eth


def test_web3_receipt_decode_and_emitter_validation():
    chain, wallet, receipt, eth = raw_reader()
    result = chain.verify_receipt(HASH, wallet)
    assert result[0]["amount"] == "123" and result[0]["kind"] == "Deposited"
    receipt["logs"][0]["address"] = "0x" + "99" * 20
    with pytest.raises(HTTPException, match="No matching"):
        chain.verify_receipt(HASH, wallet)


@pytest.mark.parametrize(
    "scenario",
    [
        "failed",
        "wrong_recipient",
        "wrong_wallet",
        "unconfirmed",
        "wrong_chain",
        "reorg",
    ],
)
def test_reject_untrusted_receipts(scenario):
    chain, wallet, receipt, eth = raw_reader()
    if scenario == "failed":
        receipt["status"] = 0
    if scenario == "wrong_recipient":
        receipt["to"] = "0x" + "99" * 20
    if scenario == "wrong_wallet":
        wallet = Account.create().address
    if scenario == "unconfirmed":
        eth.block_number = 42
    if scenario == "wrong_chain":
        eth.chain_id = 1
    if scenario == "reorg":
        eth.get_block = lambda n: {"hash": HexBytes("0x" + "ef" * 32), "timestamp": 0}
    with pytest.raises(HTTPException):
        chain.verify_receipt(HASH, wallet)
