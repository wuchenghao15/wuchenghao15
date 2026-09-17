"""M-Flow 流水线缓存机制验证

验证 enable_cache 选项:
- 关闭时无条件重新运行
- 开启时跳过已完成的流水线
- 手动重置状态后可再次触发执行
"""

from __future__ import annotations

import pytest

import m_flow
from m_flow.adapters.relational import create_db_and_tables
from m_flow.auth.methods import get_seed_user
from m_flow.pipeline import execute_workflow, WorkflowConfig
from m_flow.pipeline.layers.reset_dataset_pipeline_run_status import (
    reset_dataset_pipeline_run_status,
)
from m_flow.pipeline.tasks import Stage


class InvocationTracker:
    """记录任务被调用的次数"""

    def __init__(self):
        self.invocations = 0


async def _tracked_task(data, tracker: InvocationTracker):
    """每次执行时递增追踪器计数"""
    tracker.invocations += 1
    return tracker


async def _clean_environment():
    """清理数据与元数据，重建数据库表"""
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)
    await create_db_and_tables()


class TestCacheDisabled:
    """当缓存关闭时，流水线应无条件重复执行"""

    @pytest.mark.asyncio
    async def test_rerun_without_cache(self):
        """关闭缓存后，同一流水线应被再次执行"""
        await _clean_environment()

        tracker = InvocationTracker()
        current_user = await get_seed_user()
        job_list = [Stage(_tracked_task, tracker=tracker)]

        async for _ in execute_workflow(
            tasks=job_list,
            datasets="no_cache_ds",
            data=["payload"],
            user=current_user,
            name="nocache_pipe",
            config=WorkflowConfig(cache=False),
        ):
            pass
        after_first = tracker.invocations
        assert after_first >= 1

        async for _ in execute_workflow(
            tasks=job_list,
            datasets="no_cache_ds",
            data=["payload"],
            user=current_user,
            name="nocache_pipe",
            config=WorkflowConfig(cache=False),
        ):
            pass
        after_second = tracker.invocations
        assert after_second > after_first, f"关闭缓存后应重跑: 第一次 {after_first}, 第二次 {after_second}"


class TestCacheWithStatusReset:
    """缓存开启时，重置状态应允许再次执行"""

    @pytest.mark.asyncio
    async def test_reset_then_rerun(self):
        """重置流水线状态后，即使开启缓存也应再次执行"""
        await _clean_environment()

        tracker = InvocationTracker()
        current_user = await get_seed_user()
        ds = "status_reset_ds"
        pipe = "status_reset_pipe"
        job_list = [Stage(_tracked_task, tracker=tracker)]

        captured = []
        async for r in execute_workflow(
            tasks=job_list,
            datasets=ds,
            user=current_user,
            data=["item"],
            name=pipe,
            config=WorkflowConfig(cache=True),
        ):
            captured.append(r)
        after_first = tracker.invocations
        assert after_first >= 1

        async for _ in execute_workflow(
            tasks=job_list,
            datasets=ds,
            user=current_user,
            data=["item"],
            name=pipe,
            config=WorkflowConfig(cache=True),
        ):
            pass
        after_cached = tracker.invocations
        assert after_cached == after_first, "开启缓存后应跳过"

        await reset_dataset_pipeline_run_status(captured[0].dataset_id, current_user, pipeline_names=[pipe])

        async for _ in execute_workflow(
            tasks=job_list,
            datasets=ds,
            user=current_user,
            data=["item"],
            name=pipe,
            config=WorkflowConfig(cache=True),
        ):
            pass
        after_reset = tracker.invocations
        assert after_reset > after_cached, f"重置后应执行: 缓存后 {after_cached}, 重置后 {after_reset}"
