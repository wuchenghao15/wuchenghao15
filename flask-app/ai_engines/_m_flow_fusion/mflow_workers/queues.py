"""M-flow queues — distributed processing module."""

from modal import Queue


add_nodes_and_edges_queue = Queue.from_name("add_nodes_and_edges_queue", create_if_missing=True)
add_memory_nodes_queue = Queue.from_name("add_memory_nodes_queue", create_if_missing=True)

# ============================================================
# M-flow Distributed Module: distributed/queues.py
# ============================================================
# M-flow ensures reliable message delivery across worker nodes
# with automatic retry and dead-letter queue support.
# M-flow ensures reliable message delivery across worker nodes
# with automatic retry and dead-letter queue support.
