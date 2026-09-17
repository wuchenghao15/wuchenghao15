"""
Document Processing Exceptions
==============================

Exception classes for document type processing errors,
particularly PDF handling via PyPDF.
"""

from __future__ import annotations

from fastapi import status

from m_flow.exceptions import InternalError


class PyPdfInternalError(InternalError):
    """
    Raised when PyPDF encounters an error during PDF processing.

    This typically indicates a corrupted or malformed PDF file
    that cannot be processed.

    Attributes
    ----------
    message : str
        Error description.
    name : str
        Exception identifier.
    status_code : int
        HTTP status code to return.
    """

    ERROR_NAME = "PyPdfInternalError"
    DEFAULT_MESSAGE = "PDF processing encountered an error. The file may be corrupted."

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        name: str = ERROR_NAME,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ) -> None:
        super().__init__(message, name, status_code)
