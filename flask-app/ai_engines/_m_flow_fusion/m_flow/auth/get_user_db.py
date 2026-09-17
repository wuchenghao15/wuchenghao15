"""
User Database Access Module
============================

Provides database access utilities for user management,
integrating with FastAPI Users and SQLAlchemy.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import Depends
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from m_flow.adapters.relational import get_db_adapter

from .models.User import User


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an async database session.

    Yields
    ------
    AsyncSession
        Active database session for use in request handlers.
    """
    db = get_db_adapter()
    async with db.get_async_session() as session:
        yield session


async def get_user_db(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[SQLAlchemyUserDatabase, None]:
    """
    Provide a user database accessor.

    Parameters
    ----------
    session : AsyncSession
        Active database session (injected by FastAPI).

    Yields
    ------
    SQLAlchemyUserDatabase
        User database adapter for FastAPI Users.
    """
    yield SQLAlchemyUserDatabase(session, User)


# Context manager wrapper for programmatic use
get_user_db_context = asynccontextmanager(get_user_db)
