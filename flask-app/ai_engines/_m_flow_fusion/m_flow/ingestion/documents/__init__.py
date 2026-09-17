"""
Document Processing Module
==========================

Utilities for classifying and extracting content from documents.
"""

from __future__ import annotations

from .classify_documents import detect_format
from .extract_chunks_from_documents import segment_documents

__all__ = [
    "detect_format",
    "segment_documents",
]
