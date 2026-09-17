# m_flow/memory/procedural/safety/sensitivity.py
"""
Sensitivity classifier for procedural memory

Classify sensitivity of Procedure content to determine indexing strategy.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List

from m_flow.shared.tracing import TraceManager
from m_flow.shared.logging_utils import get_logger
from m_flow.memory.procedural.procedural_safety import redact_secrets

logger = get_logger()


class SensitivityLevel(Enum):
    """Sensitivity level"""

    LOW = "low"  # Can index normally
    MEDIUM = "medium"  # Index summary/anchor, don't index detailed points
    HIGH = "high"  # Can still store, but don't index; replace sensitive segments with placeholders


@dataclass
class SensitivityResult:
    """Sensitivity classification result"""

    level: SensitivityLevel
    allowed_to_index: bool
    index_strategy: str  # full | summary_only | none
    detected_patterns: List[str] = field(default_factory=list)
    redaction_applied: bool = False
    reason: str = ""


# Sensitive content patterns
SENSITIVITY_PATTERNS = {
    "high": [
        # Explicit keys/tokens
        (r'(?i)(api[_-]?key|token|secret|password|credential)["\'\s:=]+\S{10,}', "credential"),
        # Private keys
        (r"-----BEGIN.*PRIVATE KEY-----", "private_key"),
        # Internal domains/IPs (may be sensitive infrastructure)
        (
            r"(?i)(internal\.|\.internal|\.local|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+)",
            "internal_infra",
        ),
        # Account information
        (r'(?i)(account[_-]?id|user[_-]?id)["\'\s:=]+\w{8,}', "account_id"),
        # Ticket/incident numbers (may be associated with sensitive events)
        (r'(?i)(ticket|incident|case)[_-]?(id|number)?["\'\s:=#]+\w{6,}', "ticket_ref"),
    ],
    "medium": [
        # File paths (may contain usernames)
        (r"(?i)(/home/\w+|/Users/\w+|C:\\Users\\\w+)", "user_path"),
        # Email
        (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "email"),
        # URL parameters (may contain tokens)
        (r"https?://[^\s]+\?([\w=&]+)", "url_params"),
        # Phone numbers
        (r"(?i)(?:电话|phone|tel)[:\s]*[\d\-+()]{8,}", "phone"),
        # Specific date/time (may be used to locate events)
        (r"\d{4}[-/]\d{2}[-/]\d{2}\s+\d{2}:\d{2}:\d{2}", "timestamp"),
    ],
    "low": [
        # Version numbers
        (r"v\d+\.\d+\.\d+", "version"),
        # Generic commands
        (r"(?i)(git|npm|pip|docker|kubectl)\s+\w+", "command"),
    ],
}


class SensitivityClassifier:
    """Sensitivity classifier"""

    def __init__(self, redact_on_high: bool = True):
        """
        Args:
            redact_on_high: Whether to automatically redact for HIGH level
        """
        self.redact_on_high = redact_on_high

    def classify(
        self,
        procedure: Dict[str, Any],
    ) -> SensitivityResult:
        """
        Classify sensitivity of Procedure.

        Args:
            procedure: Procedure structure

        Returns:
            SensitivityResult
        """
        all_text = self._get_all_text(procedure)

        detected = []
        high_count = 0
        medium_count = 0

        # Detect sensitive patterns
        for pattern, label in SENSITIVITY_PATTERNS.get("high", []):
            if re.search(pattern, all_text):
                detected.append(f"high:{label}")
                high_count += 1

        for pattern, label in SENSITIVITY_PATTERNS.get("medium", []):
            if re.search(pattern, all_text):
                detected.append(f"medium:{label}")
                medium_count += 1

        # Determine level
        if high_count >= 2 or (high_count >= 1 and medium_count >= 2):
            level = SensitivityLevel.HIGH
            index_strategy = "none"
            allowed_to_index = False
            reason = f"Detected {high_count} high-sensitivity patterns"
        elif high_count >= 1 or medium_count >= 3:
            level = SensitivityLevel.MEDIUM
            index_strategy = "summary_only"
            allowed_to_index = True
            reason = f"Detected sensitive patterns: {high_count} high, {medium_count} medium"
        else:
            level = SensitivityLevel.LOW
            index_strategy = "full"
            allowed_to_index = True
            reason = "No sensitive content detected"

        # For HIGH level, consider redaction
        redaction_applied = False
        if level == SensitivityLevel.HIGH and self.redact_on_high:
            procedure = self._redact_procedure(procedure)
            redaction_applied = True

        result = SensitivityResult(
            level=level,
            allowed_to_index=allowed_to_index,
            index_strategy=index_strategy,
            detected_patterns=detected[:10],  # Limit count
            redaction_applied=redaction_applied,
            reason=reason,
        )

        # Tracing
        TraceManager.event(
            "procedural.safety.sensitivity",
            {
                "level": level.value,
                "allowed_to_index": allowed_to_index,
                "index_strategy": index_strategy,
                "detected_count": len(detected),
                "redaction_applied": redaction_applied,
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

        # Step points
        for pt in steps_pack.get("step_points") or []:
            parts.append(pt.get("name", ""))
            parts.append(pt.get("search_text", ""))

        ctx_pack = proc.get("context_pack") or {}
        parts.append(ctx_pack.get("anchor_text", ""))
        parts.append(ctx_pack.get("description", ""))

        # Context points
        for pt in ctx_pack.get("context_points") or []:
            parts.append(pt.get("name", ""))
            parts.append(pt.get("search_text", ""))

        return " ".join(parts)

    def _redact_procedure(self, proc: Dict[str, Any]) -> Dict[str, Any]:
        """Redact procedure"""
        # Redact each field
        if proc.get("summary"):
            proc["summary"] = redact_secrets(proc["summary"])

        if proc.get("search_text"):
            proc["search_text"] = redact_secrets(proc["search_text"])

        steps_pack = proc.get("steps_pack")
        if steps_pack:
            if steps_pack.get("anchor_text"):
                steps_pack["anchor_text"] = redact_secrets(steps_pack["anchor_text"])
            if steps_pack.get("description"):
                steps_pack["description"] = redact_secrets(steps_pack["description"])
            for pt in steps_pack.get("step_points") or []:
                if pt.get("name"):
                    pt["name"] = redact_secrets(pt["name"])

        ctx_pack = proc.get("context_pack")
        if ctx_pack:
            if ctx_pack.get("anchor_text"):
                ctx_pack["anchor_text"] = redact_secrets(ctx_pack["anchor_text"])
            if ctx_pack.get("description"):
                ctx_pack["description"] = redact_secrets(ctx_pack["description"])
            for pt in ctx_pack.get("context_points") or []:
                if pt.get("name"):
                    pt["name"] = redact_secrets(pt["name"])

        return proc


# ========== Convenience Functions ==========

_default_classifier = SensitivityClassifier()


def classify_sensitivity(
    procedure: Dict[str, Any],
    redact_on_high: bool = True,
) -> SensitivityResult:
    """
    Classify sensitivity of Procedure.

    Args:
        procedure: Procedure structure
        redact_on_high: Whether to automatically redact for HIGH level

    Returns:
        SensitivityResult
    """
    classifier = SensitivityClassifier(redact_on_high=redact_on_high)
    return classifier.classify(procedure)
