from __future__ import annotations

# Translation table: strip apostrophes while keeping everything else intact.
# Uses the three-argument form of str.maketrans where the third argument
# specifies characters to delete outright.
_STRIP_TABLE = str.maketrans("", "", "'")


def generate_node_name(name: str) -> str:
    """Produce a canonical node name by lower-casing and stripping apostrophes.

    The returned value is deterministic and safe for use as a graph-store key.
    """
    return name.lower().translate(_STRIP_TABLE)
