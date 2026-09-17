"""
Update Data Router

REST API endpoint for replacing existing data items in M-flow.
Handles file uploads and triggers knowledge graph reprocessing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from m_flow.shared.logging_utils import get_logger

if TYPE_CHECKING:
    from m_flow.auth.models import User

_log = get_logger()


# ---------------------------------------------------------------------------
# Telemetry Helper
# ---------------------------------------------------------------------------


def _track_update(user_id: UUID, ds_id: UUID, data_id: UUID, nodes: list[str] | None) -> None:
    """Emit telemetry for update endpoint invocation."""
    from m_flow import __version__ as ver
    from m_flow.shared.utils import send_telemetry

    send_telemetry(
        "Update API Endpoint Invoked",
        user_id,
        additional_properties={
            "endpoint": "PATCH /v1/update",
            "dataset_id": str(ds_id),
            "data_id": str(data_id),
            "graph_scope": str(nodes),
            "m_flow_version": ver,
        },
    )


# ---------------------------------------------------------------------------
# Auth Dependency
# ---------------------------------------------------------------------------


def _auth():
    """Return authentication dependency."""
    from m_flow.auth.methods import get_authenticated_user

    return get_authenticated_user


# ---------------------------------------------------------------------------
# Router Factory
# ---------------------------------------------------------------------------


def get_update_router() -> APIRouter:
    """
    Construct the data update API router.

    Provides PATCH / endpoint for replacing existing data items
    with new content and reprocessing the knowledge graph.
    """
    router = APIRouter()

    @router.patch("", response_model=None)
    async def replace_data_item(
        data_id: UUID,
        dataset_id: UUID,
        data: list[UploadFile] = File(default=None),
        graph_scope: list[str] | None = Form(default=[""], examples=[[""]]),
        user: "User" = Depends(_auth()),
    ):
        """
        Replace an existing data item with new content.

        Removes the existing document, ingests the replacement,
        and reprocesses affected graph segments.

        Args:
            data_id: Identifier of the item to replace.
            dataset_id: Target dataset UUID.
            data: Replacement files to upload.
            graph_scope: Node identifiers for organization.

        Returns:
            Pipeline execution details or error response.
        """
        _track_update(user.id, dataset_id, data_id, graph_scope)

        # Normalize empty graph_scope
        effective_nodes = graph_scope if graph_scope and graph_scope != [""] else None

        from m_flow.api.v1.update import update as update_impl
        from m_flow.pipeline.models.RunEvent import RunFailed

        try:
            result = await update_impl(
                data_id=data_id,
                data=data,
                dataset_id=dataset_id,
                user=user,
                graph_scope=effective_nodes,
            )

            # Check for pipeline errors
            if any(isinstance(v, RunFailed) for v in result.values()):
                return JSONResponse(status_code=420, content=jsonable_encoder(result))
            return result

        except Exception as err:
            _log.error("Error during data update: %s", err)
            return JSONResponse(status_code=409, content={"error": str(err)})

    return router
