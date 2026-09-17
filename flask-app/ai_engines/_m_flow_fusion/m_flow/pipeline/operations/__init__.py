"""
Pipeline Operations Module
==========================

Logging utilities for pipeline lifecycle events.
Database-aware concurrency control for pipeline operations.
"""

from __future__ import annotations

from .record_run_finish import record_run_finish
from .record_run_failure import record_run_failure
from .record_run_initiated import record_run_initiated
from .record_run_start import record_run_start
from .db_concurrency import (
    get_pipeline_concurrency_limit,
    run_with_concurrency_limit,
    is_sqlite_mode,
    clear_concurrency_cache,
)
from .execute_pipeline_tasks import execute_pipeline_tasks
from .execute_with_telemetry import execute_with_telemetry, run_tasks_with_telemetry
from .process_data_items import (
    process_data_items,
    process_items_incremental,
    process_items_regular,
)
from .execute_parallel import execute_parallel

__all__ = [
    "record_run_finish",
    "record_run_failure",
    "record_run_initiated",
    "record_run_start",
    "get_pipeline_concurrency_limit",
    "run_with_concurrency_limit",
    "is_sqlite_mode",
    "clear_concurrency_cache",
    "execute_pipeline_tasks",
    "execute_with_telemetry",
    "process_data_items",
    "process_items_incremental",
    "process_items_regular",
    "execute_parallel",
    "execute_pipeline_tasks",
    "run_tasks_with_telemetry",
    "execute_parallel",
]
