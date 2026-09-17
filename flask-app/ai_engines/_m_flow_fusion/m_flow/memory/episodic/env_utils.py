# m_flow/memory/episodic/env_utils.py
"""
Environment variable utility functions

Provides unified environment variable reading functions supporting boolean, integer, and float types.
Avoids duplicate definitions of the same utility functions across modules.

Phase 6C: Unified environment variable functions
Event-Level Sections: Added environment variable switches
"""

from __future__ import annotations

import os
from typing import Optional


def as_bool_env(name: str, default: bool = False) -> bool:
    """
    Read boolean value from environment variable

    Supported True values: "1", "true", "yes", "y", "on" (case-insensitive)
    Supported False values: "0", "false", "no", "n", "off" (case-insensitive)

    Args:
        name: Environment variable name
        default: Default value (used when environment variable doesn't exist or cannot be parsed)

    Returns:
        Boolean value
    """
    val = os.getenv(name)
    if val is None:
        return default

    val = val.strip().lower()
    if val in ("1", "true", "yes", "y", "on"):
        return True
    if val in ("0", "false", "no", "n", "off"):
        return False

    return default


def as_int_env(name: str, default: int) -> int:
    """
    Read integer value from environment variable

    Args:
        name: Environment variable name
        default: Default value (used when environment variable doesn't exist or cannot be parsed)

    Returns:
        Integer value
    """
    raw = os.getenv(name)
    if raw is None:
        return default

    try:
        return int(raw.strip())
    except (ValueError, TypeError):
        return default


def as_float_env(name: str, default: float) -> float:
    """
    Read float value from environment variable

    Args:
        name: Environment variable name
        default: Default value (used when environment variable doesn't exist or cannot be parsed)

    Returns:
        Float value
    """
    raw = os.getenv(name)
    if raw is None:
        return default

    try:
        return float(raw.strip())
    except (ValueError, TypeError):
        return default


def as_str_env(name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Read string value from environment variable

    Args:
        name: Environment variable name
        default: Default value (used when environment variable doesn't exist)

    Returns:
        String value or None
    """
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip() or default


# ============================================================
# Indexing Environment Variable Switches
# ============================================================

# Whether to skip FragmentDigest_text indexing
# When enabled, FragmentDigest will not be indexed to vector database
MFLOW_SKIP_TEXTSUMMARY_INDEX = as_bool_env("MFLOW_SKIP_TEXTSUMMARY_INDEX", True)
