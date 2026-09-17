"""
Pipeline Exceptions Module
==========================

Custom error types for pipeline execution failures.
"""

from __future__ import annotations

from .exceptions import WorkflowRunFailedError

__all__ = [
    "WorkflowRunFailedError",
]
