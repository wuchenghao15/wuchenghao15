#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路由权限约束引擎
Route Permission Constraint Engine

处理路由逻辑和权限约束的相互作用：
1. 路由级别权限约束（rule_constraints 表）
2. 角色访问控制规则（access_control_rules 表）
3. 业务规则动态约束（system_rules 表）
4. 实时会话和资源限制
5. 约束冲突检测和解决
"""
import sqlite3
import json
import re
import time
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, List, Tuple, Optional, Any
from flask import request, session, jsonify, g

logger = logging.getLogger('route_constraint_engine')

DB_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'


class RouteConstraintEngine:
    """路由权限约束引擎 - 路由逻辑与权限约束的交互处理"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._cache = {}
        self._cache_ttl = 30  # 缓存30秒

    def get_db(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ==================== 路由约束检查 ====================

    def check_route_constraints(self, path: str, method: str, user_context: Dict) -> Dict:
        """
        检查路由的完整约束链

        返回：
        {
            'allowed': bool,
            'reason': str,
            'matched_constraints': list,
            'access_control': dict,
            'business_rules': dict,
            'rate_limit': dict,
            'time_window': dict
        }
        """
        result = {
            'allowed': True,
            'reason': None,
            'matched_constraints': [],
            'access_control': None,
            'business_rules': {},
            'rate_limit': None,
            'time_window': None
        }

        try:
            # 1. 检查访问控制规则（角色 → 路径 → 方法）
            acr = self._check_access_control(path, method, user_context.get('role'))
            result['access_control'] = acr
            if not acr['allowed']:
                result['allowed'] = False
                result['reason'] = f"access_control: {acr['reason']}"
                return result

            # 2. 检查约束规则（rule_constraints）
            constraints = self._get_applicable_constraints(path, user_context)
            for constraint in constraints:
                check = self._evaluate_constraint(constraint, user_context, path)
                result['matched_constraints'].append({
                    'key': constraint['constraint_key'],
                    'name': constraint['constraint_name'],
                    'result': check
                })
                if not check['passed']:
                    result['allowed'] = False
                    result['reason'] = f"constraint: {constraint['constraint_key']} - {check['reason']}"
                    return result

            # 3. 检查业务规则（system_rules）
            business = self._check_business_rules(path, method, user_context)
            result['business_rules'] = business
            if not business['allowed']:
                result['allowed'] = False
                result['reason'] = f"business_rule: {business['reason']}"
                return result

            # 4. 检查速率限制
            rate = self._check_rate_limit(path, user_context)
            result['rate_limit'] = rate
            if not rate['allowed']:
                result['allowed'] = False
                result['reason'] = f"rate_limit: {rate['reason']}"
                return result

            # 5. 检查时间窗口
            time_window = self._check_time_window(path)
            result['time_window'] = time_window
            if not time_window['allowed']:
                result['allowed'] = False
                result['reason'] = f"time_window: {time_window['reason']}"
                return result

        except Exception as e:
            logger.error(f"约束检查失败: {e}")
            # 出错时默认拒绝（fail-closed）
            result['allowed'] = False
            result['reason'] = f"engine_error: {str(e)}"

        return result

    def _check_access_control(self, path: str, method: str, role: str) -> Dict:
        """检查访问控制规则"""
        cache_key = f"ac_{path}_{method}_{role}"
        if cache_key in self._cache:
            cached, ts = self._cache[cache_key]
            if time.time() - ts < self._cache_ttl:
                return cached

        try:
            conn = self.get_db()
            cursor = conn.cursor()

            # 匹配路径规则
            cursor.execute("""
                SELECT * FROM access_control_rules
                WHERE is_active = 1
                ORDER BY priority ASC
            """)
            rules = [dict(row) for row in cursor.fetchall()]

            matched_rule = None
            for rule in rules:
                if self._match_path(rule['resource_path'], path):
                    # 检查角色匹配
                    rule_role = rule['role_name']
                    if rule_role == role or self._role_includes(rule_role, role):
                        # 检查方法匹配
                        try:
                            allowed_methods = json.loads(rule['allowed_methods'] or '[]')
                        except Exception:
                            allowed_methods = []
                        if not allowed_methods or method.upper() in [m.upper() for m in allowed_methods]:
                            matched_rule = rule
                            break

            conn.close()

            if matched_rule:
                result = {
                    'allowed': True,
                    'reason': 'matched',
                    'rule_id': matched_rule['rule_id'],
                    'role': matched_rule['role_name'],
                    'path_pattern': matched_rule['resource_path']
                }
            else:
                # 没有匹配的规则时，guest/student角色默认拒绝受保护路径
                protected_prefixes = ['/api/admin', '/api/settings', '/api/hardware', '/api/repair',
                                     '/api/optimizer', '/dashboard', '/settings', '/admin']
                is_protected = any(path.startswith(p) for p in protected_prefixes)
                if is_protected and role in ['guest', None]:
                    result = {'allowed': False, 'reason': 'no_rule_matched_guest'}
                else:
                    result = {'allowed': True, 'reason': 'no_rule_required'}

            self._cache[cache_key] = (result, time.time())
            return result

        except Exception as e:
            logger.error(f"访问控制检查失败: {e}")
            return {'allowed': True, 'reason': 'check_error'}

    def _match_path(self, pattern: str, path: str) -> bool:
        """路径模式匹配（支持 * 通配符）"""
        if not pattern:
            return False
        # 将通配符 * 转换为正则
        regex = re.escape(pattern).replace(r'\*', '.*')
        return bool(re.match(f'^{regex}$', path))

    def _role_includes(self, rule_role: str, user_role: str) -> bool:
        """检查用户角色是否包含在规则角色中（基于等级体系）"""
        hierarchy = {
            'guest': 0, 'student': 1, 'designer': 1,
            'admin': 3, 'super_admin': 4, 'hardware_admin': 5,
            'hardware_vikey_admin': 5
        }
        rule_level = hierarchy.get(rule_role, 0)
        user_level = hierarchy.get(user_role, 0)
        return user_level >= rule_level

    def _get_applicable_constraints(self, path: str, user_context: Dict) -> List[Dict]:
        """获取适用于当前路径的约束"""
        try:
            conn = self.get_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM rule_constraints
                WHERE is_active = 1
                ORDER BY priority ASC
            """)
            all_constraints = [dict(row) for row in cursor.fetchall()]
            conn.close()

            # 过滤适用的约束
            applicable = []
            for c in all_constraints:
                apply_to = c.get('apply_to', '') or ''
                if not apply_to or self._match_constraint_apply(apply_to, path, user_context):
                    applicable.append(c)

            return applicable
        except Exception as e:
            logger.error(f"获取约束失败: {e}")
            return []

    def _match_constraint_apply(self, apply_to: str, path: str, user_context: Dict) -> bool:
        """匹配约束的应用范围"""
        if not apply_to:
            return True

        patterns = [p.strip() for p in apply_to.split(',')]
        for p in patterns:
            if p == 'all':
                return True
            if self._match_path(p, path):
                return True
            # 特殊场景匹配
            if p == 'user_registration' and '/api/auth/register' in path:
                return True
            if p == 'session_management' and '/api/auth/' in path:
                return True
            if p == 'system_monitoring' and '/api/monitor' in path:
                return True
            if p == 'admin_operations' and '/api/admin/' in path:
                return True

        return False

    def _evaluate_constraint(self, constraint: Dict, user_context: Dict, path: str) -> Dict:
        """评估约束条件"""
        try:
            expression = constraint.get('rule_expression', '') or ''
            constraint_key = constraint.get('constraint_key', '')

            # 内置约束处理
            if constraint_key == 'sys_max_users':
                return self._check_max_users(constraint, user_context)
            elif constraint_key == 'sys_max_sessions':
                return self._check_max_sessions(constraint, user_context)
            elif constraint_key == 'sys_memory_limit':
                return self._check_memory_limit(constraint, user_context)
            elif constraint_key == 'sec_login_max_attempts':
                return self._check_login_attempts(constraint, user_context)
            elif constraint_key == 'sec_lock_duration':
                return self._check_account_locked(constraint, user_context)
            elif constraint_key == 'sec_password_min_length':
                return self._check_password_strength(constraint, user_context, path)
            else:
                # 默认通过
                return {'passed': True, 'reason': 'no_evaluator'}
        except Exception as e:
            logger.error(f"评估约束失败: {e}")
            return {'passed': True, 'reason': f'eval_error: {e}'}

    def _check_max_users(self, constraint: Dict, user_context: Dict) -> Dict:
        """检查最大用户数限制"""
        try:
            conn = self.get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            current = cursor.fetchone()[0]
            conn.close()
            max_users = int(constraint.get('constraint_value', 1000) or 1000)
            if current >= max_users:
                return {'passed': False, 'reason': f'用户数已达上限 {max_users}', 'current': current, 'max': max_users}
            return {'passed': True, 'reason': 'within_limit', 'current': current, 'max': max_users}
        except Exception:
            return {'passed': True, 'reason': 'check_failed'}

    def _check_max_sessions(self, constraint: Dict, user_context: Dict) -> Dict:
        """检查最大并发会话数"""
        try:
            conn = self.get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM auth_sessions WHERE is_active = 1 AND expires_at > datetime('now')")
            current = cursor.fetchone()[0]
            conn.close()
            max_sessions = int(constraint.get('constraint_value', 100) or 100)
            if current >= max_sessions:
                return {'passed': False, 'reason': f'并发会话数已达上限 {max_sessions}'}
            return {'passed': True, 'reason': 'within_limit'}
        except Exception:
            return {'passed': True, 'reason': 'check_failed'}

    def _check_memory_limit(self, constraint: Dict, user_context: Dict) -> Dict:
        """检查内存使用限制（仅监控，不阻断）"""
        try:
            import psutil
            mem = psutil.virtual_memory()
            limit = int(constraint.get('constraint_value', 90) or 90)
            if mem.percent >= limit:
                return {'passed': False, 'reason': f'内存使用率 {mem.percent}% 超过限制 {limit}%'}
            return {'passed': True, 'reason': 'within_limit', 'current': mem.percent}
        except ImportError:
            return {'passed': True, 'reason': 'psutil_unavailable'}

    def _check_login_attempts(self, constraint: Dict, user_context: Dict) -> Dict:
        """检查登录尝试次数"""
        if '/api/auth/login' not in request.path:
            return {'passed': True, 'reason': 'not_login_endpoint'}

        ip = request.remote_addr
        try:
            conn = self.get_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM auth_failed_logins
                WHERE ip_address = ? AND created_at > datetime('now', '-15 minutes')
            """, (ip,))
            attempts = cursor.fetchone()[0]
            conn.close()
            max_attempts = int(constraint.get('constraint_value', 5) or 5)
            if attempts >= max_attempts:
                return {'passed': False, 'reason': f'IP {ip} 登录失败次数过多'}
            return {'passed': True, 'reason': 'within_limit', 'attempts': attempts}
        except Exception:
            return {'passed': True, 'reason': 'check_failed'}

    def _check_account_locked(self, constraint: Dict, user_context: Dict) -> Dict:
        """检查账户是否被锁定"""
        if '/api/auth/login' not in request.path:
            return {'passed': True, 'reason': 'not_login_endpoint'}

        data = request.get_json(silent=True) or {}
        username = data.get('username', '')
        if not username:
            return {'passed': True, 'reason': 'no_username'}

        try:
            conn = self.get_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT locked_until FROM users WHERE username = ? AND locked_until > datetime('now')
            """, (username,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return {'passed': False, 'reason': f'账户已锁定至 {row["locked_until"]}'}
            return {'passed': True, 'reason': 'not_locked'}
        except Exception:
            return {'passed': True, 'reason': 'check_failed'}

    def _check_password_strength(self, constraint: Dict, user_context: Dict, path: str) -> Dict:
        """检查密码强度"""
        if '/api/auth/register' not in path and '/api/auth/change-password' not in path:
            return {'passed': True, 'reason': 'not_password_endpoint'}

        data = request.get_json(silent=True) or {}
        password = data.get('password', '')
        min_length = int(constraint.get('constraint_value', 6) or 6)
        if len(password) < min_length:
            return {'passed': False, 'reason': f'密码长度不足 {min_length} 位'}
        return {'passed': True, 'reason': 'strength_ok'}

    def _check_business_rules(self, path: str, method: str, user_context: Dict) -> Dict:
        """检查业务规则"""
        try:
            conn = self.get_db()
            cursor = conn.cursor()

            # 维护模式检查
            cursor.execute("SELECT rule_value FROM system_rules WHERE rule_code = 'SYS_MAINTENANCE_MODE' AND is_active = 1")
            row = cursor.fetchone()
            if row and str(row['rule_value']).lower() == 'true':
                role = user_context.get('role', 'guest')
                if role not in ['super_admin', 'hardware_admin', 'hardware_vikey_admin']:
                    conn.close()
                    return {'allowed': False, 'reason': '系统维护中'}

            # 硬件认证必需检查
            cursor.execute("SELECT rule_value FROM system_rules WHERE rule_code = 'HW_AUTH_REQUIRED' AND is_active = 1")
            row = cursor.fetchone()
            if row and str(row['rule_value']).lower() == 'true':
                if '/api/hardware' in path or '/api/admin/hardware' in path:
                    if not session.get('hardware_session_id'):
                        conn.close()
                        return {'allowed': False, 'reason': '需要硬件加密狗认证'}

            conn.close()
            return {'allowed': True, 'reason': 'business_rules_passed'}
        except Exception as e:
            logger.error(f"业务规则检查失败: {e}")
            return {'allowed': True, 'reason': 'check_error'}

    def _check_rate_limit(self, path: str, user_context: Dict) -> Dict:
        """检查速率限制（基于规则或默认）"""
        try:
            conn = self.get_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT rule_value FROM system_rules
                WHERE rule_code = 'API_RATE_LIMIT' AND is_active = 1
            """)
            row = cursor.fetchone()
            conn.close()

            if not row:
                return {'allowed': True, 'reason': 'no_limit_configured'}

            try:
                limit = int(row['rule_value'])
            except Exception:
                return {'allowed': True, 'reason': 'invalid_limit'}

            # 简单的滑动窗口检查
            user_id = user_context.get('user_id') or request.remote_addr
            cache_key = f"rate_{user_id}_{path}"
            now = time.time()

            if cache_key not in self._cache:
                self._cache[cache_key] = []

            requests = self._cache[cache_key]
            # 清理60秒前的记录
            requests[:] = [t for t in requests if now - t < 60]

            if len(requests) >= limit:
                return {'allowed': False, 'reason': f'速率限制: {limit} 次/分钟'}

            requests.append(now)
            return {'allowed': True, 'reason': 'within_limit', 'limit': limit, 'current': len(requests)}
        except Exception as e:
            logger.error(f"速率限制检查失败: {e}")
            return {'allowed': True, 'reason': 'check_error'}

    def _check_time_window(self, path: str) -> Dict:
        """检查时间窗口限制（如考试时间）"""
        # 这里可以实现特定路径的时间窗口限制
        # 例如：考试只能在特定时间访问
        return {'allowed': True, 'reason': 'no_time_window'}


# ==================== 全局实例 ====================

_engine_instance = None

def get_constraint_engine() -> RouteConstraintEngine:
    """获取约束引擎单例"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = RouteConstraintEngine()
    return _engine_instance


# ==================== 装饰器 ====================

def with_constraint_check(f):
    """装饰器：在路由处理前执行约束检查"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        engine = get_constraint_engine()
        user_context = {
            'user_id': session.get('user_id'),
            'username': session.get('username'),
            'role': session.get('role', 'guest')
        }

        result = engine.check_route_constraints(
            request.path,
            request.method,
            user_context
        )

        # 保存到 g，供日志使用
        g.constraint_result = result

        if not result['allowed']:
            status_code = 403
            if 'rate_limit' in (result.get('reason') or ''):
                status_code = 429
            elif 'maintenance' in (result.get('reason') or '').lower():
                status_code = 503
            elif 'locked' in (result.get('reason') or '').lower():
                status_code = 423

            return jsonify({
                'success': False,
                'error': 'ConstraintViolation',
                'reason': result['reason'],
                'message': _get_friendly_message(result['reason']),
                'details': {
                    'matched_constraints': result['matched_constraints'],
                    'access_control': result['access_control']
                }
            }), status_code

        return f(*args, **kwargs)
    return decorated_function


def _get_friendly_message(reason: str) -> str:
    """获取友好的错误消息"""
    if not reason:
        return '请求被拒绝'
    messages = {
        'maintenance': '系统维护中,请稍后再试',
        'rate_limit': '请求过于频繁,请稍后再试',
        'locked': '账户已被锁定',
        'no_rule_matched_guest': '请先登录',
    }
    for key, msg in messages.items():
        if key in reason.lower():
            return msg
    return reason


def init_route_constraint_engine(app):
    """初始化路由约束引擎中间件"""
    get_constraint_engine()
    logger.info("路由约束引擎已初始化")
    return app
