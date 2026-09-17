"""
Chunking Utilities
==================

Text segmentation strategies for different granularities.
"""

from __future__ import annotations

from .split_paragraphs import split_paragraphs
from .split_rows import split_rows
from .split_sentences import split_sentences
from .split_words import split_words
from .remove_disconnected_chunks import remove_disconnected_chunks

__all__ = [
    "split_paragraphs",
    "split_rows",
    "split_sentences",
    "split_words",
    "remove_disconnected_chunks",
]
