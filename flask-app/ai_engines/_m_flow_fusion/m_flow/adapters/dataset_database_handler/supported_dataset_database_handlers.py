"""Registry of supported dataset database handlers."""

from __future__ import annotations

from typing import Any, Dict

from m_flow.adapters.graph.kuzu.KuzuDatasetDatabaseHandler import (
    KuzuDatasetStoreHandler,
)
from m_flow.adapters.graph.neo4j_driver.Neo4jAuraDevDatasetDatabaseHandler import (
    Neo4jAuraDevDatasetStoreHandler,
)
from m_flow.adapters.vector.lancedb.LanceDBDatasetDatabaseHandler import (
    LanceDBDatasetStoreHandler,
)

supported_dataset_database_handlers: Dict[str, Dict[str, Any]] = {
    "neo4j_aura_dev": {
        "handler_instance": Neo4jAuraDevDatasetStoreHandler,
        "handler_provider": "neo4j",
    },
    "lancedb": {
        "handler_instance": LanceDBDatasetStoreHandler,
        "handler_provider": "lancedb",
    },
    "kuzu": {
        "handler_instance": KuzuDatasetStoreHandler,
        "handler_provider": "kuzu",
    },
}
