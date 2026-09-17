"""Resolve a single dataset by its display name under the caller's permission scope."""

from __future__ import annotations

import logging
from typing import Optional

from m_flow.auth.models import User
from m_flow.data.methods.get_authorized_existing_datasets import (
    get_authorized_existing_datasets,
)
from ..models import Dataset

_logger = logging.getLogger(__name__)


async def get_authorized_dataset_by_name(
    dataset_name: str,
    user: User,
    permission_type: str,
) -> Optional[Dataset]:
    """Look up an accessible dataset whose name matches *dataset_name*.

    The caller's permission scope is resolved first, then the resulting
    collection is scanned for an exact name match.  Returns the first
    hit or ``None`` when no dataset with that name is visible to
    *user* under *permission_type*.

    Parameters
    ----------
    dataset_name:
        Exact display name to search for.
    user:
        Principal whose access grants are evaluated.
    permission_type:
        Access level required (``"read"``, ``"write"``, ``"delete"``,
        ``"share"``).

    Returns
    -------
    Optional[Dataset]
        The resolved dataset, or ``None`` if not found / not permitted.
    """
    visible_datasets = await get_authorized_existing_datasets(
        [],
        permission_type,
        user,
    )

    _logger.debug(
        "mflow.dataset.lookup_by_name user=%s name=%s visible=%d",
        getattr(user, "id", "?"),
        dataset_name,
        len(visible_datasets),
    )

    matched_dataset: Optional[Dataset] = None
    for candidate in visible_datasets:
        if candidate.name == dataset_name:
            matched_dataset = candidate
            break

    return matched_dataset
