# m_flow/memory/procedural/safety/__init__.py
"""
Security and compliance enhancement for procedural memory

Sensitivity classification and indexing strategy.
"""

from .sensitivity import (
    classify_sensitivity,
    SensitivityLevel,
    SensitivityResult,
    SensitivityClassifier,
)

# Reuse existing security functions
from m_flow.memory.procedural.procedural_safety import (
    redact_secrets,
    contains_dangerous_content,
    has_high_risk_operations,
    has_redacted_content,
)

__all__ = [
    "classify_sensitivity",
    "SensitivityLevel",
    "SensitivityResult",
    "SensitivityClassifier",
    "redact_secrets",
    "contains_dangerous_content",
    "has_high_risk_operations",
    "has_redacted_content",
]
