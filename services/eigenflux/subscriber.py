"""
订阅与接收模块

管理订阅规则、接收匹配消息、轮询或实时推送。
"""

import time
import logging
import threading
from typing import Optional, List, Dict, Any, Callable
from collections import deque

from .config import EigenFluxConfig
from .models import (
    BroadcastMessage,
    Subscription,
    MatchResult,
    InboxMessage,
    BroadcastType,
    MessagePriority,
)
from .client import EigenFluxClient
from .matcher import SimpleMatcher

logger = logging.getLogger(__name__)


class Subscriber:
    """订阅管理器

    管理订阅规则，通过轮询或 WebSocket 接收消息，
    并将匹配到的消息分发到回调函数。
    """

    def __init__(
        self,
        config: Optional[EigenFluxConfig] = None,
        client: Optional[EigenFluxClient] = None,
        matcher: Optional[SimpleMatcher] = None,
    ):
        from .config import get_config
        self.config = config or get_config()
        self.client = client or EigenFluxClient(self.config)
        self.matcher = matcher or SimpleMatcher(threshold=self.config.match_threshold)

        self._subscriptions: Dict[str, Subscription] = {}
        self._inbox: deque[InboxMessage] = deque(maxlen=self.config.max_cached_messages)
        self._handlers: List[Callable[[InboxMessage], None]] = []
        self._poll_thread: Optional[threading.Thread] = None
        self._poll_running = False
        self._last_poll_ts: int = 0

        # 初始化默认订阅
        self._init_default_subscription()

    def _init_default_subscription(self) -> None:
        """初始化默认订阅"""
        default_sub = Subscription(
            name="default-interests",
            description="默认兴趣订阅",
            agent_id=self.config.agent_id,
            tags=self.config.default_interests,
            keywords=self.config.default_interests,
            threshold=self.config.match_threshold,
        )
        self.add_subscription(default_sub, sync_to_remote=False)

    # ========== 订阅管理 ==========

    def add_subscription(
        self,
        subscription: Subscription,
        sync_to_remote: bool = True,
    ) -> str:
        """添加订阅规则

        Returns:
            subscription ID
        """
        subscription.agent_id = self.config.agent_id
        self._subscriptions[subscription.subscription_id] = subscription
        logger.info(f"[EigenFlux] Subscription added: id={subscription.subscription_id} name={subscription.name!r}")

        if sync_to_remote and self.config.api_token:
            try:
                self.client.create_subscription(subscription)
            except Exception as e:
                logger.warning(f"[EigenFlux] Failed to sync subscription to remote: {e}")

        return subscription.subscription_id

    def remove_subscription(self, subscription_id: str) -> bool:
        """移除订阅"""
        if subscription_id in self._subscriptions:
            sub = self._subscriptions.pop(subscription_id)
            logger.info(f"[EigenFlux] Subscription removed: {subscription_id}")
            try:
                self.client.delete_subscription(subscription_id)
            except Exception:
                pass
            return True
        return False

    def get_subscriptions(self) -> List[Subscription]:
        """获取所有订阅"""
        return list(self._subscriptions.values())

    def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """获取单个订阅"""
        return self._subscriptions.get(subscription_id)

    def subscribe_keywords(
        self,
        keywords: List[str],
        name: str = "",
        **kwargs,
    ) -> str:
        """快速创建关键词订阅"""
        sub = Subscription(
            name=name or f"kw-{'-'.join(keywords[:3])}",
            agent_id=self.config.agent_id,
            keywords=keywords,
            threshold=kwargs.pop("threshold", self.config.match_threshold),
            match_mode=kwargs.pop("match_mode", "any"),
            **kwargs,
        )
        return self.add_subscription(sub)

    def subscribe_tags(
        self,
        tags: List[str],
        name: str = "",
        **kwargs,
    ) -> str:
        """快速创建标签订阅"""
        sub = Subscription(
            name=name or f"tags-{'-'.join(tags[:3])}",
            agent_id=self.config.agent_id,
            tags=tags,
            threshold=kwargs.pop("threshold", 0.3),
            match_mode="any",
            **kwargs,
        )
        return self.add_subscription(sub)

    def subscribe_broadcast_type(
        self,
        types: List[BroadcastType],
        name: str = "",
        **kwargs,
    ) -> str:
        """订阅特定类型的广播"""
        sub = Subscription(
            name=name or f"type-{'-'.join(t.value for t in types[:3])}",
            agent_id=self.config.agent_id,
            broadcast_types=types,
            threshold=0.1,
            match_mode="any",
            **kwargs,
        )
        return self.add_subscription(sub)

    # ========== 匹配处理 ==========

    def process_broadcast(self, broadcast: BroadcastMessage) -> Optional[InboxMessage]:
        """处理一条广播，匹配所有订阅

        Returns:
            匹配成功返回 InboxMessage，否则 None
        """
        best_match: Optional[MatchResult] = None
        best_sub: Optional[Subscription] = None

        for sub in self._subscriptions.values():
            if not sub.enabled:
                continue
            result = self.matcher.match(broadcast, sub)
            if result.score >= sub.threshold:
                if best_match is None or result.score > best_match.score:
                    best_match = result
                    best_sub = sub

        if best_match is None:
            # 尝试本地无订阅匹配（基于默认兴趣）
            if self.config.enable_local_matching:
                default_sub = Subscription(
                    keywords=self.config.default_interests,
                    tags=self.config.default_interests,
                    threshold=self.config.match_threshold,
                )
                result = self.matcher.match(broadcast, default_sub)
                if result.score >= self.config.match_threshold:
                    best_match = result

        if best_match is None:
            return None

        inbox = InboxMessage(match_result=best_match)
        self._inbox.append(inbox)
        self._dispatch(inbox)

        if self.config.log_matching:
            logger.info(
                f"[EigenFlux] Matched broadcast {broadcast.broadcast_id} "
                f"score={best_match.score:.2f} sub={best_sub.name if best_sub else 'default'}"
            )

        return inbox

    def process_broadcast_dict(self, data: Dict[str, Any]) -> Optional[InboxMessage]:
        """从字典数据处理广播"""
        try:
            broadcast = BroadcastMessage.from_dict(data)
        except Exception as e:
            logger.error(f"[EigenFlux] Failed to parse broadcast: {e}")
            return None
        return self.process_broadcast(broadcast)

    # ========== 消息分发 ==========

    def add_handler(self, handler: Callable[[InboxMessage], None]) -> None:
        """添加收件箱消息处理器"""
        self._handlers.append(handler)

    def remove_handler(self, handler: Callable[[InboxMessage], None]) -> None:
        """移除消息处理器"""
        if handler in self._handlers:
            self._handlers.remove(handler)

    def _dispatch(self, inbox: InboxMessage) -> None:
        """分发消息到处理器"""
        for handler in list(self._handlers):
            try:
                handler(inbox)
            except Exception as e:
                logger.error(f"[EigenFlux] Inbox handler error: {e}")

        # 回调订阅的 webhook
        sub = inbox.match_result.subscription
        if sub and sub.callback_url:
            self._fire_webhook(sub, inbox)

    def _fire_webhook(self, sub: Subscription, inbox: InboxMessage) -> None:
        """触发 webhook 回调"""
        try:
            import requests
            payload = inbox.to_dict()
            requests.post(
                sub.callback_url,
                json=payload,
                headers=sub.webhook_headers,
                timeout=10,
            )
        except Exception as e:
            logger.warning(f"[EigenFlux] Webhook failed for {sub.callback_url}: {e}")

    # ========== 收件箱操作 ==========

    def get_inbox(
        self,
        limit: int = 50,
        unread_only: bool = False,
        min_score: Optional[float] = None,
    ) -> List[InboxMessage]:
        """获取收件箱消息"""
        messages = list(self._inbox)
        if unread_only:
            messages = [m for m in messages if not m.read]
        if min_score is not None:
            messages = [m for m in messages if m.match_result.score >= min_score]
        return messages[-limit:]

    def mark_read(self, broadcast_id: str) -> bool:
        """标记消息已读"""
        for msg in self._inbox:
            if msg.broadcast.broadcast_id == broadcast_id:
                msg.read = True
                msg.processed_at = int(time.time())
                return True
        return False

    def mark_all_read(self) -> int:
        """标记所有消息已读"""
        count = 0
        for msg in self._inbox:
            if not msg.read:
                msg.read = True
                msg.processed_at = int(time.time())
                count += 1
        return count

    def get_unread_count(self) -> int:
        """获取未读消息数"""
        return sum(1 for m in self._inbox if not m.read)

    def star_message(self, broadcast_id: str, starred: bool = True) -> bool:
        """星标/取消星标消息"""
        for msg in self._inbox:
            if msg.broadcast.broadcast_id == broadcast_id:
                msg.starred = starred
                return True
        return False

    def archive_message(self, broadcast_id: str, archived: bool = True) -> bool:
        """归档消息"""
        for msg in self._inbox:
            if msg.broadcast.broadcast_id == broadcast_id:
                msg.archived = archived
                return True
        return False

    # ========== 轮询 / 实时接收 ==========

    def poll_once(self) -> List[InboxMessage]:
        """执行一次轮询，拉取新消息并处理"""
        new_messages: List[InboxMessage] = []
        since = self._last_poll_ts or None
        self._last_poll_ts = int(time.time())

        try:
            # 方式1：直接调 API 收件箱
            resp = self.client.get_inbox(since=since, page_size=100)
            items = resp.get("items") or resp.get("data") or []
            for item in items:
                broadcast_data = item.get("broadcast") if isinstance(item, dict) else item
                inbox = self.process_broadcast_dict(broadcast_data)
                if inbox:
                    new_messages.append(inbox)
        except Exception as e:
            # 方式2：fallback 到 list_broadcasts
            try:
                resp = self.client.list_broadcasts(since=since, page_size=100)
                items = resp.get("items") or resp.get("data") or []
                for item in items:
                    inbox = self.process_broadcast_dict(item)
                    if inbox:
                        new_messages.append(inbox)
            except Exception as e2:
                logger.debug(f"[EigenFlux] Poll failed (both methods): {e2}")

        return new_messages

    def start_polling(self) -> bool:
        """启动后台轮询线程"""
        if self._poll_running:
            return True

        def _poll_loop():
            self._poll_running = True
            while self._poll_running:
                try:
                    self.poll_once()
                except Exception as e:
                    logger.error(f"[EigenFlux] Poll loop error: {e}")
                for _ in range(int(self.config.poll_interval)):
                    if not self._poll_running:
                        break
                    time.sleep(1)

        self._poll_thread = threading.Thread(target=_poll_loop, daemon=True)
        self._poll_thread.start()
        logger.info("[EigenFlux] Polling started")
        return True

    def stop_polling(self) -> None:
        """停止后台轮询"""
        self._poll_running = False

    def start_websocket(self) -> bool:
        """启动 WebSocket 实时接收"""
        def _ws_handler(msg: Dict[str, Any]) -> None:
            msg_type = msg.get("type")
            if msg_type == "broadcast":
                broadcast_data = msg.get("data") or msg.get("broadcast")
                if broadcast_data:
                    self.process_broadcast_dict(broadcast_data)
            elif msg_type == "inbox":
                inbox_list = msg.get("data") or []
                for item in inbox_list:
                    self.process_broadcast_dict(item)

        self.client.add_message_handler(_ws_handler)
        return self.client.start_websocket()

    def stop_all(self) -> None:
        """停止所有后台任务"""
        self.stop_polling()
        self.client.stop_websocket()

    # ========== 教育场景快捷订阅 ==========

    def subscribe_education_news(self) -> str:
        """订阅教育新闻和趋势"""
        return self.subscribe_keywords(
            keywords=["教育", "教学", "学习", "课改", "考试政策", "教育技术", "edtech"],
            name="education-news",
            categories=["education", "trends"],
        )

    def subscribe_subject_resources(self, subject: str) -> str:
        """订阅特定学科资源"""
        return self.subscribe_tags(
            tags=["education", "resource", subject.lower()],
            name=f"subject-{subject.lower()}-resources",
            description=f"{subject}学科学习资源订阅",
        )

    def subscribe_homework_requests(self, subject: Optional[str] = None) -> str:
        """订阅作业求助广播"""
        tags = ["homework-help"]
        if subject:
            tags.append(subject.lower())
        return self.subscribe_broadcast_type(
            types=[BroadcastType.REQUEST],
            name="homework-requests" + (f"-{subject.lower()}" if subject else ""),
            tags=tags,
            min_priority=MessagePriority.NORMAL,
        )

    def subscribe_ai_education_signals(self) -> str:
        """订阅 AI 教育领域信号"""
        return self.subscribe_keywords(
            keywords=[
                "AI教育", "AI tutor", "智能教育", "个性化学习",
                "自适应学习", "大模型教育", "LLM教育应用",
            ],
            tags=["ai", "education", "ai-agent", "edtech"],
            name="ai-education-signals",
            threshold=0.5,
        )
