"""
Pipeline execution with telemetry.

Wraps task execution with start/complete/error events.
"""

from __future__ import annotations

import json
from typing import Any

from m_flow import __version__ as mflow_version
from m_flow.auth.models import User
from m_flow.config.settings import get_current_settings
from m_flow.shared.logging_utils import get_logger
from m_flow.shared.utils import send_telemetry

from ..tasks import Stage
from .execute_pipeline_tasks import execute_pipeline_tasks

logger = get_logger("telemetry_runner")


async def execute_with_telemetry(
    tasks: list[Stage],
    data: Any,
    user: User,
    workflow_name: str,
    context: dict = None,
):
    """
    Execute pipeline with telemetry events.

    Sends events at start, completion, and error.
    Yields results from underlying task execution.

    Args:
        tasks: Pipeline tasks.
        data: Input data.
        user: Executing user.
        workflow_name: Pipeline identifier.
        context: Optional execution context.

    Yields:
        Stage execution results.
    """
    settings = get_current_settings()

    logger.debug(
        "Pipeline config:\n%s",
        json.dumps(settings, indent=2),
    )

    props = _build_telemetry_props(workflow_name, user, settings)

    try:
        logger.info("Pipeline started: %s", workflow_name)
        send_telemetry("Pipeline Run Started", user.id, additional_properties=props)

        async for result in execute_pipeline_tasks(tasks, data, user, context):
            yield result

        logger.info("Pipeline finished: %s", workflow_name)
        send_telemetry("Pipeline Run Completed", user.id, additional_properties=props)

    except Exception as err:
        logger.exception(
            "Pipeline failed: %s - %s",
            workflow_name,
            str(err),
        )
        send_telemetry("Pipeline Run Errored", user.id, additional_properties=props)
        raise


def _build_telemetry_props(name: str, user: User, settings: dict) -> dict:
    """Assemble telemetry payload."""
    tenant = str(user.tenant_id) if user.tenant_id else "default"

    return {
        "workflow_name": name,
        "m_flow_version": mflow_version,
        "tenant_id": tenant,
        **settings,
    }


# Backward-compatible alias
run_tasks_with_telemetry = execute_with_telemetry
