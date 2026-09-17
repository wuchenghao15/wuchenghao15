"""
Pipeline execution modes for M-flow.

Provides functions to run pipelines either synchronously (blocking)
or as background tasks with progress updates.
"""

from __future__ import annotations

import asyncio
from typing import (
    Any,
    AsyncGenerator,
    AsyncIterable,
    Awaitable,
    Callable,
    Dict,
    Union,
)

from m_flow.pipeline.models.RunEvent import (
    RunCompleted,
    RunFailed,
)
from m_flow.pipeline.queues.workflow_run_info_queues import push_to_queue

# Type alias for pipeline-like async iterables
PipelineLike = Union[
    AsyncIterable[Any],
    AsyncGenerator[Any, None],
    Callable[..., AsyncIterable[Any]],
    Callable[..., AsyncGenerator[Any, None]],
]


async def run_pipeline_blocking(
    pipeline: PipelineLike,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Execute pipeline synchronously, blocking until completion.

    Collects run info for each dataset and returns a mapping
    of dataset_id to final run info.

    Args:
        pipeline: Async generator or callable returning one.
        **kwargs: Parameters passed to pipeline if callable.

    Returns:
        Mapping of dataset_id to run info, or run info directly
        if no dataset_id is present.
    """
    gen = pipeline(**kwargs) if callable(pipeline) else pipeline

    results: Dict[str, Any] = {}

    async for info in gen:
        ds_id = getattr(info, "dataset_id", None)
        if ds_id:
            results[ds_id] = info
        else:
            results = info

    return results


async def run_pipeline_as_background_process(
    pipeline: PipelineLike,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Start pipeline(s) and return immediately with initial status.

    For each dataset, starts a pipeline run and returns the
    "started" status. Continues execution in background, pushing
    updates to a queue until completion.

    Args:
        pipeline: Async generator or callable returning one.
        **kwargs: Parameters including 'datasets' (str or list).

    Returns:
        Mapping of dataset_id to initial run info.
    """
    datasets = kwargs.get("datasets")
    if isinstance(datasets, str):
        datasets = [datasets]

    started_info: Dict[str, Any] = {}
    active_runs: list = []
    # Track dataset_id for each generator to restore ContextVar in background task
    gen_dataset_ids: Dict[int, str] = {}

    # Initialize each dataset's pipeline
    for ds in datasets:
        call_kwargs = dict(kwargs)
        call_kwargs["datasets"] = ds

        gen = pipeline(**call_kwargs) if callable(pipeline) else pipeline

        # Get initial "started" info
        info = await anext(gen)
        ds_id = info.dataset_id

        # Clear payload for serialization safety
        if hasattr(info, "payload") and info.payload:
            info.payload = []

        started_info[ds_id] = info
        active_runs.append(gen)
        # Map gen to dataset_id for ContextVar restoration
        gen_dataset_ids[id(gen)] = str(ds_id)

    # Background task to process remaining updates
    async def _process_remaining(runs: list) -> None:
        # Import here to avoid circular import
        from m_flow.context_global_variables import current_dataset_id
        from m_flow.shared.logging_utils import get_logger

        logger = get_logger("pipeline_executor")

        for gen in runs:
            # Restore correct dataset_id in ContextVar before resuming generator
            # This fixes the issue where multiple datasets in background mode
            # would all use the last dataset's context
            ds_id = gen_dataset_ids.get(id(gen))
            if ds_id:
                current_dataset_id.set(ds_id)

            while True:
                try:
                    info = await anext(gen)
                    push_to_queue(info.workflow_run_id, info)

                    if isinstance(info, (RunCompleted, RunFailed)):
                        break
                except StopAsyncIteration:
                    break

        # After all background pipelines complete, force checkpoint
        # to persist WAL data to disk (prevents data loss on crash)
        try:
            from m_flow.adapters.graph.get_graph_adapter import get_graph_provider

            graph_engine = await get_graph_provider()
            if hasattr(graph_engine, "checkpoint"):
                await graph_engine.checkpoint()
                logger.info("[background] Graph database checkpoint completed")
        except Exception as e:
            logger.warning(f"[background] Graph checkpoint failed: {e}")

    asyncio.create_task(_process_remaining(active_runs))
    return started_info


def get_pipeline_executor(
    run_in_background: bool = False,
) -> Callable[..., Awaitable[Dict[str, Any]]]:
    """
    Select the appropriate pipeline executor.

    Args:
        run_in_background: If True, returns async background executor.

    Returns:
        Executor function (blocking or background).
    """
    if run_in_background:
        return run_pipeline_as_background_process
    return run_pipeline_blocking
