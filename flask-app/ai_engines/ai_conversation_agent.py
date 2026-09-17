#!/usr/bin/env python3
"""AI智能对话Agent"""

import os
import re
import logging
import json
from datetime import datetime
from typing import Dict, List, Any
from ai_engines.ai_employee_system import AIEmployee

logger = logging.getLogger(__name__)

class AIConversationAgent(AIEmployee):
    """AI对话Agent"""

    def __init__(self, employee_id: str, name: str = "AI对话专家"):
        super().__init__(employee_id, name, 'conversation', 6)
        self.skills = [
            '对话管理', '意图识别', '对话理解',
            '回复生成', '多轮对话', '上下文管理',
            '情感分析', '意图分类', '对话总结',
            '代码修复', '代码调试', '代码优化'
        ]
        self.conversations = {}
        self.total_conversations = 0
        self.total_messages = 0

    def create_conversation(self, user_id: str) -> Dict[str, Any]:
        """创建对话"""
        conversation_id = f"conv_{datetime.now().timestamp()}"

        self.conversations[conversation_id] = {
            'conversation_id': conversation_id,
            'user_id': user_id,
            'messages': [],
            'created_at': datetime.now().isoformat(),
            'last_message_at': None
        }

        self.total_conversations += 1

        return self.conversations[conversation_id]

    def add_message(self, conversation_id: str, role: str, content: str) -> Dict[str, Any]:
        """添加消息"""
        if conversation_id not in self.conversations:
            return {'error': '对话不存在'}

        conversation = self.conversations[conversation_id]
        message = {
            'id': f"msg_{datetime.now().timestamp()}",
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }

        conversation['messages'].append(message)
        conversation['last_message_at'] = message['timestamp']
        self.total_messages += 1

        return message

    def get_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """获取对话"""
        return self.conversations.get(conversation_id, {'error': '对话不存在'})

    def _extract_code_blocks(self, text: str) -> List[str]:
        """提取消息中的代码块"""
        pattern = r''
