# m_flow/tests/unit/tasks/episodic/test_ingestion_config.py
"""
EpisodicIngestionConfig unit tests.

Tests configuration loading, environment variable override, parameter merging, etc.
"""

import os
import pytest
from unittest.mock import patch

from m_flow.memory.episodic.episodic_ingestion_config import (
    EpisodicIngestionConfig,
    get_ingestion_config,
    merge_config_with_params,
    _as_bool_env,
    _as_float_env,
    _as_int_env,
)


class TestHelperFunctions:
    """Test helper functions."""

    def test_as_bool_env_true_values(self):
        """Test boolean environment variable true values."""
        for val in ["1", "true", "True", "TRUE", "yes", "Yes", "YES", "on", "ON"]:
            with patch.dict(os.environ, {"TEST_BOOL": val}):
                assert _as_bool_env("TEST_BOOL", False) is True

    def test_as_bool_env_false_values(self):
        """Test boolean environment variable false values."""
        for val in ["0", "false", "False", "FALSE", "no", "No", "NO", "off", "OFF"]:
            with patch.dict(os.environ, {"TEST_BOOL": val}):
                assert _as_bool_env("TEST_BOOL", True) is False

    def test_as_bool_env_unrecognized_uses_default(self):
        """Test unrecognized values use default."""
        with patch.dict(os.environ, {"TEST_BOOL": "anything"}):
            # Unrecognized values should return default
            assert _as_bool_env("TEST_BOOL", True) is True
            assert _as_bool_env("TEST_BOOL", False) is False

    def test_as_bool_env_default(self):
        """Test boolean environment variable default values."""
        # Ensure environment variable doesn't exist
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("TEST_BOOL_NOT_EXIST", None)
            assert _as_bool_env("TEST_BOOL_NOT_EXIST", True) is True
            assert _as_bool_env("TEST_BOOL_NOT_EXIST", False) is False

    def test_as_float_env_valid(self):
        """Test float environment variable valid values."""
        with patch.dict(os.environ, {"TEST_FLOAT": "0.95"}):
            assert _as_float_env("TEST_FLOAT", 0.5) == 0.95

    def test_as_float_env_invalid(self):
        """Test float environment variable invalid values."""
        with patch.dict(os.environ, {"TEST_FLOAT": "not_a_float"}):
            assert _as_float_env("TEST_FLOAT", 0.5) == 0.5

    def test_as_float_env_default(self):
        """Test float environment variable default values."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("TEST_FLOAT_NOT_EXIST", None)
            assert _as_float_env("TEST_FLOAT_NOT_EXIST", 0.75) == 0.75

    def test_as_int_env_valid(self):
        """Test integer environment variable valid values."""
        with patch.dict(os.environ, {"TEST_INT": "42"}):
            assert _as_int_env("TEST_INT", 10) == 42

    def test_as_int_env_invalid(self):
        """Test integer environment variable invalid values."""
        with patch.dict(os.environ, {"TEST_INT": "not_an_int"}):
            assert _as_int_env("TEST_INT", 10) == 10

    def test_as_int_env_default(self):
        """Test integer environment variable default values."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("TEST_INT_NOT_EXIST", None)
            assert _as_int_env("TEST_INT_NOT_EXIST", 100) == 100


class TestEpisodicIngestionConfig:
    """Test configuration class."""

    def test_default_values(self):
        """Test default values."""
        config = EpisodicIngestionConfig()

        # Feature flags
        assert config.enable_semantic_merge is False
        assert config.enable_episode_routing is True
        assert config.enable_facet_points is True
        assert config.enable_llm_entity_for_routing is True
        assert config.mock_episodic is False

        # Numerical thresholds
        assert config.semantic_merge_threshold == 0.90
        assert config.llm_concurrency_limit == 15

        # Capacity limits
        assert config.max_entities_per_episode == 0
        assert config.max_new_facets_per_batch == 20
        assert config.max_existing_facets_in_prompt == 60
        assert config.max_chunk_summaries_in_prompt == 40
        assert config.max_candidate_entities_in_prompt == 25
        assert config.max_aliases_per_facet == 10
        assert config.aliases_text_max_chars == 400
        assert config.evidence_chunks_per_facet == 3

        # File configuration
        assert config.episodic_nodeset_name == "Episodic"

    def test_custom_values(self):
        """Test custom values."""
        config = EpisodicIngestionConfig(
            enable_semantic_merge=True,
            semantic_merge_threshold=0.85,
            max_new_facets_per_batch=30,
            episodic_nodeset_name="CustomMemorySpace",
        )

        assert config.enable_semantic_merge is True
        assert config.semantic_merge_threshold == 0.85
        assert config.max_new_facets_per_batch == 30
        assert config.episodic_nodeset_name == "CustomMemorySpace"

    def test_validation_semantic_merge_threshold_too_high(self):
        """Test semantic_merge_threshold upper bound validation."""
        with pytest.raises(ValueError, match="semantic_merge_threshold"):
            EpisodicIngestionConfig(semantic_merge_threshold=1.5)

    def test_validation_semantic_merge_threshold_too_low(self):
        """Test semantic_merge_threshold lower bound validation."""
        with pytest.raises(ValueError, match="semantic_merge_threshold"):
            EpisodicIngestionConfig(semantic_merge_threshold=-0.1)

    def test_validation_llm_concurrency_limit(self):
        """Test llm_concurrency_limit validation."""
        with pytest.raises(ValueError, match="llm_concurrency_limit"):
            EpisodicIngestionConfig(llm_concurrency_limit=0)

    def test_validation_max_new_facets_per_batch(self):
        """Test max_new_facets_per_batch validation."""
        with pytest.raises(ValueError, match="max_new_facets_per_batch"):
            EpisodicIngestionConfig(max_new_facets_per_batch=0)


class TestGetIngestionConfig:
    """Test get_ingestion_config function."""

    def test_default_config(self):
        """Test default configuration."""
        # Clear all related environment variables
        env_vars_to_clear = [
            "MFLOW_EPISODIC_ENABLE_SEMANTIC_MERGE",
            "MFLOW_EPISODIC_SEMANTIC_MERGE_THRESHOLD",
            "MFLOW_EPISODIC_ENABLE_REVIEW",
            "MFLOW_EPISODIC_ENABLE_ROUTING",
            "MFLOW_EPISODIC_ENABLE_FACET_POINTS",
            "MFLOW_EPISODIC_USE_LLM_ENTITY_FOR_ROUTING",
            "MFLOW_LLM_CONCURRENCY_LIMIT",
            "MOCK_EPISODIC",
        ]

        clean_env = {k: v for k, v in os.environ.items() if k not in env_vars_to_clear}
        with patch.dict(os.environ, clean_env, clear=True):
            config = get_ingestion_config()

            assert config.enable_semantic_merge is False
            assert config.semantic_merge_threshold == 0.90

    def test_env_override(self):
        """Test environment variable override."""
        env_vars = {
            "MFLOW_EPISODIC_ENABLE_SEMANTIC_MERGE": "true",
            "MFLOW_EPISODIC_SEMANTIC_MERGE_THRESHOLD": "0.85",
            "MFLOW_EPISODIC_ENABLE_REVIEW": "false",
            "MFLOW_LLM_CONCURRENCY_LIMIT": "20",
        }

        with patch.dict(os.environ, env_vars):
            config = get_ingestion_config()

            assert config.enable_semantic_merge is True
            assert config.semantic_merge_threshold == 0.85
            assert config.llm_concurrency_limit == 20


class TestMergeConfigWithParams:
    """Test merge_config_with_params function."""

    def test_no_overrides(self):
        """Test using config default values when no overrides."""
        config = EpisodicIngestionConfig(
            enable_semantic_merge=True,
            max_new_facets_per_batch=50,
        )

        merged = merge_config_with_params(config)

        assert merged.enable_semantic_merge is True
        assert merged.max_new_facets_per_batch == 50

    def test_param_overrides_config(self):
        """Test parameters override config."""
        config = EpisodicIngestionConfig(
            enable_semantic_merge=True,
            max_new_facets_per_batch=50,
        )

        merged = merge_config_with_params(
            config,
            enable_semantic_merge=False,  # Override
            max_new_facets_per_batch=100,  # Override
        )

        assert merged.enable_semantic_merge is False
        assert merged.max_new_facets_per_batch == 100

    def test_partial_override(self):
        """Test partial override."""
        config = EpisodicIngestionConfig(
            enable_semantic_merge=True,
            semantic_merge_threshold=0.80,
            max_new_facets_per_batch=50,
        )

        merged = merge_config_with_params(
            config,
            enable_semantic_merge=False,  # Override
            # semantic_merge_threshold not passed, use config value
            # max_new_facets_per_batch not passed, use config value
        )

        assert merged.enable_semantic_merge is False  # Overridden
        assert merged.semantic_merge_threshold == 0.80  # Keep config value
        assert merged.max_new_facets_per_batch == 50  # Keep config value

    def test_none_config_uses_env(self):
        """Test reading from environment variables when config=None."""
        env_vars = {
            "MFLOW_EPISODIC_ENABLE_SEMANTIC_MERGE": "true",
        }

        with patch.dict(os.environ, env_vars):
            merged = merge_config_with_params(
                None,  # Read from environment variables
                max_new_facets_per_batch=100,  # Parameter override
            )

            assert merged.enable_semantic_merge is True  # From environment variable
            assert merged.max_new_facets_per_batch == 100  # From parameter

    def test_backward_compatibility(self):
        """Test backward compatibility - simulate write_episodic_memories call pattern."""
        # Simulate old code call pattern: all parameters are None
        merged = merge_config_with_params(
            None,
            enable_semantic_merge=None,
            semantic_merge_threshold=None,
            enable_episode_routing=None,
        )

        # Should use default values
        assert merged.enable_semantic_merge is False
        assert merged.semantic_merge_threshold == 0.90
        assert merged.enable_episode_routing is True

    def test_explicit_false_not_treated_as_none(self):
        """Test explicit False is not treated as None."""
        config = EpisodicIngestionConfig(
            enable_semantic_merge=True,
        )

        merged = merge_config_with_params(
            config,
            enable_semantic_merge=False,  # Explicit False
        )

        assert merged.enable_semantic_merge is False
