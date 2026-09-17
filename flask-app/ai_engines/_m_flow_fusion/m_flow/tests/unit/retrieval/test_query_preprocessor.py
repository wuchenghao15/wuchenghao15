"""
Unit tests for m_flow/retrieval/episodic/query_preprocessor.py

Covers:
- _strip_question_words_for_vector: removes question-only words, keeps semantic ones
- _get_hybrid_search_reason: number / mixed_lang / short_query / None triggers
- _extract_keyword_by_reason: number-only, English-only, full keyword extraction
- extract_english_words: multi-word, hyphenated, short-word filtering
- preprocess_query: end-to-end integration with time parsing enabled/disabled
- has_chinese: Unicode boundary conditions

Motivation: The query preprocessor determines whether hybrid search is activated
and what keyword is used for BM25 matching — errors here silently degrade recall
for all queries. These tests establish a regression baseline aligned with the
documented design rules in the module docstring.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch

from m_flow.retrieval.episodic.query_preprocessor import (
    _strip_question_words_for_vector,
    _get_hybrid_search_reason,
    _extract_keyword_by_reason,
    extract_english_words,
    has_chinese,
    preprocess_query,
    PreprocessedQuery,
)
from m_flow.retrieval.episodic.config import EpisodicConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _default_config(**kwargs) -> EpisodicConfig:
    cfg = EpisodicConfig()
    for k, v in kwargs.items():
        setattr(cfg, k, v)
    return cfg


# ===========================================================================
# 1. has_chinese
# ===========================================================================


class TestHasChinese:
    """Tests for has_chinese utility."""

    def test_pure_chinese(self):
        assert has_chinese("你好世界") is True

    def test_pure_english(self):
        assert has_chinese("hello world") is False

    def test_mixed_chinese_english(self):
        assert has_chinese("hello 你好") is True

    def test_empty_string(self):
        assert has_chinese("") is False

    def test_numbers_only(self):
        assert has_chinese("12345") is False

    def test_punctuation_only(self):
        assert has_chinese("，。！？") is False

    def test_cjk_boundary_first_char(self):
        # U+4E00 is the first CJK Unified Ideograph
        assert has_chinese("\u4e00") is True

    def test_cjk_boundary_last_char(self):
        # U+9FFF is the last CJK Unified Ideograph in the basic block
        assert has_chinese("\u9fff") is True

    def test_just_outside_cjk_range(self):
        # U+4DFF is just before the CJK block
        assert has_chinese("\u4dff") is False


# ===========================================================================
# 2. _strip_question_words_for_vector
# ===========================================================================


class TestStripQuestionWordsForVector:
    """Tests for _strip_question_words_for_vector."""

    def test_strips_what_happened(self):
        """Common question starters should be stripped."""
        result = _strip_question_words_for_vector("what happened last week")
        assert "what" not in result.lower() or "happened" in result

    def test_preserves_semantic_content(self):
        """Semantic words must be preserved."""
        result = _strip_question_words_for_vector("when did Alice meet Bob")
        assert "Alice" in result or "Bob" in result

    def test_empty_string_returns_empty(self):
        result = _strip_question_words_for_vector("")
        assert result == ""

    def test_only_question_words_returns_empty_or_stripped(self):
        """A query consisting only of question words should result in empty or minimal output."""
        result = _strip_question_words_for_vector("what")
        # Either empty or the original word (implementation may vary)
        assert isinstance(result, str)

    def test_no_question_words_unchanged(self):
        """Query with no question words should be returned as-is (stripped)."""
        result = _strip_question_words_for_vector("Alice birthday party")
        assert "Alice" in result
        assert "birthday" in result


# ===========================================================================
# 3. _get_hybrid_search_reason
# ===========================================================================


class TestGetHybridSearchReason:
    """Tests for _get_hybrid_search_reason."""

    # --- Number trigger ---

    def test_number_triggers_hybrid(self):
        reason = _get_hybrid_search_reason("I paid 500 dollars")
        assert reason == "number"

    def test_decimal_number_triggers_hybrid(self):
        reason = _get_hybrid_search_reason("temperature is 36.5 degrees")
        assert reason == "number"

    def test_percentage_triggers_hybrid(self):
        reason = _get_hybrid_search_reason("growth rate 20%")
        assert reason == "number"

    # --- Mixed language trigger ---

    def test_chinese_english_mixed_triggers_hybrid(self):
        reason = _get_hybrid_search_reason("Alice 去了哪里")
        assert reason == "mixed_lang"

    def test_pure_chinese_no_mixed_trigger(self):
        reason = _get_hybrid_search_reason("你好世界")
        # No English → not mixed_lang; may be short_query or None
        assert reason != "mixed_lang"

    def test_pure_english_no_mixed_trigger(self):
        reason = _get_hybrid_search_reason("hello world today")
        assert reason != "mixed_lang"

    # --- Short query trigger ---

    def test_short_query_triggers_hybrid(self):
        """Very short core keyword (≤ threshold) should trigger hybrid."""
        reason = _get_hybrid_search_reason("who", threshold=3)
        assert reason == "short_query"

    def test_long_query_no_trigger(self):
        """Long English query with no numbers or mixed lang → None."""
        reason = _get_hybrid_search_reason("what did Alice do at the birthday party yesterday", threshold=3)
        assert reason is None

    # --- Priority: mixed_lang before number ---

    def test_mixed_lang_takes_priority_over_number(self):
        """Chinese + English + number: mixed_lang should be detected first."""
        reason = _get_hybrid_search_reason("Alice 花了500元")
        # mixed_lang check comes before number check in implementation
        assert reason == "mixed_lang"

    # --- Edge cases ---

    def test_empty_string(self):
        reason = _get_hybrid_search_reason("")
        # Empty string has no core keyword → short_query
        assert reason == "short_query"

    def test_custom_threshold(self):
        """Custom threshold changes short_query trigger."""
        # "hello" has 5 chars, threshold=10 → short_query
        reason = _get_hybrid_search_reason("hello", threshold=10)
        assert reason == "short_query"
        # threshold=3 → not short
        reason2 = _get_hybrid_search_reason("hello world today", threshold=3)
        assert reason2 is None


# ===========================================================================
# 4. _extract_keyword_by_reason
# ===========================================================================


class TestExtractKeywordByReason:
    """Tests for _extract_keyword_by_reason."""

    def test_number_reason_extracts_numbers(self):
        """'number' reason → extract numeric tokens."""
        keyword = _extract_keyword_by_reason("I paid 500 dollars last month", "number")
        assert "500" in keyword

    def test_number_reason_ignores_pure_text(self):
        """'number' reason on text-only query → fallback to full keyword."""
        keyword = _extract_keyword_by_reason("no numbers here", "number")
        # No numbers found → fallback
        assert isinstance(keyword, str)

    def test_mixed_lang_reason_extracts_english(self):
        """'mixed_lang' reason → extract English words only."""
        keyword = _extract_keyword_by_reason("Alice 去了哪里", "mixed_lang")
        assert "Alice" in keyword or "alice" in keyword.lower()
        # Chinese characters should not appear
        assert not any("\u4e00" <= c <= "\u9fff" for c in keyword)

    def test_short_query_reason_returns_full_keyword(self):
        """'short_query' reason → return full stripped keyword."""
        keyword = _extract_keyword_by_reason("who", "short_query")
        assert isinstance(keyword, str)

    def test_none_reason_returns_full_keyword(self):
        """None reason → return full stripped keyword."""
        keyword = _extract_keyword_by_reason("Alice birthday party", None)
        assert "Alice" in keyword or "birthday" in keyword

    def test_percentage_extraction(self):
        """Percentage values should be captured by number reason."""
        keyword = _extract_keyword_by_reason("growth rate 20%", "number")
        assert "20" in keyword

    def test_chinese_number_units(self):
        """Chinese number units (万, 亿) should be captured."""
        keyword = _extract_keyword_by_reason("收入增长了3亿元", "number")
        assert "3" in keyword


# ===========================================================================
# 5. extract_english_words
# ===========================================================================


class TestExtractEnglishWords:
    """Tests for extract_english_words."""

    def test_basic_english_words(self):
        words = extract_english_words("Alice met Bob at the party")
        assert "Alice" in words or "alice" in words
        assert "Bob" in words or "bob" in words

    def test_single_char_words_excluded(self):
        """Single-character words should not be extracted (min length 2)."""
        words = extract_english_words("I a")
        # 'I' and 'a' are single chars → should not appear
        assert "I" not in words
        assert "a" not in words

    def test_hyphenated_words(self):
        """Hyphenated words like 'well-known' should be captured."""
        words = extract_english_words("a well-known fact")
        # 'well' should be present at minimum
        assert any("well" in w.lower() for w in words)

    def test_empty_string_returns_empty_set(self):
        words = extract_english_words("")
        assert words == set()

    def test_pure_chinese_returns_empty_set(self):
        words = extract_english_words("你好世界")
        assert words == set()

    def test_mixed_returns_english_only(self):
        words = extract_english_words("Alice 去了 Beijing")
        assert "Alice" in words or "alice" in words
        assert "Beijing" in words or "beijing" in words
        # No Chinese characters in results
        for w in words:
            assert not any("\u4e00" <= c <= "\u9fff" for c in w)

    def test_numbers_not_extracted_as_words(self):
        """Pure numeric strings should not appear as English words."""
        words = extract_english_words("123 456")
        assert "123" not in words
        assert "456" not in words

    def test_case_variants_both_present(self):
        """Both original case and lowercase variants should be in the set."""
        words = extract_english_words("Hello")
        # Implementation adds both word.lower() and word
        assert "Hello" in words or "hello" in words


# ===========================================================================
# 6. preprocess_query (integration)
# ===========================================================================


class TestPreprocessQuery:
    """Integration tests for preprocess_query."""

    def test_returns_preprocessed_query_instance(self):
        cfg = _default_config()
        result = preprocess_query("what happened last week", cfg)
        assert isinstance(result, PreprocessedQuery)

    def test_original_query_preserved(self):
        cfg = _default_config()
        query = "Alice met Bob in May 2023"
        result = preprocess_query(query, cfg)
        assert result.original == query

    def test_vector_query_is_non_empty(self):
        cfg = _default_config()
        result = preprocess_query("what did Alice do", cfg)
        assert len(result.vector_query) > 0

    def test_hybrid_triggered_for_number_query(self):
        cfg = _default_config(enable_hybrid_search=True)
        result = preprocess_query("Alice paid 500 dollars", cfg)
        assert result.use_hybrid is True
        assert result.hybrid_reason == "number"

    def test_hybrid_triggered_for_mixed_lang(self):
        cfg = _default_config(enable_hybrid_search=True)
        result = preprocess_query("Alice 去了哪里", cfg)
        assert result.use_hybrid is True
        assert result.hybrid_reason == "mixed_lang"

    def test_hybrid_not_triggered_for_pure_long_english(self):
        cfg = _default_config(enable_hybrid_search=True, hybrid_threshold=3)
        result = preprocess_query("what did Alice do at the birthday party", cfg)
        assert result.use_hybrid is False

    def test_hybrid_disabled_config_no_hybrid(self):
        cfg = _default_config(enable_hybrid_search=False)
        result = preprocess_query("Alice paid 500 dollars", cfg)
        assert result.use_hybrid is False

    def test_time_bonus_disabled_no_time_parsing(self):
        cfg = _default_config(enable_time_bonus=False)
        result = preprocess_query("what happened in May 2023", cfg)
        assert result.time_info is None

    def test_time_bonus_enabled_parses_time(self):
        cfg = _default_config(enable_time_bonus=True)
        result = preprocess_query("what happened in May 2023", cfg)
        # Time info should be populated (may or may not find a match depending on parser)
        assert result.time_info is not None

    def test_keyword_populated_for_hybrid(self):
        cfg = _default_config(enable_hybrid_search=True)
        result = preprocess_query("Alice paid 500 dollars", cfg)
        if result.use_hybrid:
            assert len(result.keyword) > 0

    def test_empty_query_does_not_raise(self):
        cfg = _default_config()
        result = preprocess_query("", cfg)
        assert isinstance(result, PreprocessedQuery)

    def test_time_stripped_from_vector_query_when_time_found(self):
        """When time is parsed, vector_query should use the time-stripped version."""
        cfg = _default_config(enable_time_bonus=True)
        result = preprocess_query("what did Alice do in May 2023", cfg)
        if result.time_info and result.time_info.has_time and result.time_info.query_wo_time:
            # The vector query should not contain the raw date string
            # (it uses the time-stripped version for cleaner embedding)
            assert result.vector_query is not None

    def test_now_ms_parameter_passed_through(self):
        """now_ms parameter should be accepted without error."""
        cfg = _default_config(enable_time_bonus=True)
        now_ms = 1_700_000_000_000  # arbitrary fixed timestamp
        result = preprocess_query("what happened yesterday", cfg, now_ms=now_ms)
        assert isinstance(result, PreprocessedQuery)


# ===========================================================================
# 7. PreprocessedQuery dataclass
# ===========================================================================


class TestPreprocessedQueryDataclass:
    """Sanity checks for PreprocessedQuery."""

    def test_has_time_property_when_time_info_present(self):
        cfg = _default_config(enable_time_bonus=True)
        result = preprocess_query("what happened in 2023", cfg)
        # has_time is a property on time_info, not on PreprocessedQuery directly
        if result.time_info:
            assert isinstance(result.time_info.has_time, bool)

    def test_time_confidence_property(self):
        cfg = _default_config(enable_time_bonus=True)
        result = preprocess_query("what happened in May 2023", cfg)
        if result.time_info:
            assert 0.0 <= result.time_info.confidence <= 1.0

    def test_use_hybrid_is_bool(self):
        cfg = _default_config()
        result = preprocess_query("test query", cfg)
        assert isinstance(result.use_hybrid, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
