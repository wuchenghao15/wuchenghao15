"""
Convenience re-export: ``from m_flow.pipelines import Stage, run_tasks``.
"""

from m_flow.pipeline import (  # noqa: F401
    Stage,
    execute_workflow,
    WorkflowConfig,
    run_tasks,
    execute_parallel,
)
