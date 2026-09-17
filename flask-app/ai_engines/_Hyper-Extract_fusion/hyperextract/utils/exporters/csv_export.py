"""CSV exporters for pairwise graphs and hypergraphs.

Writes spreadsheet-friendly tables using the stdlib :mod:`csv` module
(correct quoting for commas, quotes, and newlines).

This module is named ``csv_export`` so it does not shadow the stdlib
:mod:`csv` package. Import from :mod:`hyperextract.utils.exporters`.

Pairwise graphs
    ``nodes.csv`` (``id`` + schema scalars) and ``edges.csv``
    (``source``, ``target`` + edge scalars). Endpoint order is preserved;
    endpoints are never sorted.

Hypergraphs
    ``nodes.csv`` and ``hyperedges.csv``. ``hyperedges.csv`` has an ``id``
    column plus a ``members`` column. Members are joined with
    :data:`HYPEREDGE_MEMBER_SEP` (``|``) and **sorted lexicographically** so
    the file is deterministic. This is the opposite of binary CSV, which
    must not sort endpoints.
"""

import csv
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from hyperextract.utils.logging import get_logger

from .common import (
    HYPEREDGE_MEMBER_SEP,
    default_edge_id,
    incident_ids,
    resolve_nodes,
    scalar_fields,
)

logger = get_logger(__name__)


def export_to_csv(
    nodes: Sequence[BaseModel],
    edges: Sequence[BaseModel],
    *,
    node_id_extractor: Callable[[Any], str],
    incident_nodes_extractor: Callable[[Any], Sequence[str]],
    folder_path: str | Path,
    edge_id_extractor: Callable[[Any], str] | None = None,
    hypergraph: bool = False,
    overwrite: bool = False,
) -> Path:
    """Export nodes and edges to CSV files in ``folder_path``.

    Args:
        nodes: Node/entity models to export.
        edges: Edge/hyperedge models to export.
        node_id_extractor: Maps a node to its unique key.
        incident_nodes_extractor: Maps an edge to incident node keys
            (a 2-tuple for pairwise graphs, an N-tuple for hypergraphs).
        folder_path: Destination directory.
        edge_id_extractor: Optional edge -> id (used for ``hyperedges.csv``
            and ignored for pairwise ``edges.csv``). Defaults to ``e0``,
            ``e1``, ...
        hypergraph: If True, write ``hyperedges.csv`` instead of
            ``edges.csv``. Hyperedge members are sorted; binary endpoints
            are not.
        overwrite: Allow writing into an existing, non-empty directory.

    Returns:
        The output directory :class:`~pathlib.Path`.

    Raises:
        FileExistsError: If ``folder_path`` exists, is non-empty, and
            ``overwrite`` is False.
        NotADirectoryError: If ``folder_path`` exists and is a file.
    """
    root = Path(folder_path)
    if root.exists() and root.is_file():
        raise NotADirectoryError(
            f"Destination '{root}' is a file; pass a directory for CSV export."
        )
    if root.exists() and root.is_dir() and any(root.iterdir()) and not overwrite:
        raise FileExistsError(
            f"Destination '{root}' already exists and is not empty. "
            f"Pass overwrite=True to write into it."
        )
    root.mkdir(parents=True, exist_ok=True)

    by_id = resolve_nodes(nodes, node_id_extractor)
    node_rows = _node_rows(by_id)
    _write_csv(root / "nodes.csv", ["id"], node_rows)

    if hypergraph:
        edge_rows, skipped = _hyperedge_rows(
            edges, incident_nodes_extractor, by_id, edge_id_extractor
        )
        _write_csv(root / "hyperedges.csv", ["id", "members"], edge_rows)
        edge_count = len(edge_rows)
        kind = "hypergraph"
    else:
        edge_rows, skipped = _pairwise_edge_rows(edges, incident_nodes_extractor, by_id)
        _write_csv(root / "edges.csv", ["source", "target"], edge_rows)
        edge_count = len(edge_rows)
        kind = "graph"

    logger.info(
        "csv: exported kind=%s nodes=%d edges=%d skipped_edges=%d path=%s",
        kind,
        len(node_rows),
        edge_count,
        skipped,
        root,
    )
    return root


def _node_rows(by_id: dict[str, BaseModel]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for node_id, node in by_id.items():
        row: dict[str, Any] = {"id": node_id}
        for key, value in scalar_fields(node).items():
            if key == "id":
                continue
            row[key] = value
        rows.append(row)
    return rows


def _pairwise_edge_rows(
    edges: Sequence[BaseModel],
    incident_nodes_extractor: Callable[[Any], Sequence[str]],
    by_id: dict[str, BaseModel],
) -> tuple[list[dict[str, Any]], int]:
    rows: list[dict[str, Any]] = []
    skipped = 0
    for edge in edges:
        members = incident_ids(edge, incident_nodes_extractor)
        if members is None or len(members) != 2:
            skipped += 1
            if members is not None and len(members) > 2:
                logger.warning(
                    "export.csv: skipping non-pairwise edge members=%s "
                    "(pass hypergraph=True for N-ary edges)",
                    members,
                )
            continue
        source, target = members[0], members[1]
        if source not in by_id or target not in by_id:
            skipped += 1
            logger.warning(
                "export.csv: skipping edge with missing endpoint source=%s target=%s",
                source,
                target,
            )
            continue
        row: dict[str, Any] = {"source": source, "target": target}
        for key, value in scalar_fields(edge).items():
            if key in {"source", "target"}:
                continue
            row[key] = value
        rows.append(row)
    return rows, skipped


def _hyperedge_rows(
    edges: Sequence[BaseModel],
    incident_nodes_extractor: Callable[[Any], Sequence[str]],
    by_id: dict[str, BaseModel],
    edge_id_extractor: Callable[[Any], str] | None,
) -> tuple[list[dict[str, Any]], int]:
    rows: list[dict[str, Any]] = []
    skipped = 0
    for index, edge in enumerate(edges):
        members = incident_ids(edge, incident_nodes_extractor)
        if members is None:
            skipped += 1
            continue
        known = [mid for mid in members if mid in by_id]
        missing = [mid for mid in members if mid not in by_id]
        if missing:
            skipped += 1
            logger.warning(
                "export.csv: skipping hyperedge with missing members %s",
                missing,
            )
            continue
        if not known:
            skipped += 1
            continue
        edge_id = default_edge_id(edge, index, edge_id_extractor)
        # Sorted for stable output; binary CSV must not sort endpoints.
        members_cell = HYPEREDGE_MEMBER_SEP.join(sorted(known))
        row: dict[str, Any] = {"id": edge_id, "members": members_cell}
        dumped = edge.model_dump()
        for key, value in scalar_fields(edge).items():
            if key in {"id", "members"}:
                continue
            # Membership lists are represented by the members column.
            if isinstance(dumped.get(key), (list, tuple, set, dict)):
                continue
            row[key] = value
        rows.append(row)
    return rows, skipped


def _write_csv(path: Path, primary: Sequence[str], rows: list[dict[str, Any]]) -> None:
    fieldnames = _fieldnames(primary, rows)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            quoting=csv.QUOTE_MINIMAL,
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def _fieldnames(primary: Sequence[str], rows: list[dict[str, Any]]) -> list[str]:
    names = list(primary)
    seen = set(primary)
    for row in rows:
        for key in row:
            if key not in seen:
                names.append(key)
                seen.add(key)
    return names
