import os
from datetime import datetime, timedelta
from typing import Callable, Optional, Set

from fastapi import HTTPException, Request
from redis.asyncio import Redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_DB = int(os.getenv("REDIS_DB", "1"))

# Roles that are exempt from rate limiting (comma-separated list)
# Valid values: member, admin, owner
# Example: "admin,owner" means admins and owners have unlimited requests
_EXEMPT_ROLES_STR = os.getenv("ASSISTANT_RATE_LIMIT_EXEMPT_ROLES", "")
RATE_LIMIT_EXEMPT_ROLES: Set[str] = {
    role.strip().lower() 
    for role in _EXEMPT_ROLES_STR.split(",") 
    if role.strip()
}

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


def _get_local_date() -> str:
    """Get today's date in the server's local timezone as ISO format string."""
    return datetime.now().date().isoformat()


def _seconds_until_local_midnight() -> int:
    """Calculate seconds until midnight in the server's local timezone."""
    now = datetime.now()
    tomorrow = (now + timedelta(days=1)).date()
    # Midnight tomorrow in local time
    midnight = datetime(tomorrow.year, tomorrow.month, tomorrow.day)
    return max(1, int((midnight - now).total_seconds()))

# Atomic: increment and set expiry only if first time
LUA_INCR_EXPIRE = """
local v = redis.call('INCR', KEYS[1])
if v == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return v
"""


def is_role_exempt(user_role: str) -> bool:
    """Check if a user role is exempt from rate limiting."""
    return user_role.lower() in RATE_LIMIT_EXEMPT_ROLES


async def check_rate_limit(user_id: str, endpoint: str, limit: int, user_role: Optional[str] = None) -> None:
    """
    Check if user has exceeded their daily rate limit.
    Raises HTTPException with 429 if limit exceeded.
    
    The daily limit resets at midnight in the server's local timezone.
    
    Users with roles in ASSISTANT_RATE_LIMIT_EXEMPT_ROLES are exempt from rate limiting.
    
    Args:
        user_id: The user's ID
        endpoint: Endpoint identifier for the rate limit key
        limit: Maximum requests per day
        user_role: The user's role (member, admin, owner) - if exempt, skip rate limiting
    """
    # Check if user role is exempt from rate limiting
    if user_role and is_role_exempt(user_role):
        return  # No rate limit for exempt roles
    
    redis = await get_redis()
    
    # Include date (server local time) so keys naturally partition by day
    day = _get_local_date()
    key = f"rl:assistant:{user_id}:{endpoint}:{day}"
    
    ttl = _seconds_until_local_midnight()
    count = await redis.eval(LUA_INCR_EXPIRE, 1, key, ttl)
    
    if int(count) > limit:
        raise HTTPException(
            status_code=429,
            detail=f"Daily limit exceeded for this endpoint ({limit}/day). Try again tomorrow.",
            headers={"Retry-After": str(ttl)},
        )


async def get_rate_limit_status(user_id: str, endpoint: str, limit: int, user_role: Optional[str] = None) -> dict:
    """
    Get the current rate limit status for a user.
    
    The daily limit resets at midnight in the server's local timezone.
    
    Args:
        user_id: The user's ID
        endpoint: Endpoint identifier for the rate limit key
        limit: Maximum requests per day
        user_role: The user's role - if exempt, returns unlimited status
    
    Returns:
        dict with 'used', 'limit', 'remaining', 'resets_in_seconds', 'is_exempt'
    """
    # Check if user role is exempt from rate limiting
    if user_role and is_role_exempt(user_role):
        return {
            "used": 0,
            "limit": -1,  # -1 indicates unlimited
            "remaining": -1,  # -1 indicates unlimited
            "resets_in_seconds": 0,
            "is_exempt": True,
        }
    
    redis = await get_redis()
    
    day = _get_local_date()
    key = f"rl:assistant:{user_id}:{endpoint}:{day}"
    
    count = await redis.get(key)
    used = int(count) if count else 0
    ttl = _seconds_until_local_midnight()
    
    return {
        "used": used,
        "limit": limit,
        "remaining": max(0, limit - used),
        "resets_in_seconds": ttl,
        "is_exempt": False,
    }
