from collections import Counter
from threading import Lock

from app.database import get_db

from app.integrations.registrar_client import (
    fetch_registrar_students
)

from app.mappers.registrar_mapper import (
    map_registrar_record
)

from app.repositories.students import (
    upsert_student
)

from app.utils.dates import utc_now


sync_lock = Lock()


class RegistrarSyncBusy(Exception):
    pass


def synchronize_registrar(actor_user_id: int):
    if not sync_lock.acquire(blocking=False):
        raise RegistrarSyncBusy(
            "Registrar synchronization is already running."
        )

    try:
        return perform_sync(actor_user_id)

    finally:
        sync_lock.release()


def perform_sync(actor_user_id: int):
    started_at = utc_now()

    # Fetch everything before touching the database.
    source_records = fetch_registrar_students()

    mapped = []
    rejections = []

    # Validate and transform each source record.
    for number, source in enumerate(
        source_records,
        start=1
    ):
        try:
            student = map_registrar_record(source)

            mapped.append((number, student))

        except ValueError as error:
            rejections.append({
                "record_number": number,
                "reason": str(error)
            })

    # Detect duplicate IDs in mapped records.
    counts = Counter(
        student.student_id
        for _, student in mapped
    )

    accepted = []

    for number, student in mapped:
        if counts[student.student_id] > 1:
            rejections.append({
                "record_number": number,
                "reason": "Duplicate student ID."
            })
        else:
            accepted.append(student)

    # Store accepted records and history together.
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO registrar_sync_runs (
                actor_user_id,
                started_at,
                completed_at,
                received_count,
                accepted_count,
                rejected_count
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            actor_user_id,
            started_at,
            utc_now(),
            len(source_records),
            len(accepted),
            len(rejections)
        ))

        sync_id = cursor.lastrowid

        for student in accepted:
            upsert_student(
                student,
                conn=conn
            )

        for rejected in rejections:
            conn.execute("""
                INSERT INTO registrar_sync_rejections (
                    sync_id,
                    record_number,
                    reason,
                    rejected_at
                )
                VALUES (?, ?, ?, ?)
            """, (
                sync_id,
                rejected["record_number"],
                rejected["reason"],
                utc_now()
            ))

        conn.execute("""
            UPDATE registrar_sync_runs
            SET completed_at = ?
            WHERE sync_id = ?
        """, (
            utc_now(),
            sync_id
        ))

    return {
        "sync_id": sync_id,
        "message": "Registrar synchronization completed.",
        "received": len(source_records),
        "accepted": len(accepted),
        "rejected": len(rejections)
    }
