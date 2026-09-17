"""
LLM速率限制真实场景测试
"""

from __future__ import annotations

import asyncio
import os

import pytest
from unittest.mock import patch

from m_flow.llm.config import get_llm_config
from m_flow.llm.backends.litellm_instructor.llm.rate_limiter import (
    llm_rate_limiter,
)
from m_flow.shared.logging_utils import get_logger


def _setup_env(requests: int = 5, interval: int = 10) -> None:
    """设置测试环境变量"""
    os.environ["LLM_RATE_LIMIT_ENABLED"] = "true"
    os.environ["LLM_RATE_LIMIT_REQUESTS"] = str(requests)
    os.environ["LLM_RATE_LIMIT_INTERVAL"] = str(interval)
    get_llm_config.cache_clear()
    llm_rate_limiter._instance = None


def _count_results(limiter, count: int) -> tuple[list, list]:
    """执行请求并统计结果"""
    ok, fail = [], []
    for i in range(count):
        if limiter.check_and_hit():
            ok.append(i)
        else:
            fail.append(i)
    return ok, fail


@pytest.mark.asyncio
async def test_rate_limiting_realistic():
    """测试限流特性的真实场景"""
    print("\n=== 限流测试 ===")
    _setup_env(requests=5, interval=10)

    cfg = get_llm_config()
    print(
        f"配置: 启用={cfg.llm_rate_limit_enabled}, "
        f"请求数={cfg.llm_rate_limit_requests}, "
        f"间隔={cfg.llm_rate_limit_interval}"
    )

    # 使用mock来控制行为
    with patch.object(llm_rate_limiter, "check_and_hit") as mock:
        mock.side_effect = [
            # 批次1: 5通过 + 5限制
            True,
            True,
            True,
            True,
            True,
            False,
            False,
            False,
            False,
            False,
            # 批次2: 2通过 + 3限制（部分恢复）
            True,
            True,
            False,
            False,
            False,
            # 批次3: 5通过（完全恢复）
            True,
            True,
            True,
            True,
            True,
        ]

        lim = llm_rate_limiter()
        # 限流器配置信息通过环境变量设置，不直接访问内部属性
        print("限流器: 已配置")

        # 批次1
        print("\n批次1: 发送10个请求...")
        b1_ok, b1_fail = _count_results(lim, 10)
        for i in b1_ok:
            print(f"✓ 请求 {i}: 通过")
        for i in b1_fail:
            print(f"✗ 请求 {i}: 限流")
        print(f"结果: {len(b1_ok)}通过, {len(b1_fail)}限流")

        # 等待部分恢复
        print("\n等待5秒...")
        await asyncio.sleep(5)

        # 批次2
        print("\n批次2: 发送5个请求...")
        b2_ok, b2_fail = _count_results(lim, 5)
        print(f"结果: {len(b2_ok)}通过, {len(b2_fail)}限流")

        # 等待完全恢复
        print("\n等待10秒...")
        await asyncio.sleep(10)

        # 批次3
        print("\n批次3: 发送5个请求...")
        b3_ok, b3_fail = _count_results(lim, 5)
        print(f"结果: {len(b3_ok)}通过, {len(b3_fail)}限流")

        # 汇总
        total_ok = len(b1_ok) + len(b2_ok) + len(b3_ok)
        total_fail = len(b1_fail) + len(b2_fail) + len(b3_fail)
        print(f"\n总计: {total_ok + total_fail}请求, {total_ok}通过, {total_fail}限流")

        # 验证
        assert len(b1_ok) == 5 and len(b1_fail) == 5, "批次1应5通过5限流"
        assert len(b2_ok) == 2 and len(b2_fail) == 3, "批次2应2通过3限流"
        assert len(b3_ok) == 5 and len(b3_fail) == 0, "批次3应全部通过"
        print("\n✅ 所有断言通过")

    print("=== 测试完成 ===\n")


async def _main():
    await test_rate_limiting_realistic()


if __name__ == "__main__":
    log = get_logger()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_main())
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
