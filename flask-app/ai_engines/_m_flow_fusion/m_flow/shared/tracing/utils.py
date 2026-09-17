# m_flow/shared/tracing/utils.py
"""
P6-1: Trace Utilities

Convert payload to safe JSON (truncate, remove large objects, redact).
"""

from __future__ import annotations
import json
import math
from typing import Any, Dict

from .redaction import redact_text


def truncate(s: str, max_len: int) -> str:
    """Truncate string to specified length."""
    if s is None:
        return ""
    s = str(s)
    return s if len(s) <= max_len else s[:max_len] + "…(truncated)"


def _safe_number(x: Any) -> Any:
    """Handle special floating point numbers (NaN, Inf)."""
    try:
        if isinstance(x, float):
            if math.isnan(x) or math.isinf(x):
                return None
        return x
    except Exception:
        return None


def safe_payload(
    obj: Any,
    *,
    max_str_len: int = 800,
    max_list_len: int = 50,
    max_depth: int = 5,
) -> Any:
    """
    Convert any object to "JSON serializable + non-explosive + minimal leakage" form.

    Args:
        obj: Any object
        max_str_len: Maximum string length
        max_list_len: Maximum list/dict length
        max_depth: Maximum recursion depth

    Returns:
        Safe serializable object
    """
    if max_depth <= 0:
        return "<max_depth_reached>"

    if obj is None:
        return None

    if isinstance(obj, (bool, int)):
        return obj

    if isinstance(obj, float):
        return _safe_number(obj)

    if isinstance(obj, str):
        red, _ = redact_text(obj)
        return truncate(red, max_str_len)

    if isinstance(obj, bytes):
        return f"<bytes:{len(obj)}>"

    if isinstance(obj, dict):
        out: Dict[str, Any] = {}
        items = list(obj.items())[:max_list_len]
        for k, v in items:
            out[str(k)] = safe_payload(v, max_str_len=max_str_len, max_list_len=max_list_len, max_depth=max_depth - 1)
        if len(obj) > max_list_len:
            out["__truncated__"] = f"dict_size={len(obj)}"
        return out

    if isinstance(obj, (list, tuple, set)):
        lst = list(obj)
        out_list = [
            safe_payload(v, max_str_len=max_str_len, max_list_len=max_list_len, max_depth=max_depth - 1)
            for v in lst[:max_list_len]
        ]
        if len(lst) > max_list_len:
            out_list.append(f"<truncated_list size={len(lst)}>")
        return out_list

    # Common objects: those with __dict__
    if hasattr(obj, "__dict__"):
        return safe_payload(
            obj.__dict__,
            max_str_len=max_str_len,
            max_list_len=max_list_len,
            max_depth=max_depth - 1,
        )

    # Fallback
    return truncate(repr(obj), max_str_len)


def dumps_json(obj: Any) -> str:
    """Safely serialize to JSON string."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=False, default=str)
