
import hashlib
import hmac
import os

ITERATIONS = 600_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        ITERATIONS
    )

    return (
        f"pbkdf2_sha256:{ITERATIONS}:"
        f"{salt.hex()}:{digest.hex()}"
    )


def check_password(password: str, stored: str) -> bool:
    try:
        algorithm, rounds, salt_hex, digest_hex = (
            stored.split(":")
        )

        iterations = int(rounds)

        if algorithm != "pbkdf2_sha256":
            return False

        if not 200_000 <= iterations <= 2_000_000:
            return False

        salt = bytes.fromhex(salt_hex)

        if len(salt) != 16:
            return False

        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations
        )

        return hmac.compare_digest(
            digest.hex(),
            digest_hex
        )

    except (ValueError, TypeError):
        return False
