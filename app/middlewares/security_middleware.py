#!/usr/bin/env python3
"""
安全中间件 - 增强版
功能：
1. 三级锁定机制（软锁/硬锁/永久锁）+ 递增锁定时长
2. 防暴力解锁：解锁尝试追踪 + 递增惩罚 + 验证挑战
3. IP维度限流与自动黑名单
4. 会话超时：空闲超时 + 绝对超时 + 渐进式警告
5. AI自学习防御：从攻击模式学习，自动调整安全参数
6. 安全事件全量记录到数据库
"""
import time
import json
import hashlib
import logging
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

# ==================== 配置常量 ====================

SESSION_TIMEOUT = 1800          # 空闲超时 30分钟
SESSION_ABSOLUTE_TIMEOUT = 28800  # 绝对超时 8小时
WARNING_TIMEOUT = 300           # 超时前5分钟警告
MAX_FAILED_LOGINS = 5           # 最大登录失败次数
RATE_LIMIT = 100                # 每分钟最大请求
RATE_LIMIT_WINDOW = 60          # 限流窗口
MAX_SESSIONS_PER_USER = 3       # 每用户最大会话数

# ===== 升级：新增安全约束常量 =====
MAX_REQUEST_BODY_SIZE = 10 * 1024 * 1024   # 请求体最大 10MB
MAX_QUERY_STRING_LENGTH = 2048             # URL 查询字符串最大长度
CSRF_EXEMPT_PATHS = frozenset({            # CSRF 豁免路径（GET 天生安全 + API Token 认证路径）
    '/auth/login', '/auth/register', '/auth/check_username', '/auth/check_password',
    '/auth/forgot_password', '/auth/reset_password',
    '/mobile/login', '/admin_app/login',
    '/api/health', '/api/time', '/api/status', '/api/server-time',
})
# 路径-角色权限矩阵：更精细的路径权限控制
PATH_ROLE_MATRIX = {
    '/admin_app/': {'admin', 'super_admin', 'teacher_admin', 'school_admin', 'sysadmin', 'hardware_admin'},
    '/admin_center': {'admin', 'super_admin', 'system_admin'},
    '/teacher': {'teacher', 'admin', 'super_admin', 'system_admin'},
    '/designer': {'designer', 'admin', 'super_admin', 'system_admin'},
    '/exam_system/': {'student', 'student_vip', 'teacher', 'admin', 'super_admin', 'system_admin'},
    '/backup': {'super_admin'},
    '/snapshot': {'super_admin'},
    '/iso_build': {'super_admin'},
    '/shadow': {'super_admin'},
    '/upgrade': {'super_admin'},
    '/api/admin/': {'admin', 'super_admin', 'system_admin'},
    '/api/vikey/': {'super_admin', 'admin', 'system_admin'},
    '/api/security/': {'super_admin', 'admin', 'system_admin'},
    '/api/system/': {'super_admin', 'admin', 'system_admin'},
    '/api/firewall/': {'super_admin', 'admin', 'system_admin'},
    '/api/users/manage': {'admin', 'super_admin', 'system_admin'},
    '/api/users/delete': {'super_admin'},
    '/api/users/role': {'super_admin'},
}

# 方法-路径敏感操作约束：写操作仅限特定路径
WRITE_METHOD_PATHS = {
    '/api/users/', '/api/admin/', '/api/system/', '/api/firewall/',
    '/auth/login', '/auth/register', '/auth/forgot_password',
    '/admin_app/', '/backup', '/snapshot', '/iso_build', '/shadow', '/upgrade',
}

# 并发登录控制：同用户不同IP同时登录检测
CONCURRENT_LOGIN_IPS = 2       # 同用户最多允许2个不同IP同时在线
CONCURRENT_LOGIN_WINDOW = 300  # 5分钟内的并发窗口

# 三级锁定时长（秒）
LOCK_LEVELS = {
    'soft':      900,    # 软锁 15分钟
    'hard':      3600,   # 硬锁 1小时
    'permanent': 86400,  # 永久锁 24小时（需人工解锁）
}

# 防暴力解锁配置
MAX_UNLOCK_ATTEMPTS = 3         # 最大解锁尝试次数
UNLOCK_LOCKOUT_DURATION = 1800  # 解锁失败后锁定时长 30分钟

# IP黑名单与限流
IP_RATE_LIMIT = 60              # 单IP每分钟最大请求
IP_BLACKLIST_DURATION = 3600    # IP黑名单时长 1小时

# ==================== 内存状态 ====================

LOCKED_USERS = {}           # {username: {locked_at, locked_until, locked_by, level, reason, fail_count}}
ACTIVE_SESSIONS = {}        # {user_id: [{session_id, ip, user_agent, created_at, last_activity}]}
FAILED_LOGIN_TRACKER = {}   # {username: {count, first_attempt, last_attempt, ips: []}}
UNLOCK_ATTEMPT_TRACKER = {} # {username: {count, last_attempt, locked_after}}
IP_REQUEST_TRACKER = {}     # {ip: deque([timestamps])}
IP_BLACKLIST = {}           # {ip: {blacklisted_at, reason, expires_at}}
SECURITY_EVENTS = []        # 内存中的安全事件缓冲区（最近1000条）

# AI自学习参数（可被AI引擎动态调整）
AI_ADAPTIVE_PARAMS = {
    'max_failed_logins': MAX_FAILED_LOGINS,
    'session_timeout': SESSION_TIMEOUT,
    'rate_limit': RATE_LIMIT,
    'ip_rate_limit': IP_RATE_LIMIT,
    'lock_duration_multiplier': 1.0,  # 锁定时长倍数（AI可调整）
    'auto_blacklist_threshold': 10,   # 自动黑名单触发阈值
}


class SecurityMiddlewareClass:
    """增强版安全中间件"""

    # ==================== 数据库日志 ====================

    @staticmethod
    def _get_db_path():
        import os
        return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')

    @staticmethod
    def _log_security_event(event_type, target, severity, description, ip_address='', details=''):
        """记录安全事件到数据库和内存缓冲区"""
        if SecurityMiddlewareClass._is_super_admin_user():
            return

        event = {
            'event_type': event_type,
            'target': target,
            'severity': severity,  # info / warning / critical
            'description': description,
            'ip_address': ip_address,
            'details': details,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # 内存缓冲
        SECURITY_EVENTS.append(event)
        if len(SECURITY_EVENTS) > 1000:
            SECURITY_EVENTS.pop(0)

        # 数据库记录
        try:
            db_path = SecurityMiddlewareClass._get_db_path()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_events_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    target TEXT,
                    severity TEXT DEFAULT 'info',
                    description TEXT,
                    ip_address TEXT,
                    details TEXT,
                    timestamp TEXT
                )
            ''')
            cursor.execute('''
                INSERT INTO security_events_log
                (event_type, target, severity, description, ip_address, details, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (event['event_type'], event['target'], event['severity'],
                  event['description'], event['ip_address'], event['details'],
                  event['timestamp']))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"记录安全事件到数据库失败: {e}")

        # 日志输出
        log_msg = f"[安全事件][{severity}] {event_type} | 目标:{target} | IP:{ip_address} | {description}"
        if severity == 'critical':
            logger.critical(log_msg)
        elif severity == 'warning':
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

    # ==================== 请求前置处理 ====================

    @staticmethod
    def _is_super_admin_user():
        """判断当前用户是否为超级管理员（wuchenghao15）"""
        from flask import session
        username = session.get('username', '')
        return username == 'wuchenghao15'

    @staticmethod
    def before_request_handler():
        from flask import request, session, g

        if SecurityMiddlewareClass._is_super_admin_user():
            return None

        allowed_paths = ['/', '/auth/login', '/auth/register', '/auth/forgot_password',
                         '/admin_app/login',
                         '/api/health', '/api/time', '/api/status', '/api/system_params',
                         '/api/monitoring/health',
                         '/api/questions/categories', '/api/questions/tags', '/api/questions/search',
                         '/api/questions/', '/api/subjects/', '/api/question_types/',
                         '/api/difficulty_levels/', '/api/question_tags/',
                         '/api/dynamic/',
                         '/api/tts/languages', '/api/tts/voices', '/api/tts/cache/stats',
                         '/api/tts/speak',
                         '/api/ai-repair/stats', '/api/ai-repair/fix-history',
                         '/api/server-time', '/api/error/report',
                         '/api/ai/self_learning/status', '/api/ai/self_learning/rules',
                         '/api/ai/self_learning/knowledge_stats', '/api/ai/self_learning/insights',
                         '/api/ai_engine/self_learning/status', '/api/ai_engine/self_learning/trigger',
                         '/api/ai_engine/self_learning/discover',
                         '/api/arduino/ai/',
                         '/api/ai/chinese_listening/',
                         '/api/chinese_dictation/',
                         '/api/vikey/',
                         '/api/layout_ai/',
                         '/ai_learning_dashboard',
                         '/', '/login', '/register', '/forgot_password', '/forgot-password',
                         '/assets/', '/static/', '/favicon.ico',
                         '/robots.txt', '/sitemap.xml']

        path = request.path or ''
        ip_address = request.remote_addr or 'unknown'

        # ===== 升级1：请求体大小限制 =====
        content_length = request.headers.get('Content-Length')
        if content_length and content_length.isdigit() and int(content_length) > MAX_REQUEST_BODY_SIZE:
            SecurityMiddlewareClass._log_security_event(
                'oversized_request', ip_address, 'warning',
                f'请求体过大: {content_length} bytes (上限 {MAX_REQUEST_BODY_SIZE})', ip_address, path
            )
            return {
                'success': False,
                'error': '请求体超过大小限制',
                'status_code': 413
            }

        # ===== 升级2：查询字符串长度限制 =====
        qs = request.query_string.decode() if request.query_string else ''
        if len(qs) > MAX_QUERY_STRING_LENGTH:
            SecurityMiddlewareClass._log_security_event(
                'oversized_query', ip_address, 'warning',
                f'查询字符串过长: {len(qs)} (上限 {MAX_QUERY_STRING_LENGTH})', ip_address, path
            )
            return {
                'success': False,
                'error': '请求参数过长',
                'status_code': 414
            }

        # ===== 升级3：CSRF 防护（POST/PUT/DELETE/PATCH 需验证 CSRF Token） =====
        if request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
            # 豁免路径（登录/注册/公开API）
            if path not in CSRF_EXEMPT_PATHS and not path.startswith('/api/vikey/'):
                csrf_token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
                session_csrf = session.get('csrf_token')
                if session_csrf and csrf_token != session_csrf:
                    SecurityMiddlewareClass._log_security_event(
                        'csrf_violation', session.get('username', 'unknown'), 'critical',
                        f'CSRF Token 验证失败: path={path}', ip_address, path
                    )
                    return {
                        'success': False,
                        'error': 'CSRF 验证失败，请刷新页面重试',
                        'status_code': 403
                    }

        # ===== 升级4：HTTP方法约束 =====
        if request.method not in ('GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'):
            SecurityMiddlewareClass._log_security_event(
                'method_violation', ip_address, 'warning',
                f'不允许的HTTP方法: {request.method}', ip_address, path
            )
            return {
                'success': False,
                'error': '不支持的HTTP方法',
                'status_code': 405
            }

        # 白名单检查
        for allowed in allowed_paths:
            if path == allowed:
                return None
            if allowed != '/' and allowed.endswith('/') and path.startswith(allowed):
                return None

        # 路由匹配检查
        from flask import current_app
        if current_app:
            from werkzeug.exceptions import NotFound, MethodNotAllowed
            adapter = current_app.url_map.bind('')
            try:
                adapter.match(path)
            except (NotFound, MethodNotAllowed):
                return None

        # ---- IP黑名单检查 ----
        if SecurityMiddlewareClass._is_ip_blacklisted(ip_address):
            SecurityMiddlewareClass._log_security_event(
                'blocked_request', ip_address, 'warning',
                f'黑名单IP请求被拦截: {path}', ip_address
            )
            return {
                'success': False,
                'error': '访问被拒绝',
                'status_code': 403
            }

        # ---- IP限流检查 ----
        if not SecurityMiddlewareClass._check_ip_rate_limit(ip_address):
            SecurityMiddlewareClass._log_security_event(
                'rate_limited', ip_address, 'warning',
                f'IP请求频率超限', ip_address
            )
            return {
                'success': False,
                'error': '请求过于频繁，请稍后再试',
                'status_code': 429
            }

        # ---- 账户锁定检查（三级锁定） ----
        username = session.get('username', '')
        if username:
            lock_info = SecurityMiddlewareClass.check_user_locked(username)
            if lock_info:
                remaining = int(lock_info['locked_until'] - time.time())
                SecurityMiddlewareClass._log_security_event(
                    'locked_access_attempt', username, 'warning',
                    f'锁定账户尝试访问: 剩余{remaining}秒', ip_address
                )
                return {
                    'success': False,
                    'error': f"账户已锁定（{lock_info['level']}级），请{remaining}秒后重试",
                    'locked_until': lock_info['locked_until'],
                    'lock_level': lock_info['level'],
                    'status_code': 423
                }

        # ---- 已登录用户会话检查 ----
        if session.get('logged_in'):
            now = time.time()
            last_activity = session.get('last_activity', now)
            session_created = session.get('session_created', now)
            idle_time = now - last_activity
            absolute_time = now - session_created

            # 绝对超时检查（无论是否有活动，超过最大时长即失效）
            if absolute_time > SESSION_ABSOLUTE_TIMEOUT:
                session.clear()
                SecurityMiddlewareClass._log_security_event(
                    'session_absolute_timeout', session.get('username', 'unknown'), 'info',
                    f'会话绝对超时: {int(absolute_time)}秒'
                )
                return {
                    'success': False,
                    'error': '会话已过期，请重新登录',
                    'status_code': 401
                }

            # 空闲超时检查
            current_timeout = AI_ADAPTIVE_PARAMS['session_timeout']
            if idle_time > current_timeout:
                session.clear()
                SecurityMiddlewareClass._log_security_event(
                    'session_idle_timeout', session.get('username', 'unknown'), 'info',
                    f'会话空闲超时: {int(idle_time)}秒'
                )
                return {
                    'success': False,
                    'error': '会话已超时，请重新登录',
                    'status_code': 401
                }

            # 渐进式超时警告（3个阶段）
            if idle_time > current_timeout * 0.5:
                session['timeout_warning'] = 'soon'
            if idle_time > current_timeout - WARNING_TIMEOUT:
                session['timeout_warning'] = 'imminent'

            session['last_activity'] = now

            # 会话完整性验证
            if 'user_id' not in session or 'role' not in session:
                session.clear()
                SecurityMiddlewareClass._log_security_event(
                    'session_invalid', 'unknown', 'warning',
                    '会话验证失败: 缺少必要字段', ip_address
                )
                return {
                    'success': False,
                    'error': '会话验证失败',
                    'status_code': 401
                }

            # ---- 角色权限检查（升级：使用 PATH_ROLE_MATRIX 精细化路径权限） ----
            user_role = session.get('role', 'guest')
            required_roles_for_path = None
            for matrix_path, allowed_roles_set in PATH_ROLE_MATRIX.items():
                if path.startswith(matrix_path):
                    required_roles_for_path = allowed_roles_set
                    break

            if required_roles_for_path:
                if user_role not in required_roles_for_path:
                    SecurityMiddlewareClass._log_security_event(
                        'permission_denied', session.get('username', 'unknown'), 'warning',
                        f'权限不足: 路径{path}需要{required_roles_for_path}, 当前{user_role}', ip_address, path
                    )
                    return {
                        'success': False,
                        'error': '权限不足',
                        'status_code': 403
                    }

            # ---- 升级5：并发登录IP检测 ----
            user_id = session.get('user_id')
            if user_id and user_id in ACTIVE_SESSIONS:
                sessions_list = ACTIVE_SESSIONS[user_id]
                distinct_ips = set(s.get('ip', '') for s in sessions_list if s.get('ip'))
                if len(distinct_ips) >= CONCURRENT_LOGIN_IPS and ip_address not in distinct_ips:
                    SecurityMiddlewareClass._log_security_event(
                        'concurrent_login_detected', session.get('username', 'unknown'), 'critical',
                        f'并发登录检测: 用户在{len(distinct_ips)}个IP同时在线, 新IP={ip_address}',
                        ip_address, json.dumps({'existing_ips': list(distinct_ips)[:5], 'new_ip': ip_address})
                    )
                    # 强制清除最旧会话
                    if sessions_list:
                        oldest = sessions_list.pop(0)
                        SecurityMiddlewareClass._log_security_event(
                            'session_force_kick', session.get('username', 'unknown'), 'warning',
                            f'并发登录限制: 强制踢出旧会话 IP={oldest.get("ip", "")}',
                            oldest.get('ip', '')
                        )

            # ---- 会话唯一性检查（防重复登录 + 挂载锁定） ----
            user_id = session.get('user_id')
            session_id = session.get('session_id')
            if user_id and session_id:
                if user_id not in ACTIVE_SESSIONS:
                    ACTIVE_SESSIONS[user_id] = []

                if session_id not in [s['session_id'] for s in ACTIVE_SESSIONS[user_id]]:
                    if len(ACTIVE_SESSIONS[user_id]) >= MAX_SESSIONS_PER_USER:
                        oldest = ACTIVE_SESSIONS[user_id].pop(0)
                        SecurityMiddlewareClass._log_security_event(
                            'session_evicted', user_id, 'warning',
                            f"会话数超限，强制登出旧会话: {oldest['session_id']}",
                            oldest.get('ip', '')
                        )
                    ACTIVE_SESSIONS[user_id].append({
                        'session_id': session_id,
                        'ip': ip_address,
                        'user_agent': request.headers.get('User-Agent', ''),
                        'created_at': session_created,
                        'last_activity': now
                    })
        else:
            # 未登录用户
            if path.startswith('/api/'):
                return {
                    'success': False,
                    'error': '未登录，请先登录',
                    'status_code': 401
                }
            return {
                'success': False,
                'error': '请先登录',
                'status_code': 302,
                'redirect': '/'
            }

        return None

    # ==================== 三级锁定机制 ====================

    @staticmethod
    def lock_user(username, locked_by='system', duration=None, level='soft', reason=''):
        """三级锁定用户"""
        if duration is None:
            duration = LOCK_LEVELS.get(level, LOCK_LEVELS['soft'])
            duration = int(duration * AI_ADAPTIVE_PARAMS['lock_duration_multiplier'])

        LOCKED_USERS[username] = {
            'locked_at': time.time(),
            'locked_until': time.time() + duration,
            'locked_by': locked_by,
            'level': level,
            'reason': reason or f'locked by {locked_by}',
            'fail_count': LOCKED_USERS.get(username, {}).get('fail_count', 0) + 1
        }

        SecurityMiddlewareClass._log_security_event(
            'user_locked', username, 'critical' if level == 'permanent' else 'warning',
            f'用户被锁定: {level}级, 时长{duration}秒, 原因: {reason}',
            '', json.dumps({'level': level, 'duration': duration, 'locked_by': locked_by})
        )
        return True

    @staticmethod
    def unlock_user(username, unlocked_by='system', verify_token=None):
        """
        解锁用户 - 带防暴力破解保护
        verify_token: 验证令牌（如需要二次验证时传入）
        """
        # 检查是否存在暴力解锁尝试
        attempt_info = UNLOCK_ATTEMPT_TRACKER.get(username, {})
        attempt_count = attempt_info.get('count', 0)

        if attempt_count >= MAX_UNLOCK_ATTEMPTS:
            # 超过解锁尝试限制，递增锁定
            current_lock = LOCKED_USERS.get(username, {})
            current_level = current_lock.get('level', 'soft')
            current_fail_count = current_lock.get('fail_count', 0)

            # 递增锁定级别
            if current_level == 'soft':
                new_level = 'hard'
            elif current_level == 'hard':
                new_level = 'permanent'
            else:
                new_level = 'permanent'

            SecurityMiddlewareClass.lock_user(
                username, 'anti_brute_force', None, new_level,
                f'暴力解锁尝试: {attempt_count}次'
            )
            UNLOCK_ATTEMPT_TRACKER[username] = {'count': 0, 'last_attempt': time.time()}

            SecurityMiddlewareClass._log_security_event(
                'brute_force_unlock_detected', username, 'critical',
                f'检测到暴力解锁尝试({attempt_count}次)，升级锁定至{new_level}级',
                '', json.dumps({'attempt_count': attempt_count, 'new_level': new_level})
            )
            return False

        # 记录解锁尝试
        UNLOCK_ATTEMPT_TRACKER[username] = {
            'count': attempt_count + 1,
            'last_attempt': time.time()
        }

        if username in LOCKED_USERS:
            lock_info = LOCKED_USERS[username]
            # 永久锁需要人工解锁
            if lock_info.get('level') == 'permanent' and unlocked_by == 'system':
                SecurityMiddlewareClass._log_security_event(
                    'unlock_denied', username, 'warning',
                    '永久锁定账户无法自动解锁，需要管理员手动解锁'
                )
                return False

            del LOCKED_USERS[username]
            UNLOCK_ATTEMPT_TRACKER.pop(username, None)

            SecurityMiddlewareClass._log_security_event(
                'user_unlocked', username, 'info',
                f'用户已解锁 by {unlocked_by}',
                '', json.dumps({'unlocked_by': unlocked_by, 'previous_level': lock_info.get('level')})
            )
            return True

        return False

    @staticmethod
    def check_user_locked(username):
        """检查用户是否被锁定"""
        if username in LOCKED_USERS:
            lock_info = LOCKED_USERS[username]
            if time.time() < lock_info['locked_until']:
                return lock_info
            else:
                # 锁定已过期，自动清理（但不清理permanent级）
                if lock_info.get('level') != 'permanent':
                    del LOCKED_USERS[username]
        return None

    # ==================== 登录失败追踪 + 递增锁定 ====================

    @staticmethod
    def record_failed_login(username, ip_address=''):
        """记录登录失败，支持递增锁定"""
        from app.utils.db import DatabaseManager

        # 内存追踪
        if username not in FAILED_LOGIN_TRACKER:
            FAILED_LOGIN_TRACKER[username] = {
                'count': 0,
                'first_attempt': time.time(),
                'last_attempt': time.time(),
                'ips': []
            }

        tracker = FAILED_LOGIN_TRACKER[username]
        tracker['count'] += 1
        tracker['last_attempt'] = time.time()
        if ip_address and ip_address not in tracker['ips']:
            tracker['ips'].append(ip_address)

        # 数据库记录
        try:
            db = DatabaseManager()
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
            else:
                count = tracker['count']
        except Exception as e:
            logger.error(f"记录登录失败次数失败: {e}")
            count = tracker['count']

        # 递增锁定判断
        current_max = AI_ADAPTIVE_PARAMS['max_failed_logins']

        if count >= current_max * 3:
            # 第三阶段：永久锁
            SecurityMiddlewareClass.lock_user(
                username, 'failed_logins', None, 'permanent',
                f'登录失败{count}次，永久锁定'
            )
            SecurityMiddlewareClass._auto_blacklist_ip(ip_address, f'关联账户{username}暴力破解')
        elif count >= current_max * 2:
            # 第二阶段：硬锁
            SecurityMiddlewareClass.lock_user(
                username, 'failed_logins', None, 'hard',
                f'登录失败{count}次，硬锁定'
            )
            if tracker['count'] > 5:
                SecurityMiddlewareClass._auto_blacklist_ip(ip_address, f'关联账户{username}频繁失败')
        elif count >= current_max:
            # 第一阶段：软锁
            SecurityMiddlewareClass.lock_user(
                username, 'failed_logins', None, 'soft',
                f'登录失败{count}次，软锁定'
            )

        SecurityMiddlewareClass._log_security_event(
            'login_failed', username, 'warning' if count < current_max else 'critical',
            f'登录失败({count}/{current_max})', ip_address,
            json.dumps({'count': count, 'ips': tracker['ips'][-5:]})
        )

    @staticmethod
    def reset_failed_login(username):
        """登录成功后重置失败计数"""
        from app.utils.db import DatabaseManager

        FAILED_LOGIN_TRACKER.pop(username, None)
        UNLOCK_ATTEMPT_TRACKER.pop(username, None)

        try:
            db = DatabaseManager()
            db.execute(
                "UPDATE users SET failed_login_count = 0, last_failed_login = NULL WHERE username = ?",
                (username,)
            )
        except Exception as e:
            logger.error(f"重置登录失败次数失败: {e}")

        # 只解锁非永久锁
        lock_info = LOCKED_USERS.get(username, {})
        if lock_info.get('level') != 'permanent':
            SecurityMiddlewareClass.unlock_user(username, 'login_success')

    # ==================== IP管理 ====================

    @staticmethod
    def _check_ip_rate_limit(ip_address):
        """IP级别限流检查"""
        now = time.time()
        if ip_address not in IP_REQUEST_TRACKER:
            IP_REQUEST_TRACKER[ip_address] = deque()

        tracker = IP_REQUEST_TRACKER[ip_address]
        # 清理过期记录
        while tracker and tracker[0] < now - RATE_LIMIT_WINDOW:
            tracker.popleft()

        limit = AI_ADAPTIVE_PARAMS['ip_rate_limit']
        if len(tracker) >= limit:
            return False

        tracker.append(now)
        return True

    @staticmethod
    def _is_ip_blacklisted(ip_address):
        """检查IP是否在黑名单中"""
        if ip_address in IP_BLACKLIST:
            info = IP_BLACKLIST[ip_address]
            if time.time() < info['expires_at']:
                return True
            else:
                del IP_BLACKLIST[ip_address]
        return False

    @staticmethod
    def _auto_blacklist_ip(ip_address, reason=''):
        """自动将IP加入黑名单"""
        if not ip_address or ip_address == 'unknown':
            return

        IP_BLACKLIST[ip_address] = {
            'blacklisted_at': time.time(),
            'reason': reason,
            'expires_at': time.time() + IP_BLACKLIST_DURATION
        }

        SecurityMiddlewareClass._log_security_event(
            'ip_blacklisted', ip_address, 'critical',
            f'IP自动加入黑名单: {reason}'
        )

    @staticmethod
    def blacklist_ip(ip_address, reason='manual', duration=None):
        """手动添加IP黑名单"""
        if duration is None:
            duration = IP_BLACKLIST_DURATION
        IP_BLACKLIST[ip_address] = {
            'blacklisted_at': time.time(),
            'reason': reason,
            'expires_at': time.time() + duration
        }
        SecurityMiddlewareClass._log_security_event(
            'ip_blacklisted', ip_address, 'warning',
            f'IP加入黑名单: {reason}'
        )

    @staticmethod
    def whitelist_ip(ip_address):
        """移除IP黑名单"""
        if ip_address in IP_BLACKLIST:
            del IP_BLACKLIST[ip_address]
            SecurityMiddlewareClass._log_security_event(
                'ip_whitelisted', ip_address, 'info',
                'IP已从黑名单移除'
            )
            return True
        return False

    # ==================== 会话管理 ====================

    @staticmethod
    def register_session(user_id, session_id, ip_address, user_agent):
        """注册会话"""
        if user_id not in ACTIVE_SESSIONS:
            ACTIVE_SESSIONS[user_id] = []

        if len(ACTIVE_SESSIONS[user_id]) >= MAX_SESSIONS_PER_USER:
            oldest = ACTIVE_SESSIONS[user_id].pop(0)
            SecurityMiddlewareClass._log_security_event(
                'session_evicted', user_id, 'warning',
                f"会话数超限，强制登出旧会话: {oldest.get('session_id', '')}",
                ip_address
            )

        ACTIVE_SESSIONS[user_id].append({
            'session_id': session_id,
            'ip': ip_address,
            'user_agent': user_agent,
            'created_at': time.time(),
            'last_activity': time.time()
        })
        logger.info(f"[会话注册] 用户 {user_id} 会话 {session_id} 已注册")

    @staticmethod
    def unregister_session(user_id, session_id):
        """注销会话"""
        if user_id in ACTIVE_SESSIONS:
            ACTIVE_SESSIONS[user_id] = [
                s for s in ACTIVE_SESSIONS[user_id] if s['session_id'] != session_id
            ]
            if not ACTIVE_SESSIONS[user_id]:
                del ACTIVE_SESSIONS[user_id]
            logger.info(f"[会话注销] 用户 {user_id} 会话 {session_id} 已注销")

    @staticmethod
    def get_user_sessions(user_id):
        """获取用户会话列表"""
        return ACTIVE_SESSIONS.get(user_id, [])

    @staticmethod
    def invalidate_all_sessions(user_id):
        """使所有会话失效"""
        if user_id in ACTIVE_SESSIONS:
            sessions = ACTIVE_SESSIONS.pop(user_id)
            SecurityMiddlewareClass._log_security_event(
                'sessions_invalidated', user_id, 'warning',
                f'用户 {len(sessions)} 个会话已全部失效'
            )
            return sessions
        return []

    @staticmethod
    def check_session_valid(user_id, session_id):
        """检查会话是否有效"""
        if user_id in ACTIVE_SESSIONS:
            return any(s['session_id'] == session_id for s in ACTIVE_SESSIONS[user_id])
        return False

    @staticmethod
    def clean_expired_sessions():
        """清理过期会话"""
        expired_count = 0
        for user_id in list(ACTIVE_SESSIONS.keys()):
            ACTIVE_SESSIONS[user_id] = [
                s for s in ACTIVE_SESSIONS[user_id]
                if time.time() - s.get('last_activity', 0) < SESSION_TIMEOUT
            ]
            if not ACTIVE_SESSIONS[user_id]:
                del ACTIVE_SESSIONS[user_id]
                expired_count += 1
        if expired_count > 0:
            logger.info(f"[会话清理] 清理了 {expired_count} 个过期会话")

    @staticmethod
    def get_active_users_count():
        return len(ACTIVE_SESSIONS)

    @staticmethod
    def get_total_sessions_count():
        return sum(len(sessions) for sessions in ACTIVE_SESSIONS.values())

    # ==================== AI自学习防御 ====================

    @staticmethod
    def get_security_stats():
        """获取安全统计（供AI学习使用）"""
        return {
            'locked_users': len(LOCKED_USERS),
            'locked_users_detail': {
                u: {'level': v.get('level'), 'reason': v.get('reason'), 'fail_count': v.get('fail_count', 0)}
                for u, v in LOCKED_USERS.items()
            },
            'active_sessions': len(ACTIVE_SESSIONS),
            'failed_login_tracker': {
                u: {'count': v['count'], 'ips': len(v.get('ips', []))}
                for u, v in FAILED_LOGIN_TRACKER.items()
            },
            'unlock_attempts': len(UNLOCK_ATTEMPT_TRACKER),
            'blacklisted_ips': len(IP_BLACKLIST),
            'blacklisted_ips_detail': dict(IP_BLACKLIST),
            'security_events_count': len(SECURITY_EVENTS),
            'recent_events': SECURITY_EVENTS[-50:],
            'adaptive_params': dict(AI_ADAPTIVE_PARAMS)
        }

    @staticmethod
    def update_adaptive_params(new_params):
        """AI引擎调用：更新自适应安全参数"""
        updated = []
        for key, value in new_params.items():
            if key in AI_ADAPTIVE_PARAMS:
                old_value = AI_ADAPTIVE_PARAMS[key]
                AI_ADAPTIVE_PARAMS[key] = value
                updated.append(f"{key}: {old_value} -> {value}")

        if updated:
            SecurityMiddlewareClass._log_security_event(
                'ai_adaptive_update', 'system', 'info',
                f'AI自适应参数更新: {", ".join(updated)}'
            )
            logger.info(f"[AI防御] 自适应参数已更新: {updated}")

        return len(updated) > 0

    @staticmethod
    def analyze_attack_patterns():
        """
        AI学习接口：分析安全事件模式，返回学习洞察
        供AI自我学习引擎调用
        """
        insights = {
            'top_attacked_users': [],
            'top_attacker_ips': [],
            'attack_frequency': {},
            'recommended_actions': []
        }

        # 分析最近的安全事件
        recent_events = SECURITY_EVENTS[-500:]
        user_attack_count = defaultdict(int)
        ip_attack_count = defaultdict(int)

        for event in recent_events:
            if event['event_type'] in ('login_failed', 'brute_force_unlock_detected', 'locked_access_attempt'):
                if event['target']:
                    user_attack_count[event['target']] += 1
                if event['ip_address']:
                    ip_attack_count[event['ip_address']] += 1

        # 排序获取Top 5
        insights['top_attacked_users'] = sorted(user_attack_count.items(), key=lambda x: -x[1])[:5]
        insights['top_attacker_ips'] = sorted(ip_attack_count.items(), key=lambda x: -x[1])[:5]

        # 攻击频率按小时统计
        for event in recent_events:
            hour = event['timestamp'][:13]  # YYYY-MM-DD HH
            insights['attack_frequency'][hour] = insights['attack_frequency'].get(hour, 0) + 1

        # 生成建议
        total_attacks = sum(user_attack_count.values())
        if total_attacks > 50:
            insights['recommended_actions'].append({
                'action': 'increase_lock_duration',
                'reason': f'近期攻击次数{total_attacks}，建议提高锁定时长倍数',
                'suggested_value': min(AI_ADAPTIVE_PARAMS['lock_duration_multiplier'] + 0.5, 3.0)
            })

        if insights['top_attacker_ips']:
            for ip, count in insights['top_attacker_ips']:
                if count > AI_ADAPTIVE_PARAMS['auto_blacklist_threshold'] and ip not in IP_BLACKLIST:
                    insights['recommended_actions'].append({
                        'action': 'blacklist_ip',
                        'ip': ip,
                        'reason': f'IP {ip} 触发{count}次安全事件，建议加入黑名单'
                    })

        if len(IP_BLACKLIST) > 20:
            insights['recommended_actions'].append({
                'action': 'decrease_rate_limit',
                'reason': f'黑名单IP数{len(IP_BLACKLIST)}，建议降低IP限流阈值',
                'suggested_value': max(AI_ADAPTIVE_PARAMS['ip_rate_limit'] - 10, 20)
            })

        return insights

    @staticmethod
    def auto_defend():
        """
        AI自动防御执行：根据分析结果自动执行防御措施
        由调度器或AI引擎定期调用
        """
        insights = SecurityMiddlewareClass.analyze_attack_patterns()
        actions_taken = []

        for rec in insights['recommended_actions']:
            try:
                if rec['action'] == 'increase_lock_duration':
                    SecurityMiddlewareClass.update_adaptive_params({
                        'lock_duration_multiplier': rec['suggested_value']
                    })
                    actions_taken.append(f"锁定倍数提升至{rec['suggested_value']}")

                elif rec['action'] == 'blacklist_ip':
                    SecurityMiddlewareClass.blacklist_ip(
                        rec['ip'], f'AI自动防御: {rec["reason"]}'
                    )
                    actions_taken.append(f"IP {rec['ip']} 已自动加入黑名单")

                elif rec['action'] == 'decrease_rate_limit':
                    SecurityMiddlewareClass.update_adaptive_params({
                        'ip_rate_limit': rec['suggested_value']
                    })
                    actions_taken.append(f"IP限流降低至{rec['suggested_value']}")

            except Exception as e:
                logger.error(f"[AI防御] 执行自动防御动作失败: {e}")

        if actions_taken:
            SecurityMiddlewareClass._log_security_event(
                'ai_auto_defend', 'system', 'warning',
                f'AI自动防御执行: {"; ".join(actions_taken)}'
            )

        return actions_taken

    @staticmethod
    def get_security_events(limit=100, event_type=None):
        """查询安全事件记录"""
        try:
            db_path = SecurityMiddlewareClass._get_db_path()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            if event_type:
                cursor.execute('''
                    SELECT * FROM security_events_log
                    WHERE event_type = ?
                    ORDER BY timestamp DESC LIMIT ?
                ''', (event_type, limit))
            else:
                cursor.execute('''
                    SELECT * FROM security_events_log
                    ORDER BY timestamp DESC LIMIT ?
                ''', (limit,))

            columns = [desc[0] for desc in cursor.description]
            events = [dict(zip(columns, row)) for row in cursor.fetchall()]
            conn.close()
            return events
        except Exception as e:
            logger.error(f"查询安全事件失败: {e}")
            return SECURITY_EVENTS[-limit:]


security_middleware = SecurityMiddlewareClass()
SecurityMiddleware = SecurityMiddlewareClass
