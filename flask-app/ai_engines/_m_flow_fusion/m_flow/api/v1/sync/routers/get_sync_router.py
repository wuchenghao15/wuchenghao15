"""
Cloud sync API router.

Endpoints for syncing data to M-flow Cloud.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from m_flow import __version__ as m_flow_version
from m_flow.api.DTO import InDTO
from m_flow.api.v1.sync import SyncResponse
from m_flow.auth.methods import get_authenticated_user
from m_flow.auth.models import User
from m_flow.auth.permissions.methods import get_specific_user_permission_datasets
from m_flow.shared.logging_utils import get_logger
from m_flow.shared.sync.methods import get_running_sync_operations_for_user
from m_flow.shared.utils import send_telemetry, to_iso_z

_log = get_logger()


class SyncRequest(InDTO):
    """Payload for initiating sync."""

    dataset_ids: Optional[list[UUID]] = None


def get_sync_router() -> APIRouter:
    """Build the sync API router."""
    router = APIRouter()

    @router.post("")
    async def sync_to_cloud(
        request: SyncRequest,
        user: User = Depends(get_authenticated_user),
    ):
        """
        Start cloud synchronization for selected datasets.

        If dataset_ids is omitted, syncs all user datasets.
        Returns immediately; sync runs in background.
        """
        send_telemetry(
            "Cloud Sync Triggered",
            user.id,
            additional_properties={
                "endpoint": "POST /v1/sync",
                "version": m_flow_version,
                "datasets": [str(d) for d in request.dataset_ids] if request.dataset_ids else "*",
            },
        )

        from m_flow.api.v1.sync import sync as run_sync

        try:
            # Reject if already syncing
            running = await get_running_sync_operations_for_user(user.id)
            if running:
                active = running[0]
                return JSONResponse(
                    status_code=409,
                    content={
                        "error": "Sync already running",
                        "details": {
                            "run_id": active.run_id,
                            "status": "already_running",
                            "dataset_ids": active.dataset_ids,
                            "dataset_names": active.dataset_names,
                            "progress_percentage": active.progress_percentage,
                            "timestamp": to_iso_z(active.created_at),
                            "message": f"Active sync: {active.run_id}. Wait for completion.",
                        },
                    },
                )

            # Resolve authorized datasets
            datasets = await get_specific_user_permission_datasets(
                user.id,
                "write",
                request.dataset_ids,
            )

            result = await run_sync(datasets=datasets, user=user)
            return result

        except ValueError as ve:
            return JSONResponse(status_code=400, content={"error": str(ve)})
        except PermissionError as pe:
            return JSONResponse(status_code=403, content={"error": str(pe)})
        except ConnectionError as ce:
            return JSONResponse(status_code=409, content={"error": f"Cloud unavailable: {ce}"})
        except Exception as exc:
            _log.error("Sync failed: %s", exc)
            return JSONResponse(status_code=409, content={"error": "Sync failed"})

    @router.get("/status")
    async def get_sync_status_overview(
        user: User = Depends(get_authenticated_user),
    ):
        """
        Check for running sync operations.

        Returns count and details of any active syncs.
        """
        send_telemetry(
            "Sync Status Check",
            user.id,
            additional_properties={
                "endpoint": "GET /v1/sync/status",
                "version": m_flow_version,
            },
        )

        try:
            running = await get_running_sync_operations_for_user(user.id)
            resp = {
                "has_running_sync": len(running) > 0,
                "running_sync_count": len(running),
            }

            if running:
                latest = running[0]
                resp["latest_running_sync"] = {
                    "run_id": latest.run_id,
                    "dataset_ids": latest.dataset_ids,
                    "dataset_names": latest.dataset_names,
                    "progress_percentage": latest.progress_percentage,
                    "created_at": to_iso_z(latest.created_at),
                }
            return resp

        except Exception as exc:
            _log.error("Status check failed: %s", exc)
            return JSONResponse(status_code=500, content={"error": "Status unavailable"})

    return router
