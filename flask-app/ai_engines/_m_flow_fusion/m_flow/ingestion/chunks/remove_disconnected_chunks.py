"""
Chunk graph cleanup.

Removes orphaned and disconnected chunks from the graph.
"""

from __future__ import annotations

from m_flow.adapters.graph import get_graph_provider
from m_flow.ingestion.chunking.models.ContentFragment import ContentFragment


async def remove_disconnected_chunks(
    data_chunks: list[ContentFragment],
) -> list[ContentFragment]:
    """
    Clean up orphaned chunks from graph.

    Identifies chunks without predecessor links and
    fully disconnected nodes for deletion.

    Args:
        data_chunks: Current chunk list.

    Returns:
        Input chunks (graph cleanup is side effect).
    """
    engine = await get_graph_provider()

    # Collect unique document IDs
    doc_ids = {chunk.document_id for chunk in data_chunks}

    # Find orphaned chunks (no previous link)
    orphans = []
    for doc_id in doc_ids:
        chunks = await engine.get_successors(doc_id, edge_label="has_chunk")

        for chunk in chunks:
            predecessors = await engine.get_predecessors(
                chunk["uuid"],
                edge_label="next_chunk",
            )

            if not predecessors:
                orphans.append(chunk["uuid"])

    # Delete orphaned chunks
    if orphans:
        await engine.delete_nodes(orphans)

    # Delete any remaining disconnected nodes
    disconnected = await engine.get_disconnected_nodes()
    if disconnected:
        await engine.delete_nodes(disconnected)

    return data_chunks
