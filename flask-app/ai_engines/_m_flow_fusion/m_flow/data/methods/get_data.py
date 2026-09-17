"""
Data Retrieval Module
=====================

Provides secure access to data records with authorization checks.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from m_flow.adapters.relational import get_db_adapter

from ..exceptions import UnauthorizedDataAccessError
from ..models import Data


async def get_data(user_id: UUID, data_id: UUID) -> Optional[Data]:
    """
    Retrieve a data record with authorization verification.

    Fetches the data record and verifies that the requesting
    user has ownership rights before returning it.

    Parameters
    ----------
    user_id : UUID
        Identifier of the user making the request.
    data_id : UUID
        Identifier of the data record to retrieve.

    Returns
    -------
    Data | None
        The data record if found and authorized, None if not found.

    Raises
    ------
    UnauthorizedDataAccessError
        If the user does not own the requested data.
    """
    db = get_db_adapter()

    async with db.get_async_session() as session:
        data_record = await session.get(Data, data_id)

        # Check ownership if record exists
        if data_record is not None and data_record.owner_id != user_id:
            raise UnauthorizedDataAccessError(message=f"User {user_id} is not authorized to access data {data_id}")

        return data_record
