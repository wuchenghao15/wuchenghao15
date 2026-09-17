"""
Authentication & authorization exceptions.
"""

from __future__ import annotations

from .exceptions import (
    PermissionDeniedError,
    PermissionNotFoundError,
    RoleNotFoundError,
    TenantNotFoundError,
    UserNotFoundError,
)

__all__ = [
    "PermissionDeniedError",
    "PermissionNotFoundError",
    "RoleNotFoundError",
    "TenantNotFoundError",
    "UserNotFoundError",
]
