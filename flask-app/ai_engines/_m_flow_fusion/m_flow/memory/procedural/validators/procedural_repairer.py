# m_flow/memory/procedural/validators/procedural_repairer.py
"""
Procedure automatic repairer

Automatically repair Procedure Bundle based on validation issues.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from m_flow.shared.tracing import TraceManager

from .procedural_contract import ValidationIssue
from .procedural_validator import ProcedureBundle, validate_procedure_bundle


class RepairAction(Enum):
    """Repair action type"""

    ADD_MISSING = "add_missing"
    SET_DEFAULT = "set_default"
    REORDER = "reorder"
    DEDUPLICATE = "deduplicate"
    TRUNCATE = "truncate"
    REBUILD = "rebuild"
    LLM_REWRITE = "llm_rewrite"


@dataclass
class RepairResult:
    """Repair result"""

    success: bool
    bundle: ProcedureBundle
    actions: List[Dict[str, Any]] = field(default_factory=list)
    remaining_issues: List[ValidationIssue] = field(default_factory=list)


def repair_procedure_bundle(
    bundle: ProcedureBundle,
    issues: List[ValidationIssue],
    use_llm: bool = False,
) -> RepairResult:
    """
    Automatically repair Procedure Bundle.

    Args:
        bundle: Bundle to repair
        issues: List of validation issues
        use_llm: Whether to use LLM repair (only when deterministic cannot repair)

    Returns:
        RepairResult
    """
    actions: List[Dict[str, Any]] = []

    for issue in issues:
        repaired = _repair_issue(bundle, issue)
        if repaired:
            actions.append(
                {
                    "issue_code": issue.code,
                    "action": repaired["action"].value,
                    "detail": repaired.get("detail", ""),
                }
            )

    # Re-validate
    ok, remaining = validate_procedure_bundle(bundle, strict=False)

    # If still has issues and LLM allowed, try LLM repair
    if remaining and use_llm:
        llm_actions = _llm_repair(bundle, remaining)
        actions.extend(llm_actions)
        ok, remaining = validate_procedure_bundle(bundle, strict=False)

    # Tracing
    TraceManager.event(
        "procedural.repair",
        {
            "bundle_id": bundle.procedure_id or bundle.procedure_key,
            "actions_count": len(actions),
            "remaining_issues": len(remaining),
            "action_types": [a["action"] for a in actions],
        },
    )

    return RepairResult(
        success=ok,
        bundle=bundle,
        actions=actions,
        remaining_issues=remaining,
    )


def _repair_issue(
    bundle: ProcedureBundle,
    issue: ValidationIssue,
) -> Optional[Dict[str, Any]]:
    """Try to repair a single issue"""

    code = issue.code

    # ========== Identity repair ==========

    if code == "PROCEDURE_KEY_REQUIRED":
        # Generate key from name or summary
        if bundle.name:
            key = _normalize_to_key(bundle.name)
            bundle.procedure_key = key
            bundle.signature = key
            return {"action": RepairAction.SET_DEFAULT, "detail": f"generated key: {key}"}

    if code == "VERSION_NUM_POSITIVE":
        bundle.version = 1
        return {"action": RepairAction.SET_DEFAULT, "detail": "set version=1"}

    if code == "STATUS_VALID":
        bundle.status = "active"
        return {"action": RepairAction.SET_DEFAULT, "detail": "set status=active"}

    # ========== Structure repair ==========

    if code == "HAS_STEPS_PACK":
        bundle.steps_pack = {
            "id": "",
            "name": f"{bundle.name}_steps",
            "search_text": bundle.search_text or bundle.name,
            "anchor_text": "Steps: (to be filled)",
            "description": "",
            "step_points": [],
        }
        return {"action": RepairAction.ADD_MISSING, "detail": "created empty StepsPack"}

    if code == "HAS_CONTEXT_PACK":
        bundle.context_pack = {
            "id": "",
            "name": f"{bundle.name}_context",
            "search_text": bundle.search_text or bundle.name,
            "anchor_text": "When: Not specified\nWhy: Not specified\nBoundary: Not specified",
            "description": "",
            "context_points": [],
        }
        return {"action": RepairAction.ADD_MISSING, "detail": "created empty ContextPack"}

    if code == "STEPS_PACK_HAS_SEARCH_TEXT":
        if bundle.steps_pack:
            bundle.steps_pack["search_text"] = _extract_search_text(bundle.steps_pack.get("anchor_text") or bundle.name)
            return {"action": RepairAction.REBUILD, "detail": "generated search_text from anchor"}

    if code == "STEPS_PACK_HAS_ANCHOR_TEXT":
        if bundle.steps_pack:
            # Rebuild from step_points
            points = bundle.steps_pack.get("step_points") or []
            if points:
                lines = []
                for i, pt in enumerate(points, 1):
                    lines.append(f"{i}. {pt.get('name', '')}")
                bundle.steps_pack["anchor_text"] = "\n".join(lines)
            else:
                bundle.steps_pack["anchor_text"] = f"Steps for {bundle.name}"
            return {"action": RepairAction.REBUILD, "detail": "rebuilt anchor_text from points"}

    if code == "CONTEXT_PACK_HAS_SEARCH_TEXT":
        if bundle.context_pack:
            bundle.context_pack["search_text"] = _extract_search_text(
                bundle.context_pack.get("anchor_text") or bundle.name
            )
            return {"action": RepairAction.REBUILD, "detail": "generated search_text from anchor"}

    if code == "CONTEXT_PACK_HAS_ANCHOR_TEXT":
        if bundle.context_pack:
            # Rebuild from fields
            when = bundle.context_pack.get("when_text") or "Not specified"
            why = bundle.context_pack.get("why_text") or "Not specified"
            boundary = bundle.context_pack.get("boundary_text") or "Not specified"
            bundle.context_pack["anchor_text"] = f"When: {when}\nWhy: {why}\nBoundary: {boundary}"
            return {"action": RepairAction.REBUILD, "detail": "rebuilt anchor_text from fields"}

    # ========== Context completeness repair ==========

    if code == "CONTEXT_HAS_WHEN":
        if bundle.context_pack:
            _ensure_context_section(bundle.context_pack, "When")
            return {"action": RepairAction.ADD_MISSING, "detail": "added When section"}

    if code == "CONTEXT_HAS_WHY":
        if bundle.context_pack:
            _ensure_context_section(bundle.context_pack, "Why")
            return {"action": RepairAction.ADD_MISSING, "detail": "added Why section"}

    if code == "CONTEXT_HAS_BOUNDARY":
        if bundle.context_pack:
            _ensure_context_section(bundle.context_pack, "Boundary")
            return {"action": RepairAction.ADD_MISSING, "detail": "added Boundary section"}

    # ========== Step order repair ==========

    if code == "STEP_POINTS_NO_DUPLICATE_INDEX":
        if bundle.steps_pack:
            points = bundle.steps_pack.get("step_points") or []
            for i, pt in enumerate(points, 1):
                pt["order_index"] = i
                pt["step_number"] = i
            return {"action": RepairAction.REORDER, "detail": f"reordered {len(points)} points"}

    return None


def _normalize_to_key(text: str) -> str:
    """Convert text to normalized key"""
    # Remove special characters, convert to lowercase, join with underscores
    text = text.lower().strip()
    text = re.sub(r"[^\w\s\u4e00-\u9fff]", "", text)  # Keep Chinese, English, and numbers
    text = re.sub(r"\s+", "_", text)
    text = text[:50]  # Limit length
    return text or "unknown_procedure"


def _extract_search_text(text: str) -> str:
    """Extract search keywords from text"""
    # Take first 100 characters, remove newlines
    text = text.replace("\n", " ").replace("\r", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:100]


def _ensure_context_section(ctx: Dict[str, Any], section: str) -> None:
    """Ensure context contains specified section"""
    anchor = ctx.get("anchor_text") or ""
    desc = ctx.get("description") or ""

    # Check if already exists
    section_lower = section.lower()
    if f"{section_lower}:" in anchor.lower() or f"{section_lower}:" in desc.lower():
        return

    # Add to anchor_text
    addition = f"\n{section}: Not specified"
    ctx["anchor_text"] = anchor + addition

    # Set corresponding field
    field_name = f"{section_lower}_text"
    if field_name in ("when_text", "why_text", "boundary_text"):
        ctx[field_name] = "Not specified"


def _llm_repair(
    bundle: ProcedureBundle,
    issues: List[ValidationIssue],
) -> List[Dict[str, Any]]:
    """Use LLM repair (only when deterministic cannot repair)"""
    # Temporarily return empty, can integrate LLM later
    # For example: summary extremely incoherent, context semantic missing
    return []


# ========== Convenience Functions ==========


def validate_and_repair(
    bundle: ProcedureBundle,
    use_llm: bool = False,
) -> Tuple[bool, ProcedureBundle, List[Dict[str, Any]]]:
    """
    Validate and repair bundle.

    Returns:
        (ok, repaired_bundle, actions)
    """
    ok, issues = validate_procedure_bundle(bundle, strict=False)

    if ok:
        return True, bundle, []

    result = repair_procedure_bundle(bundle, issues, use_llm=use_llm)
    return result.success, result.bundle, result.actions
