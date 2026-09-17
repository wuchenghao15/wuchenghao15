"""
Data Module Exceptions
======================

Custom exception classes for data-related operations including
dataset management, data access control, and validation errors.
"""

from fastapi import status

from m_flow.exceptions import BadInputError, ConfigError


# --- Configuration Errors ---


class UnstructuredLibraryImportError(ConfigError):
    """
    Raised when the optional 'unstructured' library is missing.

    The unstructured library is required for parsing complex document
    formats like PDFs, Word documents, and HTML files.
    """

    DEFAULT_MSG = "Cannot import unstructured library. Please install it first."
    ERROR_NAME = "UnstructuredModuleImportError"

    def __init__(
        self,
        message: str = DEFAULT_MSG,
        name: str = ERROR_NAME,
        status_code: int = status.HTTP_422_UNPROCESSABLE_CONTENT,
    ):
        super().__init__(message, name, status_code)


# --- Authorization Errors ---


class UnauthorizedDataAccessError(BadInputError):
    """
    Raised when a user attempts to access data without proper permissions.

    This typically occurs when trying to read, modify, or delete datasets
    that belong to another user or tenant.
    """

    DEFAULT_MSG = "Access denied: insufficient permissions for this data."
    ERROR_NAME = "UnauthorizedDataAccessError"

    def __init__(
        self,
        message: str = DEFAULT_MSG,
        name: str = ERROR_NAME,
        status_code: int = status.HTTP_401_UNAUTHORIZED,
    ):
        super().__init__(message, name, status_code)


# --- Resource Errors ---


class DatasetNotFoundError(BadInputError):
    """
    Raised when a requested dataset does not exist in the system.

    This can occur when querying by ID or name for a dataset that
    has been deleted or never existed.
    """

    DEFAULT_MSG = "The requested dataset could not be found."
    ERROR_NAME = "DatasetNotFoundError"

    def __init__(
        self,
        message: str = DEFAULT_MSG,
        name: str = ERROR_NAME,
        status_code: int = status.HTTP_404_NOT_FOUND,
    ):
        super().__init__(message, name, status_code)


# --- Validation Errors ---


class DatasetTypeError(BadInputError):
    """
    Raised when an unsupported dataset type is encountered.

    M-flow supports specific dataset types (e.g., document, structured).
    Using an unknown type triggers this exception.
    """

    DEFAULT_MSG = "The specified dataset type is not supported."
    ERROR_NAME = "DatasetTypeError"

    def __init__(
        self,
        message: str = DEFAULT_MSG,
        name: str = ERROR_NAME,
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ):
        super().__init__(message, name, status_code)


class InvalidTableAttributeError(BadInputError):
    """
    Raised when a data model lacks the required '__tablename__' attribute.

    SQLAlchemy models require this attribute to map to database tables.
    """

    DEFAULT_MSG = "Data model is missing the required '__tablename__' attribute."
    ERROR_NAME = "InvalidTableAttributeError"

    def __init__(
        self,
        message: str = DEFAULT_MSG,
        name: str = ERROR_NAME,
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ):
        super().__init__(message, name, status_code)
