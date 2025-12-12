"""
Auth dependencies for backend routes.
Verifies tokens by calling the auth service.
"""
import os
import logging
from typing import Optional
from enum import Enum

import httpx
from fastapi import HTTPException, Depends, Header, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

logger = logging.getLogger(__name__)

AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://localhost:8002")

# Security scheme for JWT
security = HTTPBearer(auto_error=False)


class UserRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class AuthenticatedUser(BaseModel):
    """Authenticated user information from token verification"""
    user_id: str
    username: str
    role: UserRole
    
    @property
    def is_owner(self) -> bool:
        return self.role == UserRole.OWNER
    
    @property
    def can_write(self) -> bool:
        return self.role in [UserRole.OWNER, UserRole.ADMIN]


async def verify_token_with_auth_service(token: str) -> Optional[AuthenticatedUser]:
    """Verify a token by calling the auth service"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{AUTH_SERVICE_URL}/api/auth/verify",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code != 200:
                logger.debug(f"Token verification failed with status {response.status_code}")
                return None
            
            data = response.json()
            if not data.get("valid"):
                return None
            
            return AuthenticatedUser(
                user_id=data["user_id"],
                username=data["username"],
                role=UserRole(data["role"])
            )
    except httpx.ConnectError:
        logger.error(f"Failed to connect to auth service at {AUTH_SERVICE_URL}")
        raise HTTPException(
            status_code=503,
            detail="Auth service unavailable"
        )
    except httpx.TimeoutException:
        logger.error(f"Timeout connecting to auth service")
        raise HTTPException(
            status_code=504,
            detail="Auth service timeout"
        )
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    token: Optional[str] = Query(None, description="JWT token (for SSE/EventSource which doesn't support headers)")
) -> Optional[AuthenticatedUser]:
    """Get current user from JWT token (returns None if not authenticated).
    
    Supports both:
    - Authorization header (standard approach)
    - Query parameter 'token' (for EventSource/SSE which doesn't support custom headers)
    """
    # Try Authorization header first
    if credentials:
        return await verify_token_with_auth_service(credentials.credentials)
    
    # Fall back to query parameter (for SSE/EventSource)
    if token:
        return await verify_token_with_auth_service(token)
    
    return None


async def require_auth(
    user: Optional[AuthenticatedUser] = Depends(get_current_user)
) -> AuthenticatedUser:
    """Require authenticated user"""
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user


async def require_write_access(
    user: AuthenticatedUser = Depends(require_auth)
) -> AuthenticatedUser:
    """Require write access (owner or readwrite)"""
    if not user.can_write:
        raise HTTPException(
            status_code=403,
            detail="Write access required"
        )
    return user


async def require_owner(
    user: AuthenticatedUser = Depends(require_auth)
) -> AuthenticatedUser:
    """Require owner role"""
    if not user.is_owner:
        raise HTTPException(
            status_code=403,
            detail="Owner access required"
        )
    return user
