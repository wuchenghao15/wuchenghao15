# m_flow/memory/procedural/versioning/__init__.py
"""
Version management: conflict detection and version diff

Conflict detection and version diff.
"""

from .conflict_detector import (
    detect_conflict,
    ConflictLevel,
    ConflictResult,
    ConflictDetector,
)
from .generate_version_diff import (
    generate_version_diff,
    VersionDiff,
)

__all__ = [
    "detect_conflict",
    "ConflictLevel",
    "ConflictResult",
    "ConflictDetector",
    "generate_version_diff",
    "VersionDiff",
]
