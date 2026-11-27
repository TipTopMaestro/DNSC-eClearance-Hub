import pytest

from app.database import get_db

from app.security.manifests import (
    build_manifest,
    verify_manifest,
    read_manifest
)

from app.services.import_service import (
    import_signed_file
)

import app.security.manifests as manifests
import app.services.import_service as service


DATA = (
    b"student_no,balance\n"
    b"2023-0104,1500.00\n"
)


def make_manifest(data=DATA):
    return build_manifest(
        data,
        "ACCOUNTING",
        1,
        "accounting.csv"
    )


def test_valid_signature():
    manifest = make_manifest()

    verify_manifest(
        DATA,
        manifest,
        "accounting.csv"
    )


def test_tampered_file():
    manifest = make_manifest()

    tampered = DATA.replace(
        b"1500.00",
        b"0.00"
    )

    with pytest.raises(ValueError, match="hash mismatch"):
        verify_manifest(
            tampered,
            manifest,
            "accounting.csv"
        )


def test_tampered_manifest():
    manifest = make_manifest()

    manifest["period_id"] = 2

    with pytest.raises(ValueError, match="manifest signature"):
        verify_manifest(
            DATA,
            manifest,
            "accounting.csv"
        )


def test_invalid_signature():
    manifest = make_manifest()

    manifest["manifest_hmac"] = "0" * 64

    with pytest.raises(ValueError, match="manifest signature"):
        verify_manifest(
            DATA,
            manifest,
            "accounting.csv"
        )


def test_duplicate_manifest_fields():
    data = b'{"period_id": 1, "period_id": 2}'

    with pytest.raises(ValueError):
        read_manifest(data)


def test_successful_secure_import(client):
    manifest = make_manifest()

    result = import_signed_file(
        DATA,
        manifest,
        "accounting.csv"
    )

    assert result["accepted"] == 1
    assert result["rejected"] == 0

    with get_db() as conn:
        record = conn.execute("""
            SELECT status, reason
            FROM clearance_records
            WHERE student_id = ?
                AND period_id = ?
                AND office = ?
        """, (
            "2023-0104",
            1,
            "ACCOUNTING"
        )).fetchone()

    assert record["status"] == "HOLD"


def test_replay_attack(client):
    manifest = make_manifest()

    import_signed_file(
        DATA,
        manifest,
        "accounting.csv"
    )

    with pytest.raises(ValueError, match="Replay detected"):
        import_signed_file(
            DATA,
            manifest,
            "accounting.csv"
        )

    with get_db() as conn:
        row = conn.execute("""
            SELECT COUNT(*) AS total
            FROM import_batches
            WHERE batch_id = ?
        """, (manifest["batch_id"],)).fetchone()

    assert row["total"] == 1


def test_outdated_batch(client, monkeypatch):
    monkeypatch.setattr(
        manifests,
        "utc_now",
        lambda: "2026-11-25T08:00:00+00:00"
    )

    old_manifest = make_manifest()

    monkeypatch.setattr(
        manifests,
        "utc_now",
        lambda: "2026-11-26T08:00:00+00:00"
    )

    new_manifest = make_manifest()

    import_signed_file(
        DATA,
        new_manifest,
        "accounting.csv"
    )

    with pytest.raises(ValueError, match="Outdated"):
        import_signed_file(
            DATA,
            old_manifest,
            "accounting.csv"
        )


def test_rejection_log(client):
    data = DATA + b"104,-100.00\n"

    manifest = make_manifest(data)

    result = import_signed_file(
        data,
        manifest,
        "accounting.csv"
    )

    assert result["accepted"] == 1
    assert result["rejected"] == 1

    with get_db() as conn:
        rejection = conn.execute("""
            SELECT record_number, reason
            FROM import_rejections
            WHERE batch_id = ?
        """, (manifest["batch_id"],)).fetchone()

    assert rejection["record_number"] == 2


def test_tampered_file_not_saved(client):
    manifest = make_manifest()

    tampered = DATA.replace(
        b"1500.00",
        b"0.00"
    )

    with pytest.raises(ValueError):
        import_signed_file(
            tampered,
            manifest,
            "accounting.csv"
        )

    with get_db() as conn:
        batch = conn.execute("""
            SELECT batch_id
            FROM import_batches
            WHERE batch_id = ?
        """, (manifest["batch_id"],)).fetchone()

    assert batch is None


def test_import_rollback(client, monkeypatch):
    manifest = make_manifest()

    with get_db() as conn:
        before = conn.execute(
            "SELECT * FROM clearance_records"
        ).fetchall()

    original_save = service.save_clearance

    def failed_save(conn, record):
        original_save(conn, record)

        raise RuntimeError("Simulated database failure.")

    monkeypatch.setattr(
        service,
        "save_clearance",
        failed_save
    )

    with pytest.raises(RuntimeError):
        import_signed_file(
            DATA,
            manifest,
            "accounting.csv"
        )

    with get_db() as conn:
        after = conn.execute(
            "SELECT * FROM clearance_records"
        ).fetchall()

        batch = conn.execute("""
            SELECT batch_id
            FROM import_batches
            WHERE batch_id = ?
        """, (manifest["batch_id"],)).fetchone()

    assert before == after
    assert batch is None
