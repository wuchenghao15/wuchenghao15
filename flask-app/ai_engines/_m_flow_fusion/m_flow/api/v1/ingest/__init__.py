"""
M-flow one-step ingestion module.

Provides simplified ingest() API that combines add() and memorize() into a single call.
"""

from .ingest import ingest, IngestResult, IngestStatus

__all__ = ["ingest", "IngestResult", "IngestStatus"]
