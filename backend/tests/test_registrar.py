
import httpx
import pytest

from app.database import get_db

from app.integrations.registrar_client import (
    fetch_students,
    RegistrarAPIError
)

from app.mappers.registrar_mapper import (
    map_registrar_record
)

from app.repositories.students import find_student
from app.repositories.users import create_user

import app.services.registrar_service as service


def valid_source():
    return {
        "id": "2023-0200",
        "name": "Demo Student",
        "program": " bsit ",
        "year": "3",
        "email": "demo@dnsc.edu.ph"
    }


def test_valid_registrar_mapping():
    student = map_registrar_record(
        valid_source()
    )

    assert student.student_id == "2023-0200"
    assert student.year_level == 3
    assert student.program == "BSIT"


@pytest.mark.parametrize(
    "field,value",
    [
        ("id", "104"),
        ("year", "3rd"),
        ("year", 7),
        ("year", True),
        ("program", "UNKNOWN"),
        ("email", "invalid-email"),
        ("name", " ")
    ]
)
def test_invalid_registrar_mapping(field, value):
    source = valid_source()
    source[field] = value

    with pytest.raises(ValueError):
        map_registrar_record(source)


def test_registrar_pagination():
    requested_pages = []

    def handler(request):
        page = int(request.url.params["page"])
        requested_pages.append(page)

        source = valid_source()
        source["id"] = f"2023-020{page}"

        return httpx.Response(
            200,
            json={
                "items": [source],
                "page": page,
                "page_size": 1,
                "total": 2
            }
        )

    transport = httpx.MockTransport(handler)

    with httpx.Client(
        transport=transport,
        base_url="http://registrar.test"
    ) as http_client:
        students = fetch_students(
            http_client,
            page_size=1
        )

    assert len(students) == 2
    assert requested_pages == [1, 2]


@pytest.mark.parametrize(
    "upstream_status",
    [401, 404, 500, 503]
)
def test_registrar_http_errors(upstream_status):
    def handler(request):
        return httpx.Response(upstream_status)

    with httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url="http://registrar.test"
    ) as http_client:
        with pytest.raises(RegistrarAPIError) as error:
            fetch_students(http_client)

    assert error.value.status_code == 502


def test_registrar_timeout():
    attempts = []

    def handler(request):
        attempts.append(1)

        raise httpx.ReadTimeout(
            "Simulated timeout",
            request=request
        )

    with httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url="http://registrar.test"
    ) as http_client:
        with pytest.raises(RegistrarAPIError) as error:
            fetch_students(http_client)

    assert error.value.status_code == 504
    assert len(attempts) == 3


def test_bad_registrar_json():
    def handler(request):
        return httpx.Response(
            200,
            content=b"Not valid JSON"
        )

    with httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url="http://registrar.test"
    ) as http_client:
        with pytest.raises(RegistrarAPIError):
            fetch_students(http_client)


def test_bad_registrar_structure():
    def handler(request):
        return httpx.Response(
            200,
            json={"unexpected": "data"}
        )

    with httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url="http://registrar.test"
    ) as http_client:
        with pytest.raises(RegistrarAPIError):
            fetch_students(http_client)



def admin_headers(client):
    create_user(
        username="admin01",
        password="TestPassword123!",
        role="ADMIN"
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "admin01",
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


def test_admin_sync(client, monkeypatch):
    invalid = valid_source()
    invalid["id"] = "2023-0201"
    invalid["year"] = "3rd"

    monkeypatch.setattr(
        service,
        "fetch_registrar_students",
        lambda: [valid_source(), invalid]
    )

    headers = admin_headers(client)

    response = client.post(
        "/api/v1/admin/sync/registrar",
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert data["received"] == 2
    assert data["accepted"] == 1
    assert data["rejected"] == 1

    assert find_student("2023-0200") is not None
    assert find_student("2023-0201") is None

    result = client.get(
        f"/api/v1/admin/sync/registrar/"
        f"{data['sync_id']}/rejections",
        headers=headers
    )

    assert result.status_code == 200
    assert len(result.json()["items"]) == 1


def test_repeated_sync_no_duplicate(
    client,
    monkeypatch
):
    monkeypatch.setattr(
        service,
        "fetch_registrar_students",
        lambda: [valid_source()]
    )

    headers = admin_headers(client)

    for _ in range(2):
        response = client.post(
            "/api/v1/admin/sync/registrar",
            headers=headers
        )

        assert response.status_code == 200

    with get_db() as conn:
        row = conn.execute("""
            SELECT COUNT(*) AS total
            FROM students
            WHERE student_id = ?
        """, ("2023-0200",)).fetchone()

    assert row["total"] == 1


def test_duplicate_source_ids(
    client,
    monkeypatch
):
    monkeypatch.setattr(
        service,
        "fetch_registrar_students",
        lambda: [
            valid_source(),
            valid_source()
        ]
    )

    response = client.post(
        "/api/v1/admin/sync/registrar",
        headers=admin_headers(client)
    )

    assert response.status_code == 200
    assert response.json()["accepted"] == 0
    assert response.json()["rejected"] == 2
    assert find_student("2023-0200") is None


def test_student_cannot_sync(client):
    login = client.post(
        "/api/v1/auth/login",
        json={
            "username": "student01",
            "password": "TestPassword123!"
        }
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    response = client.post(
        "/api/v1/admin/sync/registrar",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 403


def test_sync_without_token(client):
    response = client.post(
        "/api/v1/admin/sync/registrar"
    )

    assert response.status_code == 401


def test_failed_sync_preserves_data(
    client,
    monkeypatch
):
    original = find_student("2023-0104")

    def handler(request):
        page = int(request.url.params["page"])

        if page == 1:
            source = valid_source()
            source["id"] = "2023-0104"
            source["year"] = 4

            return httpx.Response(
                200,
                json={
                    "items": [source],
                    "page": 1,
                    "page_size": 1,
                    "total": 2
                }
            )

        return httpx.Response(500)

    def fetch_failed_snapshot():
        with httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="http://registrar.test"
        ) as http_client:
            return fetch_students(
                http_client,
                page_size=1
            )

    monkeypatch.setattr(
        service,
        "fetch_registrar_students",
        fetch_failed_snapshot
    )

    response = client.post(
        "/api/v1/admin/sync/registrar",
        headers=admin_headers(client)
    )

    assert response.status_code == 502
    assert find_student("2023-0104") == original

    with get_db() as conn:
        row = conn.execute("""
            SELECT COUNT(*) AS total
            FROM registrar_sync_runs
        """).fetchone()

    assert row["total"] == 0
