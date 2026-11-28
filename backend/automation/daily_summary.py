import json
from pathlib import Path

from app.database import get_db
from app.repositories.periods import get_current_period
from app.services.clearance_service import REQUIRED_OFFICES
from app.utils.dates import today_ph


def generate_daily_summary(data_dir=Path("data")):
    today = today_ph()
    period = get_current_period(today)

    summary = {
        "date": today.isoformat(),
        "period_id": period["period_id"] if period else None,
        "offices": []
    }

    if period:
        summary["period_name"] = period["name"]

        with get_db() as conn:
            for office in REQUIRED_OFFICES:
                rows = conn.execute("""
                    SELECT s.student_id
                    FROM students AS s

                    LEFT JOIN clearance_records AS c
                        ON s.student_id = c.student_id
                        AND c.period_id = ?
                        AND c.office = ?

                    WHERE c.status = 'HOLD'
                        OR c.record_id IS NULL

                    ORDER BY s.student_id
                """, (
                    period["period_id"],
                    office
                )).fetchall()

                summary["offices"].append({
                    "office": office,
                    "hold_count": len(rows),
                    "students_on_hold": [
                        "****-" + row["student_id"][-4:]
                        for row in rows
                    ]
                })

    reports_dir = data_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    output = reports_dir / f"hold-summary-{today}.json"

    temporary = output.with_suffix(".tmp")

    with temporary.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=4)

    temporary.replace(output)

    return summary