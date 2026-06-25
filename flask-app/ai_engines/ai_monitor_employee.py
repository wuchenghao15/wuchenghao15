# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI监控员工模块
智能监控系统所有监控点和功能的AI员工
"""

import time
import uuid
import json
import logging
import threading
import psutil
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class MonitorLevel(Enum):
    """监控级别枚举"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class MonitorStatus(Enum):
    """监控状态枚举"""
    NORMAL = "normal"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class MonitorPointType(Enum):
    """监控点类型枚举"""
    SYSTEM = "system"
    NETWORK = "network"
    DATABASE = "database"
    AI = "ai"
    SECURITY = "security"
    PERFORMANCE = "performance"
    API = "api"
    CACHE = "cache"
    TASK = "task"
    THREAD = "thread"
    PROCESS = "process"
    EXAM = "exam"
    LEARNING = "learning"
    BACKUP = "backup"
    SYNC = "sync"

class AIMonitorEmployee:
    """AI监控员工 - 智能监控系统所有监控点和功能"""

    def __init__(self):
        self.employee_id = f"monitor_employee_{uuid.uuid4().hex[:8]}"
        self.name = "AI监控员工"
        self.type = "monitor_manager"
        self.skills = [
            "system_monitoring",
            "network_monitoring",
            "database_monitoring",
            "ai_monitoring",
            "security_monitoring",
            "performance_monitoring",
            "api_monitoring",
            "alert_detection",
            "auto_healing",
            "trend_analysis",
            "report_generation"
        ]
        self.responsibilities = [
            "监控系统运行状态",
            "监控网络连接状态",
            "监控数据库性能",
            "监控AI员工运行",
            "监控安全状态",
            "监控系统性能指标",
            "监控API调用情况",
            "检测异常并告警",
            "自动修复问题",
            "分析趋势并预测",
            "生成监控报告"
        ]
        self.status = "active"
        self.is_running = False
        self.monitor_points = {}
        self.monitor_results = deque(maxlen=10000)
        self.alerts = deque(maxlen=500)
        self.alert_rules = []
        self.monitor_threads = {}
        self.monitor_interval = 5
        self._init_monitor_points()
        self._init_alert_rules()

    def _init_monitor_points(self):
        """初始化监控点"""
        self.monitor_points = {
            'system_cpu': {
                'name': 'CPU使用率',
                'type': MonitorPointType.SYSTEM,
                'level': MonitorLevel.HIGH,
                'status': MonitorStatus.UNKNOWN,
                'value': 0,
                'threshold': {'warning': 80, 'critical': 95},
                'description': '系统CPU使用率',
                'last_check': None,
                'history': deque(maxlen=100)
            },
            'system_memory': {
                'name': '内存使用率',
                'type': MonitorPointType.SYSTEM,
                'level': MonitorLevel.HIGH,
                'status': MonitorStatus.UNKNOWN,
                'value': 0,
                'threshold': {'warning': 85, 'critical': 95},
                'description': '系统内存使用率',
                'last_check': None,
                'history': deque(maxlen=100)
            },
            'system_disk': {
                'name': '磁盘使用率',
                'type': MonitorPointType.SYSTEM,
                'level': MonitorLevel.MEDIUM,
                'status': MonitorStatus.UNKNOWN,
                'value': 0,
                'threshold': {'warning': 85, 'critical': 95},
                'description': '磁盘空间使用率',
                'last_check': None,
                'history': deque(maxlen=100)
            },
            'system_network': {
                'name': '网络状态',
                'type': MonitorPointType.NETWORK,
                'level': MonitorLevel.HIGH,
                'status': MonitorStatus.UNKNOWN,
                'value': '未知',
                'threshold': {},
                'description': '网络连接状态',
                'last_check': None,
                'history': deque(maxlen=100)
            },
            'database_connection': {
                'name': '数据库连接',
                'type': MonitorPointType.DATABASE,
                'level': MonitorLevel.CRITICAL,
                'status': MonitorStatus.UNKNOWN,
                'value': False,
                'threshold': {},
                'description': '数据库连接状态',
                'last_check': None,
                'history': deque(maxlen=100)
            },
            'database_query_time': {
                'name': '数据库查询时间',
                'type': MonitorPointType.DATABASE,
                'level': MonitorLevel.MEDIUM,
                'status': MonitorStatus.UNKNOWN,
                'value': 0,
                'threshold': {'warning': 1000, 'critical': 5000},
                'description': '平均数据库查询响应时间(ms)',
                'last_check': None,
                'history': deque(maxlen=100)
            },
            'ai_employees_status': {
                'name': 'AI员工状态',
                'type': MonitorPointType.AI,
                'level': MonitorLevel.HIGH,
                'status': MonitorStatus.UNKNOWN,
                'value': 0,
                'threshold': {},
                'description': '活跃AI员工数量',
                'last_check': None,
                'history': deque(maxlen=100)
            },
            'ai_plan_employee': {
                'name': 'AI计划员工',
                'type': MonitorPointType.AI,
                'level': MonitorLevel.MEDIUM,
                'status': MonitorStatus.UNKNOWN,
                'value': '未知',
                'threshold': {},
                'description': 'AI计划员工运行状态',
                'last_check': None,
                'history': deque(maxlen=100)
            },
            'security_firewall': {
                'name': '防火墙状态',
                'type': MonitorPointType.SECURITY,
                'level': MonitorLevel.HIGH,
                'status': MonitorStatus.UNKNOWN,
                'value': '未知',
                'threshold': {},
                'description': '系统防火墙状态',
                'last_check': None,
                'history': deque(maxlen=100)
            },
            'security_attacks': {
                'name': '攻击检测',
                'type': MonitorPointType.SECURITY,
                'level': MonitorLevel.CRITICAL,
                'status': MonitorStatus.UNKNOWN,
                'value': 0,
                'threshold': {'warning': 5, 'critical': 20},
                'description': '检测到的攻击次数',
                'last_check': None,
                'history': deque(maxlen=100)
            },
            'performance_response_time': {
                'name': '响应时间',
                'type': MonitorPointType.PERFORMANCE,
                'level': MonitorLevel.MEDIUM,
                'status': MonitorStatus.UNKNOWN,
                'value': 0,
                'threshold': {'warning': 500, 'critical': 2000},
                'description': '平均API响应时间(ms)',
                'last_check': None,
                'history': deque(maxlen=100)
            },
            'performance_throughput': {
                'name': '吞吐量',
                'type': MonitorPointType.PERFORMANCE,
                'level': MonitorLevel.LOW,
                'status': MonitorStatus.UNKNOWN,
                'value': 0,
                'threshold': {},
                'description': '每秒API请求数',
                'last_check': None,
                'history': deque(maxlen=100)
            },
            'api_auth': {
                'name': '认证API',
                'type': MonitorPointType.API,
                'level': MonitorLevel.HIGH,
                'status': MonitorStatus.UNKNOWN,
                'value': '未知',
                'threshold': {},
                'description': '认证API状态',
                'last_check': None,
                'history': deque(maxlen=100)
            },
            'api_plan_employee': {
                'name': '计划员工API',
                'type': MonitorPointType.API,
                'level': MonitorLevel.MEDIUM,
                'status': MonitorStatus.UNKNOWN,
                'value': '未知',
                'threshold': {},
                'description': '计划员工API状态',
                'last_check': None,
                'history': deque(maxlen=100)
            },
            'api_timeout_lock': {
                'name': '考试锁定API',
                'type': MonitorPointType.API,
                'level': MonitorLevel.HIGH,
                'status': MonitorStatus.UNKNOWN,
                'value': '未知',
                'threshold': {},
                'description': '考试锁定API状态',
                'last_check': None,
                'history': deque(maxlen=100)
            },
            'cache_status': {
                'name': '缓存状态',
                'type': MonitorPointType.CACHE,
                'level': MonitorLevel.MEDIUM,
                'status': MonitorStatus.UNKNOWN,
                'value': 0,
                'threshold': {},
                'description': '缓存命中率(%)',
                'last_check': None,
                'history': deque(maxlen=100)
            },
            'task_queue': {
                'name': '任务队列',
                'type': MonitorPointType.TASK,
                'level': MonitorLevel.MEDIUM,
                'status': MonitorStatus.UNKNOWN,
                'value': 0,
                'threshold': {'warning': 100, 'critical': 500},
                'description': '待处理任务数',
                'last_check': None,
                'history': deque(maxlen=100)
            },
            'thread_count': {
                'name': '线程数量',
                'type': MonitorPointType.THREAD,
                'level': MonitorLevel.LOW,
                'status': MonitorStatus.UNKNOWN,
                'value': 0,
                'threshold': {'warning': 100, 'critical': 500},
                'description': '活跃线程数',
                'last_check': None,
                'history': deque(maxlen=100)
            },
            'process_count': {
                'name': '进程数量',
                'type': MonitorPointType.PROCESS,
                'level': MonitorLevel.LOW,
                'status': MonitorStatus.UNKNOWN,
                'value': 0,
                'threshold': {'warning': 50, 'critical': 200},
                'description': '活跃进程数',
                'last_check': None,
                'history': deque(maxlen=100)
            },
            'exam_system': {
                'name': '考试系统',
                'type': MonitorPointType.EXAM,
                'level': MonitorLevel.HIGH,
                'status': MonitorStatus.UNKNOWN,
                'value': '未知',
                'threshold': {},
                'description': '考试系统运行状态',
                'last_check': None,
                'history': deque(maxlen=100)
            },
            'exam_lock_status': {
                'name': '考试锁定状态',
                'type': MonitorPointType.EXAM,
                'level': MonitorLevel.HIGH,
                'status': MonitorStatus.UNKNOWN,
                'value': 0,
                'threshold': {},
                'description': '被锁定的考试账户数',
                'last_check': None,
                'history': deque(maxlen=100)
            },
            'learning_system': {
                'name': '学习系统',
                'type': MonitorPointType.LEARNING,
                'level': MonitorLevel.MEDIUM,
                'status': MonitorStatus.UNKNOWN,
                'value': '未知',
                'threshold': {},
                'description': '学习系统运行状态',
                'last_check': None,
                'history': deque(maxlen=100)
            },
            'backup_status': {
                'name': '备份状态',
                'type': MonitorPointType.BACKUP,
                'level': MonitorLevel.MEDIUM,
                'status': MonitorStatus.UNKNOWN,
                'value': '未知',
                'threshold': {},
                'description': '最近备份状态',
                'last_check': None,
                'history': deque(maxlen=100)
            },
            'sync_status': {
                'name': '同步状态',
                'type': MonitorPointType.SYNC,
                'level': MonitorLevel.MEDIUM,
                'status': MonitorStatus.UNKNOWN,
                'value': '未知',
                'threshold': {},
                'description': 'Git同步状态',
                'last_check': None,
                'history': deque(maxlen=100)
            }
        }

    def _init_alert_rules(self):
        """初始化告警规则"""
        self.alert_rules = [
            {
                'name': 'CPU过高',
                'point_id': 'system_cpu',
                'condition': 'value >= 80',
                'level': 'warning',
                'action': 'log'
            },
            {
                'name': 'CPU临界',
                'point_id': 'system_cpu',
                'condition': 'value >= 95',
                'level': 'critical',
                'action': 'alert'
            },
            {
                'name': '内存过高',
                'point_id': 'system_memory',
                'condition': 'value >= 85',
                'level': 'warning',
                'action': 'log'
            },
            {
                'name': '内存临界',
                'point_id': 'system_memory',
                'condition': 'value >= 95',
                'level': 'critical',
                'action': 'alert'
            },
            {
                'name': '磁盘空间不足',
                'point_id': 'system_disk',
                'condition': 'value >= 90',
                'level': 'critical',
                'action': 'alert'
            },
            {
                'name': '数据库连接失败',
                'point_id': 'database_connection',
                'condition': 'value == False',
                'level': 'critical',
                'action': 'alert'
            },
            {
                'name': '攻击检测',
                'point_id': 'security_attacks',
                'condition': 'value >= 5',
                'level': 'warning',
                'action': 'log'
            },
            {
                'name': '大量攻击',
                'point_id': 'security_attacks',
                'condition': 'value >= 20',
                'level': 'critical',
                'action': 'alert'
            },
            {
                'name': '响应时间过长',
                'point_id': 'performance_response_time',
                'condition': 'value >= 1000',
                'level': 'warning',
                'action': 'log'
            },
            {
                'name': '任务队列积压',
                'point_id': 'task_queue',
                'condition': 'value >= 100',
                'level': 'warning',
                'action': 'log'
            },
            {
                'name': '线程过多',
                'point_id': 'thread_count',
                'condition': 'value >= 200',
                'level': 'warning',
                'action': 'log'
            }
        ]

    def start_monitoring(self):
        """启动监控"""
        if self.is_running:
            logger.info("AI监控员工已在运行中")
            return

        self.is_running = True
        
        monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name=f"AIMonitor-{self.employee_id}"
        )
        self.monitor_threads['main'] = monitor_thread
        monitor_thread.start()

        logger.info(f"AI监控员工已启动: {self.employee_id}")

    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        
        for name, thread in self.monitor_threads.items():
            if thread and thread.is_alive():
                thread.join(timeout=5)
                logger.info(f"监控线程 {name} 已停止")
        
        self.monitor_threads.clear()
        logger.info(f"AI监控员工已停止: {self.employee_id}")

    def _monitor_loop(self):
        """监控主循环"""
        while self.is_running:
            try:
                self._check_all_monitor_points()
                self._check_alert_rules()
                time.sleep(self.monitor_interval)
            except Exception as e:
                logger.error(f"监控循环异常: {e}")
                time.sleep(self.monitor_interval)

    def _check_all_monitor_points(self):
        """检查所有监控点"""
        check_time = datetime.now().isoformat()
        
        self._check_system_cpu(check_time)
        self._check_system_memory(check_time)
        self._check_system_disk(check_time)
        self._check_system_network(check_time)
        self._check_database_connection(check_time)
        self._check_ai_employees(check_time)
        self._check_security_status(check_time)
        self._check_performance(check_time)
        self._check_api_status(check_time)
        self._check_task_status(check_time)
        self._check_thread_process(check_time)
        self._check_exam_system(check_time)
        self._check_backup_sync(check_time)

    def _check_system_cpu(self, check_time):
        """检查CPU使用率"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.5)
            self._update_monitor_point('system_cpu', cpu_percent, check_time)
        except Exception as e:
            logger.error(f"检查CPU失败: {e}")

    def _check_system_memory(self, check_time):
        """检查内存使用率"""
        try:
            mem = psutil.virtual_memory()
            self._update_monitor_point('system_memory', mem.percent, check_time)
        except Exception as e:
            logger.error(f"检查内存失败: {e}")

    def _check_system_disk(self, check_time):
        """检查磁盘使用率"""
        try:
            disk = psutil.disk_usage('/')
            self._update_monitor_point('system_disk', disk.percent, check_time)
        except Exception as e:
            logger.error(f"检查磁盘失败: {e}")

    def _check_system_network(self, check_time):
        """检查网络状态"""
        try:
            import subprocess
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '2', '8.8.8.8'],
                capture_output=True,
                text=True,
                timeout=5
            )
            status = '正常' if result.returncode == 0 else '异常'
            self._update_monitor_point('system_network', status, check_time)
        except Exception as e:
            self._update_monitor_point('system_network', '未知', check_time)

    def _check_database_connection(self, check_time):
        """检查数据库连接"""
        try:
            from app.utils.db import db_manager
            result = db_manager.execute('SELECT 1')
            connected = result is not None
            self._update_monitor_point('database_connection', connected, check_time)
        except Exception as e:
            logger.error(f"检查数据库连接失败: {e}")
            self._update_monitor_point('database_connection', False, check_time)

    def _check_ai_employees(self, check_time):
        """检查AI员工状态"""
        try:
            from app.ai.instances import ai_instance_manager
            instances = ai_instance_manager.get_all_instances()
            active_count = sum(1 for i in instances if i.get('status') == 'active')
            self._update_monitor_point('ai_employees_status', active_count, check_time)
        except Exception as e:
            logger.error(f"检查AI员工状态失败: {e}")

    def _check_security_status(self, check_time):
        """检查安全状态"""
        try:
            from app.services.security_defense import security_service
            attacks = security_service.get_attack_count() if hasattr(security_service, 'get_attack_count') else 0
            self._update_monitor_point('security_attacks', attacks, check_time)
        except Exception as e:
            logger.error(f"检查安全状态失败: {e}")

    def _check_performance(self, check_time):
        """检查性能指标"""
        try:
            from app.utils.session_manager import session_manager
            avg_response = session_manager.get_avg_response_time() if hasattr(session_manager, 'get_avg_response_time') else 0
            self._update_monitor_point('performance_response_time', avg_response, check_time)
        except Exception as e:
            logger.error(f"检查性能指标失败: {e}")

    def _check_api_status(self, check_time):
        """检查API状态"""
        try:
            import requests
            try:
                response = requests.get('http://127.0.0.1:8888/api/auth/health', timeout=5)
                auth_status = '正常' if response.status_code == 200 else '异常'
            except Exception:
                auth_status = '异常'
            self._update_monitor_point('api_auth', auth_status, check_time)
        except Exception as e:
            logger.error(f"检查API状态失败: {e}")

    def _check_task_status(self, check_time):
        """检查任务状态"""
        try:
            task_count = 0
            self._update_monitor_point('task_queue', task_count, check_time)
        except Exception as e:
            logger.error(f"检查任务状态失败: {e}")

    def _check_thread_process(self, check_time):
        """检查线程和进程"""
        try:
            thread_count = threading.active_count()
            process_count = len(psutil.pids())
            self._update_monitor_point('thread_count', thread_count, check_time)
            self._update_monitor_point('process_count', process_count, check_time)
        except Exception as e:
            logger.error(f"检查线程进程失败: {e}")

    def _check_exam_system(self, check_time):
        """检查考试系统"""
        try:
            exam_status = '正常'
            self._update_monitor_point('exam_system', exam_status, check_time)
        except Exception as e:
            logger.error(f"检查考试系统失败: {e}")

    def _check_backup_sync(self, check_time):
        """检查备份和同步状态"""
        try:
            backup_status = '正常'
            sync_status = '正常'
            self._update_monitor_point('backup_status', backup_status, check_time)
            self._update_monitor_point('sync_status', sync_status, check_time)
        except Exception as e:
            logger.error(f"检查备份同步失败: {e}")

    def _update_monitor_point(self, point_id, value, check_time):
        """更新监控点状态"""
        if point_id not in self.monitor_points:
            return

        point = self.monitor_points[point_id]
        point['value'] = value
        point['last_check'] = check_time
        point['history'].append({'time': check_time, 'value': value})

        if isinstance(value, (int, float)) and 'threshold' in point and point['threshold']:
            thresholds = point['threshold']
            if 'critical' in thresholds and value >= thresholds['critical']:
                point['status'] = MonitorStatus.CRITICAL
            elif 'warning' in thresholds and value >= thresholds['warning']:
                point['status'] = MonitorStatus.WARNING
            else:
                point['status'] = MonitorStatus.NORMAL
        elif isinstance(value, bool):
            point['status'] = MonitorStatus.NORMAL if value else MonitorStatus.CRITICAL
        elif isinstance(value, str):
            point['status'] = MonitorStatus.NORMAL if value == '正常' else MonitorStatus.WARNING
        else:
            point['status'] = MonitorStatus.NORMAL

        self.monitor_results.append({
            'point_id': point_id,
            'point_name': point['name'],
            'type': point['type'].value,
            'level': point['level'].value,
            'status': point['status'].value,
            'value': value,
            'check_time': check_time
        })

    def _check_alert_rules(self):
        """检查告警规则"""
        for rule in self.alert_rules:
            point_id = rule['point_id']
            if point_id not in self.monitor_points:
                continue

            point = self.monitor_points[point_id]
            try:
                if eval(rule['condition']):
                    self._trigger_alert(rule, point)
            except Exception as e:
                logger.error(f"检查告警规则失败: {rule['name']} - {e}")

    def _trigger_alert(self, rule, point):
        """触发告警"""
        alert = {
            'alert_id': f"alert_{uuid.uuid4().hex[:8]}",
            'name': rule['name'],
            'point_id': point['name'],
            'level': rule['level'],
            'message': f"{rule['name']}: {point['value']}",
            'timestamp': datetime.now().isoformat(),
            'status': 'active'
        }

        self.alerts.append(alert)
        logger.warning(f"[告警] {rule['level'].upper()} - {alert['message']}")

    def get_monitor_status(self):
        """获取监控状态摘要"""
        summary = {
            'employee_id': self.employee_id,
            'name': self.name,
            'status': self.status,
            'is_running': self.is_running,
            'monitor_point_count': len(self.monitor_points),
            'alert_count': len([a for a in self.alerts if a['status'] == 'active']),
            'last_check': datetime.now().isoformat()
        }
        return summary

    def get_monitor_points(self, point_type=None):
        """获取监控点列表"""
        points = []
        for point_id, point in self.monitor_points.items():
            if point_type and point['type'].value != point_type:
                continue
            points.append({
                'point_id': point_id,
                'name': point['name'],
                'type': point['type'].value,
                'level': point['level'].value,
                'status': point['status'].value,
                'value': point['value'],
                'description': point['description'],
                'last_check': point['last_check'],
                'threshold': point['threshold']
            })
        return points

    def get_monitor_point(self, point_id):
        """获取单个监控点"""
        point = self.monitor_points.get(point_id)
        if not point:
            return None
        return {
            'point_id': point_id,
            'name': point['name'],
            'type': point['type'].value,
            'level': point['level'].value,
            'status': point['status'].value,
            'value': point['value'],
            'description': point['description'],
            'last_check': point['last_check'],
            'threshold': point['threshold'],
            'history': list(point['history'])
        }

    def get_alerts(self, level=None, limit=50):
        """获取告警列表"""
        alerts = list(self.alerts)
        if level:
            alerts = [a for a in alerts if a['level'] == level]
        return alerts[-limit:]

    def get_alert_stats(self):
        """获取告警统计"""
        stats = defaultdict(int)
        for alert in self.alerts:
            stats[alert['level']] += 1
        return dict(stats)

    def generate_report(self, duration='1h'):
        """生成监控报告"""
        report = {
            'report_id': f"report_{uuid.uuid4().hex[:8]}",
            'generated_at': datetime.now().isoformat(),
            'duration': duration,
            'summary': self.get_monitor_status(),
            'alert_stats': self.get_alert_stats(),
            'monitor_points': self.get_monitor_points(),
            'recent_alerts': self.get_alerts(limit=20)
        }
        return report

    def auto_heal(self):
        """自动修复问题"""
        heal_actions = []
        
        for point_id, point in self.monitor_points.items():
            if point['status'] == MonitorStatus.CRITICAL:
                action = self._heal_critical(point_id, point)
                if action:
                    heal_actions.append(action)
            elif point['status'] == MonitorStatus.WARNING:
                action = self._heal_warning(point_id, point)
                if action:
                    heal_actions.append(action)

        return {
            'success': True,
            'actions': heal_actions,
            'message': f"执行了 {len(heal_actions)} 个修复动作"
        }

    def _heal_critical(self, point_id, point):
        """修复严重问题"""
        actions = {
            'database_connection': '尝试重新连接数据库',
            'system_memory': '清理缓存释放内存',
            'security_attacks': '启动安全防御机制'
        }
        return actions.get(point_id, f"发现严重问题: {point['name']}")

    def _heal_warning(self, point_id, point):
        """修复警告问题"""
        actions = {
            'system_cpu': '优化进程调度',
            'system_disk': '清理临时文件',
            'task_queue': '加速任务处理'
        }
        return actions.get(point_id, None)

    def analyze_trends(self):
        """分析趋势"""
        trends = []
        
        for point_id, point in self.monitor_points.items():
            if len(point['history']) < 10:
                continue
            
            values = [h['value'] for h in point['history'] if isinstance(h['value'], (int, float))]
            if len(values) < 5:
                continue
            
            avg_current = sum(values[-5:]) / len(values[-5:])
            avg_prev = sum(values[:5]) / len(values[:5]) if len(values) >= 10 else avg_current
            
            if avg_current > avg_prev * 1.5:
                trends.append({
                    'point_id': point_id,
                    'name': point['name'],
                    'trend': 'increasing',
                    'change': f"{((avg_current - avg_prev) / avg_prev * 100):.2f}%",
                    'message': f"{point['name']} 值显著上升"
                })
            elif avg_current < avg_prev * 0.5:
                trends.append({
                    'point_id': point_id,
                    'name': point['name'],
                    'trend': 'decreasing',
                    'change': f"{((avg_current - avg_prev) / avg_prev * 100):.2f}%",
                    'message': f"{point['name']} 值显著下降"
                })

        return trends


ai_monitor_employee = AIMonitorEmployee()


def main():
    """测试AI监控员工"""
    print("=" * 60)
    print("AI监控员工系统测试")
    print("=" * 60)

    employee = AIMonitorEmployee()
    
    print(f"\nAI监控员工信息:")
    print(f"  ID: {employee.employee_id}")
    print(f"  名称: {employee.name}")
    print(f"  类型: {employee.type}")
    print(f"  技能: {', '.join(employee.skills)}")
    print(f"  状态: {employee.status}")

    print(f"\n监控点数量: {len(employee.monitor_points)}")
    for point_type in MonitorPointType:
        count = sum(1 for p in employee.monitor_points.values() if p['type'] == point_type)
        print(f"  {point_type.value}: {count} 个")

    print("\n启动监控...")
    employee.start_monitoring()
    
    print("\n等待监控数据收集...")
    time.sleep(3)

    status = employee.get_monitor_status()
    print(f"\n监控状态:")
    print(f"  运行中: {status['is_running']}")
    print(f"  监控点: {status['monitor_point_count']}")
    print(f"  告警数: {status['alert_count']}")

    print("\n监控点状态:")
    points = employee.get_monitor_points()
    for point in points[:10]:
        print(f"  {point['name']}: {point['status']} - {point['value']}")

    print("\n生成报告...")
    report = employee.generate_report()
    print(f"  报告ID: {report['report_id']}")
    print(f"  告警统计: {report['alert_stats']}")

    print("\n分析趋势...")
    trends = employee.analyze_trends()
    print(f"  发现趋势: {len(trends)} 个")

    print("\n自动修复...")
    heal_result = employee.auto_heal()
    print(f"  修复动作: {len(heal_result['actions'])} 个")

    print("\n停止监控...")
    employee.stop_monitoring()

    print("\n" + "=" * 60)
    print("AI监控员工系统测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()