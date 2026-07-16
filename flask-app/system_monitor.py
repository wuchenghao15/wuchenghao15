#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS系统监控仪表盘API
提供系统状态、性能指标、日志查询等功能
"""

import os
import sys
import json
import psutil
import time
import threading
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = print

class SystemMonitor:
    """系统监控"""
    
    def __init__(self):
        self.metrics = {
            'cpu': [],
            'memory': [],
            'disk': [],
            'network': [],
            'processes': []
        }
        self.max_metrics_history = 60
        self.is_monitoring = False
        self.monitor_thread = None
        self.lock = threading.Lock()
        
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'monitor_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'enabled': True,
            'monitor_interval': 5,
            'alert_thresholds': {
                'cpu_warning': 80,
                'cpu_critical': 95,
                'memory_warning': 80,
                'memory_critical': 95,
                'disk_warning': 80,
                'disk_critical': 95
            },
            'log_retention_days': 30,
            'max_processes_to_monitor': 20
        }
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'monitor_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _collect_metrics(self):
        """收集系统指标"""
        timestamp = datetime.now().isoformat()
        
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        with self.lock:
            self.metrics['cpu'].append({
                'timestamp': timestamp,
                'value': cpu_percent,
                'cores': psutil.cpu_count(),
                'status': self._get_status(cpu_percent, 'cpu')
            })
            
            self.metrics['memory'].append({
                'timestamp': timestamp,
                'percent': memory.percent,
                'used': memory.used,
                'available': memory.available,
                'total': memory.total,
                'status': self._get_status(memory.percent, 'memory')
            })
            
            self.metrics['disk'].append({
                'timestamp': timestamp,
                'percent': disk.percent,
                'used': disk.used,
                'free': disk.free,
                'total': disk.total,
                'status': self._get_status(disk.percent, 'disk')
            })
            
            self.metrics['network'].append({
                'timestamp': timestamp,
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            })
            
            for key in self.metrics:
                if len(self.metrics[key]) > self.max_metrics_history:
                    self.metrics[key] = self.metrics[key][-self.max_metrics_history:]
    
    def _get_status(self, value: float, metric_type: str) -> str:
        """获取状态等级"""
        thresholds = self.config['alert_thresholds']
        critical = thresholds.get(f'{metric_type}_critical', 95)
        warning = thresholds.get(f'{metric_type}_warning', 80)
        
        if value >= critical:
            return 'critical'
        elif value >= warning:
            return 'warning'
        return 'normal'
    
    def _monitor_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                self._collect_metrics()
            except Exception as e:
                logger(f"[监控] 收集指标失败: {e}")
            time.sleep(self.config['monitor_interval'])
    
    def start_monitoring(self):
        """开始监控"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger(f"[监控] 系统监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logger(f"[监控] 系统监控已停止")
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        return {
            'os': {
                'name': os.name,
                'platform': sys.platform,
                'version': os.uname().version,
                'machine': os.uname().machine
            },
            'cpu': {
                'count': psutil.cpu_count(),
                'percent': psutil.cpu_percent(),
                'freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {}
            },
            'memory': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'used': psutil.virtual_memory().used,
                'percent': psutil.virtual_memory().percent
            },
            'disk': {
                'total': psutil.disk_usage('/').total,
                'used': psutil.disk_usage('/').used,
                'free': psutil.disk_usage('/').free,
                'percent': psutil.disk_usage('/').percent
            },
            'network': psutil.net_io_counters()._asdict(),
            'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat(),
            'python_version': sys.version
        }
    
    def get_recent_metrics(self) -> Dict[str, Any]:
        """获取最近指标"""
        with self.lock:
            return {
                'cpu': self.metrics['cpu'][-10:],
                'memory': self.metrics['memory'][-10:],
                'disk': self.metrics['disk'][-10:],
                'network': self.metrics['network'][-10:]
            }
    
    def get_metrics_history(self) -> Dict[str, Any]:
        """获取完整指标历史"""
        with self.lock:
            return self.metrics.copy()
    
    def get_process_list(self) -> List[Dict[str, Any]]:
        """获取进程列表"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                processes.append(proc.info)
            except:
                pass
        
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        return processes[:self.config['max_processes_to_monitor']]
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """获取警报"""
        alerts = []
        thresholds = self.config['alert_thresholds']
        
        recent_cpu = self.metrics['cpu'][-1] if self.metrics['cpu'] else None
        recent_memory = self.metrics['memory'][-1] if self.metrics['memory'] else None
        recent_disk = self.metrics['disk'][-1] if self.metrics['disk'] else None
        
        if recent_cpu and recent_cpu['status'] != 'normal':
            alerts.append({
                'type': 'cpu',
                'level': recent_cpu['status'],
                'value': recent_cpu['value'],
                'message': f"CPU使用率过高: {recent_cpu['value']}%",
                'timestamp': recent_cpu['timestamp']
            })
        
        if recent_memory and recent_memory['status'] != 'normal':
            alerts.append({
                'type': 'memory',
                'level': recent_memory['status'],
                'value': recent_memory['percent'],
                'message': f"内存使用率过高: {recent_memory['percent']}%",
                'timestamp': recent_memory['timestamp']
            })
        
        if recent_disk and recent_disk['status'] != 'normal':
            alerts.append({
                'type': 'disk',
                'level': recent_disk['status'],
                'value': recent_disk['percent'],
                'message': f"磁盘使用率过高: {recent_disk['percent']}%",
                'timestamp': recent_disk['timestamp']
            })
        
        return alerts
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表盘数据"""
        return {
            'system_info': self.get_system_info(),
            'recent_metrics': self.get_recent_metrics(),
            'alerts': self.get_alerts(),
            'processes': self.get_process_list(),
            'status': 'running' if self.is_monitoring else 'stopped'
        }
    
    def set_alert_threshold(self, metric_type: str, warning: float, critical: float):
        """设置警报阈值"""
        self.config['alert_thresholds'][f'{metric_type}_warning'] = warning
        self.config['alert_thresholds'][f'{metric_type}_critical'] = critical
        self._save_config()
        logger(f"[监控] 警报阈值已更新: {metric_type}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取监控状态"""
        return {
            'status': 'running' if self.is_monitoring else 'stopped',
            'interval': self.config['monitor_interval'],
            'history_size': self.max_metrics_history,
            'alert_thresholds': self.config['alert_thresholds']
        }

system_monitor = SystemMonitor()
