"""
Remote Kuzu 压力测试
批量创建节点和关系
"""

from __future__ import annotations

import asyncio
import random
import time

from m_flow.adapters.graph.config import get_graph_config
from m_flow.adapters.graph.kuzu.remote_kuzu_adapter import RemoteKuzuAdapter
from m_flow.shared.logging_utils import get_logger

_BATCH_SIZE = 5000
_NUM_BATCHES = 10
_TOTAL_NODES = _BATCH_SIZE * _NUM_BATCHES
_TOTAL_EDGES = _TOTAL_NODES - 1

log = get_logger()


async def _insert_node(adapter: RemoteKuzuAdapter, node: dict) -> None:
    """插入单个节点"""
    cypher = f"CREATE (n:TestNode {{id: '{node['id']}', name: '{node['name']}', value: {node['value']}}})"
    await adapter.query(cypher)


async def _insert_edge(adapter: RemoteKuzuAdapter, src: str, tgt: str) -> None:
    """插入单条边"""
    w = random.random()
    cypher = f"MATCH (a:TestNode {{id: '{src}'}}), (b:TestNode {{id: '{tgt}'}}) CREATE (a)-[r:CONNECTS_TO {{weight: {w}}}]->(b)"
    await adapter.query(cypher)


async def _process_batch(adapter: RemoteKuzuAdapter, start: int, size: int) -> float:
    """处理单个批次"""
    t0 = time.time()
    batch_num = start // size + 1

    log.info(f"准备批次 {batch_num}/{_NUM_BATCHES}...")

    # 构建节点数据
    nodes = [
        {"id": str(start + i), "name": f"TestNode_{start + i}", "value": random.randint(1, 1000)} for i in range(size)
    ]

    # 并发创建节点
    log.info(f"批次 {batch_num}: 创建 {size} 个节点...")
    t1 = time.time()
    await asyncio.gather(*[_insert_node(adapter, n) for n in nodes])
    node_time = time.time() - t1

    # 并发创建边
    log.info(f"批次 {batch_num}: 创建边...")
    t2 = time.time()
    await asyncio.gather(*[_insert_edge(adapter, nodes[j]["id"], nodes[j + 1]["id"]) for j in range(len(nodes) - 1)])
    edge_time = time.time() - t2

    elapsed = time.time() - t0
    log.info(f"批次 {batch_num} 完成: {elapsed:.2f}s (节点: {node_time:.2f}s, 边: {edge_time:.2f}s)")
    return elapsed


async def _create_test_data(adapter: RemoteKuzuAdapter) -> float:
    """创建所有测试数据"""
    tasks = [asyncio.create_task(_process_batch(adapter, i, _BATCH_SIZE)) for i in range(0, _TOTAL_NODES, _BATCH_SIZE)]
    times = await asyncio.gather(*tasks)
    return sum(times)


async def run_stress_test():
    """运行压力测试"""
    cfg = get_graph_config()
    adapter = RemoteKuzuAdapter(cfg.graph_database_url, cfg.graph_database_username, cfg.graph_database_password)

    try:
        log.info("=== Kuzu 压力测试开始 ===")
        log.info(f"配置: {_NUM_BATCHES} 批 × {_BATCH_SIZE} 节点")
        log.info(f"预计节点数: {_TOTAL_NODES}, 预计边数: {_TOTAL_EDGES}")

        t0 = time.time()

        # 清理
        log.info("[1/5] 删除旧表...")
        await adapter.query("DROP TABLE IF EXISTS CONNECTS_TO")
        await adapter.query("DROP TABLE IF EXISTS TestNode")

        # 创建节点表
        log.info("[2/5] 创建节点表...")
        await adapter.query("CREATE NODE TABLE TestNode (id STRING, name STRING, value INT64, PRIMARY KEY (id))")

        # 创建边表
        log.info("[3/5] 创建边表...")
        await adapter.query("CREATE REL TABLE CONNECTS_TO (FROM TestNode TO TestNode, weight DOUBLE)")

        # 清空数据
        log.info("[4/5] 清空数据...")
        await adapter.query("MATCH (n:TestNode) DETACH DELETE n")

        # 创建测试数据
        log.info(f"[5/5] 创建测试数据 ({_NUM_BATCHES} 并发批次)...")
        batch_time = await _create_test_data(adapter)

        total = time.time() - t0

        # 验证
        log.info("验证数据...")
        res = await adapter.query("MATCH (n:TestNode) RETURN COUNT(n) as count")
        log.info(f"节点数: {res}")
        res = await adapter.query("MATCH ()-[r:CONNECTS_TO]->() RETURN COUNT(r) as count")
        log.info(f"边数: {res}")

        log.info("=== 测试摘要 ===")
        log.info(f"批处理时间: {batch_time:.2f}s, 总时间: {total:.2f}s")

    finally:
        await adapter.close()


if __name__ == "__main__":
    asyncio.run(run_stress_test())
