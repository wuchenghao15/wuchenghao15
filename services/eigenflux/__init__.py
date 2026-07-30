"""
EigenFlux.ai - AI Agent 广播网络通信层集成模块

EigenFlux 是一个为自主智能体打造的通信层开源框架，支持：
- Agent 广播信息、需求、能力
- Agent 订阅感兴趣的主题
- AI 匹配引擎进行个性化内容路由
- 自部署 Hub 或连接公共网络
"""

from .config import EigenFluxConfig, get_config
from .models import (
    BroadcastMessage,
    Subscription,
    AgentProfile,
    MatchResult,
    BroadcastResponse,
    InboxMessage,
    Visibility,
    BroadcastType,
    MessagePriority,
)
from .client import EigenFluxClient
from .broadcaster import Broadcaster
from .subscriber import Subscriber
from .matcher import SimpleMatcher
from .hub import EigenFluxHubManager, HubStatus
from .service import EigenFluxService, get_service

__all__ = [
    # 配置
    "EigenFluxConfig",
    "get_config",
    # 数据模型
    "BroadcastMessage",
    "Subscription",
    "AgentProfile",
    "MatchResult",
    "BroadcastResponse",
    "InboxMessage",
    "Visibility",
    "BroadcastType",
    "MessagePriority",
    # 核心组件
    "EigenFluxClient",
    "Broadcaster",
    "Subscriber",
    "SimpleMatcher",
    "EigenFluxHubManager",
    "HubStatus",
    # 服务
    "EigenFluxService",
    "get_service",
]

__version__ = "1.0.0"
