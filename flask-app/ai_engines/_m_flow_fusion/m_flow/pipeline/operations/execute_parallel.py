"""
Parallel task execution for m_flow pipelines.

This module provides utilities to run multiple pipeline tasks in parallel,
with support for result merging and deduplication.
"""

from typing import Any, List, Optional, Set
from uuid import UUID
import asyncio
from m_flow.shared.logging_utils import get_logger
from ..tasks import Stage

logger = get_logger("run_parallel")


async def _update_parallel_step(context: Optional[dict], step_name: str) -> None:
    """Update current step for parallel execution (fire-and-forget)."""
    if not context:
        return

    run_id_str = context.get("workflow_run_id")
    if not run_id_str:
        return

    try:
        from m_flow.pipeline.operations.update_pipeline_progress import (
            update_pipeline_progress,
        )

        await update_pipeline_progress(
            UUID(run_id_str),
            current_step=step_name,
        )
    except Exception as e:
        logger.debug(f"Failed to update step: {e}")


def execute_parallel(
    tasks: List[Stage],
    merge_results: bool = True,
    deduplicate: bool = True,
) -> Stage:
    """
    Execute multiple tasks in parallel and merge results

    Args:
        tasks: List of tasks to execute in parallel
        merge_results: Whether to merge output lists from all tasks (default True)
        deduplicate: Whether to deduplicate based on MemoryNode.id (default True)

    Returns:
        Task: Wrapped parallel task

    Example:
        ```python
        parallel_task = execute_parallel([
            Stage(write_episodic_memories),
            Stage(write_procedural_memories),
        ])
        # parallel_task will merge outputs from both tasks
        ```

    Note:
        - Uses return_exceptions=True to ensure all tasks complete
        - Even if some tasks fail, results from other tasks are preserved
        - Will raise the first exception at the end
    """

    async def parallel_run(data, context: Optional[dict] = None):
        # Context is passed as a positional argument by execute_pipeline_tasks
        # when the function signature includes 'context' parameter

        # Get task names for step display
        task_names = [getattr(t.executable, "__name__", f"task_{i}") for i, t in enumerate(tasks)]
        step_name = f"Parallel: {', '.join(task_names)}"

        # Update progress with parallel step name
        asyncio.create_task(_update_parallel_step(context, step_name))

        logger.info(f"[parallel] Starting {len(tasks)} parallel tasks")

        # Create all tasks - pass data and context to each
        parallel_tasks = [asyncio.create_task(task.run(data, context=context)) for task in tasks]

        # Use return_exceptions=True to ensure all tasks complete
        results = await asyncio.gather(*parallel_tasks, return_exceptions=True)

        # Collect exceptions and valid results
        exceptions: List[Exception] = []
        valid_results: List[Any] = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                task_name = getattr(tasks[i].executable, "__name__", f"task_{i}")
                logger.error(f"[parallel] Stage '{task_name}' failed: {result}")
                exceptions.append(result)
            else:
                valid_results.append(result)

        # Log result statistics
        logger.info(f"[parallel] Completed: {len(valid_results)} succeeded, {len(exceptions)} failed")

        # Update progress to show completion
        asyncio.create_task(_update_parallel_step(context, "Parallel tasks completed"))

        # If exceptions exist, log warning but continue processing valid results
        if exceptions:
            logger.warning(
                f"[parallel] {len(exceptions)} tasks failed, processing {len(valid_results)} successful results"
            )

        if merge_results:
            # Merge all list outputs
            merged: List[Any] = []
            seen_ids: Set[str] = set()

            for result in valid_results:
                if isinstance(result, list):
                    for item in result:
                        # Deduplicate: based on MemoryNode.id or dict['id']
                        if deduplicate:
                            item_id = None
                            if hasattr(item, "id"):
                                item_id = str(item.id)
                            elif isinstance(item, dict) and "id" in item:
                                item_id = str(item["id"])

                            if item_id is not None:
                                if item_id in seen_ids:
                                    logger.debug(f"[parallel] Skipping duplicate: {item_id[:8]}...")
                                    continue
                                seen_ids.add(item_id)
                        merged.append(item)
                else:
                    # Non-list results added directly
                    merged.append(result)

            # Calculate deduplication count
            total_items_before_dedup = sum(len(r) if isinstance(r, list) else 1 for r in valid_results)
            removed_count = total_items_before_dedup - len(merged) if deduplicate else 0

            logger.info(
                f"[parallel] Merged {len(merged)} items (deduplicated: {deduplicate}, removed: {removed_count})"
            )

            # If exceptions exist, raise first exception after returning results
            if exceptions:
                raise exceptions[0]

            return merged
        else:
            # Don't merge, return last valid result
            if exceptions:
                raise exceptions[0]
            return valid_results[-1] if valid_results else []

    return Stage(parallel_run)


# Backward-compatible alias
