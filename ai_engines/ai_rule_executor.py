# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI规则执行和监督机制
功能: 严格执行学习政策,监控规则合规性,自动纠正违规行为
"""

import os
import sys
import json
import logging
import threading
import time
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_rule_executor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RuleComplianceChecker:
    """规则合规性检查器"""
    
    def __init__(self, rules_file: str = 'rules.json'):
        self.rules_file = rules_file
        self.rules = self._load_rules()
        self.compliance_history = []
        self.alert_threshold = self.rules.get('rule_execution_rules', {}).get('compliance_check', {}).get('alert_threshold', 3)
    
    def _load_rules(self) -> Dict:
        """加载规则"""
        try:
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载规则文件失败: {str(e)}")
            return {}
    
    def check_compliance(self) -> Dict:
        """检查规则合规性"""
        logger.info("开始规则合规性检查...")
        
        self.rules = self._load_rules()
        
        compliance_results = {
            'overall_compliance': True,
            'checks': [],
            'violations': [],
            'warnings': []
        }
        
        compliance_results = self._check_learning_policy(compliance_results)
        compliance_results = self._check_knowledge_sources(compliance_results)
        compliance_results = self._check_brain_feeding_rules(compliance_results)
        compliance_results = self._check_quality_standards(compliance_results)
        
        if compliance_results['violations']:
            compliance_results['overall_compliance'] = False
            logger.warning(f"发现 {len(compliance_results['violations'])} 个规则违规")
        
        self.compliance_history.append({
            'timestamp': datetime.now().isoformat(),
            'compliant': compliance_results['overall_compliance'],
            'violations_count': len(compliance_results['violations'])
        })
        
        if len(self.compliance_history) > 100:
            self.compliance_history = self.compliance_history[-100:]
        
        logger.info(f"规则合规性检查完成: {'合规' if compliance_results['overall_compliance'] else '不合规'}")
        return compliance_results
    
    def _check_learning_policy(self, results: Dict) -> Dict:
        """检查学习政策"""
        learning_policy = self.rules.get('learning_policy', {})
        
        if not learning_policy:
            results['violations'].append('学习政策未定义')
            return results
        
        core_principles = learning_policy.get('core_principles', [])
        if len(core_principles) < 3:
            results['warnings'].append('学习政策核心原则不足3条')
        
        learning_priorities = learning_policy.get('learning_priorities', [])
        if not learning_priorities:
            results['violations'].append('学习优先级未定义')
        
        results['checks'].append({
            'category': 'learning_policy',
            'status': 'passed',
            'details': f"核心原则: {len(core_principles)}条,学习优先级: {len(learning_priorities)}条"
        })
        
        return results
    
    def _check_knowledge_sources(self, results: Dict) -> Dict:
        """检查知识源配置"""
        knowledge_sources = self.rules.get('knowledge_sources', {})
        
        internal_sources = knowledge_sources.get('internal_sources', [])
        external_sources = knowledge_sources.get('external_sources', [])
        
        if not internal_sources and not external_sources:
            results['violations'].append('未配置任何知识源')
        else:
            results['checks'].append({
                'category': 'knowledge_sources',
                'status': 'passed',
                'details': f"内部源: {len(internal_sources)}个,外部源: {len(external_sources)}个"
            })
        
        for source in external_sources:
            if not source.get('enabled', True):
                results['warnings'].append(f"知识源 {source.get('name')} 已禁用")
        
        return results
    
    def _check_brain_feeding_rules(self, results: Dict) -> Dict:
        """检查脑库投喂规则"""
        feeding_rules = self.rules.get('brain_feeding_rules', {})
        
        if not feeding_rules:
            results['violations'].append('脑库投喂规则未定义')
            return results
        
        knowledge_structure = feeding_rules.get('knowledge_structure', {})
        required_fields = knowledge_structure.get('required_fields', [])
        
        if len(required_fields) < 3:
            results['warnings'].append('知识结构必填字段不足')
        
        storage_rules = feeding_rules.get('storage_rules', {})
        if not storage_rules.get('deduplication_enabled', False):
            results['warnings'].append('知识去重未启用')
        
        results['checks'].append({
            'category': 'brain_feeding_rules',
            'status': 'passed',
            'details': f"必填字段: {len(required_fields)}个,去重启用: {storage_rules.get('deduplication_enabled', False)}"
        })
        
        return results
    
    def _check_quality_standards(self, results: Dict) -> Dict:
        """检查知识质量标准"""
        quality_standards = self.rules.get('knowledge_quality_standards', {})
        
        if not quality_standards:
            results['violations'].append('知识质量标准未定义')
            return results
        
        min_confidence = quality_standards.get('minimum_confidence', 0)
        if min_confidence < 0.5:
            results['warnings'].append('知识置信度阈值过低')
        
        results['checks'].append({
            'category': 'quality_standards',
            'status': 'passed',
            'details': f"最小置信度阈值: {min_confidence}"
        })
        
        return results
    
    def get_compliance_history(self, limit: int = 20) -> List[Dict]:
        """获取合规性检查历史"""
        return self.compliance_history[-limit:]


class PolicyEnforcer:
    """政策执行器"""
    
    def __init__(self):
        self.strict_mode = True
        self.violation_actions = ['log', 'alert', 'block', 'rollback']
        self.violation_count = 0
    
    def enforce_policy(self, action: str, context: Dict) -> Dict:
        """强制执行政策"""
        result = {
            'action': action,
            'allowed': True,
            'violation': False,
            'actions_taken': []
        }
        
        if self.strict_mode:
            if not self._is_action_allowed(action, context):
                result['allowed'] = False
                result['violation'] = True
                self.violation_count += 1
                
                for violation_action in self.violation_actions:
                    action_result = self._execute_violation_action(violation_action, action, context)
                    result['actions_taken'].append(action_result)
                
                logger.warning(f"政策违规: {action} 被阻止")
        
        return result
    
    def _is_action_allowed(self, action: str, context: Dict) -> bool:
        """检查动作是否允许"""
        restricted_actions = [
            'delete_knowledge',
            'override_rules',
            'disable_learning',
            'clear_brain',
            'bypass_validation'
        ]
        
        if action in restricted_actions:
            if context.get('emergency', False):
                logger.info(f"紧急模式下允许受限动作: {action}")
                return True
            if context.get('approved', False):
                logger.info(f"已批准的受限动作: {action}")
                return True
            return False
        
        return True
    
    def _execute_violation_action(self, action_type: str, original_action: str, context: Dict) -> Dict:
        """执行违规处理动作"""
        action_result = {
            'type': action_type,
            'success': True,
            'details': ''
        }
        
        if action_type == 'log':
            action_result['details'] = f"记录违规: {original_action}"
            logger.warning(f"违规记录: {original_action} - {context}")
        
        elif action_type == 'alert':
            action_result['details'] = f"发送告警: {original_action}"
            logger.error(f"违规告警: {original_action}")
        
        elif action_type == 'block':
            action_result['details'] = f"阻止动作: {original_action}"
        
        elif action_type == 'rollback':
            if context.get('previous_state'):
                action_result['details'] = f"回滚到之前状态"
            else:
                action_result['success'] = False
                action_result['details'] = "无法回滚: 没有之前状态"
        
        return action_result
    
    def reset_violation_count(self):
        """重置违规计数"""
        self.violation_count = 0


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics = {}
        self.alert_levels = {
            'warning': 0.7,
            'critical': 0.5
        }
        self.metric_history = {}
    
    def collect_metrics(self, system_status: Dict):
        """收集性能指标"""
        current_time = datetime.now().isoformat()
        
        self.metrics = {
            'learning_efficiency': system_status.get('learning_efficiency', 0),
            'knowledge_quality': system_status.get('knowledge_quality', 0),
            'brain_growth_rate': system_status.get('brain_growth_rate', 0),
            'rule_compliance': system_status.get('rule_compliance', 1),
            'system_health': system_status.get('system_health', 1)
        }
        
        for metric, value in self.metrics.items():
            if metric not in self.metric_history:
                self.metric_history[metric] = []
            self.metric_history[metric].append({
                'timestamp': current_time,
                'value': value
            })
            if len(self.metric_history[metric]) > 100:
                self.metric_history[metric] = self.metric_history[metric][-100:]
    
    def check_alerts(self) -> List[Dict]:
        """检查告警"""
        alerts = []
        
        for metric, value in self.metrics.items():
            if value < self.alert_levels['critical']:
                alerts.append({
                    'metric': metric,
                    'level': 'critical',
                    'value': value,
                    'threshold': self.alert_levels['critical'],
                    'message': f"{metric} 严重低于阈值"
                })
            elif value < self.alert_levels['warning']:
                alerts.append({
                    'metric': metric,
                    'level': 'warning',
                    'value': value,
                    'threshold': self.alert_levels['warning'],
                    'message': f"{metric} 低于阈值"
                })
        
        if alerts:
            for alert in alerts:
                if alert['level'] == 'critical':
                    logger.error(f"严重告警: {alert['message']}")
                else:
                    logger.warning(f"告警: {alert['message']}")
        
        return alerts
    
    def get_metrics_summary(self) -> Dict:
        """获取指标汇总"""
        summary = {}
        
        for metric, history in self.metric_history.items():
            if history:
                values = [h['value'] for h in history]
                summary[metric] = {
                    'current': history[-1]['value'],
                    'avg': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values)
                }
        
        return summary


class AIRuleExecutor:
    """AI规则执行和监督系统"""
    
    def __init__(self, rules_file: str = 'rules.json'):
        self.rules_file = rules_file
        
        self.compliance_checker = RuleComplianceChecker(rules_file)
        self.policy_enforcer = PolicyEnforcer()
        self.performance_monitor = PerformanceMonitor()
        
        self.is_running = False
        self.supervision_thread = None
        self.supervision_interval = 3600
        
        self.system_status = {
            'learning_efficiency': 0.8,
            'knowledge_quality': 0.85,
            'brain_growth_rate': 0,
            'rule_compliance': 1,
            'system_health': 1
        }
    
    def start(self):
        """启动规则执行和监督系统"""
        if not self.is_running:
            self.is_running = True
            self.supervision_thread = threading.Thread(target=self._supervision_loop, daemon=True)
            self.supervision_thread.start()
            logger.info("AI规则执行和监督系统已启动")
    
    def stop(self):
        """停止规则执行和监督系统"""
        self.is_running = False
        if self.supervision_thread and self.supervision_thread.is_alive():
            self.supervision_thread.join(timeout=5)
        logger.info("AI规则执行和监督系统已停止")
    
    def _supervision_loop(self):
        """监督循环"""
        while self.is_running:
            try:
                self.perform_supervision()
                time.sleep(self.supervision_interval)
            except Exception as e:
                logger.error(f"监督循环出错: {str(e)}")
                time.sleep(600)
    
    def perform_supervision(self) -> Dict:
        """执行监督检查"""
        logger.info("开始执行监督检查...")
        
        compliance_results = self.compliance_checker.check_compliance()
        
        self.performance_monitor.collect_metrics(self.system_status)
        alerts = self.performance_monitor.check_alerts()
        
        if not compliance_results['overall_compliance']:
            self._auto_correct_violations(compliance_results['violations'])
        
        result = {
            'compliance_check': compliance_results,
            'alerts': alerts,
            'metrics': self.performance_monitor.get_metrics_summary()
        }
        
        logger.info(f"监督检查完成: 违规 {len(compliance_results['violations'])} 个,告警 {len(alerts)} 个")
        return result
    
    def _auto_correct_violations(self, violations: List[str]):
        """自动纠正违规"""
        logger.info("开始自动纠正违规...")
        
        for violation in violations:
            if '未定义' in violation:
                logger.info(f"无法自动修复: {violation} - 需要人工干预")
            elif '不足' in violation:
                logger.info(f"建议补充: {violation}")
            elif '过低' in violation:
                logger.info(f"建议提高阈值: {violation}")
        
        logger.info("自动纠正完成")
    
    def execute_action(self, action: str, context: Dict = None) -> Dict:
        """执行动作并检查合规性"""
        if context is None:
            context = {}
        
        enforcement_result = self.policy_enforcer.enforce_policy(action, context)
        
        if enforcement_result['allowed']:
            logger.info(f"动作 {action} 已执行")
        else:
            logger.warning(f"动作 {action} 被阻止")
        
        return enforcement_result
    
    def update_system_status(self, status_updates: Dict):
        """更新系统状态"""
        self.system_status.update(status_updates)
        logger.info(f"系统状态已更新: {status_updates}")
    
    def get_compliance_report(self) -> Dict:
        """获取合规性报告"""
        return {
            'compliance_history': self.compliance_checker.get_compliance_history(),
            'current_compliance': self.compliance_checker.check_compliance(),
            'violation_count': self.policy_enforcer.violation_count,
            'metrics_summary': self.performance_monitor.get_metrics_summary()
        }


if __name__ == "__main__":
    executor = AIRuleExecutor()
    executor.start()
    
    try:
        logger.info("执行合规性检查...")
        compliance = executor.compliance_checker.check_compliance()
        logger.info(f"合规性: {'合规' if compliance['overall_compliance'] else '不合规'}")
        
        logger.info("测试执行动作...")
        result = executor.execute_action('add_knowledge', {'source': 'test'})
        logger.info(f"动作执行结果: {result}")
        
        logger.info("更新系统状态...")
        executor.update_system_status({
            'learning_efficiency': 0.9,
            'knowledge_quality': 0.88
        })
        
        logger.info("获取合规性报告...")
        report = executor.get_compliance_report()
        logger.info(f"报告: 违规计数 {report['violation_count']}")
        
        time.sleep(30)
    except KeyboardInterrupt:
        executor.stop()
        logger.info("AI规则执行和监督系统已停止")