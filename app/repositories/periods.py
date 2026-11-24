
from datetime import date

from app.database import get_db


def create_period(
    name: str,
    start_date: date,
    deadline: date
):
    if not name.strip():
        raise ValueError("Period name is required.")

    if deadline < start_date:
        raise ValueError(
            "Deadline cannot be before the start date."
        )

    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO clearance_periods (
                name,
                start_date,
                deadline
            )
            VALUES (?, ?, ?)
        """, (
            name.strip(),
            start_date.isoformat(),
            deadline.isoformat()
        ))

        return cursor.lastrowid


def find_period(period_id: int):
    with get_db() as conn:
        row = conn.execute("""
            SELECT *
            FROM clearance_periods
            WHERE period_id = ?
        """, (period_id,)).fetchone()

        return dict(row) if row else None


def list_periods():
    with get_db() as conn:
        rows = conn.execute("""
            SELECT *
            FROM clearance_periods
            ORDER BY start_date DESC
        """).fetchall()

        return [dict(row) for row in rows]
