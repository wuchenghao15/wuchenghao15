"""
Kuzu Graph Database Integration Test
=====================================
m_flow.tests.test_kuzu

Validates Kuzu as a local graph database backend:
- Embedded graph storage and retrieval
- Knowledge graph construction in Kuzu
- Multi-mode search with Kuzu backend
- MemorySpace (graph_scope) functionality
- Complete cleanup verification with automatic directory removal
"""

import pathlib
import shutil
import os

import m_flow
from m_flow.shared.files.storage import get_storage_config
from m_flow.core.domain.models import MemorySpace
from m_flow.retrieval.unified_triplet_search import UnifiedTripletSearch
from m_flow.shared.logging_utils import get_logger
from m_flow.search.types import RecallMode
from m_flow.search.operations import get_history
from m_flow.auth.methods import get_seed_user

_logger = get_logger()


async def main():
    """
    Primary test execution for Kuzu integration.

    Uses try/finally pattern to ensure cleanup even on test failure.
    """
    # Configure storage paths
    test_root = pathlib.Path(__file__).parent
    data_dir = (test_root / ".data_storage" / "test_kuzu").resolve()
    system_dir = (test_root / ".mflow/system" / "test_kuzu").resolve()

    try:
        # Configure Kuzu as graph backend
        m_flow.config.set_graph_database_provider("kuzu")
        m_flow.config.data_root_directory(str(data_dir))
        m_flow.config.system_root_directory(str(system_dir))

        # Initialize clean state
        await m_flow.prune.prune_data()
        await m_flow.prune.prune_system(metadata=True)

        # Prepare test data
        ds_name = "cs_explanations"
        nlp_file = test_root / "test_data" / "Natural_language_processing.txt"
        quantum_file = test_root / "test_data" / "Quantum_computers.txt"

        await m_flow.add([str(nlp_file)], ds_name)

        # Verify graph is empty before memorize
        from m_flow.adapters.graph import get_graph_provider

        graph = await get_graph_provider()

        is_empty = await graph.is_empty()
        assert is_empty, "Kuzu must be empty initially"

        await m_flow.add([str(quantum_file)], ds_name)
        is_empty = await graph.is_empty()
        assert is_empty, "Kuzu must be empty before memorize"

        # Execute memorization
        await m_flow.memorize([ds_name])
        is_empty = await graph.is_empty()
        assert not is_empty, "Kuzu must contain data after memorize"

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

        cypher_content = "Neo4j is a graph database that supports cypher."
        await m_flow.add([cypher_content], ds_name, graph_scope=["first"])
        await m_flow.memorize([ds_name])

        # Search existing node set
        existing_ctx = await UnifiedTripletSearch(
            node_type=MemorySpace,
            node_name=["first"],
        ).get_context("What is in the context?")

        # Search non-existent node set
        missing_ctx = await UnifiedTripletSearch(
            node_type=MemorySpace,
            node_name=["nonexistent"],
        ).get_context("What is in the context?")

        assert isinstance(existing_ctx, list) and existing_ctx, (
            f"Node set should return non-empty list: {existing_ctx!r}"
        )
        assert missing_ctx == [], f"Missing node set should return empty list: {missing_ctx!r}"

        # =========================================
        # Cleanup verification
        # =========================================
        await m_flow.prune.prune_data()
        storage_cfg = get_storage_config()
        assert not os.path.isdir(storage_cfg["data_root_directory"]), "Data directory persists after cleanup"

        await m_flow.prune.prune_system(metadata=True)
        is_empty = await graph.is_empty()
        assert is_empty, "Kuzu should be empty after cleanup"

        _logger.info("Kuzu integration test completed")

    finally:
        # Ensure directory cleanup even on test failure
        for cleanup_path in [data_dir, system_dir]:
            if cleanup_path.exists():
                shutil.rmtree(cleanup_path)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
