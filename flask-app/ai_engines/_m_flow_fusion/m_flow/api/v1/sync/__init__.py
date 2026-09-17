"""
Sync Module for M-flow API v1.

Provides data synchronization capabilities between local files and the M-flow system.
Includes utilities for checking file hashes, detecting changes, and pruning stale data.
"""

# Import core sync functionality
from .sync import sync as sync

# Request models for sync operations
from .sync import CheckMissingHashesRequest as CheckMissingHashesRequest
from .sync import PruneDatasetRequest as PruneDatasetRequest

# Response models for sync operations
from .sync import SyncResponse as SyncResponse
from .sync import CheckHashesDiffResponse as CheckHashesDiffResponse

# Data models for file information
from .sync import LocalFileInfo as LocalFileInfo

# Define public API surface
__all__: list[str] = [
    # Core function
    "sync",
    # Request types
    "CheckMissingHashesRequest",
    "PruneDatasetRequest",
    # Response types
    "SyncResponse",
    "CheckHashesDiffResponse",
    # Data types
    "LocalFileInfo",
]
