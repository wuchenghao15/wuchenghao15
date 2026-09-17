"""Data identification utility."""

from __future__ import annotations

from uuid import UUID

from m_flow.auth.models import User
from m_flow.data.methods import get_unique_data_id

from .data_types import IngestionData


async def identify(data: IngestionData, user: User) -> UUID:
    """Get or create unique ID for ingested data."""
    content_hash = data.get_identifier()
    return await get_unique_data_id(data_identifier=content_hash, user=user)
