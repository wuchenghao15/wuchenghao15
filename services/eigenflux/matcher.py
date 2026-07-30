"""
本地匹配引擎

在 Agent 本地对广播和订阅进行匹配，减少网络请求。
采用关键词 + 标签 + 分类 + 语义启发式的综合评分算法。
"""

import re
import logging
from typing import Optional, List, Dict, Any, Tuple
from collections import Counter

from .models import (
    BroadcastMessage,
    Subscription,
    MatchResult,
    BroadcastType,
    MessagePriority,
)

logger = logging.getLogger(__name__)


class SimpleMatcher:
    """简单但高效的广播-订阅匹配器

    评分算法（各项加权，总分0-1）：
    - 关键词匹配：30%
    - 标签匹配：25%
    - 分类匹配：15%
    - 类型匹配：10%
    - 目标受众匹配：10%
    - 发送者白名单：5%
    - 优先级加分：最高 +0.1
    """

    def __init__(
        self,
        threshold: float = 0.6,
        language: str = "zh",
    ):
        self.threshold = threshold
        self.language = language
        self._stopwords_zh = set("的了是我在有和就不人都一一个上也很到说要去你会着没有看好这来他她它".split())

    # ========== 文本处理 ==========

    def _tokenize(self, text: str) -> List[str]:
        """简单分词（中英文混合）"""
        text = text.lower()
        # 英文单词
        words = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", text)
        # 中文 2-4 字片段
        chinese_chars = re.findall(r"[\u4e00-\u9fff]{2,}", text)
        for segment in chinese_chars:
            for i in range(len(segment)):
                for j in range(i + 2, min(i + 5, len(segment) + 1)):
                    words.append(segment[i:j])
        # 过滤停用词
        words = [w for w in words if w not in self._stopwords_zh]
        return words

    def _keyword_match_score(
        self,
        keywords: List[str],
        text: str,
        threshold: float = 0.6,
    ) -> Tuple[float, List[str]]:
        """关键词匹配评分（0-1），返回分数和匹配到的关键词"""
        if not keywords:
            return 0.0, []

        text_tokens = set(self._tokenize(text))
        matched = []
        total_score = 0.0

        for kw in keywords:
            kw_lower = kw.lower()
            # 直接字符串包含
            if kw_lower in text.lower():
                matched.append(kw)
                total_score += 1.0
                continue
            # 分词后匹配
            kw_tokens = set(self._tokenize(kw))
            if kw_tokens:
                overlap = len(kw_tokens & text_tokens)
                kw_score = overlap / max(len(kw_tokens), 1)
                if kw_score >= threshold:
                    matched.append(kw)
                    total_score += kw_score

        score = total_score / max(len(keywords), 1)
        return min(score, 1.0), matched

    # ========== 单项匹配 ==========

    def _tags_match(self, sub_tags: List[str], msg_tags: List[str]) -> Tuple[float, List[str]]:
        if not sub_tags or not msg_tags:
            return 0.0, []
        sub_set = {t.lower() for t in sub_tags}
        msg_set = {t.lower() for t in msg_tags}
        matched = list(sub_set & msg_set)
        score = len(matched) / max(len(sub_set), 1)
        return min(score, 1.0), matched

    def _categories_match(
        self, sub_cats: List[str], msg_cats: List[str],
    ) -> float:
        if not sub_cats or not msg_cats:
            return 0.0
        sub_set = {c.lower() for c in sub_cats}
        msg_set = {c.lower() for c in msg_cats}
        return len(sub_set & msg_set) / max(len(sub_set), 1)

    def _type_match(
        self, sub_types: List[BroadcastType], msg_type: BroadcastType,
    ) -> float:
        if not sub_types:
            return 0.0
        return 1.0 if msg_type in sub_types else 0.0

    def _sender_match(
        self, sub_senders: List[str], msg_sender: str,
    ) -> float:
        if not sub_senders:
            return 0.0
        return 1.0 if msg_sender in sub_senders else 0.0

    def _target_audience_match(
        self, sub_agent_capabilities: List[str], msg_audience: List[str],
    ) -> float:
        if not msg_audience or not sub_agent_capabilities:
            return 0.5  # 无特殊受众，默认半匹配
        caps = {c.lower() for c in sub_agent_capabilities}
        audience = {a.lower() for a in msg_audience}
        if caps & audience:
            return 1.0
        return 0.0

    def _priority_bonus(self, priority: MessagePriority) -> float:
        bonuses = {
            MessagePriority.LOW: -0.05,
            MessagePriority.NORMAL: 0.0,
            MessagePriority.HIGH: 0.05,
            MessagePriority.URGENT: 0.1,
        }
        return bonuses.get(priority, 0.0)

    # ========== 主匹配方法 ==========

    def match(
        self,
        broadcast: BroadcastMessage,
        subscription: Optional[Subscription] = None,
        agent_capabilities: Optional[List[str]] = None,
    ) -> MatchResult:
        """计算广播与订阅的匹配度"""
        reasons: List[str] = []
        matched_keywords: List[str] = []
        matched_tags: List[str] = []

        # 各子项分数
        kw_score = 0.0
        tag_score = 0.0
        cat_score = 0.0
        type_score = 0.0
        audience_score = 0.0
        sender_score = 0.0

        text_for_match = (
            f"{broadcast.content} "
            f"{' '.join(broadcast.tags)} "
            f"{' '.join(broadcast.categories)} "
            f"{' '.join(str(k) + ' ' + str(v) for k, v in broadcast.structured_data.items() if isinstance(v, str))}"
        )

        if subscription:
            # 关键词
            kw_score, matched_keywords = self._keyword_match_score(
                subscription.keywords, text_for_match, subscription.threshold,
            )
            if matched_keywords:
                reasons.append(f"关键词匹配: {', '.join(matched_keywords[:5])}")

            # 标签
            tag_score, matched_tags = self._tags_match(subscription.tags, broadcast.tags)
            if matched_tags:
                reasons.append(f"标签匹配: {', '.join(matched_tags[:5])}")

            # 分类
            cat_score = self._categories_match(subscription.categories, broadcast.categories)
            if cat_score > 0:
                reasons.append("分类匹配")

            # 类型
            type_score = self._type_match(subscription.broadcast_types, broadcast.broadcast_type)
            if type_score > 0:
                reasons.append(f"类型匹配: {broadcast.broadcast_type.value}")

            # 发送者
            sender_score = self._sender_match(subscription.sender_agent_ids, broadcast.agent_id)
            if sender_score > 0:
                reasons.append("发送者白名单匹配")

            # 最低优先级
            if subscription.min_priority:
                priority_order = ["low", "normal", "high", "urgent"]
                msg_idx = priority_order.index(broadcast.priority.value)
                min_idx = priority_order.index(subscription.min_priority.value)
                if msg_idx < min_idx:
                    return MatchResult(
                        broadcast=broadcast,
                        subscription=subscription,
                        score=0.0,
                        matched_reasons=["低于最低优先级"],
                    )

        # 目标受众（无订阅时也计算）
        caps = agent_capabilities or []
        audience_score = self._target_audience_match(caps, broadcast.target_audience)
        if audience_score == 1.0:
            reasons.append("命中目标受众")

        # 总分（加权）
        weights = {
            "kw": 0.30,
            "tag": 0.25,
            "cat": 0.15,
            "type": 0.10,
            "audience": 0.10,
            "sender": 0.05,
        }
        total = (
            weights["kw"] * kw_score
            + weights["tag"] * tag_score
            + weights["cat"] * cat_score
            + weights["type"] * type_score
            + weights["audience"] * audience_score
            + weights["sender"] * sender_score
        )

        # 优先级加分
        total += self._priority_bonus(broadcast.priority)
        total = max(0.0, min(1.0, total))

        if total == 0 and not reasons:
            reasons.append("无明确匹配特征")

        return MatchResult(
            broadcast=broadcast,
            subscription=subscription,
            score=total,
            matched_reasons=reasons,
            matched_keywords=matched_keywords,
            matched_tags=matched_tags,
        )

    def match_batch(
        self,
        broadcasts: List[BroadcastMessage],
        subscription: Subscription,
        agent_capabilities: Optional[List[str]] = None,
        sort: bool = True,
    ) -> List[MatchResult]:
        """批量匹配多个广播"""
        results = [
            self.match(b, subscription, agent_capabilities)
            for b in broadcasts
        ]
        if sort:
            results.sort(key=lambda r: r.score, reverse=True)
        return results

    def filter_by_threshold(
        self,
        results: List[MatchResult],
        threshold: Optional[float] = None,
    ) -> List[MatchResult]:
        """按阈值过滤匹配结果"""
        th = threshold if threshold is not None else self.threshold
        return [r for r in results if r.score >= th]

    # ========== 便捷评估 ==========

    def explain(self, result: MatchResult) -> str:
        """生成匹配结果的可读解释"""
        parts = [f"匹配分数: {result.score:.2f} (阈值 {self.threshold:.2f})"]
        if result.matched_reasons:
            parts.append("原因：")
            for reason in result.matched_reasons:
                parts.append(f"  - {reason}")
        if result.matched_keywords:
            parts.append(f"命中关键词: {', '.join(result.matched_keywords)}")
        if result.matched_tags:
            parts.append(f"命中标签: {', '.join(result.matched_tags)}")
        return "\n".join(parts)
