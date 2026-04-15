#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则与权限管理器
负责规则与权限的管理
"""

import os
import sys
import time
import json
import logging
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('rules_permissions_manager')

class RulesPermissionsManager:
    """规则与权限管理器"""
    
    def __init__(self):
        """初始化规则与权限管理器"""
        self.manager_version = "1.0.0"
        self.roles = self.load_roles()
        self.permissions = self.load_permissions()
        self.rules = self.load_rules()
        logger.info(f"规则与权限管理器初始化完成，版本: {self.manager_version}")
    
    def load_roles(self) -> List[Dict]:
        """加载角色信息
        
        Returns:
            List[Dict]: 角色列表
        """
        return [
            {
                'id': 'super_admin',
                'name': '超级管理员',
                'description': '拥有系统所有权限',
                'priority': 100
            },
            {
                'id': 'admin',
                'name': '管理员',
                'description': '拥有大部分管理权限',
                'priority': 80
            },
            {
                'id': 'hardware_admin',
                'name': '硬件管理员',
                'description': '负责硬件管理',
                'priority': 60
            },
            {
                'id': 'teacher',
                'name': '教师',
                'description': '负责教学管理',
                'priority': 40
            },
            {
                'id': 'student',
                'name': '学生',
                'description': '普通用户',
                'priority': 20
            }
        ]
    
    def load_permissions(self) -> List[Dict]:
        """加载权限信息
        
        Returns:
            List[Dict]: 权限列表
        """
        return [
            {
                'id': 'system_management',
                'name': '系统管理',
                'description': '管理系统设置和配置',
                'required_role': 'super_admin'
            },
            {
                'id': 'user_management',
                'name': '用户管理',
                'description': '管理用户账户',
                'required_role': 'admin'
            },
            {
                'id': 'hardware_management',
                'name': '硬件管理',
                'description': '管理硬件设备',
                'required_role': 'hardware_admin'
            },
            {
                'id': 'course_management',
                'name': '课程管理',
                'description': '管理课程内容',
                'required_role': 'teacher'
            },
            {
                'id': 'exam_management',
                'name': '考试管理',
                'description': '管理考试内容',
                'required_role': 'teacher'
            },
            {
                'id': 'learning_access',
                'name': '学习访问',
                'description': '访问学习内容',
                'required_role': 'student'
            },
            {
                'id': 'exam_access',
                'name': '考试访问',
                'description': '参加考试',
                'required_role': 'student'
            }
        ]
    
    def load_rules(self) -> List[Dict]:
        """加载规则信息
        
        Returns:
            List[Dict]: 规则列表
        """
        return [
            {
                'id': 'login_rule',
                'name': '登录规则',
                'description': '用户登录验证规则',
                'priority': 10
            },
            {
                'id': 'permission_check_rule',
                'name': '权限检查规则',
                'description': '权限验证规则',
                'priority': 20
            },
            {
                'id': 'data_access_rule',
                'name': '数据访问规则',
                'description': '数据访问控制规则',
                'priority': 30
            },
            {
                'id': 'action_limit_rule',
                'name': '操作限制规则',
                'description': '用户操作限制规则',
                'priority': 40
            },
            {
                'id': 'security_rule',
                'name': '安全规则',
                'description': '安全防护规则',
                'priority': 50
            }
        ]
    
    def check_permission(self, user_role: str, required_permission: str) -> Dict:
        """检查用户权限
        
        Args:
            user_role: 用户角色
            required_permission: 需要的权限
            
        Returns:
            Dict: 权限检查结果
        """
        try:
            logger.info(f"检查用户角色 {user_role} 是否拥有权限 {required_permission}")
            
            # 查找权限信息
            permission = next((p for p in self.permissions if p['id'] == required_permission), None)
            if not permission:
                return {
                    "success": False,
                    "error": "权限不存在"
                }
            
            # 查找用户角色信息
            user_role_info = next((r for r in self.roles if r['id'] == user_role), None)
            if not user_role_info:
                return {
                    "success": False,
                    "error": "角色不存在"
                }
            
            # 查找所需权限的角色信息
            required_role_info = next((r for r in self.roles if r['id'] == permission['required_role']), None)
            if not required_role_info:
                return {
                    "success": False,
                    "error": "所需角色不存在"
                }
            
            # 检查角色优先级
            if user_role_info['priority'] >= required_role_info['priority']:
                return {
                    "success": True,
                    "data": {
                        'user_role': user_role,
                        'required_permission': required_permission,
                        'has_permission': True
                    }
                }
            else:
                return {
                    "success": True,
                    "data": {
                        'user_role': user_role,
                        'required_permission': required_permission,
                        'has_permission': False
                    }
                }
                
        except Exception as e:
            logger.error(f"检查权限失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_user_permissions(self, user_role: str) -> Dict:
        """获取用户权限列表
        
        Args:
            user_role: 用户角色
            
        Returns:
            Dict: 用户权限列表
        """
        try:
            logger.info(f"获取用户角色 {user_role} 的权限列表")
            
            # 查找用户角色信息
            user_role_info = next((r for r in self.roles if r['id'] == user_role), None)
            if not user_role_info:
                return {
                    "success": False,
                    "error": "角色不存在"
                }
            
            # 获取用户拥有的权限
            user_permissions = []
            for permission in self.permissions:
                required_role_info = next((r for r in self.roles if r['id'] == permission['required_role']), None)
                if required_role_info and user_role_info['priority'] >= required_role_info['priority']:
                    user_permissions.append(permission)
            
            return {
                "success": True,
                "data": {
                    'user_role': user_role,
                    'permissions': user_permissions
                }
            }
            
        except Exception as e:
            logger.error(f"获取用户权限失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def add_role(self, role: Dict) -> Dict:
        """添加角色
        
        Args:
            role: 角色信息
            
        Returns:
            Dict: 添加结果
        """
        try:
            logger.info(f"添加角色: {role['name']}")
            
            # 检查角色是否已存在
            existing_role = next((r for r in self.roles if r['id'] == role['id']), None)
            if existing_role:
                return {
                    "success": False,
                    "error": "角色已存在"
                }
            
            # 添加角色
            self.roles.append(role)
            
            return {
                "success": True,
                "data": {
                    'role': role,
                    'status': 'added'
                }
            }
            
        except Exception as e:
            logger.error(f"添加角色失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def add_permission(self, permission: Dict) -> Dict:
        """添加权限
        
        Args:
            permission: 权限信息
            
        Returns:
            Dict: 添加结果
        """
        try:
            logger.info(f"添加权限: {permission['name']}")
            
            # 检查权限是否已存在
            existing_permission = next((p for p in self.permissions if p['id'] == permission['id']), None)
            if existing_permission:
                return {
                    "success": False,
                    "error": "权限已存在"
                }
            
            # 添加权限
            self.permissions.append(permission)
            
            return {
                "success": True,
                "data": {
                    'permission': permission,
                    'status': 'added'
                }
            }
            
        except Exception as e:
            logger.error(f"添加权限失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_system_status(self) -> Dict:
        """获取系统状态
        
        Returns:
            Dict: 系统状态
        """
        try:
            logger.info("获取规则与权限系统状态")
            
            status = {
                'roles_count': len(self.roles),
                'permissions_count': len(self.permissions),
                'rules_count': len(self.rules),
                'manager_version': self.manager_version,
                'timestamp': time.time()
            }
            
            return {
                "success": True,
                "status": status
            }
            
        except Exception as e:
            logger.error(f"获取系统状态失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

# 全局规则与权限管理器实例
rules_permissions_manager = RulesPermissionsManager()

def get_rules_permissions_manager() -> RulesPermissionsManager:
    """获取规则与权限管理器实例
    
    Returns:
        RulesPermissionsManager: 规则与权限管理器实例
    """
    return rules_permissions_manager
