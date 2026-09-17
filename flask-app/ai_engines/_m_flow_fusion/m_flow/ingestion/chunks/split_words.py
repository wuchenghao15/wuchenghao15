"""
Word-level tokenizer preserving whitespace for exact reconstruction.
"""

from __future__ import annotations

import re
from typing import Iterator, Literal, Tuple

_RE_SENT_END = re.compile(r"[.;!?…。！？]")
_RE_PARA_END = re.compile(r"[\n\r]")

TokenKind = Literal["word", "sentence_end", "paragraph_end"]


def _lookahead_upper(text: str, pos: int) -> bool:
    """Return True if next non-whitespace char is uppercase."""
    idx = pos + 1
    length = len(text)
    while idx < length:
        ch = text[idx]
        if ch not in (" ", "\n", "\r"):
            return ch.isupper()
        idx += 1
    return False


def is_real_paragraph_end(last_char: str, pos: int, text: str) -> bool:
    """
    Heuristic: consider a position a paragraph boundary if the last char
    is a sentence-ending punctuation or followed by an uppercase letter.
    """
    if _RE_SENT_END.match(last_char):
        return True
    return _lookahead_upper(text, pos)


def split_words(data: str) -> Iterator[Tuple[str, TokenKind]]:
    """
    Yield (token, kind) tuples where *kind* is one of:

    * ``"word"`` – regular word token (includes trailing space if any)
    * ``"sentence_end"`` – sentence-ending punctuation plus trailing space
    * ``"paragraph_end"`` – same, but followed by newline

    Concatenating all tokens reproduces *data* exactly.
    """
    buf = ""
    idx = 0
    length = len(data)

    while idx < length:
        ch = data[idx]
        buf += ch

        if ch == " ":
            yield buf, "word"
            buf = ""
            idx += 1
            continue

        if _RE_SENT_END.match(ch):
            # consume trailing spaces
            nxt = idx + 1
            while nxt < length and data[nxt] == " ":
                buf += data[nxt]
                nxt += 1
            is_para = nxt < length and _RE_PARA_END.match(data[nxt])
            yield buf, ("paragraph_end" if is_para else "sentence_end")
            buf = ""
            idx = nxt
            continue

        idx += 1

    if buf:
        yield buf, "word"
