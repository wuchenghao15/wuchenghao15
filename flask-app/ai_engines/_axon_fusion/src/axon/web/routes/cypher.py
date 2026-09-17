"""Cypher query execution route — read-only raw Cypher against the graph."""

from __future__ import annotations

import logging
import re
import time

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from axon.core.cypher_guard import WRITE_KEYWORDS, sanitize_cypher

logger = logging.getLogger(__name__)

router = APIRouter(tags=["cypher"])


class CypherRequest(BaseModel):
    """Body for the POST /cypher endpoint."""

    query: str = Field(min_length=1, max_length=10000)


def _extract_return_columns(query: str) -> list[str]:
    """Best-effort extraction of column names from a Cypher RETURN clause.

    Handles aliases (``AS name``), dotted properties (``n.name``), and
    function calls (``count(n)``).
    """
    match = re.search(r"\bRETURN\b\s+(.*?)(?:\bORDER\b|\bLIMIT\b|\bSKIP\b|$)", query, re.IGNORECASE | re.DOTALL)
    if not match:
        return []

    return_expr = match.group(1).strip()
    columns = []
    for part in return_expr.split(","):
        part = part.strip()
        alias_match = re.search(r"\bAS\s+(\w+)\s*$", part, re.IGNORECASE)
        if alias_match:
            columns.append(alias_match.group(1))
        else:
            columns.append(part)

    return columns


@router.post("/cypher")
def execute_cypher(body: CypherRequest, request: Request) -> dict:
    """Execute a read-only Cypher query and return structured results."""
    storage = request.app.state.storage

    cleaned = sanitize_cypher(body.query)
    if WRITE_KEYWORDS.search(cleaned):
        raise HTTPException(
            status_code=400,
            detail=(
                "Only read-only queries (MATCH/RETURN) are allowed. "
                "Write operations (DELETE, DROP, CREATE, SET, MERGE) are not permitted."
            ),
        )

    columns = _extract_return_columns(body.query)

    start = time.perf_counter()
    try:
        rows = storage.execute_raw(body.query)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Cypher query failed: {exc}") from exc
    duration_ms = round((time.perf_counter() - start) * 1000, 2)

    if rows is None:
        rows = []

    serialized_rows = [[_serialize_value(v) for v in row] for row in rows]

    return {
        "columns": columns,
        "rows": serialized_rows,
        "rowCount": len(serialized_rows),
        "durationMs": duration_ms,
    }


def _serialize_value(value: object) -> object:
    """Convert non-JSON-serializable values to strings."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [_serialize_value(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _serialize_value(v) for k, v in value.items()}
    return str(value)
