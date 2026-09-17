"""
分布式边队列添加模块
"""

from __future__ import annotations


async def queued_add_edges(edges: list) -> None:
    """
    将边批次加入分布式队列

    超大批次会自动拆分重试
    """
    from grpclib import GRPCError

    from ..queues import add_nodes_and_edges_queue

    try:
        await add_nodes_and_edges_queue.put.aio(([], edges))
    except GRPCError:
        mid = len(edges) // 2
        await queued_add_edges(edges[:mid])
        await queued_add_edges(edges[mid:])
