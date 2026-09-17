"""
Custom Dataset Database Handler Tests for M-flow.

Tests custom database handler registration and usage for both
vector (LanceDB) and graph (Kuzu) databases per-dataset isolation.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import TYPE_CHECKING

# Configure environment before imports
os.environ["MFLOW_VECTOR_DATASET_DATABASE_HANDLER"] = "custom_lancedb_handler"
os.environ["MFLOW_GRAPH_DATASET_DATABASE_HANDLER"] = "custom_kuzu_handler"

import m_flow
from m_flow.adapters.dataset_database_handler import DatasetStoreHandlerInterface
from m_flow.adapters.dataset_database_handler.use_dataset_database_handler import (
    use_dataset_database_handler,
)
from m_flow.api.v1.search import RecallMode
from m_flow.auth.methods import get_seed_user
from m_flow.shared.logging_utils import ERROR, setup_logging

if TYPE_CHECKING:
    from typing import Any

# ============================================================================
# Test Configuration
# ============================================================================

TESTS_DIR = Path(__file__).parent
DATA_STORAGE = TESTS_DIR / ".data_storage" / "test_dataset_database_handler"
SYSTEM_STORAGE = TESTS_DIR / ".mflow/system" / "test_dataset_database_handler"

VECTOR_DB_NAME = "test.lance.db"
GRAPH_DB_NAME = "test.kuzu"


# ============================================================================
# Custom Handler Implementations
# ============================================================================


class CustomLanceDBHandler(DatasetStoreHandlerInterface):
    """Custom LanceDB dataset handler for isolated vector storage."""

    @classmethod
    async def create_dataset(cls, dataset_id: str, user: Any) -> dict[str, str]:
        """Create isolated LanceDB configuration for a dataset."""
        user_db_dir = SYSTEM_STORAGE / "databases" / str(user.id)
        user_db_dir.mkdir(parents=True, exist_ok=True)

        db_path = user_db_dir / VECTOR_DB_NAME

        return {
            "vector_dataset_database_handler": "custom_lancedb_handler",
            "vector_database_name": VECTOR_DB_NAME,
            "vector_database_url": str(db_path),
            "vector_database_provider": "lancedb",
        }


class CustomKuzuHandler(DatasetStoreHandlerInterface):
    """Custom Kuzu dataset handler for isolated graph storage."""

    @classmethod
    async def create_dataset(cls, dataset_id: str, user: Any) -> dict[str, str]:
        """Create isolated Kuzu configuration for a dataset."""
        user_db_dir = SYSTEM_STORAGE / "databases" / str(user.id)
        user_db_dir.mkdir(parents=True, exist_ok=True)

        db_path = user_db_dir / GRAPH_DB_NAME

        return {
            "graph_dataset_database_handler": "custom_kuzu_handler",
            "graph_database_name": GRAPH_DB_NAME,
            "graph_database_url": str(db_path),
            "graph_database_provider": "kuzu",
        }


# ============================================================================
# Test Execution
# ============================================================================


async def execute_handler_test() -> None:
    """Test custom dataset database handler functionality."""

    # Configure storage paths
    m_flow.config.data_root_directory(str(DATA_STORAGE.resolve()))
    m_flow.config.system_root_directory(str(SYSTEM_STORAGE.resolve()))

    # Register custom handlers
    use_dataset_database_handler("custom_lancedb_handler", CustomLanceDBHandler, "lancedb")
    use_dataset_database_handler("custom_kuzu_handler", CustomKuzuHandler, "kuzu")

    # Reset system state
    print("Clearing M-flow state...")
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)
    print("State cleared.\n")

    # Add sample content
    sample_text = """
    Natural language processing (NLP) is an interdisciplinary
    subfield of computer science and information retrieval.
    """

    print("Adding sample text:")
    print(sample_text.strip())

    await m_flow.add(sample_text)
    print("Content added.\n")

    # Process content
    await m_flow.memorize()
    print("Content processed.\n")

    # Test search
    query = "Tell me about NLP"
    print(f"Executing search: '{query}'")

    results = await m_flow.search(
        query_type=RecallMode.TRIPLET_COMPLETION,
        query_text=query,
    )

    print("Search results:")
    for entry in results:
        print(f"  - {entry}")

    # Verify custom databases were created
    user = await get_seed_user()
    user_db_path = SYSTEM_STORAGE / "databases" / str(user.id)

    graph_db_exists = (user_db_path / GRAPH_DB_NAME).exists()
    vector_db_exists = (user_db_path / VECTOR_DB_NAME).exists()

    assert graph_db_exists, f"Graph database not found at {user_db_path / GRAPH_DB_NAME}"
    assert vector_db_exists, f"Vector database not found at {user_db_path / VECTOR_DB_NAME}"

    print("\nCustom database handler test passed!")


# ============================================================================
# Main Entry Point
# ============================================================================


if __name__ == "__main__":
    setup_logging(log_level=ERROR)

    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)

    try:
        event_loop.run_until_complete(execute_handler_test())
    finally:
        event_loop.run_until_complete(event_loop.shutdown_asyncgens())
