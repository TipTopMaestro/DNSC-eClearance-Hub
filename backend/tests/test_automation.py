import json

from datetime import date

from app.security.manifests import build_manifest

from automation.process_drop import process_drop

import automation.daily_summary as summary


DATA = (
    b"student_no,balance\n"
    b"2023-0104,1500.00\n"
)


def create_batch(tmp_path, tampered=False):
    folder = tmp_path / "drop" / "test-batch"
    folder.mkdir(parents=True)

    manifest = build_manifest(
        DATA,
        "ACCOUNTING",
        1,
        "accounting.csv"
    )

    data = DATA

    if tampered:
        data = DATA.replace(b"1500.00", b"0.00")

    (folder / "accounting.csv").write_bytes(data)

    (folder / "manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8"
    )

    return folder


def test_valid_batch_archived(client, tmp_path):
    folder = create_batch(tmp_path)

    result = process_drop(tmp_path)

    assert result["processed"] == 1
    assert result["rejected"] == 0

    assert not folder.exists()
    assert len(list(
        (tmp_path / "archive").iterdir()
    )) == 1


def test_tampered_batch_rejected(client, tmp_path):
    folder = create_batch(tmp_path, tampered=True)

    result = process_drop(tmp_path)

    assert result["processed"] == 0
    assert result["rejected"] == 1

    assert not folder.exists()
    assert len(list(
        (tmp_path / "rejected").iterdir()
    )) == 1


def test_empty_drop_folder(tmp_path):
    result = process_drop(tmp_path)

    assert result == {
        "processed": 0,
        "rejected": 0,
        "deferred": 0
    }


def test_missing_manifest(tmp_path):
    folder = tmp_path / "drop" / "test-batch"
    folder.mkdir(parents=True)

    (folder / "accounting.csv").write_bytes(DATA)

    result = process_drop(tmp_path)

    assert result["rejected"] == 1
    assert not folder.exists()


def test_daily_summary(client, tmp_path, monkeypatch):
    monkeypatch.setattr(
        summary,
        "today_ph",
        lambda: date(2026, 11, 28)
    )

    result = summary.generate_daily_summary(tmp_path)

    assert result["period_id"] == 1
    assert len(result["offices"]) == 4

    output = (
        tmp_path / "reports"
        / "hold-summary-2026-11-28.json"
    )

    assert output.exists()


def test_missing_clearance_is_hold(
    client,
    tmp_path,
    monkeypatch
):
    monkeypatch.setattr(
        summary,
        "today_ph",
        lambda: date(2026, 11, 28)
    )

    result = summary.generate_daily_summary(tmp_path)

    for office in result["offices"]:
        assert office["hold_count"] == 1
        assert "****-0104" in office["students_on_hold"]