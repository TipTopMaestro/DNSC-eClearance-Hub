
import re
from decimal import Decimal

ID_RULE = re.compile(r"[0-9]{4}-[0-9]{4}")

EMAIL_RULE = re.compile(
    r"[\w.+-]+@[\w-]+\.[\w.-]+"
)

MONEY_RULE = re.compile(
    r"[0-9]{1,9}(?:\.[0-9]{1,2})?"
)

PROGRAMS = {
    "BSIT": "Bachelor of Science in Information Technology",
    "BSIS": "Bachelor of Science in Information Systems"
}


def validate_student_id(value):
    if not isinstance(value, str):
        return False

    return ID_RULE.fullmatch(value.strip()) is not None


def validate_email(value):
    if not isinstance(value, str):
        return False

    return (
        len(value) <= 255
        and EMAIL_RULE.fullmatch(value.strip()) is not None
    )


def parse_money(value):
    if not isinstance(value, str):
        raise ValueError("Amount must be text.")

    value = value.strip()

    if not MONEY_RULE.fullmatch(value):
        raise ValueError("Invalid monetary amount.")

    return Decimal(value)


def parse_book_count(value):
    if not isinstance(value, str):
        raise ValueError("Book count must be text.")

    value = value.strip()

    if not re.fullmatch(r"[0-9]{1,5}", value):
        raise ValueError("Invalid book count.")

    return int(value)
