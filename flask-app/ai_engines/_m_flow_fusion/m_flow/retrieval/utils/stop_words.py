"""
Stop word definitions for text preprocessing.

Provides common English stop words used to filter low-information
tokens during text processing and search operations.
"""

from __future__ import annotations

from typing import FrozenSet

# Immutable set of common English stop words
# Organized by grammatical category for maintainability
_ARTICLES = frozenset({"a", "an", "the"})
_CONJUNCTIONS = frozenset({"and", "or", "but"})
_PREPOSITIONS = frozenset(
    {
        "in",
        "on",
        "at",
        "to",
        "for",
        "with",
        "by",
        "about",
        "of",
        "from",
        "as",
    }
)
_PRONOUNS = frozenset(
    {
        "it",
        "its",
        "they",
        "them",
        "their",
        "he",
        "she",
        "his",
        "her",
        "him",
        "we",
        "our",
        "you",
        "your",
    }
)
_DEMONSTRATIVES = frozenset({"this", "that", "these", "those"})
_VERBS_BE = frozenset({"is", "are", "was", "were", "be", "been", "being"})
_VERBS_HAVE = frozenset({"have", "has", "had"})
_VERBS_DO = frozenset({"do", "does", "did"})
_MODALS = frozenset(
    {
        "can",
        "could",
        "will",
        "would",
        "shall",
        "should",
        "may",
        "might",
        "must",
    }
)
_INTERROGATIVES = frozenset(
    {
        "when",
        "where",
        "which",
        "who",
        "whom",
        "whose",
        "why",
        "how",
    }
)
_NEGATION = frozenset({"not"})

# Combined default stop word set
DEFAULT_STOP_WORDS: FrozenSet[str] = (
    _ARTICLES
    | _CONJUNCTIONS
    | _PREPOSITIONS
    | _PRONOUNS
    | _DEMONSTRATIVES
    | _VERBS_BE
    | _VERBS_HAVE
    | _VERBS_DO
    | _MODALS
    | _INTERROGATIVES
    | _NEGATION
)


def is_stop_word(word: str) -> bool:
    """Check if a word is a stop word."""
    return word.lower() in DEFAULT_STOP_WORDS


def filter_stop_words(tokens: list[str]) -> list[str]:
    """Remove stop words from a list of tokens."""
    return [t for t in tokens if t.lower() not in DEFAULT_STOP_WORDS]
