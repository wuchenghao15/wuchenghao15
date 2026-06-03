# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Session Manager for MTSCOS AI System
会话超时管理模块 - 增强版
"""

import sqlite3
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Generator
from contextlib import contextmanager
from flask import session, request, make_response, jsonify
import hashlib
import uuid
import json
import os

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """数据库连接上下文管理器"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def __enter__(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            return self.cursor, self.conn
        except sqlite3.Error as e:
            logger.error(f"数据库连接失败: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            try:
                if exc_type is None:
                    self.conn.commit()
                else:
                    self.conn.rollback()
            except sqlite3.Error as e:
                logger.error(f"数据库提交/回滚失败: {e}")
            finally:
                self.conn.close()


class SessionManager:
    """会话管理器 - 增强版"""

    def __init__(self, db_path: str, timeout_minutes: int = 30):
        self.db_path = db_path
        self.timeout_minutes = timeout_minutes
        self._init_db()

    @contextmanager
    def get_db_connection(self) -> Generator:
        """获取数据库连接的上下文管理器"""
        with DatabaseConnection(self.db_path) as (cursor, conn):
            yield cursor, conn

    def _init_db(self):
        """初始化数据库表"""
        with self.get_db_connection() as (cursor, conn):
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id INTEGER,
                    username TEXT,
                    role TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_access TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    user_agent TEXT,
                    data TEXT,
                    expires_at TIMESTAMP,
                    last_activity TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS login_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    ip_address TEXT NOT NULL,
                    success INTEGER DEFAULT 0,
                    attempt_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_agent TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_locks (
                    username TEXT PRIMARY KEY,
                    locked_until TIMESTAMP,
                    lock_reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS session_activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    activity_type TEXT NOT NULL,
                    activity_data TEXT,
                    ip_address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_login_attempts_username ON login_attempts(username)
            ''')

            logger.info("会话管理数据库表初始化完成")

    def create_session(self, user_id: int, username: str, role: str,
                       ip_address: str, user_agent: str) -> Optional[str]:
        """创建会话"""
        try:
            session_id = self._generate_session_id()
            expires_at = datetime.now() + timedelta(minutes=self.timeout_minutes)
            last_activity = datetime.now().isoformat()

            with self.get_db_connection() as (cursor, conn):
                cursor.execute('''
                    INSERT INTO sessions
                    (session_id, user_id, username, role, ip_address, user_agent, expires_at, last_activity)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (session_id, user_id, username, role, ip_address, user_agent, expires_at, last_activity))

                cursor.execute('''
                    INSERT INTO session_activities (session_id, activity_type, activity_data, ip_address)
                    VALUES (?, ?, ?, ?)
                ''', (session_id, 'session_created', f'user:{username}', ip_address))

            session['session_id'] = session_id
            session['user_id'] = user_id
            session['username'] = username
            session['role'] = role
            session['last_activity'] = last_activity
            session.permanent = True

            logger.info(f"会话创建成功: session_id={session_id[:16]}..., user={username}")
            return session_id

        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            return None

    def _generate_session_id(self) -> str:
        """生成唯一会话ID"""
        timestamp = str(time.time())
        random_str = str(uuid.uuid4())
        combined = f"{timestamp}{random_str}{uuid.uuid4()}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def validate_session(self, session_id: str) -> Optional[Dict]:
        """验证会话是否有效"""
        try:
            with self.get_db_connection() as (cursor, conn):
                cursor.execute('SELECT * FROM sessions WHERE session_id = ?', (session_id,))
                session_row = cursor.fetchone()

                if not session_row:
                    return None

                session_dict = dict(session_row)

                expires_at = session_dict.get('expires_at')
                if expires_at:
                    try:
                        if isinstance(expires_at, str):
                            expires_dt = datetime.fromisoformat(expires_at.replace(' ', 'T'))
                        else:
                            expires_dt = expires_at

                        if datetime.now() > expires_dt:
                            self._safe_invalidate_session(session_id, cursor)
                            logger.warning(f"会话已过期: session_id={session_id[:16]}...")
                            return None
                    except (ValueError, TypeError) as e:
                        logger.error(f"解析expires_at失败: {e}")
                        return None

                return session_dict

        except Exception as e:
            logger.error(f"验证会话失败: {e}")
            return None

    def _safe_invalidate_session(self, session_id: str, cursor):
        """安全地使会话失效(内部方法,不关闭连接)"""
        try:
            cursor.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
        except sqlite3.Error as e:
            logger.error(f"删除会话失败: {e}")

    def refresh_session(self, session_id: str) -> bool:
        """刷新会话(更新过期时间和最后活动时间)"""
        try:
            new_expires = datetime.now() + timedelta(minutes=self.timeout_minutes)
            last_activity = datetime.now().isoformat()

            with self.get_db_connection() as (cursor, conn):
                cursor.execute('''
                    UPDATE sessions
                    SET last_access = ?, expires_at = ?, last_activity = ?
                    WHERE session_id = ?
                ''', (datetime.now(), new_expires, last_activity, session_id))

                cursor.execute('''
                    INSERT INTO session_activities (session_id, activity_type, ip_address)
                    VALUES (?, ?, ?)
                ''', (session_id, 'session_refresh', request.remote_addr if request else None))

            session['last_activity'] = last_activity
            return True

        except Exception as e:
            logger.error(f"刷新会话失败: {e}")
            return False

    def invalidate_session(self, session_id: str) -> bool:
        """使会话失效"""
        try:
            with self.get_db_connection() as (cursor, conn):
                cursor.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
                cursor.execute('DELETE FROM session_activities WHERE session_id = ?', (session_id,))

            session.clear()
            logger.info(f"会话已失效: session_id={session_id[:16]}...")
            return True

        except Exception as e:
            logger.error(f"使会话失效失败: {e}")
            return False

    def invalidate_user_sessions(self, user_id: int, except_session_id: str = None) -> int:
        """使用户所有会话失效(可选保留当前会话)"""
        try:
            with self.get_db_connection() as (cursor, conn):
                if except_session_id:
                    cursor.execute('''
                        DELETE FROM sessions
                        WHERE user_id = ? AND session_id != ?
                    ''', (user_id, except_session_id))
                else:
                    cursor.execute('DELETE FROM sessions WHERE user_id = ?', (user_id,))

                affected = cursor.rowcount

            logger.info(f"用户 {user_id} 的 {affected} 个会话已失效")
            return affected

        except Exception as e:
            logger.error(f"使用户会话失效失败: {e}")
            return 0

    def record_login_attempt(self, username: str, ip_address: str, success: bool,
                             user_agent: str = None):
        """记录登录尝试"""
        try:
            with self.get_db_connection() as (cursor, conn):
                cursor.execute('''
                    INSERT INTO login_attempts (username, ip_address, success, user_agent)
                    VALUES (?, ?, ?, ?)
                ''', (username, ip_address, 1 if success else 0, user_agent))

        except Exception as e:
            logger.error(f"记录登录尝试失败: {e}")

    def check_login_attempts(self, username: str, ip_address: str = None,
                            max_attempts: int = 5, lock_minutes: int = 5) -> Dict[str, Any]:
        """检查登录尝试次数,返回详细状态"""
        try:
            with self.get_db_connection() as (cursor, conn):
                cursor.execute('SELECT locked_until, lock_reason FROM user_locks WHERE username = ?',
                             (username,))
                lock_result = cursor.fetchone()

                if lock_result:
                    locked_until = dict(lock_result).get('locked_until')
                    lock_reason = dict(lock_result).get('lock_reason')

                    if locked_until:
                        try:
                            if isinstance(locked_until, str):
                                locked_dt = datetime.fromisoformat(locked_until.replace(' ', 'T'))
                            else:
                                locked_dt = locked_until

                            if datetime.now() < locked_dt:
                                remaining_seconds = int((locked_dt - datetime.now()).total_seconds())
                                return {
                                    'allowed': False,
                                    'reason': 'locked',
                                    'message': f'账户已锁定,请{remaining_seconds}秒后重试',
                                    'locked_until': locked_until,
                                    'lock_reason': lock_reason,
                                    'remaining_seconds': remaining_seconds
                                }
                            else:
                                cursor.execute('DELETE FROM user_locks WHERE username = ?', (username,))
                        except (ValueError, TypeError) as e:
                            logger.error(f"解析locked_until失败: {e}")
                            cursor.execute('DELETE FROM user_locks WHERE username = ?', (username,))

                time_threshold = datetime.now() - timedelta(hours=1)
                cursor.execute('''
                    SELECT COUNT(*) FROM login_attempts
                    WHERE username = ? AND success = 0 AND attempt_time > ?
                ''', (username, time_threshold))

                fail_count = cursor.fetchone()[0]

                remaining_attempts = max(0, max_attempts - fail_count)

                if fail_count >= max_attempts:
                    locked_until = datetime.now() + timedelta(minutes=lock_minutes)
                    cursor.execute('''
                        INSERT OR REPLACE INTO user_locks (username, locked_until, lock_reason)
                        VALUES (?, ?, ?)
                    ''', (username, locked_until, f'登录失败{max_attempts}次'))

                    logger.warning(f"用户 {username} 因登录失败{max_attempts}次被锁定")

                    return {
                        'allowed': False,
                        'reason': 'max_attempts_exceeded',
                        'message': f'登录失败次数过多,账户已锁定{lock_minutes}分钟',
                        'locked_until': locked_until.isoformat(),
                        'fail_count': fail_count,
                        'remaining_attempts': 0
                    }

                return {
                    'allowed': True,
                    'reason': 'ok',
                    'message': f'还可以尝试{remaining_attempts}次',
                    'fail_count': fail_count,
                    'remaining_attempts': remaining_attempts
                }

        except Exception as e:
            logger.error(f"检查登录尝试失败: {e}")
            return {'allowed': True, 'reason': 'error', 'message': '检查登录状态时发生错误'}

    def unlock_user(self, username: str) -> bool:
        """解锁用户"""
        try:
            with self.get_db_connection() as (cursor, conn):
                cursor.execute('DELETE FROM user_locks WHERE username = ?', (username,))

            logger.info(f"用户 {username} 已解锁")
            return True

        except Exception as e:
            logger.error(f"解锁用户失败: {e}")
            return False

    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """获取会话信息"""
        return self.validate_session(session_id)

    def clean_expired_sessions(self) -> int:
        """清理过期会话"""
        try:
            with self.get_db_connection() as (cursor, conn):
                cursor.execute('DELETE FROM sessions WHERE expires_at < ?', (datetime.now(),))
                deleted_count = cursor.rowcount

            if deleted_count > 0:
                logger.info(f"已清理 {deleted_count} 个过期会话")

            return deleted_count

        except Exception as e:
            logger.error(f"清理过期会话失败: {e}")
            return 0

    def get_active_sessions(self, user_id: Optional[int] = None,
                           include_expired: bool = False) -> list:
        """获取活跃会话"""
        try:
            with self.get_db_connection() as (cursor, conn):
                if user_id:
                    if include_expired:
                        cursor.execute('''
                            SELECT * FROM sessions WHERE user_id = ?
                            ORDER BY last_access DESC
                        ''', (user_id,))
                    else:
                        cursor.execute('''
                            SELECT * FROM sessions WHERE user_id = ? AND expires_at > ?
                            ORDER BY last_access DESC
                        ''', (user_id, datetime.now()))
                else:
                    if include_expired:
                        cursor.execute('SELECT * FROM sessions ORDER BY last_access DESC')
                    else:
                        cursor.execute('SELECT * FROM sessions WHERE expires_at > ? ORDER BY last_access DESC',
                                     (datetime.now(),))

                sessions = [dict(row) for row in cursor.fetchall()]

            return sessions

        except Exception as e:
            logger.error(f"获取活跃会话失败: {e}")
            return []

    def get_session_statistics(self) -> Dict[str, Any]:
        """获取会话统计信息"""
        try:
            with self.get_db_connection() as (cursor, conn):
                cursor.execute('SELECT COUNT(*) FROM sessions')
                total_sessions = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM sessions WHERE expires_at > ?', (datetime.now(),))
                active_sessions = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(DISTINCT user_id) FROM sessions WHERE expires_at > ?',
                             (datetime.now(),))
                unique_users = cursor.fetchone()[0]

                cursor.execute('''
                    SELECT role, COUNT(*) as count FROM sessions
                    WHERE expires_at > ? GROUP BY role
                ''', (datetime.now(),))
                sessions_by_role = {row['role']: row['count'] for row in cursor.fetchall()}

                cursor.execute('SELECT COUNT(*) FROM login_attempts WHERE attempt_time > ?',
                             (datetime.now() - timedelta(hours=24),))
                login_attempts_24h = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM login_attempts WHERE success = 0 AND attempt_time > ?',
                             (datetime.now() - timedelta(hours=24),))
                failed_logins_24h = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM user_locks')
                locked_users = cursor.fetchone()[0]

            return {
                'total_sessions': total_sessions,
                'active_sessions': active_sessions,
                'unique_users': unique_users,
                'sessions_by_role': sessions_by_role,
                'login_attempts_24h': login_attempts_24h,
                'failed_logins_24h': failed_logins_24h,
                'locked_users': locked_users
            }

        except Exception as e:
            logger.error(f"获取会话统计失败: {e}")
            return {}

    def log_session_activity(self, session_id: str, activity_type: str,
                            activity_data: str = None, ip_address: str = None) -> bool:
        """记录会话活动"""
        try:
            with self.get_db_connection() as (cursor, conn):
                cursor.execute('''
                    INSERT INTO session_activities (session_id, activity_type, activity_data, ip_address)
                    VALUES (?, ?, ?, ?)
                ''', (session_id, activity_type, activity_data, ip_address))

            return True

        except Exception as e:
            logger.error(f"记录会话活动失败: {e}")
            return False

    def get_session_activities(self, session_id: str, limit: int = 50) -> list:
        """获取会话活动历史"""
        try:
            with self.get_db_connection() as (cursor, conn):
                cursor.execute('''
                    SELECT * FROM session_activities
                    WHERE session_id = ?
                    ORDER BY created_at DESC LIMIT ?
                ''', (session_id, limit))

                return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"获取会话活动失败: {e}")
            return []


session_manager: Optional[SessionManager] = None


def init_session_manager(db_path: str, timeout_minutes: int = 30) -> SessionManager:
    """初始化会话管理器"""
    global session_manager
    session_manager = SessionManager(db_path, timeout_minutes)
    logger.info(f"会话管理器初始化完成,超时时间: {timeout_minutes}分钟")
    return session_manager


def get_session_manager() -> SessionManager:
    """获取会话管理器实例"""
    global session_manager
    if session_manager is None:
        db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'
        session_manager = SessionManager(db_path)
    return session_manager


def session_timeout_middleware(app):
    """会话超时中间件"""
    @app.before_request
    def check_session_timeout():
        if request.path.startswith('/static/') or request.path in ['/login', '/register', '/', '/auth/logout']:
            return None

        session_id = session.get('session_id')
        if not session_id:
            return None

        sm = get_session_manager()
        session_data = sm.validate_session(session_id)

        if not session_data:
            session.clear()
            return jsonify({
                'success': False,
                'error': 'SessionExpired',
                'message': '会话已过期,请重新登录'
            }), 401

        sm.refresh_session(session_id)
        return None

    return app


def login_required(f):
    """装饰器:要求登录"""
    def wrapper(*args, **kwargs):
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'Unauthorized',
                'message': '请先登录'
            }), 401

        sm = get_session_manager()
        session_data = sm.validate_session(session_id)

        if not session_data:
            session.clear()
            return jsonify({
                'success': False,
                'error': 'SessionExpired',
                'message': '会话已过期,请重新登录'
            }), 401

        return f(*args, **kwargs)
    return wrapper


def role_required(allowed_roles: list):
    """装饰器:要求特定角色"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            session_id = session.get('session_id')
            if not session_id:
                return jsonify({
                    'success': False,
                    'error': 'Unauthorized',
                    'message': '请先登录'
                }), 401

            user_role = session.get('role', 'guest')

            if user_role not in allowed_roles:
                return jsonify({
                    'success': False,
                    'error': 'Forbidden',
                    'message': '您没有权限访问此资源'
                }), 403

            return f(*args, **kwargs)
        return wrapper
    return decorator
