"""
Recall mode enumeration for memory search operations.
"""

from __future__ import annotations

from enum import Enum


class RecallMode(str, Enum):
    """
    Identifiers for supported retrieval strategies.

    Each value maps to a registered retriever in the search subsystem.
    """

    # Lexical / keyword-based
    CHUNKS_LEXICAL = "CHUNKS_LEXICAL"

    # Triplet-based retrieval (vector search → graph triplet ranking)
    TRIPLET_COMPLETION = "TRIPLET_COMPLETION"

    # Direct Cypher query execution
    CYPHER = "CYPHER"

    # Context-aware memory retrieval
    EPISODIC = "EPISODIC"
    PROCEDURAL = "PROCEDURAL"
