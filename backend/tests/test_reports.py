import csv
import json
import pytest

from io import StringIO
from xml.etree import ElementTree as ET

from app.database import get_db
from app.repositories.users import create_user
from app.repositories.clearance import save_clearance
from app.schemas import ClearanceRecordInput

from app.services.report_service import (
    build_clearance_report,
    safe_csv_cell
)


URL = "/api/v1/reports/clearance"


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


def admin_headers(client):
    create_user(
        username="reportadmin",
        password="TestPassword123!",
        role="ADMIN"
    )

    return login_headers(client, "reportadmin")


@pytest.mark.parametrize(
    "format,media_type",
    [
        ("csv", "text/csv"),
        ("json", "application/json"),
        ("xml", "application/xml")
    ]
)
def test_report_formats(client, format, media_type):
    response = client.get(
        URL,
        params={
            "period_id": 1,
            "format": format
        },
        headers=admin_headers(client)
    )

    assert response.status_code == 200

    assert response.headers[
        "content-type"
    ].startswith(media_type)

    assert (
        f"clearance-period-1.{format}"
        in response.headers["content-disposition"]
    )

    assert "2023-0104" not in response.text
    assert "****-0104" in response.text

    if format == "csv":
        records = list(
            csv.DictReader(StringIO(response.text))
        )

    elif format == "json":
        records = json.loads(response.text)

    else:
        root = ET.fromstring(response.content)

        records = [
            {
                child.tag: child.text
                for child in student
            }
            for student in root.findall("student")
        ]

    assert len(records) == 1
    assert records[0]["student_id_masked"] == "****-0104"
    assert records[0]["overall_status"] == "HOLD"


def test_registrar_can_download(client):
    create_user(
        username="reportregistrar",
        password="TestPassword123!",
        role="STAFF",
        office="REGISTRAR"
    )

    response = client.get(
        URL,
        params={"period_id": 1},
        headers=login_headers(
            client, "reportregistrar"
        )
    )

    assert response.status_code == 200


@pytest.mark.parametrize(
    "username",
    ["student01", "library01"]
)
def test_unauthorized_roles(client, username):
    response = client.get(
        URL,
        params={"period_id": 1},
        headers=login_headers(client, username)
    )

    assert response.status_code == 403


def test_missing_token(client):
    response = client.get(
        URL,
        params={"period_id": 1}
    )

    assert response.status_code == 401


def test_invalid_format(client):
    response = client.get(
        URL,
        params={
            "period_id": 1,
            "format": "pdf"
        },
        headers=admin_headers(client)
    )

    assert response.status_code == 422


def test_nonexistent_period(client):
    response = client.get(
        URL,
        params={"period_id": 9999},
        headers=admin_headers(client)
    )

    assert response.status_code == 404


def test_invalid_period(client):
    response = client.get(
        URL,
        params={"period_id": -1},
        headers=admin_headers(client)
    )

    assert response.status_code == 422


def test_fully_cleared_student(client):
    offices = [
        "REGISTRAR",
        "LIBRARY",
        "ACCOUNTING",
        "STUDENT_AFFAIRS"
    ]

    with get_db() as conn:
        for office in offices:
            save_clearance(
                conn,
                ClearanceRecordInput(
                    student_id="2023-0104",
                    period_id=1,
                    office=office,
                    status="CLEARED",
                    reason=None
                )
            )

    report = build_clearance_report(1)

    assert report[0]["overall_status"] == "CLEARED"


def test_csv_formula_sanitization():
    assert safe_csv_cell("=1+1") == "'=1+1"
    assert safe_csv_cell("+123") == "'+123"
    assert safe_csv_cell("CLEARED") == "CLEARED"
    assert safe_csv_cell("****-0104") == "****-0104"