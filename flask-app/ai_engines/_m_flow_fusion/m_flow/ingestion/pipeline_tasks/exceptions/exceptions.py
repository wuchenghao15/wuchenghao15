"""
Ingestion Pipeline Task Exceptions
==================================

Exception classes for errors during pipeline task execution.
"""

from fastapi import status

from m_flow.exceptions import InternalError


class S3FileSystemNotFoundError(InternalError):
    """
    Raised when the S3 file system cannot be located or accessed.

    This typically indicates a configuration issue with AWS credentials
    or the s3fs library not being properly initialized.
    """

    ERROR_NAME = "S3FileSystemNotFoundError"
    DEFAULT_MESSAGE = "S3 file system is unavailable or not configured."

    def __init__(
        self,
        name: str = ERROR_NAME,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ):
        super().__init__(self.DEFAULT_MESSAGE, name, status_code)
