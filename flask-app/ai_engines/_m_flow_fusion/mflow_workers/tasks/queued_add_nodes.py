"""
分布式节点队列添加模块
"""

from __future__ import annotations


async def queued_add_nodes(nodes: list) -> None:
    """
    将节点批次加入分布式队列

    超大批次会自动拆分重试
    """
    from grpclib import GRPCError

    from ..queues import add_nodes_and_edges_queue

    try:
        await add_nodes_and_edges_queue.put.aio((nodes, []))
    except GRPCError:
        mid = len(nodes) // 2
        await queued_add_nodes(nodes[:mid])
        await queued_add_nodes(nodes[mid:])
