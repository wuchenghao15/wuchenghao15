"""Pipeline task validation."""

from __future__ import annotations

from typing import List

from ..exceptions.tasks import WrongTaskTypeError
from ..tasks import Stage


def ensure_valid_tasks(tasks: List[Stage]) -> None:
    """
    Validate that tasks is a list of Stage instances.

    Raises
    ------
    WrongTaskTypeError
        If tasks is not a list or contains non-Stage items.
    """
    if not isinstance(tasks, list):
        raise WrongTaskTypeError(f"Expected list, got {type(tasks).__name__}.")

    for item in tasks:
        if not isinstance(item, Stage):
            raise WrongTaskTypeError(f"Expected Stage, got {type(item).__name__}.")
