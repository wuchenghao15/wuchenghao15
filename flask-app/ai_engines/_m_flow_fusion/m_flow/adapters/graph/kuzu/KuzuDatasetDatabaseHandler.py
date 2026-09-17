"""
Kuzu database handler for datasets.

Provisions and deletes Kuzu graph instances per dataset.
"""

from __future__ import annotations

import os
from typing import Optional
from uuid import UUID

from m_flow.adapters.dataset_database_handler import DatasetStoreHandlerInterface
from m_flow.adapters.graph.get_graph_adapter import _build_adapter
from m_flow.auth.models import DatasetStore, User
from m_flow.base_config import get_base_config


class KuzuDatasetStoreHandler(DatasetStoreHandlerInterface):
    """Manages Kuzu graph database lifecycle."""

    @classmethod
    async def create_dataset(cls, dataset_id: Optional[UUID], user: Optional[User]) -> dict:
        """
        Provision Kuzu database for dataset.

        Args:
            dataset_id: Dataset UUID.
            user: Owning user.

        Returns:
            Connection configuration dict.
        """
        from m_flow.adapters.graph.config import get_graph_config

        cfg = get_graph_config()

        if cfg.graph_database_provider != "kuzu":
            raise ValueError("Handler requires Kuzu provider")

        return {
            "graph_database_name": f"{dataset_id}.pkl",
            "graph_database_url": cfg.graph_database_url,
            "graph_database_provider": cfg.graph_database_provider,
            "graph_database_key": cfg.graph_database_key,
            "graph_dataset_database_handler": "kuzu",
            "graph_database_connection_info": {
                "graph_database_username": cfg.graph_database_username,
                "graph_database_password": cfg.graph_database_password,
            },
        }

    @classmethod
    async def delete_dataset(cls, dataset_database: DatasetStore):
        """
        Remove Kuzu database for dataset.

        Args:
            dataset_database: Database record to delete.
        """
        base = get_base_config()
        db_dir = os.path.join(
            base.system_root_directory,
            "databases",
            str(dataset_database.owner_id),
        )
        graph_path = os.path.join(db_dir, dataset_database.graph_database_name)

        conn_info = dataset_database.graph_database_connection_info or {}

        engine = _build_adapter(
            graph_database_provider=dataset_database.graph_database_provider,
            graph_database_url=dataset_database.graph_database_url,
            graph_database_name=dataset_database.graph_database_name,
            graph_database_key=dataset_database.graph_database_key,
            graph_file_path=graph_path,
            graph_database_username=conn_info.get("graph_database_username", ""),
            graph_database_password=conn_info.get("graph_database_password", ""),
            graph_dataset_database_handler="",
            graph_database_port="",
        )

        await engine.delete_graph()
