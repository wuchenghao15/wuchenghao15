"""
Global context variables for multi-tenant database isolation.

Provides coroutine-safe ``ContextVar`` slots that let M-flow maintain
per-request database configurations when running behind an async server.
"""

from __future__ import annotations

import os
from contextvars import ContextVar
from typing import Union
from uuid import UUID

from m_flow.base_config import get_base_config
from m_flow.adapters.vector.config import get_vectordb_config
from m_flow.adapters.graph.config import get_graph_config
from m_flow.adapters.utils import (
    get_or_create_dataset_database,
    resolve_dataset_database_connection_info,
)
from m_flow.shared.files.storage.config import file_storage_config
from m_flow.auth.methods import get_user

# ── Per-request context slots ────────────────────────────────────────
_vector_cfg: ContextVar = ContextVar("_vector_cfg", default=None)
_graph_cfg: ContextVar = ContextVar("_graph_cfg", default=None)
_active_user: ContextVar = ContextVar("_active_user", default=None)
# Dataset ID for Episode Routing isolation (works regardless of ENABLE_BACKEND_ACCESS_CONTROL)
_dataset_id: ContextVar = ContextVar("_dataset_id", default=None)

# Public aliases (many modules import these names directly)
vector_db_config = _vector_cfg
graph_db_config = _graph_cfg
session_user = _active_user
current_dataset_id = _dataset_id


# ── Helpers ──────────────────────────────────────────────────────────

_ACL_ENV_KEY = "ENABLE_BACKEND_ACCESS_CONTROL"


async def set_session_user_context_variable(user) -> None:
    """Store the authenticated user in the current async context."""
    _active_user.set(user)


def _require_handler_registered(
    handler_name: str,
    kind: str,
    registry: dict,
) -> None:
    """Raise ``EnvironmentError`` when *handler_name* is absent from *registry*."""
    if handler_name in registry:
        return
    raise EnvironmentError(
        f"The {kind} dataset-database handler '{handler_name}' is not recognised. "
        f"Supported handlers: {list(registry)}. "
        f"Set {_ACL_ENV_KEY}=false to disable access-control mode."
    )


def _require_handler_matches_provider(
    handler_name: str,
    provider: str,
    kind: str,
    registry: dict,
) -> None:
    """Raise when the handler's expected provider differs from the configured one."""
    expected = registry[handler_name]["handler_provider"]
    if expected == provider:
        return
    raise EnvironmentError(
        f"Mismatch: the {kind} handler '{handler_name}' expects provider "
        f"'{expected}' but '{provider}' is configured. "
        f"Set {_ACL_ENV_KEY}=false to disable access-control mode."
    )


# ── Public API ───────────────────────────────────────────────────────


def multi_user_support_possible() -> bool:
    """Return *True* when both graph and vector backends support dataset
    isolation, otherwise raise ``EnvironmentError`` with guidance."""
    from m_flow.adapters.dataset_database_handler import (
        supported_dataset_database_handlers as _handlers,
    )

    g_cfg = get_graph_config()
    v_cfg = get_vectordb_config()

    for name, kind in (
        (g_cfg.graph_dataset_database_handler, "graph"),
        (v_cfg.vector_dataset_database_handler, "vector"),
    ):
        _require_handler_registered(name, kind, _handlers)

    _require_handler_matches_provider(
        g_cfg.graph_dataset_database_handler,
        g_cfg.graph_database_provider,
        "graph",
        _handlers,
    )
    _require_handler_matches_provider(
        v_cfg.vector_dataset_database_handler,
        v_cfg.vector_db_provider,
        "vector",
        _handlers,
    )
    return True


def backend_access_control_enabled() -> bool:
    """Determine whether per-dataset database isolation is active.

    * env unset  → auto-detect from DB support
    * ``"true"`` → verify DB support (raise on failure)
    * anything else → disabled
    """
    raw = os.environ.get(_ACL_ENV_KEY)
    if raw is None or raw.strip().lower() == "true":
        return multi_user_support_possible()
    return False


async def set_db_context(
    dataset: Union[str, UUID],
    user_id: UUID,
) -> None:
    """Populate context slots with dataset-specific DB connection details.

    Every isolated dataset gets its own graph / vector database when
    access-control is on.  This resolver writes the three ``ContextVar``
    slots so downstream code transparently connects to the right DB.

    Parameters
    ----------
    dataset:
        Dataset name or UUID.
    user_id:
        Owner of the dataset.
    """
    if not backend_access_control_enabled():
        return

    owner = await get_user(user_id)
    ds_db = await get_or_create_dataset_database(dataset, owner)
    ds_db = await resolve_dataset_database_connection_info(ds_db)

    cfg = get_base_config()
    tenant_root = os.path.join(
        cfg.data_root_directory,
        str(owner.tenant_id or owner.id),
    )
    db_dir = os.path.join(cfg.system_root_directory, "databases", str(owner.id))

    _vector_cfg.set(
        {
            "vector_db_provider": ds_db.vector_database_provider,
            "vector_db_url": ds_db.vector_database_url,
            "vector_db_key": ds_db.vector_database_key,
            "vector_db_name": ds_db.vector_database_name,
        }
    )

    conn_info = ds_db.graph_database_connection_info
    _graph_cfg.set(
        {
            "graph_database_provider": ds_db.graph_database_provider,
            "graph_database_url": ds_db.graph_database_url,
            "graph_database_name": ds_db.graph_database_name,
            "graph_database_key": ds_db.graph_database_key,
            "graph_file_path": os.path.join(db_dir, ds_db.graph_database_name),
            "graph_database_username": conn_info.get("graph_database_username", ""),
            "graph_database_password": conn_info.get("graph_database_password", ""),
            "graph_dataset_database_handler": "",
            "graph_database_port": "",
        }
    )

    file_storage_config.set({"data_root_directory": tenant_root})
