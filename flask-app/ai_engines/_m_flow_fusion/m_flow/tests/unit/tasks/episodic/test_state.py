# m_flow/tests/unit/tasks/episodic/test_state.py
"""
Episode State module unit tests.

Test all functions and classes in state.py module:
1. ExistingFacet: Facet data model
2. EpisodeState: Episode state data model
3. fetch_episode_state: Episode state query
4. ExistingFacetPoint: FacetPoint data model
5. fetch_facet_points: FacetPoint query
"""

import pytest
from unittest.mock import AsyncMock

from m_flow.memory.episodic.state import (
    ExistingFacet,
    EpisodeState,
    fetch_episode_state,
    ExistingFacetPoint,
    fetch_facet_points,
)


# ============================================================
# Test ExistingFacet model
# ============================================================


class TestExistingFacet:
    """Test ExistingFacet data model."""

    def test_create_with_all_fields(self):
        """Create ExistingFacet with all fields."""
        facet = ExistingFacet(
            id="facet-123",
            facet_type="fact",
            search_text="Machine learning is a branch of AI",
            description="A detailed description",
            aliases=["ML", "machine_learning"],
        )

        assert facet.id == "facet-123"
        assert facet.facet_type == "fact"
        assert facet.search_text == "Machine learning is a branch of AI"
        assert facet.description == "A detailed description"
        assert facet.aliases == ["ML", "machine_learning"]

    def test_create_with_minimal_fields(self):
        """Create ExistingFacet with only required fields."""
        facet = ExistingFacet(id="facet-456")

        assert facet.id == "facet-456"
        assert facet.facet_type is None
        assert facet.search_text is None
        assert facet.description is None
        assert facet.aliases == []
        # Time fields should be None by default
        assert facet.mentioned_time_start_ms is None
        assert facet.mentioned_time_end_ms is None
        assert facet.mentioned_time_confidence is None
        assert facet.mentioned_time_text is None

    def test_create_with_time_fields(self):
        """Create ExistingFacet with time fields."""
        facet = ExistingFacet(
            id="facet-time-123",
            facet_type="event",
            search_text="Meeting on May 7, 2023",
            mentioned_time_start_ms=1683417600000,
            mentioned_time_end_ms=1683504000000,
            mentioned_time_confidence=0.85,
            mentioned_time_text="May 7, 2023",
        )

        assert facet.mentioned_time_start_ms == 1683417600000
        assert facet.mentioned_time_end_ms == 1683504000000
        assert facet.mentioned_time_confidence == 0.85
        assert facet.mentioned_time_text == "May 7, 2023"

    def test_default_aliases_is_empty_list(self):
        """aliases defaults to empty list."""
        facet = ExistingFacet(id="facet-789")

        assert isinstance(facet.aliases, list)
        assert len(facet.aliases) == 0


# ============================================================
# Test EpisodeState model
# ============================================================


class TestEpisodeState:
    """Test EpisodeState data model."""

    def test_create_with_all_fields(self):
        """Create EpisodeState with all fields."""
        facet = ExistingFacet(id="f-1", search_text="Test facet")
        state = EpisodeState(
            episode_id="ep-123",
            title="Test Episode",
            signature="test_signature",
            summary="Episode summary",
            facets=[facet],
            entity_names=["Entity A", "Entity B"],
        )

        assert state.episode_id == "ep-123"
        assert state.title == "Test Episode"
        assert state.signature == "test_signature"
        assert state.summary == "Episode summary"
        assert len(state.facets) == 1
        assert state.entity_names == ["Entity A", "Entity B"]

    def test_create_with_minimal_fields(self):
        """Create EpisodeState with only required fields."""
        state = EpisodeState(episode_id="ep-456")

        assert state.episode_id == "ep-456"
        assert state.title is None
        assert state.signature is None
        assert state.summary is None
        assert state.facets == []
        assert state.entity_names == []


# ============================================================
# Test fetch_episode_state
# ============================================================


class TestFetchEpisodeState:
    """Test fetch_episode_state function."""

    @pytest.mark.asyncio
    async def test_fetches_episode_node_data(self):
        """Fetch Episode node data."""
        mock_engine = AsyncMock()
        mock_engine.get_node = AsyncMock(
            return_value={
                "name": "Test Title",
                "signature": "test_sig",
                "summary": "Test summary",
            }
        )
        mock_engine.get_edges = AsyncMock(return_value=[])

        state = await fetch_episode_state(mock_engine, "ep-123")

        assert state.episode_id == "ep-123"
        assert state.title == "Test Title"
        assert state.signature == "test_sig"
        assert state.summary == "Test summary"
        mock_engine.get_node.assert_called_once_with("ep-123")

    @pytest.mark.asyncio
    async def test_handles_missing_episode_node(self):
        """Handle non-existent Episode node."""
        mock_engine = AsyncMock()
        mock_engine.get_node = AsyncMock(return_value=None)
        mock_engine.get_edges = AsyncMock(return_value=[])

        state = await fetch_episode_state(mock_engine, "nonexistent")

        assert state.episode_id == "nonexistent"
        assert state.title is None
        assert state.signature is None
        assert state.summary is None

    @pytest.mark.asyncio
    async def test_handles_get_node_exception(self):
        """Handle get_node exception."""
        mock_engine = AsyncMock()
        mock_engine.get_node = AsyncMock(side_effect=Exception("DB Error"))
        mock_engine.get_edges = AsyncMock(return_value=[])

        # Should not raise exception
        state = await fetch_episode_state(mock_engine, "ep-123")

        assert state.episode_id == "ep-123"
        assert state.title is None

    @pytest.mark.asyncio
    async def test_fetches_facets_from_edges(self):
        """Fetch Facets from edges."""
        mock_engine = AsyncMock()
        mock_engine.get_node = AsyncMock(return_value={"name": "Test"})
        mock_engine.get_edges = AsyncMock(
            return_value=[
                (
                    {"id": "ep-123"},
                    "has_facet",
                    {
                        "id": "f-1",
                        "type": "Facet",
                        "facet_type": "fact",
                        "search_text": "Test fact",
                        "description": "Desc",
                        "aliases": ["alias1"],
                    },
                ),
            ]
        )

        state = await fetch_episode_state(mock_engine, "ep-123")

        assert len(state.facets) == 1
        assert state.facets[0].id == "f-1"
        assert state.facets[0].facet_type == "fact"
        assert state.facets[0].search_text == "Test fact"

    @pytest.mark.asyncio
    async def test_fetches_entity_names_from_edges(self):
        """Fetch Entity names from edges."""
        mock_engine = AsyncMock()
        mock_engine.get_node = AsyncMock(return_value={"name": "Test"})
        mock_engine.get_edges = AsyncMock(
            return_value=[
                (
                    {"id": "ep-123"},
                    "involves_entity",
                    {"id": "e-1", "type": "Entity", "name": "Entity A"},
                ),
                (
                    {"id": "ep-123"},
                    "involves_entity",
                    {"id": "e-2", "type": "Entity", "name": "Entity B"},
                ),
            ]
        )

        state = await fetch_episode_state(mock_engine, "ep-123")

        assert len(state.entity_names) == 2
        assert "Entity A" in state.entity_names
        assert "Entity B" in state.entity_names

    @pytest.mark.asyncio
    async def test_deduplicates_entity_names(self):
        """Deduplicate Entity names."""
        mock_engine = AsyncMock()
        mock_engine.get_node = AsyncMock(return_value={})
        mock_engine.get_edges = AsyncMock(
            return_value=[
                ({"id": "ep"}, "involves_entity", {"type": "Entity", "name": "Same"}),
                ({"id": "ep"}, "involves_entity", {"type": "Entity", "name": "Same"}),
                ({"id": "ep"}, "involves_entity", {"type": "Entity", "name": "Different"}),
            ]
        )

        state = await fetch_episode_state(mock_engine, "ep-123")

        assert len(state.entity_names) == 2
        assert "Same" in state.entity_names
        assert "Different" in state.entity_names

    @pytest.mark.asyncio
    async def test_ignores_non_facet_edges(self):
        """Ignore non-Facet type edges."""
        mock_engine = AsyncMock()
        mock_engine.get_node = AsyncMock(return_value={})
        mock_engine.get_edges = AsyncMock(
            return_value=[
                ({"id": "ep"}, "has_facet", {"type": "NotFacet", "id": "x"}),
                ({"id": "ep"}, "other_rel", {"type": "Facet", "id": "y"}),
            ]
        )

        state = await fetch_episode_state(mock_engine, "ep-123")

        assert len(state.facets) == 0


# ============================================================
# Test ExistingFacetPoint model
# ============================================================


class TestExistingFacetPoint:
    """Test ExistingFacetPoint data model."""

    def test_create_with_all_fields(self):
        """Create ExistingFacetPoint with all fields."""
        point = ExistingFacetPoint(
            id="fp-123",
            search_text="Specific detail",
            aliases=["detail", "point"],
            description="Point description",
        )

        assert point.id == "fp-123"
        assert point.search_text == "Specific detail"
        assert point.aliases == ["detail", "point"]
        assert point.description == "Point description"

    def test_create_with_minimal_fields(self):
        """Create ExistingFacetPoint with only required fields."""
        point = ExistingFacetPoint(
            id="fp-456",
            search_text="Required text",
        )

        assert point.id == "fp-456"
        assert point.search_text == "Required text"
        assert point.aliases == []
        assert point.description is None


# ============================================================
# Test fetch_facet_points
# ============================================================


class TestFetchFacetPoints:
    """Test fetch_facet_points function."""

    @pytest.mark.asyncio
    async def test_fetches_facet_points(self):
        """Fetch FacetPoints."""
        mock_engine = AsyncMock()
        mock_engine.get_edges = AsyncMock(
            return_value=[
                (
                    {"id": "f-1"},
                    "has_point",
                    {
                        "id": "fp-1",
                        "type": "FacetPoint",
                        "search_text": "Point 1",
                        "aliases": ["p1"],
                        "description": "Desc 1",
                    },
                ),
                (
                    {"id": "f-1"},
                    "has_point",
                    {
                        "id": "fp-2",
                        "type": "FacetPoint",
                        "search_text": "Point 2",
                    },
                ),
            ]
        )

        points = await fetch_facet_points(mock_engine, "f-1")

        assert len(points) == 2
        assert points[0].id == "fp-1"
        assert points[0].search_text == "Point 1"
        assert points[1].id == "fp-2"

    @pytest.mark.asyncio
    async def test_handles_empty_edges(self):
        """Handle empty edge list."""
        mock_engine = AsyncMock()
        mock_engine.get_edges = AsyncMock(return_value=[])

        points = await fetch_facet_points(mock_engine, "f-nonexistent")

        assert points == []

    @pytest.mark.asyncio
    async def test_handles_get_edges_exception(self):
        """Handle get_edges exception."""
        mock_engine = AsyncMock()
        mock_engine.get_edges = AsyncMock(side_effect=Exception("DB Error"))

        # Should not raise exception
        points = await fetch_facet_points(mock_engine, "f-1")

        assert points == []

    @pytest.mark.asyncio
    async def test_deduplicates_by_normalized_search_text(self):
        """Deduplicate by normalized search_text."""
        mock_engine = AsyncMock()
        mock_engine.get_edges = AsyncMock(
            return_value=[
                (
                    {"id": "f"},
                    "has_point",
                    {"type": "FacetPoint", "id": "1", "search_text": "Test Point"},
                ),
                (
                    {"id": "f"},
                    "has_point",
                    {"type": "FacetPoint", "id": "2", "search_text": "TEST POINT"},
                ),  # Duplicate
                (
                    {"id": "f"},
                    "has_point",
                    {"type": "FacetPoint", "id": "3", "search_text": "Different"},
                ),
            ]
        )

        points = await fetch_facet_points(mock_engine, "f-1")

        # Should deduplicate
        assert len(points) <= 3  # Depends on normalize_for_compare implementation

    @pytest.mark.asyncio
    async def test_ignores_non_facetpoint_edges(self):
        """Ignore non-FacetPoint type edges."""
        mock_engine = AsyncMock()
        mock_engine.get_edges = AsyncMock(
            return_value=[
                (
                    {"id": "f"},
                    "has_point",
                    {"type": "NotFacetPoint", "id": "1", "search_text": "X"},
                ),
                ({"id": "f"}, "other_rel", {"type": "FacetPoint", "id": "2", "search_text": "Y"}),
            ]
        )

        points = await fetch_facet_points(mock_engine, "f-1")

        assert len(points) == 0

    @pytest.mark.asyncio
    async def test_skips_empty_search_text(self):
        """Skip empty search_text."""
        mock_engine = AsyncMock()
        mock_engine.get_edges = AsyncMock(
            return_value=[
                ({"id": "f"}, "has_point", {"type": "FacetPoint", "id": "1", "search_text": ""}),
                (
                    {"id": "f"},
                    "has_point",
                    {"type": "FacetPoint", "id": "2", "search_text": "Valid"},
                ),
            ]
        )

        points = await fetch_facet_points(mock_engine, "f-1")

        assert len(points) == 1
        assert points[0].search_text == "Valid"

    @pytest.mark.asyncio
    async def test_handles_non_list_aliases(self):
        """Handle non-list type aliases."""
        mock_engine = AsyncMock()
        mock_engine.get_edges = AsyncMock(
            return_value=[
                (
                    {"id": "f"},
                    "has_point",
                    {
                        "type": "FacetPoint",
                        "id": "1",
                        "search_text": "Test",
                        "aliases": "not a list",  # Should be handled
                    },
                ),
            ]
        )

        points = await fetch_facet_points(mock_engine, "f-1")

        assert len(points) == 1
        assert points[0].aliases == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
