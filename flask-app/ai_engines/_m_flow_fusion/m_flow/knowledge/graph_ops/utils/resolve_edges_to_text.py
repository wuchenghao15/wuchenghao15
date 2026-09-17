"""
Convert graph edges to human-readable text.

Formats nodes and connections for LLM consumption.
"""

from __future__ import annotations

import re
import string
from collections import Counter
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from m_flow.knowledge.graph_ops.m_flow_graph.MemoryGraphElements import Edge

from m_flow.retrieval.utils.stop_words import DEFAULT_STOP_WORDS


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
                # Label to distinguish from event time
                if label_created_at:
                    return f"{date_str} (recorded)"
                return date_str
        except (ValueError, OSError, TypeError):
            pass

    return None


def _top_words(text: str, n: int = 3, stop: set | None = None, sep: str = ", ") -> str:
    """Extract n most frequent non-stop words."""
    stop = stop or DEFAULT_STOP_WORDS
    tokens = [w.lower().strip(string.punctuation) for w in text.split()]
    filtered = [w for w in tokens if w and w not in stop]
    top = [word for word, _ in Counter(filtered).most_common(n)]
    return sep.join(top)


def _make_title(text: str, head_words: int = 7, freq_words: int = 3) -> str:
    """Combine start of text with frequent keywords."""
    start = " ".join(text.split()[:head_words])
    keywords = _top_words(text, n=freq_words)
    return f"{start}... [{keywords}]"


def _collect_nodes(edges: list[Edge]) -> dict:
    """Build node dictionary with metadata."""
    nodes = {}
    for edge in edges:
        for nd in (edge.node1, edge.node2):
            if nd.id in nodes:
                continue

            attrs = nd.attributes
            ntype = attrs.get("type", "")
            txt = attrs.get("text")

            if ntype == "Episode":
                ep_id = attrs.get("name", "Episode")
                summary = attrs.get("summary") or txt or ""
                time_str = _format_episode_time(attrs)
                name = "[Episode]"
                if time_str:
                    content = f"[{time_str}] ID: {ep_id}\nSummary: {summary}"
                else:
                    content = f"ID: {ep_id}\nSummary: {summary}"
            elif ntype == "Facet":
                # Use Facet's own time fields for display
                facet_name = attrs.get("search_text") or attrs.get("name", "Unnamed")
                facet_desc = attrs.get("description", "")
                time_str = _format_episode_time(attrs)  # Reuse same format function
                name = f"[Facet: {facet_name}]"
                if time_str:
                    content = f"[{time_str}] {facet_desc}" if facet_desc else f"[{time_str}]"
                else:
                    content = facet_desc if facet_desc else facet_name
            elif ntype == "FacetPoint":
                # Use FacetPoint's own time fields for display
                point_name = attrs.get("search_text") or attrs.get("name", "Unnamed")
                point_desc = attrs.get("description", "")
                time_str = _format_episode_time(attrs)
                name = f"[FacetPoint: {point_name}]"
                if time_str:
                    content = f"[{time_str}] {point_desc}" if point_desc else f"[{time_str}]"
                else:
                    content = point_desc if point_desc else point_name
            elif txt:
                name = _make_title(txt)
                content = txt
            else:
                name = attrs.get("name", "Unnamed")
                content = attrs.get("description", name)

            nodes[nd.id] = {"node": nd, "name": name, "content": content, "type": ntype}
    return nodes


async def resolve_edges_to_text(edges: list[Edge]) -> str:
    """
    Format edges as readable text.

    Returns nodes block + connections block.
    """
    nodes = _collect_nodes(edges)

    node_lines = []
    for info in nodes.values():
        node_lines.append(f"Node: {info['name']}\n__node_content_start__\n{info['content']}\n__node_content_end__")
    node_section = "\n".join(node_lines)

    conn_lines = []
    for e in edges:
        src = nodes[e.node1.id]["name"]
        dst = nodes[e.node2.id]["name"]
        label = e.attributes.get("edge_text") or e.attributes.get("relationship_type")
        conn_lines.append(f"{src} --[{label}]--> {dst}")
    conn_section = "\n".join(conn_lines)

    return f"Nodes:\n{node_section}\n\nConnections:\n{conn_section}"
