from app.utils.validators import (
    validate_student_id,
    parse_book_count,
    parse_money
)


def map_library_record(source: dict) -> dict:
    # 1. Validate source fields
    expected = {
        "id",
        "unreturned_books",
        "unpaid_fines"
    }

    if set(source) != expected:
        raise ValueError("Unexpected Library fields.")

    student_id = source["id"]

    if not validate_student_id(student_id):
        raise ValueError("Invalid student ID.")

    books = parse_book_count(source["unreturned_books"])
    fines = parse_money(source["unpaid_fines"])

    # 2. Transform source data
    reasons = []

    if books > 0:
        reasons.append(f"Unreturned books: {books}")

    if fines > 0:
        reasons.append(f"Unpaid fines: PHP {fines:.2f}")

    # 3. Return common clearance schema
    return {
        "student_id": student_id.strip(),
        "office": "LIBRARY",
        "status": "HOLD" if reasons else "CLEARED",
        "reason": "; ".join(reasons) if reasons else None
    }
