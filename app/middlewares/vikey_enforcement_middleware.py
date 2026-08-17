#!/usr/bin/env python3
"""
Vikey USB加密狗强制认证中间件
功能：
1. 首页和超级管理员所有页面必须检测vikey加密狗
2. 未检测到加密狗、状态异常或离线无网络都不能使用
3. 实时监控加密狗状态变化
4. 自动锁定系统当加密狗被拔出
"""

import os
import time
import json
import logging
import sqlite3
import requests
from datetime import datetime, timedelta
from functools import wraps

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

VIKEY_CHECK_INTERVAL = 2  # 检查间隔（秒）
NETWORK_CHECK_TIMEOUT = 5  # 网络检查超时（秒）
VIKEY_LOCK_TIMEOUT = 300  # 加密狗拔出后锁定超时时间（秒）

# 需要强制vikey认证的路径模式
VIKEY_REQUIRED_PATHS = [
    '/',
    '/dashboard',
    '/admin_center',
    '/super_admin',
    '/admin_app/',
    '/settings',
    '/vikey_manager',
    '/system_status',
    '/backup_manager',
    '/approval_management',
    '/layout_manager',
]

# 白名单路径（不需要vikey检查）
VIKEY_WHITELIST_PATHS = [
    '/auth/login',
    '/auth/register',
    '/auth/forgot_password',
    '/api/vikey/',
    '/api/health',
    '/api/status',
    '/api/time',
    '/api/server-time',
    '/static/',
    '/assets/',
    '/favicon.ico',
    '/robots.txt',
]


class VikeyEnforcementMiddleware:
    """Vikey USB加密狗强制认证中间件"""

    def __init__(self):
        self._vikey_cache = {}
        self._network_cache = {}
        self._lock_states = {}

    @staticmethod
    def _get_db_path():
        return os.path.join(PROJECT_ROOT, 'app.db')

    @staticmethod
    def _check_network():
        """检查网络连接状态"""
        try:
            response = requests.get('https://www.baidu.com', timeout=NETWORK_CHECK_TIMEOUT)
            return response.status_code == 200
        except Exception:
            try:
                response = requests.get('https://www.google.com', timeout=NETWORK_CHECK_TIMEOUT)
                return response.status_code == 200
            except Exception:
                return False

    @staticmethod
    def _check_vikey():
        """检查vikey加密狗状态"""
        try:
            from core.services.vikey_driver import get_vikey_manager
            mgr = get_vikey_manager()
            result = mgr.detect()
            
            devices = result.get('devices', [])
            for dev in devices:
                binding = dev.get('binding', {})
                if dev.get('is_present') and binding.get('binding_status') == 'bound':
                    username = str(binding.get('username') or '').lower()
                    if username == 'wuchenghao15':
                        return {
                            'status': 'ok',
                            'serial': dev.get('serial'),
                            'username': binding.get('username'),
                            'message': 'Vikey USB加密狗检测正常',
                        }
            
            return {
                'status': 'no_device',
                'message': '未检测到Vikey USB加密狗',
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Vikey检测异常: {str(e)}',
            }

    @staticmethod
    def _log_event(event_type, severity, description):
        """记录vikey强制认证事件"""
        try:
            db_path = VikeyEnforcementMiddleware._get_db_path()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vikey_enforcement_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    severity TEXT DEFAULT 'info',
                    description TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                INSERT INTO vikey_enforcement_logs
                (event_type, severity, description, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (event_type, severity, description, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"记录vikey强制认证事件失败: {e}")

    def _is_vikey_required(self, path):
        """判断路径是否需要vikey认证"""
        for whitelist in VIKEY_WHITELIST_PATHS:
            if path == whitelist or (whitelist.endswith('/') and path.startswith(whitelist)):
                return False
        
        for required in VIKEY_REQUIRED_PATHS:
            if path == required or (required.endswith('/') and path.startswith(required)):
                return True
        
        return False

    def check_vikey_enforcement(self, path, username=None):
        """检查vikey强制认证"""
        if not self._is_vikey_required(path):
            return {'allowed': True, 'reason': '路径不在强制认证列表'}
        
        is_super_admin = (username or '').lower() == 'wuchenghao15'
        
        if is_super_admin:
            vikey_status = self._check_vikey()
            network_status = self._check_network()
            
            if vikey_status['status'] != 'ok':
                self._log_event('vikey_denied', 'critical', 
                               f'超级管理员访问被拒绝: {vikey_status["message"]}, 路径: {path}')
                return {
                    'allowed': False,
                    'reason': vikey_status['message'],
                    'vikey_status': vikey_status['status'],
                    'network_status': network_status,
                }
            
            if not network_status:
                self._log_event('network_denied', 'warning', 
                               f'超级管理员访问被拒绝: 网络离线, 路径: {path}')
                return {
                    'allowed': False,
                    'reason': '网络离线，请检查网络连接',
                    'vikey_status': vikey_status['status'],
                    'network_status': False,
                }
            
            self._log_event('vikey_granted', 'info', 
                           f'超级管理员访问允许: {vikey_status["serial"]}, 路径: {path}')
            return {
                'allowed': True,
                'reason': 'Vikey认证通过',
                'vikey_status': vikey_status['status'],
                'network_status': network_status,
                'serial': vikey_status.get('serial'),
            }
        
        return {'allowed': True, 'reason': '非超级管理员，不需要vikey认证'}

    def create_flask_middleware(self):
        """创建Flask中间件装饰器"""
        from flask import request, session, redirect, jsonify
        
        def middleware(fn):
            @wraps(fn)
            def wrapped(*args, **kwargs):
                path = request.path
                username = session.get('username', '')
                
                result = self.check_vikey_enforcement(path, username)
                
                if not result['allowed']:
                    if request.path.startswith('/api/'):
                        return jsonify({
                            'success': False,
                            'error': result['reason'],
                            'vikey_status': result.get('vikey_status'),
                            'network_status': result.get('network_status'),
                        }), 403
                    
                    return redirect(f'/auth/login?error={result["reason"]}')
                
                return fn(*args, **kwargs)
            
            return wrapped
        
        return middleware

    def enforce_vikey_on_page(self):
        """为Flask路由创建vikey强制认证装饰器"""
        from flask import request, session, abort
        
        def decorator(fn):
            @wraps(fn)
            def wrapped(*args, **kwargs):
                path = request.path
                username = session.get('username', '')
                
                result = self.check_vikey_enforcement(path, username)
                
                if not result['allowed']:
                    abort(403, description=result['reason'])
                
                return fn(*args, **kwargs)
            
            return wrapped
        
        return decorator

    def get_vikey_status(self):
        """获取当前vikey状态"""
        vikey_status = self._check_vikey()
        network_status = self._check_network()
        
        return {
            'vikey': vikey_status,
            'network': network_status,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

    def get_enforcement_logs(self, limit=100):
        """获取强制认证日志"""
        try:
            db_path = self._get_db_path()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM vikey_enforcement_logs
                ORDER BY timestamp DESC LIMIT ?
            ''', (limit,))
            columns = [desc[0] for desc in cursor.description]
            logs = [dict(zip(columns, row)) for row in cursor.fetchall()]
            conn.close()
            return logs
        except Exception as e:
            logger.error(f"获取强制认证日志失败: {e}")
            return []


vikey_enforcement = VikeyEnforcementMiddleware()


def vikey_required(func):
    """装饰器：标记需要vikey认证的路由"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        from flask import request, session, abort
        path = request.path
        username = session.get('username', '')
        
        result = vikey_enforcement.check_vikey_enforcement(path, username)
        
        if not result['allowed']:
            abort(403, description=result['reason'])
        
        return func(*args, **kwargs)
    
    return wrapper


def check_super_admin_vikey(username):
    """检查超级管理员的vikey状态"""
    is_super_admin = (username or '').lower() == 'wuchenghao15'
    
    if not is_super_admin:
        return {'allowed': True, 'reason': '非超级管理员'}
    
    vikey_status = VikeyEnforcementMiddleware._check_vikey()
    network_status = VikeyEnforcementMiddleware._check_network()
    
    return {
        'allowed': vikey_status['status'] == 'ok' and network_status,
        'vikey_status': vikey_status,
        'network_status': network_status,
        'reason': vikey_status['message'] if vikey_status['status'] != 'ok' else 
                  '网络离线' if not network_status else '认证通过',
    }
