"""Graph dataset database handler lookup."""

from __future__ import annotations

from typing import Any, Dict

from m_flow.auth.models.DatasetStore import DatasetStore


def get_graph_dataset_database_handler(db_cfg: DatasetStore) -> Dict[str, Any]:
    """Return handler config for the dataset's graph database."""
    from m_flow.adapters.dataset_database_handler.supported_dataset_database_handlers import (
        supported_dataset_database_handlers,
    )

    return supported_dataset_database_handlers[db_cfg.graph_dataset_database_handler]
