"""
Unit tests for adaptive_scoring module - Phase 3 verification.

Tests:
1. f_dist function - distance factor
2. f_gap function - gap factor
3. compute_confidence function
4. compute_collection_stats function
5. compute_adaptive_context function
6. compute_lambda function
7. compute_struct_score function
8. compute_final_score function
"""

import pytest
from dataclasses import dataclass
from uuid import uuid4

from m_flow.retrieval.episodic.config import EpisodicConfig
from m_flow.retrieval.episodic.adaptive_scoring import (
    f_dist,
    f_gap,
    compute_confidence,
    compute_collection_stats,
    compute_adaptive_context,
    compute_lambda,
    compute_struct_score,
    compute_final_score,
    get_exact_match_bonus,
    CollectionStats,
)


# Mock VectorSearchHit for testing
@dataclass
class MockScoredResult:
    id: str
    score: float
    payload: dict
    raw_distance: float = None
    collection_name: str = None


class TestFDist:
    """Tests for f_dist function."""

    def test_perfect_match(self):
        """ratio=0 should return 1.0"""
        config = EpisodicConfig()
        assert f_dist(0.0, config) == 1.0

    def test_very_good_match(self):
        """ratio < 0.5 should return 1.0"""
        config = EpisodicConfig()
        assert f_dist(0.3, config) == 1.0
        assert f_dist(0.49, config) == 1.0

    def test_good_match(self):
        """ratio=0.75 should be between 0.5 and 1.0"""
        config = EpisodicConfig()
        result = f_dist(0.75, config)
        assert 0.5 < result < 1.0
        # Should be approximately 0.75
        assert abs(result - 0.75) < 0.01

    def test_average_match(self):
        """ratio=1.0 should return 0.5"""
        config = EpisodicConfig()
        assert f_dist(1.0, config) == 0.5

    def test_poor_match(self):
        """ratio=1.5 should return 0.3"""
        config = EpisodicConfig()
        assert f_dist(1.5, config) == 0.3

    def test_very_poor_match(self):
        """ratio > 1.5 should approach 0.1"""
        config = EpisodicConfig()
        result = f_dist(2.0, config)
        assert result >= 0.1
        assert result < 0.3

    def test_monotonicity(self):
        """f_dist should be monotonically decreasing"""
        config = EpisodicConfig()
        ratios = [0.0, 0.3, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
        values = [f_dist(r, config) for r in ratios]
        for i in range(len(values) - 1):
            assert values[i] >= values[i + 1], f"Not monotonic at {ratios[i]} -> {ratios[i + 1]}"


class TestFGap:
    """Tests for f_gap function."""

    def test_no_gap(self):
        """gap=0 should return 0.2"""
        config = EpisodicConfig()
        assert f_gap(0.0, config) == 0.2

    def test_trivial_gap(self):
        """gap at threshold should be continuous"""
        config = EpisodicConfig()
        # Just below threshold
        below = f_gap(0.0099, config)
        # Just above threshold
        above = f_gap(0.0101, config)
        # Should be continuous (difference < 0.05)
        assert abs(above - below) < 0.05

    def test_low_gap(self):
        """gap=0.05 should return approximately 0.6"""
        config = EpisodicConfig()
        result = f_gap(0.05, config)
        # At gap_low threshold, should be 0.6
        assert abs(result - 0.6) < 0.01

    def test_medium_gap(self):
        """gap=0.10 should be between 0.6 and 1.0"""
        config = EpisodicConfig()
        result = f_gap(0.10, config)
        assert 0.6 < result < 1.0

    def test_high_gap(self):
        """gap >= 0.15 should return 1.0"""
        config = EpisodicConfig()
        assert f_gap(0.15, config) == 1.0
        assert f_gap(0.20, config) == 1.0

    def test_monotonicity(self):
        """f_gap should be monotonically increasing"""
        config = EpisodicConfig()
        gaps = [0.0, 0.01, 0.03, 0.05, 0.10, 0.15, 0.20]
        values = [f_gap(g, config) for g in gaps]
        for i in range(len(values) - 1):
            assert values[i] <= values[i + 1], f"Not monotonic at {gaps[i]} -> {gaps[i + 1]}"

    def test_continuity_at_boundaries(self):
        """f_gap should be continuous at threshold boundaries"""
        config = EpisodicConfig()

        # At gap_trivial (0.01)
        below_trivial = f_gap(0.0099, config)
        above_trivial = f_gap(0.0101, config)
        assert abs(above_trivial - below_trivial) < 0.02

        # At gap_low (0.05)
        below_low = f_gap(0.0499, config)
        above_low = f_gap(0.0501, config)
        assert abs(above_low - below_low) < 0.02


class TestComputeConfidence:
    """Tests for compute_confidence function."""

    def test_perfect_match(self):
        """Perfect match should have high confidence"""
        config = EpisodicConfig()
        conf, ratio = compute_confidence(0.25, 0.5, 0.2, config)
        # ratio = 0.5, gap = 0.2 → high confidence
        assert conf > 0.8

    def test_poor_match(self):
        """Poor match should have low confidence"""
        config = EpisodicConfig()
        conf, ratio = compute_confidence(1.0, 0.5, 0.005, config)
        # ratio = 2.0, gap = 0.005 → low confidence
        assert conf < 0.3

    def test_confidence_range(self):
        """Confidence should always be in [0, 1]"""
        config = EpisodicConfig()

        test_cases = [
            (0.1, 0.5, 0.2),
            (0.5, 0.5, 0.1),
            (1.0, 0.5, 0.05),
            (1.5, 0.7, 0.01),
        ]

        for raw, baseline, gap in test_cases:
            conf, ratio = compute_confidence(raw, baseline, gap, config)
            assert 0 <= conf <= 1, f"Confidence out of range for raw={raw}, baseline={baseline}, gap={gap}"


class TestComputeCollectionStats:
    """Tests for compute_collection_stats function."""

    def test_with_valid_results(self):
        """Test with valid search results"""
        config = EpisodicConfig()

        results = {
            "FacetPoint_search_text": [
                MockScoredResult(
                    str(uuid4()),
                    0.0,
                    {},
                    raw_distance=0.35,
                    collection_name="FacetPoint_search_text",
                ),
                MockScoredResult(
                    str(uuid4()),
                    0.5,
                    {},
                    raw_distance=0.52,
                    collection_name="FacetPoint_search_text",
                ),
            ],
            "Entity_name": [
                MockScoredResult(str(uuid4()), 0.0, {}, raw_distance=0.40, collection_name="Entity_name"),
            ],
        }

        stats = compute_collection_stats(results, config)

        assert "FacetPoint_search_text" in stats
        assert "Entity_name" in stats

        fp_stats = stats["FacetPoint_search_text"]
        assert fp_stats.top1_raw_distance == 0.35
        assert fp_stats.gap == pytest.approx(0.17, rel=0.01)
        assert fp_stats.collection_type == "node"

    def test_with_none_raw_distance(self):
        """Test fallback when raw_distance is None"""
        config = EpisodicConfig()

        results = {
            "FacetPoint_search_text": [
                MockScoredResult(str(uuid4()), 0.0, {}, raw_distance=None),
            ],
        }

        stats = compute_collection_stats(results, config)

        # Should use baseline as fallback
        fp_stats = stats["FacetPoint_search_text"]
        assert fp_stats.top1_raw_distance == 0.5  # baseline for FacetPoint_search_text
        assert fp_stats.ratio == pytest.approx(1.0, rel=0.01)

    def test_empty_collection(self):
        """Test with empty results"""
        config = EpisodicConfig()

        results = {
            "FacetPoint_search_text": [],
        }

        stats = compute_collection_stats(results, config)

        # Empty collection should be skipped
        assert "FacetPoint_search_text" not in stats


class TestComputeAdaptiveContext:
    """Tests for compute_adaptive_context function."""

    def test_basic_context(self):
        """Test basic adaptive context computation"""
        config = EpisodicConfig()

        collection_stats = {
            "FacetPoint_search_text": CollectionStats(
                collection_name="FacetPoint_search_text",
                top1_raw_distance=0.35,
                top2_raw_distance=0.52,
                gap=0.17,
                baseline=0.5,
                ratio=0.7,
                confidence=0.8,
                collection_type="node",
            ),
            "RelationType_relationship_name": CollectionStats(
                collection_name="RelationType_relationship_name",
                top1_raw_distance=0.28,
                top2_raw_distance=0.50,
                gap=0.22,
                baseline=0.56,
                ratio=0.5,
                confidence=0.9,
                collection_type="edge",
            ),
        }

        context = compute_adaptive_context(collection_stats, config)

        assert context.conf_node == 0.8
        assert context.conf_edge == 0.9
        assert context.best_gap == 0.22
        assert context.best_node_source == "FacetPoint_search_text"
        assert context.best_edge_source == "RelationType_relationship_name"

    def test_weight_clipping(self):
        """Test that weights are clipped to [0.2, 0.8]"""
        config = EpisodicConfig()

        # Extreme confidence difference
        collection_stats = {
            "FacetPoint_search_text": CollectionStats(
                collection_name="FacetPoint_search_text",
                top1_raw_distance=0.25,
                top2_raw_distance=0.50,
                gap=0.25,
                baseline=0.5,
                ratio=0.5,
                confidence=1.0,
                collection_type="node",
            ),
            "RelationType_relationship_name": CollectionStats(
                collection_name="RelationType_relationship_name",
                top1_raw_distance=0.80,
                top2_raw_distance=0.81,
                gap=0.01,
                baseline=0.56,
                ratio=1.4,
                confidence=0.1,
                collection_type="edge",
            ),
        }

        context = compute_adaptive_context(collection_stats, config)

        # Weights should be clipped (use approx for float comparison)
        assert context.w_node <= 0.8 + 1e-9
        assert context.w_edge >= 0.2 - 1e-9


class TestComputeLambda:
    """Tests for compute_lambda function."""

    def test_minimum_lambda(self):
        """Low confidence should give low lambda"""
        config = EpisodicConfig()

        # Low confidence, no exact match, no gap
        lam = compute_lambda(0.2, 0.2, 0.0, 0.0, 0.5, config)

        assert lam == config.lambda_min  # 0.3

    def test_maximum_lambda(self):
        """All boosts should give high lambda"""
        config = EpisodicConfig()

        # High confidence, exact match, high gap, good semantic
        lam = compute_lambda(0.9, 0.9, 0.15, 0.2, 0.05, config)

        assert lam == config.lambda_max  # 0.95

    def test_exact_match_boost(self):
        """Exact match should boost lambda"""
        config = EpisodicConfig()

        # Without exact match
        lam1 = compute_lambda(0.5, 0.5, 0.0, 0.0, 0.5, config)

        # With exact match
        lam2 = compute_lambda(0.5, 0.5, 0.15, 0.0, 0.5, config)

        assert lam2 > lam1

    def test_lambda_range(self):
        """Lambda should always be in [lambda_min, lambda_max]"""
        config = EpisodicConfig()

        test_cases = [
            (0.1, 0.1, 0.0, 0.0, 0.8),
            (1.0, 1.0, 0.2, 0.3, 0.01),
            (0.5, 0.3, 0.08, 0.12, 0.15),
        ]

        for cn, ce, em, gap, sem in test_cases:
            lam = compute_lambda(cn, ce, em, gap, sem, config)
            assert config.lambda_min <= lam <= config.lambda_max


class TestComputeStructScore:
    """Tests for compute_struct_score function."""

    def test_rank_zero(self):
        """rank=0 should return 0"""
        config = EpisodicConfig()
        assert compute_struct_score(0, config) == 0.0

    def test_rank_one(self):
        """rank=1 should return approximately 0.33"""
        config = EpisodicConfig()
        result = compute_struct_score(1, config)
        assert abs(result - 0.333) < 0.01

    def test_monotonicity(self):
        """struct score should increase with rank"""
        config = EpisodicConfig()

        prev = 0.0
        for rank in range(1, 20):
            score = compute_struct_score(rank, config)
            assert score > prev
            prev = score

    def test_bounded(self):
        """struct score should always be in [0, 1)"""
        config = EpisodicConfig()

        for rank in [0, 1, 5, 10, 50, 100, 1000]:
            score = compute_struct_score(rank, config)
            assert 0 <= score < 1


class TestComputeFinalScore:
    """Tests for compute_final_score function."""

    def test_high_lambda_semantic_dominant(self):
        """High lambda should make semantic dominant"""
        config = EpisodicConfig()

        # Good semantic, bad rank
        final = compute_final_score(0.1, 10, 0.95, config)

        # Should be close to semantic because lambda is high
        assert final < 0.2

    def test_low_lambda_struct_dominant(self):
        """Low lambda should make struct dominant"""
        config = EpisodicConfig()

        # Good semantic, bad rank
        final = compute_final_score(0.1, 10, 0.3, config)

        # Should be influenced more by struct
        assert final > 0.3  # More influenced by struct

    def test_rank_zero_struct_zero(self):
        """rank=0 should give final = lambda * semantic"""
        config = EpisodicConfig()

        semantic = 0.2
        lam = 0.7

        final = compute_final_score(semantic, 0, lam, config)

        # struct = 0 at rank 0
        expected = lam * semantic
        assert abs(final - expected) < 0.001


class TestGetExactMatchBonus:
    """Tests for get_exact_match_bonus function."""

    def test_strong_match(self):
        """Very low scores should indicate strong match"""
        bonus = get_exact_match_bonus(0.02, 0.03)
        assert bonus == 0.15

    def test_medium_match(self):
        """Medium low scores should indicate medium match"""
        bonus = get_exact_match_bonus(0.08, 0.07)
        assert bonus == 0.08

    def test_no_match(self):
        """High scores should indicate no exact match"""
        bonus = get_exact_match_bonus(0.5, 0.6)
        assert bonus == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
