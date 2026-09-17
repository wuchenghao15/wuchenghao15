"""KA-level adapters for GraphML, CSV, JSON-LD, and Cypher export.

CLI ``he export graphml/csv/jsonld/cypher`` and MCP ``export_graphml`` /
``export_csv`` / ``export_jsonld`` / ``export_cypher`` call these functions
so extractor
wiring and the graph-type check live in one place. Encoders stay pure
functions over node/edge models.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import resolve_export_file
from .csv_export import export_to_csv
from .cypher import export_to_cypher
from .graphml import export_to_graphml
from .jsonld import export_to_jsonld

GRAPH_TYPE_ERROR = (
    "Graph export (GraphML/CSV/JSON-LD/Cypher) is only supported for graph-type "
    "knowledge abstracts (graph, hypergraph, temporal/spatial graphs)."
)


class GraphTypeError(ValueError):
    """Raised when a non-graph KA is passed to a graph exporter."""


def is_hypergraph_ka(ka: Any) -> bool:
    """True for AutoHypergraph; temporal/spatial graphs are pairwise."""
    if type(ka).__name__ == "AutoHypergraph":
        return True
    meta = getattr(ka, "metadata", None)
    return isinstance(meta, dict) and meta.get("type") == "hypergraph"


def require_graph_ka(ka: Any) -> None:
    if hasattr(ka, "export_obsidian"):
        return
    raise GraphTypeError(GRAPH_TYPE_ERROR)


def export_ka_graphml(ka: Any, dest: str | Path, *, overwrite: bool = False) -> Path:
    """Export a loaded graph-family KA to GraphML."""
    require_graph_ka(ka)
    dest = resolve_export_file(dest, overwrite=overwrite)
    return export_to_graphml(
        ka.nodes,
        ka.edges,
        node_id_extractor=ka.node_key_extractor,
        incident_nodes_extractor=ka.nodes_in_edge_extractor,
        file_path=dest,
        edge_id_extractor=getattr(ka, "edge_key_extractor", None),
    )


def export_ka_csv(ka: Any, dest: str | Path, *, overwrite: bool = False) -> Path:
    """Export a loaded graph-family KA to CSV tables."""
    require_graph_ka(ka)
    return export_to_csv(
        ka.nodes,
        ka.edges,
        node_id_extractor=ka.node_key_extractor,
        incident_nodes_extractor=ka.nodes_in_edge_extractor,
        folder_path=dest,
        edge_id_extractor=getattr(ka, "edge_key_extractor", None),
        hypergraph=is_hypergraph_ka(ka),
        overwrite=overwrite,
    )


def export_ka_cypher(ka: Any, dest: str | Path, *, overwrite: bool = False) -> Path:
    """Export a loaded graph-family KA to a Cypher MERGE script."""
    require_graph_ka(ka)
    dest = resolve_export_file(dest, overwrite=overwrite)
    return export_to_cypher(
        ka.nodes,
        ka.edges,
        node_id_extractor=ka.node_key_extractor,
        incident_nodes_extractor=ka.nodes_in_edge_extractor,
        file_path=dest,
        edge_id_extractor=getattr(ka, "edge_key_extractor", None),
    )


def export_ka_jsonld(ka: Any, dest: str | Path, *, overwrite: bool = False) -> Path:
    """Export a loaded graph-family KA to JSON-LD."""
    require_graph_ka(ka)
    dest = resolve_export_file(dest, overwrite=overwrite)
    return export_to_jsonld(
        ka.nodes,
        ka.edges,
        node_id_extractor=ka.node_key_extractor,
        incident_nodes_extractor=ka.nodes_in_edge_extractor,
        file_path=dest,
        edge_id_extractor=getattr(ka, "edge_key_extractor", None),
    )
