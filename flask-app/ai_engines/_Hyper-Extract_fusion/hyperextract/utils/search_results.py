"""Normalize AutoType.search returns for CLI and MCP display.

``AutoType.search`` keeps its native shapes (list, ``(nodes, edges)``,
``(nodes, edges, community_context)``, or a mapping). Presentation layers
must not iterate a graph tuple as two opaque results.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

SearchKind = Literal["list", "graph", "mapping"]


def dump_search_value(item: Any) -> Any:
    """Recursively coerce Pydantic models (and nested containers) to dicts."""
    if hasattr(item, "model_dump"):
        return item.model_dump()
    if hasattr(item, "dict") and callable(item.dict) and not isinstance(item, dict):
        return item.dict()
    if isinstance(item, list):
        return [dump_search_value(child) for child in item]
    if isinstance(item, tuple):
        return [dump_search_value(child) for child in item]
    if isinstance(item, dict):
        return {key: dump_search_value(value) for key, value in item.items()}
    return item


@dataclass(frozen=True)
class SearchHits:
    """Display-ready search hits.

    ``kind``:
        * ``list`` — payload ``{"results": [...]}``
        * ``graph`` — payload ``{"nodes", "edges"}`` plus optional
          ``community_context`` (may be ``None``)
        * ``mapping`` — dumped mapping (e.g. cog_rag ``themes`` / ``entities``)
    """

    kind: SearchKind
    payload: dict[str, Any]

    @property
    def count(self) -> int:
        """Hit count: nodes+edges for graphs, not ``len(tuple)``."""
        if self.kind == "list":
            results = self.payload.get("results") or []
            return len(results) if isinstance(results, list) else 1
        if self.kind == "graph":
            nodes = self.payload.get("nodes") or []
            edges = self.payload.get("edges") or []
            return len(nodes) + len(edges)
        total = 0
        for value in self.payload.values():
            total += len(value) if isinstance(value, list) else 1
        return total


def coerce_search_results(results: Any) -> SearchHits:
    """Wrap an AutoType search return into :class:`SearchHits`."""
    if results is None:
        return SearchHits(kind="list", payload={"results": []})
    if isinstance(results, dict):
        return SearchHits(kind="mapping", payload=dump_search_value(results))
    if isinstance(results, tuple):
        nodes = dump_search_value(results[0] if len(results) >= 1 else [])
        edges = dump_search_value(results[1] if len(results) >= 2 else [])
        payload: dict[str, Any] = {"nodes": nodes, "edges": edges}
        if len(results) >= 3:
            payload["community_context"] = dump_search_value(results[2])
        return SearchHits(kind="graph", payload=payload)
    if isinstance(results, list):
        return SearchHits(kind="list", payload={"results": dump_search_value(results)})
    return SearchHits(kind="list", payload={"results": [dump_search_value(results)]})
