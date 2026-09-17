# m_flow/memory/episodic/aliases.py
"""
Alias filtering and concatenation utilities for episodic memory.

Functions:
- is_bad_alias: Check if alias is too short/long/template/generic
- clean_aliases: Clean alias list (dedupe, filter bad ones)
- make_aliases_text: Generate indexed aliases_text
"""

import re
from typing import List, Optional

# Import _nfkc from normalization module (single source of truth)
from m_flow.memory.episodic.normalization import _nfkc


# Template-like prefixes (low information density)
_BAD_PREFIX = (
    "本段",
    "上述",
    "该内容",
    "这里",
    "这部分",
    "这段",
    "本文",
    "this section",
    "the above",
    "this part",
    "here",
)

# Too generic words (no specific anchor)
_TOO_GENERIC = {
    "风险",
    "决策",
    "进展",
    "总结",
    "原因",
    "影响",
    "问题",
    "方案",
    "计划",
    "结果",
    "risk",
    "decision",
    "progress",
    "summary",
    "reason",
    "impact",
    "issue",
    "plan",
    "result",
}


def _normalize_for_compare(text: str) -> str:
    """Normalize text for comparison (whitespace/case/fullwidth)"""
    if not text:
        return ""
    t = _nfkc(text)
    t = t.lower()
    t = re.sub(r"\s+", " ", t)
    return t


def is_bad_alias(s: str, max_len: int = 50) -> bool:
    """
    Check if alias is unusable (too short/template/generic).

    Args:
        s: alias string
        max_len: maximum length allowed (default 50, use 0 to disable length check)

    Returns:
        True if should be filtered out
    """
    if not s:
        return True
    s = _nfkc(s)
    if len(s) < 3:  # too short
        return True
    # Length check is now optional via max_len parameter
    if max_len > 0 and len(s) > max_len:
        return True
    if s.startswith(_BAD_PREFIX):  # template-like prefix
        return True
    if s in _TOO_GENERIC:  # too generic
        return True
    return False


def clean_aliases(
    search_text: str,
    aliases: Optional[List[str]],
    max_aliases: int = 10,
) -> List[str]:
    """
    Clean alias list:
    - Remove bad aliases
    - Remove duplicates of search_text
    - Dedupe (normalized comparison)
    - Keep at most max_aliases

    Args:
        search_text: facet's main handle
        aliases: original alias list
        max_aliases: max to keep

    Returns:
        Cleaned alias list
    """
    st = _nfkc(search_text or "")
    st_norm = _normalize_for_compare(st)
    out: List[str] = []
    seen = {st_norm}  # search_text counts as seen

    for a in aliases or []:
        a = _nfkc(a)
        if is_bad_alias(a):
            continue
        a_norm = _normalize_for_compare(a)
        if a_norm in seen:
            continue
        seen.add(a_norm)
        out.append(a)
        if len(out) >= max_aliases:
            break

    return out


def make_aliases_text(aliases: List[str], max_chars: int = 400) -> Optional[str]:
    """
    Generate indexed aliases_text.

    Args:
        aliases: cleaned alias list
        max_chars: max characters (truncate if exceeded)

    Returns:
        "\\n".join(aliases) or None if empty
    """
    if not aliases:
        return None
    txt = "\n".join([_nfkc(a) for a in aliases if _nfkc(a)])
    txt = txt.strip()
    if not txt:
        return None
    if len(txt) > max_chars:
        txt = txt[: max_chars - 1].rstrip() + "…"
    return txt
