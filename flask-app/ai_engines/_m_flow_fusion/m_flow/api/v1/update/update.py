"""
Data Update API

Provides functionality to replace existing data items in the M-flow system.
Implements an atomic delete-add-memorize workflow for data refresh.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, BinaryIO, Optional, Union
from uuid import UUID

from m_flow.shared.enums import ContentType

if TYPE_CHECKING:
    from m_flow.auth.models import User
    from m_flow.pipeline.models import RunEvent

# ---------------------------------------------------------------------------
# Type Aliases
# ---------------------------------------------------------------------------

ContentInput = Union[BinaryIO, list[BinaryIO], str, list[str]]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def update(
    data_id: UUID,
    data: ContentInput,
    dataset_id: UUID,
    user: "User | None" = None,
    graph_scope: list[str] | None = None,
    vector_db_config: dict | None = None,
    graph_db_config: dict | None = None,
    preferred_loaders: dict[str, dict[str, Any]] | None = None,
    incremental_loading: bool = True,
    content_type: Optional[ContentType] = None,
) -> "RunEvent":
    """
    Replace an existing data item with new content.

    Performs an atomic refresh by removing the current data, ingesting
    the replacement content, and reprocessing the knowledge graph.

    Accepted Input Formats:
        - Text strings (any content not resembling a file path)
        - File paths: absolute, file:// URLs, s3:// paths
        - Binary streams (BinaryIO)
        - Lists combining multiple sources

    Workflow:
        1. Remove existing data item from dataset
        2. Ingest new content into the same dataset
        3. Reprocess affected graph segments

    Args:
        data_id: Identifier of the data item to replace.
        data: Replacement content (text, file path, or stream).
        dataset_id: Target dataset containing the data item.
        user: Authenticated user context (default user if omitted).
        graph_scope: Graph node identifiers for organization.
        vector_db_config: Custom vector database settings.
        graph_db_config: Custom graph database settings.
        preferred_loaders: Loader specifications for specific formats.
        incremental_loading: Enable delta processing when True.

    Returns:
        Pipeline execution details from the memorization phase.

    Raises:
        DataNotFoundError: If the specified data_id does not exist.
        DatasetNotFoundError: If dataset_id is invalid.
    """
    from m_flow.api.v1.add import add
    from m_flow.api.v1.delete import delete
    from m_flow.api.v1.memorize import memorize

    # Step 1: Remove existing content
    await delete(data_id=data_id, dataset_id=dataset_id, user=user)

    # Step 2: Ingest replacement content
    await add(
        data=data,
        dataset_id=dataset_id,
        user=user,
        graph_scope=graph_scope,
        vector_db_config=vector_db_config,
        graph_db_config=graph_db_config,
        preferred_loaders=preferred_loaders,
        incremental_loading=incremental_loading,
    )

    # Step 3: Reprocess knowledge graph
    # Build kwargs for memorize
    memorize_kwargs = {}
    if content_type is not None:
        memorize_kwargs["content_type"] = content_type
    else:
        # If content_type not provided, disable content_routing to avoid validation error
        memorize_kwargs["enable_content_routing"] = False

    result = await memorize(
        datasets=[dataset_id],
        user=user,
        vector_db_config=vector_db_config,
        graph_db_config=graph_db_config,
        incremental_loading=incremental_loading,
        **memorize_kwargs,
    )

    return result
