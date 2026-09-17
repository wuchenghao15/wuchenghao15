# m_flow/memory/episodic/normalization.py
"""
Text normalization module

Provides unified text normalization functions for:
- Comparing text similarity
- Generating deterministic IDs
- Search text validation

Step 3D: Extracted from write_episodic_memories.py
Phase 6: Added SearchTextQuality enum and evaluate_search_text function
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


def _nfkc(s: str) -> str:
    """
    Unicode NFKC normalization

    Args:
        s: Input string

    Returns:
        Normalized string, returns empty string if input is None or empty
    """
    if not s:
        return ""
    return unicodedata.normalize("NFKC", str(s)).strip()


def normalize_for_compare(text: str) -> str:
    """
    Text normalization for comparison

    Processing: NFKC + strip + lower + collapse whitespace

    Args:
        text: Input text

    Returns:
        Normalized text (lowercase, whitespace collapsed)
    """
    if not text:
        return ""
    t = _nfkc(text)
    t = t.lower()
    t = re.sub(r"\s+", " ", t)
    return t


def normalize_for_id(text: str) -> str:
    """
    Text normalization for ID generation

    More aggressive normalization to reduce duplicates caused by whitespace/punctuation differences

    Args:
        text: Input text

    Returns:
        Normalized text (no whitespace, no punctuation)
    """
    t = normalize_for_compare(text)
    t = t.replace(" ", "")
    t = re.sub(r"[，,。.；;：:()[\]【】<>《》" "\"''!！？?]+", "", t)
    return t


def truncate(s: Any, max_chars: int) -> str:
    """
    Truncate string to specified length

    Args:
        s: Input string or object that can be converted to string
        max_chars: Maximum character count

    Returns:
        Truncated string (ends with … if truncated)
    """
    if s is None:
        return ""
    s = str(s).strip()
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 1].rstrip() + "…"


# ============================================================
# Search Text Quality Evaluation
# ============================================================


class SearchTextQuality(Enum):
    """Search text quality level"""

    GOOD = "good"  # High quality, normal processing
    WARNING = "warning"  # Low quality but usable, log warning and keep
    CRITICAL = "critical"  # Invalid, should discard


@dataclass
class SearchTextEvaluation:
    """Search text evaluation result"""

    quality: SearchTextQuality
    reason: Optional[str] = None
    normalized_text: str = ""

    @property
    def is_usable(self) -> bool:
        """Whether usable (not CRITICAL)"""
        return self.quality != SearchTextQuality.CRITICAL

    @property
    def should_warn(self) -> bool:
        """Whether should log warning"""
        return self.quality == SearchTextQuality.WARNING


# Invalid search text prefix list (Chinese and English) - CRITICAL level
_BAD_PREFIX = (
    # Chinese
    "本段",
    "上述",
    "该内容",
    "这里",
    "这部分",
    "这段",
    "本文",
    # English
    "this section",
    "the above",
    "this part",
    "here",
    "the following",
)

# Overly generic search text (Chinese and English) - WARNING level (warn only)
_TOO_GENERIC = {
    # Chinese
    "风险",
    "决策",
    "进展",
    "总结",
    "原因",
    "影响",
    "问题",
    "方案",
    "计划",
    "结果",
    # English
    "risk",
    "decision",
    "progress",
    "summary",
    "reason",
    "impact",
    "issue",
    "plan",
    "result",
    "cause",
    "effect",
    "solution",
    "background",
    "goal",
    "content",
    "situation",
    "description",
    "note",
    "other",
}


def evaluate_search_text(text: str) -> SearchTextEvaluation:
    """
    Evaluate search text quality

    Returns three levels:
    - GOOD: High quality, normal processing
    - WARNING: Low quality but usable, log warning and keep
    - CRITICAL: Invalid, should discard

    CRITICAL conditions (discard):
    - Empty or pure whitespace
    - Too short (less than 2 characters)
    - Pure digits
    - Pure punctuation
    - Starts with invalid prefix (e.g., "本段", "该内容", etc.)

    WARNING conditions (keep but warn):
    - Overly generic vocabulary (e.g., "总结", "问题", etc.)

    Args:
        text: Search text

    Returns:
        SearchTextEvaluation containing quality level, reason, and normalized text
    """
    # Empty text -> CRITICAL
    if not text or not text.strip():
        return SearchTextEvaluation(
            quality=SearchTextQuality.CRITICAL,
            reason="empty_or_whitespace",
            normalized_text="",
        )

    t = _nfkc(text).strip()
    t_lower = t.lower()

    # Empty text -> CRITICAL
    if not t:
        return SearchTextEvaluation(
            quality=SearchTextQuality.CRITICAL,
            reason="empty_after_normalize",
            normalized_text="",
        )

    # Too short -> CRITICAL
    if len(t) < 2:
        return SearchTextEvaluation(
            quality=SearchTextQuality.CRITICAL,
            reason="too_short",
            normalized_text=t,
        )

    # Pure digits -> CRITICAL
    if t.isdigit():
        return SearchTextEvaluation(
            quality=SearchTextQuality.CRITICAL,
            reason="pure_digits",
            normalized_text=t,
        )

    # Pure punctuation -> CRITICAL
    if re.match(r"^[^\w\u4e00-\u9fff]+$", t):
        return SearchTextEvaluation(
            quality=SearchTextQuality.CRITICAL,
            reason="pure_punctuation",
            normalized_text=t,
        )

    # Starts with invalid prefix -> CRITICAL
    if t_lower.startswith(tuple(p.lower() for p in _BAD_PREFIX)):
        return SearchTextEvaluation(
            quality=SearchTextQuality.CRITICAL,
            reason="bad_prefix",
            normalized_text=t,
        )

    # Overly generic vocabulary -> WARNING (keep but warn)
    if t_lower in {g.lower() for g in _TOO_GENERIC}:
        return SearchTextEvaluation(
            quality=SearchTextQuality.WARNING,
            reason="too_generic",
            normalized_text=t,
        )

    # Other cases -> GOOD
    return SearchTextEvaluation(
        quality=SearchTextQuality.GOOD,
        reason=None,
        normalized_text=t,
    )


def is_bad_search_text(text: str) -> bool:
    """
    Check if search text is invalid (backward compatibility function)

    Note: This function now only returns True for CRITICAL level
    WARNING level (e.g., overly generic vocabulary) will return False, allowing retention

    For finer control, use evaluate_search_text()

    Args:
        text: Search text

    Returns:
        True means invalid (CRITICAL), False means usable (GOOD or WARNING)
    """
    evaluation = evaluate_search_text(text)
    return evaluation.quality == SearchTextQuality.CRITICAL
