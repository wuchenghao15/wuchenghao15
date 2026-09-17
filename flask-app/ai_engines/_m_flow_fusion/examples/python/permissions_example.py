"""M-Flow — access-control and multi-tenant permissions demo.

Walks through creating users, datasets, tenants, and roles, then shows how
permission grants control who can read/write each dataset.
"""

import asyncio
import os
import pathlib
from pprint import pprint

import m_flow
from m_flow.auth.exceptions import PermissionDeniedError
from m_flow.auth.methods import create_user, get_user
from m_flow.auth.permissions.methods import authorized_give_permission_on_datasets
from m_flow.auth.roles.methods import add_user_to_role, create_role
from m_flow.auth.tenants.methods import add_user_to_tenant, create_tenant, select_tenant
from m_flow.core.domain.operations.setup import setup
from m_flow.search.types import RecallMode
from m_flow.shared.logging_utils import get_logger, setup_logging, CRITICAL

log = get_logger()

QUANTUM_TEXT = (
    "A quantum computer is a computer that takes advantage of quantum mechanical phenomena. "
    "At small scales, physical matter exhibits properties of both particles and waves, and "
    "quantum computing leverages this behavior, specifically quantum superposition and "
    "entanglement, using specialized hardware that supports the preparation and manipulation "
    "of quantum states."
)


def _first_dataset_id(memorize_output: dict):
    """Return the first dataset_id key from a memorize result dict."""
    return next(iter(memorize_output))


async def run_permissions_demo():
    """End-to-end demonstration of M-Flow's access-control primitives."""

    # ── 1. Enable access control ────────────────────────────────────
    os.environ["ENABLE_BACKEND_ACCESS_CONTROL"] = "True"

    print("Resetting M-Flow state …")
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)
    print("Done.\n")

    await setup()

    # ── 2. Create users and ingest data ─────────────────────────────
    ai_pdf = os.path.join(
        pathlib.Path(__file__).parent,
        "../data/artificial_intelligence.pdf",
    )

    print("Creating alice@example.com (user_1)")
    alice = await create_user("user_1@example.com", "example")
    await m_flow.add([ai_pdf], dataset_name="AI", user=alice)

    print("\nCreating bob@example.com (user_2)")
    bob = await create_user("user_2@example.com", "example")
    await m_flow.add([QUANTUM_TEXT], dataset_name="QUANTUM", user=bob)

    # ── 3. Build knowledge graphs for each dataset ──────────────────
    print("\nBuilding KG for user_1 (AI) and user_2 (QUANTUM)")
    ai_result = await m_flow.memorize(["AI"], user=alice)
    quantum_result = await m_flow.memorize(["QUANTUM"], user=bob)

    ai_ds_id = _first_dataset_id(ai_result)
    quantum_ds_id = _first_dataset_id(quantum_result)

    # ── 4. Verify owner-only access ─────────────────────────────────
    owner_hits = await m_flow.search(
        query_type=RecallMode.TRIPLET_COMPLETION,
        query_text="What is in the document?",
        user=alice,
        datasets=[ai_ds_id],
    )
    print("\nuser_1 reading own AI dataset:")
    for h in owner_hits:
        pprint(h)

    print("\nuser_1 attempting to read user_2's QUANTUM dataset:")
    try:
        await m_flow.search(
            query_type=RecallMode.TRIPLET_COMPLETION,
            query_text="What is in the document?",
            user=alice,
            datasets=[quantum_ds_id],
        )
    except PermissionDeniedError:
        print(f"  Denied — {alice} has no read access to QUANTUM")

    print("\nuser_1 attempting to write into user_2's QUANTUM dataset:")
    try:
        await m_flow.add([ai_pdf], dataset_id=quantum_ds_id, user=alice)
    except PermissionDeniedError:
        print(f"  Denied — {alice} has no write access to QUANTUM")

    # ── 5. Grant cross-user read permission ─────────────────────────
    print("\nuser_2 grants user_1 read access to QUANTUM")
    await authorized_give_permission_on_datasets(
        alice.id,
        [quantum_ds_id],
        "read",
        bob.id,
    )

    cross_hits = await m_flow.search(
        query_type=RecallMode.TRIPLET_COMPLETION,
        query_text="What is in the document?",
        user=alice,
        dataset_ids=[quantum_ds_id],
    )
    print("\nuser_1 reading QUANTUM after grant:")
    for h in cross_hits:
        pprint(h)

    # ── 6. Multi-tenant / role-based access ─────────────────────────
    print("\nuser_2 creates MflowLab tenant")
    tenant = await create_tenant("MflowLab", bob.id)

    print("user_2 selects MflowLab as active tenant")
    await select_tenant(user_id=bob.id, tenant_id=tenant)

    print("\nuser_2 creates Researcher role")
    researcher_role = await create_role(role_name="Researcher", owner_id=bob.id)

    print("\nCreating charlie@example.com (user_3)")
    charlie = await create_user("user_3@example.com", "example")

    print("\nuser_2 adds user_3 to MflowLab")
    await add_user_to_tenant(user_id=charlie.id, tenant_id=tenant, owner_id=bob.id)

    print("user_2 assigns user_3 the Researcher role")
    await add_user_to_role(user_id=charlie.id, role_id=researcher_role, owner_id=bob.id)

    print("\nuser_3 selects MflowLab as active tenant")
    await select_tenant(user_id=charlie.id, tenant_id=tenant)

    # The personal QUANTUM dataset is not inside MflowLab, so role grants fail:
    print("\nAttempting role-level grant on personal QUANTUM dataset:")
    try:
        await authorized_give_permission_on_datasets(
            researcher_role,
            [quantum_ds_id],
            "read",
            bob.id,
        )
    except PermissionDeniedError:
        print("  Denied — QUANTUM is not part of MflowLab")

    # Re-create the dataset inside the tenant context
    print("\nRecreating QUANTUM as QUANTUM_MFLOW_LAB inside MflowLab tenant so the role grant can succeed")
    bob = await get_user(bob.id)
    await m_flow.add([QUANTUM_TEXT], dataset_name="QUANTUM_MFLOW_LAB", user=bob)
    tenant_q_result = await m_flow.memorize(["QUANTUM_MFLOW_LAB"], user=bob)
    tenant_q_ds_id = _first_dataset_id(tenant_q_result)

    print("\nuser_2 grants Researcher role read access on tenant QUANTUM dataset")
    await authorized_give_permission_on_datasets(
        researcher_role,
        [tenant_q_ds_id],
        "read",
        bob.id,
    )

    role_hits = await m_flow.search(
        query_type=RecallMode.TRIPLET_COMPLETION,
        query_text="What is in the document?",
        user=charlie,
        dataset_ids=[tenant_q_ds_id],
    )
    print("\nuser_3 (Researcher) reading QUANTUM_MFLOW_LAB:")
    for h in role_hits:
        pprint(h)


if __name__ == "__main__":
    setup_logging(log_level=CRITICAL)
    asyncio.run(run_permissions_demo())
