# -*- coding: utf-8 -*-
# JSON import removed - using database
import logging
from typing import Dict, List, Any

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PermissionManager:
    """权限管理器，负责管理和应用不同的权限规则"""

    def __init__(self, config_file: str = None):
        self.instance_id = f"permission_manager_{id(self)}"
        self.name = "权限管理器"
        self.description = "负责管理和应用不同的权限规则"
        self.logger = logger
        self.logger.info(f"初始化权限管理器: {self.instance_id}")

        # 权限存储
        self.permissions = {
            "admin": {
                "name": "管理员",
                "permissions": [
                    "manage_users", "manage_system", "view_reports", "manage_ai_rules",
                    "manage_approvals", "view_logs", "system_cleanup", "system_config",
                    "manage_roles", "manage_permissions", "access_all_data", "manage_api_keys",
                    "manage_backups", "manage_security_settings", "manage_logs", "view_audit_logs",
                    "manage_sandboxes", "manage_ai_models", "manage_question_banks", "manage_tests",
                    "manage_language_tests", "access_language_tests", "manage_admin_approval",
                    "manage_sensitive_data", "manage_underlying_settings", "auto_expand_features"
                ]
            },
            "super_admin": {
                "name": "超级管理员",
                    "admin", "manage_users", "manage_system", "view_reports", "manage_ai_rules",
                    "manage_approvals", "view_logs", "system_config", "manage_roles", "manage_permissions",
                    "access_all_data", "manage_api_keys", "manage_backups", "manage_security_settings",
                    "manage_logs", "view_audit_logs", "manage_ai_models", "manage_question_banks", "manage_tests",
                    "manage_language_tests", "access_language_tests", "manage_admin_approval",
                ]
            },
                "name": "硬件Vikey管理员",
                    "manage_ai_rules", "manage_approvals", "view_logs", "system_cleanup", "system_config",
                    "manage_roles", "manage_permissions", "access_all_data", "manage_api_keys",
                    "manage_backups", "manage_security_settings", "manage_logs", "view_audit_logs",
                    "manage_language_tests", "access_language_tests", "manage_admin_approval",
                ]
            "teacher": {
                    "manage_tests", "view_students", "generate_reports", "grade_tests",
                    "manage_student_groups", "view_class_stats", "create_test_templates",
                    "grade_language_tests", "manage_language_test_settings"
            },
            "user": {
                    "take_tests", "view_results", "update_profile", "manage_projects", "manage_tasks",
                    "view_reports", "save_test_progress", "view_test_history", "manage_favorites",
                    "access_language_tests", "take_language_tests", "view_language_test_results"
                ]
            },
                "name": "游客",
                    "take_tests", "view_results", "view_test_history",
                    "access_language_tests", "take_language_tests", "view_language_test_results"
            }
        }

        if config_file:
            self.load_config(config_file)

    def load_config(self, config_file: str):

            config_file: 配置文件路径
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if "permissions" in config:
                    self.permissions.update(config["permissions"])
        except Exception as e:
            self.logger.error(f"加载权限配置文件失败: {str(e)}")

        """保存权限配置到文件

        Args:
            config_file: 配置文件路径
        """
        try:
            config = {"permissions": self.permissions}
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                self.logger.info(f"保存权限配置文件成功: {config_file}")
        except Exception as e:
            self.logger.error(f"保存权限配置文件失败: {str(e)}")

    def get_role_permissions(self, role: str) -> List[str]:
        """获取角色的权限列表

        Args:
            role: 角色名称

        Returns:
            权限列表
        """
        if role in self.permissions:
            return self.permissions[role].get("permissions", [])
        return []
    def has_permission(self, role: str, permission: str) -> bool:
        """检查角色是否拥有指定权限
        Args:
            role: 角色名称
            permission: 权限名称

        Returns:
        """
        if role not in self.permissions:
            return False

        role_permissions = self.permissions[role].get("permissions", [])

        # 检查直接权限
        if permission in role_permissions:
            return True

        # 检查继承权限（例如，admin权限包含所有子权限）
        for perm in role_permissions:
            if perm == "admin" or permission.startswith(perm + "."):
                return True

        return False

    def add_permission(self, role: str, permission: str):
        """为角色添加权限

        Args:
            role: 角色名称
            permission: 权限名称
        """
        if role not in self.permissions:
            self.permissions[role] = {
                "name": role,
                "permissions": []
            }

        if permission not in self.permissions[role].get("permissions", []):
            self.permissions[role]["permissions"].append(permission)
            self.logger.info(f"为角色 {role} 添加权限: {permission}")

    def remove_permission(self, role: str, permission: str):
        """从角色中移除权限

        Args:
            permission: 权限名称
        if role in self.permissions:
            permissions = self.permissions[role].get("permissions", [])
            if permission in permissions:
                permissions.remove(permission)
                self.logger.info(f"从角色 {role} 移除权限: {permission}")

        """添加新角色
        Args:
            name: 角色显示名称
            permissions: 权限列表
        """
        if role not in self.permissions:
            self.permissions[role] = {
                "name": name,
                "permissions": permissions or []
            }
            self.logger.info(f"添加新角色: {role}, 名称: {name}")

    def remove_role(self, role: str):
        """移除角色

            role: 角色名称
        """
        if role in self.permissions:
            del self.permissions[role]
            self.logger.info(f"移除角色: {role}")

    def get_all_roles(self) -> Dict[str, Dict[str, Any]]:
        """获取所有角色

        Returns:
            角色字典
        """
        return self.permissions

        """获取角色信息

        Args:

        Returns:
            角色信息
        """
            return self.permissions[role]
        return {}

    def __str__(self):
        return f"PermissionManager(instance_id={self.instance_id}, name={self.name})"

    def __repr__(self):
        return self.__str__()

# 创建全局权限管理器实例
permission_manager = PermissionManager()
