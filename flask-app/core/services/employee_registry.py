#!/usr/bin/env python3
"""
AI员工注册表
管理AI员工的注册、查询、健康维护与技能刷新。
提供单例访问入口 get_employee_registry()。
"""
import os
import sys
import logging

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

logger = logging.getLogger(__name__)


class EmployeeRegistry:
    """AI员工注册器，维护员工实例的元信息与状态。"""

    def __init__(self):
        self._employees = {}
        logger.info("EmployeeRegistry 初始化完成")

    def register_employee(self, role, employee=None):
        """注册一个AI员工。

        Args:
            role: 员工角色标识
            employee: 员工信息字典，为空时自动创建默认条目

        Returns:
            注册的员工信息字典
        """
        logger.info(f"注册AI员工: {role}")
        entry = employee if employee is not None else {'role': role, 'status': 'active'}
        if 'role' not in entry:
            entry['role'] = role
        self._employees[role] = entry
        return entry

    def get_employee(self, role):
        """获取指定角色的AI员工信息。"""
        logger.info(f"获取AI员工: {role}")
        return self._employees.get(role)

    def list_employees(self):
        """列出所有已注册的AI员工。"""
        employees = list(self._employees.values())
        logger.info(f"列出AI员工，共 {len(employees)} 个")
        return employees

    def restart_employee(self, role):
        """重启指定角色的AI员工，将其状态重置为 active。"""
        logger.info(f"重启AI员工: {role}")
        emp = self._employees.get(role)
        if emp is None:
            logger.warning(f"重启失败，未找到员工: {role}")
            return False
        emp['status'] = 'active'
        return True

    def refresh_skills(self, role):
        """刷新指定角色AI员工的技能配置。"""
        logger.info(f"刷新AI员工技能: {role}")
        if role not in self._employees:
            logger.warning(f"刷新失败，未找到员工: {role}")
            return False
        return True


_registry = None


def get_employee_registry():
    """获取 EmployeeRegistry 单例实例。"""
    global _registry
    if _registry is None:
        _registry = EmployeeRegistry()
    return _registry
