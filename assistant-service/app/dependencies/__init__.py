"""
Auth dependencies for assistant service routes.
"""
from .auth import (
    AuthenticatedUser,
    UserRole,
    get_current_user,
    require_auth,
)

__all__ = [
    "AuthenticatedUser",
    "UserRole",
    "get_current_user",
    "require_auth",
]

