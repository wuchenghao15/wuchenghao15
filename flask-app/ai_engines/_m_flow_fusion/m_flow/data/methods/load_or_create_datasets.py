"""
Dataset resolution utility.

Resolves dataset identifiers to Dataset instances.
"""

from __future__ import annotations

from typing import List, Union
from uuid import UUID

from m_flow.data.exceptions import DatasetNotFoundError
from m_flow.data.methods.create_authorized_dataset import create_authorized_dataset
from m_flow.data.models import Dataset


async def load_or_create_datasets(
    dataset_names: List[Union[str, UUID]],
    existing_datasets: List[Dataset],
    user,
) -> List[Dataset]:
    """
    Resolve identifiers to Dataset instances.

    Matches against existing datasets first, creates
    new ones for unrecognized string names.

    Args:
        dataset_names: Names or UUIDs to resolve.
        existing_datasets: Known datasets to match.
        user: User for new dataset ownership.

    Returns:
        List of Dataset instances.

    Raises:
        DatasetNotFoundError: UUID doesn't match existing.
    """
    result: List[Dataset] = []

    for identifier in dataset_names:
        # Find in existing
        match = _find_matching(identifier, existing_datasets)

        if match:
            result.append(match)
            continue

        # UUID must match existing
        if isinstance(identifier, UUID):
            raise DatasetNotFoundError(f"Unknown dataset UUID: {identifier}")

        # Create new for string name
        new_ds = await create_authorized_dataset(identifier, user)
        result.append(new_ds)

    return result


def _find_matching(
    identifier: Union[str, UUID],
    datasets: List[Dataset],
) -> Dataset | None:
    """Find dataset by name or ID."""
    for ds in datasets:
        if ds.name == identifier or ds.id == identifier:
            return ds
    return None
