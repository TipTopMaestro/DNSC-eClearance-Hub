
from app.services.clearance_service import (
    calculate_overall_status,
    REQUIRED_OFFICES
)


def cleared_records():
    return [
        {
            "office": office,
            "status": "CLEARED",
            "reason": None
        }
        for office in REQUIRED_OFFICES
    ]


def test_all_offices_cleared():
    result = calculate_overall_status(
        cleared_records()
    )

    assert result["overall_status"] == "CLEARED"


def test_one_office_on_hold():
    records = cleared_records()

    records[1]["status"] = "HOLD"
    records[1]["reason"] = "Unreturned book."

    result = calculate_overall_status(records)

    assert result["overall_status"] == "HOLD"


def test_missing_office():
    records = cleared_records()[:-1]

    result = calculate_overall_status(records)

    assert result["overall_status"] == "HOLD"


def test_empty_clearance_records():
    result = calculate_overall_status([])

    assert result["overall_status"] == "HOLD"
    assert len(result["offices"]) == 4


def test_missing_office_has_reason():
    result = calculate_overall_status([])

    for office in result["offices"]:
        assert office["reason"]
