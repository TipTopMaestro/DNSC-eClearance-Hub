
import os
from dotenv import load_dotenv

load_dotenv()


def require_env(name):
    value = os.environ.get(name)

    if not value:
        raise RuntimeError(
            f"Required environment variable {name} is missing."
        )

    return value


APP_NAME = os.getenv(
    "APP_NAME", "DNSC e-Clearance Hub"
)

DATABASE_PATH = os.getenv(
    "DATABASE_PATH", "data/clearance.db"
)

REGISTRAR_API_URL = os.getenv(
    "REGISTRAR_API_URL", "http://127.0.0.1:9000"
)

HOLIDAYS_API_URL = os.getenv(
    "HOLIDAYS_API_URL", "https://date.nager.at/api/v3"
)

CLEARANCE_WORKING_DAYS = int(
    os.getenv("CLEARANCE_WORKING_DAYS", "10")
)

TOKEN_EXPIRY_MINUTES = int(
    os.getenv("TOKEN_EXPIRY_MINUTES", "30")
)

EXCHANGE_KEY_LIBRARY = require_env(
    "EXCHANGE_KEY_LIBRARY"
)

EXCHANGE_KEY_ACCOUNTING = require_env(
    "EXCHANGE_KEY_ACCOUNTING"
)

SLIP_SIGNING_KEY = require_env("SLIP_SIGNING_KEY")
FERNET_KEY = require_env("FERNET_KEY")

if not 1 <= CLEARANCE_WORKING_DAYS <= 365:
    raise RuntimeError("Invalid clearance working days.")

if not 1 <= TOKEN_EXPIRY_MINUTES <= 1440:
    raise RuntimeError("Invalid token expiry.")
