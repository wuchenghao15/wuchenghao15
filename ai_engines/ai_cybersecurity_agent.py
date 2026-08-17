#!/usr/bin/env python3
"""AI智能网络安全Agent"""

import os
import logging
import json
import re
from datetime import datetime
from typing import Dict, List, Any
from ai_engines.ai_employee_system import AIEmployee

logger = logging.getLogger(__name__)

class AICybersecurityAgent(AIEmployee):
    """AI网络安全Agent"""
    
    def __init__(self, employee_id: str, name: str = "AI网络安全专家"):
        super().__init__(employee_id, name, 'cybersecurity', 9)
        self.skills = [
            '入侵检测', '威胁分析', '安全监控',
            '防火墙管理', '入侵防御', '安全事件响应',
            '安全评估', '安全培训', '合规检查'
        ]
        self.threat_history = []
        self.total_threats = 0
        self.blocked_attempts = 0
    
    def detect_intrusion(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """检测入侵"""
        threats = []
        
        suspicious_patterns = [
            (r'^(192\.168\.[0-9]+\.[0-9]+)$', '内部IP访问外部', 'medium'),
            (r'^(10\.[0-9]+\.[0-9]+\.[0-9]+)$', '私有IP访问', 'medium'),
            (r'(\d{4,5})', '异常端口访问', 'high'),
            (r'admin|root|test', '常见用户名尝试', 'high'),
            (r'password|passwd|pwd', '密码字段访问', 'high'),
            (r'scan|probe|nmap', '端口扫描行为', 'critical'),
            (r'botnet|malware|virus', '恶意软件特征', 'critical'),
            (r'brute.*force|暴力破解', '暴力破解尝试', 'critical'),
            (r'sql.*inject|注入', 'SQL注入攻击', 'critical'),
            (r'xss|cross.*site', '跨站脚本攻击', 'high')
        ]
        
        log_content = str(network_data.get('log', ''))
        
        for pattern, description, severity in suspicious_patterns:
            matches = re.findall(pattern, log_content, re.IGNORECASE)
            if matches:
                threats.append({
                    'type': description,
                    'severity': severity,
                    'matches': len(matches),
                    'source_ip': network_data.get('source_ip', ''),
                    'target_ip': network_data.get('target_ip', '')
                })
                self.total_threats += 1
        
        return {'success': True, 'threats': threats, 'total_found': len(threats)}
    
    def analyze_threat(self, threat: Dict[str, Any]) -> Dict[str, Any]:
        """分析威胁"""
        risk_score = {
            'critical': 10,
            'high': 8,
            'medium': 5,
            'low': 2
        }.get(threat.get('severity', 'medium'), 5)
        
        return {
            'success': True,
            'analysis': {
                'threat_type': threat.get('type', ''),
                'severity': threat.get('severity', ''),
                'risk_score': risk_score,
                'impact': self._get_threat_impact(threat.get('severity', '')),
                'recommended_action': self._get_recommended_action(threat.get('type', ''))
            }
        }
    
    def _get_threat_impact(self, severity: str) -> str:
        impacts = {
            'critical': '可能导致系统被完全入侵，数据泄露或服务中断',
            'high': '可能导致敏感数据泄露或系统权限被获取',
            'medium': '可能导致部分系统功能异常或信息泄露',
            'low': '可能被用于信息收集或作为进一步攻击的跳板'
        }
        return impacts.get(severity, '影响未知')
    
    def _get_recommended_action(self, threat_type: str) -> str:
        actions = {
            'SQL注入攻击': '立即阻止来源IP，审查代码并修复SQL注入漏洞',
            '跨站脚本攻击': '阻止来源IP，对用户输入进行HTML转义',
            '暴力破解尝试': '临时封禁来源IP，实施账户锁定策略',
            '端口扫描行为': '封禁来源IP，配置防火墙规则',
            '恶意软件特征': '隔离受影响系统，进行全面病毒扫描',
            '内部IP访问外部': '审查网络配置，确认是否为合法行为',
            '常见用户名尝试': '实施账户锁定策略，使用多因素认证'
        }
        return actions.get(threat_type, '请根据安全策略采取相应措施')
    
    def manage_firewall(self, action: str, **kwargs) -> Dict[str, Any]:
        """防火墙管理"""
        actions = {
            'block_ip': self._block_ip,
            'allow_ip': self._allow_ip,
            'add_rule': self._add_rule,
            'remove_rule': self._remove_rule,
            'list_rules': self._list_rules
        }
        
        if action in actions:
            return actions[action](**kwargs)
        return {'success': False, 'message': f'未知操作: {action}'}
    
    def _block_ip(self, **kwargs) -> Dict[str, Any]:
        ip = kwargs.get('ip', '')
        reason = kwargs.get('reason', '')
        
        block_record = {
            'ip': ip,
            'action': 'block',
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }
        
        self.threat_history.append(block_record)
        self.blocked_attempts += 1
        
        return {'success': True, 'message': f'IP {ip} 已被封禁', 'block_record': block_record}
    
    def _allow_ip(self, **kwargs) -> Dict[str, Any]:
        ip = kwargs.get('ip', '')
        
        allow_record = {
            'ip': ip,
            'action': 'allow',
            'timestamp': datetime.now().isoformat()
        }
        
        self.threat_history.append(allow_record)
        
        return {'success': True, 'message': f'IP {ip} 已被允许', 'allow_record': allow_record}
    
    def _add_rule(self, **kwargs) -> Dict[str, Any]:
        rule = {
            'rule_id': f'rule_{datetime.now().timestamp()}',
            'name': kwargs.get('name', ''),
            'action': kwargs.get('action', 'block'),
            'protocol': kwargs.get('protocol', 'tcp'),
            'port': kwargs.get('port', ''),
            'source_ip': kwargs.get('source_ip', ''),
            'description': kwargs.get('description', ''),
            'created_at': datetime.now().isoformat()
        }
        
        self.threat_history.append(rule)
        
        return {'success': True, 'rule': rule}
    
    def _remove_rule(self, **kwargs) -> Dict[str, Any]:
        rule_id = kwargs.get('rule_id', '')
        for i, record in enumerate(self.threat_history):
            if record.get('rule_id') == rule_id:
                del self.threat_history[i]
                return {'success': True, 'message': '规则已删除'}
        return {'success': False, 'message': '规则不存在'}
    
    def _list_rules(self, **kwargs) -> Dict[str, Any]:
        rules = [r for r in self.threat_history if 'rule_id' in r]
        return {'success': True, 'rules': rules, 'count': len(rules)}
    
    def respond_to_incident(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """响应安全事件"""
        response = {
            'incident_id': incident.get('incident_id', f'incident_{datetime.now().timestamp()}'),
            'type': incident.get('type', ''),
            'severity': incident.get('severity', 'medium'),
            'status': 'investigating',
            'response_actions': [],
            'timestamp': datetime.now().isoformat()
        }
        
        if incident.get('severity') == 'critical':
            response['status'] = 'contained'
            response['response_actions'] = [
                '立即隔离受影响系统',
                '通知安全团队',
                '启动应急预案',
                '收集证据进行分析'
            ]
        elif incident.get('severity') == 'high':
            response['status'] = 'investigating'
            response['response_actions'] = [
                '监控受影响系统',
                '收集相关日志',
                '评估影响范围',
                '准备修复方案'
            ]
        
        self.threat_history.append(response)
        
        return {'success': True, 'response': response}
    
    def generate_security_report(self) -> Dict[str, Any]:
        """生成安全报告"""
        critical = sum(1 for t in self.threat_history if isinstance(t, dict) and t.get('severity') == 'critical')
        high = sum(1 for t in self.threat_history if isinstance(t, dict) and t.get('severity') == 'high')
        
        return {
            'success': True,
            'report': {
                'generated_at': datetime.now().isoformat(),
                'total_threats_detected': self.total_threats,
                'blocked_attempts': self.blocked_attempts,
                'critical_incidents': critical,
                'high_incidents': high,
                'security_level': self._get_security_level()
            }
        }
    
    def _get_security_level(self) -> str:
        if self.total_threats > 100 or self.blocked_attempts > 50:
            return '警戒'
        elif self.total_threats > 50:
            return '注意'
        else:
            return '正常'
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'total_threats': self.total_threats,
            'blocked_attempts': self.blocked_attempts,
            'threat_history_count': len(self.threat_history),
            'employee_id': self.employee_id,
            'name': self.name,
            'employee_type': self.employee_type
        }