#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS指标收集与告警服务
提供统一的应用指标收集和告警通知
"""

import os
import sys
import json
import time
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable

logger = print


class Metric:
    """指标"""

    def __init__(self, metric_id: str, name: str, metric_type: str = 'gauge',
                 value: float = 0, unit: str = '', description: str = '',
                 tags: Dict[str, str] = None):
        self.metric_id = metric_id
        self.name = name
        self.metric_type = metric_type  # gauge, counter, histogram, summary
        self.value = value
        self.unit = unit
        self.description = description
        self.tags = tags or {}
        self.history: List[Dict[str, Any]] = []
        self.last_updated = datetime.now().isoformat()

    def record(self, value: float):
        """记录值"""
        if self.metric_type == 'counter':
            self.value += value
        else:
            self.value = value

        self.last_updated = datetime.now().isoformat()
        self.history.append({
            'value': self.value,
            'timestamp': self.last_updated
        })

        if len(self.history) > 1000:
            self.history = self.history[-500:]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'metric_id': self.metric_id,
            'name': self.name,
            'type': self.metric_type,
            'value': self.value,
            'unit': self.unit,
            'description': self.description,
            'tags': self.tags,
            'last_updated': self.last_updated,
            'history_count': len(self.history)
        }


class AlertRule:
    """告警规则"""

    def __init__(self, rule_id: str, name: str, metric_name: str,
                 condition: str, threshold: float,
                 duration: int = 60, severity: str = 'warning',
                 enabled: bool = True, description: str = ''):
        self.rule_id = rule_id
        self.name = name
        self.metric_name = metric_name
        self.condition = condition  # gt, lt, gte, lte, eq
        self.threshold = threshold
        self.duration = duration
        self.severity = severity  # info, warning, critical
        self.enabled = enabled
        self.description = description
        self.triggered = False
        self.triggered_at = None
        self.trigger_count = 0
        self.last_check = None

    def evaluate(self, value: float) -> bool:
        """评估规则"""
        if self.condition == 'gt':
            return value > self.threshold
        elif self.condition == 'lt':
            return value < self.threshold
        elif self.condition == 'gte':
            return value >= self.threshold
        elif self.condition == 'lte':
            return value <= self.threshold
        elif self.condition == 'eq':
            return value == self.threshold
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'metric_name': self.metric_name,
            'condition': self.condition,
            'threshold': self.threshold,
            'duration': self.duration,
            'severity': self.severity,
            'enabled': self.enabled,
            'description': self.description,
            'triggered': self.triggered,
            'triggered_at': self.triggered_at,
            'trigger_count': self.trigger_count,
            'last_check': self.last_check
        }


class MetricsAlertService:
    """指标收集与告警服务"""

    def __init__(self):
        self.metrics: Dict[str, Metric] = {}
        self.alert_rules: Dict[str, AlertRule] = {}
        self.alert_history: List[Dict[str, Any]] = []
        self.is_running = False
        self.check_thread = None
        self.lock = threading.Lock()
        self.alert_callbacks: List[Callable] = []

        self._init_database()
        self._register_default_metrics()
        self._register_default_alerts()

    def _init_database(self):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    type TEXT DEFAULT 'gauge',
                    value REAL DEFAULT 0,
                    unit TEXT,
                    description TEXT,
                    tags TEXT,
                    last_updated TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metric_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_id TEXT NOT NULL,
                    value REAL,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alert_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    condition TEXT NOT NULL,
                    threshold REAL,
                    duration INTEGER DEFAULT 60,
                    severity TEXT DEFAULT 'warning',
                    enabled INTEGER DEFAULT 1,
                    description TEXT,
                    trigger_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alert_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_id TEXT NOT NULL,
                    rule_name TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL,
                    threshold REAL,
                    severity TEXT,
                    status TEXT DEFAULT 'triggered',
                    message TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_metrics_id ON metrics(metric_id)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_alert_rules_id ON alert_rules(rule_id)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_metric_history_metric ON metric_history(metric_id)
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[指标] 初始化数据库失败: {e}")

    def _register_default_metrics(self):
        """注册默认指标"""
        defaults = [
            Metric('m_req_total', '请求总数', 'counter', 0, '次', '系统总请求数'),
            Metric('m_req_rate', '请求速率', 'gauge', 0, 'req/s', '每秒请求数'),
            Metric('m_error_rate', '错误率', 'gauge', 0, '%', '请求错误率'),
            Metric('m_response_time', '平均响应时间', 'gauge', 0, 'ms', 'API平均响应时间'),
            Metric('m_active_users', '活跃用户数', 'gauge', 0, '人', '当前活跃用户数'),
            Metric('m_db_connections', '数据库连接数', 'gauge', 0, '个', '数据库活跃连接数'),
            Metric('m_cache_hit_rate', '缓存命中率', 'gauge', 0, '%', '缓存命中率'),
            Metric('m_queue_size', '队列大小', 'gauge', 0, '条', '消息队列积压数'),
            Metric('m_cpu_usage', 'CPU使用率', 'gauge', 0, '%', 'CPU使用率'),
            Metric('m_memory_usage', '内存使用率', 'gauge', 0, '%', '内存使用率')
        ]

        for metric in defaults:
            if metric.metric_id not in self.metrics:
                self.metrics[metric.metric_id] = metric
                self._save_metric_to_db(metric)

    def _register_default_alerts(self):
        """注册默认告警规则"""
        defaults = [
            AlertRule('a_error_rate', '错误率告警', 'm_error_rate', 'gt', 5.0,
                     duration=60, severity='critical', description='错误率超过5%'),
            AlertRule('a_response_time', '响应时间告警', 'm_response_time', 'gt', 1000.0,
                     duration=120, severity='warning', description='平均响应时间超过1秒'),
            AlertRule('a_cpu_usage', 'CPU使用率告警', 'm_cpu_usage', 'gt', 80.0,
                     duration=300, severity='warning', description='CPU使用率超过80%'),
            AlertRule('a_memory_usage', '内存使用率告警', 'm_memory_usage', 'gt', 85.0,
                     duration=300, severity='warning', description='内存使用率超过85%'),
            AlertRule('a_queue_size', '队列积压告警', 'm_queue_size', 'gt', 1000.0,
                     duration=60, severity='critical', description='队列积压超过1000条')
        ]

        for alert in defaults:
            if alert.rule_id not in self.alert_rules:
                self.alert_rules[alert.rule_id] = alert
                self._save_alert_to_db(alert)

    def _save_metric_to_db(self, metric: Metric):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO metrics
                (metric_id, name, type, value, unit, description, tags, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metric.metric_id, metric.name, metric.metric_type,
                metric.value, metric.unit, metric.description,
                json.dumps(metric.tags), metric.last_updated
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[指标] 保存指标失败: {e}")

    def _save_alert_to_db(self, alert: AlertRule):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO alert_rules
                (rule_id, name, metric_name, condition, threshold, duration,
                 severity, enabled, description, trigger_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert.rule_id, alert.name, alert.metric_name,
                alert.condition, alert.threshold, alert.duration,
                alert.severity, 1 if alert.enabled else 0,
                alert.description, alert.trigger_count
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[指标] 保存告警规则失败: {e}")

    def record_metric(self, metric_id: str, value: float):
        """记录指标"""
        with self.lock:
            metric = self.metrics.get(metric_id)
            if not metric:
                logger(f"[指标] 指标不存在: {metric_id}")
                return

            metric.record(value)

        self._update_metric_in_db(metric)
        self._save_metric_history(metric)

    def _update_metric_in_db(self, metric: Metric):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE metrics SET value = ?, last_updated = ? WHERE metric_id = ?
            ''', (metric.value, metric.last_updated, metric.metric_id))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[指标] 更新指标失败: {e}")

    def _save_metric_history(self, metric: Metric):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO metric_history (metric_id, value, timestamp)
                VALUES (?, ?, ?)
            ''', (metric.metric_id, metric.value, metric.last_updated))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[指标] 保存指标历史失败: {e}")

    def increment_counter(self, metric_id: str, value: float = 1):
        """增加计数器"""
        with self.lock:
            metric = self.metrics.get(metric_id)
            if metric and metric.metric_type == 'counter':
                metric.record(value)

        if metric:
            self._update_metric_in_db(metric)
            self._save_metric_history(metric)

    def add_metric(self, name: str, metric_type: str = 'gauge',
                   unit: str = '', description: str = '',
                   tags: Dict[str, str] = None) -> str:
        """添加自定义指标"""
        import uuid
        metric_id = f"m_{uuid.uuid4().hex[:12]}"

        metric = Metric(
            metric_id=metric_id,
            name=name,
            metric_type=metric_type,
            unit=unit,
            description=description,
            tags=tags or {}
        )

        with self.lock:
            self.metrics[metric_id] = metric

        self._save_metric_to_db(metric)
        logger(f"[指标] 添加指标: {name}")

        return metric_id

    def add_alert_rule(self, name: str, metric_name: str, condition: str,
                       threshold: float, duration: int = 60,
                       severity: str = 'warning', description: str = '') -> str:
        """添加告警规则"""
        import uuid
        rule_id = f"a_{uuid.uuid4().hex[:12]}"

        rule = AlertRule(
            rule_id=rule_id,
            name=name,
            metric_name=metric_name,
            condition=condition,
            threshold=threshold,
            duration=duration,
            severity=severity,
            description=description
        )

        with self.lock:
            self.alert_rules[rule_id] = rule

        self._save_alert_to_db(rule)
        logger(f"[指标] 添加告警规则: {name}")

        return rule_id

    def add_alert_callback(self, callback: Callable):
        """添加告警回调"""
        self.alert_callbacks.append(callback)

    def _check_alerts_loop(self):
        """告警检查循环"""
        while self.is_running:
            try:
                time.sleep(30)

                with self.lock:
                    for rule in self.alert_rules.values():
                        if not rule.enabled:
                            continue

                        metric = self._find_metric_by_name(rule.metric_name)
                        rule.last_check = datetime.now().isoformat()

                        if not metric:
                            continue

                        is_breaching = rule.evaluate(metric.value)

                        if is_breaching and not rule.triggered:
                            rule.triggered = True
                            rule.triggered_at = datetime.now().isoformat()
                            rule.trigger_count += 1

                            alert_record = {
                                'rule_id': rule.rule_id,
                                'rule_name': rule.name,
                                'metric_name': rule.metric_name,
                                'metric_value': metric.value,
                                'threshold': rule.threshold,
                                'severity': rule.severity,
                                'status': 'triggered',
                                'message': f"{rule.name}: {rule.metric_name}={metric.value} {rule.condition} {rule.threshold}",'timestamp': rule.triggered_at}

                            self.alert_history.append(alert_record)
                            self._save_alert_history(alert_record)

                            for callback in self.alert_callbacks:
                                try:
                                    callback(alert_record)
                                except Exception as e:
                                    logger(f"[指标] 告警回调失败: {e}")

                            logger(f"[指标] 告警触发: {rule.name}")

                        elif not is_breaching and rule.triggered:
                            rule.triggered = False

                            resolved_record = {
                                'rule_id': rule.rule_id,
                                'rule_name': rule.name,
                                'metric_name': rule.metric_name,
                                'metric_value': metric.value,
                                'threshold': rule.threshold,
                                'severity': rule.severity,
                                'status': 'resolved',
                                'message': f"{rule.name} 已恢复正常",
                                'timestamp': datetime.now().isoformat()
                            }

                            self.alert_history.append(resolved_record)
                            self._save_alert_history(resolved_record)

                            logger(f"[指标] 告警恢复: {rule.name}")

            except Exception as e:
                logger(f"[指标] 告警检查错误: {e}")

    def _find_metric_by_name(self, name: str) -> Optional[Metric]:
        """通过名称查找指标"""
        for metric in self.metrics.values():
            if metric.name == name or metric.metric_id == name:
                return metric
        return None

    def _save_alert_history(self, record: Dict[str, Any]):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO alert_history
                (rule_id, rule_name, metric_name, metric_value, threshold,
                 severity, status, message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record['rule_id'], record['rule_name'],
                record['metric_name'], record['metric_value'],
                record['threshold'], record['severity'],
                record['status'], record['message']
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[指标] 保存告警历史失败: {e}")

    def get_metric(self, metric_id: str) -> Optional[Metric]:
        return self.metrics.get(metric_id)

    def get_metrics(self, metric_type: str = None) -> List[Metric]:
        with self.lock:
            if metric_type:
                return [m for m in self.metrics.values() if m.metric_type == metric_type]
            return list(self.metrics.values())

    def get_metric_history(self, metric_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM metric_history
                WHERE metric_id = ?
                ORDER BY timestamp DESC LIMIT ?
            ''', (metric_id, limit))

            columns = [desc[0] for desc in cursor.description]
            history = [dict(zip(columns, row)) for row in cursor.fetchall()]

            conn.close()
            return history
        except Exception as e:
            logger(f"[指标] 获取指标历史失败: {e}")
            return []

    def get_alert_rules(self, enabled_only: bool = False) -> List[AlertRule]:
        with self.lock:
            if enabled_only:
                return [r for r in self.alert_rules.values() if r.enabled]
            return list(self.alert_rules.values())

    def get_alert_history(self, rule_id: str = None, status: str = None,
                          limit: int = 100) -> List[Dict[str, Any]]:
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            query = 'SELECT * FROM alert_history WHERE 1=1'
            params = []

            if rule_id:
                query += ' AND rule_id = ?'
                params.append(rule_id)
            if status:
                query += ' AND status = ?'
                params.append(status)

            query += ' ORDER BY created_at DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)

            columns = [desc[0] for desc in cursor.description]
            history = [dict(zip(columns, row)) for row in cursor.fetchall()]

            conn.close()
            return history
        except Exception as e:
            logger(f"[指标] 获取告警历史失败: {e}")
            return []

    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            triggered = sum(1 for r in self.alert_rules.values() if r.triggered)

            return {
                'status': 'running' if self.is_running else 'stopped',
                'total_metrics': len(self.metrics),
                'total_alert_rules': len(self.alert_rules),
                'triggered_alerts': triggered,
                'total_alert_history': len(self.alert_history),
                'alert_callbacks': len(self.alert_callbacks)
            }

    def start(self):
        if self.is_running:
            return

        self.is_running = True
        self.check_thread = threading.Thread(target=self._check_alerts_loop, daemon=True)
        self.check_thread.start()
        logger(f"[指标] 指标收集与告警服务已启动")

    def stop(self):
        self.is_running = False
        if self.check_thread:
            self.check_thread.join()
        logger(f"[指标] 指标收集与告警服务已停止")


metrics_alert_service = MetricsAlertService()
