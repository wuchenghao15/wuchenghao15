"""
分布式处理入口点
启动工作器并执行示例任务
"""

from __future__ import annotations

import asyncio
import os

import m_flow
from mflow_workers.app import app
from mflow_workers.queues import add_memory_nodes_queue, add_nodes_and_edges_queue
from mflow_workers.signal import QueueSignal
from mflow_workers.workers.graph_persistence_worker import graph_persistence_worker
from mflow_workers.workers.memory_node_saving_worker import memory_node_saving_worker
from m_flow.api.v1.prune import prune
from m_flow.core.domain.operations.setup import setup
from m_flow.shared.logging_utils import get_logger

_log = get_logger()

os.environ["MFLOW_DISTRIBUTED"] = "True"

_GRAPH_WORKERS = 1
_MEMORY_WORKERS = 10


@app.local_entrypoint()
async def main():
    """分布式处理主入口"""
    # 清空队列
    await add_nodes_and_edges_queue.clear.aio()
    await add_memory_nodes_queue.clear.aio()

    workers = []

    # 清理数据
    await prune.prune_data()
    await prune.prune_system(metadata=True)
    await setup()

    # 启动图保存工作器
    for _ in range(_GRAPH_WORKERS):
        workers.append(graph_persistence_worker.spawn())

    # 启动记忆节点工作器
    for _ in range(_MEMORY_WORKERS):
        workers.append(memory_node_saving_worker.spawn())

    sample_data = [
        "Tokyo is the capital of Japan and a major financial hub",
        "The Amazon rainforest spans nine countries in South America",
        "CERN operates the Large Hadron Collider near Geneva",
        "The Nile is the longest river in Africa",
        "SpaceX developed the reusable Falcon 9 rocket",
    ]

    await m_flow.add(sample_data, dataset_name="demo-dataset")
    await m_flow.memorize(datasets=["demo-dataset"])

    # 发送停止信号
    await add_nodes_and_edges_queue.put.aio(QueueSignal.STOP)
    await add_memory_nodes_queue.put.aio(QueueSignal.STOP)

    # 等待所有工作器完成
    for w in workers:
        try:
            print("等待工作器完成...")
            result = w.get()
            print(f"工作器完成: {result}")
        except Exception as e:
            _log.error("工作器异常: %s", e)


if __name__ == "__main__":
    asyncio.run(main())
