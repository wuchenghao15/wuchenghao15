"""
Exception types for Neptune Analytics adapter.
"""

from __future__ import annotations

from fastapi import status as http_status

from m_flow.exceptions import (
    ConfigError,
    InternalError,
    TransientError,
    BadInputError,
)

# HTTP codes
_500 = http_status.HTTP_500_INTERNAL_SERVER_ERROR
_504 = http_status.HTTP_504_GATEWAY_TIMEOUT
_429 = http_status.HTTP_429_TOO_MANY_REQUESTS
_404 = http_status.HTTP_404_NOT_FOUND
_401 = http_status.HTTP_401_UNAUTHORIZED
_400 = http_status.HTTP_400_BAD_REQUEST


class NeptuneAnalyticsError(InternalError):
    """Base for all Neptune exceptions."""

    def __init__(self, msg: str = "Graph operation failed", code: int = _500):
        super().__init__(msg, self.__class__.__name__, code)


class NeptuneAnalyticsConnectionError(TransientError):
    """Network or endpoint issues."""

    def __init__(self, msg: str = "Cannot connect to graph service", code: int = _404):
        super().__init__(msg, self.__class__.__name__, code)


class NeptuneAnalyticsQueryError(BadInputError):
    """Bad Cypher syntax or semantics."""

    def __init__(self, msg: str = "Query error", code: int = _400):
        super().__init__(msg, self.__class__.__name__, code)


class NeptuneAnalyticsAuthenticationError(ConfigError):
    """AWS credential rejection."""

    def __init__(self, msg: str = "Credential error", code: int = _401):
        super().__init__(msg, self.__class__.__name__, code)


class NeptuneAnalyticsConfigurationError(ConfigError):
    """Missing or invalid setup."""

    def __init__(self, msg: str = "Config error", code: int = _500):
        super().__init__(msg, self.__class__.__name__, code)


class NeptuneAnalyticsTimeoutError(TransientError):
    """Deadline exceeded."""

    def __init__(self, msg: str = "Timeout", code: int = _504):
        super().__init__(msg, self.__class__.__name__, code)


class NeptuneAnalyticsThrottlingError(TransientError):
    """Rate limit hit."""

    def __init__(self, msg: str = "Throttled", code: int = _429):
        super().__init__(msg, self.__class__.__name__, code)


class NeptuneAnalyticsResourceNotFoundError(BadInputError):
    """Requested entity missing."""

    def __init__(self, msg: str = "Not found", code: int = _404):
        super().__init__(msg, self.__class__.__name__, code)


class NeptuneAnalyticsInvalidParameterError(BadInputError):
    """Bad input parameters."""

    def __init__(self, msg: str = "Invalid param", code: int = _400):
        super().__init__(msg, self.__class__.__name__, code)
