# m_flow/memory/procedural/procedure_builder/merge_utils.py
"""
Merge Utilities: Content merging and deduplication for procedural memory.

Pure functions for merging points_text, context fields, and deduplicating candidates.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

from m_flow.memory.procedural.models import ContextPackDraft
from m_flow.memory.procedural.procedural_points_builder import normalize_for_id
from m_flow.shared.data_models import ProceduralCandidate


# ============================================================
# Points Text Merging
# ============================================================


def _strip_line_prefix(line: str) -> str:
    """Remove line number/bullet prefix like '1.', '2)', '- ', '* ' etc."""
    return re.sub(r"^\s*[\d]+[.)、:\-\s]+", "", line).strip()


def merge_points_text_with_dedup(existing: str, new: str) -> str:
    """
    Merge points_text with line-level deduplication.
    Uses normalize_for_id to detect duplicate lines.
    Strips line number prefixes before comparison.

    Args:
        existing: Existing points_text (may be multi-line)
        new: New points_text to merge in

    Returns:
        Merged text with duplicates removed
    """
    if not new or not new.strip():
        return existing

    existing_lines = [line.strip() for line in existing.split("\n") if line.strip()]
    new_lines = [line.strip() for line in new.split("\n") if line.strip()]

    # Track seen normalized forms (without line number prefix)
    seen = {normalize_for_id(_strip_line_prefix(line)) for line in existing_lines}

    # Add truly new lines
    for line in new_lines:
        norm = normalize_for_id(_strip_line_prefix(line))
        if norm and norm not in seen:
            existing_lines.append(line)
            seen.add(norm)

    return "\n".join(existing_lines)


# ============================================================
# Context Fields Merging
# ============================================================


def merge_context_fields(
    existing_context_text: str,
    new_context: Optional[ContextPackDraft],
) -> ContextPackDraft:
    """
    Merge context fields: new fills in where existing is empty (doesn't overwrite).

    Args:
        existing_context_text: Existing context as formatted text (e.g., "When: ...; Why: ...")
        new_context: New context draft from LLM compilation

    Returns:
        Merged ContextPackDraft
    """
    # Parse existing context_text
    old = _parse_context_text(existing_context_text)

    if not new_context:
        return ContextPackDraft(
            when_text=old.get("when"),
            why_text=old.get("why"),
            boundary_text=old.get("boundary"),
            outcome_text=old.get("outcome"),
            prereq_text=old.get("prereq"),
            exception_text=old.get("exception"),
        )

    # Merge: new fills in if old is empty
    return ContextPackDraft(
        when_text=old.get("when") or new_context.when_text,
        why_text=old.get("why") or new_context.why_text,
        boundary_text=old.get("boundary") or new_context.boundary_text,
        outcome_text=old.get("outcome") or new_context.outcome_text,
        prereq_text=old.get("prereq") or new_context.prereq_text,
        exception_text=old.get("exception") or new_context.exception_text,
    )


def _parse_context_text(context_text: str) -> Dict[str, Optional[str]]:
    """
    Parse context_text back to individual fields.
    Format: "When: ...; Why: ...; Boundary: ..."

    Args:
        context_text: Formatted context string

    Returns:
        Dict with keys: when, why, boundary, outcome, prereq, exception
    """
    result: Dict[str, Optional[str]] = {}
    if not context_text:
        return result

    # Split by semicolon or newline
    parts = re.split(r"[;\n]", context_text)

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Try to match "Field: value" pattern
        match = re.match(
            r"^(When|Why|Boundary|Outcome|Prerequisites|Exception):\s*(.+)$",
            part,
            re.IGNORECASE,
        )
        if match:
            field = match.group(1).lower()
            value = match.group(2).strip()
            if field == "prerequisites":
                field = "prereq"
            result[field] = value

    return result


# ============================================================
# Candidate Deduplication
# ============================================================


def dedup_candidates(
    candidates: List[ProceduralCandidate],
) -> List[ProceduralCandidate]:
    """
    Deduplicate candidates by normalized search_text.
    Keep the one with highest confidence.

    Args:
        candidates: List of candidates (may contain duplicates)

    Returns:
        Deduplicated list
    """
    seen: Dict[str, ProceduralCandidate] = {}

    for c in candidates:
        key = normalize_for_id(c.search_text)
        if not key:
            continue

        if key not in seen or c.confidence > seen[key].confidence:
            seen[key] = c

    return list(seen.values())
