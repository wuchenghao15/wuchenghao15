import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from m_flow.storage.index_memory_nodes import index_memory_nodes
from m_flow.core import MemoryNode


class TestMemoryNode(MemoryNode):
    name: str
    metadata: dict = {"index_fields": ["name"]}


@pytest.mark.asyncio
async def test_index_memory_nodes_calls_vector_engine():
    """Test that index_memory_nodes creates vector index and indexes data."""
    memory_nodes = [TestMemoryNode(name="test1")]

    mock_vector_engine = AsyncMock()
    mock_vector_engine.embedding_engine.get_batch_size = MagicMock(return_value=100)

    with patch.dict(
        index_memory_nodes.__globals__,
        {"get_vector_provider": lambda: mock_vector_engine},
    ):
        await index_memory_nodes(memory_nodes)

    assert mock_vector_engine.create_vector_index.await_count >= 1
    assert mock_vector_engine.index_memory_nodes.await_count >= 1
