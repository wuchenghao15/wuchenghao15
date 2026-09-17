"""
M-flow API Exception Classes.

This module exports custom exception types for the M-flow API layer.
These exceptions provide structured error handling for common scenarios
such as missing resources, invalid configurations, and data access issues.
"""

# Configuration-related exceptions
from .exceptions import InvalidConfigAttributeError as InvalidConfigAttributeError

# Document-related exceptions
from .exceptions import DocumentNotFoundError as DocumentNotFoundError
from .exceptions import DocumentSubgraphNotFoundError as DocumentSubgraphNotFoundError

# Dataset-related exceptions
from .exceptions import DatasetNotFoundError as DatasetNotFoundError

# General data exceptions
from .exceptions import DataNotFoundError as DataNotFoundError

# Node-related exceptions
from .exceptions import NodeNotFoundError as NodeNotFoundError

# Permission exceptions
from .exceptions import PermissionDeniedError as PermissionDeniedError

# Concurrency exceptions
from .exceptions import ConcurrentMemorizeError as ConcurrentMemorizeError

# Public API exports
__all__: list[str] = [
    "InvalidConfigAttributeError",
    "DocumentNotFoundError",
    "DocumentSubgraphNotFoundError",
    "DatasetNotFoundError",
    "DataNotFoundError",
    "NodeNotFoundError",
    "PermissionDeniedError",
    "ConcurrentMemorizeError",
]
