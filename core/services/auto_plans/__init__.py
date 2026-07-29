# -*- coding: utf-8 -*-
"""
MTSCOS AI 自动计划调度系统 (Auto Plans)
========================================

提供模块化、可扩展的自动化计划管理框架：
  - AbstractAutoPlan: 所有计划的抽象基类
  - CentralPlanScheduler: 统一调度管理器
  - 各业务计划: 继承基类的具体实现

使用方式:
    from core.services.auto_plans import get_plan_scheduler
    scheduler = get_plan_scheduler()
    scheduler.start_all()

    # 或单独运行某个计划
    from core.services.auto_plans import get_plan
    plan = get_plan('system_maintenance')
    result = plan.run_once()
"""

from .scheduler_base import (
    AbstractAutoPlan,
    CentralPlanScheduler,
    PlanStatus,
    PlanResult,
    get_plan_scheduler,
    get_plan,
    list_all_plans,
    create_all_plans_and_register,
)

from .plan_system_maintenance import SystemMaintenancePlan
from .plan_ai_feeding import AIFeedingPlan
from .plan_question_bank import QuestionBankPlan
from .plan_teaching_sync import TeachingSyncPlan
from .plan_ai_employee import AIEmployeeMaintenancePlan
from .plan_backend_inspection import BackendInspectionPlan
from .plan_db_security import DBSecurityPlan
from .plan_vikey_monitor import VikeyMonitorPlan
from .plan_ai_conversation import AIConversationPlan
from .plan_points_reset import PointsResetPlan
from .plan_points_mall import PointsMallPlan
from .plan_lunar_buddhist import LunarBuddhistPlan
from .plan_auto_extend import AutoExtendPlan, get_dynamic_generator

__all__ = [
    'AbstractAutoPlan',
    'CentralPlanScheduler',
    'PlanStatus',
    'PlanResult',
    'get_plan_scheduler',
    'get_plan',
    'list_all_plans',
    'create_all_plans_and_register',
    # 具体计划
    'SystemMaintenancePlan',
    'AIFeedingPlan',
    'QuestionBankPlan',
    'TeachingSyncPlan',
    'AIEmployeeMaintenancePlan',
    'BackendInspectionPlan',
    'DBSecurityPlan',
    'VikeyMonitorPlan',
    'AIConversationPlan',
    'PointsResetPlan',
    'PointsMallPlan',
    'LunarBuddhistPlan',
    'AutoExtendPlan',
    'get_dynamic_generator',
]
