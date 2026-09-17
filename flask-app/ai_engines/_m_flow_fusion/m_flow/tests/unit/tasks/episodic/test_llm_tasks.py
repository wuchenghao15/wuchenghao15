# m_flow/tests/unit/tasks/episodic/test_llm_tasks.py
"""
LLM 任务模块单元测试 (Phase 4C)

测试 llm_tasks.py 模块中的所有 LLM 函数：
1. llm_select_entities: Entity 选择
2. llm_extract_entity_names: Entity 名称提取
3. llm_write_entity_descriptions: Entity 描述生成
4. llm_extract_facet_points: FacetPoint 提取

Note: llm_compile_episode 和 llm_review_and_supplement 已移除。
Facet 生成现在直接使用 section-based 路径（零信息损失）。

使用 Mock 避免实际 LLM 调用。
"""

import pytest
import os
from unittest.mock import patch

from m_flow.memory.episodic.llm_tasks import (
    llm_select_entities,
    llm_extract_entity_names,
    llm_write_entity_descriptions,
    llm_extract_facet_points,
    _as_bool_env,
)
from m_flow.memory.episodic.models import (
    ConceptSelectionResult,
    ConceptNamesResult,
    ConceptDescriptionResult,
    FacetPointExtractionResult,
)


# ============================================================
# Test _as_bool_env
# ============================================================


class TestAsBoolEnv:
    """测试 _as_bool_env 辅助函数"""

    def test_true_values(self):
        """测试 true 值"""
        with patch.dict(os.environ, {"TEST_VAR": "true"}):
            assert _as_bool_env("TEST_VAR") == True

        with patch.dict(os.environ, {"TEST_VAR": "1"}):
            assert _as_bool_env("TEST_VAR") == True

        with patch.dict(os.environ, {"TEST_VAR": "yes"}):
            assert _as_bool_env("TEST_VAR") == True

    def test_false_values(self):
        """测试 false 值"""
        with patch.dict(os.environ, {"TEST_VAR": "false"}):
            assert _as_bool_env("TEST_VAR") == False

        with patch.dict(os.environ, {"TEST_VAR": "0"}):
            assert _as_bool_env("TEST_VAR") == False

    def test_default_value(self):
        """测试默认值"""
        # 移除可能存在的环境变量
        with patch.dict(os.environ, {}, clear=True):
            assert _as_bool_env("NONEXISTENT_VAR", default=False) == False
            assert _as_bool_env("NONEXISTENT_VAR", default=True) == True


# ============================================================
# Test llm_select_entities with Mock
# ============================================================


class TestLlmSelectEntities:
    """测试 llm_select_entities 函数"""

    @pytest.mark.asyncio
    async def test_mock_mode_returns_result(self):
        """Mock 模式返回有效的 ConceptSelectionResult"""
        with patch.dict(os.environ, {"MOCK_EPISODIC": "true"}):
            result = await llm_select_entities(
                chunk_summaries=["Summary 1"],
                generated_facets=["- fact | Test fact"],
                candidate_entities=["Entity A", "Entity B", "Entity C"],
            )

            assert isinstance(result, ConceptSelectionResult)
            assert hasattr(result, "facet_entities")  # 实际字段名
            assert isinstance(result.facet_entities, list)

    @pytest.mark.asyncio
    async def test_empty_candidates(self):
        """空候选列表测试"""
        with patch.dict(os.environ, {"MOCK_EPISODIC": "true"}):
            result = await llm_select_entities(
                chunk_summaries=[],
                generated_facets=[],
                candidate_entities=[],
            )

            assert isinstance(result, ConceptSelectionResult)


# ============================================================
# Test llm_extract_entity_names with Mock
# ============================================================


class TestLlmExtractConceptNames:
    """测试 llm_extract_entity_names 函数"""

    @pytest.mark.asyncio
    async def test_mock_mode_returns_result(self):
        """Mock 模式返回有效的 ConceptNamesResult"""
        with patch.dict(os.environ, {"MOCK_EPISODIC": "true"}):
            result = await llm_extract_entity_names(
                text="Python 是一种编程语言。Guido van Rossum 创建了 Python。",
                batch_index=0,
            )

            assert isinstance(result, ConceptNamesResult)
            assert hasattr(result, "names")
            assert isinstance(result.names, list)

    @pytest.mark.asyncio
    async def test_empty_text(self):
        """空文本测试"""
        with patch.dict(os.environ, {"MOCK_EPISODIC": "true"}):
            result = await llm_extract_entity_names(
                text="",
                batch_index=0,
            )

            assert isinstance(result, ConceptNamesResult)


# ============================================================
# Test llm_write_entity_descriptions with Mock
# ============================================================


class TestLlmWriteConceptDescriptions:
    """测试 llm_write_entity_descriptions 函数"""

    @pytest.mark.asyncio
    async def test_mock_mode_returns_result(self):
        """Mock 模式返回有效的 ConceptDescriptionResult"""
        with patch.dict(os.environ, {"MOCK_EPISODIC": "true"}):
            result = await llm_write_entity_descriptions(
                entity_names=["Python", "Guido van Rossum"],
                source_text="Python is a programming language created by Guido.",
                batch_index=0,
            )

            assert isinstance(result, ConceptDescriptionResult)
            assert hasattr(result, "descriptions")

    @pytest.mark.asyncio
    async def test_empty_entity_names(self):
        """空实体名称列表测试"""
        with patch.dict(os.environ, {"MOCK_EPISODIC": "true"}):
            result = await llm_write_entity_descriptions(
                entity_names=[],
                source_text="Some context",
                batch_index=0,
            )

            assert isinstance(result, ConceptDescriptionResult)


# ============================================================
# Test llm_extract_facet_points with Mock
# ============================================================


class TestLlmExtractFacetPoints:
    """测试 llm_extract_facet_points 函数"""

    @pytest.mark.asyncio
    async def test_mock_mode_returns_result(self):
        """Mock 模式返回有效的 FacetPointExtractionResult"""
        with patch.dict(os.environ, {"MOCK_EPISODIC": "true"}):
            result = await llm_extract_facet_points(
                facet_type="fact",
                facet_search_text="Machine learning is a branch of AI",
                facet_description="ML description",
                existing_points=["Point 1", "Point 2"],
                prompt_file_name="episodic_extract_facet_points.txt",
            )

            assert isinstance(result, FacetPointExtractionResult)
            assert hasattr(result, "points")
            assert isinstance(result.points, list)

    @pytest.mark.asyncio
    async def test_empty_existing_points(self):
        """空已有 points 测试"""
        with patch.dict(os.environ, {"MOCK_EPISODIC": "true"}):
            result = await llm_extract_facet_points(
                facet_type="fact",
                facet_search_text="Test fact",
                facet_description="Test description",
                existing_points=[],
            )

            assert isinstance(result, FacetPointExtractionResult)


# ============================================================
# Test LLM function integration
# ============================================================


class TestLlmFunctionsIntegration:
    """集成测试：验证所有 LLM 函数可以正常调用"""

    @pytest.mark.asyncio
    async def test_all_functions_callable_in_mock_mode(self):
        """所有函数在 Mock 模式下可调用"""
        with patch.dict(os.environ, {"MOCK_EPISODIC": "true"}):
            # llm_select_entities
            r2 = await llm_select_entities(
                chunk_summaries=["s1"],
                generated_facets=["- fact | Test"],
                candidate_entities=["A"],
            )
            assert r2 is not None

            # llm_extract_entity_names
            r3 = await llm_extract_entity_names(
                text="Test text",
                batch_index=0,
            )
            assert r3 is not None

            # llm_write_entity_descriptions
            r4 = await llm_write_entity_descriptions(
                entity_names=["A"],
                source_text="Context",
                batch_index=0,
            )
            assert r4 is not None

            # llm_extract_facet_points
            r5 = await llm_extract_facet_points(
                facet_type="fact",
                facet_search_text="Test",
                facet_description="Description",
                existing_points=[],
            )
            assert r5 is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
