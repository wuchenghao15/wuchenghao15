# m_flow/tests/unit/episodic/test_episode_size_check.py
"""
Unit tests for Episode Size Check module.

Tests cover:
1. Configuration
2. Detection logic (IQR + absolute threshold)
3. Split validation
4. Audit result parsing
"""

import pytest

# Import module under test
from m_flow.memory.episodic.episode_size_check import (
    EpisodeSizeCheckConfig,
    EpisodeStats,
    SplitSuggestion,
    AuditResult,
    validate_splits,
)


# ============================================================
# Test Configuration
# ============================================================


class TestEpisodeSizeCheckConfig:
    """Test configuration class."""

    def test_default_values(self):
        """Test default configuration values."""
        config = EpisodeSizeCheckConfig()

        assert config.enabled == True
        assert config.detection_mode == "fixed"
        assert config.fixed_threshold == 18
        assert config.base_threshold == 12
        assert config.absolute_threshold == 25
        assert config.max_threshold == 50
        assert config.min_facets_to_check == 9
        assert config.adaptive_increment == 5
        assert config.iqr_multiplier == 1.5

    def test_custom_values(self):
        """Test custom configuration values."""
        config = EpisodeSizeCheckConfig(
            base_threshold=15,
            absolute_threshold=25,
            min_facets_to_check=10,
        )

        assert config.base_threshold == 15
        assert config.absolute_threshold == 25
        assert config.min_facets_to_check == 10


# ============================================================
# Test Validate Splits
# ============================================================


class TestValidateSplits:
    """Test split validation logic."""

    def test_valid_splits(self):
        """Test valid split suggestions pass validation."""
        splits = [
            SplitSuggestion(new_episode_name="Episode A", facet_indices=[0, 1, 2], rationale="Group A"),
            SplitSuggestion(new_episode_name="Episode B", facet_indices=[3, 4], rationale="Group B"),
        ]

        result = validate_splits(splits, total_facets=5)
        assert len(result) == 2

    def test_index_out_of_bounds(self):
        """Test index out of bounds raises ValueError."""
        splits = [
            SplitSuggestion(
                new_episode_name="Episode A",
                facet_indices=[0, 1, 10],  # 10 is out of bounds
                rationale="Group A",
            ),
        ]

        with pytest.raises(ValueError, match="Invalid facet index"):
            validate_splits(splits, total_facets=5)

    def test_negative_index(self):
        """Test negative index raises ValueError."""
        splits = [
            SplitSuggestion(new_episode_name="Episode A", facet_indices=[-1, 0, 1], rationale="Group A"),
        ]

        with pytest.raises(ValueError, match="Invalid facet index"):
            validate_splits(splits, total_facets=5)

    def test_duplicate_indices(self):
        """Test duplicate indices raises ValueError."""
        splits = [
            SplitSuggestion(new_episode_name="Episode A", facet_indices=[0, 1, 2], rationale="Group A"),
            SplitSuggestion(
                new_episode_name="Episode B",
                facet_indices=[2, 3, 4],  # 2 is duplicate
                rationale="Group B",
            ),
        ]

        with pytest.raises(ValueError, match="Duplicate facet indices"):
            validate_splits(splits, total_facets=5)

    def test_missing_facets(self):
        """Test not all facets assigned raises ValueError."""
        splits = [
            SplitSuggestion(new_episode_name="Episode A", facet_indices=[0, 1], rationale="Group A"),
            # Missing indices 2, 3, 4
        ]

        with pytest.raises(ValueError, match="Not all facets assigned"):
            validate_splits(splits, total_facets=5)

    def test_empty_splits(self):
        """Test empty splits list raises ValueError."""
        with pytest.raises(ValueError, match="Not all facets assigned"):
            validate_splits([], total_facets=5)


# ============================================================
# Test Audit Result Parsing
# ============================================================


class TestAuditResultParsing:
    """Test audit result model parsing."""

    def test_keep_decision(self):
        """Test parsing KEEP decision."""
        result = AuditResult(decision="KEEP", reasoning="All facets are related", splits=None)

        assert result.decision == "KEEP"
        assert result.splits is None

    def test_split_decision(self):
        """Test parsing SPLIT decision."""
        result = AuditResult(
            decision="SPLIT",
            reasoning="Two distinct topics found",
            splits=[
                SplitSuggestion(new_episode_name="Topic A", facet_indices=[0, 1], rationale="Related to A"),
                SplitSuggestion(new_episode_name="Topic B", facet_indices=[2, 3], rationale="Related to B"),
            ],
        )

        assert result.decision == "SPLIT"
        assert len(result.splits) == 2
        assert result.splits[0].new_episode_name == "Topic A"


# ============================================================
# Test Detection Logic (Mock)
# ============================================================


class TestDetectionLogic:
    """Test detection logic with mocked data."""

    def test_iqr_calculation(self):
        """Test IQR threshold calculation."""
        import numpy as np

        # Simulate facet counts
        counts = [5, 8, 10, 12, 15, 18, 20, 25, 30]

        q1, q3 = np.percentile(counts, [25, 75])
        iqr = q3 - q1

        # Dynamic threshold = Q3 + 1.5 * IQR
        dynamic_threshold = q3 + 1.5 * iqr

        # numpy.percentile with default linear interpolation:
        # Q1=10.0, Q3=20.0, IQR=10.0
        # Threshold = 20.0 + 1.5 * 10.0 = 35.0
        assert dynamic_threshold > 30
        assert dynamic_threshold < 40

    def test_absolute_threshold_override(self):
        """Test absolute threshold overrides IQR when appropriate."""
        config = EpisodeSizeCheckConfig(
            base_threshold=12,
            absolute_threshold=30,
        )

        # Episode with 35 facets should trigger check even if IQR says 42
        episode = EpisodeStats(
            episode_id="ep1",
            episode_name="Large Episode",
            facet_count=35,
            current_threshold=0,
        )

        # Should check because 35 > absolute_threshold (30)
        should_check = (
            episode.facet_count > 42  # IQR threshold
            or episode.facet_count > config.absolute_threshold
        )

        assert should_check == True

    def test_min_facets_filter(self):
        """Test episodes below min_facets_to_check are filtered."""
        config = EpisodeSizeCheckConfig(min_facets_to_check=9)

        episodes = [
            EpisodeStats("ep1", "Small", 5, 0),
            EpisodeStats("ep2", "Medium", 8, 0),
            EpisodeStats("ep3", "Large", 15, 0),
        ]

        candidates = [ep for ep in episodes if ep.facet_count >= config.min_facets_to_check]

        assert len(candidates) == 1
        assert candidates[0].episode_name == "Large"


# ============================================================
# Test Adaptive Threshold Logic
# ============================================================


class TestAdaptiveThreshold:
    """Test adaptive threshold calculation."""

    def test_threshold_calculation(self):
        """Test new threshold = current_facet_count + increment."""
        config = EpisodeSizeCheckConfig(
            adaptive_increment=5,
            max_threshold=50,
        )

        current_facet_count = 35
        new_threshold = min(current_facet_count + config.adaptive_increment, config.max_threshold)

        assert new_threshold == 40

    def test_threshold_ceiling(self):
        """Test threshold doesn't exceed max_threshold."""
        config = EpisodeSizeCheckConfig(
            adaptive_increment=5,
            max_threshold=50,
        )

        current_facet_count = 48
        new_threshold = min(current_facet_count + config.adaptive_increment, config.max_threshold)

        # 48 + 5 = 53, but capped at 50
        assert new_threshold == 50


# ============================================================
# Run tests
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
