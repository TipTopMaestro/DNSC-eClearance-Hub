from app.database import get_db
from app.schemas import ClearanceRecordInput
from app.repositories.clearance import save_clearance
from app.utils.dates import utc_now


class ClearanceNotFoundError(Exception):
    pass


def check_references(conn, student_id, period_id):
    student = conn.execute("""
        SELECT student_id
        FROM students
        WHERE student_id = ?
    """, (student_id,)).fetchone()

    if student is None:
        raise ClearanceNotFoundError("Student not found.")

    period = conn.execute("""
        SELECT period_id
        FROM clearance_periods
        WHERE period_id = ?
    """, (period_id,)).fetchone()

    if period is None:
        raise ClearanceNotFoundError("Clearance period not found.")


def read_record(conn, student_id, period_id, office):
    row = conn.execute("""
        SELECT student_id, period_id, office,
               status, reason, updated_at
        FROM clearance_records
        WHERE student_id = ?
            AND period_id = ?
            AND office = ?
    """, (
        student_id,
        period_id,
        office
    )).fetchone()

    return dict(row) if row else None


def get_office_clearance(student_id, period_id, office):
    with get_db() as conn:
        check_references(conn, student_id, period_id)

        record = read_record(
            conn, student_id, period_id, office
        )

        if record is None:
            return {
                "student_id": student_id,
                "period_id": period_id,
                "office": office,
                "status": "HOLD",
                "reason": "Awaiting office clearance.",
                "updated_at": None
            }

        return record


def update_office_clearance(
    student_id,
    period_id,
    user,
    body
):
    office = user["office"]

    record = ClearanceRecordInput(
        student_id=student_id,
        period_id=period_id,
        office=office,
        **body.model_dump()
    )

    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")

        check_references(conn, student_id, period_id)

        previous = read_record(
            conn, student_id, period_id, office
        )

        old_status = previous["status"] if previous else None

        # Reuse existing clearance repository.
        save_clearance(conn, record)

        action = (
            "SIGN_OFF"
            if record.status == "CLEARED"
            else "PLACE_HOLD"
        )

        # Save the audit log in the same transaction.
        conn.execute("""
            INSERT INTO audit_logs (
                actor_user_id,
                student_id,
                period_id,
                office,
                action,
                old_status,
                new_status,
                reason,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user["user_id"],
            student_id,
            period_id,
            office,
            action,
            old_status,
            record.status,
            record.reason,
            utc_now()
        ))

        return read_record(
            conn, student_id, period_id, office
        )