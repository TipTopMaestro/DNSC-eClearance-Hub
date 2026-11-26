
import re

from fastapi import Depends, HTTPException, status

from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials
)

from app.repositories.sessions import (
    find_active_session
)


bearer_scheme = HTTPBearer(auto_error=False)

TOKEN_PATTERN = re.compile(
    r"[A-Za-z0-9_-]{43}"
)


def get_bearer_token(
    credentials: HTTPAuthorizationCredentials | None
    = Depends(bearer_scheme)
):
    if (
        credentials is None
        or credentials.scheme.lower() != "bearer"
        or not TOKEN_PATTERN.fullmatch(
            credentials.credentials
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return credentials.credentials


def get_current_user(
    token: str = Depends(get_bearer_token)
):
    user = find_active_session(token)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user


def require_roles(*allowed_roles: str):

    def check_role(
        user: dict = Depends(get_current_user)
    ):
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions."
            )

        return user

    return check_role
