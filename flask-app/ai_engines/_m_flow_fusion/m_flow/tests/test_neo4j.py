"""
Neo4j Graph Database Integration Test
=====================================
m_flow.tests.test_neo4j

Validates Neo4j as a graph database backend:
- Graph storage and retrieval operations
- Knowledge graph construction in Neo4j
- Multi-mode search with Neo4j backend
- Node set (MemorySpace) functionality
- Complete cleanup verification
"""

import pathlib
import os

import m_flow
from m_flow.shared.files.storage import get_storage_config
from m_flow.retrieval.unified_triplet_search import UnifiedTripletSearch
from m_flow.search.operations import get_history
from m_flow.auth.methods import get_seed_user
from m_flow.shared.logging_utils import get_logger
from m_flow.search.types import RecallMode
from m_flow.core.domain.models import MemorySpace

_logger = get_logger()


async def main():
    """
    Primary test runner for Neo4j integration.

    Configures Neo4j and validates full graph database functionality.
    """
    # Configure Neo4j as graph backend
    m_flow.config.set_graph_database_provider("neo4j")

    # Initialize storage paths
    test_root = pathlib.Path(__file__).parent
    data_dir = (test_root / ".data_storage" / "test_neo4j").resolve()
    system_dir = (test_root / ".mflow/system" / "test_neo4j").resolve()

    m_flow.config.data_root_directory(str(data_dir))
    m_flow.config.system_root_directory(str(system_dir))

    # Clean start
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)

    # Prepare test data
    ds_name = "cs_explanations"
    nlp_file = test_root / "test_data" / "Natural_language_processing.txt"
    quantum_file = test_root / "test_data" / "Quantum_computers.txt"

    # Get graph engine and verify empty state
    from m_flow.adapters.graph import get_graph_provider

    graph = await get_graph_provider()

    is_empty = await graph.is_empty()
    assert is_empty, "Graph must be empty before test"

    # Add data
    await m_flow.add([str(nlp_file)], ds_name)
    await m_flow.add([str(quantum_file)], ds_name)

    # Verify graph still empty before memorize
    is_empty = await graph.is_empty()
    assert is_empty, "Graph must be empty before memorize"

    # Execute memorization
    await m_flow.memorize([ds_name])

    # Verify graph has content after memorize
    is_empty = await graph.is_empty()
    assert not is_empty, "Graph should contain data after memorize"

    # Initialize vector search
    from m_flow.adapters.vector import get_vector_provider

    vec = get_vector_provider()

    concept_hit = (await vec.search("Entity_name", "Quantum computer"))[0]
    query_text = concept_hit.payload["text"]

    # Test TRIPLET_COMPLETION mode
    completion = await m_flow.search(
        query_type=RecallMode.TRIPLET_COMPLETION,
        query_text=query_text,
    )
    assert len(completion) > 0, "TRIPLET_COMPLETION returned empty"
    _logger.info("Graph completion: %d results", len(completion))

    # Test EPISODIC mode
    episodic = await m_flow.search(
        query_type=RecallMode.EPISODIC,
        query_text=query_text,
    )
    _logger.info("Episodic: %d results", len(episodic))

    # Validate search history
    user = await get_seed_user()
    history = await get_history(user.id)
    assert len(history) > 0, "History should not be empty"

    # =========================================
    # Test: MemorySpace (graph_scope) functionality
    # =========================================
    _logger.info("Testing MemorySpace functionality")

    neo4j_content = "Neo4j is a graph database that supports cypher."
    await m_flow.add([neo4j_content], ds_name, graph_scope=["first"])
    await m_flow.memorize([ds_name])

    # Search existing node set - should return results
    existing_context = await UnifiedTripletSearch(
        node_type=MemorySpace,
        node_name=["first"],
    ).get_context("What is in the context?")

    # Search non-existent node set - should return empty
    missing_context = await UnifiedTripletSearch(
        node_type=MemorySpace,
        node_name=["nonexistent"],
    ).get_context("What is in the context?")

    assert isinstance(existing_context, list) and existing_context, (
        f"Node set search should return non-empty list: {existing_context!r}"
    )
    assert missing_context == [], f"Missing node set should return empty list: {missing_context!r}"

    # =========================================
    # Cleanup verification
    # =========================================
    await m_flow.prune.prune_data()
    storage_cfg = get_storage_config()
    assert not os.path.isdir(storage_cfg["data_root_directory"]), "Data directory persists after cleanup"

    await m_flow.prune.prune_system(metadata=True)
    is_empty = await graph.is_empty()
    assert is_empty, "Neo4j should be empty after cleanup"

    _logger.info("Neo4j integration test completed")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
