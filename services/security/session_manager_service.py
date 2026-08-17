#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS会话管理服务
提供分布式会话和Token管理功能
"""

import os
import sys
import json
import time
import hashlib
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple

logger = print


class Session:
    """会话"""

    def __init__(self, session_id: str, user_id: str,
                 data: Dict[str, Any] = None,
                 expires_at: float = None, ip_address: str = '',
                 user_agent: str = '', device_id: str = ''):
        self.session_id = session_id
        self.user_id = user_id
        self.data = data or {}
        self.created_at = time.time()
        self.expires_at = expires_at or (time.time() + 86400)
        self.last_activity = time.time()
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.device_id = device_id
        self.is_active = True

    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    def touch(self):
        """更新活动时间"""
        self.last_activity = time.time()

    def extend(self, seconds: int = 3600):
        """延长会话"""
        self.expires_at = time.time() + seconds

    def to_dict(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'created_at': self.created_at,
            'expires_at': self.expires_at,
            'last_activity': self.last_activity,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'device_id': self.device_id,
            'is_active': self.is_active,
            'is_expired': self.is_expired()
        }


class Token:
    """Token"""

    def __init__(self, token_id: str, token_type: str, user_id: str,
                 value: str, expires_at: float = None,
                 scope: List[str] = None, client_id: str = ''):
        self.token_id = token_id
        self.token_type = token_type  # access, refresh, api
        self.user_id = user_id
        self.value = value
        self.created_at = time.time()
        self.expires_at = expires_at or (time.time() + 3600)
        self.scope = scope or []
        self.client_id = client_id
        self.is_revoked = False
        self.last_used = None

    def is_valid(self) -> bool:
        return not self.is_revoked and time.time() <= self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            'token_id': self.token_id,
            'token_type': self.token_type,
            'user_id': self.user_id,
            'created_at': self.created_at,
            'expires_at': self.expires_at,
            'scope': self.scope,
            'client_id': self.client_id,
            'is_revoked': self.is_revoked,
            'is_valid': self.is_valid(),
            'last_used': self.last_used
        }


class SessionManagerService:
    """会话管理服务"""

    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.tokens: Dict[str, Token] = {}
        self.is_running = False
        self.cleanup_thread = None
        self.lock = threading.Lock()

        self.session_timeout = 86400  # 24小时
        self.refresh_token_timeout = 604800  # 7天
        self.access_token_timeout = 3600  # 1小时
        self.api_token_timeout = 2592000  # 30天

        self._init_database()

    def _init_database(self):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL UNIQUE,
                    user_id TEXT NOT NULL,
                    data TEXT,
                    created_at REAL,
                    expires_at REAL,
                    last_activity REAL,
                    ip_address TEXT,
                    user_agent TEXT,
                    device_id TEXT,
                    is_active INTEGER DEFAULT 1
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token_id TEXT NOT NULL UNIQUE,
                    token_type TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    token_value TEXT NOT NULL,
                    created_at REAL,
                    expires_at REAL,
                    scope TEXT,
                    client_id TEXT,
                    is_revoked INTEGER DEFAULT 0,
                    last_used REAL
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS session_activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    user_id TEXT,
                    action TEXT NOT NULL,
                    ip_address TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sessions_id ON sessions(session_id)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_tokens_id ON tokens(token_id)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_tokens_user ON tokens(user_id)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_tokens_value ON tokens(token_value)
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[会话] 初始化数据库失败: {e}")

    def _generate_session_id(self) -> str:
        import uuid
        return uuid.uuid4().hex

    def _generate_token_id(self) -> str:
        import uuid
        return uuid.uuid4().hex

    def _generate_token_value(self, user_id: str, token_type: str) -> str:
        """生成Token值"""
        data = f"{user_id}:{token_type}:{time.time()}:{os.urandom(16).hex()}"
        return hashlib.sha256(data.encode()).hexdigest()

    def create_session(self, user_id: str, ip_address: str = '',
                       user_agent: str = '', device_id: str = '',
                       data: Dict[str, Any] = None,
                       timeout: int = None) -> str:
        """创建会话"""
        session_id = self._generate_session_id()
        timeout = timeout or self.session_timeout
        expires_at = time.time() + timeout

        session = Session(
            session_id=session_id,
            user_id=user_id,
            data=data or {},
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            device_id=device_id
        )

        with self.lock:
            self.sessions[session_id] = session

        self._save_session_to_db(session)
        self._log_session_activity(session_id, user_id, 'create', ip_address)

        logger(f"[会话] 创建会话: user={user_id}")
        return session_id

    def _save_session_to_db(self, session: Session):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO sessions
                (session_id, user_id, data, created_at, expires_at,
                 last_activity, ip_address, user_agent, device_id, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session.session_id, session.user_id,
                json.dumps(session.data),
                session.created_at, session.expires_at,
                session.last_activity, session.ip_address,
                session.user_agent, session.device_id,
                1 if session.is_active else 0
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[会话] 保存会话失败: {e}")

    def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        with self.lock:
            session = self.sessions.get(session_id)

            if not session:
                return None

            if session.is_expired() or not session.is_active:
                return None

            session.touch()
            return session

    def update_session_data(self, session_id: str, data: Dict[str, Any]) -> bool:
        """更新会话数据"""
        with self.lock:
            session = self.sessions.get(session_id)
            if not session or not session.is_active:
                return False

            session.data.update(data)
            session.touch()

        self._save_session_to_db(session)
        return True

    def destroy_session(self, session_id: str) -> bool:
        """销毁会话"""
        with self.lock:
            session = self.sessions.get(session_id)
            if not session:
                return False

            session.is_active = False
            del self.sessions[session_id]

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            cursor.execute('UPDATE sessions SET is_active = 0 WHERE session_id = ?', (session_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[会话] 销毁会话失败: {e}")

        self._log_session_activity(session_id, session.user_id, 'destroy')
        logger(f"[会话] 销毁会话: {session_id}")
        return True

    def destroy_user_sessions(self, user_id: str) -> int:
        """销毁用户所有会话"""
        count = 0

        with self.lock:
            to_remove = [
                sid for sid, session in self.sessions.items()
                if session.user_id == user_id
            ]

            for sid in to_remove:
                session = self.sessions[sid]
                session.is_active = False
                del self.sessions[sid]
                self._log_session_activity(sid, user_id, 'destroy_all')
                count += 1

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            cursor.execute('UPDATE sessions SET is_active = 0 WHERE user_id = ?', (user_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[会话] 批量销毁会话失败: {e}")

        logger(f"[会话] 销毁用户 {user_id} 的 {count} 个会话")
        return count

    def get_user_sessions(self, user_id: str) -> List[Session]:
        """获取用户所有活跃会话"""
        with self.lock:
            return [
                s for s in self.sessions.values()
                if s.user_id == user_id and s.is_active and not s.is_expired()
            ]

    def create_token(self, user_id: str, token_type: str = 'access',
                     scope: List[str] = None, client_id: str = '',
                     timeout: int = None) -> Tuple[str, str]:
        """创建Token"""
        token_id = self._generate_token_id()
        token_value = self._generate_token_value(user_id, token_type)

        if timeout is None:
            if token_type == 'access':
                timeout = self.access_token_timeout
            elif token_type == 'refresh':
                timeout = self.refresh_token_timeout
            elif token_type == 'api':
                timeout = self.api_token_timeout
            else:
                timeout = self.access_token_timeout

        expires_at = time.time() + timeout

        token = Token(
            token_id=token_id,
            token_type=token_type,
            user_id=user_id,
            value=token_value,
            expires_at=expires_at,
            scope=scope or [],
            client_id=client_id
        )

        with self.lock:
            self.tokens[token_value] = token

        self._save_token_to_db(token)
        logger(f"[会话] 创建Token: user={user_id}, type={token_type}")

        return token_id, token_value

    def _save_token_to_db(self, token: Token):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO tokens
                (token_id, token_type, user_id, token_value, created_at,
                 expires_at, scope, client_id, is_revoked, last_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                token.token_id, token.token_type, token.user_id,
                token.value, token.created_at, token.expires_at,
                json.dumps(token.scope), token.client_id,
                1 if token.is_revoked else 0, token.last_used
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[会话] 保存Token失败: {e}")

    def validate_token(self, token_value: str) -> Optional[Token]:
        """验证Token"""
        with self.lock:
            token = self.tokens.get(token_value)

            if not token:
                return None

            if not token.is_valid():
                return None

            token.last_used = time.time()
            return token

    def revoke_token(self, token_value: str) -> bool:
        """撤销Token"""
        with self.lock:
            token = self.tokens.get(token_value)
            if not token:
                return False

            token.is_revoked = True

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()
            cursor.execute('UPDATE tokens SET is_revoked = 1 WHERE token_value = ?', (token_value,))
            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[会话] 撤销Token失败: {e}")

        logger(f"[会话] 撤销Token: {token.token_id}")
        return True

    def revoke_user_tokens(self, user_id: str, token_type: str = None) -> int:
        """撤销用户Token"""
        count = 0

        with self.lock:
            for token in self.tokens.values():
                if token.user_id == user_id:
                    if token_type and token.token_type != token_type:
                        continue
                    token.is_revoked = True
                    count += 1

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            if token_type:
                cursor.execute(
                    'UPDATE tokens SET is_revoked = 1 WHERE user_id = ? AND token_type = ?',
                    (user_id, token_type)
                )
            else:
                cursor.execute(
                    'UPDATE tokens SET is_revoked = 1 WHERE user_id = ?',
                    (user_id,)
                )

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[会话] 批量撤销Token失败: {e}")

        logger(f"[会话] 撤销用户 {user_id} 的 {count} 个Token")
        return count

    def refresh_token(self, refresh_token_value: str) -> Optional[Tuple[str, str]]:
        """刷新Token"""
        with self.lock:
            token = self.tokens.get(refresh_token_value)

            if not token or token.token_type != 'refresh' or not token.is_valid():
                return None

            token.is_revoked = True

        new_token_id, new_token_value = self.create_token(
            user_id=token.user_id,
            token_type='access',
            scope=token.scope,
            client_id=token.client_id
        )

        self._save_token_to_db(token)

        return new_token_id, new_token_value

    def _log_session_activity(self, session_id: str, user_id: str,
                              action: str, ip_address: str = ''):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO session_activity_logs
                (session_id, user_id, action, ip_address)
                VALUES (?, ?, ?, ?)
            ''', (session_id, user_id, action, ip_address))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[会话] 记录活动失败: {e}")

    def _cleanup_loop(self):
        """清理循环"""
        while self.is_running:
            try:
                time.sleep(300)

                now = time.time()

                with self.lock:
                    expired_sessions = [
                        sid for sid, s in self.sessions.items()
                        if s.is_expired() or not s.is_active
                    ]

                    for sid in expired_sessions:
                        del self.sessions[sid]

                    expired_tokens = [
                        tv for tv, t in self.tokens.items()
                        if not t.is_valid()
                    ]

                    for tv in expired_tokens:
                        del self.tokens[tv]

                if expired_sessions:
                    logger(f"[会话] 清理过期会话: {len(expired_sessions)} 个")
                if expired_tokens:
                    logger(f"[会话] 清理过期Token: {len(expired_tokens)} 个")

            except Exception as e:
                logger(f"[会话] 清理错误: {e}")

    def get_session_activity_logs(self, user_id: str = None,
                                  limit: int = 100) -> List[Dict[str, Any]]:
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            query = 'SELECT * FROM session_activity_logs WHERE 1=1'
            params = []

            if user_id:
                query += ' AND user_id = ?'
                params.append(user_id)

            query += ' ORDER BY created_at DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)

            columns = [desc[0] for desc in cursor.description]
            logs = [dict(zip(columns, row)) for row in cursor.fetchall()]

            conn.close()
            return logs
        except Exception as e:
            logger(f"[会话] 获取活动日志失败: {e}")
            return []

    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            return {
                'status': 'running' if self.is_running else 'stopped',
                'active_sessions': len(self.sessions),
                'active_tokens': sum(1 for t in self.tokens.values() if t.is_valid()),
                'revoked_tokens': sum(1 for t in self.tokens.values() if t.is_revoked),
                'session_timeout': self.session_timeout,
                'access_token_timeout': self.access_token_timeout,
                'refresh_token_timeout': self.refresh_token_timeout
            }

    def start(self):
        if self.is_running:
            return

        self.is_running = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        logger(f"[会话] 会话管理服务已启动")

    def stop(self):
        self.is_running = False
        if self.cleanup_thread:
            self.cleanup_thread.join()
        logger(f"[会话] 会话管理服务已停止")


session_manager_service = SessionManagerService()
