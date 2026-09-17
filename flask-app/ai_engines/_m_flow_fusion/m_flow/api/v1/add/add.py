"""
Data Ingestion API

Core entry point for adding data to M-flow knowledge graph system.
Handles various input formats and orchestrates the ingestion pipeline.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, BinaryIO, Union
from uuid import UUID

from m_flow.shared.logging_utils import get_logger

if TYPE_CHECKING:
    from m_flow.auth.models import User
    from m_flow.pipeline.models import RunEvent

_log = get_logger()

# ---------------------------------------------------------------------------
# Type Aliases
# ---------------------------------------------------------------------------

DataInput = Union[BinaryIO, list[BinaryIO], str, list[str]]
LoaderSpec = Union[str, dict[str, dict[str, Any]]]


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------


def _normalize_loader_config(loaders: list[LoaderSpec] | None) -> dict[str, dict] | None:
    """
    Transform loader specifications into a unified dictionary format.

    Accepts:
        - String identifiers: ["pdf", "docx"] -> {"pdf": {}, "docx": {}}
        - Dict configs: [{"pdf": {"key": "val"}}] -> {"pdf": {"key": "val"}}
        - Mixed: ["txt", {"csv": {"delimiter": ","}}]

    Returns None if input is None.
    """
    if loaders is None:
        return None

    result: dict[str, dict] = {}
    for spec in loaders:
        if isinstance(spec, dict):
            result.update(spec)
        else:
            result[spec] = {}
    return result


def _normalize_created_at(created_at: int | datetime | None) -> int | None:
    """
    Normalize created_at to milliseconds timestamp.

    Args:
        created_at: Input timestamp
            - int: Unix milliseconds, return as-is
            - datetime: Convert to milliseconds (naive datetime treated as UTC)
            - None: Return None (use default behavior)

    Returns:
        Milliseconds timestamp or None

    Raises:
        ValueError: If input is not int, datetime, or None
    """
    if created_at is None:
        return None

    if isinstance(created_at, datetime):
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        return int(created_at.timestamp() * 1000)

    if isinstance(created_at, int):
        return created_at

    raise ValueError(f"created_at must be int, datetime, or None, got {type(created_at)}")


def _build_ingestion_tasks(
    ds_name: str,
    usr: "User",
    nodes: list[str] | None,
    ds_id: UUID | None,
    loader_cfg: dict | None,
    created_at_ms: int | None = None,
) -> list:
    """Construct the pipeline task sequence for data ingestion."""
    from m_flow.ingestion.pipeline_tasks import ingest_data, resolve_data_directories
    from m_flow.pipeline import Stage

    return [
        Stage(resolve_data_directories, include_subdirectories=True),
        Stage(ingest_data, ds_name, usr, nodes, ds_id, loader_cfg, created_at_ms),
    ]


async def _prepare_pipeline_context(
    ds_name: str,
    ds_id: UUID | None,
    usr: "User" | None,
) -> tuple["User", Any]:
    """
    Initialize system and resolve user/dataset authorization.

    Returns:
        Tuple of (authorized_user, authorized_dataset)
    """
    from m_flow.core.domain.operations.setup import setup
    from m_flow.pipeline.layers.reset_dataset_pipeline_run_status import (
        reset_dataset_pipeline_run_status,
    )
    from m_flow.pipeline.layers.authorize_dataset import (
        authorize_dataset,
    )

    await setup()

    auth_user, auth_dataset = await authorize_dataset(
        dataset_name=ds_name,
        dataset_id=ds_id,
        user=usr,
    )

    await reset_dataset_pipeline_run_status(
        auth_dataset.id,
        auth_user,
        pipeline_names=["add_pipeline", "memorize_pipeline"],
    )

    return auth_user, auth_dataset


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def add(
    data: DataInput,
    dataset_name: str = "main_dataset",
    user: "User" | None = None,
    graph_scope: list[str] | None = None,
    vector_db_config: dict | None = None,
    graph_db_config: dict | None = None,
    dataset_id: UUID | None = None,
    preferred_loaders: list[LoaderSpec] | None = None,
    incremental_loading: bool = True,
    enable_cache: bool = True,
    items_per_batch: int | None = 20,
    created_at: int | datetime | None = None,
) -> "RunEvent":
    """
    Ingest data into the M-flow knowledge graph system.

    This function serves as the primary entry point for data ingestion,
    accepting various formats and storing them for subsequent processing.

    Supported Formats:
        * Plain text strings
        * File paths (absolute, relative, file://, s3://)
        * Binary file objects (BinaryIO)
        * Web URLs (http://, https://)
        * Lists combining any of the above

    File Types:
        Text (.txt, .md, .csv), PDF, Images (OCR), Audio (transcription),
        Code files, Office documents (.docx, .pptx)

    Args:
        data: Content to ingest - text, file path, URL, or binary stream.
        dataset_name: Target dataset identifier (default: "main_dataset").
        user: Authenticated user; uses system default if not provided.
        graph_scope: Graph node identifiers for data organization.
        vector_db_config: Custom vector database settings.
        graph_db_config: Custom graph database settings.
        dataset_id: Explicit dataset UUID (overrides dataset_name).
        preferred_loaders: List of loader names or configs for specific formats.
        incremental_loading: Skip already-processed files when True.
        enable_cache: When True, skip add_pipeline if qualification reports completed.
        items_per_batch: Number of items per processing batch.
        created_at: Optional timestamp for the content.
            - int: Unix timestamp in milliseconds
            - datetime: Python datetime object (naive treated as UTC)
            - None: Use current system time (default)
            Use this when importing historical data to preserve original timestamps.

    Returns:
        Pipeline execution information including run ID, dataset ID,
        processing status, and execution metadata.

    Usage:
        >>> import m_flow
        >>> await m_flow.add("Some text content")
        >>> await m_flow.add("/path/to/document.pdf", dataset_name="docs")
        >>> await m_flow.add(["text", "/file.pdf", "https://example.com"])
        >>> # Import historical chat with original timestamp
        >>> from datetime import datetime
        >>> await m_flow.add("I went hiking yesterday", created_at=datetime(2023, 5, 8))

    Environment:
        Required: LLM_API_KEY
        Optional: LLM_PROVIDER, LLM_MODEL, VECTOR_DB_PROVIDER,
                  GRAPH_DATABASE_PROVIDER, TAVILY_API_KEY
    """
    from m_flow.pipeline import execute_workflow

    # Normalize loader configuration
    loader_cfg = _normalize_loader_config(preferred_loaders)

    # Normalize created_at to milliseconds
    created_at_ms = _normalize_created_at(created_at)

    # Resolve authorization context
    auth_user, auth_dataset = await _prepare_pipeline_context(dataset_name, dataset_id, user)

    # Build task pipeline
    tasks = _build_ingestion_tasks(dataset_name, auth_user, graph_scope, dataset_id, loader_cfg, created_at_ms)

    # Execute ingestion pipeline
    result: "RunEvent" | None = None
    from m_flow.pipeline.operations.pipeline import WorkflowConfig

    async for run_detail in execute_workflow(
        tasks=tasks,
        datasets=[auth_dataset.id],
        data=data,
        user=auth_user,
        name="add_pipeline",
        config=WorkflowConfig(
            vector_db=vector_db_config,
            graph_db=graph_db_config,
            cache=enable_cache,
            incremental=incremental_loading,
            batch_size=items_per_batch,
        ),
    ):
        result = run_detail

    return result
