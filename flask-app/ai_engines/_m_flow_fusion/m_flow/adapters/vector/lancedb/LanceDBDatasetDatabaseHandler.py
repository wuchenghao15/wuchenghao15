"""
LanceDB dataset handler.
"""

from __future__ import annotations

import os
from uuid import UUID

from m_flow.adapters.dataset_database_handler import DatasetStoreHandlerInterface
from m_flow.adapters.vector import get_vectordb_config
from m_flow.adapters.vector.create_vector_engine import create_vector_engine
from m_flow.auth.models import DatasetStore, User
from m_flow.base_config import get_base_config

_HANDLER_KEY = "lancedb"
_DB_SUFFIX = ".lance.db"


class LanceDBDatasetStoreHandler(DatasetStoreHandlerInterface):
    """Provisions and removes LanceDB instances for datasets."""

    @classmethod
    async def create_dataset(cls, dataset_id: UUID | None, user: User | None) -> dict:
        """Build connection info for a new LanceDB instance."""
        vec_cfg = get_vectordb_config()
        root = get_base_config().system_root_directory

        if vec_cfg.vector_db_provider != _HANDLER_KEY:
            raise ValueError("Only LanceDB provider is supported by this handler")

        user_dir = os.path.join(root, "databases", str(user.id))
        name = f"{dataset_id}{_DB_SUFFIX}"

        return {
            "vector_database_provider": vec_cfg.vector_db_provider,
            "vector_database_url": os.path.join(user_dir, name),
            "vector_database_key": vec_cfg.vector_db_key,
            "vector_database_name": name,
            "vector_dataset_database_handler": _HANDLER_KEY,
        }

    @classmethod
    async def delete_dataset(cls, db_record: DatasetStore) -> None:
        """Wipe data from the dataset's vector store."""
        vec = create_vector_engine(
            vector_db_provider=db_record.vector_database_provider,
            vector_db_url=db_record.vector_database_url,
            vector_db_key=db_record.vector_database_key,
            vector_db_name=db_record.vector_database_name,
        )
        await vec.prune()
