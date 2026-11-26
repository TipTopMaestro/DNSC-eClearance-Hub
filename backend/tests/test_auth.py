
from app.database import get_db
from app.repositories.users import find_user_by_username
from app.security.tokens import hash_token


def login(client, username="student01"):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": username,
            "password": "TestPassword123!"
        }
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}"
    }


def test_successful_login(client):
    token = login(client)

    assert len(token) == 43


def test_wrong_password(client):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "student01",
            "password": "IncorrectPassword"
        }
    )

    assert response.status_code == 401


def test_missing_token(client):
    response = client.get(
        "/api/v1/auth/me"
    )

    assert response.status_code == 401


def test_student_profile(client):
    token = login(client)

    response = client.get(
        "/api/v1/students/me",
        headers=auth_headers(token)
    )

    assert response.status_code == 200

    data = response.json()

    assert data["student_id"] == "2023-0104"
    assert "email_encrypted" not in data
    assert "password_hash" not in data


def test_wrong_role(client):
    token = login(client, "library01")

    response = client.get(
        "/api/v1/students/me",
        headers=auth_headers(token)
    )

    assert response.status_code == 403


def test_logout_revokes_token(client):
    token = login(client)
    headers = auth_headers(token)

    logout = client.post(
        "/api/v1/auth/logout",
        headers=headers
    )

    assert logout.status_code == 200

    response = client.get(
        "/api/v1/auth/me",
        headers=headers
    )

    assert response.status_code == 401


def test_expired_token(client):
    token = login(client)

    with get_db() as conn:
        conn.execute("""
            UPDATE sessions
            SET expires_at = ?
            WHERE token_hash = ?
        """, (
            "2000-01-01T00:00:00+00:00",
            hash_token(token)
        ))

    response = client.get(
        "/api/v1/auth/me",
        headers=auth_headers(token)
    )

    assert response.status_code == 401


def test_sql_injection_repository(client):
    result = find_user_by_username(
        "x' OR '1'='1"
    )

    assert result is None


def test_invalid_login_input(client):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "x' OR '1'='1",
            "password": "TestPassword123!"
        }
    )

    assert response.status_code == 422


def test_token_is_hashed_in_database(client):
    token = login(client)

    with get_db() as conn:
        session = conn.execute("""
            SELECT token_hash
            FROM sessions
            WHERE token_hash = ?
        """, (hash_token(token),)).fetchone()

    assert session is not None
    assert session["token_hash"] != token
    assert session["token_hash"] == hash_token(token)


def test_password_hash_not_exposed(client):
    token = login(client)

    response = client.get(
        "/api/v1/auth/me",
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    assert "password_hash" not in response.json()


def test_invalid_clearance_period(client):
    token = login(client)

    response = client.get(
        "/api/v1/clearance/me?period_id=-1",
        headers=auth_headers(token)
    )

    assert response.status_code == 422


def test_login_rate_limit(client):
    for _ in range(5):
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "student01",
                "password": "IncorrectPassword"
            }
        )

        assert response.status_code == 401

    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "student01",
            "password": "IncorrectPassword"
        }
    )

    assert response.status_code == 429
