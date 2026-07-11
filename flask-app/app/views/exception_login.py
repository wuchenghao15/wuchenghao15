# -*- coding: utf-8 -*-
"""
强化修复的异常登录页面
- 增强安全性
- 添加更多状态类型
- 改进用户交互
- 优化视觉体验
"""
from flask import Blueprint, render_template, request, jsonify, session
import sqlite3
import logging
from datetime import datetime
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('exception_login')

exception_bp = Blueprint('exception_login', __name__, url_prefix='/auth')


def get_db_path():
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, 'app.db')


def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    if request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr or 'unknown'


def log_exception_event(event_type, status_type, status_title, status_message,
                       username=None, ip=None, reason=None, lock_time=None,
                       unlock_time=None, remaining_time=None):
    """上报异常登录事件到数据库"""
    import json
    import time
    max_retries = 3
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(get_db_path(), timeout=20)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS exception_login_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE NOT NULL,
                    event_type TEXT NOT NULL,
                    status_type TEXT NOT NULL,
                    status_title TEXT NOT NULL,
                    status_message TEXT,
                    username TEXT,
                    ip_address TEXT,
                    reason TEXT,
                    lock_time TEXT,
                    unlock_time TEXT,
                    remaining_time TEXT,
                    user_agent TEXT,
                    referer TEXT,
                    request_path TEXT,
                    created_at TEXT NOT NULL,
                    details TEXT
                )
            """)

            event_id = hashlib.md5(
                f"{event_type}{username}{ip}{datetime.now().isoformat()}{attempt}".encode()
            ).hexdigest()[:16]

            details = {
                'session_id': session.get('session_id'),
                'request_method': request.method,
                'request_args': dict(request.args),
                'headers': {
                    'Accept-Language': request.headers.get('Accept-Language', ''),
                    'Accept-Encoding': request.headers.get('Accept-Encoding', ''),
                }
            }

            cursor.execute("""
                INSERT INTO exception_login_logs
                (event_id, event_type, status_type, status_title, status_message,
                 username, ip_address, reason, lock_time, unlock_time, remaining_time,
                 user_agent, referer, request_path, created_at, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_id, event_type, status_type, status_title, status_message,
                username, ip, reason, lock_time, unlock_time, remaining_time,
                request.headers.get('User-Agent', ''),
                request.headers.get('Referer', ''),
                request.path,
                datetime.now().isoformat(),
                json.dumps(details)
            ))

            conn.commit()
            conn.close()

            logger.info(f"异常登录事件已上报: {event_id} ({event_type})")
            return event_id

        except sqlite3.OperationalError as e:
            if 'locked' in str(e).lower() and attempt < max_retries - 1:
                logger.warning(f"数据库锁定，重试 {attempt + 1}/{max_retries}: {e}")
                time.sleep(0.5 * (attempt + 1))
                continue
            logger.error(f"上报异常登录事件失败: {e}")
            return None
        except Exception as e:
            logger.error(f"上报异常登录事件失败: {e}")
            return None
    return None


@exception_bp.route('/exception-login', methods=['GET'])
def exception_login_page():
    """异常登录页面"""
    status_type = request.args.get('type', 'info')
    status_title = request.args.get('title', '系统提示')
    status_message = request.args.get('message', '')
    username = request.args.get('username', '')
    reason = request.args.get('reason', '')
    lock_time = request.args.get('lock_time', '')
    unlock_time = request.args.get('unlock_time', '')
    remaining_time = request.args.get('remaining_time', '')

    ip = get_client_ip()

    details = {}
    if username:
        details['username'] = username
    if ip:
        details['ip'] = ip
    if lock_time:
        details['lock_time'] = lock_time
    if unlock_time:
        details['unlock_time'] = unlock_time
    if reason:
        details['reason'] = reason
    if remaining_time:
        details['remaining_time'] = remaining_time

    log_exception_event(
        event_type='view',
        status_type=status_type,
        status_title=status_title,
        status_message=status_message,
        username=username,
        ip=ip,
        reason=reason,
        lock_time=lock_time,
        unlock_time=unlock_time,
        remaining_time=remaining_time
    )

    return render_template('exception_login.html',
                          status_type=status_type,
                          status_title=status_title,
                          status_message=status_message,
                          details=details)


@exception_bp.route('/exception-login/locked', methods=['GET'])
def account_locked():
    """账户锁定页面"""
    username = request.args.get('username', '')
    reason = request.args.get('reason', '多次登录失败')
    lock_minutes = int(request.args.get('minutes', 30))

    from datetime import timedelta
    lock_time = datetime.now()
    unlock_time = lock_time + timedelta(minutes=lock_minutes)
    remaining_time = f"{lock_minutes // 60:02d}:{lock_minutes % 60:02d}:00"

    ip = get_client_ip()

    log_exception_event(
        event_type='account_locked',
        status_type='locked',
        status_title='账户已锁定',
        status_message=f'您的账户因"{reason}"已被系统锁定',
        username=username,
        ip=ip,
        reason=reason,
        lock_time=lock_time.strftime('%Y-%m-%d %H:%M:%S'),
        unlock_time=unlock_time.strftime('%Y-%m-%d %H:%M:%S'),
        remaining_time=remaining_time
    )

    return render_template('exception_login.html',
                          status_type='locked',
                          status_title='账户已锁定',
                          status_message=f'您的账户因"{reason}"已被系统锁定',
                          details={
                              'username': username,
                              'ip': ip,
                              'lock_time': lock_time.strftime('%Y-%m-%d %H:%M:%S'),
                              'unlock_time': unlock_time.strftime('%Y-%m-%d %H:%M:%S'),
                              'reason': reason,
                              'remaining_time': remaining_time
                          })


@exception_bp.route('/exception-login/warning', methods=['GET'])
def account_warning():
    """账户警告页面"""
    username = request.args.get('username', '')
    reason = request.args.get('reason', '检测到异常登录尝试')

    ip = get_client_ip()

    log_exception_event(
        event_type='account_warning',
        status_type='warning',
        status_title='安全警告',
        status_message=reason,
        username=username,
        ip=ip,
        reason=reason
    )

    return render_template('exception_login.html',
                          status_type='warning',
                          status_title='安全警告',
                          status_message=reason,
                          details={
                              'username': username,
                              'ip': ip,
                              'reason': reason
                          })


@exception_bp.route('/api/exception-logs', methods=['GET'])
def get_exception_logs():
    """获取异常登录日志（API）"""
    try:
        limit = int(request.args.get('limit', 50))
        event_type = request.args.get('type', '')

        conn = sqlite3.connect(get_db_path())
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if event_type:
            cursor.execute("""
                SELECT * FROM exception_login_logs
                WHERE event_type = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (event_type, limit))
        else:
            cursor.execute("""
                SELECT * FROM exception_login_logs
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        logs = [dict(row) for row in rows]

        return jsonify({
            "success": True,
            "data": {
                "total": len(logs),
                "logs": logs
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@exception_bp.route('/api/exception-stats', methods=['GET'])
def get_exception_stats():
    """获取异常登录统计（API）"""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM exception_login_logs")
        total = cursor.fetchone()[0]

        cursor.execute("""
            SELECT event_type, COUNT(*) as count
            FROM exception_login_logs
            GROUP BY event_type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute("""
            SELECT status_type, COUNT(*) as count
            FROM exception_login_logs
            GROUP BY status_type
        """)
        by_status = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute("""
            SELECT ip_address, COUNT(*) as count
            FROM exception_login_logs
            WHERE ip_address IS NOT NULL
            GROUP BY ip_address
            ORDER BY count DESC
            LIMIT 10
        """)
        top_ips = [{"ip": row[0], "count": row[1]} for row in cursor.fetchall()]

        conn.close()

        return jsonify({
            "success": True,
            "data": {
                "total_events": total,
                "by_event_type": by_type,
                "by_status": by_status,
                "top_ips": top_ips
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
