"""
图数据库节点读取子进程测试
用于测试并发读取场景
"""

from __future__ import annotations

import asyncio

from m_flow.adapters.graph.kuzu.adapter import KuzuAdapter

_DB_PATH = "test.db"
_QUERY_COUNT = 6


async def execute_read_test() -> None:
    """执行读取测试"""
    graph = KuzuAdapter(_DB_PATH)

    for i in range(_QUERY_COUNT):
        res = await graph.query("MATCH (n:Node) RETURN COUNT(n)")
        count = res[0][0] if res and res[0] else res
        print(f"Reader[{i + 1}]: 节点数={count}")


if __name__ == "__main__":
    asyncio.run(execute_read_test())
