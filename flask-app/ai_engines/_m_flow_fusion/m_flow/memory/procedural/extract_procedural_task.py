"""
Pipeline Task wrapper for extracting procedural memories from existing episodes.

This adapts `extract_procedural_from_episodic` to the Pipeline Task interface
so it can run through the standard pipeline system with:
- Dashboard visibility (WorkflowRun records)
- Duplicate prevention (check_cache_status)
- Automatic database context (set_db_context)
- Background execution support
"""

from __future__ import annotations

from typing import Any, List

from m_flow.shared.logging_utils import get_logger
from m_flow.memory.procedural.write_procedural_from_episodic import (
    extract_procedural_from_episodic,
)

logger = get_logger("extract_procedural_task")


async def extract_procedural_task(
    data: Any,
    force_reprocess: bool = False,
    limit: int = 100,
) -> List[Any]:
    """
    Pipeline-compatible task that extracts procedural memories from episodes.

    Called by execute_workflow's task execution engine. The pipeline system
    already handles:
    - Setting database context via set_db_context
    - Per-dataset iteration
    - Pipeline run logging (INITIATED → STARTED → COMPLETED)

    Args:
        data: Input data items from pipeline (not directly used —
              we query Episode nodes from the graph instead).
        force_reprocess: If True, reprocess already-extracted episodes.
        limit: Max episodes to process per dataset.

    Returns:
        List of created MemoryNode objects (Procedure, StepPoint, etc.)
    """
    logger.info(f"[extract_procedural_task] Starting, force={force_reprocess}, limit={limit}")

    result = await extract_procedural_from_episodic(
        limit=limit,
        force_reprocess=force_reprocess,
    )

    nodes = result.get("result", [])
    analyzed = result.get("episodes_analyzed", 0)
    written = result.get("nodes_written", 0)

    logger.info(
        f"[extract_procedural_task] Done: analyzed={analyzed}, "
        f"nodes_written={written}, procedures={len([n for n in nodes if hasattr(n, '__class__') and n.__class__.__name__ == 'Procedure'])}"
    )

    return nodes
