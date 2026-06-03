# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI自动化服务 - 负责管理和协调AI自动化系统
"""

from app.ai.automation import ai_automation_manager
from app.utils.logging import logger
import threading
import time
import logging
import sys


class AIAutomationService:
    """AI自动化服务类"""

    def __init__(self):
        self.is_running = False
        self.thread = None
        self.auto_generation_enabled = True
        self.plan_execution_interval = 3600

    def start(self):
        """启动AI自动化服务"""
        if self.is_running:
            logger.info("AI自动化服务已在运行")
            return

        logger.info("启动AI自动化服务...")
        self.is_running = True

        if self.auto_generation_enabled:
            self._auto_generate_ai_system()

        self.thread = threading.Thread(target=self._run_plan_execution_loop, daemon=True)
        self.thread.start()

        logger.info("AI自动化服务启动成功")

    def stop(self):
        """停止AI自动化服务"""
        if not self.is_running:
            logger.info("AI自动化服务未在运行")
            return

        logger.info("停止AI自动化服务...")
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)

        logger.info("AI自动化服务已停止")

    def _auto_generate_ai_system(self):
        """自动生成AI系统"""
        try:
            logger.info("开始自动生成AI系统...")
            success = ai_automation_manager.auto_generate_ai_system()
            if success:
                logger.info("AI系统自动生成成功")
            else:
                logger.error("AI系统自动生成失败")
        except Exception as e:
            logger.error(f"自动生成AI系统时发生错误: {str(e)}")

    def _run_plan_execution_loop(self):
        """AI计划执行循环"""
        while self.is_running:
            try:
                self._execute_pending_plans()
                time.sleep(self.plan_execution_interval)
            except Exception as e:
                logger.error(f"执行AI计划时发生错误: {str(e)}")
                time.sleep(60)

    def _execute_pending_plans(self):
        """执行所有待处理的AI计划"""
        try:
            plans = ai_automation_manager.get_ai_plans()
            for plan in plans:
                if plan.get('status') == 'draft':
                    logger.info(f"执行AI计划: {plan['name']} ({plan['plan_id']})")
                    success = ai_automation_manager.execute_ai_plan(plan['plan_id'])
                    if success:
                        logger.info(f"AI计划执行成功: {plan['name']} ({plan['plan_id']})")
                    else:
                        logger.error(f"AI计划执行失败: {plan['name']} ({plan['plan_id']})")
        except Exception as e:
            logger.error(f"执行AI计划时发生错误: {str(e)}")

    def generate_ai_butler(self, name, description=""):
        """生成AI管家"""
        try:
            return ai_automation_manager.create_ai_butler(name, description)
        except Exception as e:
            logger.error(f"生成AI管家失败: {str(e)}")
            return None

    def generate_ai_collection(self, name, description=""):
        """生成AI集"""
        try:
            return ai_automation_manager.create_ai_collection(name, description)
        except Exception as e:
            logger.error(f"生成AI集失败: {str(e)}")
            return None

    def generate_ai_employee(self, name, role, responsibilities, collection_id=None):
        """生成AI员工"""
        try:
            return ai_automation_manager.create_ai_employee(name, role, responsibilities, collection_id)
        except Exception as e:
            logger.error(f"生成AI员工失败: {str(e)}")
            return None

    def generate_ai_plan(self, name, description="", tasks=None):
        """生成AI计划表"""
        try:
            return ai_automation_manager.create_ai_plan(name, description, tasks)
        except Exception as e:
            logger.error(f"生成AI计划表失败: {str(e)}")
            return None

    def get_ai_butlers(self):
        """获取所有AI管家"""
        return ai_automation_manager.get_ai_butlers()

    def get_ai_plans(self):
        """获取所有AI计划表"""
        return ai_automation_manager.get_ai_plans()


ai_automation_service = AIAutomationService()
