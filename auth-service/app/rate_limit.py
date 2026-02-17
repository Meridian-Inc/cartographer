"""
In-memory sliding window rate limiter for auth endpoints.

Provides per-IP rate limiting as a FastAPI dependency.
"""

import logging
import time
from collections import defaultdict

from fastapi import HTTPException, Request

__all__ = ["rate_limit", "get_client_ip"]

logger = logging.getLogger(__name__)

# Stores: { key: [timestamp, timestamp, ...] }
_request_log: dict[str, list[float]] = defaultdict(list)

# Cleanup counter to avoid unbounded memory growth
_cleanup_counter = 0
_CLEANUP_INTERVAL = 100


def _cleanup_expired(window_seconds: int = 120) -> None:
    """Remove entries older than the largest plausible window."""
    now = time.monotonic()
    keys_to_delete = []
    for key, timestamps in _request_log.items():
        _request_log[key] = [t for t in timestamps if now - t < window_seconds]
        if not _request_log[key]:
            keys_to_delete.append(key)
    for key in keys_to_delete:
        del _request_log[key]


def _check_rate_limit(key: str, max_requests: int, window_seconds: int) -> int:
    """
    Check and enforce rate limit for a given key.

    Returns the number of seconds until the client can retry.
    Raises nothing — returns 0 if the request is allowed.
    """
    global _cleanup_counter
    _cleanup_counter += 1
    if _cleanup_counter >= _CLEANUP_INTERVAL:
        _cleanup_counter = 0
        _cleanup_expired()

    now = time.monotonic()
    timestamps = _request_log[key]

    # Remove timestamps outside the window
    _request_log[key] = [t for t in timestamps if now - t < window_seconds]
    timestamps = _request_log[key]

    if len(timestamps) >= max_requests:
        oldest_in_window = min(timestamps)
        retry_after = int(window_seconds - (now - oldest_in_window)) + 1
        return max(retry_after, 1)

    _request_log[key].append(now)
    return 0


def get_client_ip(request: Request) -> str:
    """Extract the client IP from request headers (supports X-Forwarded-For)."""
    forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    if forwarded:
        return forwarded
    return request.client.host if request.client else "unknown"


def rate_limit(max_requests: int, window_seconds: int = 60):
    """
    Create a FastAPI dependency that enforces per-IP rate limiting.

    Args:
        max_requests: Maximum number of requests allowed in the window.
        window_seconds: Time window in seconds (default: 60).
    """

    async def dependency(request: Request) -> None:
        client_ip = get_client_ip(request)
        key = f"{request.url.path}:{client_ip}"
        retry_after = _check_rate_limit(key, max_requests, window_seconds)

        if retry_after > 0:
            logger.warning(
                "Rate limit exceeded: ip=%s endpoint=%s",
                client_ip,
                request.url.path,
            )
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": str(retry_after)},
            )

    return dependency
