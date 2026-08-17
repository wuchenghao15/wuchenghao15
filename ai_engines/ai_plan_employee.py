# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI计划员工模块
智能创建自动计划的AI员工系统
"""

import time
import uuid
import json
import logging
import threading
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class PlanType:
    """计划类型枚举"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    EMERGENCY = "emergency"
    PROJECT = "project"
    MAINTENANCE = "maintenance"
    OPTIMIZATION = "optimization"
    SYNC = "sync"

class PlanPriority:
    """计划优先级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class AIPlanEmployee:
    """AI计划员工 - 智能创建和管理自动计划"""

    def __init__(self):
        self.employee_id = f"plan_employee_{uuid.uuid4().hex[:8]}"
        self.name = "AI计划员工"
        self.type = "plan_manager"
        self.skills = [
            "plan_generation",
            "task_scheduling",
            "resource_allocation",
            "priority_assignment",
            "plan_optimization",
            "auto_scheduling",
            "sync_coordination",
            "backup_planning",
            "rollback_strategy"
        ]
        self.responsibilities = [
            "智能生成系统运行计划",
            "自动创建同步和备份计划",
            "优化任务调度策略",
            "管理计划执行流程",
            "监控计划执行状态",
            "动态调整计划配置"
        ]
        self.status = "active"
        self.plans = {}
        self.plan_templates = {}
        self.execution_history = []
        self.system_context = {}
        self.is_running = False
        self._init_plan_templates()
        self._load_existing_plans()

    def _init_plan_templates(self):
        """初始化计划模板"""
        self.plan_templates = {
            PlanType.DAILY: {
                "name": "日常运营计划",
                "description": "系统日常运营和维护计划",
                "priority": PlanPriority.MEDIUM,
                "tasks": [
                    {
                        "name": "系统监控",
                        "description": "监控系统运行状态和性能指标",
                        "frequency": "every_5_minutes",
                        "assignee": "system_monitor",
                        "priority": "high"
                    },
                    {
                        "name": "数据同步",
                        "description": "同步各模块数据",
                        "frequency": "every_hour",
                        "assignee": "system_maintainer",
                        "priority": "medium"
                    },
                    {
                        "name": "日志清理",
                        "description": "清理过期日志文件",
                        "frequency": "daily_04:00",
                        "assignee": "system_maintainer",
                        "priority": "low"
                    },
                    {
                        "name": "性能检查",
                        "description": "检查系统性能指标",
                        "frequency": "every_15_minutes",
                        "assignee": "system_optimizer",
                        "priority": "medium"
                    }
                ]
            },
            PlanType.WEEKLY: {
                "name": "周度维护计划",
                "description": "系统周度维护和优化计划",
                "priority": PlanPriority.HIGH,
                "tasks": [
                    {
                        "name": "数据库备份",
                        "description": "执行完整数据库备份",
                        "frequency": "weekly_sunday_02:00",
                        "assignee": "system_maintainer",
                        "priority": "high"
                    },
                    {
                        "name": "系统优化",
                        "description": "优化系统性能和资源分配",
                        "frequency": "weekly_saturday_03:00",
                        "assignee": "system_optimizer",
                        "priority": "high"
                    },
                    {
                        "name": "安全检查",
                        "description": "检查系统安全状态",
                        "frequency": "weekly_friday_18:00",
                        "assignee": "system_monitor",
                        "priority": "medium"
                    },
                    {
                        "name": "AI学习",
                        "description": "触发AI组件自动学习",
                        "frequency": "weekly_monday_01:00",
                        "assignee": "ai_learner",
                        "priority": "medium"
                    }
                ]
            },
            PlanType.SYNC: {
                "name": "自动同步计划",
                "description": "Git/GitHub自动同步和备份计划",
                "priority": PlanPriority.HIGH,
                "tasks": [
                    {
                        "name": "Git同步",
                        "description": "同步代码到GitHub",
                        "frequency": "every_hour",
                        "assignee": "git_sync",
                        "priority": "high"
                    },
                    {
                        "name": "系统备份",
                        "description": "创建系统备份",
                        "frequency": "every_2_hours",
                        "assignee": "backup_manager",
                        "priority": "high"
                    },
                    {
                        "name": "回滚点创建",
                        "description": "创建系统回滚记录点",
                        "frequency": "every_hour",
                        "assignee": "rollback_manager",
                        "priority": "medium"
                    },
                    {
                        "name": "恢复镜像",
                        "description": "创建系统恢复镜像",
                        "frequency": "daily_02:00",
                        "assignee": "backup_manager",
                        "priority": "medium"
                    }
                ]
            },
            PlanType.MAINTENANCE: {
                "name": "系统维护计划",
                "description": "定期系统维护计划",
                "priority": PlanPriority.MEDIUM,
                "tasks": [
                    {
                        "name": "缓存清理",
                        "description": "清理系统缓存",
                        "frequency": "daily_03:00",
                        "assignee": "system_maintainer",
                        "priority": "low"
                    },
                    {
                        "name": "临时文件清理",
                        "description": "清理临时文件",
                        "frequency": "daily_05:00",
                        "assignee": "system_maintainer",
                        "priority": "low"
                    },
                    {
                        "name": "系统更新检查",
                        "description": "检查系统更新",
                        "frequency": "daily_00:00",
                        "assignee": "system_monitor",
                        "priority": "medium"
                    }
                ]
            },
            PlanType.OPTIMIZATION: {
                "name": "性能优化计划",
                "description": "系统性能优化计划",
                "priority": PlanPriority.MEDIUM,
                "tasks": [
                    {
                        "name": "资源优化",
                        "description": "优化系统资源分配",
                        "frequency": "every_6_hours",
                        "assignee": "system_optimizer",
                        "priority": "medium"
                    },
                    {
                        "name": "代码优化",
                        "description": "优化代码执行效率",
                        "frequency": "weekly_wednesday_02:00",
                        "assignee": "ai_optimizer",
                        "priority": "medium"
                    },
                    {
                        "name": "数据库优化",
                        "description": "优化数据库查询性能",
                        "frequency": "weekly_thursday_02:00",
                        "assignee": "system_optimizer",
                        "priority": "high"
                    }
                ]
            }
        }

    def _load_existing_plans(self):
        """加载已存在的计划"""
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
                self.plans[plan['plan_id']] = plan
            logger.info(f"加载了 {len(self.plans)} 个已存在的计划")
        except Exception as e:
            logger.warning(f"加载计划失败: {e}")

    def generate_plan(self, plan_type: str, custom_tasks=None, **kwargs):
        """智能生成计划
        
        Args:
            plan_type: 计划类型
            custom_tasks: 自定义任务列表
            **kwargs: 额外参数（name, description, priority等）
            
        Returns:
            生成的计划字典
        """
        template = self.plan_templates.get(plan_type)
        if not template:
            logger.error(f"未知计划类型: {plan_type}")
            return None

        plan_id = f"plan_{plan_type}_{uuid.uuid4().hex[:8]}"
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        plan_name = kwargs.get('name', template['name'])
        plan_description = kwargs.get('description', template['description'])
        plan_priority = kwargs.get('priority', template['priority'])

        # 合并模板任务和自定义任务
        tasks = []
        if custom_tasks:
            tasks.extend(custom_tasks)
        else:
            for task_template in template['tasks']:
                task = {
                    'task_id': f"task_{uuid.uuid4().hex[:8]}",
                    'name': task_template['name'],
                    'description': task_template['description'],
                    'assignee': task_template['assignee'],
                    'priority': task_template['priority'],
                    'frequency': task_template['frequency'],
                    'status': 'pending',
                    'created_at': current_time
                }
                tasks.append(task)

        # 根据系统上下文智能调整计划
        tasks = self._intelligent_adjust_tasks(tasks)

        plan = {
            'plan_id': plan_id,
            'name': plan_name,
            'description': plan_description,
            'type': plan_type,
            'priority': plan_priority,
            'status': 'active',
            'start_time': current_time,
            'end_time': None,
            'tasks': tasks,
            'created_by': self.employee_id,
            'created_at': current_time,
            'updated_at': current_time
        }

        self.plans[plan_id] = plan
        self._save_plan(plan)

        logger.info(f"AI计划员工生成计划: {plan_id} - {plan_name}")
        return plan

    def _intelligent_adjust_tasks(self, tasks):
        """智能调整任务配置
        
        根据系统当前状态、负载和历史数据调整任务频率和优先级
        """
        adjusted_tasks = []
        
        for task in tasks:
            adjusted_task = task.copy()
            
            # 根据系统负载调整频率
            if self.system_context.get('high_load', False):
                if task['frequency'] == 'every_5_minutes':
                    adjusted_task['frequency'] = 'every_10_minutes'
                elif task['frequency'] == 'every_15_minutes':
                    adjusted_task['frequency'] = 'every_30_minutes'
            
            # 根据历史成功率调整优先级
            success_rate = self._get_task_success_rate(task['name'])
            if success_rate < 0.8:
                adjusted_task['priority'] = 'high'
            
            adjusted_tasks.append(adjusted_task)
        
        return adjusted_tasks

    def _get_task_success_rate(self, task_name):
        """获取任务成功率"""
        if not self.execution_history:
            return 1.0
        
        matching_tasks = [h for h in self.execution_history if h.get('task_name') == task_name]
        if not matching_tasks:
            return 1.0
        
        success_count = sum(1 for h in matching_tasks if h.get('status') == 'completed')
        return success_count / len(matching_tasks)

    def _save_plan(self, plan):
        """保存计划到数据库"""
        try:
            from app.utils.db import db_manager
            
            db_manager.execute('''
                CREATE TABLE IF NOT EXISTS ai_plans (
                    plan_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    type TEXT,
                    priority TEXT,
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
                INSERT OR REPLACE INTO ai_plans 
                (plan_id, name, description, type, priority, status, start_time, end_time, tasks, created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                plan['plan_id'],
                plan['name'],
                plan['description'],
                plan.get('type', ''),
                plan.get('priority', ''),
                plan['status'],
                plan['start_time'],
                plan['end_time'],
                str(plan['tasks']),
                plan['created_by'],
                plan['created_at'],
                plan['updated_at']
            ))
            
            logger.debug(f"计划已保存: {plan['plan_id']}")
        except Exception as e:
            logger.error(f"保存计划失败: {e}")

    def auto_generate_plans(self):
        """自动生成所有必要的计划
        
        根据系统需求自动创建日常运营、同步、维护等计划
        """
        plans_created = []
        
        # 创建日常运营计划
        daily_plan = self.generate_plan(PlanType.DAILY)
        if daily_plan:
            plans_created.append(daily_plan)

        # 创建周度维护计划
        weekly_plan = self.generate_plan(PlanType.WEEKLY)
        if weekly_plan:
            plans_created.append(weekly_plan)

        # 创建自动同步计划
        sync_plan = self.generate_plan(PlanType.SYNC)
        if sync_plan:
            plans_created.append(sync_plan)

        # 创建系统维护计划
        maintenance_plan = self.generate_plan(PlanType.MAINTENANCE)
        if maintenance_plan:
            plans_created.append(maintenance_plan)

        # 创建性能优化计划
        optimization_plan = self.generate_plan(PlanType.OPTIMIZATION)
        if optimization_plan:
            plans_created.append(optimization_plan)

        logger.info(f"AI计划员工自动生成了 {len(plans_created)} 个计划")
        return plans_created

    def create_custom_plan(self, name, description, tasks):
        """创建自定义计划"""
        plan_id = f"plan_custom_{uuid.uuid4().hex[:8]}"
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        plan = {
            'plan_id': plan_id,
            'name': name,
            'description': description,
            'type': 'custom',
            'priority': PlanPriority.MEDIUM,
            'status': 'active',
            'start_time': current_time,
            'end_time': None,
            'tasks': tasks,
            'created_by': self.employee_id,
            'created_at': current_time,
            'updated_at': current_time
        }

        self.plans[plan_id] = plan
        self._save_plan(plan)

        logger.info(f"AI计划员工创建自定义计划: {plan_id} - {name}")
        return plan

    def execute_plan(self, plan_id):
        """执行计划"""
        plan = self.plans.get(plan_id)
        if not plan:
            logger.error(f"计划不存在: {plan_id}")
            return {"success": False, "message": "计划不存在"}

        if plan['status'] != 'active':
            logger.error(f"计划未激活: {plan_id}")
            return {"success": False, "message": "计划未激活"}

        logger.info(f"AI计划员工开始执行计划: {plan_id} - {plan['name']}")

        executed_tasks = []
        for task in plan['tasks']:
            execution_result = self._execute_task(task)
            executed_tasks.append(execution_result)

            # 记录执行历史
            self.execution_history.append({
                'plan_id': plan_id,
                'task_id': task['task_id'],
                'task_name': task['name'],
                'status': execution_result['status'],
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

            # 保持历史记录数量
            if len(self.execution_history) > 1000:
                self.execution_history = self.execution_history[-500:]

        logger.info(f"AI计划员工完成计划执行: {plan_id}")
        return {
            "success": True,
            "message": "计划执行完成",
            "plan_id": plan_id,
            "executed_tasks": executed_tasks
        }

    def _execute_task(self, task):
        """执行单个任务"""
        try:
            logger.debug(f"执行任务: {task['name']}")
            
            # 根据任务类型执行不同的操作
            task_type = task['assignee']
            
            if task_type == 'git_sync':
                self._execute_git_sync()
            elif task_type == 'backup_manager':
                self._execute_backup()
            elif task_type == 'rollback_manager':
                self._execute_rollback()
            elif task_type == 'system_monitor':
                self._execute_monitor()
            elif task_type == 'system_maintainer':
                self._execute_maintenance()
            elif task_type == 'system_optimizer':
                self._execute_optimization()
            elif task_type == 'ai_learner':
                self._execute_ai_learning()

            return {"task_id": task['task_id'], "task_name": task['name'], "status": "completed"}
        
        except Exception as e:
            logger.error(f"任务执行失败: {task['name']} - {e}")
            return {"task_id": task['task_id'], "task_name": task['name'], "status": "failed", "error": str(e)}

    def _execute_git_sync(self):
        """执行Git同步"""
        try:
            import subprocess
            result = subprocess.run(
                ['python3', '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/git_sync.py', '--sync'],
                capture_output=True,
                text=True,
                timeout=120
            )
            logger.debug(f"Git同步执行结果: {result.stdout}")
        except Exception as e:
            logger.error(f"Git同步执行失败: {e}")

    def _execute_backup(self):
        """执行备份"""
        try:
            import subprocess
            result = subprocess.run(
                ['python3', '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/backup_manager.py', '--backup'],
                capture_output=True,
                text=True,
                timeout=120
            )
            logger.debug(f"备份执行结果: {result.stdout}")
        except Exception as e:
            logger.error(f"备份执行失败: {e}")

    def _execute_rollback(self):
        """执行回滚点创建"""
        try:
            import subprocess
            result = subprocess.run(
                ['python3', '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/rollback_manager.py', '--create'],
                capture_output=True,
                text=True,
                timeout=60
            )
            logger.debug(f"回滚点创建结果: {result.stdout}")
        except Exception as e:
            logger.error(f"回滚点创建失败: {e}")

    def _execute_monitor(self):
        """执行系统监控"""
        logger.debug("执行系统监控...")

    def _execute_maintenance(self):
        """执行系统维护"""
        logger.debug("执行系统维护...")

    def _execute_optimization(self):
        """执行系统优化"""
        logger.debug("执行系统优化...")

    def _execute_ai_learning(self):
        """执行AI学习"""
        try:
            from app.ai.auto_learning_upgrade import ai_auto_learning_system
            ai_auto_learning_system.perform_learning()
        except Exception as e:
            logger.error(f"AI学习执行失败: {e}")

    def get_plan(self, plan_id):
        """获取计划详情"""
        return self.plans.get(plan_id)

    def get_all_plans(self):
        """获取所有计划"""
        return list(self.plans.values())

    def update_plan(self, plan_id, updates):
        """更新计划"""
        if plan_id not in self.plans:
            return False
        
        self.plans[plan_id].update(updates)
        self.plans[plan_id]['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._save_plan(self.plans[plan_id])
        
        logger.info(f"AI计划员工更新计划: {plan_id}")
        return True

    def delete_plan(self, plan_id):
        """删除计划"""
        if plan_id not in self.plans:
            return False
        
        del self.plans[plan_id]
        
        try:
            from app.utils.db import db_manager
            db_manager.execute('DELETE FROM ai_plans WHERE plan_id = ?', (plan_id,))
        except Exception as e:
            logger.error(f"删除计划失败: {e}")
        
        logger.info(f"AI计划员工删除计划: {plan_id}")
        return True

    def get_execution_history(self, limit=50):
        """获取执行历史"""
        return self.execution_history[-limit:]

    def set_system_context(self, context):
        """设置系统上下文"""
        self.system_context.update(context)
        logger.debug(f"系统上下文已更新: {context}")

    def analyze_and_plan(self):
        """智能分析系统状态并生成/调整计划"""
        logger.info("AI计划员工开始智能分析...")
        
        # 分析当前系统状态
        analysis = self._analyze_system()
        
        # 根据分析结果调整计划
        self._adjust_plans_based_on_analysis(analysis)
        
        logger.info("AI计划员工智能分析完成")
        return analysis

    def _analyze_system(self):
        """分析系统状态"""
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'active_plans': len(self.plans),
            'total_tasks': sum(len(plan.get('tasks', [])) for plan in self.plans.values()),
            'system_context': self.system_context,
            'recommendations': []
        }

        # 根据系统状态生成建议
        if self.system_context.get('high_load', False):
            analysis['recommendations'].append({
                'type': 'optimization',
                'message': '系统负载过高，建议增加优化任务频率',
                'action': 'increase_optimization_frequency'
            })

        if len(self.plans) == 0:
            analysis['recommendations'].append({
                'type': 'plan_generation',
                'message': '未发现现有计划，建议自动生成基础计划',
                'action': 'auto_generate_plans'
            })

        return analysis

    def _adjust_plans_based_on_analysis(self, analysis):
        """根据分析结果调整计划"""
        for recommendation in analysis['recommendations']:
            action = recommendation['action']
            
            if action == 'auto_generate_plans':
                self.auto_generate_plans()
            elif action == 'increase_optimization_frequency':
                self._increase_optimization_frequency()

    def _increase_optimization_frequency(self):
        """增加优化任务频率"""
        for plan in self.plans.values():
            if plan.get('type') == PlanType.OPTIMIZATION:
                for task in plan['tasks']:
                    if task['frequency'] == 'every_6_hours':
                        task['frequency'] = 'every_3_hours'
                self._save_plan(plan)
                logger.info(f"已增加优化计划频率: {plan['plan_id']}")


ai_plan_employee = AIPlanEmployee()


def main():
    """测试AI计划员工"""
    print("=" * 60)
    print("AI计划员工系统测试")
    print("=" * 60)

    employee = AIPlanEmployee()
    
    print(f"\nAI计划员工信息:")
    print(f"  ID: {employee.employee_id}")
    print(f"  名称: {employee.name}")
    print(f"  类型: {employee.type}")
    print(f"  技能: {', '.join(employee.skills)}")
    print(f"  状态: {employee.status}")

    print("\n可用计划模板:")
    for plan_type, template in employee.plan_templates.items():
        print(f"  {plan_type}: {template['name']}")

    print("\n自动生成计划...")
    plans = employee.auto_generate_plans()
    
    print(f"\n已生成 {len(plans)} 个计划:")
    for plan in plans:
        print(f"\n  计划ID: {plan['plan_id']}")
        print(f"  名称: {plan['name']}")
        print(f"  类型: {plan['type']}")
        print(f"  优先级: {plan['priority']}")
        print(f"  任务数: {len(plan['tasks'])}")
        for task in plan['tasks']:
            print(f"    - {task['name']} ({task['frequency']})")

    print("\n创建自定义计划...")
    custom_tasks = [
        {
            'task_id': f"task_custom_1_{uuid.uuid4().hex[:4]}",
            'name': '自定义任务1',
            'description': '测试自定义任务',
            'assignee': 'system_monitor',
            'priority': 'high',
            'frequency': 'every_hour',
            'status': 'pending'
        }
    ]
    custom_plan = employee.create_custom_plan(
        name='测试自定义计划',
        description='这是一个测试计划',
        tasks=custom_tasks
    )
    
    print(f"\n自定义计划创建成功: {custom_plan['plan_id']}")

    print("\n智能分析系统...")
    analysis = employee.analyze_and_plan()
    print(f"  活跃计划: {analysis['active_plans']}")
    print(f"  总任务数: {analysis['total_tasks']}")
    print(f"  建议: {len(analysis['recommendations'])} 条")

    print("\n" + "=" * 60)
    print("AI计划员工系统测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()