"""
Authorized Dataset Creation
===========================

Creates datasets with full permission grants for the creating user.
This ensures the user has complete control over their own datasets.
"""

from __future__ import annotations

from m_flow.adapters.relational import get_db_adapter
from m_flow.auth.models import User
from m_flow.auth.permissions.methods import give_permission_on_dataset
from m_flow.data.models import Dataset

from .create_dataset import create_dataset


# Permission types to grant on new datasets
_FULL_ACCESS_PERMISSIONS = ("read", "write", "delete", "share")


async def create_authorized_dataset(dataset_name: str, user: User) -> Dataset:
    """
    Create a new dataset and grant full permissions to the user.

    This is the recommended way to create datasets as it ensures
    the creator has complete access rights from the start.

    Parameters
    ----------
    dataset_name : str
        Human-readable name for the dataset.
    user : User
        The user who will own and have full access to the dataset.

    Returns
    -------
    Dataset
        The newly created dataset with permissions configured.

    Example
    -------
    >>> dataset = await create_authorized_dataset("My Research Data", current_user)
    >>> print(f"Created dataset: {dataset.id}")
    """
    db = get_db_adapter()

    # Create the dataset record
    async with db.get_async_session() as session:
        new_dataset = await create_dataset(dataset_name, user, session)

    # Grant all access permissions to the creator
    for permission_type in _FULL_ACCESS_PERMISSIONS:
        await give_permission_on_dataset(user, new_dataset.id, permission_type)

    return new_dataset
