# m_flow/eval/__init__.py
"""
P7: Evaluation System and Regression Testing

Procedural / Episodic / Atomic end-to-end evaluation system.

Core components:
- EvalConfig: Evaluation configuration
- CaseLoader: Dataset loading
- EvalRunner: Evaluation runner
- EvalMetrics: Metrics calculation
- EvalReport: Report generation

Usage:
    python -m m_flow.eval --dataset procedural_eval_v1.jsonl
    python -m m_flow.eval --dataset procedural_eval_v1.jsonl --compare-baseline
"""

from .config import EvalConfig, EvalSetup
from .loader import CaseLoader, EvalCase
from .runner import EvalRunner, CaseResult
from .metrics import EvalMetrics
from .report import EvalReport

__all__ = [
    "EvalConfig",
    "EvalSetup",
    "CaseLoader",
    "EvalCase",
    "EvalRunner",
    "CaseResult",
    "EvalMetrics",
    "EvalReport",
]
