"""
Dataset Management Router

Provides REST API endpoints for managing datasets, including CRUD operations,
graph visualization, data item management, and processing status queries.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from typing_extensions import Annotated

from m_flow.api.DTO import InDTO, OutDTO
from m_flow.api.v1.exceptions import DataNotFoundError, DatasetNotFoundError
from m_flow.shared.logging_utils import get_logger

if TYPE_CHECKING:
    from m_flow.auth.models import User

_logger = get_logger()

# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------


class _ErrMsg(BaseModel):
    """Error response payload."""

    message: str


class DatasetDTO(OutDTO):
    """Dataset metadata response."""

    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime | None = None
    owner_id: UUID


class DatasetWithCountsDTO(OutDTO):
    """Dataset metadata with data item counts."""

    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime | None = None
    owner_id: UUID
    data_count: int = 0


class DataDTO(OutDTO):
    """Data item metadata response."""

    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime | None = None
    extension: str
    mime_type: str
    processed_path: str
    dataset_id: UUID
    data_size: int | None = None
    token_count: int | None = None
    workflow_state: dict | None = None


class GraphNodeDTO(OutDTO):
    """Knowledge graph node."""

    id: UUID
    label: str
    properties: dict


class GraphEdgeDTO(OutDTO):
    """Knowledge graph edge."""

    source: UUID
    target: UUID
    relationship: str


class GraphDTO(OutDTO):
    """Complete knowledge graph structure."""

    nodes: list[GraphNodeDTO]
    edges: list[GraphEdgeDTO]


class DatasetCreationPayload(InDTO):
    """Request body for dataset creation."""

    name: str = Field(..., min_length=1, max_length=255)


# ---------------------------------------------------------------------------
# Telemetry Helper
# ---------------------------------------------------------------------------


def _emit_telemetry(endpoint_desc: str, user_id: UUID, **extra) -> None:
    """Send telemetry event for API endpoint invocation."""
    from m_flow import __version__ as mflow_ver
    from m_flow.shared.utils import send_telemetry

    props = {"endpoint": endpoint_desc, "m_flow_version": mflow_ver, **extra}
    send_telemetry("Datasets API Endpoint Invoked", user_id, additional_properties=props)


# ---------------------------------------------------------------------------
# Authorization Helpers
# ---------------------------------------------------------------------------


async def _require_dataset_access(
    dataset_ids: list[UUID],
    permission: str,
    user: "User",
) -> list:
    """
    Verify user has specified permission on datasets.

    Raises DatasetNotFoundError if no datasets found with required permission.
    """
    from m_flow.data.methods import get_authorized_existing_datasets

    result = await get_authorized_existing_datasets(dataset_ids, permission, user)
    if not result:
        raise DatasetNotFoundError(message=f"Dataset(s) not found or access denied: {dataset_ids}")
    return result


# ---------------------------------------------------------------------------
# Route Handlers
# ---------------------------------------------------------------------------


def _register_list_datasets(router: APIRouter) -> None:
    """Register GET / endpoint for listing datasets."""

    @router.get("", response_model=list[DatasetDTO] | list[DatasetWithCountsDTO])
    async def list_datasets(
        with_counts: bool = Query(default=False, description="Include data item counts for each dataset"),
        user: "User" = Depends(_get_auth_user()),
    ):
        """
        List all datasets accessible to the authenticated user.

        Returns datasets where user has read permission, including
        metadata like ID, name, timestamps, and owner information.

        If with_counts=true, also includes the number of data items in each dataset.
        """
        _emit_telemetry("GET /v1/datasets", user.id, with_counts=with_counts)

        from m_flow.auth.permissions.methods import get_all_user_permission_datasets

        try:
            datasets = await get_all_user_permission_datasets(user, "read")

            if not with_counts:
                return datasets

            # Add counts for each dataset
            from m_flow.data.methods import fetch_dataset_items

            result = []
            for ds in datasets:
                items = await fetch_dataset_items(dataset_id=ds.id)
                count = len(items) if items else 0
                result.append(
                    DatasetWithCountsDTO(
                        id=ds.id,
                        name=ds.name,
                        created_at=ds.created_at,
                        updated_at=ds.updated_at,
                        owner_id=ds.owner_id,
                        data_count=count,
                    )
                )
            return result

        except Exception as err:
            _logger.error("Error listing datasets: %s", err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving datasets: {err}",
            ) from err


def _register_create_dataset(router: APIRouter) -> None:
    """Register POST / endpoint for dataset creation."""

    @router.post("", response_model=DatasetDTO)
    async def create_dataset_endpoint(
        payload: DatasetCreationPayload,
        user: "User" = Depends(_get_auth_user()),
    ):
        """
        Create a new dataset or return existing with matching name.

        User automatically receives full permissions (read/write/share/delete)
        on newly created datasets.
        """
        _emit_telemetry("POST /v1/datasets", user.id)

        from m_flow.adapters.relational import get_db_adapter
        from m_flow.auth.permissions.methods import give_permission_on_dataset
        from m_flow.data.methods import create_dataset, get_datasets_by_name

        try:
            # Check for existing dataset with same name
            existing = await get_datasets_by_name([payload.name], user.id)
            if existing:
                return existing[0]

            # Create new dataset
            engine = get_db_adapter()
            async with engine.get_async_session() as session:
                new_dataset = await create_dataset(
                    dataset_name=payload.name,
                    user=user,
                    session=session,
                )
                # Grant full permissions
                for perm in ("read", "write", "share", "delete"):
                    await give_permission_on_dataset(user, new_dataset.id, perm)
                return new_dataset
        except Exception as err:
            _logger.error("Error creating dataset: %s", err)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating dataset: {err}",
            ) from err


def _register_get_dataset(router: APIRouter) -> None:
    """Register GET /{dataset_id} endpoint for single dataset retrieval."""

    @router.get(
        "/{dataset_id}",
        response_model=DatasetWithCountsDTO,
        responses={404: {"model": _ErrMsg}},
    )
    async def get_dataset(
        dataset_id: UUID,
        user: "User" = Depends(_get_auth_user()),
    ):
        """
        Retrieve a single dataset by ID.

        Returns dataset metadata including data item count.
        Requires read permission on the target dataset.
        """
        _emit_telemetry(
            f"GET /v1/datasets/{dataset_id}",
            user.id,
            dataset_id=str(dataset_id),
        )

        from m_flow.data.methods import fetch_dataset_items

        datasets = await _require_dataset_access([dataset_id], "read", user)
        ds = datasets[0]

        # Get data count
        items = await fetch_dataset_items(dataset_id=ds.id)
        count = len(items) if items else 0

        return DatasetWithCountsDTO(
            id=ds.id,
            name=ds.name,
            created_at=ds.created_at,
            updated_at=ds.updated_at,
            owner_id=ds.owner_id,
            data_count=count,
        )


def _register_delete_dataset(router: APIRouter) -> None:
    """Register DELETE /{dataset_id} endpoint."""

    @router.delete(
        "/{dataset_id}",
        response_model=None,
        responses={404: {"model": _ErrMsg}},
    )
    async def remove_dataset(
        dataset_id: UUID,
        user: "User" = Depends(_get_auth_user()),
    ):
        """
        Permanently delete a dataset and all associated data.

        Requires delete permission on the target dataset.
        """
        _emit_telemetry(
            f"DELETE /v1/datasets/{dataset_id}",
            user.id,
            dataset_id=str(dataset_id),
        )

        from m_flow.data.methods import delete_dataset

        datasets = await _require_dataset_access([dataset_id], "delete", user)
        await delete_dataset(datasets[0])


def _register_delete_data_item(router: APIRouter) -> None:
    """Register DELETE /{dataset_id}/data/{data_id} endpoint."""

    @router.delete(
        "/{dataset_id}/data/{data_id}",
        response_model=None,
        responses={404: {"model": _ErrMsg}},
    )
    async def remove_data_item(
        dataset_id: UUID,
        data_id: UUID,
        user: "User" = Depends(_get_auth_user()),
    ):
        """
        Remove a specific data item from a dataset.

        Dataset remains intact; only the specified item is deleted.
        """
        _emit_telemetry(
            f"DELETE /v1/datasets/{dataset_id}/data/{data_id}",
            user.id,
            dataset_id=str(dataset_id),
            data_id=str(data_id),
        )

        from m_flow.data.methods import delete_data, get_data, get_dataset

        # Verify dataset access
        ds = await get_dataset(user.id, dataset_id)
        if ds is None:
            raise DatasetNotFoundError(message=f"Dataset ({dataset_id}) not found.")

        # Verify data item access
        item = await get_data(user.id, data_id)
        if item is None:
            raise DataNotFoundError(message=f"Data ({data_id}) not found.")

        await delete_data(item)


def _register_get_graph(router: APIRouter) -> None:
    """Register GET /{dataset_id}/graph endpoint."""

    @router.get("/{dataset_id}/graph", response_model=GraphDTO)
    async def fetch_dataset_graph(
        dataset_id: UUID,
        user: "User" = Depends(_get_auth_user()),
    ):
        """
        Retrieve knowledge graph visualization data for a dataset.

        Returns nodes and edges representing entity relationships
        extracted from the dataset content.
        """
        from m_flow.knowledge.graph_ops.methods import get_formatted_graph_data

        return await get_formatted_graph_data(dataset_id, user)


def _register_get_data_items(router: APIRouter) -> None:
    """Register GET /{dataset_id}/data endpoint."""

    @router.get(
        "/{dataset_id}/data",
        response_model=list[DataDTO],
        responses={404: {"model": _ErrMsg}},
    )
    async def fetch_data_items(
        dataset_id: UUID,
        user: "User" = Depends(_get_auth_user()),
    ):
        """
        List all data items belonging to a dataset.

        Returns metadata for each item including file type,
        storage location, and timestamps.
        """
        _emit_telemetry(
            f"GET /v1/datasets/{dataset_id}/data",
            user.id,
            dataset_id=str(dataset_id),
        )

        from m_flow.data.methods import get_authorized_existing_datasets, fetch_dataset_items

        ds_list = await get_authorized_existing_datasets([dataset_id], "read", user)
        if not ds_list:
            return JSONResponse(
                status_code=404,
                content={"message": f"Dataset ({dataset_id}) not found."},
            )

        ds_id = ds_list[0].id
        items = await fetch_dataset_items(dataset_id=ds_id)
        if not items:
            return []

        return [{**jsonable_encoder(item), "dataset_id": ds_id} for item in items]


def _register_get_status(router: APIRouter) -> None:
    """Register GET /status endpoint."""

    @router.get("/status")
    async def fetch_processing_status(
        datasets: Annotated[list[UUID], Query(alias="dataset")] = [],
        user: "User" = Depends(_get_auth_user()),
    ):
        """
        Query processing status for specified datasets.

        Returns a mapping of dataset IDs to their current pipeline
        status (pending/running/completed/failed).
        """
        _emit_telemetry(
            "GET /v1/datasets/status",
            user.id,
            datasets=[str(d) for d in datasets],
        )

        from m_flow.api.v1.datasets.datasets import datasets as ds_module
        from m_flow.data.methods import get_authorized_existing_datasets

        try:
            authorized = await get_authorized_existing_datasets(datasets, "read", user)
            return await ds_module.get_status([d.id for d in authorized])
        except Exception as err:
            return JSONResponse(status_code=409, content={"error": str(err)})


def _register_get_raw_file(router: APIRouter) -> None:
    """Register GET /{dataset_id}/data/{data_id}/raw endpoint."""

    @router.get(
        "/{dataset_id}/data/{data_id}/raw",
        response_class=FileResponse,
    )
    async def download_raw_data(
        dataset_id: UUID,
        data_id: UUID,
        user: "User" = Depends(_get_auth_user()),
    ):
        """
        Download the original unprocessed data file.

        Returns the raw file for a specific data item within a dataset.
        """
        _emit_telemetry(
            f"GET /v1/datasets/{dataset_id}/data/{data_id}/raw",
            user.id,
            dataset_id=str(dataset_id),
            data_id=str(data_id),
        )

        from m_flow.data.methods import (
            get_authorized_existing_datasets,
            get_data,
            fetch_dataset_items,
        )

        # Verify dataset access
        ds_list = await get_authorized_existing_datasets([dataset_id], "read", user)
        if not ds_list:
            return JSONResponse(
                status_code=404,
                content={"detail": f"Dataset ({dataset_id}) not found."},
            )

        # Get data items for dataset
        items = await fetch_dataset_items(ds_list[0].id)
        if not items:
            raise DataNotFoundError(message=f"No data found in dataset ({dataset_id}).")

        # Find matching data item
        matches = [item for item in items if item.id == data_id]
        if not matches:
            raise DataNotFoundError(message=f"Data ({data_id}) not found in dataset ({dataset_id}).")

        # Fetch and return raw location
        data_obj = await get_data(user.id, data_id)
        if data_obj is None:
            raise DataNotFoundError(message=f"Data ({data_id}) not found in dataset ({dataset_id}).")

        raw_loc = data_obj.processed_path or ""
        raw_loc = raw_loc.removeprefix("file://")
        if not raw_loc or not os.path.exists(raw_loc):
            return JSONResponse(
                status_code=404,
                content={"detail": f"Raw file not found on disk: {data_obj.name}"},
            )
        return FileResponse(raw_loc, filename=f"{data_obj.name}.{data_obj.extension}")


# ---------------------------------------------------------------------------
# Dependency Helper
# ---------------------------------------------------------------------------


def _get_auth_user():
    """Return the authentication dependency."""
    from m_flow.auth.methods import get_authenticated_user

    return get_authenticated_user


# ---------------------------------------------------------------------------
# Router Factory
# ---------------------------------------------------------------------------


def get_datasets_router() -> APIRouter:
    """
    Construct and return the datasets API router.

    Registers all dataset-related endpoints including:
    - List/create/delete datasets
    - Get single dataset details
    - Manage data items within datasets
    - Knowledge graph visualization
    - Processing status queries
    - Raw data file downloads
    """
    router = APIRouter()

    _register_list_datasets(router)
    _register_create_dataset(router)
    _register_get_status(router)  # Must be before /{dataset_id} to avoid path conflict
    _register_get_dataset(router)
    _register_delete_dataset(router)
    _register_delete_data_item(router)
    _register_get_graph(router)
    _register_get_data_items(router)
    _register_get_raw_file(router)

    return router
