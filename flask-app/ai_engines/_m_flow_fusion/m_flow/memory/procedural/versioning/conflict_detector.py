# m_flow/memory/procedural/versioning/conflict_detector.py
"""
Conflict detection enhancement

Two-level conflict detection: Deterministic first, LLM fallback.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Set

from m_flow.shared.tracing import TraceManager
from m_flow.shared.logging_utils import get_logger

logger = get_logger()


class ConflictLevel(Enum):
    """Conflict level"""

    NONE = "none"  # No conflict, can patch
    MILD = "mild"  # Mild conflict, prefer patch
    STRONG = "strong"  # Strong conflict, must new_version


class ConflictType(Enum):
    """Conflict type"""

    STEPS_CHANGED = "steps_changed"
    BOUNDARY_CHANGED = "boundary_changed"
    TOOLCHAIN_CHANGED = "toolchain_changed"
    RISK_CHANGED = "risk_changed"
    PREREQ_CHANGED = "prereq_changed"
    OUTCOME_CHANGED = "outcome_changed"


@dataclass
class ConflictResult:
    """Conflict detection result"""

    level: ConflictLevel
    conflict_types: List[str] = field(default_factory=list)
    recommended_action: str = "patch_existing"  # patch_existing | new_version
    reason: str = ""
    deterministic_score: float = 0.0
    llm_used: bool = False


# Conflict signal words
CONFLICT_SIGNALS = {
    "strong": [
        "替换",
        "改为",
        "不再",
        "取消",
        "弃用",
        "改成",
        "禁止",
        "废弃",
        "replace",
        "deprecate",
        "remove",
        "cancel",
        "instead of",
        "必须改",
        "不能用",
        "已废弃",
        "已取消",
    ],
    "mild": [
        "新增",
        "补充",
        "添加",
        "优化",
        "调整",
        "更新",
        "add",
        "update",
        "enhance",
        "improve",
        "modify",
    ],
}

# Boundary constraint words
BOUNDARY_WORDS = [
    "仅",
    "只",
    "必须",
    "禁止",
    "不能",
    "不要",
    "不得",
    "only",
    "must",
    "should not",
    "cannot",
    "forbidden",
    "限制",
    "约束",
    "前提",
    "条件",
]


class ConflictDetector:
    """Conflict detector"""

    def __init__(self, use_llm: bool = False):
        self.use_llm = use_llm

    def detect(
        self,
        existing: Dict[str, Any],
        candidate: Dict[str, Any],
    ) -> ConflictResult:
        """
        Detect conflicts.

        Args:
            existing: Existing Procedure structure
            candidate: New candidate structure

        Returns:
            ConflictResult
        """
        # 1. Deterministic detection
        det_result = self._deterministic_detect(existing, candidate)

        # 2. If Deterministic uncertain and LLM allowed, call LLM
        if det_result.level == ConflictLevel.MILD and self.use_llm:
            llm_result = self._llm_detect(existing, candidate, det_result)
            llm_result.llm_used = True
            return llm_result

        # Tracing
        TraceManager.event(
            "procedural.merge.conflict",
            {
                "level": det_result.level.value,
                "conflict_types": det_result.conflict_types,
                "recommended_action": det_result.recommended_action,
                "deterministic_score": det_result.deterministic_score,
                "llm_used": det_result.llm_used,
            },
        )

        return det_result

    def _deterministic_detect(
        self,
        existing: Dict[str, Any],
        candidate: Dict[str, Any],
    ) -> ConflictResult:
        """Deterministic conflict detection"""
        conflict_types = []
        score = 0.0

        # ========== Step layer detection ==========

        existing_steps = self._extract_step_texts(existing)
        candidate_steps = self._extract_step_texts(candidate)

        # Jaccard distance
        step_jaccard = self._jaccard_distance(existing_steps, candidate_steps)
        if step_jaccard > 0.5:
            conflict_types.append(ConflictType.STEPS_CHANGED.value)
            score += 0.3

        # Conflict signal word detection
        all_candidate_text = self._get_all_text(candidate)

        strong_signals = sum(1 for w in CONFLICT_SIGNALS["strong"] if w in all_candidate_text)
        if strong_signals > 0:
            score += 0.4 * min(strong_signals, 3)
            conflict_types.append("strong_signal_detected")

        mild_signals = sum(1 for w in CONFLICT_SIGNALS["mild"] if w in all_candidate_text)
        if mild_signals > 0:
            score += 0.1 * min(mild_signals, 3)

        # ========== Boundary layer detection ==========

        existing_boundary = self._extract_boundary_text(existing)
        candidate_boundary = self._extract_boundary_text(candidate)

        # Check boundary constraint word changes
        existing_constraints = {w for w in BOUNDARY_WORDS if w in existing_boundary}
        candidate_constraints = {w for w in BOUNDARY_WORDS if w in candidate_boundary}

        new_constraints = candidate_constraints - existing_constraints
        removed_constraints = existing_constraints - candidate_constraints

        if new_constraints or removed_constraints:
            conflict_types.append(ConflictType.BOUNDARY_CHANGED.value)
            score += 0.3

        # ========== Decision ==========

        if score >= 0.7:
            level = ConflictLevel.STRONG
            action = "new_version"
        elif score >= 0.3:
            level = ConflictLevel.MILD
            action = "patch_existing"  # Prefer patch, but can be overridden by LLM
        else:
            level = ConflictLevel.NONE
            action = "patch_existing"

        return ConflictResult(
            level=level,
            conflict_types=conflict_types,
            recommended_action=action,
            reason=f"deterministic_score={score:.2f}",
            deterministic_score=score,
        )

    def _llm_detect(
        self,
        existing: Dict[str, Any],
        candidate: Dict[str, Any],
        det_result: ConflictResult,
    ) -> ConflictResult:
        """LLM conflict detection (temporarily returns deterministic result)"""
        # TODO: Integrate LLM call
        # Input: old version summary + new candidate
        # Output: conflict level + types + recommended_action + reason
        return det_result

    def _extract_step_texts(self, proc: Dict[str, Any]) -> Set[str]:
        """Extract step text set"""
        texts = set()

        steps_pack = proc.get("steps_pack") or {}

        # Extract from anchor_text
        anchor = steps_pack.get("anchor_text") or ""
        for line in anchor.split("\n"):
            line = line.strip()
            if line:
                texts.add(self._normalize_text(line))

        # Extract from step_points
        points = steps_pack.get("step_points") or []
        for pt in points:
            name = pt.get("name") or pt.get("search_text") or ""
            if name:
                texts.add(self._normalize_text(name))

        return texts

    def _extract_boundary_text(self, proc: Dict[str, Any]) -> str:
        """Extract boundary-related text"""
        ctx = proc.get("context_pack") or {}

        parts = []
        if ctx.get("boundary_text"):
            parts.append(ctx["boundary_text"])
        if ctx.get("anchor_text"):
            parts.append(ctx["anchor_text"])
        if ctx.get("description"):
            parts.append(ctx["description"])

        return " ".join(parts).lower()

    def _get_all_text(self, proc: Dict[str, Any]) -> str:
        """Get all text"""
        parts = []

        parts.append(proc.get("name", ""))
        parts.append(proc.get("summary", ""))
        parts.append(proc.get("search_text", ""))

        steps_pack = proc.get("steps_pack") or {}
        parts.append(steps_pack.get("anchor_text", ""))
        parts.append(steps_pack.get("description", ""))

        ctx_pack = proc.get("context_pack") or {}
        parts.append(ctx_pack.get("anchor_text", ""))
        parts.append(ctx_pack.get("description", ""))

        return " ".join(parts).lower()

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        text = text.lower().strip()
        text = re.sub(r"^\d+[\.\)]\s*", "", text)  # Remove numbering
        text = re.sub(r"\s+", " ", text)
        return text

    def _jaccard_distance(self, set1: Set[str], set2: Set[str]) -> float:
        """Calculate Jaccard distance"""
        if not set1 and not set2:
            return 0.0

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        if union == 0:
            return 0.0

        return 1.0 - (intersection / union)


# ========== Convenience Functions ==========

_default_detector = ConflictDetector()


def detect_conflict(
    existing: Dict[str, Any],
    candidate: Dict[str, Any],
    use_llm: bool = False,
) -> ConflictResult:
    """
    Detect conflicts.

    Args:
        existing: Existing Procedure structure
        candidate: New candidate structure
        use_llm: Whether to use LLM

    Returns:
        ConflictResult
    """
    detector = ConflictDetector(use_llm=use_llm)
    return detector.detect(existing, candidate)
