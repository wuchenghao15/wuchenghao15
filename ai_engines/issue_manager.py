# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
问题分类管理器
自动将安全发现分类到不同危险等级，支持批量处理
"""

import os
import json
import uuid
import sqlite3
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

SEVERITY_LEVELS = ['critical', 'high', 'medium', 'low']
SEVERITY_COLORS = {
    'critical': '#dc2626',
    'high': '#ea580c',
    'medium': '#ca8a04',
    'low': '#2563eb'
}

SEVERITY_DEFINITIONS = {
    'critical': {
        'description': 'Critical - 严重漏洞，可能导致系统被入侵、数据泄露或服务崩溃',
        'response_time': '24小时',
        'priority': 1,
        'impact': '严重'
    },
    'high': {
        'description': 'High - 高危漏洞，可能导致数据泄露或权限提升',
        'response_time': '72小时',
        'priority': 2,
        'impact': '较高'
    },
    'medium': {
        'description': 'Medium - 中危漏洞，可能被利用作为攻击跳板',
        'response_time': '7天',
        'priority': 3,
        'impact': '中等'
    },
    'low': {
        'description': 'Low - 低危漏洞，安全风险较低',
        'response_time': '30天',
        'priority': 4,
        'impact': '较低'
    }
}

ISSUE_CATEGORIES = {
    'hardcoded_credentials': {'name': '硬编码凭证', 'severity': 'critical'},
    'code_execution': {'name': '代码执行', 'severity': 'critical'},
    'command_injection': {'name': '命令注入', 'severity': 'critical'},
    'deserialization': {'name': '反序列化漏洞', 'severity': 'critical'},
    'sql_injection': {'name': 'SQL注入', 'severity': 'critical'},
    'xss': {'name': '跨站脚本', 'severity': 'high'},
    'csrf': {'name': '跨站请求伪造', 'severity': 'high'},
    'debug_enabled': {'name': '调试模式开启', 'severity': 'high'},
    'weak_secret_key': {'name': '弱密钥', 'severity': 'high'},
    'http_port_open': {'name': 'HTTP端口开放', 'severity': 'medium'},
    'env_file': {'name': '环境变量文件', 'severity': 'medium'},
    'db_permissions': {'name': '数据库权限', 'severity': 'medium'},
    'json_deserialization': {'name': 'JSON反序列化', 'severity': 'medium'},
    'parameter_injection': {'name': '参数注入', 'severity': 'medium'},
    'request_handling': {'name': '请求处理', 'severity': 'low'},
    'open_ports': {'name': '开放端口', 'severity': 'low'}
}

class IssueManager:
    """问题分类管理器"""

    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'issue_manager.db')
        self._create_tables()
        self.issues = []
        self.categorized_issues = defaultdict(list)

    def _create_tables(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS issue_triage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    issue_id TEXT UNIQUE,
                    finding_id TEXT,
                    category TEXT,
                    severity TEXT,
                    title TEXT,
                    description TEXT,
                    location TEXT,
                    recommendation TEXT,
                    status TEXT DEFAULT 'pending',
                    priority INTEGER,
                    response_deadline TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS issue_batches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id TEXT UNIQUE,
                    batch_name TEXT,
                    severity TEXT,
                    issue_count INTEGER,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS issue_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_id TEXT UNIQUE,
                    issue_id TEXT,
                    action_type TEXT,
                    action_description TEXT,
                    executed_by TEXT,
                    result TEXT,
                    executed_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            logger.info("[IssueManager] 数据库表创建完成")

    def load_findings(self, findings: List[Dict]) -> Dict[str, Any]:
        """加载安全发现并分类"""
        logger.info(f"[IssueManager] 加载 {len(findings)} 个安全发现...")
        
        self.issues = []
        self.categorized_issues = defaultdict(list)
        
        for finding in findings:
            categorized = self._categorize_finding(finding)
            self.issues.append(categorized)
            self.categorized_issues[categorized['severity']].append(categorized)
            self._save_issue(categorized)
        
        summary = self.get_summary()
        logger.info(f"[IssueManager] 分类完成: {summary}")
        return summary

    def _categorize_finding(self, finding: Dict) -> Dict[str, Any]:
        """分类单个安全发现"""
        category = finding.get('category', 'unknown')
        category_info = ISSUE_CATEGORIES.get(category, {'name': category, 'severity': 'medium'})
        
        severity = finding.get('severity', category_info['severity'])
        if severity not in SEVERITY_LEVELS:
            severity = 'medium'
        
        severity_def = SEVERITY_DEFINITIONS[severity]
        
        deadline = (datetime.now() + self._parse_response_time(severity_def['response_time'])).isoformat()
        
        return {
            'issue_id': f"issue_{uuid.uuid4().hex[:8]}",
            'finding_id': finding.get('finding_id', ''),
            'category': category,
            'category_name': category_info['name'],
            'severity': severity,
            'severity_color': SEVERITY_COLORS[severity],
            'title': f"{category_info['name']} - {finding.get('description', '')[:50]}",
            'description': finding.get('description', ''),
            'location': finding.get('location', ''),
            'recommendation': finding.get('recommendation', ''),
            'status': 'pending',
            'priority': severity_def['priority'],
            'response_deadline': deadline,
            'impact': severity_def['impact'],
            'response_time': severity_def['response_time'],
            'created_at': datetime.now().isoformat()
        }

    def _parse_response_time(self, response_time: str) -> float:
        """解析响应时间"""
        if '24h' in response_time:
            return timedelta(hours=24)
        elif '72h' in response_time:
            return timedelta(hours=72)
        elif '7天' in response_time:
            return timedelta(days=7)
        elif '30天' in response_time:
            return timedelta(days=30)
        return timedelta(days=7)

    def _save_issue(self, issue: Dict):
        """保存问题到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO issue_triage 
                    (issue_id, finding_id, category, severity, title, description, 
                     location, recommendation, status, priority, response_deadline)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    issue['issue_id'],
                    issue['finding_id'],
                    issue['category'],
                    issue['severity'],
                    issue['title'],
                    issue['description'],
                    issue['location'],
                    issue['recommendation'],
                    issue['status'],
                    issue['priority'],
                    issue['response_deadline']
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"[IssueManager] 保存问题失败: {e}")

    def get_summary(self) -> Dict[str, Any]:
        """获取问题汇总"""
        summary = {
            'total': len(self.issues),
            'by_severity': {},
            'by_category': {}
        }
        
        for severity in SEVERITY_LEVELS:
            count = len(self.categorized_issues[severity])
            summary['by_severity'][severity] = {
                'count': count,
                'issues': self.categorized_issues[severity]
            }
        
        category_counts = defaultdict(int)
        for issue in self.issues:
            category_counts[issue['category']] += 1
        summary['by_category'] = dict(category_counts)
        
        return summary

    def get_issues_by_severity(self, severity: str) -> List[Dict]:
        """按危险等级获取问题"""
        if severity not in SEVERITY_LEVELS:
            return []
        return self.categorized_issues[severity]

    def get_priority_issues(self, limit: int = 10) -> List[Dict]:
        """获取高优先级问题"""
        sorted_issues = sorted(self.issues, key=lambda x: x['priority'])
        return sorted_issues[:limit]

    def create_batch(self, severity: str, batch_name: str = None) -> Dict[str, Any]:
        """创建批量处理任务"""
        batch_id = f"batch_{uuid.uuid4().hex[:8]}"
        issues = self.get_issues_by_severity(severity)
        
        if not batch_name:
            batch_name = f"{severity.upper()}级问题处理批次"
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO issue_batches (batch_id, batch_name, severity, issue_count, status)
                    VALUES (?, ?, ?, ?, ?)
                ''', (batch_id, batch_name, severity, len(issues), 'pending'))
                conn.commit()
        except Exception as e:
            logger.error(f"[IssueManager] 创建批次失败: {e}")
            return {'success': False, 'error': str(e)}
        
        return {
            'success': True,
            'batch_id': batch_id,
            'batch_name': batch_name,
            'severity': severity,
            'issue_count': len(issues),
            'issues': issues
        }

    def update_issue_status(self, issue_id: str, status: str, action_description: str = '') -> bool:
        """更新问题状态"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE issue_triage SET status = ?, updated_at = ? WHERE issue_id = ?
                ''', (status, datetime.now().isoformat(), issue_id))
                
                if action_description:
                    action_id = f"action_{uuid.uuid4().hex[:8]}"
                    cursor.execute('''
                        INSERT INTO issue_actions (action_id, issue_id, action_type, action_description, result)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (action_id, issue_id, 'status_update', action_description, status))
                
                conn.commit()
            
            for issue in self.issues:
                if issue['issue_id'] == issue_id:
                    issue['status'] = status
                    break
            
            return True
        except Exception as e:
            logger.error(f"[IssueManager] 更新问题状态失败: {e}")
            return False

    def get_all_issues(self) -> List[Dict]:
        """获取所有问题"""
        return self.issues

    def get_issue_by_id(self, issue_id: str) -> Optional[Dict]:
        """根据ID获取问题"""
        for issue in self.issues:
            if issue['issue_id'] == issue_id:
                return issue
        return None

    def get_status_counts(self) -> Dict[str, int]:
        """获取各状态问题数量"""
        counts = defaultdict(int)
        for issue in self.issues:
            counts[issue['status']] += 1
        return dict(counts)

