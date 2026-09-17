"""
Exact match bonus module.

Apply exact match bonus to vector search results:
- Number matching (full/partial)
- English matching (when Chinese-English mixed)
- Keyword matching
"""

import re
from dataclasses import dataclass
from typing import List, Set

from .config import EpisodicConfig
from .query_preprocessor import PreprocessedQuery, extract_english_words, has_chinese


@dataclass
class NumberToken:
    """Number token."""

    raw: str  # Bare number: "40"
    full: str  # Full form: "40万"
    unit: str = ""


def extract_number_tokens(text: str) -> List[NumberToken]:
    """
    Extract number tokens from text.

    Example: "40万" -> [NumberToken(raw="40", full="40万", unit="万")]
    """
    if not text:
        return []

    tokens: List[NumberToken] = []
    seen_positions: Set[int] = set()

    # Match numbers with units. Prefer longer/more specific units before shorter ones
    # so phrases like "12 个月" resolve to "月" instead of the generic classifier "个".
    pattern_with_unit = (
        r"(\d+\.?\d*)\s*(分钟|小时|个月|个小时|个星期|个周|万|亿|TB|GB|MB|KB|次|条|人|家|天|月|年|元|%|个|分|秒)"
    )
    for match in re.finditer(pattern_with_unit, text, re.IGNORECASE):
        if match.start() in seen_positions:
            continue
        seen_positions.add(match.start())

        num = match.group(1)
        unit = match.group(2)
        full = (num + unit).replace(" ", "")
        tokens.append(NumberToken(raw=num, full=full, unit=unit))

    # Match pure numbers
    pattern_pure = r"\b(\d+\.?\d*)\b"
    for match in re.finditer(pattern_pure, text):
        if match.start() in seen_positions:
            continue
        end_pos = match.end()
        if end_pos < len(text) and re.match(
            r"\s*(分钟|小时|个月|个小时|个星期|个周|万|亿|TB|GB|MB|KB|次|条|人|家|天|月|年|元|%|个|分|秒)",
            text[end_pos:],
            re.IGNORECASE,
        ):
            continue

        num = match.group(1)
        tokens.append(NumberToken(raw=num, full=num, unit=""))

    return tokens


def calculate_number_match_bonus(
    query_tokens: List[NumberToken],
    node_tokens: List[NumberToken],
    config: EpisodicConfig,
) -> float:
    """
    Calculate number match bonus.

    - Full match (40万 = 40万): High bonus
    - Partial match (40万 vs 40%): Low bonus
    """
    if not query_tokens or not node_tokens:
        return 0.0

    bonus = 0.0
    matched_indices: Set[int] = set()

    # Full match
    for qi, qt in enumerate(query_tokens):
        for nt in node_tokens:
            if qt.full.lower() == nt.full.lower():
                bonus -= config.full_number_match_bonus
                matched_indices.add(qi)
                break

    # Partial match
    for qi, qt in enumerate(query_tokens):
        if qi in matched_indices:
            continue
        for nt in node_tokens:
            if qt.raw == nt.raw and qt.full.lower() != nt.full.lower():
                bonus -= config.partial_number_match_bonus
                break

    return max(bonus, -config.full_number_match_bonus * 2)


def calculate_exact_match_bonus(
    query: str,
    node_text: str,
    config: EpisodicConfig,
) -> float:
    """
    Calculate exact match bonus (returns negative value to reduce distance).
    """
    if not query or not node_text:
        return 0.0

    bonus = 0.0

    # Number matching
    query_tokens = extract_number_tokens(query)
    if query_tokens:
        node_tokens = extract_number_tokens(node_text)
        bonus += calculate_number_match_bonus(query_tokens, node_tokens, config)

    # English matching (only when Chinese-English mixed)
    if has_chinese(query):
        query_english = extract_english_words(query)
        if query_english:
            node_english = extract_english_words(node_text)
            matched_count = sum(1 for qe in query_english if any(qe.lower() == ne.lower() for ne in node_english))
            if matched_count > 0:
                bonus -= min(matched_count * config.english_match_bonus, config.english_match_bonus * 2)

    return bonus


def apply_exact_match_bonus(
    query: str,
    scored_results: list,
    config: EpisodicConfig,
) -> None:
    """
    Apply exact match bonus to vector search results (modifies in place).
    """
    if not scored_results:
        return

    for r in scored_results:
        try:
            payload = getattr(r, "payload", {}) or {}
            node_text = str(payload.get("text", ""))

            if not node_text:
                continue

            bonus = calculate_exact_match_bonus(query, node_text, config)

            if bonus < 0:
                current_score = float(getattr(r, "score", 1.0))
                if current_score >= 0.1:
                    r.score = max(0.0, current_score + bonus)
        except Exception:
            continue


def apply_keyword_match_bonus(
    preprocessed: PreprocessedQuery,
    scored_results: list,
    config: EpisodicConfig,
) -> None:
    """
    Apply keyword match bonus to vector search results (modifies in place).
    """
    if not preprocessed.use_hybrid or not preprocessed.keyword or not scored_results:
        return

    keyword_norm = _normalize_for_keyword(preprocessed.keyword)

    for r in scored_results:
        try:
            payload = getattr(r, "payload", {}) or {}
            node_text = str(payload.get("text", ""))

            if not node_text:
                continue

            text_norm = _normalize_for_keyword(node_text)

            # Full substring match
            if keyword_norm in text_norm:
                current_score = float(getattr(r, "score", 1.0))
                r.score = max(0.0, current_score - config.keyword_match_bonus)
        except Exception:
            continue


def _normalize_for_keyword(s: str) -> str:
    """Normalize string for keyword matching."""
    s = (s or "").lower()
    return re.sub(r"[\s，,。.；;：:！!？?、]+", "", s)
