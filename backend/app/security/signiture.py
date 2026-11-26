import hashlib
import hmac
import json


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sign(data: bytes, secret: bytes) -> str:
    return hmac.new(
        secret,
        data,
        hashlib.sha256
    ).hexdigest()


def verify(data: bytes, signature: str,
           secret: bytes) -> bool:

    expected = sign(data, secret)

    return hmac.compare_digest(
        expected,
        signature
    )


def canonical_json(data: dict) -> bytes:
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False
    ).encode("utf-8")
