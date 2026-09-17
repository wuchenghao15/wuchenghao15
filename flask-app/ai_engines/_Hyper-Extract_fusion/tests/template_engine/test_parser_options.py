"""Unit tests for template parsers - options (merge strategy resolution)."""

from pathlib import Path
from typing import get_args

import pytest

import hyperextract
from hyperextract.utils.template_engine.parsers import load_template, parse_option
from hyperextract.utils.template_engine.parsers.options import resolve_merge_strategy
from hyperextract.utils.template_engine.parsers.schemas.base import (
    VALID_MERGE_STRATEGIES,
)
from hyperextract.utils.template_engine.parsers.schemas.naive import NaiveOptionsSchema

PRESETS_DIR = Path(hyperextract.__file__).parent / "templates" / "presets"


class TestResolveMergeStrategy:
    """``resolve_merge_strategy`` must resolve every documented strategy."""

    @pytest.mark.parametrize("strategy", get_args(VALID_MERGE_STRATEGIES))
    def test_every_valid_strategy_resolves(self, strategy):
        """No value declared in ``VALID_MERGE_STRATEGIES`` may resolve to None.

        Regression test: multi-word ``llm_*`` strategies such as
        ``llm_prefer_incoming`` / ``llm_prefer_existing`` used to fall through the
        resolver and silently return ``None`` (their name splits into 3 parts,
        which failed the ``len(parts) == 2`` guard).
        """
        assert resolve_merge_strategy(strategy) is not None

    @pytest.mark.parametrize("strategy", ["llm_prefer_incoming", "llm_prefer_existing"])
    def test_multiword_llm_strategies_map_to_llm_member(self, strategy):
        """Multi-word ``llm_*`` strategies map onto the nested ``MergeStrategy.LLM``."""
        from ontomem.merger import MergeStrategy

        expected = getattr(MergeStrategy.LLM, strategy[len("llm_") :].upper())
        assert resolve_merge_strategy(strategy) == expected


class TestParseOptionChunkValidation:
    """YAML ``options.chunk_size`` / ``chunk_overlap`` cross-checks."""

    def test_valid_chunk_size_and_overlap_enter_kwargs(self):
        options = NaiveOptionsSchema(chunk_size=2048, chunk_overlap=256)
        kwargs = parse_option(options, "model")
        assert kwargs["chunk_size"] == 2048
        assert kwargs["chunk_overlap"] == 256

    def test_overlap_equal_to_size_fails(self):
        options = NaiveOptionsSchema(chunk_size=2048, chunk_overlap=2048)
        with pytest.raises(ValueError, match="chunk_overlap"):
            parse_option(options, "model")

    def test_overlap_greater_than_size_fails(self):
        options = NaiveOptionsSchema(chunk_size=256, chunk_overlap=4096)
        with pytest.raises(ValueError, match="chunk_overlap"):
            parse_option(options, "model")

    @pytest.mark.parametrize("chunk_size", [0, -1])
    def test_chunk_size_not_positive_fails(self, chunk_size):
        options = NaiveOptionsSchema(chunk_size=chunk_size)
        with pytest.raises(ValueError, match="chunk_size"):
            parse_option(options, "model")

    def test_negative_overlap_fails(self):
        options = NaiveOptionsSchema(chunk_overlap=-1)
        with pytest.raises(ValueError, match="chunk_overlap"):
            parse_option(options, "model")

    def test_size_only_with_overlap_none_passes(self):
        options = NaiveOptionsSchema(chunk_size=2048, chunk_overlap=None)
        kwargs = parse_option(options, "model")
        assert kwargs["chunk_size"] == 2048
        assert "chunk_overlap" not in kwargs

    def test_both_chunk_fields_default_pass(self):
        kwargs = parse_option(NaiveOptionsSchema(), "model")
        assert "chunk_size" not in kwargs
        assert "chunk_overlap" not in kwargs

    def test_options_none_returns_empty_dict(self):
        assert parse_option(None, "model") == {}


class TestParseOptionPresets:
    """Bundled presets, including education, must still parse after load_template."""

    @pytest.mark.parametrize(
        "relpath",
        [
            "education/course_concept_graph.yaml",
            "education/curriculum_structure.yaml",
            "general/workflow_graph.yaml",
            "general/base_graph.yaml",
            "general/base_model.yaml",
        ],
    )
    def test_preset_load_and_parse_option(self, relpath):
        cfg = load_template(PRESETS_DIR / relpath)
        parse_option(cfg.options, cfg.type)
