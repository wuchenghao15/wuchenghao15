import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from m_flow.knowledge.graph_ops.exceptions.exceptions import ConceptNotFoundError
from m_flow.knowledge.graph_ops.m_flow_graph.MemoryGraph import MemoryGraph
from m_flow.knowledge.graph_ops.m_flow_graph.MemoryGraphElements import Edge, Node
from m_flow.retrieval.episodic.bundle_scorer import RelationshipIndex
from m_flow.retrieval.episodic.config import EpisodicConfig
from m_flow.retrieval.episodic.exact_match_bonus import (
    NumberToken,
    apply_exact_match_bonus,
    apply_keyword_match_bonus,
    calculate_exact_match_bonus,
    calculate_number_match_bonus,
    extract_number_tokens,
)
from m_flow.retrieval.episodic.memory_fragment import (
    compute_best_node_distances,
    get_episodic_memory_fragment,
)
from m_flow.retrieval.episodic.output_assembler import (
    _filter_summary_sections,
    _find_episode_node,
)
from m_flow.retrieval.episodic.query_preprocessor import PreprocessedQuery


class TestExtractNumberTokens:
    def test_extracts_number_units_and_pure_numbers_without_duplication(self):
        tokens = extract_number_tokens("预算 40万，周期 12 个月，备用金 12")

        assert [(token.raw, token.full, token.unit) for token in tokens] == [
            ("40", "40万", "万"),
            ("12", "12个月", "个月"),
            ("12", "12", ""),
        ]

    def test_returns_empty_list_for_blank_input(self):
        assert extract_number_tokens("") == []
        assert extract_number_tokens(None) == []


class TestExactMatchBonus:
    def test_number_match_bonus_prefers_full_match_and_caps_total_bonus(self):
        config = EpisodicConfig(full_number_match_bonus=0.2, partial_number_match_bonus=0.05)
        query = [NumberToken(raw="40", full="40万", unit="万"), NumberToken(raw="7", full="7", unit="")]
        node = [
            NumberToken(raw="40", full="40万", unit="万"),
            NumberToken(raw="7", full="7天", unit="天"),
            NumberToken(raw="8", full="8", unit=""),
        ]

        assert calculate_number_match_bonus(query, node, config) == pytest.approx(-0.25)

    def test_calculate_exact_match_bonus_combines_number_and_english_matches(self):
        config = EpisodicConfig(full_number_match_bonus=0.2, english_match_bonus=0.03)

        bonus = calculate_exact_match_bonus("请总结 Apollo 项目的 40万 预算", "Apollo 项目预算控制在 40万 内", config)

        assert bonus == pytest.approx(-0.23)

    def test_apply_exact_match_bonus_updates_only_results_above_score_floor(self):
        config = EpisodicConfig(full_number_match_bonus=0.2)
        high = SimpleNamespace(score=0.5, payload={"text": "预算 40万"})
        low = SimpleNamespace(score=0.05, payload={"text": "预算 40万"})
        empty = SimpleNamespace(score=0.9, payload={})

        apply_exact_match_bonus("40万", [high, low, empty], config)

        assert high.score == pytest.approx(0.3)
        assert low.score == pytest.approx(0.05)
        assert empty.score == pytest.approx(0.9)

    def test_apply_keyword_match_bonus_normalizes_spacing_and_punctuation(self):
        config = EpisodicConfig(keyword_match_bonus=0.2)
        preprocessed = PreprocessedQuery(
            original="阿波罗 项目",
            vector_query="阿波罗 项目",
            keyword="阿波罗 项目",
            hybrid_reason="short_query",
            use_hybrid=True,
        )
        hit = SimpleNamespace(score=0.6, payload={"text": "这是阿波罗，项目的总结"})
        miss = SimpleNamespace(score=0.6, payload={"text": "这是其他主题"})

        apply_keyword_match_bonus(preprocessed, [hit, miss], config)

        assert hit.score == pytest.approx(0.4)
        assert miss.score == pytest.approx(0.6)


class TestMemoryFragmentHelpers:
    @pytest.mark.asyncio
    async def test_get_episodic_memory_fragment_uses_strict_filtering_when_supported(self):
        graph_engine = object()
        fragment = AsyncMock(spec=MemoryGraph)

        with (
            patch("m_flow.retrieval.episodic.memory_fragment.MemoryGraph", return_value=fragment),
            patch(
                "m_flow.retrieval.episodic.memory_fragment.get_graph_provider", new=AsyncMock(return_value=graph_engine)
            ),
        ):
            result = await get_episodic_memory_fragment(
                episodic_nodeset_name="workspace",
                relevant_ids_to_filter=["n1"],
                strict_nodeset_filtering=True,
            )

        assert result is fragment
        fragment.project_graph_from_db.assert_awaited_once()
        kwargs = fragment.project_graph_from_db.await_args.kwargs
        assert kwargs["node_name"] == ["workspace"]
        assert kwargs["relevant_ids_to_filter"] == ["n1"]
        assert kwargs["strict_nodeset_filtering"] is True

    @pytest.mark.asyncio
    async def test_get_episodic_memory_fragment_retries_without_strict_flag_for_legacy_projector(self):
        graph_engine = object()
        fragment = AsyncMock(spec=MemoryGraph)
        fragment.project_graph_from_db = AsyncMock(side_effect=[TypeError("legacy"), None])

        with (
            patch("m_flow.retrieval.episodic.memory_fragment.MemoryGraph", return_value=fragment),
            patch(
                "m_flow.retrieval.episodic.memory_fragment.get_graph_provider", new=AsyncMock(return_value=graph_engine)
            ),
        ):
            await get_episodic_memory_fragment(strict_nodeset_filtering=True)

        assert fragment.project_graph_from_db.await_count == 2
        first_kwargs = fragment.project_graph_from_db.await_args_list[0].kwargs
        second_kwargs = fragment.project_graph_from_db.await_args_list[1].kwargs
        assert first_kwargs["strict_nodeset_filtering"] is True
        assert "strict_nodeset_filtering" not in second_kwargs

    @pytest.mark.asyncio
    async def test_get_episodic_memory_fragment_swallows_missing_nodeset(self):
        fragment = AsyncMock(spec=MemoryGraph)
        fragment.project_graph_from_db = AsyncMock(side_effect=ConceptNotFoundError("missing"))

        with (
            patch("m_flow.retrieval.episodic.memory_fragment.MemoryGraph", return_value=fragment),
            patch("m_flow.retrieval.episodic.memory_fragment.get_graph_provider", new=AsyncMock(return_value=object())),
        ):
            result = await get_episodic_memory_fragment()

        assert result is fragment

    def test_compute_best_node_distances_keeps_best_score_per_id_and_skips_edge_collection(self):
        node_distances = {
            "Episode_summary": [SimpleNamespace(id="ep-1", score=0.42), SimpleNamespace(id="ep-2", score=0.3)],
            "Entity_name": [SimpleNamespace(id="ep-1", score=0.18), SimpleNamespace(id="", score=0.05)],
            "RelationType_relationship_name": [SimpleNamespace(id="edge-1", score=0.01)],
        }

        best = compute_best_node_distances(node_distances)

        assert best == {"ep-1": 0.18, "ep-2": 0.3}


class TestOutputAssemblerHelpers:
    def test_filter_summary_sections_matches_titles_case_insensitively(self):
        summary = "【Overview】Alpha 【Timeline】Beta 【Risks】Gamma"

        filtered = _filter_summary_sections(summary, {"timeline", "risks"})

        assert filtered == "【Timeline】Beta 【Risks】Gamma"

    def test_filter_summary_sections_falls_back_to_full_summary_when_no_sections_match(self):
        summary = "【Overview】Alpha 【Timeline】Beta"
        assert _filter_summary_sections(summary, {"budget"}) == summary
        assert _filter_summary_sections("plain text summary", {"budget"}) == "plain text summary"

    def test_find_episode_node_checks_facet_edges_before_entity_edges(self):
        episode = Node("ep-1", {"type": "Episode", "summary": "Summary"})
        facet = Node("fa-1", {"type": "Facet", "name": "Timeline"})
        entity = Node("en-1", {"type": "Entity", "name": "Apollo"})
        facet_edge = Edge(episode, facet, {"relationship_name": "has_facet"})
        entity_edge = Edge(episode, entity, {"relationship_name": "involves_entity"})
        index = RelationshipIndex(
            episode_ids={"ep-1"},
            facet_ids={"fa-1"},
            point_ids=set(),
            entity_ids={"en-1"},
            ep_facet_edge={("ep-1", "fa-1"): facet_edge},
            facet_point_edge={},
            ep_entity_edge={("ep-1", "en-1"): entity_edge},
            facet_entity_edge={},
            facets_by_episode={"ep-1": {"fa-1"}},
            points_by_facet={},
            entities_by_episode={"ep-1": {"en-1"}},
            entities_by_facet={},
        )

        assert _find_episode_node("ep-1", index) is episode
