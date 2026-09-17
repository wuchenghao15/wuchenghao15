"""
Base task execution engine.

Core pipeline task runner with telemetry and error handling.
"""

from __future__ import annotations

import asyncio
import inspect
from uuid import UUID

from m_flow import __version__ as mflow_version
from m_flow.auth.models import User
from m_flow.shared.logging_utils import get_logger
from m_flow.shared.utils import send_telemetry

from ..tasks import Stage

logger = get_logger("task_runner")


async def _update_current_step(context: dict, step_name: str) -> None:
    """Update current step in progress (fire-and-forget)."""
    if not context:
        logger.debug(f"[step_update] No context, skipping step update for: {step_name}")
        return

    run_id_str = context.get("workflow_run_id")
    if not run_id_str:
        logger.debug(f"[step_update] No workflow_run_id in context, skipping: {step_name}")
        return

    try:
        from m_flow.pipeline.operations.update_pipeline_progress import (
            update_pipeline_progress,
        )

        run_id = UUID(run_id_str)
        logger.info(f"[step_update] Updating currentStep to: {step_name}")
        await update_pipeline_progress(run_id, current_step=step_name)
    except Exception as e:
        logger.warning(f"[step_update] Failed to update step: {e}")


async def execute_pipeline_tasks(
    tasks: list[Stage],
    data=None,
    user: User = None,
    context: dict = None,
):
    """
    Execute pipeline tasks sequentially.

    Processes tasks head-first, passing results
    to remaining tasks recursively.

    Args:
        tasks: Stage list to execute.
        data: Input data.
        user: Executing user.
        context: Shared context dict.

    Yields:
        Task results.
    """
    if not tasks:
        yield data
        return

    current = tasks[0]
    remaining = tasks[1:]

    # Determine batch size from next task
    batch_size = 1
    if remaining:
        batch_size = remaining[0].task_config.get("batch_size", 1)

    args = [data] if data is not None else []

    async for result in _execute_task(current, args, remaining, batch_size, user, context):
        yield result


async def _execute_task(
    task: Stage,
    args: list,
    remaining: list[Stage],
    batch_size: int,
    user: User,
    context: dict,
):
    """
    Run single task with instrumentation.

    Handles context injection, telemetry events,
    and error propagation.
    """
    name = task.executable.__name__
    task_type = task.task_type

    # Update current step (fire-and-forget, don't block)
    asyncio.create_task(_update_current_step(context, name))

    # Log start
    logger.info("%s started: %s", task_type, name)
    _send_event(f"{task_type} Task Started", user, name)

    # Inject context if needed
    sig = inspect.signature(task.executable)
    if "context" in sig.parameters:
        args.append(context)

    try:
        async for batch in task.execute(args, batch_size):
            async for result in execute_pipeline_tasks(remaining, batch, user, context):
                yield result

        logger.info("%s finished: %s", task_type, name)
        _send_event(f"{task_type} Task Completed", user, name)

    except Exception as err:
        logger.exception("%s failed: %s - %s", task_type, name, str(err))
        _send_event(f"{task_type} Task Errored", user, name)
        raise


def _send_event(event: str, user: User, task_name: str):
    """Emit telemetry event."""
    tenant = str(user.tenant_id) if user.tenant_id else "default"

    send_telemetry(
        event,
        user_id=user.id,
        additional_properties={
            "task_name": task_name,
            "m_flow_version": mflow_version,
            "tenant_id": tenant,
        },
    )


# Backward-compatible alias
