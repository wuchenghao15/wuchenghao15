# m_flow/eval/metrics.py
"""
P7-3: Metrics Design

R0 (retrieval layer) + R1 (injection layer) metrics calculation.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .loader import EvalCase
from .runner import CaseResult


def _contains_any(s: str, subs: List[str]) -> bool:
    """Check if string contains any substring"""
    s = (s or "").lower()
    return any((x or "").lower() in s for x in subs if x)


@dataclass
class MetricResult:
    """Single metric result"""

    value: float
    count: int
    total: int

    @property
    def percentage(self) -> float:
        return self.value * 100


@dataclass
class TypeMetrics:
    """Metrics by type"""

    n: int = 0
    recall_at_1: float = 0.0
    recall_at_2: float = 0.0
    recall_at_3: float = 0.0
    active_hit_at_1: float = 0.0
    fp_inject_rate: float = 0.0
    ctx_completeness: float = 0.0
    has_steps_rate: float = 0.0
    trigger_accuracy: float = 0.0
    # P7-3.3: Coordination metrics
    overshadow_rate: float = 0.0  # Rate at which procedural crowds out episodic/atomic


@dataclass
class EvalMetricsResult:
    """Evaluation metrics result"""

    overall: TypeMetrics = field(default_factory=TypeMetrics)
    by_type: Dict[str, TypeMetrics] = field(default_factory=dict)

    # Detailed statistics
    total_cases: int = 0
    successful_cases: int = 0
    failed_cases: int = 0


class EvalMetrics:
    """
    Evaluation metrics calculator.

    Supports:
    - Recall@K (procedure_key/title)
    - ActiveHit@K
    - FalsePositiveInjectRate
    - ContextCompleteness
    - TriggerAccuracy
    """

    @staticmethod
    def procedure_hit(case: EvalCase, result: CaseResult, k: int) -> bool:
        """Check if procedure is hit"""
        exp_keys = case.expect.procedures.any_of_keys
        exp_titles = case.expect.procedures.any_of_titles_contains

        # If no expectation, return True (not evaluated)
        if not exp_keys and not exp_titles:
            return True

        hits = result.procedural.top_hits[:k]

        for h in hits:
            key = h.get("key", "")
            title = h.get("title", "")

            # Check key match
            if exp_keys and key in exp_keys:
                return True

            # Check title contains
            if exp_titles:
                if _contains_any(title, exp_titles) or _contains_any(key, exp_titles):
                    return True

        return False

    @staticmethod
    def active_hit(case: EvalCase, result: CaseResult, k: int) -> bool:
        """Check if active procedure is hit"""
        if not case.expect.procedures.at_least_one_active:
            return True

        hits = result.procedural.top_hits[:k]
        return any(h.get("active", True) for h in hits)

    @staticmethod
    def injection_ok(case: EvalCase, result: CaseResult) -> Tuple[bool, List[str]]:
        """Check if injection meets constraints"""
        reasons = []
        constraints = case.expect.injection_constraints

        # Check if should inject
        should_inject = case.expect.should_inject_procedural
        if should_inject is not None:
            if result.procedural.injected != should_inject:
                reasons.append(f"injected={result.procedural.injected} != expected={should_inject}")

        # Check card count
        if constraints.max_procedural_cards is not None:
            if result.procedural.cards_count > constraints.max_procedural_cards:
                reasons.append(f"cards={result.procedural.cards_count} > max={constraints.max_procedural_cards}")

        # Check context fields
        for rf in constraints.require_context_fields:
            if rf not in result.procedural.context_fields_present:
                reasons.append(f"missing_context_field:{rf}")

        # Check steps
        if constraints.require_steps and not result.procedural.has_steps:
            reasons.append("missing_steps")

        return len(reasons) == 0, reasons

    @staticmethod
    def trigger_correct(case: EvalCase, result: CaseResult) -> bool:
        """Check if trigger is correct"""
        expected = case.expect.should_trigger_procedural
        if expected is None:
            return True  # Not evaluated
        return result.procedural.triggered == expected

    @classmethod
    def compute(
        cls,
        cases: List[EvalCase],
        results: List[CaseResult],
    ) -> EvalMetricsResult:
        """Calculate all metrics"""
        assert len(cases) == len(results), "Cases and results must have same length"

        metrics = EvalMetricsResult(
            total_cases=len(cases),
        )

        # Statistics counters
        overall = {
            "n": 0,
            "recall@1": 0,
            "recall@2": 0,
            "recall@3": 0,
            "active@1": 0,
            "fp_inject": 0,
            "fp_total": 0,
            "ctx_complete": 0,
            "has_steps": 0,
            "trigger_correct": 0,
            "trigger_total": 0,
            "overshadow": 0,
            "overshadow_total": 0,  # P7-3.3
        }
        by_type: Dict[str, Dict[str, int]] = {}

        for case, result in zip(cases, results):
            if result.ok:
                metrics.successful_cases += 1
            else:
                metrics.failed_cases += 1
                continue  # Skip failed cases

            t = case.type or "unknown"
            if t not in by_type:
                by_type[t] = {
                    "n": 0,
                    "recall@1": 0,
                    "recall@2": 0,
                    "recall@3": 0,
                    "active@1": 0,
                    "fp_inject": 0,
                    "fp_total": 0,
                    "ctx_complete": 0,
                    "has_steps": 0,
                    "trigger_correct": 0,
                    "trigger_total": 0,
                    "overshadow": 0,
                    "overshadow_total": 0,
                }

            overall["n"] += 1
            by_type[t]["n"] += 1

            # Recall@K
            if cls.procedure_hit(case, result, 1):
                overall["recall@1"] += 1
                by_type[t]["recall@1"] += 1
            if cls.procedure_hit(case, result, 2):
                overall["recall@2"] += 1
                by_type[t]["recall@2"] += 1
            if cls.procedure_hit(case, result, 3):
                overall["recall@3"] += 1
                by_type[t]["recall@3"] += 1

            # Active hit
            if cls.active_hit(case, result, 1):
                overall["active@1"] += 1

            # False positive inject (negative samples)
            if case.type == "negative":
                overall["fp_total"] += 1
                by_type[t]["fp_total"] += 1
                if result.procedural.injected:
                    overall["fp_inject"] += 1
                    by_type[t]["fp_inject"] += 1

            # Context completeness
            ok_inj, _ = cls.injection_ok(case, result)
            if ok_inj:
                overall["ctx_complete"] += 1
                by_type[t]["ctx_complete"] += 1

            # Has steps
            if result.procedural.has_steps:
                overall["has_steps"] += 1
                by_type[t]["has_steps"] += 1

            # Trigger accuracy
            if case.expect.should_trigger_procedural is not None:
                overall["trigger_total"] += 1
                by_type[t]["trigger_total"] += 1
                if cls.trigger_correct(case, result):
                    overall["trigger_correct"] += 1
                    by_type[t]["trigger_correct"] += 1

            # P7-3.3: OvershadowRate
            # When episodic should be retrieved but is actually empty, consider it overshadow
            if case.expect.episodic.should_retrieve:
                overall["overshadow_total"] += 1
                by_type[t]["overshadow_total"] = by_type[t].get("overshadow_total", 0) + 1
                if result.episodic.edges_count == 0:
                    overall["overshadow"] += 1
                    by_type[t]["overshadow"] = by_type[t].get("overshadow", 0) + 1

        # Convert to rates
        def to_rate(stats: Dict[str, int]) -> TypeMetrics:
            n = max(1, stats["n"])
            fp_total = max(1, stats.get("fp_total", 1))
            trigger_total = max(1, stats.get("trigger_total", 1))
            overshadow_total = max(1, stats.get("overshadow_total", 1))

            return TypeMetrics(
                n=stats["n"],
                recall_at_1=stats["recall@1"] / n,
                recall_at_2=stats["recall@2"] / n,
                recall_at_3=stats["recall@3"] / n,
                active_hit_at_1=stats["active@1"] / n,
                fp_inject_rate=stats["fp_inject"] / fp_total if stats.get("fp_total") else 0.0,
                ctx_completeness=stats["ctx_complete"] / n,
                has_steps_rate=stats["has_steps"] / n,
                trigger_accuracy=stats["trigger_correct"] / trigger_total if stats.get("trigger_total") else 1.0,
                overshadow_rate=stats.get("overshadow", 0) / overshadow_total if stats.get("overshadow_total") else 0.0,
            )

        metrics.overall = to_rate(overall)
        metrics.by_type = {t: to_rate(s) for t, s in by_type.items()}

        return metrics
