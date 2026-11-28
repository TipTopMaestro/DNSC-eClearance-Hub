from app.repositories.students import find_student
from app.repositories.periods import find_period
from app.repositories.clearance import get_student_clearance


REQUIRED_OFFICES = (
    "REGISTRAR",
    "LIBRARY",
    "ACCOUNTING",
    "STUDENT_AFFAIRS"
)


def calculate_overall_status(records: list):
    records_by_office = {
        record["office"]: record
        for record in records
    }

    offices = []

    for office in REQUIRED_OFFICES:
        record = records_by_office.get(office)

        if record is None:
            offices.append({
                "office": office,
                "status": "HOLD",
                "reason": "Awaiting office clearance."
            })

        else:
            offices.append(record)

    is_cleared = all(
        record["status"] == "CLEARED"
        for record in offices
    )

    return {
        "overall_status": (
            "CLEARED" if is_cleared else "HOLD"
        ),
        "offices": offices
    }


def get_clearance_summary(
    student_id: str,
    period_id: int
):
    student = find_student(student_id)

    if student is None:
        raise ValueError("Student not found.")

    period = find_period(period_id)

    if period is None:
        raise ValueError("Clearance period not found.")

    records = get_student_clearance(
        student_id,
        period_id
    )

    summary = calculate_overall_status(records)

    return {
        "student_id": student_id,
        "full_name": student["full_name"],
        "period_id": period_id,
        "overall_status": summary["overall_status"],
        "offices": summary["offices"]
    }
