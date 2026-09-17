"""
Retrieve document IDs accessible by a user.

Queries ACL entries to determine which documents the user can read.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from m_flow.adapters.relational import get_db_adapter
from m_flow.data.methods import fetch_dataset_items
from m_flow.data.models import Dataset, DatasetEntry
from ...models import ACL, Permission


async def get_document_ids_for_user(
    user_id: UUID,
    datasets: list[str] | None = None,
) -> list[str]:
    """
    Get document IDs user has read access to.

    Args:
        user_id: User UUID.
        datasets: Optional list of dataset names to filter.

    Returns:
        List of document IDs with read permission.
    """
    engine = get_db_adapter()

    async with engine.get_async_session() as session:
        async with session.begin():
            # Find datasets where user has read permission
            dataset_ids = (
                await session.scalars(
                    select(Dataset.id)
                    .join(ACL.dataset)
                    .join(ACL.permission)
                    .where(
                        ACL.principal_id == user_id,
                        Permission.name == "read",
                    )
                )
            ).all()

            # Collect documents from accessible datasets
            doc_ids = []
            for ds_id in dataset_ids:
                data_list = await fetch_dataset_items(ds_id)
                doc_ids.extend(d.id for d in data_list)

            # Filter by specified datasets if provided
            if not datasets:
                return doc_ids

            return await _filter_by_dataset_names(session, user_id, datasets, doc_ids)


async def _filter_by_dataset_names(
    session,
    user_id: UUID,
    dataset_names: list[str],
    doc_ids: list,
) -> list[str]:
    """Filter documents to those in specified datasets."""
    filtered = set()

    for ds_name in dataset_names:
        # Find dataset by name and owner
        ds_id = (
            await session.scalars(
                select(Dataset.id).where(
                    Dataset.name == ds_name,
                    Dataset.owner_id == user_id,
                )
            )
        ).one_or_none()

        if ds_id is None:
            continue

        # Check which documents belong to this dataset
        for doc_id in doc_ids:
            found = (
                await session.scalars(
                    select(DatasetEntry.data_id).where(
                        DatasetEntry.dataset_id == ds_id,
                        DatasetEntry.data_id == doc_id,
                    )
                )
            ).one_or_none()

            if found:
                filtered.add(doc_id)

    return list(filtered)
