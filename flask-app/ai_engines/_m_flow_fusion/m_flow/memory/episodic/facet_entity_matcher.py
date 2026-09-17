# m_flow/memory/episodic/facet_entity_matcher.py
"""
Facet-Entity Matching Module.

This module provides functionality to match extracted entities to specific Facets
based on their text content. The matching is done using exact text matching
(with word boundary awareness) since entities are extracted using EXACT original form.

Design rationale:
- Entity names are extracted with EXACT form preservation (per extract_entity_names.txt)
- This allows efficient regex-based matching without semantic analysis
- Facet-Entity edges enable fine-grained retrieval and Episode splitting

Usage:
    from m_flow.memory.episodic.facet_entity_matcher import match_entities_to_facets

    entity_to_facets = match_entities_to_facets(
        entity_names=["Caroline", "LGBTQ advocacy"],
        facets=draft.facets,
    )
"""

from __future__ import annotations

import re
from typing import Dict, List, Any, TYPE_CHECKING

from m_flow.shared.logging_utils import get_logger
from m_flow.memory.episodic.edge_text_generators import make_facet_involves_entity_edge_text

if TYPE_CHECKING:
    pass

logger = get_logger("episodic.facet_entity_matcher")


def _is_cjk_char(c: str) -> bool:
    """Check if a single character is CJK."""
    return (
        "\u4e00" <= c <= "\u9fff"  # CJK Unified Ideographs
        or "\u3040" <= c <= "\u309f"  # Hiragana
        or "\u30a0" <= c <= "\u30ff"  # Katakana
        or "\uac00" <= c <= "\ud7af"
    )  # Hangul Syllables


def _is_cjk(text: str) -> bool:
    """Check if text contains CJK (Chinese/Japanese/Korean) characters."""
    return any(_is_cjk_char(c) for c in text)


def _is_single_digit(text: str) -> bool:
    """Check if text is a single digit (0-9)."""
    return len(text) == 1 and text.isdigit()


def _is_single_letter(text: str) -> bool:
    """Check if text is a single ASCII letter (a-z, A-Z)."""
    return len(text) == 1 and text.isascii() and text.isalpha()


def _is_single_cjk(text: str) -> bool:
    """Check if text is a single CJK character."""
    return len(text) == 1 and _is_cjk_char(text)


def _build_entity_pattern(entity_name: str) -> re.Pattern:
    """
    Build a regex pattern for matching an entity name.

    Special handling for single-character entities:
    - Single digit: must be surrounded by non-digit characters
      e.g., "有7个" ✓, "77" ✗, " 7 " ✓
    - Single letter: must be surrounded by space/CJK/digit (not other letters)
      e.g., "A B" ✓, "ABC" ✗, "测试A测试" ✓, "A1" ✓
    - Single CJK: must be surrounded by space/letter/digit (not other CJK)
      e.g., "中国" ✗, "test中test" ✓, " 中 " ✓

    For multi-character entities:
    - Non-CJK: uses word boundaries (\b)
    - CJK: uses simple substring matching

    Args:
        entity_name: The entity name to match

    Returns:
        Compiled regex pattern
    """
    escaped = re.escape(entity_name)

    # Special handling for single-character entities
    if _is_single_digit(entity_name):
        # Single digit: surrounded by non-digit characters
        # (?<!\d) = not preceded by digit, (?!\d) = not followed by digit
        pattern = rf"(?<!\d){escaped}(?!\d)"
        return re.compile(pattern)

    if _is_single_letter(entity_name):
        # Single letter: surrounded by space/CJK/digit, not other letters
        # Lookbehind: start of string OR (space OR CJK OR digit)
        # Lookahead: end of string OR (space OR CJK OR digit)
        # CJK range: \u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af
        cjk_range = r"\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af"
        # Use a simpler approach: negative lookbehind/lookahead for letters
        pattern = rf"(?<![a-zA-Z]){escaped}(?![a-zA-Z])"
        return re.compile(pattern, re.IGNORECASE)

    if _is_single_cjk(entity_name):
        # Single CJK: surrounded by space/letter/digit, not other CJK
        # Negative lookbehind/lookahead for CJK characters
        cjk_range = r"\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af"
        pattern = rf"(?<![{cjk_range}]){escaped}(?![{cjk_range}])"
        return re.compile(pattern)

    # Multi-character entities
    if _is_cjk(entity_name):
        # For CJK, use simple substring match (no word boundaries in CJK)
        return re.compile(escaped)
    else:
        # For non-CJK, use word boundaries for exact matching
        # Handle special cases like possessives (Caroline's)
        pattern = rf"\b{escaped}(?:\'s)?\b"
        return re.compile(pattern, re.IGNORECASE)


def _get_facet_text(facet: Any) -> str:
    """
    Extract searchable text from a Facet object.

    Combines search_text and description for comprehensive matching.

    Args:
        facet: Facet object (or dict-like)

    Returns:
        Combined text for matching
    """
    search_text = ""
    description = ""

    if hasattr(facet, "search_text"):
        search_text = facet.search_text or ""
    elif isinstance(facet, dict):
        search_text = facet.get("search_text", "")

    if hasattr(facet, "description"):
        description = facet.description or ""
    elif isinstance(facet, dict):
        description = facet.get("description", "")

    return f"{search_text} {description}"


def _get_facet_id(facet: Any) -> str:
    """Extract ID from a Facet object."""
    if hasattr(facet, "id"):
        return str(facet.id)
    elif isinstance(facet, dict):
        return str(facet.get("id", ""))
    return ""


def _get_facet_search_text(facet: Any) -> str:
    """Extract search_text from a Facet object."""
    if hasattr(facet, "search_text"):
        return facet.search_text or ""
    elif isinstance(facet, dict):
        return facet.get("search_text", "")
    return ""


def match_entities_to_facets(
    entity_names: List[str],
    facets: List[Any],
    min_entity_length: int = 1,
) -> Dict[str, List[Dict[str, str]]]:
    """
    Match entity names to Facets where they appear.

    Uses exact text matching with context-aware boundaries:
    - Single digit: only matches when surrounded by non-digits
    - Single letter: only matches when surrounded by non-letters
    - Single CJK: only matches when surrounded by non-CJK
    - Multi-char: uses word boundaries (non-CJK) or substring (CJK)

    Entities are sorted by length (longest first) to prioritize specific matches.

    Args:
        entity_names: List of entity names (extracted with EXACT original form)
        facets: List of Facet objects
        min_entity_length: Minimum entity name length (default 1, single chars use strict matching)

    Returns:
        Dict mapping entity_name to list of matched facet info:
        {
            "entity_name": [
                {"facet_id": "...", "facet_search_text": "..."},
                ...
            ]
        }
    """
    if not entity_names or not facets:
        return {}

    # Filter out entities shorter than min_entity_length
    # Note: single-char entities (length=1) now use strict boundary matching,
    # so they can be safely included when min_entity_length=1
    filtered_entities = [name for name in entity_names if len(name) >= min_entity_length]

    if len(filtered_entities) < len(entity_names):
        skipped = len(entity_names) - len(filtered_entities)
        logger.debug(f"[facet_entity_matcher] Skipped {skipped} entities shorter than {min_entity_length} chars")

    if not filtered_entities:
        return {}

    # Sort by length DESC to match longer (more specific) entities first
    sorted_entities = sorted(filtered_entities, key=len, reverse=True)

    # Pre-compile patterns for efficiency
    entity_patterns: Dict[str, re.Pattern] = {name: _build_entity_pattern(name) for name in sorted_entities}

    # Initialize result dict
    entity_to_facets: Dict[str, List[Dict[str, str]]] = {name: [] for name in sorted_entities}

    # Match each entity against each facet
    for facet in facets:
        facet_id = _get_facet_id(facet)
        facet_search_text = _get_facet_search_text(facet)
        facet_text = _get_facet_text(facet)

        if not facet_id or not facet_text.strip():
            continue

        for entity_name in sorted_entities:
            pattern = entity_patterns[entity_name]

            if pattern.search(facet_text):
                entity_to_facets[entity_name].append(
                    {
                        "facet_id": facet_id,
                        "facet_search_text": facet_search_text,
                    }
                )

    # Remove entities with no matches
    entity_to_facets = {name: matches for name, matches in entity_to_facets.items() if matches}

    # Log statistics
    total_matches = sum(len(v) for v in entity_to_facets.values())
    logger.debug(
        f"[facet_entity_matcher] Matched {len(entity_to_facets)}/{len(filtered_entities)} entities "
        f"to {total_matches} facet locations"
    )

    return entity_to_facets


def build_facet_entity_edges(
    entity_to_facets: Dict[str, List[Dict[str, str]]],
    entity_description_map: Dict[str, str],
) -> List[Dict[str, Any]]:
    """
    Build edge data for Facet -> Entity relationships.

    Args:
        entity_to_facets: Output from match_entities_to_facets()
        entity_description_map: Dict mapping entity_name to description

    Returns:
        List of edge data dicts ready for graph insertion:
        [
            {
                "source_id": facet_id,
                "target_entity_name": entity_name,
                "edge_text": "...",
                "relationship_name": "involves_entity",
            },
            ...
        ]
    """
    edges: List[Dict[str, Any]] = []

    for entity_name, facet_matches in entity_to_facets.items():
        entity_desc = entity_description_map.get(entity_name, "")

        for match in facet_matches:
            facet_id = match["facet_id"]
            facet_search_text = match["facet_search_text"]

            edge_text = make_facet_involves_entity_edge_text(
                entity_name=entity_name,
                entity_description=entity_desc,
                facet_search_text=facet_search_text,
            )

            edges.append(
                {
                    "source_id": facet_id,
                    "target_entity_name": entity_name,
                    "edge_text": edge_text,
                    "relationship_name": "involves_entity",
                }
            )

    logger.debug(f"[facet_entity_matcher] Built {len(edges)} Facet-Entity edges")

    return edges
