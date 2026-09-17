"""
Dataset database connection resolver.

Populates connection details for vector and graph databases.
"""

from __future__ import annotations

from m_flow.adapters.utils.get_graph_dataset_database_handler import (
    get_graph_dataset_database_handler,
)
from m_flow.adapters.utils.get_vector_dataset_database_handler import (
    get_vector_dataset_database_handler,
)
from m_flow.auth.models.DatasetStore import DatasetStore


async def resolve_dataset_database_connection_info(
    dataset_database: DatasetStore,
) -> DatasetStore:
    """
    Resolve connection details for dataset databases.

    Delegates to both vector and graph handlers to
    populate full connection information.

    Args:
        dataset_database: Record to update.

    Returns:
        Updated DatasetStore with resolved connections.
    """
    # Get handlers
    vector_handler = get_vector_dataset_database_handler(dataset_database)
    graph_handler = get_graph_dataset_database_handler(dataset_database)

    # Resolve vector connection
    dataset_database = await vector_handler["handler_instance"].resolve_dataset_connection_info(dataset_database)

    # Resolve graph connection
    dataset_database = await graph_handler["handler_instance"].resolve_dataset_connection_info(dataset_database)

    return dataset_database
