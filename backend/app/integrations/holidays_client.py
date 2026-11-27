import logging
import re
import time

from datetime import date
from threading import Lock

import httpx

from app.config import (
    HOLIDAYS_API_URL,
    HOLIDAYS_CACHE_SECONDS
)


logger = logging.getLogger(__name__)

COUNTRY_CODE = "PH"

MAX_ATTEMPTS = 3
RETRYABLE_STATUS = {502, 503, 504}

# year -> (expiration time, immutable holiday dates)
holiday_cache = {}
cache_lock = Lock()


class HolidaysAPIError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 502
    ):
        super().__init__(message)
        self.status_code = status_code


def parse_holidays(payload, year: int):
    if not isinstance(payload, list) or not payload:
        raise HolidaysAPIError(
            "Invalid or empty holidays response."
        )

    holidays = set()

    for item in payload:
        if not isinstance(item, dict):
            raise HolidaysAPIError(
                "Invalid holiday record."
            )

        raw_date = item.get("date")
        country = item.get("countryCode")
        global_holiday = item.get("global")
        types = item.get("types")

        if (
            not isinstance(raw_date, str)
            or not re.fullmatch(
                r"[0-9]{4}-[0-9]{2}-[0-9]{2}",
                raw_date
            )
            or country != COUNTRY_CODE
            or type(global_holiday) is not bool
            or not isinstance(types, list)
            or not types
            or not all(
                isinstance(t, str) for t in types
            )
        ):
            raise HolidaysAPIError(
                "Invalid holiday record fields."
            )

        try:
            holiday_date = date.fromisoformat(raw_date)

        except ValueError:
            raise HolidaysAPIError(
                "Invalid holiday date."
            ) from None

        if holiday_date.year != year:
            raise HolidaysAPIError(
                "Holiday response has an incorrect year."
            )

        # Count nationwide public holidays only.
        if global_holiday and "Public" in types:
            holidays.add(holiday_date)

    if not holidays:
        raise HolidaysAPIError(
            "No nationwide public holidays were returned."
        )

    return frozenset(holidays)


def fetch_holidays(client, year: int):
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = client.get(
                f"PublicHolidays/{year}/{COUNTRY_CODE}"
            )

            response.raise_for_status()

        except httpx.TimeoutException:
            if attempt == MAX_ATTEMPTS:
                raise HolidaysAPIError(
                    "Holidays API timed out.",
                    504
                ) from None

        except httpx.HTTPStatusError as error:
            code = error.response.status_code

            logger.warning(
                "Holidays API returned HTTP %s",
                code
            )

            if (
                code not in RETRYABLE_STATUS
                or attempt == MAX_ATTEMPTS
            ):
                raise HolidaysAPIError(
                    "Holidays API returned an error."
                ) from None

        except httpx.RequestError:
            raise HolidaysAPIError(
                "Holidays API is unavailable.",
                503
            ) from None

        else:
            try:
                payload = response.json()

            except ValueError:
                raise HolidaysAPIError(
                    "Holidays API returned invalid JSON."
                ) from None

            return parse_holidays(payload, year)

        time.sleep(0.25 * attempt)

    raise HolidaysAPIError(
        "Holidays request failed."
    )


def get_public_holidays(year: int):
    if type(year) is not int or not 2000 <= year <= 2100:
        raise ValueError("Unsupported holiday year.")

    with cache_lock:
        cached = holiday_cache.get(year)

        if cached and time.monotonic() < cached[0]:
            return cached[1]

    with httpx.Client(
        base_url=HOLIDAYS_API_URL.rstrip("/") + "/",
        timeout=httpx.Timeout(5.0, connect=2.0),
        follow_redirects=False,
        headers={"Accept": "application/json"}
    ) as client:
        holidays = fetch_holidays(client, year)

    with cache_lock:
        if len(holiday_cache) >= 16:
            holiday_cache.clear()

        holiday_cache[year] = (
            time.monotonic() + HOLIDAYS_CACHE_SECONDS,
            holidays
        )

    return holidays
