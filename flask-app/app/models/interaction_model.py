#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交互模型 - 用户与系统交互管理
包含会话管理、消息处理、事件驱动、反馈收集等交互功能

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable

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

    def process_message(self, session_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理消息"""
        return self.message_handler.process(session_id, message)

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
        self.session_timeout = 3600  # 1小时超时
        logger.info("会话管理器初始化完成")

    def create_session(self, user_id: str) -> str:
        """创建会话"""
        session_id = str(uuid.uuid4())
            'user_id': user_id,
            'created_at': datetime.now(),
            'last_activity': datetime.now(),
            'data': {}
        }
        logger.info(f"创建会话: {session_id}")
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话"""
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]

        # 检查超时
        if (datetime.now() - session['last_activity']).seconds > self.session_timeout:
            del self.sessions[session_id]
            logger.info(f"会话超时: {session_id}")
            return None

        return session

        """更新会话数据"""
        if session_id in self.sessions:
            self.sessions[session_id]['data'].update(data)
            self.sessions[session_id]['last_activity'] = datetime.now()
            logger.info(f"更新会话: {session_id}")

    def destroy_session(self, session_id: str):
        """销毁会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"销毁会话: {session_id}")

    def cleanup_expired_sessions(self):
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

        results = []
        for handler in self.handlers[message_type]:
            try:
                result = handler(session_id, message)
                results.append({'success': True, 'result': result})
                results.append({'success': False, 'error': str(e)})
                logger.error(f"消息处理失败 {message_type}: {str(e)}")

        return {'status': 'success', 'results': results}

class EventSystem:
    """事件系统"""

    def __init__(self):
        logger.info("事件系统初始化完成")

    def register_listener(self, event_type: str, handler: Callable):
        """注册事件监听器"""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(handler)
        logger.info(f"注册事件监听器: {event_type}")

    def trigger(self, event_type: str, data: Dict[str, Any]):
        if event_type not in self.listeners:
            logger.warning(f"未找到事件监听器: {event_type}")
            return

        event = {
            'type': event_type,
            'data': data,
        }

        for listener in self.listeners[event_type]:
            try:
                listener(event)
                logger.error(f"事件处理失败 {event_type}: {str(e)}")

        logger.info(f"触发事件: {event_type}")
class FeedbackCollector:
    """反馈收集器"""

    def __init__(self):
        logger.info("反馈收集器初始化完成")

    def collect(self, feedback: Dict[str, Any]):
        feedback['timestamp'] = datetime.now().isoformat()
        self.feedbacks.append(feedback)

    def get_feedbacks(self, filter_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取反馈"""
        if filter_type:
            return [f for f in self.feedbacks if f.get('type') == filter_type]
        return self.feedbacks
    def analyze_feedbacks(self) -> Dict[str, Any]:
        """分析反馈"""
        analysis = {
            'total': len(self.feedbacks),
            'types': {},
            'ratings': {'positive': 0, 'neutral': 0, 'negative': 0}
        }

        for feedback in self.feedbacks:
            feedback_type = feedback.get('type', 'other')
            analysis['types'][feedback_type] = analysis['types'].get(feedback_type, 0) + 1

            rating = feedback.get('rating', 3)
            if rating >= 4:
                analysis['ratings']['positive'] += 1
            elif rating == 3:
                analysis['ratings']['neutral'] += 1
                analysis['ratings']['negative'] += 1

        return analysis

# 全局实例
interaction_model = InteractionModel()

def init_interaction_model():
    """初始化交互模型"""
    logger.info("初始化交互模型...")

    # 注册消息处理器
    interaction_model.message_handler.register_handler(
        'user_command',
        lambda session_id, msg: {'processed': True, 'command': msg.get('content')}
    )

    interaction_model.message_handler.register_handler(
        'system_event',
        lambda session_id, msg: {'processed': True, 'event': msg.get('event')}
    )

    # 注册事件监听器
    interaction_model.register_event_listener(
        'user_login',
        lambda event: logger.info(f"用户登录: {event['data'].get('user_id')}")
    )

    interaction_model.register_event_listener(
        'user_logout',
        lambda event: logger.info(f"用户登出: {event['data'].get('user_id')}")
    )

    logger.info("交互模型初始化完成")

if __name__ == "__main__":
    init_interaction_model()
