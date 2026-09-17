"""Branch diff route — structural comparison between two git refs."""

from __future__ import annotations

import logging
import re

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, field_validator

from axon.core.diff import diff_branches
from axon.web.routes.graph import _serialize_edge, _serialize_node

logger = logging.getLogger(__name__)

router = APIRouter(tags=["diff"])

# Allow only safe characters in git refs: alphanumerics, dots, slashes,
# hyphens, tildes, carets, at-signs, and braces. Rejects shell meta-chars.
_SAFE_REF = re.compile(r"^[a-zA-Z0-9._/\-~^@{}]+$")


class DiffRequest(BaseModel):
    """Body for the POST /diff endpoint."""

    base: str
    compare: str

    @field_validator("base", "compare")
    @classmethod
    def validate_ref(cls, v: str) -> str:
        if not v or not _SAFE_REF.match(v):
            raise ValueError("Invalid git ref")
        if v.startswith("-"):
            raise ValueError("Git ref cannot start with -")
        return v


@router.post("/diff")
def compute_diff(body: DiffRequest, request: Request) -> dict:
    """Compare two branches structurally and return added/removed/modified entities."""
    repo_path = request.app.state.repo_path
    if repo_path is None:
        raise HTTPException(status_code=400, detail="No repo_path configured")

    branch_range = f"{body.base}..{body.compare}"

    try:
        result = diff_branches(repo_path, branch_range)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Diff failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Diff operation failed") from exc

    return {
        "added": [_serialize_node(n) for n in result.added_nodes],
        "removed": [_serialize_node(n) for n in result.removed_nodes],
        "modified": [
            {"before": _serialize_node(base), "after": _serialize_node(current)}
            for base, current in result.modified_nodes
        ],
        "addedEdges": [_serialize_edge(r) for r in result.added_relationships],
        "removedEdges": [_serialize_edge(r) for r in result.removed_relationships],
    }
