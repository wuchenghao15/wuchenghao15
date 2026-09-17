"""
Unit tests for EpisodicConfig - Phase 2 verification.

Tests:
1. Default values
2. New adaptive scoring fields
3. Environment variable overrides
4. get_baseline method
"""

import pytest
from m_flow.retrieval.episodic.config import EpisodicConfig, get_episodic_config


class TestEpisodicConfigDefaults:
    """Tests for default configuration values."""

    def test_default_adaptive_weights_enabled(self):
        """By default, adaptive weights should be enabled."""
        config = EpisodicConfig()
        assert config.enable_adaptive_weights is True

    def test_default_baselines(self):
        """Test default baseline values."""
        config = EpisodicConfig()

        assert config.collection_baselines["FacetPoint_search_text"] == 0.50
        assert config.collection_baselines["Facet_search_text"] == 0.60
        assert config.collection_baselines["Entity_name"] == 0.68
        assert config.collection_baselines["Episode_summary"] == 1.06
        assert config.default_baseline == 0.70

    def test_default_f_dist_thresholds(self):
        """Test default f_dist thresholds."""
        config = EpisodicConfig()

        assert config.ratio_good == 0.5
        assert config.ratio_avg == 1.0
        assert config.ratio_poor == 1.5

    def test_default_f_gap_thresholds(self):
        """Test default f_gap thresholds."""
        config = EpisodicConfig()

        assert config.gap_trivial == 0.01
        assert config.gap_low == 0.05
        assert config.gap_high == 0.15

    def test_default_weight_clip(self):
        """Test default weight clip values."""
        config = EpisodicConfig()

        assert config.weight_clip_min == 0.2
        assert config.weight_clip_max == 0.8

    def test_default_lambda_range(self):
        """Test default lambda range."""
        config = EpisodicConfig()

        assert config.lambda_min == 0.3
        assert config.lambda_max == 0.95

    def test_default_debug_mode_off(self):
        """Debug mode should be off by default."""
        config = EpisodicConfig()
        assert config.adaptive_debug_mode is False


class TestGetBaseline:
    """Tests for get_baseline method."""

    def test_known_collection(self):
        """Test getting baseline for known collection."""
        config = EpisodicConfig()

        assert config.get_baseline("FacetPoint_search_text") == 0.50
        assert config.get_baseline("Episode_summary") == 1.06

    def test_unknown_collection(self):
        """Test getting baseline for unknown collection."""
        config = EpisodicConfig()

        # Should return default baseline
        assert config.get_baseline("UnknownCollection") == 0.70
        assert config.get_baseline("SomeOtherCollection") == 0.70


class TestEnvironmentOverrides:
    """Tests for environment variable overrides."""

    def test_adaptive_enable_override(self, monkeypatch):
        """Test enabling/disabling adaptive weights via env var."""
        # Disable
        monkeypatch.setenv("EPISODIC_ENABLE_ADAPTIVE", "false")
        config = get_episodic_config()
        assert config.enable_adaptive_weights is False

        # Enable
        monkeypatch.setenv("EPISODIC_ENABLE_ADAPTIVE", "true")
        config = get_episodic_config()
        assert config.enable_adaptive_weights is True

    def test_debug_mode_override(self, monkeypatch):
        """Test debug mode override via env var."""
        monkeypatch.setenv("EPISODIC_ADAPTIVE_DEBUG", "true")
        config = get_episodic_config()
        assert config.adaptive_debug_mode is True

    def test_baseline_override(self, monkeypatch):
        """Test default baseline override via env var."""
        monkeypatch.setenv("EPISODIC_DEFAULT_BASELINE", "0.85")
        config = get_episodic_config()
        assert config.default_baseline == 0.85

    def test_lambda_range_override(self, monkeypatch):
        """Test lambda range override via env var."""
        monkeypatch.setenv("EPISODIC_LAMBDA_MIN", "0.4")
        monkeypatch.setenv("EPISODIC_LAMBDA_MAX", "0.9")
        config = get_episodic_config()
        assert config.lambda_min == 0.4
        assert config.lambda_max == 0.9

    def test_weight_clip_override(self, monkeypatch):
        """Test weight clip override via env var."""
        monkeypatch.setenv("EPISODIC_WEIGHT_CLIP_MIN", "0.3")
        monkeypatch.setenv("EPISODIC_WEIGHT_CLIP_MAX", "0.7")
        config = get_episodic_config()
        assert config.weight_clip_min == 0.3
        assert config.weight_clip_max == 0.7


class TestLambdaBoostConfig:
    """Tests for lambda boost configuration."""

    def test_lambda_boost_defaults(self):
        """Test lambda boost default values."""
        config = EpisodicConfig()

        assert config.lambda_match_strong == 0.2
        assert config.lambda_match_weak == 0.1
        assert config.lambda_gap_high == 0.15
        assert config.lambda_gap_mid == 0.10
        assert config.lambda_semantic_boost == 0.3
        assert config.lambda_semantic_mid == 0.15

    def test_exact_match_thresholds(self):
        """Test exact match threshold defaults."""
        config = EpisodicConfig()

        assert config.exact_match_threshold_strong == 0.10
        assert config.exact_match_threshold_weak == 0.05
        assert config.semantic_threshold_excellent == 0.10
        assert config.semantic_threshold_good == 0.20


class TestStructDecay:
    """Tests for struct decay configuration."""

    def test_struct_decay_default(self):
        """Test struct decay factor default."""
        config = EpisodicConfig()
        assert config.struct_decay_factor == 0.5


class TestConsistencyBonus:
    """Tests for consistency bonus configuration."""

    def test_consistency_bonus_disabled_by_default(self):
        """Consistency bonus should be disabled by default."""
        config = EpisodicConfig()
        assert config.enable_consistency_bonus is False

    def test_consistency_bonus_value(self):
        """Test consistency bonus value."""
        config = EpisodicConfig()
        assert config.consistency_bonus_per_hit == 0.08


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
