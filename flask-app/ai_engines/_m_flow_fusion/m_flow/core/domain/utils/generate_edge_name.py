from __future__ import annotations

import re

# Pre-compiled pattern matching characters to be replaced or stripped
_NORMALIZE_PATTERN = re.compile(r"[ ']")

# Mapping: space → underscore; apostrophe → removed
_CHAR_MAP: dict[str, str] = {" ": "_"}


def generate_edge_name(name: str) -> str:
    """Return a normalised form of *name* suitable for use as an edge label.

    Lowercases the input, converts whitespace to underscores, and removes
    apostrophe characters so the result is safe for graph storage.
    """
    lowered = name.lower()
    return _NORMALIZE_PATTERN.sub(lambda hit: _CHAR_MAP.get(hit.group(), ""), lowered)
