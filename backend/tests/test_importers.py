import pytest

from app.database import get_db

from app.importers.accounting_csv import read_accounting_csv
from app.importers.library_xml import read_library_xml
from app.importers.pipeline import prepare_import


def test_read_accounting_csv():
    data = b"student_no,balance\n2023-0104,500.00\n"

    records = read_accounting_csv(data)

    assert records == [
        {
            "student_no": "2023-0104",
            "balance": "500.00"
        }
    ]


def test_read_library_xml():
    data = b"""
    <library>
        <student id="2023-0104">
            <unreturned_books>2</unreturned_books>
            <unpaid_fines>50.00</unpaid_fines>
        </student>
    </library>
    """

    records = read_library_xml(data)

    assert records[0]["id"] == "2023-0104"
    assert records[0]["unreturned_books"] == "2"
    assert records[0]["unpaid_fines"] == "50.00"


def test_invalid_csv_headers():
    data = b"student_id,amount\n2023-0104,500.00\n"

    with pytest.raises(ValueError):
        read_accounting_csv(data)


def test_malformed_xml():
    data = b"<library><student>"

    with pytest.raises(ValueError):
        read_library_xml(data)


def test_unsafe_xml():
    data = b"""
    <!DOCTYPE library [
        <!ENTITY test "unsafe">
    ]>
    <library>&test;</library>
    """

    with pytest.raises(ValueError):
        read_library_xml(data)


def test_duplicate_xml_fields():
    data = b"""
    <library>
        <student id="2023-0104">
            <unreturned_books>0</unreturned_books>
            <unreturned_books>2</unreturned_books>
        </student>
    </library>
    """

    with pytest.raises(ValueError):
        read_library_xml(data)


def test_valid_accounting_import(client):
    data = b"student_no,balance\n2023-0104,500.00\n"

    accepted, rejected = prepare_import(
        data, "ACCOUNTING", 1
    )

    assert len(accepted) == 1
    assert len(rejected) == 0
    assert accepted[0].status == "HOLD"
    assert accepted[0].period_id == 1


def test_valid_library_import(client):
    data = b"""
    <library>
        <student id="2023-0104">
            <unreturned_books>0</unreturned_books>
            <unpaid_fines>0.00</unpaid_fines>
        </student>
    </library>
    """

    accepted, rejected = prepare_import(
        data, "LIBRARY", 1
    )

    assert len(accepted) == 1
    assert len(rejected) == 0
    assert accepted[0].status == "CLEARED"


def test_unknown_student(client):
    data = b"student_no,balance\n2023-9999,0.00\n"

    accepted, rejected = prepare_import(
        data, "ACCOUNTING", 1
    )

    assert len(accepted) == 0
    assert len(rejected) == 1
    assert "masterlist" in rejected[0]["reason"]


def test_duplicate_students(client):
    data = (
        b"student_no,balance\n"
        b"2023-0104,500.00\n"
        b"2023-0104,0.00\n"
    )

    accepted, rejected = prepare_import(
        data, "ACCOUNTING", 1
    )

    assert len(accepted) == 0
    assert len(rejected) == 2


def test_mixed_valid_and_invalid_records(client):
    data = (
        b"student_no,balance\n"
        b"2023-0104,500.00\n"
        b"2023-9999,0.00\n"
        b"104,-100.00\n"
    )

    accepted, rejected = prepare_import(
        data, "ACCOUNTING", 1
    )

    assert len(accepted) == 1
    assert len(rejected) == 2


def test_invalid_period(client):
    data = b"student_no,balance\n2023-0104,0.00\n"

    with pytest.raises(ValueError):
        prepare_import(data, "ACCOUNTING", 9999)


def test_preview_does_not_write_database(client):
    data = b"student_no,balance\n2023-0104,500.00\n"

    with get_db() as conn:
        before = conn.execute(
            "SELECT * FROM clearance_records"
        ).fetchall()

    prepare_import(data, "ACCOUNTING", 1)

    with get_db() as conn:
        after = conn.execute(
            "SELECT * FROM clearance_records"
        ).fetchall()

    assert before == after
