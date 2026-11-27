from datetime import date, timedelta

from app.config import (
    CLEARANCE_WORKING_DAYS,
    EXTRA_NON_WORKING_DATES
)

from app.integrations.holidays_client import (
    get_public_holidays
)


def calculate_deadline(
    start_date: date,
    working_days: int = CLEARANCE_WORKING_DAYS
) -> date:

    if type(start_date) is not date:
        raise ValueError("Invalid starting date.")

    if not 2000 <= start_date.year <= 2098:
        raise ValueError("Unsupported starting year.")

    if (
        type(working_days) is not int
        or not 1 <= working_days <= 365
    ):
        raise ValueError(
            "Working days must be between 1 and 365."
        )

    current = start_date
    counted_days = 0

    # Holiday dates already retrieved during
    # this particular calculation.
    holidays_by_year = {}

    # Safety limit to prevent an unbounded loop.
    for _ in range(1096):

        # Move to the next calendar day.
        current += timedelta(days=1)

        # Skip Saturday and Sunday.
        if current.weekday() >= 5:
            continue

        # Retrieve holidays when entering a new year.
        if current.year not in holidays_by_year:
            holidays_by_year[current.year] = (
                get_public_holidays(current.year)
            )

        holidays = holidays_by_year[current.year]

        # Skip nationwide public holidays.
        if current in holidays:
            continue

        # Skip additional confirmed closures.
        if current in EXTRA_NON_WORKING_DATES:
            continue

        # Count only eligible working days.
        counted_days += 1

        if counted_days == working_days:
            return current

    raise ValueError(
        "Unable to calculate deadline within the limit."
    )
