"""
Concurrency-safe permission retrieval and creation.

This module provides a helper function to safely get or create Permission
records in concurrent scenarios, avoiding IntegrityError from UNIQUE constraint
violations on the `permissions.name` column.

The implementation uses SQLAlchemy's SAVEPOINT (begin_nested) pattern as
recommended in the official documentation:
https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#using-savepoint
"""

from __future__ import annotations

from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from m_flow.auth.models import Permission


async def get_or_create_permission(
    session: AsyncSession,
    permission_name: str,
) -> Permission:
    """
    Get existing permission or create new one (concurrency-safe).

    This function handles the race condition where multiple concurrent requests
    attempt to create the same permission simultaneously. It uses a SAVEPOINT
    to isolate the INSERT operation, allowing the outer transaction to continue
    even if IntegrityError occurs.

    The pattern works as follows:
    1. Try to find existing permission
    2. If not found, attempt to create within SAVEPOINT
    3. If IntegrityError (another request created it), SAVEPOINT auto-rolls back
    4. Re-query to get the permission (either ours or the concurrent one)

    Args:
        session: SQLAlchemy async session (must be within a transaction)
        permission_name: Name of the permission (e.g., "read", "write")

    Returns:
        Permission object (either existing or newly created)

    Raises:
        RuntimeError: If permission cannot be retrieved after creation attempt
            (indicates a serious bug)

    Example:
        async with engine.get_async_session() as session:
            perm = await get_or_create_permission(session, "read")
            # Use perm.id for ACL creation
            await session.commit()
    """
    # Step 1: Try to find existing permission (fast path)
    perm_query = select(Permission).where(Permission.name == permission_name)
    perm = (await session.execute(perm_query)).scalars().first()

    if perm is not None:
        return perm

    # Step 2: Permission doesn't exist, try to create it using SAVEPOINT
    # The SAVEPOINT automatically rolls back on IntegrityError,
    # allowing the outer transaction to continue unaffected.
    try:
        async with session.begin_nested():
            # This INSERT is wrapped in a SAVEPOINT
            await session.execute(insert(Permission).values(name=permission_name))
            # If we reach here, the INSERT succeeded
            # SAVEPOINT will be RELEASED (committed to outer transaction)
            # when exiting the context manager
    except IntegrityError:
        # Another concurrent request created it first
        # SAVEPOINT was automatically rolled back by SQLAlchemy
        # The outer transaction remains intact and usable
        # DO NOT call session.rollback() here - it would roll back
        # the entire outer transaction!
        pass

    # Step 3: Re-query to get the permission
    # This will find either:
    # - The permission we just created (if our INSERT succeeded)
    # - The permission created by another concurrent request (if IntegrityError)
    perm = (await session.execute(perm_query)).scalars().first()

    if perm is None:
        # This should never happen in normal operation
        # If we get here, it means:
        # - Our INSERT failed with IntegrityError (another request created it)
        # - But the re-query didn't find it
        # This could indicate a transaction isolation issue or a bug
        raise RuntimeError(
            f"Failed to get or create permission '{permission_name}' "
            "after IntegrityError - this indicates a serious bug. "
            "Please check transaction isolation settings."
        )

    return perm
