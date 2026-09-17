# m_flow/memory/procedural/governance/procedural_classifier.py
"""
Procedural Classifier: Pre-filter

Quickly determine if input may contain procedural content before LLM extraction.
Used to filter non-procedural content like pure events/conversations/common knowledge.

Design principles:
- Prefer false negatives over false positives
- Use rule-based + lightweight LLM two-layer judgment
- Fast, low cost
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple

from m_flow.shared.logging_utils import get_logger

logger = get_logger()


class ContentType(Enum):
    """Content type"""

    PROCEDURAL = "procedural"  # Clearly contains steps/processes/methods
    LIKELY_PROCEDURAL = "likely"  # May contain procedural (needs LLM confirmation)
    EPISODIC = "episodic"  # Event description/meeting records
    FACTUAL = "factual"  # Pure facts/knowledge
    CONVERSATIONAL = "conversational"  # Conversation/chat
    GENERIC = "generic"  # Common knowledge (not worth remembering)


@dataclass
class ClassificationResult:
    """Classification result"""

    content_type: ContentType
    is_procedural: bool  # Whether should extract procedural
    confidence: float  # 0.0 ~ 1.0
    signals: List[str] = field(default_factory=list)
    reason: str = ""


# ========== Signal Patterns ==========

# Strong Procedural signals (high weight)
STRONG_PROCEDURAL_PATTERNS = [
    # Explicit step markers
    (r"(?:^|\n)\s*(?:步骤|step)\s*[1-9]", 0.4),
    (r"(?:^|\n)\s*[1-9][.、)]\s*[^\n]{5,}", 0.3),  # 1. xxx
    (r"(?:^|\n)\s*第[一二三四五六七八九十]+步", 0.4),
    # Process/method keywords
    (r"(?:如何|怎么|怎样|how\s+to)\s+\S{2,}", 0.3),
    (r"(?:流程|步骤|方法|规范|指南|教程|procedure|process|workflow)", 0.2),
    # Commands/tools
    (r'(?:执行|运行|输入|run|execute|cmd|command)[:\s]+[`\'"]\S+', 0.3),
    (r"(?:git|docker|kubectl|npm|pip|curl|wget|ssh)\s+\w+", 0.3),
    # Conditions/branches
    (r"(?:如果|当|若|when|if)\s+.{5,}\s*(?:则|就|then)", 0.2),
    (r"(?:否则|otherwise|else)", 0.1),
    # Notes/warnings
    (r"(?:注意|警告|重要|caution|warning|important)[：:]\s*\S", 0.2),
    (r"(?:必须|需要|应该|不要|不能|must|should|cannot)", 0.15),
]

# Implicit Procedural signals (identify extractable methods from unstructured content)
IMPLICIT_PROCEDURAL_PATTERNS = [
    # Sequential action words (implicit steps)
    (r"(?:先|首先|第一).{5,}(?:然后|接着|再|其次|之后)", 0.35),
    (r"(?:然后|接着|再).{3,}(?:最后|最终|完成)", 0.3),
    # Experience sharing patterns
    (r"(?:我们?是这样|一般是这样|通常是|我的做法是)", 0.3),
    (r"(?:上次|之前).{5,}(?:这样|这么|如此)(?:解决|处理|做)", 0.25),
    # Methods in Q&A
    (r"(?:怎么|如何|怎样)\s*(?:处理|解决|做|搞定)", 0.25),
    (r"(?:Q|问)[：:].{5,}(?:A|答)[：:]", 0.2),
    # Decisions/rules
    (r"(?:决定|采用|使用).{5,}(?:方式|方法|流程)", 0.25),
    (r"(?:以后|今后|从现在起).{5,}(?:都要|必须|应该)", 0.2),
    # Processes in emails/notifications
    (r"(?:关于|对于).{3,}(?:流程|方案|计划|安排)", 0.2),
    (r"(?:通过后|验证后|完成后).{3,}(?:再|然后|接着)", 0.25),
    # Cause/effect/conditions
    (r"(?:如果|若|当).{5,}(?:就|则|立即|马上)", 0.2),
    (r"(?:发现|遇到|碰到).{5,}(?:就|则|应该)", 0.2),
]

# Strong Episodic signals (negative weight)
STRONG_EPISODIC_PATTERNS = [
    # Time descriptions
    (r"(?:今天|昨天|上周|刚才|之前)\s*(?:我|我们|他|她)", -0.3),
    (r"(?:开了个?会|会议上|讨论了|说了|提到了)", -0.3),
    (r"\d{1,2}[:\s点]\d{2}\s*(?:分|到|开始)", -0.2),
    # Event descriptions
    (r"(?:发生了|出现了|遇到了|碰到了)", -0.2),
    (r"(?:张三|李四|王五|某某)\s*(?:说|做|去|来)", -0.2),
]

# Generic/common knowledge signals (negative weight)
GENERIC_PATTERNS = [
    # Overly simple operations
    (r"(?:打开|关闭|点击|选择)\s*(?:文件|窗口|按钮|菜单|应用)", -0.4),
    (r"(?:open|close|click|select)\s+(?:file|window|button|app)", -0.4),
    # Common knowledge content
    (r"(?:大家都知道|众所周知|显而易见)", -0.3),
    (r"(?:一般来说|通常情况下|正常情况)", -0.2),
    # Too short step list (insufficient content)
    (r"^[^\n]{0,100}$", -0.2),  # Total less than 100 characters
]

# Content quality check (for filtering overly simple content)
MIN_MEANINGFUL_STEPS = 3  # At least 3 meaningful steps
MIN_CONTENT_LENGTH = 80  # Minimum character count


class ProceduralClassifier:
    """Procedural content classifier"""

    def __init__(
        self,
        procedural_threshold: float = 0.3,
        likely_threshold: float = 0.1,
    ):
        """
        Args:
            procedural_threshold: Threshold for explicit procedural
            likely_threshold: Threshold for likely procedural
        """
        self.procedural_threshold = procedural_threshold
        self.likely_threshold = likely_threshold

    def classify(self, content: str) -> ClassificationResult:
        """
        Classify content.

        Args:
            content: Input text

        Returns:
            ClassificationResult
        """
        if not content or len(content.strip()) < 20:
            return ClassificationResult(
                content_type=ContentType.GENERIC,
                is_procedural=False,
                confidence=0.9,
                reason="内容过短",
            )

        # Calculate signal score
        score = 0.0
        signals = []

        # Positive signals - explicit
        for pattern, weight in STRONG_PROCEDURAL_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                score += weight
                signals.append(f"+explicit:{pattern[:15]}")

        # Positive signals - implicit (identify from unstructured content)
        for pattern, weight in IMPLICIT_PROCEDURAL_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                score += weight
                signals.append(f"+implicit:{pattern[:15]}")

        # Negative signals
        for pattern, weight in STRONG_EPISODIC_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                score += weight  # weight is negative
                signals.append(f"episodic:{pattern[:15]}")

        for pattern, weight in GENERIC_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                score += weight
                signals.append(f"generic:{pattern[:15]}")

        # Additional heuristic checks
        # 0. Content quality check - directly penalize content that's too short
        if len(content.strip()) < MIN_CONTENT_LENGTH:
            score -= 0.3
            signals.append("too_short")

        # 1. Step count
        step_lines = re.findall(r"(?:^|\n)\s*[1-9][.、)]\s*[^\n]{5,}", content)
        if len(step_lines) >= MIN_MEANINGFUL_STEPS:
            score += 0.2
            signals.append(f"steps_count:{len(step_lines)}")
        elif len(step_lines) < 2 and len(content) < 200:
            # Too few steps and content too short
            score -= 0.2
            signals.append("few_steps")

        # 2. Code blocks
        if "```" in content or re.search(r"(?:^|\n)\s{4,}\S", content):
            score += 0.15
            signals.append("code_block")

        # 3. Length bonus (longer content more likely valuable)
        if len(content) > 500:
            score += 0.1
        elif len(content) > 1000:
            score += 0.15

        # Decision
        if score >= self.procedural_threshold:
            content_type = ContentType.PROCEDURAL
            is_procedural = True
            confidence = min(0.9, 0.5 + score)
            reason = "检测到明确的 procedural 信号"
        elif score >= self.likely_threshold:
            content_type = ContentType.LIKELY_PROCEDURAL
            is_procedural = True  # Still extract, but confidence is lower
            confidence = 0.4 + score * 0.5
            reason = "可能包含 procedural 内容"
        elif score <= -0.3:
            # Strong negative signals
            if any("episodic" in s for s in signals):
                content_type = ContentType.EPISODIC
                reason = "检测到事件/对话特征"
            else:
                content_type = ContentType.GENERIC
                reason = "检测到通用/常识特征"
            is_procedural = False
            confidence = 0.6 - score  # score is negative, so +
        else:
            # Uncertain
            content_type = ContentType.FACTUAL
            is_procedural = False
            confidence = 0.5
            reason = "未检测到明确的 procedural 信号"

        return ClassificationResult(
            content_type=content_type,
            is_procedural=is_procedural,
            confidence=round(confidence, 2),
            signals=signals[:10],
            reason=reason,
        )

    def should_extract_procedural(self, content: str) -> Tuple[bool, str]:
        """
        Simplified interface: whether should extract procedural.

        Returns:
            (should_extract, reason)
        """
        result = self.classify(content)
        return result.is_procedural, result.reason


# ========== Convenience Functions ==========

_default_classifier = ProceduralClassifier()


def classify_content(content: str) -> ClassificationResult:
    """Classify whether content is procedural."""
    return _default_classifier.classify(content)


def should_extract_procedural(content: str) -> Tuple[bool, str]:
    """
    Determine whether should extract procedural.

    Returns:
        (should_extract, reason)
    """
    return _default_classifier.should_extract_procedural(content)
