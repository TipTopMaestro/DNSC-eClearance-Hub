
import secrets
import hashlib
from datetime import datetime, timedelta, timezone

from app.config import TOKEN_EXPIRY_MINUTES


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def get_token_expiration() -> str:
    expiration = (
        datetime.now(timezone.utc)
        + timedelta(minutes=TOKEN_EXPIRY_MINUTES)
    )

    return expiration.isoformat(timespec="seconds")
