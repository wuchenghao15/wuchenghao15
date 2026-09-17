"""Verify that a shared *context* value is threaded through every task
in the pipeline and correctly participates in the computation.

Scenario
--------
Three-stage numeric pipeline where context acts as an additive offset,
a no-op passthrough, and finally an exponentiation base.

    stage 1:  val + ctx         -> 5 + 7 = 12
    stage 2:  val * 2           -> 12 * 2 = 24    (ctx ignored)
    stage 3:  val ** ctx        -> 24 ** 7 = 4_586_471_424
"""

from __future__ import annotations

import asyncio
from typing import Any

import m_flow
from m_flow.adapters.relational import create_db_and_tables
from m_flow.auth.methods import get_seed_user
from m_flow.pipeline.operations.execute_pipeline_tasks import execute_pipeline_tasks
from m_flow.pipeline.tasks import Stage

SEED_VALUE = 5
CTX_PARAM = 7
EXPECTED_OUTPUT = 4_586_471_424  # (5+7)*2 = 24; 24**7 = 4_586_471_424


def _apply_offset(val: Any, context: Any) -> int:
    """Add *context* to *val*."""
    return int(val) + int(context)


def _amplify(val: Any) -> int:
    """Double the incoming value (context-agnostic)."""
    return int(val) * 2


def _exponentiate_by_ctx(val: Any, context: Any) -> int:
    """Raise *val* to the power of *context*."""
    return int(val) ** int(context)


async def _run_context_pipeline() -> None:
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)
    await create_db_and_tables()

    usr = await get_seed_user()

    chain = [
        Stage(_apply_offset),
        Stage(_amplify),
        Stage(_exponentiate_by_ctx),
    ]

    stream = execute_pipeline_tasks(
        chain,
        data=SEED_VALUE,
        user=usr,
        context=CTX_PARAM,
    )

    async for result in stream:
        assert result == EXPECTED_OUTPUT, f"Context pipeline produced {result}, expected {EXPECTED_OUTPUT}"


def test_context_is_threaded_through_pipeline() -> None:
    asyncio.run(_run_context_pipeline())


if __name__ == "__main__":
    test_context_is_threaded_through_pipeline()
