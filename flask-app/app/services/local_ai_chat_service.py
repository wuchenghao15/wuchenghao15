# -*- coding: utf-8 -*-
"""
本地集成AI对话服务
支持多种本地AI后端（Ollama、本地模型、模拟模式）
提供完整的对话管理、上下文记忆、人格设定等功能
"""

import logging
import sqlite3
import json
import os
import time
import hashlib
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Generator
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class LocalAIChatService:
    """本地AI对话服务"""

    _instance = None
    _lock = threading.RLock()

    def __new__(cls, db_path: str = None):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(LocalAIChatService, cls).__new__(cls)
                    cls._instance._initialize(db_path)
        return cls._instance

    def _initialize(self, db_path: str = None):
        """初始化服务"""
        if db_path:
            self.db_path = db_path
        else:
            self.db_path = os.path.join(
                os.path.dirname(__file__), '..', '..', 'app.db'
            )
        self._init_tables()
        self._init_personalities()
        self._init_provider()
        logger.info("本地AI对话服务初始化完成")

    @contextmanager
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_tables(self):
        """初始化数据库表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_chat_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT DEFAULT '新对话',
                personality_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                message_count INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                tokens INTEGER DEFAULT 0,
                model TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_chat_personalities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                description TEXT,
                system_prompt TEXT NOT NULL,
                avatar TEXT,
                is_default INTEGER DEFAULT 0,
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_chat_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                provider TEXT DEFAULT 'mock',
                model TEXT DEFAULT 'default',
                temperature REAL DEFAULT 0.7,
                max_tokens INTEGER DEFAULT 2000,
                top_p REAL DEFAULT 0.9,
                context_window INTEGER DEFAULT 10,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id)
            )
            ''')

            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ai_chat_conv_user ON ai_chat_conversations(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ai_chat_msg_conv ON ai_chat_messages(conversation_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ai_chat_msg_user ON ai_chat_messages(user_id)')

            conn.commit()

    def _init_personalities(self):
        """初始化AI人格"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as count FROM ai_chat_personalities')
            count = cursor.fetchone()['count']

            if count == 0:
                personalities = [
                    (
                        'assistant', '智能助手',
                        '通用AI助手，擅长回答各种问题',
                        '你是一个友好、专业的AI助手。你会用简洁明了的语言回答用户的问题，提供实用的建议和帮助。',
                        '🤖', 1, 1
                    ),
                    (
                        'teacher', '学习导师',
                        '专注于学习辅导和知识讲解',
                        '你是一位耐心的学习导师。你擅长用通俗易懂的方式解释复杂概念，会引导学生思考，帮助他们真正理解知识。你会鼓励学生，激发他们的学习兴趣。',
                        '📚', 0, 2
                    ),
                    (
                        'code', '编程助手',
                        '专业的编程和技术问题解答',
                        '你是一位资深程序员和技术专家。你精通多种编程语言和技术栈，能够解答各种技术问题，提供代码示例和最佳实践建议。你会仔细分析问题，给出清晰的解决方案。',
                        '💻', 0, 3
                    ),
                    (
                        'writer', '写作助手',
                        '帮助写作和内容创作',
                        '你是一位才华横溢的写作助手。你擅长各种文体的写作，包括文章、报告、邮件、故事等。你会帮助用户优化表达，提升文采，同时保持用户的个人风格。',
                        '✍️', 0, 4
                    ),
                    (
                        'translator', '翻译官',
                        '多语言翻译和语言学习',
                        '你是一位专业的翻译官。你精通多种语言，能够提供准确、自然的翻译。你还会解释语言差异，帮助用户学习外语，了解不同文化。',
                        '🌐', 0, 5
                    ),
                ]

                for p in personalities:
                    cursor.execute(
                        '''INSERT INTO ai_chat_personalities 
                           (name, display_name, description, system_prompt, avatar, is_default, sort_order)
                           VALUES (?, ?, ?, ?, ?, ?, ?)''',
                        p
                    )
                conn.commit()
                logger.info("初始化AI人格完成")

    def _init_provider(self):
        """初始化AI提供商"""
        try:
            import requests
            self.ollama_available = False
            try:
                resp = requests.get('http://localhost:11434/api/tags', timeout=2)
                if resp.status_code == 200:
                    self.ollama_available = True
                    self.ollama_models = resp.json().get('models', [])
                    logger.info(f"检测到Ollama服务，可用模型: {len(self.ollama_models)}个")
            except Exception:
                self.ollama_available = False
                logger.info("未检测到Ollama服务，使用模拟模式")
        except ImportError:
            self.ollama_available = False
            logger.info("requests库不可用，使用模拟模式")

    def get_personalities(self) -> List[Dict]:
        """获取所有AI人格"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM ai_chat_personalities ORDER BY sort_order, id'
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_default_personality(self) -> Optional[Dict]:
        """获取默认人格"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM ai_chat_personalities WHERE is_default = 1 LIMIT 1'
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def create_conversation(self, user_id: int, title: str = None, personality_id: int = None) -> int:
        """创建新对话"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if personality_id is None:
                default = self.get_default_personality()
                personality_id = default['id'] if default else None

            cursor.execute(
                '''INSERT INTO ai_chat_conversations (user_id, title, personality_id)
                   VALUES (?, ?, ?)''',
                (user_id, title or '新对话', personality_id)
            )
            conn.commit()
            conv_id = cursor.lastrowid
            logger.info(f"创建新对话: 用户={user_id}, 对话ID={conv_id}")
            return conv_id

    def get_conversations(self, user_id: int, limit: int = 50) -> List[Dict]:
        """获取用户的对话列表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''SELECT * FROM ai_chat_conversations 
                   WHERE user_id = ? AND is_active = 1
                   ORDER BY updated_at DESC LIMIT ?''',
                (user_id, limit)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_conversation(self, conversation_id: int, user_id: int) -> Optional[Dict]:
        """获取对话详情"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM ai_chat_conversations WHERE id = ? AND user_id = ?',
                (conversation_id, user_id)
            )
            row = cursor.fetchone()
            if not row:
                return None

            conv = dict(row)

            cursor.execute(
                '''SELECT * FROM ai_chat_messages 
                   WHERE conversation_id = ?
                   ORDER BY created_at ASC''',
                (conversation_id,)
            )
            conv['messages'] = [dict(row) for row in cursor.fetchall()]

            return conv

    def get_messages(self, conversation_id: int, limit: int = 50) -> List[Dict]:
        """获取对话消息"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''SELECT * FROM ai_chat_messages 
                   WHERE conversation_id = ?
                   ORDER BY created_at DESC LIMIT ?''',
                (conversation_id, limit)
            )
            return [dict(row) for row in reversed(cursor.fetchall())]

    def send_message(self, conversation_id: int, user_id: int, content: str,
                     provider: str = None, model: str = None) -> Dict:
        """发送消息并获取回复"""
        settings = self.get_user_settings(user_id)
        provider = provider or settings.get('provider', 'mock')
        model = model or settings.get('model', 'default')

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                'SELECT * FROM ai_chat_conversations WHERE id = ? AND user_id = ?',
                (conversation_id, user_id)
            )
            conv = cursor.fetchone()
            if not conv:
                raise ValueError("对话不存在")

            cursor.execute(
                '''INSERT INTO ai_chat_messages 
                   (conversation_id, user_id, role, content, model)
                   VALUES (?, ?, ?, ?, ?)''',
                (conversation_id, user_id, 'user', content, model)
            )

            history = self._build_history(cursor, conversation_id, settings.get('context_window', 10))

            personality = self._get_personality_by_id(cursor, conv['personality_id'])
            system_prompt = personality['system_prompt'] if personality else ''

            reply = self._generate_response(
                content, history, system_prompt,
                provider, model,
                temperature=settings.get('temperature', 0.7),
                max_tokens=settings.get('max_tokens', 2000)
            )

            reply_tokens = len(reply)
            user_tokens = len(content)

            cursor.execute(
                '''INSERT INTO ai_chat_messages 
                   (conversation_id, user_id, role, content, tokens, model)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (conversation_id, user_id, 'assistant', reply, reply_tokens, model)
            )

            cursor.execute(
                '''UPDATE ai_chat_conversations 
                   SET updated_at = ?, message_count = message_count + 2
                   WHERE id = ?''',
                (datetime.now().isoformat(), conversation_id)
            )

            first_message = conv['message_count'] == 0
            if first_message and content:
                title = content[:20] + ('...' if len(content) > 20 else '')
                cursor.execute(
                    'UPDATE ai_chat_conversations SET title = ? WHERE id = ?',
                    (title, conversation_id)
                )

            conn.commit()

            return {
                'role': 'assistant',
                'content': reply,
                'tokens': reply_tokens,
                'model': model,
                'created_at': datetime.now().isoformat()
            }

    def _build_history(self, cursor, conversation_id: int, window: int) -> List[Dict]:
        """构建对话历史"""
        cursor.execute(
            '''SELECT role, content FROM ai_chat_messages 
               WHERE conversation_id = ?
               ORDER BY created_at DESC LIMIT ?''',
            (conversation_id, window)
        )
        rows = cursor.fetchall()
        return [{'role': row['role'], 'content': row['content']} for row in reversed(rows)]

    def _get_personality_by_id(self, cursor, personality_id: int) -> Optional[Dict]:
        """获取人格信息"""
        if not personality_id:
            return None
        cursor.execute('SELECT * FROM ai_chat_personalities WHERE id = ?', (personality_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def _generate_response(self, user_message: str, history: List[Dict],
                           system_prompt: str, provider: str, model: str,
                           temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """生成AI回复"""
        if provider == 'ollama' and self.ollama_available:
            try:
                return self._ollama_generate(user_message, history, system_prompt, model, temperature, max_tokens)
            except Exception as e:
                logger.warning(f"Ollama调用失败，回退到模拟模式: {e}")

        return self._mock_generate(user_message, history, system_prompt)

    def _ollama_generate(self, user_message: str, history: List[Dict],
                         system_prompt: str, model: str,
                         temperature: float, max_tokens: int) -> str:
        """使用Ollama生成回复"""
        import requests

        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.extend(history)
        messages.append({'role': 'user', 'content': user_message})

        resp = requests.post(
            'http://localhost:11434/api/chat',
            json={
                'model': model,
                'messages': messages,
                'stream': False,
                'options': {
                    'temperature': temperature,
                    'num_predict': max_tokens
                }
            },
            timeout=60
        )

        if resp.status_code == 200:
            data = resp.json()
            return data.get('message', {}).get('content', '抱歉，我无法生成回复。')
        else:
            raise Exception(f"Ollama API错误: {resp.status_code}")

    def _mock_generate(self, user_message: str, history: List[Dict],
                       system_prompt: str) -> str:
        """模拟生成回复（用于测试和无AI环境）"""
        msg = user_message.strip()

        if not msg:
            return "你好！有什么我可以帮助你的吗？"

        greetings = ['你好', '您好', 'hi', 'hello', '嗨', '在吗']
        if any(g.lower() in msg.lower() for g in greetings):
            return "你好！👋 我是你的AI助手，很高兴见到你！有什么我可以帮助你的吗？"

        thanks = ['谢谢', '感谢', 'thanks', 'thank']
        if any(t.lower() in msg.lower() for t in thanks):
            return "不客气！😊 如果还有其他问题，随时问我。"

        questions = ['什么是', '如何', '怎么', '为什么', '怎样', '可以']
        if any(q in msg for q in questions):
            return (
                f"关于「{msg}」，这是一个很好的问题！\n\n"
                f"根据我的理解，我来为你解释一下：\n"
                f"1. 首先，这涉及到多个方面的知识\n"
                f"2. 核心概念需要从基础开始理解\n"
                f"3. 实践是巩固知识的最好方式\n\n"
                f"💡 建议：你可以先从基础概念入手，然后逐步深入。"
                f"如果有具体的问题，我可以更详细地为你解答。"
            )

        if len(msg) < 5:
            return f"我收到了你的消息：「{msg}」。能告诉我更多细节吗？这样我可以更好地帮助你。"

        return (
            f"我已经收到你的消息了。关于你提到的内容，我的建议是：\n\n"
            f"📌 核心要点：\n"
            f"   • 仔细分析问题的各个方面\n"
            f"   • 从不同角度思考解决方案\n"
            f"   • 逐步实施并验证效果\n\n"
            f"如果你需要更具体的帮助，请告诉我更多细节，我会尽力为你提供支持！💪"
        )

    def get_user_settings(self, user_id: int) -> Dict:
        """获取用户设置"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM ai_chat_settings WHERE user_id = ?',
                (user_id,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)

            cursor.execute(
                '''INSERT INTO ai_chat_settings (user_id, provider, model)
                   VALUES (?, 'mock', 'default')''',
                (user_id,)
            )
            conn.commit()
            return {
                'user_id': user_id,
                'provider': 'mock',
                'model': 'default',
                'temperature': 0.7,
                'max_tokens': 2000,
                'top_p': 0.9,
                'context_window': 10
            }

    def update_user_settings(self, user_id: int, settings: Dict) -> Dict:
        """更新用户设置"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            fields = []
            values = []
            for key in ['provider', 'model', 'temperature', 'max_tokens', 'top_p', 'context_window']:
                if key in settings:
                    fields.append(f'{key} = ?')
                    values.append(settings[key])

            if fields:
                values.extend([datetime.now().isoformat(), user_id])
                cursor.execute(
                    f'''UPDATE ai_chat_settings SET {', '.join(fields)}, updated_at = ?
                       WHERE user_id = ?''',
                    values
                )
                conn.commit()

            return self.get_user_settings(user_id)

    def delete_conversation(self, conversation_id: int, user_id: int) -> bool:
        """删除对话"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE ai_chat_conversations SET is_active = 0 WHERE id = ? AND user_id = ?',
                (conversation_id, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def rename_conversation(self, conversation_id: int, user_id: int, title: str) -> bool:
        """重命名对话"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''UPDATE ai_chat_conversations SET title = ?, updated_at = ?
                   WHERE id = ? AND user_id = ?''',
                (title, datetime.now().isoformat(), conversation_id, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_available_models(self, provider: str = None) -> List[Dict]:
        """获取可用模型列表"""
        models = []

        models.append({
            'provider': 'mock',
            'name': 'default',
            'display_name': '模拟模式',
            'description': '本地模拟AI，用于测试和演示',
            'available': True
        })

        if self.ollama_available:
            for m in self.ollama_models:
                models.append({
                    'provider': 'ollama',
                    'name': m.get('name', 'unknown'),
                    'display_name': m.get('name', 'unknown'),
                    'description': f"Ollama本地模型 - 参数大小: {m.get('size', '未知')}",
                    'available': True
                })

        if provider:
            models = [m for m in models if m['provider'] == provider]

        return models

    def get_stats(self, user_id: int) -> Dict:
        """获取用户AI对话统计"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                'SELECT COUNT(*) as count FROM ai_chat_conversations WHERE user_id = ? AND is_active = 1',
                (user_id,)
            )
            conv_count = cursor.fetchone()['count']

            cursor.execute(
                'SELECT COUNT(*) as count FROM ai_chat_messages WHERE user_id = ? AND role = ?',
                (user_id, 'user')
            )
            msg_count = cursor.fetchone()['count']

            cursor.execute(
                'SELECT COALESCE(SUM(tokens), 0) as total FROM ai_chat_messages WHERE user_id = ?',
                (user_id,)
            )
            total_tokens = cursor.fetchone()['total']

        return {
            'conversations': conv_count,
            'messages': msg_count,
            'total_tokens': total_tokens,
            'provider_available': {
                'mock': True,
                'ollama': self.ollama_available
            }
        }
