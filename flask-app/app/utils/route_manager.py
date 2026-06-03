# -*- coding: utf-8 -*-
import logging
from typing import Dict, List, Any, Callable
from flask import Blueprint, request, redirect, url_for

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RouteManager:
    """路由管理器: 负责管理和应用不同的路由规则"""

    def __init__(self, config_file: str = None):
        self.instance_id = f"route_manager_{id(self)}"
        self.name = "路由管理器"
        self.description = "负责管理和应用不同的路由规则"
        self.logger = logger
        self.logger.info(f"初始化路由管理器: {self.instance_id}")

        self.routes = {
            'auth': {
                "login": "/login",
                "register": "/register",
                "logout": "/logout",
                "forgot_password": "/forgot-password",
                "reset_password": "/reset-password/<token>",
                "auto_guest_login": "/auto_guest_login",
                "confirm_guest_logout": "/confirm_guest_logout",
                "github_login": "/github/login",
                "google_login": "/google/login",
                "weixin_login": "/weixin/login",
                "github_callback": "/auth/github/callback",
                "google_callback": "/auth/google/callback",
                "weixin_callback": "/auth/weixin/callback",
                "login_vikey": "/api/auth/login-vikey"
            },
            'main': {
                "index": "/",
                "index_html": "/index.html",
                "admin_center": "/admin/center",
                "test_system": "/test-system"
            },
            'language_tests': {
                "test_system": "/test-system",
                "japanese_test": "/test-system/japanese"
            },
            'integrated_design': {
                "integrated_design": "/integrated-design"
            },
            'api': {
                "auto_update": "/api/auto-update",
                "exam_test": "/api"
            },
            'debug': {
                "routes": "/debug/routes"
            },
            'health': {
                "check": "/health"
            },
            'test': {
                "test": "/test",
                "preloader": "/test/preloader",
                "auto_update_status": "/test/auto-update/status"
            }
        }

        self.route_permissions = {
            "auth.login": [],
            "auth.register": [],
            "auth.forgot_password": [],
            "auth.reset_password": [],
            "auth.auto_guest_login": [],
            "auth.confirm_guest_logout": [],
            "auth.github_login": [],
            "auth.google_login": [],
            "auth.weixin_login": [],
            "auth.github_callback": [],
            "auth.google_callback": [],
            "auth.weixin_callback": [],
            "auth.login_vikey": [],
            "main.index": [],
            "main.index_html": [],
            "main.admin_center": ["admin"],
            "main.test_system": [],
            "language_tests.test_system": [],
            "language_tests.japanese_test": [],
            "integrated_design.integrated_design": ["admin"],
            "api.auto_update": ["admin"],
            "api.exam_test": [],
            "debug.routes": ["admin"],
            "health.check": [],
            "test.test": [],
            "test.preloader": [],
            "test.auto_update_status": ["admin"]
        }

        self.blueprints = {}

        if config_file:
            self.load_config(config_file)

    def load_config(self, config_file: str):
        """加载路由配置文件

        Args:
            config_file: 配置文件路径
        """
        try:
            import json
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if "routes" in config:
                    self.routes.update(config["routes"])
                if "route_permissions" in config:
                    self.route_permissions.update(config["route_permissions"])
                self.logger.info(f"加载路由配置文件成功: {config_file}")
        except Exception as e:
            self.logger.error(f"加载路由配置文件失败: {str(e)}")

    def save_config(self, config_file: str):
        """保存路由配置到文件

        Args:
            config_file: 配置文件路径
        """
        try:
            import json
            config = {
                "routes": self.routes,
                "route_permissions": self.route_permissions
            }
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存路由配置文件失败: {str(e)}")

    def get_route(self, blueprint: str, route_name: str):
        """获取路由

        Args:
            blueprint: 蓝图名称
            route_name: 路由名称

        Returns:
            路由路径
        """
        if blueprint in self.routes and route_name in self.routes[blueprint]:
            return self.routes[blueprint][route_name]
        return None

    def set_route(self, blueprint: str, route_name: str, path: str):
        """设置路由

        Args:
            blueprint: 蓝图名称
            route_name: 路由名称
            path: 路由路径
        """
        if blueprint not in self.routes:
            self.routes[blueprint] = {}
        self.routes[blueprint][route_name] = path
        self.logger.info(f"设置路由: {blueprint}.{route_name} = {path}")

    def get_route_permissions(self, route: str) -> List[str]:
        """获取路由的权限要求

        Args:
            route: 路由名称,格式为 "blueprint.route"

        Returns:
            权限列表
        """
        if route in self.route_permissions:
            return self.route_permissions[route]
        return []

    def set_route_permission(self, route: str, permissions: List[str]):
        """设置路由的权限要求

        Args:
            route: 路由名称,格式为 "blueprint.route"
            permissions: 权限列表
        """
        self.route_permissions[route] = permissions
        self.logger.info(f"设置路由权限: {route} = {permissions}")

    def register_blueprint(self, blueprint: Blueprint):
        """注册蓝图

        Args:
            blueprint: 蓝图实例
        """
        self.blueprints[blueprint.name] = blueprint
        self.logger.info(f"注册蓝图: {blueprint.name}")

    def get_blueprint(self, blueprint_name: str) -> Blueprint:
        """获取蓝图

        Args:
            blueprint_name: 蓝图名称

        Returns:
            蓝图实例
        """
        if blueprint_name in self.blueprints:
            return self.blueprints[blueprint_name]
        return None

    def register_all_routes(self, app):
        """注册所有路由

        Args:
            app: Flask应用实例
        """
        for blueprint_name, blueprint in self.blueprints.items():
            app.register_blueprint(blueprint)
            self.logger.info(f"注册蓝图路由: {blueprint_name}")

    def check_route_permission(self, route: str, user_role: str, user_permissions: List[str]) -> bool:
        """检查路由权限

        Args:
            route: 路由名称,格式为 "blueprint.route"
            user_role: 用户角色
            user_permissions: 用户权限列表

        Returns:
            是否有权限
        """
        required_permissions = self.get_route_permissions(route)
        if not required_permissions:
            return True

        for perm in required_permissions:
            if perm not in user_permissions:
                return False
        return True

    def __str__(self):
        return f"RouteManager(instance_id={self.instance_id})"

    def __repr__(self):
        return self.__str__()
