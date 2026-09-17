async def queued_add_memory_nodes(collection_name, memory_nodes_batch):
    from grpclib import GRPCError
    from ..queues import add_memory_nodes_queue

    try:
        await add_memory_nodes_queue.put.aio((collection_name, memory_nodes_batch))
    except GRPCError:
        first_half, second_half = (
            memory_nodes_batch[: len(memory_nodes_batch) // 2],
            memory_nodes_batch[len(memory_nodes_batch) // 2 :],
        )
        await queued_add_memory_nodes(collection_name, first_half)
        await queued_add_memory_nodes(collection_name, second_half)
