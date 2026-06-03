# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交互模型 - 用户与系统交互管理
包含会话管理、消息处理、事件驱动、反馈收集等交互功能
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
import sys

logger = logging.getLogger(__name__)


class InteractionModel:
    """交互模型核心类"""

    def __init__(self):
        self.session_manager = SessionManager()
        self.message_handler = MessageHandler()
        self.event_system = EventSystem()
        self.feedback_collector = FeedbackCollector()
        logger.info("交互模型初始化完成")

    def create_session(self, user_id: str) -> str:
        """创建会话"""
        return self.session_manager.create_session(user_id)

    def register_event_listener(self, event_type: str, handler: Callable):
        """注册事件监听器"""
        self.event_system.register_listener(event_type, handler)

    def trigger_event(self, event_type: str, data: Dict[str, Any]):
        """触发事件"""
        self.event_system.trigger(event_type, data)

    def collect_feedback(self, feedback: Dict[str, Any]):
        """收集反馈"""
        self.feedback_collector.collect(feedback)


class SessionManager:
    """会话管理器"""

    def __init__(self):
        self.sessions = {}
        self.session_timeout = 3600
        logger.info("会话管理器初始化完成")

    def create_session(self, user_id: str) -> str:
        """创建会话"""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            'user_id': user_id,
            'created_at': datetime.now(),
            'last_activity': datetime.now(),
            'data': {}
        }
        logger.info(f"创建会话: {session_id}")
        return session_id

    def destroy_session(self, session_id: str):
        """销毁会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"销毁会话: {session_id}")

    def cleanup_expired_sessions(self):
        """清理过期会话"""
        now = datetime.now()
        expired = [
            sid for sid, session in self.sessions.items()
            if (now - session['last_activity']).seconds > self.session_timeout
        ]

        for sid in expired:
            del self.sessions[sid]

        if expired:
            logger.info(f"清理过期会话: {len(expired)} 个")


class MessageHandler:
    """消息处理器"""

    def __init__(self):
        self.handlers = {}
        logger.info("消息处理器初始化完成")

    def register_handler(self, message_type: str, handler: Callable):
        """注册消息处理器"""
        if message_type not in self.handlers:
            self.handlers[message_type] = []
        self.handlers[message_type].append(handler)
        logger.info(f"注册消息处理器: {message_type}")

    def process(self, session_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理消息"""
        message_type = message.get('type', 'unknown')

        if message_type not in self.handlers:
            logger.warning(f"未找到消息处理器: {message_type}")
            return {'status': 'error', 'message': f'未找到消息处理器: {message_type}'}

        results = []
        for handler in self.handlers[message_type]:
            try:
                result = handler(session_id, message)
                results.append({'success': True, 'result': result})
            except Exception as e:
                results.append({'success': False, 'error': str(e)})
                logger.error(f"消息处理失败 {message_type}: {str(e)}")

        return {'status': 'success', 'results': results}


class EventSystem:
    """事件系统"""

    def __init__(self):
        self.listeners = {}
        logger.info("事件系统初始化完成")

    def register_listener(self, event_type: str, handler: Callable):
        """注册事件监听器"""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(handler)
        logger.info(f"注册事件监听器: {event_type}")

    def trigger(self, event_type: str, data: Dict[str, Any]):
        """触发事件"""
        if event_type not in self.listeners:
            logger.warning(f"未找到事件监听器: {event_type}")
            return

        event = {
            'type': event_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }

        for listener in self.listeners[event_type]:
            try:
                listener(event)
            except Exception as e:
                logger.error(f"事件处理失败 {event_type}: {str(e)}")

        logger.info(f"触发事件: {event_type}")


class FeedbackCollector:
    """反馈收集器"""

    def __init__(self):
        self.feedbacks = []
        logger.info("反馈收集器初始化完成")

    def collect(self, feedback: Dict[str, Any]):
        """收集反馈"""
        feedback['timestamp'] = datetime.now().isoformat()
        self.feedbacks.append(feedback)
        logger.info(f"收集反馈: {feedback.get('type', 'unknown')}")

    def get_feedbacks(self, filter_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取反馈"""
        if filter_type:
            return [f for f in self.feedbacks if f.get('type') == filter_type]
        return self.feedbacks


def init_interaction_model():
    """初始化交互模型"""
    logger.info("初始化交互模型...")

    interaction_model = InteractionModel()

    interaction_model.message_handler.register_handler(
        'user_command',
        lambda session_id, msg: {'processed': True, 'command': msg.get('content')}
    )

    interaction_model.message_handler.register_handler(
        'system_event',
        lambda session_id, msg: {'processed': True, 'event': msg.get('event')}
    )

    interaction_model.register_event_listener(
        'user_login',
        lambda event: logger.info(f"用户登录: {event['data'].get('user_id')}")
    )

    interaction_model.register_event_listener(
        'user_logout',
        lambda event: logger.info(f"用户登出: {event['data'].get('user_id')}")
    )

    logger.info("交互模型初始化完成")
    return interaction_model


if __name__ == "__main__":
    init_interaction_model()
