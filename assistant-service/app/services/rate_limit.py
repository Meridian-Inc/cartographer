import os
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

from fastapi import HTTPException, Request
from redis.asyncio import Redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_DB = int(os.getenv("REDIS_DB", "1"))

_redis: Redis | None = None

async def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = Redis.from_url(
            REDIS_URL,
            db=REDIS_DB,
            decode_responses=True,
        )
    return _redis

def _seconds_until_utc_midnight() -> int:
    now = datetime.now(timezone.utc)
    tomorrow = (now + timedelta(days=1)).date()
    midnight = datetime(tomorrow.year, tomorrow.month, tomorrow.day, tzinfo=timezone.utc)
    return max(1, int((midnight - now).total_seconds()))

# Atomic: increment and set expiry only if first time
LUA_INCR_EXPIRE = """
local v = redis.call('INCR', KEYS[1])
if v == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return v
"""

def rate_limit_per_day(
    limit: int,
    key_fn: Optional[Callable[[Request], str]] = None,
):
    """
    Returns a FastAPI dependency that enforces a fixed-window daily limit.
    """
    async def _dep(request: Request):
        redis = await get_redis()

        if key_fn:
            key = key_fn(request)
        else:
            # expects auth to have put user somewhere; see router usage below
            user = getattr(request.state, "user", None)
            user_id = getattr(user, "id", None) or getattr(user, "user_id", None)
            if not user_id:
                # If you can't reliably access user here, pass your own key_fn
                raise HTTPException(status_code=500, detail="Rate limit missing user identity")

            # include date so keys naturally partition by day
            day = datetime.now(timezone.utc).date().isoformat()
            key = f"rl:assistant:{user_id}:{request.method}:{request.url.path}:{day}"

        ttl = _seconds_until_utc_midnight()
        count = await redis.eval(LUA_INCR_EXPIRE, 1, key, ttl)

        if int(count) > limit:
            # Optional: include a Retry-After hint
            raise HTTPException(
                status_code=429,
                detail=f"Daily limit exceeded for this endpoint ({limit}/day). Try again later.",
                headers={"Retry-After": str(ttl)},
            )

    return _dep
