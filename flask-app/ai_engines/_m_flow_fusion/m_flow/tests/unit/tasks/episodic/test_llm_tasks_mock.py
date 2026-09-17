# m_flow/tests/unit/tasks/episodic/test_llm_tasks_mock.py
"""
LLM Tasks Mock 测试

使用 unittest.mock.patch 来 Mock 掉 LLM 调用，
验证 llm_tasks.py 中的函数行为。

这些测试不会调用真实的 LLM API。
"""

import pytest
from unittest.mock import AsyncMock, patch

from m_flow.memory.episodic.llm_tasks import (
    llm_select_entities,
    llm_extract_entity_names,
    llm_write_entity_descriptions,
    llm_extract_facet_points,
)
from m_flow.memory.episodic.models import (
    ConceptSelectionResult,
    ConceptNamesResult,
    ConceptDescriptionResult,
    FacetPointExtractionResult,
    FacetConceptMapping,
    ConceptContextInfo,
    ConceptDescription,
    FacetPointDraft,
)


# =============================================================================
# TestLlmSelectEntities - 测试 llm_select_entities 函数
# =============================================================================


class TestLlmSelectEntities:
    """测试 llm_select_entities 函数"""

    @pytest.mark.asyncio
    async def test_empty_facets_returns_empty(self):
        """空 facets 应返回空结果"""
        result = await llm_select_entities(
            chunk_summaries=["summary1"],
            generated_facets=[],
            candidate_entities=["entity1 | description"],
        )
        assert result.facet_entities == []

    @pytest.mark.asyncio
    async def test_empty_candidates_returns_empty(self):
        """空 candidates 应返回空结果"""
        result = await llm_select_entities(
            chunk_summaries=["summary1"],
            generated_facets=["facet1 | description"],
            candidate_entities=[],
        )
        assert result.facet_entities == []

    @pytest.mark.asyncio
    @patch("m_flow.memory.episodic.llm_tasks.LLMService")
    @patch("m_flow.memory.episodic.llm_tasks.read_query_prompt")
    async def test_llm_call_with_mock(self, mock_read_prompt, mock_gateway):
        """Mock LLM 调用测试"""
        # Setup mocks
        mock_read_prompt.return_value = "system prompt"

        mock_result = ConceptSelectionResult(
            facet_entities=[
                FacetConceptMapping(
                    facet_search_text="test facet",
                    entities=[ConceptContextInfo(name="TestEntity", context_description="Test description")],
                )
            ]
        )
        mock_gateway.extract_structured = AsyncMock(return_value=mock_result)

        # Call function
        result = await llm_select_entities(
            chunk_summaries=["summary1"],
            generated_facets=["test facet | description"],
            candidate_entities=["TestEntity | entity description"],
        )

        # Verify
        assert len(result.facet_entities) == 1
        assert result.facet_entities[0].facet_search_text == "test facet"
        assert len(result.facet_entities[0].entities) == 1
        assert result.facet_entities[0].entities[0].name == "TestEntity"

    @pytest.mark.asyncio
    @patch("m_flow.memory.episodic.llm_tasks.LLMService")
    @patch("m_flow.memory.episodic.llm_tasks.read_query_prompt")
    async def test_llm_exception_returns_empty(self, mock_read_prompt, mock_gateway):
        """LLM 调用异常时应返回空结果"""
        mock_read_prompt.return_value = "system prompt"
        mock_gateway.extract_structured = AsyncMock(side_effect=Exception("API error"))

        result = await llm_select_entities(
            chunk_summaries=["summary1"],
            generated_facets=["facet1 | description"],
            candidate_entities=["entity1 | description"],
        )

        assert result.facet_entities == []


# =============================================================================
# TestLlmExtractEntityNames - 测试 llm_extract_entity_names 函数
# =============================================================================


class TestLlmExtractEntityNames:
    """测试 llm_extract_entity_names 函数"""

    @pytest.mark.asyncio
    async def test_empty_text_returns_empty(self):
        """空文本应返回空结果"""
        result = await llm_extract_entity_names(text="")
        assert result.names == []

    @pytest.mark.asyncio
    async def test_whitespace_text_returns_empty(self):
        """纯空白文本应返回空结果"""
        result = await llm_extract_entity_names(text="   \n\t  ")
        assert result.names == []

    @pytest.mark.asyncio
    @patch("m_flow.memory.episodic.llm_tasks.LLMService")
    @patch("m_flow.memory.episodic.llm_tasks.read_query_prompt")
    async def test_llm_call_with_mock(self, mock_read_prompt, mock_gateway):
        """Mock LLM 调用测试"""
        mock_read_prompt.return_value = "system prompt"

        mock_result = ConceptNamesResult(names=["Entity1", "Entity2", "Entity3"])
        mock_gateway.extract_structured = AsyncMock(return_value=mock_result)

        result = await llm_extract_entity_names(
            text="This is a test document about Entity1, Entity2 and Entity3.", batch_index=0
        )

        assert len(result.names) == 3
        assert "Entity1" in result.names
        assert "Entity2" in result.names
        assert "Entity3" in result.names

    @pytest.mark.asyncio
    @patch("m_flow.memory.episodic.llm_tasks.LLMService")
    @patch("m_flow.memory.episodic.llm_tasks.read_query_prompt")
    async def test_llm_exception_returns_empty(self, mock_read_prompt, mock_gateway):
        """LLM 调用异常时应返回空结果"""
        mock_read_prompt.return_value = "system prompt"
        mock_gateway.extract_structured = AsyncMock(side_effect=Exception("API error"))

        result = await llm_extract_entity_names(text="test text")

        assert result.names == []


# =============================================================================
# TestLlmWriteEntityDescriptions - 测试 llm_write_entity_descriptions 函数
# =============================================================================


class TestLlmWriteEntityDescriptions:
    """测试 llm_write_entity_descriptions 函数"""

    @pytest.mark.asyncio
    async def test_empty_entity_names_returns_empty(self):
        """空实体列表应返回空结果"""
        result = await llm_write_entity_descriptions(entity_names=[], source_text="test source")
        assert result.descriptions == []

    @pytest.mark.asyncio
    @patch("m_flow.memory.episodic.llm_tasks.LLMService")
    @patch("m_flow.memory.episodic.llm_tasks.read_query_prompt")
    async def test_llm_call_with_mock(self, mock_read_prompt, mock_gateway):
        """Mock LLM 调用测试"""
        mock_read_prompt.return_value = "system prompt"

        mock_result = ConceptDescriptionResult(
            descriptions=[
                ConceptDescription(name="Entity1", description="Description of Entity1", entity_type="Person"),
                ConceptDescription(name="Entity2", description="Description of Entity2", entity_type="Organization"),
            ]
        )
        mock_gateway.extract_structured = AsyncMock(return_value=mock_result)

        result = await llm_write_entity_descriptions(
            entity_names=["Entity1", "Entity2"],
            source_text="Test source text about Entity1 and Entity2",
        )

        assert len(result.descriptions) == 2
        assert result.descriptions[0].name == "Entity1"
        assert result.descriptions[1].name == "Entity2"

    @pytest.mark.asyncio
    @patch("m_flow.memory.episodic.llm_tasks.LLMService")
    @patch("m_flow.memory.episodic.llm_tasks.read_query_prompt")
    async def test_llm_exception_returns_empty(self, mock_read_prompt, mock_gateway):
        """LLM 调用异常时应返回空结果"""
        mock_read_prompt.return_value = "system prompt"
        mock_gateway.extract_structured = AsyncMock(side_effect=Exception("API error"))

        result = await llm_write_entity_descriptions(entity_names=["Entity1"], source_text="test")

        assert result.descriptions == []


# =============================================================================
# TestLlmExtractFacetPoints - 测试 llm_extract_facet_points 函数
# =============================================================================


class TestLlmExtractFacetPoints:
    """测试 llm_extract_facet_points 函数"""

    @pytest.mark.asyncio
    @patch("m_flow.memory.episodic.llm_tasks.LLMService")
    @patch("m_flow.memory.episodic.llm_tasks.read_query_prompt")
    async def test_llm_call_with_mock(self, mock_read_prompt, mock_gateway):
        """Mock LLM 调用测试"""
        mock_read_prompt.return_value = "system prompt"

        mock_result = FacetPointExtractionResult(
            facet_search_text="test facet",
            points=[
                FacetPointDraft(
                    search_text="Point 1 text",
                    aliases=["alias1"],
                    description="Description of point 1",
                ),
                FacetPointDraft(search_text="Point 2 text", aliases=[], description="Description of point 2"),
            ],
        )
        mock_gateway.extract_structured = AsyncMock(return_value=mock_result)

        result = await llm_extract_facet_points(
            facet_type="generic",
            facet_search_text="test facet",
            facet_description="This is the facet description with details",
            existing_points=[],
        )

        assert result.facet_search_text == "test facet"
        assert len(result.points) == 2
        assert result.points[0].search_text == "Point 1 text"
        assert result.points[1].search_text == "Point 2 text"

    @pytest.mark.asyncio
    @patch("m_flow.memory.episodic.llm_tasks.LLMService")
    @patch("m_flow.memory.episodic.llm_tasks.read_query_prompt")
    async def test_with_existing_points(self, mock_read_prompt, mock_gateway):
        """已存在 points 时的测试"""
        mock_read_prompt.return_value = "system prompt"

        mock_result = FacetPointExtractionResult(
            facet_search_text="test facet",
            points=[FacetPointDraft(search_text="New point", aliases=[], description="New point description")],
        )
        mock_gateway.extract_structured = AsyncMock(return_value=mock_result)

        result = await llm_extract_facet_points(
            facet_type="generic",
            facet_search_text="test facet",
            facet_description="This is the facet description",
            existing_points=["Existing point 1", "Existing point 2"],
        )

        assert len(result.points) == 1
        assert result.points[0].search_text == "New point"

        # Verify the prompt included existing points
        call_args = mock_gateway.extract_structured.call_args
        text_input = call_args.kwargs.get("text_input", "")
        assert "Existing point 1" in text_input or "Existing Points:" in text_input

    @pytest.mark.asyncio
    @patch("m_flow.memory.episodic.llm_tasks.read_query_prompt")
    async def test_missing_prompt_raises_error(self, mock_read_prompt):
        """缺少 prompt 文件时应抛出异常"""
        mock_read_prompt.return_value = None

        with pytest.raises(ValueError, match="Missing facet point prompt file"):
            await llm_extract_facet_points(
                facet_type="generic",
                facet_search_text="test facet",
                facet_description="description",
                existing_points=[],
            )


# =============================================================================
# TestMockEnvironmentVariable - 测试 MOCK_EPISODIC 环境变量
# =============================================================================


class TestMockEnvironmentVariable:
    """测试 MOCK_EPISODIC 环境变量"""

    @pytest.mark.asyncio
    @patch.dict("os.environ", {"MOCK_EPISODIC": "true"})
    async def test_llm_select_entities_with_mock_env(self):
        """MOCK_EPISODIC=true 时应跳过 LLM 调用"""
        result = await llm_select_entities(
            chunk_summaries=["summary"],
            generated_facets=["facet | desc"],
            candidate_entities=["entity | desc"],
        )
        # 使用 Mock 模式时返回空结果
        assert result.facet_entities == []

    @pytest.mark.asyncio
    @patch.dict("os.environ", {"MOCK_EPISODIC": "true"})
    async def test_llm_extract_entity_names_with_mock_env(self):
        """MOCK_EPISODIC=true 时应跳过 LLM 调用"""
        result = await llm_extract_entity_names(text="test text")
        assert result.names == []

    @pytest.mark.asyncio
    @patch.dict("os.environ", {"MOCK_EPISODIC": "true"})
    async def test_llm_write_entity_descriptions_with_mock_env(self):
        """MOCK_EPISODIC=true 时应跳过 LLM 调用"""
        result = await llm_write_entity_descriptions(entity_names=["entity1"], source_text="source")
        assert result.descriptions == []

    @pytest.mark.asyncio
    @patch.dict("os.environ", {"MOCK_EPISODIC": "true"})
    async def test_llm_extract_facet_points_with_mock_env(self):
        """MOCK_EPISODIC=true 时应跳过 LLM 调用"""
        result = await llm_extract_facet_points(
            facet_type="generic",
            facet_search_text="test",
            facet_description="description",
            existing_points=[],
        )
        assert result.points == []
        assert result.facet_search_text == "test"
