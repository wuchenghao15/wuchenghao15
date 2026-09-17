# m_flow/api/v1/maintenance/orphans.py
"""
Orphan Record Detection and Cleanup APIs.

Provides utilities to detect and fix orphan records in the relational
database - records that point to non-existent files in storage.

This can happen when:
- `prune_data()` is called without `prune_system(metadata=True)`
- File storage is manually cleared
- Interrupted ingestion operations
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select

from m_flow.adapters.relational import get_db_adapter
from m_flow.data.models import Data
from m_flow.shared.files.storage import get_file_storage, get_storage_config
from m_flow.shared.logging_utils import get_logger

_logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclass
class OrphanReport:
    """
    Report of orphan records found in the relational database.

    Attributes
    ----------
    total_checked : int
        Total number of Data records examined.
    orphan_count : int
        Number of records pointing to non-existent files.
    orphan_ids : List[str]
        UUIDs of orphan records (limited to first 100).
    orphan_locations : List[str]
        File paths that don't exist (limited to first 10).
    storage_types_checked : List[str]
        Storage types examined ('local', 's3', or both).
    """

    total_checked: int = 0
    orphan_count: int = 0
    orphan_ids: List[str] = field(default_factory=list)
    orphan_locations: List[str] = field(default_factory=list)
    storage_types_checked: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "total_checked": self.total_checked,
            "orphan_count": self.orphan_count,
            "orphan_ids": self.orphan_ids,
            "orphan_locations": self.orphan_locations,
            "storage_types_checked": self.storage_types_checked,
        }


@dataclass
class FixResult:
    """
    Result of orphan record fix operation.

    Attributes
    ----------
    orphan_count : int
        Number of orphan records found.
    fixed_count : int
        Number of records successfully deleted.
    fixed_ids : List[str]
        UUIDs of deleted records.
    warning : Optional[str]
        Warning message about limitations.
    """

    orphan_count: int = 0
    fixed_count: int = 0
    fixed_ids: List[str] = field(default_factory=list)
    warning: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        result = {
            "orphan_count": self.orphan_count,
            "fixed_count": self.fixed_count,
            "fixed_ids": self.fixed_ids,
        }
        if self.warning:
            result["warning"] = self.warning
        return result


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


async def _check_file_exists(
    storage_path: str,
    file_location: str,
) -> bool:
    """
    Check if a file exists in storage.

    Handles both local and S3 storage transparently.

    Args:
        storage_path: Root storage path.
        file_location: Relative or absolute path to the file.

    Returns:
        True if file exists, False otherwise.
    """
    try:
        storage = get_file_storage(storage_path)

        # Normalize path
        if file_location.startswith(storage_path):
            # Already absolute path within storage
            relative_path = file_location[len(storage_path) :].lstrip("/\\")
        elif file_location.startswith("s3://"):
            # S3 path - use as-is
            relative_path = file_location
        else:
            # Relative path
            relative_path = file_location

        return await storage.file_exists(relative_path)
    except Exception as e:
        _logger.debug(f"Error checking file existence: {e}")
        return False


async def _get_all_data_records() -> List[Data]:
    """
    Retrieve all Data records from the relational database.

    Returns:
        List of Data model instances.
    """
    engine = get_db_adapter()

    try:
        async with engine.get_async_session() as session:
            result = await session.execute(select(Data))
            return list(result.scalars().all())
    except Exception as e:
        _logger.warning(f"Failed to query Data records: {e}")
        return []


async def _delete_data_records(record_ids: List[UUID]) -> int:
    """
    Delete Data records by their IDs.

    Args:
        record_ids: UUIDs of records to delete.

    Returns:
        Number of records successfully deleted.
    """
    if not record_ids:
        return 0

    engine = get_db_adapter()
    deleted_count = 0

    async with engine.get_async_session() as session:
        for record_id in record_ids:
            try:
                result = await session.execute(select(Data).where(Data.id == record_id))
                record = result.scalar_one_or_none()

                if record:
                    await session.delete(record)
                    deleted_count += 1
            except Exception as e:
                _logger.warning(f"Failed to delete record {record_id}: {e}")

        await session.commit()

    return deleted_count


# ---------------------------------------------------------------------------
# Public APIs
# ---------------------------------------------------------------------------


async def check_orphans(
    *,
    storage_type: Optional[str] = None,
    limit: Optional[int] = None,
) -> OrphanReport:
    """
    Check for orphan records in the relational database.

    Orphan records are Data entries whose associated files no longer
    exist in storage. This commonly occurs after `prune_data()` is
    called without `prune_system(metadata=True)`.

    Args:
        storage_type: Filter by storage type ('local' or 's3').
                     If None, checks all records.
        limit: Maximum number of records to check. If None, checks all.

    Returns:
        OrphanReport with details about found orphans.

    Example:
        >>> import m_flow
        >>> report = await m_flow.maintenance.check_orphans()
        >>> if report.orphan_count > 0:
        ...     print(f"Found {report.orphan_count} orphan records")
        ...     # Fix them
        ...     result = await m_flow.maintenance.fix_orphans()

    Note:
        This is a read-only operation and does not modify any data.
    """
    _logger.info("[check_orphans] Starting orphan record scan...")

    # Get storage configuration
    cfg = get_storage_config()
    storage_path = cfg.get("data_root_directory", ".data_storage")

    # Determine storage types to check
    storage_types_checked = []
    if storage_type:
        storage_types_checked = [storage_type]
    else:
        # Auto-detect based on storage path
        if storage_path.startswith("s3://"):
            storage_types_checked = ["s3"]
        else:
            storage_types_checked = ["local"]

    # Get all data records
    all_records = await _get_all_data_records()

    if limit and len(all_records) > limit:
        all_records = all_records[:limit]

    _logger.info(f"[check_orphans] Checking {len(all_records)} Data records...")

    report = OrphanReport(
        total_checked=len(all_records),
        storage_types_checked=storage_types_checked,
    )

    if not all_records:
        _logger.info("[check_orphans] No Data records found")
        return report

    # Check each record's file existence
    orphan_ids: List[str] = []
    orphan_locations: List[str] = []

    for record in all_records:
        file_location = record.processed_path

        if not file_location:
            # No file location - treat as orphan
            orphan_ids.append(str(record.id))
            continue

        # Filter by storage type if specified
        is_s3 = file_location.startswith("s3://")
        if storage_type == "local" and is_s3:
            continue
        if storage_type == "s3" and not is_s3:
            continue

        # Check file existence
        exists = await _check_file_exists(storage_path, file_location)

        if not exists:
            orphan_ids.append(str(record.id))
            if len(orphan_locations) < 10:  # Limit sample locations
                orphan_locations.append(file_location)

    report.orphan_count = len(orphan_ids)
    report.orphan_ids = orphan_ids[:100]  # Limit IDs in report
    report.orphan_locations = orphan_locations

    _logger.info(f"[check_orphans] Scan complete: {report.orphan_count}/{report.total_checked} orphan records found")

    if report.orphan_count > 0:
        _logger.warning(
            f"[check_orphans] Found {report.orphan_count} orphan records. "
            "Run `await m_flow.maintenance.fix_orphans()` to clean them up."
        )

    return report


async def fix_orphans(
    *,
    dry_run: bool = False,
    storage_type: Optional[str] = None,
) -> FixResult:
    """
    Delete orphan records from the relational database.

    This cleans up Data records whose associated files no longer
    exist in storage, preventing FileNotFoundError during subsequent
    ingestion operations.

    Args:
        dry_run: If True, report what would be deleted without
                actually deleting. Default is False.
        storage_type: Filter by storage type ('local' or 's3').
                     If None, fixes all orphan records.

    Returns:
        FixResult with details about the cleanup operation.

    Example:
        >>> import m_flow
        >>> # Preview what will be deleted
        >>> result = await m_flow.maintenance.fix_orphans(dry_run=True)
        >>> print(f"Would delete {result.orphan_count} records")

        >>> # Actually delete
        >>> result = await m_flow.maintenance.fix_orphans()
        >>> print(f"Deleted {result.fixed_count} orphan records")

    Warnings
    --------
    - This operation deletes records from the relational database.
    - Graph and vector database entries may still reference deleted Data IDs.
    - For complete cleanup, use `await m_flow.prune.all()` instead.

    Note:
        This is a P1 implementation that only cleans the relational database.
        Graph/vector database cleanup requires manual intervention or
        full system prune.
    """
    mode_str = "[DRY RUN] " if dry_run else ""
    _logger.info(f"[fix_orphans] {mode_str}Starting orphan cleanup...")

    # First, identify orphans
    report = await check_orphans(storage_type=storage_type)

    result = FixResult(
        orphan_count=report.orphan_count,
        warning=(
            "P1 limitation: Only relational database records are deleted. "
            "Graph/vector DB may still have references. "
            "For complete cleanup, use `prune.all()`."
        ),
    )

    if report.orphan_count == 0:
        _logger.info("[fix_orphans] No orphan records to fix")
        return result

    if dry_run:
        _logger.info(
            f"[fix_orphans] [DRY RUN] Would delete {report.orphan_count} orphan records: {report.orphan_ids[:5]}..."
        )
        result.fixed_ids = report.orphan_ids
        return result

    # Convert string IDs to UUIDs for deletion
    record_ids = [UUID(id_str) for id_str in report.orphan_ids]

    # Delete orphan records
    deleted_count = await _delete_data_records(record_ids)

    result.fixed_count = deleted_count
    result.fixed_ids = report.orphan_ids[:deleted_count]

    _logger.info(f"[fix_orphans] Cleanup complete: deleted {deleted_count}/{report.orphan_count} orphan records")

    return result
