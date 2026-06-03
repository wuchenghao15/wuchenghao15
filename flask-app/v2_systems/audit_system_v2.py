# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
审计系统 V2.0 (Audit System)
增强版审计系统，支持多维度审计、实时监控、告警和报告生成
"""

import time
import uuid
import json
import logging
import threading
import sqlite3
from enum import Enum
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Set
import sys
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('audit_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AuditSystem')

class AuditCategory(Enum):
    """审计分类枚举"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    SYSTEM = "system"
    PERFORMANCE = "performance"
    SECURITY = "security"
    CONFIGURATION = "configuration"
    AUDIT = "audit"

class AuditAction(Enum):
    """审计操作枚举"""
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    GRANT = "grant"
    REVOKE = "revoke"
    CONFIG_CHANGE = "config_change"
    SYSTEM_START = "system_start"
    SYSTEM_SHUTDOWN = "system_shutdown"
    ERROR = "error"
    WARNING = "warning"
    ALERT = "alert"
    BACKUP = "backup"
    RESTORE = "restore"

class SeverityLevel(Enum):
    """严重级别枚举"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertType(Enum):
    """告警类型枚举"""
    FAILED_LOGIN = "failed_login"
    ACCESS_VIOLATION = "access_violation"
    CONFIG_CHANGE = "config_change"
    SYSTEM_ERROR = "system_error"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    PERFORMANCE_DEGRADE = "performance_degrade"

@dataclass
class AuditEvent:
    """审计事件"""
    event_id: str
    category: AuditCategory
    action: AuditAction
    user_id: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Dict = None
    severity: SeverityLevel = SeverityLevel.INFO
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: float = 0.0
    success: bool = True
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
        if self.timestamp == 0.0:
            self.timestamp = time.time()

@dataclass
class AlertRule:
    """告警规则"""
    rule_id: str
    name: str
    description: str
    conditions: Dict
    severity: SeverityLevel
    threshold: int = 1
    time_window: int = 300
    active: bool = True
    created_at: float = 0.0
    
    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()

@dataclass
class AlertInstance:
    """告警实例"""
    alert_id: str
    rule_id: str
    event_ids: List[str]
    message: str
    severity: SeverityLevel
    timestamp: float = 0.0
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[float] = None
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()

class AuditSystem:
    """增强版审计系统"""
    
    def __init__(self):
        """初始化审计系统"""
        self.events: Dict[str, AuditEvent] = {}
        self.alert_rules: Dict[str, AlertRule] = {}
        self.alerts: Dict[str, AlertInstance] = {}
        
        self.lock = threading.Lock()
        self.alert_lock = threading.Lock()
        
        self.event_buffer = deque(maxlen=1000)
        self.recent_events = deque(maxlen=100)
        
        self._init_database()
        self._load_default_alert_rules()
        
        self._start_monitor()
        self._start_alert_processor()
        
        logger.info("审计系统初始化完成")
    
    def _init_database(self):
        """初始化数据库"""
        try:
            self.db_conn = sqlite3.connect('audit_system.db', check_same_thread=False)
            cursor = self.db_conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    action TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    resource_type TEXT,
                    resource_id TEXT,
                    details TEXT,
                    severity TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp REAL NOT NULL,
                    success BOOLEAN DEFAULT TRUE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alert_rules (
                    rule_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    conditions TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    threshold INTEGER DEFAULT 1,
                    time_window INTEGER DEFAULT 300,
                    active BOOLEAN DEFAULT TRUE,
                    created_at REAL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    alert_id TEXT PRIMARY KEY,
                    rule_id TEXT NOT NULL,
                    event_ids TEXT,
                    message TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    acknowledged BOOLEAN DEFAULT FALSE,
                    acknowledged_by TEXT,
                    acknowledged_at REAL,
                    FOREIGN KEY (rule_id) REFERENCES alert_rules(rule_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_reports (
                    report_id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    data TEXT NOT NULL,
                    generated_at REAL NOT NULL,
                    period_start REAL,
                    period_end REAL
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_timestamp ON audit_events(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_user ON audit_events(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_category ON audit_events(category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)')
            
            self.db_conn.commit()
            logger.info("审计数据库初始化完成")
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
    
    def _load_default_alert_rules(self):
        """加载默认告警规则"""
        default_rules = [
            AlertRule(
                rule_id="rule_failed_login",
                name="登录失败告警",
                description="连续多次登录失败触发告警",
                conditions={"action": "login_failed", "category": "authentication"},
                severity=SeverityLevel.WARNING,
                threshold=3,
                time_window=300
            ),
            AlertRule(
                rule_id="rule_access_denied",
                name="访问拒绝告警",
                description="连续多次访问被拒绝触发告警",
                conditions={"action": "access_denied", "category": "authorization"},
                severity=SeverityLevel.WARNING,
                threshold=5,
                time_window=300
            ),
            AlertRule(
                rule_id="rule_config_change",
                name="配置变更告警",
                description="配置变更时触发告警",
                conditions={"action": "config_change", "category": "configuration"},
                severity=SeverityLevel.INFO,
                threshold=1,
                time_window=300
            ),
            AlertRule(
                rule_id="rule_system_error",
                name="系统错误告警",
                description="系统错误发生时触发告警",
                conditions={"action": "error", "category": "system"},
                severity=SeverityLevel.ERROR,
                threshold=1,
                time_window=60
            ),
            AlertRule(
                rule_id="rule_suspicious_activity",
                name="可疑活动告警",
                description="检测到可疑活动时触发告警",
                conditions={"action": "alert", "category": "security"},
                severity=SeverityLevel.CRITICAL,
                threshold=1,
                time_window=60
            )
        ]
        
        with self.lock:
            for rule in default_rules:
                if rule.rule_id not in self.alert_rules:
                    self.alert_rules[rule.rule_id] = rule
                    self._save_alert_rule(rule)
    
    def _save_alert_rule(self, rule: AlertRule):
        """保存告警规则到数据库"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO alert_rules
                (rule_id, name, description, conditions, severity, threshold, time_window, active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                rule.rule_id,
                rule.name,
                rule.description,
                json.dumps(rule.conditions),
                rule.severity.value,
                rule.threshold,
                rule.time_window,
                rule.active,
                rule.created_at
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"保存告警规则失败: {str(e)}")
    
    def log_event(self, category: AuditCategory, action: AuditAction, user_id: str,
                 resource_type: str = None, resource_id: str = None,
                 details: Dict = None, severity: SeverityLevel = SeverityLevel.INFO,
                 ip_address: str = None, user_agent: str = None, success: bool = True) -> str:
        """记录审计事件"""
        event_id = f"event_{uuid.uuid4().hex[:8]}"
        
        event = AuditEvent(
            event_id=event_id,
            category=category,
            action=action,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            severity=severity,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success
        )
        
        with self.lock:
            self.events[event_id] = event
            self.event_buffer.append(event)
            self.recent_events.append(event)
            
            if len(self.recent_events) > 100:
                self.recent_events.popleft()
        
        self._save_event(event)
        self._trigger_alerts(event)
        
        logger.debug(f"记录审计事件: {category.value}.{action.value} - {user_id}")
        return event_id
    
    def _save_event(self, event: AuditEvent):
        """保存事件到数据库"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO audit_events
                (event_id, category, action, user_id, resource_type, resource_id, 
                 details, severity, ip_address, user_agent, timestamp, success)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.event_id,
                event.category.value,
                event.action.value,
                event.user_id,
                event.resource_type,
                event.resource_id,
                json.dumps(event.details, ensure_ascii=False),
                event.severity.value,
                event.ip_address,
                event.user_agent,
                event.timestamp,
                event.success
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"保存审计事件失败: {str(e)}")
    
    def _trigger_alerts(self, event: AuditEvent):
        """触发告警检查"""
        with self.alert_lock:
            for rule_id, rule in self.alert_rules.items():
                if not rule.active:
                    continue
                
                if self._matches_rule(event, rule):
                    self._check_alert_threshold(rule, event)
    
    def _matches_rule(self, event: AuditEvent, rule: AlertRule) -> bool:
        """检查事件是否匹配规则"""
        conditions = rule.conditions
        
        if 'category' in conditions and event.category.value != conditions['category']:
            return False
        
        if 'action' in conditions and event.action.value != conditions['action']:
            return False
        
        if 'severity' in conditions and event.severity.value != conditions['severity']:
            return False
        
        if 'user_id' in conditions and event.user_id != conditions['user_id']:
            return False
        
        return True
    
    def _check_alert_threshold(self, rule: AlertRule, event: AuditEvent):
        """检查告警阈值"""
        window_start = time.time() - rule.time_window
        
        with self.lock:
            count = sum(
                1 for e in self.recent_events
                if e.timestamp >= window_start and self._matches_rule(e, rule)
            )
        
        if count >= rule.threshold:
            self._create_alert(rule, event)
    
    def _create_alert(self, rule: AlertRule, event: AuditEvent):
        """创建告警"""
        alert_id = f"alert_{uuid.uuid4().hex[:8]}"
        
        alert = AlertInstance(
            alert_id=alert_id,
            rule_id=rule.rule_id,
            event_ids=[event.event_id],
            message=f"{rule.name}: 检测到符合条件的事件",
            severity=rule.severity
        )
        
        with self.alert_lock:
            self.alerts[alert_id] = alert
        
        self._save_alert(alert)
        
        logger.warning(f"触发告警: {alert_id} - {alert.message}")
    
    def _save_alert(self, alert: AlertInstance):
        """保存告警到数据库"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO alerts
                (alert_id, rule_id, event_ids, message, severity, timestamp, 
                 acknowledged, acknowledged_by, acknowledged_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert.alert_id,
                alert.rule_id,
                json.dumps(alert.event_ids),
                alert.message,
                alert.severity.value,
                alert.timestamp,
                alert.acknowledged,
                alert.acknowledged_by,
                alert.acknowledged_at
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"保存告警失败: {str(e)}")
    
    def acknowledge_alert(self, alert_id: str, user_id: str) -> bool:
        """确认告警"""
        with self.alert_lock:
            alert = self.alerts.get(alert_id)
            if not alert:
                logger.error(f"告警不存在: {alert_id}")
                return False
            
            alert.acknowledged = True
            alert.acknowledged_by = user_id
            alert.acknowledged_at = time.time()
            
            cursor = self.db_conn.cursor()
            cursor.execute('''
                UPDATE alerts 
                SET acknowledged = ?, acknowledged_by = ?, acknowledged_at = ?
                WHERE alert_id = ?
            ''', (True, user_id, alert.acknowledged_at, alert_id))
            self.db_conn.commit()
        
        logger.info(f"告警已确认: {alert_id} by {user_id}")
        return True
    
    def get_events(self, filters: Dict = None, limit: int = 100) -> List[Dict]:
        """查询审计事件"""
        query = 'SELECT * FROM audit_events WHERE 1=1'
        params = []
        
        if filters:
            if 'category' in filters:
                query += ' AND category = ?'
                params.append(filters['category'])
            
            if 'action' in filters:
                query += ' AND action = ?'
                params.append(filters['action'])
            
            if 'user_id' in filters:
                query += ' AND user_id = ?'
                params.append(filters['user_id'])
            
            if 'severity' in filters:
                query += ' AND severity = ?'
                params.append(filters['severity'])
            
            if 'start_time' in filters:
                query += ' AND timestamp >= ?'
                params.append(filters['start_time'])
            
            if 'end_time' in filters:
                query += ' AND timestamp <= ?'
                params.append(filters['end_time'])
            
            if 'success' in filters:
                query += ' AND success = ?'
                params.append(filters['success'])
        
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        cursor = self.db_conn.cursor()
        cursor.execute(query, params)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "event_id": row[0],
                "category": row[1],
                "action": row[2],
                "user_id": row[3],
                "resource_type": row[4],
                "resource_id": row[5],
                "details": json.loads(row[6]) if row[6] else {},
                "severity": row[7],
                "ip_address": row[8],
                "user_agent": row[9],
                "timestamp": row[10],
                "success": row[11]
            })
        
        return results
    
    def get_alerts(self, acknowledged: bool = None, severity: SeverityLevel = None) -> List[Dict]:
        """获取告警列表"""
        query = 'SELECT * FROM alerts WHERE 1=1'
        params = []
        
        if acknowledged is not None:
            query += ' AND acknowledged = ?'
            params.append(acknowledged)
        
        if severity:
            query += ' AND severity = ?'
            params.append(severity.value)
        
        query += ' ORDER BY timestamp DESC'
        
        cursor = self.db_conn.cursor()
        cursor.execute(query, params)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "alert_id": row[0],
                "rule_id": row[1],
                "event_ids": json.loads(row[2]) if row[2] else [],
                "message": row[3],
                "severity": row[4],
                "timestamp": row[5],
                "acknowledged": row[6],
                "acknowledged_by": row[7],
                "acknowledged_at": row[8]
            })
        
        return results
    
    def add_alert_rule(self, name: str, description: str, conditions: Dict,
                       severity: SeverityLevel, threshold: int = 1, time_window: int = 300) -> str:
        """添加告警规则"""
        rule_id = f"rule_{uuid.uuid4().hex[:8]}"
        
        rule = AlertRule(
            rule_id=rule_id,
            name=name,
            description=description,
            conditions=conditions,
            severity=severity,
            threshold=threshold,
            time_window=time_window
        )
        
        with self.lock:
            self.alert_rules[rule_id] = rule
            self._save_alert_rule(rule)
        
        logger.info(f"添加告警规则: {name}")
        return rule_id
    
    def enable_alert_rule(self, rule_id: str) -> bool:
        """启用告警规则"""
        with self.lock:
            rule = self.alert_rules.get(rule_id)
            if not rule:
                return False
            
            rule.active = True
            self._save_alert_rule(rule)
        
        logger.info(f"启用告警规则: {rule_id}")
        return True
    
    def disable_alert_rule(self, rule_id: str) -> bool:
        """禁用告警规则"""
        with self.lock:
            rule = self.alert_rules.get(rule_id)
            if not rule:
                return False
            
            rule.active = False
            self._save_alert_rule(rule)
        
        logger.info(f"禁用告警规则: {rule_id}")
        return True
    
    def generate_report(self, report_type: str = "daily", 
                       start_time: float = None, end_time: float = None) -> Dict:
        """生成审计报告"""
        if start_time is None:
            start_time = time.time() - 86400
        
        if end_time is None:
            end_time = time.time()
        
        events = self.get_events({
            "start_time": start_time,
            "end_time": end_time
        }, limit=10000)
        
        stats = self._calculate_stats(events)
        
        report = {
            "report_id": f"report_{uuid.uuid4().hex[:8]}",
            "type": report_type,
            "generated_at": time.time(),
            "period_start": start_time,
            "period_end": end_time,
            "summary": stats,
            "event_summary": self._summarize_events(events),
            "alert_summary": self._summarize_alerts(start_time, end_time)
        }
        
        self._save_report(report)
        
        logger.info(f"生成审计报告: {report_type}")
        return report
    
    def _calculate_stats(self, events: List[Dict]) -> Dict:
        """计算统计信息"""
        by_category = defaultdict(int)
        by_action = defaultdict(int)
        by_severity = defaultdict(int)
        success_count = 0
        failure_count = 0
        
        for event in events:
            by_category[event['category']] += 1
            by_action[event['action']] += 1
            by_severity[event['severity']] += 1
            if event['success']:
                success_count += 1
            else:
                failure_count += 1
        
        return {
            "total_events": len(events),
            "by_category": dict(by_category),
            "by_action": dict(by_action),
            "by_severity": dict(by_severity),
            "success_count": success_count,
            "failure_count": failure_count,
            "success_rate": success_count / len(events) if events else 0
        }
    
    def _summarize_events(self, events: List[Dict]) -> Dict:
        """汇总事件"""
        top_users = defaultdict(int)
        top_resources = defaultdict(int)
        
        for event in events:
            top_users[event['user_id']] += 1
            if event['resource_type']:
                top_resources[event['resource_type']] += 1
        
        return {
            "top_users": dict(sorted(top_users.items(), key=lambda x: -x[1])[:10]),
            "top_resources": dict(sorted(top_resources.items(), key=lambda x: -x[1])[:10])
        }
    
    def _summarize_alerts(self, start_time: float, end_time: float) -> Dict:
        """汇总告警"""
        alerts = self.get_alerts()
        period_alerts = [a for a in alerts if start_time <= a['timestamp'] <= end_time]
        
        by_severity = defaultdict(int)
        acknowledged_count = sum(1 for a in period_alerts if a['acknowledged'])
        
        for alert in period_alerts:
            by_severity[alert['severity']] += 1
        
        return {
            "total_alerts": len(period_alerts),
            "by_severity": dict(by_severity),
            "acknowledged_count": acknowledged_count,
            "unacknowledged_count": len(period_alerts) - acknowledged_count
        }
    
    def _save_report(self, report: Dict):
        """保存报告到数据库"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO audit_reports
                (report_id, type, data, generated_at, period_start, period_end)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                report['report_id'],
                report['type'],
                json.dumps(report, ensure_ascii=False),
                report['generated_at'],
                report['period_start'],
                report['period_end']
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"保存报告失败: {str(e)}")
    
    def get_reports(self, report_type: str = None) -> List[Dict]:
        """获取报告列表"""
        query = 'SELECT * FROM audit_reports'
        params = []
        
        if report_type:
            query += ' WHERE type = ?'
            params.append(report_type)
        
        query += ' ORDER BY generated_at DESC LIMIT 100'
        
        cursor = self.db_conn.cursor()
        cursor.execute(query, params)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "report_id": row[0],
                "type": row[1],
                "data": json.loads(row[2]),
                "generated_at": row[3],
                "period_start": row[4],
                "period_end": row[5]
            })
        
        return results
    
    def get_stats(self) -> Dict:
        """获取审计统计信息"""
        recent_events = self.get_events(limit=1000)
        
        stats = {
            "total_events_stored": len(self.events),
            "recent_events_count": len(recent_events),
            "active_alert_rules": sum(1 for r in self.alert_rules.values() if r.active),
            "total_alert_rules": len(self.alert_rules),
            "active_alerts": len([a for a in self.alerts.values() if not a.acknowledged]),
            "total_alerts": len(self.alerts),
            "last_event_time": max(e['timestamp'] for e in recent_events) if recent_events else 0
        }
        
        return stats
    
    def export_data(self, output_file: str, start_time: float = None, 
                   end_time: float = None) -> Dict:
        """导出审计数据"""
        events = self.get_events({
            "start_time": start_time,
            "end_time": end_time
        }, limit=100000)
        
        data = {
            "export_time": time.time(),
            "start_time": start_time,
            "end_time": end_time,
            "event_count": len(events),
            "events": events
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"审计数据已导出: {output_file}")
        return {"file": output_file, "record_count": len(events)}
    
    def _start_monitor(self):
        """启动监控线程"""
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            name="audit_monitor",
            daemon=True
        )
        self.monitor_thread.start()
    
    def _monitor_loop(self):
        """监控循环"""
        while True:
            try:
                self._cleanup_old_events()
                time.sleep(300)
            except Exception as e:
                logger.error(f"监控线程错误: {str(e)}")
                time.sleep(60)
    
    def _cleanup_old_events(self):
        """清理旧事件"""
        max_age = time.time() - 30 * 24 * 3600
        
        with self.lock:
            old_events = [eid for eid, event in self.events.items() if event.timestamp < max_age]
            for eid in old_events[:100]:
                del self.events[eid]
        
        cursor = self.db_conn.cursor()
        cursor.execute('DELETE FROM audit_events WHERE timestamp < ?', (max_age,))
        self.db_conn.commit()
    
    def _start_alert_processor(self):
        """启动告警处理线程"""
        self.alert_processor = threading.Thread(
            target=self._alert_processor_loop,
            name="alert_processor",
            daemon=True
        )
        self.alert_processor.start()
    
    def _alert_processor_loop(self):
        """告警处理循环"""
        while True:
            try:
                self._process_pending_alerts()
                time.sleep(10)
            except Exception as e:
                logger.error(f"告警处理线程错误: {str(e)}")
                time.sleep(60)
    
    def _process_pending_alerts(self):
        """处理待处理告警"""
        pass


def test_audit_system():
    """测试审计系统"""
    print("审计系统 V2.0 测试")
    print("=" * 60)
    
    audit = AuditSystem()
    
    print("记录审计事件...")
    events = [
        ('authentication', 'login', 'user123', None, None, {}, 'info', '192.168.1.100', True),
        ('authorization', 'access_granted', 'user123', 'exam', 'exam001', {}, 'info', '192.168.1.100', True),
        ('data_modification', 'create', 'user123', 'question', 'q001', {'subject': 'math'}, 'info', '192.168.1.100', True),
        ('authentication', 'login_failed', 'hacker', None, None, {'reason': 'wrong password'}, 'warning', '10.0.0.1', False),
        ('authentication', 'login_failed', 'hacker', None, None, {'reason': 'wrong password'}, 'warning', '10.0.0.1', False),
        ('authentication', 'login_failed', 'hacker', None, None, {'reason': 'wrong password'}, 'warning', '10.0.0.1', False),
        ('system', 'error', 'system', None, None, {'error': 'connection failed'}, 'error', None, False),
        ('configuration', 'config_change', 'admin', 'setting', 'api.port', {'old_value': 5000, 'new_value': 5001}, 'info', '192.168.1.100', True)
    ]
    
    for category, action, user_id, resource_type, resource_id, details, severity, ip, success in events:
        audit.log_event(
            AuditCategory(category),
            AuditAction(action),
            user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            severity=SeverityLevel(severity),
            ip_address=ip,
            success=success
        )
    
    print(f"已记录 {len(events)} 个审计事件")
    
    print("\n查询审计事件:")
    filtered_events = audit.get_events({"category": "authentication"}, limit=5)
    for event in filtered_events:
        print(f"  {event['action']}: {event['user_id']} - {'成功' if event['success'] else '失败'}")
    
    print("\n获取告警列表:")
    alerts = audit.get_alerts()
    for alert in alerts:
        print(f"  {alert['severity'].upper()}: {alert['message']}")
    
    print("\n确认告警:")
    if alerts:
        audit.acknowledge_alert(alerts[0]['alert_id'], 'admin')
        print(f"  已确认告警: {alerts[0]['alert_id']}")
    
    print("\n获取统计信息:")
    stats = audit.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n生成日报:")
    report = audit.generate_report("daily")
    print(f"  报告ID: {report['report_id']}")
    print(f"  事件总数: {report['summary']['total_events']}")
    print(f"  成功率: {report['summary']['success_rate']:.2%}")
    
    print("\n导出审计数据:")
    export_result = audit.export_data("audit_export.json")
    print(f"  导出文件: {export_result['file']}")
    print(f"  记录数: {export_result['record_count']}")
    
    print("\n审计系统 V2.0 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_audit_system()