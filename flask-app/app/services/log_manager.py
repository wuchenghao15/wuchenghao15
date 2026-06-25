# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
日志管理模块,用于集中管理和分析系统日志
增强版：集成审计系统功能，支持多维度审计、实时监控、告警和报告生成
"""

import os
import sys
import logging
import threading
import time
import uuid
import json
import sqlite3
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
from typing import Dict, List, Any, Optional
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class AuditCategory(Enum):
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
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(Enum):
    FAILED_LOGIN = "failed_login"
    ACCESS_VIOLATION = "access_violation"
    CONFIG_CHANGE = "config_change"
    SYSTEM_ERROR = "system_error"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    PERFORMANCE_DEGRADE = "performance_degrade"


class LogManager:
    """日志管理模块 - 增强版"""

    def __init__(self):
        """初始化日志管理器"""
        self.logger = logging.getLogger(__name__)

        self.config = {
            'log_dir': os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs'),
            'log_file': 'system.log',
            'max_log_size': 10 * 1024 * 1024,
            'backup_count': 5,
            'log_level': logging.INFO,
            'analysis_interval': 3600
        }

        if not os.path.exists(self.config['log_dir']):
            os.makedirs(self.config['log_dir'])

        self.logs = []
        self.log_lock = threading.RLock()

        self.analysis_results = {
            'error_count': 0,
            'warning_count': 0,
            'info_count': 0,
            'debug_count': 0,
            'error_types': {},
            'warning_types': {},
            'info_types': {},
            'debug_types': {},
            'time_distribution': {},
            'module_distribution': {},
            'trends': []
        }

        self.analysis_thread = None
        self.running = False

        self._init_audit_database()
        self._load_default_alert_rules()
        self._start_monitor()
        self._start_alert_processor()

        self._setup_logging()

        self.logger.info("日志管理器已初始化")

    def _init_audit_database(self):
        """初始化审计数据库"""
        try:
            db_path = os.path.join(self.config['log_dir'], 'audit.db')
            self.db_conn = sqlite3.connect(db_path, check_same_thread=False)
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
            self.logger.info("审计数据库初始化完成")

            self.events: Dict[str, Any] = {}
            self.alert_rules: Dict[str, Any] = {}
            self.alerts: Dict[str, Any] = {}
            self.alert_lock = threading.Lock()
            self.event_buffer = deque(maxlen=1000)
            self.recent_events = deque(maxlen=100)

        except Exception as e:
            self.logger.error(f"审计数据库初始化失败: {str(e)}")

    def _load_default_alert_rules(self):
        """加载默认告警规则"""
        default_rules = [
            {
                'rule_id': 'rule_failed_login',
                'name': '登录失败告警',
                'description': '连续多次登录失败触发告警',
                'conditions': {'action': 'login_failed', 'category': 'authentication'},
                'severity': 'warning',
                'threshold': 3,
                'time_window': 300
            },
            {
                'rule_id': 'rule_access_denied',
                'name': '访问拒绝告警',
                'description': '连续多次访问被拒绝触发告警',
                'conditions': {'action': 'access_denied', 'category': 'authorization'},
                'severity': 'warning',
                'threshold': 5,
                'time_window': 300
            },
            {
                'rule_id': 'rule_config_change',
                'name': '配置变更告警',
                'description': '配置变更时触发告警',
                'conditions': {'action': 'config_change', 'category': 'configuration'},
                'severity': 'info',
                'threshold': 1,
                'time_window': 300
            },
            {
                'rule_id': 'rule_system_error',
                'name': '系统错误告警',
                'description': '系统错误发生时触发告警',
                'conditions': {'action': 'error', 'category': 'system'},
                'severity': 'error',
                'threshold': 1,
                'time_window': 60
            },
            {
                'rule_id': 'rule_suspicious_activity',
                'name': '可疑活动告警',
                'description': '检测到可疑活动时触发告警',
                'conditions': {'action': 'alert', 'category': 'security'},
                'severity': 'critical',
                'threshold': 1,
                'time_window': 60
            }
        ]

        with self.log_lock:
            for rule in default_rules:
                if rule['rule_id'] not in self.alert_rules:
                    self.alert_rules[rule['rule_id']] = rule
                    self._save_alert_rule(rule)

    def _save_alert_rule(self, rule: Dict):
        """保存告警规则到数据库"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO alert_rules
                (rule_id, name, description, conditions, severity, threshold, time_window, active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                rule['rule_id'],
                rule['name'],
                rule['description'],
                json.dumps(rule['conditions']),
                rule['severity'],
                rule['threshold'],
                rule['time_window'],
                rule.get('active', True),
                rule.get('created_at', time.time())
            ))
            self.db_conn.commit()
        except Exception as e:
            self.logger.error(f"保存告警规则失败: {str(e)}")

    def _setup_logging(self):
        """设置日志记录器"""
        log_file = os.path.join(self.config['log_dir'], self.config['log_file'])

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(self.config['log_level'])

        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)

        self.logger.info(f"日志配置完成,日志文件: {log_file}")

    def start(self):
        """启动日志管理器"""
        if self.running:
            self.logger.warning("日志管理器已经在运行中")
            return

        self.logger.info("正在启动日志管理器...")
        self.running = True

        self.analysis_thread = threading.Thread(target=self._analysis_loop, daemon=True)
        self.analysis_thread.start()
        self.logger.info("日志分析线程已启动")

        self.logger.info("日志管理器启动成功")

    def stop(self):
        """停止日志管理器"""
        if not self.running:
            self.logger.warning("日志管理器已经停止")
            return

        self.running = False

        if self.analysis_thread:
            self.analysis_thread.join(timeout=5)
            self.logger.info("日志分析线程已停止")

        self.logger.info("日志管理器已停止")

    def _analysis_loop(self):
        """分析循环"""
        while self.running:
            self.analyze_logs()
            time.sleep(self.config['analysis_interval'])

    def analyze_logs(self):
        """分析日志"""
        self.logger.info("开始分析日志...")

        try:
            log_file = os.path.join(self.config['log_dir'], self.config['log_file'])

            if not os.path.exists(log_file):
                self.logger.warning("日志文件不存在")
                return

            with open(log_file, 'r', encoding='utf-8') as f:
                log_lines = f.readlines()

            analysis_results = {
                'error_count': 0,
                'warning_count': 0,
                'info_count': 0,
                'debug_count': 0,
                'error_types': {},
                'warning_types': {},
                'info_types': {},
                'debug_types': {},
                'time_distribution': {},
                'module_distribution': {}
            }

            log_pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (.*?) - (ERROR|WARNING|INFO|DEBUG) - (.*)$'

            for line in log_lines:
                match = re.match(log_pattern, line)
                if match:
                    timestamp, module, level, message = match.groups()

                    if level == 'ERROR':
                        analysis_results['error_count'] += 1
                        error_type = self._extract_error_type(message)
                        analysis_results['error_types'][error_type] = analysis_results['error_types'].get(error_type, 0) + 1
                    elif level == 'WARNING':
                        analysis_results['warning_count'] += 1
                        warning_type = self._extract_warning_type(message)
                        analysis_results['warning_types'][warning_type] = analysis_results['warning_types'].get(warning_type, 0) + 1
                    elif level == 'INFO':
                        analysis_results['info_count'] += 1
                        info_type = self._extract_info_type(message)
                        analysis_results['info_types'][info_type] = analysis_results['info_types'].get(info_type, 0) + 1
                    elif level == 'DEBUG':
                        analysis_results['debug_count'] += 1
                        debug_type = self._extract_debug_type(message)
                        analysis_results['debug_types'][debug_type] = analysis_results['debug_types'].get(debug_type, 0) + 1

                    analysis_results['module_distribution'][module] = analysis_results['module_distribution'].get(module, 0) + 1

                    hour = timestamp.split(' ')[1].split(':')[0]
                    analysis_results['time_distribution'][hour] = analysis_results['time_distribution'].get(hour, 0) + 1

            with self.log_lock:
                self.analysis_results = analysis_results

            self.logger.info(f"日志分析完成,错误: {analysis_results['error_count']}, 警告: {analysis_results['warning_count']}, 信息: {analysis_results['info_count']}")
        except Exception as e:
            self.logger.error(f"分析日志失败: {str(e)}")

    def _extract_error_type(self, message: str) -> str:
        """提取错误类型"""
        error_patterns = {
            'ImportError': r'ImportError',
            'KeyError': r'KeyError',
            'AttributeError': r'AttributeError',
            'ValueError': r'ValueError',
            'TypeError': r'TypeError',
            'IOError': r'IOError',
            'FileNotFoundError': r'FileNotFoundError',
            'ConnectionError': r'ConnectionError',
            'TimeoutError': r'TimeoutError',
            'DatabaseError': r'DatabaseError',
            'OtherError': r'.*'
        }

        for error_type, pattern in error_patterns.items():
            if re.search(pattern, message):
                return error_type
        return 'OtherError'

    def _extract_warning_type(self, message: str) -> str:
        """提取警告类型"""
        if 'deprecated' in message.lower():
            return 'DeprecationWarning'
        elif 'performance' in message.lower():
            return 'PerformanceWarning'
        else:
            return 'GeneralWarning'

    def _extract_info_type(self, message: str) -> str:
        """提取信息类型"""
        if 'started' in message.lower():
            return 'StartInfo'
        elif 'completed' in message.lower():
            return 'CompletionInfo'
        else:
            return 'GeneralInfo'

    def _extract_debug_type(self, message: str) -> str:
        """提取调试类型"""
        return 'GeneralDebug'

    def get_analysis_results(self) -> Dict[str, Any]:
        """获取分析结果"""
        with self.log_lock:
            return self.analysis_results.copy()

    def log_event(self, level: str, message: str, module: str = None):
        """记录日志事件"""
        if level == 'ERROR':
            self.logger.error(f"[{module}] {message}" if module else message)
        elif level == 'WARNING':
            self.logger.warning(f"[{module}] {message}" if module else message)
        elif level == 'INFO':
            self.logger.info(f"[{module}] {message}" if module else message)
        elif level == 'DEBUG':
            self.logger.debug(f"[{module}] {message}" if module else message)

    def log_audit_event(self, category: str, action: str, user_id: str,
                       resource_type: str = None, resource_id: str = None,
                       details: Dict = None, severity: str = 'info',
                       ip_address: str = None, user_agent: str = None, success: bool = True) -> str:
        """记录审计事件"""
        event_id = f"event_{uuid.uuid4().hex[:8]}"

        event = {
            'event_id': event_id,
            'category': category,
            'action': action,
            'user_id': user_id,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'details': details or {},
            'severity': severity,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'timestamp': time.time(),
            'success': success
        }

        with self.log_lock:
            self.events[event_id] = event
            self.event_buffer.append(event)
            self.recent_events.append(event)

        self._save_audit_event(event)
        self._trigger_alerts(event)

        self.logger.debug(f"记录审计事件: {category}.{action} - {user_id}")
        return event_id

    def _save_audit_event(self, event: Dict):
        """保存审计事件到数据库"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO audit_events
                (event_id, category, action, user_id, resource_type, resource_id, 
                 details, severity, ip_address, user_agent, timestamp, success)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event['event_id'],
                event['category'],
                event['action'],
                event['user_id'],
                event['resource_type'],
                event['resource_id'],
                json.dumps(event['details'], ensure_ascii=False),
                event['severity'],
                event['ip_address'],
                event['user_agent'],
                event['timestamp'],
                event['success']
            ))
            self.db_conn.commit()
        except Exception as e:
            self.logger.error(f"保存审计事件失败: {str(e)}")

    def _trigger_alerts(self, event: Dict):
        """触发告警检查"""
        with self.alert_lock:
            for rule_id, rule in self.alert_rules.items():
                if not rule.get('active', True):
                    continue

                if self._matches_rule(event, rule):
                    self._check_alert_threshold(rule, event)

    def _matches_rule(self, event: Dict, rule: Dict) -> bool:
        """检查事件是否匹配规则"""
        conditions = rule.get('conditions', {})

        if 'category' in conditions and event['category'] != conditions['category']:
            return False

        if 'action' in conditions and event['action'] != conditions['action']:
            return False

        if 'severity' in conditions and event['severity'] != conditions['severity']:
            return False

        if 'user_id' in conditions and event['user_id'] != conditions['user_id']:
            return False

        return True

    def _check_alert_threshold(self, rule: Dict, event: Dict):
        """检查告警阈值"""
        window_start = time.time() - rule['time_window']

        with self.log_lock:
            count = sum(
                1 for e in self.recent_events
                if e['timestamp'] >= window_start and self._matches_rule(e, rule)
            )

        if count >= rule['threshold']:
            self._create_alert(rule, event)

    def _create_alert(self, rule: Dict, event: Dict):
        """创建告警"""
        alert_id = f"alert_{uuid.uuid4().hex[:8]}"

        alert = {
            'alert_id': alert_id,
            'rule_id': rule['rule_id'],
            'event_ids': [event['event_id']],
            'message': f"{rule['name']}: 检测到符合条件的事件",
            'severity': rule['severity'],
            'timestamp': time.time(),
            'acknowledged': False,
            'acknowledged_by': None,
            'acknowledged_at': None
        }

        with self.alert_lock:
            self.alerts[alert_id] = alert

        self._save_alert(alert)

        self.logger.warning(f"触发告警: {alert_id} - {alert['message']}")

    def _save_alert(self, alert: Dict):
        """保存告警到数据库"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO alerts
                (alert_id, rule_id, event_ids, message, severity, timestamp, 
                 acknowledged, acknowledged_by, acknowledged_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert['alert_id'],
                alert['rule_id'],
                json.dumps(alert['event_ids']),
                alert['message'],
                alert['severity'],
                alert['timestamp'],
                alert['acknowledged'],
                alert['acknowledged_by'],
                alert['acknowledged_at']
            ))
            self.db_conn.commit()
        except Exception as e:
            self.logger.error(f"保存告警失败: {str(e)}")

    def acknowledge_alert(self, alert_id: str, user_id: str) -> bool:
        """确认告警"""
        with self.alert_lock:
            alert = self.alerts.get(alert_id)
            if not alert:
                self.logger.error(f"告警不存在: {alert_id}")
                return False

            alert['acknowledged'] = True
            alert['acknowledged_by'] = user_id
            alert['acknowledged_at'] = time.time()

            cursor = self.db_conn.cursor()
            cursor.execute('''
                UPDATE alerts 
                SET acknowledged = ?, acknowledged_by = ?, acknowledged_at = ?
                WHERE alert_id = ?
            ''', (True, user_id, alert['acknowledged_at'], alert_id))
            self.db_conn.commit()

        self.logger.info(f"告警已确认: {alert_id} by {user_id}")
        return True

    def get_audit_events(self, filters: Dict = None, limit: int = 100) -> List[Dict]:
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
                'event_id': row[0],
                'category': row[1],
                'action': row[2],
                'user_id': row[3],
                'resource_type': row[4],
                'resource_id': row[5],
                'details': json.loads(row[6]) if row[6] else {},
                'severity': row[7],
                'ip_address': row[8],
                'user_agent': row[9],
                'timestamp': row[10],
                'success': row[11]
            })

        return results

    def get_alerts(self, acknowledged: bool = None, severity: str = None) -> List[Dict]:
        """获取告警列表"""
        query = 'SELECT * FROM alerts WHERE 1=1'
        params = []

        if acknowledged is not None:
            query += ' AND acknowledged = ?'
            params.append(acknowledged)

        if severity:
            query += ' AND severity = ?'
            params.append(severity)

        query += ' ORDER BY timestamp DESC'

        cursor = self.db_conn.cursor()
        cursor.execute(query, params)

        results = []
        for row in cursor.fetchall():
            results.append({
                'alert_id': row[0],
                'rule_id': row[1],
                'event_ids': json.loads(row[2]) if row[2] else [],
                'message': row[3],
                'severity': row[4],
                'timestamp': row[5],
                'acknowledged': row[6],
                'acknowledged_by': row[7],
                'acknowledged_at': row[8]
            })

        return results

    def generate_report(self, report_type: str = 'daily',
                       start_time: float = None, end_time: float = None) -> Dict:
        """生成审计报告"""
        if start_time is None:
            start_time = time.time() - 86400

        if end_time is None:
            end_time = time.time()

        events = self.get_audit_events({
            'start_time': start_time,
            'end_time': end_time
        }, limit=10000)

        stats = self._calculate_audit_stats(events)

        report = {
            'report_id': f"report_{uuid.uuid4().hex[:8]}",
            'type': report_type,
            'generated_at': time.time(),
            'period_start': start_time,
            'period_end': end_time,
            'summary': stats,
            'event_summary': self._summarize_events(events),
            'alert_summary': self._summarize_alerts(start_time, end_time)
        }

        self._save_report(report)

        self.logger.info(f"生成审计报告: {report_type}")
        return report

    def _calculate_audit_stats(self, events: List[Dict]) -> Dict:
        """计算审计统计信息"""
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
            'total_events': len(events),
            'by_category': dict(by_category),
            'by_action': dict(by_action),
            'by_severity': dict(by_severity),
            'success_count': success_count,
            'failure_count': failure_count,
            'success_rate': success_count / len(events) if events else 0
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
            'top_users': dict(sorted(top_users.items(), key=lambda x: -x[1])[:10]),
            'top_resources': dict(sorted(top_resources.items(), key=lambda x: -x[1])[:10])
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
            'total_alerts': len(period_alerts),
            'by_severity': dict(by_severity),
            'acknowledged_count': acknowledged_count,
            'unacknowledged_count': len(period_alerts) - acknowledged_count
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
            self.logger.error(f"保存报告失败: {str(e)}")

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
                'report_id': row[0],
                'type': row[1],
                'data': json.loads(row[2]),
                'generated_at': row[3],
                'period_start': row[4],
                'period_end': row[5]
            })

        return results

    def get_audit_stats(self) -> Dict:
        """获取审计统计信息"""
        recent_events = self.get_audit_events(limit=1000)

        stats = {
            'total_events_stored': len(self.events),
            'recent_events_count': len(recent_events),
            'active_alert_rules': sum(1 for r in self.alert_rules.values() if r.get('active', True)),
            'total_alert_rules': len(self.alert_rules),
            'active_alerts': len([a for a in self.alerts.values() if not a.get('acknowledged', False)]),
            'total_alerts': len(self.alerts),
            'last_event_time': max(e['timestamp'] for e in recent_events) if recent_events else 0
        }

        return stats

    def export_audit_data(self, output_file: str, start_time: float = None,
                         end_time: float = None) -> Dict:
        """导出审计数据"""
        events = self.get_audit_events({
            'start_time': start_time,
            'end_time': end_time
        }, limit=100000)

        data = {
            'export_time': time.time(),
            'start_time': start_time,
            'end_time': end_time,
            'event_count': len(events),
            'events': events
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self.logger.info(f"审计数据已导出: {output_file}")
        return {'file': output_file, 'record_count': len(events)}

    def _start_monitor(self):
        """启动监控线程"""
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            name='audit_monitor',
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
                self.logger.error(f"监控线程错误: {str(e)}")
                time.sleep(60)

    def _cleanup_old_events(self):
        """清理旧事件"""
        max_age = time.time() - 30 * 24 * 3600

        with self.log_lock:
            old_events = [eid for eid, event in self.events.items() if event['timestamp'] < max_age]
            for eid in old_events[:100]:
                del self.events[eid]

        cursor = self.db_conn.cursor()
        cursor.execute('DELETE FROM audit_events WHERE timestamp < ?', (max_age,))
        self.db_conn.commit()

    def _start_alert_processor(self):
        """启动告警处理线程"""
        self.alert_processor = threading.Thread(
            target=self._alert_processor_loop,
            name='alert_processor',
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
                self.logger.error(f"告警处理线程错误: {str(e)}")
                time.sleep(60)

    def _process_pending_alerts(self):
        """处理待处理告警"""
        pass


log_manager = LogManager()