from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response
)

from app.schemas import (
    LoginRequest,
    TokenResponse,
    UserResponse,
    MessageResponse
)

from app.services.auth_service import (
    authenticate_user,
    logout_user,
    InvalidCredentialsError
)

from app.security.permissions import (
    get_current_user,
    get_bearer_token
)

from app.security.rate_limit import check_login_limit


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"]
)


@router.post(
    "/login",
    response_model=TokenResponse
)
def login(
    body: LoginRequest,
    request: Request,
    response: Response
):
    client_ip = (
        request.client.host
        if request.client
        else "unknown"
    )

    check_login_limit(client_ip)

    try:
        result = authenticate_user(
            body.username,
            body.password
        )

    except InvalidCredentialsError:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    response.headers["Cache-Control"] = "no-store"

    return result


@router.get(
    "/me",
    response_model=UserResponse
)
def get_my_account(
    user: dict = Depends(get_current_user)
):
    return UserResponse(
        user_id=user["user_id"],
        username=user["username"],
        role=user["role"],
        student_id=user["student_id"],
        office=user["office"]
    )


@router.post(
    "/logout",
    response_model=MessageResponse
)
def logout(
    token: str = Depends(get_bearer_token),
    user: dict = Depends(get_current_user)
):
    logout_user(token)

    return MessageResponse(
        message="Logged out successfully."
    )
