#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Session Manager - 会话管理系统
支持退出登出、暂时锁定、超时登出、非法操作强行登出
增强：登录状态保持、记住我、Refresh Token
"""

from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
import uuid
import hashlib
import json
from enum import Enum

class SessionStatus(Enum):
    """会话状态"""
    ACTIVE = "active"
    LOCKED = "locked"
    TIMEOUT = "timeout"
    LOGGED_OUT = "logged_out"
    FORCED_LOGOUT = "forced_logout"
    INVALID = "invalid"

class SessionEvent(Enum):
    """会话事件类型"""
    LOGIN = "login"
    LOGOUT = "logout"
    LOCK = "lock"
    UNLOCK = "unlock"
    TIMEOUT = "timeout"
    FORCED_LOGOUT = "forced_logout"
    INVALID_TOKEN = "invalid_token"
    SESSION_EXPIRED = "session_expired"
    CONCURRENT_LOGIN = "concurrent_login"
    REFRESH_TOKEN = "refresh_token"
    AUTO_LOGIN = "auto_login"

class RememberMeToken:
    """记住我令牌"""
    
    def __init__(self, user_id: str):
        self.token_id = str(uuid.uuid4())
        self.user_id = user_id
        self.token_hash = self._generate_token()
        self.created_at = datetime.now()
        self.expires_at = datetime.now() + timedelta(days=30)
        self.last_used_at = None
        self.is_revoked = False
    
    def _generate_token(self) -> str:
        """生成令牌哈希"""
        raw_token = f"{uuid.uuid4().hex}{uuid.uuid4().hex}"
        return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
    
    def is_valid(self) -> bool:
        """检查令牌是否有效"""
        return not self.is_revoked and self.expires_at > datetime.now()
    
    def refresh(self):
        """刷新令牌"""
        self.token_hash = self._generate_token()
        self.expires_at = datetime.now() + timedelta(days=30)
        self.last_used_at = datetime.now()
    
    def revoke(self):
        """撤销令牌"""
        self.is_revoked = True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "token_id": self.token_id,
            "user_id": self.user_id,
            "token_hash": self.token_hash,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "is_revoked": self.is_revoked
        }

class Session:
    """会话对象"""
    
    def __init__(self, user_id: str, username: str = "", remember_me: bool = False):
        self.session_id = str(uuid.uuid4())
        self.user_id = user_id
        self.username = username
        self.status = SessionStatus.ACTIVE
        self.created_at = datetime.now()
        self.last_activity_at = datetime.now()
        self.expires_at = datetime.now() + timedelta(hours=2)
        self.lock_time = None
        self.lock_reason = ""
        self.ip_address = ""
        self.user_agent = ""
        self.events: List[Dict[str, Any]] = []
        self.permissions: Set[str] = set()
        self.remember_me = remember_me
        self.remember_me_token = None
        
        if remember_me:
            self.remember_me_token = RememberMeToken(user_id)
    
    def is_active(self) -> bool:
        """检查会话是否活跃"""
        return self.status == SessionStatus.ACTIVE and self.expires_at > datetime.now()
    
    def is_locked(self) -> bool:
        """检查会话是否锁定"""
        return self.status == SessionStatus.LOCKED
    
    def is_expired(self) -> bool:
        """检查会话是否过期"""
        return self.expires_at <= datetime.now()
    
    def update_activity(self):
        """更新活动时间"""
        self.last_activity_at = datetime.now()
        self.expires_at = datetime.now() + timedelta(hours=2)
    
    def lock(self, reason: str = "暂时锁定"):
        """锁定会话"""
        self.status = SessionStatus.LOCKED
        self.lock_time = datetime.now()
        self.lock_reason = reason
        self.add_event(SessionEvent.LOCK, reason)
    
    def unlock(self):
        """解锁会话"""
        self.status = SessionStatus.ACTIVE
        self.lock_time = None
        self.lock_reason = ""
        self.add_event(SessionEvent.UNLOCK, "解锁会话")
    
    def logout(self):
        """正常退出"""
        self.status = SessionStatus.LOGGED_OUT
        self.add_event(SessionEvent.LOGOUT, "正常退出")
    
    def force_logout(self, reason: str = "非法操作"):
        """强行退出"""
        self.status = SessionStatus.FORCED_LOGOUT
        self.add_event(SessionEvent.FORCED_LOGOUT, reason)
    
    def timeout(self):
        """超时退出"""
        self.status = SessionStatus.TIMEOUT
        self.add_event(SessionEvent.TIMEOUT, "会话超时")
    
    def invalidate(self):
        """使会话无效"""
        self.status = SessionStatus.INVALID
        self.add_event(SessionEvent.INVALID_TOKEN, "会话无效")
    
    def add_event(self, event_type: SessionEvent, description: str = ""):
        """添加会话事件"""
        self.events.append({
            "event_type": event_type.value,
            "timestamp": datetime.now().isoformat(),
            "description": description
        })
    
    def extend_session(self, days: int = 30):
        """延长会话有效期（记住我功能）"""
        self.expires_at = datetime.now() + timedelta(days=days)
        if self.remember_me_token:
            self.remember_me_token.expires_at = datetime.now() + timedelta(days=days)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "username": self.username,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_activity_at": self.last_activity_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "lock_time": self.lock_time.isoformat() if self.lock_time else None,
            "lock_reason": self.lock_reason,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "events": self.events,
            "permissions": list(self.permissions),
            "remember_me": self.remember_me,
            "remember_me_token": self.remember_me_token.token_id if self.remember_me_token else None
        }


class SessionLog:
    """会话日志"""
    
    def __init__(self):
        self.logs: List[Dict[str, Any]] = []
    
    def log(self, session: Session, event_type: SessionEvent, description: str = "", details: Dict[str, Any] = None):
        """记录日志"""
        log_entry = {
            "log_id": str(uuid.uuid4()),
            "session_id": session.session_id,
            "user_id": session.user_id,
            "username": session.username,
            "event_type": event_type.value,
            "description": description,
            "details": details or {},
            "timestamp": datetime.now().isoformat(),
            "ip_address": session.ip_address,
            "user_agent": session.user_agent,
            "session_status": session.status.value
        }
        self.logs.append(log_entry)
        self._save_to_database(log_entry)
    
    def _save_to_database(self, log_entry: Dict[str, Any]):
        """保存到数据库"""
        try:
            from core.database import db
            db.execute("""
                INSERT INTO session_logs (
                    log_id, session_id, user_id, username, event_type, 
                    description, details, timestamp, ip_address, user_agent, session_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log_entry["log_id"],
                log_entry["session_id"],
                log_entry["user_id"],
                log_entry["username"],
                log_entry["event_type"],
                log_entry["description"],
                json.dumps(log_entry["details"]),
                log_entry["timestamp"],
                log_entry["ip_address"],
                log_entry["user_agent"],
                log_entry["session_status"]
            ))
        except Exception as e:
            from core.logging import logger
            logger.error(f"Failed to save session log to database: {e}")
    
    def get_logs_by_user(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取用户的会话日志"""
        try:
            from core.database import db
            rows = db.query("""
                SELECT * FROM session_logs 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (user_id, limit))
            return [dict(zip(["log_id", "session_id", "user_id", "username", "event_type", 
                            "description", "details", "timestamp", "ip_address", 
                            "user_agent", "session_status"], row)) for row in rows]
        except Exception as e:
            from core.logging import logger
            logger.error(f"Failed to get session logs: {e}")
            return self.logs[-limit:]
    
    def get_logs_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会话的日志"""
        return [log for log in self.logs if log["session_id"] == session_id]


class SessionManager:
    """会话管理器"""
    
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.user_sessions: Dict[str, List[str]] = {}
        self.remember_me_tokens: Dict[str, RememberMeToken] = {}
        self.log = SessionLog()
        self.max_sessions_per_user = 5
        self.session_timeout = timedelta(hours=2)
        self.lock_duration = timedelta(minutes=30)
        self.remember_me_duration = timedelta(days=30)
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表"""
        try:
            from core.database import db
            db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    username TEXT,
                    status TEXT,
                    created_at TEXT,
                    last_activity_at TEXT,
                    expires_at TEXT,
                    lock_time TEXT,
                    lock_reason TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    permissions TEXT,
                    remember_me INTEGER,
                    remember_me_token_id TEXT
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS session_logs (
                    log_id TEXT PRIMARY KEY,
                    session_id TEXT,
                    user_id TEXT,
                    username TEXT,
                    event_type TEXT,
                    description TEXT,
                    details TEXT,
                    timestamp TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    session_status TEXT
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS remember_me_tokens (
                    token_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    token_hash TEXT,
                    created_at TEXT,
                    expires_at TEXT,
                    last_used_at TEXT,
                    is_revoked INTEGER
                )
            """)
        except Exception as e:
            from core.logging import logger
            logger.error(f"Failed to initialize session tables: {e}")
    
    def create_session(self, user_id: str, username: str = "", remember_me: bool = False,
                      ip_address: str = "", user_agent: str = "") -> Session:
        """创建新会话"""
        self._cleanup_expired_sessions()
        
        self._limit_user_sessions(user_id)
        
        session = Session(user_id, username, remember_me)
        session.ip_address = ip_address
        session.user_agent = user_agent
        
        self.sessions[session.session_id] = session
        
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = []
        self.user_sessions[user_id].append(session.session_id)
        
        if remember_me and session.remember_me_token:
            self.remember_me_tokens[session.remember_me_token.token_id] = session.remember_me_token
            self._save_remember_me_token(session.remember_me_token)
        
        self.log.log(session, SessionEvent.LOGIN, "用户登录", {"remember_me": remember_me})
        
        self._save_session(session)
        
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        session = self.sessions.get(session_id)
        if session and session.is_expired():
            session.timeout()
            self.log.log(session, SessionEvent.SESSION_EXPIRED, "会话已过期")
            return None
        return session
    
    def validate_session(self, session_id: str) -> Tuple[bool, str]:
        """验证会话"""
        session = self.get_session(session_id)
        
        if not session:
            return False, "会话不存在"
        
        if session.status == SessionStatus.INVALID:
            return False, "会话已失效"
        
        if session.status == SessionStatus.LOCKED:
            return False, "会话已锁定"
        
        if session.status == SessionStatus.TIMEOUT:
            return False, "会话已超时"
        
        if session.status == SessionStatus.LOGGED_OUT:
            return False, "用户已退出"
        
        if session.status == SessionStatus.FORCED_LOGOUT:
            return False, "用户被强行退出"
        
        if session.is_expired():
            session.timeout()
            self.log.log(session, SessionEvent.TIMEOUT, "会话超时")
            return False, "会话已过期"
        
        session.update_activity()
        self._save_session(session)
        
        return True, "会话有效"
    
    def update_session_activity(self, session_id: str):
        """更新会话活动"""
        session = self.sessions.get(session_id)
        if session:
            session.update_activity()
            self._save_session(session)
    
    def lock_session(self, session_id: str, reason: str = "暂时锁定"):
        """锁定会话"""
        session = self.sessions.get(session_id)
        if session:
            session.lock(reason)
            self.log.log(session, SessionEvent.LOCK, reason)
            self._save_session(session)
    
    def unlock_session(self, session_id: str):
        """解锁会话"""
        session = self.sessions.get(session_id)
        if session:
            session.unlock()
            self.log.log(session, SessionEvent.UNLOCK, "解锁会话")
            self._save_session(session)
    
    def logout(self, session_id: str, revoke_remember_me: bool = False):
        """正常退出"""
        session = self.sessions.get(session_id)
        if session:
            session.logout()
            self.log.log(session, SessionEvent.LOGOUT, "正常退出")
            
            if revoke_remember_me and session.remember_me_token:
                self.revoke_remember_me_token(session.remember_me_token.token_id)
            
            self._cleanup_session(session_id)
    
    def force_logout(self, session_id: str, reason: str = "非法操作"):
        """强行退出"""
        session = self.sessions.get(session_id)
        if session:
            session.force_logout(reason)
            self.log.log(session, SessionEvent.FORCED_LOGOUT, reason)
            self._cleanup_session(session_id)
    
    def logout_all(self, user_id: str, revoke_remember_me: bool = False):
        """退出用户所有会话"""
        session_ids = self.user_sessions.get(user_id, [])
        for session_id in session_ids.copy():
            self.logout(session_id, revoke_remember_me)
        
        if revoke_remember_me:
            self.revoke_all_remember_me_tokens(user_id)
    
    def force_logout_all(self, user_id: str, reason: str = "强制退出所有会话"):
        """强行退出用户所有会话"""
        session_ids = self.user_sessions.get(user_id, [])
        for session_id in session_ids.copy():
            self.force_logout(session_id, reason)
    
    def _limit_user_sessions(self, user_id: str):
        """限制用户会话数量"""
        sessions = self.user_sessions.get(user_id, [])
        if len(sessions) >= self.max_sessions_per_user:
            oldest_session_id = sessions[0]
            session = self.sessions.get(oldest_session_id)
            if session:
                session.force_logout("并发登录限制")
                self.log.log(session, SessionEvent.CONCURRENT_LOGIN, "超过最大会话数")
                self._cleanup_session(oldest_session_id)
    
    def _cleanup_session(self, session_id: str):
        """清理会话"""
        session = self.sessions.get(session_id)
        if session:
            if session.user_id in self.user_sessions:
                self.user_sessions[session.user_id].remove(session_id)
            del self.sessions[session_id]
    
    def _cleanup_expired_sessions(self):
        """清理过期会话"""
        expired_ids = []
        for session_id, session in self.sessions.items():
            if session.is_expired():
                expired_ids.append(session_id)
        
        for session_id in expired_ids:
            session = self.sessions.get(session_id)
            if session:
                session.timeout()
                self.log.log(session, SessionEvent.TIMEOUT, "会话超时自动清理")
                self._cleanup_session(session_id)
        
        self._cleanup_expired_remember_me_tokens()
    
    def _cleanup_expired_remember_me_tokens(self):
        """清理过期的记住我令牌"""
        expired_tokens = []
        for token_id, token in self.remember_me_tokens.items():
            if not token.is_valid():
                expired_tokens.append(token_id)
        
        for token_id in expired_tokens:
            del self.remember_me_tokens[token_id]
    
    def _save_session(self, session: Session):
        """保存会话到数据库"""
        try:
            from core.database import db
            permissions = json.dumps(list(session.permissions))
            
            db.execute("""
                INSERT OR REPLACE INTO sessions (
                    session_id, user_id, username, status, created_at, 
                    last_activity_at, expires_at, lock_time, lock_reason, 
                    ip_address, user_agent, permissions, remember_me, remember_me_token_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session.session_id,
                session.user_id,
                session.username,
                session.status.value,
                session.created_at.isoformat(),
                session.last_activity_at.isoformat(),
                session.expires_at.isoformat(),
                session.lock_time.isoformat() if session.lock_time else None,
                session.lock_reason,
                session.ip_address,
                session.user_agent,
                permissions,
                1 if session.remember_me else 0,
                session.remember_me_token.token_id if session.remember_me_token else None
            ))
        except Exception as e:
            from core.logging import logger
            logger.error(f"Failed to save session to database: {e}")
    
    def _save_remember_me_token(self, token: RememberMeToken):
        """保存记住我令牌到数据库"""
        try:
            from core.database import db
            db.execute("""
                INSERT OR REPLACE INTO remember_me_tokens (
                    token_id, user_id, token_hash, created_at, 
                    expires_at, last_used_at, is_revoked
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                token.token_id,
                token.user_id,
                token.token_hash,
                token.created_at.isoformat(),
                token.expires_at.isoformat(),
                token.last_used_at.isoformat() if token.last_used_at else None,
                1 if token.is_revoked else 0
            ))
        except Exception as e:
            from core.logging import logger
            logger.error(f"Failed to save remember me token: {e}")
    
    def load_sessions_from_database(self):
        """从数据库加载会话"""
        try:
            from core.database import db
            rows = db.query("SELECT * FROM sessions")
            
            for row in rows:
                session = Session(row[1], row[2], row[12] == 1)
                session.session_id = row[0]
                session.status = SessionStatus(row[3])
                session.created_at = datetime.fromisoformat(row[4])
                session.last_activity_at = datetime.fromisoformat(row[5])
                session.expires_at = datetime.fromisoformat(row[6])
                session.lock_time = datetime.fromisoformat(row[7]) if row[7] else None
                session.lock_reason = row[8]
                session.ip_address = row[9]
                session.user_agent = row[10]
                session.permissions = set(json.loads(row[11]))
                
                if session.is_active():
                    self.sessions[session.session_id] = session
                    if session.user_id not in self.user_sessions:
                        self.user_sessions[session.user_id] = []
                    self.user_sessions[session.user_id].append(session.session_id)
            
            self.load_remember_me_tokens_from_database()
        except Exception as e:
            from core.logging import logger
            logger.error(f"Failed to load sessions from database: {e}")
    
    def load_remember_me_tokens_from_database(self):
        """从数据库加载记住我令牌"""
        try:
            from core.database import db
            rows = db.query("SELECT * FROM remember_me_tokens")
            
            for row in rows:
                token = RememberMeToken(row[1])
                token.token_id = row[0]
                token.token_hash = row[2]
                token.created_at = datetime.fromisoformat(row[3])
                token.expires_at = datetime.fromisoformat(row[4])
                token.last_used_at = datetime.fromisoformat(row[5]) if row[5] else None
                token.is_revoked = row[6] == 1
                
                if token.is_valid():
                    self.remember_me_tokens[token.token_id] = token
        except Exception as e:
            from core.logging import logger
            logger.error(f"Failed to load remember me tokens: {e}")
    
    def get_user_sessions(self, user_id: str) -> List[Session]:
        """获取用户的所有会话"""
        session_ids = self.user_sessions.get(user_id, [])
        return [self.sessions.get(sid) for sid in session_ids if self.sessions.get(sid)]
    
    def get_active_sessions_count(self) -> int:
        """获取活跃会话数量"""
        self._cleanup_expired_sessions()
        return len(self.sessions)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取会话统计信息"""
        self._cleanup_expired_sessions()
        
        status_counts = {}
        for session in self.sessions.values():
            status = session.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_sessions": len(self.sessions),
            "status_counts": status_counts,
            "users_with_sessions": len(self.user_sessions),
            "max_sessions_per_user": self.max_sessions_per_user,
            "remember_me_tokens_count": len(self.remember_me_tokens)
        }
    
    def auto_login(self, token_id: str) -> Optional[Session]:
        """通过记住我令牌自动登录"""
        token = self.remember_me_tokens.get(token_id)
        
        if not token or not token.is_valid():
            return None
        
        token.last_used_at = datetime.now()
        self._save_remember_me_token(token)
        
        session = self.create_session(token.user_id, remember_me=True)
        session.add_event(SessionEvent.AUTO_LOGIN, "通过记住我令牌自动登录")
        self.log.log(session, SessionEvent.AUTO_LOGIN, "自动登录成功")
        
        return session
    
    def refresh_remember_me_token(self, token_id: str) -> Optional[str]:
        """刷新记住我令牌"""
        token = self.remember_me_tokens.get(token_id)
        
        if not token or not token.is_valid():
            return None
        
        old_token_id = token.token_id
        token.refresh()
        self._save_remember_me_token(token)
        
        del self.remember_me_tokens[old_token_id]
        self.remember_me_tokens[token.token_id] = token
        
        return token.token_id
    
    def revoke_remember_me_token(self, token_id: str):
        """撤销记住我令牌"""
        token = self.remember_me_tokens.get(token_id)
        if token:
            token.revoke()
            self._save_remember_me_token(token)
            del self.remember_me_tokens[token_id]
    
    def revoke_all_remember_me_tokens(self, user_id: str):
        """撤销用户所有记住我令牌"""
        tokens_to_revoke = [
            token_id for token_id, token in self.remember_me_tokens.items()
            if token.user_id == user_id
        ]
        
        for token_id in tokens_to_revoke:
            self.revoke_remember_me_token(token_id)
    
    def get_remember_me_tokens_by_user(self, user_id: str) -> List[RememberMeToken]:
        """获取用户的所有记住我令牌"""
        return [
            token for token in self.remember_me_tokens.values()
            if token.user_id == user_id and token.is_valid()
        ]


# 全局实例
session_manager = SessionManager()
