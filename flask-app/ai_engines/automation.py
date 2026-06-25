#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI自动化系统,包括AI管家,AI集,AI员工和AI计划表
"""

import uuid
import time
import json
from app.utils.logging import logger
try:
    from app.models.ai import AIInstance, AICollection
except ImportError:
    AIInstance = None
    AICollection = None
try:
    from app.models.enhanced_ai_employee import EnhancedAIEmployee
except ImportError:
    EnhancedAIEmployee = None
try:
    from app.ai.instances import ai_instance_manager
except ImportError:
    ai_instance_manager = None

class AIAutomationManager:
    """AI自动化管理器: 负责协调和管理AI管家,AI集,AI员工和AI计划表"""

    def __init__(self):
        self.ai_butlers = {}
        self.ai_plans = {}
        self.auto_generation_enabled = True
        self._load_ai_butlers()
        self._load_ai_plans()

    def _load_ai_butlers(self):
        """从数据库加载AI管家"""
        try:
            instances = AIInstance.get_all_instances()
            for instance in instances:
                if instance.ai_type == "butler":
                    self.ai_butlers[instance.instance_id] = instance.to_dict()
            logger.info(f"从数据库加载了 {len(self.ai_butlers)} 个AI管家")
        except Exception as e:
            logger.error(f"加载AI管家失败: {str(e)}")

    def _load_ai_plans(self):
        """从数据库加载AI计划表"""
        try:
            from app.utils.db import db_manager
            rows = db_manager.fetch_all('SELECT * FROM ai_plans')
            for row in rows:
                plan = {
                    'plan_id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'status': row[3],
                    'start_time': row[4],
                    'end_time': row[5],
                    'tasks': eval(row[6]) if row[6] else [],
                    'created_by': row[7],
                    'created_at': row[8],
                    'updated_at': row[9]
                }
                self.ai_plans[plan['plan_id']] = plan
            logger.info(f"从数据库加载了 {len(self.ai_plans)} 个AI计划表")
        except Exception as e:
            logger.error(f"加载AI计划表失败: {str(e)}")

    def create_ai_butler(self, name, description=""):
        """创建AI管家
        
        AI管家负责系统的整体管理和协调,是AI系统的核心管理者
        """
        try:
            instance_id = f"butler_{uuid.uuid4().hex[:8]}"
            ai_butler = AIInstance(
                instance_id=instance_id,
                ai_type="butler",
                name=name,
                description=description,
                functions=[
                    "system_monitoring",
                    "task_coordination",
                    "resource_management",
                    "problem_diagnosis",
                    "self_optimization"
                ],
                responsibilities=[
                    "管理和协调所有AI实例",
                    "监控系统运行状态",
                    "优化系统性能",
                    "处理系统异常",
                    "生成和执行AI计划"
                ],
                status="active",
                config={
                    "monitoring_interval": 60,
                    "optimization_interval": 3600,
                }
            )

            ai_butler.save()
            self.ai_butlers[instance_id] = ai_butler.to_dict()

            logger.info(f"创建AI管家成功: {instance_id}, 名称: {name}")
            return ai_butler
        except Exception as e:
            logger.error(f"创建AI管家失败: {str(e)}")
            return None

    def create_ai_employee(self, name, role, responsibilities, collection_id=None):
        """创建AI员工
        
        AI员工是具有特定职责的AI实例,用于执行具体的系统任务
        """
        try:
            instance_id = f"employee_{uuid.uuid4().hex[:8]}"

            functions_map = {
                "monitor": ["system_monitoring", "performance_analysis", "alert_generation"],
                "optimizer": ["performance_optimization", "resource_allocation", "system_tuning"],
                "maintainer": ["system_maintenance", "bug_fixing", "data_backup"],
                "analyzer": ["data_analysis", "report_generation", "trend_prediction"],
                "developer": ["code_generation", "feature_development", "system_extension"]
            }

            functions = functions_map.get(role, ["general_task"])

            ai_employee = AIInstance(
                instance_id=instance_id,
                collection_id=collection_id,
                ai_type="employee",
                name=name,
                description=f"AI员工,角色: {role}",
                functions=functions,
                responsibilities=responsibilities,
                status="active",
                config={
                    "role": role,
                    "performance_target": 0.95,
                    "response_time": 1.0
                }
            )

            ai_employee.save()
            logger.info(f"创建AI员工成功: {instance_id}, 名称: {name}, 角色: {role}")
            return ai_employee
        except Exception as e:
            logger.error(f"创建AI员工失败: {str(e)}")
            return None

    def create_ai_plan(self, name, description="", tasks=None):
        """创建AI计划表
        
        AI计划表用于自动化生成和管理系统运行计划,提高系统的自动化程度
        """
        try:
            plan_id = f"plan_{uuid.uuid4().hex[:8]}"
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")

            from app.utils.db import db_manager
            
            db_manager.execute('''
                CREATE TABLE IF NOT EXISTS ai_plans (
                    plan_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL DEFAULT 'draft',
                    start_time TEXT,
                    end_time TEXT,
                    tasks TEXT NOT NULL DEFAULT '[]',
                    created_by TEXT NOT NULL DEFAULT 'system',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            db_manager.execute('''
                INSERT INTO ai_plans (plan_id, name, description, status, tasks, created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (plan_id, name, description, "draft", str(tasks or []), "system", current_time, current_time))

            ai_plan = {
                'plan_id': plan_id,
                'name': name,
                'description': description,
                'status': "draft",
                'start_time': None,
                'end_time': None,
                'tasks': tasks or [],
                'created_by': "system",
                'created_at': current_time,
                'updated_at': current_time
            }

            self.ai_plans[plan_id] = ai_plan
            logger.info(f"创建AI计划表成功: {plan_id}, 名称: {name}")
            return ai_plan
        except Exception as e:
            logger.error(f"创建AI计划表失败: {str(e)}")
            return None

    def create_ai_collection(self, name, description=""):
        """创建AI集"""
        try:
            collection_id = f"collection_{uuid.uuid4().hex[:8]}"
            collection = AICollection(
                collection_id=collection_id,
                name=name,
                description=description,
                status="active"
            )
            collection.save()
            logger.info(f"创建AI集成功: {collection_id}, 名称: {name}")
            return collection
        except Exception as e:
            logger.error(f"创建AI集失败: {str(e)}")
            return None

    def auto_generate_ai_system(self):
        """自动生成完整的AI系统,包括AI管家,AI集和AI员工
        
        根据系统需求自动生成所需的AI组件,提高系统的智能化和自动化程度
        """
        if not self.auto_generation_enabled:
            logger.info("AI自动生成功能已禁用")
            return False

        try:
            logger.info("开始自动生成AI系统...")

            if not self.ai_butlers:
                ai_butler = self.create_ai_butler(
                    name="系统管家",
                    description="负责系统的整体管理和协调,是AI系统的核心管理者"
                )
                if ai_butler:
                    logger.info(f"自动生成AI管家: {ai_butler.instance_id}")

            core_collection = self.create_ai_collection(
                name="核心AI集",
                description="核心AI员工集合"
            )

            if core_collection:
                ai_roles = [
                    {
                        "name": "系统监控员",
                        "role": "monitor",
                        "responsibilities": ["监控系统运行状态", "生成系统告警", "分析系统性能"]
                    },
                    {
                        "name": "系统优化师",
                        "role": "optimizer",
                        "responsibilities": ["优化系统性能", "分配系统资源", "调整系统参数"]
                    },
                    {
                        "name": "系统维护员",
                        "role": "maintainer",
                        "responsibilities": ["执行系统维护", "修复系统故障", "备份系统数据"]
                    },
                    {
                        "name": "数据分析员",
                        "role": "analyzer",
                        "responsibilities": ["分析系统数据", "生成分析报告", "预测系统趋势"]
                    },
                    {
                        "name": "系统开发员",
                        "role": "developer",
                        "responsibilities": ["生成系统代码", "开发新功能", "扩展系统能力"]
                    }
                ]

                for role_info in ai_roles:
                    ai_employee = self.create_ai_employee(
                        name=role_info["name"],
                        role=role_info["role"],
                        responsibilities=role_info["responsibilities"],
                        collection_id=core_collection.collection_id
                    )
                    if ai_employee:
                        logger.info(f"自动生成AI员工: {ai_employee.instance_id}, 角色: {role_info['role']}")

            ai_plan = self.create_ai_plan(
                name="系统日常维护计划",
                description="系统日常维护和优化计划",
                tasks=[
                    {
                        "task_id": f"task_{uuid.uuid4().hex[:8]}",
                        "name": "系统监控",
                        "description": "监控系统运行状态",
                        "assignee": "system_monitor",
                        "priority": "high",
                        "frequency": "every_5_minutes",
                        "status": "pending"
                    },
                    {
                        "task_id": f"task_{uuid.uuid4().hex[:8]}",
                        "name": "性能优化",
                        "description": "优化系统性能",
                        "assignee": "system_optimizer",
                        "priority": "medium",
                        "frequency": "every_hour",
                        "status": "pending"
                    },
                    {
                        "task_id": f"task_{uuid.uuid4().hex[:8]}",
                        "name": "数据备份",
                        "description": "备份系统数据",
                        "assignee": "system_maintainer",
                        "priority": "high",
                        "frequency": "every_day",
                        "status": "pending"
                    }
                ]
            )

            if ai_plan:
                logger.info(f"自动生成AI计划表: {ai_plan['plan_id']}")

            logger.info("AI系统自动生成完成")
            return True
        except Exception as e:
            logger.error(f"自动生成AI系统失败: {str(e)}")
            return False

    def get_ai_butlers(self):
        """获取所有AI管家"""
        return list(self.ai_butlers.values())

    def get_ai_plans(self):
        """获取所有AI计划表"""
        return list(self.ai_plans.values())

    def get_ai_plan(self, plan_id):
        """获取指定AI计划表"""
        return self.ai_plans.get(plan_id)

    def update_ai_plan(self, plan_id, updates):
        """更新AI计划表"""
        if plan_id not in self.ai_plans:
            return False
        
        self.ai_plans[plan_id].update(updates)
        self.ai_plans[plan_id]['updated_at'] = time.strftime("%Y-%m-%d %H:%M:%S")
        return True

    def delete_ai_plan(self, plan_id):
        """删除AI计划表"""
        if plan_id in self.ai_plans:
            del self.ai_plans[plan_id]
            return True
        return False
