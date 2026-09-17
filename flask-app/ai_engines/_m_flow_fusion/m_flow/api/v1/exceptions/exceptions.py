"""
API v1 Exception Classes
========================

Custom exceptions for the M-flow API v1 endpoints.
Includes configuration errors and resource not found errors.
"""

from fastapi import status

from m_flow.exceptions import ConfigError, BadInputError


# --- Configuration Errors ---


class InvalidConfigAttributeError(ConfigError):
    """
    Raised when an invalid attribute is specified in configuration.

    Parameters
    ----------
    attribute : str
        The invalid attribute name that was provided.
    """

    ERROR_NAME = "InvalidConfigAttributeError"

    def __init__(
        self,
        attribute: str,
        name: str = ERROR_NAME,
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ):
        error_msg = f"Configuration attribute '{attribute}' is not valid."
        super().__init__(error_msg, name, status_code)


# --- Resource Not Found Errors ---


class DocumentNotFoundError(BadInputError):
    """
    Raised when a requested document cannot be located.

    This typically occurs when querying by ID for a document
    that has been deleted or never existed.
    """

    ERROR_NAME = "DocumentNotFoundError"
    DEFAULT_MESSAGE = "The requested document does not exist."

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        name: str = ERROR_NAME,
        status_code: int = status.HTTP_404_NOT_FOUND,
    ):
        super().__init__(message, name, status_code)


class DatasetNotFoundError(BadInputError):
    """
    Raised when a requested dataset cannot be located.

    Verify the dataset ID is correct and that the dataset
    has not been deleted.
    """

    ERROR_NAME = "DatasetNotFoundError"
    DEFAULT_MESSAGE = "The requested dataset does not exist."

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        name: str = ERROR_NAME,
        status_code: int = status.HTTP_404_NOT_FOUND,
    ):
        super().__init__(message, name, status_code)


class DataNotFoundError(BadInputError):
    """
    Raised when requested data cannot be located.

    This is a generic error for missing data entries.
    """

    ERROR_NAME = "DataNotFoundError"
    DEFAULT_MESSAGE = "The requested data does not exist."

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        name: str = ERROR_NAME,
        status_code: int = status.HTTP_404_NOT_FOUND,
    ):
        super().__init__(message, name, status_code)


class DocumentSubgraphNotFoundError(BadInputError):
    """
    Raised when a document's subgraph cannot be found in the graph database.

    This may indicate the document hasn't been processed yet or
    the graph data has been cleared.
    """

    ERROR_NAME = "DocumentSubgraphNotFoundError"
    DEFAULT_MESSAGE = "The document subgraph could not be found in the graph database."

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        name: str = ERROR_NAME,
        status_code: int = status.HTTP_404_NOT_FOUND,
    ):
        super().__init__(message, name, status_code)


class NodeNotFoundError(BadInputError):
    """
    Raised when a requested graph node cannot be located.

    This typically occurs when querying by node ID for a node
    that has been deleted or never existed.
    """

    ERROR_NAME = "NodeNotFoundError"
    DEFAULT_MESSAGE = "The requested node does not exist."

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        name: str = ERROR_NAME,
        status_code: int = status.HTTP_404_NOT_FOUND,
    ):
        super().__init__(message, name, status_code)


# --- Permission Errors ---


class PermissionDeniedError(BadInputError):
    """
    Raised when user lacks permission to perform an operation.

    This returns HTTP 403 Forbidden, unlike Python's built-in
    PermissionError which would cause a 500 error.
    """

    ERROR_NAME = "PermissionDeniedError"
    DEFAULT_MESSAGE = "Permission denied for this operation."

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        name: str = ERROR_NAME,
        status_code: int = status.HTTP_403_FORBIDDEN,
    ):
        super().__init__(message, name, status_code)


# --- Concurrency Errors ---


class ConcurrentMemorizeError(BadInputError):
    """
    Raised when attempting to memorize a dataset that is already being processed.

    This indicates a concurrent operation conflict. The caller should either:
    - Wait and retry later
    - Use conflict_mode="ignore" to proceed without checking
    - Use conflict_mode="warn" to log a warning but continue

    Note:
        This protection only works within a single process. In multi-process
        deployments (e.g., Gunicorn with multiple workers), use external
        distributed locks (Redis, database row locks) for full protection.
    """

    ERROR_NAME = "ConcurrentMemorizeError"
    DEFAULT_MESSAGE = "Dataset is already being processed by another memorize operation."

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        name: str = ERROR_NAME,
        status_code: int = status.HTTP_409_CONFLICT,
    ):
        super().__init__(message, name, status_code)
