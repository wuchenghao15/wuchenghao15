"""
Custom exceptions for the Mflow API.

This module defines a set of exceptions for handling various graph errors
"""

from .exceptions import (
    ConceptNotFoundError as ConceptNotFoundError,
    ConceptAlreadyExistsError as ConceptAlreadyExistsError,
    InvalidDimensionsError as InvalidDimensionsError,
    DimensionOutOfRangeError as DimensionOutOfRangeError,
)
