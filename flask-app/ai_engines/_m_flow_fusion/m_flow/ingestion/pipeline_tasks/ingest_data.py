"""
Data Ingestion Pipeline Task

Orchestrates the ingestion of data items into M-flow datasets.
Handles file processing, metadata extraction, deduplication,
and database persistence.
"""

from __future__ import annotations

import inspect
import json
from typing import TYPE_CHECKING, Any, BinaryIO
from uuid import UUID

import m_flow.ingestion.core as ingestion
from m_flow.adapters.relational import get_db_adapter
from m_flow.data.models import Data
from m_flow.ingestion.core.exceptions import IngestionError

from .data_item_to_text_file import data_item_to_text_file
from .save_data_item_to_storage import save_data_item_to_storage

if TYPE_CHECKING:
    from m_flow.auth.models import User


# ---------------------------------------------------------------------------
# Metadata Extraction
# ---------------------------------------------------------------------------


def _extract_external_meta(item: BinaryIO | str | Any) -> dict[str, Any]:
    """
    Extract external metadata from a data item if available.

    Checks for a .dict() method (Pydantic-style) and captures
    the item's type information.
    """
    dict_method = getattr(item, "dict", None)
    if dict_method is not None and inspect.ismethod(dict_method):
        return {"metadata": item.dict(), "origin": str(type(item))}
    return {}


# ---------------------------------------------------------------------------
# Dataset Resolution
# ---------------------------------------------------------------------------


async def _resolve_target_dataset(
    ds_name: str,
    ds_id: UUID | None,
    user: "User",
):
    """
    Resolve the target dataset by ID or name.

    If ds_id is provided, fetches that specific dataset.
    Otherwise, finds or creates a dataset by name.
    """
    from m_flow.auth.permissions.methods import get_specific_user_permission_datasets
    from m_flow.data.methods import (
        get_authorized_existing_datasets,
        load_or_create_datasets,
    )

    if ds_id:
        result = await get_specific_user_permission_datasets(user.id, "write", [ds_id])
        return result[0] if isinstance(result, list) else result

    existing = await get_authorized_existing_datasets(
        user=user,
        permission_type="write",
        datasets=[ds_name],
    )
    result = await load_or_create_datasets(
        dataset_names=[ds_name],
        existing_datasets=existing,
        user=user,
    )
    return result[0] if isinstance(result, list) else result


# ---------------------------------------------------------------------------
# File Processing
# ---------------------------------------------------------------------------


async def _process_single_item(
    item: Any,
    loaders: dict[str, dict[str, Any]] | None,
    user: "User",
    node_labels: list[str] | None,
    existing_ids: set[str],
    created_at_ms: int | None = None,
) -> tuple[Data | None, str]:
    """
    Process a single data item: store, convert, extract metadata, create Data record.

    Args:
        item: Data item to process.
        loaders: Loader configurations.
        user: Authenticated user.
        node_labels: Node labels for graph.
        existing_ids: Set of existing data IDs.
        created_at_ms: Optional timestamp in milliseconds for historical data.

    Returns:
        Tuple of (Data instance or None, status: 'new'|'update'|'skip')
    """
    from sqlalchemy import select

    from m_flow.shared.files.utils.get_data_file_path import get_data_file_path
    from m_flow.shared.files.utils.open_data_file import open_data_file

    # Save raw item to storage
    orig_path = await save_data_item_to_storage(item)
    actual_path = get_data_file_path(orig_path)

    # Convert to text file
    storage_path, loader = await data_item_to_text_file(actual_path, loaders)
    if loader is None:
        raise IngestionError("Loader cannot be None")

    # Extract original file metadata
    async with open_data_file(orig_path) as f:
        classified = ingestion.classify(f)
        data_id = await ingestion.identify(classified, user)
        orig_meta = classified.get_metadata()

    # Extract storage file metadata
    async with open_data_file(storage_path) as f:
        classified = ingestion.classify(f)
        store_meta = classified.get_metadata()

    # Build external metadata
    ext_meta = _extract_external_meta(item)
    if node_labels:
        ext_meta["graph_scope"] = node_labels

    # Check for existing record and update if found
    db = get_db_adapter()
    async with db.get_async_session() as sess:
        existing = (await sess.execute(select(Data).filter(Data.id == data_id))).scalar_one_or_none()

        if existing is not None:
            # Update existing record within the same session to avoid detached object issues
            existing.name = orig_meta["name"]
            existing.processed_path = storage_path
            existing.source_path = orig_meta["file_path"]
            existing.extension = store_meta["extension"]
            existing.mime_type = store_meta["mime_type"]
            existing.original_extension = orig_meta["extension"]
            existing.original_mime_type = orig_meta["mime_type"]
            existing.parser_name = loader.loader_name
            existing.owner_id = user.id
            existing.content_hash = orig_meta["content_hash"]
            existing.source_digest = store_meta["content_hash"]
            existing.data_size = orig_meta["file_size"]
            existing.external_metadata = ext_meta
            existing.graph_scope = json.dumps(node_labels) if node_labels else None
            existing.tenant_id = user.tenant_id or None

            # Merge and expunge to get a detached but updated object
            merged = await sess.merge(existing)
            await sess.commit()
            # Refresh to ensure all attributes are loaded before detaching
            await sess.refresh(merged)

            status = "update" if str(merged.id) in existing_ids else "new_to_dataset"
            return merged, status

    # Skip if already in dataset
    if str(data_id) in existing_ids:
        return None, "skip"

    # Create new record
    record = Data(
        id=data_id,
        name=orig_meta["name"],
        processed_path=storage_path,
        source_path=orig_meta["file_path"],
        extension=store_meta["extension"],
        mime_type=store_meta["mime_type"],
        original_extension=orig_meta["extension"],
        original_mime_type=orig_meta["mime_type"],
        parser_name=loader.loader_name,
        owner_id=user.id,
        content_hash=orig_meta["content_hash"],
        source_digest=store_meta["content_hash"],
        external_metadata=ext_meta,
        graph_scope=json.dumps(node_labels) if node_labels else None,
        data_size=orig_meta["file_size"],
        tenant_id=user.tenant_id or None,
        workflow_state={},
        token_count=-1,
    )

    # Set created_at from user-provided timestamp (for historical data import)
    if created_at_ms is not None:
        from datetime import datetime, timezone

        record.created_at = datetime.fromtimestamp(created_at_ms / 1000, tz=timezone.utc)

    return record, "new"


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------


async def ingest_data(
    data: Any,
    dataset_name: str,
    user: "User",
    graph_scope: list[str] | None = None,
    dataset_id: UUID | None = None,
    preferred_loaders: dict[str, dict[str, Any]] | None = None,
    created_at_ms: int | None = None,
) -> list[Data]:
    """
    Ingest data items into a dataset.

    Processes each item, extracts metadata, handles deduplication,
    and persists to the database.

    Args:
        data: Single item or list of items to ingest.
        dataset_name: Target dataset name.
        user: Owner/authenticated user.
        graph_scope: Optional node labels for graph organization.
        dataset_id: Specific dataset UUID (overrides name).
        preferred_loaders: Loader configurations by file type.
        created_at_ms: Optional timestamp in milliseconds for historical data.
            When provided, sets Data.created_at to this value instead of
            the current system time.

    Returns:
        List of Data records created or updated.
    """
    from m_flow.auth.methods import get_seed_user
    from m_flow.data.methods import fetch_dataset_items

    if not user:
        user = await get_seed_user()

    # Ensure data is a list
    items = data if isinstance(data, list) else [data]

    # Resolve target dataset
    dataset = await _resolve_target_dataset(dataset_name, dataset_id, user)

    # Build existing data map
    current_data: list[Data] = await fetch_dataset_items(dataset.id)
    existing_ids = {str(d.id) for d in current_data}

    # Process each item
    new_records: list[Data] = []
    updated_records: list[Data] = []
    dataset_additions: list[Data] = []

    for item in items:
        record, status = await _process_single_item(
            item, preferred_loaders, user, graph_scope, existing_ids, created_at_ms
        )

        if record is None:
            continue

        existing_ids.add(str(record.id))

        if status == "new":
            new_records.append(record)
        elif status == "update":
            updated_records.append(record)
        elif status == "new_to_dataset":
            dataset_additions.append(record)

    # Persist changes
    db = get_db_adapter()
    async with db.get_async_session() as sess:
        # Re-attach dataset to this session
        dataset = await sess.merge(dataset)

        if new_records:
            dataset.data.extend(new_records)

        # Note: updated_records have already been committed in _process_single_item
        # We only need to ensure dataset associations are correct
        for rec in updated_records:
            # Re-attach to session and ensure dataset association
            rec = await sess.merge(rec)

        if dataset_additions:
            dataset.data.extend(dataset_additions)

        await sess.commit()

    return updated_records + dataset_additions + new_records
