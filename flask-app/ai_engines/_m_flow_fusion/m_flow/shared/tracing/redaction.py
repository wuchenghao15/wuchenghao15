# m_flow/shared/tracing/redaction.py
"""
P6-1: Trace Redaction

Simple redaction: ensure traces don't write keys/privacy to disk.
"""

from __future__ import annotations
import re
from typing import Tuple, List, Pattern

# Redaction pattern list
_PATTERNS: List[Tuple[Pattern, str]] = [
    # OpenAI / general api key style (sk-xxx, sk-proj-xxx)
    (re.compile(r"\bsk-[A-Za-z0-9\-_]{20,}\b"), "sk-***REDACTED***"),
    # AWS access key
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "***REDACTED_AWS_KEY***"),
    # Private key blocks
    (
        re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----[\s\S]+?-----END [A-Z ]+PRIVATE KEY-----"),
        "***REDACTED_PRIVATE_KEY***",
    ),
    # password-like fields
    (re.compile(r"(?i)(password|passwd|pwd)\s*[:=]\s*([^\s,;]+)"), r"\1=***REDACTED***"),
    (re.compile(r"(?i)(token|secret|api_key|apikey)\s*[:=]\s*([^\s,;]+)"), r"\1=***REDACTED***"),
    # Bearer token
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9\-_\.]+"), "Bearer ***REDACTED***"),
    # Connection strings
    (re.compile(r"(?i)(mongodb|mysql|postgres|redis)://[^\s]+"), r"\1://***REDACTED***"),
]


def redact_text(text: str) -> Tuple[str, bool]:
    """
    Perform redaction on text.

    Args:
        text: Original text

    Returns:
        (Redacted text, whether redaction occurred)
    """
    if not text:
        return text, False

    changed = False
    out = text

    for pat, repl in _PATTERNS:
        new = pat.sub(repl, out)
        if new != out:
            changed = True
            out = new

    return out, changed
