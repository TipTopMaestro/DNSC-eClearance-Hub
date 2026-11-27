import pytest

from app.schemas import ClearanceRecordInput
from app.mappers.library_mapper import map_library_record
from app.mappers.accounting_mapper import map_accounting_record


@pytest.mark.parametrize(
    "books,fines,expected",
    [
        ("0", "0.00", "CLEARED"),
        ("2", "0.00", "HOLD"),
        ("0", "50.00", "HOLD"),
        ("2", "50.00", "HOLD")
    ]
)
def test_library_mapping(books, fines, expected):
    record = map_library_record({
        "id": "2023-0104",
        "unreturned_books": books,
        "unpaid_fines": fines
    })

    assert record["status"] == expected
    assert record["office"] == "LIBRARY"
    assert bool(record["reason"]) == (expected == "HOLD")


@pytest.mark.parametrize(
    "balance,expected",
    [
        ("0.00", "CLEARED"),
        ("1500.00", "HOLD")
    ]
)
def test_accounting_mapping(balance, expected):
    record = map_accounting_record({
        "student_no": "2023-0104",
        "balance": balance
    })

    assert record["status"] == expected
    assert record["office"] == "ACCOUNTING"
    assert bool(record["reason"]) == (expected == "HOLD")


@pytest.mark.parametrize(
    "balance",
    ["-100.00", "abc", "10.999"]
)
def test_invalid_balance(balance):
    with pytest.raises(ValueError):
        map_accounting_record({
            "student_no": "2023-0104",
            "balance": balance
        })


def test_invalid_book_count():
    with pytest.raises(ValueError):
        map_library_record({
            "id": "2023-0104",
            "unreturned_books": "-2",
            "unpaid_fines": "0.00"
        })


def test_invalid_student_id():
    with pytest.raises(ValueError):
        map_accounting_record({
            "student_no": "104",
            "balance": "0.00"
        })


def test_missing_accounting_field():
    with pytest.raises(ValueError):
        map_accounting_record({
            "student_no": "2023-0104"
        })


def test_missing_library_field():
    with pytest.raises(ValueError):
        map_library_record({
            "id": "2023-0104",
            "unreturned_books": "2"
        })


def test_library_combined_reasons():
    record = map_library_record({
        "id": "2023-0104",
        "unreturned_books": "2",
        "unpaid_fines": "50.00"
    })

    assert record["reason"] == (
        "Unreturned books: 2; Unpaid fines: PHP 50.00"
    )


def test_common_clearance_schema():
    mapped = map_accounting_record({
        "student_no": "2023-0104",
        "balance": "1500.00"
    })

    record = ClearanceRecordInput(
        **mapped,
        period_id=1
    )

    assert record.period_id == 1
    assert record.status == "HOLD"
    assert record.office == "ACCOUNTING"
