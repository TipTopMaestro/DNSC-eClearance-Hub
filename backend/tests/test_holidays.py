
from datetime import date

import httpx
import pytest

from app.integrations.holidays_client import (
    fetch_holidays,
    parse_holidays,
    HolidaysAPIError
)

import app.integrations.holidays_client as holidays_client


def sample_holiday():
    return {
        "date": "2026-12-25",
        "countryCode": "PH",
        "global": True,
        "types": ["Public"],
        "name": "Christmas Day"
    }


def test_valid_holiday_response():
    result = parse_holidays(
        [sample_holiday()],
        2026
    )

    assert date(2026, 12, 25) in result


def test_duplicate_holiday_dates():
    result = parse_holidays(
        [sample_holiday(), sample_holiday()],
        2026
    )

    assert len(result) == 1


def test_non_public_holiday_excluded():
    observance = sample_holiday()
    observance["date"] = "2026-12-24"
    observance["types"] = ["Observance"]

    result = parse_holidays(
        [sample_holiday(), observance],
        2026
    )

    assert date(2026, 12, 24) not in result


def test_regional_holiday_excluded():
    regional = sample_holiday()
    regional["date"] = "2026-12-28"
    regional["global"] = False

    result = parse_holidays(
        [sample_holiday(), regional],
        2026
    )

    assert date(2026, 12, 28) not in result


@pytest.mark.parametrize(
    "field,value",
    [
        ("date", "2026-02-30"),
        ("date", "2027-12-25"),
        ("countryCode", "US"),
        ("global", "true"),
        ("types", "Public")
    ]
)
def test_invalid_holiday_fields(field, value):
    holiday = sample_holiday()
    holiday[field] = value

    with pytest.raises(HolidaysAPIError):
        parse_holidays([holiday], 2026)


def test_empty_holiday_response():
    with pytest.raises(HolidaysAPIError):
        parse_holidays([], 2026)


def test_holiday_api_success():
    def handler(request):
        assert request.url.path == (
            "/api/v3/PublicHolidays/2026/PH"
        )

        return httpx.Response(
            200,
            json=[sample_holiday()]
        )

    with httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url="https://holidays.test/api/v3/"
    ) as client:

        result = fetch_holidays(client, 2026)

    assert date(2026, 12, 25) in result


@pytest.mark.parametrize(
    "status_code",
    [400, 404, 500, 503]
)
def test_holiday_http_error(
    status_code,
    monkeypatch
):
    monkeypatch.setattr(
        holidays_client.time,
        "sleep",
        lambda seconds: None
    )

    def handler(request):
        return httpx.Response(status_code)

    with httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url="https://holidays.test/"
    ) as client:

        with pytest.raises(HolidaysAPIError) as error:
            fetch_holidays(client, 2026)

    assert error.value.status_code == 502


def test_holiday_api_timeout(monkeypatch):
    monkeypatch.setattr(
        holidays_client.time,
        "sleep",
        lambda seconds: None
    )

    attempts = []

    def handler(request):
        attempts.append(1)

        raise httpx.ReadTimeout(
            "Simulated timeout",
            request=request
        )

    with httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url="https://holidays.test/"
    ) as client:

        with pytest.raises(HolidaysAPIError) as error:
            fetch_holidays(client, 2026)

    assert error.value.status_code == 504
    assert len(attempts) == 3


def test_malformed_holiday_json():
    def handler(request):
        return httpx.Response(
            200,
            content=b"Invalid JSON"
        )

    with httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url="https://holidays.test/"
    ) as client:

        with pytest.raises(HolidaysAPIError):
            fetch_holidays(client, 2026)
