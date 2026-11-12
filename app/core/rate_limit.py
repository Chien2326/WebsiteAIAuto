"""In-memory sliding-window rate limiting.

Limits are kept per process. With several workers or servers, each keeps its
own counters; move this to Redis when the app is scaled out.
"""

import math
import threading
import time
from collections import deque

from fastapi import HTTPException, Request, status


class RateLimiter:
    def __init__(self, limit: int, window_seconds: float) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()
        self._calls_since_sweep = 0

    def _prune(self, key: str, now: float) -> deque[float] | None:
        hits = self._hits.get(key)
        if hits is None:
            return None
        cutoff = now - self.window_seconds
        while hits and hits[0] <= cutoff:
            hits.popleft()
        if not hits:
            del self._hits[key]
            return None
        return hits

    def _sweep(self, now: float) -> None:
        self._calls_since_sweep += 1
        if self._calls_since_sweep < 1000:
            return
        self._calls_since_sweep = 0
        for key in list(self._hits):
            self._prune(key, now)

    def retry_after(self, key: str) -> float | None:
        """Seconds until another hit is allowed, or None if allowed now."""
        now = time.monotonic()
        with self._lock:
            hits = self._prune(key, now)
            if hits is None or len(hits) < self.limit:
                return None
            return max(hits[0] + self.window_seconds - now, 0.0)

    def record(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            self._sweep(now)
            self._prune(key, now)
            self._hits.setdefault(key, deque()).append(now)

    def hit(self, key: str) -> float | None:
        """Record a hit if allowed; otherwise return the seconds to wait."""
        now = time.monotonic()
        with self._lock:
            self._sweep(now)
            hits = self._prune(key, now)
            if hits is not None and len(hits) >= self.limit:
                return max(hits[0] + self.window_seconds - now, 0.0)
            self._hits.setdefault(key, deque()).append(now)
            return None

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


def client_ip(request: Request) -> str:
    # Behind a reverse proxy, run uvicorn with --proxy-headers and
    # --forwarded-allow-ips so request.client is the real visitor address.
    return request.client.host if request.client else "unknown"


def too_many_requests(retry_after: float, detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=detail,
        headers={"Retry-After": str(max(1, math.ceil(retry_after)))},
    )


def enforce(limiter: RateLimiter, key: str, detail: str) -> None:
    retry_after = limiter.hit(key)
    if retry_after is not None:
        raise too_many_requests(retry_after, detail)


login_ip_limiter = RateLimiter(limit=20, window_seconds=5 * 60)
login_failure_limiter = RateLimiter(limit=5, window_seconds=15 * 60)
register_limiter = RateLimiter(limit=5, window_seconds=60 * 60)
contact_limiter = RateLimiter(limit=5, window_seconds=10 * 60)
generation_limiter = RateLimiter(limit=20, window_seconds=10 * 60)

ALL_LIMITERS = (
    login_ip_limiter,
    login_failure_limiter,
    register_limiter,
    contact_limiter,
    generation_limiter,
)
