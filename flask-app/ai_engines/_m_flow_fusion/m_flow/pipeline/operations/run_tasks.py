"""
Pipeline task orchestration — execute task graphs against datasets.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable
from uuid import UUID

from m_flow.adapters.graph import get_graph_provider
from m_flow.adapters.relational import get_db_adapter
from m_flow.auth.methods import get_seed_user
from m_flow.auth.models import User
from m_flow.data.models import Data, Dataset
from m_flow.ingestion.pipeline_tasks import resolve_data_directories
from m_flow.pipeline.exceptions import WorkflowRunFailedError
from m_flow.pipeline.models.RunEvent import (
    RunCompleted,
    RunFailed,
    RunStarted,
)
from m_flow.pipeline.operations import (
    record_run_finish,
    record_run_failure,
    record_run_start,
)
from m_flow.pipeline.operations.update_pipeline_progress import (
    set_pipeline_started,
    update_pipeline_progress,
)
from m_flow.pipeline.utils import derive_pipeline_key
from m_flow.shared.logging_utils import get_logger

from ..tasks import Stage
from .process_data_items import process_data_items, preload_processing_status, clear_processing_status_cache
from .db_concurrency import run_with_concurrency_limit, get_pipeline_concurrency_limit

_log = get_logger("m_flow.pipeline.run_tasks")


@runtime_checkable
class RemoteSyncable(Protocol):
    """Adapters that can push local data to a remote object store."""

    async def sync_to_remote(self) -> None: ...


@dataclass
class _RunContext:
    """Holds identifiers created during pipeline initialisation."""

    run_id: UUID
    pipe_id: str
    dataset: Dataset
    user: User
    workflow_name: str
    data: list[Any] | None

    @property
    def started_event(self) -> RunStarted:
        return RunStarted(
            workflow_run_id=self.run_id,
            dataset_id=self.dataset.id,
            dataset_name=self.dataset.name,
            payload=self.data,
        )

    def completed_event(self, results: list) -> RunCompleted:
        return RunCompleted(
            workflow_run_id=self.run_id,
            dataset_id=self.dataset.id,
            dataset_name=self.dataset.name,
            processing_results=results,
        )

    def failed_event(self, err: Exception, results: list) -> RunFailed:
        return RunFailed(
            workflow_run_id=self.run_id,
            payload=str(err),
            dataset_id=self.dataset.id,
            dataset_name=self.dataset.name,
            processing_results=results,
        )


def _want_distributed(override: bool | None) -> bool:
    if override is not None:
        return override
    return os.getenv("MFLOW_DISTRIBUTED", "false").lower() == "true"


async def _init_run(
    user: User | None,
    dataset_id: UUID,
    workflow_name: str,
    data: list[Any] | None,
) -> _RunContext:
    """Resolve user, load dataset, register the pipeline run."""
    resolved_user = user or await get_seed_user()

    async with get_db_adapter().get_async_session() as session:
        dataset = await session.get(Dataset, dataset_id)

    pipe_id = derive_pipeline_key(resolved_user.id, dataset.id, workflow_name)
    run_detail = await record_run_start(pipe_id, workflow_name, dataset_id, data)

    return _RunContext(
        run_id=run_detail.workflow_run_id,
        pipe_id=pipe_id,
        dataset=dataset,
        user=resolved_user,
        workflow_name=workflow_name,
        data=data,
    )


async def _process_batches(
    ctx: _RunContext,
    tasks: list[Stage],
    context: dict | None,
    incremental_loading: bool,
    items_per_batch: int,
) -> list:
    """Run task graph over data items in concurrency-limited batches."""
    items = ctx.data if isinstance(ctx.data, list) else [ctx.data]

    if incremental_loading:
        items = await resolve_data_directories(items)

    total = len(items)
    await set_pipeline_started(ctx.run_id, total)

    merged_ctx = {**(context or {}), "workflow_run_id": str(ctx.run_id)}
    limit = get_pipeline_concurrency_limit()
    results: list = []

    for offset in range(0, len(items), items_per_batch):
        batch = items[offset : offset + items_per_batch]

        if incremental_loading:
            batch_ids = [item.id for item in batch if isinstance(item, Data)]
            if batch_ids:
                await preload_processing_status(batch_ids, ctx.workflow_name, ctx.dataset.id)

        coros = [
            process_data_items(
                item,
                ctx.dataset,
                tasks,
                ctx.workflow_name,
                ctx.pipe_id,
                ctx.run_id,
                merged_ctx,
                ctx.user,
                incremental_loading,
            )
            for item in batch
        ]

        batch_results = await run_with_concurrency_limit(coros, limit)
        results.extend(r for r in batch_results if r)

        await update_pipeline_progress(ctx.run_id, processed_items=min(offset + len(batch), total))

    clear_processing_status_cache()

    errors = [r for r in results if isinstance(r.get("run_detail"), RunFailed)]
    if errors:
        raise WorkflowRunFailedError("One or more data items failed processing")

    return results


async def _flush_remote_storage() -> None:
    """Sync local graph/relational stores to remote if the adapter supports it."""
    for adapter in [await get_graph_provider(), get_db_adapter()]:
        if isinstance(adapter, RemoteSyncable):
            await adapter.sync_to_remote()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


async def run_tasks(
    tasks: list[Stage],
    dataset_id: UUID,
    user: User | None = None,
    workflow_name: str = "unnamed_pipeline",
    data: list[Any] | None = None,
    context: dict | None = None,
    items_per_batch: int = 20,
    incremental_loading: bool = False,
    *,
    distributed: bool | None = None,
) -> AsyncIterator[Any]:
    """
    Execute *tasks* for a single dataset, yielding status events.

    When ``distributed`` is True (or the ``MFLOW_DISTRIBUTED`` env var is
    set), execution is delegated to the Modal-based distributed runner.
    """
    if _want_distributed(distributed):
        from m_flow.pipeline.operations.dispatch_remote import dispatch_remote

        async for evt in dispatch_remote(
            tasks=tasks,
            dataset_id=dataset_id,
            user=user,
            workflow_name=workflow_name,
            data=data,
            context=context,
            items_per_batch=items_per_batch,
            incremental_loading=incremental_loading,
        ):
            yield evt
        return

    ctx = await _init_run(user, dataset_id, workflow_name, data)
    yield ctx.started_event

    results: list = []
    try:
        results = await _process_batches(ctx, tasks, context, incremental_loading, items_per_batch)
        await record_run_finish(ctx.run_id, ctx.pipe_id, ctx.workflow_name, dataset_id, data)
        yield ctx.completed_event(results)
        await _flush_remote_storage()
    except WorkflowRunFailedError as err:
        await record_run_failure(ctx.run_id, ctx.pipe_id, ctx.workflow_name, dataset_id, data, err)
        yield ctx.failed_event(err, results)
    except Exception as err:
        await record_run_failure(ctx.run_id, ctx.pipe_id, ctx.workflow_name, dataset_id, data, err)
        yield ctx.failed_event(err, results)
        raise
