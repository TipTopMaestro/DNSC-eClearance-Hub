from datetime import date

import pytest

import app.services.deadline_service as service

from app.repositories.users import create_user
from app.repositories.periods import get_current_period
from app.integrations.holidays_client import (
    HolidaysAPIError
)

import app.routers.deadlines as deadline_router



@pytest.fixture(autouse=True)
def mock_holidays(monkeypatch):
    holiday_data = {
        2026: frozenset({
            date(2026, 12, 25),
            date(2026, 12, 30),
            date(2026, 12, 31)
        }),
        2027: frozenset({
            date(2027, 1, 1)
        })
    }

    monkeypatch.setattr(
        service,
        "get_public_holidays",
        lambda year: holiday_data.get(
            year, frozenset()
        )
    )

    monkeypatch.setattr(
        service,
        "EXTRA_NON_WORKING_DATES",
        frozenset()
    )


def test_normal_working_days():
    result = service.calculate_deadline(
        date(2026, 11, 23),
        3
    )

    assert result == date(2026, 11, 26)


def test_start_date_excluded():
    result = service.calculate_deadline(
        date(2026, 11, 23),
        1
    )

    assert result == date(2026, 11, 24)


def test_skip_weekend():
    result = service.calculate_deadline(
        date(2026, 11, 27),
        1
    )

    assert result == date(2026, 11, 30)


def test_skip_public_holiday():
    result = service.calculate_deadline(
        date(2026, 12, 24),
        1
    )

    assert result == date(2026, 12, 28)


def test_cross_year_boundary():
    result = service.calculate_deadline(
        date(2026, 12, 24),
        3
    )

    assert result == date(2027, 1, 4)


def test_start_on_weekend():
    result = service.calculate_deadline(
        date(2026, 12, 26),
        1
    )

    assert result == date(2026, 12, 28)


def test_extra_campus_closure(monkeypatch):
    monkeypatch.setattr(
        service,
        "EXTRA_NON_WORKING_DATES",
        frozenset({date(2026, 12, 28)})
    )

    result = service.calculate_deadline(
        date(2026, 12, 24),
        1
    )

    assert result == date(2026, 12, 29)


@pytest.mark.parametrize(
    "working_days",
    [0, -1, 366, True]
)
def test_invalid_working_days(working_days):
    with pytest.raises(ValueError):
        service.calculate_deadline(
            date(2026, 12, 24),
            working_days
        )


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
            "Bearer "
            + response.json()["access_token"]
        )
    }


def make_admin(client):
    create_user(
        username="deadlineadmin",
        password="TestPassword123!",
        role="ADMIN"
    )

    return login_headers(
        client,
        "deadlineadmin"
    )


def sample_period():
    return {
        "name": "Holiday Test Semester",
        "start_date": "2026-12-24",
        "working_days": 3
    }


def test_admin_create_period(client):
    response = client.post(
        "/api/v1/admin/periods",
        json=sample_period(),
        headers=make_admin(client)
    )

    assert response.status_code == 201
    assert response.json()["deadline"] == "2027-01-04"


def test_student_cannot_create_period(client):
    response = client.post(
        "/api/v1/admin/periods",
        json=sample_period(),
        headers=login_headers(client, "student01")
    )

    assert response.status_code == 403


def test_invalid_period_date(client):
    body = sample_period()
    body["start_date"] = "2026-02-30"

    response = client.post(
        "/api/v1/admin/periods",
        json=body,
        headers=make_admin(client)
    )

    assert response.status_code == 422


def test_duplicate_period(client):
    headers = make_admin(client)

    first = client.post(
        "/api/v1/admin/periods",
        json=sample_period(),
        headers=headers
    )

    assert first.status_code == 201

    second = client.post(
        "/api/v1/admin/periods",
        json=sample_period(),
        headers=headers
    )

    assert second.status_code == 409


def test_overlapping_period(client):
    body = sample_period()

    # Existing test period:
    # November 24 to December 10.
    body["start_date"] = "2026-11-25"

    response = client.post(
        "/api/v1/admin/periods",
        json=body,
        headers=make_admin(client)
    )

    assert response.status_code == 409


def test_get_current_deadline(client, monkeypatch):
    monkeypatch.setattr(
        deadline_router,
        "today_ph",
        lambda: date(2026, 11, 27)
    )

    response = client.get(
        "/api/v1/deadlines/current",
        headers=login_headers(client, "student01")
    )

    assert response.status_code == 200

    data = response.json()

    assert data["deadline"] == "2026-12-10"
    assert data["days_remaining"] == 13
    assert data["is_open"] is True


def test_deadline_has_passed(client, monkeypatch):
    monkeypatch.setattr(
        deadline_router,
        "today_ph",
        lambda: date(2026, 12, 11)
    )

    response = client.get(
        "/api/v1/deadlines/current",
        headers=login_headers(client, "student01")
    )

    assert response.status_code == 200
    assert response.json()["deadline_passed"] is True
    assert response.json()["is_open"] is False


def test_no_started_period(client, monkeypatch):
    monkeypatch.setattr(
        deadline_router,
        "today_ph",
        lambda: date(2026, 1, 1)
    )

    response = client.get(
        "/api/v1/deadlines/current",
        headers=login_headers(client, "student01")
    )

    assert response.status_code == 404


def test_holiday_failure_does_not_create_period(
    client,
    monkeypatch
):
    def unavailable(year):
        raise HolidaysAPIError(
            "Holidays API is unavailable.",
            503
        )

    monkeypatch.setattr(
        service,
        "get_public_holidays",
        unavailable
    )

    response = client.post(
        "/api/v1/admin/periods",
        json=sample_period(),
        headers=make_admin(client)
    )

    assert response.status_code == 503

    period = get_current_period(
        date(2026, 12, 25)
    )

    assert period["name"] == "Test Semester"