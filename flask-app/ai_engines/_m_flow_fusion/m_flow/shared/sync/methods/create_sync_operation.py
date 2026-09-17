"""
Sync operation creation.

Provides functionality for creating new sync operation records
in the database to track background synchronization tasks.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Sequence
from uuid import UUID

from m_flow.adapters.relational import get_db_adapter
from m_flow.shared.sync.models import SyncOperation, SyncStatus


def _utc_now() -> datetime:
    """Return current UTC timestamp."""
    return datetime.now(tz=timezone.utc)


def _uuids_to_strings(uuids: Sequence[UUID]) -> list[str]:
    """Convert a sequence of UUIDs to strings for JSON storage."""
    return [str(uid) for uid in uuids]


async def create_sync_operation(
    run_id: str,
    dataset_ids: Sequence[UUID],
    dataset_names: Sequence[str],
    user_id: UUID,
    total_records_to_sync: Optional[int] = None,
    total_records_to_download: Optional[int] = None,
    total_records_to_upload: Optional[int] = None,
) -> SyncOperation:
    """
    Initialize a new sync operation tracking record.

    Creates a database entry to track the progress and status of a
    background synchronization task.

    Parameters
    ----------
    run_id
        User-facing identifier for this operation.
    dataset_ids
        UUIDs of datasets being synchronized.
    dataset_names
        Display names of datasets being synchronized.
    user_id
        UUID of the user who initiated the sync.
    total_records_to_sync
        Expected total record count (optional).
    total_records_to_download
        Expected download count (optional).
    total_records_to_upload
        Expected upload count (optional).

    Returns
    -------
    SyncOperation
        The newly created database record.
    """
    db = get_db_adapter()

    record = SyncOperation(
        run_id=run_id,
        user_id=user_id,
        dataset_ids=_uuids_to_strings(dataset_ids),
        dataset_names=list(dataset_names),
        status=SyncStatus.STARTED,
        total_records_to_sync=total_records_to_sync,
        total_records_to_download=total_records_to_download,
        total_records_to_upload=total_records_to_upload,
        created_at=_utc_now(),
    )

    async with db.get_async_session() as session:
        session.add(record)
        await session.commit()
        await session.refresh(record)

    return record
