"""Pipeline task execution with generators and batching."""

from __future__ import annotations

import asyncio

import m_flow
from m_flow.adapters.relational import create_db_and_tables
from m_flow.auth.methods import get_seed_user
from m_flow.pipeline.operations.execute_pipeline_tasks import execute_pipeline_tasks
from m_flow.pipeline.tasks import Stage


def _produce_sequence(count: int):
    for position in range(count):
        yield position + 1


async def _increment_all(items):
    for item in items:
        yield item + 1


async def _double_first(items):
    yield items[0] * 2


async def _increment_single(items):
    yield items[0] + 1


async def _execute():
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)

    await create_db_and_tables()
    current_user = await get_seed_user()

    pipeline_output = execute_pipeline_tasks(
        [
            Stage(_produce_sequence),
            Stage(_increment_all, task_config={"batch_size": 5}),
            Stage(_double_first, task_config={"batch_size": 1}),
            Stage(_increment_single),
        ],
        data=10,
        user=current_user,
    )

    anticipated = [5, 7, 9, 11, 13, 15, 17, 19, 21, 23]
    position = 0
    async for output in pipeline_output:
        assert output[0] == anticipated[position], (
            f"Mismatch at index {position}: got {output[0]}, want {anticipated[position]}"
        )
        position += 1


def test_run_tasks():
    asyncio.run(_execute())


if __name__ == "__main__":
    test_run_tasks()
