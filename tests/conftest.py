
import pytest

from datetime import date
from fastapi.testclient import TestClient

import app.database as database

from app.main import app
from app.schemas import StudentRecord
from app.repositories.students import upsert_student
from app.repositories.users import create_user
from app.repositories.periods import create_period
from app.security.rate_limit import attempts


@pytest.fixture
def client(tmp_path, monkeypatch):

    # Redirect database operations to a temporary DB.
    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        str(tmp_path / "test.db")
    )

    attempts.clear()

    database.init_db()
    database.init_additional_tables()

    upsert_student(
        StudentRecord(
            student_id="2023-0104",
            full_name="Ana Reyes",
            program="BSIT",
            year_level=3,
            email="ana@dnsc.edu.ph"
        )
    )

    create_period(
        name="Test Semester",
        start_date=date(2026, 11, 24),
        deadline=date(2026, 12, 10)
    )

    create_user(
        username="student01",
        password="TestPassword123!",
        role="STUDENT",
        student_id="2023-0104"
    )

    create_user(
        username="library01",
        password="TestPassword123!",
        role="STAFF",
        office="LIBRARY"
    )

    with TestClient(app) as test_client:
        yield test_client

    attempts.clear()
