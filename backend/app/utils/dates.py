from datetime import datetime, timezone
from datetime import date, timedelta



def utc_now():
    return datetime.now(
        timezone.utc
    ).isoformat(timespec="seconds")


PH_TIMEZONE = timezone(timedelta(hours=8))

def today_ph() -> date:
    return datetime.now(PH_TIMEZONE).date()
