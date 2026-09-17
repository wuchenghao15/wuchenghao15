# m_flow/memory/procedural/procedural_points_builder.py
"""
Procedural Memory: Points Builder

Deterministic generation of KeyPoints/ContextPoints from structured content.
No LLM used, avoiding fabrication, ensuring stability and anchor coverage.

Architecture: Points link directly to Procedure (no Pack intermediate).

Core functions:
- Generate KeyPoints from key points text by line/step splitting
- Generate ContextPoints from context fields (when/why/boundary)
- Coverage completion: Automatically detect key anchors, add points if not covered
- Deduplication: Normalize then dedup, keep better version
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple

from m_flow.core import Edge
from m_flow.core.domain.utils.generate_node_id import generate_node_id
from m_flow.core.domain.models import ProcedureStepPoint, ProcedureContextPoint

from m_flow.memory.episodic.normalization import _nfkc


# ============================================================
# Normalize / Cleaning
# ============================================================


def normalize_for_id(text: str) -> str:
    """Normalize text to stable key (for dedup and ID generation).

    Aggressive normalization: removes ALL whitespace and punctuation
    to ensure "Python 编码规范" and "Python编码规范" produce same ID.
    """
    text = _nfkc(text).lower()
    # Remove ALL whitespace (not just collapse)
    text = re.sub(r"\s+", "", text)
    # Remove punctuation but keep letters, numbers, and CJK
    text = re.sub(r"[^\w\u4e00-\u9fff]+", "", text)
    return text


def clean_search_text(raw: str, max_len: int = 120) -> str:
    """Clean search_text: remove numbering, special chars, control length."""
    text = raw.strip()
    # Remove step numbering prefix
    text = re.sub(r"^\s*\d+[.)、:\-\s]+", "", text)
    # Remove code blocks
    text = re.sub(r"`[^`]*`", "", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) > max_len:
        text = text[: max_len - 1] + "…"
    return text


# ============================================================
# Anchor Token Extraction (for coverage completion)
# ============================================================


def extract_anchor_tokens(text: str, min_len: int = 2, max_count: int = 50) -> List[str]:
    """
    Extract key anchor tokens from text:
    - Numbers with units
    - English terms (2+ chars)
    - Technical terms
    """
    if not text:
        return []

    tokens: List[str] = []
    seen: Set[str] = set()

    # Numbers with units
    for m in re.finditer(r"\d+\.?\d*\s*(?:TB|GB|MB|KB|%|次|个|分钟|秒|小时|天|ms|s|min)", text, re.I):
        t = m.group(0).strip()
        k = t.lower()
        if k not in seen and len(t) >= min_len:
            seen.add(k)
            tokens.append(t)

    # English terms (2+ chars, camelCase or regular)
    for m in re.finditer(r"[A-Za-z][A-Za-z0-9_\-]*[A-Za-z0-9]", text):
        t = m.group(0)
        k = t.lower()
        if k not in seen and len(t) >= min_len:
            seen.add(k)
            tokens.append(t)

    # Path-like strings
    for m in re.finditer(r"[/\\][\w./\\-]+", text):
        t = m.group(0)
        k = t.lower()
        if k not in seen and len(t) >= 3:
            seen.add(k)
            tokens.append(t)

    return tokens[:max_count]


def token_covered(token: str, existing_text: str) -> bool:
    """Check if a token is already covered by existing point text."""
    return token.lower() in existing_text.lower()


def pick_snippet_containing(text: str, token: str, window: int = 80) -> Optional[str]:
    """Pick a snippet from text that contains the token, aligned to sentence boundaries."""
    idx = text.lower().find(token.lower())
    if idx < 0:
        return None

    start = max(0, idx - window // 2)
    end = min(len(text), idx + len(token) + window // 2)

    # Align START to nearest sentence boundary (look backwards from start)
    sentence_starts = ["。", "；", "; ", ". ", "\n", "，"]
    if start > 0:
        best_start = start
        search_region = text[max(0, start - 20) : start + 5]
        for sep in sentence_starts:
            pos = search_region.rfind(sep)
            if pos >= 0:
                candidate = max(0, start - 20) + pos + len(sep)
                if candidate <= idx:
                    best_start = candidate
                    break
        start = best_start

    snippet = text[start:end].strip()

    # Trim END to sentence boundary
    for sep in ["。", "；", "; ", ". ", "\n"]:
        pos = snippet.find(sep)
        if 10 < pos < len(snippet) - 5:
            snippet = snippet[:pos]
            break

    return clean_search_text(snippet)


# ============================================================
# Build KeyPoints (Deterministic)
# ============================================================


def build_step_points(
    steps_pack_id: str,  # procedure_id
    steps_anchor_text: str,
    safety_max_points: int = 500,
    time_fields: Optional[Dict[str, any]] = None,
) -> List[Tuple[Edge, ProcedureStepPoint]]:
    """
    Deterministic generation of KeyPoints from key points text.

    Points link directly to Procedure (no Pack intermediate).

    Args:
        steps_pack_id: Parent ID (procedure_id in new architecture)
        steps_anchor_text: Full key points text
        safety_max_points: Maximum number of points
        time_fields: Time fields dict for propagation
    """
    pairs: List[Tuple[Edge, ProcedureStepPoint]] = []
    seen: Dict[str, ProcedureStepPoint] = {}  # norm -> point

    if not steps_anchor_text:
        return pairs

    # Split by line (supports multiple formats)
    lines = re.split(r"[\n\r]+", steps_anchor_text)
    step_number = 0

    for line in lines:
        line = line.strip()
        if not line or len(line) < 5:
            continue

        # Detect numbering
        num_match = re.match(r"^\s*(\d+)[.)、:\-\s]+", line)
        if num_match:
            step_number = int(num_match.group(1))
        else:
            step_number += 1

        search_text = clean_search_text(line)
        if not search_text or len(search_text) < 5:
            continue

        norm = normalize_for_id(search_text)
        if not norm:
            continue

        # Deduplication: If exists, keep smaller index (earlier prioritized)
        if norm in seen:
            existing = seen[norm]
            existing_idx = existing.point_index if existing.point_index is not None else 9999
            if step_number < existing_idx:
                existing.point_index = step_number
            continue

        # Generate ID (uses parent_id as seed)
        point_id = str(generate_node_id(f"ProcedureStepPoint:{steps_pack_id}:{norm[:50]}"))

        point = ProcedureStepPoint(
            id=point_id,
            name=search_text[:100] if len(search_text) > 100 else search_text,
            search_text=search_text,
            point_index=step_number,
            description=None,
            **(time_fields or {}),
        )
        seen[norm] = point

        if len(seen) >= safety_max_points:
            break

    # Coverage completion: Check for missing key anchors
    all_point_text = " ".join([p.search_text for p in seen.values()])
    all_anchors = extract_anchor_tokens(steps_anchor_text)

    for tok in all_anchors:
        if len(seen) >= safety_max_points:
            break
        if token_covered(tok, all_point_text):
            continue

        snippet = pick_snippet_containing(steps_anchor_text, tok)
        if not snippet or len(snippet) < 5:
            continue

        norm = normalize_for_id(snippet)
        if norm in seen:
            continue

        point_id = str(generate_node_id(f"ProcedureStepPoint:{steps_pack_id}:cov:{norm[:40]}"))

        point = ProcedureStepPoint(
            id=point_id,
            name=snippet[:100] if len(snippet) > 100 else snippet,
            search_text=snippet,
            point_index=None,
            description="auto_coverage",
            **(time_fields or {}),
        )
        seen[norm] = point

    # Build edge pairs (sorted by index)
    for p in sorted(seen.values(), key=lambda x: (x.point_index is None, x.point_index or 999)):
        edge = Edge(
            relationship_type="has_key_point",
            edge_text=f"point:{p.point_index or '-'} | {p.search_text[:80]}",
        )
        pairs.append((edge, p))

    return pairs


# ============================================================
# Build ContextPoints (Deterministic)
# ============================================================


def build_context_points(
    context_pack_id: str,  # procedure_id
    when_text: Optional[str],
    why_text: Optional[str],
    boundary_text: Optional[str],
    outcome_text: Optional[str],
    prereq_text: Optional[str],
    exception_text: Optional[str],
    context_anchor_text: Optional[str] = None,
    safety_max_points: int = 500,
    time_fields: Optional[Dict[str, Any]] = None,
) -> List[Tuple[Edge, ProcedureContextPoint]]:
    """
    Deterministic generation of ContextPoints from context fields.

    Points link directly to Procedure (no Pack intermediate).

    Args:
        context_pack_id: Parent ID (procedure_id in new architecture)
        time_fields: Time fields dict for propagation
    """
    pairs: List[Tuple[Edge, ProcedureContextPoint]] = []
    seen: Dict[str, ProcedureContextPoint] = {}  # norm -> point

    # Process by type
    type_texts = [
        ("when", when_text),
        ("why", why_text),
        ("boundary", boundary_text),
        ("outcome", outcome_text),
        ("prereq", prereq_text),
        ("exception", exception_text),
    ]

    for point_type, text in type_texts:
        if not text:
            continue

        # Split by separator (supports multiple formats)
        parts = re.split(r"[；;]\s*|[。\.]\s+|[\n\r]+", text)

        for part in parts:
            part = part.strip()
            if not part or len(part) < 5:
                continue

            search_text = clean_search_text(part)
            if not search_text or len(search_text) < 5:
                continue

            norm = normalize_for_id(search_text)
            if not norm:
                continue

            # Deduplication: If exists, merge point_type (take more specific)
            if norm in seen:
                old = seen[norm]
                if old.point_type in (None, "", "misc") and point_type not in (None, "", "misc"):
                    old.point_type = point_type
                continue

            # Generate ID (uses parent_id as seed)
            point_id = str(generate_node_id(f"ProcedureContextPoint:{context_pack_id}:{point_type}:{norm[:40]}"))

            point = ProcedureContextPoint(
                id=point_id,
                name=search_text[:100] if len(search_text) > 100 else search_text,
                search_text=search_text,
                point_type=point_type,
                description=None,
                **(time_fields or {}),
            )
            seen[norm] = point

            if len(seen) >= safety_max_points:
                break

        if len(seen) >= safety_max_points:
            break

    # Coverage completion
    full_text = " ".join([t or "" for _, t in type_texts]) + " " + (context_anchor_text or "")
    all_point_text = " ".join([p.search_text for p in seen.values()])
    all_anchors = extract_anchor_tokens(full_text)

    for tok in all_anchors:
        if len(seen) >= safety_max_points:
            break
        if token_covered(tok, all_point_text):
            continue

        snippet = pick_snippet_containing(full_text, tok)
        if not snippet or len(snippet) < 5:
            continue

        norm = normalize_for_id(snippet)
        if norm in seen:
            continue

        point_id = str(generate_node_id(f"ProcedureContextPoint:{context_pack_id}:cov:{norm[:40]}"))

        point = ProcedureContextPoint(
            id=point_id,
            name=snippet[:100] if len(snippet) > 100 else snippet,
            search_text=snippet,
            point_type="misc",
            description="auto_coverage",
            **(time_fields or {}),
        )
        seen[norm] = point

    # Build edge pairs
    for p in seen.values():
        edge = Edge(
            relationship_type="has_context_point",
            edge_text=f"{p.point_type or 'misc'}: {p.search_text[:80]}",
        )
        pairs.append((edge, p))

    return pairs
