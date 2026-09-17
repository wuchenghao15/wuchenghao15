"""
Neptune Analytics Vector Backend Tests for M-flow.

Integration tests for AWS Neptune Analytics as a vector store backend,
including configuration validation, CRUD operations, and search functionality.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

import m_flow
from m_flow.adapters.hybrid.neptune_analytics.NeptuneAnalyticsAdapter import (
    IndexSchema,
    NeptuneAnalyticsAdapter,
)
from m_flow.adapters.vector import get_vector_provider
from m_flow.auth.methods import get_seed_user
from m_flow.search.operations import get_history
from m_flow.search.types import RecallMode
from m_flow.shared.logging_utils import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger()

# ============================================================================
# Test Configuration
# ============================================================================

TESTS_DIR = Path(__file__).parent
DATA_STORAGE_PATH = TESTS_DIR / ".data_storage" / "test_neptune"
SYSTEM_STORAGE_PATH = TESTS_DIR / ".mflow/system" / "test_neptune"

NLP_TEST_FILE = TESTS_DIR / "test_data" / "Natural_language_processing.txt"
QUANTUM_TEST_FILE = TESTS_DIR / "test_data" / "Quantum_computers.txt"

DATASET_LABEL = "cs_explanations"


# ============================================================================
# Helper Functions
# ============================================================================


def get_neptune_graph_id() -> str:
    """Retrieve Neptune graph ID from environment."""
    return os.getenv("GRAPH_ID", "")


def configure_neptune_backend() -> None:
    """Set up M-flow to use Neptune Analytics vector store."""
    graph_identifier = get_neptune_graph_id()

    m_flow.config.set_vector_db_provider("neptune_analytics")
    m_flow.config.set_vector_db_url(f"neptune-graph://{graph_identifier}")


def configure_test_storage() -> str:
    """Configure test storage directories and return data path."""
    data_path = str(DATA_STORAGE_PATH.resolve())
    system_path = str(SYSTEM_STORAGE_PATH.resolve())

    m_flow.config.data_root_directory(data_path)
    m_flow.config.system_root_directory(system_path)

    return data_path


async def reset_mflow_state() -> None:
    """Clear all M-flow data and system state."""
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)


# ============================================================================
# End-to-End Integration Test
# ============================================================================


async def run_neptune_integration_test() -> None:
    """Full integration test for Neptune Analytics backend."""
    configure_neptune_backend()
    data_path = configure_test_storage()

    await reset_mflow_state()

    # Add test documents
    await m_flow.add([str(NLP_TEST_FILE)], DATASET_LABEL)
    await m_flow.add([str(QUANTUM_TEST_FILE)], DATASET_LABEL)

    # Process documents
    await m_flow.memorize([DATASET_LABEL])

    # Perform vector search to get a node
    engine = get_vector_provider()
    search_hits = await engine.search("Entity_name", "Quantum computer")
    assert len(search_hits) > 0, "No search results from vector engine"

    target_text = search_hits[0].payload["text"]

    # Test graph completion search
    completion_results = await m_flow.search(
        query_type=RecallMode.TRIPLET_COMPLETION,
        query_text=target_text,
    )
    assert len(completion_results) > 0, "Graph completion search returned no results"
    logger.info(f"Graph completion found {len(completion_results)} results")

    # Test episodic search
    episodic_results = await m_flow.search(
        query_type=RecallMode.EPISODIC,
        query_text=target_text,
    )
    assert len(episodic_results) > 0, "Episodic search returned no results"
    logger.info(f"Episodic search found {len(episodic_results)} results")

    # Verify search history
    user = await get_seed_user()
    history_records = await get_history(user.id)
    assert len(history_records) > 0, "History should not be empty"

    # Cleanup and verify
    await m_flow.prune.prune_data()
    assert not os.path.isdir(data_path), "Data directory should be removed after prune"

    await m_flow.prune.prune_system(metadata=True)


# ============================================================================
# Vector Backend API Tests
# ============================================================================


async def run_vector_api_tests() -> None:
    """Test Neptune Analytics vector engine API directly."""
    m_flow.config.set_vector_db_provider("neptune_analytics")

    # Test: Missing URL raises OSError
    m_flow.config.set_vector_db_url(None)
    with pytest.raises(OSError):
        get_vector_provider()

    # Test: Invalid URL format raises ValueError
    m_flow.config.set_vector_db_url("invalid_url_format")
    with pytest.raises(ValueError):
        get_vector_provider()

    # Test: Valid URL returns adapter
    graph_id = get_neptune_graph_id()
    m_flow.config.set_vector_db_url(f"neptune-graph://{graph_id}")

    engine = get_vector_provider()
    assert isinstance(engine, NeptuneAnalyticsAdapter), "Expected NeptuneAnalyticsAdapter instance"

    # Setup test data
    collection = "test"

    id_1 = str(uuid.uuid4())
    text_1 = "Hello world"
    point_1 = IndexSchema(id=id_1, text=text_1)

    id_2 = str(uuid.uuid4())
    text_2 = "Mflow"
    point_2 = IndexSchema(id=id_2, text=text_2)

    # Clear existing data
    await engine.prune()

    # Test: has_collection always returns True
    assert await engine.has_collection(collection)

    # Test: create_collection is no-op
    await engine.create_collection(collection, IndexSchema)

    # Test: Create memory nodes
    await engine.create_memory_nodes(collection, [point_1, point_2])

    # Test: Search returns results
    search_results = await engine.search(
        collection_name=collection,
        query_text=text_1,
        query_vector=None,
        limit=10,
        with_vector=True,
    )
    assert len(search_results) == 2, f"Expected 2 results, got {len(search_results)}"

    # Test: Retrieve specific points
    retrieved = await engine.retrieve(collection, [id_1, id_2])

    found_1 = any(str(r.id) == id_1 and r.payload["text"] == text_1 for r in retrieved)
    found_2 = any(str(r.id) == id_2 and r.payload["text"] == text_2 for r in retrieved)
    assert found_1 and found_2, "Failed to retrieve both data points"

    # Test: Batch search
    batch_results = await engine.batch_search(
        collection_name=collection,
        query_texts=[text_1, text_2],
        limit=10,
        with_vectors=False,
    )
    assert len(batch_results) == 2, "Batch search should return 2 result sets"
    assert all(len(batch) == 2 for batch in batch_results), "Each batch should have 2 results"

    # Test: Delete memory nodes
    await engine.delete_memory_nodes(collection, [id_1, id_2])

    # Verify deletion
    after_delete = await engine.retrieve(collection, [id_1])
    assert len(after_delete) == 0, "Deleted point should not be retrievable"


# ============================================================================
# Main Entry Point
# ============================================================================


if __name__ == "__main__":
    asyncio.run(run_neptune_integration_test())
    asyncio.run(run_vector_api_tests())
