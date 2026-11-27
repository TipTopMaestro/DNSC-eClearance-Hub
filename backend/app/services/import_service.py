
from app.database import get_db

from app.security.manifests import verify_manifest

from app.importers.pipeline import (
    prepare_import,
    MAX_FILE_BYTES
)

from app.repositories.clearance import save_clearance
from app.utils.dates import utc_now


def import_signed_file(
    data: bytes,
    manifest: dict,
    filename: str
):
    if len(data) > MAX_FILE_BYTES:
        raise ValueError("Import file is too large.")

    # 1. Verify authenticity and integrity.
    verify_manifest(data, manifest, filename)

    batch_id = manifest["batch_id"]
    office = manifest["office"]
    period_id = manifest["period_id"]
    created_at = manifest["created_at"]

    with get_db() as conn:
        conn.execute("BEGIN IMMEDIATE")

        # 2. Reject an already imported batch.
        existing = conn.execute("""
            SELECT batch_id
            FROM import_batches
            WHERE batch_id = ?
        """, (batch_id,)).fetchone()

        if existing:
            raise ValueError("Replay detected: batch already imported.")

        # 3. Reject outdated batches.
        newer = conn.execute("""
            SELECT batch_id
            FROM import_batches
            WHERE office = ?
                AND period_id = ?
                AND source_created_at >= ?
            LIMIT 1
        """, (
            office,
            period_id,
            created_at
        )).fetchone()

        if newer:
            raise ValueError("Outdated import batch.")

        # 4. Reuse our existing import pipeline.
        accepted, rejected = prepare_import(
            data,
            office,
            period_id
        )

        # 5. Record the import batch.
        conn.execute("""
            INSERT INTO import_batches (
                batch_id,
                office,
                period_id,
                filename,
                file_hash,
                source_created_at,
                processed_at,
                accepted_count,
                rejected_count
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            batch_id,
            office,
            period_id,
            filename,
            manifest["sha256"],
            created_at,
            utc_now(),
            len(accepted),
            len(rejected)
        ))

        # 6. Save accepted clearance records.
        for record in accepted:
            save_clearance(conn, record)

        # 7. Save rejected-record logs.
        for record in rejected:
            conn.execute("""
                INSERT INTO import_rejections (
                    batch_id,
                    record_number,
                    reason,
                    rejected_at
                )
                VALUES (?, ?, ?, ?)
            """, (
                batch_id,
                record["record_number"],
                record["reason"],
                utc_now()
            ))

    return {
        "batch_id": batch_id,
        "office": office,
        "period_id": period_id,
        "accepted": len(accepted),
        "rejected": len(rejected)
    }
