import hashlib
import hmac
import secrets
import threading
import time
from fastapi import HTTPException


def now_ms():
    return int(time.time() * 1000)


def token_hash(value):
    return hashlib.sha256(value.encode()).hexdigest()


def password_hash(password, salt=None):
    # Node's scryptSync defaults: N=16384, r=8, p=1; salt is the hex STRING.
    # Keeping this encoding lets pre-migration accounts sign in without a reset.
    salt = salt or secrets.token_hex(16)
    digest = hashlib.scrypt(
        password.encode(),
        salt=salt.encode(),
        n=16384,
        r=8,
        p=1,
        dklen=64,
        maxmem=64 * 1024 * 1024,
    )
    return f"{salt}:{digest.hex()}"


def verify_password(password, encoded):
    try:
        salt, expected = encoded.split(":")
        return hmac.compare_digest(
            password_hash(password, salt).split(":")[1], expected
        )
    except (ValueError, TypeError):
        return False


class RateLimiter:
    """Single-instance throttling. Untrusted forwarding headers are not identity."""

    def __init__(self, limit):
        self.limit, self.entries, self.lock = limit, {}, threading.Lock()

    def check(self, key):
        now = time.monotonic()
        with self.lock:
            self.entries = {k: v for k, v in self.entries.items() if v[1] > now}
            count, until = self.entries.get(key, (0, now + 60))
            self.entries[key] = (count + 1, until)
            if count >= self.limit:
                raise HTTPException(429, "Too many attempts. Try again in a minute.")
