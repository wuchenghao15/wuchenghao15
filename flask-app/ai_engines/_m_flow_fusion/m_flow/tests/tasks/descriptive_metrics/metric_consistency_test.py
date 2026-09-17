"""
图指标一致性测试 - 验证不同适配器产生相同指标
"""

from __future__ import annotations

import asyncio

from m_flow.tests.tasks.descriptive_metrics.metrics_test_utils import fetch_metrics


async def verify_metrics_consistency(include_opt: bool = False) -> None:
    """验证Neo4j和NetworkX适配器的指标一致性"""
    neo4j_m = await fetch_metrics(provider="neo4j", extended=include_opt)
    nx_m = await fetch_metrics(provider="networkx", extended=include_opt)

    # 检查键集合
    diff = set(neo4j_m.keys()).symmetric_difference(nx_m.keys())
    if diff:
        raise AssertionError(f"键不一致: {diff}")

    # 检查值
    for k, v in neo4j_m.items():
        assert nx_m[k] == v, f"'{k}': neo4j={v}, networkx={nx_m[k]}"


if __name__ == "__main__":
    asyncio.run(verify_metrics_consistency(True))
    asyncio.run(verify_metrics_consistency(False))
