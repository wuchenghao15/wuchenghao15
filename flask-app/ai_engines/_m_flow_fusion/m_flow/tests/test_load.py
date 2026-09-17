"""
负载测试
"""

from __future__ import annotations

import asyncio
import pathlib
import time

import m_flow
from m_flow.search.types import RecallMode
from m_flow.shared.logging_utils import get_logger

log = get_logger()


async def _process_and_search(n: int) -> float:
    """处理并搜索"""
    t0 = time.time()

    await m_flow.memorize()

    await asyncio.gather(
        *[m_flow.search(query_text="文档相关内容", query_type=RecallMode.TRIPLET_COMPLETION) for _ in range(n)]
    )

    return time.time() - t0


async def run_load_test():
    """运行负载测试"""
    base = pathlib.Path(__file__).parent
    m_flow.config.data_root_directory(str(base / ".data_storage/test_load"))
    m_flow.config.system_root_directory(str(base / ".mflow/system/test_load"))

    pdf_count = 10
    reps = 5
    max_mins = 10
    avg_mins = 8

    times = []
    for _ in range(reps):
        await m_flow.prune.prune_data()
        await m_flow.prune.prune_system(metadata=True)

        await m_flow.add("s3://m_flow-test-load-s3-bucket")
        times.append(await _process_and_search(pdf_count))

    avg = sum(times) / len(times)

    assert avg <= avg_mins * 60, f"平均时间{avg}秒超过{avg_mins}分钟"
    assert all(t <= max_mins * 60 for t in times), "存在超时记录"


if __name__ == "__main__":
    asyncio.run(run_load_test())
