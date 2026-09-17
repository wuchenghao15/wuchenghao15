"""
Live configuration snapshot retrieval.

This module provides a unified interface for collecting the current
configuration state of all M-flow adapters (LLM, vector DB, graph DB,
and relational DB).
"""

from __future__ import annotations

from typing import TypedDict

from m_flow.adapters.graph import get_graph_config
from m_flow.adapters.relational.config import get_relational_config
from m_flow.adapters.vector import get_vectordb_config
from m_flow.llm import get_llm_config


class LLMSettings(TypedDict):
    """LLM adapter configuration snapshot."""

    model: str
    provider: str


class VectorDBSettings(TypedDict):
    """Vector database adapter configuration snapshot."""

    url: str
    provider: str


class GraphDBSettings(TypedDict):
    """Graph database adapter configuration snapshot."""

    url: str
    provider: str


class RelationalSettings(TypedDict):
    """Relational database adapter configuration snapshot."""

    url: str
    provider: str


class SettingsDict(TypedDict):
    """Aggregated settings for all M-flow adapters."""

    llm: LLMSettings
    graph: GraphDBSettings
    vector: VectorDBSettings
    relational: RelationalSettings


def _build_relational_url(config) -> str:
    """
    Construct a connection URL string from relational config.

    Args:
        config: Relational database configuration object.

    Returns:
        Connection URL string (host:port or path/name format).
    """
    if hasattr(config, "db_host") and config.db_host:
        return f"{config.db_host}:{config.db_port}"
    return f"{config.db_path}/{config.db_name}"


def get_current_settings() -> SettingsDict:
    """
    Retrieve a snapshot of all active adapter configurations.

    Collects the current state of LLM, graph database, vector database,
    and relational database configurations into a single typed dictionary.

    Returns:
        SettingsDict containing the live configuration of each adapter.

    Example:
        >>> settings = get_current_settings()
        >>> print(settings["llm"]["provider"])
        'openai'
    """
    llm_cfg = get_llm_config()
    graph_cfg = get_graph_config()
    vector_cfg = get_vectordb_config()
    relational_cfg = get_relational_config()

    graph_url = graph_cfg.graph_database_url or graph_cfg.graph_file_path

    return {
        "llm": {
            "provider": llm_cfg.llm_provider,
            "model": llm_cfg.llm_model,
        },
        "graph": {
            "provider": graph_cfg.graph_database_provider,
            "url": graph_url,
        },
        "vector": {
            "provider": vector_cfg.vector_db_provider,
            "url": vector_cfg.vector_db_url,
        },
        "relational": {
            "provider": relational_cfg.db_provider,
            "url": _build_relational_url(relational_cfg),
        },
    }
