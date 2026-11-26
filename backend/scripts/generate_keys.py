import secrets
from cryptography.fernet import Fernet

print("EXCHANGE_KEY_LIBRARY=" + secrets.token_hex(32))
print("EXCHANGE_KEY_ACCOUNTING=" + secrets.token_hex(32))
print("SLIP_SIGNING_KEY=" + secrets.token_hex(32))
print("FERNET_KEY=" + Fernet.generate_key().decode())
