# -*- coding: utf-8 -*-
"""
MTSCOS 系统功能拓展模块
为系统自动处理器添加新的 Agent 模板、自动化进程、计划任务
为 AI 集群管理器添加新的员工类型和集群
提供真实的功能拓展，而非仅管理界面
"""

import os
import sys
import json
import time
import logging
import threading
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('SystemFunctionExtender')

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')


# ==================== 新增 Agent 模板定义 ====================

EXTENDED_AGENT_TEMPLATES = {
    'notification_agent': {
        'name': '通知管理Agent',
        'type': 'notification_specialist',
        'capabilities': ['notification_dispatch', 'message_routing', 'alert_escalation', 'broadcast_management'],
        'level': 3,
        'auto_scale': True,
        'min_instances': 1,
        'max_instances': 3
    },
    'backup_agent': {
        'name': '备份管理Agent',
        'type': 'backup_specialist',
        'capabilities': ['backup_creation', 'restore_operations', 'integrity_verification', 'iso_generation'],
        'level': 4,
        'auto_scale': True,
        'min_instances': 1,
        'max_instances': 2
    },
    'learning_agent': {
        'name': '学习增强Agent',
        'type': 'learning_specialist',
        'capabilities': ['knowledge_extraction', 'pattern_recognition', 'adaptive_learning', 'brain_bank_sync'],
        'level': 4,
        'auto_scale': True,
        'min_instances': 2,
        'max_instances': 5
    },
    'analytics_agent': {
        'name': '数据分析Agent',
        'type': 'data_analyst',
        'capabilities': ['data_mining', 'statistical_analysis', 'trend_prediction', 'report_generation'],
        'level': 3,
        'auto_scale': True,
        'min_instances': 1,
        'max_instances': 3
    },
    'security_audit_agent': {
        'name': '安全审计Agent',
        'type': 'security_auditor',
        'capabilities': ['vulnerability_scan', 'audit_log_analysis', 'compliance_check', 'threat_detection'],
        'level': 5,
        'auto_scale': False,
        'min_instances': 1,
        'max_instances': 1
    },
    'content_agent': {
        'name': '内容生成Agent',
        'type': 'content_generator',
        'capabilities': ['question_generation', 'content_curation', 'translation', 'summarization'],
        'level': 2,
        'auto_scale': True,
        'min_instances': 2,
        'max_instances': 8
    }
}


# ==================== 新增自动化进程定义 ====================

EXTENDED_PROCESS_CONFIGS = {
    'security_scan': {
        'name': '安全扫描进程',
        'interval': 300,
        'enabled': True,
        'description': '定期扫描系统安全漏洞和异常访问'
    },
    'log_analyzer': {
        'name': '日志分析进程',
        'interval': 180,
        'enabled': True,
        'description': '分析系统日志，识别异常模式和性能瓶颈'
    },
    'health_report': {
        'name': '健康报告进程',
        'interval': 600,
        'enabled': True,
        'description': '生成系统健康报告并上传数据库'
    },
    'auto_backup_check': {
        'name': '备份检查进程',
        'interval': 900,
        'enabled': True,
        'description': '检查备份完整性和可用性'
    },
    'capacity_monitor': {
        'name': '容量监控进程',
        'interval': 240,
        'enabled': True,
        'description': '监控系统资源容量和使用趋势'
    }
}


# ==================== 新增计划任务定义 ====================

EXTENDED_PLANS = {
    'monthly_report': {
        'name': '月度运维报告',
        'trigger': 'cron',
        'day': 1,
        'hour': 5,
        'minute': 0,
        'func': 'monthly_report_generation',
        'enabled': True
    },
    'security_audit': {
        'name': '安全审计',
        'trigger': 'cron',
        'day_of_week': 'sat',
        'hour': 2,
        'minute': 30,
        'func': 'security_audit_task',
        'enabled': True
    },
    'capacity_planning': {
        'name': '容量规划',
        'trigger': 'interval',
        'hours': 6,
        'func': 'capacity_planning_task',
        'enabled': True
    },
    'knowledge_consolidation': {
        'name': '知识库整合',
        'trigger': 'cron',
        'hour': 22,
        'minute': 0,
        'func': 'knowledge_consolidation_task',
        'enabled': True
    },
    'employee_performance_review': {
        'name': '员工绩效评估',
        'trigger': 'cron',
        'day_of_week': 'fri',
        'hour': 18,
        'minute': 0,
        'func': 'performance_review_task',
        'enabled': True
    }
}


# ==================== 新增 AI 员工类型和集群 ====================

EXTENDED_EMPLOYEE_TYPES = {
    'security_analyst': {
        'name': '安全分析师',
        'capabilities': ['threat_analysis', 'vulnerability_assessment', 'incident_response', 'security_reporting'],
        'cluster_id': 'security_cluster_ext',
        'cluster_type': 'security'
    },
    'data_scientist': {
        'name': '数据科学家',
        'capabilities': ['data_modeling', 'machine_learning', 'statistical_analysis', 'predictive_modeling'],
        'cluster_id': 'analytics_cluster_ext',
        'cluster_type': 'analytics'
    },
    'content_generator': {
        'name': '内容生成师',
        'capabilities': ['question_writing', 'content_creation', 'curriculum_design', 'translation'],
        'cluster_id': 'content_cluster_ext',
        'cluster_type': 'content'
    },
    'translator': {
        'name': '翻译专家',
        'capabilities': ['japanese_translation', 'english_translation', 'bilingual_support', 'audio_subtitle'],
        'cluster_id': 'content_cluster_ext',
        'cluster_type': 'content'
    },
    'code_reviewer': {
        'name': '代码审查师',
        'capabilities': ['code_review', 'bug_detection', 'best_practices', 'refactoring_suggestions'],
        'cluster_id': 'quality_cluster_ext',
        'cluster_type': 'quality'
    },
    'user_experience_analyst': {
        'name': '用户体验分析师',
        'capabilities': ['ux_analysis', 'user_behavior_tracking', 'interface_optimization', 'accessibility_audit'],
        'cluster_id': 'analytics_cluster_ext',
        'cluster_type': 'analytics'
    }
}


class SystemFunctionExtender:
    """系统功能拓展器 - 单例模式"""

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
        self.extension_results = {
            'agents_added': 0,
            'processes_added': 0,
            'plans_added': 0,
            'employee_types_added': 0,
            'clusters_added': 0,
            'employees_registered': 0
        }
        self._initialized = True
        logger.info("SystemFunctionExtender 初始化完成")

    def extend_all(self) -> Dict[str, Any]:
        """执行所有功能拓展"""
        with self._lock:
            results = {
                'start_time': datetime.now().isoformat(),
                'extensions': []
            }

            # 1. 拓展 Agent 模板
            r1 = self.extend_agent_templates()
            results['extensions'].append(r1)

            # 2. 拓展自动化进程
            r2 = self.extend_process_configs()
            results['extensions'].append(r2)

            # 3. 拓展计划任务
            r3 = self.extend_plan_configs()
            results['extensions'].append(r3)

            # 4. 拓展 AI 员工类型和集群
            r4 = self.extend_employee_types()
            results['extensions'].append(r4)

            results['end_time'] = datetime.now().isoformat()
            results['summary'] = self.extension_results
            results['success'] = True

            self._save_extension_record(results)
            return results

    def extend_agent_templates(self) -> Dict[str, Any]:
        """拓展 Agent 模板"""
        try:
            from ai_engines.system_auto_processor import AutoAgentManager
            am = AutoAgentManager()

            added = 0
            skipped = 0
            for template_id, template in EXTENDED_AGENT_TEMPLATES.items():
                if template_id not in am.default_agent_templates:
                    am.default_agent_templates[template_id] = template
                    added += 1
                    logger.info(f"添加 Agent 模板: {template['name']}")
                else:
                    skipped += 1

            self.extension_results['agents_added'] = added
            return {
                'extension': 'agent_templates',
                'success': True,
                'added': added,
                'skipped': skipped,
                'total_templates': len(am.default_agent_templates)
            }
        except Exception as e:
            logger.error(f"拓展 Agent 模板失败: {e}")
            return {'extension': 'agent_templates', 'success': False, 'error': str(e)}

    def extend_process_configs(self) -> Dict[str, Any]:
        """拓展自动化进程"""
        try:
            from ai_engines.system_auto_processor import AutoProcessManager
            pm = AutoProcessManager()

            added = 0
            skipped = 0
            for pid, config in EXTENDED_PROCESS_CONFIGS.items():
                if pid not in pm.auto_process_configs:
                    pm.auto_process_configs[pid] = config
                    added += 1
                    logger.info(f"添加自动化进程: {config['name']}")
                else:
                    skipped += 1

            self.extension_results['processes_added'] = added
            return {
                'extension': 'process_configs',
                'success': True,
                'added': added,
                'skipped': skipped,
                'total_processes': len(pm.auto_process_configs)
            }
        except Exception as e:
            logger.error(f"拓展自动化进程失败: {e}")
            return {'extension': 'process_configs', 'success': False, 'error': str(e)}

    def extend_plan_configs(self) -> Dict[str, Any]:
        """拓展计划任务"""
        try:
            from ai_engines.system_auto_processor import AutoPlanScheduler
            ps = AutoPlanScheduler()

            added = 0
            skipped = 0
            for plan_id, config in EXTENDED_PLANS.items():
                if plan_id not in ps.default_plans:
                    ps.default_plans[plan_id] = config
                    added += 1
                    logger.info(f"添加计划任务: {config['name']}")
                else:
                    skipped += 1

            self.extension_results['plans_added'] = added
            return {
                'extension': 'plan_configs',
                'success': True,
                'added': added,
                'skipped': skipped,
                'total_plans': len(ps.default_plans)
            }
        except Exception as e:
            logger.error(f"拓展计划任务失败: {e}")
            return {'extension': 'plan_configs', 'success': False, 'error': str(e)}

    def extend_employee_types(self) -> Dict[str, Any]:
        """拓展 AI 员工类型和集群"""
        try:
            from ai_engines.ai_cluster_manager import ai_cluster_manager

            added_types = 0
            added_clusters = 0
            added_employees = 0
            cluster_ids_created = set()

            for emp_type, config in EXTENDED_EMPLOYEE_TYPES.items():
                cluster_id = config['cluster_id']

                # 创建集群（如果不存在）- 使用公共API
                if cluster_id not in ai_cluster_manager.clusters:
                    if ai_cluster_manager.create_cluster(cluster_id, config['cluster_type']):
                        added_clusters += 1
                        cluster_ids_created.add(cluster_id)
                        logger.info(f"创建集群: {cluster_id} ({config['cluster_type']})")
                    else:
                        # create_cluster 返回False可能是已存在，直接使用
                        if cluster_id not in ai_cluster_manager.clusters:
                            continue

                # 注册员工类型到数据库
                if self._register_employee_type(emp_type, config):
                    added_types += 1

                # 为新集群创建初始员工 - 使用公共API
                emp_id = f"{emp_type}_{int(time.time())}_{added_employees}"
                if ai_cluster_manager.create_employee(emp_id, emp_type, config['capabilities']):
                    if ai_cluster_manager.assign_employee_to_cluster(emp_id, cluster_id):
                        added_employees += 1
                        logger.info(f"注册员工: {emp_id} ({config['name']})")

            self.extension_results['employee_types_added'] = added_types
            self.extension_results['clusters_added'] = added_clusters
            self.extension_results['employees_registered'] = added_employees

            return {
                'extension': 'employee_types',
                'success': True,
                'types_added': added_types,
                'clusters_added': added_clusters,
                'employees_registered': added_employees,
                'total_clusters': len(ai_cluster_manager.clusters),
                'total_employees': len(ai_cluster_manager.employees)
            }
        except Exception as e:
            logger.error(f"拓展员工类型失败: {e}")
            return {'extension': 'employee_types', 'success': False, 'error': str(e)}

    def _register_employee_type(self, emp_type: str, config: Dict) -> bool:
        """注册员工类型到数据库"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO ai_employee_config
                    (employee_id, employee_type, capabilities, config, assigned_cluster, status, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    f"type_def_{emp_type}",
                    emp_type,
                    json.dumps(config['capabilities']),
                    json.dumps({'name': config['name'], 'type_def': True}),
                    config['cluster_id'],
                    'active',
                    datetime.now().isoformat()
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"注册员工类型 {emp_type} 失败: {e}")
            return False

    def _save_extension_record(self, results: Dict):
        """保存拓展记录到数据库"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS mtscos_function_extensions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        extension_type TEXT NOT NULL,
                        details TEXT,
                        summary TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                cursor.execute('''
                    INSERT INTO mtscos_function_extensions
                    (extension_type, details, summary, created_at)
                    VALUES (?, ?, ?, ?)
                ''', (
                    'full_extension',
                    json.dumps(results, ensure_ascii=False),
                    json.dumps(results.get('summary', {}), ensure_ascii=False),
                    datetime.now().isoformat()
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"保存拓展记录失败: {e}")

    def get_extension_summary(self) -> Dict[str, Any]:
        """获取拓展摘要"""
        return {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'summary': self.extension_results,
            'extended_agent_templates': list(EXTENDED_AGENT_TEMPLATES.keys()),
            'extended_processes': list(EXTENDED_PROCESS_CONFIGS.keys()),
            'extended_plans': list(EXTENDED_PLANS.keys()),
            'extended_employee_types': list(EXTENDED_EMPLOYEE_TYPES.keys())
        }


system_function_extender = SystemFunctionExtender()
