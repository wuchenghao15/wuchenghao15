"""
EigenFlux 统一服务层

整合客户端、广播器、订阅器、Hub 管理器，
提供一站式的高层面向业务的 API。
"""

import json
import logging
from typing import Optional, List, Dict, Any, Callable
from pathlib import Path

from .config import EigenFluxConfig, get_config
from .models import (
    BroadcastMessage,
    BroadcastResponse,
    Subscription,
    AgentProfile,
    InboxMessage,
    BroadcastType,
    MessagePriority,
    MatchResult,
)
from .client import EigenFluxClient
from .broadcaster import Broadcaster
from .subscriber import Subscriber
from .matcher import SimpleMatcher
from .hub import EigenFluxHubManager, HubStatus

logger = logging.getLogger(__name__)


class EigenFluxService:
    """EigenFlux 统一服务

    使用方式：
    ```python
    from services.eigenflux import get_service
    ef = get_service()

    # 启动后台接收
    ef.start()

    # 广播
    ef.broadcast("分享一个学习方法...")
    ef.broadcast_request("需要一位数学老师帮我出题")

    # 订阅
    sub_id = ef.subscribe_keywords(["高考", "数学", "复习方法"])

    # 获取收件箱
    msgs = ef.get_inbox(unread_only=True)
    ```
    """

    def __init__(
        self,
        config: Optional[EigenFluxConfig] = None,
    ):
        self.config = config or get_config()
        self.client = EigenFluxClient(self.config)
        self.matcher = SimpleMatcher(threshold=self.config.match_threshold)
        self.broadcaster = Broadcaster(self.config, self.client)
        self.subscriber = Subscriber(self.config, self.client, self.matcher)
        self.hub = EigenFluxHubManager(self.config)

        self._started = False
        self._on_new_message_handlers: List[Callable[[InboxMessage], None]] = []

    # ========== 生命周期 ==========

    def start(
        self,
        auto_register: bool = True,
        enable_polling: bool = True,
        enable_websocket: bool = True,
    ) -> bool:
        """启动 EigenFlux 服务

        Args:
            auto_register: 自动注册 Agent 档案
            enable_polling: 启用后台轮询
            enable_websocket: 启用 WebSocket 实时接收（如果可用）

        Returns:
            是否启动成功
        """
        if self._started:
            return True

        if not self.config.enabled:
            logger.info("[EigenFlux] Service disabled by config")
            return False

        logger.info("[EigenFlux] Starting service...")

        # 注册 Agent
        if auto_register and self.config.api_token:
            try:
                self.register_agent()
            except Exception as e:
                logger.warning(f"[EigenFlux] Auto-register agent failed: {e}")

        # 收件箱回调分发
        def _inbox_handler(msg: InboxMessage):
            for h in self._on_new_message_handlers:
                try:
                    h(msg)
                except Exception as e:
                    logger.error(f"[EigenFlux] on_new_message handler error: {e}")

        self.subscriber.add_handler(_inbox_handler)

        # 启动接收
        ws_ok = False
        if enable_websocket:
            try:
                ws_ok = self.subscriber.start_websocket()
            except Exception as e:
                logger.info(f"[EigenFlux] WebSocket init skipped: {e}")

        if enable_polling and not ws_ok:
            try:
                self.subscriber.start_polling()
            except Exception as e:
                logger.warning(f"[EigenFlux] Polling start failed: {e}")

        self._started = True
        logger.info(
            f"[EigenFlux] Service started (agent_id={self.config.agent_id}, "
            f"hub={self.config.hub_url}, ws={ws_ok})"
        )
        return True

    def stop(self) -> None:
        """停止服务"""
        if self._started:
            self.subscriber.stop_all()
            self._started = False
            logger.info("[EigenFlux] Service stopped")

    def is_started(self) -> bool:
        return self._started

    # ========== 新消息通知 ==========

    def on_new_message(self, handler: Callable[[InboxMessage], None]) -> None:
        """注册新消息回调"""
        self._on_new_message_handlers.append(handler)

    def remove_on_new_message(self, handler: Callable[[InboxMessage], None]) -> None:
        """移除新消息回调"""
        if handler in self._on_new_message_handlers:
            self._on_new_message_handlers.remove(handler)

    # ========== 广播 API ==========

    def broadcast(
        self,
        content: str,
        broadcast_type: str = "information",
        **kwargs,
    ) -> BroadcastResponse:
        """发送一条广播"""
        return self.broadcaster.send_text(
            content, broadcast_type=broadcast_type, **kwargs,
        )

    def broadcast_request(
        self,
        need: str,
        details: Optional[str] = None,
        **kwargs,
    ) -> BroadcastResponse:
        """发送需求广播"""
        return self.broadcaster.send_request(need, details, **kwargs)

    def broadcast_capability(
        self,
        title: str,
        description: str,
        capability_tags: Optional[List[str]] = None,
        **kwargs,
    ) -> BroadcastResponse:
        """广播能力提供"""
        return self.broadcaster.send_capability(
            title, description, capability_tags, **kwargs,
        )

    def broadcast_signal(
        self,
        signal_type: str,
        title: str,
        details: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> BroadcastResponse:
        """广播信号/事件"""
        return self.broadcaster.send_signal(signal_type, title, details, **kwargs)

    def broadcast_reply(
        self,
        reply_to_broadcast_id: str,
        content: str,
        **kwargs,
    ) -> BroadcastResponse:
        """回复一条广播"""
        msg = self.broadcaster.build_broadcast(
            content,
            broadcast_type="discussion",
            reply_to=reply_to_broadcast_id,
            **kwargs,
        )
        return self.broadcaster.send(msg)

    # ========== 订阅 API ==========

    def subscribe_keywords(
        self,
        keywords: List[str],
        name: str = "",
        **kwargs,
    ) -> str:
        """创建关键词订阅，返回订阅 ID"""
        return self.subscriber.subscribe_keywords(keywords, name, **kwargs)

    def subscribe_tags(
        self,
        tags: List[str],
        name: str = "",
        **kwargs,
    ) -> str:
        """创建标签订阅"""
        return self.subscriber.subscribe_tags(tags, name, **kwargs)

    def add_subscription(self, subscription: Subscription) -> str:
        """添加自定义订阅"""
        return self.subscriber.add_subscription(subscription)

    def remove_subscription(self, subscription_id: str) -> bool:
        """取消订阅"""
        return self.subscriber.remove_subscription(subscription_id)

    def list_subscriptions(self) -> List[Dict[str, Any]]:
        """列出所有订阅"""
        return [s.to_dict() for s in self.subscriber.get_subscriptions()]

    # ========== 收件箱 API ==========

    def get_inbox(
        self,
        limit: int = 50,
        unread_only: bool = False,
        min_score: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """获取收件箱消息"""
        return [
            m.to_dict()
            for m in self.subscriber.get_inbox(limit, unread_only, min_score)
        ]

    def get_unread_count(self) -> int:
        return self.subscriber.get_unread_count()

    def mark_read(self, broadcast_id: str) -> bool:
        return self.subscriber.mark_read(broadcast_id)

    def mark_all_read(self) -> int:
        return self.subscriber.mark_all_read()

    def star_message(self, broadcast_id: str, starred: bool = True) -> bool:
        return self.subscriber.star_message(broadcast_id, starred)

    def archive_message(self, broadcast_id: str, archived: bool = True) -> bool:
        return self.subscriber.archive_message(broadcast_id, archived)

    def poll_once(self) -> int:
        """手动触发一次轮询，返回新增消息数"""
        msgs = self.subscriber.poll_once()
        return len(msgs)

    # ========== Agent 档案 ==========

    def register_agent(self) -> Dict[str, Any]:
        """注册/更新 Agent 档案到 Hub"""
        profile = AgentProfile(
            agent_id=self.config.agent_id,
            name=self.config.agent_name,
            description=self.config.agent_description,
            capabilities=self.config.agent_capabilities,
            tags=self.config.default_interests,
        )
        return self.client.register_agent(profile)

    def get_my_profile(self) -> Dict[str, Any]:
        return self.client.get_agent_profile(self.config.agent_id)

    # ========== 搜索 & 浏览 ==========

    def search_broadcasts(
        self,
        query: str,
        tags: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """搜索广播"""
        return self.client.search_broadcasts(query, tags, page, page_size)

    def list_public_broadcasts(
        self,
        broadcast_type: Optional[str] = None,
        tag: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """浏览公共广播"""
        return self.client.list_broadcasts(
            broadcast_type=broadcast_type, tag=tag,
            page=page, page_size=page_size,
        )

    def list_public_agents(
        self,
        capability: Optional[str] = None,
        tag: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """浏览公共 Agent 列表"""
        return self.client.list_agents(capability, tag, page, page_size)

    # ========== 统计 ==========

    def get_network_stats(self) -> Dict[str, Any]:
        """获取网络统计"""
        try:
            return self.client.get_stats()
        except Exception as e:
            return {"error": str(e)}

    def get_my_stats(self) -> Dict[str, Any]:
        """获取当前 Agent 统计"""
        try:
            return self.client.get_my_stats()
        except Exception as e:
            return {"error": str(e)}

    # ========== 本地 Hub ==========

    def start_local_hub(
        self,
        mode: Optional[str] = None,
        switch_immediately: bool = True,
    ) -> HubStatus:
        """启动本地 Hub"""
        status = self.hub.start(mode)
        if status.running and switch_immediately:
            self.hub.switch_to_local_hub()
        return status

    def stop_local_hub(self) -> bool:
        return self.hub.stop()

    def local_hub_status(self) -> HubStatus:
        return self.hub.status()

    # ========== CLI 封装 ==========

    def install_cli(self) -> bool:
        return self.client.cli_install()

    def cli_available(self) -> bool:
        return self.client.cli_installed()

    def cli_run(self, *args: str) -> Dict[str, Any]:
        return self.client.cli_run(*args)

    # ========== 认证 ==========

    def auth_request_code(self, email: str) -> Dict[str, Any]:
        """请求邮箱登录验证码"""
        return self.client.auth_request_login_code(email)

    def auth_verify_code(self, email: str, code: str) -> Dict[str, Any]:
        """验证验证码并登录"""
        return self.client.auth_verify_login_code(email, code)

    def health_check(self) -> bool:
        return self.client.health_check()

    # ========== 持久化 ==========

    def save_state(self, path: Optional[str] = None) -> str:
        """保存当前状态（订阅、收件箱等）到 JSON 文件"""
        state_path = Path(path or (self.config.home_dir + "/state.json"))
        state_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "config": self.config.to_dict(),
            "subscriptions": [s.to_dict() for s in self.subscriber.get_subscriptions()],
            "inbox": [m.to_dict() for m in self.subscriber.get_inbox(limit=500)],
            "outbox": [m.to_dict() for m in self.broadcaster.get_outbox(limit=500)],
        }
        state_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(state_path)

    def load_state(self, path: Optional[str] = None) -> bool:
        """从 JSON 文件恢复状态"""
        state_path = Path(path or (self.config.home_dir + "/state.json"))
        if not state_path.exists():
            return False
        try:
            data = json.loads(state_path.read_text(encoding="utf-8"))
            # 恢复订阅
            for s in data.get("subscriptions", []):
                self.subscriber.add_subscription(
                    Subscription.from_dict(s), sync_to_remote=False,
                )
            return True
        except Exception as e:
            logger.error(f"[EigenFlux] Failed to load state: {e}")
            return False


# ===== 全局单例 =====
_service_instance: Optional[EigenFluxService] = None


def get_service(**overrides) -> EigenFluxService:
    """获取 EigenFlux 服务单例"""
    global _service_instance
    if _service_instance is None:
        cfg = get_config(**overrides)
        _service_instance = EigenFluxService(cfg)
    return _service_instance
