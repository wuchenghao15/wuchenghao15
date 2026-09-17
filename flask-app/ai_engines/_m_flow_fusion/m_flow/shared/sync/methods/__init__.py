"""
Database operations for sync tracking.

Exposes functions to create, query, and update SyncOperation records.
All operations are async and work with the relational database backend.
"""

from __future__ import annotations


def __getattr__(name: str):
    """Lazy import to avoid circular dependencies."""
    if name == "create_sync_operation":
        from .create_sync_operation import create_sync_operation

        return create_sync_operation

    if name in (
        "get_sync_operation",
        "get_user_sync_operations",
        "get_running_sync_operations_for_user",
    ):
        import importlib

        mod = importlib.import_module(".get_sync_operation", __package__)
        return getattr(mod, name)

    if name in (
        "update_sync_operation",
        "mark_sync_started",
        "mark_sync_completed",
        "mark_sync_failed",
    ):
        import importlib

        mod = importlib.import_module(".update_sync_operation", __package__)
        return getattr(mod, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
