"""
Multi-Tenancy Integration Test
==============================
m_flow.tests.test_multi_tenancy

Validates multi-tenant access control features:
- Tenant-based data isolation
- Role-based permission management
- Cross-tenant permission restrictions
- Tenant switching and context validation
"""

import m_flow
import pytest

from m_flow.auth.exceptions import PermissionDeniedError
from m_flow.auth.tenants.methods import select_tenant
from m_flow.auth.methods import get_user, create_user
from m_flow.shared.logging_utils import get_logger, setup_logging, CRITICAL
from m_flow.search.types import RecallMode
from m_flow.auth.permissions.methods import authorized_give_permission_on_datasets
from m_flow.auth.roles.methods import add_user_to_role, create_role
from m_flow.auth.tenants.methods import create_tenant, add_user_to_tenant
from m_flow.core.domain.operations.setup import setup

_logger = get_logger()


def _get_first_dataset_id(memorize_output):
    """Extract the first dataset_id from memorize output dictionary."""
    for ds_id in memorize_output.keys():
        return ds_id
    return None


# Sample quantum computing content for testing
_QUANTUM_CONTENT = """A quantum computer is a computer that takes advantage of quantum mechanical phenomena.
At small scales, physical matter exhibits properties of both particles and waves, and quantum computing leverages
this behavior, specifically quantum superposition and entanglement, using specialized hardware that supports the
preparation and manipulation of quantum state"""


async def main():
    """
    Primary test execution for multi-tenancy features.

    Tests tenant isolation, role permissions, and context switching.
    """
    # Initialize clean environment
    _logger.info("Initializing test environment...")
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)
    _logger.info("Environment ready")

    # Setup user management infrastructure
    await setup()

    # =========================================
    # Create test users
    # =========================================
    _logger.info("Creating test users")
    primary_user = await create_user("user_1@example.com", "example")
    secondary_user = await create_user("user_2@example.com", "example")

    # Add dataset for primary user
    await m_flow.add([_QUANTUM_CONTENT], dataset_name="AI", user=primary_user)
    ai_result = await m_flow.memorize(["AI"], user=primary_user)
    ai_ds_id = _get_first_dataset_id(ai_result)

    # =========================================
    # Test: Owner can access own dataset
    # =========================================
    owner_search = await m_flow.search(
        query_type=RecallMode.TRIPLET_COMPLETION,
        query_text="What is in the document?",
        user=primary_user,
        datasets=[ai_ds_id],
    )
    assert len(owner_search) > 0, "Owner should access own dataset"

    # =========================================
    # Test: Non-owner cannot access without permission
    # =========================================
    with pytest.raises(PermissionDeniedError):
        await m_flow.search(
            query_type=RecallMode.TRIPLET_COMPLETION,
            query_text="What is in the document?",
            user=secondary_user,
            datasets=[ai_ds_id],
        )

    # =========================================
    # Setup: Create tenant and role structure
    # =========================================
    _logger.info("Creating tenant structure")
    tenant_1 = await create_tenant("MflowLab", primary_user.id)
    await select_tenant(user_id=primary_user.id, tenant_id=tenant_1)

    researcher_role = await create_role(role_name="Researcher", owner_id=primary_user.id)

    await add_user_to_tenant(
        user_id=secondary_user.id,
        tenant_id=tenant_1,
        owner_id=primary_user.id,
        set_as_active_tenant=True,
    )
    await add_user_to_role(
        user_id=secondary_user.id,
        role_id=researcher_role,
        owner_id=primary_user.id,
    )

    # =========================================
    # Test: Cannot share dataset from different tenant
    # =========================================
    # AI dataset was created in default tenant, not MflowLab
    with pytest.raises(PermissionDeniedError):
        await authorized_give_permission_on_datasets(
            researcher_role,
            [ai_ds_id],
            "read",
            primary_user.id,
        )

    # =========================================
    # Create dataset in current tenant and share
    # =========================================
    primary_user = await get_user(primary_user.id)  # Refresh with tenant context
    await m_flow.add([_QUANTUM_CONTENT], dataset_name="AI_MFLOW_LAB", user=primary_user)
    lab_result = await m_flow.memorize(["AI_MFLOW_LAB"], user=primary_user)
    lab_ds_id = _get_first_dataset_id(lab_result)

    await authorized_give_permission_on_datasets(
        researcher_role,
        [lab_ds_id],
        "read",
        primary_user.id,
    )

    # Test: Secondary user can now access shared dataset
    shared_search = await m_flow.search(
        query_type=RecallMode.TRIPLET_COMPLETION,
        query_text="What is in the document?",
        user=secondary_user,
        dataset_ids=[lab_ds_id],
    )
    assert len(shared_search) > 0, "Role member should access shared dataset"

    # =========================================
    # Test: Tenant switching isolation
    # =========================================
    _logger.info("Testing tenant switching")
    tenant_2 = await create_tenant("MflowLab2", primary_user.id)
    await select_tenant(user_id=primary_user.id, tenant_id=tenant_2)
    primary_user = await get_user(primary_user.id)

    await m_flow.add([_QUANTUM_CONTENT], dataset_name="AI_MFLOW_LAB", user=primary_user)
    await m_flow.memorize(["AI_MFLOW_LAB"], user=primary_user)

    tenant_2_search = await m_flow.search(
        query_type=RecallMode.TRIPLET_COMPLETION,
        query_text="What is in the document?",
        user=primary_user,
    )

    # Only datasets from current tenant should be visible
    assert len(tenant_2_search) == 1, f"Should see only current tenant's dataset: {tenant_2_search}"
    assert tenant_2_search[0]["dataset_name"] == "AI_MFLOW_LAB", f"Dataset name mismatch: {tenant_2_search[0]}"
    assert tenant_2_search[0]["dataset_tenant_id"] == str(primary_user.tenant_id), (
        f"Tenant ID mismatch: {tenant_2_search[0]}"
    )

    # =========================================
    # Test: Switch back to default tenant
    # =========================================
    await select_tenant(user_id=primary_user.id, tenant_id=None)
    primary_user = await get_user(primary_user.id)

    default_search = await m_flow.search(
        query_type=RecallMode.TRIPLET_COMPLETION,
        query_text="What is in the document?",
        user=primary_user,
    )

    assert len(default_search) == 1, f"Should see only default tenant's dataset: {default_search}"
    assert default_search[0]["dataset_name"] == "AI", f"Should see original AI dataset: {default_search[0]}"

    _logger.info("Multi-tenancy test completed successfully")


if __name__ == "__main__":
    log_handler = setup_logging(log_level=CRITICAL)
    import asyncio

    asyncio.run(main())
