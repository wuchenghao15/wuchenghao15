"""
Sync operation tracking for M-flow datasets.

This package provides infrastructure for tracking background
synchronization operations, including:

- SyncOperation model for database persistence
- Status tracking (STARTED, IN_PROGRESS, COMPLETED, FAILED)
- Methods for creating, updating, and querying sync records

Usage
-----
>>> from m_flow.shared.sync.methods import create_sync_operation
>>> op = await create_sync_operation(
...     run_id="sync-123",
...     dataset_ids=[uuid],
...     dataset_names=["my_dataset"],
...     user_id=user_uuid,
... )
"""
