"""
Ingestion-side time extraction module.

Provides:
- extract_mentioned_time: Extract event occurrence time from text
- contains_time_hint: Quick filter to check if text contains time signals

Design principles:
1. Fast filter first: Don't call LLM for text without time signals
2. Evidence constraint: LLM output time must be supported by original text
3. Prefer missing over wrong: Don't extract when confidence is low
"""

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, List

from .query_time_parser import (
    parse_query_time,
    contains_time_hint,
)

# Regex patterns for extracting explicit dates to use as anchor
# These are copied from query_time_parser but simplified for anchor extraction

_ANCHOR_DATE_PATTERNS = [
    # 2024年3月15日 / 2024年3月15号 -> (year, month, day)
    (r"(\d{4})年(\d{1,2})月(\d{1,2})[日号]?", "ymd_cn"),
    # 2024-03-15 / 2024/03/15 / 2024.03.15 -> (year, month, day)
    (r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", "ymd_iso"),
    # March 15, 2024 / October 15, 2023 -> need special parsing
    (
        r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s*(\d{4})",
        "mdy_en",
    ),
    # 15 March 2024 -> (day, month_name, year)
    (
        r"(\d{1,2})(?:st|nd|rd|th)?\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?),?\s*(\d{4})",
        "dmy_en",
    ),
]

_ANCHOR_MONTH_MAP = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}


def _extract_anchor_from_explicit_dates(text: str) -> Optional[int]:
    """
    Extract the earliest explicit date from text to use as anchor for relative time parsing.

    This allows text like "[October 15, 2023] ... next month" to correctly parse
    "next month" as November 2023, not based on current system time.

    Args:
        text: Text to extract dates from

    Returns:
        Millisecond timestamp of the earliest explicit date found, or None if no explicit date found
    """
    earliest_ms: Optional[int] = None

    for pattern, ptype in _ANCHOR_DATE_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            try:
                if ptype == "ymd_cn" or ptype == "ymd_iso":
                    year = int(m.group(1))
                    month = int(m.group(2))
                    day = int(m.group(3))
                elif ptype == "mdy_en":
                    # "October 15, 2023" -> month is in group 0 text, day in group 1, year in group 2
                    match_text = m.group(0).lower()
                    day = int(m.group(1))
                    year = int(m.group(2))
                    # Extract month name from match text
                    month = None
                    for month_name, month_num in _ANCHOR_MONTH_MAP.items():
                        if month_name in match_text:
                            month = month_num
                            break
                    if month is None:
                        continue
                elif ptype == "dmy_en":
                    # "15 October, 2023" -> day in group 1, year in group 2
                    match_text = m.group(0).lower()
                    day = int(m.group(1))
                    year = int(m.group(2))
                    month = None
                    for month_name, month_num in _ANCHOR_MONTH_MAP.items():
                        if month_name in match_text:
                            month = month_num
                            break
                    if month is None:
                        continue
                else:
                    continue

                # Validate date
                if not (1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100):
                    continue

                # Convert to timestamp (start of day UTC)
                dt = datetime(year, month, day, 0, 0, 0, tzinfo=timezone.utc)
                ts_ms = int(dt.timestamp() * 1000)

                # Keep earliest date
                if earliest_ms is None or ts_ms < earliest_ms:
                    earliest_ms = ts_ms

            except (ValueError, OverflowError):
                continue

    return earliest_ms


@dataclass
class MentionedTimeResult:
    """Time extraction result."""

    has_time: bool = False
    start_ms: Optional[int] = None
    end_ms: Optional[int] = None
    confidence: float = 0.0
    evidence_text: Optional[str] = None  # Time expression evidence from original text

    def to_dict(self) -> dict:
        """Convert to dictionary (for writing to MemoryNode fields)."""
        if not self.has_time:
            return {}
        return {
            "mentioned_time_start_ms": self.start_ms,
            "mentioned_time_end_ms": self.end_ms,
            "mentioned_time_confidence": self.confidence,
            "mentioned_time_text": self.evidence_text,
        }


def extract_mentioned_time(
    text: str,
    anchor_time_ms: Optional[int] = None,
    min_confidence: float = 0.5,
) -> MentionedTimeResult:
    """
    Extract event occurrence time (mentioned_time) from text.

    This is a lightweight rule-based extractor that does not depend on LLM.

    Args:
        text: Text to extract time from
        anchor_time_ms: Anchor time (millisecond timestamp) for parsing relative time
                       If None, will try to extract from explicit dates in text first,
                       then fallback to current time
        min_confidence: Minimum confidence threshold, below which no result is returned

    Returns:
        MentionedTimeResult: Extraction result

    Design principles:
    - anchor_time is key: relative time (e.g., "yesterday") will be parsed relative to anchor_time
    - NEW: If text contains explicit dates (e.g., "[October 15, 2023]"), use the earliest
      explicit date as anchor for parsing relative time expressions
    - If document source has explicit time, use source time as anchor
    - If not, fallback to ingestion current time (but this may cause incorrect relative time parsing for old documents)
    """
    if not text or not text.strip():
        return MentionedTimeResult()

    # Step 1: Fast filter - return immediately if no time signal
    if not contains_time_hint(text):
        return MentionedTimeResult()

    # Step 2: Prepare anchor time (millisecond timestamp)
    # NEW: ALWAYS try to extract from explicit dates in text first
    # This ensures that text like "[October 15, 2023] ... next month" correctly uses
    # October 2023 as the anchor, not the ingestion time (which could be years later)
    explicit_anchor = _extract_anchor_from_explicit_dates(text)
    if explicit_anchor is not None:
        # Prefer explicit date from text over passed-in anchor
        anchor_time_ms = explicit_anchor
    elif anchor_time_ms is None:
        anchor_time_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

    # Step 3: Use parse_query_time to parse (reuse existing logic)
    # Note: parse_query_time expects now_ms parameter (millisecond timestamp)
    time_info = parse_query_time(text, now_ms=anchor_time_ms)

    if not time_info.has_time:
        return MentionedTimeResult()

    # Step 4: Check confidence
    if time_info.confidence < min_confidence:
        return MentionedTimeResult()

    # Step 5: Extract evidence text
    evidence = _extract_evidence_spans(text, time_info.matched_spans)

    return MentionedTimeResult(
        has_time=True,
        start_ms=time_info.start_ms,
        end_ms=time_info.end_ms,
        confidence=time_info.confidence,
        evidence_text=evidence,
    )


def _extract_evidence_spans(text: str, matched_spans: List) -> Optional[str]:
    """
    Extract evidence text from matched time expressions.

    Args:
        text: Original text
        matched_spans: List of TimeSpan objects returned by parse_query_time

    Returns:
        Merged evidence text, or None
    """
    if not matched_spans:
        return None

    # Deduplicate and limit length
    unique_spans = []
    seen = set()
    total_len = 0
    max_len = 100  # Maximum evidence length

    for span_obj in matched_spans:
        # TimeSpan object has matched_text attribute
        if hasattr(span_obj, "matched_text"):
            span_text = span_obj.matched_text
        elif isinstance(span_obj, str):
            span_text = span_obj
        else:
            continue

        span_text = span_text.strip()
        if not span_text or span_text.lower() in seen:
            continue
        seen.add(span_text.lower())

        if total_len + len(span_text) > max_len:
            break

        unique_spans.append(span_text)
        total_len += len(span_text) + 2  # Add separator length

    if not unique_spans:
        return None

    return ", ".join(unique_spans)


def merge_mentioned_times(
    time1: Optional[MentionedTimeResult],
    time2: Optional[MentionedTimeResult],
) -> Optional[MentionedTimeResult]:
    """
    Merge two time extraction results (for incremental update scenarios).

    Strategy:
    - If both are valid, take union
    - Confidence is weighted average
    - Merge evidence text

    Args:
        time1: First time result
        time2: Second time result

    Returns:
        Merged result, or None
    """
    if time1 is None or not time1.has_time:
        return time2
    if time2 is None or not time2.has_time:
        return time1

    # Both valid, take union
    merged_start = min(time1.start_ms, time2.start_ms)
    merged_end = max(time1.end_ms, time2.end_ms)

    # Weighted average confidence (weighted by time range width)
    w1 = time1.end_ms - time1.start_ms
    w2 = time2.end_ms - time2.start_ms
    total_w = w1 + w2
    if total_w > 0:
        merged_conf = (time1.confidence * w1 + time2.confidence * w2) / total_w
    else:
        merged_conf = (time1.confidence + time2.confidence) / 2

    # Merge evidence
    evidences = []
    if time1.evidence_text:
        evidences.append(time1.evidence_text)
    if time2.evidence_text and time2.evidence_text != time1.evidence_text:
        evidences.append(time2.evidence_text)
    merged_evidence = "; ".join(evidences)[:100] if evidences else None

    return MentionedTimeResult(
        has_time=True,
        start_ms=merged_start,
        end_ms=merged_end,
        confidence=merged_conf,
        evidence_text=merged_evidence,
    )


def dict_to_mentioned_time(d: dict) -> Optional[MentionedTimeResult]:
    """
    Restore MentionedTimeResult from dictionary (e.g., MemoryNode fields).

    Args:
        d: Dictionary containing mentioned_time_* fields

    Returns:
        MentionedTimeResult or None
    """
    start = d.get("mentioned_time_start_ms")
    end = d.get("mentioned_time_end_ms")

    if start is None or end is None:
        return None

    return MentionedTimeResult(
        has_time=True,
        start_ms=start,
        end_ms=end,
        confidence=d.get("mentioned_time_confidence", 0.5),
        evidence_text=d.get("mentioned_time_text"),
    )


# ============================================================
# Time field validation
# ============================================================

# Import logging for validation function
import logging as _logging

_validate_logger = _logging.getLogger("time.validation")


def validate_time_range(
    start_ms: Optional[int],
    end_ms: Optional[int],
    raise_on_error: bool = False,
) -> bool:
    """
    Validate if time range is valid.

    Validation rules:
    1. None values are considered "valid" (indicates no time information, won't cause error)
    2. If both have values, then start_ms <= end_ms
    3. Timestamps should be in reasonable range (1970-01-01 to 2100-01-01)

    Args:
        start_ms: Start time (millisecond timestamp), can be None
        end_ms: End time (millisecond timestamp), can be None
        raise_on_error: If True, raise ValueError on validation failure

    Returns:
        True if time range is valid (including None values), False if invalid

    Note:
        - None value means "no time information", which is a valid state (won't cause error)
        - But None does not mean "any time" or "match all times"
        - During retrieval, if query has time but candidate doesn't, no time bonus will be awarded
    """
    # None values are considered valid (indicates no time information)
    if start_ms is None or end_ms is None:
        return True

    # Validate start_ms <= end_ms
    if start_ms > end_ms:
        _validate_logger.warning(
            f"Invalid time range: start_ms={start_ms} > end_ms={end_ms}. "
            f"start={datetime.fromtimestamp(start_ms / 1000, tz=timezone.utc).isoformat()}, "
            f"end={datetime.fromtimestamp(end_ms / 1000, tz=timezone.utc).isoformat()}"
        )
        if raise_on_error:
            raise ValueError(f"Invalid time range: start_ms={start_ms} > end_ms={end_ms}")
        return False

    # Validate timestamps in reasonable range (1970-01-01 to 2100-01-01)
    min_ts = 0  # 1970-01-01 00:00:00 UTC
    max_ts = 4102444800000  # 2100-01-01 00:00:00 UTC

    if not (min_ts <= start_ms <= max_ts and min_ts <= end_ms <= max_ts):
        _validate_logger.warning(f"Time range out of bounds: start_ms={start_ms}, end_ms={end_ms}")
        if raise_on_error:
            raise ValueError(f"Time range out of bounds: start_ms={start_ms}, end_ms={end_ms}")
        return False

    return True
