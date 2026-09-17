"""
Principal query module.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from m_flow.adapters.relational import get_db_adapter
from m_flow.auth.models.Principal import Principal


async def get_principal(principal_id: UUID) -> Principal:
    """
    Get principal entity by ID.

    Args:
        principal_id: Principal unique identifier.

    Returns:
        Principal entity.

    Raises:
        NoResultFound: No matching principal found.
    """
    db = get_db_adapter()

    async with db.get_async_session() as sess:
        stmt = select(Principal).where(Principal.id == principal_id)
        result = await sess.execute(stmt)
        return result.unique().scalar_one()
