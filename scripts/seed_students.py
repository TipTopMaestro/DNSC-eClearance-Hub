
from app.database import (
    get_db,
    init_db,
    init_additional_tables
)

from app.schemas import (
    StudentRecord,
    ClearanceRecordInput
)

from app.repositories.students import upsert_student
from app.repositories.clearance import save_clearance


def main():
    init_db()
    init_additional_tables()

    students = [
        StudentRecord(
            student_id="2023-0104",
            full_name="Ana Reyes",
            program="BSIT",
            year_level=3,
            email="ana@dnsc.edu.ph"
        ),
        StudentRecord(
            student_id="2023-0105",
            full_name="Ben Cruz",
            program="BSIT",
            year_level=3,
            email="ben@dnsc.edu.ph"
        ),
        StudentRecord(
            student_id="2023-0106",
            full_name="Carla Lim",
            program="BSIS",
            year_level=4,
            email="carla@dnsc.edu.ph"
        )
    ]

    for student in students:
        upsert_student(student)

    with get_db() as conn:
        conn.execute("""
            INSERT INTO clearance_periods (
                name,
                start_date,
                deadline
            )
            VALUES (?, ?, ?)
            ON CONFLICT(name) DO NOTHING
        """, (
            "DEMO Semester",
            "2026-11-24",
            "2026-12-10"
        ))

        period = conn.execute("""
            SELECT period_id
            FROM clearance_periods
            WHERE name = ?
        """, ("DEMO Semester",)).fetchone()

        period_id = period["period_id"]

        sample_records = [
            ("REGISTRAR", "CLEARED", None),
            ("LIBRARY", "HOLD", "One unreturned book."),
            ("ACCOUNTING", "CLEARED", None),
            ("STUDENT_AFFAIRS", "CLEARED", None)
        ]

        for office, status, reason in sample_records:
            record = ClearanceRecordInput(
                student_id="2023-0104",
                period_id=period_id,
                office=office,
                status=status,
                reason=reason
            )

            save_clearance(conn, record)

    print("Demo students created successfully.")
    print("Clearance period ID:", period_id)


if __name__ == "__main__":
    main()
