# m_flow/memory/procedural/validators/procedural_contract.py
"""
Data contract and invariant definitions for procedural memory

Define invariants that Procedure must satisfy.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class IssueSeverity(Enum):
    """Issue severity"""

    ERROR = "error"  # Must fix, otherwise should not write
    WARNING = "warning"  # Recommended to fix, but can write
    INFO = "info"  # Informational, can ignore


@dataclass
class ValidationIssue:
    """Validation issue"""

    code: str  # Issue code (e.g., "MISSING_CONTEXT_PACK")
    severity: IssueSeverity  # Severity
    message: str  # Description
    field_path: str = ""  # Issue field path (e.g., "context_pack.description")
    suggestion: str = ""  # Fix suggestion

    def __str__(self) -> str:
        return f"[{self.severity.value}] {self.code}: {self.message}"


class ProcedureContract:
    """
    Procedure data contract.

    Define all invariant rules:
    - Identity/version rules
    - Structure rules
    - Context completeness rules
    - Step order rules
    """

    # ========== Identity/Version Invariants ==========

    IDENTITY_RULES = {
        "PROCEDURE_KEY_REQUIRED": {
            "check": lambda p: bool(p.get("procedure_key") or p.get("signature")),
            "severity": IssueSeverity.ERROR,
            "message": "procedure_key or signature cannot be empty",
            "suggestion": "Use Identity Normalizer to generate canonical_key",
        },
        "VERSION_NUM_POSITIVE": {
            "check": lambda p: (p.get("version", 1) or 1) >= 1,
            "severity": IssueSeverity.ERROR,
            "message": "version_num must be a positive integer",
            "suggestion": "Set version = 1",
        },
        "STATUS_VALID": {
            "check": lambda p: p.get("status", "active") in ("active", "deprecated", "superseded"),
            "severity": IssueSeverity.WARNING,
            "message": "status must be one of active/deprecated/superseded",
            "suggestion": "Set status = 'active'",
        },
    }

    # ========== Structure Invariants ==========

    STRUCTURE_RULES = {
        "HAS_STEPS_PACK": {
            "check": lambda p: p.get("steps_pack") is not None,
            "severity": IssueSeverity.ERROR,
            "message": "StepsPack must exist",
            "suggestion": "Create empty StepsPack or generate from steps",
        },
        "HAS_CONTEXT_PACK": {
            "check": lambda p: p.get("context_pack") is not None,
            "severity": IssueSeverity.ERROR,
            "message": "ContextPack must exist",
            "suggestion": "Create empty ContextPack or generate from context",
        },
        "STEPS_PACK_HAS_SEARCH_TEXT": {
            "check": lambda p: bool((p.get("steps_pack") or {}).get("search_text")),
            "severity": IssueSeverity.WARNING,
            "message": "StepsPack should have search_text",
            "suggestion": "Extract keywords from anchor_text as search_text",
        },
        "STEPS_PACK_HAS_ANCHOR_TEXT": {
            "check": lambda p: bool((p.get("steps_pack") or {}).get("anchor_text")),
            "severity": IssueSeverity.WARNING,
            "message": "StepsPack should have anchor_text",
            "suggestion": "Generate anchor_text from description or points",
        },
        "CONTEXT_PACK_HAS_SEARCH_TEXT": {
            "check": lambda p: bool((p.get("context_pack") or {}).get("search_text")),
            "severity": IssueSeverity.WARNING,
            "message": "ContextPack should have search_text",
            "suggestion": "Extract keywords from anchor_text as search_text",
        },
        "CONTEXT_PACK_HAS_ANCHOR_TEXT": {
            "check": lambda p: bool((p.get("context_pack") or {}).get("anchor_text")),
            "severity": IssueSeverity.WARNING,
            "message": "ContextPack should have anchor_text",
            "suggestion": "Generate anchor_text from description or points",
        },
    }

    # ========== Context Completeness Invariants ==========

    @staticmethod
    def _check_context_has_when(p: dict) -> bool:
        ctx = p.get("context_pack") or {}
        desc = (ctx.get("description") or ctx.get("anchor_text") or "").lower()
        return "when:" in desc or "when：" in desc or ctx.get("when_text")

    @staticmethod
    def _check_context_has_why(p: dict) -> bool:
        ctx = p.get("context_pack") or {}
        desc = (ctx.get("description") or ctx.get("anchor_text") or "").lower()
        return "why:" in desc or "why：" in desc or ctx.get("why_text")

    @staticmethod
    def _check_context_has_boundary(p: dict) -> bool:
        ctx = p.get("context_pack") or {}
        desc = (ctx.get("description") or ctx.get("anchor_text") or "").lower()
        return "boundary:" in desc or "boundary：" in desc or "边界" in desc or ctx.get("boundary_text")

    CONTEXT_RULES = {
        "CONTEXT_HAS_WHEN": {
            "check": _check_context_has_when.__func__,
            "severity": IssueSeverity.WARNING,
            "message": "ContextPack should contain When section",
            "suggestion": "Add 'When: Not specified' to description",
        },
        "CONTEXT_HAS_WHY": {
            "check": _check_context_has_why.__func__,
            "severity": IssueSeverity.WARNING,
            "message": "ContextPack should contain Why section",
            "suggestion": "Add 'Why: Not specified' to description",
        },
        "CONTEXT_HAS_BOUNDARY": {
            "check": _check_context_has_boundary.__func__,
            "severity": IssueSeverity.WARNING,
            "message": "ContextPack should contain Boundary section",
            "suggestion": "Add 'Boundary: Not specified' to description",
        },
    }

    # ========== Step Order Invariants ==========

    @staticmethod
    def _check_step_points_ordered(p: dict) -> bool:
        steps_pack = p.get("steps_pack") or {}
        points = steps_pack.get("step_points") or []
        if not points:
            return True

        indices = [pt.get("order_index") or pt.get("step_number") for pt in points]
        # Allow partial missing, but existing ones must be sortable
        valid_indices = [i for i in indices if i is not None]
        if not valid_indices:
            return True  # All missing is OK (will be repaired)

        return len(valid_indices) == len(set(valid_indices))  # No duplicates

    STEP_RULES = {
        "STEP_POINTS_NO_DUPLICATE_INDEX": {
            "check": _check_step_points_ordered.__func__,
            "severity": IssueSeverity.WARNING,
            "message": "StepPoint order_index cannot have duplicates",
            "suggestion": "Reassign 1..N sequence",
        },
    }

    @classmethod
    def get_all_rules(cls) -> dict:
        """Get all rules"""
        rules = {}
        rules.update(cls.IDENTITY_RULES)
        rules.update(cls.STRUCTURE_RULES)
        rules.update(cls.CONTEXT_RULES)
        rules.update(cls.STEP_RULES)
        return rules
