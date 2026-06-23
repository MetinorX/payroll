import time
from collections import defaultdict
from fastapi import HTTPException, Request, status
from app.config import settings

_attempts: dict[str, list[float]] = defaultdict(list)


async def cleanup_old_entries():
    now = time.time()
    for ip in list(_attempts.keys()):
        _attempts[ip] = [t for t in _attempts[ip] if now - t < 300]
        if not _attempts[ip]:
            del _attempts[ip]


def rate_limit(max_attempts: int = 5, window_seconds: int = 60):
    async def _rate_limit(request: Request):
        if not settings.rate_limit_enabled:
            return

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        _attempts[client_ip] = [t for t in _attempts[client_ip] if now - t < window_seconds]

        if len(_attempts[client_ip]) >= max_attempts:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {window_seconds} seconds.",
            )
        _attempts[client_ip].append(now)

    return _rate_limit
