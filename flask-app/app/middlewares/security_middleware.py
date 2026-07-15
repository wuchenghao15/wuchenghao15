#!/usr/bin/env python3
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

LOCKED_USERS = {}
SESSION_TIMEOUT = 1800
WARNING_TIMEOUT = 300
MAX_FAILED_LOGINS = 5
RATE_LIMIT = 100
RATE_LIMIT_WINDOW = 60

class SecurityMiddlewareClass:
    @staticmethod
    def before_request_handler():
        from flask import request, session, g

        allowed_paths = ['/auth/login', '/auth/register', '/auth/forgot_password',
                         '/admin_app/login',
                         '/api/health', '/api/time', '/api/status', '/api/system_params',
                         '/api/monitoring/health',
                         '/api/questions/categories', '/api/questions/tags', '/api/questions/search',
                         '/api/tts/languages', '/api/tts/voices', '/api/tts/cache/stats',
                         '/api/tts/speak',
                         '/api/ai-repair/stats', '/api/ai-repair/fix-history',
                         '/api/server-time', '/api/error/report',
                         '/', '/login', '/register', '/forgot_password', '/forgot-password',
                         '/assets/', '/static/', '/favicon.ico',
                         '/robots.txt', '/sitemap.xml']

        path = request.path

        # 检查是否在白名单中
        for allowed in allowed_paths:
            if path == allowed:
                return None
            if allowed != '/' and allowed.endswith('/') and path.startswith(allowed):
                return None

        # 检查URL是否匹配任何已注册的路由规则
        from flask import current_app
        if current_app:
            from werkzeug.exceptions import NotFound, MethodNotAllowed
            adapter = current_app.url_map.bind('')
            try:
                adapter.match(path)
            except (NotFound, MethodNotAllowed):
                # 没有匹配的路由，让Flask处理404
                return None

        # 账户锁定检查
        if session.get('locked_until') and time.time() < session['locked_until']:
            return {
                'success': False,
                'error': '账户已锁定',
                'locked_until': session['locked_until'],
                'status_code': 423
            }

        # 已登录用户的会话检查
        if session.get('logged_in'):
            last_activity = session.get('last_activity', time.time())
            idle_time = time.time() - last_activity

            if idle_time > SESSION_TIMEOUT:
                session.clear()
                return {
                    'success': False,
                    'error': '会话已超时，请重新登录',
                    'status_code': 401
                }

            if idle_time > SESSION_TIMEOUT - WARNING_TIMEOUT:
                session['timeout_warning'] = True

            session['last_activity'] = time.time()

            if 'user_id' not in session or 'role' not in session:
                session.clear()
                return {
                    'success': False,
                    'error': '会话验证失败',
                    'status_code': 401
                }

            # 基于路径的角色权限检查
            required_role = None
            if '/admin_app/' in path or '/admin_center' in path:
                required_role = ['admin', 'super_admin', 'system_admin']
            elif '/teacher' in path:
                required_role = ['teacher', 'admin', 'super_admin', 'system_admin']
            elif '/designer' in path:
                required_role = ['designer', 'admin', 'super_admin', 'system_admin']

            if required_role:
                user_role = session.get('role')
                if user_role not in required_role:
                    return {
                        'success': False,
                        'error': '权限不足',
                        'status_code': 403
                    }
        else:
            # 未登录用户访问受保护页面 - 重定向到登录页
            # API路径返回JSON错误
            if path.startswith('/api/'):
                return {
                    'success': False,
                    'error': '未登录，请先登录',
                    'status_code': 401
                }
            # 页面路径重定向到登录
            return {
                'success': False,
                'error': '请先登录',
                'status_code': 302,
                'redirect': '/auth/login'
            }

        return None
    
    @staticmethod
    def unlock_user(username):
        if username in LOCKED_USERS:
            del LOCKED_USERS[username]
            return True
        return False
    
    @staticmethod
    def lock_user(username, locked_by='system', duration=900):
        LOCKED_USERS[username] = {
            'locked_at': time.time(),
            'locked_until': time.time() + duration,
            'locked_by': locked_by
        }
        return True
    
    @staticmethod
    def check_user_locked(username):
        if username in LOCKED_USERS:
            lock_info = LOCKED_USERS[username]
            if time.time() < lock_info['locked_until']:
                return lock_info
        return None
    
    @staticmethod
    def record_failed_login(username):
        from app.utils.db import DatabaseManager
        db = DatabaseManager()
        try:
            result = db.fetch_one(
                "SELECT failed_login_count, last_failed_login FROM users WHERE username = ?",
                (username,)
            )
            if result:
                count = result[0] + 1 if result[0] else 1
                db.execute(
                    "UPDATE users SET failed_login_count = ?, last_failed_login = ? WHERE username = ?",
                    (count, datetime.now().isoformat(), username)
                )
                if count >= MAX_FAILED_LOGINS:
                    SecurityMiddlewareClass.lock_user(username, 'failed_logins', 3600)
        except Exception as e:
            logger.error(f"记录登录失败次数失败: {e}")
    
    @staticmethod
    def reset_failed_login(username):
        from app.utils.db import DatabaseManager
        db = DatabaseManager()
        try:
            db.execute(
                "UPDATE users SET failed_login_count = 0, last_failed_login = NULL WHERE username = ?",
                (username,)
            )
            SecurityMiddlewareClass.unlock_user(username)
        except Exception as e:
            logger.error(f"重置登录失败次数失败: {e}")

security_middleware = SecurityMiddlewareClass()
SecurityMiddleware = SecurityMiddlewareClass