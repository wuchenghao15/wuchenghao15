import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ServerPermissionManager:
    """子服务器权限管理器，负责管理和应用子服务器系统的权限"""
    
    def __init__(self, config_file: str = None):
        self.instance_id = f"server_permission_manager_{id(self)}"
        self.name = "子服务器权限管理器"
        self.description = "负责管理和应用子服务器系统的权限"
        self.logger = logger
        self.logger.info(f"初始化子服务器权限管理器: {self.instance_id}")
        
        # 权限存储
        self.permissions = {
            "admin": [
                "manage_servers",
                "manage_rules",
                "manage_permissions",
                "view_server_info",
                "view_server_stats",
                "view_server_logs",
                "start_server",
                "stop_server",
                "restart_server",
                "deploy_server",
                "undeploy_server",
                "manage_server_config",
                "manage_server_resources",
                "manage_load_balancing",
                "manage_security",
                "view_ai_analysis",
                "manage_ai_settings"
            ],
            "operator": [
                "view_server_info",
                "view_server_stats",
                "view_server_logs",
                "start_server",
                "stop_server",
                "restart_server",
                "view_ai_analysis"
            ],
            "monitor": [
                "view_server_info",
                "view_server_stats",
                "view_server_logs",
                "view_ai_analysis"
            ],
            "guest": [
                "view_server_info"
            ]
        }
        
        # 权限历史记录
        self.permission_history = {
            "admin": [],
            "operator": [],
            "monitor": [],
            "guest": []
        }
        
        # 加载配置文件
        if config_file:
            self.load_config(config_file)
    
    def load_config(self, config_file: str):
        """加载权限配置文件
        
        Args:
            config_file: 配置文件路径
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if "server_permissions" in config:
                    self.permissions.update(config["server_permissions"])
                self.logger.info(f"加载子服务器权限配置文件成功: {config_file}")
        except Exception as e:
            self.logger.error(f"加载子服务器权限配置文件失败: {str(e)}")
    
    def save_config(self, config_file: str):
        """保存权限配置到文件
        
        Args:
            config_file: 配置文件路径
        """
        try:
            config = {
                "server_permissions": self.permissions
            }
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                self.logger.info(f"保存子服务器权限配置文件成功: {config_file}")
        except Exception as e:
            self.logger.error(f"保存子服务器权限配置文件失败: {str(e)}")
    
    def get_permissions(self, role: str) -> List[str]:
        """获取角色的权限
        
        Args:
            role: 角色名称
            
        Returns:
            权限列表
        """
        if role in self.permissions:
            return self.permissions[role]
        return []
    
    def add_permission(self, role: str, permission: str):
        """添加权限
        
        Args:
            role: 角色名称
            permission: 权限名称
        """
        if role not in self.permissions:
            self.permissions[role] = []
        
        # 记录权限历史
        if role not in self.permission_history:
            self.permission_history[role] = []
        
        if permission not in self.permissions[role]:
            self.permission_history[role].append({
                "action": "add",
                "permission": permission,
                "timestamp": datetime.now().isoformat()
            })
            
            self.permissions[role].append(permission)
            self.logger.info(f"添加权限: {role} -> {permission}")
    
    def remove_permission(self, role: str, permission: str):
        """移除权限
        
        Args:
            role: 角色名称
            permission: 权限名称
        """
        if role in self.permissions and permission in self.permissions[role]:
            # 记录权限历史
            if role not in self.permission_history:
                self.permission_history[role] = []
            
            self.permission_history[role].append({
                "action": "remove",
                "permission": permission,
                "timestamp": datetime.now().isoformat()
            })
            
            self.permissions[role].remove(permission)
            self.logger.info(f"移除权限: {role} -> {permission}")
    
    def has_permission(self, role: str, permission: str) -> bool:
        """检查角色是否有指定权限
        
        Args:
            role: 角色名称
            permission: 权限名称
            
        Returns:
            是否有权限
        """
        if role in self.permissions:
            return permission in self.permissions[role]
        return False
    
    def update_permissions(self, role: str, permissions: List[str]):
        """更新角色的权限
        
        Args:
            role: 角色名称
            permissions: 权限列表
        """
        # 记录权限历史
        if role not in self.permission_history:
            self.permission_history[role] = []
        
        # 记录旧权限
        old_permissions = self.permissions.get(role, [])
        
        # 记录新增的权限
        for permission in permissions:
            if permission not in old_permissions:
                self.permission_history[role].append({
                    "action": "add",
                    "permission": permission,
                    "timestamp": datetime.now().isoformat()
                })
        
        # 记录移除的权限
        for permission in old_permissions:
            if permission not in permissions:
                self.permission_history[role].append({
                    "action": "remove",
                    "permission": permission,
                    "timestamp": datetime.now().isoformat()
                })
        
        # 更新权限
        self.permissions[role] = permissions
        self.logger.info(f"更新权限: {role}, 权限数: {len(permissions)}")
    
    def get_roles(self) -> List[str]:
        """获取所有角色
        
        Returns:
            角色列表
        """
        return list(self.permissions.keys())
    
    def add_role(self, role: str, permissions: List[str] = None):
        """添加角色
        
        Args:
            role: 角色名称
            permissions: 权限列表
        """
        if role not in self.permissions:
            self.permissions[role] = permissions or []
            self.logger.info(f"添加角色: {role}, 权限数: {len(self.permissions[role])}")
    
    def remove_role(self, role: str):
        """移除角色
        
        Args:
            role: 角色名称
        """
        if role in self.permissions:
            del self.permissions[role]
            if role in self.permission_history:
                del self.permission_history[role]
            self.logger.info(f"移除角色: {role}")
    
    def check_server_access(self, role: str, server_id: str, action: str) -> bool:
        """检查用户对服务器的访问权限
        
        Args:
            role: 角色名称
            server_id: 服务器ID
            action: 操作类型 (view, start, stop, restart, deploy, undeploy, config, resources)
            
        Returns:
            是否有权限
        """
        # 根据操作类型检查权限
        permission_map = {
            "view": "view_server_info",
            "start": "start_server",
            "stop": "stop_server",
            "restart": "restart_server",
            "deploy": "deploy_server",
            "undeploy": "undeploy_server",
            "config": "manage_server_config",
            "resources": "manage_server_resources"
        }
        
        required_permission = permission_map.get(action)
        if required_permission:
            return self.has_permission(role, required_permission)
        
        return False
    
    def check_rule_access(self, role: str, action: str) -> bool:
        """检查用户对规则的访问权限
        
        Args:
            role: 角色名称
            action: 操作类型 (view, manage)
            
        Returns:
            是否有权限
        """
        # 根据操作类型检查权限
        permission_map = {
            "view": "view_server_info",
            "manage": "manage_rules"
        }
        
        required_permission = permission_map.get(action)
        if required_permission:
            return self.has_permission(role, required_permission)
        
        return False
    
    def check_permission_access(self, role: str, action: str) -> bool:
        """检查用户对权限的访问权限
        
        Args:
            role: 角色名称
            action: 操作类型 (view, manage)
            
        Returns:
            是否有权限
        """
        # 根据操作类型检查权限
        permission_map = {
            "view": "view_server_info",
            "manage": "manage_permissions"
        }
        
        required_permission = permission_map.get(action)
        if required_permission:
            return self.has_permission(role, required_permission)
        
        return False
    
    def check_ai_access(self, role: str, action: str) -> bool:
        """检查用户对AI功能的访问权限
        
        Args:
            role: 角色名称
            action: 操作类型 (view, manage)
            
        Returns:
            是否有权限
        """
        # 根据操作类型检查权限
        permission_map = {
            "view": "view_ai_analysis",
            "manage": "manage_ai_settings"
        }
        
        required_permission = permission_map.get(action)
        if required_permission:
            return self.has_permission(role, required_permission)
        
        return False
    
    def get_permission_history(self, role: str) -> List[Dict[str, Any]]:
        """获取权限历史记录
        
        Args:
            role: 角色名称
            
        Returns:
            权限历史记录
        """
        if role in self.permission_history:
            return self.permission_history[role]
        return []
    
    def get_all_permissions(self) -> Dict[str, List[str]]:
        """获取所有权限
        
        Returns:
            权限字典
        """
        return self.permissions
    
    def __str__(self):
        return f"ServerPermissionManager(instance_id={self.instance_id}, name={self.name})"
    
    def __repr__(self):
        return self.__str__()

# 创建全局子服务器权限管理器实例
server_permission_manager = ServerPermissionManager()