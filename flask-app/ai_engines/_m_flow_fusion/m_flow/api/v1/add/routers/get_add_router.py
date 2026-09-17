"""
Add Data Router

REST API endpoint for ingesting data into M-flow datasets.
Handles file uploads, URLs, and repository imports.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Union
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse

from m_flow.shared.logging_utils import get_logger

if TYPE_CHECKING:
    from m_flow.auth.models import User

_log = get_logger()


# ---------------------------------------------------------------------------
# Telemetry Helper
# ---------------------------------------------------------------------------


def _track_add_event(user_id: UUID, nodes: list[str] | None) -> None:
    """Emit telemetry for add endpoint invocation."""
    from m_flow import __version__ as ver
    from m_flow.shared.utils import send_telemetry

    send_telemetry(
        "Add API Endpoint Invoked",
        user_id,
        additional_properties={
            "endpoint": "POST /v1/add",
            "graph_scope": nodes,
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


def get_add_router() -> APIRouter:
    """
    Construct the data ingestion API router.

    Provides POST / endpoint for adding files and content
    to M-flow datasets for knowledge graph processing.
    """
    router = APIRouter()

    @router.post("", response_model=dict)
    async def ingest_data(
        data: list[UploadFile] = File(default=None),
        datasetName: str | None = Form(default=None),
        datasetId: Union[UUID, Literal[""], None] = Form(default=None, examples=[""]),
        graph_scope: list[str] | None = Form(default=[""], examples=[[""]]),
        incremental_loading: bool = Form(default=True),
        user: "User" = Depends(_auth()),
    ):
        """
        Ingest files into a dataset for knowledge graph construction.

        Accepts file uploads, HTTP URLs, or GitHub repository URLs.
        Content is processed, analyzed, and integrated into the graph.

        Args:
            data: Files to upload (can include URLs if enabled).
            datasetName: Target dataset name (creates if new).
            datasetId: Existing dataset UUID (mutually exclusive with name).
            graph_scope: Node identifiers for graph organization.

        Returns:
            Pipeline execution details on success.

        Raises:
            ValueError: If neither datasetId nor datasetName provided.
            HTTPException 409: On processing errors.
        """
        _track_add_event(user.id, graph_scope)

        # Validate required parameters
        if not datasetId and not datasetName:
            raise ValueError("Either datasetId or datasetName must be provided.")

        # Normalize empty graph_scope
        effective_nodes = graph_scope if graph_scope != [""] else None

        from m_flow.api.v1.add import add as add_impl
        from m_flow.pipeline.models import RunFailed

        try:
            result = await add_impl(
                data,
                datasetName,
                user=user,
                dataset_id=datasetId,
                graph_scope=effective_nodes,
                incremental_loading=incremental_loading,
            )
            if isinstance(result, RunFailed):
                return JSONResponse(status_code=420, content=result.model_dump(mode="json"))
            return result.model_dump()
        except Exception as err:
            return JSONResponse(status_code=409, content={"error": str(err)})

    return router
