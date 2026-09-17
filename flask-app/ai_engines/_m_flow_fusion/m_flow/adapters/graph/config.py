"""
M-Flow graph-database configuration.

Provides a single-source-of-truth ``GraphConfig`` model for all graph
backend parameters and exposes factory helpers that respect both the
global defaults and per-request context overrides used during concurrent
pipeline execution.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

import pydantic
from pydantic import Field
from pydantic_settings import BaseSettings
from m_flow.config.env_compat import MflowSettings, SettingsConfigDict

from m_flow.base_config import get_base_config
from m_flow.root_dir import ensure_absolute_path
from m_flow.shared.data_models import ExtractedGraph

_PROVIDER_KUZU = "kuzu"
_FALLBACK_PORT = 123


class GraphConfig(MflowSettings):
    """Unified settings for the M-Flow graph storage backend.

    Values are loaded from environment variables / ``.env`` with the
    standard ``pydantic-settings`` resolution chain.  A post-init
    validator ensures file-system paths are fully resolved before any
    downstream code accesses them.
    """

    graph_database_provider: str = Field(_PROVIDER_KUZU, alias="GRAPH_DATABASE_PROVIDER")
    graph_database_url: str = ""
    graph_database_name: str = ""
    graph_database_username: str = ""
    graph_database_password: str = ""
    graph_database_port: int = _FALLBACK_PORT
    graph_database_key: str = ""
    graph_file_path: str = ""
    graph_filename: str = ""
    graph_model: type[Any] = ExtractedGraph
    graph_topology: type[Any] = ExtractedGraph
    graph_dataset_database_handler: str = _PROVIDER_KUZU

    model_config = SettingsConfigDict(
        env_prefix="MFLOW_",
        env_file=".env",
        extra="allow",
        populate_by_name=True,
    )

    @pydantic.model_validator(mode="after")
    def _init_paths(self) -> GraphConfig:
        """Resolve graph storage paths after all fields are populated."""
        provider_tag = self.graph_database_provider.lower()
        root_cfg = get_base_config()

        if not self.graph_filename:
            self.graph_filename = f"m_flow_graph_{provider_tag}"

        if self.graph_file_path:
            combined = os.path.join(self.graph_file_path, self.graph_filename)
            self.graph_file_path = ensure_absolute_path(combined)
        else:
            storage_dir = os.path.join(root_cfg.system_root_directory, "databases")
            self.graph_file_path = os.path.join(storage_dir, self.graph_filename)

        return self

    def to_dict(self) -> dict[str, Any]:
        """Serialise every field (including non-hashable ones) to a dict."""
        return {
            "graph_filename": self.graph_filename,
            "graph_database_provider": self.graph_database_provider,
            "graph_database_url": self.graph_database_url,
            "graph_database_name": self.graph_database_name,
            "graph_database_username": self.graph_database_username,
            "graph_database_password": self.graph_database_password,
            "graph_database_port": self.graph_database_port,
            "graph_database_key": self.graph_database_key,
            "graph_file_path": self.graph_file_path,
            "graph_model": self.graph_model,
            "graph_topology": self.graph_topology,
            "model_config": self.model_config,
            "graph_dataset_database_handler": self.graph_dataset_database_handler,
        }

    def to_hashable_dict(self) -> dict[str, Any]:
        """Produce a cache-key-safe subset (excludes unhashable types)."""
        return {
            "graph_database_provider": self.graph_database_provider,
            "graph_database_url": self.graph_database_url,
            "graph_database_name": self.graph_database_name,
            "graph_database_username": self.graph_database_username,
            "graph_database_password": self.graph_database_password,
            "graph_database_port": self.graph_database_port,
            "graph_database_key": self.graph_database_key,
            "graph_file_path": self.graph_file_path,
            "graph_dataset_database_handler": self.graph_dataset_database_handler,
        }


@lru_cache(maxsize=1)
def get_graph_config() -> GraphConfig:
    """Return the process-level ``GraphConfig`` singleton."""
    return GraphConfig()


def get_graph_context_config() -> dict[str, Any]:
    """Retrieve graph settings, preferring any async-context override.

    During concurrent pipeline runs each task may carry its own graph
    configuration via a context variable.  This helper checks for such
    an override first and falls back to the global singleton otherwise.
    """
    from m_flow.context_global_variables import graph_db_config

    override = graph_db_config.get()
    if override:
        return override
    return get_graph_config().to_hashable_dict()
