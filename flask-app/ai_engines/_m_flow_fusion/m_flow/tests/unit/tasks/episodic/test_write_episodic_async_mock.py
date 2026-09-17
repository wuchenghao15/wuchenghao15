"""
Async Mock tests for write_episodic_memories.py

These tests verify the async functions using minimal mocking.
Complex integration tests are deferred to Phase 3.

Test Coverage: 6 async functions
- _find_existing_entities_by_canonical_name
- _batch_find_existing_entities_by_canonical_names
- _route_documents_to_episodes
- write_episodic_memories (basic)
- write_same_entity_edges
- write_facet_entity_edges
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ============================================================
# Test Data Factories
# ============================================================


def new_uuid() -> str:
    return str(uuid.uuid4())


@dataclass
class MockSection:
    """Mock Section for testing."""

    heading: str = ""
    text: str = ""


@dataclass
class MockContentFragment:
    """Mock ContentFragment for testing."""

    id: str = field(default_factory=new_uuid)
    text: str = "Sample chunk text"
    chunk_index: int = 0
    is_part_of: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    contains: List[Any] = field(default_factory=list)


@dataclass
class MockDocument:
    """Mock Document for testing."""

    id: str = field(default_factory=new_uuid)


@dataclass
class MockFragmentDigest:
    """Mock FragmentDigest for testing."""

    text: str = ""
    made_from: Any = None
    sections: List[MockSection] = field(default_factory=list)
    overall_topic: str = ""


def create_mock_fragment_digest(
    text: str = "Test content",
    sections: Optional[List[tuple]] = None,
    chunk_index: int = 0,
    doc_id: Optional[str] = None,
) -> MockFragmentDigest:
    """Factory for creating test FragmentDigest."""
    doc_id = doc_id or new_uuid()
    doc = MockDocument(id=doc_id)
    chunk = MockContentFragment(
        text=text,
        chunk_index=chunk_index,
        is_part_of=doc,
    )

    section_objs = []
    if sections:
        for heading, content in sections:
            section_objs.append(MockSection(heading=heading, text=content))

    return MockFragmentDigest(
        text=text,
        made_from=chunk,
        sections=section_objs,
    )


def create_mock_by_doc(num_docs: int = 1, chunks_per_doc: int = 1) -> Dict[str, List[MockFragmentDigest]]:
    """Create mock by_doc dictionary for routing tests."""
    by_doc = {}
    for i in range(num_docs):
        doc_id = new_uuid()
        fragments = []
        for j in range(chunks_per_doc):
            fragments.append(
                create_mock_fragment_digest(
                    text=f"Content for doc {i}, chunk {j}",
                    chunk_index=j,
                    doc_id=doc_id,
                )
            )
        by_doc[doc_id] = fragments
    return by_doc


def create_mock_graph_engine():
    """Create a mock graph engine."""
    mock = MagicMock()
    mock.query = AsyncMock(return_value=[])
    mock.add_nodes = AsyncMock(return_value=True)
    mock.add_edges = AsyncMock(return_value=True)
    return mock


def create_mock_vector_engine():
    """Create a mock vector engine."""
    mock = MagicMock()
    mock.search = AsyncMock(return_value=[])
    mock.add = AsyncMock(return_value=True)
    return mock


# ============================================================
# Test _route_documents_to_episodes
# ============================================================


class TestRouteDocumentsToEpisodes:
    """Tests for _route_documents_to_episodes function."""

    @pytest.mark.asyncio
    async def test_empty_by_doc(self):
        """Test with empty input."""
        from m_flow.memory.episodic.write_episodic_memories import _route_documents_to_episodes

        mock_graph = create_mock_graph_engine()
        mock_vector = create_mock_vector_engine()

        result = await _route_documents_to_episodes(
            by_doc={},
            graph_engine=mock_graph,
            vector_engine=mock_vector,
            enable_episode_routing=False,
            enable_llm_entity_for_routing=False,
            max_entities_per_episode=10,
            max_chunk_summaries_in_prompt=5,
        )

        assert result.by_episode == {}

    @pytest.mark.asyncio
    async def test_routing_single_doc(self):
        """Test routing with single document."""
        from m_flow.memory.episodic.write_episodic_memories import _route_documents_to_episodes

        mock_graph = create_mock_graph_engine()
        mock_vector = create_mock_vector_engine()

        by_doc = create_mock_by_doc(num_docs=1, chunks_per_doc=1)

        result = await _route_documents_to_episodes(
            by_doc=by_doc,
            graph_engine=mock_graph,
            vector_engine=mock_vector,
            enable_episode_routing=False,
            enable_llm_entity_for_routing=False,
            max_entities_per_episode=10,
            max_chunk_summaries_in_prompt=5,
        )

        # Each doc should get its own episode
        assert len(result.by_episode) == 1
        # Routing decision will be either "disabled" or "new" depending on concurrency limit
        for decision in result.routing_decisions.values():
            assert decision in ("disabled", "new")

    @pytest.mark.asyncio
    async def test_routing_multiple_docs(self):
        """Test routing with multiple documents."""
        from m_flow.memory.episodic.write_episodic_memories import _route_documents_to_episodes

        mock_graph = create_mock_graph_engine()
        mock_vector = create_mock_vector_engine()

        by_doc = create_mock_by_doc(num_docs=3, chunks_per_doc=1)

        result = await _route_documents_to_episodes(
            by_doc=by_doc,
            graph_engine=mock_graph,
            vector_engine=mock_vector,
            enable_episode_routing=False,
            enable_llm_entity_for_routing=False,
            max_entities_per_episode=10,
            max_chunk_summaries_in_prompt=5,
        )

        # Each doc gets its own episode
        assert len(result.by_episode) == 3


# ============================================================
# Test write_same_entity_edges and write_facet_entity_edges
# ============================================================


class TestWriteSameEntityEdges:
    """Tests for write_same_entity_edges function."""

    @pytest.mark.asyncio
    async def test_empty_input(self):
        """Test with empty memory_nodes list."""
        from m_flow.memory.episodic.edge_writers import write_same_entity_edges

        result = await write_same_entity_edges([])

        assert result == []


class TestWriteFacetEntityEdges:
    """Tests for write_facet_entity_edges function."""

    @pytest.mark.asyncio
    async def test_empty_input(self):
        """Test with empty memory_nodes list."""
        from m_flow.memory.episodic.edge_writers import write_facet_entity_edges

        result = await write_facet_entity_edges([])

        assert result == []


# ============================================================
# Function Existence Tests
# ============================================================


class TestFunctionSignatures:
    """Tests to verify function signatures and existence."""

    def test_find_existing_entities_exists(self):
        """Verify _find_existing_entities_by_canonical_name exists."""
        from m_flow.memory.episodic.write_episodic_memories import (
            _find_existing_entities_by_canonical_name,
        )

        assert callable(_find_existing_entities_by_canonical_name)

    def test_batch_find_exists(self):
        """Verify _batch_find_existing_entities_by_canonical_names exists."""
        from m_flow.memory.episodic.write_episodic_memories import (
            _batch_find_existing_entities_by_canonical_names,
        )

        assert callable(_batch_find_existing_entities_by_canonical_names)

    def test_route_documents_exists(self):
        """Verify _route_documents_to_episodes exists."""
        from m_flow.memory.episodic.write_episodic_memories import _route_documents_to_episodes

        assert callable(_route_documents_to_episodes)

    def test_write_episodic_memories_exists(self):
        """Verify write_episodic_memories exists."""
        from m_flow.memory.episodic.write_episodic_memories import write_episodic_memories

        assert callable(write_episodic_memories)

    def test_write_same_entity_edges_exists(self):
        """Verify write_same_entity_edges exists."""
        from m_flow.memory.episodic.edge_writers import write_same_entity_edges

        assert callable(write_same_entity_edges)

    def test_write_facet_entity_edges_exists(self):
        """Verify write_facet_entity_edges exists."""
        from m_flow.memory.episodic.edge_writers import write_facet_entity_edges

        assert callable(write_facet_entity_edges)


# ============================================================
# Semaphore and Concurrency Tests
# ============================================================


class TestSemaphoreControl:
    """Tests for LLM concurrency control via semaphore."""

    def test_semaphore_functions_exist(self):
        """Verify semaphore functions exist and are callable."""
        from m_flow.shared.llm_concurrency import (
            get_global_llm_semaphore,
            get_llm_concurrency_limit,
        )

        assert callable(get_global_llm_semaphore)
        assert callable(get_llm_concurrency_limit)

        # Get the concurrency limit
        limit = get_llm_concurrency_limit()
        assert isinstance(limit, int)
        assert limit > 0


# ============================================================
# RoutingResult Tests
# ============================================================


class TestRoutingResult:
    """Tests for RoutingResult dataclass."""

    def test_routing_result_creation(self):
        """Test RoutingResult can be created."""
        from m_flow.memory.episodic.write_episodic_memories import RoutingResult

        result = RoutingResult(
            by_episode={},
            episode_doc_titles={},
            doc_entity_cache={},
        )

        assert result.by_episode == {}
        assert result.episode_doc_titles == {}
        assert result.doc_entity_cache == {}
        assert result.routing_decisions == {}  # default
        assert result.episode_memory_types == {}  # default

    def test_routing_result_with_data(self):
        """Test RoutingResult with actual data."""
        from m_flow.memory.episodic.write_episodic_memories import RoutingResult

        episode_id = new_uuid()

        result = RoutingResult(
            by_episode={episode_id: []},
            episode_doc_titles={episode_id: ["doc1"]},
            doc_entity_cache={"doc1": ["Entity1"]},
            routing_decisions={episode_id: "new"},
            episode_memory_types={episode_id: "episodic"},
        )

        assert episode_id in result.by_episode
        assert result.routing_decisions[episode_id] == "new"
        assert result.episode_memory_types[episode_id] == "episodic"


# ============================================================
# Run Tests
# ============================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
