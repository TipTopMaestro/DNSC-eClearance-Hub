from collections import OrderedDict, deque
from threading import Lock
from time import monotonic

from fastapi import HTTPException


MAX_ATTEMPTS = 5
WINDOW_SECONDS = 60
MAX_TRACKED_CLIENTS = 10_000

attempts = OrderedDict()
lock = Lock()


def check_login_limit(client_ip: str):
    now = monotonic()

    with lock:
        if client_ip not in attempts:
            if len(attempts) >= MAX_TRACKED_CLIENTS:
                raise HTTPException(
                    status_code=429,
                    detail="Login service temporarily busy.",
                    headers={"Retry-After": "60"}
                )

            attempts[client_ip] = deque()

        history = attempts[client_ip]

        while history and (
            now - history[0] >= WINDOW_SECONDS
        ):
            history.popleft()

        if len(history) >= MAX_ATTEMPTS:
            raise HTTPException(
                status_code=429,
                detail="Too many login attempts.",
                headers={"Retry-After": "60"}
            )

        history.append(now)

        # Remove expired client entries.
        for ip in list(attempts):
            if ip == client_ip:
                continue

            records = attempts[ip]

            if not records or (
                now - records[-1] >= WINDOW_SECONDS
            ):
                del attempts[ip]
