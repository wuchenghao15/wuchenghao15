"""Graph adapter registration utility."""

from __future__ import annotations

from typing import Any

from .supported_databases import supported_databases


def use_graph_adapter(name: str, adapter: Any) -> None:
    """Register a graph database adapter."""
    supported_databases[name] = adapter
