"""Search API route — hybrid search across the knowledge graph."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from axon.core.embeddings.embedder import embed_query
from axon.core.search.hybrid import hybrid_search

logger = logging.getLogger(__name__)

router = APIRouter(tags=["search"])


class SearchRequest(BaseModel):
    """Body for the POST /search endpoint."""

    query: str = Field(min_length=1, max_length=1000)
    limit: int = Field(default=20, ge=1, le=200)


@router.post("/search")
def search(body: SearchRequest, request: Request) -> dict:
    """Run hybrid search (FTS + optional vector) and return results."""
    storage = request.app.state.storage

    query_embedding = embed_query(body.query)
    if query_embedding is None:
        logger.warning("Embedding failed for query %r; falling back to FTS-only", body.query)

    try:
        results = hybrid_search(
            body.query,
            storage,
            query_embedding=query_embedding,
            limit=body.limit,
        )
    except Exception as exc:
        logger.error("Search failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Search failed") from exc

    return {
        "results": [
            {
                "nodeId": r.node_id,
                "score": r.score,
                "name": r.node_name,
                "filePath": r.file_path,
                "label": r.label,
                "snippet": r.snippet,
            }
            for r in results
        ]
    }
