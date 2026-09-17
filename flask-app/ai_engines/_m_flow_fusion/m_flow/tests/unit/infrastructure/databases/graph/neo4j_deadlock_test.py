"""
Neo4j死锁重试测试
"""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest
from neo4j.exceptions import Neo4jError

from m_flow.adapters.graph.neo4j_driver.deadlock_retry import deadlock_retry


def _future(val):
    """创建已完成的Future"""
    f = asyncio.Future()
    f.set_result(val)
    return f


class TestDeadlockRetry:
    """死锁重试装饰器测试"""

    @pytest.mark.asyncio
    async def test_exceeds_max_retries(self):
        """超过最大重试次数抛出异常"""
        mock_fn = MagicMock(
            side_effect=[
                Neo4jError("DeadlockDetected"),
                Neo4jError("DeadlockDetected"),
                _future(True),
            ]
        )

        wrapped = deadlock_retry(max_retries=1)(mock_fn)
        with pytest.raises(Neo4jError):
            await wrapped(self=None)

    @pytest.mark.asyncio
    async def test_success_after_retry(self):
        """一次重试后成功"""
        mock_fn = MagicMock(
            side_effect=[
                Neo4jError("DeadlockDetected"),
                _future(True),
            ]
        )

        wrapped = deadlock_retry(max_retries=2)(mock_fn)
        result = await wrapped(self=None)
        assert result is True

    @pytest.mark.asyncio
    async def test_exhaustive_retries(self):
        """用尽所有重试后成功"""
        mock_fn = MagicMock(
            side_effect=[
                Neo4jError("DeadlockDetected"),
                Neo4jError("DeadlockDetected"),
                _future(True),
            ]
        )

        wrapped = deadlock_retry(max_retries=2)(mock_fn)
        result = await wrapped(self=None)
        assert result is True


if __name__ == "__main__":

    async def _run():
        t = TestDeadlockRetry()
        await t.test_success_after_retry()
        await t.test_exhaustive_retries()
        # test_exceeds_max_retries会抛异常，单独测试

    asyncio.run(_run())
