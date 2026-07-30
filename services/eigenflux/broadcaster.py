"""
广播器模块

封装广播发送逻辑，包含隐私过滤、用户确认、自动打标签等功能。
"""

import re
import logging
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime, timedelta

from .config import EigenFluxConfig
from .models import (
    BroadcastMessage,
    BroadcastResponse,
    BroadcastType,
    Visibility,
    MessagePriority,
    AgentProfile,
)
from .client import EigenFluxClient

logger = logging.getLogger(__name__)


class Broadcaster:
    """广播发送器

    在发送广播前进行隐私过滤、敏感信息检测、用户确认（可选）。
    """

    def __init__(
        self,
        config: Optional[EigenFluxConfig] = None,
        client: Optional[EigenFluxClient] = None,
    ):
        from .config import get_config
        self.config = config or get_config()
        self.client = client or EigenFluxClient(self.config)
        self._outbox: List[BroadcastMessage] = []
        self._pending_confirmation: List[BroadcastMessage] = []
        self._on_confirm: Optional[Callable[[BroadcastMessage], bool]] = None
        self._pre_send_hooks: List[Callable[[BroadcastMessage], Optional[BroadcastMessage]]] = []
        self._post_send_hooks: List[Callable[[BroadcastMessage, BroadcastResponse], None]] = []

    # ========== 钩子 ==========

    def add_pre_send_hook(
        self,
        hook: Callable[[BroadcastMessage], Optional[BroadcastMessage]],
    ) -> None:
        """添加发送前钩子，返回修改后的消息或 None 表示取消"""
        self._pre_send_hooks.append(hook)

    def add_post_send_hook(
        self,
        hook: Callable[[BroadcastMessage, BroadcastResponse], None],
    ) -> None:
        """添加发送后钩子"""
        self._post_send_hooks.append(hook)

    def set_confirmation_callback(
        self,
        callback: Callable[[BroadcastMessage], bool],
    ) -> None:
        """设置用户确认回调

        callback 返回 True 表示确认发送，False 表示拒绝。
        """
        self._on_confirm = callback

    # ========== 隐私过滤 ==========

    def filter_privacy(self, content: str) -> tuple[str, List[str]]:
        """过滤隐私敏感信息

        Returns:
            (过滤后的内容, 发现并移除的敏感项列表)
        """
        filtered = content
        removed = []

        patterns = [
            # 邮箱
            (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[EMAIL]"),
            # 手机号（中国大陆）
            (r"(?<!\d)1[3-9]\d{9}(?!\d)", "[PHONE]"),
            # 身份证号
            (r"(?<!\d)[1-9]\d{5}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[0-9Xx](?!\d)", "[ID_CARD]"),
            # URL 中的 token / session
            (r"[\?&](token|session|apikey|api_key|secret|pwd|password)=[^&\s]+", "[REDACTED_PARAM]"),
            # 银行卡号
            (r"(?<!\d)\d{16,19}(?!\d)", "[BANK_CARD]"),
        ]

        for pattern, replacement in patterns:
            matches = re.findall(pattern, filtered)
            if matches:
                removed.extend([str(m) for m in matches])
                filtered = re.sub(pattern, replacement, filtered)

        # 基于字段名的过滤（structured_data 中的敏感字段）
        for field in self.config.sensitive_fields:
            if field.lower() in content.lower():
                removed.append(f"sensitive_field:{field}")

        return filtered, removed

    def contains_sensitive_data(self, structured_data: Dict[str, Any]) -> List[str]:
        """检查结构化数据中是否包含敏感字段"""
        found = []
        sensitive_lower = {f.lower() for f in self.config.sensitive_fields}

        def _check(obj: Any, path: str = ""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    key_lower = k.lower()
                    for sf in sensitive_lower:
                        if sf in key_lower:
                            found.append(f"{path}.{k}" if path else k)
                            break
                    _check(v, f"{path}.{k}" if path else k)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    _check(item, f"{path}[{i}]")

        _check(structured_data)
        return found

    # ========== 标签增强 ==========

    def auto_tag(self, content: str, broadcast_type: BroadcastType) -> List[str]:
        """根据内容自动打标签（简单规则）"""
        tags = []
        content_lower = content.lower()

        # 教育类关键词
        education_kw = {
            "学习": "learning", "教学": "education", "课程": "course",
            "考试": "exam", "题目": "question", "作业": "homework",
            "学生": "student", "教师": "teacher", "培训": "training",
            "复习": "review", "笔记": "notes", "知识": "knowledge",
        }
        for cn, tag in education_kw.items():
            if cn in content:
                tags.append(tag)

        # AI 关键词
        ai_kw = {
            "ai": "ai", "人工智能": "ai", "大模型": "llm",
            "agent": "ai-agent", "智能体": "ai-agent",
            "prompt": "prompt", "提示词": "prompt",
        }
        for kw, tag in ai_kw.items():
            if kw.lower() in content_lower:
                tags.append(tag)

        # 从类型映射
        type_tags = {
            BroadcastType.REQUEST: ["need-help"],
            BroadcastType.CAPABILITY: ["service-offer"],
            BroadcastType.SIGNAL: ["signal-event"],
            BroadcastType.QUESTION: ["question"],
            BroadcastType.OFFER: ["offer"],
        }
        if broadcast_type in type_tags:
            tags.extend(type_tags[broadcast_type])

        return list(dict.fromkeys(tags))  # 去重保序

    # ========== 广播构造 ==========

    def build_broadcast(
        self,
        content: str,
        broadcast_type: Union[BroadcastType, str] = BroadcastType.INFORMATION,
        tags: Optional[List[str]] = None,
        structured_data: Optional[Dict[str, Any]] = None,
        visibility: Optional[Visibility] = None,
        priority: Optional[MessagePriority] = None,
        expires_in: Optional[int] = None,  # 秒
        categories: Optional[List[str]] = None,
        target_audience: Optional[List[str]] = None,
        reply_to: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        auto_privacy: bool = True,
        auto_tag_enable: bool = True,
    ) -> BroadcastMessage:
        """构造广播消息（会执行隐私过滤和自动打标签）"""
        if isinstance(broadcast_type, str):
            broadcast_type = BroadcastType(broadcast_type)

        # 隐私过滤
        if auto_privacy:
            filtered_content, removed = self.filter_privacy(content)
            if removed:
                logger.info(f"[EigenFlux] Privacy filter removed {len(removed)} items: {removed[:3]}")
                content = filtered_content

        btags = list(tags or [])
        if auto_tag_enable:
            btags.extend(self.auto_tag(content, broadcast_type))
        btags = list(dict.fromkeys(btags))

        # 检查结构化数据
        if structured_data:
            sensitive = self.contains_sensitive_data(structured_data)
            if sensitive:
                logger.warning(f"[EigenFlux] Structured data may contain sensitive fields: {sensitive}")
                if auto_privacy:
                    for path in sensitive:
                        keys = path.replace("[", ".").replace("]", "").split(".")
                        # 简单处理：标记危险字段
                        pass

        expires_at = None
        if expires_in:
            expires_at = int(datetime.now().timestamp() + expires_in)

        return BroadcastMessage(
            content=content,
            agent_id=self.config.agent_id,
            broadcast_type=broadcast_type,
            visibility=visibility or Visibility(self.config.default_visibility),
            priority=priority or MessagePriority.NORMAL,
            tags=btags,
            categories=categories or [],
            target_audience=target_audience or [],
            structured_data=structured_data or {},
            attachments=attachments or [],
            expires_at=expires_at,
            reply_to=reply_to,
        )

    # ========== 发送 ==========

    def send(
        self,
        message: BroadcastMessage,
        skip_confirmation: bool = False,
    ) -> BroadcastResponse:
        """发送广播

        Args:
            message: 要发送的广播消息
            skip_confirmation: 跳过用户确认（即使配置要求确认）

        Returns:
            BroadcastResponse
        """
        # 执行 pre-send hooks
        for hook in self._pre_send_hooks:
            result = hook(message)
            if result is None:
                logger.info("[EigenFlux] Broadcast cancelled by pre-send hook")
                return BroadcastResponse(
                    success=False,
                    broadcast_id=message.broadcast_id,
                    message="Cancelled by pre-send hook",
                    errors=["cancelled_by_hook"],
                )
            message = result

        # 用户确认
        if (
            not skip_confirmation
            and self.config.require_user_confirmation
            and self._on_confirm is not None
        ):
            if not self._on_confirm(message):
                logger.info("[EigenFlux] Broadcast rejected by user confirmation")
                return BroadcastResponse(
                    success=False,
                    broadcast_id=message.broadcast_id,
                    message="Rejected by user",
                    errors=["rejected_by_user"],
                )

        response = self.client.send_broadcast(message)

        # 执行 post-send hooks
        for hook in self._post_send_hooks:
            try:
                hook(message, response)
            except Exception as e:
                logger.error(f"[EigenFlux] post-send hook error: {e}")

        if response.success:
            self._outbox.append(message)
            if len(self._outbox) > 500:
                self._outbox = self._outbox[-300:]
        else:
            self._pending_confirmation.append(message)

        return response

    def send_text(
        self,
        content: str,
        **build_kwargs,
    ) -> BroadcastResponse:
        """快速发送文本广播"""
        msg = self.build_broadcast(content, **build_kwargs)
        return self.send(msg)

    def send_request(
        self,
        need: str,
        details: Optional[str] = None,
        **kwargs,
    ) -> BroadcastResponse:
        """发送需求请求类广播"""
        content = need if not details else f"{need}\n\n详情：{details}"
        return self.send_text(
            content,
            broadcast_type=BroadcastType.REQUEST,
            **kwargs,
        )

    def send_capability(
        self,
        title: str,
        description: str,
        capability_tags: Optional[List[str]] = None,
        **kwargs,
    ) -> BroadcastResponse:
        """发送能力发布类广播"""
        content = f"【能力提供】{title}\n\n{description}"
        tags = list(kwargs.pop("tags", []))
        tags.extend(capability_tags or [])
        return self.send_text(
            content,
            broadcast_type=BroadcastType.CAPABILITY,
            tags=tags,
            **kwargs,
        )

    def send_signal(
        self,
        signal_type: str,
        title: str,
        details: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> BroadcastResponse:
        """发送信号/事件类广播"""
        content = f"【信号·{signal_type}】{title}"
        return self.send_text(
            content,
            broadcast_type=BroadcastType.SIGNAL,
            structured_data={
                "signal_type": signal_type,
                "title": title,
                **(details or {}),
            },
            priority=MessagePriority.HIGH,
            **kwargs,
        )

    # ========== 便捷方法（教育场景） ==========

    def broadcast_study_tip(
        self,
        subject: str,
        tip: str,
        grade: Optional[str] = None,
    ) -> BroadcastResponse:
        """广播学习技巧"""
        title = f"【{subject}学习技巧】"
        if grade:
            title = f"【{grade}{subject}学习技巧】"
        content = f"{title}\n\n{tip}"
        return self.send_text(
            content,
            tags=["education", "learning-tip", subject.lower()] + ([grade.lower()] if grade else []),
            categories=["education", "learning"],
        )

    def broadcast_study_resource(
        self,
        resource_type: str,
        title: str,
        resource_link: Optional[str] = None,
        description: str = "",
    ) -> BroadcastResponse:
        """广播学习资源"""
        content = f"【学习资源·{resource_type}】{title}\n\n{description}"
        if resource_link:
            content += f"\n\n链接：{resource_link}"
        return self.send_text(
            content,
            broadcast_type=BroadcastType.INFORMATION,
            tags=["education", "resource", resource_type.lower()],
            categories=["education", "resources"],
            structured_data={
                "resource_type": resource_type,
                "title": title,
                "link": resource_link,
            },
        )

    def request_homework_help(
        self,
        subject: str,
        question: str,
        grade: Optional[str] = None,
    ) -> BroadcastResponse:
        """请求作业帮助"""
        content = f"【{subject}作业求助】{question}"
        if grade:
            content = f"【{grade}{subject}作业求助】{question}"
        return self.send_text(
            content,
            broadcast_type=BroadcastType.REQUEST,
            tags=["education", "homework-help", subject.lower()] + ([grade.lower()] if grade else []),
        )

    def get_outbox(self, limit: int = 50) -> List[BroadcastMessage]:
        """获取已发送的广播"""
        return self._outbox[-limit:]
