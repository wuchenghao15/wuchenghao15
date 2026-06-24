#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
角色路由跳转规则系统
根据用户组别自动跳转至对应页面
"""
import sqlite3
import json
import logging
from flask import Blueprint, jsonify, request, session, redirect, url_for

logger = logging.getLogger('role_router')

DB_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'


class RoleRouter:
    """角色路由跳转管理器"""

    def __init__(self):
        self.rules = self._load_rules()

    def _load_rules(self) -> dict:
        """加载角色跳转规则"""
        rules = {
            'student': {
                'name': '学生',
                'redirect': '/exam_system',
                'description': '考试系统首页',
                'permissions': ['exam_view', 'exam_take', 'results_view'],
                'sidebar_items': [
                    {'name': '考试系统首页', 'icon': 'fas fa-graduation-cap', 'path': '/exam_system'},
                    {'name': '考试中心', 'icon': 'fas fa-file-alt', 'path': '/exam'},
                    {'name': '我的成绩', 'icon': 'fas fa-chart-line', 'path': '/exam/results'},
                    {'name': '学习记录', 'icon': 'fas fa-book', 'path': '/exam/history'}
                ]
            },
            'designer': {
                'name': '设计师',
                'redirect': '/arduino',
                'description': 'Arduino设计页面',
                'permissions': ['arduino_view', 'project_create', 'component_access'],
                'sidebar_items': [
                    {'name': 'Arduino设计', 'icon': 'fas fa-microchip', 'path': '/arduino'},
                    {'name': '项目管理', 'icon': 'fas fa-folder', 'path': '/arduino/projects'},
                    {'name': '组件库', 'icon': 'fas fa-box', 'path': '/arduino/components'}
                ]
            },
            'teacher': {
                'name': '教师',
                'redirect': '/teacher',
                'description': '教师管理后台',
                'permissions': ['exam_manage', 'questions_manage', 'students_view', 'grade_view'],
                'sidebar_items': [
                    {'name': '考试管理', 'icon': 'fas fa-file-alt', 'path': '/teacher/exams'},
                    {'name': '题库管理', 'icon': 'fas fa-question-circle', 'path': '/teacher/questions'},
                    {'name': '学生管理', 'icon': 'fas fa-users', 'path': '/teacher/students'},
                    {'name': '成绩分析', 'icon': 'fas fa-chart-bar', 'path': '/teacher/grades'}
                ]
            },
            'researcher': {
                'name': '教研员',
                'redirect': '/researcher',
                'description': '教研员专属页面',
                'permissions': ['research_analysis', 'data_export', 'report_generate', 'system_config'],
                'sidebar_items': [
                    {'name': '教研分析', 'icon': 'fas fa-search', 'path': '/researcher/analysis'},
                    {'name': '数据报表', 'icon': 'fas fa-table', 'path': '/researcher/reports'},
                    {'name': '题库分析', 'icon': 'fas fa-database', 'path': '/researcher/questions'},
                    {'name': '系统配置', 'icon': 'fas fa-cog', 'path': '/researcher/config'}
                ]
            },
            'admin': {
                'name': '管理员',
                'redirect': '/settings',
                'description': '系统设置',
                'permissions': ['user_manage', 'role_manage', 'system_view', 'logs_view'],
                'sidebar_items': [
                    {'name': '用户管理', 'icon': 'fas fa-users', 'path': '/settings/users'},
                    {'name': '角色管理', 'icon': 'fas fa-lock', 'path': '/settings/permissions'},
                    {'name': '系统日志', 'icon': 'fas fa-file-log', 'path': '/settings/logs'}
                ]
            },
            'super_admin': {
                'name': '超级管理员',
                'redirect': '/settings',
                'description': '系统设置（全部权限）',
                'permissions': ['full_access'],
                'sidebar_items': [
                    {'name': '用户管理', 'icon': 'fas fa-users', 'path': '/settings/users'},
                    {'name': '角色管理', 'icon': 'fas fa-lock', 'path': '/settings/permissions'},
                    {'name': '系统日志', 'icon': 'fas fa-file-log', 'path': '/settings/logs'},
                    {'name': '数据库管理', 'icon': 'fas fa-database', 'path': '/settings/database-settings'},
                    {'name': '安全设置', 'icon': 'fas fa-shield-alt', 'path': '/settings/security'}
                ]
            },
            'hardware_admin': {
                'name': '硬件管理员',
                'redirect': '/settings',
                'description': '系统设置（最高权限）',
                'permissions': ['full_access'],
                'sidebar_items': [
                    {'name': '用户管理', 'icon': 'fas fa-users', 'path': '/settings/users'},
                    {'name': '角色管理', 'icon': 'fas fa-lock', 'path': '/settings/permissions'},
                    {'name': '系统日志', 'icon': 'fas fa-file-log', 'path': '/settings/logs'},
                    {'name': '数据库管理', 'icon': 'fas fa-database', 'path': '/settings/database-settings'},
                    {'name': '安全设置', 'icon': 'fas fa-shield-alt', 'path': '/settings/security'},
                    {'name': '硬件管理', 'icon': 'fas fa-key', 'path': '/settings/hardware'}
                ]
            },
            'hardware_vikey_admin': {
                'name': '硬件管理员',
                'redirect': '/settings',
                'description': '系统设置（最高权限）',
                'permissions': ['full_access'],
                'sidebar_items': [
                    {'name': '用户管理', 'icon': 'fas fa-users', 'path': '/settings/users'},
                    {'name': '角色管理', 'icon': 'fas fa-lock', 'path': '/settings/permissions'},
                    {'name': '系统日志', 'icon': 'fas fa-file-log', 'path': '/settings/logs'},
                    {'name': '数据库管理', 'icon': 'fas fa-database', 'path': '/settings/database-settings'},
                    {'name': '安全设置', 'icon': 'fas fa-shield-alt', 'path': '/settings/security'},
                    {'name': '硬件管理', 'icon': 'fas fa-key', 'path': '/settings/hardware'}
                ]
            },
            'guest': {
                'name': '访客',
                'redirect': '/',
                'description': '首页',
                'permissions': [],
                'sidebar_items': []
            }
        }
        return rules

    def get_redirect_path(self, role: str) -> str:
        """获取角色对应的跳转路径"""
        return self.rules.get(role, self.rules['guest'])['redirect']

    def get_role_info(self, role: str) -> dict:
        """获取角色完整信息"""
        return self.rules.get(role, self.rules['guest'])

    def get_sidebar_items(self, role: str) -> list:
        """获取角色的侧边栏菜单"""
        return self.rules.get(role, self.rules['guest'])['sidebar_items']

    def get_role_list(self) -> list:
        """获取所有角色列表"""
        return [{'role': k, 'name': v['name'], 'description': v['description']} 
                for k, v in self.rules.items()]


# ==================== 全局实例 ====================

_router_instance = None

def get_role_router() -> RoleRouter:
    global _router_instance
    if _router_instance is None:
        _router_instance = RoleRouter()
    return _router_instance


# ==================== API Blueprint ====================

role_router_bp = Blueprint('role_router', __name__, url_prefix='/api/role-router')


@role_router_bp.route('/rules', methods=['GET'])
def get_rules():
    """获取所有角色跳转规则"""
    router = get_role_router()
    return jsonify({
        'success': True,
        'rules': router.get_role_list()
    })


@role_router_bp.route('/redirect', methods=['GET'])
def get_redirect():
    """获取当前用户的跳转路径"""
    role = session.get('role', 'guest')
    router = get_role_router()
    info = router.get_role_info(role)
    return jsonify({
        'success': True,
        'role': role,
        'redirect': info['redirect'],
        'name': info['name'],
        'description': info['description'],
        'sidebar_items': info['sidebar_items']
    })


@role_router_bp.route('/role-info/<role>', methods=['GET'])
def get_role_info(role):
    """获取指定角色的信息"""
    router = get_role_router()
    info = router.get_role_info(role)
    return jsonify({
        'success': True,
        'role': role,
        **info
    })


# ==================== 登录后自动跳转路由 ====================

def create_role_routes(app):
    """注册角色路由API（路由本身已在app.py中定义）"""
    if hasattr(app, '_role_routes_created') and app._role_routes_created:
        return app

    app._role_routes_created = True
    return app
