"""
Dataset Deletion Test Module
============================
m_flow.tests.test_dataset_delete

Validates the complete lifecycle of dataset deletion including:
- Database cleanup after delete operations
- File system artifact removal
- Integration with vector and graph databases
"""

import pathlib
import asyncio
import os
from uuid import UUID

import m_flow
from m_flow.shared.logging_utils import setup_logging, ERROR
from m_flow.data.methods.delete_dataset import delete_dataset
from m_flow.data.methods.get_dataset import get_dataset
from m_flow.auth.methods import get_seed_user


async def run_deletion_test():
    """
    Main test execution for dataset deletion functionality.

    Creates datasets, processes them, then deletes and verifies cleanup.
    """
    # Configure storage locations
    test_dir = pathlib.Path(__file__).parent
    data_storage = (test_dir / ".data_storage" / "test_dataset_delete").resolve()
    system_storage = (test_dir / ".mflow/system" / "test_dataset_delete").resolve()

    m_flow.config.data_root_directory(str(data_storage))
    m_flow.config.system_root_directory(str(system_storage))

    # Initialize clean state
    print("Initializing test environment...")
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)
    print("Environment ready.\n")

    # Sample content for knowledge graph construction
    nlp_content = """
    Natural language processing (NLP) is an interdisciplinary
    subfield of computer science and information retrieval.
    """
    quantum_content = "Quantum computing is the study of quantum computers."

    # Create and process datasets
    await m_flow.add(nlp_content, "nlp_dataset")
    await m_flow.add(quantum_content, "quantum_dataset")

    # Execute memorization pipeline
    processed_datasets = await m_flow.memorize()
    current_user = await get_seed_user()

    # Verify and delete each processed dataset
    for dataset_id_str in processed_datasets:
        dataset_uuid = str(dataset_id_str)

        # Construct expected database paths
        user_db_folder = system_storage / "databases" / str(current_user.id)
        vector_db_file = user_db_folder / f"{dataset_uuid}.lance.db"
        graph_db_file = user_db_folder / f"{dataset_uuid}.pkl"

        # Assert databases were created
        assert os.path.exists(graph_db_file), f"Graph database missing before delete: {graph_db_file}"
        assert os.path.exists(vector_db_file), f"Vector database missing before delete: {vector_db_file}"

        # Retrieve and delete dataset
        target_dataset = await get_dataset(
            user_id=current_user.id,
            dataset_id=UUID(dataset_uuid),
        )
        await delete_dataset(target_dataset)

        # Confirm complete cleanup
        assert not os.path.exists(graph_db_file), f"Graph database persists after delete: {graph_db_file}"
        assert not os.path.exists(vector_db_file), f"Vector database persists after delete: {vector_db_file}"

    print("Dataset deletion test completed successfully.")


if __name__ == "__main__":
    log_handler = setup_logging(log_level=ERROR)
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    try:
        event_loop.run_until_complete(run_deletion_test())
    finally:
        event_loop.run_until_complete(event_loop.shutdown_asyncgens())
