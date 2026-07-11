#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统保护法则 - Security Rules Framework
MTSCOS AI Project v3.1
定义、执行和管理系统安全规则
"""

import os
import sys
import json
import sqlite3
import logging
import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('security_rules.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('security_rules')

class RuleType(Enum):
    """规则类型"""
    ACCESS_CONTROL = "access_control"           # 访问控制
    RATE_LIMITING = "rate_limiting"             # 速率限制
    INPUT_VALIDATION = "input_validation"        # 输入验证
    AUTHENTICATION = "authentication"            # 身份认证
    AUTHORIZATION = "authorization"              # 权限控制
    DATA_PROTECTION = "data_protection"        # 数据保护
    SYSTEM_INTEGRITY = "system_integrity"        # 系统完整性
    NETWORK_SECURITY = "network_security"        # 网络安全
    ENCRYPTION = "encryption"                   # 加密规则
    AUDIT = "audit"                            # 审计规则

class RuleSeverity(Enum):
    """规则严重级别"""
    CRITICAL = "critical"    # 严重（立即阻止）
    HIGH = "high"          # 高危（阻止并告警）
    MEDIUM = "medium"      # 中等（警告）
    LOW = "low"           # 低（记录）
    INFO = "info"         # 信息

class RuleAction(Enum):
    """规则动作"""
    ALLOW = "allow"              # 允许
    DENY = "deny"               # 拒绝
    BLOCK = "block"             # 阻止
    WARN = "warn"               # 警告
    LOG = "log"                 # 记录
    ALERT = "alert"             # 告警
    QUARANTINE = "quarantine"   # 隔离
    TERMINATE = "terminate"     # 终止

class RuleStatus(Enum):
    """规则状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TESTING = "testing"
    DEPRECATED = "deprecated"

@dataclass
class SecurityRule:
    """安全规则定义"""
    rule_id: str
    name: str
    description: str
    rule_type: RuleType
    severity: RuleSeverity
    action: RuleAction
    conditions: List[Dict[str, Any]]
    exceptions: List[str] = field(default_factory=list)
    enabled: bool = True
    priority: int = 50
    created_at: str = None
    updated_at: str = None
    hit_count: int = 0
    last_triggered: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'description': self.description,
            'rule_type': self.rule_type.value if isinstance(self.rule_type, Enum) else self.rule_type,
            'severity': self.severity.value if isinstance(self.severity, Enum) else self.severity,
            'action': self.action.value if isinstance(self.action, Enum) else self.action,
            'conditions': self.conditions,
            'exceptions': self.exceptions,
            'enabled': self.enabled,
            'priority': self.priority,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'hit_count': self.hit_count,
            'last_triggered': self.last_triggered
        }

@dataclass
class Violation:
    """违规记录"""
    violation_id: str
    rule_id: str
    rule_name: str
    severity: str
    action: str
    source_ip: str
    user_id: str
    target_resource: str
    details: Dict[str, Any]
    timestamp: str
    status: str = "open"
    resolved_by: str = None
    resolved_at: str = None

class RuleCondition:
    """规则条件"""
    
    @staticmethod
    def check_ip_range(ip: str, ranges: List[str]) -> bool:
        """检查IP是否在范围内"""
        try:
            import ipaddress
            ip_obj = ipaddress.ip_address(ip)
            for range_str in ranges:
                if '-' in range_str:
                    start, end = range_str.split('-')
                    start_ip = ipaddress.ip_address(start.strip())
                    end_ip = ipaddress.ip_address(end.strip())
                    if start_ip <= ip_obj <= end_ip:
                        return True
                else:
                    if ipaddress.ip_address(range_str) == ip_obj:
                        return True
            return False
        except:
            return False
    
    @staticmethod
    def check_rate_limit(count: int, limit: int, window: int) -> bool:
        """检查速率限制"""
        return count > limit
    
    @staticmethod
    def check_time_window(timestamp: datetime, start_hour: int, end_hour: int) -> bool:
        """检查时间窗口"""
        hour = timestamp.hour
        return not (start_hour <= hour < end_hour)
    
    @staticmethod
    def check_file_extension(filename: str, allowed_exts: List[str]) -> bool:
        """检查文件扩展名"""
        ext = os.path.splitext(filename)[1].lower()
        return ext not in [e.lower() for e in allowed_exts]
    
    @staticmethod
    def check_sql_keywords(text: str) -> bool:
        """检查SQL注入关键字"""
        sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'UNION', 'EXEC', 'EXECUTE']
        text_upper = text.upper()
        return any(keyword in text_upper for keyword in sql_keywords)
    
    @staticmethod
    def check_xss_patterns(text: str) -> bool:
        """检查XSS模式"""
        xss_patterns = ['<script', 'javascript:', 'onerror=', 'onload=', '<iframe']
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in xss_patterns)
    
    @staticmethod
    def check_path_traversal(path: str) -> bool:
        """检查路径遍历"""
        dangerous_patterns = ['../', '..\\', '/etc/passwd', 'C:\\Windows']
        return any(pattern in path for pattern in dangerous_patterns)

class SecurityRulesEngine:
    """安全规则引擎"""
    
    def __init__(self, db_path: str = "security_rules.db"):
        self.db_path = db_path
        self.rules: Dict[str, SecurityRule] = {}
        self.violations: List[Violation] = []
        self._init_database()
        self._load_rules()
        self._init_default_rules()
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rules (
                rule_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                rule_type TEXT,
                severity TEXT,
                action TEXT,
                conditions TEXT,
                exceptions TEXT,
                enabled INTEGER DEFAULT 1,
                priority INTEGER DEFAULT 50,
                created_at TEXT,
                updated_at TEXT,
                hit_count INTEGER DEFAULT 0,
                last_triggered TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS violations (
                violation_id TEXT PRIMARY KEY,
                rule_id TEXT,
                rule_name TEXT,
                severity TEXT,
                action TEXT,
                source_ip TEXT,
                user_id TEXT,
                target_resource TEXT,
                details TEXT,
                timestamp TEXT,
                status TEXT DEFAULT 'open',
                resolved_by TEXT,
                resolved_at TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rule_executions (
                execution_id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id TEXT,
                execution_time TEXT,
                success BOOLEAN,
                result TEXT,
                error_message TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_stats (
                stat_date TEXT PRIMARY KEY,
                total_violations INTEGER DEFAULT 0,
                critical_violations INTEGER DEFAULT 0,
                high_violations INTEGER DEFAULT 0,
                medium_violations INTEGER DEFAULT 0,
                low_violations INTEGER DEFAULT 0,
                blocked_requests INTEGER DEFAULT 0,
                allowed_requests INTEGER DEFAULT 0
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"安全规则数据库初始化完成: {self.db_path}")
    
    def _load_rules(self):
        """加载规则"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rules WHERE enabled = 1 ORDER BY priority DESC")
        rows = cursor.fetchall()
        conn.close()
        
        columns = ['rule_id', 'name', 'description', 'rule_type', 'severity', 'action',
                  'conditions', 'exceptions', 'enabled', 'priority', 'created_at',
                  'updated_at', 'hit_count', 'last_triggered']
        
        for row in rows:
            data = dict(zip(columns, row))
            data['conditions'] = json.loads(data['conditions'])
            data['exceptions'] = json.loads(data['exceptions'])
            data['enabled'] = bool(data['enabled'])
            
            rule = SecurityRule(
                rule_id=data['rule_id'],
                name=data['name'],
                description=data['description'],
                rule_type=RuleType(data['rule_type']),
                severity=RuleSeverity(data['severity']),
                action=RuleAction(data['action']),
                conditions=data['conditions'],
                exceptions=data['exceptions'],
                enabled=data['enabled'],
                priority=data['priority'],
                created_at=data['created_at'],
                updated_at=data['updated_at'],
                hit_count=data['hit_count'],
                last_triggered=data['last_triggered']
            )
            self.rules[rule.rule_id] = rule
        
        logger.info(f"已加载 {len(self.rules)} 条安全规则")
    
    def _init_default_rules(self):
        """初始化默认规则"""
        default_rules = [
            {
                'rule_id': 'SR-001',
                'name': 'SQL注入防护',
                'description': '检测和阻止SQL注入攻击',
                'rule_type': RuleType.INPUT_VALIDATION,
                'severity': RuleSeverity.CRITICAL,
                'action': RuleAction.BLOCK,
                'conditions': [{'type': 'sql_keywords', 'enabled': True}],
                'priority': 100
            },
            {
                'rule_id': 'SR-002',
                'name': 'XSS攻击防护',
                'description': '检测和阻止跨站脚本攻击',
                'rule_type': RuleType.INPUT_VALIDATION,
                'severity': RuleSeverity.CRITICAL,
                'action': RuleAction.BLOCK,
                'conditions': [{'type': 'xss_patterns', 'enabled': True}],
                'priority': 100
            },
            {
                'rule_id': 'SR-003',
                'name': '路径遍历防护',
                'description': '阻止目录遍历攻击',
                'rule_type': RuleType.INPUT_VALIDATION,
                'severity': RuleSeverity.HIGH,
                'action': RuleAction.BLOCK,
                'conditions': [{'type': 'path_traversal', 'enabled': True}],
                'priority': 90
            },
            {
                'rule_id': 'SR-004',
                'name': '登录失败限制',
                'description': '限制连续登录失败次数',
                'rule_type': RuleType.RATE_LIMITING,
                'severity': RuleSeverity.HIGH,
                'action': RuleAction.BLOCK,
                'conditions': [{'type': 'max_failures', 'value': 5, 'window': 300}],
                'priority': 80
            },
            {
                'rule_id': 'SR-005',
                'name': 'IP白名单保护',
                'description': '保护IP白名单不被未授权访问',
                'rule_type': RuleType.ACCESS_CONTROL,
                'severity': RuleSeverity.CRITICAL,
                'action': RuleAction.ALERT,
                'conditions': [{'type': 'ip_whitelist_access', 'enabled': True}],
                'priority': 95
            },
            {
                'rule_id': 'SR-006',
                'name': '敏感文件访问控制',
                'description': '限制对敏感文件的访问',
                'rule_type': RuleType.ACCESS_CONTROL,
                'severity': RuleSeverity.HIGH,
                'action': RuleAction.DENY,
                'conditions': [
                    {'type': 'file_extensions', 'values': ['.key', '.pem', '.env', '.sql']}
                ],
                'priority': 85
            },
            {
                'rule_id': 'SR-007',
                'name': '异常时间访问限制',
                'description': '限制非工作时间访问',
                'rule_type': RuleType.ACCESS_CONTROL,
                'severity': RuleSeverity.MEDIUM,
                'action': RuleAction.WARN,
                'conditions': [
                    {'type': 'time_window', 'start': 22, 'end': 6}
                ],
                'priority': 50
            },
            {
                'rule_id': 'SR-008',
                'name': '请求速率限制',
                'description': '防止API滥用和DDoS攻击',
                'rule_type': RuleType.RATE_LIMITING,
                'severity': RuleSeverity.HIGH,
                'action': RuleAction.BLOCK,
                'conditions': [
                    {'type': 'max_requests', 'value': 100, 'window': 60}
                ],
                'priority': 75
            },
            {
                'rule_id': 'SR-009',
                'name': '数据加密验证',
                'description': '验证敏感数据的加密状态',
                'rule_type': RuleType.DATA_PROTECTION,
                'severity': RuleSeverity.HIGH,
                'action': RuleAction.ALERT,
                'conditions': [
                    {'type': 'sensitive_fields', 'values': ['password', 'token', 'key', 'secret']}
                ],
                'priority': 80
            },
            {
                'rule_id': 'SR-010',
                'name': '文件上传安全',
                'description': '限制危险文件上传',
                'rule_type': RuleType.INPUT_VALIDATION,
                'severity': RuleSeverity.HIGH,
                'action': RuleAction.BLOCK,
                'conditions': [
                    {'type': 'blocked_extensions', 'values': ['.exe', '.sh', '.bat', '.cmd', '.php', '.asp']}
                ],
                'priority': 85
            },
            {
                'rule_id': 'SR-011',
                'name': '会话安全管理',
                'description': '防止会话劫持和固定',
                'rule_type': RuleType.AUTHENTICATION,
                'severity': RuleSeverity.HIGH,
                'action': RuleAction.TERMINATE,
                'conditions': [
                    {'type': 'session_fixation', 'enabled': True},
                    {'type': 'ip_change_detection', 'enabled': True}
                ],
                'priority': 90
            },
            {
                'rule_id': 'SR-012',
                'name': '审计日志完整性',
                'description': '确保关键操作被记录',
                'rule_type': RuleType.AUDIT,
                'severity': RuleSeverity.MEDIUM,
                'action': RuleAction.LOG,
                'conditions': [
                    {'type': 'operations', 'values': ['login', 'logout', 'delete', 'update', 'admin']}
                ],
                'priority': 60
            },
            {
                'rule_id': 'SR-013',
                'name': 'CSRF防护',
                'description': '防止跨站请求伪造',
                'rule_type': RuleType.AUTHENTICATION,
                'severity': RuleSeverity.HIGH,
                'action': RuleAction.BLOCK,
                'conditions': [
                    {'type': 'csrf_token', 'enabled': True}
                ],
                'priority': 85
            },
            {
                'rule_id': 'SR-014',
                'name': 'HTTP头部安全',
                'description': '设置安全HTTP头部',
                'rule_type': RuleType.NETWORK_SECURITY,
                'severity': RuleSeverity.MEDIUM,
                'action': RuleAction.LOG,
                'conditions': [
                    {'type': 'required_headers', 'values': ['X-Frame-Options', 'X-Content-Type-Options', 'X-XSS-Protection']}
                ],
                'priority': 50
            },
            {
                'rule_id': 'SR-015',
                'name': '密钥轮换策略',
                'description': '强制定期更换密钥',
                'rule_type': RuleType.ENCRYPTION,
                'severity': RuleSeverity.HIGH,
                'action': RuleAction.ALERT,
                'conditions': [
                    {'type': 'max_key_age_days', 'value': 90}
                ],
                'priority': 70
            }
        ]
        
        for rule_data in default_rules:
            if rule_data['rule_id'] not in self.rules:
                self.add_rule(SecurityRule(**rule_data))
                logger.info(f"添加默认规则: {rule_data['name']}")
    
    def add_rule(self, rule: SecurityRule) -> bool:
        """添加规则"""
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO rules 
                (rule_id, name, description, rule_type, severity, action, conditions, 
                 exceptions, enabled, priority, created_at, updated_at, hit_count, last_triggered)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rule.rule_id, rule.name, rule.description, rule.rule_type.value,
                rule.severity.value, rule.action.value, json.dumps(rule.conditions),
                json.dumps(rule.exceptions), int(rule.enabled), rule.priority,
                rule.created_at, rule.updated_at, rule.hit_count, rule.last_triggered
            ))
            conn.commit()
            conn.close()
            
            self.rules[rule.rule_id] = rule
            logger.info(f"规则已添加: {rule.name}")
            return True
        except Exception as e:
            logger.error(f"添加规则失败: {e}")
            return False
    
    def remove_rule(self, rule_id: str) -> bool:
        """删除规则"""
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM rules WHERE rule_id = ?", (rule_id,))
            conn.commit()
            conn.close()
            
            if rule_id in self.rules:
                del self.rules[rule_id]
            
            logger.info(f"规则已删除: {rule_id}")
            return True
        except Exception as e:
            logger.error(f"删除规则失败: {e}")
            return False
    
    def enable_rule(self, rule_id: str) -> bool:
        """启用规则"""
        rule = self.rules.get(rule_id)
        if rule:
            rule.enabled = True
            rule.updated_at = datetime.now().isoformat()
            return self.add_rule(rule)
        return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """禁用规则"""
        rule = self.rules.get(rule_id)
        if rule:
            rule.enabled = False
            rule.updated_at = datetime.now().isoformat()
            return self.add_rule(rule)
        return False
    
    def evaluate_conditions(self, rule: SecurityRule, context: Dict[str, Any]) -> Tuple[bool, str]:
        """评估规则条件"""
        for condition in rule.conditions:
            cond_type = condition.get('type')
            
            if cond_type == 'sql_keywords' and condition.get('enabled'):
                if 'input_text' in context:
                    if RuleCondition.check_sql_keywords(context['input_text']):
                        return True, "检测到SQL注入关键字"
            
            elif cond_type == 'xss_patterns' and condition.get('enabled'):
                if 'input_text' in context:
                    if RuleCondition.check_xss_patterns(context['input_text']):
                        return True, "检测到XSS攻击模式"
            
            elif cond_type == 'path_traversal' and condition.get('enabled'):
                if 'path' in context:
                    if RuleCondition.check_path_traversal(context['path']):
                        return True, "检测到路径遍历攻击"
            
            elif cond_type == 'max_failures':
                if context.get('failure_count', 0) >= condition.get('value', 5):
                    return True, f"登录失败次数超过限制: {condition.get('value')}"
            
            elif cond_type == 'file_extensions':
                if 'filename' in context:
                    ext = os.path.splitext(context['filename'])[1].lower()
                    if ext in [e.lower() for e in condition.get('values', [])]:
                        return True, f"检测到危险文件扩展名: {ext}"
            
            elif cond_type == 'blocked_extensions':
                if 'filename' in context:
                    ext = os.path.splitext(context['filename'])[1].lower()
                    if ext in [e.lower() for e in condition.get('values', [])]:
                        return True, f"检测到禁止的文件类型: {ext}"
            
            elif cond_type == 'time_window':
                start = condition.get('start', 22)
                end = condition.get('end', 6)
                if RuleCondition.check_time_window(datetime.now(), start, end):
                    return True, f"访问时间异常: {start}:00-{end}:00"
            
            elif cond_type == 'sensitive_fields':
                if 'data' in context:
                    for field_name in condition.get('values', []):
                        if field_name.lower() in str(context['data']).lower():
                            if not context.get('encrypted', False):
                                return True, f"敏感字段未加密: {field_name}"
            
            elif cond_type == 'csrf_token' and condition.get('enabled'):
                if not context.get('csrf_valid', True):
                    return True, "CSRF令牌验证失败"
            
            elif cond_type == 'ip_whitelist_access' and condition.get('enabled'):
                if context.get('ip_address') in context.get('whitelist', []):
                    if context.get('user_id') not in context.get('authorized_users', []):
                        return True, "未授权访问白名单资源"
        
        return False, ""
    
    def execute_rules(self, context: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """执行所有规则"""
        triggered_rules = []
        final_action = RuleAction.ALLOW
        should_block = False
        
        sorted_rules = sorted(self.rules.values(), key=lambda r: r.priority, reverse=True)
        
        for rule in sorted_rules:
            if not rule.enabled:
                continue
            
            if 'user_id' in context and context['user_id'] in rule.exceptions:
                continue
            
            violated, reason = self.evaluate_conditions(rule, context)
            
            if violated:
                rule.hit_count += 1
                rule.last_triggered = datetime.now().isoformat()
                
                violation = Violation(
                    violation_id=f"V-{int(time.time())}-{rule.rule_id}",
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    severity=rule.severity.value,
                    action=rule.action.value,
                    source_ip=context.get('ip_address', 'unknown'),
                    user_id=context.get('user_id', 'unknown'),
                    target_resource=context.get('resource', 'unknown'),
                    details={'reason': reason, 'context': context},
                    timestamp=datetime.now().isoformat()
                )
                self.record_violation(violation)
                
                triggered_rules.append({
                    'rule': rule,
                    'violation': violation,
                    'reason': reason
                })
                
                if rule.action == RuleAction.BLOCK or rule.action == RuleAction.DENY:
                    should_block = True
                    final_action = rule.action
                
                if rule.action == RuleAction.TERMINATE:
                    should_block = True
                    final_action = RuleAction.TERMINATE
                
                if rule.action == RuleAction.ALERT:
                    self.send_alert(rule, violation)
        
        return not should_block, triggered_rules
    
    def record_violation(self, violation: Violation):
        """记录违规"""
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO violations 
                (violation_id, rule_id, rule_name, severity, action, source_ip, 
                 user_id, target_resource, details, timestamp, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                violation.violation_id, violation.rule_id, violation.rule_name,
                violation.severity, violation.action, violation.source_ip,
                violation.user_id, violation.target_resource,
                json.dumps(violation.details), violation.timestamp, violation.status
            ))
            conn.commit()
            conn.close()
            
            self.violations.append(violation)
            logger.warning(f"⚠️ 安全违规: {violation.rule_name} - {violation.details.get('reason', '')}")
        except Exception as e:
            logger.error(f"记录违规失败: {e}")
    
    def send_alert(self, rule: SecurityRule, violation: Violation):
        """发送告警"""
        alert_message = f"""
🚨 安全告警
═══════════════════════════════════════
规则: {rule.name}
严重级别: {violation.severity.upper()}
来源IP: {violation.source_ip}
用户ID: {violation.user_id}
目标资源: {violation.target_resource}
时间: {violation.timestamp}
详情: {violation.details.get('reason', '')}
═══════════════════════════════════════
        """
        logger.warning(alert_message)
    
    def get_violations(self, limit: int = 100, status: str = None) -> List[Dict[str, Any]]:
        """获取违规记录"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        if status:
            cursor.execute("""
                SELECT * FROM violations 
                WHERE status = ?
                ORDER BY timestamp DESC LIMIT ?
            """, (status, limit))
        else:
            cursor.execute("""
                SELECT * FROM violations 
                ORDER BY timestamp DESC LIMIT ?
            """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        columns = ['violation_id', 'rule_id', 'rule_name', 'severity', 'action',
                  'source_ip', 'user_id', 'target_resource', 'details', 
                  'timestamp', 'status', 'resolved_by', 'resolved_at']
        
        violations = []
        for row in rows:
            data = dict(zip(columns, row))
            data['details'] = json.loads(data['details'])
            violations.append(data)
        
        return violations
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM violations")
        total_violations = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM violations WHERE severity = 'critical'")
        critical = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM violations WHERE severity = 'high'")
        high = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM violations WHERE severity = 'medium'")
        medium = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM violations WHERE severity = 'low'")
        low = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(hit_count) FROM rules")
        total_hits = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM rules WHERE enabled = 1")
        active_rules = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_violations': total_violations,
            'critical_violations': critical,
            'high_violations': high,
            'medium_violations': medium,
            'low_violations': low,
            'total_rule_hits': total_hits,
            'active_rules': active_rules,
            'total_rules': len(self.rules)
        }
    
    def generate_report(self) -> str:
        """生成安全报告"""
        stats = self.get_statistics()
        violations = self.get_violations(10)
        
        report = f"""
{'='*60}
系统安全报告
{'='*60}
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*60}

📊 统计概览
─────────────────────────────────────────────
总违规数:    {stats['total_violations']}
严重违规:    {stats['critical_violations']}
高危违规:    {stats['high_violations']}
中危违规:    {stats['medium_violations']}
低危违规:    {stats['low_violations']}
─────────────────────────────────────────────

📋 规则统计
─────────────────────────────────────────────
活跃规则:    {stats['active_rules']}
总规则数:    {stats['total_rules']}
规则触发:    {stats['total_rule_hits']} 次
─────────────────────────────────────────────

🚨 最近违规
─────────────────────────────────────────────
"""
        
        for v in violations[:10]:
            report += f"""
{v['rule_name']}
  级别: {v['severity']} | IP: {v['source_ip']} | 时间: {v['timestamp']}
"""
        
        report += f"""
{'='*60}
"""
        
        return report

def main():
    """测试主函数"""
    print("\n🛡️ 系统保护法则测试")
    print("=" * 60)
    
    engine = SecurityRulesEngine()
    
    print("\n📋 规则列表:")
    print(f"  加载规则数: {len(engine.rules)}")
    for rule_id, rule in list(engine.rules.items())[:5]:
        print(f"  - {rule.name} [{rule.severity.value}] [{rule.action.value}]")
    
    print("\n🔍 测试SQL注入检测:")
    test_context = {
        'input_text': "'; DROP TABLE users; --",
        'ip_address': '192.168.1.100',
        'user_id': 'test_user'
    }
    allowed, violations = engine.execute_rules(test_context)
    print(f"  允许访问: {allowed}")
    print(f"  触发规则: {len(violations)}")
    for v in violations:
        print(f"    - {v['rule'].name}: {v['reason']}")
    
    print("\n🔍 测试正常输入:")
    test_context = {
        'input_text': "Hello World",
        'ip_address': '192.168.1.100',
        'user_id': 'test_user'
    }
    allowed, violations = engine.execute_rules(test_context)
    print(f"  允许访问: {allowed}")
    print(f"  触发规则: {len(violations)}")
    
    print("\n📊 安全统计:")
    stats = engine.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n📝 生成安全报告:")
    report = engine.generate_report()
    print(report)
    
    print("=" * 60)
    print("✅ 系统保护法则测试完成")

if __name__ == '__main__':
    main()
