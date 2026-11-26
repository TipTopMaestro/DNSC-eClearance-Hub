
from cryptography.fernet import Fernet
from app.config import FERNET_KEY


cipher = Fernet(FERNET_KEY.encode())


def encrypt_text(value: str) -> str:
    return cipher.encrypt(
        value.encode("utf-8")
    ).decode()


def decrypt_text(value: str) -> str:
    return cipher.decrypt(
        value.encode()
    ).decode()


def encrypt_bytes(data: bytes) -> bytes:
    return cipher.encrypt(data)


def decrypt_bytes(data: bytes) -> bytes:
    return cipher.decrypt(data)
