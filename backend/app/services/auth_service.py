import secrets

from app.config import TOKEN_EXPIRY_MINUTES
from app.repositories.users import find_user_by_username

from app.repositories.sessions import (
    create_session,
    revoke_session
)

from app.security.passwords import (
    hash_password,
    check_password
)

from app.security.tokens import (
    generate_token,
    get_token_expiration
)

from app.schemas import TokenResponse


class InvalidCredentialsError(Exception):
    pass


# Used to perform a password check even when
# the supplied username does not exist.
DUMMY_PASSWORD_HASH = hash_password(
    secrets.token_urlsafe(32)
)


def authenticate_user(username: str, password: str):
    user = find_user_by_username(username)

    stored_hash = (
        user["password_hash"]
        if user is not None
        else DUMMY_PASSWORD_HASH
    )

    valid_password = check_password(
        password,
        stored_hash
    )

    if (
        user is None
        or not valid_password
        or not user["is_active"]
    ):
        raise InvalidCredentialsError(
            "Invalid username or password."
        )

    token = generate_token()
    expires_at = get_token_expiration()

    create_session(
        user_id=user["user_id"],
        token=token,
        expires_at=expires_at
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=TOKEN_EXPIRY_MINUTES * 60
    )


def logout_user(token: str):
    return revoke_session(token)
