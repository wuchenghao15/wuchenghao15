"""M-Flow 队列驱动任务链验证"""

from __future__ import annotations

import asyncio
from queue import Queue

import m_flow
from m_flow.adapters.relational import create_db_and_tables
from m_flow.auth.methods import get_seed_user
from m_flow.pipeline.operations.execute_pipeline_tasks import execute_pipeline_tasks
from m_flow.pipeline.tasks import Stage


class ShutdownableQueue(Queue):
    """支持关闭信号的队列"""

    def __init__(self):
        super().__init__()
        self.halted = False


async def _build_and_verify_chain(sq: ShutdownableQueue):
    """构建任务链并校验每个输出"""
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)

    async def drain_queue():
        while not sq.halted:
            if not sq.empty():
                yield sq.get()
            else:
                await asyncio.sleep(0.3)

    async def increment(values):
        yield values[0] + 1

    async def double(values):
        yield values[0] * 2

    await create_db_and_tables()
    active_user = await get_seed_user()

    pipeline_output = execute_pipeline_tasks(
        [Stage(drain_queue), Stage(increment), Stage(double)],
        data=None,
        user=active_user,
    )

    reference = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
    pos = 0
    async for item in pipeline_output:
        assert item[0] == reference[pos], f"索引 {pos}: 实际值 {item[0]} \u2260 预期值 {reference[pos]}"
        pos += 1


async def _orchestrate():
    """协调生产者与消费者流水线"""
    sq = ShutdownableQueue()

    async def feed():
        for n in range(10):
            sq.put(n)
            await asyncio.sleep(0.1)
        sq.halted = True

    await asyncio.gather(_build_and_verify_chain(sq), feed())


def test_run_tasks_from_queue():
    asyncio.run(_orchestrate())


if __name__ == "__main__":
    asyncio.run(_orchestrate())
