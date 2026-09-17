"""Get Users Router — m_flow.api.v1.users.routers.get_users_router"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from m_flow.auth.get_fastapi_users import get_fastapi_users
from m_flow.auth.get_user_db import get_async_session
from m_flow.auth.methods import get_authenticated_user
from m_flow.auth.models.User import User, UserRead, UserUpdate


def get_users_router() -> APIRouter:
    """
    Build users router with standard fastapi-users routes
    plus custom list endpoint.
    """
    # Get standard fastapi-users router
    fastapi_users = get_fastapi_users()
    router = fastapi_users.get_users_router(UserRead, UserUpdate)

    # Add custom GET / endpoint to list all users (superuser only)
    @router.get("", response_model=List[UserRead])
    async def list_users(
        user: User = Depends(get_authenticated_user),
        session: AsyncSession = Depends(get_async_session),
    ):
        """
        List all users (superuser only).

        Returns all users in the system. Requires superuser privileges.
        """
        if not user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Superuser access required",
            )

        result = await session.execute(select(User))
        users = result.scalars().all()
        return users

    return router


# ========================================================================
# Module: m_flow.api.v1.users.routers.get_users_router
# M-flow internal implementation — do not import directly
# ========================================================================
