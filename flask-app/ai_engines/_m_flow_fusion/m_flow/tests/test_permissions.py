"""
Access Control and Permissions Tests for M-flow.

Integration tests for multi-user permission enforcement including:
- Dataset isolation between users
- Write/read/delete permission grants
- Permission denied exceptions
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

import m_flow
from m_flow.auth.exceptions import PermissionDeniedError
from m_flow.auth.methods import create_user, get_seed_user
from m_flow.auth.permissions.methods import authorized_give_permission_on_datasets
from m_flow.data.methods import fetch_dataset_items
from m_flow.search.types import RecallMode
from m_flow.shared.logging_utils import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger()

# ============================================================================
# Test Configuration
# ============================================================================

TESTS_DIR = Path(__file__).parent
DATA_STORAGE = TESTS_DIR / ".data_storage" / "test_permissions"
SYSTEM_STORAGE = TESTS_DIR / ".mflow/system" / "test_permissions"

NLP_FILE = TESTS_DIR / "test_data" / "Natural_language_processing.txt"
QUANTUM_FILE = TESTS_DIR / "test_data" / "Quantum_computers.txt"

NLP_DATASET = "NLP"
QUANTUM_DATASET = "QUANTUM"

TEST_USER_EMAIL = "user@example.com"
TEST_USER_PASSWORD = "example"

SEARCH_QUERY = "What is in the document?"


# ============================================================================
# Helper Functions
# ============================================================================


def enable_access_control() -> None:
    """Enable backend access control feature."""
    os.environ["ENABLE_BACKEND_ACCESS_CONTROL"] = "True"


def configure_storage() -> None:
    """Set up test storage directories."""
    m_flow.config.data_root_directory(str(DATA_STORAGE.resolve()))
    m_flow.config.system_root_directory(str(SYSTEM_STORAGE.resolve()))


async def reset_state() -> None:
    """Clear all M-flow data and system state."""
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)


def extract_dataset_id(memorize_result: dict) -> str | None:
    """Extract first dataset ID from memorize result."""
    for dataset_id in memorize_result:
        return dataset_id
    return None


async def search_as_user(user: Any, dataset_ids: list | None = None) -> list:
    """Execute search as specified user."""
    kwargs = {
        "query_type": RecallMode.TRIPLET_COMPLETION,
        "query_text": SEARCH_QUERY,
        "user": user,
    }
    if dataset_ids:
        kwargs["dataset_ids"] = dataset_ids

    return await m_flow.search(**kwargs)


def assert_permission_denied(raised: bool, operation: str) -> None:
    """Verify permission denied was raised."""
    assert raised, f"PermissionDeniedError expected for {operation} but not raised"


# ============================================================================
# Test Execution
# ============================================================================


async def run_permissions_test() -> None:
    """Execute comprehensive permissions test suite."""
    enable_access_control()
    configure_storage()
    await reset_state()

    # --- Setup: Create users and datasets ---
    default_user = await get_seed_user()
    test_user = await create_user(TEST_USER_EMAIL, TEST_USER_PASSWORD)

    # Add datasets for each user
    await m_flow.add([str(NLP_FILE)], dataset_name=NLP_DATASET)
    await m_flow.add([str(QUANTUM_FILE)], dataset_name=QUANTUM_DATASET, user=test_user)

    # Process datasets
    nlp_result = await m_flow.memorize([NLP_DATASET], user=default_user)
    quantum_result = await m_flow.memorize([QUANTUM_DATASET], user=test_user)

    nlp_dataset_id = extract_dataset_id(nlp_result)
    quantum_dataset_id = extract_dataset_id(quantum_result)

    logger.info(f"NLP dataset ID: {nlp_dataset_id}")
    logger.info(f"Quantum dataset ID: {quantum_dataset_id}")

    # --- Test: User isolation ---
    # Default user sees only NLP
    results = await search_as_user(default_user)
    assert len(results) == 1, f"Expected 1 result, got {len(results)}"
    assert results[0]["dataset_name"] == NLP_DATASET
    logger.info("✓ Default user sees only NLP dataset")

    # Test user sees only QUANTUM
    results = await search_as_user(test_user)
    assert len(results) == 1, f"Expected 1 result, got {len(results)}"
    assert results[0]["dataset_name"] == QUANTUM_DATASET
    logger.info("✓ Test user sees only QUANTUM dataset")

    # --- Test: Write permission denied ---
    write_denied = False
    try:
        await m_flow.add(
            [str(NLP_FILE)],
            dataset_name=QUANTUM_DATASET,
            dataset_id=quantum_dataset_id,
            user=default_user,
        )
    except PermissionDeniedError:
        write_denied = True
    assert_permission_denied(write_denied, "add to other user's dataset")
    logger.info("✓ Write to foreign dataset denied")

    # --- Test: Memorize permission denied ---
    memorize_denied = False
    try:
        await m_flow.memorize(datasets=[quantum_dataset_id], user=default_user)
    except PermissionDeniedError:
        memorize_denied = True
    assert_permission_denied(memorize_denied, "memorize other user's dataset")
    logger.info("✓ Memorize foreign dataset denied")

    # --- Test: Grant permission denied (no share permission) ---
    grant_denied = False
    try:
        await authorized_give_permission_on_datasets(
            default_user.id,
            [quantum_dataset_id],
            "write",
            default_user.id,
        )
    except PermissionDeniedError:
        grant_denied = True
    assert_permission_denied(grant_denied, "grant permission without share rights")
    logger.info("✓ Permission grant without share rights denied")

    # --- Test: Grant write permission ---
    await authorized_give_permission_on_datasets(
        default_user.id,
        [quantum_dataset_id],
        "write",
        test_user.id,
    )

    # Now default user can write
    await m_flow.add(
        [str(NLP_FILE)],
        dataset_name=QUANTUM_DATASET,
        dataset_id=quantum_dataset_id,
        user=default_user,
    )
    await m_flow.memorize(datasets=[quantum_dataset_id], user=default_user)
    logger.info("✓ Write access granted successfully")

    # --- Test: Grant read permission ---
    await authorized_give_permission_on_datasets(
        default_user.id,
        [quantum_dataset_id],
        "read",
        test_user.id,
    )

    # Default user can now search quantum dataset
    results = await search_as_user(default_user, dataset_ids=[quantum_dataset_id])
    assert len(results) == 1
    assert results[0]["dataset_name"] == QUANTUM_DATASET
    logger.info("✓ Read access granted successfully")

    # Default user sees both datasets
    results = await search_as_user(default_user)
    assert len(results) == 2
    logger.info("✓ User sees both owned and shared datasets")

    # --- Test: Delete permission denied ---
    dataset_data = await fetch_dataset_items(quantum_dataset_id)
    data_id = dataset_data[0].id

    delete_denied = False
    try:
        await m_flow.delete(
            data_id=data_id,
            dataset_id=quantum_dataset_id,
            user=default_user,
        )
    except PermissionDeniedError:
        delete_denied = True
    assert_permission_denied(delete_denied, "delete without permission")
    logger.info("✓ Delete without permission denied")

    # --- Test: Owner can delete ---
    await m_flow.delete(
        data_id=data_id,
        dataset_id=quantum_dataset_id,
        user=test_user,
    )
    logger.info("✓ Owner can delete data")

    # --- Test: Grant delete permission ---
    await authorized_give_permission_on_datasets(
        default_user.id,
        [quantum_dataset_id],
        "delete",
        test_user.id,
    )

    dataset_data = await fetch_dataset_items(quantum_dataset_id)
    remaining_data_id = dataset_data[0].id

    await m_flow.delete(
        data_id=remaining_data_id,
        dataset_id=quantum_dataset_id,
        user=default_user,
    )
    logger.info("✓ Delete with granted permission succeeded")

    print("\n=== All Permission Tests Passed ===")


# ============================================================================
# Main Entry Point
# ============================================================================


if __name__ == "__main__":
    asyncio.run(run_permissions_test())
