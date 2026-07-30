"""
EigenFlux 数据模型

定义广播消息、订阅、Agent 档案等核心数据结构。
"""

import uuid
import time
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Union
from enum import Enum


class Visibility(str, Enum):
    """广播可见性"""
    PUBLIC = "public"          # 全网可见
    PRIVATE = "private"        # 仅自己可见
    FRIENDS = "friends"        # 仅好友可见
    SUBSCRIBERS = "subscribers"  # 仅订阅者可见


class BroadcastType(str, Enum):
    """广播类型"""
    INFORMATION = "information"    # 信息分享
    REQUEST = "request"            # 需求请求
    CAPABILITY = "capability"      # 能力发布
    SIGNAL = "signal"              # 信号/事件
    QUESTION = "question"          # 问题
    OFFER = "offer"                # 提供服务
    DISCUSSION = "discussion"      # 讨论


class MessagePriority(str, Enum):
    """消息优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


def _generate_id() -> str:
    return str(uuid.uuid4())


def _current_ts() -> int:
    return int(time.time())


@dataclass
class AgentProfile:
    """Agent 档案"""
    agent_id: str
    name: str = ""
    description: str = ""
    capabilities: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: int = field(default_factory=_current_ts)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentProfile":
        return cls(
            agent_id=data.get("agent_id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            capabilities=data.get("capabilities", []),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", _current_ts()),
        )


@dataclass
class BroadcastMessage:
    """广播消息"""
    content: str                                              # 广播内容（自然语言）
    agent_id: str                                             # 发送者 Agent ID
    broadcast_id: str = field(default_factory=_generate_id)
    broadcast_type: BroadcastType = BroadcastType.INFORMATION
    visibility: Visibility = Visibility.PUBLIC
    priority: MessagePriority = MessagePriority.NORMAL
    tags: List[str] = field(default_factory=list)             # 主题标签
    categories: List[str] = field(default_factory=list)       # 分类
    target_audience: List[str] = field(default_factory=list)  # 目标受众标签
    structured_data: Dict[str, Any] = field(default_factory=dict)  # 结构化数据
    attachments: List[Dict[str, Any]] = field(default_factory=list) # 附件
    expires_at: Optional[int] = None                           # 过期时间戳
    reply_to: Optional[str] = None                             # 回复的广播 ID
    created_at: int = field(default_factory=_current_ts)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["broadcast_type"] = self.broadcast_type.value
        d["visibility"] = self.visibility.value
        d["priority"] = self.priority.value
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BroadcastMessage":
        return cls(
            content=data.get("content", ""),
            agent_id=data.get("agent_id", ""),
            broadcast_id=data.get("broadcast_id", _generate_id()),
            broadcast_type=BroadcastType(data.get("broadcast_type", "information")),
            visibility=Visibility(data.get("visibility", "public")),
            priority=MessagePriority(data.get("priority", "normal")),
            tags=data.get("tags", []),
            categories=data.get("categories", []),
            target_audience=data.get("target_audience", []),
            structured_data=data.get("structured_data", {}),
            attachments=data.get("attachments", []),
            expires_at=data.get("expires_at"),
            reply_to=data.get("reply_to"),
            created_at=data.get("created_at", _current_ts()),
        )

    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

    def summary(self, max_len: int = 100) -> str:
        """获取内容摘要"""
        if len(self.content) <= max_len:
            return self.content
        return self.content[:max_len] + "..."


@dataclass
class Subscription:
    """订阅规则"""
    subscription_id: str = field(default_factory=_generate_id)
    agent_id: str = ""
    name: str = ""
    description: str = ""

    # 匹配条件（任一匹配即可，或者组合匹配）
    keywords: List[str] = field(default_factory=list)         # 关键词匹配
    tags: List[str] = field(default_factory=list)              # 标签匹配
    categories: List[str] = field(default_factory=list)       # 分类匹配
    broadcast_types: List[BroadcastType] = field(default_factory=list)  # 类型匹配
    sender_agent_ids: List[str] = field(default_factory=list)  # 指定发送者
    min_priority: Optional[MessagePriority] = None            # 最低优先级

    # 匹配模式
    match_mode: str = "any"     # "any": 满足任一条件, "all": 必须满足所有条件
    threshold: float = 0.6      # 关键词匹配阈值（0-1）

    # 行为配置
    enabled: bool = True
    auto_reply: bool = False                               # 收到后自动回复
    notification: bool = True                              # 是否通知用户
    callback_url: Optional[str] = None                     # 回调 URL
    webhook_headers: Dict[str, str] = field(default_factory=dict)

    created_at: int = field(default_factory=_current_ts)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["broadcast_types"] = [bt.value for bt in self.broadcast_types]
        if self.min_priority:
            d["min_priority"] = self.min_priority.value
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Subscription":
        bts = [BroadcastType(bt) for bt in data.get("broadcast_types", [])]
        mp = data.get("min_priority")
        return cls(
            subscription_id=data.get("subscription_id", _generate_id()),
            agent_id=data.get("agent_id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            keywords=data.get("keywords", []),
            tags=data.get("tags", []),
            categories=data.get("categories", []),
            broadcast_types=bts,
            sender_agent_ids=data.get("sender_agent_ids", []),
            min_priority=MessagePriority(mp) if mp else None,
            match_mode=data.get("match_mode", "any"),
            threshold=float(data.get("threshold", 0.6)),
            enabled=bool(data.get("enabled", True)),
            auto_reply=bool(data.get("auto_reply", False)),
            notification=bool(data.get("notification", True)),
            callback_url=data.get("callback_url"),
            webhook_headers=data.get("webhook_headers", {}),
            created_at=data.get("created_at", _current_ts()),
        )


@dataclass
class MatchResult:
    """匹配结果"""
    broadcast: BroadcastMessage
    subscription: Optional[Subscription]
    score: float                                          # 匹配分数 0-1
    matched_reasons: List[str] = field(default_factory=list)  # 匹配原因
    matched_keywords: List[str] = field(default_factory=list)  # 匹配到的关键词
    matched_tags: List[str] = field(default_factory=list)     # 匹配到的标签
    timestamp: int = field(default_factory=_current_ts)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "broadcast": self.broadcast.to_dict(),
            "subscription": self.subscription.to_dict() if self.subscription else None,
            "score": self.score,
            "matched_reasons": self.matched_reasons,
            "matched_keywords": self.matched_keywords,
            "matched_tags": self.matched_tags,
            "timestamp": self.timestamp,
        }


@dataclass
class BroadcastResponse:
    """广播响应"""
    success: bool
    broadcast_id: str = ""
    message: str = ""
    matched_count: int = 0                                  # 匹配到的接收者数量
    estimated_reach: int = 0                                # 预估触达
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InboxMessage:
    """收件箱消息（匹配到的广播 + 处理状态）"""
    match_result: MatchResult
    read: bool = False
    replied: bool = False
    starred: bool = False
    archived: bool = False
    labels: List[str] = field(default_factory=list)
    received_at: int = field(default_factory=_current_ts)
    processed_at: Optional[int] = None

    @property
    def broadcast(self) -> BroadcastMessage:
        return self.match_result.broadcast

    def to_dict(self) -> Dict[str, Any]:
        return {
            "match_result": self.match_result.to_dict(),
            "read": self.read,
            "replied": self.replied,
            "starred": self.starred,
            "archived": self.archived,
            "labels": self.labels,
            "received_at": self.received_at,
            "processed_at": self.processed_at,
        }
