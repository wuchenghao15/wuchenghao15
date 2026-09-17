"""
Procedural Trigger.

Two-layer trigger mechanism:
- Layer 1: Rule trigger (zero cost)
- Layer 2: LLM light classification (low cost, optional)

Triggers procedural retrieval if any condition is met (but whether injection is used is decided later):
1. User shows clear "process intent" words
2. User expresses "want to do something"
3. Conversation is in "task execution state"
4. User mentions "reuse/according to previous habit"
"""

import re
from dataclasses import dataclass
from typing import Optional, List
from m_flow.shared.logging_utils import get_logger

logger = get_logger("ProceduralTrigger")


@dataclass
class TriggerResult:
    """
    Trigger result.

    Attributes:
        triggered: Whether to trigger procedural retrieval
        reason: Trigger reason (for debugging)
        intent_phrase: Intent phrase (for QueryBuilder)
        confidence: Confidence high/medium/low
        source: Trigger source rule/llm
    """

    triggered: bool
    reason: str = ""
    intent_phrase: str = ""
    confidence: str = "medium"  # high / medium / low
    source: str = "rule"  # rule / llm


class ProceduralTrigger:
    """
    Procedural trigger.

    Two-layer trigger:
    1. Rule trigger (enabled by default)
    2. LLM classification (optional enhancement)
    """

    # ========== Rule Trigger Mode ==========

    # Strong signal words (direct trigger)
    STRONG_PATTERNS = [
        (r"步骤", "流程意图词:步骤"),
        (r"流程", "流程意图词:流程"),
        (r"方法", "流程意图词:方法"),
        (r"指南", "流程意图词:指南"),
        (r"排查", "流程意图词:排查"),
        (r"配置", "流程意图词:配置"),
        (r"回滚", "流程意图词:回滚"),
        (r"修复", "流程意图词:修复"),
        (r"部署", "流程意图词:部署"),
        (r"上线", "流程意图词:上线"),
        (r"复盘", "流程意图词:复盘"),
        (r"安装", "流程意图词:安装"),
        (r"操作流程", "流程意图词:操作流程"),
        (r"操作步骤", "流程意图词:操作步骤"),
        (r"怎么做", "流程意图词:怎么做"),
        (r"SOP", "流程意图词:SOP"),
        (r"runbook", "流程意图词:runbook"),
        (r"playbook", "流程意图词:playbook"),
        (r"checklist", "流程意图词:checklist"),
    ]

    # "怎么/如何" patterns (need to exclude state inquiries)
    HOW_PATTERNS = [
        (r"怎么[^\s样了]{1,}", "怎么+动作"),
        (r"如何[^\s了]{1,}", "如何+动作"),
    ]

    # Exclusion patterns (these are not procedural intent)
    EXCLUDE_PATTERNS = [
        r"怎么样",  # Asks about state
        r"怎么了",  # Asks what happened
        r"如何了",  # Asks about state
    ]

    # "Want to do something" patterns
    TASK_INTENT_PATTERNS = [
        (r"我要[^\s]{1,}", "任务意图:我要"),
        (r"帮我[^\s]{1,}", "任务意图:帮我"),
        (r"我们来[^\s]{1,}", "任务意图:我们来"),
        (r"接下来做[^\s]*", "任务意图:接下来做"),
        (r"给我一个\s*(plan|方案|计划)", "任务意图:给我方案"),
    ]

    # "Reuse/according to previous" patterns
    REUSE_PATTERNS = [
        (r"按我们之前", "复用:按我们之前"),
        (r"还是老流程", "复用:老流程"),
        (r"照旧", "复用:照旧"),
        (r"老办法", "复用:老办法"),
        (r"按以前", "复用:按以前"),
        (r"复用", "复用:复用"),
        (r"习惯", "复用:习惯"),
    ]

    # English signal words
    ENGLISH_PATTERNS = [
        (r"\bhow\s+to\b", "英文:how to"),
        (r"\bsteps?\b", "英文:steps"),
        (r"\bprocedure\b", "英文:procedure"),
        (r"\brunbook\b", "英文:runbook"),
        (r"\btroubleshoot", "英文:troubleshoot"),
        (r"\brollback\b", "英文:rollback"),
        (r"\bdeploy", "英文:deploy"),
        (r"\bconfig", "英文:config"),
        (r"\bsetup\b", "英文:setup"),
        (r"\binstall", "英文:install"),
    ]

    # Task execution state context signals
    EXECUTION_CONTEXT_PATTERNS = [
        (r"继续", "执行态:继续"),
        (r"下一步", "执行态:下一步"),
        (r"照做", "执行态:照做"),
        (r"执行", "执行态:执行"),
        (r"开始吧", "执行态:开始吧"),
        (r"进行", "执行态:进行"),
    ]

    def __init__(
        self,
        enable_llm_trigger: bool = False,
        llm_model: Optional[str] = None,
    ):
        """
        Initialize trigger.

        Args:
            enable_llm_trigger: Whether to enable LLM layer trigger
            llm_model: LLM model name (for layer 2)
        """
        self.enable_llm_trigger = enable_llm_trigger
        self.llm_model = llm_model

    def check(
        self,
        user_msg: str,
        conversation_ctx: Optional[List[str]] = None,
    ) -> TriggerResult:
        """
        Check whether to trigger procedural retrieval.

        Args:
            user_msg: Current user message
            conversation_ctx: Conversation context (recent assistant replies)

        Returns:
            TriggerResult
        """
        # Layer 1: Rule trigger
        rule_result = self._rule_trigger(user_msg, conversation_ctx)

        if rule_result.triggered:
            return rule_result

        # Layer 2: LLM trigger (optional)
        if self.enable_llm_trigger:
            llm_result = self._llm_trigger(user_msg, conversation_ctx)
            if llm_result.triggered:
                return llm_result

        return TriggerResult(
            triggered=False,
            reason="无匹配",
            intent_phrase="",
            confidence="low",
            source="rule",
        )

    def _rule_trigger(
        self,
        user_msg: str,
        conversation_ctx: Optional[List[str]] = None,
    ) -> TriggerResult:
        """Layer 1: Rule trigger."""

        # First check exclusion patterns
        for pattern in self.EXCLUDE_PATTERNS:
            if re.search(pattern, user_msg):
                # Check if there are other strong signal words overriding
                has_override = any(re.search(p[0], user_msg, re.IGNORECASE) for p in self.STRONG_PATTERNS)
                if not has_override:
                    return TriggerResult(
                        triggered=False,
                        reason=f"排除模式:{pattern}",
                    )

        user_msg_lower = user_msg.lower()

        # Check various patterns (by priority)
        all_patterns = [
            (self.STRONG_PATTERNS, "high"),
            (self.REUSE_PATTERNS, "high"),
            (self.HOW_PATTERNS, "medium"),
            (self.TASK_INTENT_PATTERNS, "medium"),
            (self.ENGLISH_PATTERNS, "medium"),
        ]

        for patterns, confidence in all_patterns:
            for pattern, reason in patterns:
                flags = re.IGNORECASE if any(c.isalpha() and c.islower() for c in pattern) else 0
                if re.search(pattern, user_msg, flags) or re.search(pattern, user_msg_lower, flags):
                    # Extract intent_phrase
                    intent_phrase = self._extract_intent_phrase(user_msg, pattern)
                    return TriggerResult(
                        triggered=True,
                        reason=reason,
                        intent_phrase=intent_phrase,
                        confidence=confidence,
                        source="rule",
                    )

        # Check task execution state (needs context)
        if conversation_ctx:
            for pattern, reason in self.EXECUTION_CONTEXT_PATTERNS:
                if re.search(pattern, user_msg):
                    # Check if last assistant response gave plan/steps
                    last_response = conversation_ctx[-1] if conversation_ctx else ""
                    if self._has_plan_in_response(last_response):
                        return TriggerResult(
                            triggered=True,
                            reason=reason + "+上轮有计划",
                            intent_phrase=user_msg,
                            confidence="medium",
                            source="rule",
                        )

        return TriggerResult(triggered=False, reason="无规则匹配")

    def _llm_trigger(
        self,
        user_msg: str,
        conversation_ctx: Optional[List[str]] = None,
    ) -> TriggerResult:
        """
        Layer 2: LLM light classification trigger.

        Use short prompt to let LLM determine whether to recall procedural.

        Note: This function returns synchronously, internally uses asyncio.run() to call LLM.
        """
        # TODO: Implement LLM trigger
        # Need to use LLMService for classification
        # Temporarily return not triggered
        logger.debug("[trigger] LLM trigger not implemented yet")
        return TriggerResult(triggered=False, reason="LLM trigger disabled")

    def _extract_intent_phrase(self, user_msg: str, matched_pattern: str) -> str:
        """Extract intent phrase from user message."""
        # Simple strategy: return key part of user message
        # Remove common colloquial words
        phrase = user_msg
        for word in ["请", "帮我", "我想", "我要", "能不能", "可以", "麻烦"]:
            phrase = phrase.replace(word, "")
        return phrase.strip()[:50]  # Limit length

    def _has_plan_in_response(self, response: str) -> bool:
        """Check if assistant response contains plan/steps."""
        plan_signals = [
            r"\d+\.\s",  # Numbered list
            r"第[一二三四五六七八九十\d]+步",
            r"首先.*然后",
            r"步骤如下",
            r"操作如下",
            r"接下来",
        ]
        return any(re.search(p, response) for p in plan_signals)


def should_trigger_procedural(
    user_msg: str,
    conversation_ctx: Optional[List[str]] = None,
    enable_llm: bool = False,
) -> TriggerResult:
    """
    Convenience function: determine whether to trigger procedural retrieval.

    Args:
        user_msg: User message
        conversation_ctx: Conversation context
        enable_llm: Whether to enable LLM trigger

    Returns:
        TriggerResult
    """
    trigger = ProceduralTrigger(enable_llm_trigger=enable_llm)
    return trigger.check(user_msg, conversation_ctx)
