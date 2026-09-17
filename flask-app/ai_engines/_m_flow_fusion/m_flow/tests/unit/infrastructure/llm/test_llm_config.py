"""M-Flow LLM 配置字段引号清理验证"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from m_flow.llm.config import LLMConfig


def _make_config() -> LLMConfig:
    """构建带有各类引号情形的配置实例"""
    return LLMConfig(
        llm_api_key='"double_value"',
        llm_endpoint="'single_value'",
        llm_api_version="no_quotes_value",
        fallback_model='""',
        baml_llm_api_key=None,
        fallback_endpoint="\"mixed_quote'",
        baml_llm_model='"internal"quotes"',
    )


class TestQuoteStripping:
    """验证 LLMConfig 模型验证器对各种引号场景的处理"""

    @pytest.fixture(autouse=True)
    def _setup(self):
        with patch.dict(os.environ, {}, clear=True):
            self.cfg = _make_config()

    def test_surrounding_double_quotes_removed(self):
        """双引号包裹的值应去除引号"""
        assert self.cfg.llm_api_key == "double_value"

    def test_surrounding_single_quotes_removed(self):
        """单引号包裹的值应去除引号"""
        assert self.cfg.llm_endpoint == "single_value"

    def test_unquoted_string_unchanged(self):
        """无引号的字符串保持原样"""
        assert self.cfg.llm_api_version == "no_quotes_value"

    def test_empty_double_quotes_yield_blank(self):
        """空双引号应变为空字符串"""
        assert self.cfg.fallback_model == ""

    def test_none_stays_none(self):
        """None 传入后仍为 None"""
        assert self.cfg.baml_llm_api_key is None

    def test_mismatched_quotes_left_intact(self):
        """引号不匹配时保持原始值"""
        assert self.cfg.fallback_endpoint == "\"mixed_quote'"

    def test_embedded_quotes_handled(self):
        """字符串内部的引号应被正确保留"""
        assert self.cfg.baml_llm_model == 'internal"quotes'
