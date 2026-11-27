from datetime import date

from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from app.security.permissions import (
    get_current_user
)

from app.repositories.periods import (
    get_current_period
)

from app.utils.dates import today_ph


router = APIRouter(
    prefix="/api/v1/deadlines",
    tags=["Clearance Deadlines"]
)


@router.get("/current")
def current_deadline(
    user: dict = Depends(get_current_user)
):
    today = today_ph()

    period = get_current_period(today)

    if period is None:
        raise HTTPException(
            status_code=404,
            detail="No clearance period has started."
        )

    deadline = date.fromisoformat(
        period["deadline"]
    )

    days_remaining = max(
        (deadline - today).days,
        0
    )

    return {
        "period_id": period["period_id"],
        "name": period["name"],
        "start_date": period["start_date"],
        "deadline": period["deadline"],
        "today": today.isoformat(),
        "days_remaining": days_remaining,
        "is_open": today <= deadline,
        "deadline_passed": today > deadline
    }
