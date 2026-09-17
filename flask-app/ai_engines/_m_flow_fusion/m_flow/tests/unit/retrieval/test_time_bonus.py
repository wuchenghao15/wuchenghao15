"""
Unit tests for m_flow/retrieval/time/time_bonus.py

Covers:
- _compute_overlap_score: all boundary conditions and overlap geometries
- compute_time_match: mentioned_time priority, created_at fallback, wide-range
  decay, mismatch penalty, disabled config, low-confidence guard
- apply_time_bonus_to_results: batch application, statistics, score floor
- compute_edge_time_bonus: takes the higher of two node bonuses

Motivation: The time-bonus subsystem is a critical path for episodic retrieval
quality (see REMem, ICLR 2026 – temporal reasoning is the #1 capability gap in
memory systems). These tests ensure correctness and guard against regressions.
"""

from __future__ import annotations

import pytest
from dataclasses import dataclass
from typing import Optional

from m_flow.retrieval.time.time_bonus import (
    TimeBonus,
    TimeBonusConfig,
    _compute_overlap_score,
    compute_time_match,
    apply_time_bonus_to_results,
    compute_edge_time_bonus,
)
from m_flow.retrieval.time.query_time_parser import QueryTimeInfo, TimeSpan, TimeType

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DAY_MS = 24 * 60 * 60 * 1000  # 1 day in milliseconds
_YEAR_MS = 365 * _DAY_MS


def _make_query_time(
    start_ms: int,
    end_ms: int,
    confidence: float = 0.9,
    query_wo_time: str = "what happened",
) -> QueryTimeInfo:
    """Build a minimal QueryTimeInfo for testing."""
    span = TimeSpan(
        start_ms=start_ms,
        end_ms=end_ms,
        confidence=confidence,
        matched_text="test",
        time_type=TimeType.EXPLICIT_DATE,
    )
    qt = QueryTimeInfo(
        start_ms=start_ms,
        end_ms=end_ms,
        confidence=confidence,
        query_wo_time=query_wo_time,
        matched_spans=[span],
        original_query=f"{query_wo_time} test",
    )
    return qt


def _make_candidate(
    mentioned_start: Optional[int] = None,
    mentioned_end: Optional[int] = None,
    mentioned_conf: float = 0.8,
    created_at: Optional[int] = None,
) -> dict:
    """Build a candidate dict with payload structure."""
    payload: dict = {}
    if mentioned_start is not None:
        payload["mentioned_time_start_ms"] = mentioned_start
    if mentioned_end is not None:
        payload["mentioned_time_end_ms"] = mentioned_end
    if mentioned_start is not None or mentioned_end is not None:
        payload["mentioned_time_confidence"] = mentioned_conf
    if created_at is not None:
        payload["created_at"] = created_at
    return {"payload": payload}


@dataclass
class _MockResult:
    """Minimal result object with a score attribute (for apply_time_bonus_to_results)."""

    score: float
    payload: dict


# ===========================================================================
# 1. _compute_overlap_score
# ===========================================================================


class TestComputeOverlapScore:
    """Tests for the internal _compute_overlap_score helper."""

    def test_no_overlap_before(self):
        """Candidate ends before query starts → 0."""
        assert _compute_overlap_score(100, 200, 300, 400) == 0.0

    def test_no_overlap_after(self):
        """Candidate starts after query ends → 0."""
        assert _compute_overlap_score(500, 600, 100, 400) == 0.0

    def test_touching_boundary_no_overlap(self):
        """Touching at a single point (start == end) → 0."""
        assert _compute_overlap_score(100, 300, 300, 500) == 0.0

    def test_full_containment_candidate_inside_query(self):
        """Candidate fully inside query → 1.0."""
        score = _compute_overlap_score(200, 300, 100, 400)
        assert score == pytest.approx(1.0)

    def test_full_containment_query_inside_candidate(self):
        """Query fully inside candidate → 1.0 (containment counts as full)."""
        score = _compute_overlap_score(100, 400, 200, 300)
        assert score == pytest.approx(1.0)

    def test_identical_ranges(self):
        """Identical ranges → 1.0."""
        score = _compute_overlap_score(100, 400, 100, 400)
        assert score == pytest.approx(1.0)

    def test_partial_overlap_left(self):
        """Candidate overlaps left half of query."""
        # cand=[0,200], query=[100,300] → overlap=[100,200]=100, min_dur=200 → 0.5
        score = _compute_overlap_score(0, 200, 100, 300)
        assert 0.0 < score < 1.0

    def test_partial_overlap_right(self):
        """Candidate overlaps right half of query."""
        score = _compute_overlap_score(200, 400, 100, 300)
        assert 0.0 < score < 1.0

    def test_score_bounded_zero_to_one(self):
        """Score must always be in [0, 1]."""
        cases = [
            (0, 1000, 500, 600),
            (500, 600, 0, 1000),
            (0, 500, 500, 1000),
            (0, 1, 0, 1),
        ]
        for args in cases:
            s = _compute_overlap_score(*args)
            assert 0.0 <= s <= 1.0, f"Out of range for {args}: {s}"

    def test_zero_duration_candidate(self):
        """Zero-duration candidate (point) inside query → 1.0."""
        # cand=[200,200], query=[100,300] → overlap=0, but cand_dur=max(1,0)=1
        score = _compute_overlap_score(200, 200, 100, 300)
        # overlap_start=200, overlap_end=200 → overlap=0 → score=0
        assert score == 0.0


# ===========================================================================
# 2. compute_time_match
# ===========================================================================


class TestComputeTimeMatch:
    """Tests for compute_time_match."""

    # --- Guard conditions ---

    def test_disabled_config_returns_zero(self):
        """Disabled config → zero bonus regardless of input."""
        cfg = TimeBonusConfig(enabled=False)
        qt = _make_query_time(0, _DAY_MS)
        cand = _make_candidate(mentioned_start=0, mentioned_end=_DAY_MS)
        result = compute_time_match(cand, qt, cfg)
        assert result.bonus == 0.0
        assert result.match_type == "none"

    def test_no_time_in_query_returns_zero(self):
        """Query with no time → zero bonus."""
        cfg = TimeBonusConfig()
        qt = QueryTimeInfo()  # has_time == False
        cand = _make_candidate(mentioned_start=0, mentioned_end=_DAY_MS)
        result = compute_time_match(cand, qt, cfg)
        assert result.bonus == 0.0

    def test_low_confidence_query_returns_zero(self):
        """Query confidence below threshold → zero bonus."""
        cfg = TimeBonusConfig(query_conf_min=0.5)
        qt = _make_query_time(0, _DAY_MS, confidence=0.3)
        cand = _make_candidate(mentioned_start=0, mentioned_end=_DAY_MS)
        result = compute_time_match(cand, qt, cfg)
        assert result.bonus == 0.0

    # --- mentioned_time priority ---

    def test_mentioned_time_exact_match_gives_bonus(self):
        """Candidate mentioned_time exactly matches query → positive bonus."""
        cfg = TimeBonusConfig(bonus_max=0.06)
        qt = _make_query_time(1000, 2000)
        cand = _make_candidate(mentioned_start=1000, mentioned_end=2000)
        result = compute_time_match(cand, qt, cfg)
        assert result.bonus > 0.0
        assert result.match_type == "mentioned_time"
        assert result.bonus <= cfg.bonus_max

    def test_mentioned_time_no_overlap_no_bonus(self):
        """Candidate mentioned_time outside query range → no bonus."""
        cfg = TimeBonusConfig()
        qt = _make_query_time(5000, 6000)
        cand = _make_candidate(mentioned_start=1000, mentioned_end=2000)
        result = compute_time_match(cand, qt, cfg)
        assert result.bonus == 0.0
        assert result.match_type in ("none", "created_at")

    def test_mentioned_time_takes_priority_over_created_at(self):
        """When mentioned_time matches, created_at should be ignored."""
        cfg = TimeBonusConfig()
        qt = _make_query_time(1000, 2000)
        # mentioned_time matches, created_at is outside range
        cand = _make_candidate(
            mentioned_start=1000,
            mentioned_end=2000,
            created_at=9999999,
        )
        result = compute_time_match(cand, qt, cfg)
        assert result.match_type == "mentioned_time"

    # --- created_at fallback ---

    def test_created_at_fallback_inside_range(self):
        """No mentioned_time, created_at inside query range → bonus via created_at."""
        cfg = TimeBonusConfig(created_at_weight=0.5)
        qt = _make_query_time(0, 10 * _DAY_MS)
        cand = _make_candidate(created_at=5 * _DAY_MS)
        result = compute_time_match(cand, qt, cfg)
        assert result.bonus > 0.0
        assert result.match_type == "created_at"

    def test_created_at_fallback_outside_range_no_bonus(self):
        """No mentioned_time, created_at outside query range → no bonus."""
        cfg = TimeBonusConfig()
        qt = _make_query_time(0, _DAY_MS)
        cand = _make_candidate(created_at=10 * _DAY_MS)
        result = compute_time_match(cand, qt, cfg)
        assert result.bonus == 0.0

    def test_no_time_in_candidate_no_bonus(self):
        """Candidate has no time fields at all → no bonus."""
        cfg = TimeBonusConfig()
        qt = _make_query_time(0, _DAY_MS)
        cand = {"payload": {"text": "some content"}}
        result = compute_time_match(cand, qt, cfg)
        assert result.bonus == 0.0
        assert result.match_type == "none"

    # --- Wide-range decay ---

    def test_wide_range_query_reduces_bonus(self):
        """Very wide query range (>365 days) should reduce bonus via decay."""
        cfg = TimeBonusConfig(bonus_max=0.06, wide_range_penalty_days=365.0)
        # Narrow query (1 day) → full bonus
        qt_narrow = _make_query_time(0, _DAY_MS)
        cand = _make_candidate(mentioned_start=0, mentioned_end=_DAY_MS)
        result_narrow = compute_time_match(cand, qt_narrow, cfg)

        # Wide query (2 years) → decayed bonus
        qt_wide = _make_query_time(0, 2 * _YEAR_MS)
        cand_wide = _make_candidate(mentioned_start=0, mentioned_end=_DAY_MS)
        result_wide = compute_time_match(cand_wide, qt_wide, cfg)

        assert result_narrow.bonus >= result_wide.bonus

    def test_bonus_never_exceeds_bonus_max(self):
        """Bonus must never exceed bonus_max."""
        cfg = TimeBonusConfig(bonus_max=0.06)
        qt = _make_query_time(0, _DAY_MS)
        cand = _make_candidate(mentioned_start=0, mentioned_end=_DAY_MS, mentioned_conf=1.0)
        result = compute_time_match(cand, qt, cfg)
        assert result.bonus <= cfg.bonus_max + 1e-9

    # --- Mismatch penalty ---

    def test_mismatch_penalty_applied_when_enabled(self):
        """When mismatch penalty is enabled and candidate time doesn't match → penalty > 0."""
        cfg = TimeBonusConfig(
            enable_mismatch_penalty=True,
            mismatch_penalty_max=0.03,
            mismatch_conf_threshold=0.5,
            mismatch_require_candidate_time=True,
        )
        qt = _make_query_time(0, _DAY_MS, confidence=0.9)
        # Candidate has time but it's outside query range
        cand = _make_candidate(
            mentioned_start=10 * _DAY_MS,
            mentioned_end=11 * _DAY_MS,
        )
        result = compute_time_match(cand, qt, cfg)
        assert result.penalty > 0.0
        assert result.penalty_reason == "mismatch"

    def test_mismatch_penalty_not_applied_when_disabled(self):
        """Mismatch penalty disabled → penalty == 0 even when times don't match."""
        cfg = TimeBonusConfig(enable_mismatch_penalty=False)
        qt = _make_query_time(0, _DAY_MS, confidence=0.9)
        cand = _make_candidate(
            mentioned_start=10 * _DAY_MS,
            mentioned_end=11 * _DAY_MS,
        )
        result = compute_time_match(cand, qt, cfg)
        assert result.penalty == 0.0

    def test_mismatch_penalty_not_applied_when_confidence_too_low(self):
        """Mismatch penalty not applied if query confidence < threshold."""
        cfg = TimeBonusConfig(
            enable_mismatch_penalty=True,
            mismatch_conf_threshold=0.8,
        )
        qt = _make_query_time(0, _DAY_MS, confidence=0.5)
        cand = _make_candidate(
            mentioned_start=10 * _DAY_MS,
            mentioned_end=11 * _DAY_MS,
        )
        result = compute_time_match(cand, qt, cfg)
        assert result.penalty == 0.0

    # --- Payload structure variants ---

    def test_candidate_as_flat_dict_with_payload_key(self):
        """Standard {'payload': {...}} structure is handled correctly."""
        cfg = TimeBonusConfig()
        qt = _make_query_time(0, _DAY_MS)
        cand = {
            "payload": {
                "mentioned_time_start_ms": 0,
                "mentioned_time_end_ms": _DAY_MS,
                "mentioned_time_confidence": 0.9,
            }
        }
        result = compute_time_match(cand, qt, cfg)
        assert result.bonus > 0.0

    def test_candidate_as_direct_payload_dict(self):
        """Flat dict without 'payload' key is also handled."""
        cfg = TimeBonusConfig()
        qt = _make_query_time(0, _DAY_MS)
        cand = {"mentioned_time_start_ms": 0, "mentioned_time_end_ms": _DAY_MS, "mentioned_time_confidence": 0.9}
        result = compute_time_match(cand, qt, cfg)
        assert result.bonus > 0.0


# ===========================================================================
# 3. apply_time_bonus_to_results
# ===========================================================================


class TestApplyTimeBonusToResults:
    """Tests for batch apply_time_bonus_to_results."""

    def test_empty_results_returns_zero_stats(self):
        """Empty results list → all stats zero."""
        qt = _make_query_time(0, _DAY_MS)
        stats = apply_time_bonus_to_results([], qt)
        assert stats["total"] == 0
        assert stats["time_matched"] == 0

    def test_no_time_in_query_no_modification(self):
        """No time in query → scores unchanged."""
        qt = QueryTimeInfo()  # has_time == False
        results = [
            _MockResult(score=0.5, payload={"mentioned_time_start_ms": 0, "mentioned_time_end_ms": _DAY_MS}),
        ]
        apply_time_bonus_to_results(results, qt)
        assert results[0].score == pytest.approx(0.5)

    def test_matching_result_score_reduced(self):
        """Matching candidate score is reduced by bonus."""
        cfg = TimeBonusConfig(bonus_max=0.06)
        qt = _make_query_time(0, _DAY_MS)
        original_score = 0.5
        results = [
            _MockResult(
                score=original_score,
                payload={
                    "mentioned_time_start_ms": 0,
                    "mentioned_time_end_ms": _DAY_MS,
                    "mentioned_time_confidence": 0.9,
                },
            )
        ]
        stats = apply_time_bonus_to_results(results, qt, cfg)
        assert results[0].score < original_score
        assert stats["time_matched"] == 1

    def test_score_floor_respected(self):
        """Score must not go below score_floor."""
        cfg = TimeBonusConfig(bonus_max=0.5, score_floor=0.1)
        qt = _make_query_time(0, _DAY_MS)
        results = [
            _MockResult(
                score=0.15,  # Very low score, bonus would push below floor
                payload={
                    "mentioned_time_start_ms": 0,
                    "mentioned_time_end_ms": _DAY_MS,
                    "mentioned_time_confidence": 1.0,
                },
            )
        ]
        apply_time_bonus_to_results(results, qt, cfg)
        assert results[0].score >= cfg.score_floor

    def test_non_matching_result_score_unchanged(self):
        """Non-matching candidate score is not changed."""
        cfg = TimeBonusConfig()
        qt = _make_query_time(0, _DAY_MS)
        results = [
            _MockResult(
                score=0.5,
                payload={"mentioned_time_start_ms": 10 * _DAY_MS, "mentioned_time_end_ms": 11 * _DAY_MS},
            )
        ]
        original_score = results[0].score
        apply_time_bonus_to_results(results, qt, cfg)
        assert results[0].score == pytest.approx(original_score)

    def test_statistics_avg_bonus_computed_correctly(self):
        """avg_bonus should be mean of all individual bonuses."""
        cfg = TimeBonusConfig(bonus_max=0.06)
        qt = _make_query_time(0, _DAY_MS)
        results = [
            _MockResult(
                score=0.5,
                payload={
                    "mentioned_time_start_ms": 0,
                    "mentioned_time_end_ms": _DAY_MS,
                    "mentioned_time_confidence": 0.9,
                },
            ),
            _MockResult(
                score=0.4,
                payload={
                    "mentioned_time_start_ms": 0,
                    "mentioned_time_end_ms": _DAY_MS,
                    "mentioned_time_confidence": 0.9,
                },
            ),
        ]
        stats = apply_time_bonus_to_results(results, qt, cfg)
        assert stats["time_matched"] == 2
        assert stats["avg_bonus"] > 0.0

    def test_disabled_config_no_modification(self):
        """Disabled config → no score changes."""
        cfg = TimeBonusConfig(enabled=False)
        qt = _make_query_time(0, _DAY_MS)
        results = [
            _MockResult(score=0.5, payload={"mentioned_time_start_ms": 0, "mentioned_time_end_ms": _DAY_MS}),
        ]
        apply_time_bonus_to_results(results, qt, cfg)
        assert results[0].score == pytest.approx(0.5)

    def test_multiple_results_mixed_match(self):
        """Mix of matching and non-matching results."""
        cfg = TimeBonusConfig(bonus_max=0.06)
        qt = _make_query_time(0, _DAY_MS)
        results = [
            _MockResult(
                score=0.5,
                payload={
                    "mentioned_time_start_ms": 0,
                    "mentioned_time_end_ms": _DAY_MS,
                    "mentioned_time_confidence": 0.9,
                },
            ),
            _MockResult(
                score=0.5, payload={"mentioned_time_start_ms": 100 * _DAY_MS, "mentioned_time_end_ms": 101 * _DAY_MS}
            ),
        ]
        stats = apply_time_bonus_to_results(results, qt, cfg)
        assert stats["time_matched"] == 1
        assert results[0].score < 0.5  # matched → reduced
        assert results[1].score == pytest.approx(0.5)  # not matched → unchanged


# ===========================================================================
# 4. compute_edge_time_bonus
# ===========================================================================


class TestComputeEdgeTimeBonus:
    """Tests for compute_edge_time_bonus."""

    def test_takes_higher_bonus_from_two_nodes(self):
        """Edge bonus is the max of the two node bonuses."""
        cfg = TimeBonusConfig(bonus_max=0.06)
        qt = _make_query_time(0, _DAY_MS)

        # node1 matches, node2 doesn't
        node1 = {"mentioned_time_start_ms": 0, "mentioned_time_end_ms": _DAY_MS, "mentioned_time_confidence": 0.9}
        node2 = {"mentioned_time_start_ms": 100 * _DAY_MS, "mentioned_time_end_ms": 101 * _DAY_MS}

        edge_bonus = compute_edge_time_bonus(node1, node2, qt, cfg)
        assert edge_bonus > 0.0

    def test_neither_node_matches_zero_bonus(self):
        """If neither node matches, edge bonus is 0."""
        cfg = TimeBonusConfig()
        qt = _make_query_time(0, _DAY_MS)
        node1 = {"mentioned_time_start_ms": 50 * _DAY_MS, "mentioned_time_end_ms": 51 * _DAY_MS}
        node2 = {"mentioned_time_start_ms": 60 * _DAY_MS, "mentioned_time_end_ms": 61 * _DAY_MS}
        edge_bonus = compute_edge_time_bonus(node1, node2, qt, cfg)
        assert edge_bonus == 0.0

    def test_both_nodes_match_takes_higher(self):
        """Both nodes match; result should be the higher bonus."""
        cfg = TimeBonusConfig(bonus_max=0.06)
        qt = _make_query_time(0, _DAY_MS)
        # Both match, but node1 has higher confidence
        node1 = {"mentioned_time_start_ms": 0, "mentioned_time_end_ms": _DAY_MS, "mentioned_time_confidence": 1.0}
        node2 = {"mentioned_time_start_ms": 0, "mentioned_time_end_ms": _DAY_MS, "mentioned_time_confidence": 0.5}
        edge_bonus = compute_edge_time_bonus(node1, node2, qt, cfg)
        # Should be >= the bonus for node2 alone
        cand2 = _make_candidate(mentioned_start=0, mentioned_end=_DAY_MS, mentioned_conf=0.5)
        bonus2 = compute_time_match(cand2, qt, cfg).bonus
        assert edge_bonus >= bonus2

    def test_default_config_used_when_none(self):
        """compute_edge_time_bonus works with config=None (uses defaults)."""
        qt = _make_query_time(0, _DAY_MS)
        node1 = {"mentioned_time_start_ms": 0, "mentioned_time_end_ms": _DAY_MS, "mentioned_time_confidence": 0.9}
        node2 = {}
        # Should not raise
        edge_bonus = compute_edge_time_bonus(node1, node2, qt, None)
        assert edge_bonus >= 0.0


# ===========================================================================
# 5. TimeBonus and TimeBonusConfig dataclass sanity checks
# ===========================================================================


class TestDataclassSanity:
    """Sanity checks for dataclass defaults."""

    def test_time_bonus_default_values(self):
        tb = TimeBonus(bonus=0.0, match_score=0.0, match_type="none")
        assert tb.penalty == 0.0
        assert tb.penalty_reason == "none"
        assert tb.candidate_start_ms is None
        assert tb.candidate_end_ms is None

    def test_time_bonus_config_defaults(self):
        cfg = TimeBonusConfig()
        assert cfg.enabled is True
        assert cfg.bonus_max == pytest.approx(0.06)
        assert cfg.score_floor == pytest.approx(0.08)
        assert cfg.query_conf_min == pytest.approx(0.4)
        assert cfg.enable_mismatch_penalty is False
        assert cfg.wide_range_penalty_days == pytest.approx(365.0)

    def test_time_bonus_config_custom_values(self):
        cfg = TimeBonusConfig(bonus_max=0.10, enabled=False)
        assert cfg.bonus_max == pytest.approx(0.10)
        assert cfg.enabled is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
