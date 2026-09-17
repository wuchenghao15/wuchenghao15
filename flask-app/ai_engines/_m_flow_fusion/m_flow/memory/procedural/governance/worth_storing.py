# m_flow/memory/procedural/governance/worth_storing.py
"""
Worth-Storing screening strategy for procedural memory

Evaluate whether Procedure is worth storing and indexing.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from m_flow.shared.tracing import TraceManager
from m_flow.shared.logging_utils import get_logger

logger = get_logger()


class WorthSignal(Enum):
    """Worth signal type"""

    USER_PREFERENCE = "user_preference"  # User preference/habit
    ORG_SPECIFIC = "org_specific"  # Organization-specific
    TOOLCHAIN_SPECIFIC = "toolchain_specific"  # Toolchain-specific
    SAFETY_CRITICAL = "safety_critical"  # Safety-critical
    NOVELTY = "novelty"  # Novel/unique
    COMPLEXITY = "complexity"  # High complexity
    FREQUENCY = "frequency"  # High-frequency operation


@dataclass
class WorthResult:
    """Worth evaluation result"""

    worth_score: float  # 0.0 ~ 1.0
    worth_reason: str  # Brief reason
    signals: List[str] = field(default_factory=list)
    should_index: bool = True  # Whether should index
    index_level: str = "full"  # full | summary_only | none


# Common/generic steps (low value)
GENERIC_PATTERNS = [
    r"^(打开|关闭|点击|选择|输入|复制|粘贴|保存|确认|取消)",
    r"^(open|close|click|select|enter|copy|paste|save|confirm|cancel)",
    r"^(安装|卸载|下载|上传|登录|注销)",
    r"^(install|uninstall|download|upload|login|logout)",
    r"(如有疑问|如有问题|如需帮助|详见文档|参考官方)",
]

# High-value signals
HIGH_VALUE_PATTERNS = {
    WorthSignal.SAFETY_CRITICAL: [
        r"(备份|回滚|恢复|权限|安全|加密|脱敏|审计)",
        r"(backup|rollback|restore|permission|security|encrypt|audit)",
        r"(生产环境|正式环境|线上|prod)",
    ],
    WorthSignal.ORG_SPECIFIC: [
        r"(内部|公司|团队|项目|我们的)",
        r"(internal|company|team|project|our)",
    ],
    WorthSignal.TOOLCHAIN_SPECIFIC: [
        r"(jenkins|gitlab|docker|kubernetes|k8s|terraform|ansible)",
        r"(mysql|postgresql|redis|mongodb|elasticsearch)",
        r"(aws|gcp|azure|阿里云|腾讯云)",
    ],
    WorthSignal.COMPLEXITY: [
        r"(分布式|集群|高可用|容灾|负载均衡)",
        r"(distributed|cluster|high.?availability|failover|load.?balance)",
    ],
}

# Index threshold
INDEX_THRESHOLD = 0.4  # Don't index below this value


class WorthEvaluator:
    """Worth evaluator"""

    def __init__(self, threshold: float = INDEX_THRESHOLD):
        self.threshold = threshold

    def evaluate(
        self,
        procedure: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> WorthResult:
        """
        Evaluate storage worth of Procedure.

        Args:
            procedure: Procedure structure
            context: Additional context (e.g., source, user, etc.)

        Returns:
            WorthResult
        """
        all_text = self._get_all_text(procedure)

        # Base score
        score = 0.5
        signals = []
        reasons = []

        # ========== Negative signals (deduct points) ==========

        generic_count = 0
        for pattern in GENERIC_PATTERNS:
            if re.search(pattern, all_text, re.IGNORECASE):
                generic_count += 1

        if generic_count > 3:
            score -= 0.3
            reasons.append("通用步骤过多")
        elif generic_count > 1:
            score -= 0.1

        # Content too short
        if len(all_text) < 100:
            score -= 0.2
            reasons.append("内容过短")

        # ========== Positive signals (add points) ==========

        for signal, patterns in HIGH_VALUE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, all_text, re.IGNORECASE):
                    score += 0.15
                    signals.append(signal.value)
                    break  # Each signal type adds at most once

        # Step count
        steps_count = self._count_steps(procedure)
        if steps_count >= 5:
            score += 0.1
            signals.append(WorthSignal.COMPLEXITY.value)

        # Context completeness
        ctx = procedure.get("context_pack") or {}
        if ctx.get("when_text") and ctx.get("why_text") and ctx.get("boundary_text"):
            score += 0.1
            signals.append("context_complete")

        # ========== Normalize ==========

        score = max(0.0, min(1.0, score))

        # Determine index level
        if score >= self.threshold:
            should_index = True
            index_level = "full"
        elif score >= self.threshold * 0.5:
            should_index = True
            index_level = "summary_only"  # Only index summary, don't index points
        else:
            should_index = False
            index_level = "none"

        # Generate reason
        if not reasons:
            if score >= 0.7:
                reasons.append("高价值流程")
            elif score >= 0.5:
                reasons.append("中等价值")
            else:
                reasons.append("低价值/通用流程")

        result = WorthResult(
            worth_score=round(score, 2),
            worth_reason="；".join(reasons),
            signals=list(set(signals)),
            should_index=should_index,
            index_level=index_level,
        )

        # Tracing
        TraceManager.event(
            "procedural.worth",
            {
                "score": result.worth_score,
                "signals": result.signals,
                "should_index": result.should_index,
                "index_level": result.index_level,
            },
        )

        return result

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

        return " ".join(parts)

    def _count_steps(self, proc: Dict[str, Any]) -> int:
        """Count step count"""
        steps_pack = proc.get("steps_pack") or {}
        points = steps_pack.get("step_points") or []

        if points:
            return len(points)

        # Count from anchor_text
        anchor = steps_pack.get("anchor_text") or ""
        return len([line for line in anchor.split("\n") if line.strip()])


# ========== Convenience Functions ==========

_default_evaluator = WorthEvaluator()


def evaluate_worth(
    procedure: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
    threshold: float = INDEX_THRESHOLD,
) -> WorthResult:
    """
    Evaluate storage worth of Procedure.

    Args:
        procedure: Procedure structure
        context: Additional context
        threshold: Index threshold

    Returns:
        WorthResult
    """
    evaluator = WorthEvaluator(threshold=threshold)
    return evaluator.evaluate(procedure, context)
