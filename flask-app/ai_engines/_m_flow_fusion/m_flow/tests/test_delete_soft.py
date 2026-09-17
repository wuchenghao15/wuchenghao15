"""
软删除测试
"""

from __future__ import annotations

import asyncio
import pathlib

import m_flow
from m_flow.adapters.graph import get_graph_provider
from m_flow.data.methods import fetch_dataset_items
from m_flow.shared.logging_utils import get_logger

log = get_logger()
_TEST_DATA = pathlib.Path(__file__).parent / "test_data"

_CAR_TEXT = """
1. Audi - 现代设计与先进技术的结合，以Quattro全轮驱动系统闻名。
2. BMW - 巴伐利亚发动机制造厂，专注于驾驶乐趣与性能。
3. Mercedes-Benz - 奢华与品质的代名词，创新安全功能。
4. Porsche - 高性能跑车代表，911系列举世闻名。
5. Volkswagen - "人民的汽车"，从甲壳虫到高尔夫的经典传承。
"""


async def run_soft_delete_test():
    """运行软删除测试"""
    await m_flow.prune.prune_data()
    await m_flow.prune.prune_system(metadata=True)

    files = [
        str(_TEST_DATA / "artificial-intelligence.pdf"),
        str(_TEST_DATA / "Natural_language_processing_copy.txt"),
        _CAR_TEXT,
    ]

    result = await m_flow.add(files)
    ds_id = result.dataset_id

    await m_flow.memorize()

    graph = await get_graph_provider()
    nodes, edges = await graph.get_graph_data()
    assert len(nodes) > 10 and len(edges) > 10, "图数据库未导入"

    data_items = await fetch_dataset_items(ds_id)
    assert len(data_items) > 0, "数据集应包含数据"

    # 软删除每个文档
    # 注意：m_flow.delete() 是正确的 API，不是 m_flow.remove()
    for item in data_items:
        await m_flow.delete(item.id, ds_id, mode="soft")

    nodes, edges = await graph.get_graph_data()
    assert len(nodes) == 0 and len(edges) == 0, "软删除后图应为空"


if __name__ == "__main__":
    asyncio.run(run_soft_delete_test())
