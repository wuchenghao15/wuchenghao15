"""
Pipeline run info queue management.

Provides in-memory async queues for streaming pipeline status updates.
"""

from __future__ import annotations

from asyncio import Queue
from typing import Optional
from uuid import UUID

from m_flow.pipeline.models import RunEvent

# Global registry of queues keyed by pipeline run ID
_queues: dict[str, Queue] = {}


def initialize_queue(run_id: UUID) -> Queue:
    """Create a new queue for the given pipeline run."""
    key = str(run_id)
    _queues[key] = Queue()
    return _queues[key]


def get_queue(run_id: UUID) -> Optional[Queue]:
    """
    Get queue for pipeline run, creating if needed.

    Args:
        run_id: Pipeline run identifier.

    Returns:
        Queue instance or None if not found.
    """
    key = str(run_id)
    if key not in _queues:
        initialize_queue(run_id)
    return _queues.get(key)


def remove_queue(run_id: UUID) -> None:
    """Remove and cleanup queue for completed run."""
    key = str(run_id)
    _queues.pop(key, None)


def push_to_queue(run_id: UUID, info: RunEvent) -> None:
    """Push status update to the run's queue."""
    q = get_queue(run_id)
    if q is not None:
        q.put_nowait(info)


def get_from_queue(run_id: UUID) -> Optional[RunEvent]:
    """
    Non-blocking pop from queue.

    Returns:
        RunEvent or None if queue empty.
    """
    q = get_queue(run_id)
    if q and not q.empty():
        return q.get_nowait()
    return None
