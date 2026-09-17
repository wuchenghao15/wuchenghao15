"""
M-Flow custom pipeline orchestration.

Dispatches user-supplied task sequences through the M-Flow execution engine,
supporting both foreground and background scheduling modes.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from m_flow.auth.models import User
from m_flow.pipeline import execute_workflow
from m_flow.pipeline.layers.pipeline_execution_mode import get_pipeline_executor
from m_flow.pipeline.tasks import Stage
from m_flow.shared.logging_utils import get_logger

_logger = get_logger()

_FALLBACK_DATASET = "main_dataset"
_EMPTY_TASK_LIST: list = []


async def run_custom_pipeline(
    tasks: list[Stage] | list[str] | None = None,
    data: Any = None,
    dataset: str | UUID = "main_dataset",
    user: User | None = None,
    vector_db_config: dict | None = None,
    graph_db_config: dict | None = None,
    enable_cache: bool = False,
    incremental_loading: bool = False,
    items_per_batch: int = 20,
    run_in_background: bool = False,
    workflow_name: str = "custom_pipeline",
):
    """Dispatch a caller-defined task chain via the M-Flow pipeline engine.

    Enables ad-hoc pipeline construction by accepting an ordered sequence of
    tasks and feeding them through the standard execution machinery.  The
    caller may optionally override vector/graph storage backends and control
    batching behaviour.

    Parameters
    ----------
    tasks:
        Ordered task definitions to run.  Accepts ``Task`` instances or
        string identifiers that resolve to registered tasks.
    data:
        Payload forwarded to the first task in the chain.
    dataset:
        Logical dataset identifier (name or UUID) that scopes the run.
    user:
        Caller identity for access-control enforcement.
    vector_db_config:
        Optional overrides for the vector storage backend.
    graph_db_config:
        Optional overrides for the graph storage backend.
    enable_cache:
        When ``True``, previously completed stages are skipped.
    incremental_loading:
        When ``True``, only delta data is processed.
    items_per_batch:
        Number of data items processed concurrently per batch.
    run_in_background:
        If ``True``, pipeline runs asynchronously and control returns
        immediately.
    workflow_name:
        Human-readable label used for logging and monitoring.
    """
    resolved_tasks = list(tasks) if tasks else _EMPTY_TASK_LIST

    dispatch_fn = get_pipeline_executor(run_in_background=run_in_background)

    from m_flow.pipeline.operations.pipeline import WorkflowConfig

    pipeline_kwargs = {
        "pipeline": execute_workflow,
        "tasks": resolved_tasks,
        "user": user,
        "data": data,
        "datasets": dataset,
        "name": workflow_name,
        "config": WorkflowConfig(
            vector_db=vector_db_config,
            graph_db=graph_db_config,
            cache=enable_cache,
            incremental=incremental_loading,
            batch_size=items_per_batch,
        ),
    }

    return await dispatch_fn(**pipeline_kwargs)
