#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS集中式权限管理优化服务 提供角色管理、功能模块管理、用户角色分配、权限检查与审计日志功能 """

import os
import sys
import json
import time
import uuid
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union

logger = print

# 默认角色权限定义
DEFAULT_ROLES = [
    {
        'role_name': '超级管理员',
        'role_code': 'super_admin',
        'description': '拥有系统全部权限，可管理所有模块和用户',
        'permissions': ['*'],
        'is_system': 1
    },
    {
        'role_name': '管理员',
        'role_code': 'admin',
        'description': '系统管理员，拥有系统主要管理权限',
        'permissions': ['system', 'users', 'education', 'security', 'communication', 'sslvpn', 'ai'],
        'is_system': 1
    },
    {
        'role_name': '教师',
        'role_code': 'teacher',
        'description': '教师角色，拥有教学相关权限',
        'permissions': ['education', 'exam', 'question_bank', 'student_manage'],
        'is_system': 1
    },
    {
        'role_name': '学生',
        'role_code': 'student',
        'description': '学生角色，拥有学习相关权限',
        'permissions': ['exam', 'study', 'profile', 'communication'],
        'is_system': 1
    },
    {
        'role_name': '访客',
        'role_code': 'guest',
        'description': '访客角色，仅拥有基本访问权限',
        'permissions': ['profile', 'dashboard'],
        'is_system': 1
    }
]

# 默认功能模块定义
DEFAULT_MODULES = [
    {
        'module_name': '仪表盘',
        'module_code': 'dashboard',
        'module_url': '/dashboard',
        'module_icon': 'dashboard',
        'parent_id': None,
        'sort_order': 1,
        'required_permission': 'dashboard',
        'is_visible': 1
    },
    {
        'module_name': '用户管理',
        'module_code': 'user_management',
        'module_url': '/users',
        'module_icon': 'users',
        'parent_id': None,
        'sort_order': 2,
        'required_permission': 'users',
        'is_visible': 1
    },
    {
        'module_name': '教育管理',
        'module_code': 'education_management',
        'module_url': '/education',
        'module_icon': 'education',
        'parent_id': None,
        'sort_order': 3,
        'required_permission': 'education',
        'is_visible': 1
    },
    {
        'module_name': '题库管理',
        'module_code': 'question_bank',
        'module_url': '/question-bank',
        'module_icon': 'question-bank',
        'parent_id': None,
        'sort_order': 4,
        'required_permission': 'question_bank',
        'is_visible': 1
    },
    {
        'module_name': '考试管理',
        'module_code': 'exam_management',
        'module_url': '/exam',
        'module_icon': 'exam',
        'parent_id': None,
        'sort_order': 5,
        'required_permission': 'exam',
        'is_visible': 1
    },
    {
        'module_name': 'AI智能中心',
        'module_code': 'ai_center',
        'module_url': '/ai-center',
        'module_icon': 'ai',
        'parent_id': None,
        'sort_order': 6,
        'required_permission': 'ai',
        'is_visible': 1
    },
    {
        'module_name': '安全管理',
        'module_code': 'security_management',
        'module_url': '/security',
        'module_icon': 'security',
        'parent_id': None,
        'sort_order': 7,
        'required_permission': 'security',
        'is_visible': 1
    },
    {
        'module_name': '通讯中心',
        'module_code': 'communication_center',
        'module_url': '/communication',
        'module_icon': 'communication',
        'parent_id': None,
        'sort_order': 8,
        'required_permission': 'communication',
        'is_visible': 1
    },
    {
        'module_name': 'SSL/VPN管理',
        'module_code': 'sslvpn_management',
        'module_url': '/sslvpn',
        'module_icon': 'sslvpn',
        'parent_id': None,
        'sort_order': 9,
        'required_permission': 'sslvpn',
        'is_visible': 1
    },
    {
        'module_name': '系统设置',
        'module_code': 'system_settings',
        'module_url': '/settings',
        'module_icon': 'settings',
        'parent_id': None,
        'sort_order': 10,
        'required_permission': 'system',
        'is_visible': 1
    },
    {
        'module_name': '数据分析',
        'module_code': 'data_analysis',
        'module_url': '/data-analysis',
        'module_icon': 'data-analysis',
        'parent_id': None,
        'sort_order': 11,
        'required_permission': 'system',
        'is_visible': 1
    },
    {
        'module_name': '日志监控',
        'module_code': 'log_monitor',
        'module_url': '/logs',
        'module_icon': 'logs',
        'parent_id': None,
        'sort_order': 12,
        'required_permission': 'system',
        'is_visible': 1
    }
]


class PermissionOptimizerService:
    """集中式权限管理优化服务"""

    def __init__(self):
        self.db_path = 'app.db'
        self.lock = threading.RLock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """获取SQLite数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        return conn

    def _init_db(self):
        """初始化数据库表与默认数据"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()

                # 角色表
                cursor.execute(''' CREATE TABLE IF NOT EXISTS permission_roles ( role_id INTEGER PRIMARY KEY AUTOINCREMENT, role_name TEXT NOT NULL, role_code TEXT NOT NULL UNIQUE, description TEXT, permissions TEXT DEFAULT '[]', is_system INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP ) ''')

                # 功能模块表
                cursor.execute(''' CREATE TABLE IF NOT EXISTS permission_modules ( module_id INTEGER PRIMARY KEY AUTOINCREMENT, module_name TEXT NOT NULL, module_code TEXT NOT NULL UNIQUE, module_url TEXT, module_icon TEXT, parent_id INTEGER, sort_order INTEGER DEFAULT 0, required_permission TEXT, is_visible INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP ) ''')

                # 用户角色分配表
                cursor.execute(''' CREATE TABLE IF NOT EXISTS user_role_assignments ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, role_id INTEGER NOT NULL, assigned_by TEXT, assigned_at TEXT DEFAULT CURRENT_TIMESTAMP, expires_at TEXT, FOREIGN KEY (role_id) REFERENCES permission_roles(role_id) ON DELETE CASCADE ) ''')

                # 权限审计日志表
                # 注意：若已存在旧版表（字段不兼容），则备份为 permission_audit_logs_legacy 后重建
                self._migrate_audit_logs_table_if_needed(cursor)

                cursor.execute(''' CREATE TABLE IF NOT EXISTS permission_audit_logs ( log_id TEXT PRIMARY KEY, user_id TEXT, action TEXT, module TEXT, resource TEXT, permission_level TEXT, status TEXT, ip_address TEXT, details TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP ) ''')

                # 按钮权限表
                cursor.execute(''' CREATE TABLE IF NOT EXISTS permission_buttons ( button_id INTEGER PRIMARY KEY AUTOINCREMENT, module_id INTEGER NOT NULL, button_name TEXT NOT NULL, button_code TEXT NOT NULL, button_label TEXT, parent_button_id INTEGER, sort_order INTEGER DEFAULT 0, is_visible INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (module_id) REFERENCES permission_modules(module_id) ON DELETE CASCADE, FOREIGN KEY (parent_button_id) REFERENCES permission_buttons(button_id) ON DELETE CASCADE ) ''')

                # 角色按钮权限关联表
                cursor.execute(''' CREATE TABLE IF NOT EXISTS role_button_permissions ( id INTEGER PRIMARY KEY AUTOINCREMENT, role_id INTEGER NOT NULL, button_id INTEGER NOT NULL, allowed INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (role_id) REFERENCES permission_roles(role_id) ON DELETE CASCADE, FOREIGN KEY (button_id) REFERENCES permission_buttons(button_id) ON DELETE CASCADE, UNIQUE (role_id, button_id) ) ''')

                # 数据权限表
                cursor.execute(''' CREATE TABLE IF NOT EXISTS permission_data_rules ( rule_id INTEGER PRIMARY KEY AUTOINCREMENT, role_id INTEGER NOT NULL, module_code TEXT NOT NULL, data_scope TEXT DEFAULT 'all', data_level TEXT DEFAULT 'full', special_rules TEXT DEFAULT '{}', is_active INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (role_id) REFERENCES permission_roles(role_id) ON DELETE CASCADE, UNIQUE (role_id, module_code) ) ''')

                # 接口权限表
                cursor.execute(''' CREATE TABLE IF NOT EXISTS permission_api_rules ( rule_id INTEGER PRIMARY KEY AUTOINCREMENT, role_id INTEGER NOT NULL, api_path TEXT NOT NULL, api_method TEXT DEFAULT 'GET', allowed INTEGER DEFAULT 1, is_active INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (role_id) REFERENCES permission_roles(role_id) ON DELETE CASCADE, UNIQUE (role_id, api_path, api_method) ) ''')

                # 创建索引以提升查询性能
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_role_user ON user_role_assignments(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_role_role ON user_role_assignments(role_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_user ON permission_audit_logs(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_created ON permission_audit_logs(created_at)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_modules_parent ON permission_modules(parent_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_buttons_module ON permission_buttons(module_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_role_button_role ON role_button_permissions(role_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_role_button_button ON role_button_permissions( button_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_data_role ON permission_data_rules(role_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_data_module ON permission_data_rules(module_code)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_api_role ON permission_api_rules(role_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_api_path ON permission_api_rules(api_path)')

                conn.commit()

                # 初始化默认角色
                self._init_default_roles(cursor)
                # 初始化默认模块
                self._init_default_modules(cursor)
                # 初始化默认按钮权限
                self._init_default_buttons(cursor)
                # 初始化默认数据权限
                self._init_default_data_rules(cursor)
                # 初始化默认接口权限
                self._init_default_api_rules(cursor)

                conn.commit()
                conn.close()
                logger('[PermissionService] 数据库初始化完成')
            except Exception as e:
                logger(f'[PermissionService] 数据库初始化失败: {e}')
                try:
                    conn.close()
                except Exception:
                    pass

    def _migrate_audit_logs_table_if_needed(self, cursor):
        """若 permission_audit_logs 表结构与目标 schema 不兼容，则备份旧表后允许重建"""
        cursor.execute(''' SELECT name FROM sqlite_master WHERE type='table' AND name='permission_audit_logs' ''')
        if cursor.fetchone() is None:
            return  # 表不存在，无需迁移

        # 检查必需列是否存在
        required_columns = {
            'log_id', 'user_id', 'action', 'module', 'resource',
            'permission_level', 'status', 'ip_address', 'details', 'created_at'
        }
        cursor.execute('PRAGMA table_info(permission_audit_logs)')
        existing_columns = {row[1] for row in cursor.fetchall()}

        # 若缺少关键列，则将旧表重命名为 legacy 表以保留历史数据
        if not required_columns.issubset(existing_columns):
            cursor.execute('ALTER TABLE permission_audit_logs RENAME TO permission_audit_logs_legacy')
            logger('[PermissionService] 旧版 permission_audit_logs 表已备份为 permission_audit_logs_legacy')

    def _init_default_roles(self, cursor):
        """初始化默认角色"""
        for role in DEFAULT_ROLES:
            cursor.execute('SELECT role_id FROM permission_roles WHERE role_code = ?', (role['role_code'],))
            if cursor.fetchone() is None:
                cursor.execute(''' INSERT INTO permission_roles (role_name, role_code, description, permissions, is_system) VALUES (?, ?, ?, ?, ?) ''', (
                    role['role_name'],
                    role['role_code'],
                    role['description'],
                    json.dumps(role['permissions'], ensure_ascii=False),
                    role['is_system']
                ))

    def _init_default_modules(self, cursor):
        """初始化默认功能模块"""
        for module in DEFAULT_MODULES:
            cursor.execute('SELECT module_id FROM permission_modules WHERE module_code = ?', (module['module_code'],))
            if cursor.fetchone() is None:
                cursor.execute(''' INSERT INTO permission_modules (module_name, module_code, module_url, module_icon, parent_id, sort_order, required_permission, is_visible) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ''', (
                    module['module_name'],
                    module['module_code'],
                    module['module_url'],
                    module['module_icon'],
                    module['parent_id'],
                    module['sort_order'],
                    module['required_permission'],
                    module['is_visible']
                ))

    def _init_default_buttons(self, cursor):
        """初始化默认按钮权限"""
        DEFAULT_BUTTONS = [
            {'module_code': 'dashboard', 'button_name': '刷新', 'button_code': 'refresh', 'button_label': '刷新'},
            {'module_code': 'dashboard', 'button_name': '导出', 'button_code': 'export', 'button_label': '导出'},
            
            {'module_code': 'user_management', 'button_name': '查看用户', 'button_code': 'view_user', 'button_label': '查看'},
            {'module_code': 'user_management', 'button_name': '创建用户', 'button_code': 'create_user',
            'button_label': '创建'},
            {'module_code': 'user_management', 'button_name': '编辑用户', 'button_code': 'edit_user', 'button_label': '编辑'},
            {'module_code': 'user_management', 'button_name': '删除用户', 'button_code': 'delete_user',
            'button_label': '删除'},
            {'module_code': 'user_management', 'button_name': '分配角色', 'button_code': 'assign_role',
            'button_label': '分配角色'},
            
            {'module_code': 'education_management', 'button_name': '查看课程', 'button_code': 'view_course',
            'button_label': '查看'},
            {'module_code': 'education_management', 'button_name': '创建课程', 'button_code': 'create_course',
            'button_label': '创建'},
            {'module_code': 'education_management', 'button_name': '编辑课程', 'button_code': 'edit_course',
            'button_label': '编辑'},
            {'module_code': 'education_management', 'button_name': '删除课程', 'button_code': 'delete_course',
            'button_label': '删除'},
            {'module_code': 'education_management', 'button_name': '发布课程', 'button_code': 'publish_course',
            'button_label': '发布'},
            
            {'module_code': 'question_bank', 'button_name': '查看题目', 'button_code': 'view_question',
            'button_label': '查看'},
            {'module_code': 'question_bank', 'button_name': '添加题目', 'button_code': 'add_question',
            'button_label': '添加'},
            {'module_code': 'question_bank', 'button_name': '编辑题目', 'button_code': 'edit_question',
            'button_label': '编辑'},
            {'module_code': 'question_bank', 'button_name': '删除题目', 'button_code': 'delete_question',
            'button_label': '删除'},
            {'module_code': 'question_bank', 'button_name': '导入题目', 'button_code': 'import_question',
            'button_label': '导入'},
            
            {'module_code': 'exam_management', 'button_name': '查看考试', 'button_code': 'view_exam', 'button_label': '查看'},
            {'module_code': 'exam_management', 'button_name': '创建考试', 'button_code': 'create_exam',
            'button_label': '创建'},
            {'module_code': 'exam_management', 'button_name': '编辑考试', 'button_code': 'edit_exam', 'button_label': '编辑'},
            {'module_code': 'exam_management', 'button_name': '删除考试', 'button_code': 'delete_exam',
            'button_label': '删除'},
            {'module_code': 'exam_management', 'button_name': '发布考试', 'button_code': 'publish_exam',
            'button_label': '发布'},
            
            {'module_code': 'ai_center', 'button_name': '查看AI', 'button_code': 'view_ai', 'button_label': '查看'},
            {'module_code': 'ai_center', 'button_name': '配置AI', 'button_code': 'config_ai', 'button_label': '配置'},
            
            {'module_code': 'security_management', 'button_name': '查看日志', 'button_code': 'view_log',
            'button_label': '查看日志'},
            {'module_code': 'security_management', 'button_name': '管理IP', 'button_code': 'manage_ip',
            'button_label': 'IP管理'},
            {'module_code': 'security_management', 'button_name': '管理策略', 'button_code': 'manage_policy',
            'button_label': '策略管理'},
            
            {'module_code': 'system_settings', 'button_name': '查看设置', 'button_code': 'view_setting',
            'button_label': '查看'},
            {'module_code': 'system_settings', 'button_name': '编辑设置', 'button_code': 'edit_setting',
            'button_label': '编辑'},
        ]
        
        for btn in DEFAULT_BUTTONS:
            cursor.execute('SELECT module_id FROM permission_modules WHERE module_code = ?', (btn['module_code'],))
            module_row = cursor.fetchone()
            if module_row:
                module_id = module_row['module_id']
                cursor.execute('SELECT button_id FROM permission_buttons WHERE module_id = ? AND button_code = ?',
                (module_id, btn['button_code']))
                if cursor.fetchone() is None:
                    cursor.execute(''' INSERT INTO permission_buttons (module_id, button_name, button_code, button_label, sort_order) VALUES (?, ?, ?, ?, 0) ''', (module_id, btn['button_name'], btn['button_code'], btn['button_label']))

    def _init_default_data_rules(self, cursor):
        """初始化默认数据权限规则"""
        DEFAULT_DATA_RULES = [
            {'role_code': 'super_admin', 'module_code': '*', 'data_scope': 'all', 'data_level': 'full'},
            {'role_code': 'admin', 'module_code': '*', 'data_scope': 'all', 'data_level': 'full'},
            {'role_code': 'teacher', 'module_code': 'education_management', 'data_scope': 'own', 'data_level': 'full'},
            {'role_code': 'teacher', 'module_code': 'exam_management', 'data_scope': 'own', 'data_level': 'full'},
            {'role_code': 'teacher', 'module_code': 'question_bank', 'data_scope': 'own', 'data_level': 'full'},
            {'role_code': 'student', 'module_code': '*', 'data_scope': 'own', 'data_level': 'read'},
            {'role_code': 'guest', 'module_code': '*', 'data_scope': 'public', 'data_level': 'read'},
        ]
        
        for rule in DEFAULT_DATA_RULES:
            cursor.execute('SELECT role_id FROM permission_roles WHERE role_code = ?', (rule['role_code'],))
            role_row = cursor.fetchone()
            if role_row:
                role_id = role_row['role_id']
                cursor.execute('SELECT rule_id FROM permission_data_rules WHERE role_id = ? AND module_code = ?',
                (role_id, rule['module_code']))
                if cursor.fetchone() is None:
                    cursor.execute(''' INSERT INTO permission_data_rules (role_id, module_code, data_scope, data_level) VALUES (?, ?, ?, ?) ''', (role_id, rule['module_code'], rule['data_scope'], rule['data_level']))

    def _init_default_api_rules(self, cursor):
        """初始化默认接口权限规则"""
        DEFAULT_API_RULES = [
            {'role_code': 'super_admin', 'api_path': '*', 'api_method': '*', 'allowed': 1},
            {'role_code': 'admin', 'api_path': '/api/optimization/permissions/*', 'api_method': '*', 'allowed': 1},
            {'role_code': 'admin', 'api_path': '/api/users/*', 'api_method': '*', 'allowed': 1},
            {'role_code': 'admin', 'api_path': '/api/education/*', 'api_method': '*', 'allowed': 1},
            {'role_code': 'teacher', 'api_path': '/api/education/*', 'api_method': '*', 'allowed': 1},
            {'role_code': 'teacher', 'api_path': '/api/exam/*', 'api_method': '*', 'allowed': 1},
            {'role_code': 'student', 'api_path': '/api/exam/*', 'api_method': 'GET', 'allowed': 1},
            {'role_code': 'student', 'api_path': '/api/profile/*', 'api_method': '*', 'allowed': 1},
            {'role_code': 'guest', 'api_path': '/api/public/*', 'api_method': 'GET', 'allowed': 1},
        ]
        
        for rule in DEFAULT_API_RULES:
            cursor.execute('SELECT role_id FROM permission_roles WHERE role_code = ?', (rule['role_code'],))
            role_row = cursor.fetchone()
            if role_row:
                role_id = role_row['role_id']
                cursor.execute(''' SELECT rule_id FROM permission_api_rules WHERE role_id = ? AND api_path = ? AND api_method = ? ''', (role_id, rule['api_path'], rule['api_method']))
                if cursor.fetchone() is None:
                    cursor.execute(''' INSERT INTO permission_api_rules (role_id, api_path, api_method, allowed) VALUES (?, ?, ?, ?) ''', (role_id, rule['api_path'], rule['api_method'], rule['allowed']))

    # ========== 权限查询 ==========

    def get_user_roles(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户角色列表"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(''' SELECT r.role_id, r.role_name, r.role_code, r.description, r.permissions, r.is_system, r.created_at, a.assigned_at, a.expires_at, a.assigned_by FROM user_role_assignments a INNER JOIN permission_roles r ON a.role_id = r.role_id WHERE a.user_id = ? ORDER BY a.assigned_at DESC ''', (user_id,))
                rows = cursor.fetchall()
                conn.close()

                roles = []
                now = datetime.now().isoformat()
                for row in rows:
                    # 过滤已过期角色
                    if row['expires_at'] and row['expires_at'] < now:
                        continue
                    try:
                        permissions = json.loads(row['permissions']) if row['permissions'] else []
                    except (json.JSONDecodeError, TypeError):
                        permissions = []
                    roles.append({
                        'role_id': row['role_id'],
                        'role_name': row['role_name'],
                        'role_code': row['role_code'],
                        'description': row['description'],
                        'permissions': permissions,
                        'is_system': bool(row['is_system']),
                        'created_at': row['created_at'],
                        'assigned_at': row['assigned_at'],
                        'expires_at': row['expires_at'],
                        'assigned_by': row['assigned_by']
                    })
                return roles
            except Exception as e:
                logger(f'[PermissionService] 获取用户角色失败: {e}')
                try:
                    conn.close()
                except Exception:
                    pass
                return []

    def get_user_permissions(self, user_id: str) -> List[str]:
        """获取用户所有权限（合并所有角色的权限）"""
        roles = self.get_user_roles(user_id)
        permissions_set = set()
        for role in roles:
            for perm in role.get('permissions', []):
                permissions_set.add(perm)
        # 超级管理员拥有所有权限
        if '*' in permissions_set:
            return ['*']
        return list(permissions_set)

    def check_permission(self, user_id: str, permission_code: str) -> bool:
        """检查用户是否拥有某项权限"""
        permissions = self.get_user_permissions(user_id)
        if '*' in permissions:
            return True
        return permission_code in permissions

    def get_accessible_modules(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户可访问的模块列表（用于侧边栏菜单生成）"""
        permissions = self.get_user_permissions(user_id)
        has_all = '*' in permissions

        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(''' SELECT module_id, module_name, module_code, module_url, module_icon, parent_id, sort_order, required_permission, is_visible, created_at FROM permission_modules WHERE is_visible = 1 ORDER BY sort_order ASC, module_id ASC ''')
                rows = cursor.fetchall()
                conn.close()

                modules = []
                for row in rows:
                    required = row['required_permission']
                    if has_all or not required or required in permissions:
                        modules.append({
                            'module_id': row['module_id'],
                            'module_name': row['module_name'],
                            'module_code': row['module_code'],
                            'module_url': row['module_url'],
                            'module_icon': row['module_icon'],
                            'parent_id': row['parent_id'],
                            'sort_order': row['sort_order'],
                            'required_permission': required,
                            'is_visible': bool(row['is_visible']),
                            'created_at': row['created_at']
                        })
                return modules
            except Exception as e:
                logger(f'[PermissionService] 获取可访问模块失败: {e}')
                try:
                    conn.close()
                except Exception:
                    pass
                return []

    # ========== 按钮权限 ==========

    def get_module_buttons(self, module_code: str) -> List[Dict[str, Any]]:
        """获取模块下的所有按钮"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(''' SELECT b.button_id, b.module_id, b.button_name, b.button_code, b.button_label, b.parent_button_id, b.sort_order, b.is_visible, b.created_at, m.module_name, m.module_code FROM permission_buttons b INNER JOIN permission_modules m ON b.module_id = m.module_id WHERE m.module_code = ? AND b.is_visible = 1 ORDER BY b.sort_order ASC, b.button_id ASC ''', (module_code,))
                rows = cursor.fetchall()
                conn.close()

                buttons = []
                for row in rows:
                    buttons.append({
                        'button_id': row['button_id'],
                        'module_id': row['module_id'],
                        'module_name': row['module_name'],
                        'module_code': row['module_code'],
                        'button_name': row['button_name'],
                        'button_code': row['button_code'],
                        'button_label': row['button_label'],
                        'parent_button_id': row['parent_button_id'],
                        'sort_order': row['sort_order'],
                        'is_visible': bool(row['is_visible']),
                        'created_at': row['created_at']
                    })
                return buttons
            except Exception as e:
                logger(f'[PermissionService] 获取模块按钮失败: {e}')
                try:
                    conn.close()
                except Exception:
                    pass
                return []

    def get_all_buttons(self) -> List[Dict[str, Any]]:
        """获取所有按钮"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(''' SELECT b.button_id, b.module_id, b.button_name, b.button_code, b.button_label, b.parent_button_id, b.sort_order, b.is_visible, b.created_at, m.module_name, m.module_code FROM permission_buttons b INNER JOIN permission_modules m ON b.module_id = m.module_id ORDER BY m.sort_order ASC, b.sort_order ASC ''')
                rows = cursor.fetchall()
                conn.close()

                buttons = []
                for row in rows:
                    buttons.append({
                        'button_id': row['button_id'],
                        'module_id': row['module_id'],
                        'module_name': row['module_name'],
                        'module_code': row['module_code'],
                        'button_name': row['button_name'],
                        'button_code': row['button_code'],
                        'button_label': row['button_label'],
                        'parent_button_id': row['parent_button_id'],
                        'sort_order': row['sort_order'],
                        'is_visible': bool(row['is_visible']),
                        'created_at': row['created_at']
                    })
                return buttons
            except Exception as e:
                logger(f'[PermissionService] 获取所有按钮失败: {e}')
                try:
                    conn.close()
                except Exception:
                    pass
                return []

    def add_button(self, module_code: str, button_name: str, button_code: str,
                   button_label: str = '', parent_button_id: int = None,
                   sort_order: int = 0) -> Dict[str, Any]:
        """添加按钮"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()

                cursor.execute('SELECT module_id FROM permission_modules WHERE module_code = ?', (module_code,))
                module_row = cursor.fetchone()
                if module_row is None:
                    conn.close()
                    return {'success': False, 'message': f'模块不存在: {module_code}'}

                module_id = module_row['module_id']
                cursor.execute('SELECT button_id FROM permission_buttons WHERE module_id = ? AND button_code = ?',
                (module_id, button_code))
                if cursor.fetchone() is not None:
                    conn.close()
                    return {'success': False, 'message': f'按钮编码已存在: {button_code}'}

                cursor.execute(''' INSERT INTO permission_buttons (module_id, button_name, button_code, button_label, parent_button_id, sort_order) VALUES (?, ?, ?, ?, ?, ?) ''', (module_id, button_name, button_code, button_label, parent_button_id, sort_order))
                conn.commit()
                button_id = cursor.lastrowid
                conn.close()

                return {'success': True, 'message': f'按钮添加成功: {button_name}', 'button_id': button_id}
            except Exception as e:
                logger(f'[PermissionService] 添加按钮失败: {e}')
                try:
                    conn.close()
                except Exception:
                    pass
                return {'success': False, 'message': f'添加按钮失败: {str(e)}'}

    def check_button_permission(self, user_id: str, module_code: str, button_code: str) -> bool:
        """检查用户是否拥有按钮权限"""
        roles = self.get_user_roles(user_id)
        
        for role in roles:
            if '*' in role.get('permissions', []):
                return True

        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()

                cursor.execute('SELECT module_id FROM permission_modules WHERE module_code = ?', (module_code,))
                module_row = cursor.fetchone()
                if module_row is None:
                    conn.close()
                    return False

                module_id = module_row['module_id']
                cursor.execute('SELECT button_id FROM permission_buttons WHERE module_id = ? AND button_code = ?',
                (module_id, button_code))
                button_row = cursor.fetchone()
                if button_row is None:
                    conn.close()
                    return True

                button_id = button_row['button_id']

                role_ids = [role['role_id'] for role in roles]
                if not role_ids:
                    conn.close()
                    return False

                placeholders = ','.join('?' * len(role_ids))
                cursor.execute(f''' SELECT COUNT(*) AS cnt FROM role_button_permissions WHERE button_id = ? AND role_id IN ({placeholders}) AND allowed = 1 ''', (button_id, *role_ids))
                count = cursor.fetchone()['cnt']
                conn.close()

                return count > 0
            except Exception as e:
                logger(f'[PermissionService] 检查按钮权限失败: {e}')
                try:
                    conn.close()
                except Exception:
                    pass
                return False

    def get_user_button_permissions(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户所有按钮权限"""
        roles = self.get_user_roles(user_id)
        
        for role in roles:
            if '*' in role.get('permissions', []):
                all_buttons = self.get_all_buttons()
                return [{'module_code': b['module_code'], 'button_code': b['button_code'],
                'allowed': True} for b in all_buttons]

        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()

                role_ids = [role['role_id'] for role in roles]
                if not role_ids:
                    conn.close()
                    return []

                placeholders = ','.join('?' * len(role_ids))
                cursor.execute(f''' SELECT b.module_code, b.button_code, bp.allowed FROM role_button_permissions bp INNER JOIN permission_buttons btn ON bp.button_id = btn.button_id INNER JOIN permission_modules b ON btn.module_id = b.module_id WHERE bp.role_id IN ({placeholders}) ''', tuple(role_ids))
                rows = cursor.fetchall()
                conn.close()

                permissions = []
                for row in rows:
                    permissions.append({
                        'module_code': row['module_code'],
                        'button_code': row['button_code'],
                        'allowed': bool(row['allowed'])
                    })
                return permissions
            except Exception as e:
                logger(f'[PermissionService] 获取用户按钮权限失败: {e}')
                try:
                    conn.close()
                except Exception:
                    pass
                return []

    def delete_button(self, button_id: int) -> Dict[str, Any]:
        """删除按钮"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()

                cursor.execute('SELECT button_id, button_code FROM permission_buttons WHERE button_id = ?', (button_id,
                ))
                row = cursor.fetchone()
                if row is None:
                    conn.close()
                    return {'success': False, 'message': f'按钮不存在: {button_id}'}

                button_code = row['button_code']
                cursor.execute('DELETE FROM permission_buttons WHERE button_id = ?', (button_id,))
                conn.commit()
                conn.close()

                return {'success': True, 'message': f'按钮已删除: {button_code}'}
            except Exception as e:
                logger(f'[PermissionService] 删除按钮失败: {e}')
                try:
                    conn.close()
                except Exception:
                    pass
                return {'success': False, 'message': f'删除按钮失败: {str(e)}'}

    # ========== 数据权限 ==========

    def get_data_rules(self, role_code: str = None, module_code: str = None) -> List[Dict[str, Any]]:
        """获取数据权限规则"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()

                query = ''' SELECT dr.rule_id, dr.role_id, dr.module_code, dr.data_scope, dr.data_level, dr.special_rules, dr.is_active, dr.created_at, r.role_name, r.role_code FROM permission_data_rules dr INNER JOIN permission_roles r ON dr.role_id = r.role_id WHERE 1=1 '''
                params = []

                if role_code:
                    query += ' AND r.role_code = ?'
                    params.append(role_code)
                if module_code:
                    query += ' AND dr.module_code = ?'
                    params.append(module_code)

                query += ' ORDER BY r.role_code, dr.module_code'
                cursor.execute(query, params)
                rows = cursor.fetchall()
                conn.close()

                rules = []
                for row in rows:
                    try:
                        special_rules = json.loads(row['special_rules']) if row['special_rules'] else {}
                    except (json.JSONDecodeError, TypeError):
                        special_rules = {}
                    rules.append({
                        'rule_id': row['rule_id'],
                        'role_id': row['role_id'],
                        'role_code': row['role_code'],
                        'role_name': row['role_name'],
                        'module_code': row['module_code'],
                        'data_scope': row['data_scope'],
                        'data_level': row['data_level'],
                        'special_rules': special_rules,
                        'is_active': bool(row['is_active']),
                        'created_at': row['created_at']
                    })
                return rules
            except Exception as e:
                logger(f'[PermissionService] 获取数据权限规则失败: {e}')
                try:
                    conn.close()
                except Exception:
                    pass
                return []

    def get_user_data_permission(self, user_id: str, module_code: str) -> Dict[str, Any]:
        """获取用户在指定模块的数据权限"""
        roles = self.get_user_roles(user_id)
        
        for role in roles:
            if '*' in role.get('permissions', []):
                return {'data_scope': 'all', 'data_level': 'full', 'special_rules': {}}

        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()

                role_ids = [role['role_id'] for role in roles]
                if not role_ids:
                    conn.close()
                    return {'data_scope': 'none', 'data_level': 'none', 'special_rules': {}}

                placeholders = ','.join('?' * len(role_ids))
                cursor.execute(f''' SELECT data_scope, data_level, special_rules FROM permission_data_rules WHERE role_id IN ({placeholders}) AND (module_code = ? OR module_code = '*') ORDER BY CASE WHEN module_code = ? THEN 0 ELSE 1 END LIMIT 1 ''', (*role_ids, module_code, module_code))
                row = cursor.fetchone()
                conn.close()

                if row:
                    try:
                        special_rules = json.loads(row['special_rules']) if row['special_rules'] else {}
                    except (json.JSONDecodeError, TypeError):
                        special_rules = {}
                    return {
                        'data_scope': row['data_scope'],
                        'data_level': row['data_level'],
                        'special_rules': special_rules
                    }
                return {'data_scope': 'none', 'data_level': 'none', 'special_rules': {}}
            except Exception as e:
                logger(f'[PermissionService] 获取用户数据权限失败: {e}')
                try:
                    conn.close()
                except Exception:
                    pass
                return {'data_scope': 'none', 'data_level': 'none', 'special_rules': {}}

    def update_data_rule(self, role_code: str, module_code: str, data_scope: str, 
                         data_level: str, special_rules: dict = None) -> Dict[str, Any]:
        """更新数据权限规则"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()

                cursor.execute('SELECT role_id FROM permission_roles WHERE role_code = ?', (role_code,))
                role_row = cursor.fetchone()
                if role_row is None:
                    conn.close()
                    return {'success': False, 'message': f'角色不存在: {role_code}'}

                role_id = role_row['role_id']
                special_rules_json = json.dumps(special_rules or {}, ensure_ascii=False)

                cursor.execute(''' INSERT OR REPLACE INTO permission_data_rules (role_id, module_code, data_scope, data_level, special_rules) VALUES (?, ?, ?, ?, ?) ''', (role_id, module_code, data_scope, data_level, special_rules_json))
                conn.commit()
                conn.close()

                return {'success': True, 'message': '数据权限规则更新成功'}
            except Exception as e:
                logger(f'[PermissionService] 更新数据权限规则失败: {e}')
                try:
                    conn.close()
                except Exception:
                    pass
                return {'success': False, 'message': f'更新数据权限规则失败: {str(e)}'}

    def update_data_rule_by_id(self, rule_id: int, data_scope: str = None, 
                                data_level: str = None) -> Dict[str, Any]:
        """通过ID更新数据权限规则"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()

                cursor.execute('SELECT rule_id FROM permission_data_rules WHERE rule_id = ?', (rule_id,))
                if cursor.fetchone() is None:
                    conn.close()
                    return {'success': False, 'message': f'规则不存在: {rule_id}'}

                updates = []
                params = []
                if data_scope:
                    updates.append('data_scope = ?')
                    params.append(data_scope)
                if data_level:
                    updates.append('data_level = ?')
                    params.append(data_level)

                if not updates:
                    conn.close()
                    return {'success': False, 'message': '没有可更新的字段'}

                params.append(rule_id)
                cursor.execute(f'UPDATE permission_data_rules SET {", ".join(updates)} WHERE rule_id = ?', params)
                conn.commit()
                conn.close()

                return {'success': True, 'message': '数据权限规则更新成功'}
            except Exception as e:
                logger(f'[PermissionService] 更新数据权限规则失败: {e}')
                try:
                    conn.close()
                except Exception:
                    pass
                return {'success': False, 'message': f'更新数据权限规则失败: {str(e)}'}

    def delete_data_rule(self, rule_id: int) -> Dict[str, Any]:
        """删除数据权限规则"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()

                cursor.execute('SELECT rule_id, module_code FROM permission_data_rules WHERE rule_id = ?', (rule_id,))
                row = cursor.fetchone()
                if row is None:
                    conn.close()
                    return {'success': False, 'message': f'规则不存在: {rule_id}'}

                module_code = row['module_code']
                cursor.execute('DELETE FROM permission_data_rules WHERE rule_id = ?', (rule_id,))
                conn.commit()
                conn.close()

                return {'success': True, 'message': f'数据权限规则已删除: {module_code}'}
            except Exception as e:
                logger(f'[PermissionService] 删除数据权限规则失败: {e}')
                try:
                    conn.close()
                except Exception:
                    pass
                return {'success': False, 'message': f'删除数据权限规则失败: {str(e)}'}

    # ========== 接口权限 ==========

    def get_api_rules(self, role_code: str = None) -> List[Dict[str, Any]]:
        """获取接口权限规则"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()

                query = ''' SELECT ar.rule_id, ar.role_id, ar.api_path, ar.api_method, ar.allowed, ar.is_active, ar.created_at, r.role_name, r.role_code FROM permission_api_rules ar INNER JOIN permission_roles r ON ar.role_id = r.role_id WHERE 1=1 '''
                params = []

                if role_code:
                    query += ' AND r.role_code = ?'
                    params.append(role_code)

                query += ' ORDER BY r.role_code, ar.api_path'
                cursor.execute(query, params)
                rows = cursor.fetchall()
                conn.close()

                rules = []
                for row in rows:
                    rules.append({
                        'rule_id': row['rule_id'],
                        'role_id': row['role_id'],
                        'role_code': row['role_code'],
                        'role_name': row['role_name'],
                        'api_path': row['api_path'],
                        'api_method': row['api_method'],
                        'allowed': bool(row['allowed']),
                        'is_active': bool(row['is_active']),
                        'created_at': row['created_at']
                    })
                return rules
            except Exception as e:
                logger(f'[PermissionService] 获取接口权限规则失败: {e}')
                try:
                    conn.close()
                except Exception:
                    pass
                return []

    def check_api_permission(self, user_id: str, api_path: str, api_method: str = 'GET') -> bool:
        """检查用户是否拥有接口权限"""
        roles = self.get_user_roles(user_id)
        
        for role in roles:
            if '*' in role.get('permissions', []):
                return True

        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()

                role_ids = [role['role_id'] for role in roles]
                if not role_ids:
                    conn.close()
                    return False

                placeholders = ','.join('?' * len(role_ids))
                cursor.execute(f''' SELECT allowed, api_path FROM permission_api_rules WHERE role_id IN ({placeholders}) AND is_active = 1 AND (api_method = ? OR api_method = '*') ORDER BY CASE WHEN api_path = ? THEN 0 WHEN api_path LIKE '%*%' THEN 1 WHEN api_path = '*' THEN 2 ELSE 3 END ''', (*role_ids, api_method, api_path))
                rows = cursor.fetchall()
                conn.close()

                for row in rows:
                    rule_path = row['api_path']
                    allowed = bool(row['allowed'])
                    
                    if rule_path == api_path or rule_path == '*':
                        return allowed
                    
                    if '*' in rule_path:
                        pattern = rule_path.replace('*', '%')
                        if api_path.startswith(rule_path[:rule_path.index('*')]):
                            return allowed

                return False
            except Exception as e:
                logger(f'[PermissionService] 检查接口权限失败: {e}')
                try:
                    conn.close()
                except Exception:
                    pass
                return False

    def add_api_rule(self, role_code: str, api_path: str, api_method: str = 'GET', allowed: bool = True) -> Dict[str,
    Any]:
        """添加接口权限规则"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()

                cursor.execute('SELECT role_id FROM permission_roles WHERE role_code = ?', (role_code,))
                role_row = cursor.fetchone()
                if role_row is None:
                    conn.close()
                    return {'success': False, 'message': f'角色不存在: {role_code}'}

                role_id = role_row['role_id']

                cursor.execute(''' INSERT OR REPLACE INTO permission_api_rules (role_id, api_path, api_method, allowed) VALUES (?, ?, ?, ?) ''', (role_id, api_path, api_method, 1 if allowed else 0))
                conn.commit()
                conn.close()

                return {'success': True, 'message': '接口权限规则添加成功'}
            except Exception as e:
                logger(f'[PermissionService] 添加接口权限规则失败: {e}')
                try:
                    conn.close()
                except Exception:
                    pass
                return {'success': False, 'message': f'添加接口权限规则失败: {str(e)}'}

    def update_api_rule_by_id(self, rule_id: int, allowed: bool = None) -> Dict[str, Any]:
        """通过ID更新接口权限规则"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()

                cursor.execute('SELECT rule_id FROM permission_api_rules WHERE rule_id = ?', (rule_id,))
                if cursor.fetchone() is None:
                    conn.close()
                    return {'success': False, 'message': f'规则不存在: {rule_id}'}

                if allowed is None:
                    conn.close()
                    return {'success': False, 'message': '没有可更新的字段'}

                cursor.execute('UPDATE permission_api_rules SET allowed = ? WHERE rule_id = ?', (1 if allowed else 0,
                rule_id))
                conn.commit()
                conn.close()

                return {'success': True, 'message': '接口权限规则更新成功'}
            except Exception as e:
                logger(f'[PermissionService] 更新接口权限规则失败: {e}')
                try:
                    conn.close()
                except Exception:
                    pass
                return {'success': False, 'message': f'更新接口权限规则失败: {str(e)}'}

    def delete_api_rule(self, rule_id: int) -> Dict[str, Any]:
        """删除接口权限规则"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()

                cursor.execute('SELECT rule_id, api_path FROM permission_api_rules WHERE rule_id = ?', (rule_id,))
                row = cursor.fetchone()
                if row is None:
                    conn.close()
                    return {'success': False, 'message': f'规则不存在: {rule_id}'}

                api_path = row['api_path']
                cursor.execute('DELETE FROM permission_api_rules WHERE rule_id = ?', (rule_id,))
                conn.commit()
                conn.close()

                return {'success': True, 'message': f'接口权限规则已删除: {api_path}'}
            except Exception as e:
                logger(f'[PermissionService] 删除接口权限规则失败: {e}')
                try:
                    conn.close()
                except Exception:
                    pass
                return {'success': False, 'message': f'删除接口权限规则失败: {str(e)}'}

    # ========== 角色分配 ==========

    def assign_role(self, user_id: str, role_code: str,
                    assigned_by: Optional[str] = None,
                    expires_at: Optional[str] = None) -> Dict[str, Any]:
        """为用户分配角色"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()

                cursor.execute('SELECT role_id, role_name FROM permission_roles WHERE role_code = ?', (role_code,))
                row = cursor.fetchone()
                if row is None:
                    return {'success': False, 'message': f'角色不存在: {role_code}'}

                role_id = row['role_id']
                role_name = row['role_name']

                # 检查是否已分配（未过期的相同角色）
                cursor.execute(''' SELECT id, expires_at FROM user_role_assignments WHERE user_id = ? AND role_id = ? ORDER BY assigned_at DESC LIMIT 1 ''', (user_id, role_id))
                existing = cursor.fetchone()
                if existing is not None:
                    now = datetime.now().isoformat()
                    if existing['expires_at'] is None or existing['expires_at'] >= now:
                        return {'success': False, 'message': f'用户已拥有该角色: {role_name}'}

                cursor.execute(''' INSERT INTO user_role_assignments (user_id, role_id, assigned_by, expires_at) VALUES (?, ?, ?, ?) ''', (user_id, role_id, assigned_by, expires_at))
                conn.commit()
                conn.close()

                self.audit_log(
                    user_id=assigned_by,
                    action='assign_role',
                    module='permission',
                    resource=f'user:{user_id}',
                    status='success',
                    details=json.dumps({
                        'target_user_id': user_id,
                        'role_code': role_code,
                        'expires_at': expires_at
                    }, ensure_ascii=False)
                )

                return {
                    'success': True,
                    'message': f'角色分配成功: {role_name}',
                    'role_code': role_code
                }
            except Exception as e:
                logger(f'[PermissionService] 分配角色失败: {e}')
                try:
                    conn.close()
                except Exception:
                    pass
                return {'success': False, 'message': f'分配角色失败: {str(e)}'}

    def revoke_role(self, user_id: str, role_code: str) -> Dict[str, Any]:
        """撤销用户角色"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()

                cursor.execute('SELECT role_id, role_name FROM permission_roles WHERE role_code = ?', (role_code,))
                row = cursor.fetchone()
                if row is None:
                    return {'success': False, 'message': f'角色不存在: {role_code}'}

                role_id = row['role_id']
                role_name = row['role_name']

                cursor.execute(''' DELETE FROM user_role_assignments WHERE user_id = ? AND role_id = ? ''', (user_id, role_id))
                affected = cursor.rowcount
                conn.commit()
                conn.close()

                if affected == 0:
                    return {'success': False, 'message': f'用户未拥有该角色: {role_name}'}

                self.audit_log(
                    user_id=user_id,
                    action='revoke_role',
                    module='permission',
                    resource=f'user:{user_id}',
                    status='success',
                    details=json.dumps({
                        'target_user_id': user_id,
                        'role_code': role_code
                    }, ensure_ascii=False)
                )

                return {
                    'success': True,
                    'message': f'角色已撤销: {role_name}',
                    'role_code': role_code
                }
            except Exception as e:
                logger(f'[PermissionService] 撤销角色失败: {e}')
                try:
                    conn.close()
                except Exception:
                    pass
                return {'success': False, 'message': f'撤销角色失败: {str(e)}'}

    # ========== 模块管理 ==========

    def get_all_modules(self) -> List[Dict[str, Any]]:
        """获取所有功能模块"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(''' SELECT module_id, module_name, module_code, module_url, module_icon, parent_id, sort_order, required_permission, is_visible, created_at FROM permission_modules ORDER BY sort_order ASC, module_id ASC ''')
                rows = cursor.fetchall()
                conn.close()

                modules = []
                for row in rows:
                    modules.append({
                        'module_id': row['module_id'],
                        'module_name': row['module_name'],
                        'module_code': row['module_code'],
                        'module_url': row['module_url'],
                        'module_icon': row['module_icon'],
                        'parent_id': row['parent_id'],
                        'sort_order': row['sort_order'],
                        'required_permission': row['required_permission'],
                        'is_visible': bool(row['is_visible']),
                        'created_at': row['created_at']
                    })
                return modules
            except Exception as e:
                logger(f'[PermissionService] 获取所有模块失败: {e}')
                try:
                    conn.close()
                except Exception:
                    pass
                return []

    def add_module(self, module_name: str, module_code: str, module_url: str = '',
                   module_icon: str = '', parent_id: Optional[int] = None,
                   sort_order: int = 0, required_permission: str = '',
                   is_visible: bool = True) -> Dict[str, Any]:
        """添加功能模块"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()

                cursor.execute('SELECT module_id FROM permission_modules WHERE module_code = ?', (module_code,))
                if cursor.fetchone() is not None:
                    conn.close()
                    return {'success': False, 'message': f'模块编码已存在: {module_code}'}

                cursor.execute(''' INSERT INTO permission_modules (module_name, module_code, module_url, module_icon, parent_id, sort_order, required_permission, is_visible) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ''', (
                    module_name, module_code, module_url, module_icon,
                    parent_id, sort_order, required_permission, 1 if is_visible else 0
                ))
                conn.commit()
                module_id = cursor.lastrowid
                conn.close()

                self.audit_log(
                    user_id='system',
                    action='add_module',
                    module='permission',
                    resource=f'module:{module_code}',
                    status='success',
                    details=json.dumps({
                        'module_id': module_id,
                        'module_name': module_name,
                        'module_code': module_code
                    }, ensure_ascii=False)
                )

                return {
                    'success': True,
                    'message': f'模块添加成功: {module_name}',
                    'module_id': module_id
                }
            except Exception as e:
                logger(f'[PermissionService] 添加模块失败: {e}')
                try:
                    conn.close()
                except Exception:
                    pass
                return {'success': False, 'message': f'添加模块失败: {str(e)}'}

    def update_module(self, module_id: int, **kwargs) -> Dict[str, Any]:
        """更新功能模块"""
        allowed_fields = {
            'module_name', 'module_code', 'module_url', 'module_icon',
            'parent_id', 'sort_order', 'required_permission', 'is_visible'
        }

        updates = {}
        for key, value in kwargs.items():
            if key in allowed_fields:
                if key == 'is_visible':
                    updates[key] = 1 if value else 0
                else:
                    updates[key] = value

        if not updates:
            return {'success': False, 'message': '没有可更新的字段'}

        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()

                cursor.execute('SELECT module_id, module_code FROM permission_modules WHERE module_id = ?', (module_id,
                ))
                row = cursor.fetchone()
                if row is None:
                    conn.close()
                    return {'success': False, 'message': f'模块不存在: {module_id}'}

                set_clauses = [f'{field} = ?' for field in updates.keys()]
                values = list(updates.values())
                values.append(module_id)

                cursor.execute(
                    f"UPDATE permission_modules SET {', '.join(set_clauses)} WHERE module_id = ?",
                    values
                )
                conn.commit()
                conn.close()

                self.audit_log(
                    user_id='system',
                    action='update_module',
                    module='permission',
                    resource=f'module:{row["module_code"]}',
                    status='success',
                    details=json.dumps({'module_id': module_id, 'updates': updates}, ensure_ascii=False)
                )

                return {'success': True, 'message': f'模块更新成功: {module_id}'}
            except Exception as e:
                logger(f'[PermissionService] 更新模块失败: {e}')
                try:
                    conn.close()
                except Exception:
                    pass
                return {'success': False, 'message': f'更新模块失败: {str(e)}'}

    def delete_module(self, module_id: int) -> Dict[str, Any]:
        """删除功能模块"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()

                cursor.execute('SELECT module_id, module_code FROM permission_modules WHERE module_id = ?', (module_id,
                ))
                row = cursor.fetchone()
                if row is None:
                    conn.close()
                    return {'success': False, 'message': f'模块不存在: {module_id}'}

                module_code = row['module_code']

                # 将子模块的 parent_id 置空
                cursor.execute('UPDATE permission_modules SET parent_id = NULL WHERE parent_id = ?', (module_id,))
                cursor.execute('DELETE FROM permission_modules WHERE module_id = ?', (module_id,))
                conn.commit()
                conn.close()

                self.audit_log(
                    user_id='system',
                    action='delete_module',
                    module='permission',
                    resource=f'module:{module_code}',
                    status='success',
                    details=json.dumps({'module_id': module_id}, ensure_ascii=False)
                )

                return {'success': True, 'message': f'模块已删除: {module_code}'}
            except Exception as e:
                logger(f'[PermissionService] 删除模块失败: {e}')
                try:
                    conn.close()
                except Exception:
                    pass
                return {'success': False, 'message': f'删除模块失败: {str(e)}'}

    # ========== 角色管理 ==========

    def get_all_roles(self) -> List[Dict[str, Any]]:
        """获取所有角色"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(''' SELECT role_id, role_name, role_code, description, permissions, is_system, created_at FROM permission_roles ORDER BY is_system DESC, role_id ASC ''')
                rows = cursor.fetchall()
                conn.close()

                roles = []
                for row in rows:
                    try:
                        permissions = json.loads(row['permissions']) if row['permissions'] else []
                    except (json.JSONDecodeError, TypeError):
                        permissions = []
                    roles.append({
                        'role_id': row['role_id'],
                        'role_name': row['role_name'],
                        'role_code': row['role_code'],
                        'description': row['description'],
                        'permissions': permissions,
                        'is_system': bool(row['is_system']),
                        'created_at': row['created_at']
                    })
                return roles
            except Exception as e:
                logger(f'[PermissionService] 获取所有角色失败: {e}')
                try:
                    conn.close()
                except Exception:
                    pass
                return []

    def create_role(self, role_name: str, role_code: str,
                    permissions: List[str], description: str = '') -> Dict[str, Any]:
        """创建角色"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()

                cursor.execute('SELECT role_id FROM permission_roles WHERE role_code = ?', (role_code,))
                if cursor.fetchone() is not None:
                    conn.close()
                    return {'success': False, 'message': f'角色编码已存在: {role_code}'}

                cursor.execute(''' INSERT INTO permission_roles (role_name, role_code, description, permissions, is_system) VALUES (?, ?, ?, ?, 0) ''', (
                    role_name, role_code, description,
                    json.dumps(permissions, ensure_ascii=False)
                ))
                conn.commit()
                role_id = cursor.lastrowid
                conn.close()

                self.audit_log(
                    user_id='system',
                    action='create_role',
                    module='permission',
                    resource=f'role:{role_code}',
                    status='success',
                    details=json.dumps({
                        'role_id': role_id,
                        'role_name': role_name,
                        'permissions': permissions
                    }, ensure_ascii=False)
                )

                return {
                    'success': True,
                    'message': f'角色创建成功: {role_name}',
                    'role_id': role_id
                }
            except Exception as e:
                logger(f'[PermissionService] 创建角色失败: {e}')
                try:
                    conn.close()
                except Exception:
                    pass
                return {'success': False, 'message': f'创建角色失败: {str(e)}'}

    def update_role(self, role_id: int, **kwargs) -> Dict[str, Any]:
        """更新角色"""
        allowed_fields = {'role_name', 'role_code', 'description', 'permissions'}

        updates = {}
        for key, value in kwargs.items():
            if key in allowed_fields:
                if key == 'permissions':
                    updates[key] = json.dumps(value, ensure_ascii=False) if isinstance(value, list) else value
                else:
                    updates[key] = value

        if not updates:
            return {'success': False, 'message': '没有可更新的字段'}

        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()

                cursor.execute('SELECT role_id, role_code, is_system FROM permission_roles WHERE role_id = ?', (role_id,
                ))
                row = cursor.fetchone()
                if row is None:
                    conn.close()
                    return {'success': False, 'message': f'角色不存在: {role_id}'}

                # 系统角色不允许修改 role_code
                if row['is_system'] == 1 and 'role_code' in updates:
                    del updates['role_code']

                if not updates:
                    conn.close()
                    return {'success': False, 'message': '系统角色的编码不可修改'}

                set_clauses = [f'{field} = ?' for field in updates.keys()]
                values = list(updates.values())
                values.append(role_id)

                cursor.execute(
                    f"UPDATE permission_roles SET {', '.join(set_clauses)} WHERE role_id = ?",
                    values
                )
                conn.commit()
                conn.close()

                self.audit_log(
                    user_id='system',
                    action='update_role',
                    module='permission',
                    resource=f'role:{row["role_code"]}',
                    status='success',
                    details=json.dumps({'role_id': role_id, 'updates': updates}, ensure_ascii=False)
                )

                return {'success': True, 'message': f'角色更新成功: {role_id}'}
            except Exception as e:
                logger(f'[PermissionService] 更新角色失败: {e}')
                try:
                    conn.close()
                except Exception:
                    pass
                return {'success': False, 'message': f'更新角色失败: {str(e)}'}

    def delete_role(self, role_id: int) -> Dict[str, Any]:
        """删除角色（系统角色不可删除）"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()

                cursor.execute('SELECT role_id, role_code, role_name, is_system FROM permission_roles WHERE role_id = ?', (role_id,))
                row = cursor.fetchone()
                if row is None:
                    conn.close()
                    return {'success': False, 'message': f'角色不存在: {role_id}'}

                if row['is_system'] == 1:
                    conn.close()
                    return {'success': False, 'message': f'系统角色不可删除: {row["role_name"]}'}

                role_code = row['role_code']

                cursor.execute('DELETE FROM permission_roles WHERE role_id = ?', (role_id,))
                conn.commit()
                conn.close()

                self.audit_log(
                    user_id='system',
                    action='delete_role',
                    module='permission',
                    resource=f'role:{role_code}',
                    status='success',
                    details=json.dumps({'role_id': role_id}, ensure_ascii=False)
                )

                return {'success': True, 'message': f'角色已删除: {role_code}'}
            except Exception as e:
                logger(f'[PermissionService] 删除角色失败: {e}')
                try:
                    conn.close()
                except Exception:
                    pass
                return {'success': False, 'message': f'删除角色失败: {str(e)}'}

    # ========== 审计日志 ==========

    def audit_log(self, user_id: str, action: str, module: str,
                  resource: str, status: str = 'success',
                  permission_level: Optional[str] = None,
                  ip_address: Optional[str] = None,
                  details: Optional[str] = None):
        """记录权限审计日志"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                log_id = str(uuid.uuid4())
                cursor.execute(''' INSERT INTO permission_audit_logs (log_id, user_id, action, module, resource, permission_level, status, ip_address, details) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (
                    log_id, user_id, action, module, resource,
                    permission_level, status, ip_address, details
                ))
                conn.commit()
                conn.close()
                return log_id
            except Exception as e:
                logger(f'[PermissionService] 记录审计日志失败: {e}')
                try:
                    conn.close()
                except Exception:
                    pass
                return None

    def get_audit_logs(self, user_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """获取权限审计日志"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()

                if user_id:
                    cursor.execute(''' SELECT log_id, user_id, action, module, resource, permission_level, status, ip_address, details, created_at FROM permission_audit_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT ? ''', (user_id, limit))
                else:
                    cursor.execute(''' SELECT log_id, user_id, action, module, resource, permission_level, status, ip_address, details, created_at FROM permission_audit_logs ORDER BY created_at DESC LIMIT ? ''', (limit,))

                rows = cursor.fetchall()
                conn.close()

                logs = []
                for row in rows:
                    details = row['details']
                    try:
                        if details:
                            details_data = json.loads(details)
                        else:
                            details_data = None
                    except (json.JSONDecodeError, TypeError):
                        details_data = details

                    logs.append({
                        'log_id': row['log_id'],
                        'user_id': row['user_id'],
                        'action': row['action'],
                        'module': row['module'],
                        'resource': row['resource'],
                        'permission_level': row['permission_level'],
                        'status': row['status'],
                        'ip_address': row['ip_address'],
                        'details': details_data,
                        'created_at': row['created_at']
                    })
                return logs
            except Exception as e:
                logger(f'[PermissionService] 获取审计日志失败: {e}')
                try:
                    conn.close()
                except Exception:
                    pass
                return []

    # ========== 统计信息 ==========

    def get_permission_stats(self) -> Dict[str, Any]:
        """获取权限统计信息"""
        with self.lock:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()

                # 角色数
                cursor.execute('SELECT COUNT(*) AS cnt FROM permission_roles')
                role_count = cursor.fetchone()['cnt']

                # 系统角色数
                cursor.execute('SELECT COUNT(*) AS cnt FROM permission_roles WHERE is_system = 1')
                system_role_count = cursor.fetchone()['cnt']

                # 模块数
                cursor.execute('SELECT COUNT(*) AS cnt FROM permission_modules')
                module_count = cursor.fetchone()['cnt']

                # 可见模块数
                cursor.execute('SELECT COUNT(*) AS cnt FROM permission_modules WHERE is_visible = 1')
                visible_module_count = cursor.fetchone()['cnt']

                # 分配的角色记录数
                cursor.execute('SELECT COUNT(*) AS cnt FROM user_role_assignments')
                assignment_count = cursor.fetchone()['cnt']

                # 不同用户数
                cursor.execute('SELECT COUNT(DISTINCT user_id) AS cnt FROM user_role_assignments')
                user_with_role_count = cursor.fetchone()['cnt']

                # 审计日志数
                cursor.execute('SELECT COUNT(*) AS cnt FROM permission_audit_logs')
                audit_log_count = cursor.fetchone()['cnt']

                # 各角色用户数统计
                cursor.execute(''' SELECT r.role_code, r.role_name, COUNT(a.user_id) AS user_count FROM permission_roles r LEFT JOIN user_role_assignments a ON r.role_id = a.role_id GROUP BY r.role_id ORDER BY user_count DESC ''')
                role_distribution = []
                for row in cursor.fetchall():
                    role_distribution.append({
                        'role_code': row['role_code'],
                        'role_name': row['role_name'],
                        'user_count': row['user_count']
                    })

                conn.close()

                return {
                    'role_count': role_count,
                    'system_role_count': system_role_count,
                    'custom_role_count': role_count - system_role_count,
                    'module_count': module_count,
                    'visible_module_count': visible_module_count,
                    'hidden_module_count': module_count - visible_module_count,
                    'assignment_count': assignment_count,
                    'user_with_role_count': user_with_role_count,
                    'audit_log_count': audit_log_count,
                    'role_distribution': role_distribution
                }
            except Exception as e:
                logger(f'[PermissionService] 获取权限统计失败: {e}')
                try:
                    conn.close()
                except Exception:
                    pass
                return {
                    'role_count': 0,
                    'system_role_count': 0,
                    'custom_role_count': 0,
                    'module_count': 0,
                    'visible_module_count': 0,
                    'hidden_module_count': 0,
                    'assignment_count': 0,
                    'user_with_role_count': 0,
                    'audit_log_count': 0,
                    'role_distribution': []
                }


# 全局实例
permission_service = PermissionOptimizerService()


if __name__ == '__main__':
    # 简单自测
    print('=== 权限服务自测 ===')
    stats = permission_service.get_permission_stats()
    print(f'统计信息: {json.dumps(stats, ensure_ascii=False, indent=2)}')

    print('\n=== 所有角色 ===')
    for role in permission_service.get_all_roles():
        print(f'- {role["role_code"]}: {role["permissions"]}')

    print('\n=== 所有模块 ===')
    for module in permission_service.get_all_modules():
        print(f'- {module["module_code"]}: {module["module_url"]} (需要权限: {module["required_permission"]})')

    print('\n=== 测试用户角色分配 ===')
    result = permission_service.assign_role('test_user_001', 'teacher', assigned_by='admin')
    print(f'分配角色: {result}')

    print('\n=== 用户角色 ===')
    for role in permission_service.get_user_roles('test_user_001'):
        print(f'- {role["role_code"]}')

    print('\n=== 用户权限 ===')
    print(permission_service.get_user_permissions('test_user_001'))

    print('\n=== 权限检查 ===')
    print(f'检查 education 权限: {permission_service.check_permission("test_user_001", "education")}')
    print(f'检查 system 权限: {permission_service.check_permission("test_user_001", "system")}')

    print('\n=== 可访问模块 ===')
    for module in permission_service.get_accessible_modules('test_user_001'):
        print(f'- {module["module_name"]}: {module["module_url"]}')

    print('\n=== 审计日志 ===')
    for log in permission_service.get_audit_logs(limit=5):
        print(f'- [{log["created_at"]}] {log["action"]} - {log["status"]}')

    print('\n=== 撤销角色 ===')
    result = permission_service.revoke_role('test_user_001', 'teacher')
    print(f'撤销角色: {result}')
