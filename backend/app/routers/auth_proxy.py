"""
Auth Proxy Router
Proxies authentication requests to the Auth microservice

Performance optimizations:
- Uses shared HTTP client pool with connection reuse
- Circuit breaker prevents cascade failures
- Connections are pre-warmed on startup

Security:
- Public endpoints (login, setup, invite accept) have no auth requirement
- Protected endpoints require authentication at proxy level for defense in depth
- Owner-only endpoints (user management, invitations) require owner role at proxy level
"""
import logging
from typing import Optional, Any

from fastapi import APIRouter, HTTPException, Request, Response, Depends, Header
from fastapi.responses import JSONResponse

from ..dependencies import (
    AuthenticatedUser,
    require_auth,
    require_owner,
)
from ..services.http_client import http_pool

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])


async def proxy_request(
    method: str,
    path: str,
    request: Request,
    body: Optional[dict] = None
) -> Any:
    """Proxy a request to the auth service using the shared client pool"""
    # Forward authorization header if present
    headers = {}
    auth_header = request.headers.get("Authorization")
    if auth_header:
        headers["Authorization"] = auth_header
    
    headers["Content-Type"] = "application/json"
    
    return await http_pool.request(
        service_name="auth",
        method=method,
        path=path,
        json_body=body,
        headers=headers
        )


# ==================== Setup Endpoints ====================
# These endpoints are intentionally public for initial application setup

@router.get("/auth/setup/status")
async def get_setup_status(request: Request):
    """Check if initial setup is complete (public endpoint)"""
    return await proxy_request("GET", "/api/auth/setup/status", request)


@router.post("/auth/setup/owner")
async def setup_owner(request: Request):
    """Create the initial owner account (public endpoint - only works once)"""
    body = await request.json()
    return await proxy_request("POST", "/api/auth/setup/owner", request, body)


# ==================== Authentication Endpoints ====================
# Login is public, logout/session require authentication

@router.post("/auth/login")
async def login(request: Request):
    """Authenticate and get access token (public endpoint)"""
    body = await request.json()
    return await proxy_request("POST", "/api/auth/login", request, body)


@router.post("/auth/logout")
async def logout(request: Request, user: AuthenticatedUser = Depends(require_auth)):
    """Logout current user. Requires authentication."""
    return await proxy_request("POST", "/api/auth/logout", request)


@router.get("/auth/session")
async def get_session(request: Request, user: AuthenticatedUser = Depends(require_auth)):
    """Get current session information. Requires authentication."""
    return await proxy_request("GET", "/api/auth/session", request)


@router.post("/auth/verify")
async def verify_token(request: Request):
    """Verify if the current token is valid (public - returns valid: false if no token)"""
    return await proxy_request("POST", "/api/auth/verify", request)


# ==================== User Management Endpoints ====================
# Creating and deleting users requires owner role
# Listing and viewing requires authentication (auth service further restricts visibility)

@router.get("/auth/users")
async def list_users(request: Request, user: AuthenticatedUser = Depends(require_auth)):
    """List all users. Requires authentication (owners see all, others see only themselves)."""
    return await proxy_request("GET", "/api/auth/users", request)


@router.post("/auth/users")
async def create_user(request: Request, user: AuthenticatedUser = Depends(require_owner)):
    """Create a new user. Requires owner role."""
    body = await request.json()
    return await proxy_request("POST", "/api/auth/users", request, body)


@router.get("/auth/users/{user_id}")
async def get_user(user_id: str, request: Request, user: AuthenticatedUser = Depends(require_auth)):
    """Get user by ID. Requires authentication."""
    return await proxy_request("GET", f"/api/auth/users/{user_id}", request)


@router.patch("/auth/users/{user_id}")
async def update_user(user_id: str, request: Request, user: AuthenticatedUser = Depends(require_auth)):
    """Update a user. Requires authentication."""
    body = await request.json()
    return await proxy_request("PATCH", f"/api/auth/users/{user_id}", request, body)


@router.delete("/auth/users/{user_id}")
async def delete_user(user_id: str, request: Request, user: AuthenticatedUser = Depends(require_owner)):
    """Delete a user. Requires owner role."""
    return await proxy_request("DELETE", f"/api/auth/users/{user_id}", request)


# ==================== Profile Endpoints ====================
# All profile endpoints require authentication

@router.get("/auth/me")
async def get_current_profile(request: Request, user: AuthenticatedUser = Depends(require_auth)):
    """Get current user's profile. Requires authentication."""
    return await proxy_request("GET", "/api/auth/me", request)


@router.patch("/auth/me")
async def update_current_profile(request: Request, user: AuthenticatedUser = Depends(require_auth)):
    """Update current user's profile. Requires authentication."""
    body = await request.json()
    return await proxy_request("PATCH", "/api/auth/me", request, body)


@router.post("/auth/me/change-password")
async def change_password(request: Request, user: AuthenticatedUser = Depends(require_auth)):
    """Change current user's password. Requires authentication."""
    body = await request.json()
    return await proxy_request("POST", "/api/auth/me/change-password", request, body)


# ==================== Invitation Endpoints ====================
# All invitation management endpoints require owner role

@router.get("/auth/invites")
async def list_invites(request: Request, user: AuthenticatedUser = Depends(require_owner)):
    """List all invitations. Requires owner role."""
    return await proxy_request("GET", "/api/auth/invites", request)


@router.post("/auth/invites")
async def create_invite(request: Request, user: AuthenticatedUser = Depends(require_owner)):
    """Create a new invitation. Requires owner role."""
    body = await request.json()
    return await proxy_request("POST", "/api/auth/invites", request, body)


@router.get("/auth/invites/{invite_id}")
async def get_invite(invite_id: str, request: Request, user: AuthenticatedUser = Depends(require_owner)):
    """Get invitation by ID. Requires owner role."""
    return await proxy_request("GET", f"/api/auth/invites/{invite_id}", request)


@router.delete("/auth/invites/{invite_id}")
async def revoke_invite(invite_id: str, request: Request, user: AuthenticatedUser = Depends(require_owner)):
    """Revoke an invitation. Requires owner role."""
    return await proxy_request("DELETE", f"/api/auth/invites/{invite_id}", request)


@router.post("/auth/invites/{invite_id}/resend")
async def resend_invite(invite_id: str, request: Request, user: AuthenticatedUser = Depends(require_owner)):
    """Resend an invitation email. Requires owner role."""
    return await proxy_request("POST", f"/api/auth/invites/{invite_id}/resend", request)


# ==================== Public Invitation Endpoints ====================
# These endpoints are intentionally public - they allow users to accept invitations

@router.get("/auth/invite/verify/{token}")
async def verify_invite_token(token: str, request: Request):
    """Verify an invitation token (public endpoint)"""
    return await proxy_request("GET", f"/api/auth/invite/verify/{token}", request)


@router.post("/auth/invite/accept")
async def accept_invite(request: Request):
    """Accept an invitation and create account (public endpoint)"""
    body = await request.json()
    return await proxy_request("POST", "/api/auth/invite/accept", request, body)
