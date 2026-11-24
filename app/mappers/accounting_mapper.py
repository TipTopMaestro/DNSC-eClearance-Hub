from app.utils.validators import (
    validate_student_id,
    parse_money
)


def map_accounting_record(source: dict) -> dict:
    # 1. Validate source fields
    expected = {"student_no", "balance"}

    if set(source) != expected:
        raise ValueError("Unexpected Accounting fields.")

    student_id = source["student_no"]

    if not validate_student_id(student_id):
        raise ValueError("Invalid student ID.")

    balance = parse_money(source["balance"])

    # 2. Transform source data
    status = "HOLD" if balance > 0 else "CLEARED"

    reason = (
        f"Outstanding balance: PHP {balance:.2f}"
        if balance > 0 else None
    )

    # 3. Return common clearance schema
    return {
        "student_id": student_id.strip(),
        "office": "ACCOUNTING",
        "status": status,
        "reason": reason
    }
