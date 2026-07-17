# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
加强版AI员工服务
"""

from app.models.enhanced_ai_employee import EnhancedAIEmployee
from app.services.ai_brain_service import ai_brain_service
from app.utils.logging import logger
from app.ai.instances import ai_instance_manager
import logging
import sys


class EnhancedAIService:
    """加强版AI员工服务类"""

    def __init__(self):
        self._init_tables()

    def _init_tables(self):
        """初始化表"""
        try:
            EnhancedAIEmployee.create_table()
            logger.info("✓ 加强版AI员工表初始化成功")
        except Exception as e:
            logger.error(f"✗ 加强版AI员工表初始化失败: {str(e)}")

    def create_enhanced_ai_employee(self, name, ai_type, description, capabilities=None, config=None):
        """创建加强版AI员工"""
        try:
            ai_employee = EnhancedAIEmployee(
                name=name,
                ai_type=ai_type,
                description=description,
                capabilities=capabilities or [],
                config=config or {}
            )
            ai_employee.save()
            logger.info(f"✓ 成功创建加强版AI员工: {ai_employee.employee_id}")
            return ai_employee
        except Exception as e:
            logger.error(f"✗ 创建加强版AI员工失败: {str(e)}")
            return None

    def get_enhanced_ai_employee(self, employee_id):
        """获取加强版AI员工"""
        try:
            ai_employee = EnhancedAIEmployee.get_by_id(employee_id)
            return ai_employee
        except Exception as e:
            logger.error(f"✗ 获取加强版AI员工失败: {str(e)}")
            return None

    def get_all_enhanced_ai_employees(self):
        """获取所有加强版AI员工"""
        try:
            employees = EnhancedAIEmployee.get_all()
            return employees
        except Exception as e:
            logger.error(f"✗ 获取所有加强版AI员工失败: {str(e)}")
            return []

    def activate_enhanced_ai_employee(self, employee_id):
        """激活加强版AI员工"""
        try:
            ai_employee = self.get_enhanced_ai_employee(employee_id)
            if not ai_employee:
                logger.warning(f"✗ 未找到加强版AI员工: {employee_id}")
                return None
            ai_employee.activate()
            logger.info(f"✓ 成功激活加强版AI员工: {employee_id}")
            return ai_employee
        except Exception as e:
            logger.error(f"✗ 激活加强版AI员工失败: {str(e)}")
            return None

    def deactivate_enhanced_ai_employee(self, employee_id):
        """停用加强版AI员工"""
        try:
            ai_employee = self.get_enhanced_ai_employee(employee_id)
            if not ai_employee:
                logger.warning(f"✗ 未找到加强版AI员工: {employee_id}")
                return None
            ai_employee.deactivate()
            logger.info(f"✓ 成功停用加强版AI员工: {employee_id}")
            return ai_employee
        except Exception as e:
            logger.error(f"✗ 停用加强版AI员工失败: {str(e)}")
            return None

    def upgrade_enhanced_ai_employee(self, employee_id):
        """升级加强版AI员工"""
        try:
            ai_employee = self.get_enhanced_ai_employee(employee_id)
            if not ai_employee:
                logger.warning(f"✗ 未找到加强版AI员工: {employee_id}")
                return None
            ai_employee.upgrade()
            logger.info(f"✓ 成功升级加强版AI员工: {employee_id}")
            return ai_employee
        except Exception as e:
            logger.error(f"✗ 升级加强版AI员工失败: {str(e)}")
            return None

    def integrate_with_brain(self, employee_id):
        """与AI脑库集成"""
        try:
            ai_employee = self.get_enhanced_ai_employee(employee_id)
            if not ai_employee:
                logger.warning(f"✗ 未找到加强版AI员工: {employee_id}")
                return None
            ai_brain_service.integrate(ai_employee)
            logger.info(f"✓ 成功将AI员工与脑库集成: {employee_id}")
            return ai_employee
        except Exception as e:
            logger.error(f"✗ 与AI脑库集成失败: {str(e)}")
            return None

    def adapt_to_system(self, employee_id):
        """使加强版AI员工适配系统"""
        try:
            ai_employee = self.get_enhanced_ai_employee(employee_id)
            if not ai_employee:
                logger.warning(f"✗ 未找到加强版AI员工: {employee_id}")
                return None
            ai_employee.adapt_to_system()
            logger.info(f"✓ 成功使AI员工适配系统: {employee_id}")
            return ai_employee
        except Exception as e:
            logger.error(f"✗ 系统适配失败: {str(e)}")
            return None

    def create_super_ai_employee(self):
        """创建超级AI员工: 具备全面系统控制能力"""
        try:
            super_ai = self.create_enhanced_ai_employee(
                name="超级系统控制AI",
                ai_type="super_controller",
                description="具备全面系统控制能力的加强版AI员工,能够控制系统并完成适配",
                capabilities=[
                    "系统控制",
                    "AI脑库管理",
                    "AI集统管",
                    "系统适配",
                    "自我学习",
                    "故障诊断",
                    "自动修复",
                ],
                config={
                    "system_control": {
                        "enabled": True,
                        "access_level": "full",
                        "permissions": ["read", "write", "execute", "admin"]
                    },
                    "brain_integration": {
                        "enabled": True,
                        "sync_interval": 300
                    },
                    "self_learning": {
                        "enabled": True,
                        "learning_rate": 0.8,
                        "memory_capacity": "unlimited"
                    },
                    "system_adaptation": {
                        "enabled": True,
                        "auto_adapt": True,
                        "adaptation_threshold": 0.5
                    }
                }
            )

            if super_ai:
                self.integrate_with_brain(super_ai.employee_id)
                self.adapt_to_system(super_ai.employee_id)
                logger.info(f"✓ 成功创建并激活超级AI员工: {super_ai.employee_id}")

            return super_ai
        except Exception as e:
            logger.error(f"✗ 创建超级AI员工失败: {str(e)}")
            return None

    def control_system(self, employee_id):
        """使加强版AI员工控制系统"""
        try:
            ai_employee = self.get_enhanced_ai_employee(employee_id)
            if not ai_employee:
                logger.warning(f"✗ 未找到加强版AI员工: {employee_id}")
                return None
            result = ai_employee.control_system()
            logger.info(f"✓ AI员工 {employee_id} 执行系统控制")
            return result
        except Exception as e:
            logger.error(f"✗ 系统控制失败: {str(e)}")
            return None


enhanced_ai_service = EnhancedAIService()
