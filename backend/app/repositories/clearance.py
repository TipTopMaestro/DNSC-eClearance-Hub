
from app.database import get_db
from app.schemas import ClearanceRecordInput
from app.utils.dates import utc_now


def save_clearance(conn, record: ClearanceRecordInput):
    conn.execute("""
        INSERT INTO clearance_records (
            student_id,
            period_id,
            office,
            status,
            reason,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?)

        ON CONFLICT(student_id, office, period_id)
        DO UPDATE SET
            status = excluded.status,
            reason = excluded.reason,
            updated_at = excluded.updated_at
    """, (
        record.student_id,
        record.period_id,
        record.office,
        record.status,
        record.reason,
        utc_now()
    ))


def get_student_clearance(
    student_id: str,
    period_id: int
):
    with get_db() as conn:
        rows = conn.execute("""
            SELECT
                office,
                status,
                reason,
                updated_at
            FROM clearance_records
            WHERE student_id = ?
            AND period_id = ?
            ORDER BY office
        """, (
            student_id,
            period_id
        )).fetchall()

        return [dict(row) for row in rows]
