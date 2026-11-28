from datetime import date
import logging

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query
)

from app.database import get_db

from app.security.permissions import (
    require_roles
)

from app.services.registrar_service import (
    synchronize_registrar,
    RegistrarSyncBusy
)

from app.integrations.registrar_client import (
    RegistrarAPIError
)

from app.schemas import ClearancePeriodCreate

from app.services.deadline_service import (
    calculate_deadline
)

from app.repositories.periods import (
    create_period,
    PeriodConflictError
)

from app.integrations.holidays_client import (
    HolidaysAPIError
)


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["Administration"]
)


@router.post("/sync/registrar")
def sync_registrar(
    user: dict = Depends(
        require_roles("ADMIN")
    )
):
    try:
        return synchronize_registrar(
            actor_user_id=user["user_id"]
        )

    except RegistrarAPIError as error:
        logger.warning(
            "Registrar sync failed: %s",
            str(error)
        )

        raise HTTPException(
            status_code=error.status_code,
            detail=str(error)
        )

    except RegistrarSyncBusy as error:
        raise HTTPException(
            status_code=409,
            detail=str(error)
        )


@router.get("/sync/registrar/{sync_id}/rejections")
def get_registrar_rejections(
    sync_id: int = Path(gt=0),
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),

    user: dict = Depends(
        require_roles("ADMIN")
    )
):
    with get_db() as conn:
        run = conn.execute("""
            SELECT sync_id
            FROM registrar_sync_runs
            WHERE sync_id = ?
        """, (sync_id,)).fetchone()

        if run is None:
            raise HTTPException(
                status_code=404,
                detail="Synchronization run not found."
            )

        rows = conn.execute("""
            SELECT
                record_number,
                reason,
                rejected_at
            FROM registrar_sync_rejections
            WHERE sync_id = ?
            ORDER BY record_number
            LIMIT ? OFFSET ?
        """, (
            sync_id,
            limit,
            offset
        )).fetchall()

        return {
            "sync_id": sync_id,
            "limit": limit,
            "offset": offset,
            "items": [
                dict(row) for row in rows
            ]
        }

#Periods Router

@router.post("/periods", status_code=201)
def create_clearance_period(
    body: ClearancePeriodCreate,

    user: dict = Depends(
        require_roles("ADMIN")
    )
):
    start_date = date.fromisoformat(
        body.start_date
    )

    try:
        deadline = calculate_deadline(
            start_date,
            body.working_days
        )

        period_id = create_period(
            name=body.name,
            start_date=start_date,
            deadline=deadline
        )

    except HolidaysAPIError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail=str(error)
        )

    except PeriodConflictError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error)
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    return {
        "period_id": period_id,
        "name": body.name,
        "start_date": start_date.isoformat(),
        "working_days": body.working_days,
        "deadline": deadline.isoformat()
    }

#BATCH FILES IMPORTS
@router.get("/imports")
def get_imports(
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: dict = Depends(require_roles("ADMIN"))
):
    with get_db() as conn:
        rows = conn.execute("""
            SELECT batch_id, office, period_id,
                   filename, source_created_at,
                   processed_at, accepted_count,
                   rejected_count
            FROM import_batches
            ORDER BY processed_at DESC, batch_id DESC
            LIMIT ? OFFSET ?
        """, (limit, offset)).fetchall()

        return [dict(row) for row in rows]
    
#Rejected Logs
@router.get("/rejections")
def get_rejections(
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: dict = Depends(require_roles("ADMIN"))
):
    with get_db() as conn:
        rows = conn.execute("""
            SELECT r.rejection_id,
                   r.batch_id,
                   b.office,
                   r.record_number,
                   r.student_id_masked,
                   r.reason,
                   r.rejected_at
            FROM import_rejections AS r
            JOIN import_batches AS b
                ON r.batch_id = b.batch_id
            ORDER BY r.rejection_id DESC
            LIMIT ? OFFSET ?
        """, (limit, offset)).fetchall()

        return [dict(row) for row in rows]

#Audit
@router.get("/audit")
def get_audit_logs(
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: dict = Depends(require_roles("ADMIN"))
):
    with get_db() as conn:
        rows = conn.execute("""
            SELECT a.audit_id,
                   a.actor_user_id,
                   u.username,
                   a.student_id,
                   a.period_id,
                   a.office,
                   a.action,
                   a.old_status,
                   a.new_status,
                   a.reason,
                   a.created_at
            FROM audit_logs AS a
            JOIN users AS u
                ON a.actor_user_id = u.user_id
            ORDER BY a.audit_id DESC
            LIMIT ? OFFSET ?
        """, (limit, offset)).fetchall()

        return [dict(row) for row in rows]