
from app.database import get_db
from app.security.tokens import hash_token
from app.utils.dates import utc_now


def create_session(
    user_id: int,
    token: str,
    expires_at: str
):
    token_hash = hash_token(token)

    with get_db() as conn:
        conn.execute("""
            INSERT INTO sessions (
                token_hash,
                user_id,
                created_at,
                expires_at
            )
            VALUES (?, ?, ?, ?)
        """, (
            token_hash,
            user_id,
            utc_now(),
            expires_at
        ))


def find_active_session(token: str):
    token_hash = hash_token(token)

    with get_db() as conn:
        row = conn.execute("""
            SELECT
                u.user_id,
                u.username,
                u.role,
                u.student_id,
                u.office,
                s.expires_at

            FROM sessions AS s

            INNER JOIN users AS u
                ON s.user_id = u.user_id

            WHERE s.token_hash = ?
                AND s.revoked_at IS NULL
                AND s.expires_at > ?
                AND u.is_active = 1
        """, (
            token_hash,
            utc_now()
        )).fetchone()

        return dict(row) if row else None


def revoke_session(token: str):
    with get_db() as conn:
        cursor = conn.execute("""
            UPDATE sessions
            SET revoked_at = ?
            WHERE token_hash = ?
                AND revoked_at IS NULL
        """, (
            utc_now(),
            hash_token(token)
        ))

        return cursor.rowcount > 0


def delete_expired_sessions():
    with get_db() as conn:
        cursor = conn.execute("""
            DELETE FROM sessions
            WHERE expires_at <= ?
        """, (utc_now(),))

        return cursor.rowcount
