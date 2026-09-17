"""Data deletion utility."""

from __future__ import annotations

from uuid import UUID

from m_flow.adapters.relational import get_db_adapter
from m_flow.data.exceptions.exceptions import InvalidTableAttributeError
from m_flow.data.models import Data


async def delete_data(data: Data) -> UUID:
    """
    Delete a data record from the database.

    Raises
    ------
    InvalidTableAttributeError
        If data object lacks __tablename__ attribute.
    """
    if not hasattr(data, "__tablename__"):
        raise InvalidTableAttributeError()

    engine = get_db_adapter()
    return await engine.delete_data_entity(data.id)
