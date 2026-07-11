# -*- coding: utf-8 -*-
"""
MTSCOS AI 动态路由管理器
从统一规则配置中心动态加载路由规则，支持权限检查和热更新
"""

import logging
logger = logging.getLogger(__name__)

import os
import json
import importlib
from datetime import datetime
from flask import Flask, request, redirect, jsonify, session, render_template, abort
from functools import wraps
from typing import Dict, List, Tuple, Optional, Callable

# 从统一规则配置中心导入路由规则
try:
    from app.config.unified_rules import (
        EXAM_SYSTEM_ROUTES,
        TEST_SYSTEM_ROUTES,
        LEARNING_SYSTEM_ROUTES,
        USER_SYSTEM_ROUTES,
        ADMIN_SYSTEM_ROUTES,
        ROLE_HIERARCHY,
        SUPER_ADMIN_ROLES,
        check_route_permission,
        check_permission_by_rule,
        get_role_level,
        is_super_admin
    )
    ROUTE_RULES_LOADED = True
except ImportError as e:
    logger.error(f"加载统一规则配置失败: {e}")
    ROUTE_RULES_LOADED = False
    EXAM_SYSTEM_ROUTES = {}
    TEST_SYSTEM_ROUTES = {}
    LEARNING_SYSTEM_ROUTES = {}
    USER_SYSTEM_ROUTES = {}
    ADMIN_SYSTEM_ROUTES = {}
    ROLE_HIERARCHY = {'guest': 0, 'user': 1, 'student': 2}
    SUPER_ADMIN_ROLES = ['hardware_admin', 'system_admin']
    
    def check_route_permission(route_path, user_role):
        return True, "未加载规则，默认允许"
    
    def check_permission_by_rule(rule_code, user_role):
        return True, "未加载规则，默认允许"
    
    def get_role_level(role):
        return ROLE_HIERARCHY.get(role, 0)
    
    def is_super_admin(user_role):
        return user_role in SUPER_ADMIN_ROLES


class DynamicRouteManager:
    """动态路由管理器"""
    
    def __init__(self, app: Flask = None):
        self.app = app
        self.registered_routes = {}
        self.route_handlers = {}
        self.permission_decorators = {}
        
    def init_app(self, app: Flask):
        """初始化Flask应用"""
        self.app = app
        self._register_core_routes()
        self._setup_before_request_hook()
    
    def _register_core_routes(self):
        """注册核心路由管理API"""
        @self.app.route('/api/routes/list', methods=['GET'])
        def list_routes_api():
            """列出所有注册的路由"""
            routes = self.list_all_routes()
            return jsonify({'success': True, 'routes': routes})
        
        @self.app.route('/api/routes/reload', methods=['POST'])
        def reload_routes_api():
            """热更新路由规则"""
            try:
                self.reload_routes()
                return jsonify({'success': True, 'message': '路由规则已更新'})
            except Exception as e:
                logger.error(f"热更新路由失败: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/routes/check', methods=['POST'])
        def check_route_api():
            """检查路由权限"""
            data = request.get_json()
            route_path = data.get('route', '')
            user_role = data.get('role', 'guest')
            allowed, reason = check_route_permission(route_path, user_role)
            return jsonify({
                'success': True,
                'allowed': allowed,
                'reason': reason,
                'role_level': get_role_level(user_role)
            })
    
    def _setup_before_request_hook(self):
        """设置请求前权限检查钩子"""
        @self.app.before_request
        def before_request_permission_check():
            # 跳过静态文件和API路由
            if request.path.startswith('/static/') or request.path.startswith('/api/'):
                return None
            
            # 获取用户角色
            user_role = session.get('role', 'guest')
            user_id = session.get('user_id')
            
            # 检查路由权限
            allowed, reason = check_route_permission(request.path, user_role)
            
            if not allowed:
                logger.warning(f"权限拒绝: 用户角色={user_role}, 路径={request.path}, 原因={reason}")
                
                # 如果是未登录用户，显示美化的登录提示页面
                if user_role == 'guest' or not user_id:
                    return render_template('login_required.html', request_path=request.path), 401
                
                # 已登录但无权限，显示美化的403页面
                return render_template('403.html', current_role=user_role, request_path=request.path), 403
            
            return None
    
    def load_routes_from_rules(self):
        """从统一规则配置中心加载路由规则"""
        if not ROUTE_RULES_LOADED:
            logger.warning("统一规则配置未加载，跳过动态路由加载")
            return
        
        # 合并所有路由规则
        all_routes = {}
        all_routes.update(EXAM_SYSTEM_ROUTES)
        all_routes.update(TEST_SYSTEM_ROUTES)
        all_routes.update(LEARNING_SYSTEM_ROUTES)
        all_routes.update(USER_SYSTEM_ROUTES)
        all_routes.update(ADMIN_SYSTEM_ROUTES)
        
        # 为每个路由创建权限装饰器（避免重复注册已存在的路由）
        for route_path, route_config in all_routes.items():
            # 检查是否已存在路由（蓝图路由或app.route注册的路由）
            if self._check_existing_route(route_path):
                logger.info(f"[动态路由] 路由 {route_path} 已存在，跳过动态注册")
                # 将已存在路由的配置信息记录到registered_routes中，用于统一权限管理
                self.registered_routes[route_path] = route_config
                continue
            
            self._create_route_handler(route_path, route_config)
    
    def _create_route_handler(self, route_path: str, route_config: Dict):
        """为路由创建处理函数"""
        allowed_roles = route_config.get('allowed_roles', [])
        require_login = route_config.get('require_login', True)
        redirect_on_fail = route_config.get('redirect_on_fail', '/auth/login')
        description = route_config.get('description', '')
        
        # 创建权限检查装饰器
        def permission_decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                user_id = session.get('user_id')
                user_role = session.get('role', 'guest')
                
                # 超级管理员跳过所有权限检查
                if is_super_admin(user_role):
                    return f(*args, **kwargs)
                
                # 检查登录状态
                if require_login and not user_id:
                    if redirect_on_fail:
                        return redirect(redirect_on_fail)
                    return jsonify({'success': False, 'error': '未登录'}), 401
                
                # 检查角色权限
                if allowed_roles and user_role not in allowed_roles:
                    logger.warning(f"权限拒绝: 角色={user_role}, 路径={route_path}, 允许角色={allowed_roles}")
                    if redirect_on_fail:
                        return redirect(redirect_on_fail)
                    return jsonify({'success': False, 'error': '权限不足'}), 403
                
                return f(*args, **kwargs)
            
            return decorated_function
        
        # 保存装饰器
        self.permission_decorators[route_path] = permission_decorator
        
        # 创建路由处理函数
        def route_handler(*args, **kwargs):
            user_info = {
                'user_id': session.get('user_id'),
                'username': session.get('username', ''),
                'role': session.get('role', 'guest')
            }
            
            # 尝试渲染对应的模板
            template_name = self._get_template_name(route_path)
            if template_name and os.path.exists(os.path.join(self.app.template_folder, template_name)):
                try:
                    return render_template(template_name, user=user_info)
                except Exception as e:
                    logger.warning(f"渲染模板失败 {template_name}: {e}")
            
            # 返回路由信息
            return jsonify({
                'success': True,
                'route': route_path,
                'description': description,
                'allowed_roles': allowed_roles,
                'user': user_info
            })
        
        # 注册路由
        if route_path not in self.registered_routes:
            self.app.add_url_rule(
                route_path,
                endpoint=f'dynamic_{route_path.replace("/", "_")}',
                view_func=permission_decorator(route_handler),
                methods=['GET']
            )
            self.registered_routes[route_path] = route_config
            logger.info(f"动态注册路由: {route_path} -> 允许角色: {allowed_roles}")
    
    def _check_existing_route(self, route_path: str) -> bool:
        """检查路由是否已存在（包括蓝图路由和app.route注册的路由）"""
        if not self.app:
            return False
        
        # 检查url_map中是否已存在该路由且不是动态路由
        for rule in self.app.url_map.iter_rules():
            if str(rule) == route_path and not rule.endpoint.startswith('dynamic_'):
                return True
        
        return False
    
    def _get_template_name(self, route_path: str) -> Optional[str]:
        """根据路由路径推断模板名称"""
        template_map = {
            '/exam_system': 'exam_system.html',
            '/test_system': 'test_system.html',
            '/learning_system': 'learning_system.html',
            '/user_system': 'user_system.html',
            '/admin_center': 'admin_center.html',
            '/super_admin_dashboard': 'super_admin_dashboard.html',
            '/admin_app/exams': 'admin_exams.html'
        }
        return template_map.get(route_path)
    
    def reload_routes(self):
        """热更新路由规则（仅更新配置和权限缓存，不修改Flask路由）"""
        logger.info("开始热更新路由配置...")
        
        try:
            # 重新导入统一规则配置（强制重新加载）
            import app.config.unified_rules as unified_rules_module
            importlib.reload(unified_rules_module)
            
            # 更新registered_routes配置（用于权限检查）
            all_routes = {}
            try:
                all_routes.update(unified_rules_module.EXAM_SYSTEM_ROUTES)
                all_routes.update(unified_rules_module.TEST_SYSTEM_ROUTES)
                all_routes.update(unified_rules_module.LEARNING_SYSTEM_ROUTES)
                all_routes.update(unified_rules_module.USER_SYSTEM_ROUTES)
                all_routes.update(unified_rules_module.ADMIN_SYSTEM_ROUTES)
            except AttributeError as e:
                logger.warning(f"部分路由规则未加载: {e}")
            
            for route_path, route_config in all_routes.items():
                self.registered_routes[route_path] = route_config
            
            # 更新数据库中的路由规则缓存
            self._update_route_cache_in_db(all_routes)
            
            logger.info(f"路由配置热更新完成，共更新 {len(self.registered_routes)} 条路由规则配置")
            return True
            
        except Exception as e:
            logger.error(f"热更新路由配置失败: {e}")
            return False
    
    def _update_route_cache_in_db(self, routes_dict):
        """更新数据库中的路由规则缓存"""
        try:
            import sqlite3
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 确保表存在
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS route_config_cache (
                    route_path TEXT PRIMARY KEY,
                    allowed_roles TEXT,
                    require_login INTEGER,
                    description TEXT,
                    updated_at TEXT
                )
            ''')
            
            # 更新路由配置
            for route_path, route_config in routes_dict.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO route_config_cache 
                    (route_path, allowed_roles, require_login, description, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    route_path,
                    json.dumps(route_config.get('allowed_roles', [])),
                    route_config.get('require_login', 1),
                    route_config.get('description', ''),
                    datetime.now().isoformat()
                ))
            
            conn.commit()
            conn.close()
            logger.info("路由配置缓存已更新到数据库")
            
        except Exception as e:
            logger.warning(f"更新路由配置缓存失败: {e}")
    
    def _clear_dynamic_routes(self):
        """清除所有动态注册的路由"""
        if not self.app:
            return
        
        # 获取所有动态路由的endpoint前缀
        dynamic_endpoints = [ep for ep in self.app.view_functions.keys() if ep.startswith('dynamic_')]
        
        # 移除这些路由
        for endpoint in dynamic_endpoints:
            self.app.view_functions.pop(endpoint, None)
        
        # 从url_map中移除
        rules_to_remove = []
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint.startswith('dynamic_'):
                rules_to_remove.append(rule)
        
        for rule in rules_to_remove:
            self.app.url_map._rules.remove(rule)
            self.app.url_map._rules_by_endpoint.pop(rule.endpoint, None)
        
        self.registered_routes.clear()
        logger.info(f"已清除 {len(dynamic_endpoints)} 条动态路由")
    
    def list_all_routes(self) -> List[Dict]:
        """列出所有注册的路由"""
        if not self.app:
            return []
        
        routes = []
        for rule in self.app.url_map.iter_rules():
            is_dynamic = rule.endpoint.startswith('dynamic_')
            route_config = self.registered_routes.get(str(rule), {})
            
            # 检查是否是蓝图路由（非动态路由且存在配置）
            is_blueprint = not is_dynamic and route_config.get('description', '') != ''
            
            routes.append({
                'rule': str(rule),
                'endpoint': rule.endpoint,
                'methods': sorted([m for m in rule.methods if m not in ['OPTIONS', 'HEAD']]),
                'is_dynamic': is_dynamic,
                'is_blueprint': is_blueprint,
                'route_type': 'dynamic' if is_dynamic else ('blueprint' if is_blueprint else 'static'),
                'description': route_config.get('description', ''),
                'allowed_roles': route_config.get('allowed_roles', []),
                'require_login': route_config.get('require_login', True),
                'permission_managed_by': 'dynamic_route_manager' if route_config else 'unknown'
            })
        
        return sorted(routes, key=lambda x: x['rule'])
    
    def get_route_config(self, route_path: str) -> Optional[Dict]:
        """获取指定路由的配置"""
        return self.registered_routes.get(route_path)
    
    def add_custom_route(self, route_path: str, handler: Callable, 
                        allowed_roles: List[str] = None, 
                        methods: List[str] = None,
                        description: str = ''):
        """添加自定义路由"""
        if allowed_roles is None:
            allowed_roles = ['guest']
        if methods is None:
            methods = ['GET']
        
        # 创建权限检查装饰器
        def permission_decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                user_id = session.get('user_id')
                user_role = session.get('role', 'guest')
                
                if user_role not in allowed_roles:
                    return jsonify({'success': False, 'error': '权限不足'}), 403
                
                return f(*args, **kwargs)
            
            return decorated_function
        
        # 注册路由
        self.app.add_url_rule(
            route_path,
            endpoint=f'dynamic_custom_{route_path.replace("/", "_")}',
            view_func=permission_decorator(handler),
            methods=methods
        )
        
        self.registered_routes[route_path] = {
            'allowed_roles': allowed_roles,
            'methods': methods,
            'description': description,
            'require_login': True
        }
        
        logger.info(f"添加自定义路由: {route_path} -> {allowed_roles}")
    
    def remove_route(self, route_path: str):
        """移除指定路由"""
        if route_path not in self.registered_routes:
            return False
        
        # 获取endpoint
        endpoint = f'dynamic_{route_path.replace("/", "_")}'
        
        # 从view_functions中移除
        self.app.view_functions.pop(endpoint, None)
        
        # 从url_map中移除
        for rule in list(self.app.url_map.iter_rules()):
            if rule.endpoint == endpoint:
                self.app.url_map._rules.remove(rule)
                self.app.url_map._rules_by_endpoint.pop(endpoint, None)
                break
        
        self.registered_routes.pop(route_path, None)
        logger.info(f"移除路由: {route_path}")
        return True


# 创建全局动态路由管理器实例
dynamic_route_manager = DynamicRouteManager()


def init_dynamic_routes(app: Flask):
    """初始化动态路由系统"""
    dynamic_route_manager.init_app(app)
    dynamic_route_manager.load_routes_from_rules()
    
    # 注册路由管理API
    logger.info("[动态路由] 动态路由系统初始化完成")
    logger.info(f"[动态路由] 已注册 {len(dynamic_route_manager.registered_routes)} 条动态路由")
    
    return dynamic_route_manager


# 导出
__all__ = [
    'DynamicRouteManager',
    'dynamic_route_manager',
    'init_dynamic_routes'
]