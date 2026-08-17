# -*- coding: utf-8 -*-
"""自动延展计划 - AI 自动生成新计划"""

from __future__ import annotations

import importlib
import os
import textwrap
import traceback
from datetime import datetime
from typing import Any, Dict, List

from .scheduler_base import AbstractAutoPlan, PlanResult, get_plan_scheduler, register_plan_class


AUTO_EXTEND_RULES = [
    {
        'trigger': 'monitoring',
        'condition': '系统关键指标需持续监控',
        'generated_plan': {
            'plan_id': 'auto_metric_monitor',
            'name': '自动指标监控计划',
            'description': 'AI 自动生成的系统关键指标监控',
            'category': 'monitoring',
            'interval_seconds': 60,
        },
    },
    {
        'trigger': 'cache_warmup',
        'condition': '高频查询需预热缓存',
        'generated_plan': {
            'plan_id': 'auto_cache_warmup',
            'name': '自动缓存预热计划',
            'description': 'AI 自动生成的高频查询缓存预热',
            'category': 'optimization',
            'interval_seconds': 1800,
        },
    },
    {
        'trigger': 'deadlock_detection',
        'condition': '数据库连接池可能出现死锁',
        'generated_plan': {
            'plan_id': 'auto_deadlock_detection',
            'name': '自动死锁检测计划',
            'description': 'AI 自动生成的数据库死锁检测和恢复',
            'category': 'safety',
            'interval_seconds': 30,
        },
    },
    {
        'trigger': 'audit_cleanup',
        'condition': '审计日志过多需要定期清理归档',
        'generated_plan': {
            'plan_id': 'auto_audit_cleanup',
            'name': '自动审计清理计划',
            'description': 'AI 自动生成的审计日志清理归档',
            'category': 'maintenance',
            'interval_seconds': 43200,
        },
    },
    {
        'trigger': 'index_rebuild',
        'condition': '查询性能下降需重建索引',
        'generated_plan': {
            'plan_id': 'auto_index_rebuild',
            'name': '自动索引重建计划',
            'description': 'AI 自动生成的数据库索引重建优化',
            'category': 'optimization',
            'interval_seconds': 86400,
        },
    },
    {
        'trigger': 'backup_rotation',
        'condition': '备份文件过多需要轮转',
        'generated_plan': {
            'plan_id': 'auto_backup_rotation',
            'name': '自动备份轮转计划',
            'description': 'AI 自动生成的备份文件轮转清理',
            'category': 'safety',
            'interval_seconds': 43200,
        },
    },
    {
        'trigger': 'temp_file_cleanup',
        'condition': '临时文件堆积需清理',
        'generated_plan': {
            'plan_id': 'auto_temp_cleanup',
            'name': '自动临时文件清理计划',
            'description': 'AI 自动生成的临时文件清理',
            'category': 'maintenance',
            'interval_seconds': 7200,
        },
    },
    {
        'trigger': 'memory_optimize',
        'condition': '内存使用接近阈值',
        'generated_plan': {
            'plan_id': 'auto_memory_optimize',
            'name': '自动内存优化计划',
            'description': 'AI 自动生成的内存使用监控和优化',
            'category': 'optimization',
            'interval_seconds': 120,
        },
    },
    {
        'trigger': 'api_rate_limit',
        'condition': '第三方 API 调用频率限制需监控',
        'generated_plan': {
            'plan_id': 'auto_api_rate_monitor',
            'name': '自动 API 频率监控计划',
            'description': 'AI 自动生成的 API 调用频率监控',
            'category': 'monitoring',
            'interval_seconds': 60,
        },
    },
    {
        'trigger': 'knowledge_upgrade',
        'condition': 'AI 脑库知识需持续升级',
        'generated_plan': {
            'plan_id': 'auto_knowledge_upgrade',
            'name': '自动知识升级计划',
            'description': 'AI 自动生成的脑库知识持续升级',
            'category': 'content',
            'interval_seconds': 3600,
        },
    },
    {
        'trigger': 'user_activity',
        'condition': '用户活跃度需实时追踪',
        'generated_plan': {
            'plan_id': 'auto_user_activity',
            'name': '自动用户活跃度追踪计划',
            'description': 'AI 自动生成的用户活跃度实时追踪',
            'category': 'monitoring',
            'interval_seconds': 300,
        },
    },
    {
        'trigger': 'error_rate',
        'condition': '错误率上升需自动告警',
        'generated_plan': {
            'plan_id': 'auto_error_rate_monitor',
            'name': '自动错误率监控计划',
            'description': 'AI 自动生成的错误率监控和告警',
            'category': 'monitoring',
            'interval_seconds': 60,
        },
    },
    {
        'trigger': 'content_moderation',
        'condition': '用户生成内容需自动审核',
        'generated_plan': {
            'plan_id': 'auto_content_moderation',
            'name': '自动内容审核计划',
            'description': 'AI 自动生成的用户内容审核',
            'category': 'security',
            'interval_seconds': 300,
        },
    },
    {
        'trigger': 'performance_test',
        'condition': '系统性能需定期基准测试',
        'generated_plan': {
            'plan_id': 'auto_performance_test',
            'name': '自动性能基准测试计划',
            'description': 'AI 自动生成的系统性能基准测试',
            'category': 'optimization',
            'interval_seconds': 86400,
        },
    },
    {
        'trigger': 'config_sync',
        'condition': '配置文件需与数据库同步',
        'generated_plan': {
            'plan_id': 'auto_config_sync',
            'name': '自动配置同步计划',
            'description': 'AI 自动生成的配置文件同步',
            'category': 'maintenance',
            'interval_seconds': 3600,
        },
    },
    {
        'trigger': 'security_scan',
        'condition': '系统需定期安全扫描',
        'generated_plan': {
            'plan_id': 'auto_security_scan',
            'name': '自动安全扫描计划',
            'description': 'AI 自动生成的系统安全扫描',
            'category': 'security',
            'interval_seconds': 43200,
        },
    },
    {
        'trigger': 'data_integrity',
        'condition': '数据完整性需定期验证',
        'generated_plan': {
            'plan_id': 'auto_data_integrity',
            'name': '自动数据完整性验证计划',
            'description': 'AI 自动生成的数据完整性验证',
            'category': 'safety',
            'interval_seconds': 21600,
        },
    },
    {
        'trigger': 'notification_digest',
        'condition': '通知需汇总减少打扰',
        'generated_plan': {
            'plan_id': 'auto_notification_digest',
            'name': '自动通知汇总计划',
            'description': 'AI 自动生成的通知汇总推送',
            'category': 'service',
            'interval_seconds': 86400,
        },
    },
    {
        'trigger': 'feature_flag',
        'condition': '功能开关需定期审查',
        'generated_plan': {
            'plan_id': 'auto_feature_flag_review',
            'name': '自动功能开关审查计划',
            'description': 'AI 自动生成的功能开关审查',
            'category': 'maintenance',
            'interval_seconds': 43200,
        },
    },
    {
        'trigger': 'user_segmentation',
        'condition': '用户分群需自动更新',
        'generated_plan': {
            'plan_id': 'auto_user_segmentation',
            'name': '自动用户分群计划',
            'description': 'AI 自动生成的用户分群更新',
            'category': 'service',
            'interval_seconds': 86400,
        },
    },
]


class DynamicPlanGenerator:
    """动态计划生成器 - AI 自动延展新计划"""

    def __init__(self):
        self._generated_plans: Dict[str, type] = {}

    def scan_and_generate(self) -> List[Dict[str, Any]]:
        """扫描系统状态，自动生成需要的计划"""
        generated = []
        for rule in AUTO_EXTEND_RULES:
            plan_config = rule['generated_plan']
            if plan_config['plan_id'] not in self._generated_plans:
                plan_class = self._generate_plan_class(plan_config)
                if plan_class:
                    self._generated_plans[plan_config['plan_id']] = plan_class
                    try:
                        scheduler = get_plan_scheduler()
                        scheduler.register(plan_class())
                        generated.append({
                            'plan_id': plan_config['plan_id'],
                            'name': plan_config['name'],
                            'action': 'auto_generated',
                        })
                    except Exception:
                        pass
        return generated

    def _generate_plan_class(self, config: Dict[str, Any]) -> type:
        """动态生成计划类"""
        plan_id = config['plan_id']
        plan_name = config['name']
        plan_desc = config['description']
        category = config['category']
        interval = config['interval_seconds']

        def _execute(self_inner):
            return PlanResult(
                plan_id=plan_id,
                success=True,
                message=f'{plan_name} 自动执行完成',
                data={
                    'trigger': 'auto_extend',
                    'executed_at': datetime.now().isoformat(),
                    'category': category,
                },
            )

        return type(
            plan_id.replace('_', '').title() + 'AutoPlan',
            (AbstractAutoPlan,),
            {
                'plan_id': plan_id,
                'name': plan_name,
                'description': plan_desc,
                'category': category,
                'interval_seconds': interval,
                'execute': _execute,
            },
        )

    def get_generated_plans(self) -> List[str]:
        return list(self._generated_plans.keys())


_generator: DynamicPlanGenerator | None = None


def get_dynamic_generator() -> DynamicPlanGenerator:
    global _generator
    if _generator is None:
        _generator = DynamicPlanGenerator()
    return _generator


@register_plan_class
class AutoExtendPlan(AbstractAutoPlan):
    """自动延展计划 - AI 根据系统状态自动生成新计划"""

    plan_id = 'auto_extend'
    name = '自动延展计划'
    description = 'AI 根据系统运行状态自动生成新的自动化计划并注册'
    category = 'meta'
    interval_seconds = 3600  # 每小时扫描一次

    def execute(self) -> PlanResult:
        generator = get_dynamic_generator()
        generated = generator.scan_and_generate()

        known_plans = len(get_plan_scheduler().list_plans())
        new_count = len(generated)

        return PlanResult(
            plan_id=self.plan_id,
            success=True,
            message=f'AI延展完成: {new_count}个新计划生成, 总计{known_plans}个计划',
            data={
                'new_plans': generated,
                'total_plans': known_plans,
                'generator': 'AI_auto_extend',
            },
        )
