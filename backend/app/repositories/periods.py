from datetime import date

from app.database import get_db

class PeriodConflictError(Exception):
    pass


def create_period(
    name: str,
    start_date: date,
    deadline: date
):
    name = name.strip()

    if not name:
        raise ValueError(
            "Period name is required."
        )

    if deadline < start_date:
        raise ValueError(
            "Deadline cannot be before the start date."
        )

    with get_db() as conn:

        # Prevent another writer from inserting
        # a conflicting period between our check
        # and INSERT operation.
        conn.execute("BEGIN IMMEDIATE")

        existing_name = conn.execute("""
            SELECT period_id
            FROM clearance_periods
            WHERE name = ?
        """, (name,)).fetchone()

        if existing_name:
            raise PeriodConflictError(
                "A period with this name already exists."
            )

        overlapping = conn.execute("""
            SELECT period_id
            FROM clearance_periods
            WHERE start_date <= ?
                AND deadline >= ?
        """, (
            deadline.isoformat(),
            start_date.isoformat()
        )).fetchone()

        if overlapping:
            raise PeriodConflictError(
                "Clearance period overlaps an existing period."
            )

        cursor = conn.execute("""
            INSERT INTO clearance_periods (
                name,
                start_date,
                deadline
            )
            VALUES (?, ?, ?)
        """, (
            name,
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

def get_current_period(today: date):
    with get_db() as conn:
        row = conn.execute("""
            SELECT
                period_id,
                name,
                start_date,
                deadline

            FROM clearance_periods

            WHERE start_date <= ?

            ORDER BY
                start_date DESC,
                period_id DESC

            LIMIT 1
        """, (
            today.isoformat(),
        )).fetchone()

        return dict(row) if row else None
