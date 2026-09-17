"""
Query preprocessing module.

Responsible for:
- Time expression parsing and stripping (time enhancement)
- Question word removal
- Hybrid retrieval determination
- Keyword extraction
"""

import re
from dataclasses import dataclass
from typing import Optional, Set

from .config import EpisodicConfig
from m_flow.retrieval.time.query_time_parser import (
    parse_query_time,
    QueryTimeInfo,
)


# Question words to strip (no semantic value for vector retrieval)
_STRIP_QUESTION_WORDS = [
    "是什么",
    "是啥",
    "什么是",
    "啥是",
    "怎么做",
    "怎样做",
    "如何做",
    "为什么",
    "为啥",
    "怎么",
    "怎样",
    "如何",
    "吗",
    "呢",
    "？",
    "?",
]

# Question words to keep (have semantic value)
_KEEP_QUESTION_WORDS = [
    "多少",
    "几个",
    "几条",
    "几项",
    "哪些",
    "哪个",
    "哪里",
    "哪儿",
    "多久",
    "多长",
    "多大",
    "多高",
    "什么时候",
    "何时",
]

_ALL_QUESTION_WORDS = _STRIP_QUESTION_WORDS + _KEEP_QUESTION_WORDS


@dataclass
class PreprocessedQuery:
    """Preprocessed query."""

    original: str  # Original query
    vector_query: str  # Query for vector retrieval (stripped question words + time expressions)
    keyword: str  # Keyword for keyword matching
    hybrid_reason: Optional[str]  # Hybrid retrieval trigger reason: "number" | "mixed_lang" | "short_query" | None
    use_hybrid: bool  # Whether to use hybrid retrieval

    # Time enhancement fields
    time_info: Optional[QueryTimeInfo] = None  # Time parsing result

    @property
    def has_time(self) -> bool:
        """Whether valid time identified."""
        return self.time_info is not None and self.time_info.has_time

    @property
    def time_start_ms(self) -> Optional[int]:
        """Time range start (milliseconds)."""
        return self.time_info.start_ms if self.time_info else None

    @property
    def time_end_ms(self) -> Optional[int]:
        """Time range end (milliseconds)."""
        return self.time_info.end_ms if self.time_info else None

    @property
    def time_confidence(self) -> float:
        """Time parsing confidence."""
        return self.time_info.confidence if self.time_info else 0.0


def preprocess_query(
    query: str,
    config: EpisodicConfig,
    now_ms: Optional[int] = None,
) -> PreprocessedQuery:
    """
    Preprocess query text.

    Args:
        query: Original query
        config: Configuration object
        now_ms: Current timestamp (milliseconds), for parsing relative time

    Returns:
        PreprocessedQuery: Preprocessing result
    """
    # Time enhancement: parse time expressions first
    time_info: Optional[QueryTimeInfo] = None
    query_for_processing = query

    if config.enable_time_bonus:
        time_info = parse_query_time(query, now_ms=now_ms)
        # Use query without time for subsequent processing (avoid date numbers polluting hybrid/number bonus)
        if time_info.query_wo_time:
            query_for_processing = time_info.query_wo_time

    # 1. For vector retrieval: remove question words without semantic value
    vector_query = _strip_question_words_for_vector(query_for_processing)
    if not vector_query:
        vector_query = query_for_processing if query_for_processing else query

    # 2. Determine whether to enable hybrid retrieval (use query without time)
    hybrid_reason = _get_hybrid_search_reason(query_for_processing, config.hybrid_threshold)
    use_hybrid = config.enable_hybrid_search and hybrid_reason is not None

    # 3. Extract keyword based on trigger reason (use query without time)
    keyword = _extract_keyword_by_reason(query_for_processing, hybrid_reason)

    return PreprocessedQuery(
        original=query,
        vector_query=vector_query,
        keyword=keyword,
        hybrid_reason=hybrid_reason,
        use_hybrid=use_hybrid,
        time_info=time_info,
    )


def _strip_question_words_for_vector(query: str) -> str:
    """Remove question words without value for vector retrieval (keep those with semantic value)."""
    result = query
    for word in _STRIP_QUESTION_WORDS:
        result = result.replace(word, "")
    return result.strip()


def _strip_all_question_words(query: str) -> str:
    """Remove all question words (for keyword matching)."""
    result = query
    for word in _ALL_QUESTION_WORDS:
        result = result.replace(word, "")
    return result.strip()


def _get_core_keyword_length(query: str) -> int:
    """Get core keyword length after removing all question words."""
    core = _strip_all_question_words(query)
    core = re.sub(r"[\s，,。.；;：:！!]+", "", core)
    return len(core)


def _has_numbers(text: str) -> bool:
    """Check if text contains numbers."""
    return bool(re.search(r"\d", text))


def has_chinese(text: str) -> bool:
    """Check if text contains Chinese characters."""
    return bool(re.search(r"[\u4e00-\u9fff]", text))


# Alias
_has_chinese = has_chinese


def _is_mixed_chinese_english(text: str) -> bool:
    """Check if text is Chinese-English mixed."""
    return _has_chinese(text) and bool(re.search(r"[A-Za-z]", text))


def _get_hybrid_search_reason(query: str, threshold: int = 3) -> Optional[str]:
    """
    Determine whether to use hybrid retrieval and return trigger reason.

    Returns:
        - "number": Triggered by containing numbers
        - "mixed_lang": Triggered by Chinese-English mixed
        - "short_query": Triggered by core keyword too short
        - None: Don't need hybrid retrieval
    """
    # Rule 1: Chinese-English mixed
    if _is_mixed_chinese_english(query):
        return "mixed_lang"

    # Rule 2: Contains numbers
    if _has_numbers(query):
        return "number"

    # Rule 3: Core keyword too short
    core_len = _get_core_keyword_length(query)
    if core_len <= threshold:
        return "short_query"

    return None


def _extract_keyword_by_reason(query: str, reason: Optional[str]) -> str:
    """
    Extract keyword based on hybrid retrieval trigger reason.

    - "number": Only extract numbers and quantifiers
    - "mixed_lang": Only extract English part
    - "short_query" / None: Use full keyword
    """
    base_keyword = _strip_all_question_words(query)
    base_keyword = re.sub(r"[\s，,。.；;：:！!？?、]+", "", base_keyword)

    if reason == "number":
        pattern = r"\d+\.?\d*[%％]?[万亿千百十个元块美金日月年周天小时分秒倍次条个台件套人名位家批轮期季度]*"
        matches = re.findall(pattern, base_keyword)
        return "".join(matches) if matches else base_keyword

    elif reason == "mixed_lang":
        pattern = r"[A-Za-z][A-Za-z0-9]*"
        matches = re.findall(pattern, base_keyword)
        return "".join(matches) if matches else base_keyword

    return base_keyword


def extract_english_words(text: str) -> Set[str]:
    """Extract normalized English words from text (at least 2 characters)."""
    if not text:
        return set()

    words = set()
    pattern = r"[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9]|[A-Za-z]{2,}"
    for match in re.finditer(pattern, text):
        word = match.group(0)
        if len(word) >= 2:
            words.add(word.lower())

    return words
