"""
Sync operation tracking model.

Provides SQLAlchemy ORM model for persisting and querying the status
of background synchronization tasks in the M-flow system.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional
from uuid import uuid4

from sqlalchemy import Column, DateTime, Integer, JSON, Text
from sqlalchemy import UUID as SA_UUID
from sqlalchemy import Enum as SA_Enum

from m_flow.adapters.relational import Base

if TYPE_CHECKING:
    pass


class SyncStatus(str, Enum):
    """
    Lifecycle states for a sync operation.

    Values:
        STARTED: Operation has been created but not yet processing.
        IN_PROGRESS: Actively downloading/uploading data.
        COMPLETED: Successfully finished all transfers.
        FAILED: Terminated due to an error.
        CANCELLED: Manually aborted by user or system.
    """

    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


def _utc_now() -> datetime:
    """Return current UTC timestamp."""
    return datetime.now(tz=timezone.utc)


class SyncOperation(Base):
    """
    ORM model for tracking synchronization operations.

    Captures metadata, progress metrics, and timing information for
    background sync tasks that transfer data between local storage
    and cloud services.

    Table: sync_operations
    """

    __tablename__ = "sync_operations"

    # === Identity ===
    id = Column(
        SA_UUID,
        primary_key=True,
        default=uuid4,
        doc="Primary key (UUID)",
    )
    run_id = Column(
        Text,
        unique=True,
        index=True,
        doc="User-facing operation identifier",
    )
    user_id = Column(
        SA_UUID,
        index=True,
        doc="Owner of this operation",
    )

    # === Status ===
    status = Column(
        SA_Enum(SyncStatus),
        default=SyncStatus.STARTED,
        doc="Current lifecycle state",
    )
    progress_percentage = Column(
        Integer,
        default=0,
        doc="Completion percentage (0-100)",
    )
    error_message = Column(
        Text,
        nullable=True,
        doc="Error details if status is FAILED",
    )
    retry_count = Column(
        Integer,
        default=0,
        doc="Number of retry attempts made",
    )

    # === Dataset info ===
    dataset_ids = Column(JSON, doc="List of dataset UUIDs")
    dataset_names = Column(JSON, doc="List of dataset display names")
    dataset_sync_hashes = Column(
        JSON,
        doc="Per-dataset content hash tracking",
    )

    # === Timestamps ===
    created_at = Column(
        DateTime(timezone=True),
        default=_utc_now,
        doc="When operation was created",
    )
    started_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="When processing began",
    )
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="When operation finished",
    )

    # === Counters ===
    total_records_to_sync = Column(Integer, nullable=True)
    total_records_to_download = Column(Integer, nullable=True)
    total_records_to_upload = Column(Integer, nullable=True)
    records_downloaded = Column(Integer, default=0)
    records_uploaded = Column(Integer, default=0)
    bytes_downloaded = Column(Integer, default=0)
    bytes_uploaded = Column(Integer, default=0)

    # === Helper methods ===

    def compute_duration(self) -> Optional[float]:
        """
        Calculate elapsed time in seconds.

        Returns:
            Seconds from created_at to completed_at (or now),
            or None if created_at is not set.
        """
        if self.created_at is None:
            return None
        end = self.completed_at or _utc_now()
        delta = end - self.created_at
        return delta.total_seconds()

    def to_progress_dict(self) -> dict[str, Any]:
        """
        Build a progress summary dictionary.

        Returns:
            Dictionary with status, progress, counters, and timing.
        """
        downloaded = self.records_downloaded or 0
        uploaded = self.records_uploaded or 0
        total = self.total_records_to_sync

        return {
            "status": self.status.value if self.status else None,
            "progress_percentage": self.progress_percentage or 0,
            "records_processed": f"{downloaded + uploaded}/{total or 'unknown'}",
            "records_downloaded": downloaded,
            "records_uploaded": uploaded,
            "bytes_transferred": (self.bytes_downloaded or 0) + (self.bytes_uploaded or 0),
            "bytes_downloaded": self.bytes_downloaded or 0,
            "bytes_uploaded": self.bytes_uploaded or 0,
            "duration_seconds": self.compute_duration(),
            "error_message": self.error_message,
            "dataset_sync_hashes": self.dataset_sync_hashes or {},
        }

    def collect_all_hashes(self) -> list[str]:
        """
        Gather all content hashes across datasets.

        Returns:
            Deduplicated list of content hashes from uploads and downloads.
        """
        hashes: set[str] = set()
        mapping = self.dataset_sync_hashes or {}

        for ops in mapping.values():
            if not isinstance(ops, dict):
                continue
            hashes.update(ops.get("uploaded", []))
            hashes.update(ops.get("downloaded", []))

        return list(hashes)

    def hashes_for_dataset(self, dataset_id: str) -> dict[str, list[str]]:
        """
        Get upload/download hashes for a specific dataset.

        Args:
            dataset_id: The dataset identifier to query.

        Returns:
            Dict with 'uploaded' and 'downloaded' hash lists.
        """
        mapping = self.dataset_sync_hashes or {}
        return mapping.get(dataset_id, {"uploaded": [], "downloaded": []})

    def contains_hash(
        self,
        content_hash: str,
        dataset_id: Optional[str] = None,
    ) -> bool:
        """
        Check if a content hash was part of this sync.

        Args:
            content_hash: The hash to look for.
            dataset_id: Optional dataset to scope the search.

        Returns:
            True if the hash was uploaded or downloaded.
        """
        if dataset_id is not None:
            ds_hashes = self.hashes_for_dataset(dataset_id)
            return content_hash in ds_hashes.get("uploaded", []) or content_hash in ds_hashes.get("downloaded", [])

        return content_hash in self.collect_all_hashes()
