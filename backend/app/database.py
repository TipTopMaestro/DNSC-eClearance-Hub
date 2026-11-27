
import sqlite3
from pathlib import Path
from contextlib import contextmanager

from app.config import DATABASE_PATH


@contextmanager
def get_db():
    path = Path(DATABASE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(
        str(path),
        timeout=10
    )

    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA foreign_keys = ON")

    try:
        yield conn
        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                program TEXT NOT NULL,
                year_level INTEGER NOT NULL
                    CHECK(year_level BETWEEN 1 AND 4),
                email_encrypted TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,

                role TEXT NOT NULL
                    CHECK(role IN (
                        'STUDENT', 'STAFF', 'ADMIN'
                    )),

                student_id TEXT,
                office TEXT,

                is_active INTEGER NOT NULL DEFAULT 1
                    CHECK(is_active IN (0, 1)),

                FOREIGN KEY(student_id)
                    REFERENCES students(student_id),

                CHECK (
                    (
                        role = 'STUDENT'
                        AND student_id IS NOT NULL
                        AND office IS NULL
                    )
                    OR
                    (
                        role = 'STAFF'
                        AND student_id IS NULL
                        AND office IS NOT NULL
                        AND office IN (
                            'REGISTRAR',
                            'LIBRARY',
                            'ACCOUNTING',
                            'STUDENT_AFFAIRS'
                        )
                    )
                    OR
                    (
                        role = 'ADMIN'
                        AND student_id IS NULL
                        AND office IS NULL
                    )
                )
            );

            CREATE TABLE IF NOT EXISTS clearance_periods (
                period_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                start_date TEXT NOT NULL,
                deadline TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS clearance_records (
                record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                period_id INTEGER NOT NULL,

                office TEXT NOT NULL
                    CHECK(office IN (
                        'REGISTRAR',
                        'LIBRARY',
                        'ACCOUNTING',
                        'STUDENT_AFFAIRS'
                    )),

                status TEXT NOT NULL DEFAULT 'HOLD'
                    CHECK(status IN ('CLEARED', 'HOLD')),

                reason TEXT,
                updated_at TEXT NOT NULL,

                FOREIGN KEY(student_id)
                    REFERENCES students(student_id),

                FOREIGN KEY(period_id)
                    REFERENCES clearance_periods(period_id),

                UNIQUE(student_id, office, period_id),

                CHECK (
                    (status = 'CLEARED' AND reason IS NULL)
                    OR
                    (
                        status = 'HOLD'
                        AND reason IS NOT NULL
                        AND length(trim(reason)) > 0
                    )
                )
            );
        """)

def init_additional_tables():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                revoked_at TEXT,

                FOREIGN KEY(user_id)
                    REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS import_batches (
                batch_id TEXT PRIMARY KEY,

                office TEXT NOT NULL
                    CHECK(office IN (
                        'LIBRARY',
                        'ACCOUNTING'
                    )),

                period_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                source_created_at TEXT NOT NULL,
                processed_at TEXT NOT NULL,

                accepted_count INTEGER NOT NULL DEFAULT 0
                    CHECK(accepted_count >= 0),

                rejected_count INTEGER NOT NULL DEFAULT 0
                    CHECK(rejected_count >= 0),

                FOREIGN KEY(period_id)
                    REFERENCES clearance_periods(period_id)
            );

            CREATE TABLE IF NOT EXISTS import_rejections (
                rejection_id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT NOT NULL,
                record_number INTEGER NOT NULL,
                student_id_masked TEXT,
                reason TEXT NOT NULL,
                rejected_at TEXT NOT NULL,

                FOREIGN KEY(batch_id)
                    REFERENCES import_batches(batch_id)
            );

            CREATE TABLE IF NOT EXISTS audit_logs (
                audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                actor_user_id INTEGER NOT NULL,
                student_id TEXT NOT NULL,
                period_id INTEGER NOT NULL,
                office TEXT NOT NULL,

                action TEXT NOT NULL
                    CHECK(action IN (
                        'SIGN_OFF',
                        'PLACE_HOLD'
                    )),

                old_status TEXT
                    CHECK(old_status IN ('CLEARED', 'HOLD')),

                new_status TEXT NOT NULL
                    CHECK(new_status IN ('CLEARED', 'HOLD')),

                reason TEXT,
                created_at TEXT NOT NULL,

                FOREIGN KEY(actor_user_id)
                    REFERENCES users(user_id),

                FOREIGN KEY(student_id)
                    REFERENCES students(student_id),

                FOREIGN KEY(period_id)
                    REFERENCES clearance_periods(period_id)
            );

            CREATE TABLE IF NOT EXISTS clearance_slips (
                slip_id TEXT PRIMARY KEY,
                student_id TEXT NOT NULL,
                period_id INTEGER NOT NULL,
                issued_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                revoked_at TEXT,

                FOREIGN KEY(student_id)
                    REFERENCES students(student_id),

                FOREIGN KEY(period_id)
                    REFERENCES clearance_periods(period_id)
            );

            CREATE INDEX IF NOT EXISTS idx_sessions_user
                ON sessions(user_id);

            CREATE INDEX IF NOT EXISTS idx_clearance_period
                ON clearance_records(period_id, office, status);

            CREATE INDEX IF NOT EXISTS idx_audit_student
                ON audit_logs(student_id, period_id);

            CREATE INDEX IF NOT EXISTS idx_import_source
                ON import_batches(office, period_id, source_created_at);
        """)


def init_registrar_tables():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS registrar_sync_runs (
                sync_id INTEGER PRIMARY KEY AUTOINCREMENT,

                actor_user_id INTEGER NOT NULL,

                started_at TEXT NOT NULL,
                completed_at TEXT NOT NULL,

                received_count INTEGER NOT NULL
                    CHECK(received_count >= 0),

                accepted_count INTEGER NOT NULL
                    CHECK(accepted_count >= 0),

                rejected_count INTEGER NOT NULL
                    CHECK(rejected_count >= 0),

                CHECK(
                    received_count =
                    accepted_count + rejected_count
                ),

                FOREIGN KEY(actor_user_id)
                    REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS registrar_sync_rejections (
                rejection_id INTEGER PRIMARY KEY AUTOINCREMENT,

                sync_id INTEGER NOT NULL,

                record_number INTEGER NOT NULL
                    CHECK(record_number > 0),

                reason TEXT NOT NULL,
                rejected_at TEXT NOT NULL,

                FOREIGN KEY(sync_id)
                    REFERENCES registrar_sync_runs(sync_id),

                UNIQUE(sync_id, record_number)
            );
        """)
