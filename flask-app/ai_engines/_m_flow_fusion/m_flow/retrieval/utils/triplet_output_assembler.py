"""
Triplet Output Assembler for fine_grained_triplet_search / UnifiedTripletSearch.

Resolves top-k triplet edges back to their parent Episodes,
deduplicates, and returns a ranked list of unique Episode summaries.

Problem solved:
  fine_grained_triplet_search returns flat top-k edges which may contain
  multiple edges referencing the same Episode (e.g., Episode→Concept_A,
  Episode→Concept_B, Facet→FacetPoint where Facet belongs to the same Episode).
  This causes the same Episode summary to appear multiple times in RAG context.

Solution:
  1. For each edge, find the parent Episode (direct or via graph traversal)
  2. Deduplicate by Episode ID
  3. Rank by average position (ties broken by first appearance)
  4. Return ≤ max_episodes unique Episode summaries
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from m_flow.knowledge.graph_ops.m_flow_graph.MemoryGraphElements import Edge
from m_flow.shared.logging_utils import get_logger

logger = get_logger(__name__)


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


def _format_episode_time_from_info(info: dict, label_created_at: bool = True) -> Optional[str]:
    """Extract human-readable time from Episode info dictionary.

    Priority (handles relative time expressions):
    1. mentioned_time_text IF it contains an explicit date
    2. mentioned_time_start_ms (convert to date string) - ALWAYS precise
    3. mentioned_time_text as fallback (even if relative)
    4. created_at (convert to date string, if numeric)
    5. None (no time available)

    Args:
        info: Episode info dictionary
        label_created_at: If True, add "(recorded)" suffix when using created_at
                         to distinguish from event time (mentioned_time).
                         Default True since created_at is ingestion time, not event time.

    Note on created_at vs mentioned_time:
        - mentioned_time: The time the EVENT occurred (semantic time from content)
        - created_at: The time the data was RECORDED/INGESTED (technical timestamp)
        These represent different time dimensions. When only created_at is available,
        LLM may incorrectly interpret it as event time.
    """
    time_text = info.get("mentioned_time_text")
    start_ms = info.get("mentioned_time_start_ms")

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
    created_at = info.get("created_at")
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


def assemble_episode_summaries(
    triplet_edges: List[Edge],
    max_episodes: int = 10,
) -> List[str]:
    """
    Extract unique Episode summaries from triplet search results.

    For each triplet edge:
    - If one node is an Episode, use it directly
    - If nodes are Facet/FacetPoint/Entity, trace upward through
      other edges in the result set to find the parent Episode

    Episodes are ranked by average rank position across all their
    edges, with ties broken by first appearance.

    Args:
        triplet_edges: Edges from fine_grained_triplet_search or
                       UnifiedTripletSearch, assumed to be pre-sorted
                       by importance (best first).
        max_episodes: Maximum number of unique Episode summaries to return.

    Returns:
        List of formatted Episode summary strings, ordered by rank.
    """
    if not triplet_edges:
        return []

    # Step 1: Build node-id → Episode-id mapping from the edges
    # Also collect Episode node objects and all node→Episode parent links
    episode_nodes: Dict[str, dict] = {}  # episode_id → {name, summary}
    node_to_episode: Dict[str, str] = {}  # node_id → episode_id
    facet_nodes: Dict[str, dict] = {}  # facet_id → {time info}
    episode_facets: Dict[str, List[str]] = defaultdict(list)  # episode_id → [facet_ids]

    # First pass: identify all Episode and Facet nodes
    for edge in triplet_edges:
        for node in (edge.node1, edge.node2):
            nid = str(node.id)
            ntype = node.attributes.get("type", "")

            if ntype == "Episode":
                episode_nodes[nid] = {
                    "name": node.attributes.get("name", ""),
                    "summary": node.attributes.get("summary", ""),
                    # Time fields for LLM context (fallback if no Facet time)
                    "mentioned_time_text": node.attributes.get("mentioned_time_text"),
                    "mentioned_time_start_ms": node.attributes.get("mentioned_time_start_ms"),
                    "created_at": node.attributes.get("created_at"),
                }
                node_to_episode[nid] = nid
            elif ntype in ("Facet", "FacetPoint"):
                # Collect Facet/FacetPoint time info for prioritized display
                facet_nodes[nid] = {
                    "search_text": node.attributes.get("search_text", ""),
                    "mentioned_time_text": node.attributes.get("mentioned_time_text"),
                    "mentioned_time_start_ms": node.attributes.get("mentioned_time_start_ms"),
                    "created_at": node.attributes.get("created_at"),
                }

    # Second pass: map non-Episode nodes to their parent Episode via edges
    # An edge like Episode→Facet or Episode→Entity tells us the Facet/Entity's parent
    # Also collect Episode→Facet associations for time display
    for edge in triplet_edges:
        n1_id = str(edge.node1.id)
        n2_id = str(edge.node2.id)
        n1_type = edge.node1.attributes.get("type", "")
        n2_type = edge.node2.attributes.get("type", "")

        if n1_type == "Episode" and n2_type != "Episode":
            node_to_episode[n2_id] = n1_id
            # Track Facet association for time display
            if n2_type in ("Facet", "FacetPoint") and n2_id in facet_nodes:
                episode_facets[n1_id].append(n2_id)
        elif n2_type == "Episode" and n1_type != "Episode":
            node_to_episode[n1_id] = n2_id
            # Track Facet association for time display
            if n1_type in ("Facet", "FacetPoint") and n1_id in facet_nodes:
                episode_facets[n2_id].append(n1_id)

    # Third pass: for Facet→FacetPoint edges, propagate the Facet's Episode
    # If Facet is mapped to an Episode, FacetPoint inherits that mapping
    for edge in triplet_edges:
        n1_id = str(edge.node1.id)
        n2_id = str(edge.node2.id)
        n1_type = edge.node1.attributes.get("type", "")
        n2_type = edge.node2.attributes.get("type", "")

        if n1_type == "Facet" and n2_type == "FacetPoint":
            if n1_id in node_to_episode and n2_id not in node_to_episode:
                node_to_episode[n2_id] = node_to_episode[n1_id]
        elif n2_type == "Facet" and n1_type == "FacetPoint":
            if n2_id in node_to_episode and n1_id not in node_to_episode:
                node_to_episode[n1_id] = node_to_episode[n2_id]

    # Step 2: For each edge (ranked by position), record its Episode
    episode_positions: Dict[str, List[int]] = defaultdict(list)  # ep_id → [positions]
    episode_first_seen: Dict[str, int] = {}  # ep_id → first position

    for rank, edge in enumerate(triplet_edges):
        # Find Episode for this edge via either endpoint
        n1_id = str(edge.node1.id)
        n2_id = str(edge.node2.id)

        ep_id = node_to_episode.get(n1_id) or node_to_episode.get(n2_id)
        if not ep_id:
            # Could not resolve to an Episode — try to use Episode-type node directly
            for node in (edge.node1, edge.node2):
                if node.attributes.get("type") == "Episode":
                    ep_id = str(node.id)
                    episode_nodes.setdefault(
                        ep_id,
                        {
                            "name": node.attributes.get("name", ""),
                            "summary": node.attributes.get("summary", ""),
                            # Time fields for LLM context
                            "mentioned_time_text": node.attributes.get("mentioned_time_text"),
                            "mentioned_time_start_ms": node.attributes.get("mentioned_time_start_ms"),
                            "created_at": node.attributes.get("created_at"),
                        },
                    )
                    break

        if not ep_id or ep_id not in episode_nodes:
            continue

        episode_positions[ep_id].append(rank)
        if ep_id not in episode_first_seen:
            episode_first_seen[ep_id] = rank

    if not episode_positions:
        logger.warning("No Episodes found in triplet edges")
        return []

    # Step 3: Rank Episodes by average position, ties broken by first appearance
    def sort_key(ep_id: str) -> Tuple[float, int]:
        positions = episode_positions[ep_id]
        avg_rank = sum(positions) / len(positions)
        first_seen = episode_first_seen[ep_id]
        return (avg_rank, first_seen)

    ranked_episode_ids = sorted(episode_positions.keys(), key=sort_key)
    ranked_episode_ids = ranked_episode_ids[:max_episodes]

    # Step 4: Format output with time prefix
    # Priority: Use Facet time if available, fallback to Episode time
    summaries = []
    for ep_id in ranked_episode_ids:
        info = episode_nodes.get(ep_id, {})
        summary = info.get("summary", "")
        name = info.get("name", "")

        if not summary:
            continue

        # Try to get time from associated Facets first
        time_str = None
        facet_ids = episode_facets.get(ep_id, [])
        for fid in facet_ids:
            facet_info = facet_nodes.get(fid, {})
            facet_time = _format_episode_time_from_info(facet_info)
            if facet_time:
                time_str = facet_time
                break  # Use first Facet with valid time

        # Fallback to Episode time
        if not time_str:
            time_str = _format_episode_time_from_info(info)

        # Build header with optional time and name
        header_parts = []
        if time_str:
            header_parts.append(f"[{time_str}]")
        if name:
            header_parts.append(f"[{name}]")

        if header_parts:
            summaries.append(f"{' '.join(header_parts)}\n{summary}")
        else:
            summaries.append(summary)

    logger.info(
        f"[triplet_output_assembler] {len(triplet_edges)} edges → "
        f"{len(episode_positions)} unique Episodes → "
        f"{len(summaries)} summaries (max {max_episodes})"
    )

    return summaries
