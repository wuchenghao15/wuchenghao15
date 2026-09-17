"""GraphML exporter for pairwise graphs and GraphML 1.0 hyperedges.

Produces a GraphML 1.0 document that Gephi, yEd, and other desktop tools
can open. Binary edges are written as ``<edge source target>``. Edges with
three or more endpoints are written as ``<hyperedge>`` with
``<endpoint node="..."/>`` children, in ``incident_nodes_extractor`` order.

Endpoint order is preserved: for pairwise edges, ``source`` is the first
incident node and ``target`` is the second. Endpoints are never sorted.
"""

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from hyperextract.utils.logging import get_logger

from .common import (
    default_edge_id,
    graphml_attr_type,
    graphml_attr_value,
    incident_ids,
    merge_graphml_type,
    resolve_nodes,
    scalar_fields,
    xml_escape,
)

logger = get_logger(__name__)

GRAPHML_NS = "http://graphml.graphdrawing.org/xmlns"

_ScalarFields = dict[str, str | int | float | bool]
_PairwiseRow = tuple[str, str, str, _ScalarFields]
_HyperedgeRow = tuple[str, list[str], _ScalarFields]


class GraphMLHypergraphError(ValueError):
    """Raised when GraphML export cannot encode an edge.

    N-ary edges are encoded as GraphML 1.0 ``<hyperedge>`` elements; this
    exception is kept for callers that still catch it.
    """


def export_to_graphml(
    nodes: Sequence[BaseModel],
    edges: Sequence[BaseModel],
    *,
    node_id_extractor: Callable[[Any], str],
    incident_nodes_extractor: Callable[[Any], Sequence[str]],
    file_path: str | Path,
    edge_id_extractor: Callable[[Any], str] | None = None,
) -> Path:
    """Export a graph to a GraphML file.

    Args:
        nodes: Node/entity models to export.
        edges: Edge models to export (pairwise or N-ary).
        node_id_extractor: Maps a node to its unique key (matches edge endpoints).
        incident_nodes_extractor: Maps an edge to incident node keys in order.
            Two endpoints become ``<edge source target>``; three or more
            become ``<hyperedge>`` with ``<endpoint>`` children.
        file_path: Destination ``.graphml`` file.
        edge_id_extractor: Optional edge -> GraphML id. Defaults to
            ``e0``, ``e1``, ...

    Returns:
        The written file :class:`~pathlib.Path`.

    Raises:
        IsADirectoryError: If ``file_path`` exists and is a directory.
    """
    dest = Path(file_path)
    if dest.exists() and dest.is_dir():
        raise IsADirectoryError(
            f"Destination '{dest}' is a directory; pass a GraphML file path."
        )
    dest.parent.mkdir(parents=True, exist_ok=True)

    by_id = resolve_nodes(nodes, node_id_extractor)

    node_keys: dict[str, str] = {}
    node_rows: list[tuple[str, _ScalarFields]] = []
    for node_id, node in by_id.items():
        fields = scalar_fields(node)
        for name, value in fields.items():
            node_keys[name] = merge_graphml_type(
                node_keys.get(name), graphml_attr_type(value)
            )
        node_rows.append((node_id, fields))

    pairwise: list[_PairwiseRow] = []
    hyperedges: list[_HyperedgeRow] = []
    edge_keys: dict[str, str] = {}
    hyperedge_keys: dict[str, str] = {}
    skipped = 0
    for index, edge in enumerate(edges):
        members = incident_ids(edge, incident_nodes_extractor)
        if members is None:
            skipped += 1
            continue
        if len(members) == 2:
            source, target = members[0], members[1]
            if source not in by_id or target not in by_id:
                skipped += 1
                logger.warning(
                    "export.graphml: skipping edge with missing endpoint "
                    "source=%s target=%s",
                    source,
                    target,
                )
                continue
            edge_id = default_edge_id(edge, index, edge_id_extractor)
            fields = scalar_fields(edge)
            for name, value in fields.items():
                edge_keys[name] = merge_graphml_type(
                    edge_keys.get(name), graphml_attr_type(value)
                )
            pairwise.append((edge_id, source, target, fields))
            continue
        if len(members) >= 3:
            missing = [member for member in members if member not in by_id]
            if missing:
                skipped += 1
                logger.warning(
                    "export.graphml: skipping hyperedge with missing endpoint(s) %s",
                    missing,
                )
                continue
            edge_id = default_edge_id(edge, index, edge_id_extractor)
            fields = scalar_fields(edge)
            for name, value in fields.items():
                hyperedge_keys[name] = merge_graphml_type(
                    hyperedge_keys.get(name), graphml_attr_type(value)
                )
            hyperedges.append((edge_id, members, fields))
            continue
        skipped += 1
        logger.warning(
            "export.graphml: skipping non-pairwise edge members=%s",
            members,
        )

    xml = _render_graphml(
        node_keys, edge_keys, hyperedge_keys, node_rows, pairwise, hyperedges
    )
    dest.write_text(xml, encoding="utf-8")

    logger.info(
        "graphml: exported nodes=%d edges=%d hyperedges=%d skipped_edges=%d path=%s",
        len(node_rows),
        len(pairwise),
        len(hyperedges),
        skipped,
        dest,
    )
    return dest


def _key_id(prefix: str, name: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in name)
    if not safe or safe[0].isdigit():
        safe = f"_{safe}"
    return f"{prefix}_{safe}"


def _render_graphml(
    node_keys: dict[str, str],
    edge_keys: dict[str, str],
    hyperedge_keys: dict[str, str],
    node_rows: list[tuple[str, _ScalarFields]],
    edges: list[_PairwiseRow],
    hyperedges: list[_HyperedgeRow],
) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<graphml xmlns="{GRAPHML_NS}">',
    ]
    node_key_ids: dict[str, str] = {}
    for name, attr_type in node_keys.items():
        kid = _key_id("n", name)
        node_key_ids[name] = kid
        lines.append(
            f'  <key id="{xml_escape(kid)}" for="node" '
            f'attr.name="{xml_escape(name)}" attr.type="{attr_type}"/>'
        )
    edge_key_ids: dict[str, str] = {}
    for name, attr_type in edge_keys.items():
        kid = _key_id("e", name)
        edge_key_ids[name] = kid
        lines.append(
            f'  <key id="{xml_escape(kid)}" for="edge" '
            f'attr.name="{xml_escape(name)}" attr.type="{attr_type}"/>'
        )
    hyperedge_key_ids: dict[str, str] = {}
    for name, attr_type in hyperedge_keys.items():
        kid = _key_id("h", name)
        hyperedge_key_ids[name] = kid
        lines.append(
            f'  <key id="{xml_escape(kid)}" for="hyperedge" '
            f'attr.name="{xml_escape(name)}" attr.type="{attr_type}"/>'
        )

    lines.append('  <graph id="G" edgedefault="directed">')
    for node_id, fields in node_rows:
        if fields:
            lines.append(f'    <node id="{xml_escape(node_id)}">')
            for name, value in fields.items():
                kid = node_key_ids[name]
                lines.append(
                    f'      <data key="{xml_escape(kid)}">'
                    f"{xml_escape(graphml_attr_value(value))}</data>"
                )
            lines.append("    </node>")
        else:
            lines.append(f'    <node id="{xml_escape(node_id)}"/>')

    for edge_id, source, target, fields in edges:
        attrs = (
            f'id="{xml_escape(edge_id)}" '
            f'source="{xml_escape(source)}" '
            f'target="{xml_escape(target)}"'
        )
        if fields:
            lines.append(f"    <edge {attrs}>")
            for name, value in fields.items():
                kid = edge_key_ids[name]
                lines.append(
                    f'      <data key="{xml_escape(kid)}">'
                    f"{xml_escape(graphml_attr_value(value))}</data>"
                )
            lines.append("    </edge>")
        else:
            lines.append(f"    <edge {attrs}/>")

    for edge_id, members, fields in hyperedges:
        lines.append(f'    <hyperedge id="{xml_escape(edge_id)}">')
        for member in members:
            lines.append(f'      <endpoint node="{xml_escape(member)}"/>')
        for name, value in fields.items():
            kid = hyperedge_key_ids[name]
            lines.append(
                f'      <data key="{xml_escape(kid)}">'
                f"{xml_escape(graphml_attr_value(value))}</data>"
            )
        lines.append("    </hyperedge>")

    lines.append("  </graph>")
    lines.append("</graphml>")
    lines.append("")
    return "\n".join(lines)
