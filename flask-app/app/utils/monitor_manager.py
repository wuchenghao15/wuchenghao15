#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitor Manager for MTSCOS AI System
监控异常处理模块
"""

import logging
logger = logging.getLogger(__name__)
import sqlite3
from contextlib import contextmanager
import json
import psutil
import time
from datetime import datetime, timedelta
from threading import Thread, Lock
from typing import Dict, List, Optional
from flask import request, session


class MonitorManager:
    """监控管理器"""
    
    def __init__(self, db_path: str, check_interval: int = 10):
        self.db_path = db_path
        self.check_interval = check_interval
        self.is_running = False
        self.lock = Lock()
        self.alerts = []
        self.system_status = {
            'cpu_usage': 0,
            'memory_usage': 0,
            'disk_usage': 0,
            'network_status': 'normal',
            'database_status': 'connected',
            'last_check': None
        }
        
        self._init_db()
        self._start_monitoring()
    
    def _init_db(self):
        """初始化监控数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建监控指标表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitor_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_type TEXT NOT NULL,
                metric_value REAL NOT NULL,
                metric_unit TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建告警表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitor_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT NOT NULL,
                alert_level TEXT NOT NULL,
                message TEXT NOT NULL,
                metric_value REAL,
                threshold REAL,
                resolved INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP
            )
        ''')
        
        # 创建系统状态表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_status_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建页面导航日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS page_navigation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                session_id TEXT,
                page_from TEXT,
                page_to TEXT,
                navigation_type TEXT,
                navigation_time REAL,
                status TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建导航异常记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS navigation_anomalies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                session_id TEXT,
                anomaly_type TEXT,
                page_from TEXT,
                page_to TEXT,
                navigation_count INTEGER,
                time_window INTEGER,
                severity TEXT,
                details TEXT,
                resolved INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _start_monitoring(self):
        """启动监控线程"""
        self.is_running = True
        
        def monitor_loop():
            while self.is_running:
                self._check_system()
                time.sleep(self.check_interval)
        
        self.monitor_thread = Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def _check_system(self):
        """检查系统状态"""
        with self.lock:
            try:
                # CPU使用率
                cpu_usage = psutil.cpu_percent(interval=1)
                self.system_status['cpu_usage'] = cpu_usage
                
                # 内存使用率
                memory = psutil.virtual_memory()
                self.system_status['memory_usage'] = memory.percent
                
                # 磁盘使用率
                disk = psutil.disk_usage('/')
                self.system_status['disk_usage'] = disk.percent
                
                # 网络状态
                try:
                    net_io = psutil.net_io_counters()
                    self.system_status['network_status'] = 'normal'
                except Exception:
                    self.system_status['network_status'] = 'unknown'
                
                # 数据库连接状态
                try:
                    with sqlite3.connect(self.db_path) as conn:
                        
                        conn.execute('SELECT 1')
                        self.system_status['database_status'] = 'connected'
                except Exception:
                    self.system_status['database_status'] = 'disconnected'
                
                self.system_status['last_check'] = datetime.now().isoformat()
                
                # 记录指标
                self._record_metrics()
                
                # 检查阈值并生成告警
                self._check_thresholds()
                
                # 记录状态日志
                self._log_status()
                
            except Exception as e:
                print(f"Monitor check error: {e}")
    
    def _record_metrics(self):
        """记录监控指标"""
        with sqlite3.connect(self.db_path) as conn:
            
            cursor = conn.cursor()
            
            metrics = [
            ('cpu_usage', self.system_status['cpu_usage'], '%'),
            ('memory_usage', self.system_status['memory_usage'], '%'),
            ('disk_usage', self.system_status['disk_usage'], '%')
            ]
            
            for metric_type, value, unit in metrics:
                cursor.execute('''
                INSERT INTO monitor_metrics (metric_type, metric_value, metric_unit)
                VALUES (?, ?, ?)
                ''', (metric_type, value, unit))
            
            conn.commit()
    
    def _check_thresholds(self):
        """检查阈值并生成告警"""
        from app.utils.rule_manager import get_rule_manager
        rm = get_rule_manager()
        
        thresholds = {
            'cpu': float(rm.get_rule('MONITOR_THRESHOLD_CPU') or 90),
            'memory': float(rm.get_rule('MONITOR_THRESHOLD_MEMORY') or 80),
            'disk': float(rm.get_rule('ALERT_THRESHOLD_DISK') or 95)
        }
        
        alerts_enabled = str(rm.get_rule('MONITOR_ALERT_ENABLED')).lower() == 'true'
        
        if not alerts_enabled:
            return
        
        # 检查CPU
        if self.system_status['cpu_usage'] >= thresholds['cpu']:
            self._create_alert('cpu_high', 'WARNING', 
                            f'CPU使用率过高: {self.system_status["cpu_usage"]}%',
                            self.system_status['cpu_usage'], thresholds['cpu'])
        
        # 检查内存
        if self.system_status['memory_usage'] >= thresholds['memory']:
            self._create_alert('memory_high', 'WARNING', 
                            f'内存使用率过高: {self.system_status["memory_usage"]}%',
                            self.system_status['memory_usage'], thresholds['memory'])
        
        # 检查磁盘
        if self.system_status['disk_usage'] >= thresholds['disk']:
            self._create_alert('disk_high', 'CRITICAL', 
                            f'磁盘使用率过高: {self.system_status["disk_usage"]}%',
                            self.system_status['disk_usage'], thresholds['disk'])
        
        # 检查数据库连接
        if self.system_status['database_status'] != 'connected':
            self._create_alert('database_disconnected', 'CRITICAL', 
                            '数据库连接断开', 0, 0)
    
    def _create_alert(self, alert_type: str, level: str, message: str, value: float = 0, threshold: float = 0):
        """创建告警"""
        # 检查是否已有相同类型的未解决告警
        with sqlite3.connect(self.db_path) as conn:
            
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT COUNT(*) FROM monitor_alerts 
            WHERE alert_type = ? AND resolved = 0
            ''', (alert_type,))
            
            if cursor.fetchone()[0] > 0:
                return
        
        # 创建新告警
        cursor.execute('''
            INSERT INTO monitor_alerts (alert_type, alert_level, message, metric_value, threshold)
            VALUES (?, ?, ?, ?, ?)
        ''', (alert_type, level, message, value, threshold))
        
        conn.commit()
        conn.close()
        
        # 添加到内存告警列表
        self.alerts.append({
            'alert_type': alert_type,
            'alert_level': level,
            'message': message,
            'metric_value': value,
            'threshold': threshold,
            'created_at': datetime.now().isoformat()
        })
        
        # 限制告警数量
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
    
    def _log_status(self):
        """记录系统状态日志"""
        with sqlite3.connect(self.db_path) as conn:
            
            cursor = conn.cursor()
            
            cursor.execute('INSERT INTO system_status_log (status_json) VALUES (?)',
            (json.dumps(self.system_status),))
            
            conn.commit()
    
    def get_system_status(self) -> Dict:
        """获取系统状态"""
        return self.system_status.copy()
    
    def get_service_statuses(self) -> List[Dict]:
        """获取所有服务状态"""
        services = [
            {
                'name': '数据库服务',
                'service_id': 'database',
                'status': self.system_status['database_status'],
                'description': 'SQLite数据库连接状态',
                'last_check': self.system_status['last_check']
            },
            {
                'name': '监控服务',
                'service_id': 'monitoring',
                'status': 'running' if self.is_running else 'stopped',
                'description': '系统监控线程状态',
                'last_check': self.system_status['last_check']
            },
            {
                'name': '规则管理器',
                'service_id': 'rule_manager',
                'status': 'running',
                'description': '规则管理服务状态',
                'last_check': datetime.now().isoformat()
            },
            {
                'name': '权限管理器',
                'service_id': 'permission_manager',
                'status': 'running',
                'description': '权限管理服务状态',
                'last_check': datetime.now().isoformat()
            },
            {
                'name': '缓存服务',
                'service_id': 'cache',
                'status': 'running',
                'description': '系统缓存服务状态',
                'last_check': datetime.now().isoformat()
            },
            {
                'name': '会话管理器',
                'service_id': 'session_manager',
                'status': 'running',
                'description': '用户会话管理服务',
                'last_check': datetime.now().isoformat()
            }
        ]
        
        return services
    
    def get_alerts(self, limit: int = 50, resolved: bool = False) -> List[Dict]:
        """获取告警列表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if resolved:
                cursor.execute('SELECT * FROM monitor_alerts ORDER BY created_at DESC LIMIT ?', (limit,))
            else:
                cursor.execute('SELECT * FROM monitor_alerts WHERE resolved = 0 ORDER BY created_at DESC LIMIT ?', (limit,))
            
            columns = ['id', 'alert_type', 'alert_level', 'message', 'metric_value', 'threshold', 'resolved', 'created_at', 'resolved_at']
            alerts = []
            for row in cursor.fetchall():
                alerts.append(dict(zip(columns, row)))
        
        return alerts
    
    def resolve_alert(self, alert_id: int) -> bool:
        """解决告警"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                
                cursor = conn.cursor()
                
                cursor.execute('UPDATE monitor_alerts SET resolved = 1, resolved_at = ? WHERE id = ?',
                (datetime.now(), alert_id))
                
                conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"Failed to resolve alert {alert_id}: {e}")
            return False
    
    def resolve_all_alerts(self) -> bool:
        """解决所有告警"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                
                cursor = conn.cursor()
                
                cursor.execute('UPDATE monitor_alerts SET resolved = 1, resolved_at = ? WHERE resolved = 0',
                (datetime.now(),))
                
                conn.commit()
            
            # 清空内存告警列表
            self.alerts = []
            
            return True
        except Exception as e:
            logger.error(f"Failed to resolve all alerts: {e}")
            return False
    
    def get_metrics(self, metric_type: str = None, hours: int = 24) -> List[Dict]:
        """获取历史指标数据"""
        with sqlite3.connect(self.db_path) as conn:
            
            cursor = conn.cursor()
            
            time_threshold = datetime.now() - timedelta(hours=hours)
            
            if metric_type:
                cursor.execute('''
                SELECT metric_value, metric_unit, created_at 
                FROM monitor_metrics 
                WHERE metric_type = ? AND created_at > ? 
                ORDER BY created_at DESC
                ''', (metric_type, time_threshold))
            else:
                cursor.execute('''
                SELECT metric_type, metric_value, metric_unit, created_at 
                FROM monitor_metrics 
                WHERE created_at > ? 
                ORDER BY created_at DESC
                ''', (time_threshold,))
            
            columns = ['metric_type', 'metric_value', 'metric_unit', 'created_at'] if not metric_type else ['metric_value', 'metric_unit', 'created_at']
            metrics = []
            for row in cursor.fetchall():
                metrics.append(dict(zip(columns, row)))
            
        return metrics
    
    def get_alert_summary(self) -> Dict:
        """获取告警摘要"""
        with sqlite3.connect(self.db_path) as conn:
            
            cursor = conn.cursor()
            
            cursor.execute('SELECT alert_level, COUNT(*) FROM monitor_alerts WHERE resolved = 0 GROUP BY alert_level')
            summary = {'CRITICAL': 0, 'WARNING': 0, 'INFO': 0}
            for row in cursor.fetchall():
                summary[row[0]] = row[1]
            
        return summary
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
    
    def get_recent_errors(self, limit: int = 50) -> List[Dict]:
        """获取最近的错误日志"""
        with sqlite3.connect(self.db_path) as conn:
            
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT id, error_type, message, details, created_at 
            FROM ai_learning_errors 
            WHERE resolved = 0 
            ORDER BY created_at DESC 
            LIMIT ?
            ''', (limit,))
            
            columns = ['id', 'error_type', 'message', 'details', 'created_at']
            errors = []
            for row in cursor.fetchall():
                errors.append(dict(zip(columns, row)))
            
        return errors
    
    def log_page_navigation(self, user_id: int, username: str, session_id: str, 
                            page_from: str, page_to: str, navigation_type: str, 
                            navigation_time: float = 0.0, status: str = 'success', 
                            error_message: str = ''):
        """记录页面导航日志"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT INTO page_navigation_logs 
                (user_id, username, session_id, page_from, page_to, navigation_type, 
                navigation_time, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, username, session_id, page_from, page_to, navigation_type,
                navigation_time, status, error_message))
                
                conn.commit()
            
            # 检测导航异常
            self.detect_navigation_anomaly(user_id, username, session_id, 
                                           page_from, page_to, navigation_type)
            
            return True
        except Exception as e:
            logger.error(f"Failed to log page navigation: {e}")
            return False
    
    def detect_navigation_anomaly(self, user_id: int, username: str, session_id: str,
                                   page_from: str, page_to: str, navigation_type: str):
        """检测导航异常"""
        from app.utils.rule_manager import get_rule_manager
        rm = get_rule_manager()
        
        # 获取异常检测规则
        back_nav_threshold = int(rm.get_rule('NAV_ANOMALY_BACK_THRESHOLD') or 5)
        time_window = int(rm.get_rule('NAV_ANOMALY_TIME_WINDOW') or 60)
        
        with sqlite3.connect(self.db_path) as conn:
            
            cursor = conn.cursor()
            
            # 检查短时间内的后退操作次数
            cursor.execute('''
            SELECT COUNT(*) FROM page_navigation_logs
            WHERE session_id = ? AND navigation_type = ? 
            AND created_at > datetime('now', '-{} seconds')
            '''.format(time_window), (session_id, 'back'))
            
            back_count = cursor.fetchone()[0]
            
            # 如果后退次数超过阈值,记录异常
            if back_count >= back_nav_threshold:
                anomaly_details = json.dumps({
                    'back_count': back_count,
                    'time_window': time_window,
                    'page_from': page_from,
                    'page_to': page_to,
                    'threshold': back_nav_threshold
                })
            
            # 检查是否已有未解决的同类异常
            cursor.execute('''
            SELECT COUNT(*) FROM navigation_anomalies
            WHERE session_id = ? AND anomaly_type = 'excessive_back' AND resolved = 0
            ''', (session_id,))
            
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                INSERT INTO navigation_anomalies
                (user_id, username, session_id, anomaly_type, page_from, page_to,
                navigation_count, time_window, severity, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, username, session_id, 'excessive_back', page_from, page_to,
                      back_count, time_window, 'WARNING', anomaly_details))
                
                # 创建告警
                self._create_alert('navigation_anomaly', 'WARNING',
                                  f'用户 {username} 在 {time_window} 秒内后退操作 {back_count} 次,可能存在异常')
                
                conn.commit()
    
    def get_navigation_logs(self, session_id: str = None, user_id: int = None, 
                            limit: int = 100) -> List[Dict]:
        """获取页面导航日志"""
        with sqlite3.connect(self.db_path) as conn:
            
            cursor = conn.cursor()
            
            query = '''
            SELECT id, user_id, username, session_id, page_from, page_to, 
            navigation_type, navigation_time, status, error_message, created_at
            FROM page_navigation_logs
            WHERE 1=1
            '''
            params = []
            
            if session_id:
                query += ' AND session_id = ?'
                params.append(session_id)
            
            if user_id:
                query += ' AND user_id = ?'
                params.append(user_id)
            
            query += ' ORDER BY created_at DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            
            columns = ['id', 'user_id', 'username', 'session_id', 'page_from', 'page_to',
                   'navigation_type', 'navigation_time', 'status', 'error_message', 'created_at']
            logs = []
            for row in cursor.fetchall():
                logs.append(dict(zip(columns, row)))
            
        return logs
    
    def get_navigation_anomalies(self, resolved: bool = False, limit: int = 50) -> List[Dict]:
        """获取导航异常记录"""
        with sqlite3.connect(self.db_path) as conn:
            
            cursor = conn.cursor()
            
            if resolved:
                cursor.execute('''
                SELECT id, user_id, username, session_id, anomaly_type, page_from, page_to,
                navigation_count, time_window, severity, details, resolved, created_at, resolved_at
                FROM navigation_anomalies
                ORDER BY created_at DESC LIMIT ?
                ''', (limit,))
            else:
                cursor.execute('''
                SELECT id, user_id, username, session_id, anomaly_type, page_from, page_to,
                navigation_count, time_window, severity, details, resolved, created_at, resolved_at
                FROM navigation_anomalies
                WHERE resolved = 0
                ORDER BY created_at DESC LIMIT ?
                ''', (limit,))
            
            columns = ['id', 'user_id', 'username', 'session_id', 'anomaly_type', 'page_from', 'page_to',
                       'navigation_count', 'time_window', 'severity', 'details', 'resolved', 'created_at', 'resolved_at']
            anomalies = []
            for row in cursor.fetchall():
                anomalies.append(dict(zip(columns, row)))
            
        return anomalies
    
    def resolve_navigation_anomaly(self, anomaly_id: int) -> bool:
        """解决导航异常"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                
                cursor = conn.cursor()
                
                cursor.execute('UPDATE navigation_anomalies SET resolved = 1, resolved_at = ? WHERE id = ?',
                (datetime.now(), anomaly_id))
                
                conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"Failed to resolve navigation anomaly {anomaly_id}: {e}")
            return False


# 全局监控管理器实例
monitor_manager: Optional[MonitorManager] = None


def init_monitor_manager(db_path: str, check_interval: int = 10):
    """初始化监控管理器"""
    global monitor_manager
    monitor_manager = MonitorManager(db_path, check_interval)
    return monitor_manager


def get_monitor_manager() -> MonitorManager:
    """获取监控管理器实例"""
    global monitor_manager
    if monitor_manager is None:
        monitor_manager = MonitorManager('/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db')
    return monitor_manager


def get_system_status() -> Dict:
    """获取系统状态"""
    return get_monitor_manager().get_system_status()


def get_alerts(limit: int = 50, resolved: bool = False) -> List[Dict]:
    """获取告警列表"""
    return get_monitor_manager().get_alerts(limit, resolved)


def resolve_alert(alert_id: int) -> bool:
    """解决告警"""
    return get_monitor_manager().resolve_alert(alert_id)


def get_alert_summary() -> Dict:
    """获取告警摘要"""
    return get_monitor_manager().get_alert_summary()


def get_recent_errors(limit: int = 50) -> List[Dict]:
    """获取最近错误"""
    return get_monitor_manager().get_recent_errors(limit)


def log_page_navigation(user_id: int, username: str, session_id: str,
                        page_from: str, page_to: str, navigation_type: str,
                        navigation_time: float = 0.0, status: str = 'success',
                        error_message: str = '') -> bool:
    """记录页面导航日志"""
    return get_monitor_manager().log_page_navigation(
        user_id, username, session_id, page_from, page_to, navigation_type,
        navigation_time, status, error_message
    )


def get_navigation_logs(session_id: str = None, user_id: int = None, limit: int = 100) -> List[Dict]:
    """获取页面导航日志"""
    return get_monitor_manager().get_navigation_logs(session_id, user_id, limit)


def get_navigation_anomalies(resolved: bool = False, limit: int = 50) -> List[Dict]:
    """获取导航异常记录"""
    return get_monitor_manager().get_navigation_anomalies(resolved, limit)


def resolve_navigation_anomaly(anomaly_id: int) -> bool:
    """解决导航异常"""
    return get_monitor_manager().resolve_navigation_anomaly(anomaly_id)
