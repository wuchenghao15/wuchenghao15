#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
前端权限控制和规则集成系统
提供动态权限检查和规则引擎集成
"""

import json
from typing import Dict, List, Any, Optional
from app.models.rule import Rule, RuleCategory
from app.utils.logging import logger


class FrontendPermissionManager:
    """前端权限管理器"""
    
    def __init__(self):
        # 定义角色权限映射
        self.role_permissions = {
            'guest': {
                'pages': ['/', '/login', '/register', '/test-system', '/level-assessment'],
                'actions': ['view_test', 'view_assessment'],
                'apis': ['/api/public/*']
            },
            'student': {
                'pages': [
                    '/', '/profile', '/student/dashboard', '/student/homework',
                    '/student/exams', '/student/grades', '/test-system', '/level-assessment'
                ],
                'actions': ['view_test', 'take_test', 'view_assessment', 'submit_homework', 'view_grades'],
                'apis': ['/api/student/*', '/api/public/*']
            },
            'teacher': {
                'pages': [
                    '/', '/profile', '/teacher/dashboard', '/teacher/students',
                    '/teacher/homework', '/teacher/exams', '/test-system', '/level-assessment'
                ],
                'actions': ['view_test', 'create_test', 'manage_students', 'grade_homework', 'view_reports'],
                'apis': ['/api/teacher/*', '/api/student/*', '/api/public/*']
            },
            'admin': {
                'pages': [
                    '/', '/profile', '/admin/dashboard', '/admin/users', '/admin/settings',
                    '/test-system', '/level-assessment'
                ],
                'actions': ['manage_users', 'manage_settings', 'view_system', 'manage_permissions'],
                'apis': ['/api/admin/*', '/api/teacher/*', '/api/student/*', '/api/public/*']
            },
            'super_admin': {
                'pages': [
                    '/', '/profile', '/admin/dashboard', '/admin/users', '/admin/settings',
                    '/hardware/dashboard', '/design/dashboard', '/test-system', '/level-assessment'
                ],
                'actions': ['manage_users', 'manage_settings', 'view_system', 'manage_permissions',
                           'manage_hardware', 'manage_design'],
                'apis': ['/api/*']
            },
            'hardware_admin': {
                'pages': [
                    '/', '/profile', '/admin/dashboard', '/admin/users', '/admin/settings',
                    '/hardware/dashboard', '/design/dashboard', '/test-system', '/level-assessment'
                ],
                'actions': ['manage_users', 'manage_settings', 'view_system', 'manage_permissions',
                           'manage_hardware', 'manage_design'],
                'apis': ['/api/*']
            },
            'designer': {
                'pages': [
                    '/', '/profile', '/design/dashboard', '/test-system', '/level-assessment'
                ],
                'actions': ['manage_design', 'view_test'],
                'apis': ['/api/design/*', '/api/public/*']
            }
        }
        
        # 权限等级
        self.permission_levels = {
            'guest': 0,
            'student': 1,
            'teacher': 2,
            'designer': 3,
            'admin': 4,
            'super_admin': 5,
            'hardware_admin': 5
        }
    
    def check_page_access(self, user_role: str, page_path: str) -> bool:
        """检查页面访问权限"""
        permissions = self.role_permissions.get(user_role, {})
        allowed_pages = permissions.get('pages', [])
        
        # 精确匹配
        if page_path in allowed_pages:
            return True
        
        # 通配符匹配
        for allowed_page in allowed_pages:
            if allowed_page.endswith('*'):
                prefix = allowed_page[:-1]
                if page_path.startswith(prefix):
                    return True
        
        return False
    
    def check_action_permission(self, user_role: str, action: str) -> bool:
        """检查操作权限"""
        permissions = self.role_permissions.get(user_role, {})
        return action in permissions.get('actions', [])
    
    def check_api_access(self, user_role: str, api_path: str) -> bool:
        """检查API访问权限"""
        permissions = self.role_permissions.get(user_role, {})
        allowed_apis = permissions.get('apis', [])
        
        # 精确匹配
        if api_path in allowed_apis:
            return True
        
        # 通配符匹配
        for allowed_api in allowed_apis:
            if allowed_api.endswith('*'):
                prefix = allowed_api[:-1]
                if api_path.startswith(prefix):
                    return True
        
        return False
    
    def get_allowed_pages(self, user_role: str) -> List[str]:
        """获取允许访问的页面列表"""
        permissions = self.role_permissions.get(user_role, {})
        return permissions.get('pages', [])
    
    def get_allowed_actions(self, user_role: str) -> List[str]:
        """获取允许的操作列表"""
        permissions = self.role_permissions.get(user_role, {})
        return permissions.get('actions', [])
    
    def get_permission_level(self, user_role: str) -> int:
        """获取权限等级"""
        return self.permission_levels.get(user_role, 0)
    
    def has_higher_permission(self, user_role: str, min_level: int) -> bool:
        """检查是否具有更高权限"""
        return self.get_permission_level(user_role) >= min_level


class FrontendRuleEngine:
    """前端规则引擎"""
    
    def __init__(self):
        self.rules = []
        self.load_rules()
    
    def load_rules(self):
        """加载规则"""
        try:
            # 从数据库加载规则
            rules = Rule.query.all()
            self.rules = [rule.to_dict() for rule in rules]
        except Exception as e:
            logger.error(f"加载规则失败: {e}")
            # 使用默认规则
            self.rules = self._get_default_rules()
    
    def _get_default_rules(self) -> List[Dict[str, Any]]:
        """获取默认规则"""
        return [
            {
                'id': 1,
                'name': '考试时间限制',
                'description': '考试时间不得超过120分钟',
                'category': 'exam',
                'condition': 'exam.duration <= 120',
                'action': 'allow',
                'priority': 1
            },
            {
                'id': 2,
                'name': '最小题目数',
                'description': '每次考试至少5道题目',
                'category': 'exam',
                'condition': 'exam.question_count >= 5',
                'action': 'allow',
                'priority': 1
            },
            {
                'id': 3,
                'name': '每日测试限制',
                'description': '学生每天最多参加3次测试',
                'category': 'exam',
                'condition': 'daily_test_count < 3',
                'action': 'allow',
                'priority': 2
            },
            {
                'id': 4,
                'name': '作业截止提醒',
                'description': '作业截止前24小时发送提醒',
                'category': 'homework',
                'condition': 'homework.due_date - now < 24h',
                'action': 'notify',
                'priority': 1
            },
            {
                'id': 5,
                'name': '成绩预警',
                'description': '连续三次考试成绩下降超过10%时发送预警',
                'category': 'performance',
                'condition': 'score_trend < -10%',
                'action': 'alert',
                'priority': 1
            }
        ]
    
    def evaluate_rule(self, rule: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """评估规则"""
        condition = rule.get('condition', '')
        
        try:
            # 将上下文变量注入本地命名空间
            local_vars = {k: v for k, v in context.items()}
            result = eval(condition, {}, local_vars)
            return bool(result)
        except Exception as e:
            logger.error(f"规则评估失败: {rule.get('name')}, 错误: {e}")
            return False
    
    def evaluate_rules(self, category: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """评估指定类别的规则"""
        results = []
        
        for rule in self.rules:
            if rule.get('category') == category:
                if self.evaluate_rule(rule, context):
                    results.append(rule)
        
        # 按优先级排序
        results.sort(key=lambda x: x.get('priority', 1))
        
        return results
    
    def get_rule_actions(self, category: str, context: Dict[str, Any]) -> List[str]:
        """获取规则触发的动作"""
        matched_rules = self.evaluate_rules(category, context)
        return [rule.get('action') for rule in matched_rules]
    
    def check_exam_rules(self, exam_context: Dict[str, Any]) -> Dict[str, Any]:
        """检查考试规则"""
        results = self.evaluate_rules('exam', exam_context)
        
        # 检查是否有阻止规则
        blocking_rules = [r for r in results if r.get('action') == 'block']
        
        return {
            'allowed': len(blocking_rules) == 0,
            'matched_rules': results,
            'blocking_rules': blocking_rules,
            'warnings': [r for r in results if r.get('action') == 'warning']
        }
    
    def get_homework_reminders(self, homework_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取作业提醒"""
        results = self.evaluate_rules('homework', homework_context)
        return [r for r in results if r.get('action') == 'notify']
    
    def check_performance_alerts(self, performance_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检查成绩预警"""
        results = self.evaluate_rules('performance', performance_context)
        return [r for r in results if r.get('action') == 'alert']


class FrontendComponentGenerator:
    """前端组件生成器"""
    
    def __init__(self):
        self.permission_manager = FrontendPermissionManager()
        self.rule_engine = FrontendRuleEngine()
    
    def generate_navigation(self, user_role: str, current_path: str) -> str:
        """生成导航菜单"""
        nav_items = []
        
        # 基础导航
        nav_items.append({
            'label': '首页',
            'url': '/',
            'icon': 'fas fa-home',
            'active': current_path == '/'
        })
        
        # 根据角色生成导航
        if user_role in ['guest', 'student', 'teacher']:
            nav_items.extend([
                {
                    'label': '测试系统',
                    'url': '/test-system',
                    'icon': 'fas fa-file-alt',
                    'active': current_path.startswith('/test-system')
                },
                {
                    'label': '等级评估',
                    'url': '/level-assessment',
                    'icon': 'fas fa-award',
                    'active': current_path.startswith('/level-assessment')
                }
            ])
        
        # 管理员导航
        if user_role in ['admin', 'super_admin', 'hardware_admin']:
            nav_items.extend([
                {
                    'label': '管理面板',
                    'url': '/admin/dashboard',
                    'icon': 'fas fa-tachometer-alt',
                    'active': current_path.startswith('/admin/dashboard')
                },
                {
                    'label': '用户管理',
                    'url': '/admin/users',
                    'icon': 'fas fa-users',
                    'active': current_path.startswith('/admin/users')
                },
                {
                    'label': '系统设置',
                    'url': '/admin/settings',
                    'icon': 'fas fa-cogs',
                    'active': current_path.startswith('/admin/settings')
                }
            ])
        
        # 硬件管理员导航
        if user_role in ['super_admin', 'hardware_admin']:
            nav_items.extend([
                {
                    'label': '硬件管理',
                    'url': '/hardware/dashboard',
                    'icon': 'fas fa-server',
                    'active': current_path.startswith('/hardware/dashboard')
                },
                {
                    'label': '设计工具',
                    'url': '/design/dashboard',
                    'icon': 'fas fa-paint-brush',
                    'active': current_path.startswith('/design/dashboard')
                }
            ])
        
        # 设计师导航
        if user_role == 'designer':
            nav_items.append({
                'label': '设计工具',
                'url': '/design/dashboard',
                'icon': 'fas fa-paint-brush',
                'active': current_path.startswith('/design/dashboard')
            })
        
        # 教师导航
        if user_role == 'teacher':
            nav_items.extend([
                {
                    'label': '教师面板',
                    'url': '/teacher/dashboard',
                    'icon': 'fas fa-chalkboard-teacher',
                    'active': current_path.startswith('/teacher/dashboard')
                },
                {
                    'label': '学生管理',
                    'url': '/teacher/students',
                    'icon': 'fas fa-users',
                    'active': current_path.startswith('/teacher/students')
                },
                {
                    'label': '作业管理',
                    'url': '/teacher/homework',
                    'icon': 'fas fa-book-open',
                    'active': current_path.startswith('/teacher/homework')
                },
                {
                    'label': '考试管理',
                    'url': '/teacher/exams',
                    'icon': 'fas fa-file-check',
                    'active': current_path.startswith('/teacher/exams')
                }
            ])
        
        # 学生导航
        if user_role == 'student':
            nav_items.extend([
                {
                    'label': '学习面板',
                    'url': '/student/dashboard',
                    'icon': 'fas fa-graduation-cap',
                    'active': current_path.startswith('/student/dashboard')
                },
                {
                    'label': '我的作业',
                    'url': '/student/homework',
                    'icon': 'fas fa-book-open',
                    'active': current_path.startswith('/student/homework')
                },
                {
                    'label': '我的考试',
                    'url': '/student/exams',
                    'icon': 'fas fa-file-check',
                    'active': current_path.startswith('/student/exams')
                },
                {
                    'label': '我的成绩',
                    'url': '/student/grades',
                    'icon': 'fas fa-chart-line',
                    'active': current_path.startswith('/student/grades')
                }
            ])
        
        # 用户信息
        if user_role != 'guest':
            nav_items.extend([
                {
                    'label': '个人中心',
                    'url': '/profile',
                    'icon': 'fas fa-user',
                    'active': current_path.startswith('/profile')
                },
                {
                    'label': '退出',
                    'url': '/logout',
                    'icon': 'fas fa-sign-out-alt',
                    'active': False
                }
            ])
        else:
            nav_items.extend([
                {
                    'label': '登录',
                    'url': '/login',
                    'icon': 'fas fa-sign-in-alt',
                    'active': current_path.startswith('/login')
                },
                {
                    'label': '注册',
                    'url': '/register',
                    'icon': 'fas fa-user-plus',
                    'active': current_path.startswith('/register')
                }
            ])
        
        return nav_items
    
    def generate_dashboard_cards(self, user_role: str) -> List[Dict[str, Any]]:
        """生成仪表板卡片"""
        cards = []
        
        if user_role == 'admin':
            cards = [
                {
                    'title': '用户管理',
                    'icon': 'fas fa-users',
                    'url': '/admin/users',
                    'description': '管理系统用户和权限',
                    'color': 'primary'
                },
                {
                    'title': '系统设置',
                    'icon': 'fas fa-cogs',
                    'url': '/admin/settings',
                    'description': '配置系统参数',
                    'color': 'secondary'
                },
                {
                    'title': '测试管理',
                    'icon': 'fas fa-file-alt',
                    'url': '/test-system',
                    'description': '管理测试题库',
                    'color': 'success'
                },
                {
                    'title': '系统状态',
                    'icon': 'fas fa-heartbeat',
                    'url': '/admin/status',
                    'description': '查看系统运行状态',
                    'color': 'info'
                }
            ]
        
        elif user_role == 'teacher':
            cards = [
                {
                    'title': '学生管理',
                    'icon': 'fas fa-users',
                    'url': '/teacher/students',
                    'description': '管理学生信息',
                    'color': 'primary'
                },
                {
                    'title': '作业管理',
                    'icon': 'fas fa-book-open',
                    'url': '/teacher/homework',
                    'description': '布置和批改作业',
                    'color': 'secondary'
                },
                {
                    'title': '考试管理',
                    'icon': 'fas fa-file-check',
                    'url': '/teacher/exams',
                    'description': '创建和管理考试',
                    'color': 'success'
                },
                {
                    'title': '成绩分析',
                    'icon': 'fas fa-chart-line',
                    'url': '/teacher/reports',
                    'description': '查看学生成绩报告',
                    'color': 'info'
                }
            ]
        
        elif user_role == 'student':
            cards = [
                {
                    'title': '学习进度',
                    'icon': 'fas fa-graduation-cap',
                    'url': '/student/dashboard',
                    'description': '查看学习进度',
                    'color': 'primary'
                },
                {
                    'title': '我的作业',
                    'icon': 'fas fa-book-open',
                    'url': '/student/homework',
                    'description': '完成和提交作业',
                    'color': 'secondary'
                },
                {
                    'title': '我的考试',
                    'icon': 'fas fa-file-check',
                    'url': '/student/exams',
                    'description': '参加考试',
                    'color': 'success'
                },
                {
                    'title': '成绩查询',
                    'icon': 'fas fa-chart-line',
                    'url': '/student/grades',
                    'description': '查看考试成绩',
                    'color': 'info'
                }
            ]
        
        return cards
    
    def generate_permission_context(self, user_role: str) -> Dict[str, Any]:
        """生成权限上下文"""
        return {
            'role': user_role,
            'permission_level': self.permission_manager.get_permission_level(user_role),
            'allowed_pages': self.permission_manager.get_allowed_pages(user_role),
            'allowed_actions': self.permission_manager.get_allowed_actions(user_role),
            'can_manage_users': self.permission_manager.check_action_permission(user_role, 'manage_users'),
            'can_manage_settings': self.permission_manager.check_action_permission(user_role, 'manage_settings'),
            'can_create_tests': self.permission_manager.check_action_permission(user_role, 'create_test'),
            'can_view_reports': self.permission_manager.check_action_permission(user_role, 'view_reports')
        }


# 创建全局实例
frontend_permission_manager = FrontendPermissionManager()
frontend_rule_engine = FrontendRuleEngine()
frontend_component_generator = FrontendComponentGenerator()
