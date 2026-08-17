# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI System Monitor Agent
后台自动监控系统：进程监控、数据监控、功能监控
"""

import os
import sys
import time
import json
import threading
import logging
import sqlite3
import psutil
from datetime import datetime
from contextlib import contextmanager
from typing import Dict, List, Optional, Any

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('ai_system_monitor.log'), logging.StreamHandler()])
logger = logging.getLogger('AI_System_Monitor')

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'app.db')

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        yield conn
    finally:
        conn.close()

class SystemMonitorAgent:
    def __init__(self):
        self.monitoring_enabled = True
        self.monitoring_interval = 10
        self.process_monitors = {}
        self.data_monitors = {}
        self.function_monitors = {}
        self.resource_stats = {}
        self.health_status = {}
        self.lock = threading.Lock()
        
        self._init_database()
        self._register_monitors()
        self._start_monitoring_thread()
        
        logger.info("AI System Monitor Agent initialized")
    
    def _init_database(self):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_monitor (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        monitor_id TEXT NOT NULL UNIQUE,
                        monitor_type TEXT NOT NULL,
                        name TEXT NOT NULL,
                        status TEXT DEFAULT 'unknown',
                        value TEXT,
                        threshold TEXT,
                        message TEXT,
                        last_check TEXT DEFAULT CURRENT_TIMESTAMP,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS process_monitor (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        process_id INTEGER,
                        process_name TEXT NOT NULL,
                        status TEXT DEFAULT 'running',
                        cpu_percent REAL DEFAULT 0.0,
                        memory_percent REAL DEFAULT 0.0,
                        memory_info().rss INTEGER DEFAULT 0,
                        start_time TEXT,
                        uptime TEXT,
                        last_check TEXT DEFAULT CURRENT_TIMESTAMP,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS data_monitor (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        table_name TEXT NOT NULL,
                        row_count INTEGER DEFAULT 0,
                        expected_min INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'ok',
                        last_check TEXT DEFAULT CURRENT_TIMESTAMP,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS function_monitor (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        function_name TEXT NOT NULL,
                        module TEXT,
                        status TEXT DEFAULT 'unknown',
                        response_time REAL DEFAULT 0.0,
                        last_success TEXT,
                        last_failure TEXT,
                        error_count INTEGER DEFAULT 0,
                        success_rate REAL DEFAULT 100.0,
                        last_check TEXT DEFAULT CURRENT_TIMESTAMP,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_resource (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cpu_percent REAL DEFAULT 0.0,
                        memory_percent REAL DEFAULT 0.0,
                        disk_percent REAL DEFAULT 0.0,
                        disk_used INTEGER DEFAULT 0,
                        disk_total INTEGER DEFAULT 0,
                        network_sent INTEGER DEFAULT 0,
                        network_recv INTEGER DEFAULT 0,
                        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS health_alert (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        alert_id TEXT NOT NULL UNIQUE,
                        type TEXT NOT NULL,
                        severity TEXT DEFAULT 'warning',
                        title TEXT NOT NULL,
                        message TEXT,
                        source TEXT,
                        status TEXT DEFAULT 'active',
                        acknowledged TEXT DEFAULT 'no',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        resolved_at TEXT
                    )
                ''')
                
                conn.commit()
                logger.info("System monitor database tables initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
    
    def _register_monitors(self):
        self.process_monitors = {
            'flask_app': {
                'name': 'Flask应用进程',
                'command': 'python3',
                'args_contains': 'app.py',
                'critical': True
            },
            'ai_cluster_manager': {
                'name': 'AI集群管理器',
                'command': 'python3',
                'args_contains': 'ai_cluster_manager',
                'critical': True
            },
            'ai_error_monitor': {
                'name': 'AI错误监控器',
                'command': 'python3',
                'args_contains': 'ai_error_monitor',
                'critical': False
            },
        }
        
        self.data_monitors = {
            'users': {
                'name': '用户表',
                'table': 'users',
                'min_rows': 1,
                'critical': True
            },
            'exams': {
                'name': '考试表',
                'table': 'exams',
                'min_rows': 0,
                'critical': False
            },
            'courses': {
                'name': '课程表',
                'table': 'courses',
                'min_rows': 0,
                'critical': False
            },
            'questions': {
                'name': '题目表',
                'table': 'questions',
                'min_rows': 0,
                'critical': False
            },
            'notifications': {
                'name': '通知表',
                'table': 'notifications',
                'min_rows': 0,
                'critical': False
            },
            'login_logs': {
                'name': '登录日志表',
                'table': 'login_logs',
                'min_rows': 0,
                'critical': False
            },
            'system_rules': {
                'name': '系统规则表',
                'table': 'system_rules',
                'min_rows': 100,
                'critical': True
            },
            'ai_cluster_config': {
                'name': 'AI集群配置表',
                'table': 'ai_cluster_config',
                'min_rows': 10,
                'critical': True
            },
            'ai_employee_config': {
                'name': 'AI员工配置表',
                'table': 'ai_employee_config',
                'min_rows': 20,
                'critical': True
            },
        }
        
        self.function_monitors = {
            'login_api': {
                'name': '登录API',
                'module': 'auth',
                'test_function': self._test_login_api,
                'critical': True
            },
            'dashboard_api': {
                'name': '仪表盘API',
                'module': 'dashboard',
                'test_function': self._test_dashboard_api,
                'critical': True
            },
            'database_connection': {
                'name': '数据库连接',
                'module': 'database',
                'test_function': self._test_database,
                'critical': True
            },
            'error_monitor': {
                'name': '错误监控',
                'module': 'monitor',
                'test_function': self._test_error_monitor,
                'critical': False
            },
            'system_rules': {
                'name': '系统规则',
                'module': 'rules',
                'test_function': self._test_system_rules,
                'critical': True
            },
        }
    
    def _start_monitoring_thread(self):
        def monitor():
            while True:
                if self.monitoring_enabled:
                    try:
                        self._monitor_processes()
                        self._monitor_data()
                        self._monitor_functions()
                        self._monitor_resources()
                        self._check_health()
                    except Exception as e:
                        logger.error(f"Monitoring thread error: {e}")
                time.sleep(self.monitoring_interval)
        
        monitoring_thread = threading.Thread(target=monitor, daemon=True)
        monitoring_thread.start()
        logger.info("System monitoring thread started")
    
    def _monitor_processes(self):
        try:
            processes = []
            
            for monitor_id, config in self.process_monitors.items():
                found = False
                for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent', 'memory_info().rss', 'create_time']):
                    try:
                        cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                        if config['command'] in proc.info['name'] and config['args_contains'] in cmdline:
                            uptime = self._format_uptime(time.time() - proc.info['create_time'])
                            processes.append({
                                'monitor_id': monitor_id,
                                'process_id': proc.info['pid'],
                                'process_name': config['name'],
                                'status': 'running',
                                'cpu_percent': proc.info['cpu_percent'],
                                'memory_percent': proc.info['memory_percent'],
                                'memory_info().rss': proc.info['memory_info().rss'],
                                'start_time': datetime.fromtimestamp(proc.info['create_time']).isoformat(),
                                'uptime': uptime
                            })
                            found = True
                    except:
                        pass
                
                if not found:
                    processes.append({
                        'monitor_id': monitor_id,
                        'process_id': 0,
                        'process_name': config['name'],
                        'status': 'stopped',
                        'cpu_percent': 0.0,
                        'memory_percent': 0.0,
                        'memory_info().rss': 0,
                        'start_time': '',
                        'uptime': '0秒'
                    })
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                for proc in processes:
                    cursor.execute('SELECT id FROM process_monitor WHERE process_name = ?', (proc['process_name'],))
                    existing = cursor.fetchone()
                    
                    if existing:
                        cursor.execute('''
                            UPDATE process_monitor SET 
                                process_id = ?, status = ?, cpu_percent = ?, memory_percent = ?,
                                memory_info().rss = ?, start_time = ?, uptime = ?, last_check = ?, updated_at = ?
                            WHERE process_name = ?
                        ''', (proc['process_id'], proc['status'], proc['cpu_percent'], proc['memory_percent'],
                              proc['memory_info().rss'], proc['start_time'], proc['uptime'], 
                              datetime.now().isoformat(), datetime.now().isoformat(), proc['process_name']))
                    else:
                        cursor.execute('''
                            INSERT INTO process_monitor 
                            (process_id, process_name, status, cpu_percent, memory_percent, 
                             memory_info().rss, start_time, uptime, last_check, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (proc['process_id'], proc['process_name'], proc['status'], 
                              proc['cpu_percent'], proc['memory_percent'], proc['memory_info().rss'],
                              proc['start_time'], proc['uptime'], datetime.now().isoformat(), datetime.now().isoformat()))
                
                conn.commit()
            
            self.health_status['processes'] = processes
            logger.debug(f"Process monitoring completed: {len(processes)} processes")
        except Exception as e:
            logger.error(f"Process monitoring failed: {e}")
    
    def _format_uptime(self, seconds):
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if days > 0:
            return f"{days}天{hours}小时{minutes}分钟"
        elif hours > 0:
            return f"{hours}小时{minutes}分钟"
        elif minutes > 0:
            return f"{minutes}分钟{secs}秒"
        else:
            return f"{secs}秒"
    
    def _monitor_data(self):
        try:
            data_status = []
            
            for monitor_id, config in self.data_monitors.items():
                try:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(f'SELECT COUNT(*) FROM {config["table"]}')
                        row_count = cursor.fetchone()[0]
                    
                    status = 'ok' if row_count >= config['min_rows'] else 'warning'
                    if config['critical'] and row_count == 0:
                        status = 'critical'
                    
                    data_status.append({
                        'monitor_id': monitor_id,
                        'table_name': config['table'],
                        'name': config['name'],
                        'row_count': row_count,
                        'expected_min': config['min_rows'],
                        'status': status
                    })
                except Exception as e:
                    data_status.append({
                        'monitor_id': monitor_id,
                        'table_name': config['table'],
                        'name': config['name'],
                        'row_count': -1,
                        'expected_min': config['min_rows'],
                        'status': 'error'
                    })
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                for data in data_status:
                    cursor.execute('SELECT id FROM data_monitor WHERE table_name = ?', (data['table_name'],))
                    existing = cursor.fetchone()
                    
                    if existing:
                        cursor.execute('''
                            UPDATE data_monitor SET 
                                row_count = ?, expected_min = ?, status = ?, 
                                last_check = ?, updated_at = ?
                            WHERE table_name = ?
                        ''', (data['row_count'], data['expected_min'], data['status'],
                              datetime.now().isoformat(), datetime.now().isoformat(), data['table_name']))
                    else:
                        cursor.execute('''
                            INSERT INTO data_monitor 
                            (table_name, row_count, expected_min, status, last_check, created_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (data['table_name'], data['row_count'], data['expected_min'],
                              data['status'], datetime.now().isoformat(), datetime.now().isoformat()))
                
                conn.commit()
            
            self.health_status['data'] = data_status
            logger.debug(f"Data monitoring completed: {len(data_status)} tables")
        except Exception as e:
            logger.error(f"Data monitoring failed: {e}")
    
    def _monitor_functions(self):
        try:
            func_status = []
            
            for monitor_id, config in self.function_monitors.items():
                start_time = time.time()
                success = False
                error_msg = ""
                
                try:
                    result = config['test_function']()
                    success = result.get('success', False)
                    error_msg = result.get('message', "")
                except Exception as e:
                    success = False
                    error_msg = str(e)
                
                response_time = time.time() - start_time
                
                func_status.append({
                    'monitor_id': monitor_id,
                    'function_name': config['name'],
                    'module': config['module'],
                    'status': 'ok' if success else 'error',
                    'response_time': round(response_time, 3),
                    'error_message': error_msg
                })
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                for func in func_status:
                    cursor.execute('SELECT id, error_count, success_rate FROM function_monitor WHERE function_name = ?', (func['function_name'],))
                    existing = cursor.fetchone()
                    
                    if existing:
                        error_count = existing[1] + (0 if func['status'] == 'ok' else 1)
                        total_checks = error_count + 1
                        success_rate = (total_checks - error_count) / total_checks * 100
                        
                        cursor.execute('''
                            UPDATE function_monitor SET 
                                status = ?, response_time = ?, error_count = ?, success_rate = ?,
                                last_check = ?, updated_at = ?,
                                last_success = ?
                            WHERE function_name = ?
                        ''', (func['status'], func['response_time'], error_count, success_rate,
                              datetime.now().isoformat(), datetime.now().isoformat(),
                              datetime.now().isoformat() if func['status'] == 'ok' else None,
                              func['function_name']))
                    else:
                        cursor.execute('''
                            INSERT INTO function_monitor 
                            (function_name, module, status, response_time, error_count, success_rate, 
                             last_check, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (func['function_name'], func['module'], func['status'], 
                              func['response_time'], 0 if func['status'] == 'ok' else 1,
                              100.0 if func['status'] == 'ok' else 0.0,
                              datetime.now().isoformat(), datetime.now().isoformat()))
                
                conn.commit()
            
            self.health_status['functions'] = func_status
            logger.debug(f"Function monitoring completed: {len(func_status)} functions")
        except Exception as e:
            logger.error(f"Function monitoring failed: {e}")
    
    def _test_login_api(self):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('wuchenghao15',))
                if cursor.fetchone()[0] > 0:
                    return {'success': True, 'message': '用户存在'}
            return {'success': False, 'message': '用户不存在'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def _test_dashboard_api(self):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM users')
                cursor.execute('SELECT COUNT(*) FROM exams')
                return {'success': True, 'message': '仪表盘数据可查询'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def _test_database(self):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('PRAGMA integrity_check')
                result = cursor.fetchone()
                if result[0] == 'ok':
                    return {'success': True, 'message': '数据库完整性检查通过'}
                return {'success': False, 'message': f'数据库损坏: {result[0]}'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def _test_error_monitor(self):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM error_monitor')
                return {'success': True, 'message': '错误监控表正常'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def _test_system_rules(self):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM system_rules')
                count = cursor.fetchone()[0]
                if count > 0:
                    return {'success': True, 'message': f'规则数量: {count}'}
                return {'success': False, 'message': '无规则数据'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def _monitor_resources(self):
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            stats = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'disk_used': disk.used,
                'disk_total': disk.total,
                'network_sent': network.bytes_sent,
                'network_recv': network.bytes_recv
            }
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO system_resource 
                    (cpu_percent, memory_percent, disk_percent, disk_used, disk_total, 
                     network_sent, network_recv, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (stats['cpu_percent'], stats['memory_percent'], stats['disk_percent'],
                      stats['disk_used'], stats['disk_total'], stats['network_sent'],
                      stats['network_recv'], datetime.now().isoformat()))
                conn.commit()
            
            self.resource_stats = stats
            logger.debug(f"Resource monitoring completed: CPU={cpu_percent}% MEM={memory.percent}% DISK={disk.percent}%")
        except Exception as e:
            logger.error(f"Resource monitoring failed: {e}")
    
    def _check_health(self):
        try:
            alerts = []
            
            for proc in self.health_status.get('processes', []):
                if proc['status'] == 'stopped':
                    alert_id = f"proc_{proc['monitor_id']}_{int(time.time())}"
                    alerts.append({
                        'alert_id': alert_id,
                        'type': 'process',
                        'severity': 'critical' if proc.get('critical', False) else 'warning',
                        'title': f"进程停止: {proc['process_name']}",
                        'message': f"进程 {proc['process_name']} 已停止运行",
                        'source': 'process_monitor'
                    })
            
            for data in self.health_status.get('data', []):
                if data['status'] == 'critical':
                    alert_id = f"data_{data['monitor_id']}_{int(time.time())}"
                    alerts.append({
                        'alert_id': alert_id,
                        'type': 'data',
                        'severity': 'critical',
                        'title': f"数据异常: {data['name']}",
                        'message': f"表 {data['table_name']} 数据量为0，低于最低要求 {data['expected_min']}",
                        'source': 'data_monitor'
                    })
                elif data['status'] == 'warning':
                    alert_id = f"data_{data['monitor_id']}_{int(time.time())}"
                    alerts.append({
                        'alert_id': alert_id,
                        'type': 'data',
                        'severity': 'warning',
                        'title': f"数据不足: {data['name']}",
                        'message': f"表 {data['table_name']} 当前 {data['row_count']} 条记录，低于最低要求 {data['expected_min']}",
                        'source': 'data_monitor'
                    })
            
            for func in self.health_status.get('functions', []):
                if func['status'] == 'error':
                    alert_id = f"func_{func['monitor_id']}_{int(time.time())}"
                    alerts.append({
                        'alert_id': alert_id,
                        'type': 'function',
                        'severity': 'critical' if func.get('critical', False) else 'warning',
                        'title': f"功能异常: {func['function_name']}",
                        'message': f"{func['function_name']} 测试失败: {func['error_message']}",
                        'source': 'function_monitor'
                    })
            
            if self.resource_stats.get('cpu_percent', 0) > 90:
                alert_id = f"res_cpu_{int(time.time())}"
                alerts.append({
                    'alert_id': alert_id,
                    'type': 'resource',
                    'severity': 'warning',
                    'title': 'CPU使用率过高',
                    'message': f"CPU使用率达到 {self.resource_stats['cpu_percent']}%",
                    'source': 'resource_monitor'
                })
            
            if self.resource_stats.get('memory_percent', 0) > 90:
                alert_id = f"res_mem_{int(time.time())}"
                alerts.append({
                    'alert_id': alert_id,
                    'type': 'resource',
                    'severity': 'warning',
                    'title': '内存使用率过高',
                    'message': f"内存使用率达到 {self.resource_stats['memory_percent']}%",
                    'source': 'resource_monitor'
                })
            
            if self.resource_stats.get('disk_percent', 0) > 95:
                alert_id = f"res_disk_{int(time.time())}"
                alerts.append({
                    'alert_id': alert_id,
                    'type': 'resource',
                    'severity': 'critical',
                    'title': '磁盘空间不足',
                    'message': f"磁盘使用率达到 {self.resource_stats['disk_percent']}%",
                    'source': 'resource_monitor'
                })
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                for alert in alerts:
                    cursor.execute('SELECT id FROM health_alert WHERE alert_id = ? AND status = "active"', (alert['alert_id'],))
                    if not cursor.fetchone():
                        cursor.execute('''
                            INSERT INTO health_alert 
                            (alert_id, type, severity, title, message, source, status, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (alert['alert_id'], alert['type'], alert['severity'],
                              alert['title'], alert['message'], alert['source'],
                              'active', datetime.now().isoformat()))
                
                conn.commit()
            
            if alerts:
                logger.warning(f"Health check: {len(alerts)} alerts detected")
        except Exception as e:
            logger.error(f"Health check failed: {e}")
    
    def get_system_status(self):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT process_name, status, cpu_percent, memory_percent, uptime FROM process_monitor')
                processes = [dict(zip(['process_name', 'status', 'cpu_percent', 'memory_percent', 'uptime'], row)) 
                           for row in cursor.fetchall()]
                
                cursor.execute('SELECT table_name, row_count, expected_min, status FROM data_monitor')
                data = [dict(zip(['table_name', 'row_count', 'expected_min', 'status'], row)) 
                       for row in cursor.fetchall()]
                
                cursor.execute('SELECT function_name, status, response_time, success_rate FROM function_monitor')
                functions = [dict(zip(['function_name', 'status', 'response_time', 'success_rate'], row)) 
                           for row in cursor.fetchall()]
                
                cursor.execute('SELECT cpu_percent, memory_percent, disk_percent, timestamp FROM system_resource ORDER BY id DESC LIMIT 1')
                resources = cursor.fetchone()
                
                cursor.execute('SELECT * FROM health_alert WHERE status = "active" ORDER BY created_at DESC LIMIT 20')
                alerts = []
                for row in cursor.fetchall():
                    alerts.append({
                        'id': row[0],
                        'alert_id': row[1],
                        'type': row[2],
                        'severity': row[3],
                        'title': row[4],
                        'message': row[5],
                        'source': row[6],
                        'status': row[7],
                        'created_at': row[9]
                    })
                
                resource_dict = {}
                if resources:
                    resource_dict = {
                        'cpu_percent': resources[0],
                        'memory_percent': resources[1],
                        'disk_percent': resources[2],
                        'timestamp': resources[3]
                    }
                
                return {
                    'processes': processes,
                    'data': data,
                    'functions': functions,
                    'resources': resource_dict,
                    'alerts': alerts,
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {}
    
    def acknowledge_alert(self, alert_id):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE health_alert SET status = 'acknowledged', acknowledged = 'yes', resolved_at = ? 
                    WHERE alert_id = ?
                ''', (datetime.now().isoformat(), alert_id))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to acknowledge alert: {e}")
            return False
    
    def resolve_alert(self, alert_id):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE health_alert SET status = 'resolved', resolved_at = ? 
                    WHERE alert_id = ?
                ''', (datetime.now().isoformat(), alert_id))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to resolve alert: {e}")
            return False

system_monitor = None

def get_system_monitor():
    global system_monitor
    if system_monitor is None:
        system_monitor = SystemMonitorAgent()
    return system_monitor

if __name__ == '__main__':
    monitor = SystemMonitorAgent()
    logger.info("AI System Monitor Agent running...")
    
    while True:
        time.sleep(30)
        status = monitor.get_system_status()
        logger.info(f"System status - Processes: {len(status.get('processes', []))}, Alerts: {len(status.get('alerts', []))}")