"""
FastAPI-Users integration: UserManager and dependency injection.
"""

from __future__ import annotations

import json
import re
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, Request, Response
from fastapi_users import BaseUserManager, UUIDIDMixin
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.exceptions import UserAlreadyExists, UserNotExists

from m_flow.shared.logging_utils import get_logger

from .get_user_db import get_user_db
from .methods.get_user_by_email import get_user_by_email
from .models import User
from .security_check import get_secret_with_production_check

_log = get_logger("UserManager")


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    """
    Custom manager extending FastAPI-Users defaults with lifecycle hooks.

    Note: Security checks for token secrets are performed at class definition time,
    ensuring configuration errors are caught at application startup.
    """

    reset_password_token_secret: str = get_secret_with_production_check(
        "FASTAPI_USERS_RESET_PASSWORD_TOKEN_SECRET",
        "change_me_in_production",
        "reset password token",
    )
    verification_token_secret: str = get_secret_with_production_check(
        "FASTAPI_USERS_VERIFICATION_TOKEN_SECRET",
        "change_me_in_production",
        "verification token",
    )

    async def get_by_email(self, email: str) -> User:
        """
        Retrieve a user by email address.

        For the default user email, automatically creates the user if missing.
        This enables seamless login recovery after database reset.

        Raises
        ------
        UserNotExists
            When no matching record is found.
        """
        record = await get_user_by_email(email)

        if record is None:
            from m_flow.base_config import get_base_config

            cfg = get_base_config()
            default_email = cfg.default_user_email or "default_user@example.com"

            if email.lower() == default_email.lower():
                if not cfg.auto_create_default_user:
                    _log.warning(
                        "Default user %s missing but auto_create_default_user=False",
                        email,
                    )
                    raise UserNotExists()

                try:
                    from .methods.create_default_user import create_default_user

                    _log.info(
                        "Default user %s missing, auto-creating during login",
                        email,
                    )
                    return await create_default_user()
                except UserAlreadyExists:
                    # Exception raised by FastAPI-Users
                    # Re-query using configured original email to avoid PostgreSQL case sensitivity issues
                    record = await get_user_by_email(default_email)
                    if record is not None:
                        return record
                    raise UserNotExists()
                except Exception as e:
                    # Only handle database unique constraint conflicts (concurrent race condition)
                    error_str = str(e).lower()
                    is_integrity_error = (
                        "UNIQUE constraint failed".lower() in error_str  # SQLite
                        or "IntegrityError" in type(e).__name__
                        or "duplicate key" in error_str  # PostgreSQL
                        or "duplicate entry" in error_str  # MySQL/MariaDB
                    )
                    if is_integrity_error:
                        _log.debug("Concurrent user creation detected, retrying lookup")
                        # Re-query using configured original email to avoid PostgreSQL case sensitivity issues
                        record = await get_user_by_email(default_email)
                        if record is not None:
                            return record
                        raise UserNotExists()
                    # Other exceptions (e.g., database connection failure) should propagate, not be hidden
                    _log.error("Failed to create default user: %s", e)
                    raise

            raise UserNotExists()

        return record

    # -------------------------------------------------------------------------
    # Lifecycle hooks
    # -------------------------------------------------------------------------

    async def on_after_login(
        self,
        user: User,
        request: Optional[Request] = None,
        response: Optional[Response] = None,
    ) -> None:
        if response is None:
            return
        cookie_hdr = response.headers.get("Set-Cookie", "")
        m = re.search(r"([^=]+)=([^;]+)", cookie_hdr)
        if m:
            token = m.group(2)
            response.status_code = 200
            response.body = json.dumps({"access_token": token, "token_type": "bearer"}).encode("utf-8")
            response.headers["Content-Type"] = "application/json"

    async def on_after_register(
        self,
        user: User,
        request: Optional[Request] = None,
    ) -> None:
        # Extension point for post-registration actions
        pass

    async def on_after_forgot_password(
        self,
        user: User,
        token: str,
        request: Optional[Request] = None,
    ) -> None:
        # Extension point for password reset notifications
        pass

    async def on_after_request_verify(
        self,
        user: User,
        token: str,
        request: Optional[Request] = None,
    ) -> None:
        # Extension point for verification workflows
        pass


async def get_user_manager(
    db: SQLAlchemyUserDatabase = Depends(get_user_db),
) -> UserManager:
    """FastAPI dependency that yields a configured UserManager."""
    yield UserManager(db)


get_user_manager_context = asynccontextmanager(get_user_manager)
