"""
Pipeline execution event models.
"""

from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from m_flow.data.models.Data import Data


class RunStatus(str, Enum):
    """Pipeline run status enumeration."""

    STARTED = "RunStarted"
    YIELD = "RunYield"
    COMPLETED = "RunCompleted"
    ALREADY_DONE = "RunAlreadyCompleted"
    ERROR = "RunFailed"


def _serialize_data(obj: Data) -> dict:
    """Serialize a Data object to dict."""
    return obj.to_json()


class RunEvent(BaseModel):
    """
    Base class for pipeline execution events.

    Attributes:
        status: Execution status.
        workflow_run_id: Pipeline run ID.
        dataset_id: Dataset ID.
        dataset_name: Dataset name.
        payload: Result payload.
        processing_results: Data ingestion information.
    """

    workflow_run_id: UUID
    status: str
    dataset_name: str
    dataset_id: UUID
    processing_results: list[Any] | None = None
    payload: Any | list[Data] | None = None

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True,
        json_encoders={Data: _serialize_data},
    )


class RunCompleted(RunEvent):
    """Pipeline execution completed event."""

    status: str = RunStatus.COMPLETED.value


class RunFailed(RunEvent):
    """Pipeline execution error event."""

    status: str = RunStatus.ERROR.value


class RunStarted(RunEvent):
    """Pipeline execution started event."""

    status: str = RunStatus.STARTED.value


class RunAlreadyCompleted(RunEvent):
    """Pipeline already completed (cached result) event."""

    status: str = RunStatus.ALREADY_DONE.value


class RunYield(RunEvent):
    """Pipeline intermediate result event."""

    status: str = RunStatus.YIELD.value
