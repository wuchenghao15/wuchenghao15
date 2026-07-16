#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS AI对话服务
提供多轮对话管理、上下文记忆和意图识别
"""

import os
import sys
import json
import time
import hashlib
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

logger = print


class Message:
    """对话消息"""

    def __init__(self, role: str, content: str, message_id: str = '',
                 tokens: int = 0, metadata: Dict[str, Any] = None,
                 timestamp: str = None):
        self.message_id = message_id or f"msg_{int(time.time()*1000)}"
        self.role = role  # system, user, assistant, tool
        self.content = content
        self.tokens = tokens
        self.metadata = metadata or {}
        self.timestamp = timestamp or datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'message_id': self.message_id,
            'role': self.role,
            'content': self.content,
            'tokens': self.tokens,
            'metadata': self.metadata,
            'timestamp': self.timestamp
        }


class Conversation:
    """对话会话"""

    def __init__(self, conversation_id: str, user_id: str = '',
                 title: str = '', system_prompt: str = '',
                 model_id: str = '', max_context_messages: int = 20):
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.title = title or '新对话'
        self.system_prompt = system_prompt
        self.model_id = model_id
        self.max_context_messages = max_context_messages
        self.messages: List[Message] = []
        self.intent: str = ''
        self.intent_confidence: float = 0.0
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.is_active = True
        self.total_tokens = 0
        self.summary = ''

    def add_message(self, role: str, content: str,
                    tokens: int = 0, metadata: Dict[str, Any] = None):
        """添加消息"""
        msg = Message(role, content, tokens=tokens, metadata=metadata)
        self.messages.append(msg)
        self.total_tokens += tokens
        self.updated_at = datetime.now().isoformat()

        if not self.title and role == 'user' and len(self.messages) == 1:
            self.title = content[:30]

        return msg

    def get_context(self) -> List[Dict[str, str]]:
        """获取上下文（最近的N条消息）"""
        recent = self.messages[-self.max_context_messages:]
        return [{'role': m.role, 'content': m.content} for m in recent]

    def get_full_context(self) -> List[Dict[str, str]]:
        """获取完整上下文"""
        context = []
        if self.system_prompt:
            context.append({'role': 'system', 'content': self.system_prompt})
        context.extend({'role': m.role, 'content': m.content} for m in self.messages)
        return context

    def to_dict(self) -> Dict[str, Any]:
        return {
            'conversation_id': self.conversation_id,
            'user_id': self.user_id,
            'title': self.title,
            'system_prompt': self.system_prompt,
            'model_id': self.model_id,
            'max_context_messages': self.max_context_messages,
            'message_count': len(self.messages),
            'intent': self.intent,
            'intent_confidence': self.intent_confidence,
            'total_tokens': self.total_tokens,
            'summary': self.summary,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'is_active': self.is_active
        }


# 意图分类规则
INTENT_PATTERNS = {
    'question': ['什么', '怎么', '如何', '为什么', '哪个', '哪里', '是否', '吗', '?', '？'],
    'command': ['执行', '运行', '创建', '删除', '修改', '更新', '设置', '启动', '停止'],
    'search': ['搜索', '查找', '找', '查询', '检索', 'search'],
    'chat': ['你好', 'hello', 'hi', '谢谢', '再见', '辛苦了'],
    'analysis': ['分析', '统计', '报表', '趋势', '对比', '预测'],
    'help': ['帮助', 'help', '用法', '说明', '教程'],
}


class AIConversationService:
    """AI对话服务"""

    def __init__(self):
        self.conversations: Dict[str, Conversation] = {}
        self.is_running = False
        self.lock = threading.Lock()
        self.max_conversations = 1000

        self._init_database()

    def _init_database(self):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL UNIQUE,
                    user_id TEXT,
                    title TEXT,
                    system_prompt TEXT,
                    model_id TEXT,
                    intent TEXT,
                    intent_confidence REAL DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    summary TEXT,
                    message_count INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT NOT NULL UNIQUE,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tokens INTEGER DEFAULT 0,
                    metadata TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_ai_conversations_user ON ai_conversations(user_id)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_ai_messages_conv ON ai_messages(conversation_id)
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[AI对话] 初始化数据库失败: {e}")

    def _generate_conversation_id(self) -> str:
        import uuid
        return f"conv_{uuid.uuid4().hex[:16]}"

    def create_conversation(self, user_id: str = '', title: str = '',
                            system_prompt: str = '', model_id: str = '') -> str:
        """创建对话"""
        conversation_id = self._generate_conversation_id()

        conv = Conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            title=title,
            system_prompt=system_prompt,
            model_id=model_id
        )

        with self.lock:
            if len(self.conversations) >= self.max_conversations:
                # 移除最旧的对话
                oldest = min(self.conversations.values(), key=lambda c: c.updated_at)
                self.conversations.pop(oldest.conversation_id, None)

            self.conversations[conversation_id] = conv

        self._save_conversation_to_db(conv)
        logger(f"[AI对话] 创建对话: {conversation_id}")

        return conversation_id

    def _save_conversation_to_db(self, conv: Conversation):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO ai_conversations
                (conversation_id, user_id, title, system_prompt, model_id,
                 intent, intent_confidence, total_tokens, summary,
                 message_count, is_active, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                conv.conversation_id, conv.user_id, conv.title,
                conv.system_prompt, conv.model_id,
                conv.intent, conv.intent_confidence, conv.total_tokens,
                conv.summary, len(conv.messages),
                1 if conv.is_active else 0, conv.updated_at
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[AI对话] 保存对话失败: {e}")

    def _save_message_to_db(self, conv_id: str, msg: Message):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO ai_messages
                (message_id, conversation_id, role, content, tokens, metadata, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                msg.message_id, conv_id, msg.role, msg.content,
                msg.tokens, json.dumps(msg.metadata), msg.timestamp
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[AI对话] 保存消息失败: {e}")

    def send_message(self, conversation_id: str, content: str,
                     role: str = 'user') -> Dict[str, Any]:
        """发送消息"""
        with self.lock:
            conv = self.conversations.get(conversation_id)
            if not conv:
                return {'success': False, 'error': 'conversation_not_found'}

            if not conv.is_active:
                return {'success': False, 'error': 'conversation_closed'}

            # 意图识别（仅对用户消息）
            if role == 'user':
                intent, confidence = self._detect_intent(content)
                conv.intent = intent
                conv.intent_confidence = confidence

            # 添加用户消息
            user_tokens = len(content) // 4
            user_msg = conv.add_message(role, content, tokens=user_tokens)
            self._save_message_to_db(conversation_id, user_msg)

        # 生成回复
        if role == 'user':
            response = self._generate_response(conv, content)

            with self.lock:
                assistant_tokens = len(response) // 4
                assistant_msg = conv.add_message('assistant', response,
                                                 tokens=assistant_tokens,
                                                 metadata={'intent': conv.intent})
                self._save_message_to_db(conversation_id, assistant_msg)

            self._save_conversation_to_db(conv)

            return {
                'success': True,
                'conversation_id': conversation_id,
                'response': response,
                'intent': conv.intent,
                'intent_confidence': conv.intent_confidence,
                'message_id': assistant_msg.message_id,
                'total_tokens': conv.total_tokens
            }

        self._save_conversation_to_db(conv)

        return {
            'success': True,
            'conversation_id': conversation_id,
            'message_id': user_msg.message_id
        }

    def _detect_intent(self, text: str) -> tuple:
        """意图识别"""
        text_lower = text.lower()
        scores = {}

        for intent, patterns in INTENT_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if pattern.lower() in text_lower:
                    score += 1
            scores[intent] = score

        if not scores or max(scores.values()) == 0:
            return ('unknown', 0.0)

        best_intent = max(scores, key=scores.get)
        confidence = min(scores[best_intent] / 3.0, 1.0)

        return (best_intent, round(confidence, 2))

    def _generate_response(self, conv: Conversation, user_input: str) -> str:
        """生成回复"""
        intent = conv.intent

        if intent == 'question':
            response = f"关于您的问题「{user_input[:50]}」，基于系统知识库分析，建议参考以下信息..."
        elif intent == 'command':
            response = f"已收到指令「{user_input[:50]}」，正在执行相关操作..."
        elif intent == 'search':
            response = f"正在搜索「{user_input[:50]}」相关信息，找到以下结果..."
        elif intent == 'chat':
            response = f"您好！很高兴为您服务。{user_input[:30]}"
        elif intent == 'analysis':
            response = f"正在对「{user_input[:50]}」进行数据分析，生成报表中..."
        elif intent == 'help':
            response = "MTSCOS AI助手可以帮助您：\n1. 回答系统相关问题\n2. 执行系统操作\n3. 搜索信息\n4. 数据分析和报表\n5. 系统监控和管理"
        else:
            response = f"已收到您的消息「{user_input[:50]}」，请问我能为您做什么？"

        return response

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        return self.conversations.get(conversation_id)

    def get_messages(self, conversation_id: str,
                     limit: int = 50) -> List[Dict[str, Any]]:
        """获取对话消息"""
        conv = self.conversations.get(conversation_id)
        if conv:
            return [m.to_dict() for m in conv.messages[-limit:]]

        # 从数据库加载
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM ai_messages WHERE conversation_id = ?
                ORDER BY timestamp DESC LIMIT ?
            ''', (conversation_id, limit))

            columns = [desc[0] for desc in cursor.description]
            messages = [dict(zip(columns, row)) for row in cursor.fetchall()]
            conn.close()

            return messages
        except:
            return []

    def get_user_conversations(self, user_id: str,
                               limit: int = 20) -> List[Dict[str, Any]]:
        """获取用户对话列表"""
        with self.lock:
            convs = [c for c in self.conversations.values() if c.user_id == user_id]
            convs.sort(key=lambda c: c.updated_at, reverse=True)
            return [c.to_dict() for c in convs[:limit]]

    def close_conversation(self, conversation_id: str) -> bool:
        """关闭对话"""
        with self.lock:
            conv = self.conversations.get(conversation_id)
            if not conv:
                return False
            conv.is_active = False

        self._save_conversation_to_db(conv)
        return True

    def delete_conversation(self, conversation_id: str) -> bool:
        """删除对话"""
        with self.lock:
            if conversation_id not in self.conversations:
                return False
            del self.conversations[conversation_id]

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM ai_conversations WHERE conversation_id = ?', (conversation_id,))
            cursor.execute('DELETE FROM ai_messages WHERE conversation_id = ?', (conversation_id,))
            conn.commit()
            conn.close()
        except:
            pass

        return True

    def summarize_conversation(self, conversation_id: str) -> str:
        """生成对话摘要"""
        conv = self.conversations.get(conversation_id)
        if not conv:
            return ''

        user_messages = [m.content for m in conv.messages if m.role == 'user']
        if not user_messages:
            return ''

        summary = f"对话包含 {len(conv.messages)} 条消息，主要话题：{user_messages[0][:50]}"

        with self.lock:
            conv.summary = summary

        self._save_conversation_to_db(conv)
        return summary

    def get_stats(self, hours: int = 24) -> Dict[str, Any]:
        """获取统计"""
        with self.lock:
            active = sum(1 for c in self.conversations.values() if c.is_active)
            total_messages = sum(len(c.messages) for c in self.conversations.values())
            total_tokens = sum(c.total_tokens for c in self.conversations.values())

            intent_dist = {}
            for c in self.conversations.values():
                if c.intent:
                    intent_dist[c.intent] = intent_dist.get(c.intent, 0) + 1

            return {
                'hours': hours,
                'total_conversations': len(self.conversations),
                'active_conversations': active,
                'total_messages': total_messages,
                'total_tokens': total_tokens,
                'intent_distribution': intent_dist
            }

    def get_status(self) -> Dict[str, Any]:
        return {
            'status': 'running' if self.is_running else 'stopped',
            'total_conversations': len(self.conversations),
            'max_conversations': self.max_conversations
        }

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        logger(f"[AI对话] 对话服务已启动")

    def stop(self):
        self.is_running = False
        logger(f"[AI对话] 对话服务已停止")


ai_conversation_service = AIConversationService()
