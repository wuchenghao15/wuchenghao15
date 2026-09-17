"""
Ingest API Router

Unified REST API endpoint for data ingestion (add + memorize).
Combines file upload and knowledge graph construction in a single call.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Literal, Optional, Union
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from m_flow.shared.logging_utils import get_logger

if TYPE_CHECKING:
    from m_flow.auth.models import User

_log = get_logger()


# ---------------------------------------------------------------------------
# Request/Response Models
# ---------------------------------------------------------------------------


class IngestRequest(BaseModel):
    """
    Ingest request body for JSON-based ingestion.

    Use this for text content ingestion without file upload.
    For file uploads, use multipart/form-data with the /upload endpoint.
    """

    content: str = Field(..., description="Text content to ingest")
    dataset_name: Optional[str] = Field(default=None, description="Target dataset name (default: 'main_dataset')")
    graph_scope: Optional[list[str]] = Field(default=None, description="Node identifiers for graph organization")
    skip_memorize: bool = Field(default=False, description="If true, only add data without building knowledge graph")
    run_in_background: bool = Field(
        default=False, description="If true, memorize runs in background (returns immediately)"
    )
    chunk_size: Optional[int] = Field(default=None, description="Chunk size for text splitting")
    chunks_per_batch: Optional[int] = Field(default=None, description="Number of chunks per processing batch")
    enable_episode_routing: Optional[bool] = Field(
        default=None,
        description="Merge new content into existing related episodes. "
        "Disable for faster concurrent ingestion of independent documents.",
    )
    enable_content_routing: Optional[bool] = Field(
        default=None,
        description="Classify each sentence by topic within a chunk. "
        "Enable when text may contain multiple topics per block. "
        "Costs extra LLM tokens per multi-sentence chunk.",
    )
    content_type: Optional[Literal["text", "dialog"]] = Field(
        default=None,
        description="'text' for articles/documents, 'dialog' for chat logs and meeting transcripts "
        "(splits by speaker turn). Auto-detected when omitted.",
    )
    enable_procedural: Optional[bool] = Field(
        default=None,
        description="Extract reusable procedures/preferences to complement episodic facts. "
        "Experimental. Costs extra LLM tokens.",
    )
    enable_facet_points: Optional[bool] = Field(
        default=None,
        description="Generate fine-grained FacetPoint nodes for more precise retrieval. "
        "Costs extra LLM tokens per facet.",
    )
    conflict_mode: Optional[str] = Field(
        default=None, description="Conflict resolution mode: 'skip', 'overwrite', 'merge'"
    )
    created_at: Optional[Union[int, str]] = Field(
        default=None,
        description=(
            "Timestamp for the content (for historical data import). "
            "Accepts: Unix milliseconds (int), ISO 8601 string, or null. "
            "When set, this timestamp is used as anchor for relative time parsing "
            "(e.g., 'yesterday' will be parsed relative to this timestamp)."
        ),
    )
    incremental_loading: bool = Field(
        default=True,
        description=(
            "Applies to add() only. When false, add always runs tasks per item "
            "(no per-Data add_pipeline workflow_state short-circuit). "
            "Use for repeated ingest into the same dataset (e.g. one API call per session). "
            "Memorize keeps incremental processing unless memorize_incremental_loading is set."
        ),
    )
    memorize_incremental_loading: Optional[bool] = Field(
        default=None,
        description=(
            "When set, overrides memorize() incremental_loading. When null (default), memorize "
            "uses true so each call only processes Data rows not yet memorized for this dataset. "
            "Set false only for intentional full re-memorize (expensive, may duplicate graph data)."
        ),
    )
    enable_cache: bool = Field(
        default=True,
        description=(
            "When false, add/memorize pipelines are not skipped when the latest run is already "
            "completed. Use false for multi-batch ingest to the same dataset; pair with "
            "incremental_loading=false on add when add was skipping incorrectly."
        ),
    )


class IngestResponse(BaseModel):
    """Ingest operation result."""

    dataset_id: str = Field(..., description="Dataset UUID")
    dataset_name: str = Field(..., description="Dataset name")
    status: str = Field(
        ..., description="Ingest status: completed, background_started, memorize_skipped, memorize_failed"
    )
    add_run_id: str = Field(..., description="Add phase pipeline run ID")
    memorize_run_id: Optional[str] = Field(default=None, description="Memorize phase pipeline run ID")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")


# ---------------------------------------------------------------------------
# Telemetry Helper
# ---------------------------------------------------------------------------


def _parse_created_at(value: Optional[Union[int, str]]) -> Optional[int]:
    """
    Parse created_at value to milliseconds timestamp.

    Args:
        value: Input timestamp
            - int: Unix milliseconds, return as-is
            - str: ISO 8601 datetime string (e.g., "2023-05-08T13:56:00Z")
            - None: Return None

    Returns:
        Milliseconds timestamp or None

    Raises:
        ValueError: If string is not valid ISO 8601 format
    """
    if value is None:
        return None

    if isinstance(value, int):
        return value

    if isinstance(value, str):
        try:
            # Try ISO 8601 format
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return int(dt.timestamp() * 1000)
        except ValueError:
            raise ValueError(
                f"Invalid created_at format: '{value}'. Expected Unix milliseconds (int) or ISO 8601 string."
            )

    raise ValueError(f"created_at must be int or str, got {type(value)}")


def _track_ingest_event(user_id: UUID, dataset_name: str | None, mode: str) -> None:
    """Emit telemetry for ingest endpoint invocation."""
    from m_flow import __version__ as ver
    from m_flow.shared.utils import send_telemetry

    send_telemetry(
        "Ingest API Endpoint Invoked",
        user_id,
        additional_properties={
            "endpoint": f"POST /v1/ingest/{mode}",
            "dataset_name": dataset_name,
            "m_flow_version": ver,
        },
    )


# ---------------------------------------------------------------------------
# Authentication Dependency
# ---------------------------------------------------------------------------


def _auth():
    """Return the user authentication dependency."""
    from m_flow.auth.methods import get_authenticated_user

    return get_authenticated_user


# ---------------------------------------------------------------------------
# Router Factory
# ---------------------------------------------------------------------------


def get_ingest_router() -> APIRouter:
    """
    Construct the unified ingest API router.

    Provides endpoints for:
    - POST / : Text content ingestion via JSON body
    - POST /upload : File upload ingestion via multipart/form-data
    """
    router = APIRouter()

    @router.post("", response_model=IngestResponse)
    async def ingest_text(
        request: IngestRequest,
        user: "User" = Depends(_auth()),
    ) -> IngestResponse:
        """
        Ingest text content into a dataset with knowledge graph construction.

        This is a unified operation that combines:
        1. add() - Store raw data in the database
        2. memorize() - Build knowledge graph (episodes, facets, entities)

        For file uploads, use the /upload endpoint instead.

        Args:
            request: Ingest request with content and options.

        Returns:
            IngestResponse with dataset info and status.

        Status values:
            - completed: Synchronous completion, data is queryable
            - background_started: Background processing started
            - memorize_skipped: Only add phase completed (skip_memorize=true)
            - memorize_failed: Add succeeded but memorize failed
        """
        _track_ingest_event(user.id, request.dataset_name, "text")

        from m_flow.api.v1.ingest import ingest

        try:
            # Build kwargs from request
            kwargs = {
                "user": user,
                "skip_memorize": request.skip_memorize,
            }

            # Add optional parameters if provided
            if request.graph_scope:
                kwargs["graph_scope"] = request.graph_scope
            if request.run_in_background:
                kwargs["run_in_background"] = request.run_in_background
            if request.chunk_size is not None:
                kwargs["chunk_size"] = request.chunk_size
            if request.chunks_per_batch is not None:
                kwargs["chunks_per_batch"] = request.chunks_per_batch
            if request.enable_episode_routing is not None:
                kwargs["enable_episode_routing"] = request.enable_episode_routing
            if request.enable_content_routing is not None:
                kwargs["enable_content_routing"] = request.enable_content_routing
            if request.content_type is not None:
                from m_flow.shared.enums import ContentType

                kwargs["content_type"] = ContentType(request.content_type)
            if request.enable_procedural is not None:
                kwargs["enable_procedural"] = request.enable_procedural
            if request.enable_facet_points is not None:
                kwargs["enable_facet_points"] = request.enable_facet_points
            if request.conflict_mode:
                kwargs["conflict_mode"] = request.conflict_mode
            if request.created_at is not None:
                kwargs["created_at"] = _parse_created_at(request.created_at)
            kwargs["incremental_loading"] = request.incremental_loading
            kwargs["enable_cache"] = request.enable_cache
            if request.memorize_incremental_loading is not None:
                kwargs["memorize_incremental_loading"] = request.memorize_incremental_loading

            result = await ingest(
                data=request.content,
                dataset_name=request.dataset_name,
                **kwargs,
            )

            return IngestResponse(
                dataset_id=str(result.dataset_id),
                dataset_name=result.dataset_name,
                status=result.status.value,
                add_run_id=str(result.add_run_id),
                memorize_run_id=str(result.memorize_run_id) if result.memorize_run_id else None,
                error_message=result.error_message,
            )

        except TypeError as err:
            # Invalid parameters
            return JSONResponse(
                status_code=400,
                content={"error": str(err), "code": "INVALID_PARAMETERS"},
            )
        except ValueError as err:
            # No data or validation error
            return JSONResponse(
                status_code=400,
                content={"error": str(err), "code": "VALIDATION_ERROR"},
            )
        except Exception as err:
            _log.exception("Ingest failed: %s", err)
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "code": "INTERNAL_ERROR"},
            )

    @router.post("/upload", response_model=IngestResponse)
    async def ingest_files(
        data: list[UploadFile] = File(..., description="Files to upload and ingest"),
        datasetName: Optional[str] = Form(default=None, description="Target dataset name"),
        datasetId: Union[UUID, Literal[""], None] = Form(
            default=None, examples=[""], description="Existing dataset UUID"
        ),
        graph_scope: Optional[list[str]] = Form(default=None, examples=[[""]], description="Node identifiers"),
        skip_memorize: bool = Form(default=False, description="Skip knowledge graph construction"),
        run_in_background: bool = Form(default=False, description="Run memorize in background"),
        chunk_size: Optional[int] = Form(default=None, description="Chunk size"),
        chunks_per_batch: Optional[int] = Form(default=None, description="Chunks per batch"),
        enable_episode_routing: Optional[bool] = Form(
            default=None,
            description="Merge new content into existing related episodes; disable for faster independent ingestion",
        ),
        enable_content_routing: Optional[bool] = Form(
            default=None, description="Classify sentences by topic within chunks; costs extra LLM tokens"
        ),
        content_type: Optional[Literal["text", "dialog"]] = Form(
            default=None, description="'text' or 'dialog' (speaker-turn split); auto-detected when omitted"
        ),
        enable_procedural: Optional[bool] = Form(
            default=None, description="Extract procedures/preferences (experimental, extra LLM tokens)"
        ),
        enable_facet_points: Optional[bool] = Form(
            default=None, description="Fine-grained FacetPoint nodes for precise retrieval (extra LLM tokens)"
        ),
        conflict_mode: Optional[str] = Form(default=None, description="Conflict mode"),
        created_at: Optional[Union[int, str]] = Form(
            default=None, description="Timestamp for content (Unix ms or ISO 8601)"
        ),
        incremental_loading: bool = Form(
            default=True, description="add() only; false for repeated ingest to same dataset"
        ),
        memorize_incremental_loading: Optional[bool] = Form(
            default=None,
            description="Override memorize incremental; omit to keep true (recommended)",
        ),
        enable_cache: bool = Form(default=True, description="false to avoid pipeline complete short-circuit"),
        user: "User" = Depends(_auth()),
    ) -> IngestResponse:
        """
        Ingest uploaded files into a dataset with knowledge graph construction.

        Accepts file uploads via multipart/form-data.
        Files are processed, analyzed, and integrated into the knowledge graph.

        For text content without file upload, use the base / endpoint.

        Args:
            data: Files to upload (required).
            datasetName: Target dataset name (creates if new).
            datasetId: Existing dataset UUID (optional).
            graph_scope: Node identifiers for graph organization.
            skip_memorize: If true, only add files without building KG.
            run_in_background: If true, memorize runs asynchronously.
            chunk_size: Text chunking size.
            chunks_per_batch: Processing batch size.
            enable_episode_routing: Episode routing toggle.
            enable_content_routing: Content routing toggle.
            enable_procedural: Procedural memory toggle.
            conflict_mode: Conflict resolution mode.

        Returns:
            IngestResponse with dataset info and status.
        """
        _track_ingest_event(user.id, datasetName, "upload")

        from m_flow.api.v1.ingest import ingest

        try:
            # Normalize empty values
            effective_nodes = graph_scope if graph_scope and graph_scope != [""] else None
            effective_dataset_id = datasetId if datasetId and datasetId != "" else None

            # Build kwargs
            kwargs = {
                "user": user,
                "skip_memorize": skip_memorize,
            }

            if effective_nodes:
                kwargs["graph_scope"] = effective_nodes
            if effective_dataset_id:
                kwargs["dataset_id"] = effective_dataset_id
            if run_in_background:
                kwargs["run_in_background"] = run_in_background
            if chunk_size is not None:
                kwargs["chunk_size"] = chunk_size
            if chunks_per_batch is not None:
                kwargs["chunks_per_batch"] = chunks_per_batch
            if enable_episode_routing is not None:
                kwargs["enable_episode_routing"] = enable_episode_routing
            if enable_content_routing is not None:
                kwargs["enable_content_routing"] = enable_content_routing
            if content_type is not None:
                from m_flow.shared.enums import ContentType

                kwargs["content_type"] = ContentType(content_type)
            if enable_procedural is not None:
                kwargs["enable_procedural"] = enable_procedural
            if enable_facet_points is not None:
                kwargs["enable_facet_points"] = enable_facet_points
            if conflict_mode:
                kwargs["conflict_mode"] = conflict_mode
            if created_at is not None:
                kwargs["created_at"] = _parse_created_at(created_at)
            kwargs["incremental_loading"] = incremental_loading
            kwargs["enable_cache"] = enable_cache
            if memorize_incremental_loading is not None:
                kwargs["memorize_incremental_loading"] = memorize_incremental_loading

            result = await ingest(
                data=data,
                dataset_name=datasetName,
                **kwargs,
            )

            return IngestResponse(
                dataset_id=str(result.dataset_id),
                dataset_name=result.dataset_name,
                status=result.status.value,
                add_run_id=str(result.add_run_id),
                memorize_run_id=str(result.memorize_run_id) if result.memorize_run_id else None,
                error_message=result.error_message,
            )

        except TypeError as err:
            return JSONResponse(
                status_code=400,
                content={"error": str(err), "code": "INVALID_PARAMETERS"},
            )
        except ValueError as err:
            return JSONResponse(
                status_code=400,
                content={"error": str(err), "code": "VALIDATION_ERROR"},
            )
        except Exception as err:
            _log.exception("File ingest failed: %s", err)
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "code": "INTERNAL_ERROR"},
            )

    return router
