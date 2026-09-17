"""
Adapter exception types.
"""

from __future__ import annotations

from fastapi import status as http

from m_flow.exceptions import (
    ConfigError,
    InternalError,
    BadInputError,
)

_422 = http.HTTP_422_UNPROCESSABLE_ENTITY
_404 = http.HTTP_404_NOT_FOUND
_409 = http.HTTP_409_CONFLICT
_400 = http.HTTP_400_BAD_REQUEST
_503 = http.HTTP_503_SERVICE_UNAVAILABLE


class DatabaseNotCreatedError(InternalError):
    """Database not initialized."""

    def __init__(self, msg: str = "Call setup() first", code: int = _422):
        super().__init__(msg, self.__class__.__name__, code)


class ConceptNotFoundError(BadInputError):
    """Requested entity missing."""

    def __init__(self, message: str = "Entity not found", code: int = _404):
        self.message = message
        self.name = self.__class__.__name__
        self.status_code = code


class ConceptAlreadyExistsError(BadInputError):
    """Duplicate entity creation."""

    def __init__(self, message: str = "Entity exists", code: int = _409):
        super().__init__(message, self.__class__.__name__, code)


class NodesetFilterNotSupportedError(ConfigError):
    """Graph DB does not support filter."""

    def __init__(self, message: str = "Filter unsupported", code: int = _404):
        self.message = message
        self.name = self.__class__.__name__
        self.status_code = code


class EmbeddingException(ConfigError):
    """Embedding operation failure."""

    def __init__(self, message: str = "Embedding error", code: int = _422):
        super().__init__(message, self.__class__.__name__, code)


class MissingQueryParameterError(BadInputError):
    """Neither text nor vector provided."""

    def __init__(self, code: int = _400):
        super().__init__("query_text or query_vector required", self.__class__.__name__, code)


class MutuallyExclusiveQueryParametersError(BadInputError):
    """Both text and vector provided."""

    def __init__(self, code: int = _400):
        super().__init__("Provide text or vector, not both", self.__class__.__name__, code)


class CacheConnectionError(ConfigError):
    """Cache service unreachable."""

    def __init__(self, message: str = "Cache unavailable", code: int = _503):
        super().__init__(message, self.__class__.__name__, code)


class SharedKuzuLockRequiresRedisError(ConfigError):
    """Redis required for shared Kuzu lock."""

    def __init__(self, message: str = "Redis required for shared lock", code: int = _400):
        super().__init__(message, self.__class__.__name__, code)
