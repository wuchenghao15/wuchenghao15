"""Async-context-aware configuration holder for the storage layer.

Provides a ContextVar that allows coroutine-scoped overrides of the
default file-storage settings without polluting the global state.
"""

from contextvars import ContextVar
from typing import Any

# Per-task storage configuration; when unset, callers fall back to the
# global base-config values retrieved at startup.
_ctx_storage_settings: ContextVar[Any | None] = ContextVar(
    "file_storage_config",
    default=None,
)

# Backward-compatible public name kept so existing imports keep working.
file_storage_config = _ctx_storage_settings
