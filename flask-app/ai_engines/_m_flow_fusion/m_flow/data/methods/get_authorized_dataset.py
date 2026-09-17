"""Fetch a single dataset by UUID with permission enforcement."""

from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from m_flow.auth.models import User
from m_flow.data.methods.get_authorized_existing_datasets import (
    get_authorized_existing_datasets,
)
from ..models import Dataset

_logger = logging.getLogger(__name__)


async def get_authorized_dataset(
    user: User,
    dataset_id: UUID,
    permission_type: str = "read",
) -> Optional[Dataset]:
    """Retrieve a dataset only when the caller holds sufficient privileges.

    Delegates to the bulk authorization helper with a single-element ID
    list.  If the dataset does not exist or the user lacks the requested
    permission, ``None`` is returned.

    Parameters
    ----------
    user:
        The requesting principal.
    dataset_id:
        Unique identifier of the target dataset.
    permission_type:
        Required access level — one of ``"read"``, ``"write"``,
        ``"delete"``, ``"share"``.  Defaults to ``"read"``.

    Returns
    -------
    Optional[Dataset]
        The permitted dataset, or ``None`` when access is denied or the
        dataset does not exist.
    """
    permitted_datasets = await get_authorized_existing_datasets(
        [dataset_id],
        permission_type,
        user,
    )

    if not permitted_datasets:
        _logger.debug(
            "mflow.dataset.access_denied dataset_id=%s user=%s perm=%s",
            dataset_id,
            getattr(user, "id", "?"),
            permission_type,
        )
        return None

    return permitted_datasets[0]
