# -*- coding: utf-8 -*-
"""
集群矩阵管理器
整合 AI员工集群矩阵、AI Agent集群矩阵、自动化集群矩阵
提供统一的矩阵数据管理和查询接口
"""

import os
import sys
import json
import time
import logging
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ClusterMatrixManager')


class ClusterMatrixManager:
    """集群矩阵管理器 - 统一管理三大矩阵"""

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._lock = threading.RLock()
        self._initialized = True

    # ==================== AI员工集群矩阵 ====================

    def get_employee_cluster_matrix(self) -> Dict[str, Any]:
        """获取AI员工集群矩阵数据"""
        try:
            from ai_engines.ai_cluster_manager import ai_cluster_manager

            clusters = []
            employees_by_cluster = {}
            all_employee_types = set()

            for cluster_id, cluster in ai_cluster_manager.clusters.items():
                cluster_info = {
                    'cluster_id': cluster_id,
                    'cluster_type': cluster.cluster_type,
                    'status': cluster.status,
                    'employee_count': len(cluster.employees),
                    'task_queue_length': len(cluster.task_queue),
                    'created_at': cluster.created_at,
                    'last_updated': cluster.last_updated
                }
                clusters.append(cluster_info)

                employees = []
                for emp_id, emp in cluster.employees.items():
                    emp_info = {
                        'employee_id': emp.employee_id,
                        'employee_type': emp.employee_type,
                        'status': emp.status,
                        'capabilities': emp.capabilities,
                        'assigned_cluster': emp.assigned_cluster,
                        'tasks_completed': emp.performance_metrics.get('tasks_completed', 0),
                        'success_rate': emp.performance_metrics.get('success_rate', 0),
                        'last_heartbeat': emp.last_heartbeat
                    }
                    employees.append(emp_info)
                    all_employee_types.add(emp.employee_type)

                employees_by_cluster[cluster_id] = employees

            # 构建矩阵: cluster x employee_type
            employee_types = sorted(list(all_employee_types))
            matrix = []
            for cluster in clusters:
                row = {
                    'cluster_id': cluster['cluster_id'],
                    'cluster_type': cluster['cluster_type'],
                    'cells': []
                }
                cluster_emps = employees_by_cluster.get(cluster['cluster_id'], [])
                for emp_type in employee_types:
                    matching = [e for e in cluster_emps if e['employee_type'] == emp_type]
                    row['cells'].append({
                        'employee_type': emp_type,
                        'count': len(matching),
                        'employees': [e['employee_id'] for e in matching],
                        'statuses': [e['status'] for e in matching]
                    })
                matrix.append(row)

            return {
                'success': True,
                'matrix_type': 'employee_cluster',
                'timestamp': datetime.now().isoformat(),
                'clusters': clusters,
                'employee_types': employee_types,
                'matrix': matrix,
                'total_clusters': len(clusters),
                'total_employees': sum(c['employee_count'] for c in clusters),
                'summary': {
                    'active_employees': sum(1 for c in clusters for e in employees_by_cluster.get(c['cluster_id'], []) if e['status'] == 'active'),
                    'busy_employees': sum(1 for c in clusters for e in employees_by_cluster.get(c['cluster_id'], []) if e['status'] == 'busy'),
                    'error_employees': sum(1 for c in clusters for e in employees_by_cluster.get(c['cluster_id'], []) if e['status'] == 'error')
                }
            }
        except Exception as e:
            logger.error(f"获取员工集群矩阵失败: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== AI Agent集群矩阵 ====================

    def get_agent_cluster_matrix(self) -> Dict[str, Any]:
        """获取AI Agent集群矩阵数据"""
        try:
            from ai_engines.system_auto_processor import AutoAgentManager

            am = AutoAgentManager()
            templates = am.get_agent_templates()
            agents = am.get_agents()

            # 按模板分组
            agents_by_template = {}
            for agent_id, agent in agents.items():
                template_id = agent.get('template', 'unknown')
                if template_id not in agents_by_template:
                    agents_by_template[template_id] = []
                agents_by_template[template_id].append(agent)

            # 构建模板矩阵
            template_matrix = []
            for template_id, template in templates.items():
                template_agents = agents_by_template.get(template_id, [])
                active_count = sum(1 for a in template_agents if a.get('status') == 'active')
                template_matrix.append({
                    'template_id': template_id,
                    'name': template['name'],
                    'type': template['type'],
                    'capabilities': template['capabilities'],
                    'level': template['level'],
                    'auto_scale': template.get('auto_scale', False),
                    'min_instances': template['min_instances'],
                    'max_instances': template['max_instances'],
                    'current_count': len(template_agents),
                    'active_count': active_count,
                    'capacity_utilization': round(len(template_agents) / max(template['max_instances'], 1) * 100, 1),
                    'agents': [{'id': a['id'], 'name': a['name'], 'status': a.get('status', 'unknown')} for a in template_agents]
                })

            return {
                'success': True,
                'matrix_type': 'agent_cluster',
                'timestamp': datetime.now().isoformat(),
                'templates': template_matrix,
                'total_templates': len(templates),
                'total_agents': len(agents),
                'summary': {
                    'auto_scale_enabled': sum(1 for t in templates.values() if t.get('auto_scale', False)),
                    'auto_scale_disabled': sum(1 for t in templates.values() if not t.get('auto_scale', False)),
                    'total_capacity': sum(t['max_instances'] for t in templates.values()),
                    'total_current': len(agents),
                    'utilization_rate': round(len(agents) / max(sum(t['max_instances'] for t in templates.values()), 1) * 100, 1)
                }
            }
        except Exception as e:
            logger.error(f"获取Agent集群矩阵失败: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== 自动化集群矩阵 ====================

    def get_automation_cluster_matrix(self) -> Dict[str, Any]:
        """获取自动化集群矩阵数据"""
        try:
            from ai_engines.system_auto_processor import SystemAutoProcessor

            processor = SystemAutoProcessor()

            # 进程矩阵
            process_status = processor.process_manager.get_process_status()
            process_matrix = []
            for pid, info in process_status.items():
                config = info.get('config') or {}
                stats = info.get('stats') or {}
                process_matrix.append({
                    'process_id': pid,
                    'name': config.get('name', pid),
                    'interval': config.get('interval', 0),
                    'enabled': config.get('enabled', False),
                    'description': config.get('description', ''),
                    'status': info.get('status', 'not_running'),
                    'execution_count': stats.get('execution_count', 0),
                    'last_execution': stats.get('last_execution'),
                    'total_duration': stats.get('total_duration', 0),
                    'start_time': stats.get('start_time')
                })

            # 计划任务矩阵
            plans = processor.plan_scheduler.get_plans()
            plan_matrix = []
            for plan_id, plan_info in plans.items():
                config = (plan_info or {}).get('config') or {}
                plan_matrix.append({
                    'plan_id': plan_id,
                    'name': config.get('name', plan_id),
                    'trigger': config.get('trigger', 'cron'),
                    'func': config.get('func', ''),
                    'enabled': config.get('enabled', False),
                    'schedule_info': self._format_schedule(config)
                })

            # 自动Agent矩阵
            agent_manager_data = self.get_agent_cluster_matrix()

            return {
                'success': True,
                'matrix_type': 'automation_cluster',
                'timestamp': datetime.now().isoformat(),
                'system_running': processor.is_running,
                'processes': process_matrix,
                'plans': plan_matrix,
                'agent_summary': {
                    'total_agents': agent_manager_data.get('total_agents', 0),
                    'total_templates': agent_manager_data.get('total_templates', 0),
                    'utilization_rate': agent_manager_data.get('summary', {}).get('utilization_rate', 0)
                },
                'summary': {
                    'total_processes': len(process_matrix),
                    'running_processes': sum(1 for p in process_matrix if p['status'] == 'running'),
                    'total_plans': len(plan_matrix),
                    'enabled_plans': sum(1 for p in plan_matrix if p['enabled']),
                    'total_agents': agent_manager_data.get('total_agents', 0),
                    'automation_coverage': round(
                        (len(process_matrix) + len(plan_matrix) + agent_manager_data.get('total_agents', 0)) /
                        max(len(process_matrix) + len(plan_matrix) + 10, 1) * 100, 1
                    )
                }
            }
        except Exception as e:
            logger.error(f"获取自动化集群矩阵失败: {e}")
            return {'success': False, 'error': str(e)}

    def _format_schedule(self, config: Dict) -> str:
        """格式化调度信息"""
        trigger = config.get('trigger', 'cron')
        if trigger == 'cron':
            parts = []
            if config.get('day_of_week'):
                parts.append(f"每周{config['day_of_week']}")
            if config.get('hour') is not None:
                parts.append(f"{config['hour']}时")
            if config.get('minute') is not None:
                parts.append(f"{config['minute']}分")
            return ' '.join(parts) if parts else 'cron'
        elif trigger == 'interval':
            for unit in ['weeks', 'days', 'hours', 'minutes', 'seconds']:
                if config.get(unit):
                    return f"每{config[unit]}{unit[:-1]}"
            return 'interval'
        return trigger

    # ==================== 统一矩阵接口 ====================

    def get_full_matrix(self) -> Dict[str, Any]:
        """获取完整矩阵数据"""
        return {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'employee_matrix': self.get_employee_cluster_matrix(),
            'agent_matrix': self.get_agent_cluster_matrix(),
            'automation_matrix': self.get_automation_cluster_matrix()
        }

    def get_matrix_overview(self) -> Dict[str, Any]:
        """获取矩阵概览"""
        emp_matrix = self.get_employee_cluster_matrix()
        agent_matrix = self.get_agent_cluster_matrix()
        auto_matrix = self.get_automation_cluster_matrix()

        return {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'overview': {
                'employee_clusters': emp_matrix.get('total_clusters', 0),
                'total_employees': emp_matrix.get('total_employees', 0),
                'agent_templates': agent_matrix.get('total_templates', 0),
                'total_agents': agent_matrix.get('total_agents', 0),
                'agent_capacity': agent_matrix.get('summary', {}).get('total_capacity', 0),
                'agent_utilization': agent_matrix.get('summary', {}).get('utilization_rate', 0),
                'automation_processes': auto_matrix.get('summary', {}).get('total_processes', 0),
                'running_processes': auto_matrix.get('summary', {}).get('running_processes', 0),
                'automation_plans': auto_matrix.get('summary', {}).get('total_plans', 0),
                'system_running': auto_matrix.get('system_running', False)
            }
        }


cluster_matrix_manager = ClusterMatrixManager()
