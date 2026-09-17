"""
High-level pipeline execution entry points.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, List, Optional, Union
from uuid import UUID

from m_flow.auth.models import User
from m_flow.context_global_variables import (
    current_dataset_id,
    set_db_context,
)
from m_flow.data.methods.fetch_dataset_items import fetch_dataset_items
from m_flow.data.models import Data, Dataset
from m_flow.pipeline.layers import ensure_valid_tasks
from m_flow.pipeline.layers.check_cache_status import check_cache_status
from m_flow.pipeline.layers.authorize_datasets import authorize_datasets
from m_flow.pipeline.layers.prepare_backends import prepare_backends
from m_flow.pipeline.models.RunEvent import RunStarted
from m_flow.pipeline.operations.run_tasks import run_tasks
from m_flow.pipeline.tasks import Stage
from m_flow.shared.logging_utils import get_logger

_log = get_logger("m_flow.pipeline")


@dataclass(frozen=True)
class WorkflowConfig:
    """Optional knobs for a workflow run."""

    vector_db: dict | None = None
    graph_db: dict | None = None
    cache: bool = False
    incremental: bool = False
    batch_size: int = 20


WorkflowConfig = WorkflowConfig


async def execute_workflow(
    tasks: list[Stage],
    data: Any | None = None,
    datasets: str | list[str] | list[UUID] | None = None,
    user: User | None = None,
    name: str = "custom_workflow",
    config: WorkflowConfig | None = None,
) -> AsyncIterator[Any]:
    """
    Execute *tasks* across one or more datasets.

    Parameters
    ----------
    tasks : list[Stage]
        Ordered pipeline stages.
    data : Any, optional
        Pre-loaded payload; when ``None`` items are fetched from *datasets*.
    datasets : str | list | None
        Dataset name(s) or UUID(s).  ``None`` processes all user datasets.
    user : User | None
        Caller identity; falls back to seed user.
    name : str
        Pipeline label used in logs and progress tracking.
    config : WorkflowConfig | None
        Runtime overrides (caching, batch size, backend config).
    """
    cfg = config or WorkflowConfig()
    resolved_user, authorised = await _prepare(tasks, datasets, user, cfg)

    for ds in authorised:
        async for info in _execute_for_dataset(
            ds,
            resolved_user,
            tasks,
            data,
            name,
            cfg,
        ):
            yield info


async def _prepare(
    tasks: list[Stage],
    datasets: str | list[str] | list[UUID] | None,
    user: User | None,
    cfg: WorkflowConfig,
) -> tuple[User, list[Dataset]]:
    """Validate inputs, initialise backends, and resolve authorised datasets."""
    ensure_valid_tasks(tasks)
    await prepare_backends(cfg.vector_db, cfg.graph_db)
    return await authorize_datasets(datasets, user)


async def _execute_for_dataset(
    ds: Dataset,
    owner: User,
    tasks: list[Stage],
    payload: Any | None,
    name: str,
    cfg: WorkflowConfig,
) -> AsyncIterator[Any]:
    """Run the pipeline for a single dataset."""
    current_dataset_id.set(str(ds.id))
    await set_db_context(ds.id, ds.owner_id)

    items: list[Data] = payload if payload else await fetch_dataset_items(dataset_id=ds.id)

    status = await check_cache_status(ds, items, name)
    if status:
        if cfg.cache:
            yield status
            return
        yield RunStarted(
            workflow_run_id=status.workflow_run_id,
            dataset_id=ds.id,
            dataset_name=ds.name,
            payload=items,
        )

    async for info in run_tasks(
        tasks=tasks,
        dataset_id=ds.id,
        user=owner,
        workflow_name=name,
        data=items,
        context={"dataset": ds},
        items_per_batch=cfg.batch_size,
        incremental_loading=cfg.incremental,
    ):
        yield info


execute_workflow = execute_workflow
