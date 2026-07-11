# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
安全中间件系统 - 提供全面的安全控制
包含: 访问权限控制、会话超时机制、账户锁定机制、统一错误处理、速率限制
配置参数统一从数据库读取
"""

import time
import threading
from functools import wraps
from typing import Dict, Any, List, Optional, Callable
from flask import request, session, jsonify, redirect, url_for
from app.utils.logging import logger

# 全局锁定用户列表（内存缓存）
LOCKED_USERS: Dict[str, Dict[str, Any]] = {}
# 登录尝试记录（内存缓存）
LOGIN_ATTEMPTS: Dict[str, Dict[str, Any]] = {}
# 请求计数（内存缓存）
REQUEST_COUNTS: Dict[str, List[float]] = {}


class SecurityMiddleware:
    """安全中间件主类"""
    
    @staticmethod
    def _get_session_timeout() -> int:
        """从数据库获取会话超时时间（秒）"""
        try:
            from app.config import get_config_value
            return get_config_value('SESSION_TIMEOUT', 30 * 60)
        except Exception:
            return 30 * 60
    
    @staticmethod
    def _get_max_login_attempts() -> int:
        """从数据库获取最大登录尝试次数"""
        try:
            from app.config import get_config_value
            return get_config_value('MAX_LOGIN_ATTEMPTS', 5)
        except Exception:
            return 5
    
    @staticmethod
    def _get_lock_duration() -> int:
        """从数据库获取账户锁定时间（秒）"""
        try:
            from app.config import get_config_value
            return get_config_value('LOCKOUT_DURATION', 15 * 60)
        except Exception:
            return 15 * 60
    
    @staticmethod
    def _get_rate_limits() -> Dict[str, Dict[str, int]]:
        """从数据库获取速率限制配置"""
        try:
            from app.config import get_config_value
            return get_config_value('RATE_LIMITS', {
                'login': {'limit': 5, 'window': 60},
                'api': {'limit': 100, 'window': 60},
                'register': {'limit': 3, 'window': 300},
            })
        except Exception:
            return {
                'login': {'limit': 5, 'window': 60},
                'api': {'limit': 100, 'window': 60},
                'register': {'limit': 3, 'window': 300},
            }
    
    @staticmethod
    def _get_permission_rules() -> Dict[str, Dict[str, List[str]]]:
        """从数据库获取权限规则"""
        try:
            from app.config import get_config_value
            return get_config_value('PERMISSION_RULES', {
                'admin': {
                    'allowed_routes': ['*'],
                    'allowed_pages': ['dashboard', 'admin*', 'system*', 'exam*', 'user*', 'api*'],
                },
                'teacher': {
                    'allowed_routes': ['/dashboard', '/exam*', '/api/exam*', '/api/question*'],
                    'allowed_pages': ['dashboard', 'exam*', 'question*'],
                },
                'student': {
                    'allowed_routes': ['/dashboard', '/exam/*', '/api/exam/*'],
                    'allowed_pages': ['dashboard', 'exam*'],
                },
                'parent': {
                    'allowed_routes': ['/dashboard', '/api/parent/*'],
                    'allowed_pages': ['dashboard', 'parent*'],
                },
                'user': {
                    'allowed_routes': ['/dashboard', '/api/user/*'],
                    'allowed_pages': ['dashboard'],
                },
            })
        except Exception:
            return {
                'admin': {
                    'allowed_routes': ['*'],
                    'allowed_pages': ['dashboard', 'admin*', 'system*', 'exam*', 'user*', 'api*'],
                },
                'teacher': {
                    'allowed_routes': ['/dashboard', '/exam*', '/api/exam*', '/api/question*'],
                    'allowed_pages': ['dashboard', 'exam*', 'question*'],
                },
                'student': {
                    'allowed_routes': ['/dashboard', '/exam/*', '/api/exam/*'],
                    'allowed_pages': ['dashboard', 'exam*'],
                },
                'parent': {
                    'allowed_routes': ['/dashboard', '/api/parent/*'],
                    'allowed_pages': ['dashboard', 'parent*'],
                },
                'user': {
                    'allowed_routes': ['/dashboard', '/api/user/*'],
                    'allowed_pages': ['dashboard'],
                },
            }

    @staticmethod
    def require_login(f: Callable) -> Callable:
        """登录装饰器 - 要求用户必须登录"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.is_json or 'application/json' in request.headers.get('Accept', ''):
                    return jsonify({
                        'success': False,
                        'error': 'NOT_LOGGED_IN',
                        'message': '用户未登录，请先登录',
                        'redirect': '/auth/login'
                    }), 401
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function

    @staticmethod
    def require_role(required_role: str) -> Callable:
        """角色装饰器 - 要求特定角色"""
        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if 'user_id' not in session:
                    if request.is_json:
                        return jsonify({
                            'success': False,
                            'error': 'NOT_LOGGED_IN',
                            'message': '用户未登录'
                        }), 401
                    return redirect(url_for('login'))
                
                user_role = session.get('role', 'user')
                permission_rules = SecurityMiddleware._get_permission_rules()
                
                if user_role == 'admin':
                    return f(*args, **kwargs)
                
                if user_role not in permission_rules:
                    if request.is_json:
                        return jsonify({
                            'success': False,
                            'error': 'PERMISSION_DENIED',
                            'message': f'未知角色: {user_role}',
                            'current_role': user_role
                        }), 403
                    return redirect(url_for('dashboard'))
                
                if user_role != required_role:
                    if request.is_json:
                        return jsonify({
                            'success': False,
                            'error': 'PERMISSION_DENIED',
                            'message': f'需要{required_role}权限',
                            'current_role': user_role
                        }), 403
                    return redirect(url_for('dashboard'))
                return f(*args, **kwargs)
            return decorated_function
        return decorator

    @staticmethod
    def require_admin(f: Callable) -> Callable:
        """管理员装饰器"""
        return SecurityMiddleware.require_role('admin')(f)

    @staticmethod
    def require_permission(permission: str) -> Callable:
        """权限装饰器 - 要求特定权限"""
        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if 'user_id' not in session:
                    if request.is_json:
                        return jsonify({
                            'success': False,
                            'error': 'NOT_LOGGED_IN',
                            'message': '用户未登录'
                        }), 401
                    return redirect(url_for('login'))
                
                user_role = session.get('role', 'user')
                if user_role == 'admin':
                    return f(*args, **kwargs)
                
                return jsonify({
                    'success': False,
                    'error': 'PERMISSION_DENIED',
                    'message': f'需要{permission}权限',
                    'current_role': user_role
                }), 403
            return decorated_function
        return decorator

    @staticmethod
    def check_session_timeout() -> Optional[dict]:
        """检查会话是否超时"""
        if 'user_id' not in session:
            return None
        
        login_time = session.get('login_time')
        if login_time:
            try:
                from datetime import datetime
                login_datetime = datetime.fromisoformat(login_time)
                now = datetime.now()
                elapsed = (now - login_datetime).total_seconds()
                
                session_timeout = SecurityMiddleware._get_session_timeout()
                
                if elapsed > session_timeout:
                    return {
                        'success': False,
                        'error': 'SESSION_TIMEOUT',
                        'message': '会话已超时，请重新登录',
                        'elapsed': elapsed,
                        'timeout': session_timeout
                    }
            except Exception as e:
                logger.error(f"会话超时检查失败: {e}")
        
        return None

    @staticmethod
    def track_login_attempt(username: str, success: bool) -> Dict[str, Any]:
        """追踪登录尝试"""
        ip = request.remote_addr
        max_attempts = SecurityMiddleware._get_max_login_attempts()
        
        if ip not in LOGIN_ATTEMPTS:
            LOGIN_ATTEMPTS[ip] = {
                'attempts': 0,
                'last_attempt': 0,
                'usernames': {}
            }
        
        if username not in LOGIN_ATTEMPTS[ip]['usernames']:
            LOGIN_ATTEMPTS[ip]['usernames'][username] = {
                'attempts': 0,
                'last_attempt': 0
            }
        
        if success:
            LOGIN_ATTEMPTS[ip]['attempts'] = 0
            LOGIN_ATTEMPTS[ip]['usernames'][username]['attempts'] = 0
            return {'success': True, 'message': '登录成功'}
        
        LOGIN_ATTEMPTS[ip]['attempts'] += 1
        LOGIN_ATTEMPTS[ip]['usernames'][username]['attempts'] += 1
        LOGIN_ATTEMPTS[ip]['last_attempt'] = time.time()
        LOGIN_ATTEMPTS[ip]['usernames'][username]['last_attempt'] = time.time()
        
        attempts = LOGIN_ATTEMPTS[ip]['usernames'][username]['attempts']
        
        if attempts >= max_attempts:
            SecurityMiddleware.lock_user(username)
            remaining = SecurityMiddleware.get_lock_remaining(username)
            return {
                'success': False,
                'error': 'ACCOUNT_LOCKED',
                'message': f'账户已锁定，请{remaining}秒后重试',
                'locked_until': LOCKED_USERS[username]['locked_until']
            }
        
        remaining = max_attempts - attempts
        return {
            'success': False,
            'error': 'LOGIN_FAILED',
            'message': f'登录失败，还有{remaining}次尝试机会',
            'remaining_attempts': remaining
        }

    @staticmethod
    def lock_user(username: str) -> None:
        """锁定用户账户"""
        lock_duration = SecurityMiddleware._get_lock_duration()
        LOCKED_USERS[username] = {
            'locked_at': time.time(),
            'locked_until': time.time() + lock_duration,
            'locked_by': request.remote_addr
        }
        logger.warning(f"用户 {username} 账户已锁定，IP: {request.remote_addr}")

    @staticmethod
    def unlock_user(username: str) -> None:
        """解锁用户账户"""
        if username in LOCKED_USERS:
            del LOCKED_USERS[username]
            logger.info(f"用户 {username} 账户已解锁")

    @staticmethod
    def is_user_locked(username: str) -> bool:
        """检查用户是否被锁定"""
        if username not in LOCKED_USERS:
            return False
        
        lock_info = LOCKED_USERS[username]
        if time.time() > lock_info['locked_until']:
            SecurityMiddleware.unlock_user(username)
            return False
        
        return True

    @staticmethod
    def get_lock_remaining(username: str) -> int:
        """获取剩余锁定时间（秒）"""
        if username not in LOCKED_USERS:
            return 0
        remaining = int(LOCKED_USERS[username]['locked_until'] - time.time())
        return max(0, remaining)

    @staticmethod
    def check_rate_limit(endpoint_type: str, key: str = None) -> Dict[str, Any]:
        """检查速率限制"""
        rate_limits = SecurityMiddleware._get_rate_limits()
        
        if endpoint_type not in rate_limits:
            return {'allowed': True}
        
        config = rate_limits[endpoint_type]
        limit = config['limit']
        window = config['window']
        
        if key is None:
            key = request.remote_addr
        
        current_time = time.time()
        
        if key not in REQUEST_COUNTS:
            REQUEST_COUNTS[key] = []
        
        REQUEST_COUNTS[key] = [t for t in REQUEST_COUNTS[key] if current_time - t <= window]
        REQUEST_COUNTS[key].append(current_time)
        
        count = len(REQUEST_COUNTS[key])
        
        if count > limit:
            return {
                'allowed': False,
                'error': 'RATE_LIMIT_EXCEEDED',
                'message': f'请求过于频繁，请{window}秒后重试',
                'limit': limit,
                'count': count,
                'window': window
            }
        
        return {
            'allowed': True,
            'remaining': limit - count,
            'limit': limit,
            'window': window
        }

    @staticmethod
    def before_request_handler() -> Optional[dict]:
        """请求前处理 - 统一检查"""
        path = request.path
        
        if path.startswith('/static/') or path.startswith('/assets/') or path == '/':
            return None
        
        if path.startswith('/auth/login') or path.startswith('/auth/register'):
            rate_result = SecurityMiddleware.check_rate_limit('login')
            if not rate_result['allowed']:
                return rate_result
            return None
        
        timeout_result = SecurityMiddleware.check_session_timeout()
        if timeout_result:
            session.clear()
            return timeout_result
        
        return None

    @staticmethod
    def handle_exception(e: Exception) -> dict:
        """统一异常处理"""
        error_info = {
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': '系统内部错误',
            'timestamp': int(time.time() * 1000)
        }
        
        logger.error(f"系统异常: {type(e).__name__} - {e}")
        
        if isinstance(e, PermissionError):
            error_info['error'] = 'PERMISSION_DENIED'
            error_info['message'] = str(e)
        elif isinstance(e, ValueError):
            error_info['error'] = 'VALIDATION_ERROR'
            error_info['message'] = str(e)
        elif isinstance(e, TypeError):
            error_info['error'] = 'TYPE_ERROR'
            error_info['message'] = str(e)
        elif isinstance(e, Exception):
            error_info['error'] = type(e).__name__
            error_info['message'] = str(e)
        
        return error_info

    @staticmethod
    def clean_expired_locks() -> None:
        """清理过期的锁定"""
        expired_users = []
        for username, lock_info in LOCKED_USERS.items():
            if time.time() > lock_info['locked_until']:
                expired_users.append(username)
        
        for username in expired_users:
            SecurityMiddleware.unlock_user(username)

    @staticmethod
    def start_cleanup_thread() -> None:
        """启动清理线程"""
        def cleanup_loop():
            while True:
                time.sleep(60)
                SecurityMiddleware.clean_expired_locks()
                SecurityMiddleware._clean_request_counts()
        
        thread = threading.Thread(target=cleanup_loop, daemon=True)
        thread.start()
        logger.info("安全中间件清理线程启动成功")

    @staticmethod
    def _clean_request_counts() -> None:
        """清理过期的请求计数"""
        current_time = time.time()
        expired_keys = []
        
        for key, counts in REQUEST_COUNTS.items():
            REQUEST_COUNTS[key] = [t for t in counts if current_time - t <= 300]
            if not REQUEST_COUNTS[key]:
                expired_keys.append(key)
        
        for key in expired_keys:
            del REQUEST_COUNTS[key]


security_middleware = SecurityMiddleware()

SecurityMiddleware.start_cleanup_thread()