#!/usr/bin/env python3
"""
系统自动报警bot - 负责监控系统状态并发送报警信息
"""

import os
import time
import threading
import smtplib
import requests
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.utils.logging import logger
from app.utils.redis_manager import redis_manager
from app.services.deep_protection import deep_protection
from app.services.security_defense import security_defense


class AlarmBot:
    """系统自动报警bot"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """单例模式"""
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(AlarmBot, cls).__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化报警bot"""
        self.config = {
            'enabled': True,
            'channels': {
                'email': {
                    'enabled': True,
                    'smtp_server': 'smtp.qq.com',
                    'username': '',
                    'password': '',
                    'from_email': '',
                    'to_emails': []
                },
                'webhook': {
                    'enabled': False,
                    'url': '',
                    'headers': {}
                },
                'sms': {
                    'enabled': False,
                    'api_key': '',
                    'phones': []
                }
            },
            'alarm_rules': {
                'system': {
                    'cpu_threshold': 90,
                    'memory_threshold': 85,
                    'disk_threshold': 90,
                    'network_threshold': 1000000
                },
                'security': {
                    'attack_attempts_threshold': 10,
                    'vulnerability_threshold': 3
                },
                'service': {
                    'response_time_threshold': 5000
                }
            },
            'check_interval': 60,
            'cooldown_period': 300,
            'alarm_history': []
        }

        self.last_alarm_time = {}
        self.lock = threading.RLock()
        self._start_monitor_thread()
        logger.info("系统自动报警bot初始化成功")

    def _start_monitor_thread(self):
        """启动监控线程"""
        self._monitor_thread = threading.Thread(target=self._monitor_system, daemon=True)
        self._monitor_thread.start()
        logger.info("系统自动报警bot监控线程启动成功")

    def _monitor_system(self):
        """监控系统状态"""
        while True:
            try:
                self._check_system_resources()
                self._check_security_status()
                self._check_service_status()
                self._check_redis_status()
                time.sleep(self.config['check_interval'])
            except Exception as e:
                logger.error(f"系统监控失败: {str(e)}")
                time.sleep(self.config['check_interval'])

    def _check_system_resources(self):
        """检查系统资源使用情况"""
        try:
            import psutil

            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            if cpu_percent > self.config['alarm_rules']['system']['cpu_threshold']:
                self._trigger_alarm(
                    'CPU使用率过高',
                    f'CPU使用率: {cpu_percent}%,超过阈值 {self.config["alarm_rules"]["system"]["cpu_threshold"]}%',
                    'high'
                )

            if memory.percent > self.config['alarm_rules']['system']['memory_threshold']:
                self._trigger_alarm(
                    '内存使用率过高',
                    f'内存使用率: {memory.percent}%,超过阈值 {self.config["alarm_rules"]["system"]["memory_threshold"]}%',
                    'high'
                )

            if disk.percent > self.config['alarm_rules']['system']['disk_threshold']:
                self._trigger_alarm(
                    '磁盘使用率过高',
                    f'磁盘使用率: {disk.percent}%,超过阈值 {self.config["alarm_rules"]["system"]["disk_threshold"]}%',
                    'high'
                )

            net_io = psutil.net_io_counters()
            bytes_sent = net_io.bytes_sent
            bytes_recv = net_io.bytes_recv

            if bytes_sent > self.config['alarm_rules']['system']['network_threshold']:
                self._trigger_alarm(
                    '网络发送流量过高',
                    f'网络发送流量: {bytes_sent} bytes,超过阈值 {self.config["alarm_rules"]["system"]["network_threshold"]} bytes',
                    'medium'
                )

            if bytes_recv > self.config['alarm_rules']['system']['network_threshold']:
                self._trigger_alarm(
                    '网络接收流量过高',
                    f'网络接收流量: {bytes_recv} bytes,超过阈值 {self.config["alarm_rules"]["system"]["network_threshold"]} bytes',
                    'medium'
                )
        except Exception as e:
            logger.error(f"检查系统资源失败: {str(e)}")

    def _check_security_status(self):
        """检查安全状态"""
        try:
            attack_attempts = len(security_defense.attack_attempts) if hasattr(security_defense, 'attack_attempts') else 0
            if attack_attempts > self.config['alarm_rules']['security']['attack_attempts_threshold']:
                self._trigger_alarm(
                    '攻击尝试次数过多',
                    f'攻击尝试次数: {attack_attempts},超过阈值 {self.config["alarm_rules"]["security"]["attack_attempts_threshold"]}',
                    'high'
                )

            if hasattr(security_defense, 'check_cheese_model'):
                cheese_status = security_defense.check_cheese_model()
                vulnerable_layers = len([layer for layer in cheese_status.get('layers', []) if not layer.get('active', True)])
                if vulnerable_layers > self.config['alarm_rules']['security']['vulnerability_threshold']:
                    self._trigger_alarm(
                        '系统漏洞数量过多',
                        f'漏洞数量: {vulnerable_layers},超过阈值 {self.config["alarm_rules"]["security"]["vulnerability_threshold"]}',
                        'high'
                    )
        except Exception as e:
            logger.error(f"检查安全状态失败: {str(e)}")

    def _check_service_status(self):
        """检查服务状态"""
        try:
            pass
        except Exception as e:
            logger.error(f"检查服务状态失败: {str(e)}")

    def _check_redis_status(self):
        """检查Redis状态"""
        try:
            redis_manager.ping()
        except Exception as e:
            self._trigger_alarm(
                'Redis连接失败',
                f'Redis连接错误: {str(e)}',
                'high'
            )
            logger.error(f"检查Redis状态失败: {str(e)}")

    def _trigger_alarm(self, title, message, level):
        """
        触发报警

        Args:
            title: 报警标题
            message: 报警消息
            level: 报警级别
        """
        with self.lock:
            alarm_key = f"{title}:{level}"
            current_time = time.time()

            if alarm_key in self.last_alarm_time:
                if current_time - self.last_alarm_time[alarm_key] < self.config['cooldown_period']:
                    return

            self.last_alarm_time[alarm_key] = current_time

            alarm = {
                'timestamp': datetime.now().isoformat(),
                'title': title,
                'message': message,
                'level': level
            }

            alarm_key_redis = f"alarm:{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            redis_manager.set(alarm_key_redis, alarm, expire=86400)

            self._send_alarm(alarm)

    def _send_alarm(self, alarm):
        """
        发送报警

        Args:
            alarm: 报警信息
        """
        if self.config['channels']['email']['enabled']:
            self._send_email(alarm)

        if self.config['channels']['webhook']['enabled']:
            self._send_webhook(alarm)

        if self.config['channels']['sms']['enabled']:
            self._send_sms(alarm)

    def _send_email(self, alarm):
        """
        发送邮件报警

        Args:
            alarm: 报警信息
        """
        try:
            email_config = self.config['channels']['email']

            msg = MIMEMultipart()
            msg['From'] = email_config['from_email']
            msg['To'] = ', '.join(email_config['to_emails'])
            msg['Subject'] = f"[系统报警] {alarm['title']} ({alarm['level']})"

            body = f"""时间: {alarm['timestamp']}
标题: {alarm['title']}
级别: {alarm['level']}
消息: {alarm['message']}
"""
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            with smtplib.SMTP(email_config['smtp_server'], 587) as server:
                server.starttls()
                server.login(email_config['username'], email_config['password'])
                server.send_message(msg)

            logger.info(f"邮件报警发送成功: {alarm['title']}")
        except Exception as e:
            logger.error(f"发送邮件报警失败: {str(e)}")

    def _send_webhook(self, alarm):
        """
        发送Webhook报警

        Args:
            alarm: 报警信息
        """
        try:
            webhook_config = self.config['channels']['webhook']

            payload = {
                'timestamp': alarm['timestamp'],
                'title': alarm['title'],
                'level': alarm['level'],
                'message': alarm['message']
            }

            response = requests.post(
                webhook_config['url'],
                json=payload,
                headers=webhook_config['headers'],
                timeout=10
            )

            if response.status_code == 200:
                logger.info(f"Webhook报警发送成功: {alarm['title']}")
            else:
                logger.error(f"发送Webhook报警失败: {response.status_code}")
        except Exception as e:
            logger.error(f"发送Webhook报警失败: {str(e)}")

    def _send_sms(self, alarm):
        """
        发送短信报警

        Args:
            alarm: 报警信息
        """
        try:
            pass
        except Exception as e:
            logger.error(f"发送短信报警失败: {str(e)}")

    def trigger_manual_alarm(self, title, message, level='medium'):
        """
        手动触发报警

        Args:
            title: 报警标题
            message: 报警消息
            level: 报警级别
        """
        self._trigger_alarm(title, message, level)

    def get_alarm_history(self, limit=100):
        """
        获取报警历史

        Args:
            limit: 限制数量

        Returns:
            list: 报警历史
        """
        return self.config['alarm_history'][-limit:]

    def clear_alarm_history(self):
        """清除报警历史"""
        self.config['alarm_history'] = []
        logger.info("报警历史已清除")

    def update_config(self, new_config):
        """
        更新配置

        Args:
            new_config: 新配置
        """
        self.config.update(new_config)
        logger.info("报警bot配置已更新")

    def get_config(self):
        """
        获取配置

        Returns:
            dict: 配置
        """
        return self.config
