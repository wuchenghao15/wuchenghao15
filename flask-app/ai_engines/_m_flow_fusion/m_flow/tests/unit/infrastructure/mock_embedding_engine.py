"""M-Flow 测试夹具：不发起外部请求的确定性嵌入后端。

本模块提供面向 ``LiteLLMEmbeddingEngine`` 的测试替身，专用于在单测中驱动
``m_flow.shared.rate_limiting`` 的令牌桶逻辑。返回的向量由常数行构成；可按
调用序号注入停顿与故障，以复现排队与重试场景，而无需 LiteLLM 或远端 API。
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from m_flow.adapters.exceptions import EmbeddingException
from m_flow.adapters.vector.embeddings.LiteLLMEmbeddingEngine import LiteLLMEmbeddingEngine
from m_flow.shared.rate_limiting import embedding_rate_limiter_context_manager

_CONSTANT_COMPONENT = 0.1


@dataclass
class _HarnessTelemetry:
    """与引擎公开 API 解耦的仿真状态（M-Flow 单测内部使用）。"""

    pause_after_dispatch_s: float = 0.0
    raise_when_invocation_multiple_of: int = 0
    invocation_index: int = field(default=0, init=False)


class MockEmbeddingEngine(LiteLLMEmbeddingEngine):
    """继承生产引擎骨架，仅在 ``embed_text`` 路径上短路为本地常数矩阵。

    保留与线上相同的 ``dimensions`` 与 tokenizer 初始化，使限流与批处理代码
    走真实分支；嵌入值本身无语义，仅占用正确形状。进入共享
    ``embedding_rate_limiter_context_manager`` 的行为与父类一致。
    """

    def __init__(self, *base_args, **base_kwargs):
        super().__init__(*base_args, **base_kwargs)
        self.mock = True
        self._telemetry = _HarnessTelemetry()

    def setup(self, *, fail_nth: int = 0, delay: float = 0.0) -> None:
        """为后续 ``embed_text`` 调用登记故障周期与人为延迟（M-Flow 限流用例入口）。

        ``fail_nth`` 为正时，每当累计调用次数为该数的整数倍即抛出
        :class:`~m_flow.adapters.exceptions.EmbeddingException`。
        ``delay`` 在进入限流上下文之前执行 ``asyncio.sleep``（秒）。
        """
        self._telemetry.raise_when_invocation_multiple_of = fail_nth
        self._telemetry.pause_after_dispatch_s = delay

    async def _apply_injected_pause(self) -> None:
        wait_s = self._telemetry.pause_after_dispatch_s
        if wait_s > 0:
            await asyncio.sleep(wait_s)

    def _emit_scheduled_fault_if_any(self) -> None:
        period = self._telemetry.raise_when_invocation_multiple_of
        if period <= 0:
            return
        idx = self._telemetry.invocation_index
        if idx % period != 0:
            return
        raise EmbeddingException(f"mflow test double: synthetic embed fault at call {idx}")

    def _synthetic_matrix(self, row_total: int) -> list[list[float]]:
        span = self.dimensions
        slab: list[list[float]] = []
        for _ in range(row_total):
            slab.append([_CONSTANT_COMPONENT] * span)
        return slab

    async def embed_text(self, segments: list[str]) -> list[list[float]]:
        """产出占位嵌入；更新内部调用序号，可选睡眠与抛错，再套限流上下文。

        参数 ``segments`` 与父类 ``text`` 含义相同，仅命名与父类不同以增强可读性。
        """
        self._telemetry.invocation_index += 1
        await self._apply_injected_pause()
        self._emit_scheduled_fault_if_any()
        async with embedding_rate_limiter_context_manager():
            return self._synthetic_matrix(len(segments))
