from typing import Literal

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response
)

from app.security.permissions import require_roles

from app.services.report_service import (
    build_clearance_report,
    export_csv,
    export_json,
    export_xml
)


router = APIRouter(
    prefix="/api/v1/reports",
    tags=["Reports"]
)


@router.get("/clearance")
def download_clearance_report(
    period_id: int = Query(gt=0),
    format: Literal["csv", "json", "xml"] = "csv",
    user: dict = Depends(
        require_roles("ADMIN", "STAFF")
    )
):
    # Only administrators and Registrar staff
    # are authorized to download reports.
    if (
        user["role"] == "STAFF"
        and user["office"] != "REGISTRAR"
    ):
        raise HTTPException(
            status_code=403,
            detail="Report access denied."
        )

    try:
        report = build_clearance_report(period_id)

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    exporters = {
        "csv": (export_csv, "text/csv"),
        "json": (export_json, "application/json"),
        "xml": (export_xml, "application/xml")
    }

    exporter, media_type = exporters[format]

    content = exporter(report)

    filename = (
        f"clearance-period-{period_id}.{format}"
    )

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            ),
            "Cache-Control": "no-store"
        }
    )