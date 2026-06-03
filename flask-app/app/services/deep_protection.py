# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
深度保护系统 - 负责系统的安全防护和监控
"""

import os
import time
import threading
import logging
import socket
import psutil
import requests
from datetime import datetime
from app.utils.logging import logger
from app.utils.redis_manager import redis_manager
from app.services.redis_integration import redis_integration
import sys

class DeepProtectionSystem:
    """深度保护系统"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """单例模式"""
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化深度保护系统"""
        self.security_rules = {
            'max_login_attempts': 5,
            'lockout_duration': 300,
            'max_requests_per_minute': 100,
            'max_requests_per_hour': 1000,
            'block_suspicious_ips': True,
            'suspicious_threshold': 10
        }

        self.monitoring_config = {
            'system_check_interval': 60,
            'network_check_interval': 30,
            'security_check_interval': 15,
            'resource_thresholds': {
                'cpu': 80,
                'memory': 85,
                'disk': 90,
                'network': 1000000
            }
        }

        self.login_attempts = {}
        self.request_counts = {}
        self.suspicious_ips = set()
        self.lock = threading.RLock()

        self._start_monitoring_threads()
        logger.info("深度保护系统初始化成功")

    def _start_monitoring_threads(self):
        """启动监控线程"""
        self._system_monitor_thread = threading.Thread(target=self._monitor_system, daemon=True)
        self._system_monitor_thread.start()

        self._network_monitor_thread = threading.Thread(target=self._monitor_network, daemon=True)
        self._network_monitor_thread.start()

        self._security_monitor_thread = threading.Thread(target=self._monitor_security, daemon=True)
        self._security_monitor_thread.start()

        logger.info("深度保护系统监控线程启动成功")

    def check_login_attempt(self, ip, username):
        """检查登录尝试

        Args:
            ip: IP地址
            username: 用户名

        Returns:
            bool: 是否允许登录
        """
        with self.lock:
            if self._is_ip_blocked(ip):
                return False

            key = f"{ip}:{username}"
            if key not in self.login_attempts:
                self.login_attempts[key] = {'count': 0, 'last_attempt': 0}

            self.login_attempts[key]['count'] += 1
            self.login_attempts[key]['last_attempt'] = time.time()

            if self.login_attempts[key]['count'] >= self.security_rules['max_login_attempts']:
                self._block_ip(ip)
                return False

            return True

    def record_successful_login(self, ip, username):
        """记录成功登录

        Args:
            ip: IP地址
            username: 用户名
        """
        with self.lock:
            key = f"{ip}:{username}"
            if key in self.login_attempts:
                del self.login_attempts[key]

    def check_rate_limit(self, ip, endpoint):
        """检查速率限制

        Args:
            ip: IP地址
            endpoint: 端点

        Returns:
            bool: 是否允许请求
        """
        key = f"rate:{ip}:{endpoint}"
        return redis_integration.rate_limit(key, self.security_rules['max_requests_per_minute'], 60)

    def check_suspicious_activity(self, ip, activity):
        """检查可疑活动

        Args:
            ip: IP地址
            activity: 活动类型

        Returns:
            bool: 是否为可疑活动
        """
        activity_key = f"activity:{ip}"
        count = redis_integration.increment_counter(activity_key)

        redis_manager.expire(activity_key, 3600)

        if count > self.security_rules['suspicious_threshold']:
            self._block_ip(ip)
            return True
        return False

    def _is_ip_blocked(self, ip):
        """检查IP是否被阻止

        Args:
            ip: IP地址

        Returns:
            bool: 是否被阻止
        """
        blocked_key = f"blocked:{ip}"
        return redis_manager.exists(blocked_key)

    def _block_ip(self, ip):
        """阻止IP

        Args:
            ip: IP地址
        """
        blocked_key = f"blocked:{ip}"
        redis_manager.set(blocked_key, "1", expire=self.security_rules['lockout_duration'])
        self.suspicious_ips.add(ip)
        logger.warning(f"IP {ip} 被阻止")

    def _clear_login_attempt(self, key):
        """清除登录尝试记录

        Args:
            key: 登录尝试键
        """
        with self.lock:
            if key in self.login_attempts:
                del self.login_attempts[key]

    def _monitor_system(self):
        """监控系统资源"""
        while True:
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')

                if cpu_percent > self.monitoring_config['resource_thresholds']['cpu']:
                    self._alert(f"CPU使用率过高: {cpu_percent}%")

                if memory.percent > self.monitoring_config['resource_thresholds']['memory']:
                    self._alert(f"内存使用率过高: {memory.percent}%")

                if disk.percent > self.monitoring_config['resource_thresholds']['disk']:
                    self._alert(f"磁盘使用率过高: {disk.percent}%")

                self._record_system_status(cpu_percent, memory.percent, disk.percent)

                time.sleep(self.monitoring_config['system_check_interval'])
            except Exception as e:
                logger.error(f"系统监控失败: {str(e)}")
                time.sleep(self.monitoring_config['system_check_interval'])

    def _monitor_network(self):
        """监控网络流量"""
        while True:
            try:
                net_io = psutil.net_io_counters()

                bytes_sent = net_io.bytes_sent
                bytes_recv = net_io.bytes_recv

                if bytes_sent > self.monitoring_config['resource_thresholds']['network']:
                    self._alert(f"网络发送流量过高: {bytes_sent} bytes")

                if bytes_recv > self.monitoring_config['resource_thresholds']['network']:
                    self._alert(f"网络接收流量过高: {bytes_recv} bytes")

                self._record_network_status(bytes_sent, bytes_recv)

                time.sleep(self.monitoring_config['network_check_interval'])
            except Exception as e:
                time.sleep(self.monitoring_config['network_check_interval'])

    def _monitor_security(self):
        """监控安全事件"""
        while True:
            try:
                self._check_suspicious_ips()
                self._check_request_rates()

                time.sleep(self.monitoring_config['security_check_interval'])
            except Exception as e:
                logger.error(f"安全监控失败: {str(e)}")
                time.sleep(self.monitoring_config['security_check_interval'])

    def _check_suspicious_ips(self):
        """检查可疑IP"""
        pass

    def _check_request_rates(self):
        """检查请求速率"""
        pass

    def _record_system_status(self, cpu, memory, disk):
        """记录系统状态

        Args:
            cpu: CPU使用率
            memory: 内存使用率
            disk: 磁盘使用率
        """
        status_key = f"system:status:{datetime.now().strftime('%Y%m%d_%H%M')}"
        status = {
            'timestamp': datetime.now().isoformat(),
            'cpu': cpu,
            'memory': memory,
            'disk': disk
        }
        redis_manager.set(status_key, status, expire=3600)

    def _record_network_status(self, bytes_sent, bytes_recv):
        """记录网络状态

        Args:
            bytes_sent: 发送字节数
            bytes_recv: 接收字节数
        """
        status_key = f"network:status:{datetime.now().strftime('%Y%m%d_%H%M')}"
        status = {
            'timestamp': datetime.now().isoformat(),
            'bytes_sent': bytes_sent,
            'bytes_recv': bytes_recv
        }
        redis_manager.set(status_key, status, expire=3600)

    def _alert(self, message):
        """发送警报

        Args:
            message: 警报消息
        """
        alert_key = f"alert:{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        alert = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'level': 'warning'
        }
        redis_manager.set(alert_key, alert, expire=86400)
        logger.warning(f"警报: {message}")

    def record_security_event(self, event_type, details):
        """记录安全事件

        Args:
            event_type: 事件类型
            details: 事件详情
        """
        event_key = f"security:event:{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'details': details
        }
        redis_manager.set(event_key, event, expire=604800)
        logger.info(f"安全事件: {event_type} - {details}")

    def generate_security_report(self, period='day'):
        """生成安全报告

        Args:
            period: 报告周期 (day, week, month)

        Returns:
            dict: 安全报告
        """
        report = {
            'period': period,
            'events': [],
            'statistics': {
                'total_events': 0,
                'blocked_ips': 0,
                'login_attempts': 0,
                'suspicious_activities': 0
            }
        }
        return report

    def block_ip(self, ip, reason):
        """手动阻止IP

        Args:
            ip: IP地址
            reason: 阻止原因
        """
        self._block_ip(ip)
        self.record_security_event('ip_blocked', f"IP {ip} 被手动阻止: {reason}")

    def unblock_ip(self, ip):
        """解除IP阻止

        Args:
            ip: IP地址
        """
        blocked_key = f"blocked:{ip}"
        redis_manager.delete(blocked_key)
        if ip in self.suspicious_ips:
            self.suspicious_ips.remove(ip)
        self.record_security_event('ip_unblocked', f"IP {ip} 被解除阻止")

    def get_blocked_ips(self):
        """获取被阻止的IP

        Returns:
            list: 被阻止的IP列表
        """
        return list(self.suspicious_ips)


deep_protection_system = DeepProtectionSystem()
