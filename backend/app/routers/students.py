from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query
)

from app.security.permissions import require_roles
from app.repositories.students import find_student
from app.repositories.periods import find_period

from app.services.clearance_service import (
    get_clearance_summary
)


router = APIRouter(
    prefix="/api/v1",
    tags=["Students"]
)


@router.get("/students/me")
def get_my_student_profile(
    user: dict = Depends(
        require_roles("STUDENT")
    )
):
    student_id = user["student_id"]

    student = find_student(student_id)

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student record not found."
        )

    return student


@router.get("/clearance/me")
def get_my_clearance(
    period_id: int = Query(gt=0),

    user: dict = Depends(
        require_roles("STUDENT")
    )
):
    student_id = user["student_id"]

    if find_period(period_id) is None:
        raise HTTPException(
            status_code=404,
            detail="Clearance period not found."
        )

    try:
        return get_clearance_summary(
            student_id,
            period_id
        )

    except ValueError:
        raise HTTPException(
            status_code=404,
            detail="Clearance record not found."
        )
