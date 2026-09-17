"""
Remote Kuzu Graph Database Test
================================
m_flow.tests.test_remote_kuzu

Validates remote Kuzu graph database connectivity and operations:
- Remote connection establishment via environment variables
- Knowledge graph construction on remote Kuzu instance
- Multi-mode search with remote graph backend
- Proper cleanup of remote graph data
"""

import pathlib
import shutil
import os

import m_flow
from m_flow.shared.files.storage import get_storage_config
from m_flow.shared.logging_utils import get_logger
from m_flow.search.types import RecallMode
from m_flow.search.operations import get_history
from m_flow.auth.methods import get_seed_user

_logger = get_logger()


async def main():
    """
    Primary test execution for remote Kuzu integration.

    Configures remote Kuzu connection and validates full functionality.
    """
    # Determine storage paths
    test_root = pathlib.Path(__file__).parent
    data_storage = (test_root / ".data_storage" / "test_remote_kuzu").resolve()
    system_storage = (test_root / ".mflow/system" / "test_remote_kuzu").resolve()

    try:
        # Configure Kuzu as graph provider
        m_flow.config.set_graph_database_provider("kuzu")
        m_flow.config.data_root_directory(str(data_storage))
        m_flow.config.system_root_directory(str(system_storage))

        # Set remote Kuzu connection parameters from environment
        os.environ.setdefault("KUZU_HOST", "localhost")
        os.environ.setdefault("KUZU_PORT", "8000")
        os.environ.setdefault("KUZU_USERNAME", "kuzu")
        os.environ.setdefault("KUZU_PASSWORD", "kuzu")
        os.environ.setdefault("KUZU_DATABASE", "m_flow_test")

        # Initialize clean state
        await m_flow.prune.prune_data()
        await m_flow.prune.prune_system(metadata=True)

        # Prepare test dataset
        ds_name = "cs_explanations"
        nlp_file = test_root / "test_data" / "Natural_language_processing.txt"
        quantum_file = test_root / "test_data" / "Quantum_computers.txt"

        await m_flow.add([str(nlp_file)], ds_name)
        await m_flow.add([str(quantum_file)], ds_name)

        # Execute memorization
        await m_flow.memorize([ds_name])

        # Search tests
        from m_flow.adapters.vector import get_vector_provider

        vec = get_vector_provider()

        concept_hit = (await vec.search("Entity_name", "Quantum computer"))[0]
        query_text = concept_hit.payload["text"]

        # TRIPLET_COMPLETION mode
        completion = await m_flow.search(
            query_type=RecallMode.TRIPLET_COMPLETION,
            query_text=query_text,
        )
        assert len(completion) > 0, "TRIPLET_COMPLETION returned empty"
        _logger.info("Completion: %d results", len(completion))

        # EPISODIC mode
        episodic = await m_flow.search(
            query_type=RecallMode.EPISODIC,
            query_text=query_text,
        )
        assert len(episodic) > 0, "EPISODIC returned empty"
        _logger.info("Episodic: %d results", len(episodic))

        # Validate search history
        user = await get_seed_user()
        history = await get_history(user.id)
        assert len(history) > 0, "History should not be empty"

        # Cleanup validation
        await m_flow.prune.prune_data()
        storage_cfg = get_storage_config()
        assert not os.path.isdir(storage_cfg["data_root_directory"]), "Local data directory persists"

        await m_flow.prune.prune_system(metadata=True)

        # Verify remote graph is empty
        from m_flow.adapters.graph import get_graph_provider

        graph = await get_graph_provider()
        nodes, edges = await graph.get_graph_data()
        assert len(nodes) == 0 and len(edges) == 0, f"Remote Kuzu not empty: {len(nodes)} nodes, {len(edges)} edges"

        _logger.info("Remote Kuzu integration test completed")

    finally:
        # Cleanup local test directories regardless of test outcome
        for cleanup_path in [data_storage, system_storage]:
            if cleanup_path.exists():
                shutil.rmtree(cleanup_path)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
