"""
Sync operation update operations.

Provides functions for updating sync operation records in the database
with retry logic for transient failures.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Optional, TypeVar

from sqlalchemy import select
from sqlalchemy.exc import (
    DisconnectionError,
    OperationalError,
    SQLAlchemyError,
    TimeoutError as SATimeoutError,
)

from m_flow.adapters.relational import get_db_adapter
from m_flow.shared.infra_utils.calculate_backoff import calculate_backoff
from m_flow.shared.logging_utils import get_logger
from m_flow.shared.sync.models import SyncOperation, SyncStatus

_log = get_logger("sync.db_operations")

T = TypeVar("T")

# Transient errors that should trigger retry
_TRANSIENT_ERRORS = (DisconnectionError, OperationalError, SATimeoutError)

# Terminal statuses that auto-set completed_at
_TERMINAL_STATUSES = frozenset([SyncStatus.COMPLETED, SyncStatus.FAILED, SyncStatus.CANCELLED])


def _utc_now() -> datetime:
    """Return current UTC timestamp."""
    return datetime.now(tz=timezone.utc)


def _clamp(value: int, lo: int, hi: int) -> int:
    """Clamp value to [lo, hi] range."""
    return max(lo, min(hi, value))


async def _with_retry(
    fn: Callable[[], Awaitable[T]],
    context: str,
    max_attempts: int = 3,
) -> T:
    """
    Execute an async function with exponential backoff retry.

    Args:
        fn: Async callable to execute.
        context: Description for logging.
        max_attempts: Maximum retry attempts.

    Returns:
        Result from the function.

    Raises:
        Exception: The last exception if all attempts fail.
    """
    last_err: Optional[Exception] = None

    for attempt in range(max_attempts):
        try:
            return await fn()
        except _TRANSIENT_ERRORS as err:
            last_err = err
            if attempt + 1 >= max_attempts:
                _log.error(
                    "DB operation failed after %d attempts [%s]: %s",
                    max_attempts,
                    context,
                    err,
                )
                break

            delay = calculate_backoff(attempt)
            _log.warning(
                "Transient DB error [%s], retry %d/%d in %.2fs: %s",
                context,
                attempt + 1,
                max_attempts,
                delay,
                err,
            )
            await asyncio.sleep(delay)
        except Exception as err:
            _log.error("Non-recoverable DB error [%s]: %s", context, err)
            raise

    if last_err is not None:
        raise last_err
    raise RuntimeError("Unexpected retry loop exit")


async def update_sync_operation(
    run_id: str,
    *,
    status: Optional[SyncStatus] = None,
    progress_percentage: Optional[int] = None,
    records_downloaded: Optional[int] = None,
    records_uploaded: Optional[int] = None,
    total_records_to_sync: Optional[int] = None,
    total_records_to_download: Optional[int] = None,
    total_records_to_upload: Optional[int] = None,
    bytes_downloaded: Optional[int] = None,
    bytes_uploaded: Optional[int] = None,
    dataset_sync_hashes: Optional[dict[str, Any]] = None,
    error_message: Optional[str] = None,
    retry_count: Optional[int] = None,
    started_at: Optional[datetime] = None,
    completed_at: Optional[datetime] = None,
) -> Optional[SyncOperation]:
    """
    Update fields on a sync operation record.

    Args:
        run_id: Public identifier for the sync operation.
        status: New lifecycle status.
        progress_percentage: Completion percentage (0-100).
        records_downloaded: Count of downloaded records.
        records_uploaded: Count of uploaded records.
        total_records_to_sync: Total record count.
        total_records_to_download: Expected download count.
        total_records_to_upload: Expected upload count.
        bytes_downloaded: Downloaded byte count.
        bytes_uploaded: Uploaded byte count.
        dataset_sync_hashes: Per-dataset hash tracking.
        error_message: Error description for failed ops.
        retry_count: Number of retry attempts.
        started_at: Processing start timestamp.
        completed_at: Completion timestamp.

    Returns:
        Updated SyncOperation or None if not found.
    """

    async def _do_update() -> Optional[SyncOperation]:
        engine = get_db_adapter()

        async with engine.get_async_session() as session:
            try:
                # Fetch existing record
                stmt = select(SyncOperation).where(SyncOperation.run_id == run_id)
                result = await session.execute(stmt)
                record = result.scalars().first()

                if record is None:
                    _log.warning("Sync operation not found: %s", run_id)
                    return None

                # Apply updates
                updates: list[str] = []

                if status is not None:
                    record.status = status
                    updates.append(f"status={status.value}")

                if progress_percentage is not None:
                    record.progress_percentage = _clamp(progress_percentage, 0, 100)
                    updates.append(f"progress={progress_percentage}%")

                if records_downloaded is not None:
                    record.records_downloaded = records_downloaded
                    updates.append(f"downloaded={records_downloaded}")

                if records_uploaded is not None:
                    record.records_uploaded = records_uploaded
                    updates.append(f"uploaded={records_uploaded}")

                if total_records_to_sync is not None:
                    record.total_records_to_sync = total_records_to_sync

                if total_records_to_download is not None:
                    record.total_records_to_download = total_records_to_download

                if total_records_to_upload is not None:
                    record.total_records_to_upload = total_records_to_upload

                if bytes_downloaded is not None:
                    record.bytes_downloaded = bytes_downloaded

                if bytes_uploaded is not None:
                    record.bytes_uploaded = bytes_uploaded

                if dataset_sync_hashes is not None:
                    record.dataset_sync_hashes = dataset_sync_hashes

                if error_message is not None:
                    record.error_message = error_message

                if retry_count is not None:
                    record.retry_count = retry_count

                if started_at is not None:
                    record.started_at = started_at

                if completed_at is not None:
                    record.completed_at = completed_at

                # Auto-timestamps for state transitions
                if status == SyncStatus.IN_PROGRESS and record.started_at is None:
                    record.started_at = _utc_now()

                if status in _TERMINAL_STATUSES and completed_at is None:
                    record.completed_at = _utc_now()

                if updates:
                    _log.debug("Updating %s: %s", run_id, ", ".join(updates))

                await session.commit()
                await session.refresh(record)

                _log.debug("Updated sync operation: %s", run_id)
                return record

            except SQLAlchemyError as err:
                _log.error("DB error updating %s: %s", run_id, err, exc_info=True)
                await session.rollback()
                raise
            except Exception as err:
                _log.error("Error updating %s: %s", run_id, err, exc_info=True)
                await session.rollback()
                raise

    return await _with_retry(_do_update, run_id)


async def mark_sync_started(run_id: str) -> Optional[SyncOperation]:
    """
    Mark a sync operation as in progress.

    Args:
        run_id: The operation identifier.

    Returns:
        Updated record or None.
    """
    return await update_sync_operation(
        run_id,
        status=SyncStatus.IN_PROGRESS,
        started_at=_utc_now(),
    )


async def mark_sync_completed(
    run_id: str,
    records_downloaded: int = 0,
    records_uploaded: int = 0,
    bytes_downloaded: int = 0,
    bytes_uploaded: int = 0,
    dataset_sync_hashes: Optional[dict[str, Any]] = None,
) -> Optional[SyncOperation]:
    """
    Mark a sync operation as successfully completed.

    Args:
        run_id: The operation identifier.
        records_downloaded: Final download count.
        records_uploaded: Final upload count.
        bytes_downloaded: Total bytes downloaded.
        bytes_uploaded: Total bytes uploaded.
        dataset_sync_hashes: Final hash tracking data.

    Returns:
        Updated record or None.
    """
    return await update_sync_operation(
        run_id,
        status=SyncStatus.COMPLETED,
        progress_percentage=100,
        records_downloaded=records_downloaded,
        records_uploaded=records_uploaded,
        bytes_downloaded=bytes_downloaded,
        bytes_uploaded=bytes_uploaded,
        dataset_sync_hashes=dataset_sync_hashes,
        completed_at=_utc_now(),
    )


async def mark_sync_failed(run_id: str, error_message: str) -> Optional[SyncOperation]:
    """
    Mark a sync operation as failed.

    Args:
        run_id: The operation identifier.
        error_message: Description of the failure.

    Returns:
        Updated record or None.
    """
    return await update_sync_operation(
        run_id,
        status=SyncStatus.FAILED,
        error_message=error_message,
        completed_at=_utc_now(),
    )
