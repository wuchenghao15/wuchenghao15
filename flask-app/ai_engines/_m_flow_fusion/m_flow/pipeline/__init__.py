"""
M-flow Workflow Engine
======================

Composable stages and workflow execution for memory pipelines.
"""

from __future__ import annotations

from .tasks.task import Stage
from .operations.run_tasks import run_tasks
from .operations.execute_parallel import execute_parallel
from .operations.pipeline import execute_workflow, WorkflowConfig

__all__ = [
    "Stage",
    "execute_workflow",
    "WorkflowConfig",
    "run_tasks",
    "execute_parallel",
]
