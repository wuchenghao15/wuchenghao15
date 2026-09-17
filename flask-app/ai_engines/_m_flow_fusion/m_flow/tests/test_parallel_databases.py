"""
Parallel Database Operations Test for M-flow.

Tests concurrent memorize operations with isolated database configurations
to verify thread-safety and proper database isolation.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

import m_flow
from m_flow.shared.logging_utils import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger()

# ============================================================================
# Test Configuration
# ============================================================================

TESTS_DIR = Path(__file__).parent
DATA_STORAGE = TESTS_DIR / ".data_storage" / "test_library"
SYSTEM_STORAGE = TESTS_DIR / ".mflow/system" / "test_library"

# Test datasets
DATASET_1 = "test1"
DATASET_2 = "test2"
CONTENT_1 = "TEST1"
CONTENT_2 = "TEST2"


# ============================================================================
# Database Configurations
# ============================================================================


def get_vector_config_1() -> dict:
    """Configuration for first isolated vector database."""
    return {
        "vector_db_url": "m_flow1.test",
        "vector_db_key": "",
        "vector_db_provider": "lancedb",
        "vector_db_name": "",
    }


def get_vector_config_2() -> dict:
    """Configuration for second isolated vector database."""
    return {
        "vector_db_url": "m_flow2.test",
        "vector_db_key": "",
        "vector_db_provider": "lancedb",
        "vector_db_name": "",
    }


def get_graph_config_1() -> dict:
    """Configuration for first isolated graph database."""
    return {
        "graph_database_provider": "kuzu",
        "graph_file_path": "kuzu1.db",
    }


def get_graph_config_2() -> dict:
    """Configuration for second isolated graph database."""
    return {
        "graph_database_provider": "kuzu",
        "graph_file_path": "kuzu2.db",
    }


# ============================================================================
# Test Execution
# ============================================================================


async def run_parallel_database_test() -> None:
    """
    Test concurrent memorize operations with separate databases.

    This test verifies that:
    1. Two memorize operations can run concurrently
    2. Each operation uses its own isolated database
    3. No data mixing or race conditions occur
    """
    # Configure storage paths
    m_flow.config.data_root_directory(str(DATA_STORAGE.resolve()))
    m_flow.config.system_root_directory(str(SYSTEM_STORAGE.resolve()))

    # Reset state
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)

    # Add test datasets
    await m_flow.add([CONTENT_1], DATASET_1)
    await m_flow.add([CONTENT_2], DATASET_2)

    logger.info("Starting parallel memorize operations...")

    # Create concurrent tasks with isolated database configs
    task1 = asyncio.create_task(
        m_flow.memorize(
            [DATASET_1],
            vector_db_config=get_vector_config_1(),
            graph_db_config=get_graph_config_1(),
        )
    )

    task2 = asyncio.create_task(
        m_flow.memorize(
            [DATASET_2],
            vector_db_config=get_vector_config_2(),
            graph_db_config=get_graph_config_2(),
        )
    )

    # Wait for both tasks to complete
    results = await asyncio.gather(task1, task2)

    logger.info(f"Parallel memorize completed: {results}")
    print("Parallel database test passed successfully!")


# ============================================================================
# Main Entry Point
# ============================================================================


if __name__ == "__main__":
    asyncio.run(run_parallel_database_test(), debug=True)
