import logging
import time

import httpx

from app.config import (
    REGISTRAR_API_URL,
    REGISTRAR_PAGE_SIZE
)


logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3
MAX_PAGES = 1000
MAX_RECORDS = 20_000

RETRYABLE_STATUS = {502, 503, 504}


class RegistrarAPIError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 502
    ):
        super().__init__(message)
        self.status_code = status_code


def request_page(client, page, page_size):
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = client.get(
                "/students",
                params={
                    "page": page,
                    "page_size": page_size
                }
            )

            response.raise_for_status()

        except httpx.TimeoutException:
            logger.warning(
                "Registrar timeout: attempt %s",
                attempt
            )

            if attempt == MAX_ATTEMPTS:
                raise RegistrarAPIError(
                    "Registrar API timed out.",
                    504
                ) from None

        except httpx.HTTPStatusError as error:
            code = error.response.status_code

            logger.warning(
                "Registrar returned HTTP %s",
                code
            )

            if (
                code not in RETRYABLE_STATUS
                or attempt == MAX_ATTEMPTS
            ):
                raise RegistrarAPIError(
                    "Registrar API returned an error."
                ) from None

        except httpx.RequestError:
            raise RegistrarAPIError(
                "Registrar API is unavailable.",
                503
            ) from None

        else:
            try:
                return response.json()

            except ValueError:
                raise RegistrarAPIError(
                    "Registrar returned invalid JSON."
                ) from None

        # Small delay before a retry.
        time.sleep(0.25 * attempt)

    raise RegistrarAPIError(
        "Registrar request failed."
    )


def fetch_students(client, page_size=100):
    if not 1 <= page_size <= 100:
        raise ValueError("Invalid page size.")

    students = []
    expected_total = None

    for page in range(1, MAX_PAGES + 1):
        payload = request_page(
            client, page, page_size
        )

        if not isinstance(payload, dict):
            raise RegistrarAPIError(
                "Invalid Registrar response structure."
            )

        items = payload.get("items")
        total = payload.get("total")

        if (
            not isinstance(items, list)
            or type(total) is not int
            or not 0 <= total <= MAX_RECORDS
            or type(payload.get("page")) is not int
            or payload["page"] != page
            or type(payload.get("page_size")) is not int
            or payload["page_size"] != page_size
        ):
            raise RegistrarAPIError(
                "Invalid Registrar pagination data."
            )

        if expected_total is None:
            expected_total = total

        elif total != expected_total:
            raise RegistrarAPIError(
                "Registrar data changed during sync."
            )

        remaining = total - len(students)
        expected_count = min(page_size, remaining)

        if len(items) != expected_count:
            raise RegistrarAPIError(
                "Incomplete Registrar response."
            )

        students.extend(items)

        if len(students) == expected_total:
            return students

    raise RegistrarAPIError(
        "Registrar pagination limit exceeded."
    )


def fetch_registrar_students():
    with httpx.Client(
        base_url=REGISTRAR_API_URL,
        timeout=httpx.Timeout(
            5.0,
            connect=2.0
        ),
        follow_redirects=False,
        headers={
            "Accept": "application/json"
        }
    ) as client:
        return fetch_students(
            client,
            REGISTRAR_PAGE_SIZE
        )
