"""
Resolve datasets with authorization.
"""

from __future__ import annotations

from typing import Union
from uuid import UUID

from m_flow.auth.methods import get_seed_user
from m_flow.auth.models import User
from m_flow.data.exceptions import DatasetNotFoundError
from m_flow.data.methods import (
    check_dataset_name,
    get_authorized_existing_datasets,
    load_or_create_datasets,
)
from m_flow.data.models import Dataset


async def authorize_datasets(
    datasets: Union[str, UUID, list[str], list[UUID]],
    user: User | None = None,
) -> tuple[User, list[Dataset]]:
    """
    Authorize and resolve datasets for pipeline processing.

    Creates new datasets if needed; validates write permissions.
    """
    usr = user or await get_seed_user()

    # Ensure list form
    ds_input = [datasets] if isinstance(datasets, (str, UUID)) else datasets

    # Fetch existing with write access
    existing = await get_authorized_existing_datasets(ds_input, "write", usr)

    # Load/create as needed
    result = existing if not ds_input else await load_or_create_datasets(ds_input, existing, usr)

    if not result:
        raise DatasetNotFoundError("No datasets found or created")

    # Validate names
    for d in result:
        check_dataset_name(d.name)

    return usr, result
