# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
权限管理系统 - 基于数据库规则的权限控制
"""

import os
import sys
import sqlite3
import json
import hashlib
import base64
from datetime import datetime
from typing import Dict, List, Optional

# 配置
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')


class PermissionManager:
    """权限管理器"""
    
    def __init__(self):
        self.cache = {}
        self.cache_timeout = 300  # 缓存5分钟
    
    def get_permission_rules(self) -> Dict:
        """获取权限规则"""
        # 尝试从缓存获取
        cache_key = 'permission_rules'
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        rules = {}
        cursor.execute("SELECT rule_code, rule_value FROM system_rules WHERE rule_type = 'json'")
        for row in cursor.fetchall():
            try:
                rules[row[0]] = json.loads(row[1])
            except Exception:
                pass
        
        conn.close()
        
        # 缓存
        self.cache[cache_key] = rules
        return rules
    
    def check_page_access(self, role: str, page_path: str) -> bool:
        """检查页面访问权限"""
        rules = self.get_permission_rules()
        
        # 获取该角色的页面访问规则
        page_access_key = f'page_access_{role}'
        if page_access_key in rules:
            rule = rules[page_access_key]
            allowed = rule.get('allowed', [])
            denied = rule.get('denied', [])
            
            # 通配符匹配
            if '*' in allowed:
                return True
            
            # 检查是否在允许列表中
            if page_path in allowed:
                return True
            
            # 检查是否在拒绝列表中
            if page_path in denied:
                return False
            
            # 检查通配符模式
            for pattern in allowed:
                if '*' in pattern and page_path.startswith(pattern.replace('*', '')):
                    return True
            
            for pattern in denied:
                if '*' in pattern and page_path.startswith(pattern.replace('*', '')):
                    return False
        
        return True  # 默认允许
    
    def check_feature_access(self, role: str, feature: str) -> bool:
        """检查功能权限"""
        rules = self.get_permission_rules()
        
        # 获取该角色的功能权限
        feature_key = f'feature_permission_{role}'
        if feature_key in rules:
            rule = rules[feature_key]
            return rule.get(feature, False)
        
        return False  # 默认拒绝
    
    def get_user_permissions(self, role: str) -> Dict:
        """获取用户的所有权限"""
        rules = self.get_permission_rules()
        
        permissions = {
            'pages': {},
            'features': {},
            'role': role
        }
        
        # 页面访问权限
        page_key = f'page_access_{role}'
        if page_key in rules:
            permissions['pages'] = rules[page_key]
        
        # 功能权限
        feature_key = f'feature_permission_{role}'
        if feature_key in rules:
            permissions['features'] = rules[feature_key]
        
        return permissions
    
    def get_role_hierarchy(self) -> Dict[str, int]:
        """获取角色等级"""
        return {
            'guest': 0,
            'student': 1,
            'teacher': 2,
            'professor': 3,
            'researcher': 4,
            'admin': 5,
            'super_admin': 6,
            'hardware_admin': 7
        }
    
    def has_higher_role(self, user_role: str, required_role: str) -> bool:
        """检查用户是否有更高权限"""
        hierarchy = self.get_role_hierarchy()
        user_level = hierarchy.get(user_role, 0)
        required_level = hierarchy.get(required_role, 0)
        return user_level >= required_level
    
    def clear_cache(self):
        """清除缓存"""
        self.cache = {}


# 全局权限管理器实例
permission_manager = PermissionManager()


def optimize_permissions():
    """优化权限系统"""
    print('\n' + '='*60)
    print('🔐 权限优化系统')
    print('='*60 + '\n')
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # 优化1: 添加角色等级规则
    role_hierarchy_rules = [
        ('role_hierarchy_guest', '访客等级', '访客角色等级', 'number', 0),
        ('role_hierarchy_student', '学生等级', '学生角色等级', 'number', 1),
        ('role_hierarchy_teacher', '教师等级', '教师角色等级', 'number', 2),
        ('role_hierarchy_professor', '教授等级', '教授角色等级', 'number', 3),
        ('role_hierarchy_researcher', '教研员等级', '教研员角色等级', 'number', 4),
        ('role_hierarchy_admin', '管理员等级', '管理员角色等级', 'number', 5),
        ('role_hierarchy_super_admin', '超级管理员等级', '超级管理员角色等级', 'number', 6),
        ('role_hierarchy_hardware_admin', '硬件管理员等级', '硬件管理员角色等级', 'number', 7),
    ]
    
    print('1. 优化角色等级规则...')
    for code, name, desc, rtype, value in role_hierarchy_rules:
        try:
            cursor.execute('''
                UPDATE system_rules 
                SET rule_value = ?, rule_name = ?, rule_description = ?
                WHERE rule_code = ?
            ''', (str(value), name, desc, code))
            
            if cursor.rowcount == 0:
                cursor.execute('''
                    INSERT INTO system_rules 
                    (rule_code, rule_name, rule_description, rule_type, rule_value, is_active, priority)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (code, name, desc, rtype, str(value), 1, 100))
            
            print(f'  ✅ {name}: 等级 {value}')
        except Exception as e:
            print(f'  ❌ {name}: {str(e)}')
    
    # 优化2: 添加权限继承规则
    print('\n2. 优化权限继承规则...')
    inheritance_rules = [
        ('permission_inheritance_student', '学生权限继承', '学生权限继承配置', 'json', {
            'inherits_from': None,
            'can_inherit_to': ['guest'],
            'restrictions': ['cannot_manage_users', 'cannot_access_admin']
        }),
        ('permission_inheritance_teacher', '教师权限继承', '教师权限继承配置', 'json', {
            'inherits_from': 'student',
            'can_inherit_to': ['student'],
            'additional': ['can_create_exam', 'can_manage_questions']
        }),
        ('permission_inheritance_professor', '教授权限继承', '教授权限继承配置', 'json', {
            'inherits_from': 'teacher',
            'can_inherit_to': ['teacher', 'student'],
            'additional': ['can_view_research', 'can_publish_papers']
        }),
        ('permission_inheritance_admin', '管理员权限继承', '管理员权限继承配置', 'json', {
            'inherits_from': 'professor',
            'can_inherit_to': ['professor', 'teacher', 'student'],
            'additional': ['can_manage_users', 'can_manage_system']
        }),
    ]
    
    for code, name, desc, rtype, value in inheritance_rules:
        try:
            value_json = json.dumps(value)
            cursor.execute('''
                UPDATE system_rules 
                SET rule_value = ?, rule_name = ?, rule_description = ?
                WHERE rule_code = ?
            ''', (value_json, name, desc, code))
            
            if cursor.rowcount == 0:
                cursor.execute('''
                    INSERT INTO system_rules 
                    (rule_code, rule_name, rule_description, rule_type, rule_value, is_active, priority)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (code, name, desc, rtype, value_json, 1, 100))
            
            print(f'  ✅ {name}')
        except Exception as e:
            print(f'  ❌ {name}: {str(e)}')
    
    # 优化3: 添加权限验证规则
    print('\n3. 优化权限验证规则...')
    validation_rules = [
        ('permission_validation_timeout', '权限验证超时', '权限验证缓存超时(秒)', 'number', 300),
        ('permission_validation_strict', '严格权限验证', '是否启用严格权限验证', 'boolean', True),
        ('permission_audit_enabled', '启用权限审计', '是否记录权限变更审计日志', 'boolean', True),
        ('permission_cache_enabled', '启用权限缓存', '是否启用权限缓存', 'boolean', True),
    ]
    
    for code, name, desc, rtype, value in validation_rules:
        try:
            cursor.execute('''
                UPDATE system_rules 
                SET rule_value = ?, rule_name = ?, rule_description = ?
                WHERE rule_code = ?
            ''', (str(value), name, desc, code))
            
            if cursor.rowcount == 0:
                cursor.execute('''
                    INSERT INTO system_rules 
                    (rule_code, rule_name, rule_description, rule_type, rule_value, is_active, priority)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (code, name, desc, rtype, str(value), 1, 100))
            
            print(f'  ✅ {name}: {value}')
        except Exception as e:
            print(f'  ❌ {name}: {str(e)}')
    
    conn.commit()
    conn.close()
    
    # 清除权限管理器缓存
    permission_manager.clear_cache()
    
    print('\n' + '='*60)
    print('✅ 权限优化完成!')
    print('='*60 + '\n')


def create_permission_api():
    """创建权限管理API"""
    print('\n📝 创建权限管理API...')
    
    api_code = '''#!/usr/bin/env python3
"""
权限管理API - Flask Blueprint
"""

from flask import Blueprint, request, jsonify, session
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.enhanced_rule_optimizer import PermissionManager, DATABASE_PATH

permission_api = Blueprint('permission_api', __name__, url_prefix='/api/permission')

pm = PermissionManager()


@permission_api.route('/check', methods=['POST'])
def check_permission():
    """检查权限"""
    data = request.json
    role = data.get('role', 'guest')
    resource = data.get('resource')
    action = data.get('action', 'view')
    
    if action == 'page':
        allowed = pm.check_page_access(role, resource)
    elif action == 'feature':
        allowed = pm.check_feature_access(role, resource)
    else:
        allowed = pm.check_page_access(role, resource)
    
    return jsonify({
        'success': True,
        'allowed': allowed,
        'role': role,
        'resource': resource
    })


@permission_api.route('/user/<role>', methods=['GET'])
def get_user_permissions(role):
    """获取用户权限"""
    permissions = pm.get_user_permissions(role)
    return jsonify({
        'success': True,
        'permissions': permissions
    })


@permission_api.route('/hierarchy', methods=['GET'])
def get_role_hierarchy():
    """获取角色等级"""
    hierarchy = pm.get_role_hierarchy()
    return jsonify({
        'success': True,
        'hierarchy': hierarchy
    })


@permission_api.route('/compare', methods=['POST'])
def compare_roles():
    """比较角色权限"""
    data = request.json
    user_role = data.get('user_role')
    required_role = data.get('required_role')
    
    has_access = pm.has_higher_role(user_role, required_role)
    
    return jsonify({
        'success': True,
        'has_access': has_access,
        'user_role': user_role,
        'required_role': required_role
    })


@permission_api.route('/refresh', methods=['POST'])
def refresh_permissions():
    """刷新权限缓存"""
    pm.clear_cache()
    return jsonify({
        'success': True,
        'message': '权限缓存已刷新'
    })
'''
    
    print('  ✅ 权限管理API代码已生成')
    return api_code


def main():
    """主函数"""
    optimize_permissions()
    api = create_permission_api()
    print('\n权限系统优化完成!')


if __name__ == '__main__':
    main()
