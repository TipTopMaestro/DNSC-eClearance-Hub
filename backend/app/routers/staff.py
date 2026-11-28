from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query
)

from app.schemas import ClearanceUpdate
from app.security.permissions import require_roles
from app.repositories.students import list_students

from app.services.staff_service import (
    get_office_clearance,
    update_office_clearance,
    ClearanceNotFoundError
)


router = APIRouter(
    prefix="/api/v1/staff",
    tags=["Staff"]
)


@router.get("/students")
def get_students(
    user: dict = Depends(require_roles("STAFF"))
):
    return list_students()


@router.get("/clearance/{student_id}")
def get_clearance(
    student_id: str = Path(
        pattern=r"^[0-9]{4}-[0-9]{4}$"
    ),
    period_id: int = Query(gt=0),
    user: dict = Depends(require_roles("STAFF"))
):
    try:
        return get_office_clearance(
            student_id,
            period_id,
            user["office"]
        )

    except ClearanceNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )


@router.patch("/clearance/{student_id}")
def update_clearance(
    body: ClearanceUpdate,
    student_id: str = Path(
        pattern=r"^[0-9]{4}-[0-9]{4}$"
    ),
    period_id: int = Query(gt=0),
    user: dict = Depends(require_roles("STAFF"))
):
    try:
        return update_office_clearance(
            student_id,
            period_id,
            user,
            body
        )

    except ClearanceNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )