"""Backward-compatible SQLite storage. All amounts are decimal wei strings."""

from contextlib import contextmanager
from pathlib import Path
import sqlite3


class Database:
    def __init__(self, path: str):
        if path == ":memory:":
            raise ValueError(
                "Use a temporary database file for tests; connections are request-scoped."
            )
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS users(
                    id INTEGER PRIMARY KEY, email TEXT UNIQUE, password TEXT,
                    role TEXT, wallet TEXT UNIQUE);
                CREATE TABLE IF NOT EXISTS sessions(
                    token TEXT PRIMARY KEY, user_id INTEGER REFERENCES users(id), expires INTEGER);
                CREATE TABLE IF NOT EXISTS challenges(
                    user_id INTEGER PRIMARY KEY, message TEXT, expires INTEGER);
                CREATE TABLE IF NOT EXISTS transactions(
                    hash TEXT, log_index INTEGER, user_id INTEGER REFERENCES users(id),
                    kind TEXT, amount TEXT, block INTEGER, created TEXT DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY(hash,log_index));
                CREATE TABLE IF NOT EXISTS audit_log(
                    id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id),
                    action TEXT NOT NULL, detail TEXT NOT NULL DEFAULT '',
                    created TEXT DEFAULT CURRENT_TIMESTAMP);
                CREATE INDEX IF NOT EXISTS ix_sessions_user ON sessions(user_id);
                CREATE INDEX IF NOT EXISTS ix_transactions_user_block ON transactions(user_id,block DESC);
                CREATE INDEX IF NOT EXISTS ix_audit_id ON audit_log(id DESC);
            """)
            # Additive migration preserves old Node accounts, sessions and history.
            columns = {r["name"] for r in db.execute("PRAGMA table_info(transactions)")}
            for name, sql_type in [("block_time", "TEXT"), ("block_hash", "TEXT")]:
                if name not in columns:
                    db.execute(f"ALTER TABLE transactions ADD COLUMN {name} {sql_type}")
            # Historical Node addresses were checksummed; normalise unique comparison.
            db.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_wallet_case ON users(lower(wallet)) WHERE wallet IS NOT NULL"
            )
            db.execute("PRAGMA user_version=2")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def audit(db, user_id, action, detail=""):
        db.execute(
            "INSERT INTO audit_log(user_id,action,detail) VALUES(?,?,?)",
            (user_id, action, detail),
        )
