# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI性能监控模块 - 实时监控系统性能并提供优化建议
"""

import logging
logger = logging.getLogger(__name__)
import os
import psutil
import time
import sqlite3
from datetime import datetime
from collections import defaultdict, deque
import sys

class AIPerformanceMonitor:
    """AI性能监控器,实现系统资源和应用性能的实时监控"""

    def __init__(self, db_path='ai_performance.db', monitor_interval=5):
        """初始化AI性能监控器

        Args:
            db_path: 数据库路径
            monitor_interval: 监控间隔(秒)
        """
        self.db_path = db_path
        self.monitor_interval = monitor_interval
        self._init_db()

        self.performance_thresholds = {
            'cpu': {
                'warning': 70.0,
                'critical': 90.0
            },
            'memory': {
                'warning': 75.0,
                'critical': 90.0
            },
            'disk': {
                'warning': 80.0,
                'critical': 90.0
            },
            'network': {
                'warning': 80.0,
                'critical': 95.0
            },
            'response_time': {
                'warning': 1.0,
                'critical': 3.0
            },
            'error_rate': {
                'warning': 5.0,
                'critical': 10.0
            }
        }

        self.history_data = defaultdict(lambda: deque(maxlen=100))

        self.app_performance = {
            'request_count': 0,
            'error_count': 0,
            'total_response_time': 0,
            'avg_response_time': 0,
            'error_rate': 0.0,
            'start_time': datetime.now()
        }

    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            cpu_usage REAL NOT NULL,
            memory_usage REAL NOT NULL,
            disk_usage REAL NOT NULL,
            network_sent REAL NOT NULL,
            network_recv REAL NOT NULL,
            load_average_1 REAL NOT NULL,
            load_average_5 REAL NOT NULL,
            load_average_15 REAL NOT NULL,
            metadata TEXT
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            request_count INTEGER NOT NULL,
            error_count INTEGER NOT NULL,
            avg_response_time REAL NOT NULL,
            error_rate REAL NOT NULL,
            endpoint TEXT NOT NULL,
            method TEXT NOT NULL,
            metadata TEXT
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_anomalies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anomaly_id TEXT UNIQUE NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            type TEXT NOT NULL,
            severity TEXT NOT NULL,
            metric TEXT NOT NULL,
            current_value REAL NOT NULL,
            threshold_value REAL,
            description TEXT NOT NULL,
            suggestion TEXT,
            metadata TEXT
            )
            ''')

            cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_perf_timestamp ON system_performance(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_app_perf_timestamp ON app_performance(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_anomaly_type ON performance_anomalies(type)')

            conn.commit()

    def get_system_stats(self):
        """获取系统资源使用情况

        Returns:
            dict: 系统资源使用情况
        """
        cpu_usage = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        memory_usage = memory.percent

        disk = psutil.disk_usage('/')
        disk_usage = disk.percent

        network = psutil.net_io_counters()
        network_sent = network.bytes_sent / (1024 * 1024)
        network_recv = network.bytes_recv / (1024 * 1024)

        load_average = psutil.getloadavg()

        return {
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'disk_usage': disk_usage,
            'network_sent': round(network_sent, 2),
            'network_recv': round(network_recv, 2),
            'load_average_1': round(load_average[0], 2),
            'load_average_5': round(load_average[1], 2),
            'load_average_15': round(load_average[2], 2),
            'timestamp': datetime.now().isoformat()
        }

    def get_process_stats(self):
        """获取当前进程的资源使用情况

        Returns:
            dict: 进程资源使用情况
        """
        process = psutil.Process(os.getpid())

        with process.oneshot():
            cpu_usage = process.cpu_percent(interval=0.1)
            memory = process.memory_percent()
            open_files = len(process.open_files())
            threads = process.num_threads()
            try:
                connections = len(process.connections())
            except Exception:
                connections = 0

        return {
            'cpu_usage': cpu_usage,
            'memory_usage': memory,
            'open_files': open_files,
            'threads': threads,
            'connections': connections,
            'timestamp': datetime.now().isoformat()
        }

    def record_request(self, endpoint, method, response_time, is_error=False):
        """记录请求性能数据

        Args:
            endpoint: 请求端点
            method: 请求方法
            response_time: 响应时间(秒)
            is_error: 是否错误
        """
        self.app_performance['request_count'] += 1
        if is_error:
            self.app_performance['error_count'] += 1
        self.app_performance['total_response_time'] += response_time

        self.app_performance['avg_response_time'] = (
            self.app_performance['total_response_time'] / self.app_performance['request_count']
        )

        self.app_performance['error_rate'] = (
            (self.app_performance['error_count'] / self.app_performance['request_count']) * 100
        )

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO app_performance
                    (request_count, error_count, avg_response_time, error_rate, endpoint, method)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    self.app_performance['request_count'],
                    self.app_performance['error_count'],
                    self.app_performance['avg_response_time'],
                    self.app_performance['error_rate'],
                    endpoint,
                    method
                ))
                conn.commit()
            except Exception as e:
                logger.error(f"Error recording request: {str(e)}")

        self._detect_performance_anomaly('response_time', self.app_performance['avg_response_time'], endpoint)

    def _detect_performance_anomaly(self, metric, value, context=None):
        """检测性能异常

        Args:
            metric: 性能指标
            value: 指标值
            context: 上下文信息

        Returns:
            tuple: (是否异常, 异常详情)
        """
        thresholds = self.performance_thresholds.get(metric, {})
        if not thresholds:
            return False, None

        severity = None
        if value > thresholds.get('critical', float('inf')):
            severity = 'critical'
        elif value > thresholds.get('warning', float('inf')):
            severity = 'warning'
        else:
            return False, None

        anomaly_id = f"anomaly_{int(time.time())}_{metric}_{hash(str(context))}"
        description, suggestion = self._generate_anomaly_details(metric, value, thresholds, context)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO performance_anomalies
                    (anomaly_id, type, severity, metric, current_value, threshold_value, description, suggestion, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    anomaly_id,
                    'performance',
                    severity,
                    metric,
                    value,
                    thresholds[severity],
                    description,
                    suggestion,
                    str({'context': context})
                ))
                conn.commit()
            except Exception as e:
                logger.error(f"Error recording anomaly: {str(e)}")

        return True, {
            'type': 'performance',
            'severity': severity,
            'metric': metric,
            'current_value': value,
            'threshold_value': thresholds[severity],
            'description': description,
            'suggestion': suggestion,
            'timestamp': datetime.now().isoformat()
        }

    def _generate_anomaly_details(self, metric, value, thresholds, context=None):
        """生成异常描述和建议

        Args:
            metric: 性能指标
            value: 指标值
            thresholds: 阈值
            context: 上下文

        Returns:
            tuple: (描述, 建议)
        """
        threshold_key = None
        if value > thresholds.get('critical', 0):
            threshold_key = 'critical'
        elif value > thresholds.get('warning', 0):
            threshold_key = 'warning'

        if threshold_key is None:
            return "未知指标异常", "请检查系统或应用配置"

        threshold_value = thresholds[threshold_key]

        metric_details = {
            'cpu': {
                'description': f'CPU使用率过高: 当前值 {value:.1f}%, 超过阈值 {threshold_value:.1f}%',
                'suggestion': '检查系统中是否有占用大量CPU的进程,考虑优化代码或增加CPU资源'
            },
            'memory': {
                'description': f'内存使用率过高: 当前值 {value:.1f}%, 超过阈值 {threshold_value:.1f}%',
                'suggestion': '检查内存泄漏,考虑增加内存或优化内存使用'
            },
            'disk': {
                'description': f'磁盘使用率过高: 当前值 {value:.1f}%, 超过阈值 {threshold_value:.1f}%',
                'suggestion': '清理磁盘空间或考虑增加磁盘容量'
            },
            'response_time': {
                'description': f'响应时间过长: 当前值 {value:.3f}秒, 超过阈值 {threshold_value:.1f}秒',
                'suggestion': '优化数据库查询,增加缓存,或考虑增加服务器资源'
            },
            'error_rate': {
                'description': f'错误率过高: 当前值 {value:.1f}%, 超过阈值 {threshold_value:.1f}%',
                'suggestion': '检查错误日志,修复应用bug,或增加错误处理机制'
            }
        }

        details = metric_details.get(metric, {})
        return details.get('description', f'{metric} 异常'), details.get('suggestion', '请检查系统或应用配置')

    def get_performance_report(self, time_window=3600):
        """生成性能报告

        Args:
            time_window: 时间窗口(秒)

        Returns:
            dict: 性能报告
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            start_time = datetime.fromtimestamp(time.time() - time_window).isoformat()
            end_time = datetime.now().isoformat()

            cursor.execute('''
                SELECT
                    AVG(cpu_usage) as avg_cpu,
                    MAX(cpu_usage) as max_cpu,
                    AVG(memory_usage) as avg_memory,
                    MAX(memory_usage) as max_memory,
                    AVG(disk_usage) as avg_disk,
                    MAX(disk_usage) as max_disk,
                    AVG(network_sent) as avg_network_sent,
                    AVG(network_recv) as avg_network_recv
                FROM system_performance
                WHERE timestamp BETWEEN ? AND ?
            ''', (start_time, end_time))
            system_stats = cursor.fetchone()

            cursor.execute('''
                SELECT
                    SUM(request_count) as total_requests,
                    SUM(error_count) as total_errors,
                    AVG(avg_response_time) as avg_response_time,
                    AVG(error_rate) as avg_error_rate
                FROM app_performance
                WHERE timestamp BETWEEN ? AND ?
            ''', (start_time, end_time))
            app_stats = cursor.fetchone()

            cursor.execute('''
                SELECT * FROM performance_anomalies
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY severity DESC, timestamp DESC
            ''', (start_time, end_time))
            anomalies = []
            for row in cursor.fetchall():
                anomalies.append({
                    'anomaly_id': row[1],
                    'timestamp': row[2],
                    'type': row[3],
                    'severity': row[4],
                    'metric': row[5],
                    'current_value': row[6],
                    'threshold_value': row[7],
                    'description': row[8],
                    'suggestion': row[9],
                    'metadata': eval(row[10]) if row[10] else {}
                })

            cursor.execute('''
                SELECT
                    endpoint,
                    method,
                    SUM(request_count) as total_requests,
                    AVG(avg_response_time) as avg_response_time,
                    AVG(error_rate) as avg_error_rate
                FROM app_performance
                WHERE timestamp BETWEEN ? AND ?
                GROUP BY endpoint, method
                ORDER BY total_requests DESC
                LIMIT 10
            ''', (start_time, end_time))
            endpoint_performance = []
            for row in cursor.fetchall():
                endpoint_performance.append({
                    'endpoint': row[0],
                    'method': row[1],
                    'total_requests': row[2],
                    'avg_response_time': row[3],
                    'avg_error_rate': row[4]
                })

            suggestions = self._generate_optimization_suggestions(
                system_stats, app_stats, anomalies
            )

            return {
                'success': True,
                'report_id': f"perf_report_{int(time.time())}",
                'start_time': start_time,
                'end_time': end_time,
                'time_window': time_window,
                'system_performance': {
                    'avg_cpu_usage': round(system_stats[0], 2) if system_stats else 0,
                    'max_cpu_usage': round(system_stats[1], 2) if system_stats else 0,
                    'avg_memory_usage': round(system_stats[2], 2) if system_stats else 0,
                    'max_memory_usage': round(system_stats[3], 2) if system_stats else 0,
                    'avg_disk_usage': round(system_stats[4], 2) if system_stats else 0,
                    'max_disk_usage': round(system_stats[5], 2) if system_stats else 0,
                },
                'app_performance': {
                    'total_requests': app_stats[0] or 0,
                    'total_errors': app_stats[1] or 0,
                    'avg_response_time': round(app_stats[2] or 0, 3),
                    'avg_error_rate': round(app_stats[3] or 0, 2)
                },
                'endpoint_performance': endpoint_performance,
                'anomalies': anomalies,
                'optimization_suggestions': suggestions,
                'generated_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error generating performance report: {str(e)}")
            return {
                'success': False,
                'message': f'生成报告失败: {str(e)}',
                'details': {}
            }
        finally:
            conn.close()

    def _generate_optimization_suggestions(self, system_stats, app_stats, anomalies):
        """生成优化建议

        Args:
            system_stats: 系统统计数据
            app_stats: 应用统计数据
            anomalies: 异常列表

        Returns:
            list: 优化建议
        """
        suggestions = []
        if system_stats:
            avg_cpu, max_cpu, avg_memory, max_memory, avg_disk, max_disk, _, _ = system_stats

            if max_cpu > 80:
                suggestions.append({
                    'type': 'system',
                    'priority': 'high',
                    'title': 'CPU使用率过高',
                    'description': f'最大CPU使用率达到 {max_cpu:.1f}%, 平均值 {avg_cpu:.1f}%',
                    'suggestion': '考虑增加CPU资源或优化占用CPU的进程',
                    'metric': 'cpu_usage'
                })

            if max_memory > 85:
                suggestions.append({
                    'type': 'system',
                    'priority': 'high',
                    'title': '内存使用率过高',
                    'description': f'最大内存使用率达到 {max_memory:.1f}%, 平均值 {avg_memory:.1f}%',
                    'suggestion': '检查内存泄漏,考虑增加内存或优化内存使用',
                    'metric': 'memory_usage'
                })

            if max_disk > 90:
                suggestions.append({
                    'type': 'system',
                    'priority': 'medium',
                    'title': '磁盘使用率过高',
                    'description': f'最大磁盘使用率达到 {max_disk:.1f}%, 平均值 {avg_disk:.1f}%',
                    'suggestion': '清理磁盘空间或考虑增加磁盘容量',
                    'metric': 'disk_usage'
                })

        if app_stats:
            total_requests, total_errors, avg_response_time, avg_error_rate = app_stats
            if avg_response_time > 1.0:
                suggestions.append({
                    'type': 'application',
                    'priority': 'high',
                    'title': '响应时间过长',
                    'description': f'平均响应时间达到 {avg_response_time:.3f} 秒',
                    'suggestion': '优化数据库查询,增加缓存,或考虑增加服务器资源',
                    'metric': 'response_time'
                })

            if avg_error_rate > 5.0:
                suggestions.append({
                    'type': 'application',
                    'priority': 'high',
                    'title': '错误率过高',
                    'description': f'平均错误率达到 {avg_error_rate:.1f}%',
                    'suggestion': '检查错误日志,修复应用bug,或增加错误处理机制',
                    'metric': 'error_rate'
                })

        if anomalies:
            anomaly_types = {}
            for anomaly in anomalies:
                anomaly_types[anomaly['metric']] = anomaly_types.get(anomaly['metric'], 0) + 1

            for metric, count in anomaly_types.items():
                if count > 3:
                    suggestions.append({
                        'type': 'anomaly',
                        'priority': 'medium',
                        'title': f'{metric} 频繁异常',
                        'description': f'在监控周期内 {metric} 出现 {count} 次异常',
                        'suggestion': f'重点优化 {metric} 相关配置或代码',
                        'metric': metric
                    })

        return suggestions

    def run_monitor(self, duration=3600):
        """运行性能监控(测试用)

        Args:
            duration: 监控持续时间(秒)
        """
        end_time = time.time() + duration

        while time.time() < end_time:
            system_stats = self.get_system_stats()

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute('''
                        INSERT INTO system_performance
                        (cpu_usage, memory_usage, disk_usage, network_sent, network_recv,
                        load_average_1, load_average_5, load_average_15)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        system_stats['cpu_usage'],
                        system_stats['memory_usage'],
                        system_stats['disk_usage'],
                        system_stats['network_sent'],
                        system_stats['network_recv'],
                        system_stats['load_average_1'],
                        system_stats['load_average_5'],
                        system_stats['load_average_15']
                    ))
                    conn.commit()
                except Exception as e:
                    logger.error(f"Error saving system stats: {str(e)}")

            self._detect_performance_anomaly('cpu', system_stats['cpu_usage'])
            self._detect_performance_anomaly('memory', system_stats['memory_usage'])

            print(f"监控 - CPU: {system_stats['cpu_usage']:.1f}% | 内存: {system_stats['memory_usage']:.1f}% | 磁盘: {system_stats['disk_usage']:.1f}%")
            time.sleep(self.monitor_interval)

    def get_current_status(self):
        """获取当前性能状态

        Returns:
            dict: 当前性能状态
        """
        system_stats = self.get_system_stats()
        process_stats = self.get_process_stats()

        app_perf_copy = self.app_performance.copy()
        if isinstance(app_perf_copy.get('start_time'), datetime):
            app_perf_copy['start_time'] = app_perf_copy['start_time'].isoformat()

        return {
            'system': system_stats,
            'process': process_stats,
            'application': app_perf_copy,
            'timestamp': datetime.now().isoformat()
        }


global_performance_monitor = None

def get_performance_monitor():
    """获取全局AI性能监控器实例

    Returns:
        AIPerformanceMonitor: AI性能监控器实例
    """
    global global_performance_monitor
    if global_performance_monitor is None:
        global_performance_monitor = AIPerformanceMonitor()
    return global_performance_monitor


if __name__ == '__main__':
    perf_monitor = AIPerformanceMonitor()
    print("AI性能监控器测试")

    print("\n1. 当前系统状态:")
    system_status = perf_monitor.get_current_status()
    print(str(system_status))

    print("\n2. 记录测试请求:")
    perf_monitor.record_request('/api/test', 'GET', 0.123)

    report = perf_monitor.get_performance_report(time_window=3600)
    print("\n3. 性能报告:")
    print(str(report))

    print("\n4. 运行监控(5秒)...")
    perf_monitor.run_monitor(duration=5)

    print("\n性能监控测试完成!")
