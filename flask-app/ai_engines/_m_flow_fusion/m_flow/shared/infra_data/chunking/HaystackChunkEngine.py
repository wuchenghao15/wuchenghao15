"""
Haystack integration for document chunking.

Provides a chunking engine that uses Haystack's document
preprocessing strategies for text segmentation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class HaystackChunkEngine:
    """
    Document chunker powered by Haystack preprocessing.

    This engine wraps Haystack's chunking strategies to provide
    configurable text segmentation for M-flow document processing.

    Attributes:
        chunk_strategy: The Haystack chunking strategy to use.
        source_data: Input data to be chunked.
        chunk_size: Target size for each chunk in characters.
        chunk_overlap: Number of characters to overlap between chunks.

    Example:
        >>> engine = HaystackChunkEngine(
        ...     chunk_size=512,
        ...     chunk_overlap=50,
        ... )
    """

    chunk_strategy: Optional[Any] = field(default=None)
    source_data: Optional[Any] = field(default=None)
    chunk_size: Optional[int] = field(default=None)
    chunk_overlap: Optional[int] = field(default=None)
