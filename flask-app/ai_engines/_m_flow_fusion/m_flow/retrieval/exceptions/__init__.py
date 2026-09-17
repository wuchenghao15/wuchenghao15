"""Re-exports retrieval pipeline failures for callers outside this package."""

from .exceptions import CypherSearchError, RecallModeNotSupported

__all__: list[str] = ["CypherSearchError", "RecallModeNotSupported"]
