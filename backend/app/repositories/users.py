
from app.database import get_db
from app.security.passwords import hash_password


def create_user(
    username: str,
    password: str,
    role: str,
    student_id: str | None = None,
    office: str | None = None
):
    if len(password) < 12 or len(password) > 128:
        raise ValueError(
            "Password must contain 12 to 128 characters."
        )

    if role not in ("STUDENT", "STAFF", "ADMIN"):
        raise ValueError("Invalid user role.")

    password_hash = hash_password(password)

    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO users (
                username,
                password_hash,
                role,
                student_id,
                office
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            username,
            password_hash,
            role,
            student_id,
            office
        ))

        return cursor.lastrowid


def find_user_by_username(username: str):
    with get_db() as conn:
        row = conn.execute("""
            SELECT
                user_id,
                username,
                password_hash,
                role,
                student_id,
                office,
                is_active
            FROM users
            WHERE username = ?
        """, (username,)).fetchone()

        return dict(row) if row else None


def find_user_by_id(user_id: int):
    with get_db() as conn:
        row = conn.execute("""
            SELECT
                user_id,
                username,
                role,
                student_id,
                office,
                is_active
            FROM users
            WHERE user_id = ?
        """, (user_id,)).fetchone()

        return dict(row) if row else None
