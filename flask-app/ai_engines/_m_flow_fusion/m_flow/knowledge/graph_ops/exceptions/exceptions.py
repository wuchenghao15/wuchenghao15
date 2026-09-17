"""
Knowledge Graph Operations Exceptions
======================================

Exception classes for graph-related operations including
concept management and dimension validation.
"""

from fastapi import status

from m_flow.exceptions import BadInputError


class ConceptNotFoundError(BadInputError):
    """
    Raised when a requested concept or entity cannot be found in the graph.

    This typically occurs during lookups by ID or name when the target
    concept has been deleted or never existed.
    """

    ERROR_NAME = "ConceptNotFoundError"
    DEFAULT_MESSAGE = "The requested entity does not exist."

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        name: str = ERROR_NAME,
        status_code: int = status.HTTP_404_NOT_FOUND,
    ):
        super().__init__(message, name, status_code)


class ConceptAlreadyExistsError(BadInputError):
    """
    Raised when attempting to create a concept that already exists.

    This is a conflict error that prevents duplicate entries in the
    knowledge graph.
    """

    ERROR_NAME = "ConceptAlreadyExistsError"
    DEFAULT_MESSAGE = "The entity already exists."

    def __init__(
        self,
        message: str = DEFAULT_MESSAGE,
        name: str = ERROR_NAME,
        status_code: int = status.HTTP_409_CONFLICT,
    ):
        super().__init__(message, name, status_code)


class InvalidDimensionsError(BadInputError):
    """
    Raised when dimension values fail validation checks.

    Dimensions must be positive integers for valid vector operations.
    """

    ERROR_NAME = "InvalidDimensionsError"
    DEFAULT_MESSAGE = "Dimensions must be positive integers."

    def __init__(
        self,
        name: str = ERROR_NAME,
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ):
        super().__init__(self.DEFAULT_MESSAGE, name, status_code)


class DimensionOutOfRangeError(BadInputError):
    """
    Raised when a dimension index exceeds the valid range.

    Parameters
    ----------
    dimension : int
        The invalid dimension index that was provided.
    max_index : int
        The maximum valid dimension index.
    """

    ERROR_NAME = "DimensionOutOfRangeError"

    def __init__(
        self,
        dimension: int,
        max_index: int,
        name: str = ERROR_NAME,
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ):
        error_msg = f"Dimension {dimension} exceeds valid range (0 to {max_index})."
        super().__init__(error_msg, name, status_code)
