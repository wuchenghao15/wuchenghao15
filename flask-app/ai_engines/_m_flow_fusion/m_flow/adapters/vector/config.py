"""
Vector store configuration management.

Handles connection settings for various vector databases
including LanceDB, PGVector, ChromaDB, and others.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import pydantic
from pydantic_settings import BaseSettings
from m_flow.config.env_compat import MflowSettings, SettingsConfigDict

from m_flow.base_config import get_base_config
from m_flow.root_dir import ensure_absolute_path


_DEFAULT_PROVIDER = "lancedb"
_DEFAULT_PORT = 1234


class VectorConfig(MflowSettings):
    """Vector database connection parameters."""

    vector_db_url: str = ""
    vector_db_port: int = _DEFAULT_PORT
    vector_db_name: str = ""
    vector_db_key: str = ""
    vector_db_provider: str = _DEFAULT_PROVIDER
    vector_dataset_database_handler: str = _DEFAULT_PROVIDER

    model_config = SettingsConfigDict(env_prefix="MFLOW_", env_file=".env", extra="allow")

    @pydantic.model_validator(mode="after")
    def validate_paths(self):
        url = self.vector_db_url

        # Existing local path -> make absolute
        if url and Path(url).exists():
            self.vector_db_url = ensure_absolute_path(url)
        # Empty -> default LanceDB location
        elif not url:
            base = get_base_config()
            self.vector_db_url = os.path.join(base.system_root_directory, "databases", "m_flow.lancedb")

        return self

    def to_dict(self) -> dict:
        return {
            k: getattr(self, k)
            for k in [
                "vector_db_url",
                "vector_db_port",
                "vector_db_name",
                "vector_db_key",
                "vector_db_provider",
                "vector_dataset_database_handler",
            ]
        }


@lru_cache
def get_vectordb_config() -> VectorConfig:
    return VectorConfig()


def get_vectordb_context_config() -> dict:
    """Retrieve config from context or singleton."""
    from m_flow.context_global_variables import vector_db_config

    ctx = vector_db_config.get()
    return ctx if ctx else get_vectordb_config().to_dict()
