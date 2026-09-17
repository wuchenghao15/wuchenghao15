"""Axon configuration — ignore patterns and language detection."""

from axon.config.ignore import DEFAULT_IGNORE_PATTERNS, load_gitignore, should_ignore
from axon.config.languages import SUPPORTED_EXTENSIONS, get_language, is_supported

__all__ = [
    "DEFAULT_IGNORE_PATTERNS",
    "SUPPORTED_EXTENSIONS",
    "get_language",
    "is_supported",
    "load_gitignore",
    "should_ignore",
]
