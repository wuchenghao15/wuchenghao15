"""
Distributed execution with Modal.

Scales pipeline processing across cloud workers.
"""

from __future__ import annotations

from typing import Any, List
from uuid import UUID

try:
    import modal
except ModuleNotFoundError:
    modal = None

from m_flow.adapters.relational import get_db_adapter
from m_flow.auth.methods import get_seed_user
from m_flow.auth.models import User
from m_flow.data.models import Dataset
from m_flow.ingestion.pipeline_tasks import resolve_data_directories
from m_flow.pipeline.exceptions import WorkflowRunFailedError
from m_flow.pipeline.models import (
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
from m_flow.pipeline.tasks import Stage
from m_flow.pipeline.utils import derive_pipeline_key
from m_flow.shared.logging_utils import get_logger

from .process_data_items import process_data_items

logger = get_logger("modal_runner")


def _configure_modal_worker():
    """Set up Modal function decorator when available.

    Only called when distributed execution is actually requested,
    not at module import time. This avoids failures in local environments
    where Modal runtime context is not available.
    """
    if not modal:
        raise RuntimeError("Modal is not installed. Install it with: pip install modal")

    import os
    from mflow_workers.app import app
    from mflow_workers.modal_image import image

    secret = modal.Secret.from_name(os.environ.get("MODAL_SECRET_NAME", "distributed_m_flow"))

    @app.function(retries=3, image=image, timeout=86400, max_containers=50, secrets=[secret])
    async def worker(item, ds_id, tasks, name, pipe_id, run_id, ctx, usr, incr):
        async with get_db_adapter().get_async_session() as sess:
            ds = await sess.get(Dataset, ds_id)
        return await process_data_items(item, ds, tasks, name, pipe_id, run_id, ctx, usr, incr)

    return worker


# Lazy initialization: worker is configured only when first needed
_modal_worker = None
_modal_worker_initialized = False


def _get_modal_worker():
    """Get or create the Modal worker (lazy init).

    Raises RuntimeError with a clear message if Modal is not available
    or not properly configured.
    """
    global _modal_worker, _modal_worker_initialized
    if not _modal_worker_initialized:
        _modal_worker = _configure_modal_worker()
        _modal_worker_initialized = True
    return _modal_worker


async def dispatch_remote(
    tasks: List[Stage],
    dataset_id: UUID,
    user: User = None,
    workflow_name: str = "pipeline",
    data: List[Any] = None,
    context: dict = None,
    items_per_batch: int = 20,
    incremental_loading: bool = False,
):
    """
    Run pipeline on Modal cloud workers.

    Distributes data items across Modal infrastructure
    for parallel processing with auto-scaling.

    Args:
        tasks: Sequence of pipeline operations.
        dataset_id: Target dataset identifier.
        data: Items to process.
        user: Execution context user.
        workflow_name: Identifier for logging.
        context: Shared state dict.
        incremental_loading: Process only new items.
        items_per_batch: Ignored in distributed mode.

    Yields:
        RunStarted, RunCompleted, or RunFailed.
    """
    usr = user or await get_seed_user()

    engine = get_db_adapter()
    async with engine.get_async_session() as sess:
        ds = await sess.get(Dataset, dataset_id)

    pipe_id = derive_pipeline_key(usr.id, ds.id, workflow_name)
    run_rec = await record_run_start(pipe_id, workflow_name, dataset_id, data)
    run_id = run_rec.workflow_run_id

    yield RunStarted(
        workflow_run_id=run_id,
        dataset_id=ds.id,
        dataset_name=ds.name,
        payload=data,
    )

    try:
        items = [data] if not isinstance(data, list) else data
        items = await resolve_data_directories(items)
        count = len(items)

        # Initialize progress tracking
        await set_pipeline_started(run_id, count)

        # Inject workflow_run_id into context for task-level updates
        ctx = context.copy() if context else {}
        ctx["workflow_run_id"] = str(run_id)

        # Build broadcast arguments
        def broadcast(v):
            return [v] * count

        map_args = [
            items,
            broadcast(ds.id),
            broadcast(tasks),
            broadcast(workflow_name),
            broadcast(pipe_id),
            broadcast(run_id),
            broadcast(ctx),
            broadcast(usr),
            broadcast(incremental_loading),
        ]

        # Collect results from workers
        worker = _get_modal_worker()
        outputs = []
        processed_count = 0
        async for out in worker.map.aio(*map_args):
            if out:
                outputs.append(out)
            processed_count += 1
            # Update progress as workers complete
            await update_pipeline_progress(run_id, processed_items=processed_count)

        # Detect failures
        failed = [o for o in outputs if isinstance(o.get("run_detail"), RunFailed)]
        if failed:
            raise WorkflowRunFailedError("Worker execution failed")

        await record_run_finish(run_id, pipe_id, workflow_name, dataset_id, data)

        yield RunCompleted(
            workflow_run_id=run_id,
            dataset_id=ds.id,
            dataset_name=ds.name,
            processing_results=outputs,
        )

    except WorkflowRunFailedError as ex:
        await record_run_failure(run_id, pipe_id, workflow_name, dataset_id, data, ex)
        yield RunFailed(
            workflow_run_id=run_id,
            payload=str(ex),
            dataset_id=ds.id,
            dataset_name=ds.name,
            processing_results=locals().get("outputs"),
        )
    except Exception as ex:
        await record_run_failure(run_id, pipe_id, workflow_name, dataset_id, data, ex)
        yield RunFailed(
            workflow_run_id=run_id,
            payload=str(ex),
            dataset_id=ds.id,
            dataset_name=ds.name,
            processing_results=locals().get("outputs"),
        )
        raise
