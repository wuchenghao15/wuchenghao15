"""
图数据保存工作器
分布式处理模块，用于批量保存节点和边到图数据库
"""

from __future__ import annotations

import asyncio
import os

import modal
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from mflow_workers.app import app
from mflow_workers.modal_image import image
from mflow_workers.queues import add_nodes_and_edges_queue
from mflow_workers.signal import QueueSignal
from m_flow.adapters.graph import get_graph_provider
from m_flow.adapters.graph.config import get_graph_config
from m_flow.shared.logging_utils import get_logger

_log = get_logger("graph_persistence_worker")

# 批量处理大小
_BATCH_SIZE = 25

# Modal密钥名称
_SECRET_NAME = os.environ.get("MODAL_SECRET_NAME", "distributed_m_flow")


class GraphDeadlockError(Exception):
    """图数据库死锁异常"""

    def __init__(self):
        super().__init__("图数据库写入时发生死锁")


def _check_deadlock(err: Exception) -> bool:
    """检查是否为死锁错误"""
    cfg = get_graph_config()

    # Neo4j死锁检测
    if cfg.graph_database_provider == "neo4j":
        from neo4j.exceptions import TransientError

        if isinstance(err, TransientError):
            if err.code == "Neo.TransientError.Transaction.DeadlockDetected":
                return True

    # Kuzu死锁检测
    err_msg = str(err).lower()
    if "deadlock" in err_msg or "cannot acquire lock" in err_msg:
        return True

    return False


@app.function(
    retries=3,
    image=image,
    timeout=86400,
    max_containers=1,
    secrets=[modal.Secret.from_name(_SECRET_NAME)],
)
async def graph_persistence_worker():
    """
    图数据保存工作器主函数

    从队列中批量获取节点和边数据，写入图数据库
    """
    print("启动图数据保存工作器")
    graph_db = await get_graph_provider()
    should_stop = False

    while True:
        if should_stop:
            print("所有数据处理完成，工作器退出")
            return True

        queue_len = await add_nodes_and_edges_queue.len.aio()
        if queue_len == 0:
            print("队列为空，等待中...")
            await asyncio.sleep(5)
            continue

        try:
            print(f"队列剩余: {queue_len}")

            nodes_batch, edges_batch = [], []
            batch_count = min(_BATCH_SIZE, queue_len)

            for _ in range(batch_count):
                item = await add_nodes_and_edges_queue.get.aio(block=False)

                if not item:
                    continue

                if item == QueueSignal.STOP:
                    await add_nodes_and_edges_queue.put.aio(QueueSignal.STOP)
                    should_stop = True
                    break

                if len(item) == 2:
                    nodes, edges = item
                    nodes_batch.extend(nodes)
                    edges_batch.extend(edges)
                else:
                    print("检测到无效数据")

            if not nodes_batch and not edges_batch:
                continue

            print(f"写入 {len(nodes_batch)} 节点, {len(edges_batch)} 边")

            @retry(
                retry=retry_if_exception_type(GraphDeadlockError),
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=2, min=1, max=6),
            )
            async def write_nodes(data):
                try:
                    await graph_db.add_nodes(data, distributed=False)
                except Exception as e:
                    if _check_deadlock(e):
                        raise GraphDeadlockError()
                    raise

            @retry(
                retry=retry_if_exception_type(GraphDeadlockError),
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=2, min=1, max=6),
            )
            async def write_edges(data):
                try:
                    await graph_db.add_edges(data, distributed=False)
                except Exception as e:
                    if _check_deadlock(e):
                        raise GraphDeadlockError()
                    raise

            if nodes_batch:
                await write_nodes(nodes_batch)

            if edges_batch:
                await write_edges(edges_batch)

            print("批次写入完成")

        except modal.exception.DeserializationError as e:
            _log.error("反序列化错误: %s", e)
            continue
