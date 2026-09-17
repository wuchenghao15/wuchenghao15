"""Fast existence check for data rows attached to a dataset."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import exists, select

from m_flow.adapters.relational import get_db_adapter
from m_flow.data.models import DatasetEntry

_logger = logging.getLogger(__name__)


async def has_dataset_data(dataset_id: UUID) -> bool:
    """Return whether *dataset_id* has at least one associated data record.

    Uses an ``EXISTS`` sub-query so the database can short-circuit as
    soon as the first matching row is found, avoiding a full count.

    Parameters
    ----------
    dataset_id:
        The dataset whose data presence is being tested.

    Returns
    -------
    bool
        ``True`` when one or more :class:`DatasetEntry` rows reference
        this dataset; ``False`` otherwise.
    """
    relational_adapter = get_db_adapter()

    async with relational_adapter.get_async_session() as db_session:
        existence_clause = select(exists().where(DatasetEntry.dataset_id == dataset_id))

        outcome = await db_session.execute(existence_clause)
        data_present = outcome.scalar_one()

    _logger.debug(
        "mflow.dataset.has_data dataset_id=%s present=%s",
        dataset_id,
        data_present,
    )
    return data_present
