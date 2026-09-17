"""
Document Processing Exceptions
==============================

Exception classes for document ingestion and chunking operations.
"""

from fastapi import status

from m_flow.exceptions import BadInputError


class WrongDataDocumentInputError(BadInputError):
    """
    Raised when document input contains missing or invalid fields.

    Parameters
    ----------
    field : str
        Name of the problematic field.
    """

    ERROR_NAME = "WrongDataDocumentInputError"

    def __init__(
        self,
        field: str,
        name: str = ERROR_NAME,
        status_code: int = status.HTTP_422_UNPROCESSABLE_CONTENT,
    ):
        error_msg = f"Invalid or missing document field: '{field}'"
        super().__init__(error_msg, name, status_code)


class InvalidChunkSizeError(BadInputError):
    """
    Raised when chunk size parameter is invalid.

    Chunk size must be a positive integer to ensure meaningful
    document segmentation.
    """

    ERROR_NAME = "InvalidChunkSizeError"

    def __init__(self, value):
        error_msg = f"Chunk size must be a positive integer, received: {value}"
        super().__init__(error_msg, self.ERROR_NAME, status.HTTP_400_BAD_REQUEST)


class InvalidChunkerError(BadInputError):
    """
    Raised when an invalid chunker class is specified.

    The chunker must be a subclass of the base Chunker class.
    """

    ERROR_NAME = "InvalidChunkerError"
    DEFAULT_MESSAGE = "Provided chunker is not a valid Chunker subclass."

    def __init__(self):
        super().__init__(
            self.DEFAULT_MESSAGE,
            self.ERROR_NAME,
            status.HTTP_400_BAD_REQUEST,
        )
