"""
Auth module error types.

Defines exception classes for authentication and authorization failures.
"""

from __future__ import annotations

from fastapi import status as http_status

from m_flow.exceptions import BadInputError

# HTTP status code constants
_NOT_FOUND = http_status.HTTP_404_NOT_FOUND
_FORBIDDEN = http_status.HTTP_403_FORBIDDEN


class RoleNotFoundError(BadInputError):
    """Raised when a role lookup fails."""

    def __init__(self, message: str = "Specified role does not exist", **kw):
        super().__init__(
            message,
            kind="RoleNotFoundError",
            http_status=kw.get("status_code", _NOT_FOUND),
        )


class TenantNotFoundError(BadInputError):
    """Raised when tenant lookup fails."""

    def __init__(self, message: str = "Specified tenant does not exist", **kw):
        super().__init__(
            message,
            kind="TenantNotFoundError",
            http_status=kw.get("status_code", _NOT_FOUND),
        )


class UserNotFoundError(BadInputError):
    """Raised when user lookup fails."""

    def __init__(self, message: str = "Specified user does not exist", **kw):
        super().__init__(
            message,
            kind="UserNotFoundError",
            http_status=kw.get("status_code", _NOT_FOUND),
        )


class PermissionDeniedError(BadInputError):
    """Raised when access check fails."""

    def __init__(self, message: str = "Operation not permitted", **kw):
        super().__init__(
            message,
            kind="PermissionDeniedError",
            http_status=kw.get("status_code", _FORBIDDEN),
        )


class PermissionNotFoundError(BadInputError):
    """Raised when permission type is undefined."""

    def __init__(self, message: str = "Unknown permission type", **kw):
        super().__init__(
            message,
            kind="PermissionNotFoundError",
            http_status=kw.get("status_code", _FORBIDDEN),
        )
