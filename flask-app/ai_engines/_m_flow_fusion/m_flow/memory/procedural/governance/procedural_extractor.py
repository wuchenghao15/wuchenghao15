# m_flow/memory/procedural/governance/procedural_extractor.py
"""
Procedural Extractor: LLM-driven abstract memory extraction

Core concept:
- Procedural is "abstract dimension" memory, not "identify step format"
- What to remember: user habits, specific practices, operations that LLM needs additional information to reproduce
- Judged and extracted by LLM, not rule matching

Two storage types:
- procedure: Multi-step process → stored in Procedure (conical structure)
- preference: Simple preference/habit → stored in PreferencePoint (flat structure)

Routing principle:
- Has clear multi-steps, conditional branches, context dependencies → procedure
- Simple preferences, habits, single rules, no steps → preference
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from m_flow.shared.logging_utils import get_logger
from m_flow.llm.LLMGateway import LLMService

logger = get_logger()


# ============================================================
# LLM Output Schema
# ============================================================


class ExtractedProcedural(BaseModel):
    """Procedural abstracted from content"""

    title: str = Field(
        ...,
        description="Short title describing what method/habit/practice this is",
    )

    summary: str = Field(
        ...,
        description="Summary: Core points of this method/habit, what info LLM needs to reproduce it",
    )

    category: str = Field(
        ...,
        description="Category: user_preference | workflow | "
        "decision_rule | naming_convention | "
        "tool_usage | format_preference | "
        "quality_standard | safety_rule | "
        "habit | convention | other",
    )

    # Storage type classification
    memory_type: str = Field(
        ...,
        description="Storage type: 'procedure'(multi-step process, needs context and steps) | "
        "'preference'(simple preference/habit, single info point, no steps needed)",
    )

    what_to_remember: str = Field(
        ...,
        description="Most critical: What does LLM need to remember to reproduce this practice? "
        "(Not common sense, but specific to this user/team)",
    )

    when_to_apply: Optional[str] = Field(
        None,
        description="When should this method/habit be applied",
    )

    # Steps (only needed for procedure type)
    steps: Optional[str] = Field(
        None,
        description="If procedure type, provide specific steps (numbered list); if preference type, leave empty",
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Extraction confidence: 0.0-1.0",
    )

    evidence: str = Field(
        ...,
        description="Key evidence from source text supporting this extraction (quote original fragment)",
    )


class ExtractionResult(BaseModel):
    """Extraction result"""

    has_procedural: bool = Field(
        ...,
        description="Whether content contains extractable procedural (method/habit/practice)",
    )

    reasoning: str = Field(
        ...,
        description="Reasoning: Why this content contains/doesn't contain extractable procedural",
    )

    procedurals: List[ExtractedProcedural] = Field(
        default_factory=list,
        description="List of extracted procedurals (one content may contain multiple)",
    )


# ============================================================
# Prompt
# ============================================================


EXTRACTION_SYSTEM_PROMPT = """你是一个 Procedural Memory 提炼专家。

你的任务是从用户输入中**抽象出可复用的方法、习惯、做法**，并正确分类存储类型。

## 什么是 Procedural Memory？

Procedural 是 LLM 的"抽象维度"记忆：
- 不是事实（"今天开了会"是事实，不是 procedural）
- 不是常识（"先安装再使用"是常识，不需要特别记住）
- 而是**这个用户/团队特有的做法，LLM 需要额外信息才能复现**

## 两种存储类型（重要！）

### 1. procedure（流程记忆）
适用于：
- **技术性**多步骤方法/流程（3步以上）
- 有明确的**技术执行顺序**（不是日常活动顺序）
- 有条件分支/判断
- 需要上下文（前置条件、边界、异常处理）
- **关键特征**：每个步骤都需要**技术操作**（命令、配置、检查）

示例：
- "代码审查流程：1. 提交PR 2. 自动测试 3. 两人审批 4. 合并" → procedure
- "部署步骤：1. 环境检查 2. 拉取代码 3. 构建 4. 部署" → procedure

### 2. preference（偏好记忆）
适用于：
- 简单偏好/习惯（**无技术步骤**或1-2步）
- 用户个人喜好
- 单条规则/约定
- 固定的参数/配置/时间/地点
- **关键特征**：只需要**记住一个信息**，不需要多步骤执行

示例：
- "我喜欢用4空格缩进" → preference（格式偏好）
- "下班6点半打球，老地方见" → preference（固定时间地点，不是技术流程）
- "日志用 JSON 格式" → preference（格式偏好）
- "commit message 用中文" → preference（规范偏好）
- "紧急bug 1小时内响应" → preference（单条规则）
- "每周五下午代码审查" → preference（固定时间安排）

### 分流原则（重要！）
- 问自己：**"这是需要多步技术操作，还是只需要记住一个信息？"**
- 日常活动安排（打球、开会时间）→ **preference**（只需记住时间地点）
- 技术流程（部署、排障、审查）→ **procedure**（需要多步骤执行）

## 应该提炼的内容

1. **用户偏好/习惯** → 通常是 preference
   - 喜欢的输出格式、命名规范、代码风格
   - 工具链偏好、参数习惯
   - "我一般这样做..."

2. **具体工作流程** → 通常是 procedure
   - 团队特有的流程（不是通用最佳实践）
   - 特定环境的操作步骤
   - 包含内部系统、工具、参数的做法

3. **决策规则** → 根据复杂度判断
   - 简单规则 "如果A就B" → preference
   - 复杂规则带多个分支 → procedure

4. **质量/安全规则** → 通常是 preference
   - 必须遵守的约束
   - "不能..."、"必须..."

## 不应该提炼的内容

- 纯事件描述（"今天发生了..."）
- 通用常识（LLM 已经知道的）
- 一次性信息（没有复用价值）
- 纯闲聊对话（无偏好信息）
- **讨论中未达成共识的内容**（如"再想想"、"待定"）
- **通用业务流程**（如"用户提问→回答"这种任何系统都有的）

## 关键问题

1. **"LLM 需要这个信息吗？"**
   - 能 → 不需要记
   - 不能 → 应该提炼

2. **"这是流程还是偏好？"**
   - 有多步骤、顺序、分支 → procedure
   - 简单信息点、无步骤 → preference

## 输出规则（重要！）

1. 如果有可提炼的内容（无论是 procedure 还是 preference）：
   - has_procedural = true
   - 将提炼结果放入 procedurals 列表
   - 正确设置每个结果的 memory_type

2. 只有当内容**完全不包含**可提炼信息时：
   - has_procedural = false
   - procedurals 列表为空

3. **偏好也是 procedural！** 不要因为是简单偏好就不放入 procedurals。

输出 JSON 格式的 ExtractionResult。
"""

EXTRACTION_USER_PROMPT = """请分析以下内容，提炼出可复用的方法/习惯/做法：

---
{content}
---

注意：
1. 只提炼那些"LLM 需要额外信息才能复现"的内容
2. 不要提炼常识或通用知识
3. 关注用户/团队特有的做法
4. 如果没有可提炼的 procedural，has_procedural 设为 false
5. **正确判断 memory_type**：
   - 多步骤流程 → procedure
   - 简单偏好/习惯 → preference
6. **讨论未达成共识不要提炼**
7. **通用业务流程不要提炼**

输出 JSON 格式的 ExtractionResult。
"""


# ============================================================
# Extractor Result
# ============================================================


@dataclass
class ProceduralExtractionResult:
    """Extraction result (Python dataclass)"""

    has_procedural: bool
    reasoning: str
    procedurals: List[Dict[str, Any]] = field(default_factory=list)

    # Classified results
    procedures: List[Dict[str, Any]] = field(default_factory=list)  # memory_type=procedure
    preferences: List[Dict[str, Any]] = field(default_factory=list)  # memory_type=preference


# ============================================================
# Extractor
# ============================================================


class ProceduralExtractor:
    """
    LLM-driven Procedural extractor.

    Abstracts reusable methods/habits/practices from any content,
    and distinguishes between procedure (process) and preference (preference) types.
    """

    async def extract(
        self,
        content: str,
        context: Optional[str] = None,
        source_ref: Optional[str] = None,  # Source tracing
    ) -> ProceduralExtractionResult:
        """
        Extract Procedural from content.

        Args:
            content: Input content
            context: Optional context (conversation history, etc.)
            source_ref: Optional source reference (for tracing)

        Returns:
            ProceduralExtractionResult, containing classified procedures and preferences
        """
        # Lower minimum length, simple preferences may only be 10-20 characters
        if not content or len(content.strip()) < 10:
            return ProceduralExtractionResult(
                has_procedural=False,
                reasoning="内容过短，无法提炼",
            )

        # Prepare prompt
        user_prompt = EXTRACTION_USER_PROMPT.format(
            content=content[:3000]  # Truncate
        )

        if context:
            user_prompt = f"对话上下文：\n{context[:1000]}\n\n{user_prompt}"

        # Call LLM
        try:
            result = await LLMService.extract_structured(
                text_input=user_prompt,
                system_prompt=EXTRACTION_SYSTEM_PROMPT,
                response_model=ExtractionResult,
            )

            # Route: Classify by memory_type
            all_procedurals = [p.model_dump() for p in result.procedurals]
            procedures = []
            preferences = []

            for p in all_procedurals:
                # Add source tracing
                if source_ref:
                    p["source_ref"] = source_ref

                memory_type = p.get("memory_type", "procedure")
                if memory_type == "preference":
                    preferences.append(p)
                else:
                    procedures.append(p)

            return ProceduralExtractionResult(
                has_procedural=result.has_procedural,
                reasoning=result.reasoning,
                procedurals=all_procedurals,
                procedures=procedures,
                preferences=preferences,
            )

        except Exception as e:
            logger.error(f"Procedural extraction failed: {e}")
            return ProceduralExtractionResult(
                has_procedural=False,
                reasoning=f"提炼失败: {e}",
            )


# ============================================================
# Convenience Functions
# ============================================================


async def extract_procedural(
    content: str,
    context: Optional[str] = None,
    source_ref: Optional[str] = None,
) -> ProceduralExtractionResult:
    """
    Extract Procedural from content.

    This is a true "abstraction" process:
    - Not identifying step format
    - But understanding semantics, extracting reusable methods/habits
    - Automatically routes to procedure and preference types

    Args:
        content: Input content
        context: Optional conversation context
        source_ref: Optional source reference (for tracing)

    Returns:
        ProceduralExtractionResult, containing:
        - procedures: Process memory list
        - preferences: Preference memory list
    """
    extractor = ProceduralExtractor()
    return await extractor.extract(content, context, source_ref)


# ============================================================
# Correct positioning of rule classifier
# ============================================================


def should_skip_extraction(content: str) -> tuple[bool, str]:
    """
    Lightweight pre-filter: Only filter content that **obviously cannot** contain procedural.

    Note: This is not "identifying procedural", but "excluding obviously not".
    Prefer missing (let LLM judge) over false positives.

    Returns:
        (should_skip, reason)
    """
    import re

    content = content.strip()

    # Too short
    if len(content) < 30:
        return True, "内容过短"

    # Pure greetings/small talk (very conservative patterns)
    greeting_patterns = [
        r"^(你好|hi|hello|hey|嗨|早上好|晚上好|下午好)[!！。]?$",
        r"^(谢谢|thanks|thank you|ok|好的|嗯|哦)[!！。]?$",
    ]
    for pattern in greeting_patterns:
        if re.match(pattern, content, re.IGNORECASE):
            return True, "简单问候"

    # Other cases: Don't skip, let LLM judge
    return False, ""
