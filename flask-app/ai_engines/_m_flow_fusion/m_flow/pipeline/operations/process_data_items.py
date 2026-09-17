"""
Pipeline data item processor.

Runs tasks on individual data items with optional incremental mode.
"""

from __future__ import annotations

import os
from typing import Any, AsyncGenerator, Dict, List, Optional, Set
from uuid import UUID

from sqlalchemy import select

import m_flow.ingestion.core as ingestion
from m_flow.adapters.relational import get_db_adapter
from m_flow.auth.models import User
from m_flow.data.models import Data, Dataset
from m_flow.ingestion.pipeline_tasks import save_data_item_to_storage
from m_flow.pipeline.models.DataItemStatus import DataItemStatus
from m_flow.pipeline.models.RunEvent import (
    RunAlreadyCompleted,
    RunCompleted,
    RunFailed,
    RunYield,
)
from m_flow.pipeline.operations.execute_with_telemetry import execute_with_telemetry
from m_flow.shared.files.utils.open_data_file import open_data_file
from m_flow.shared.logging_utils import get_logger
from ..tasks import Stage

_log = get_logger("m_flow.pipeline.process_data_items")

_RAISE_ERRORS = os.getenv("RAISE_INCREMENTAL_LOADING_ERRORS", "true").lower() == "true"

_STATUS_CACHE: Dict[str, Set[UUID]] = {}


async def preload_processing_status(
    data_ids: List[UUID],
    workflow_name: str,
    dataset_id: UUID,
) -> None:
    """Batch-load workflow_state for *data_ids* into a module-level cache.

    Subsequent calls to :func:`_is_already_processed` will read from the
    cache instead of opening individual DB sessions, reducing round-trips
    from N to 1 per batch.
    """
    if not data_ids:
        return
    cache_key = f"{workflow_name}:{dataset_id}"
    engine = get_db_adapter()
    _SQL_IN_LIMIT = 500
    completed: Set[UUID] = set()
    for offset in range(0, len(data_ids), _SQL_IN_LIMIT):
        chunk = data_ids[offset : offset + _SQL_IN_LIMIT]
        async with engine.get_async_session() as session:
            rows = (await session.execute(select(Data.id, Data.workflow_state).where(Data.id.in_(chunk)))).all()
            for row in rows:
                ws = row.workflow_state or {}
                if ws.get(workflow_name, {}).get(str(dataset_id)) == DataItemStatus.DATA_ITEM_PROCESSING_COMPLETED:
                    completed.add(row.id)
    _STATUS_CACHE[cache_key] = completed


def clear_processing_status_cache() -> None:
    """Drop all cached processing statuses (call after pipeline run)."""
    _STATUS_CACHE.clear()


async def _resolve_data_id(item: Any, user: User):
    """Determine data ID for item."""
    if isinstance(item, Data):
        return item.id

    path = await save_data_item_to_storage(item)
    async with open_data_file(path) as f:
        return await ingestion.identify(ingestion.classify(f), user)


async def _is_already_processed(data_id, workflow_name: str, dataset_id) -> bool:
    """Check if item was already processed (uses batch cache when available)."""
    cache_key = f"{workflow_name}:{dataset_id}"
    if cache_key in _STATUS_CACHE:
        return data_id in _STATUS_CACHE[cache_key]

    engine = get_db_adapter()
    async with engine.get_async_session() as session:
        record = (await session.execute(select(Data).where(Data.id == data_id))).scalar_one_or_none()

        if not record:
            return False

        status_map = (record.workflow_state or {}).get(workflow_name, {})
        return status_map.get(str(dataset_id)) == DataItemStatus.DATA_ITEM_PROCESSING_COMPLETED


async def _mark_completed(data_id, workflow_name: str, dataset_id) -> None:
    """Mark item as processed."""
    engine = get_db_adapter()
    async with engine.get_async_session() as session:
        record = (await session.execute(select(Data).where(Data.id == data_id))).scalar_one_or_none()

        if record is None:
            _log.warning(f"Cannot mark completed: data record {data_id} not found")
            return

        ps = record.workflow_state.setdefault(workflow_name, {})
        ps[str(dataset_id)] = DataItemStatus.DATA_ITEM_PROCESSING_COMPLETED
        await session.merge(record)
        await session.commit()


async def process_items_incremental(
    data_item: Any,
    dataset: Dataset,
    tasks: list[Stage],
    workflow_name: str,
    workflow_id: str,
    workflow_run_id: str,
    context: Optional[Dict[str, Any]],
    user: User,
) -> AsyncGenerator[Dict[str, Any], None]:
    """Run tasks with incremental loading support."""
    data_id = await _resolve_data_id(data_item, user)

    if await _is_already_processed(data_id, workflow_name, dataset.id):
        yield {
            "run_detail": RunAlreadyCompleted(
                workflow_run_id=workflow_run_id,
                dataset_id=dataset.id,
                dataset_name=dataset.name,
            ),
            "data_id": data_id,
        }
        return

    try:
        async for res in execute_with_telemetry(
            tasks=tasks,
            data=[data_item],
            user=user,
            workflow_name=workflow_id,
            context=context,
        ):
            yield RunYield(
                workflow_run_id=workflow_run_id,
                dataset_id=dataset.id,
                dataset_name=dataset.name,
                payload=res,
            )

        await _mark_completed(data_id, workflow_name, dataset.id)

        yield {
            "run_detail": RunCompleted(
                workflow_run_id=workflow_run_id,
                dataset_id=dataset.id,
                dataset_name=dataset.name,
            ),
            "data_id": data_id,
        }

    except Exception as e:
        _log.error(
            f"Stage failed for data_id={data_id}, dataset={dataset.name}, pipeline={workflow_name}: {e}",
            exc_info=True,
        )
        yield {
            "run_detail": RunFailed(
                workflow_run_id=workflow_run_id,
                payload=str(e),
                dataset_id=dataset.id,
                dataset_name=dataset.name,
            ),
            "data_id": data_id,
        }
        if _RAISE_ERRORS:
            raise


async def process_items_regular(
    data_item: Any,
    dataset: Dataset,
    tasks: list[Stage],
    workflow_id: str,
    workflow_run_id: str,
    context: Optional[Dict[str, Any]],
    user: User,
) -> AsyncGenerator[Dict[str, Any], None]:
    """Run tasks without incremental checking."""
    try:
        async for res in execute_with_telemetry(
            tasks=tasks,
            data=[data_item],
            user=user,
            workflow_name=workflow_id,
            context=context,
        ):
            yield RunYield(
                workflow_run_id=workflow_run_id,
                dataset_id=dataset.id,
                dataset_name=dataset.name,
                payload=res,
            )

        yield {
            "run_detail": RunCompleted(
                workflow_run_id=workflow_run_id,
                dataset_id=dataset.id,
                dataset_name=dataset.name,
            )
        }

    except Exception as e:
        _log.error(f"Stage failed for data item: {e}", exc_info=True)
        yield {
            "run_detail": RunFailed(
                workflow_run_id=workflow_run_id,
                payload=str(e),
                dataset_id=dataset.id,
                dataset_name=dataset.name,
            ),
        }
        if _RAISE_ERRORS:
            raise


async def process_data_items(
    data_item: Any,
    dataset: Dataset,
    tasks: list[Stage],
    workflow_name: str,
    workflow_id: str,
    workflow_run_id: str,
    context: Optional[Dict[str, Any]],
    user: User,
    incremental_loading: bool,
) -> Optional[Dict[str, Any]]:
    """Process data item through pipeline tasks."""
    gen = (
        process_items_incremental(
            data_item,
            dataset,
            tasks,
            workflow_name,
            workflow_id,
            workflow_run_id,
            context,
            user,
        )
        if incremental_loading
        else process_items_regular(
            data_item,
            dataset,
            tasks,
            workflow_id,
            workflow_run_id,
            context,
            user,
        )
    )

    result = None
    async for result in gen:
        pass
    return result
