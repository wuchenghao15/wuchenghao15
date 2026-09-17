"""
Single dataset authorization helper.
"""

from __future__ import annotations

from uuid import UUID

from m_flow.auth.models import User
from m_flow.data.models import Dataset
from m_flow.pipeline.layers.authorize_datasets import (
    authorize_datasets,
)


async def authorize_dataset(
    dataset_name: str,
    dataset_id: UUID | None = None,
    user: User | None = None,
) -> tuple[User, Dataset]:
    """
    Resolve a single dataset with authorization.

    Delegates to multi-dataset resolver and extracts the first result.
    """
    identifier = dataset_id if dataset_id else dataset_name
    usr, datasets = await authorize_datasets(identifier, user)
    return usr, datasets[0]
