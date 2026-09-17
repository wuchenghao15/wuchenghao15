# m_flow/eval/report.py
"""
Report generation and failure bucketing.

Generate report.json + report.md, containing failure sample list and bucketing analysis.
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from .config import EvalConfig
from .loader import EvalCase
from .runner import CaseResult
from .metrics import EvalMetrics, EvalMetricsResult


# Failure bucket types
FAILURE_BUCKETS = {
    "trigger_miss": "should_trigger=true but triggered=false",
    "query_bad": "trigger ok but top_hits all off",
    "ranking_bad": "hit but ranking not in topK",
    "inject_gate_miss": "recall hit but injection not selected",
    "format_incomplete": "injected but context/steps missing segments",
    "overshadow": "procedural injection caused episodic/atomic loss",
    "error": "runtime error",
}


@dataclass
class FailureCase:
    """Failure sample."""

    id: str
    type: str
    query: str
    trace_id: str
    buckets: List[str]
    reasons: List[str]


@dataclass
class EvalReport:
    """
    Evaluation report.

    Contains:
    - Overall metrics
    - Metrics by type
    - Failure sample list (with trace_id)
    - Parameter snapshot
    - Baseline comparison (optional)
    """

    # Metadata
    name: str = ""
    created_at: str = ""
    dataset_path: str = ""

    # Statistics
    total_cases: int = 0
    successful_cases: int = 0
    failed_cases: int = 0

    # Metrics
    metrics: Optional[EvalMetricsResult] = None

    # Failure samples
    failures: List[FailureCase] = field(default_factory=list)
    failure_buckets: Dict[str, int] = field(default_factory=dict)

    # Config snapshot
    config: Optional[EvalConfig] = None

    # Baseline comparison
    baseline_name: Optional[str] = None
    baseline_delta: Dict[str, float] = field(default_factory=dict)
    regressions: List[str] = field(default_factory=list)

    @classmethod
    def build(
        cls,
        cases: List[EvalCase],
        results: List[CaseResult],
        config: EvalConfig,
        dataset_path: str = "",
        baseline: Optional["EvalReport"] = None,
    ) -> "EvalReport":
        """Build evaluation report."""
        report = cls(
            name=config.name,
            created_at=datetime.now().isoformat(),
            dataset_path=dataset_path,
            total_cases=len(cases),
            config=config,
        )

        # Compute metrics
        report.metrics = EvalMetrics.compute(cases, results)
        report.successful_cases = report.metrics.successful_cases
        report.failed_cases = report.metrics.failed_cases

        # Analyze failure samples
        report.failures, report.failure_buckets = cls._analyze_failures(cases, results)

        # Compare with baseline
        if baseline and baseline.metrics:
            report.baseline_name = baseline.name
            report.baseline_delta, report.regressions = cls._compare_baseline(report.metrics, baseline.metrics)

        return report

    @classmethod
    def _analyze_failures(
        cls,
        cases: List[EvalCase],
        results: List[CaseResult],
    ) -> tuple[List[FailureCase], Dict[str, int]]:
        """Analyze failure samples and bucket them."""
        failures = []
        buckets: Dict[str, int] = {k: 0 for k in FAILURE_BUCKETS}

        for case, result in zip(cases, results):
            if not result.ok:
                # Runtime error
                failures.append(
                    FailureCase(
                        id=case.id,
                        type=case.type,
                        query=case.query[:100],
                        trace_id=result.trace_id,
                        buckets=["error"],
                        reasons=[result.error or "unknown error"],
                    )
                )
                buckets["error"] += 1
                continue

            # Check various failure types
            case_buckets = []
            reasons = []

            # trigger_miss
            if case.expect.should_trigger_procedural is True:
                if not result.procedural.triggered:
                    case_buckets.append("trigger_miss")
                    reasons.append("expected trigger but not triggered")

            # inject_gate_miss
            if case.expect.should_inject_procedural is True:
                if not result.procedural.injected:
                    case_buckets.append("inject_gate_miss")
                    reasons.append("expected inject but not injected")

            # ranking_bad: has expectation but not hit top3
            exp_keys = case.expect.procedures.any_of_keys
            exp_titles = case.expect.procedures.any_of_titles_contains
            if exp_keys or exp_titles:
                if not EvalMetrics.procedure_hit(case, result, 3):
                    case_buckets.append("ranking_bad")
                    reasons.append("expected procedure not in top3")

            # format_incomplete
            ok_inj, inj_reasons = EvalMetrics.injection_ok(case, result)
            if not ok_inj:
                case_buckets.append("format_incomplete")
                reasons.extend(inj_reasons)

            # overshadow
            if case.expect.episodic.should_retrieve:
                if result.episodic.edges_count == 0:
                    case_buckets.append("overshadow")
                    reasons.append("episodic expected but empty")

            if case_buckets:
                failures.append(
                    FailureCase(
                        id=case.id,
                        type=case.type,
                        query=case.query[:100],
                        trace_id=result.trace_id,
                        buckets=case_buckets,
                        reasons=reasons,
                    )
                )
                for b in case_buckets:
                    buckets[b] = buckets.get(b, 0) + 1

        return failures, buckets

    @classmethod
    def _compare_baseline(
        cls,
        current: EvalMetricsResult,
        baseline: EvalMetricsResult,
    ) -> tuple[Dict[str, float], List[str]]:
        """Compare with baseline."""
        delta = {}
        regressions = []

        # Compare main metrics
        metrics_to_compare = [
            ("recall@1", current.overall.recall_at_1, baseline.overall.recall_at_1),
            ("recall@2", current.overall.recall_at_2, baseline.overall.recall_at_2),
            ("recall@3", current.overall.recall_at_3, baseline.overall.recall_at_3),
            (
                "ctx_completeness",
                current.overall.ctx_completeness,
                baseline.overall.ctx_completeness,
            ),
            (
                "trigger_accuracy",
                current.overall.trigger_accuracy,
                baseline.overall.trigger_accuracy,
            ),
            ("fp_inject_rate", current.overall.fp_inject_rate, baseline.overall.fp_inject_rate),
        ]

        for name, curr_val, base_val in metrics_to_compare:
            diff = curr_val - base_val
            delta[name] = diff

            # Detect regression (allow small fluctuations)
            threshold = 0.02  # 2%
            if name == "fp_inject_rate":
                # FP rate increase is regression
                if diff > threshold:
                    regressions.append(f"{name}: +{diff:.2%}")
            else:
                # Other metrics decrease is regression
                if diff < -threshold:
                    regressions.append(f"{name}: {diff:.2%}")

        return delta, regressions

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "created_at": self.created_at,
            "dataset_path": self.dataset_path,
            "total_cases": self.total_cases,
            "successful_cases": self.successful_cases,
            "failed_cases": self.failed_cases,
            "metrics": {
                "overall": asdict(self.metrics.overall) if self.metrics else {},
                "by_type": {t: asdict(m) for t, m in (self.metrics.by_type if self.metrics else {}).items()},
            },
            "failures": [
                {
                    "id": f.id,
                    "type": f.type,
                    "query": f.query,
                    "trace_id": f.trace_id,
                    "buckets": f.buckets,
                    "reasons": f.reasons,
                }
                for f in self.failures[:50]  # Only keep top 50
            ],
            "failure_buckets": self.failure_buckets,
            "config": self.config.to_dict() if self.config else {},
            "baseline_name": self.baseline_name,
            "baseline_delta": self.baseline_delta,
            "regressions": self.regressions,
        }

    def save_json(self, path: str) -> None:
        """Save as JSON."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    def save_markdown(self, path: str) -> None:
        """Save as Markdown."""
        lines = []

        lines.append(f"# Evaluation Report: {self.name}")
        lines.append(f"\nGenerated: {self.created_at}")
        lines.append(f"\nDataset: {self.dataset_path}")
        lines.append("")

        # Overall statistics
        lines.append("## Overall Statistics")
        lines.append(f"- Total cases: {self.total_cases}")
        lines.append(f"- Success: {self.successful_cases}")
        lines.append(f"- Failed: {self.failed_cases}")
        lines.append("")

        # Overall metrics
        if self.metrics:
            lines.append("## Overall Metrics")
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            lines.append(f"| Recall@1 | {self.metrics.overall.recall_at_1:.2%} |")
            lines.append(f"| Recall@2 | {self.metrics.overall.recall_at_2:.2%} |")
            lines.append(f"| Recall@3 | {self.metrics.overall.recall_at_3:.2%} |")
            lines.append(f"| Active Hit@1 | {self.metrics.overall.active_hit_at_1:.2%} |")
            lines.append(f"| FP Inject Rate | {self.metrics.overall.fp_inject_rate:.2%} |")
            lines.append(f"| Context Completeness | {self.metrics.overall.ctx_completeness:.2%} |")
            lines.append(f"| Has Steps Rate | {self.metrics.overall.has_steps_rate:.2%} |")
            lines.append(f"| Trigger Accuracy | {self.metrics.overall.trigger_accuracy:.2%} |")
            lines.append(f"| Overshadow Rate | {self.metrics.overall.overshadow_rate:.2%} |")
            lines.append("")

            # Metrics by type
            lines.append("## Metrics by Type")
            lines.append("| Type | n | Recall@1 | Recall@3 | FP Rate |")
            lines.append("|------|---|----------|----------|---------|")
            for t, m in self.metrics.by_type.items():
                lines.append(f"| {t} | {m.n} | {m.recall_at_1:.2%} | {m.recall_at_3:.2%} | {m.fp_inject_rate:.2%} |")
            lines.append("")

        # Baseline comparison
        if self.baseline_name:
            lines.append("## Baseline Comparison")
            lines.append(f"Compare with baseline: {self.baseline_name}")
            lines.append("")
            if self.baseline_delta:
                lines.append("| Metric | Delta |")
                lines.append("|--------|-------|")
                for k, v in self.baseline_delta.items():
                    sign = "+" if v > 0 else ""
                    lines.append(f"| {k} | {sign}{v:.2%} |")
                lines.append("")

            if self.regressions:
                lines.append("### [Warning] Regressions")
                for r in self.regressions:
                    lines.append(f"- {r}")
                lines.append("")

        # Failure buckets
        if self.failure_buckets:
            lines.append("## Failure Buckets")
            lines.append("| Type | Count | Description |")
            lines.append("|------|-------|-------------|")
            for bucket, count in sorted(self.failure_buckets.items(), key=lambda x: -x[1]):
                if count > 0:
                    desc = FAILURE_BUCKETS.get(bucket, "")
                    lines.append(f"| {bucket} | {count} | {desc} |")
            lines.append("")

        # Top failure samples
        if self.failures:
            lines.append("## Top Failure Samples")
            lines.append("| ID | Type | Query | Trace ID | Buckets |")
            lines.append("|----|------|-------|----------|---------|")
            for f in self.failures[:20]:
                query = f.query[:40] + "..." if len(f.query) > 40 else f.query
                lines.append(f"| {f.id} | {f.type} | {query} | `{f.trace_id}` | {', '.join(f.buckets)} |")
            lines.append("")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    @classmethod
    def load(cls, path: str) -> "EvalReport":
        """Load report from JSON."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        from .metrics import TypeMetrics, EvalMetricsResult

        # Parse metrics
        metrics_data = data.get("metrics", {})
        overall_data = metrics_data.get("overall", {})
        overall = TypeMetrics(
            n=overall_data.get("n", 0),
            recall_at_1=overall_data.get("recall_at_1", 0),
            recall_at_2=overall_data.get("recall_at_2", 0),
            recall_at_3=overall_data.get("recall_at_3", 0),
            active_hit_at_1=overall_data.get("active_hit_at_1", 0),
            fp_inject_rate=overall_data.get("fp_inject_rate", 0),
            ctx_completeness=overall_data.get("ctx_completeness", 0),
            has_steps_rate=overall_data.get("has_steps_rate", 0),
            trigger_accuracy=overall_data.get("trigger_accuracy", 0),
        )

        by_type = {}
        for t, m_data in metrics_data.get("by_type", {}).items():
            by_type[t] = TypeMetrics(**m_data)

        metrics = EvalMetricsResult(
            overall=overall,
            by_type=by_type,
            total_cases=data.get("total_cases", 0),
            successful_cases=data.get("successful_cases", 0),
            failed_cases=data.get("failed_cases", 0),
        )

        # Parse failures
        failures = []
        for f_data in data.get("failures", []):
            failures.append(
                FailureCase(
                    id=f_data["id"],
                    type=f_data["type"],
                    query=f_data["query"],
                    trace_id=f_data["trace_id"],
                    buckets=f_data["buckets"],
                    reasons=f_data["reasons"],
                )
            )

        # Parse config
        config = None
        if data.get("config"):
            config = EvalConfig(
                name=data["config"].get("name", ""),
                version=data["config"].get("version", ""),
            )

        return cls(
            name=data.get("name", ""),
            created_at=data.get("created_at", ""),
            dataset_path=data.get("dataset_path", ""),
            total_cases=data.get("total_cases", 0),
            successful_cases=data.get("successful_cases", 0),
            failed_cases=data.get("failed_cases", 0),
            metrics=metrics,
            failures=failures,
            failure_buckets=data.get("failure_buckets", {}),
            config=config,
            baseline_name=data.get("baseline_name"),
            baseline_delta=data.get("baseline_delta", {}),
            regressions=data.get("regressions", []),
        )
