"""
Unique data identifier generation.

Creates deterministic UUIDs for data items with legacy compatibility.
"""

from __future__ import annotations

from uuid import NAMESPACE_OID, UUID, uuid5

from sqlalchemy import select

from m_flow.adapters.relational import get_db_adapter
from m_flow.auth.models import User
from m_flow.data.models.Data import Data


async def get_unique_data_id(data_identifier: str, user: User) -> UUID:
    """
    Generate unique UUID for data item.

    Uses deterministic hashing based on identifier + user context.
    Falls back to legacy ID if existing record found.

    Args:
        data_identifier: Content hash or name.
        user: Owning user.

    Returns:
        UUID for the data item.
    """
    modern_id = _build_modern_id(data_identifier, user)
    legacy_id = _build_legacy_id(data_identifier, user)

    # Check for existing record
    if await _legacy_record_exists(legacy_id):
        return legacy_id

    return modern_id


def _build_modern_id(identifier: str, user: User) -> UUID:
    """Build ID with tenant context."""
    tid = str(user.tenant_id) if user.tenant_id else ""
    seed = f"{identifier}{user.id}{tid}"
    return uuid5(NAMESPACE_OID, seed)


def _build_legacy_id(identifier: str, user: User) -> UUID:
    """Build ID without tenant (for migration)."""
    seed = f"{identifier}{user.id}"
    return uuid5(NAMESPACE_OID, seed)


async def _legacy_record_exists(data_id: UUID) -> bool:
    """Check if legacy record exists."""
    engine = get_db_adapter()

    async with engine.get_async_session() as session:
        result = await session.execute(select(Data).where(Data.id == data_id))
        return result.scalar_one_or_none() is not None
