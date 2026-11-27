
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
