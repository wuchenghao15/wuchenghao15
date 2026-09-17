# m_flow/memory/procedural/procedural_safety.py
"""
Procedural Safety Utilities

Security-related utility functions:
- redact_secrets: Redaction processing (API key, token, password, etc.)
- contains_dangerous_content: Detect dangerous content (violence, illegal, etc.)

Design principles:
- No hard blocking, but used for labeling/redaction
- Security first: redact if in doubt
"""

import re
from typing import List, Tuple


# -----------------------------
# Secret Redaction
# -----------------------------

# Regex patterns for sensitive information
_SECRET_PATTERNS: List[Tuple[str, str]] = [
    # API keys, tokens
    (r'(?i)(api[_-]?key|apikey|api_secret)["\'\s:=]+[\w\-]{16,}', "[REDACTED_API_KEY]"),
    (r'(?i)(token|access[_-]?token|auth[_-]?token)["\'\s:=]+[\w\-]{16,}', "[REDACTED_TOKEN]"),
    # Passwords
    (r'(?i)(password|passwd|pwd)["\'\s:=]+\S+', "[REDACTED_PASSWORD]"),
    # AWS credentials
    (r'(?i)(aws[_-]?access[_-]?key[_-]?id)["\'\s:=]+[\w]{16,}', "[REDACTED_AWS_KEY]"),
    (r'(?i)(aws[_-]?secret[_-]?access[_-]?key)["\'\s:=]+[\w/+]{32,}', "[REDACTED_AWS_SECRET]"),
    # Private keys
    (
        r"-----BEGIN\s+(?:RSA\s+)?PRIVATE KEY-----[\s\S]*?-----END\s+(?:RSA\s+)?PRIVATE KEY-----",
        "[REDACTED_PRIVATE_KEY]",
    ),
    # Bearer tokens
    (r"(?i)bearer\s+[\w\-_.]{20,}", "[REDACTED_BEARER_TOKEN]"),
    # Connection strings
    (r'(?i)(connection[_-]?string|conn[_-]?str)["\'\s:=]+[^\s]+', "[REDACTED_CONN_STRING]"),
    # Generic long hex/base64 secrets
    (r'(?i)(secret|private|credential)["\'\s:=]+[A-Za-z0-9+/=]{32,}', "[REDACTED_SECRET]"),
]


def redact_secrets(text: str) -> str:
    """
    Redact sensitive information from text.

    Patterns:
    - API keys, tokens
    - Passwords
    - AWS credentials
    - Private keys
    - Bearer tokens
    - Connection strings

    Args:
        text: Input text that may contain secrets

    Returns:
        Text with secrets replaced by [REDACTED_*] placeholders
    """
    if not text:
        return ""
    result = text
    for pattern, replacement in _SECRET_PATTERNS:
        result = re.sub(pattern, replacement, result)
    return result


def has_redacted_content(text: str) -> bool:
    """Check if text has been redacted (contains [REDACTED_*] markers)."""
    return "[REDACTED_" in text


# -----------------------------
# Dangerous Content Detection
# -----------------------------

# Patterns for dangerous content (skip writing steps)
_DANGEROUS_PATTERNS: List[str] = [
    # Self-harm
    r"(?i)(self[_-]?harm|suicide|kill\s+yourself)",
    # Weapons/explosives
    r"(?i)(make\s+a?\s*bomb|explosive\s+device|weapon\s+manufacturing)",
    # Hacking/unauthorized access
    r"(?i)(hack\s+into|unauthorized\s+access|bypass\s+security)",
    # Malware
    r"(?i)(create\s+malware|write\s+virus|ransomware)",
    # Illegal activities
    r"(?i)(steal\s+credit|fraud\s+scheme|money\s+launder)",
]


def contains_dangerous_content(text: str) -> bool:
    """
    Check if text contains dangerous/illegal content.

    Used to skip writing steps that could be harmful if executed.

    Args:
        text: Input text to check

    Returns:
        True if dangerous content detected
    """
    if not text:
        return False
    for pattern in _DANGEROUS_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


# -----------------------------
# High-risk Operation Detection
# -----------------------------

# Patterns for high-risk operations (mark but don't block)
_HIGH_RISK_PATTERNS: List[str] = [
    # Production operations
    r"(?i)(production|prod)\s*(deploy|release|push)",
    # Delete operations
    r"(?i)(delete|drop|truncate|remove)\s*(database|table|collection|all)",
    # Irreversible operations
    r"(?i)(irreversible|cannot\s+undo|permanent)",
    # Force operations
    r"(?i)(--force|--hard|-f\s+)",
    # Root/admin operations
    r"(?i)(sudo|as\s+root|admin\s+rights)",
]


def has_high_risk_operations(text: str) -> bool:
    """
    Check if text contains high-risk operations.

    These operations are not blocked but should be marked for review.

    Args:
        text: Input text to check

    Returns:
        True if high-risk operations detected
    """
    if not text:
        return False
    for pattern in _HIGH_RISK_PATTERNS:
        if re.search(pattern, text):
            return True
    return False
