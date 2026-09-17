# m_flow/api/v1/manual/routers/get_manual_router.py
"""
Manual Ingestion Router

REST API endpoints for manual episodic memory ingestion and node updates.
Allows users to bypass LLM extraction and directly specify graph node contents.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from m_flow.shared.logging_utils import get_logger

if TYPE_CHECKING:
    from m_flow.auth.models import User

_log = get_logger("manual_router")


# ---------------------------------------------------------------------------
# Auth Dependency
# ---------------------------------------------------------------------------


def _get_auth_dependency():
    """Return authentication dependency."""
    from m_flow.auth.methods import get_authenticated_user

    return get_authenticated_user


# ---------------------------------------------------------------------------
# Telemetry Helpers
# ---------------------------------------------------------------------------


def _track_manual_ingest(user_id: UUID, episode_count: int) -> None:
    """Emit telemetry for manual ingest endpoint."""
    from m_flow import __version__ as ver
    from m_flow.shared.utils import send_telemetry

    send_telemetry(
        "Manual Ingest API Endpoint Invoked",
        user_id,
        additional_properties={
            "endpoint": "POST /v1/manual/ingest",
            "episode_count": episode_count,
            "m_flow_version": ver,
        },
    )


def _track_patch_node(user_id: UUID, node_id: UUID, node_type: str) -> None:
    """Emit telemetry for patch node endpoint."""
    from m_flow import __version__ as ver
    from m_flow.shared.utils import send_telemetry

    send_telemetry(
        "Patch Node API Endpoint Invoked",
        user_id,
        additional_properties={
            "endpoint": "PATCH /v1/manual/node",
            "node_id": str(node_id),
            "node_type": node_type,
            "m_flow_version": ver,
        },
    )


# ---------------------------------------------------------------------------
# Router Factory
# ---------------------------------------------------------------------------


def get_manual_router() -> APIRouter:
    """
    Construct the manual ingestion API router.

    Provides endpoints for:
    - POST /ingest: Manual episodic memory ingestion
    - PATCH /node: Update node display_only field
    - GET /schema: Get input schema documentation
    """
    router = APIRouter()

    # =========================================================================
    # POST /ingest - Manual Episodic Memory Ingestion
    # =========================================================================

    @router.post("/ingest", response_model=None)
    async def ingest_manual_episodes(
        request: "ManualIngestRequest",
        user: "User" = Depends(_get_auth_dependency()),
    ):
        """
        Manually ingest episodic memory structures.

        Bypasses the LLM extraction pipeline. Users directly specify
        Episode, Facet, FacetPoint, and Entity contents, which are then
        embedded and stored in the graph and vector databases.

        Request Body:
            - episodes: List of episode definitions with facets and entities
            - dataset_name: Target dataset (default: "main_dataset")
            - embed_triplets: Whether to create triplet embeddings

        Returns:
            ManualIngestResult with counts of created nodes.

        Example Request:
        ```json
        {
            "episodes": [
                {
                    "name": "Project Meeting 2026-02-23",
                    "summary": "Discussed Q1 product roadmap and technical solutions...",
                    "facets": [
                        {
                            "facet_type": "decision",
                            "search_text": "Adopt microservices architecture",
                            "description": "Decided to adopt microservices for horizontal scaling"
                        }
                    ],
                    "entities": [
                        {
                            "name": "John",
                            "description": "Tech Lead, leading architecture design"
                        }
                    ]
                }
            ],
            "dataset_name": "project_docs"
        }
        ```
        """
        from m_flow.api.v1.manual import manual_ingest

        _track_manual_ingest(user.id, len(request.episodes))

        try:
            result = await manual_ingest(request, user=user)

            if not result.success:
                return JSONResponse(
                    status_code=422,
                    content=result.model_dump(),
                )

            return result.model_dump()

        except Exception as err:
            _log.error(f"[manual_ingest] Error: {err}")
            return JSONResponse(
                status_code=500,
                content={"error": str(err)},
            )

    # =========================================================================
    # PATCH /node - Update Node Fields
    # =========================================================================

    @router.patch("/node", response_model=None)
    async def patch_node_fields(
        request: "PatchNodeRequest",
        user: "User" = Depends(_get_auth_dependency()),
    ):
        """
        Update specific fields of an existing graph node.

        Currently supports updating the display_only field, which is
        shown when a node is retrieved but does NOT affect search ranking.

        Request Body:
            - node_id: UUID of the node to update
            - node_type: Type of node (Episode/Facet/FacetPoint/Entity)
            - display_only: New value (set to "" to clear)

        Returns:
            PatchNodeResult indicating success or failure.

        Example Request:
        ```json
        {
            "node_id": "550e8400-e29b-41d4-a716-446655440000",
            "node_type": "Episode",
            "display_only": "Important meeting notes, needs legal review"
        }
        ```
        """
        from m_flow.api.v1.manual import patch_node

        _track_patch_node(user.id, request.node_id, request.node_type)

        try:
            result = await patch_node(request, user=user)

            if not result.success:
                return JSONResponse(
                    status_code=404 if "not found" in (result.message or "").lower() else 422,
                    content=result.model_dump(),
                )

            return result.model_dump()

        except Exception as err:
            _log.error(f"[patch_node] Error: {err}")
            return JSONResponse(
                status_code=500,
                content={"error": str(err)},
            )

    # =========================================================================
    # GET /schema - Input Schema Documentation
    # =========================================================================

    @router.get("/schema", response_model=None)
    async def get_input_schema():
        """
        Get the JSON schema for manual ingestion input models.

        Returns the Pydantic model schemas for:
        - ManualEpisodeInput
        - ManualFacetInput
        - ManualFacetPointInput
        - ManualConceptInput

        Useful for building client-side forms or validation.
        """
        from m_flow.api.v1.manual.models import (
            ManualEpisodeInput,
            ManualFacetInput,
            ManualFacetPointInput,
            ManualConceptInput,
            ManualIngestRequest,
            PatchNodeRequest,
        )

        return {
            "ManualIngestRequest": ManualIngestRequest.model_json_schema(),
            "ManualEpisodeInput": ManualEpisodeInput.model_json_schema(),
            "ManualFacetInput": ManualFacetInput.model_json_schema(),
            "ManualFacetPointInput": ManualFacetPointInput.model_json_schema(),
            "ManualConceptInput": ManualConceptInput.model_json_schema(),
            "PatchNodeRequest": PatchNodeRequest.model_json_schema(),
        }

    return router


# Import models for type hints
from m_flow.api.v1.manual.models import (
    ManualIngestRequest,
    PatchNodeRequest,
)
