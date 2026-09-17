"""Shared helpers for GraphML and CSV exporters.

These functions operate on plain Pydantic models plus extractor callables,
matching :func:`hyperextract.utils.obsidian.export_to_obsidian`. They do not
import AutoType classes.
"""

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from hyperextract.utils.logging import get_logger

logger = get_logger(__name__)

# Stable delimiter for hyperedge membership in ``hyperedges.csv``.
# Binary CSV never sorts endpoints; hyperedge members *are* sorted
# lexicographically so the file is deterministic.
HYPEREDGE_MEMBER_SEP = "|"

_XML_ESCAPE = (
    ("&", "&amp;"),
    ("<", "&lt;"),
    (">", "&gt;"),
    ('"', "&quot;"),
    ("'", "&apos;"),
)


def xml_escape(value: Any) -> str:
    """Escape XML special characters ``& < > " '`` in document order."""
    text = str(value)
    for src, dst in _XML_ESCAPE:
        text = text.replace(src, dst)
    return text


def scalar_fields(model: BaseModel) -> dict[str, str | int | float | bool]:
    """Return exportable fields from ``model.model_dump()``.

    ``str`` / ``int`` / ``float`` / ``bool`` are kept as-is; ``None`` is
    omitted; every other value is coerced with ``str()``.
    """
    dumped = model.model_dump()
    fields: dict[str, str | int | float | bool] = {}
    for key, value in dumped.items():
        if value is None:
            continue
        if value == [] or value == {}:
            continue
        if isinstance(value, (bool, int, float, str)):
            fields[key] = value
        else:
            fields[key] = str(value)
    return fields


def graphml_attr_type(value: str | float | bool) -> str:
    """Map a Python scalar to a GraphML ``attr.type``."""
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "long"
    if isinstance(value, float):
        return "double"
    return "string"


def graphml_attr_value(value: str | float | bool) -> str:
    """Serialize a scalar for a GraphML ``<data>`` element."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def merge_graphml_type(existing: str | None, incoming: str) -> str:
    """Promote mixed attribute types to ``string``."""
    if existing is None or existing == incoming:
        return incoming
    return "string"


def resolve_nodes(
    nodes: Sequence[BaseModel],
    node_id_extractor: Callable[[Any], str],
) -> dict[str, BaseModel]:
    """Map node id -> model, keeping the first occurrence of each id."""
    by_id: dict[str, BaseModel] = {}
    for node in nodes:
        try:
            node_id = str(node_id_extractor(node))
        except Exception as exc:
            logger.debug("export: node_id_extractor raised %s; skipping node", exc)
            continue
        if node_id in by_id:
            logger.debug("export: duplicate node id %r; keeping first", node_id)
            continue
        by_id[node_id] = node
    return by_id


def incident_ids(
    edge: Any, incident_nodes_extractor: Callable[[Any], Sequence[str]]
) -> list[str] | None:
    """Normalize an edge's incident node keys.

    Returns ``None`` when the extractor fails (caller should skip the edge).
    """
    try:
        raw = incident_nodes_extractor(edge)
    except Exception as exc:
        logger.debug("export: incident_nodes_extractor raised %s; skipping edge", exc)
        return None
    if raw is None:
        return []
    if isinstance(raw, (str, bytes)):
        return [str(raw)]
    if isinstance(raw, (list, tuple, set)):
        return [str(item) for item in raw if item is not None]
    return [str(raw)]


def default_edge_id(
    edge: Any, index: int, extractor: Callable[[Any], str] | None
) -> str:
    """Return an edge id from ``extractor``, falling back to ``e{index}``."""
    if extractor is None:
        return f"e{index}"
    try:
        value = extractor(edge)
    except Exception as exc:
        logger.debug("export: edge_id_extractor raised %s", exc)
        return f"e{index}"
    if value in (None, ""):
        return f"e{index}"
    return str(value)


def resolve_export_file(path: str | Path, *, overwrite: bool = False) -> Path:
    """Resolve a file-export destination, optionally refusing overwrite.

    GraphML CLI ``--force`` and MCP ``overwrite`` map onto this flag.
    JSON-LD / Cypher can reuse the same helper after those PRs land.
    """
    dest = Path(path)
    if dest.exists() and dest.is_dir():
        raise IsADirectoryError(
            f"Destination '{dest}' is a directory; pass a file path."
        )
    existing_nonempty = dest.exists() and dest.is_file() and dest.stat().st_size > 0
    if existing_nonempty and not overwrite:
        raise FileExistsError(
            f"Destination '{dest}' already exists. Pass overwrite=True to overwrite it."
        )
    dest.parent.mkdir(parents=True, exist_ok=True)
    return dest
