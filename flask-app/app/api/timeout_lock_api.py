# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
考试系统超时锁定API模块
提供考试会话超时管理和账户锁定功能
"""

import logging
import sqlite3
import time
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session
from functools import wraps

logger = logging.getLogger(__name__)

timeout_lock_api = Blueprint('timeout_lock_api', __name__)

DATABASE_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'

# 考试系统配置
EXAM_SESSION_TIMEOUT = 30  # 考试会话超时时间（分钟）
EXAM_MAX_IDLE_TIME = 15    # 考试期间最大空闲时间（分钟）
LOCK_AFTER_FAILED_ATTEMPTS = 5  # 锁定前失败次数
LOCK_DURATION = 10          # 锁定时长（分钟）


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_exam_lock_tables():
    """初始化考试锁定相关数据库表"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 考试会话超时表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_session_timeout (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                exam_id TEXT,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                is_active INTEGER DEFAULT 1,
                timeout_reason TEXT
            )
        ''')

        # 考试账户锁定表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_account_locks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                username TEXT NOT NULL,
                locked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                locked_until TIMESTAMP NOT NULL,
                lock_reason TEXT,
                failed_attempts INTEGER DEFAULT 0,
                is_manual_lock INTEGER DEFAULT 0
            )
        ''')

        # 考试活动日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL,
                activity_data TEXT,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_exam_timeout_session ON exam_session_timeout(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_exam_timeout_user ON exam_session_timeout(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_exam_locks_user ON exam_account_locks(user_id)')

        conn.commit()
        logger.info("考试锁定数据库表初始化完成")


def check_user_exam_lock(user_id: int) -> dict:
    """检查用户是否被考试系统锁定"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM exam_account_locks
            WHERE user_id = ? AND locked_until > ?
        ''', (user_id, datetime.now()))

        lock_record = cursor.fetchone()

        if lock_record:
            locked_until = datetime.strptime(lock_record['locked_until'], '%Y-%m-%d %H:%M:%S.%f') if isinstance(lock_record['locked_until'], str) else lock_record['locked_until']
            remaining_seconds = int((locked_until - datetime.now()).total_seconds())
            return {
                'locked': True,
                'remaining_seconds': remaining_seconds,
                'lock_reason': lock_record['lock_reason'],
                'locked_until': str(lock_record['locked_until'])
            }

    return {'locked': False}


def lock_user_exam_account(user_id: int, username: str, reason: str, duration_minutes: int = None) -> bool:
    """锁定用户考试账户"""
    if duration_minutes is None:
        duration_minutes = LOCK_DURATION

    locked_until = datetime.now() + timedelta(minutes=duration_minutes)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO exam_account_locks
            (user_id, username, locked_until, lock_reason, is_manual_lock)
            VALUES (?, ?, ?, ?, 1)
        ''', (user_id, username, locked_until, reason))
        conn.commit()

    logger.warning(f"用户 {username} (ID:{user_id}) 考试账户已被锁定: {reason}")
    return True


def unlock_user_exam_account(user_id: int) -> bool:
    """解锁用户考试账户"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM exam_account_locks WHERE user_id = ?', (user_id,))
        conn.commit()

    logger.info(f"用户 ID:{user_id} 考试账户已解锁")
    return True


def create_exam_session(user_id: int, session_id: str, exam_id: str = None) -> dict:
    """创建考试会话"""
    now = datetime.now()
    expires_at = now + timedelta(minutes=EXAM_SESSION_TIMEOUT)

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 使该用户的旧考试会话失效
        cursor.execute('''
            UPDATE exam_session_timeout
            SET is_active = 0, timeout_reason = 'new_session_created'
            WHERE user_id = ? AND is_active = 1
        ''', (user_id,))

        # 创建新会话
        cursor.execute('''
            INSERT INTO exam_session_timeout
            (session_id, user_id, exam_id, expires_at, is_active)
            VALUES (?, ?, ?, ?, 1)
        ''', (session_id, user_id, exam_id, expires_at))

        # 记录活动
        cursor.execute('''
            INSERT INTO exam_activity_logs
            (session_id, user_id, activity_type, activity_data, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_id, user_id, 'exam_session_created',
              f'exam_id:{exam_id}' if exam_id else 'no_exam',
              request.remote_addr if request else None,
              request.user_agent.string if request else None))

        conn.commit()

    return {
        'success': True,
        'expires_at': str(expires_at),
        'timeout_minutes': EXAM_SESSION_TIMEOUT
    }


def validate_exam_session(session_id: str) -> dict:
    """验证考试会话是否有效"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM exam_session_timeout
            WHERE session_id = ? AND is_active = 1
        ''', (session_id,))

        record = cursor.fetchone()

        if not record:
            return {'valid': False, 'reason': 'session_not_found'}

        expires_at = record['expires_at']
        if isinstance(expires_at, str):
            expires_at = datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S.%f')

        if datetime.now() > expires_at:
            # 会话超时
            cursor.execute('''
                UPDATE exam_session_timeout
                SET is_active = 0, timeout_reason = 'expired'
                WHERE session_id = ?
            ''', (session_id,))
            conn.commit()
            return {'valid': False, 'reason': 'session_expired'}

        return {
            'valid': True,
            'user_id': record['user_id'],
            'exam_id': record['exam_id'],
            'expires_at': str(record['expires_at'])
        }


def refresh_exam_session(session_id: str) -> bool:
    """刷新考试会话活动时间"""
    now = datetime.now()
    expires_at = now + timedelta(minutes=EXAM_SESSION_TIMEOUT)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE exam_session_timeout
            SET last_activity = ?, expires_at = ?
            WHERE session_id = ? AND is_active = 1
        ''', (now, expires_at, session_id))

        if cursor.rowcount > 0:
            cursor.execute('''
                INSERT INTO exam_activity_logs
                (session_id, user_id, activity_type, ip_address)
                SELECT ?, user_id, 'session_refresh', ?
                FROM exam_session_timeout WHERE session_id = ?
            ''', (session_id, request.remote_addr if request else None, session_id))
            conn.commit()
            return True

    return False


def end_exam_session(session_id: str, reason: str = 'user_ended') -> bool:
    """结束考试会话"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE exam_session_timeout
            SET is_active = 0, timeout_reason = ?
            WHERE session_id = ?
        ''', (reason, session_id))
        conn.commit()
        return cursor.rowcount > 0


def record_exam_activity(session_id: str, user_id: int, activity_type: str, activity_data: str = None) -> bool:
    """记录考试活动"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO exam_activity_logs
                (session_id, user_id, activity_type, activity_data, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session_id, user_id, activity_type, activity_data,
                  request.remote_addr if request else None,
                  request.user_agent.string if request else None))
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"记录考试活动失败: {e}")
        return False


def get_user_exam_sessions(user_id: int, include_expired: bool = False) -> list:
    """获取用户的考试会话"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        if include_expired:
            cursor.execute('''
                SELECT * FROM exam_session_timeout
                WHERE user_id = ?
                ORDER BY start_time DESC
            ''', (user_id,))
        else:
            cursor.execute('''
                SELECT * FROM exam_session_timeout
                WHERE user_id = ? AND is_active = 1
                ORDER BY start_time DESC
            ''', (user_id,))

        return [dict(row) for row in cursor.fetchall()]


def get_exam_activity_logs(session_id: str = None, user_id: int = None, limit: int = 100) -> list:
    """获取考试活动日志"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        if session_id:
            cursor.execute('''
                SELECT * FROM exam_activity_logs
                WHERE session_id = ?
                ORDER BY created_at DESC LIMIT ?
            ''', (session_id, limit))
        elif user_id:
            cursor.execute('''
                SELECT * FROM exam_activity_logs
                WHERE user_id = ?
                ORDER BY created_at DESC LIMIT ?
            ''', (user_id, limit))
        else:
            cursor.execute('SELECT * FROM exam_activity_logs ORDER BY created_at DESC LIMIT ?', (limit,))

        return [dict(row) for row in cursor.fetchall()]


# ==================== API路由 ====================

@timeout_lock_api.route('/api/exam/lock/status', methods=['GET'])
def get_exam_lock_status():
    """获取当前用户的考试锁定状态"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    lock_status = check_user_exam_lock(user_id)
    return jsonify({
        'success': True,
        'locked': lock_status['locked'],
        'remaining_seconds': lock_status.get('remaining_seconds', 0),
        'lock_reason': lock_status.get('lock_reason', '')
    })


@timeout_lock_api.route('/api/exam/lock/unlock/<int:target_user_id>', methods=['POST'])
def unlock_exam_account(target_user_id):
    """解锁指定用户的考试账户（需要管理员权限）"""
    current_user_id = session.get('user_id')
    current_role = session.get('role')

    if not current_user_id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    # 只有管理员可以解锁
    if current_role not in ['admin', 'super_admin', 'hardware_admin']:
        return jsonify({'success': False, 'error': 'Forbidden'}), 403

    success = unlock_user_exam_account(target_user_id)
    return jsonify({'success': success})


@timeout_lock_api.route('/api/exam/session/create', methods=['POST'])
def create_exam_session_api():
    """创建考试会话"""
    user_id = session.get('user_id')
    session_id = session.get('session_id')

    if not user_id or not session_id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    # 检查是否被锁定
    lock_status = check_user_exam_lock(user_id)
    if lock_status['locked']:
        return jsonify({
            'success': False,
            'error': 'AccountLocked',
            'remaining_seconds': lock_status['remaining_seconds'],
            'message': '账户已被锁定'
        }), 403

    data = request.get_json() or {}
    exam_id = data.get('exam_id')

    result = create_exam_session(user_id, session_id, exam_id)
    return jsonify(result)


@timeout_lock_api.route('/api/exam/session/validate', methods=['GET'])
def validate_exam_session_api():
    """验证当前考试会话"""
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'valid': False, 'reason': 'no_session'})

    result = validate_exam_session(session_id)
    return jsonify(result)


@timeout_lock_api.route('/api/exam/session/refresh', methods=['POST'])
def refresh_exam_session_api():
    """刷新考试会话时间"""
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'error': 'No session'}), 401

    success = refresh_exam_session(session_id)
    return jsonify({'success': success})


@timeout_lock_api.route('/api/exam/session/end', methods=['POST'])
def end_exam_session_api():
    """结束当前考试会话"""
    session_id = session.get('session_id')
    user_id = session.get('user_id')

    if not session_id or not user_id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    reason = data.get('reason', 'user_ended')

    success = end_exam_session(session_id, reason)
    return jsonify({'success': success})


@timeout_lock_api.route('/api/exam/activity/log', methods=['POST'])
def log_exam_activity_api():
    """记录考试活动"""
    session_id = session.get('session_id')
    user_id = session.get('user_id')

    if not session_id or not user_id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    activity_type = data.get('activity_type', 'unknown')
    activity_data = data.get('activity_data', '')

    success = record_exam_activity(session_id, user_id, activity_type, activity_data)
    return jsonify({'success': success})


@timeout_lock_api.route('/api/exam/sessions', methods=['GET'])
def get_user_exam_sessions_api():
    """获取当前用户的考试会话列表"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    include_expired = request.args.get('include_expired', 'false').lower() == 'true'
    sessions = get_user_exam_sessions(user_id, include_expired)

    return jsonify({
        'success': True,
        'sessions': sessions
    })


@timeout_lock_api.route('/api/exam/logs', methods=['GET'])
def get_exam_logs_api():
    """获取考试活动日志"""
    user_id = session.get('user_id')
    role = session.get('role')

    if not user_id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    # 普通用户只能看自己的日志，管理员可以看所有
    query_user_id = user_id if role not in ['admin', 'super_admin', 'hardware_admin'] else None

    session_id = request.args.get('session_id')
    limit = int(request.args.get('limit', 100))

    logs = get_exam_activity_logs(session_id, query_user_id, limit)

    return jsonify({
        'success': True,
        'logs': logs
    })


@timeout_lock_api.route('/api/exam/config', methods=['GET'])
def get_exam_config():
    """获取考试系统配置"""
    return jsonify({
        'success': True,
        'config': {
            'session_timeout_minutes': EXAM_SESSION_TIMEOUT,
            'max_idle_minutes': EXAM_MAX_IDLE_TIME,
            'lock_after_failed_attempts': LOCK_AFTER_FAILED_ATTEMPTS,
            'lock_duration_minutes': LOCK_DURATION
        }
    })


# 初始化数据库表
try:
    init_exam_lock_tables()
except Exception as e:
    logger.warning(f"初始化考试锁定表失败: {e}")