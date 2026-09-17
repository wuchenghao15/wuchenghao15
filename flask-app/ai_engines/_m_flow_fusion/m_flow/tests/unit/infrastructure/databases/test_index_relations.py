import pytest
from unittest.mock import AsyncMock, patch
from m_flow.storage.index_graph_links import index_relations


@pytest.mark.asyncio
async def test_index_relations_success():
    """Test that index_relations retrieves edges and delegates to index_memory_nodes."""
    mock_graph_engine = AsyncMock()
    mock_graph_engine.get_graph_data.return_value = (
        None,
        [
            [{"relationship_name": "rel1"}, {"relationship_name": "rel1"}],
            [{"relationship_name": "rel2"}],
        ],
    )
    mock_index_memory_nodes = AsyncMock()

    with patch.dict(
        index_relations.__globals__,
        {
            "get_graph_provider": AsyncMock(return_value=mock_graph_engine),
            "index_memory_nodes": mock_index_memory_nodes,
        },
    ):
        await index_relations()

    mock_graph_engine.get_graph_data.assert_awaited_once()
    mock_index_memory_nodes.assert_awaited_once()

    call_args = mock_index_memory_nodes.call_args[0][0]
    assert len(call_args) == 2
    assert all(hasattr(item, "relationship_name") for item in call_args)


@pytest.mark.asyncio
async def test_index_relations_no_relationships():
    """Test that index_relations handles empty relationships correctly."""
    mock_graph_engine = AsyncMock()
    mock_graph_engine.get_graph_data.return_value = (None, [])
    mock_index_memory_nodes = AsyncMock()

    with patch.dict(
        index_relations.__globals__,
        {
            "get_graph_provider": AsyncMock(return_value=mock_graph_engine),
            "index_memory_nodes": mock_index_memory_nodes,
        },
    ):
        await index_relations()

    mock_graph_engine.get_graph_data.assert_awaited_once()
    mock_index_memory_nodes.assert_awaited_once()

    call_args = mock_index_memory_nodes.call_args[0][0]
    assert len(call_args) == 0


@pytest.mark.asyncio
async def test_index_relations_initialization_error():
    """Test that index_relations raises a RuntimeError if initialization fails."""
    with patch.dict(
        index_relations.__globals__,
        {
            "get_graph_provider": AsyncMock(side_effect=Exception("Graph engine failed")),
            "get_vector_provider": lambda: AsyncMock(),
        },
    ):
        with pytest.raises(RuntimeError, match="Initialization error"):
            await index_relations()
