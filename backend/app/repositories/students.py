
from app.database import get_db
from app.schemas import StudentRecord
from app.security.encryption import encrypt_text


def upsert_student(
    student: StudentRecord,
    *,
    conn=None
):
    # Use a new connection if the caller
    # did not provide an existing transaction.
    if conn is None:
        with get_db() as own_conn:
            upsert_student(
                student,
                conn=own_conn
            )
        return

    encrypted_email = encrypt_text(
        student.email
    )

    conn.execute("""
        INSERT INTO students (
            student_id,
            full_name,
            program,
            year_level,
            email_encrypted
        )
        VALUES (?, ?, ?, ?, ?)

        ON CONFLICT(student_id)
        DO UPDATE SET
            full_name = excluded.full_name,
            program = excluded.program,
            year_level = excluded.year_level,
            email_encrypted = excluded.email_encrypted
    """, (
        student.student_id,
        student.full_name,
        student.program,
        student.year_level,
        encrypted_email
    ))



def find_student(student_id: str):
    with get_db() as conn:
        row = conn.execute("""
            SELECT
                student_id,
                full_name,
                program,
                year_level
            FROM students
            WHERE student_id = ?
        """, (student_id,)).fetchone()

        return dict(row) if row else None


def list_students():
    with get_db() as conn:
        rows = conn.execute("""
            SELECT
                student_id,
                full_name,
                program,
                year_level
            FROM students
            ORDER BY student_id
        """).fetchall()

        return [dict(row) for row in rows]
