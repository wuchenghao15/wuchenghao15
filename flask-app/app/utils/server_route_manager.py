import json
import logging
from typing import Dict, List, Any, Optional, Callable
from flask import Blueprint, request, redirect, url_for

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ServerRouteManager:
    """子服务器路由管理器，负责管理和应用子服务器系统的路由"""
    
    def __init__(self, config_file: str = None):
        self.instance_id = f"server_route_manager_{id(self)}"
        self.name = "子服务器路由管理器"
        self.description = "负责管理和应用子服务器系统的路由"
        self.logger = logger
        self.logger.info(f"初始化子服务器路由管理器: {self.instance_id}")
        
        # 路由规则存储
        self.routes = {
            "server": {
                "list": "/servers",
                "detail": "/servers/<server_id>",
                "register": "/servers/register",
                "unregister": "/servers/<server_id>/unregister",
                "start": "/servers/<server_id>/start",
                "stop": "/servers/<server_id>/stop",
                "restart": "/servers/<server_id>/restart",
                "deploy": "/servers/deploy",
                "undeploy": "/servers/<server_id>/undeploy",
                "config": "/servers/<server_id>/config",
                "resources": "/servers/<server_id>/resources",
                "health": "/servers/<server_id>/health",
                "stats": "/servers/<server_id>/stats",
                "logs": "/servers/<server_id>/logs"
            },
            "rule": {
                "list": "/rules",
                "detail": "/rules/<rule_type>",
                "update": "/rules/<rule_type>/update"
            },
            "permission": {
                "list": "/permissions",
                "detail": "/permissions/<role>",
                "update": "/permissions/<role>/update",
                "roles": "/permissions/roles"
            },
            "ai": {
                "analysis": "/ai/analysis",
                "prediction": "/ai/prediction",
                "anomaly": "/ai/anomaly",
                "failure": "/ai/failure",
                "optimization": "/ai/optimization",
                "settings": "/ai/settings"
            },
            "load_balancing": {
                "status": "/load-balancing",
                "strategy": "/load-balancing/strategy",
                "balance": "/load-balancing/balance"
            },
            "health": {
                "check": "/health"
            }
        }
        
        # 路由权限映射
        self.route_permissions = {
            "server.list": ["admin", "operator", "monitor"],
            "server.detail": ["admin", "operator", "monitor"],
            "server.register": ["admin"],
            "server.unregister": ["admin"],
            "server.start": ["admin", "operator"],
            "server.stop": ["admin", "operator"],
            "server.restart": ["admin", "operator"],
            "server.deploy": ["admin"],
            "server.undeploy": ["admin"],
            "server.config": ["admin"],
            "server.resources": ["admin"],
            "server.health": ["admin", "operator", "monitor"],
            "server.stats": ["admin", "operator", "monitor"],
            "server.logs": ["admin", "operator", "monitor"],
            "rule.list": ["admin", "operator", "monitor"],
            "rule.detail": ["admin", "operator", "monitor"],
            "rule.update": ["admin"],
            "permission.list": ["admin"],
            "permission.detail": ["admin"],
            "permission.update": ["admin"],
            "permission.roles": ["admin"],
            "ai.analysis": ["admin", "operator", "monitor"],
            "ai.prediction": ["admin", "operator", "monitor"],
            "ai.anomaly": ["admin", "operator", "monitor"],
            "ai.failure": ["admin", "operator", "monitor"],
            "ai.optimization": ["admin", "operator"],
            "ai.settings": ["admin"],
            "load_balancing.status": ["admin", "operator", "monitor"],
            "load_balancing.strategy": ["admin"],
            "load_balancing.balance": ["admin"],
            "health.check": []
        }
        
        # 蓝图存储
        self.blueprints = {}
        
        # 加载配置文件
        if config_file:
            self.load_config(config_file)
    
    def load_config(self, config_file: str):
        """加载路由配置文件
        
        Args:
            config_file: 配置文件路径
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if "server_routes" in config:
                    self.routes.update(config["server_routes"])
                if "server_route_permissions" in config:
                    self.route_permissions.update(config["server_route_permissions"])
                self.logger.info(f"加载子服务器路由配置文件成功: {config_file}")
        except Exception as e:
            self.logger.error(f"加载子服务器路由配置文件失败: {str(e)}")
    
    def save_config(self, config_file: str):
        """保存路由配置到文件
        
        Args:
            config_file: 配置文件路径
        """
        try:
            config = {
                "server_routes": self.routes,
                "server_route_permissions": self.route_permissions
            }
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                self.logger.info(f"保存子服务器路由配置文件成功: {config_file}")
        except Exception as e:
            self.logger.error(f"保存子服务器路由配置文件失败: {str(e)}")
    
    def get_route(self, blueprint: str, route_name: str) -> str:
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
            route: 路由名称，格式为 "blueprint.route"
            
        Returns:
            权限列表
        """
        if route in self.route_permissions:
            return self.route_permissions[route]
        return []
    
    def set_route_permission(self, route: str, permissions: List[str]):
        """设置路由的权限要求
        
        Args:
            route: 路由名称，格式为 "blueprint.route"
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
    
    def check_route_permission(self, route: str, user_role: str) -> bool:
        """检查路由权限
        
        Args:
            route: 路由名称，格式为 "blueprint.route"
            user_role: 用户角色
            
        Returns:
            是否有权限
        """
        required_permissions = self.get_route_permissions(route)
        
        # 如果不需要权限，直接通过
        if not required_permissions:
            return True
        
        # 检查用户角色
        if user_role in required_permissions:
            return True
        
        return False
    
    def get_all_routes(self) -> Dict[str, Dict[str, str]]:
        """获取所有路由
        
        Returns:
            路由字典
        """
        return self.routes
    
    def get_all_blueprints(self) -> Dict[str, Blueprint]:
        """获取所有蓝图
        
        Returns:
            蓝图字典
        """
        return self.blueprints
    
    def __str__(self):
        return f"ServerRouteManager(instance_id={self.instance_id}, name={self.name})"
    
    def __repr__(self):
        return self.__str__()

# 创建全局子服务器路由管理器实例
server_route_manager = ServerRouteManager()