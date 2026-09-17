"""
LLM速率限制器单元测试
"""

from __future__ import annotations

import pytest
from unittest.mock import patch

from m_flow.llm.backends.litellm_instructor.llm.rate_limiter import (
    llm_rate_limiter,
    rate_limit_async,
    rate_limit_sync,
)

_LIMITER_PATH = "m_flow.llm.backends.litellm_instructor.llm.rate_limiter.llm_rate_limiter"
_CONFIG_PATH = "m_flow.llm.backends.litellm_instructor.llm.rate_limiter.get_llm_config"


@pytest.fixture(autouse=True)
def clean_singleton():
    """每个测试前重置单例"""
    llm_rate_limiter._instance = None
    return


class TestRateLimiterInit:
    """初始化测试"""

    def test_enabled_with_config(self):
        with patch(_CONFIG_PATH) as cfg:
            cfg.return_value.llm_rate_limit_enabled = True
            cfg.return_value.llm_rate_limit_requests = 10
            cfg.return_value.llm_rate_limit_interval = 60

            lim = llm_rate_limiter()
            assert lim._enabled is True
            assert lim._requests == 10
            assert lim._interval == 60

    def test_disabled_default(self):
        with patch(_CONFIG_PATH) as cfg:
            cfg.return_value.llm_rate_limit_enabled = False

            lim = llm_rate_limiter()
            assert lim._enabled is False
            # 禁用时 check_and_hit 始终返回 True
            assert lim.check_and_hit() is True


class TestRateLimiterSingleton:
    """单例模式测试"""

    def test_same_instance(self):
        with patch(_CONFIG_PATH) as cfg:
            cfg.return_value.llm_rate_limit_enabled = True
            cfg.return_value.llm_rate_limit_requests = 5
            cfg.return_value.llm_rate_limit_interval = 60

            lim1 = llm_rate_limiter()
            lim2 = llm_rate_limiter()
            assert lim1 is lim2


class TestDecorators:
    """装饰器测试"""

    def test_sync_decorator(self):
        """测试同步装饰器"""
        from m_flow.llm.backends.litellm_instructor.llm.rate_limiter import (
            LLMRateLimiter,
        )

        with patch.object(LLMRateLimiter, "wait_sync", return_value=0) as mock_wait:

            @rate_limit_sync
            def fn():
                return "ok"

            assert fn() == "ok"
            mock_wait.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_decorator(self):
        """测试异步装饰器"""
        from unittest.mock import AsyncMock
        from m_flow.llm.backends.litellm_instructor.llm.rate_limiter import (
            LLMRateLimiter,
        )

        with patch.object(LLMRateLimiter, "wait_async", new_callable=AsyncMock, return_value=0) as mock_wait:

            @rate_limit_async
            async def fn():
                return "ok"

            assert await fn() == "ok"
            mock_wait.assert_awaited_once()


class TestRateLimitingBehavior:
    """限流行为测试"""

    def test_small_limit(self):
        """测试小窗口限流"""
        with patch(_CONFIG_PATH) as cfg:
            cfg.return_value.llm_rate_limit_enabled = True
            cfg.return_value.llm_rate_limit_requests = 3
            cfg.return_value.llm_rate_limit_interval = 60

            llm_rate_limiter._instance = None
            lim = llm_rate_limiter()

            # 前3个请求应通过
            assert lim.check_and_hit() is True
            assert lim.check_and_hit() is True
            assert lim.check_and_hit() is True
            # 第4个应被限制
            assert lim.check_and_hit() is False

    def test_default_60_per_minute(self):
        """测试每分钟60次默认限制"""
        with patch(_CONFIG_PATH) as cfg:
            cfg.return_value.llm_rate_limit_enabled = True
            cfg.return_value.llm_rate_limit_requests = 60
            cfg.return_value.llm_rate_limit_interval = 60

            llm_rate_limiter._instance = None
            lim = llm_rate_limiter()

            ok_count = 0
            fail_count = 0
            first_fail = -1

            for i in range(70):
                if lim.check_and_hit():
                    ok_count += 1
                else:
                    if first_fail < 0:
                        first_fail = i
                    fail_count += 1

            print(f"成功: {ok_count}, 失败: {fail_count}, 首次失败: {first_fail}")

            assert 58 <= ok_count <= 62
            assert fail_count > 0
            assert 58 <= first_fail <= 62
