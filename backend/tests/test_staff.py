import pytest

from app.database import get_db
from app.repositories.users import create_user


URL = "/api/v1/staff/clearance/2023-0104?period_id=1"


def login_headers(client, username):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": username,
            "password": "TestPassword123!"
        }
    )

    assert response.status_code == 200

    return {
        "Authorization": (
            "Bearer " + response.json()["access_token"]
        )
    }


def test_staff_student_list(client):
    response = client.get(
        "/api/v1/staff/students",
        headers=login_headers(client, "library01")
    )

    assert response.status_code == 200

    assert any(
        student["student_id"] == "2023-0104"
        for student in response.json()
    )


def test_missing_record_is_hold(client):
    response = client.get(
        URL,
        headers=login_headers(client, "library01")
    )

    assert response.status_code == 200
    assert response.json()["office"] == "LIBRARY"
    assert response.json()["status"] == "HOLD"


def test_staff_sign_off(client):
    response = client.patch(
        URL,
        json={
            "status": "CLEARED",
            "reason": None
        },
        headers=login_headers(client, "library01")
    )

    assert response.status_code == 200
    assert response.json()["status"] == "CLEARED"
    assert response.json()["office"] == "LIBRARY"


def test_staff_place_hold(client):
    response = client.patch(
        URL,
        json={
            "status": "HOLD",
            "reason": "Unreturned book."
        },
        headers=login_headers(client, "library01")
    )

    assert response.status_code == 200
    assert response.json()["status"] == "HOLD"
    assert response.json()["reason"] == "Unreturned book."


def test_student_cannot_sign_off(client):
    response = client.patch(
        URL,
        json={"status": "CLEARED"},
        headers=login_headers(client, "student01")
    )

    assert response.status_code == 403


def test_staff_cannot_select_another_office(client):
    response = client.patch(
        URL,
        json={
            "office": "ACCOUNTING",
            "status": "CLEARED"
        },
        headers=login_headers(client, "library01")
    )

    assert response.status_code == 422


def test_hold_requires_reason(client):
    response = client.patch(
        URL,
        json={"status": "HOLD"},
        headers=login_headers(client, "library01")
    )

    assert response.status_code == 422


def test_staff_cannot_modify_unknown_student(client):
    response = client.patch(
        "/api/v1/staff/clearance/2023-9999?period_id=1",
        json={"status": "CLEARED"},
        headers=login_headers(client, "library01")
    )

    assert response.status_code == 404


def test_audit_log_created(client):
    headers = login_headers(client, "library01")

    first = client.patch(
        URL,
        json={
            "status": "HOLD",
            "reason": "Unreturned book."
        },
        headers=headers
    )

    assert first.status_code == 200

    second = client.patch(
        URL,
        json={"status": "CLEARED"},
        headers=headers
    )

    assert second.status_code == 200

    with get_db() as conn:
        audit = conn.execute("""
            SELECT office, action, old_status, new_status
            FROM audit_logs
            ORDER BY audit_id DESC
            LIMIT 1
        """).fetchone()

    assert audit["office"] == "LIBRARY"
    assert audit["action"] == "SIGN_OFF"
    assert audit["old_status"] == "HOLD"
    assert audit["new_status"] == "CLEARED"


def test_student_affairs_manual_clearance(client):
    create_user(
        username="affairs01",
        password="TestPassword123!",
        role="STAFF",
        office="STUDENT_AFFAIRS"
    )

    response = client.patch(
        URL,
        json={
            "status": "HOLD",
            "reason": "Unreturned equipment."
        },
        headers=login_headers(client, "affairs01")
    )

    assert response.status_code == 200
    assert response.json()["office"] == "STUDENT_AFFAIRS"


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/v1/admin/imports",
        "/api/v1/admin/rejections",
        "/api/v1/admin/audit"
    ]
)
def test_staff_cannot_access_admin_logs(client, endpoint):
    response = client.get(
        endpoint,
        headers=login_headers(client, "library01")
    )

    assert response.status_code == 403


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/v1/admin/imports",
        "/api/v1/admin/rejections",
        "/api/v1/admin/audit"
    ]
)
def test_admin_can_access_logs(client, endpoint):
    create_user(
        username="testadmin",
        password="TestPassword123!",
        role="ADMIN"
    )

    response = client.get(
        endpoint,
        headers=login_headers(client, "testadmin")
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)