"""
Delete Router Factory
=====================

Creates the FastAPI router for data deletion endpoints.
"""

from __future__ import annotations

from typing import Dict, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import JSONResponse

from m_flow.shared.logging_utils import get_logger
from m_flow.auth.models import User
from m_flow.auth.methods import get_authenticated_user
from m_flow.shared.utils import send_telemetry
from m_flow import __version__ as m_flow_version

_logger = get_logger()


def get_delete_router() -> APIRouter:
    """
    Build and return the deletion API router.

    Returns
    -------
    APIRouter
        FastAPI router with delete endpoints.
    """
    router = APIRouter()

    @router.delete("", response_model=None)
    async def delete_data(
        data_id: UUID,
        dataset_id: UUID,
        mode: str = "soft",
        user: User = Depends(get_authenticated_user),
    ):
        """
        Remove data from a dataset.

        Parameters
        ----------
        data_id : UUID
            Identifier of the data to remove.
        dataset_id : UUID
            Identifier of the containing dataset.
        mode : str
            Deletion mode:
            - "soft": Remove data association only
            - "hard": Also remove orphaned entity nodes
        user : User
            Authenticated user making the request.

        Returns
        -------
        JSONResponse
            Success or error response.
        """
        # Track API usage
        send_telemetry(
            "Delete API Endpoint Invoked",
            user.id,
            additional_properties={
                "endpoint": "DELETE /v1/delete",
                "dataset_id": str(dataset_id),
                "data_id": str(data_id),
                "m_flow_version": m_flow_version,
            },
        )

        try:
            from m_flow.api.v1.delete import delete as perform_delete

            result = await perform_delete(
                data_id=data_id,
                dataset_id=dataset_id,
                mode=mode,
                user=user,
            )
            return result

        except Exception as err:
            _logger.error(f"Deletion failed for data_id={data_id}: {err}")
            return JSONResponse(
                status_code=409,
                content={"error": str(err)},
            )

    # === Node-level deletion endpoints ===

    @router.get("/node/{node_id}/preview", response_model=None)
    async def preview_node_deletion(
        node_id: str = Path(..., description="Node ID to preview deletion"),
        dataset_id: UUID = Query(..., description="Dataset UUID"),
        user: User = Depends(get_authenticated_user),
    ) -> Dict:
        """
        Preview the impact of node deletion.

        Returns node info, edges to be disconnected, associated node types, etc.
        Does not perform actual deletion.
        """
        from m_flow.api.v1.delete.node_deletion import preview_deletion

        return await preview_deletion(node_id, dataset_id, user)

    @router.delete("/node/{node_id}", response_model=None)
    async def delete_single_node(
        node_id: str = Path(..., description="Node ID to delete"),
        dataset_id: UUID = Query(..., description="Dataset UUID"),
        cascade: bool = Query(
            default=False,
            description="Hard mode: cascade delete orphan nodes",
        ),
        user: User = Depends(get_authenticated_user),
    ) -> Dict:
        """
        Delete a single graph node.

        Uses DETACH DELETE to remove node and its associated edges.
        Does not automatically delete associated neighbor nodes (unless cascade=true).

        - **node_id**: ID of the node to delete.
        - **dataset_id**: Dataset ID (used for permission verification).
        - **cascade**: Whether to cascade delete nodes that become orphaned.
        """
        send_telemetry(
            "Delete Node API Endpoint Invoked",
            user.id,
            additional_properties={
                "endpoint": "DELETE /v1/delete/node/{node_id}",
                "dataset_id": str(dataset_id),
                "node_id": node_id,
                "cascade": cascade,
                "m_flow_version": m_flow_version,
            },
        )

        from m_flow.api.v1.delete.node_deletion import delete_node_by_id

        return await delete_node_by_id(node_id, dataset_id, cascade=cascade, user=user)

    @router.delete("/episode/{episode_id}", response_model=None)
    async def delete_episode_node(
        episode_id: str = Path(..., description="Episode ID to delete"),
        dataset_id: UUID = Query(..., description="Dataset UUID"),
        mode: Literal["soft", "hard"] = Query(
            default="soft",
            description="Deletion mode: 'soft' (default) or 'hard' (cascade cleanup)",
        ),
        user: User = Depends(get_authenticated_user),
    ) -> Dict:
        """
        Delete Episode node.

        Note: Deleting Episode does not automatically delete associated Facet/Entity
        (they may be shared by other Episodes).

        - **soft mode**: Only deletes the Episode node itself.
        - **hard mode**: Cleans up orphaned Facets after deletion.
        """
        send_telemetry(
            "Delete Episode API Endpoint Invoked",
            user.id,
            additional_properties={
                "endpoint": "DELETE /v1/delete/episode/{episode_id}",
                "dataset_id": str(dataset_id),
                "episode_id": episode_id,
                "mode": mode,
                "m_flow_version": m_flow_version,
            },
        )

        from m_flow.api.v1.delete.node_deletion import delete_episode

        return await delete_episode(episode_id, dataset_id, mode=mode, user=user)

    return router
