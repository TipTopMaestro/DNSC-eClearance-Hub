
import json

from app.database import get_db
from app.services.clearance_service import (
    get_clearance_summary
)


def main():
    with get_db() as conn:
        period = conn.execute("""
            SELECT period_id
            FROM clearance_periods
            WHERE name = ?
        """, ("DEMO Semester",)).fetchone()

    if period is None:
        raise SystemExit("Run seed_students first.")

    summary = get_clearance_summary(
        "2023-0104",
        period["period_id"]
    )

    print(json.dumps(summary, indent=4))


if __name__ == "__main__":
    main()
