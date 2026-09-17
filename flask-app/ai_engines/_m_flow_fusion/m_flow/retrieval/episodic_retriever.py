# m_flow/retrieval/episodic_retriever.py
"""
Episodic Memory Retriever.

Used for coarse-grained question retrieval, returns Episode-Facet-FacetPoint-Entity triplets.

The retriever uses two-pass output assembly:
1. episodic_bundle_search returns raw triplets (full graph edges)
2. get_context returns raw triplets (for frontend graph visualization)
3. get_completion applies display_mode filtering before sending to LLM:
   - "summary" mode (default): only Episode summaries → concise LLM context
   - "detail" mode: Facet + Entity edges → richer LLM context
"""

import asyncio
import re
from datetime import datetime, timezone
from typing import Any, Optional, Type, List, Union


# Regex to detect explicit date formats (supports MDY, DMY, ISO, Chinese)
_EXPLICIT_DATE_PATTERN = re.compile(
    r"""
    # ISO format: 2023-05-07, 2023/05/07, 2023.05.07
    \d{4}[-/\.]\d{1,2}[-/\.]\d{1,2}
    |
    # Chinese format: 2023年5月7日
    \d{4}年\d{1,2}月\d{1,2}[日号]?
    |
    # English MDY: May 7, 2023 / May 7th, 2023
    (?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|
       Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)
    \s+\d{1,2}(?:st|nd|rd|th)?,?\s*\d{4}
    |
    # English DMY: 7 May 2023 / 7th May 2023 (LOCOMO format!)
    \d{1,2}(?:st|nd|rd|th)?\s+
    (?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|
       Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)
    ,?\s*\d{4}
    """,
    re.VERBOSE | re.IGNORECASE,
)


def _is_explicit_date(time_text: str) -> bool:
    """Check if time_text contains an explicit date (not relative time)."""
    return bool(_EXPLICIT_DATE_PATTERN.search(time_text))


def _format_episode_time(attrs: dict, label_created_at: bool = True) -> Optional[str]:
    """Extract human-readable time from Episode attributes.

    Priority (handles relative time expressions):
    1. mentioned_time_text IF it contains an explicit date (e.g., "May 7, 2023")
    2. mentioned_time_start_ms (convert to date string) - ALWAYS precise
    3. mentioned_time_text as fallback (even if relative, better than nothing)
    4. created_at (convert to date string, if numeric)
    5. None (no time available)

    Args:
        attrs: Node attributes dictionary
        label_created_at: If True, add "(recorded)" suffix when using created_at
                         to distinguish from event time (mentioned_time).
                         Default True since created_at is ingestion time, not event time.

    Note on created_at vs mentioned_time:
        - mentioned_time: The time the EVENT occurred (semantic time from content)
        - created_at: The time the data was RECORDED/INGESTED (technical timestamp)
        These represent different time dimensions. When only created_at is available,
        LLM may incorrectly interpret it as event time.
    """
    time_text = attrs.get("mentioned_time_text")
    start_ms = attrs.get("mentioned_time_start_ms")

    # Priority 1: Use mentioned_time_text ONLY if it's an explicit date
    if time_text and isinstance(time_text, str) and time_text.strip():
        clean_text = time_text.strip()
        if _is_explicit_date(clean_text):
            return clean_text

    # Priority 2: Convert mentioned_time_start_ms (ALWAYS precise)
    if start_ms is not None:
        try:
            dt = datetime.fromtimestamp(int(start_ms) / 1000, tz=timezone.utc)
            return dt.strftime("%B %d, %Y")  # e.g., "May 07, 2023"
        except (ValueError, OSError, TypeError):
            pass

    # Priority 3: Fallback to mentioned_time_text (even if relative)
    if time_text and isinstance(time_text, str) and time_text.strip():
        return time_text.strip()

    # Priority 4: Convert created_at (if it's a millisecond timestamp)
    # Note: created_at is INGESTION time, not necessarily EVENT time
    created_at = attrs.get("created_at")
    if created_at is not None:
        try:
            if isinstance(created_at, (int, float)):
                ts = created_at / 1000 if created_at > 1e12 else created_at
                dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                date_str = dt.strftime("%B %d, %Y")
                # Optionally label to distinguish from event time
                if label_created_at:
                    return f"{date_str} (recorded)"
                return date_str
        except (ValueError, OSError, TypeError):
            pass

    return None


from m_flow.adapters.graph import get_graph_provider
from m_flow.knowledge.graph_ops.m_flow_graph.MemoryGraphElements import Edge
from m_flow.knowledge.graph_ops.utils.resolve_edges_to_text import resolve_edges_to_text
from m_flow.retrieval.base_graph_retriever import BaseGraphRetriever
from m_flow.retrieval.utils.completion import generate_completion, summarize_text
from m_flow.retrieval.utils.session_cache import (
    save_conversation_history,
    get_conversation_history,
)
from m_flow.shared.logging_utils import get_logger
from m_flow.context_global_variables import session_user
from m_flow.adapters.cache.config import CacheConfig

from .episodic import episodic_bundle_search, EpisodicConfig, get_episodic_config

logger = get_logger("EpisodicRetriever")


class EpisodicRetriever(BaseGraphRetriever):
    """
    Episodic Memory Retriever.

    Based on Bundle Search algorithm, supports:
    - FacetPoint two-hop closure
    - Path cost propagation
    - Hybrid retrieval (keyword + vector)
    - Exact match bonus
    - Display mode filtering (summary / detail)
    """

    def __init__(
        self,
        user_prompt_path: str = "graph_retrieval_context.txt",
        system_prompt_path: str = "direct_answer.txt",
        system_prompt: Optional[str] = None,
        top_k: Optional[int] = None,
        config: Optional[EpisodicConfig] = None,
    ):
        """
        Initialize EpisodicRetriever.

        Args:
            user_prompt_path: User prompt file path
            system_prompt_path: System prompt file path
            system_prompt: Custom system prompt
            top_k: Number of top Episodes to return (overrides config)
            config: Configuration object (optional, auto-loaded if not provided)
        """
        self.user_prompt_path = user_prompt_path
        self.system_prompt_path = system_prompt_path
        self.system_prompt = system_prompt

        self.config = config or get_episodic_config()
        if top_k is not None:
            self.config.top_k = top_k

    async def get_triplets(self, query: str) -> List[Edge]:
        """
        Retrieve triplets using episodic_bundle_search.

        Returns the full set of edges as assembled by bundle_search
        (respects config.display_mode for output assembly).

        Args:
            query: Search query

        Returns:
            List[Edge]: Episodic triplets
        """
        return await episodic_bundle_search(query=query, config=self.config)

    async def get_context(self, query: str) -> Union[List[Edge], str]:
        """
        Retrieve episodic context.

        When display_mode is "summary" or "highly_related_summary", returns
        processed text string for direct use. Otherwise returns raw triplets
        for graph visualization and downstream use.

        Args:
            query: Search query

        Returns:
            List[Edge] or str: Triplets (detail mode) or formatted text (summary modes)
        """
        graph_engine = await get_graph_provider()
        if await graph_engine.is_empty():
            logger.warning("M-Flow retrieval skipped: knowledge graph has no data")
            return []

        triplets = await self.get_triplets(query)

        # Apply display_mode filtering for summary modes
        display_mode = getattr(self.config, "display_mode", "summary")

        if display_mode == "summary":
            summaries = _extract_episode_summaries(triplets)
            if summaries:
                return "\n\n---\n\n".join(summaries)
            logger.warning("No Episode summaries found, falling back to full context")

        if display_mode == "highly_related_summary":
            summaries = _extract_filtered_summaries(triplets)
            if summaries:
                return "\n\n---\n\n".join(summaries)
            logger.warning("No filtered summaries found, falling back to full context")

        # "detail" mode or fallback: return raw triplets
        return triplets

    async def convert_retrieved_objects_to_context(self, triplets: List[Edge]) -> str:
        """
        Convert triplets to text context for LLM consumption.

        Applies display_mode filtering:
        - "summary": extracts only Episode summaries (concise)
        - "detail": includes Facet + Entity text (richer)
        """
        display_mode = getattr(self.config, "display_mode", "summary")

        if display_mode == "summary":
            summaries = _extract_episode_summaries(triplets)
            if summaries:
                return "\n\n---\n\n".join(summaries)
            logger.warning("No Episode summaries found, falling back to full context")

        if display_mode == "highly_related_summary":
            # In this mode, the output_assembler already filtered the summary
            # and stored the filtered text in edge.attributes["edge_text"].
            # Read from edge_text instead of node.summary.
            summaries = _extract_filtered_summaries(triplets)
            if summaries:
                return "\n\n---\n\n".join(summaries)
            logger.warning("No filtered summaries found, falling back to full context")

        # "detail" mode or fallback: use full edge text
        _inject_text_for_episodic_nodes(triplets)
        return await resolve_edges_to_text(triplets)

    async def get_completion(
        self,
        query: str,
        context: Optional[List[Edge]] = None,
        session_id: Optional[str] = None,
        response_model: Type = str,
    ) -> List[Any]:
        """
        Generate completion based on episodic triplets.

        The context passed to LLM is filtered by config.display_mode:
        - "summary" (default): only Episode summaries → concise, no duplication
        - "detail": Facet + Entity edges → richer context

        Args:
            query: User query
            context: Optional pre-retrieved triplets
            session_id: Session ID (for caching)
            response_model: Response model type

        Returns:
            List[Any]: LLM-generated answer
        """
        retrieved = context if context is not None else await self.get_context(query)

        if isinstance(retrieved, str):
            context_text = retrieved
        else:
            context_text = await self.convert_retrieved_objects_to_context(retrieved)

        cache_config = CacheConfig()
        user = session_user.get()
        user_id = getattr(user, "id", None)
        session_save = user_id and cache_config.caching

        if session_save:
            conversation_history = await get_conversation_history(session_id=session_id)
            context_summary, completion = await asyncio.gather(
                summarize_text(context_text),
                generate_completion(
                    query=query,
                    context=context_text,
                    user_prompt_path=self.user_prompt_path,
                    system_prompt_path=self.system_prompt_path,
                    system_prompt=self.system_prompt,
                    conversation_history=conversation_history,
                    response_model=response_model,
                ),
            )
            await save_conversation_history(
                query=query,
                context_summary=context_summary,
                answer=completion,
                session_id=session_id,
            )
        else:
            completion = await generate_completion(
                query=query,
                context=context_text,
                user_prompt_path=self.user_prompt_path,
                system_prompt_path=self.system_prompt_path,
                system_prompt=self.system_prompt,
                response_model=response_model,
            )

        return [completion]


def _extract_episode_summaries(triplets: List[Edge]) -> List[str]:
    """
    Extract unique Episode summaries from triplets.

    Deduplicates by Episode ID to avoid repeating the same summary
    when multiple edges reference the same Episode.

    Returns:
        List of unique Episode summary strings, ordered by first appearance.
        Each summary includes time prefix if available: "[Time] [Name]\nSummary"
    """
    seen_ids = set()
    summaries = []

    for edge in triplets:
        for node in (edge.node1, edge.node2):
            node_type = node.attributes.get("type")
            if node_type != "Episode":
                continue

            node_id = str(node.id)
            if node_id in seen_ids:
                continue
            seen_ids.add(node_id)

            display = node.attributes.get("display_only") or node.attributes.get("summary", "")
            if display:
                name = node.attributes.get("name", "")
                time_str = _format_episode_time(node.attributes)
                header_parts = []
                if time_str:
                    header_parts.append(f"[{time_str}]")
                if name:
                    header_parts.append(f"[{name}]")
                if header_parts:
                    summaries.append(f"{' '.join(header_parts)}\n{display}")
                else:
                    summaries.append(display)

    return summaries


def _extract_filtered_summaries(triplets: List[Edge]) -> List[str]:
    """
    Extract filtered Episode summaries from edge_text.

    Used by highly_related_summary mode where the output_assembler
    stores the section-filtered summary in edge.attributes["edge_text"]
    rather than using the full node.summary.

    Deduplicates by Episode ID. Includes time prefix if available.
    """
    seen_ids = set()
    summaries = []

    for edge in triplets:
        rel = edge.attributes.get("relationship_name", "")
        if rel != "episode_summary":
            continue

        # The Episode node
        node = edge.node1
        node_id = str(node.id)
        if node_id in seen_ids:
            continue
        seen_ids.add(node_id)

        filtered = edge.attributes.get("edge_text", "")
        if not filtered:
            filtered = node.attributes.get("display_only") or node.attributes.get("summary", "")

        if filtered:
            name = node.attributes.get("name", "")
            time_str = _format_episode_time(node.attributes)
            # Build header with optional time and name
            header_parts = []
            if time_str:
                header_parts.append(f"[{time_str}]")
            if name:
                header_parts.append(f"[{name}]")
            if header_parts:
                summaries.append(f"{' '.join(header_parts)}\n{filtered}")
            else:
                summaries.append(filtered)

    return summaries


def _inject_text_for_episodic_nodes(triplets: List[Edge]) -> None:
    """
    Inject text attributes to support resolve_edges_to_text.

    Prefers display_only when available, falling back to indexed fields:
    - Episode: display_only > summary (with time prefix if available)
    - Facet: display_only > description > anchor_text > search_text > name
    - FacetPoint: display_only > description > search_text > name
    """
    for edge in triplets:
        for node in (edge.node1, edge.node2):
            node_type = node.attributes.get("type")

            if node.attributes.get("text"):
                continue

            if node_type == "Episode":
                display = node.attributes.get("display_only") or node.attributes.get("summary")
                if display:
                    time_str = _format_episode_time(node.attributes)
                    if time_str:
                        node.attributes["text"] = f"[{time_str}] {display}"
                    else:
                        node.attributes["text"] = display

            elif node_type == "Facet":
                node.attributes["text"] = (
                    node.attributes.get("display_only")
                    or node.attributes.get("description")
                    or node.attributes.get("anchor_text")
                    or node.attributes.get("search_text")
                    or node.attributes.get("name")
                )

            elif node_type == "FacetPoint":
                node.attributes["text"] = (
                    node.attributes.get("display_only")
                    or node.attributes.get("description")
                    or node.attributes.get("search_text")
                    or node.attributes.get("name")
                )
