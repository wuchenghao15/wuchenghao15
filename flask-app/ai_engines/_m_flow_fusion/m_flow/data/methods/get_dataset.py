"""
Dataset retrieval utility.
"""

from __future__ import annotations

from uuid import UUID

from m_flow.adapters.relational import get_db_adapter
from m_flow.data.models import Dataset


async def get_dataset(
    user_id: UUID,
    dataset_id: UUID,
) -> Dataset | None:
    """
    Get dataset owned by specified user.

    Args:
        user_id: User UUID.
        dataset_id: Dataset UUID.

    Returns:
        Dataset object or None (not found or no permission).
    """
    db = get_db_adapter()

    async with db.get_async_session() as sess:
        record = await sess.get(Dataset, dataset_id)

        # Verify ownership
        if record is not None and record.owner_id != user_id:
            return None

        return record
