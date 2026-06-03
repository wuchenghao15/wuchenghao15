# -*- coding: utf-8 -*-
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ExamPermissionManager:
    """考试权限管理器: 负责管理和应用考试系统的权限"""

    def __init__(self, config_file: str = None):
        self.instance_id = f"exam_permission_manager_{id(self)}"
        self.name = "考试权限管理器"
        self.description = "负责管理和应用考试系统的权限"
        self.logger = logger
        self.logger.info(f"初始化考试权限管理器: {self.instance_id}")

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
                "provide_feedback",
                "view_reports",
                "create_exams"
            ],
            "student": [
                "view_results"
            ],
            "assistant": []
        }

        self.permission_history = {
            "teacher": [],
            "student": [],
            "assistant": []
        }

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
        """获取角色的权限列表

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

    def add_role(self, role: str, permissions: List[str] = None):
        """添加角色

        Args:
            role: 角色名称
            permissions: 权限列表
        """
        if role not in self.permissions:
            self.permissions[role] = permissions or []

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

    def get_permission_history(self, role: str) -> List[Dict[str, Any]]:
        """获取权限历史记录

        Args:
            role: 角色名称

        Returns:
            权限历史记录列表
        """
        if role in self.permission_history:
            return self.permission_history[role]
        return []

    def __str__(self):
        return f"ExamPermissionManager(instance_id={self.instance_id}, name={self.name})"

    def __repr__(self):
        return self.__str__()
