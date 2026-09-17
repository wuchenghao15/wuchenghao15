"""
嵌入向量速率限制真实场景测试
"""

from __future__ import annotations

import asyncio
import logging
import os
import time

import pytest

from m_flow.llm.config import get_llm_config
from .mock_embedding_engine import MockEmbeddingEngine

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def _setup_env(requests: int = 3, interval: int = 5) -> None:
    """设置测试环境"""
    os.environ["EMBEDDING_RATE_LIMIT_ENABLED"] = "true"
    os.environ["EMBEDDING_RATE_LIMIT_REQUESTS"] = str(requests)
    os.environ["EMBEDDING_RATE_LIMIT_INTERVAL"] = str(interval)
    os.environ["MOCK_EMBEDDING"] = "true"
    os.environ["DISABLE_RETRIES"] = "true"
    get_llm_config.cache_clear()


def _cleanup_env() -> None:
    """清理测试环境"""
    for key in [
        "EMBEDDING_RATE_LIMIT_ENABLED",
        "EMBEDDING_RATE_LIMIT_REQUESTS",
        "EMBEDDING_RATE_LIMIT_INTERVAL",
        "MOCK_EMBEDDING",
        "DISABLE_RETRIES",
    ]:
        os.environ.pop(key, None)


class TestEmbeddingRateLimiting:
    """嵌入限流测试套件"""

    @pytest.mark.asyncio
    async def test_realistic_scenario(self):
        """真实场景：3请求/5秒限制"""
        _setup_env(requests=3, interval=5)

        cfg = get_llm_config()
        log.info(f"配置: {cfg.embedding_rate_limit_requests}请求/{cfg.embedding_rate_limit_interval}秒")

        engine = MockEmbeddingEngine()
        engine.setup(delay=0.1)

        stats = {"ok": 0, "fail": 0}

        async def req(i: int) -> bool:
            try:
                log.info(f"请求 #{i + 1}")
                emb = await engine.embed_text([f"text-{i}"])
                log.info(f"请求 #{i + 1} 成功: dim={len(emb[0])}")
                return True
            except Exception as e:
                log.info(f"请求 #{i + 1} 限流: {e}")
                return False

        # 批次1: 10并发请求
        log.info("\n--- 批次1: 10并发 ---")
        t0 = time.time()
        results = await asyncio.gather(*[req(i) for i in range(10)])
        ok1, fail1 = results.count(True), results.count(False)
        log.info(f"耗时: {time.time() - t0:.2f}s, 成功: {ok1}, 限流: {fail1}")
        stats["ok"] += ok1
        stats["fail"] += fail1

        # 等待部分恢复
        log.info("\n等待2秒...")
        await asyncio.sleep(2)

        # 批次2: 5并发请求
        log.info("\n--- 批次2: 5并发 ---")
        t0 = time.time()
        results = await asyncio.gather(*[req(i) for i in range(5)])
        ok2, fail2 = results.count(True), results.count(False)
        log.info(f"耗时: {time.time() - t0:.2f}s, 成功: {ok2}, 限流: {fail2}")
        stats["ok"] += ok2
        stats["fail"] += fail2

        # 等待完全恢复
        log.info("\n等待5秒...")
        await asyncio.sleep(5)

        # 批次3: 3顺序请求
        log.info("\n--- 批次3: 3顺序 ---")
        t0 = time.time()
        ok3, fail3 = 0, 0
        for i in range(3):
            try:
                await engine.embed_text([f"seq-{i}"])
                ok3 += 1
            except Exception:
                fail3 += 1
        log.info(f"耗时: {time.time() - t0:.2f}s, 成功: {ok3}, 限流: {fail3}")
        stats["ok"] += ok3
        stats["fail"] += fail3

        # 汇总
        log.info(f"\n总计: 成功={stats['ok']}, 限流={stats['fail']}")
        assert stats["ok"] > 0, "应有成功请求"

        _cleanup_env()

    @pytest.mark.asyncio
    async def test_controlled_failures(self):
        """测试可控失败"""
        _setup_env(requests=10, interval=5)

        engine = MockEmbeddingEngine()
        engine.setup(fail_nth=3, delay=0.1)

        log.info("\n--- 可控失败测试 ---")
        for i in range(10):
            try:
                await engine.embed_text([f"test-{i}"])
                log.info(f"请求 #{i + 1} 成功")
            except Exception as e:
                log.info(f"请求 #{i + 1} 失败: {e}")

        _cleanup_env()


if __name__ == "__main__":
    asyncio.run(TestEmbeddingRateLimiting().test_realistic_scenario())
    asyncio.run(TestEmbeddingRateLimiting().test_controlled_failures())
