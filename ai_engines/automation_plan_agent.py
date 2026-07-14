#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutomationPlanAgent - 自动化计划拓展AI员工
负责自动补全、完善、拓展自动化计划及功能
分析现有计划完整性，识别缺失功能，创建新计划，优化执行效率
"""

import os
import sys
import json
import logging
import sqlite3
import threading
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation_plan_agent.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('automation_plan_agent')


class PlanType(Enum):
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    QUARTERLY = 'quarterly'
    YEARLY = 'yearly'
    ON_DEMAND = 'on_demand'
    EVENT_TRIGGERED = 'event_triggered'


class PlanPriority(Enum):
    CRITICAL = 'critical'
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'


class PlanStatus(Enum):
    DRAFT = 'draft'
    ACTIVE = 'active'
    PAUSED = 'paused'
    COMPLETED = 'completed'
    ARCHIVED = 'archived'


class AutomationPlan:
    def __init__(self, plan_id: str, name: str, plan_type: PlanType, 
                 priority: PlanPriority, schedule: str, tasks: List[Dict],
                 description: str = "", enabled: bool = True):
        self.plan_id = plan_id
        self.name = name
        self.plan_type = plan_type
        self.priority = priority
        self.schedule = schedule
        self.tasks = tasks
        self.description = description
        self.enabled = enabled
        self.status = PlanStatus.ACTIVE if enabled else PlanStatus.PAUSED
        self.created_at = datetime.now().isoformat()
        self.last_run = None
        self.next_run = None
        self.run_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.coverage_score = 0.0
        self.efficiency_score = 0.0


class PlanAnalyzer:
    """计划分析器 - 分析现有计划的完整性和覆盖范围"""
    
    SYSTEM_FUNCTION_AREAS = {
        'security': {
            'name': '安全管理',
            'description': '系统安全相关功能',
            'required_tasks': ['security_scan', 'access_audit', 'vulnerability_check', 'security_patch_management']
        },
        'performance': {
            'name': '性能优化',
            'description': '系统性能相关功能',
            'required_tasks': ['performance_monitoring', 'resource_optimization', 'cache_tuning', 'load_balancing']
        },
        'database': {
            'name': '数据库管理',
            'description': '数据库相关功能',
            'required_tasks': ['database_backup', 'database_optimization', 'data_cleanup', 'schema_validation']
        },
        'backup': {
            'name': '备份管理',
            'description': '数据备份相关功能',
            'required_tasks': ['full_backup', 'incremental_backup', 'backup_verification', 'backup_rotation']
        },
        'monitoring': {
            'name': '系统监控',
            'description': '系统监控相关功能',
            'required_tasks': ['system_health_check', 'log_analysis', 'alert_management', 'anomaly_detection']
        },
        'maintenance': {
            'name': '系统维护',
            'description': '系统维护相关功能',
            'required_tasks': ['routine_maintenance', 'cleanup', 'update_management', 'system_patch']
        },
        'testing': {
            'name': '自动化测试',
            'description': '测试相关功能',
            'required_tasks': ['unit_testing', 'integration_testing', 'regression_testing', 'performance_testing']
        },
        'deployment': {
            'name': '部署管理',
            'description': '部署相关功能',
            'required_tasks': ['deployment_validation', 'rollback_preparation', 'staging_deployment', 'production_deployment']
        },
        'reporting': {
            'name': '报表生成',
            'description': '报表相关功能',
            'required_tasks': ['daily_report', 'weekly_summary', 'monthly_report', 'performance_report']
        },
        'user_management': {
            'name': '用户管理',
            'description': '用户相关功能',
            'required_tasks': ['user_cleanup', 'access_review', 'activity_audit', 'privilege_management']
        },
        'version_control': {
            'name': '版本控制',
            'description': '版本管理相关功能',
            'required_tasks': ['version_check', 'update_trigger', 'rollback', 'change_log']
        },
        'disaster_recovery': {
            'name': '灾难恢复',
            'description': '灾难恢复相关功能',
            'required_tasks': ['recovery_test', 'failover_test', 'data_restoration', 'system_recovery']
        }
    }
    
    def __init__(self):
        self.analyzed_plans = {}
        self.function_coverage = defaultdict(dict)
    
    def analyze_plan(self, plan: AutomationPlan) -> Dict[str, Any]:
        """分析单个计划"""
        task_names = [t['name'] for t in plan.tasks]
        
        coverage = {
            'plan_id': plan.plan_id,
            'plan_name': plan.name,
            'plan_type': plan.plan_type.value,
            'priority': plan.priority.value,
            'total_tasks': len(plan.tasks),
            'task_names': task_names,
            'function_areas_covered': [],
            'function_areas_partial': [],
            'function_areas_missing': [],
            'coverage_score': 0.0,
            'efficiency_score': 0.0,
            'recommendations': []
        }
        
        for area_id, area_info in self.SYSTEM_FUNCTION_AREAS.items():
            required_tasks = area_info['required_tasks']
            matched_tasks = [t for t in required_tasks if t in task_names]
            coverage_ratio = len(matched_tasks) / len(required_tasks)
            
            self.function_coverage[area_id][plan.plan_id] = coverage_ratio
            
            if coverage_ratio == 1.0:
                coverage['function_areas_covered'].append(area_id)
            elif coverage_ratio > 0:
                coverage['function_areas_partial'].append(area_id)
                missing = [t for t in required_tasks if t not in task_names]
                coverage['recommendations'].append(
                    f"在计划 '{plan.name}' 中添加缺失的{area_info['name']}任务: {', '.join(missing)}"
                )
            else:
                coverage['function_areas_missing'].append(area_id)
        
        coverage['coverage_score'] = self._calculate_coverage_score(coverage)
        coverage['efficiency_score'] = self._calculate_efficiency_score(plan)
        
        self.analyzed_plans[plan.plan_id] = coverage
        
        return coverage
    
    def analyze_all_plans(self, plans: Dict[str, AutomationPlan]) -> Dict[str, Any]:
        """分析所有计划"""
        results = {
            'total_plans': len(plans),
            'plans_analyzed': [],
            'overall_coverage': {},
            'missing_function_areas': [],
            'partial_function_areas': [],
            'fully_covered_areas': [],
            'recommendations': [],
            'optimization_opportunities': []
        }
        
        for plan_id, plan in plans.items():
            analysis = self.analyze_plan(plan)
            results['plans_analyzed'].append(analysis)
            results['recommendations'].extend(analysis['recommendations'])
        
        for area_id, area_info in self.SYSTEM_FUNCTION_AREAS.items():
            plan_coverages = [v for v in self.function_coverage.get(area_id, {}).values()]
            avg_coverage = sum(plan_coverages) / len(plan_coverages) if plan_coverages else 0.0
            
            results['overall_coverage'][area_id] = {
                'name': area_info['name'],
                'coverage_ratio': avg_coverage,
                'plans_covering': len(plan_coverages)
            }
            
            if avg_coverage == 0:
                results['missing_function_areas'].append(area_id)
            elif avg_coverage < 1.0:
                results['partial_function_areas'].append(area_id)
            else:
                results['fully_covered_areas'].append(area_id)
        
        results['optimization_opportunities'] = self._identify_optimization_opportunities(plans)
        
        return results
    
    def _calculate_coverage_score(self, coverage: Dict) -> float:
        total_areas = len(self.SYSTEM_FUNCTION_AREAS)
        covered = len(coverage['function_areas_covered'])
        partial = len(coverage['function_areas_partial'])
        
        return (covered + partial * 0.5) / total_areas
    
    def _calculate_efficiency_score(self, plan: AutomationPlan) -> float:
        if plan.run_count == 0:
            return 1.0
        return plan.success_count / plan.run_count
    
    def _identify_optimization_opportunities(self, plans: Dict[str, AutomationPlan]) -> List[str]:
        opportunities = []
        
        plan_types = defaultdict(list)
        for plan in plans.values():
            plan_types[plan.plan_type.value].append(plan)
        
        if len(plan_types.get('daily', [])) > 10:
            opportunities.append("每日计划数量过多，建议合并或优化调度")
        
        for plan_type, plan_list in plan_types.items():
            if len(plan_list) == 0:
                opportunities.append(f"缺少{plan_type}类型的计划")
        
        for plan in plans.values():
            if plan.efficiency_score < 0.5:
                opportunities.append(f"计划 '{plan.name}' 成功率低于50%，需要优化")
            
            if len(plan.tasks) > 20:
                opportunities.append(f"计划 '{plan.name}' 任务过多，建议拆分")
        
        return opportunities


class FeatureExpander:
    """功能拓展器 - 识别缺失功能并创建新计划"""
    
    def __init__(self, analyzer: PlanAnalyzer):
        self.analyzer = analyzer
        self.created_plans = []
    
    def identify_missing_features(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """识别缺失的功能区域"""
        missing_features = []
        
        for area_id in analysis_results['missing_function_areas']:
            area_info = self.analyzer.SYSTEM_FUNCTION_AREAS[area_id]
            missing_features.append({
                'area_id': area_id,
                'area_name': area_info['name'],
                'description': area_info['description'],
                'required_tasks': area_info['required_tasks'],
                'priority': self._determine_priority(area_id)
            })
        
        for area_id in analysis_results['partial_function_areas']:
            area_info = self.analyzer.SYSTEM_FUNCTION_AREAS[area_id]
            avg_coverage = analysis_results['overall_coverage'][area_id]['coverage_ratio']
            if avg_coverage < 0.3:
                missing_features.append({
                    'area_id': area_id,
                    'area_name': area_info['name'],
                    'description': area_info['description'],
                    'required_tasks': area_info['required_tasks'],
                    'priority': self._determine_priority(area_id),
                    'note': f"当前覆盖率仅 {avg_coverage:.0%}"
                })
        
        return sorted(missing_features, key=lambda x: x['priority'].value)
    
    def _determine_priority(self, area_id: str) -> PlanPriority:
        critical_areas = ['security', 'backup', 'disaster_recovery', 'database']
        high_areas = ['monitoring', 'maintenance', 'version_control']
        
        if area_id in critical_areas:
            return PlanPriority.CRITICAL
        elif area_id in high_areas:
            return PlanPriority.HIGH
        return PlanPriority.MEDIUM
    
    def create_plan_for_feature(self, feature: Dict[str, Any]) -> AutomationPlan:
        """为缺失功能创建新计划"""
        plan_id = f"plan_{feature['area_id']}_{uuid.uuid4().hex[:8]}"
        plan_name = f"{feature['area_name']}自动化计划"
        
        schedule_map = {
            PlanPriority.CRITICAL: '02:00',
            PlanPriority.HIGH: '03:00',
            PlanPriority.MEDIUM: '04:00',
            PlanPriority.LOW: '05:00'
        }
        
        plan_type = self._determine_plan_type(feature['area_id'])
        schedule = self._determine_schedule(plan_type, schedule_map[feature['priority']])
        
        tasks = []
        for task_name in feature['required_tasks']:
            tasks.append({
                'task_id': f"task_{uuid.uuid4().hex[:8]}",
                'name': task_name,
                'description': self._get_task_description(task_name),
                'priority': feature['priority'].value,
                'timeout': 300,
                'retry_count': 3
            })
        
        plan = AutomationPlan(
            plan_id=plan_id,
            name=plan_name,
            plan_type=plan_type,
            priority=feature['priority'],
            schedule=schedule,
            tasks=tasks,
            description=f"自动创建的{feature['area_name']}自动化计划，包含{len(tasks)}个任务"
        )
        
        self.created_plans.append(plan)
        logger.info(f"为功能 '{feature['area_name']}' 创建新计划: {plan_id}")
        
        return plan
    
    def _determine_plan_type(self, area_id: str) -> PlanType:
        daily_areas = ['security', 'monitoring', 'backup']
        weekly_areas = ['performance', 'maintenance', 'testing']
        monthly_areas = ['database', 'deployment', 'reporting', 'user_management']
        quarterly_areas = ['disaster_recovery']
        
        if area_id in daily_areas:
            return PlanType.DAILY
        elif area_id in weekly_areas:
            return PlanType.WEEKLY
        elif area_id in monthly_areas:
            return PlanType.MONTHLY
        elif area_id in quarterly_areas:
            return PlanType.QUARTERLY
        return PlanType.DAILY
    
    def _determine_schedule(self, plan_type: PlanType, base_time: str) -> str:
        if plan_type == PlanType.DAILY:
            return base_time
        elif plan_type == PlanType.WEEKLY:
            return f"Sunday {base_time}"
        elif plan_type == PlanType.MONTHLY:
            return f"1st {base_time}"
        elif plan_type == PlanType.QUARTERLY:
            return f"quarterly {base_time}"
        return base_time
    
    def _get_task_description(self, task_name: str) -> str:
        descriptions = {
            'security_scan': '执行系统安全扫描',
            'access_audit': '审计用户访问权限',
            'vulnerability_check': '检查系统漏洞',
            'security_patch_management': '管理安全补丁',
            'performance_monitoring': '监控系统性能',
            'resource_optimization': '优化系统资源',
            'cache_tuning': '调优缓存策略',
            'load_balancing': '负载均衡管理',
            'database_backup': '备份数据库',
            'database_optimization': '优化数据库',
            'data_cleanup': '清理过期数据',
            'schema_validation': '验证数据库schema',
            'full_backup': '创建完整备份',
            'incremental_backup': '创建增量备份',
            'backup_verification': '验证备份完整性',
            'backup_rotation': '执行备份轮换',
            'system_health_check': '检查系统健康状态',
            'log_analysis': '分析系统日志',
            'alert_management': '管理系统告警',
            'anomaly_detection': '检测异常行为',
            'routine_maintenance': '执行例行维护',
            'cleanup': '清理系统垃圾',
            'update_management': '管理系统更新',
            'system_patch': '应用系统补丁',
            'unit_testing': '运行单元测试',
            'integration_testing': '运行集成测试',
            'regression_testing': '运行回归测试',
            'performance_testing': '运行性能测试',
            'deployment_validation': '验证部署',
            'rollback_preparation': '准备回滚方案',
            'staging_deployment': '部署到预发布环境',
            'production_deployment': '部署到生产环境',
            'daily_report': '生成日报',
            'weekly_summary': '生成周报',
            'monthly_report': '生成月报',
            'performance_report': '生成性能报告',
            'user_cleanup': '清理无效用户',
            'access_review': '审查用户权限',
            'activity_audit': '审计用户活动',
            'privilege_management': '管理用户特权',
            'version_check': '检查版本更新',
            'update_trigger': '触发版本更新',
            'rollback': '执行版本回滚',
            'change_log': '更新变更日志',
            'recovery_test': '测试灾难恢复',
            'failover_test': '测试故障转移',
            'data_restoration': '测试数据恢复',
            'system_recovery': '测试系统恢复'
        }
        return descriptions.get(task_name, f"执行任务: {task_name}")
    
    def expand_all_missing_features(self, analysis_results: Dict[str, Any]) -> List[AutomationPlan]:
        """拓展所有缺失功能"""
        missing_features = self.identify_missing_features(analysis_results)
        new_plans = []
        
        for feature in missing_features:
            plan = self.create_plan_for_feature(feature)
            new_plans.append(plan)
        
        logger.info(f"功能拓展完成: 为 {len(new_plans)} 个缺失功能创建了新计划")
        
        return new_plans


class PlanOptimizer:
    """计划优化器 - 优化现有计划的执行效率"""
    
    def __init__(self):
        self.optimizations = []
    
    def optimize_plan(self, plan: AutomationPlan) -> Dict[str, Any]:
        """优化单个计划"""
        optimizations = []
        
        if len(plan.tasks) > 15:
            optimizations.append(self._split_large_plan(plan))
        
        slow_tasks = self._identify_slow_tasks(plan)
        if slow_tasks:
            optimizations.append(self._optimize_slow_tasks(plan, slow_tasks))
        
        redundant_tasks = self._identify_redundant_tasks(plan)
        if redundant_tasks:
            optimizations.append(self._remove_redundant_tasks(plan, redundant_tasks))
        
        if plan.efficiency_score < 0.7:
            optimizations.append(self._improve_task_reliability(plan))
        
        schedule_optimization = self._optimize_schedule(plan)
        if schedule_optimization:
            optimizations.append(schedule_optimization)
        
        result = {
            'plan_id': plan.plan_id,
            'plan_name': plan.name,
            'optimizations_applied': len(optimizations),
            'optimizations': optimizations,
            'expected_improvement': len(optimizations) * 0.1
        }
        
        self.optimizations.append(result)
        
        return result
    
    def optimize_all_plans(self, plans: Dict[str, AutomationPlan]) -> Dict[str, Any]:
        """优化所有计划"""
        results = {
            'total_plans': len(plans),
            'plans_optimized': [],
            'total_optimizations': 0,
            'expected_overall_improvement': 0.0
        }
        
        for plan_id, plan in plans.items():
            optimization = self.optimize_plan(plan)
            results['plans_optimized'].append(optimization)
            results['total_optimizations'] += optimization['optimizations_applied']
            results['expected_overall_improvement'] += optimization['expected_improvement']
        
        results['expected_overall_improvement'] /= len(plans) if plans else 1
        
        return results
    
    def _split_large_plan(self, plan: AutomationPlan) -> Dict:
        split_count = (len(plan.tasks) + 9) // 10
        return {
            'type': 'split_plan',
            'description': f"计划任务过多({len(plan.tasks)}个)，建议拆分为{split_count}个计划",
            'before_task_count': len(plan.tasks),
            'after_task_count': len(plan.tasks) // split_count
        }
    
    def _identify_slow_tasks(self, plan: AutomationPlan) -> List[str]:
        return []
    
    def _optimize_slow_tasks(self, plan: AutomationPlan, slow_tasks: List[str]) -> Dict:
        return {
            'type': 'optimize_slow_tasks',
            'description': f"优化慢速任务: {', '.join(slow_tasks)}",
            'tasks': slow_tasks,
            'action': '增加超时时间或并行执行'
        }
    
    def _identify_redundant_tasks(self, plan: AutomationPlan) -> List[str]:
        task_names = [t['name'] for t in plan.tasks]
        seen = set()
        redundant = []
        for name in task_names:
            if name in seen:
                redundant.append(name)
            seen.add(name)
        return redundant
    
    def _remove_redundant_tasks(self, plan: AutomationPlan, redundant: List[str]) -> Dict:
        plan.tasks = [t for t in plan.tasks if t['name'] not in redundant]
        return {
            'type': 'remove_redundant',
            'description': f"移除重复任务: {', '.join(redundant)}",
            'removed_count': len(redundant),
            'remaining_tasks': len(plan.tasks)
        }
    
    def _improve_task_reliability(self, plan: AutomationPlan) -> Dict:
        for task in plan.tasks:
            task['retry_count'] = max(task.get('retry_count', 1), 3)
        return {
            'type': 'improve_reliability',
            'description': '提高任务重试次数以增强可靠性',
            'action': '将所有任务重试次数设置为3次'
        }
    
    def _optimize_schedule(self, plan: AutomationPlan) -> Optional[Dict]:
        resource_heavy_types = ['database', 'backup']
        for area_id in resource_heavy_types:
            if area_id in plan.name.lower():
                return {
                    'type': 'optimize_schedule',
                    'description': f"计划'{plan.name}'属于资源密集型，建议在低峰期执行",
                    'suggested_time': '02:00-04:00'
                }
        return None


class AutomationPlanAgent:
    """自动化计划拓展AI员工"""
    
    def __init__(self):
        self.employee_id = "automation_plan_agent_001"
        self.employee_name = "自动化计划拓展Agent"
        self.specialty = "自动补全、完善、拓展自动化计划及功能，分析计划完整性，识别缺失功能，创建新计划，优化执行效率"
        self.status = "active"
        self.created_at = datetime.now().isoformat()
        self.last_analysis = None
        
        self.plans: Dict[str, AutomationPlan] = {}
        self.plan_analyzer = PlanAnalyzer()
        self.feature_expander = FeatureExpander(self.plan_analyzer)
        self.plan_optimizer = PlanOptimizer()
        
        self._init_database()
        self._load_plans()
        self._start_scheduler()
        
        logger.info("AutomationPlanAgent 初始化完成")
    
    def _init_database(self):
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
        self.conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30.0)
        self.cursor = self.conn.cursor()
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS automation_plans (
                plan_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                plan_type TEXT NOT NULL,
                priority TEXT NOT NULL,
                schedule TEXT NOT NULL,
                tasks TEXT,
                description TEXT,
                enabled INTEGER DEFAULT 1,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_run TEXT,
                next_run TEXT,
                run_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                coverage_score REAL DEFAULT 0.0,
                efficiency_score REAL DEFAULT 0.0
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS plan_analysis_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_time TEXT NOT NULL,
                total_plans INTEGER,
                fully_covered INTEGER,
                partial_covered INTEGER,
                missing INTEGER,
                recommendations TEXT,
                optimization_opportunities TEXT
            )
        ''')
        
        self.conn.commit()
    
    def _load_plans(self):
        try:
            self.cursor.execute('SELECT * FROM automation_plans')
            rows = self.cursor.fetchall()
            
            for row in rows:
                plan = AutomationPlan(
                    plan_id=row[0],
                    name=row[1],
                    plan_type=PlanType(row[2]),
                    priority=PlanPriority(row[3]),
                    schedule=row[4],
                    tasks=json.loads(row[5]) if row[5] else [],
                    description=row[6],
                    enabled=bool(row[7])
                )
                plan.status = PlanStatus(row[8])
                plan.created_at = row[9]
                plan.last_run = row[10]
                plan.next_run = row[11]
                plan.run_count = row[12]
                plan.success_count = row[13]
                plan.failure_count = row[14]
                plan.coverage_score = row[15]
                plan.efficiency_score = row[16]
                
                self.plans[plan.plan_id] = plan
            
            logger.info(f"从数据库加载了 {len(self.plans)} 个自动化计划")
        except Exception as e:
            logger.error(f"加载计划失败: {e}")
            self._init_default_plans()
    
    def _init_default_plans(self):
        default_plans = [
            {
                'name': '每日安全巡检',
                'plan_type': PlanType.DAILY,
                'priority': PlanPriority.CRITICAL,
                'schedule': '02:00',
                'tasks': [
                    {'task_id': 'sec_scan', 'name': 'security_scan', 'description': '执行系统安全扫描', 'priority': 'critical', 'timeout': 300, 'retry_count': 2}
                ],
                'description': '每日安全巡检计划'
            },
            {
                'name': '每周性能优化',
                'plan_type': PlanType.WEEKLY,
                'priority': PlanPriority.HIGH,
                'schedule': 'Sunday 03:00',
                'tasks': [
                    {'task_id': 'perf_mon', 'name': 'performance_monitoring', 'description': '监控系统性能', 'priority': 'high', 'timeout': 600, 'retry_count': 2}
                ],
                'description': '每周性能优化计划'
            }
        ]
        
        for plan_data in default_plans:
            plan = AutomationPlan(
                plan_id=f"plan_{uuid.uuid4().hex[:8]}",
                **plan_data
            )
            self.plans[plan.plan_id] = plan
            self._save_plan(plan)
        
        logger.info(f"初始化了 {len(default_plans)} 个默认计划")
    
    def _save_plan(self, plan: AutomationPlan):
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO automation_plans 
                (plan_id, name, plan_type, priority, schedule, tasks, description,
                 enabled, status, created_at, last_run, next_run, run_count,
                 success_count, failure_count, coverage_score, efficiency_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                plan.plan_id, plan.name, plan.plan_type.value, plan.priority.value,
                plan.schedule, json.dumps(plan.tasks), plan.description,
                1 if plan.enabled else 0, plan.status.value, plan.created_at,
                plan.last_run, plan.next_run, plan.run_count,
                plan.success_count, plan.failure_count, plan.coverage_score,
                plan.efficiency_score
            ))
            self.conn.commit()
        except Exception as e:
            logger.error(f"保存计划失败: {e}")
    
    def _start_scheduler(self):
        self.scheduler_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        logger.info("AutomationPlanAgent调度器已启动")
    
    def _run_scheduler(self):
        while self.scheduler_running:
            try:
                self.auto_analyze_and_expand()
                time.sleep(3600)
            except Exception as e:
                logger.error(f"调度器执行错误: {e}")
    
    def analyze_plans(self) -> Dict[str, Any]:
        """分析现有计划"""
        results = self.plan_analyzer.analyze_all_plans(self.plans)
        self.last_analysis = datetime.now().isoformat()
        
        try:
            self.cursor.execute('''
                INSERT INTO plan_analysis_logs 
                (analysis_time, total_plans, fully_covered, partial_covered, 
                 missing, recommendations, optimization_opportunities)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.last_analysis,
                results['total_plans'],
                len(results['fully_covered_areas']),
                len(results['partial_function_areas']),
                len(results['missing_function_areas']),
                json.dumps(results['recommendations']),
                json.dumps(results['optimization_opportunities'])
            ))
            self.conn.commit()
        except Exception as e:
            logger.error(f"保存分析日志失败: {e}")
        
        return results
    
    def expand_features(self) -> Dict[str, Any]:
        """拓展缺失功能"""
        analysis = self.analyze_plans()
        new_plans = self.feature_expander.expand_all_missing_features(analysis)
        
        for plan in new_plans:
            self.plans[plan.plan_id] = plan
            self._save_plan(plan)
        
        return {
            'analysis_results': analysis,
            'new_plans_created': len(new_plans),
            'plan_details': [self._plan_to_dict(p) for p in new_plans]
        }
    
    def optimize_plans(self) -> Dict[str, Any]:
        """优化现有计划"""
        results = self.plan_optimizer.optimize_all_plans(self.plans)
        
        for plan in self.plans.values():
            self._save_plan(plan)
        
        return results
    
    def auto_analyze_and_expand(self) -> Dict[str, Any]:
        """自动分析并拓展计划"""
        logger.info("开始自动分析并拓展计划...")
        
        analysis = self.analyze_plans()
        new_plans = self.feature_expander.expand_all_missing_features(analysis)
        
        for plan in new_plans:
            self.plans[plan.plan_id] = plan
            self._save_plan(plan)
        
        optimization = self.optimize_plans()
        
        logger.info(f"自动分析拓展完成: 新增 {len(new_plans)} 个计划, 优化 {optimization['total_optimizations']} 项")
        
        return {
            'analysis': analysis,
            'new_plans_count': len(new_plans),
            'optimization': optimization
        }
    
    def create_custom_plan(self, name: str, plan_type: str, priority: str, 
                          schedule: str, tasks: List[Dict], description: str = "") -> AutomationPlan:
        """创建自定义计划"""
        plan = AutomationPlan(
            plan_id=f"plan_custom_{uuid.uuid4().hex[:8]}",
            name=name,
            plan_type=PlanType(plan_type),
            priority=PlanPriority(priority),
            schedule=schedule,
            tasks=tasks,
            description=description
        )
        
        self.plans[plan.plan_id] = plan
        self._save_plan(plan)
        
        logger.info(f"创建自定义计划: {plan.plan_id} - {name}")
        
        return plan
    
    def get_plan(self, plan_id: str) -> Optional[AutomationPlan]:
        """获取单个计划"""
        return self.plans.get(plan_id)
    
    def list_plans(self) -> List[Dict[str, Any]]:
        """列出所有计划"""
        return [self._plan_to_dict(plan) for plan in self.plans.values()]
    
    def _plan_to_dict(self, plan: AutomationPlan) -> Dict[str, Any]:
        return {
            'plan_id': plan.plan_id,
            'name': plan.name,
            'plan_type': plan.plan_type.value,
            'priority': plan.priority.value,
            'schedule': plan.schedule,
            'tasks': plan.tasks,
            'description': plan.description,
            'enabled': plan.enabled,
            'status': plan.status.value,
            'created_at': plan.created_at,
            'last_run': plan.last_run,
            'next_run': plan.next_run,
            'run_count': plan.run_count,
            'success_count': plan.success_count,
            'failure_count': plan.failure_count,
            'coverage_score': plan.coverage_score,
            'efficiency_score': plan.efficiency_score
        }
    
    def get_status(self) -> Dict[str, Any]:
        """获取Agent状态"""
        return {
            'employee_id': self.employee_id,
            'employee_name': self.employee_name,
            'specialty': self.specialty,
            'status': self.status,
            'created_at': self.created_at,
            'last_analysis': self.last_analysis,
            'total_plans': len(self.plans),
            'scheduler_running': self.scheduler_running,
            'analyzed_function_areas': len(self.plan_analyzer.SYSTEM_FUNCTION_AREAS)
        }
    
    def shutdown(self):
        """关闭Agent"""
        self.scheduler_running = False
        if self.conn:
            self.conn.close()
        logger.info("AutomationPlanAgent 已关闭")


# 延迟加载单例
_automation_plan_agent_instance = None

def get_automation_plan_agent():
    """获取AutomationPlanAgent单例（延迟加载）"""
    global _automation_plan_agent_instance
    if _automation_plan_agent_instance is None:
        _automation_plan_agent_instance = AutomationPlanAgent()
    return _automation_plan_agent_instance

# 兼容性别名
automation_plan_agent = None

def _ensure_automation_plan_agent():
    """确保单例已创建"""
    global automation_plan_agent
    if automation_plan_agent is None:
        automation_plan_agent = get_automation_plan_agent()
    return automation_plan_agent

if __name__ == '__main__':
    agent = AutomationPlanAgent()
    
    print("=== AutomationPlanAgent 状态 ===")
    print(json.dumps(agent.get_status(), indent=2, ensure_ascii=False))
    
    print("\n=== 当前计划列表 ===")
    plans = agent.list_plans()
    for plan in plans:
        print(f"  ID: {plan['plan_id']}")
        print(f"  名称: {plan['name']}")
        print(f"  类型: {plan['plan_type']}")
        print(f"  优先级: {plan['priority']}")
        print(f"  任务数: {len(plan['tasks'])}")
        print()
    
    print("=== 分析计划覆盖范围 ===")
    analysis = agent.analyze_plans()
    print(json.dumps({
        'total_plans': analysis['total_plans'],
        'fully_covered_areas': analysis['fully_covered_areas'],
        'partial_function_areas': analysis['partial_function_areas'],
        'missing_function_areas': analysis['missing_function_areas'],
        'optimization_opportunities': analysis['optimization_opportunities'][:3]
    }, indent=2, ensure_ascii=False))
    
    print("\n=== 拓展缺失功能 ===")
    expansion = agent.expand_features()
    print(f"分析结果: {expansion['analysis_results']['total_plans']} 个计划")
    print(f"新增计划数: {expansion['new_plans_created']}")
    if expansion['plan_details']:
        print("新增计划详情:")
        for plan in expansion['plan_details'][:3]:
            print(f"  - {plan['name']} ({plan['plan_type']})")
    
    print("\n=== 优化计划 ===")
    optimization = agent.optimize_plans()
    print(f"优化计划数: {optimization['total_plans']}")
    print(f"优化项数: {optimization['total_optimizations']}")
    print(f"预期整体提升: {optimization['expected_overall_improvement']:.1%}")
    
    print("\n=== 最终计划列表 ===")
    final_plans = agent.list_plans()
    print(f"总计: {len(final_plans)} 个计划")
    for plan in final_plans:
        print(f"  ✓ {plan['name']} ({plan['plan_type']}, {plan['priority']})")
    
    agent.shutdown()