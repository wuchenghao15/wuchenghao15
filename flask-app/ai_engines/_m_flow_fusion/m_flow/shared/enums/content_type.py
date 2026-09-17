"""
Content type declaration for explicit content routing.

This enum replaces automatic dialog detection with explicit user declaration,
ensuring safe and predictable sentence splitting behavior.
"""

from enum import Enum


class ContentType(str, Enum):
    """
    Content type declaration for sentence splitting strategy.

    When enable_content_routing=True (default), this parameter is required
    in ingest() and memorize() calls.

    Attributes:
        TEXT: Regular text content (articles, documents, notes, code comments).
              Splits by sentence boundaries (periods, exclamation marks, question marks).

        DIALOG: Conversation content (chat logs, meeting notes, interviews, scripts).
                Splits by speaker utterances, keeping each speaker's turn as one unit.
                Expected format: "[timestamp] Speaker: message" or "Speaker: message"

    Examples:
        >>> from m_flow import ContentType
        >>> await m_flow.ingest(article, content_type=ContentType.TEXT)
        >>> await m_flow.ingest(chat_logs, content_type=ContentType.DIALOG)
    """

    TEXT = "text"
    DIALOG = "dialog"
