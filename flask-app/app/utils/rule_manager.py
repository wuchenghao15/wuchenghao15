# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Rule Manager for MTSCOS AI System
系统规则数据库模块
"""

import logging
logger = logging.getLogger(__name__)
import sqlite3
from contextlib import contextmanager
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import session
import sys
import os


class RuleManager:
    """规则管理器 - 深度绑定系统规则数据库"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
        self._load_rules_cache()
    
    def _init_db(self):
        """初始化规则数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建系统规则表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_code TEXT UNIQUE NOT NULL,
                rule_name TEXT NOT NULL,
                rule_description TEXT,
                rule_type TEXT NOT NULL,
                rule_value TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                priority INTEGER DEFAULT 100,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used_at TIMESTAMP
            )
        ''')
        
        # 创建规则分组表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rule_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_name TEXT UNIQUE NOT NULL,
                group_description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建规则分组关联表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rule_group_members (
                group_id INTEGER,
                rule_code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (group_id, rule_code)
            )
        ''')
        
        # 创建规则应用日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rule_application_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_code TEXT,
                rule_type TEXT,
                user_id INTEGER,
                username TEXT,
                ip_address TEXT,
                application_result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # 初始化默认规则
        self._init_default_rules()
    
    def _init_default_rules(self):
        """初始化默认系统规则"""
        default_rules = [
            # 权限等级规则 - 核心规则
            {
                'rule_code': 'ROLE_HIERARCHY',
                'rule_name': '权限等级体系',
                'rule_description': '硬件管理员>超级管理员>管理员>游客=学生=设计师',
                'rule_type': 'permission',
                'rule_value': '["guest", "student", "designer", "admin", "super_admin", "hardware_admin"]',
                'priority': 1
            },
            # 安全规则
            {
                'rule_code': 'SEC_LOGIN_MAX_ATTEMPTS',
                'rule_name': '最大登录尝试次数',
                'rule_description': '用户登录失败最大尝试次数',
                'rule_type': 'security',
                'rule_value': '5',
                'priority': 10
            },
            {
                'rule_code': 'SEC_LOCK_DURATION',
                'rule_name': '账户锁定时长',
                'rule_description': '登录失败后账户锁定分钟数',
                'rule_type': 'security',
                'rule_value': '5',
                'priority': 10
            },
            {
                'rule_code': 'SEC_SESSION_TIMEOUT',
                'rule_name': '会话超时时间',
                'rule_description': '用户会话超时分钟数',
                'rule_type': 'security',
                'rule_value': '30',
                'priority': 10
            },
            {
                'rule_code': 'SEC_PASSWORD_EXPIRY',
                'rule_name': '密码过期天数',
                'rule_description': '密码有效期天数',
                'rule_type': 'security',
                'rule_value': '90',
                'priority': 10
            },
            # 硬件认证规则
            {
                'rule_code': 'HW_AUTH_REQUIRED',
                'rule_name': '硬件认证必需',
                'rule_description': '硬件管理员是否需要硬件加密狗',
                'rule_type': 'security',
                'rule_value': 'true',
                'priority': 2
            },
            {
                'rule_code': 'HW_SESSION_TIMEOUT',
                'rule_name': '硬件会话超时',
                'rule_description': '硬件认证会话超时时间(小时)',
                'rule_type': 'security',
                'rule_value': '8',
                'priority': 10
            },
            # 权限规则 - 新等级体系
            {
                'rule_code': 'PERM_VIEW_DASHBOARD',
                'rule_name': '查看仪表盘权限',
                'rule_description': '允许访问仪表盘的角色',
                'rule_type': 'permission',
                'rule_value': '["student", "designer", "admin", "super_admin", "hardware_admin", "hardware_vikey_admin"]',
                'priority': 20
            },
            {
                'rule_code': 'PERM_VIEW_SETTINGS',
                'rule_name': '查看设置权限',
                'rule_description': '允许访问设置页面的角色',
                'rule_type': 'permission',
                'rule_value': '["admin", "super_admin", "hardware_admin", "hardware_vikey_admin"]',
                'priority': 20
            },
            {
                'rule_code': 'PERM_MANAGE_USERS',
                'rule_name': '管理用户权限',
                'rule_description': '允许管理用户的角色',
                'rule_type': 'permission',
                'rule_value': '["admin", "super_admin", "hardware_admin", "hardware_vikey_admin"]',
                'priority': 20
            },
            {
                'rule_code': 'PERM_DELETE_USER',
                'rule_name': '删除用户权限',
                'rule_description': '允许删除用户的角色',
                'rule_type': 'permission',
                'rule_value': '["super_admin", "hardware_admin", "hardware_vikey_admin"]',
                'priority': 20
            },
            {
                'rule_code': 'PERM_MANAGE_DATABASE',
                'rule_name': '管理数据库权限',
                'rule_description': '允许管理数据库的角色',
                'rule_type': 'permission',
                'rule_value': '["super_admin", "hardware_admin", "hardware_vikey_admin"]',
                'priority': 20
            },
            {
                'rule_code': 'PERM_VIEW_LOGS',
                'rule_name': '查看日志权限',
                'rule_description': '允许查看系统日志的角色',
                'rule_type': 'permission',
                'rule_value': '["admin", "super_admin", "hardware_admin", "hardware_vikey_admin"]',
                'priority': 20
            },
            # 访问规则
            {
                'rule_code': 'ACCESS_DASHBOARD',
                'rule_name': '仪表盘访问规则',
                'rule_description': '仪表盘页面访问规则',
                'rule_type': 'access',
                'rule_value': 'require_login',
                'priority': 30
            },
            {
                'rule_code': 'ACCESS_SETTINGS',
                'rule_name': '设置页面访问规则',
                'rule_description': '设置页面访问规则',
                'rule_type': 'access',
                'rule_value': 'require_admin',
                'priority': 30
            },
            {
                'rule_code': 'ACCESS_ADMIN_CENTER',
                'rule_name': '管理员中心访问规则',
                'rule_description': '管理员中心访问规则',
                'rule_type': 'access',
                'rule_value': 'require_admin',
                'priority': 30
            },
            {
                'rule_code': 'ACCESS_SUPER_ADMIN',
                'rule_name': '超级管理员访问规则',
                'rule_description': '超级管理员专属页面访问规则',
                'rule_type': 'access',
                'rule_value': 'super_admin_or_hardware_admin',
                'priority': 25
            },
            {
                'rule_code': 'ACCESS_HARDWARE_ADMIN',
                'rule_name': '硬件管理员访问规则',
                'rule_description': '硬件管理员专属功能访问规则',
                'rule_type': 'access',
                'rule_value': 'hardware_admin_with_hardware',
                'priority': 24
            },
            # 系统规则
            {
                'rule_code': 'SYS_MAINTENANCE_MODE',
                'rule_name': '维护模式',
                'rule_description': '系统维护模式开关',
                'rule_type': 'system',
                'rule_value': 'false',
                'priority': 5
            },
            {
                'rule_code': 'SYS_ALLOW_REGISTRATION',
                'rule_name': '允许注册',
                'rule_description': '是否允许新用户注册',
                'rule_type': 'system',
                'rule_value': 'true',
                'priority': 5
            },
            {
                'rule_code': 'SYS_MAX_USERS',
                'rule_name': '最大用户数',
                'rule_description': '系统允许的最大用户数',
                'rule_type': 'system',
                'rule_value': '1000',
                'priority': 5
            },
            # 监控规则
            {
                'rule_code': 'MONITOR_ENABLED',
                'rule_name': '监控启用',
                'rule_description': '是否启用系统监控',
                'rule_type': 'monitor',
                'rule_value': 'true',
                'priority': 40
            },
            {
                'rule_code': 'MONITOR_THRESHOLD_CPU',
                'rule_name': 'CPU监控阈值',
                'rule_description': 'CPU使用率告警阈值(%)',
                'rule_type': 'monitor',
                'rule_value': '90',
                'priority': 40
            },
            {
                'rule_code': 'MONITOR_THRESHOLD_MEMORY',
                'rule_name': '内存监控阈值',
                'rule_description': '内存使用率告警阈值(%)',
                'rule_type': 'monitor',
                'rule_value': '80',
                'priority': 40
            },
            {
                'rule_code': 'MONITOR_ALERT_ENABLED',
                'rule_name': '告警启用',
                'rule_description': '是否启用告警通知',
                'rule_type': 'monitor',
                'rule_value': 'true',
                'priority': 40
            }
        ]
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for rule in default_rules:
                cursor.execute('SELECT COUNT(*) FROM system_rules WHERE rule_code = ?', (rule['rule_code'],))
                if cursor.fetchone()[0] == 0:
                    cursor.execute('''
                    INSERT INTO system_rules (rule_code, rule_name, rule_description, rule_type, rule_value, priority)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ''', (rule['rule_code'], rule['rule_name'], rule['rule_description'], 
                          rule['rule_type'], rule['rule_value'], rule['priority']))
            
            conn.commit()
    
    def _load_rules_cache(self):
        """加载规则到内存缓存"""
        self.rules_cache = {}
        import os
        logger.info(f"[规则管理器] 数据库路径: {self.db_path}, 存在: {os.path.exists(self.db_path)}")
        logger.info(f"[规则管理器] 数据库文件大小: {os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0} bytes")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM system_rules')
            total_count = cursor.fetchone()[0]
            logger.info(f"[规则管理器] 数据库中system_rules表总行数: {total_count}")
            
            cursor.execute('SELECT rule_code, rule_value, is_active FROM system_rules WHERE rule_code = "PERM_VIEW_DASHBOARD"')
            row = cursor.fetchone()
            if row:
                logger.info(f"[规则管理器] 数据库中PERM_VIEW_DASHBOARD: {row}")
            
            cursor.execute('SELECT rule_code, rule_value, is_active FROM system_rules WHERE is_active = 1')
            for row in cursor.fetchall():
                rule_code = row[0]
                rule_value = row[1]
                try:
                    self.rules_cache[rule_code] = json.loads(rule_value)
                except Exception:
                    self.rules_cache[rule_code] = rule_value
        
        logger.info(f"[规则管理器] 缓存加载完成，共 {len(self.rules_cache)} 条规则")
        logger.info(f"[规则管理器] PERM_VIEW_DASHBOARD = {self.rules_cache.get('PERM_VIEW_DASHBOARD')}")
        logger.info(f"[规则管理器] PERM_VIEW_SETTINGS = {self.rules_cache.get('PERM_VIEW_SETTINGS')}")
    
    def refresh_cache(self):
        """强制刷新规则缓存"""
        logger.info("[规则管理器] 强制刷新规则缓存...")
        self._load_rules_cache()
            
    
    def get_rule(self, rule_code: str) -> Any:
        """获取规则值"""
        # 先从缓存获取
        if rule_code in self.rules_cache:
            return self.rules_cache[rule_code]
        
        # 从数据库获取
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT rule_value, is_active FROM system_rules WHERE rule_code = ?', (rule_code,))
            row = cursor.fetchone()
        
        if row and row[1] == 1:
            try:
                value = json.loads(row[0])
            except Exception:
                value = row[0]
            self.rules_cache[rule_code] = value
            return value
        
        return None
    
    def set_rule(self, rule_code: str, rule_value: Any) -> bool:
        """设置规则值"""
        try:
            value_str = json.dumps(rule_value) if isinstance(rule_value, (dict, list)) else str(rule_value)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT OR REPLACE INTO system_rules (rule_code, rule_value, updated_at)
                VALUES (?, ?, ?)
                ''', (rule_code, value_str, datetime.now()))
                
                conn.commit()
            
            # 更新缓存
            try:
                self.rules_cache[rule_code] = json.loads(value_str)
            except Exception:
                self.rules_cache[rule_code] = value_str
            
            return True
        except Exception as e:
            logger.error(f"Failed to set rule {rule_code}: {e}")
            return False
    
    def get_rules_by_type(self, rule_type: str) -> List[Dict]:
        """按类型获取规则"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM system_rules WHERE rule_type = ? AND is_active = 1 ORDER BY priority', (rule_type,))
            columns = ['id', 'rule_code', 'rule_name', 'rule_description', 'rule_type', 
                       'rule_value', 'is_active', 'priority', 'created_at', 'updated_at', 'last_used_at']
            rules = []
            for row in cursor.fetchall():
                rule = dict(zip(columns, row))
                try:
                    rule['rule_value'] = json.loads(rule['rule_value'])
                except Exception:
                    pass
                rules.append(rule)
            
        return rules
    
    def get_all_rules(self) -> List[Dict]:
        """获取所有规则"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM system_rules ORDER BY rule_type, priority')
            columns = ['id', 'rule_code', 'rule_name', 'rule_description', 'rule_type', 
                       'rule_value', 'is_active', 'priority', 'created_at', 'updated_at', 'last_used_at']
            rules = []
            for row in cursor.fetchall():
                rule = dict(zip(columns, row))
                try:
                    rule['rule_value'] = json.loads(rule['rule_value'])
                except Exception:
                    pass
                rules.append(rule)
            
        return rules
    
    def toggle_rule(self, rule_code: str, is_active: bool) -> bool:
        """启用/禁用规则"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('UPDATE system_rules SET is_active = ?, updated_at = ? WHERE rule_code = ?',
                              (1 if is_active else 0, datetime.now(), rule_code))
                
                conn.commit()
            
            # 更新缓存
            if is_active:
                value = self.get_rule(rule_code)
                self.rules_cache[rule_code] = value
            else:
                self.rules_cache.pop(rule_code, None)
            
            return True
        except Exception as e:
            logger.error(f"Failed to toggle rule {rule_code}: {e}")
            return False
    
    def apply_rule(self, rule_code: str, user_id: int = None, username: str = None, ip_address: str = None) -> bool:
        """应用规则并记录日志"""
        rule_value = self.get_rule(rule_code)
        if rule_value is None:
            return False
        
        # 记录应用日志
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT INTO rule_application_logs (rule_code, rule_type, user_id, username, ip_address, application_result)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (rule_code, self._get_rule_type(rule_code), user_id, username, ip_address, 'applied'))
                
                cursor.execute('UPDATE system_rules SET last_used_at = ? WHERE rule_code = ?',
                              (datetime.now(), rule_code))
                
                conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"Failed to log rule application {rule_code}: {e}")
            return False
    
    def _get_rule_type(self, rule_code: str) -> str:
        """获取规则类型"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT rule_type FROM system_rules WHERE rule_code = ?', (rule_code,))
            result = cursor.fetchone()
        
        return result[0] if result else 'unknown'
    
    def get_rule_application_logs(self, limit: int = 100) -> List[Dict]:
        """获取规则应用日志"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM rule_application_logs ORDER BY created_at DESC LIMIT ?', (limit,))
            columns = ['id', 'rule_code', 'rule_type', 'user_id', 'username', 'ip_address', 'application_result', 'created_at']
            logs = []
            for row in cursor.fetchall():
                logs.append(dict(zip(columns, row)))
            
        return logs
    
    def validate_access(self, path: str, user_role: str) -> bool:
        """验证用户对路径的访问权限"""
        path_rule_map = {
            '/dashboard': 'PERM_VIEW_DASHBOARD',
            '/settings': 'PERM_VIEW_SETTINGS',
            '/settings/system': 'PERM_VIEW_SETTINGS',
            '/settings/security': 'PERM_VIEW_SETTINGS',
            '/admin_center': 'PERM_MANAGE_USERS',
            '/super_admin_dashboard': 'PERM_DELETE_USER'
        }
        
        if path in path_rule_map:
            rule_code = path_rule_map[path]
            allowed_roles = self.get_rule(rule_code)
            if isinstance(allowed_roles, list):
                return user_role in allowed_roles
        
        if path.startswith('/settings/'):
            allowed_roles = self.get_rule('PERM_VIEW_SETTINGS')
            if isinstance(allowed_roles, list):
                return user_role in allowed_roles
        
        return True
    
    def check_security_rules(self, username: str, ip_address: str) -> Dict:
        """检查安全规则"""
        max_attempts = int(self.get_rule('SEC_LOGIN_MAX_ATTEMPTS') or 5)
        lock_duration = int(self.get_rule('SEC_LOCK_DURATION') or 5)
        session_timeout = int(self.get_rule('SEC_SESSION_TIMEOUT') or 30)
        
        # 检查登录尝试次数
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 检查用户是否被锁定
            cursor.execute('SELECT locked_until FROM user_locks WHERE username = ?', (username,))
            lock_result = cursor.fetchone()
            
            if lock_result and lock_result[0]:
                if datetime.now() < datetime.fromisoformat(lock_result[0]):
                    return {'allowed': False, 'reason': 'user_locked', 'detail': '账户已被锁定'}
            
            # 统计失败尝试次数
            time_threshold = datetime.now() - timedelta(hours=1)
            cursor.execute('''
                SELECT COUNT(*) FROM login_attempts 
                WHERE username = ? AND success = 0 AND attempt_time > ?
            ''', (username, time_threshold))
            
            fail_count = cursor.fetchone()[0]
        
        if fail_count >= max_attempts:
            return {'allowed': False, 'reason': 'too_many_attempts', 'detail': f'登录失败{max_attempts}次'}
        
        return {'allowed': True, 'max_attempts': max_attempts, 'remaining_attempts': max_attempts - fail_count}
    
    def validate_rule(self, rule: Dict) -> bool:
        """验证规则的有效性"""
        required_fields = ['rule_code', 'rule_name', 'rule_type', 'rule_value']
        
        # 检查必需字段
        for field in required_fields:
            if field not in rule:
                return False
        
        # 检查规则代码格式
        if not rule['rule_code'] or not rule['rule_code'].isupper():
            return False
        
        # 检查规则类型
        valid_types = ['permission', 'security', 'access', 'system', 'monitor']
        if rule['rule_type'] not in valid_types:
            return False
        
        # 检查规则值
        if rule['rule_value'] is None:
            return False
        
        # 检查优先级
        if 'priority' in rule:
            try:
                priority = int(rule['priority'])
                if priority < 1 or priority > 1000:
                    return False
            except ValueError:
                return False
        
        return True


# 全局规则管理器实例
rule_manager: Optional[RuleManager] = None


def init_rule_manager(db_path: str):
    """初始化规则管理器"""
    global rule_manager
    rule_manager = RuleManager(db_path)
    rule_manager.refresh_cache()
    return rule_manager


def get_rule_manager() -> RuleManager:
    """获取规则管理器实例"""
    global rule_manager
    if rule_manager is None:
        rule_manager = RuleManager('/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db')
    return rule_manager


def get_rule(rule_code: str) -> Any:
    """获取规则值"""
    return get_rule_manager().get_rule(rule_code)


def set_rule(rule_code: str, rule_value: Any) -> bool:
    """设置规则值"""
    return get_rule_manager().set_rule(rule_code, rule_value)


def validate_access(path: str, user_role: str) -> bool:
    """验证访问权限"""
    return get_rule_manager().validate_access(path, user_role)


def check_security_rules(username: str, ip_address: str) -> Dict:
    """检查安全规则"""
    return get_rule_manager().check_security_rules(username, ip_address)
