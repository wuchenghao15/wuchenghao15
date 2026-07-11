# -*- coding: utf-8 -*-
"""
规则自动生成器
支持系统规则自动创建、更新迭代，方便AI员工自动触发规则执行操作
"""

import os
import json
import logging
import threading
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class SystemRuleTemplate:
    """系统规则模板"""
    
    # 性能监控规则模板
    PERFORMANCE_RULES = [
        {
            'name': 'CPU使用率过高告警',
            'template_key': 'high_cpu_alert',
            'category': 'performance',
            'conditions': [
                {'field': 'cpu_usage', 'operator': 'greater_than', 'value': 80}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': 'CPU使用率超过80%', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'performance', 'employee_template': 'performance_optimizer'}}
            ],
            'priority': 10,
            'description': '当CPU使用率超过80%时触发告警和性能优化任务'
        },
        {
            'name': '内存使用率过高告警',
            'template_key': 'high_memory_alert',
            'category': 'performance',
            'conditions': [
                {'field': 'memory_usage', 'operator': 'greater_than', 'value': 85}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '内存使用率超过85%', 'level': 'warning'}}
            ],
            'priority': 10,
            'description': '当内存使用率超过85%时触发告警'
        },
        {
            'name': '磁盘空间不足告警',
            'template_key': 'low_disk_space',
            'category': 'performance',
            'conditions': [
                {'field': 'disk_usage', 'operator': 'greater_than', 'value': 90}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '磁盘使用率超过90%，空间不足', 'level': 'critical'}},
                {'action_type': 'execute_shell', 'params': {'command': 'df -h'}}
            ],
            'priority': 15,
            'description': '当磁盘使用率超过90%时触发告警'
        }
    ]
    
    # 任务管理规则模板
    TASK_RULES = [
        {
            'name': '待处理任务过多',
            'template_key': 'pending_tasks_overflow',
            'category': 'task_management',
            'conditions': [
                {'field': 'pending_tasks', 'operator': 'greater_than', 'value': 10}
            ],
            'actions': [
                {'action_type': 'create_employee', 'params': {'template_key': 'code_fixer', 'level': 'specialist'}},
                {'action_type': 'notify_admin', 'params': {'message': '待处理任务超过10个，已自动创建额外AI员工'}}
            ],
            'priority': 8,
            'description': '当待处理任务超过10个时自动创建AI员工分担工作'
        },
        {
            'name': '任务执行失败过多',
            'template_key': 'task_failures_high',
            'category': 'task_management',
            'conditions': [
                {'field': 'failed_tasks_rate', 'operator': 'greater_than', 'value': 0.3}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '任务失败率超过30%，需要检查系统稳定性', 'level': 'critical'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'diagnostic', 'employee_template': 'system_optimizer'}}
            ],
            'priority': 12,
            'description': '当任务失败率超过30%时触发系统诊断'
        },
        {
            'name': '批量任务超时',
            'template_key': 'batch_task_timeout',
            'category': 'task_management',
            'conditions': [
                {'field': 'batch_task_duration', 'operator': 'greater_than', 'value': 300}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '批量任务执行超过5分钟，可能存在性能问题'}},
                {'action_type': 'update_status', 'params': {'status': 'timeout_warning'}}
            ],
            'priority': 7,
            'description': '批量任务执行时间超过阈值时告警'
        }
    ]
    
    # 系统健康规则模板
    HEALTH_RULES = [
        {
            'name': '服务响应异常',
            'template_key': 'service_response_error',
            'category': 'health',
            'conditions': [
                {'field': 'error_rate', 'operator': 'greater_than', 'value': 0.05}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '服务错误率超过5%', 'level': 'critical'}},
                {'action_type': 'call_api', 'params': {'url': '/api/health/check', 'method': 'GET'}}
            ],
            'priority': 15,
            'description': '服务错误率异常时触发健康检查'
        },
        {
            'name': '数据库连接异常',
            'template_key': 'db_connection_error',
            'category': 'health',
            'conditions': [
                {'field': 'db_connection_failed', 'operator': 'equals', 'value': True}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '数据库连接失败，请立即检查', 'level': 'critical'}},
                {'action_type': 'execute_shell', 'params': {'command': 'sqlite3 app.db "PRAGMA integrity_check;"'}}
            ],
            'priority': 20,
            'description': '数据库连接失败时触发紧急告警'
        },
        {
            'name': 'Agent异常退出',
            'template_key': 'agent_abnormal_exit',
            'category': 'health',
            'conditions': [
                {'field': 'agent_exit_abnormal', 'operator': 'equals', 'value': True}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': 'Agent异常退出，正在自动重启', 'level': 'warning'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'agent_restart', 'employee_template': 'system_admin'}}
            ],
            'priority': 12,
            'description': 'Agent异常退出时自动重启'
        }
    ]
    
    # AI员工协作规则模板
    AI_EMPLOYEE_RULES = [
        {
            'name': 'AI员工负载过高',
            'template_key': 'ai_employee_overload',
            'category': 'ai_collaboration',
            'conditions': [
                {'field': 'ai_employee_tasks', 'operator': 'greater_than', 'value': 5}
            ],
            'actions': [
                {'action_type': 'create_employee', 'params': {'template_key': 'task_dispatcher', 'level': 'assistant'}},
                {'action_type': 'send_message', 'params': {'message_type': 'load_balance', 'content': {'action': 'rebalance'}}}
            ],
            'priority': 6,
            'description': '单个AI员工任务过多时创建协助员工'
        },
        {
            'name': '协作会话超时',
            'template_key': 'collaboration_timeout',
            'category': 'ai_collaboration',
            'conditions': [
                {'field': 'collaboration_duration', 'operator': 'greater_than', 'value': 600}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '协作会话超过10分钟，建议检查进度'}},
                {'action_type': 'update_status', 'params': {'status': 'collaboration_review'}}
            ],
            'priority': 5,
            'description': '协作会话超时提醒'
        },
        {
            'name': '知识共享触发',
            'template_key': 'knowledge_share_trigger',
            'category': 'ai_collaboration',
            'conditions': [
                {'field': 'new_knowledge_count', 'operator': 'greater_than', 'value': 3}
            ],
            'actions': [
                {'action_type': 'send_message', 'params': {'message_type': 'knowledge_share', 'content': {'action': 'broadcast'}}}
            ],
            'priority': 4,
            'description': '新知识积累到阈值时触发共享'
        }
    ]
    
    # 用户行为规则模板
    USER_BEHAVIOR_RULES = [
        {
            'name': '异常登录检测',
            'template_key': 'abnormal_login',
            'category': 'security',
            'conditions': [
                {'field': 'login_attempts', 'operator': 'greater_than', 'value': 5}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '检测到多次登录失败，可能存在异常访问', 'level': 'warning'}},
                {'action_type': 'update_status', 'params': {'status': 'security_alert'}}
            ],
            'priority': 15,
            'description': '登录失败次数过多触发安全告警'
        },
        {
            'name': '用户活跃度下降',
            'template_key': 'user_activity_drop',
            'category': 'user_behavior',
            'conditions': [
                {'field': 'user_activity_rate', 'operator': 'less_than', 'value': 0.1}
            ],
            'actions': [
                {'action_type': 'notify_admin', 'params': {'message': '用户活跃度下降，建议优化用户体验'}},
                {'action_type': 'dispatch_task', 'params': {'task_type': 'ux_analysis', 'employee_template': 'ux_analyzer'}}
            ],
            'priority': 3,
            'description': '用户活跃度下降触发分析任务'
        }
    ]
    
    # 获取所有模板
    ALL_TEMPLATES = PERFORMANCE_RULES + TASK_RULES + HEALTH_RULES + AI_EMPLOYEE_RULES + USER_BEHAVIOR_RULES
    
    @classmethod
    def get_all_templates_with_exam(cls):
        """获取包含考试系统的所有模板"""
        from app.agents.exam_rule_templates import ExamRuleTemplate
        return cls.ALL_TEMPLATES + ExamRuleTemplate.ALL_TEMPLATES
    
    @classmethod
    def get_exam_templates(cls, category: str = None):
        """获取考试系统规则模板"""
        from app.agents.exam_rule_templates import ExamRuleTemplate
        templates = ExamRuleTemplate.ALL_TEMPLATES
        if category:
            templates = [t for t in templates if t.get('category') == category]
        return templates
    
    @classmethod
    def get_all_templates_with_question_bank(cls):
        """获取包含题库系统的所有模板"""
        from app.agents.question_bank_rule_templates import QuestionBankRuleTemplate
        return cls.ALL_TEMPLATES + QuestionBankRuleTemplate.ALL_TEMPLATES
    
    @classmethod
    def get_question_bank_templates(cls, category: str = None):
        """获取题库系统规则模板"""
        from app.agents.question_bank_rule_templates import QuestionBankRuleTemplate
        templates = QuestionBankRuleTemplate.ALL_TEMPLATES
        if category:
            templates = [t for t in templates if t.get('category') == category]
        return templates
    
    @classmethod
    def get_all_templates_with_security(cls):
        """获取包含数据安全系统的所有模板"""
        from app.agents.security_rule_templates import SecurityRuleTemplate
        return cls.ALL_TEMPLATES + SecurityRuleTemplate.ALL_TEMPLATES
    
    @classmethod
    def get_security_templates(cls, category: str = None):
        """获取数据安全系统规则模板"""
        from app.agents.security_rule_templates import SecurityRuleTemplate
        templates = SecurityRuleTemplate.ALL_TEMPLATES
        if category:
            templates = [t for t in templates if t.get('category') == category]
        return templates
    
    @classmethod
    def get_all_templates_with_network_security(cls):
        """获取包含网络层安全系统的所有模板"""
        from app.agents.network_security_rule_templates import NetworkSecurityRuleTemplate
        return cls.ALL_TEMPLATES + NetworkSecurityRuleTemplate.ALL_TEMPLATES
    
    @classmethod
    def get_network_security_templates(cls, category: str = None):
        """获取网络层安全系统规则模板"""
        from app.agents.network_security_rule_templates import NetworkSecurityRuleTemplate
        templates = NetworkSecurityRuleTemplate.ALL_TEMPLATES
        if category:
            templates = [t for t in templates if t.get('category') == category]
        return templates
    
    @classmethod
    def get_all_templates_with_frontend(cls):
        """获取包含前端系统的所有模板"""
        from app.agents.frontend_enhancement_rule_templates import FrontendEnhancementRuleTemplate
        return cls.ALL_TEMPLATES + FrontendEnhancementRuleTemplate.ALL_TEMPLATES
    
    @classmethod
    def get_frontend_templates(cls, category: str = None):
        """获取前端系统规则模板"""
        from app.agents.frontend_enhancement_rule_templates import FrontendEnhancementRuleTemplate
        templates = FrontendEnhancementRuleTemplate.ALL_TEMPLATES
        if category:
            templates = [t for t in templates if t.get('category') == category]
        return templates


class RuleAutoGenerator:
    """规则自动生成器"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._generated_rules = {}
        from app.utils.db import DatabaseManager
        db = DatabaseManager()
        self._db_path = db.db_path
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表"""
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            # 规则模板表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rule_templates (
                    template_id TEXT PRIMARY KEY,
                    template_key TEXT,
                    name TEXT,
                    category TEXT,
                    conditions TEXT,
                    actions TEXT,
                    priority INTEGER DEFAULT 0,
                    description TEXT,
                    auto_apply INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')
            
            # 规则生成历史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rule_generation_history (
                    generation_id TEXT PRIMARY KEY,
                    template_key TEXT,
                    rule_id TEXT,
                    agent_code TEXT,
                    batch_id TEXT,
                    generation_type TEXT,
                    success INTEGER DEFAULT 0,
                    created_at TEXT,
                    details TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("[规则生成器] 数据库表初始化完成")
            
        except Exception as e:
            logger.error(f"[规则生成器] 初始化数据库失败: {e}")
    
    def generate_rules_from_template(self, template_key: str, 
                                     custom_params: Dict = None,
                                     agent_code: str = 'rule_generator',
                                     batch_id: str = None) -> Dict:
        """根据模板生成规则"""
        try:
            from app.agents.auto_rule_engine import get_rule_engine
            
            engine = get_rule_engine()
            if not engine:
                return {'success': False, 'error': '规则引擎未初始化'}
            
            # 查找模板
            template = None
            for t in SystemRuleTemplate.ALL_TEMPLATES:
                if t.get('template_key') == template_key:
                    template = t
                    break
            
            if not template:
                return {'success': False, 'error': f'模板 {template_key} 不存在'}
            
            # 应用自定义参数
            conditions = template['conditions']
            actions = template['actions']
            
            if custom_params:
                # 更新条件值
                for cond in conditions:
                    field = cond['field']
                    if field in custom_params:
                        cond['value'] = custom_params[field]
                
                # 更新动作参数
                for action in actions:
                    action_params = action.get('params', {})
                    action['params'].update(custom_params.get('action_params', {}))
            
            # 生成规则
            rule_id = engine.add_rule(
                name=template['name'],
                conditions=conditions,
                actions=actions,
                priority=template['priority'],
                description=template['description']
            )
            
            if not rule_id:
                return {'success': False, 'error': '规则生成失败'}
            
            # 记录生成历史
            generation_id = f"gen_{uuid.uuid4().hex[:8]}"
            self._save_generation_history(
                generation_id, template_key, rule_id, agent_code, 
                batch_id, 'template', True, {
                    'template': template,
                    'custom_params': custom_params
                }
            )
            
            # 保存模板到数据库
            self._save_template(template, rule_id)
            
            logger.info(f"[规则生成器] 根据模板 {template_key} 成功生成规则 {rule_id}")
            
            return {
                'success': True,
                'rule_id': rule_id,
                'generation_id': generation_id,
                'template_key': template_key,
                'rule_name': template['name']
            }
            
        except Exception as e:
            logger.error(f"[规则生成器] 生成规则失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def batch_generate_rules(self, category: str = None, 
                            agent_code: str = 'batch_rule_generator',
                            auto_apply: bool = True) -> Dict:
        """批量生成规则"""
        try:
            from app.agents.auto_rule_engine import get_rule_engine
            
            engine = get_rule_engine()
            if not engine:
                return {'success': False, 'error': '规则引擎未初始化'}
            
            batch_id = f"rule_batch_{uuid.uuid4().hex[:8]}"
            generated_rules = []
            failed_rules = []
            
            # 筛选模板
            templates = SystemRuleTemplate.ALL_TEMPLATES
            if category:
                templates = [t for t in templates if t.get('category') == category]
            
            for template in templates:
                try:
                    rule_id = engine.add_rule(
                        name=template['name'],
                        conditions=template['conditions'],
                        actions=template['actions'],
                        priority=template['priority'],
                        description=template['description']
                    )
                    
                    if rule_id:
                        generation_id = f"gen_{uuid.uuid4().hex[:8]}"
                        self._save_generation_history(
                            generation_id, template['template_key'], 
                            rule_id, agent_code, batch_id, 'batch', True,
                            {'template': template}
                        )
                        self._save_template(template, rule_id, auto_apply)
                        
                        generated_rules.append({
                            'rule_id': rule_id,
                            'template_key': template['template_key'],
                            'name': template['name'],
                            'category': template['category'],
                            'generation_id': generation_id
                        })
                    else:
                        failed_rules.append({
                            'template_key': template['template_key'],
                            'name': template['name'],
                            'error': '规则创建失败'
                        })
                        
                except Exception as e:
                    failed_rules.append({
                        'template_key': template['template_key'],
                        'name': template['name'],
                        'error': str(e)
                    })
            
            logger.info(f"[规则生成器] 批量生成完成: 成功 {len(generated_rules)} 个, 失败 {len(failed_rules)} 个")
            
            return {
                'success': True,
                'batch_id': batch_id,
                'generated_rules': generated_rules,
                'failed_rules': failed_rules,
                'total_generated': len(generated_rules),
                'total_failed': len(failed_rules),
                'agent_code': agent_code
            }
            
        except Exception as e:
            logger.error(f"[规则生成器] 批量生成规则失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def _save_generation_history(self, generation_id: str, template_key: str,
                                rule_id: str, agent_code: str, batch_id: str,
                                generation_type: str, success: bool, details: Dict):
        """保存生成历史到数据库"""
        try:
            import sqlite3
            
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO rule_generation_history VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                generation_id,
                template_key,
                rule_id,
                agent_code,
                batch_id,
                generation_type,
                1 if success else 0,
                datetime.now().isoformat(),
                json.dumps(details, ensure_ascii=False)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"[规则生成器] 保存生成历史失败: {e}")
    
    def _save_template(self, template: Dict, rule_id: str, auto_apply: bool = False):
        """保存模板到数据库"""
        try:
            import sqlite3
            
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO rule_templates VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                rule_id,
                template.get('template_key'),
                template.get('name'),
                template.get('category'),
                json.dumps(template.get('conditions', []), ensure_ascii=False),
                json.dumps(template.get('actions', []), ensure_ascii=False),
                template.get('priority', 0),
                template.get('description', ''),
                1 if auto_apply else 0,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"[规则生成器] 保存模板失败: {e}")
    
    def get_available_templates(self, category: str = None, include_exam: bool = False) -> Dict:
        """获取可用模板列表"""
        if include_exam:
            templates = SystemRuleTemplate.get_all_templates_with_exam()
            categories = ['performance', 'task_management', 'health', 'ai_collaboration', 'security', 'user_behavior',
                         'exam_management', 'question_management', 'student_behavior', 'exam_security', 'exam_performance']
        else:
            templates = SystemRuleTemplate.ALL_TEMPLATES
            categories = ['performance', 'task_management', 'health', 'ai_collaboration', 'security', 'user_behavior']
        
        if category:
            templates = [t for t in templates if t.get('category') == category]
        
        return {
            'success': True,
            'templates': templates,
            'total': len(templates),
            'categories': categories
        }
    
    def get_exam_templates(self, category: str = None) -> Dict:
        """获取考试系统规则模板"""
        templates = SystemRuleTemplate.get_exam_templates(category)
        
        return {
            'success': True,
            'templates': templates,
            'total': len(templates),
            'categories': ['exam_management', 'question_management', 'student_behavior', 'exam_security', 'exam_performance']
        }
    
    def generate_exam_rules(self, category: str = None, 
                           agent_code: str = 'exam_rule_generator',
                           auto_apply: bool = True) -> Dict:
        """生成考试系统规则"""
        try:
            from app.agents.auto_rule_engine import get_rule_engine
            
            engine = get_rule_engine()
            if not engine:
                return {'success': False, 'error': '规则引擎未初始化'}
            
            batch_id = f"exam_rule_batch_{uuid.uuid4().hex[:8]}"
            generated_rules = []
            failed_rules = []
            
            templates = SystemRuleTemplate.get_exam_templates(category)
            
            for template in templates:
                try:
                    rule_id = engine.add_rule(
                        name=template['name'],
                        conditions=template['conditions'],
                        actions=template['actions'],
                        priority=template['priority'],
                        description=template['description']
                    )
                    
                    if rule_id:
                        generation_id = f"gen_{uuid.uuid4().hex[:8]}"
                        self._save_generation_history(
                            generation_id, template['template_key'], 
                            rule_id, agent_code, batch_id, 'exam', True,
                            {'template': template}
                        )
                        self._save_template(template, rule_id, auto_apply)
                        
                        generated_rules.append({
                            'rule_id': rule_id,
                            'template_key': template['template_key'],
                            'name': template['name'],
                            'category': template['category'],
                            'generation_id': generation_id
                        })
                    else:
                        failed_rules.append({
                            'template_key': template['template_key'],
                            'name': template['name'],
                            'error': '规则创建失败'
                        })
                        
                except Exception as e:
                    failed_rules.append({
                        'template_key': template['template_key'],
                        'name': template['name'],
                        'error': str(e)
                    })
            
            logger.info(f"[规则生成器] 考试系统规则生成完成: 成功 {len(generated_rules)} 个, 失败 {len(failed_rules)} 个")
            
            return {
                'success': True,
                'batch_id': batch_id,
                'generated_rules': generated_rules,
                'failed_rules': failed_rules,
                'total_generated': len(generated_rules),
                'total_failed': len(failed_rules),
                'agent_code': agent_code,
                'category': category or 'all_exam'
            }
            
        except Exception as e:
            logger.error(f"[规则生成器] 生成考试系统规则失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_question_bank_templates(self, category: str = None) -> Dict:
        """获取题库系统规则模板"""
        templates = SystemRuleTemplate.get_question_bank_templates(category)
        
        return {
            'success': True,
            'templates': templates,
            'total': len(templates),
            'categories': ['question_management', 'bank_expansion', 'quality_assurance', 'statistics', 'ai_optimization']
        }
    
    def generate_question_bank_rules(self, category: str = None, 
                                     agent_code: str = 'question_bank_rule_generator',
                                     auto_apply: bool = True) -> Dict:
        """生成题库系统规则"""
        try:
            from app.agents.auto_rule_engine import get_rule_engine
            
            engine = get_rule_engine()
            if not engine:
                return {'success': False, 'error': '规则引擎未初始化'}
            
            batch_id = f"question_bank_rule_batch_{uuid.uuid4().hex[:8]}"
            generated_rules = []
            failed_rules = []
            
            templates = SystemRuleTemplate.get_question_bank_templates(category)
            
            for template in templates:
                try:
                    rule_id = engine.add_rule(
                        name=template['name'],
                        conditions=template['conditions'],
                        actions=template['actions'],
                        priority=template['priority'],
                        description=template['description']
                    )
                    
                    if rule_id:
                        generation_id = f"gen_{uuid.uuid4().hex[:8]}"
                        self._save_generation_history(
                            generation_id, template['template_key'], 
                            rule_id, agent_code, batch_id, 'question_bank', True,
                            {'template': template}
                        )
                        self._save_template(template, rule_id, auto_apply)
                        
                        generated_rules.append({
                            'rule_id': rule_id,
                            'template_key': template['template_key'],
                            'name': template['name'],
                            'category': template['category'],
                            'generation_id': generation_id
                        })
                    else:
                        failed_rules.append({
                            'template_key': template['template_key'],
                            'name': template['name'],
                            'error': '规则创建失败'
                        })
                        
                except Exception as e:
                    failed_rules.append({
                        'template_key': template['template_key'],
                        'name': template['name'],
                        'error': str(e)
                    })
            
            logger.info(f"[规则生成器] 题库系统规则生成完成: 成功 {len(generated_rules)} 个, 失败 {len(failed_rules)} 个")
            
            return {
                'success': True,
                'batch_id': batch_id,
                'generated_rules': generated_rules,
                'failed_rules': failed_rules,
                'total_generated': len(generated_rules),
                'total_failed': len(failed_rules),
                'agent_code': agent_code,
                'category': category or 'all_question_bank'
            }
            
        except Exception as e:
            logger.error(f"[规则生成器] 生成题库系统规则失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_network_security_templates(self, category: str = None) -> Dict:
        """获取网络层安全系统规则模板"""
        templates = SystemRuleTemplate.get_network_security_templates(category)
        
        return {
            'success': True,
            'templates': templates,
            'total': len(templates),
            'categories': ['firewall_security', 'ddos_protection', 'intrusion_detection', 
                          'ssl_tls_security', 'dns_security', 'vpn_tunnel_security',
                          'network_isolation', 'network_traffic_monitoring']
        }
    
    def generate_network_security_rules(self, category: str = None, 
                                       agent_code: str = 'network_security_rule_generator',
                                       auto_apply: bool = True) -> Dict:
        """生成网络层安全系统规则"""
        try:
            from app.agents.auto_rule_engine import get_rule_engine
            
            engine = get_rule_engine()
            if not engine:
                return {'success': False, 'error': '规则引擎未初始化'}
            
            batch_id = f"network_security_rule_batch_{uuid.uuid4().hex[:8]}"
            generated_rules = []
            failed_rules = []
            
            templates = SystemRuleTemplate.get_network_security_templates(category)
            
            for template in templates:
                try:
                    rule_id = engine.add_rule(
                        name=template['name'],
                        conditions=template['conditions'],
                        actions=template['actions'],
                        priority=template['priority'],
                        description=template['description']
                    )
                    
                    if rule_id:
                        generation_id = f"gen_{uuid.uuid4().hex[:8]}"
                        self._save_generation_history(
                            generation_id, template['template_key'], 
                            rule_id, agent_code, batch_id, 'network_security', True,
                            {'template': template}
                        )
                        self._save_template(template, rule_id, auto_apply)
                        
                        generated_rules.append({
                            'rule_id': rule_id,
                            'template_key': template['template_key'],
                            'name': template['name'],
                            'category': template['category'],
                            'generation_id': generation_id
                        })
                    else:
                        failed_rules.append({
                            'template_key': template['template_key'],
                            'name': template['name'],
                            'error': '规则创建失败'
                        })
                        
                except Exception as e:
                    failed_rules.append({
                        'template_key': template['template_key'],
                        'name': template['name'],
                        'error': str(e)
                    })
            
            logger.info(f"[规则生成器] 网络层安全系统规则生成完成: 成功 {len(generated_rules)} 个, 失败 {len(failed_rules)} 个")
            
            return {
                'success': True,
                'batch_id': batch_id,
                'generated_rules': generated_rules,
                'failed_rules': failed_rules,
                'total_generated': len(generated_rules),
                'total_failed': len(failed_rules),
                'agent_code': agent_code,
                'category': category or 'all_network_security'
            }
            
        except Exception as e:
            logger.error(f"[规则生成器] 生成网络层安全系统规则失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_frontend_templates(self, category: str = None) -> Dict:
        """获取前端系统规则模板"""
        templates = SystemRuleTemplate.get_frontend_templates(category)
        
        return {
            'success': True,
            'templates': templates,
            'total': len(templates),
            'categories': ['ui_performance', 'user_interaction', 'frontend_error', 
                          'page_load', 'responsive_design', 'frontend_security',
                          'user_experience', 'resource_management']
        }
    
    def generate_frontend_rules(self, category: str = None, 
                               agent_code: str = 'frontend_rule_generator',
                               auto_apply: bool = True) -> Dict:
        """生成前端系统规则"""
        try:
            from app.agents.auto_rule_engine import get_rule_engine
            
            engine = get_rule_engine()
            if not engine:
                return {'success': False, 'error': '规则引擎未初始化'}
            
            batch_id = f"frontend_rule_batch_{uuid.uuid4().hex[:8]}"
            generated_rules = []
            failed_rules = []
            
            templates = SystemRuleTemplate.get_frontend_templates(category)
            
            for template in templates:
                try:
                    rule_id = engine.add_rule(
                        name=template['name'],
                        conditions=template['conditions'],
                        actions=template['actions'],
                        priority=template['priority'],
                        description=template['description']
                    )
                    
                    if rule_id:
                        generation_id = f"gen_{uuid.uuid4().hex[:8]}"
                        self._save_generation_history(
                            generation_id, template['template_key'], 
                            rule_id, agent_code, batch_id, 'frontend', True,
                            {'template': template}
                        )
                        self._save_template(template, rule_id, auto_apply)
                        
                        generated_rules.append({
                            'rule_id': rule_id,
                            'template_key': template['template_key'],
                            'name': template['name'],
                            'category': template['category'],
                            'generation_id': generation_id
                        })
                    else:
                        failed_rules.append({
                            'template_key': template['template_key'],
                            'name': template['name'],
                            'error': '规则创建失败'
                        })
                        
                except Exception as e:
                    failed_rules.append({
                        'template_key': template['template_key'],
                        'name': template['name'],
                        'error': str(e)
                    })
            
            logger.info(f"[规则生成器] 前端系统规则生成完成: 成功 {len(generated_rules)} 个, 失败 {len(failed_rules)} 个")
            
            return {
                'success': True,
                'batch_id': batch_id,
                'generated_rules': generated_rules,
                'failed_rules': failed_rules,
                'total_generated': len(generated_rules),
                'total_failed': len(failed_rules),
                'agent_code': agent_code,
                'category': category or 'all_frontend'
            }
            
        except Exception as e:
            logger.error(f"[规则生成器] 生成前端系统规则失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_security_templates(self, category: str = None) -> Dict:
        """获取数据安全系统规则模板"""
        templates = SystemRuleTemplate.get_security_templates(category)
        
        return {
            'success': True,
            'templates': templates,
            'total': len(templates),
            'categories': ['access_security', 'encryption_security', 'integrity_security', 
                          'privacy_protection', 'leakage_prevention', 'security_audit',
                          'database_security', 'access_control']
        }
    
    def generate_security_rules(self, category: str = None, 
                               agent_code: str = 'security_rule_generator',
                               auto_apply: bool = True) -> Dict:
        """生成数据安全系统规则"""
        try:
            from app.agents.auto_rule_engine import get_rule_engine
            
            engine = get_rule_engine()
            if not engine:
                return {'success': False, 'error': '规则引擎未初始化'}
            
            batch_id = f"security_rule_batch_{uuid.uuid4().hex[:8]}"
            generated_rules = []
            failed_rules = []
            
            templates = SystemRuleTemplate.get_security_templates(category)
            
            for template in templates:
                try:
                    rule_id = engine.add_rule(
                        name=template['name'],
                        conditions=template['conditions'],
                        actions=template['actions'],
                        priority=template['priority'],
                        description=template['description']
                    )
                    
                    if rule_id:
                        generation_id = f"gen_{uuid.uuid4().hex[:8]}"
                        self._save_generation_history(
                            generation_id, template['template_key'], 
                            rule_id, agent_code, batch_id, 'security', True,
                            {'template': template}
                        )
                        self._save_template(template, rule_id, auto_apply)
                        
                        generated_rules.append({
                            'rule_id': rule_id,
                            'template_key': template['template_key'],
                            'name': template['name'],
                            'category': template['category'],
                            'generation_id': generation_id
                        })
                    else:
                        failed_rules.append({
                            'template_key': template['template_key'],
                            'name': template['name'],
                            'error': '规则创建失败'
                        })
                        
                except Exception as e:
                    failed_rules.append({
                        'template_key': template['template_key'],
                        'name': template['name'],
                        'error': str(e)
                    })
            
            logger.info(f"[规则生成器] 数据安全系统规则生成完成: 成功 {len(generated_rules)} 个, 失败 {len(failed_rules)} 个")
            
            return {
                'success': True,
                'batch_id': batch_id,
                'generated_rules': generated_rules,
                'failed_rules': failed_rules,
                'total_generated': len(generated_rules),
                'total_failed': len(failed_rules),
                'agent_code': agent_code,
                'category': category or 'all_security'
            }
            
        except Exception as e:
            logger.error(f"[规则生成器] 生成数据安全系统规则失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_generation_history(self, limit: int = 50) -> Dict:
        """获取生成历史"""
        try:
            import sqlite3
            
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM rule_generation_history ORDER BY created_at DESC LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            history = [dict(zip(columns, row)) for row in rows]
            
            conn.close()
            
            return {'success': True, 'data': history, 'total': len(history)}
            
        except Exception as e:
            logger.error(f"[规则生成器] 获取生成历史失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_rule_from_feedback(self, rule_id: str, feedback: Dict,
                                  agent_code: str = 'rule_optimizer') -> Dict:
        """根据反馈更新规则"""
        try:
            from app.agents.auto_rule_engine import get_rule_engine
            
            engine = get_rule_engine()
            if not engine:
                return {'success': False, 'error': '规则引擎未初始化'}
            
            # 根据反馈调整规则参数
            update_params = {}
            
            if feedback.get('trigger_frequency') == 'too_high':
                # 触发频率过高，降低优先级或调整条件阈值
                update_params['priority'] = feedback.get('new_priority', -1)
                
            if feedback.get('effectiveness') == 'low':
                # 效果不佳，调整动作参数
                update_params['actions'] = feedback.get('new_actions')
                
            if feedback.get('condition_match') == 'false_positive':
                # 条件误匹配，调整条件阈值
                update_params['conditions'] = feedback.get('new_conditions')
            
            # 更新规则
            result = engine.update_rule(rule_id, **update_params)
            
            # 记录更新历史
            generation_id = f"update_{uuid.uuid4().hex[:8]}"
            self._save_generation_history(
                generation_id, 'feedback_update', rule_id, agent_code,
                None, 'update', result.get('success', False), {
                    'feedback': feedback,
                    'update_params': update_params
                }
            )
            
            return {
                'success': result.get('success', False),
                'rule_id': rule_id,
                'generation_id': generation_id,
                'message': '规则已根据反馈更新'
            }
            
        except Exception as e:
            logger.error(f"[规则生成器] 更新规则失败: {e}")
            return {'success': False, 'error': str(e)}


# 单例实例
_rule_generator_instance = None

def get_rule_generator():
    """获取规则生成器实例"""
    global _rule_generator_instance
    
    if _rule_generator_instance is None:
        _rule_generator_instance = RuleAutoGenerator()
    
    return _rule_generator_instance


def init_rule_generator():
    """初始化规则生成器"""
    generator = get_rule_generator()
    logger.info("[规则生成器] 初始化完成")
    return generator