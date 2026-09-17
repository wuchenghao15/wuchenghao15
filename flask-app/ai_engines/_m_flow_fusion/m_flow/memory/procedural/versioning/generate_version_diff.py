# m_flow/memory/procedural/versioning/generate_version_diff.py
"""
Version diff and change summary

Generate change descriptions between versions.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from m_flow.shared.tracing import TraceManager
from m_flow.shared.logging_utils import get_logger

logger = get_logger()


@dataclass
class VersionDiff:
    """Version diff result"""

    change_notes: str  # User-facing change description
    diff_summary: Dict[str, Any]  # Structured diff
    old_version: int
    new_version: int
    supersedes_id: Optional[str] = None

    # Change statistics
    steps_added: int = 0
    steps_removed: int = 0
    steps_modified: int = 0
    context_changed: bool = False
    boundary_changed: bool = False


def generate_version_diff(
    old_proc: Dict[str, Any],
    new_proc: Dict[str, Any],
    use_llm: bool = False,
) -> VersionDiff:
    """
    Generate version diff.

    Args:
        old_proc: Old version Procedure structure
        new_proc: New version Procedure structure
        use_llm: Whether to use LLM to generate more natural change descriptions

    Returns:
        VersionDiff
    """
    old_version = old_proc.get("version", 1)
    new_version = old_version + 1
    supersedes_id = old_proc.get("procedure_id") or old_proc.get("id")

    # ========== Calculate Steps Diff ==========

    old_steps = _extract_steps(old_proc)
    new_steps = _extract_steps(new_proc)

    old_step_set = set(old_steps)
    new_step_set = set(new_steps)

    steps_added = len(new_step_set - old_step_set)
    steps_removed = len(old_step_set - new_step_set)

    # Check order changes
    steps_modified = 0
    common = old_step_set & new_step_set
    for step in common:
        old_idx = old_steps.index(step) if step in old_steps else -1
        new_idx = new_steps.index(step) if step in new_steps else -1
        if old_idx != new_idx:
            steps_modified += 1

    # ========== Calculate Context Diff ==========

    old_ctx = old_proc.get("context_pack") or {}
    new_ctx = new_proc.get("context_pack") or {}

    context_changed = old_ctx.get("when_text") != new_ctx.get("when_text") or old_ctx.get("why_text") != new_ctx.get(
        "why_text"
    )

    boundary_changed = old_ctx.get("boundary_text") != new_ctx.get("boundary_text")

    # ========== Generate Change Notes ==========

    changes = []

    if steps_added > 0:
        changes.append(f"Added {steps_added} step(s)")
    if steps_removed > 0:
        changes.append(f"Removed {steps_removed} step(s)")
    if steps_modified > 0:
        changes.append(f"Reordered {steps_modified} step(s)")
    if boundary_changed:
        changes.append("Boundary conditions updated")
    if context_changed:
        changes.append("Context description updated")

    if not changes:
        change_notes = "Minor optimizations, no major changes"
    else:
        change_notes = "; ".join(changes)

    # Structured diff
    diff_summary = {
        "steps": {
            "added": list(new_step_set - old_step_set)[:5],
            "removed": list(old_step_set - new_step_set)[:5],
            "added_count": steps_added,
            "removed_count": steps_removed,
            "modified_count": steps_modified,
        },
        "context": {
            "when_changed": old_ctx.get("when_text") != new_ctx.get("when_text"),
            "why_changed": old_ctx.get("why_text") != new_ctx.get("why_text"),
            "boundary_changed": boundary_changed,
        },
    }

    result = VersionDiff(
        change_notes=change_notes,
        diff_summary=diff_summary,
        old_version=old_version,
        new_version=new_version,
        supersedes_id=supersedes_id,
        steps_added=steps_added,
        steps_removed=steps_removed,
        steps_modified=steps_modified,
        context_changed=context_changed,
        boundary_changed=boundary_changed,
    )

    # Tracing
    TraceManager.event(
        "procedural.version.diff",
        {
            "old_version": old_version,
            "new_version": new_version,
            "supersedes_id": supersedes_id,
            "steps_added": steps_added,
            "steps_removed": steps_removed,
            "boundary_changed": boundary_changed,
            "change_notes": change_notes[:100],
        },
    )

    return result


def _extract_steps(proc: Dict[str, Any]) -> List[str]:
    """Extract step list"""
    steps = []

    steps_pack = proc.get("steps_pack") or {}

    # Extract from step_points
    points = steps_pack.get("step_points") or []
    for pt in points:
        name = pt.get("name") or pt.get("search_text") or ""
        if name:
            steps.append(_normalize_step(name))

    # If no points, parse from anchor_text
    if not steps:
        anchor = steps_pack.get("anchor_text") or ""
        for line in anchor.split("\n"):
            line = line.strip()
            if line:
                steps.append(_normalize_step(line))

    return steps


def _normalize_step(text: str) -> str:
    """Normalize step text"""
    import re

    text = text.strip()
    # Remove numbering
    text = re.sub(r"^\d+[\.\)]\s*", "", text)
    # Convert to lowercase
    text = text.lower()
    return text
