"""
Content Deduplication Tests for M-flow.

Tests verify that M-flow correctly identifies and deduplicates identical content
across different file types (text, images, audio) and input methods (files, strings).
"""

from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

import m_flow
from m_flow.adapters.relational import get_db_adapter
from m_flow.adapters.relational.create_relational_engine import create_relational_engine
from m_flow.shared.logging_utils import get_logger

if TYPE_CHECKING:
    from typing import Any

logger = get_logger()

# ============================================================================
# Test Constants
# ============================================================================

PRIMARY_DATASET = "test_deduplication"
SECONDARY_DATASET = "test_deduplication2"

# Test data directory relative to this file
TEST_DATA_DIR = Path(__file__).parent / "test_data"

# Text file pairs for deduplication testing
TEXT_FILE_ORIGINAL = TEST_DATA_DIR / "Natural_language_processing.txt"
TEXT_FILE_COPY = TEST_DATA_DIR / "Natural_language_processing_copy.txt"

# Image file pairs
IMAGE_FILE_ORIGINAL = TEST_DATA_DIR / "example.png"
IMAGE_FILE_COPY = TEST_DATA_DIR / "example_copy.png"

# Audio file pairs
AUDIO_FILE_ORIGINAL = TEST_DATA_DIR / "text_to_speech.mp3"
AUDIO_FILE_COPY = TEST_DATA_DIR / "text_to_speech_copy.mp3"

# Sample text content for deduplication testing
QUANTUM_COMPUTING_TEXT = """A quantum computer is a computer that takes advantage of quantum mechanical phenomena.
At small scales, physical matter exhibits properties of both particles and waves, and quantum computing leverages this behavior, specifically quantum superposition and entanglement, using specialized hardware that supports the preparation and manipulation of quantum states.
Classical physics cannot explain the operation of these quantum devices, and a scalable quantum computer could perform some calculations exponentially faster (with respect to input size scaling) than any modern "classical" computer. In particular, a large-scale quantum computer could break widely used encryption schemes and aid physicists in performing physical simulations; however, the current state of the technology is largely experimental and impractical, with several obstacles to useful applications. Moreover, scalable quantum computers do not hold promise for many practical tasks, and for many important tasks quantum speedups are proven impossible.
The basic unit of information in quantum computing is the qubit, similar to the bit in traditional digital electronics. Unlike a classical bit, a qubit can exist in a superposition of its two "basis" states. When measuring a qubit, the result is a probabilistic output of a classical bit, therefore making quantum computers nondeterministic in general. If a quantum computer manipulates the qubit in a particular way, wave interference effects can amplify the desired measurement results. The design of quantum algorithms involves creating procedures that allow a quantum computer to perform calculations efficiently and quickly.
Physically engineering high-quality qubits has proven challenging. If a physical qubit is not sufficiently isolated from its environment, it suffers from quantum decoherence, introducing noise into calculations. Paradoxically, perfectly isolating qubits is also undesirable because quantum computations typically need to initialize qubits, perform controlled qubit interactions, and measure the resulting quantum states. Each of those operations introduces errors and suffers from noise, and such inaccuracies accumulate.
In principle, a non-quantum (classical) computer can solve the same computational problems as a quantum computer, given enough time. Quantum advantage comes in the form of time complexity rather than computability, and quantum complexity theory shows that some quantum algorithms for carefully selected tasks require exponentially fewer computational steps than the best known non-quantum algorithms. Such tasks can in theory be solved on a large-scale quantum computer whereas classical computers would not finish computations in any reasonable amount of time. However, quantum speedup is not universal or even typical across computational tasks, since basic tasks such as sorting are proven to not allow any asymptotic quantum speedup. Claims of quantum supremacy have drawn significant attention to the discipline, but are demonstrated on contrived tasks, while near-term practical use cases remain limited.
"""


# ============================================================================
# Helper Functions
# ============================================================================


async def reset_system() -> None:
    """Clear all data and metadata from M-flow."""
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)


async def fetch_table_data(table_name: str) -> list[dict[str, Any]]:
    """Retrieve all records from the specified database table."""
    engine = get_db_adapter()
    return await engine.get_all_data_from_table(table_name)


def compute_content_hash(content: str) -> str:
    """Calculate MD5 hash of text content."""
    return hashlib.md5(content.encode("utf-8")).hexdigest()


def assert_single_data_entity(records: list, msg: str = "") -> None:
    """Verify exactly one data entity exists."""
    actual_count = len(records)
    assert actual_count == 1, f"Expected 1 data entity, found {actual_count}. {msg}"


def assert_dual_datasets(records: list) -> None:
    """Verify exactly two datasets exist."""
    actual_count = len(records)
    assert actual_count == 2, f"Expected 2 datasets, found {actual_count}"


def assert_datasets_share_data(relationships: list) -> None:
    """Verify both datasets reference the same data entity."""
    assert len(relationships) == 2, "Expected 2 dataset-data relationships"

    # Same data_id but different dataset_id
    data_ids = [r["data_id"] for r in relationships]
    dataset_ids = [r["dataset_id"] for r in relationships]

    assert data_ids[0] == data_ids[1], "Data should be shared between datasets"
    assert dataset_ids[0] != dataset_ids[1], "Datasets should be distinct"


# ============================================================================
# Core Deduplication Test
# ============================================================================


async def run_deduplication_test() -> None:
    """Execute comprehensive deduplication tests across file types."""

    # --- Text file deduplication ---
    await reset_system()

    await m_flow.add([str(TEXT_FILE_ORIGINAL)], PRIMARY_DATASET, incremental_loading=False)
    await m_flow.add([str(TEXT_FILE_COPY)], SECONDARY_DATASET, incremental_loading=False)

    data_records = await fetch_table_data("data")
    assert_single_data_entity(data_records, "Text file deduplication failed")
    assert data_records[0]["name"] == "Natural_language_processing_copy", "Expected copy file name to be stored"

    dataset_records = await fetch_table_data("datasets")
    assert_dual_datasets(dataset_records)
    assert dataset_records[0]["name"] == PRIMARY_DATASET
    assert dataset_records[1]["name"] == SECONDARY_DATASET

    relationships = await fetch_table_data("dataset_data")
    assert_datasets_share_data(relationships)

    # --- Text string deduplication ---
    await reset_system()

    await m_flow.add([QUANTUM_COMPUTING_TEXT], PRIMARY_DATASET)
    await m_flow.add([QUANTUM_COMPUTING_TEXT], SECONDARY_DATASET)

    data_records = await fetch_table_data("data")
    assert_single_data_entity(data_records, "Text string deduplication failed")

    expected_hash = compute_content_hash(QUANTUM_COMPUTING_TEXT)
    actual_name = data_records[0]["name"]
    assert expected_hash in actual_name, f"Content hash {expected_hash} not found in name {actual_name}"

    # --- Image file deduplication ---
    await reset_system()

    await m_flow.add([str(IMAGE_FILE_ORIGINAL)], PRIMARY_DATASET)
    await m_flow.add([str(IMAGE_FILE_COPY)], SECONDARY_DATASET)

    data_records = await fetch_table_data("data")
    assert_single_data_entity(data_records, "Image file deduplication failed")

    # --- Audio file deduplication ---
    await reset_system()

    await m_flow.add([str(AUDIO_FILE_ORIGINAL)], PRIMARY_DATASET)
    await m_flow.add([str(AUDIO_FILE_COPY)], SECONDARY_DATASET)

    data_records = await fetch_table_data("data")
    assert_single_data_entity(data_records, "Audio file deduplication failed")

    await reset_system()


# ============================================================================
# Database-specific Tests
# ============================================================================


@pytest.mark.asyncio
async def test_deduplication_postgres() -> None:
    """Test deduplication with PostgreSQL backend."""
    m_flow.config.set_vector_db_config(
        {
            "vector_db_url": "",
            "vector_db_key": "",
            "vector_db_provider": "pgvector",
        }
    )
    m_flow.config.set_relational_db_config(
        {
            "db_name": "m_flow_db",
            "db_host": "127.0.0.1",
            "db_port": "5432",
            "db_username": "m_flow",
            "db_password": "m_flow",
            "db_provider": "postgres",
        }
    )

    create_relational_engine.cache_clear()

    await run_deduplication_test()


@pytest.mark.asyncio
async def test_deduplication_sqlite() -> None:
    """Test deduplication with SQLite backend."""
    m_flow.config.set_vector_db_config(
        {
            "vector_db_url": "",
            "vector_db_key": "",
            "vector_db_provider": "lancedb",
        }
    )
    m_flow.config.set_relational_db_config(
        {
            "db_provider": "sqlite",
        }
    )

    await run_deduplication_test()


# ============================================================================
# Main Entry Point
# ============================================================================


async def execute_all_tests() -> None:
    """Run all deduplication tests with configured storage paths."""
    tests_dir = Path(__file__).parent

    data_storage = tests_dir / ".data_storage" / "test_deduplication"
    system_storage = tests_dir / ".mflow/system" / "test_deduplication"

    m_flow.config.data_root_directory(str(data_storage.resolve()))
    m_flow.config.system_root_directory(str(system_storage.resolve()))

    print("Running PostgreSQL deduplication test...")
    await test_deduplication_postgres()

    print("Running SQLite deduplication test...")
    await test_deduplication_sqlite()

    print("All deduplication tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(execute_all_tests())
