"""
Pipeline Execution Exceptions
=============================

Exception classes for pipeline-related errors.
"""

from fastapi import status

from m_flow.exceptions import InternalError


class WorkflowRunFailedError(InternalError):
    """
    Raised when a pipeline execution fails.

    This indicates an error during the processing of data through
    the pipeline stages that prevented successful completion.
    """

    ERROR_NAME = "WorkflowRunFailedError"
    DEFAULT_MESSAGE = "Pipeline execution encountered an error."

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        name: str = ERROR_NAME,
        status_code: int = status.HTTP_422_UNPROCESSABLE_CONTENT,
    ):
        super().__init__(message, name, status_code)
