"""Playground memory retriever — search long-term memories for in-frame persons."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from m_flow.shared.logging_utils import get_logger

_log = get_logger(__name__)


@dataclass
class RetrievalResult:
    context: str = ""
    dataset_sources: list[dict] = field(default_factory=list)
    empty: bool = True


async def retrieve_memories(
    query: str,
    dataset_ids: list[str],
    user=None,
) -> RetrievalResult:
    """Search M-Flow long-term memory across the given datasets.

    Uses EPISODIC mode — pure vector/graph retrieval, no LLM involved.
    The retrieved context is later injected into the Playground's own LLM call.
    """
    if not dataset_ids or not query.strip():
        return RetrievalResult()

    try:
        from m_flow import search as m_flow_search, RecallMode

        uuids = [UUID(did) for did in dataset_ids]

        result = await m_flow_search(
            query_text=query,
            query_type=RecallMode.EPISODIC,
            dataset_ids=uuids,
            user=user,
            top_k=5,
        )

        context_text = ""
        sources: list[dict] = []

        if isinstance(result, list):
            parts = []
            for sr in result:
                sr_ctx = getattr(sr, "search_result", None) or getattr(sr, "context", "")
                if sr_ctx:
                    parts.append(str(sr_ctx))
                ds_name = getattr(sr, "dataset_name", "")
                if ds_name:
                    sources.append({"dataset_id": "", "dataset_name": ds_name})
            context_text = "\n---\n".join(parts)
        elif hasattr(result, "context"):
            ctx = result.context
            if isinstance(ctx, dict):
                context_text = ctx.get("context", "") or str(ctx)
            elif isinstance(ctx, str):
                context_text = ctx
            else:
                context_text = str(ctx)

        if not context_text.strip():
            return RetrievalResult()

        return RetrievalResult(
            context=context_text,
            dataset_sources=sources,
            empty=False,
        )

    except Exception as e:
        _log.warning(f"Memory retrieval failed (non-fatal): {e}")
        return RetrievalResult()
