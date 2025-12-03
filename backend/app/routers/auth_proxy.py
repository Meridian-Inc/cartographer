"""
Auth Proxy Router
Proxies authentication requests to the Auth microservice
"""
import os
import logging
from typing import Optional, Any

import httpx
from fastapi import APIRouter, HTTPException, Request, Response, Depends, Header
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])

AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://localhost:8002")


async def proxy_request(
    method: str,
    path: str,
    request: Request,
    body: Optional[dict] = None
) -> Any:
    """Proxy a request to the auth service"""
    url = f"{AUTH_SERVICE_URL}{path}"
    
    # Forward authorization header if present
    headers = {}
    auth_header = request.headers.get("Authorization")
    if auth_header:
        headers["Authorization"] = auth_header
    
    headers["Content-Type"] = "application/json"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=body)
            elif method == "PATCH":
                response = await client.patch(url, headers=headers, json=body)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise HTTPException(status_code=405, detail="Method not allowed")
            
            # Parse response content safely
            content = None
            if response.content:
                try:
                    content = response.json()
                except Exception as json_err:
                    logger.warning(f"Failed to parse JSON from auth service: {json_err}")
                    # If it's an error status, try to return raw text as error detail
                    if response.status_code >= 400:
                        content = {"detail": response.text or "Unknown error from auth service"}
            
            return JSONResponse(
                content=content,
                status_code=response.status_code
            )
    except httpx.ConnectError:
        logger.error(f"Failed to connect to auth service at {url}")
        raise HTTPException(
            status_code=503,
            detail="Auth service unavailable"
        )
    except httpx.TimeoutException:
        logger.error(f"Timeout connecting to auth service at {url}")
        raise HTTPException(
            status_code=504,
            detail="Auth service timeout"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error proxying to auth service: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Auth proxy error: {str(e)}"
        )


# ==================== Setup Endpoints ====================

@router.get("/auth/setup/status")
async def get_setup_status(request: Request):
    """Check if initial setup is complete"""
    return await proxy_request("GET", "/api/auth/setup/status", request)


@router.post("/auth/setup/owner")
async def setup_owner(request: Request):
    """Create the initial owner account"""
    body = await request.json()
    return await proxy_request("POST", "/api/auth/setup/owner", request, body)


# ==================== Authentication Endpoints ====================

@router.post("/auth/login")
async def login(request: Request):
    """Authenticate and get access token"""
    body = await request.json()
    return await proxy_request("POST", "/api/auth/login", request, body)


@router.post("/auth/logout")
async def logout(request: Request):
    """Logout current user"""
    return await proxy_request("POST", "/api/auth/logout", request)


@router.get("/auth/session")
async def get_session(request: Request):
    """Get current session information"""
    return await proxy_request("GET", "/api/auth/session", request)


@router.post("/auth/verify")
async def verify_token(request: Request):
    """Verify if the current token is valid"""
    return await proxy_request("POST", "/api/auth/verify", request)


# ==================== User Management Endpoints ====================

@router.get("/auth/users")
async def list_users(request: Request):
    """List all users"""
    return await proxy_request("GET", "/api/auth/users", request)


@router.post("/auth/users")
async def create_user(request: Request):
    """Create a new user"""
    body = await request.json()
    return await proxy_request("POST", "/api/auth/users", request, body)


@router.get("/auth/users/{user_id}")
async def get_user(user_id: str, request: Request):
    """Get user by ID"""
    return await proxy_request("GET", f"/api/auth/users/{user_id}", request)


@router.patch("/auth/users/{user_id}")
async def update_user(user_id: str, request: Request):
    """Update a user"""
    body = await request.json()
    return await proxy_request("PATCH", f"/api/auth/users/{user_id}", request, body)


@router.delete("/auth/users/{user_id}")
async def delete_user(user_id: str, request: Request):
    """Delete a user"""
    return await proxy_request("DELETE", f"/api/auth/users/{user_id}", request)


# ==================== Profile Endpoints ====================

@router.get("/auth/me")
async def get_current_profile(request: Request):
    """Get current user's profile"""
    return await proxy_request("GET", "/api/auth/me", request)


@router.patch("/auth/me")
async def update_current_profile(request: Request):
    """Update current user's profile"""
    body = await request.json()
    return await proxy_request("PATCH", "/api/auth/me", request, body)


@router.post("/auth/me/change-password")
async def change_password(request: Request):
    """Change current user's password"""
    body = await request.json()
    return await proxy_request("POST", "/api/auth/me/change-password", request, body)


# ==================== Invitation Endpoints ====================

@router.get("/auth/invites")
async def list_invites(request: Request):
    """List all invitations"""
    return await proxy_request("GET", "/api/auth/invites", request)


@router.post("/auth/invites")
async def create_invite(request: Request):
    """Create a new invitation"""
    body = await request.json()
    return await proxy_request("POST", "/api/auth/invites", request, body)


@router.get("/auth/invites/{invite_id}")
async def get_invite(invite_id: str, request: Request):
    """Get invitation by ID"""
    return await proxy_request("GET", f"/api/auth/invites/{invite_id}", request)


@router.delete("/auth/invites/{invite_id}")
async def revoke_invite(invite_id: str, request: Request):
    """Revoke an invitation"""
    return await proxy_request("DELETE", f"/api/auth/invites/{invite_id}", request)


@router.post("/auth/invites/{invite_id}/resend")
async def resend_invite(invite_id: str, request: Request):
    """Resend an invitation email"""
    return await proxy_request("POST", f"/api/auth/invites/{invite_id}/resend", request)


# ==================== Public Invitation Endpoints ====================

@router.get("/auth/invite/verify/{token}")
async def verify_invite_token(token: str, request: Request):
    """Verify an invitation token"""
    return await proxy_request("GET", f"/api/auth/invite/verify/{token}", request)


@router.post("/auth/invite/accept")
async def accept_invite(request: Request):
    """Accept an invitation and create account"""
    body = await request.json()
    return await proxy_request("POST", "/api/auth/invite/accept", request, body)
