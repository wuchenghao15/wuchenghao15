#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""系统增强系统 - 强化逻辑、路由和规则"""

import os
# import json removed - using database storage
import sqlite3
import logging
import re
from datetime import datetime
from typing import Dict, List, Any

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('system_enhancer')

class SystemEnhancer:
    def __init__(self):
        self.db_path = 'app.db'
        self.logic_rules = {}
        self.routes = {}
        self.access_rules = {}
        self.init_enhancement_database()
    
    def init_enhancement_database(self):
        """初始化增强数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        tables = [
            '''CREATE TABLE IF NOT EXISTS system_logic_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id TEXT UNIQUE NOT NULL,
                rule_name TEXT,
                rule_type TEXT,
                condition TEXT,
                action TEXT,
                priority INTEGER,
                enabled INTEGER DEFAULT 1,
                description TEXT,
                created_at TEXT
            )''',
            
            '''CREATE TABLE IF NOT EXISTS system_routes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route_id TEXT UNIQUE NOT NULL,
                route_name TEXT,
                path TEXT,
                method TEXT,
                controller TEXT,
                action TEXT,
                permissions TEXT,
                enabled INTEGER DEFAULT 1,
                created_at TEXT
            )''',
            
            '''CREATE TABLE IF NOT EXISTS access_control_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id TEXT UNIQUE NOT NULL,
                role TEXT,
                resource TEXT,
                action TEXT,
                allowed INTEGER,
                conditions TEXT,
                priority INTEGER,
                created_at TEXT
            )''',
            
            '''CREATE TABLE IF NOT EXISTS workflow_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id TEXT UNIQUE NOT NULL,
                workflow_name TEXT,
                steps TEXT,
                conditions TEXT,
                triggers TEXT,
                enabled INTEGER DEFAULT 1,
                created_at TEXT
            )''',
            
            '''CREATE TABLE IF NOT EXISTS validation_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id TEXT UNIQUE NOT NULL,
                field TEXT,
                validation_type TEXT,
                pattern TEXT,
                min_length INTEGER,
                max_length INTEGER,
                required INTEGER,
                error_message TEXT,
                created_at TEXT
            )'''
        ]
        
        for table_sql in tables:
            cursor.execute(table_sql)
        
        conn.commit()
        conn.close()
        logger.info("系统增强数据库表初始化完成")
    
    def enhance_logic_rules(self):
        """增强逻辑规则"""
        print("="*80)
        print("          系统逻辑规则增强")
        print("="*80)
        
        logic_rules = [
            {
                'rule_id': 'logic_001',
                'rule_name': '登录尝试限制',
                'rule_type': 'security',
                'condition': 'login_attempts > 5 AND time_window < 30min',
                'action': 'lock_account(30min)',
                'priority': 1,
                'description': '超过5次登录失败，锁定账户30分钟'
            },
            {
                'rule_id': 'logic_002',
                'rule_name': '会话超时',
                'rule_type': 'security',
                'condition': 'last_activity < 3600s',
                'action': 'invalidate_session()',
                'priority': 2,
                'description': '会话超过1小时无活动自动失效'
            },
            {
                'rule_id': 'logic_003',
                'rule_name': '异常访问检测',
                'rule_type': 'security',
                'condition': 'requests_per_minute > 100 AND is_suspicious = true',
                'action': 'block_ip(1h)',
                'priority': 1,
                'description': '每分钟超过100次请求且可疑，封禁IP1小时'
            },
            {
                'rule_id': 'logic_004',
                'rule_name': '数据完整性检查',
                'rule_type': 'data',
                'condition': 'data_hash_mismatch = true',
                'action': 'revalidate_data()',
                'priority': 2,
                'description': '数据哈希不匹配时重新验证'
            },
            {
                'rule_id': 'logic_005',
                'rule_name': '权限继承',
                'rule_type': 'access',
                'condition': 'user_role = parent_role',
                'action': 'inherit_permissions()',
                'priority': 3,
                'description': '子角色继承父角色权限'
            },
            {
                'rule_id': 'logic_006',
                'rule_name': '日志轮转',
                'rule_type': 'system',
                'condition': 'log_size > 100MB OR days_old > 30',
                'action': 'rotate_logs()',
                'priority': 4,
                'description': '日志超过100MB或30天自动轮转'
            },
            {
                'rule_id': 'logic_007',
                'rule_name': '资源清理',
                'rule_type': 'system',
                'condition': 'temp_files_age > 24h',
                'action': 'clean_temp_files()',
                'priority': 4,
                'description': '清理超过24小时的临时文件'
            },
            {
                'rule_id': 'logic_008',
                'rule_name': '性能阈值',
                'rule_type': 'monitoring',
                'condition': 'cpu_usage > 90% AND duration > 5min',
                'action': 'scale_up()',
                'priority': 1,
                'description': 'CPU使用率超过90%持续5分钟自动扩容'
            }
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for rule in logic_rules:
            cursor.execute('''
                INSERT OR REPLACE INTO system_logic_rules
                (rule_id, rule_name, rule_type, condition, action, priority, enabled, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                rule['rule_id'],
                rule['rule_name'],
                rule['rule_type'],
                rule['condition'],
                rule['action'],
                rule['priority'],
                1,
                rule['description'],
                datetime.now().isoformat()
            ))
            print(f"  ✓ {rule['rule_name']}")
        
        conn.commit()
        conn.close()
        
        print(f"\n已增强 {len(logic_rules)} 条逻辑规则")
    
    def enhance_routes(self):
        """增强路由配置"""
        print("\n" + "="*80)
        print("          系统路由增强")
        print("="*80)
        
        routes = [
            # 认证路由
            {'route_id': 'route_auth_login', 'route_name': '登录', 'path': '/auth/login', 'method': 'POST', 'controller': 'AuthController', 'action': 'login', 'permissions': '[]'},
            {'route_id': 'route_auth_logout', 'route_name': '登出', 'path': '/auth/logout', 'method': 'POST', 'controller': 'AuthController', 'action': 'logout', 'permissions': '["authenticated"]'},
            {'route_id': 'route_auth_register', 'route_name': '注册', 'path': '/auth/register', 'method': 'POST', 'controller': 'AuthController', 'action': 'register', 'permissions': '[]'},
            {'route_id': 'route_auth_refresh', 'route_name': '刷新Token', 'path': '/auth/refresh', 'method': 'POST', 'controller': 'AuthController', 'action': 'refresh', 'permissions': '["authenticated"]'},
            
            # 仪表盘路由
            {'route_id': 'route_dashboard', 'route_name': '仪表盘', 'path': '/dashboard', 'method': 'GET', 'controller': 'DashboardController', 'action': 'index', 'permissions': '["authenticated"]'},
            {'route_id': 'route_dashboard_stats', 'route_name': '统计数据', 'path': '/dashboard/stats', 'method': 'GET', 'controller': 'DashboardController', 'action': 'stats', 'permissions': '["authenticated"]'},
            
            # 用户路由
            {'route_id': 'route_users', 'route_name': '用户列表', 'path': '/api/users', 'method': 'GET', 'controller': 'UserController', 'action': 'index', 'permissions': '["admin"]'},
            {'route_id': 'route_user_create', 'route_name': '创建用户', 'path': '/api/users', 'method': 'POST', 'controller': 'UserController', 'action': 'create', 'permissions': '["admin"]'},
            {'route_id': 'route_user_show', 'route_name': '用户详情', 'path': '/api/users/:id', 'method': 'GET', 'controller': 'UserController', 'action': 'show', 'permissions': '["admin", "self"]'},
            {'route_id': 'route_user_update', 'route_name': '更新用户', 'path': '/api/users/:id', 'method': 'PUT', 'controller': 'UserController', 'action': 'update', 'permissions': '["admin", "self"]'},
            {'route_id': 'route_user_delete', 'route_name': '删除用户', 'path': '/api/users/:id', 'method': 'DELETE', 'controller': 'UserController', 'action': 'delete', 'permissions': '["admin"]'},
            
            # 题库路由
            {'route_id': 'route_questions', 'route_name': '题目列表', 'path': '/api/questions', 'method': 'GET', 'controller': 'QuestionController', 'action': 'index', 'permissions': '["authenticated"]'},
            {'route_id': 'route_question_create', 'route_name': '创建题目', 'path': '/api/questions', 'method': 'POST', 'controller': 'QuestionController', 'action': 'create', 'permissions': '["admin", "teacher"]'},
            {'route_id': 'route_question_update', 'route_name': '更新题目', 'path': '/api/questions/:id', 'method': 'PUT', 'controller': 'QuestionController', 'action': 'update', 'permissions': '["admin", "teacher"]'},
            {'route_id': 'route_question_delete', 'route_name': '删除题目', 'path': '/api/questions/:id', 'method': 'DELETE', 'controller': 'QuestionController', 'action': 'delete', 'permissions': '["admin"]'},
            
            # 测试路由
            {'route_id': 'route_assessments', 'route_name': '评估列表', 'path': '/api/assessments', 'method': 'GET', 'controller': 'AssessmentController', 'action': 'index', 'permissions': '["authenticated"]'},
            {'route_id': 'route_assessment_create', 'route_name': '创建评估', 'path': '/api/assessments', 'method': 'POST', 'controller': 'AssessmentController', 'action': 'create', 'permissions': '["admin", "teacher"]'},
            {'route_id': 'route_assessment_take', 'route_name': '参加评估', 'path': '/api/assessments/:id/take', 'method': 'POST', 'controller': 'AssessmentController', 'action': 'take', 'permissions': '["authenticated"]'},
            {'route_id': 'route_assessment_result', 'route_name': '评估结果', 'path': '/api/assessments/:id/result', 'method': 'GET', 'controller': 'AssessmentController', 'action': 'result', 'permissions': '["authenticated"]'},
            
            # AI路由
            {'route_id': 'route_ai_experts', 'route_name': 'AI专家列表', 'path': '/api/ai/experts', 'method': 'GET', 'controller': 'AIController', 'action': 'experts', 'permissions': '["admin"]'},
            {'route_id': 'route_ai_enhance', 'route_name': '增强AI能力', 'path': '/api/ai/enhance', 'method': 'POST', 'controller': 'AIController', 'action': 'enhance', 'permissions': '["admin"]'},
            
            # 系统路由
            {'route_id': 'route_system_health', 'route_name': '健康检查', 'path': '/api/system/health', 'method': 'GET', 'controller': 'SystemController', 'action': 'health', 'permissions': '[]'},
            {'route_id': 'route_system_stats', 'route_name': '系统统计', 'path': '/api/system/stats', 'method': 'GET', 'controller': 'SystemController', 'action': 'stats', 'permissions': '["admin"]'},
            {'route_id': 'route_system_config', 'route_name': '系统配置', 'path': '/api/system/config', 'method': 'GET', 'controller': 'SystemController', 'action': 'config', 'permissions': '["admin"]'}
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for route in routes:
            cursor.execute('''
                INSERT OR REPLACE INTO system_routes
                (route_id, route_name, path, method, controller, action, permissions, enabled, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                route['route_id'],
                route['route_name'],
                route['path'],
                route['method'],
                route['controller'],
                route['action'],
                route['permissions'],
                1,
                datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
        
        print(f"已增强 {len(routes)} 条路由配置")
    
    def enhance_access_rules(self):
        """增强访问控制规则"""
        print("\n" + "="*80)
        print("          访问控制规则增强")
        print("="*80)
        
        access_rules = [
            # 管理员权限
            {'rule_id': 'access_admin_all', 'role': 'admin', 'resource': '*', 'action': '*', 'allowed': 1, 'conditions': '{}', 'priority': 1},
            
            # 教师权限
            {'rule_id': 'access_teacher_questions', 'role': 'teacher', 'resource': 'questions', 'action': 'create,read,update', 'allowed': 1, 'conditions': '{}', 'priority': 2},
            {'rule_id': 'access_teacher_assessments', 'role': 'teacher', 'resource': 'assessments', 'action': 'create,read,update', 'allowed': 1, 'conditions': '{}', 'priority': 2},
            {'rule_id': 'access_teacher_users', 'role': 'teacher', 'resource': 'users', 'action': 'read', 'allowed': 1, 'conditions': '{}', 'priority': 2},
            
            # 学生权限
            {'rule_id': 'access_student_self', 'role': 'student', 'resource': 'users', 'action': 'read,update', 'allowed': 1, 'conditions': '{"self": true}', 'priority': 3},
            {'rule_id': 'access_student_assessments', 'role': 'student', 'resource': 'assessments', 'action': 'read,take', 'allowed': 1, 'conditions': '{}', 'priority': 3},
            {'rule_id': 'access_student_questions', 'role': 'student', 'resource': 'questions', 'action': 'read', 'allowed': 1, 'conditions': '{}', 'priority': 3},
            
            # 访客权限
            {'rule_id': 'access_guest_login', 'role': 'guest', 'resource': 'auth', 'action': 'login,register', 'allowed': 1, 'conditions': '{}', 'priority': 4},
            {'rule_id': 'access_guest_read', 'role': 'guest', 'resource': 'questions', 'action': 'read', 'allowed': 1, 'conditions': '{"published": true}', 'priority': 4},
            
            # 禁止规则
            {'rule_id': 'access_deny_deleted', 'role': '*', 'resource': '*', 'action': '*', 'allowed': 0, 'conditions': '{"deleted": true}', 'priority': 0}
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for rule in access_rules:
            cursor.execute('''
                INSERT OR REPLACE INTO access_control_rules
                (rule_id, role, resource, action, allowed, conditions, priority, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                rule['rule_id'],
                rule['role'],
                rule['resource'],
                rule['action'],
                rule['allowed'],
                rule['conditions'],
                rule['priority'],
                datetime.now().isoformat()
            ))
            print(f"  ✓ {rule['role']} - {rule['resource']}")
        
        conn.commit()
        conn.close()
        
        print(f"\n已增强 {len(access_rules)} 条访问控制规则")
    
    def enhance_validation_rules(self):
        """增强验证规则"""
        print("\n" + "="*80)
        print("          数据验证规则增强")
        print("="*80)
        
        validation_rules = [
            {'rule_id': 'valid_username', 'field': 'username', 'validation_type': 'regex', 'pattern': '^[a-zA-Z0-9_]{3,20}$', 'min_length': 3, 'max_length': 20, 'required': 1, 'error_message': '用户名必须3-20位字母数字下划线'},
            {'rule_id': 'valid_email', 'field': 'email', 'validation_type': 'email', 'pattern': '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$', 'min_length': 5, 'max_length': 100, 'required': 1, 'error_message': '请输入有效的邮箱地址'},
            {'rule_id': 'valid_password', 'field': 'password', 'validation_type': 'complex', 'pattern': '', 'min_length': 8, 'max_length': 128, 'required': 1, 'error_message': '密码至少8位，包含大小写字母和数字'},
            {'rule_id': 'valid_phone', 'field': 'phone', 'validation_type': 'regex', 'pattern': '^1[3-9]\\d{9}$', 'min_length': 11, 'max_length': 11, 'required': 0, 'error_message': '请输入有效的手机号码'},
            {'rule_id': 'valid_name', 'field': 'name', 'validation_type': 'regex', 'pattern': '^[\u4e00-\u9fa5a-zA-Z]{2,50}$', 'min_length': 2, 'max_length': 50, 'required': 1, 'error_message': '姓名必须2-50位中文或字母'},
            {'rule_id': 'valid_integer', 'field': 'integer', 'validation_type': 'integer', 'pattern': '', 'min_length': 0, 'max_length': 0, 'required': 0, 'error_message': '必须是整数'},
            {'rule_id': 'valid_float', 'field': 'float', 'validation_type': 'float', 'pattern': '', 'min_length': 0, 'max_length': 0, 'required': 0, 'error_message': '必须是数字'},
            {'rule_id': 'valid_json', 'field': 'json', 'validation_type': 'json', 'pattern': '', 'min_length': 0, 'max_length': 10000, 'required': 0, 'error_message': '必须是有效的JSON格式'},
            {'rule_id': 'valid_url', 'field': 'url', 'validation_type': 'url', 'pattern': '^https?://[a-zA-Z0-9.-]+(/[a-zA-Z0-9._~:/?#[\\]@!$&\'()*+,;=-]*)?$', 'min_length': 10, 'max_length': 500, 'required': 0, 'error_message': '请输入有效的URL地址'},
            {'rule_id': 'valid_datetime', 'field': 'datetime', 'validation_type': 'datetime', 'pattern': '^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}$', 'min_length': 0, 'max_length': 0, 'required': 0, 'error_message': '请输入有效的日期时间格式'}
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for rule in validation_rules:
            cursor.execute('''
                INSERT OR REPLACE INTO validation_rules
                (rule_id, field, validation_type, pattern, min_length, max_length, required, error_message, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                rule['rule_id'],
                rule['field'],
                rule['validation_type'],
                rule['pattern'],
                rule['min_length'],
                rule['max_length'],
                rule['required'],
                rule['error_message'],
                datetime.now().isoformat()
            ))
            print(f"  ✓ {rule['field']}")
        
        conn.commit()
        conn.close()
        
        print(f"\n已增强 {len(validation_rules)} 条数据验证规则")
    
    def generate_enhancement_report(self):
        """生成增强报告"""
        print("\n" + "="*80)
        print("          系统增强报告")
        print("="*80)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM system_logic_rules')
        logic_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM system_routes')
        route_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM access_control_rules')
        access_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM validation_rules')
        validation_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"\n逻辑规则: {logic_count} 条")
        print(f"路由配置: {route_count} 条")
        print(f"访问控制规则: {access_count} 条")
        print(f"数据验证规则: {validation_count} 条")
        
        print("\n" + "="*80)
        print("  系统逻辑、路由和规则增强完成！")
        print("="*80)
    
    def run_full_enhancement(self):
        """运行完整增强流程"""
        self.enhance_logic_rules()
        self.enhance_routes()
        self.enhance_access_rules()
        self.enhance_validation_rules()
        self.generate_enhancement_report()

def main():
    enhancer = SystemEnhancer()
    enhancer.run_full_enhancement()

if __name__ == "__main__":
    main()