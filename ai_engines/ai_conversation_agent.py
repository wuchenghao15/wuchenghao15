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
            '情感分析', '意图分类', '对话总结'
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
    
    def generate_response(self, conversation_id: str, user_message: str) -> Dict[str, Any]:
        """生成回复"""
        if conversation_id not in self.conversations:
            return {'error': '对话不存在'}
        
        self.add_message(conversation_id, 'user', user_message)
        
        responses = {
            'hello': ['你好！有什么我可以帮助你的吗？', '您好！很高兴为您服务。', '你好！请问需要什么帮助？'],
            'hi': ['嗨！你好！', 'Hi! 有什么需要帮助的？', '嗨！欢迎回来。'],
            'thanks': ['不客气！很高兴能帮助你。', '不用谢！有问题随时找我。', '感谢您的使用！'],
            'bye': ['再见！期待下次再见。', '拜拜！祝你一切顺利。', '再见！有需要再联系。'],
            'help': ['我可以帮助您解答问题、提供信息或完成各种任务。请告诉我您需要什么帮助？', '请问有什么我可以帮助您的吗？', '我很乐意为您提供帮助，请告诉我您的需求。'],
            'name': ['我是AI对话专家，很高兴认识你！', '我是AI助手，随时为您服务。', '我是AI对话专家，请问有什么需要帮助的？']
        }
        
        matched_key = None
        for key in responses:
            if key in user_message.lower():
                matched_key = key
                break
        
        if matched_key:
            response_content = responses[matched_key][len(self.conversations[conversation_id]['messages']) % len(responses[matched_key])]
        else:
            response_content = f"收到您的消息：{user_message[:30]}... 我会认真处理您的请求。"
        
        self.add_message(conversation_id, 'assistant', response_content)
        
        return {
            'response': response_content,
            'conversation_id': conversation_id,
            'message_count': len(self.conversations[conversation_id]['messages']),
            'timestamp': datetime.now().isoformat()
        }
    
    def analyze_intent(self, message: str) -> Dict[str, Any]:
        """分析意图"""
        intents = {
            'greeting': ['hello', 'hi', '你好', '您好', '嗨'],
            'farewell': ['bye', '再见', '拜拜', '走了'],
            'thank': ['thanks', '谢谢', '感谢', '多谢'],
            'help': ['help', '帮助', '请问', '怎么', '如何'],
            'question': ['?', '什么', '多少', '谁', '哪里', '何时'],
            'statement': ['我', '你', '他', '这', '那']
        }
        
        detected_intent = 'statement'
        confidence = 0.5
        
        for intent, keywords in intents.items():
            for keyword in keywords:
                if keyword in message.lower():
                    detected_intent = intent
                    confidence = min(0.9, confidence + 0.15)
                    break
        
        return {
            'message': message,
            'intent': detected_intent,
            'confidence': round(confidence, 2),
            'timestamp': datetime.now().isoformat()
        }
    
    def summarize_conversation(self, conversation_id: str) -> str:
        """总结对话"""
        if conversation_id not in self.conversations:
            return '对话不存在'
        
        conversation = self.conversations[conversation_id]
        messages = conversation['messages']
        
        user_messages = [m['content'] for m in messages if m['role'] == 'user']
        assistant_messages = [m['content'] for m in messages if m['role'] == 'assistant']
        
        summary = f"对话总结（{len(messages)}条消息）:\n\n"
        summary += "用户问题:\n"
        for msg in user_messages:
            summary += f"- {msg}\n"
        
        summary += "\nAI回复:\n"
        for msg in assistant_messages:
            summary += f"- {msg}\n"
        
        return summary
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """删除对话"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            'total_conversations': self.total_conversations,
            'total_messages': self.total_messages,
            'active_conversations': len(self.conversations),
            'avg_messages_per_conversation': self.total_messages / max(1, self.total_conversations)
        }

conversation_agent = AIConversationAgent('ai_conversation_001')
