# -*- coding: utf-8 -*-
"""
自动迭代更新规则配置
包含：迭代周期、触发条件、AI员工分配、审批规则、回滚策略
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class IterationConfig:
    """迭代配置常量"""
    
    ITERATION_CYCLES = {
        'daily': {
            'name': '每日迭代',
            'interval_seconds': 3600 * 24,
            'description': '每日自动执行一次迭代更新',
            'enabled': True,
            'level': 'patch'
        },
        'weekly': {
            'name': '每周迭代',
            'interval_seconds': 3600 * 24 * 7,
            'description': '每周自动执行一次迭代更新',
            'enabled': True,
            'level': 'minor'
        },
        'monthly': {
            'name': '每月迭代',
            'interval_seconds': 3600 * 24 * 30,
            'description': '每月自动执行一次迭代更新',
            'enabled': True,
            'level': 'major'
        },
        'on_demand': {
            'name': '按需迭代',
            'interval_seconds': 0,
            'description': '手动触发的迭代更新',
            'enabled': True,
            'level': 'patch'
        }
    }
    
    LEVEL_PRIORITY_MAP = {
        'patch': 'low',
        'minor': 'medium',
        'major': 'high'
    }
    
    LEVEL_APPROVAL_MAP = {
        'patch': 'auto_approve',
        'minor': 'manager_approval',
        'major': 'security_approval'
    }
    
    AUTO_MERGE_LEVELS = ['patch']
    AUTO_ROLLBACK_LEVELS = ['patch', 'minor']
    
    def get_default_interval(self) -> int:
        """获取默认迭代间隔（秒）"""
        daily_cycle = self.ITERATION_CYCLES.get('daily', {})
        return daily_cycle.get('interval_seconds', 3600 * 24)
    
    def get_priority_by_level(self, level: str) -> str:
        """根据级别获取优先级"""
        return self.LEVEL_PRIORITY_MAP.get(level, 'medium')
    
    def get_approval_level(self, level: str) -> str:
        """根据级别获取审批级别"""
        return self.LEVEL_APPROVAL_MAP.get(level, 'manager_approval')
    
    def should_auto_merge(self, level: str) -> bool:
        """判断是否自动合并"""
        return level in self.AUTO_MERGE_LEVELS
    
    def should_auto_rollback(self, level: str) -> bool:
        """判断是否自动回滚"""
        return level in self.AUTO_ROLLBACK_LEVELS
    
    TRIGGER_CONDITIONS = {
        'error_rate_high': {
            'name': '错误率过高',
            'description': 'API错误率超过阈值',
            'conditions': [
                {'field': 'api_error_rate', 'operator': 'greater_than', 'value': 5.0}
            ],
            'required_count': 3,
            'action': 'immediate_fix'
        },
        'performance_degraded': {
            'name': '性能下降',
            'description': '系统性能低于阈值',
            'conditions': [
                {'field': 'cpu_usage', 'operator': 'greater_than', 'value': 85.0},
                {'field': 'memory_usage', 'operator': 'greater_than', 'value': 90.0},
                {'field': 'response_time', 'operator': 'greater_than', 'value': 3.0}
            ],
            'required_count': 2,
            'action': 'performance_optimization'
        },
        'security_threat': {
            'name': '安全威胁',
            'description': '检测到安全漏洞',
            'conditions': [
                {'field': 'vulnerability_count', 'operator': 'greater_than', 'value': 0},
                {'field': 'critical_vulnerabilities', 'operator': 'greater_than', 'value': 0}
            ],
            'required_count': 1,
            'action': 'security_patch'
        },
        'dependency_outdated': {
            'name': '依赖过期',
            'description': '依赖包需要更新',
            'conditions': [
                {'field': 'outdated_dependencies', 'operator': 'greater_than', 'value': 10},
                {'field': 'high_risk_dependencies', 'operator': 'greater_than', 'value': 2}
            ],
            'required_count': 1,
            'action': 'dependency_upgrade'
        },
        'code_quality_low': {
            'name': '代码质量低',
            'description': '代码复杂度或重复率过高',
            'conditions': [
                {'field': 'complexity_score', 'operator': 'greater_than', 'value': 80},
                {'field': 'duplication_rate', 'operator': 'greater_than', 'value': 20}
            ],
            'required_count': 1,
            'action': 'code_refactor'
        },
        'user_feedback': {
            'name': '用户反馈',
            'description': '用户反馈问题达到一定数量',
            'conditions': [
                {'field': 'pending_issues', 'operator': 'greater_than', 'value': 5},
                {'field': 'user_complaints', 'operator': 'greater_than', 'value': 3}
            ],
            'required_count': 1,
            'action': 'feature_enhancement'
        }
    }
    
    AI_EMPLOYEE_ROLES = {
        'code_fixer': {
            'name': '代码修复专家',
            'description': '负责代码错误修复和优化',
            'skills': ['语法错误检测', '逻辑错误修复', '代码重构', '性能优化'],
            'task_types': ['bug_fix', 'code_refactor', 'performance_optimization'],
            'priority': 'high',
            'approval_required': False
        },
        'system_maintenance': {
            'name': '系统维护专家',
            'description': '负责系统日常维护和健康检查',
            'skills': ['数据库清理', '日志管理', '健康检查', '备份管理'],
            'task_types': ['system_maintenance', 'health_check', 'backup'],
            'priority': 'medium',
            'approval_required': False
        },
        'data_analyzer': {
            'name': '数据分析专家',
            'description': '负责数据分析和决策支持',
            'skills': ['数据统计', '趋势分析', '可视化生成', '预测分析'],
            'task_types': ['data_analysis', 'performance_report', 'trend_prediction'],
            'priority': 'medium',
            'approval_required': False
        },
        'security_guard': {
            'name': '安全防护专家',
            'description': '负责系统安全防护和漏洞扫描',
            'skills': ['入侵检测', '漏洞扫描', '安全加固', '渗透测试'],
            'task_types': ['security_scan', 'security_patch', 'security_audit'],
            'priority': 'high',
            'approval_required': True
        },
        'performance_optimizer': {
            'name': '性能优化专家',
            'description': '负责系统性能优化和瓶颈分析',
            'skills': ['性能监控', '瓶颈识别', '优化建议', '负载均衡'],
            'task_types': ['performance_optimization', 'load_testing', 'capacity_planning'],
            'priority': 'high',
            'approval_required': False
        },
        'qa_validator': {
            'name': '质量验证专家',
            'description': '负责测试验证和质量保证',
            'skills': ['功能测试', '回归测试', '缺陷报告', '测试用例设计'],
            'task_types': ['test_execution', 'quality_assurance', 'regression_testing'],
            'priority': 'medium',
            'approval_required': False
        },
        'knowledge_manager': {
            'name': '知识管理专家',
            'description': '负责知识积累和智能决策',
            'skills': ['知识提取', '知识分类', '知识更新', '智能推荐'],
            'task_types': ['knowledge_update', 'decision_support', 'intelligence_analysis'],
            'priority': 'low',
            'approval_required': False
        },
        'coordinator': {
            'name': '任务协调专家',
            'description': '负责任务分配和进度协调',
            'skills': ['任务分配', '进度跟踪', '资源调度', '团队协作'],
            'task_types': ['task_coordination', 'project_management', 'resource_allocation'],
            'priority': 'medium',
            'approval_required': False
        },
        'version_upgrader': {
            'name': '版本升级专家',
            'description': '负责版本管理和升级',
            'skills': ['版本规划', '升级执行', '回滚操作', '发布管理'],
            'task_types': ['version_upgrade', 'release_management', 'rollback'],
            'priority': 'high',
            'approval_required': True
        },
        'dependency_manager': {
            'name': '依赖管理专家',
            'description': '负责依赖包管理和安全更新',
            'skills': ['依赖扫描', '安全更新', '兼容性测试', '版本锁定'],
            'task_types': ['dependency_upgrade', 'security_update', 'compatibility_test'],
            'priority': 'high',
            'approval_required': False
        },
        'frontend_engineer': {
            'name': '前端开发专家',
            'description': '负责前端页面开发和优化',
            'skills': ['页面开发', '性能优化', '用户体验', '响应式设计'],
            'task_types': ['frontend_development', 'ui_optimization', 'ux_enhancement'],
            'priority': 'medium',
            'approval_required': False
        },
        'backend_engineer': {
            'name': '后端开发专家',
            'description': '负责后端系统开发和维护',
            'skills': ['API开发', '数据库设计', '业务逻辑', '系统架构'],
            'task_types': ['backend_development', 'api_design', 'database_optimization'],
            'priority': 'medium',
            'approval_required': False
        },
        'devops_engineer': {
            'name': 'DevOps专家',
            'description': '负责自动化部署和运维',
            'skills': ['自动化部署', 'CI/CD', '监控告警', '故障排查'],
            'task_types': ['deployment', 'automation', 'monitoring', 'troubleshooting'],
            'priority': 'high',
            'approval_required': False
        },
        'ai_trainer': {
            'name': 'AI训练专家',
            'description': '负责AI模型训练和优化',
            'skills': ['模型训练', '参数调优', '模型评估', '知识注入'],
            'task_types': ['model_training', 'ai_optimization', 'knowledge_enhancement'],
            'priority': 'medium',
            'approval_required': False
        }
    }
    
    APPROVAL_RULES = {
        'auto_approve': {
            'name': '自动审批',
            'description': '低风险操作自动通过',
            'conditions': [
                {'field': 'risk_level', 'operator': 'less_or_equal', 'value': 2},
                {'field': 'change_scope', 'operator': 'in_list', 'value': ['patch', 'minor']}
            ],
            'max_cost': 100,
            'enabled': True
        },
        'manager_approval': {
            'name': '管理员审批',
            'description': '中等风险操作需要管理员审批',
            'conditions': [
                {'field': 'risk_level', 'operator': 'between', 'value': [3, 5]},
                {'field': 'change_scope', 'operator': 'in_list', 'value': ['minor', 'major']}
            ],
            'max_cost': 1000,
            'timeout_seconds': 3600,
            'enabled': True
        },
        'emergency_approval': {
            'name': '紧急审批',
            'description': '紧急操作快速审批流程',
            'conditions': [
                {'field': 'risk_level', 'operator': 'greater_or_equal', 'value': 6},
                {'field': 'urgency', 'operator': 'equals', 'value': 'emergency'}
            ],
            'max_cost': 5000,
            'timeout_seconds': 300,
            'enabled': True
        },
        'security_approval': {
            'name': '安全审批',
            'description': '安全相关操作需要安全团队审批',
            'conditions': [
                {'field': 'category', 'operator': 'in_list', 'value': ['security', 'privacy', 'data']}
            ],
            'max_cost': 10000,
            'timeout_seconds': 7200,
            'enabled': True
        }
    }
    
    ROLLBACK_STRATEGIES = {
        'auto_rollback': {
            'name': '自动回滚',
            'description': '检测到问题自动回滚',
            'conditions': [
                {'field': 'error_rate', 'operator': 'greater_than', 'value': 10.0},
                {'field': 'response_time', 'operator': 'greater_than', 'value': 5.0},
                {'field': 'system_status', 'operator': 'equals', 'value': 'critical'}
            ],
            'required_count': 1,
            'delay_seconds': 60
        },
        'manual_rollback': {
            'name': '手动回滚',
            'description': '需要人工确认后回滚',
            'conditions': [
                {'field': 'user_impact', 'operator': 'greater_than', 'value': 100},
                {'field': 'data_risk', 'operator': 'greater_than', 'value': 5}
            ],
            'required_count': 1,
            'delay_seconds': 0
        },
        'partial_rollback': {
            'name': '部分回滚',
            'description': '只回滚有问题的部分',
            'conditions': [
                {'field': 'error_scope', 'operator': 'in_list', 'value': ['single_module', 'specific_api']}
            ],
            'required_count': 1,
            'delay_seconds': 30
        }
    }
    
    TEST_CRITERIA = {
        'unit_test': {
            'name': '单元测试',
            'pass_threshold': 80,
            'required': True,
            'timeout_seconds': 300
        },
        'api_test': {
            'name': 'API测试',
            'pass_threshold': 90,
            'required': True,
            'timeout_seconds': 600
        },
        'performance_test': {
            'name': '性能测试',
            'pass_threshold': 70,
            'required': False,
            'timeout_seconds': 1200
        },
        'security_test': {
            'name': '安全测试',
            'pass_threshold': 95,
            'required': False,
            'timeout_seconds': 600
        }
    }
    
    GRAY_RELEASE_CONFIG = {
        'enabled': True,
        'phases': [
            {'name': '内部测试', 'percentage': 5, 'duration_minutes': 60},
            {'name': '小范围灰度', 'percentage': 20, 'duration_minutes': 120},
            {'name': '大范围灰度', 'percentage': 50, 'duration_minutes': 180},
            {'name': '全量发布', 'percentage': 100, 'duration_minutes': 0}
        ],
        'health_check_interval': 60,
        'max_unhealthy_count': 3
    }


class IterationRuleEngine:
    """迭代规则引擎"""
    
    def __init__(self):
        self.config = IterationConfig()
    
    def evaluate_triggers(self, metrics: Dict) -> List[str]:
        """评估触发条件"""
        triggered_actions = []
        
        for trigger_key, trigger_config in self.config.TRIGGER_CONDITIONS.items():
            conditions = trigger_config['conditions']
            required_count = trigger_config['required_count']
            met_count = 0
            
            for condition in conditions:
                field = condition['field']
                operator = condition['operator']
                value = condition['value']
                
                field_value = metrics.get(field)
                
                if self._evaluate_condition(field_value, operator, value):
                    met_count += 1
            
            if met_count >= required_count:
                triggered_actions.append(trigger_config['action'])
                logger.info(f"[迭代规则] 触发条件满足: {trigger_key} -> {trigger_config['action']}")
        
        return triggered_actions
    
    def _evaluate_condition(self, field_value, operator: str, value) -> bool:
        """评估单个条件"""
        try:
            if operator == 'equals':
                return field_value == value
            elif operator == 'not_equals':
                return field_value != value
            elif operator == 'greater_than':
                return field_value is not None and field_value > value
            elif operator == 'less_than':
                return field_value is not None and field_value < value
            elif operator == 'greater_or_equal':
                return field_value is not None and field_value >= value
            elif operator == 'less_or_equal':
                return field_value is not None and field_value <= value
            elif operator == 'contains':
                return field_value is not None and value in str(field_value)
            elif operator == 'not_contains':
                return field_value is None or value not in str(field_value)
            elif operator == 'between':
                return field_value is not None and value[0] <= field_value <= value[1]
            elif operator == 'in_list':
                return field_value is not None and field_value in value
            elif operator == 'not_in_list':
                return field_value is None or field_value not in value
            elif operator == 'exists':
                return field_value is not None
            elif operator == 'not_exists':
                return field_value is None
            
            return False
        except Exception as e:
            logger.error(f"[迭代规则] 条件评估失败: {e}")
            return False
    
    def assign_employees(self, task_type: str) -> List[str]:
        """根据任务类型分配AI员工"""
        assigned_employees = []
        
        for employee_key, employee_config in self.config.AI_EMPLOYEE_ROLES.items():
            if task_type in employee_config['task_types']:
                assigned_employees.append(employee_key)
        
        return assigned_employees
    
    def get_approval_level(self, task_type: str, risk_level: int = 1, 
                          change_scope: str = 'patch') -> str:
        """获取审批级别"""
        for approval_key, approval_config in self.config.APPROVAL_RULES.items():
            conditions = approval_config['conditions']
            met_all = True
            
            for condition in conditions:
                field = condition['field']
                operator = condition['operator']
                value = condition['value']
                
                field_value = {
                    'risk_level': risk_level,
                    'change_scope': change_scope,
                    'urgency': 'normal',
                    'category': self._get_task_category(task_type)
                }.get(field)
                
                if not self._evaluate_condition(field_value, operator, value):
                    met_all = False
                    break
            
            if met_all and approval_config['enabled']:
                return approval_key
        
        return 'manager_approval'
    
    def _get_task_category(self, task_type: str) -> str:
        """获取任务分类"""
        security_tasks = ['security_scan', 'security_patch', 'security_audit']
        data_tasks = ['data_analysis', 'database_optimization', 'backup']
        
        if task_type in security_tasks:
            return 'security'
        elif task_type in data_tasks:
            return 'data'
        return 'general'
    
    def should_rollback(self, metrics: Dict) -> bool:
        """判断是否需要回滚"""
        for rollback_key, rollback_config in self.config.ROLLBACK_STRATEGIES.items():
            conditions = rollback_config['conditions']
            required_count = rollback_config['required_count']
            met_count = 0
            
            for condition in conditions:
                field = condition['field']
                operator = condition['operator']
                value = condition['value']
                
                field_value = metrics.get(field)
                
                if self._evaluate_condition(field_value, operator, value):
                    met_count += 1
            
            if met_count >= required_count:
                logger.warning(f"[迭代规则] 触发回滚策略: {rollback_key}")
                return True
        
        return False
    
    def get_test_criteria(self, task_type: str) -> List[str]:
        """获取测试标准"""
        required_tests = ['unit_test', 'api_test']
        
        security_tasks = ['security_scan', 'security_patch']
        performance_tasks = ['performance_optimization', 'load_testing']
        
        if task_type in security_tasks:
            required_tests.append('security_test')
        if task_type in performance_tasks:
            required_tests.append('performance_test')
        
        return required_tests
    
    def get_iteration_cycle(self, cycle_type: str) -> Dict:
        """获取迭代周期配置"""
        return self.config.ITERATION_CYCLES.get(cycle_type, {})
    
    def get_gray_release_config(self) -> Dict:
        """获取灰度发布配置"""
        return self.config.GRAY_RELEASE_CONFIG
    
    def validate_config(self) -> Dict:
        """验证配置"""
        errors = []
        warnings = []
        
        for key, cycle in self.config.ITERATION_CYCLES.items():
            if cycle.get('interval_seconds') < 0:
                errors.append(f"迭代周期 {key} 间隔时间无效")
        
        for key, trigger in self.config.TRIGGER_CONDITIONS.items():
            if not trigger.get('conditions'):
                errors.append(f"触发条件 {key} 没有定义条件")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }


_iteration_rule_engine_instance = None


def get_iteration_rule_engine() -> IterationRuleEngine:
    """获取迭代规则引擎实例"""
    global _iteration_rule_engine_instance
    if _iteration_rule_engine_instance is None:
        _iteration_rule_engine_instance = IterationRuleEngine()
    return _iteration_rule_engine_instance


def init_iteration_rules():
    """初始化迭代规则引擎"""
    engine = get_iteration_rule_engine()
    validation = engine.validate_config()
    
    if validation['valid']:
        logger.info("[迭代规则] 自动迭代更新规则配置验证通过")
    else:
        for error in validation['errors']:
            logger.error(f"[迭代规则] 配置错误: {error}")
    
    return engine