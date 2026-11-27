import os
from dotenv import load_dotenv
import re

load_dotenv()
from datetime import date

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



FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "http://127.0.0.1:5500"
    ).split(",")
    if origin.strip()
]

#Registrar Pagination

REGISTRAR_PAGE_SIZE = int(
    os.getenv("REGISTRAR_PAGE_SIZE", "100")
)

if not 1 <= REGISTRAR_PAGE_SIZE <= 100:
    raise RuntimeError(
        "Invalid Registrar page size."
    )
    
#DATES CONFIGURATIONS

HOLIDAYS_CACHE_SECONDS = int(
    os.getenv("HOLIDAYS_CACHE_SECONDS", "21600")
)

if not 0 <= HOLIDAYS_CACHE_SECONDS <= 86400:
    raise RuntimeError("Invalid holidays cache duration.")


def parse_extra_closures():
    raw = os.getenv("EXTRA_NON_WORKING_DATES", "")
    dates = set()

    for value in raw.split(","):
        value = value.strip()

        if not value:
            continue

        try:
            if not re.fullmatch(
                r"[0-9]{4}-[0-9]{2}-[0-9]{2}",
                value
            ):
                raise ValueError()

            dates.add(date.fromisoformat(value))

        except ValueError:
            raise RuntimeError(
                "Invalid EXTRA_NON_WORKING_DATES configuration."
            ) from None

    return frozenset(dates)


EXTRA_NON_WORKING_DATES = parse_extra_closures()
