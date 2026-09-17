"""
Database queries for sync operation records.

This module provides async functions for retrieving sync operation
data from the relational database. All queries use SQLAlchemy ORM.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.orm import Query

from m_flow.adapters.relational import get_db_adapter
from m_flow.shared.sync.models import SyncOperation, SyncStatus

if TYPE_CHECKING:
    from collections.abc import Sequence


def _order_by_newest(query: Query) -> Query:
    """Apply descending created_at ordering to a query."""
    return query.order_by(SyncOperation.created_at.desc())


def _paginate(query: Query, limit: int, offset: int) -> Query:
    """Apply limit and offset to a query."""
    return query.limit(limit).offset(offset)


async def fetch_by_run_id(run_id: str) -> Optional[SyncOperation]:
    """
    Look up a sync operation by its public run identifier.

    Parameters
    ----------
    run_id
        The user-facing identifier for the sync operation.

    Returns
    -------
    Optional[SyncOperation]
        The matching record, or None if no match exists.
    """
    db = get_db_adapter()

    async with db.get_async_session() as session:
        query = select(SyncOperation).filter(SyncOperation.run_id == run_id)
        rows = await session.execute(query)
        return rows.scalars().first()


# Alias
get_sync_operation = fetch_by_run_id


async def list_user_operations(
    user_id: UUID,
    page_size: int = 50,
    page_offset: int = 0,
) -> "Sequence[SyncOperation]":
    """
    Retrieve sync operations owned by a specific user.

    Parameters
    ----------
    user_id
        UUID of the owning user.
    page_size
        Maximum number of results to return.
    page_offset
        Number of results to skip before returning.

    Returns
    -------
    Sequence[SyncOperation]
        Operations ordered by creation time (newest first).
    """
    db = get_db_adapter()

    async with db.get_async_session() as session:
        base_query = select(SyncOperation).filter(SyncOperation.user_id == user_id)
        ordered = _order_by_newest(base_query)
        paginated = _paginate(ordered, page_size, page_offset)

        rows = await session.execute(paginated)
        return list(rows.scalars().all())


# Alias
get_user_sync_operations = list_user_operations


async def list_dataset_operations(
    dataset_id: UUID,
    page_size: int = 50,
    page_offset: int = 0,
) -> "Sequence[SyncOperation]":
    """
    Retrieve sync operations associated with a dataset.

    Parameters
    ----------
    dataset_id
        UUID of the target dataset.
    page_size
        Maximum number of results.
    page_offset
        Results to skip.

    Returns
    -------
    Sequence[SyncOperation]
        Operations ordered by creation time (newest first).
    """
    db = get_db_adapter()

    async with db.get_async_session() as session:
        base_query = select(SyncOperation).filter(SyncOperation.dataset_id == dataset_id)
        ordered = _order_by_newest(base_query)
        paginated = _paginate(ordered, page_size, page_offset)

        rows = await session.execute(paginated)
        return list(rows.scalars().all())


# Alias
get_sync_operations_by_dataset = list_dataset_operations


async def find_active_user_operations(user_id: UUID) -> "Sequence[SyncOperation]":
    """
    Find all currently active sync operations for a user.

    Active means the operation has status STARTED or IN_PROGRESS.

    Parameters
    ----------
    user_id
        UUID of the user to query.

    Returns
    -------
    Sequence[SyncOperation]
        Active operations ordered by creation time (newest first).
    """
    active_states = [SyncStatus.STARTED, SyncStatus.IN_PROGRESS]

    db = get_db_adapter()

    async with db.get_async_session() as session:
        query = select(SyncOperation).filter(
            and_(
                SyncOperation.user_id == user_id,
                SyncOperation.status.in_(active_states),
            )
        )
        ordered = _order_by_newest(query)

        rows = await session.execute(ordered)
        return list(rows.scalars().all())


# Alias
get_running_sync_operations_for_user = find_active_user_operations
