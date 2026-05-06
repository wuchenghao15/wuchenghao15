# -*- coding: utf-8 -*-
# JSON import removed - using database
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExamPermissionManager:
    """考试权限管理器，负责管理和应用考试系统的权限"""

    def __init__(self, config_file: str = None):
        self.instance_id = f"exam_permission_manager_{id(self)}"
        self.name = "考试权限管理器"
        self.description = "负责管理和应用考试系统的权限"
        self.logger = logger
        self.logger.info(f"初始化考试权限管理器: {self.instance_id}")

        # 权限存储
        self.permissions = {
            "admin": [
                "manage_system",
                "manage_users",
                "manage_questions",
                "manage_exams",
                "view_reports",
                "generate_questions",
                "create_exams",
                "score_exams",
                "analyze_learning_patterns",
                "detect_cheating",
                "generate_adaptive_tests",
                "provide_feedback"
            ],
            "teacher": [
                "manage_exams",
                "generate_questions",
                "score_exams",
                "provide_feedback"
            "student": [
                "view_results",
            ],
                "view_reports",
                "create_exams"
        }

        self.permission_history = {
            "teacher": [],
            "student": [],
            "assistant": []
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
                config = json.load(f)
                if "exam_permissions" in config:
                    self.permissions.update(config["exam_permissions"])
                self.logger.info(f"加载考试权限配置文件成功: {config_file}")
        except Exception as e:
            self.logger.error(f"加载考试权限配置文件失败: {str(e)}")

    def save_config(self, config_file: str):
        """保存权限配置到文件

        Args:
            config_file: 配置文件路径
        """
        try:
            config = {
                "exam_permissions": self.permissions
            }
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                self.logger.info(f"保存考试权限配置文件成功: {config_file}")
        except Exception as e:
            self.logger.error(f"保存考试权限配置文件失败: {str(e)}")

    def get_permissions(self, role: str) -> List[str]:

            role: 角色名称

        """
        if role in self.permissions:
            return self.permissions[role]
        return []

    def add_permission(self, role: str, permission: str):
        """添加权限
        Args:
            role: 角色名称
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

            self.logger.info(f"移除权限: {role} -> {permission}")

    def has_permission(self, role: str, permission: str) -> bool:
        """检查角色是否有指定权限

        Args:
            role: 角色名称
            permission: 权限名称
        Returns:
            是否有权限
        """
            return permission in self.permissions[role]

        """更新角色的权限

            permissions: 权限列表
        """
        if role not in self.permission_history:

        old_permissions = self.permissions.get(role, [])

        for permission in permissions:
            if permission not in old_permissions:
                self.permission_history[role].append({
                    "permission": permission,
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

    def get_roles(self) -> List[str]:

        Returns:
        """
        return list(self.permissions.keys())

    def add_role(self, role: str, permissions: List[str] = None):
        """添加角色

        Args:
            role: 角色名称
            permissions: 权限列表
        if role not in self.permissions:
            self.permissions[role] = permissions or []

        """移除角色

        """
        if role in self.permissions:
                del self.permission_history[role]
            self.logger.info(f"移除角色: {role}")
    def get_permission_history(self, role: str) -> List[Dict[str, Any]]:
        """获取权限历史记录

            role: 角色名称

        if role in self.permission_history:
            return self.permission_history[role]
        return []

        """获取所有权限

        Returns:
            权限字典
        return self.permissions

        """检查用户对考试的访问权限

        Args:
            role: 角色名称
            exam_id: 考试ID
            action: 操作类型 (view, edit, delete, take)

        Returns:
            是否有权限
        """
        # 根据操作类型检查权限
        permission_map = {
            "edit": "manage_exams",
            "delete": "manage_exams",
            "take": "take_exams"
        }
        required_permission = permission_map.get(action)
            return self.has_permission(role, required_permission)

        return False

    def check_question_access(self, role: str, question_id: str, action: str) -> bool:
        """检查用户对题目的访问权限

        Args:
            role: 角色名称
            action: 操作类型 (view, edit, delete, generate)

        Returns:
            是否有权限
        """
        # 根据操作类型检查权限
        permission_map = {
            "view": "manage_questions",
            "edit": "manage_questions",
            "delete": "manage_questions",
            "generate": "generate_questions"
        }

            return self.has_permission(role, required_permission)

        return False

    def __str__(self):
        return f"ExamPermissionManager(instance_id={self.instance_id}, name={self.name})"

    def __repr__(self):
        return self.__str__()
# 创建全局考试权限管理器实例
exam_permission_manager = ExamPermissionManager()
