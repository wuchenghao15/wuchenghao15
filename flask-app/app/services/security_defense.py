# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
安全防御系统,实现奶酪模型和百层穿透防护
"""

import os
import time
import threading
import hashlib
import base64
import random
import string
from datetime import datetime
from app.utils.logging import logger
from app.utils.redis_manager import redis_manager
from app.services.deep_protection import deep_protection
import logging


class SecurityDefenseSystem:
    """安全防御系统: 实现奶酪模型和百层穿透防护"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """单例模式"""
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(SecurityDefenseSystem, cls).__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化安全防御系统"""
        self.cheese_model = {
            'layers': [
                {'name': '网络层', 'level': 1, 'active': True},
                {'name': '应用层', 'level': 2, 'active': True},
                {'name': '数据层', 'level': 3, 'active': True},
                {'name': '认证层', 'level': 4, 'active': True},
                {'name': '授权层', 'level': 5, 'active': True},
                {'name': '监控层', 'level': 6, 'active': True},
                {'name': '审计层', 'level': 7, 'active': True},
                {'name': '响应层', 'level': 8, 'active': True}
            ],
            'vulnerability_threshold': 3,
            'scan_interval': 3600
        }

        self.penetration_protection = {
            'max_attempts': 100,
            'block_duration': 86400,
            'detection_rules': [
                {'name': 'SQL注入检测', 'pattern': r'[\'"\\;]', 'severity': 'high'},
                {'name': 'XSS检测', 'pattern': r'<script|javascript:', 'severity': 'high'},
                {'name': 'CSRF检测', 'pattern': r'csrf|token', 'severity': 'medium'},
                {'name': '命令注入检测', 'pattern': r'\\|\\&|;|\$|\`', 'severity': 'high'},
                {'name': '路径遍历检测', 'pattern': r'\.\./|\.\.\\', 'severity': 'high'}
            ],
            'honeypot_enabled': True,
            'deception_enabled': True
        }

        self.attack_attempts = {}
        self.honeypot_triggers = {}
        self.lock = threading.RLock()

        self._start_scan_threads()
        logger.info("安全防御系统初始化成功")

    def _start_scan_threads(self):
        """启动安全扫描线程"""
        self._vulnerability_scan_thread = threading.Thread(target=self._scan_vulnerabilities, daemon=True)
        self._vulnerability_scan_thread.start()

        self._penetration_detect_thread = threading.Thread(target=self._detect_penetration, daemon=True)
        self._penetration_detect_thread.start()

        logger.info("安全防御系统扫描线程启动成功")

    def check_cheese_model(self):
        """
        检查奶酪模型状态

        Returns:
            dict: 奶酪模型状态
        """
        active_layers = [layer for layer in self.cheese_model['layers'] if layer['active']]
        vulnerable_layers = []

        status = {
            'total_layers': len(self.cheese_model['layers']),
            'active_layers': len(active_layers),
            'vulnerable_layers': len(vulnerable_layers),
            'security_score': self._calculate_security_score(len(active_layers), len(vulnerable_layers)),
            'layers': self.cheese_model['layers']
        }

        if len(vulnerable_layers) >= self.cheese_model['vulnerability_threshold']:
            logger.warning(f"⚠️ 安全警告: 漏洞层数已达到阈值 {self.cheese_model['vulnerability_threshold']}")

        return status

    def _calculate_security_score(self, active_layers, vulnerable_layers):
        """
        计算安全评分

        Args:
            active_layers: 活跃层数
            vulnerable_layers: 漏洞层数

        Returns:
            int: 安全评分(0-100)
        """
        total_layers = len(self.cheese_model['layers'])
        base_score = (active_layers / total_layers) * 100
        vulnerability_penalty = (vulnerable_layers / total_layers) * 30
        score = max(0, base_score - vulnerability_penalty)
        return int(score)

    def activate_layer(self, layer_name):
        """
        激活安全层

        Args:
            layer_name: 层名称

        Returns:
            bool: 是否成功
        """
        for layer in self.cheese_model['layers']:
            if layer['name'] == layer_name:
                layer['active'] = True
                self._alert(f"安全层 {layer_name} 已激活", "info")
                return True
        return False

    def deactivate_layer(self, layer_name):
        """
        停用安全层

        Args:
            layer_name: 层名称

        Returns:
            bool: 是否成功
        """
        for layer in self.cheese_model['layers']:
            if layer['name'] == layer_name:
                layer['active'] = False
                return True
        return False

    def check_penetration_attempt(self, ip, request_path, request_data):
        """
        检查穿透尝试

        Args:
            ip: IP地址
            request_path: 请求路径
            request_data: 请求数据

        Returns:
            dict: 检测结果
        """
        with self.lock:
            self.attack_attempts[ip] = self.attack_attempts.get(ip, 0) + 1

            if self.penetration_protection['honeypot_enabled']:
                self._trigger_honeypot(ip, request_path)

            if ip in self.attack_attempts:
                if self.attack_attempts[ip] >= self.penetration_protection['max_attempts']:
                    self._block_ip(ip, "穿透尝试次数过多")
                    return {'status': 'blocked', 'reason': 'max_attempts_exceeded'}

        return {'status': 'allowed', 'attempts': self.attack_attempts.get(ip, 0)}

    def _trigger_honeypot(self, ip, path):
        """
        触发蜜罐

        Args:
            ip: IP地址
            path: 路径
        """
        if ip not in self.honeypot_triggers:
            self.honeypot_triggers[ip] = []

        self.honeypot_triggers[ip].append({
            'timestamp': datetime.now().isoformat(),
            'path': path,
            'action': 'honeypot_triggered'
        })

        self._alert(f"蜜罐被触发: {ip} 访问 {path}", "high")
        deep_protection.block_ip(ip, "蜜罐触发")

    def _block_ip(self, ip, reason):
        """
        阻止IP

        Args:
            ip: IP地址
            reason: 阻止原因
        """
        blocked_key = f"penetration:blocked:{ip}"
        redis_manager.set(blocked_key, reason, expire=self.penetration_protection['block_duration'])
        deep_protection.block_ip(ip, reason)
        logger.warning(f"IP {ip} 因 {reason} 被阻止")

    def is_ip_blocked(self, ip):
        """
        检查IP是否被阻止

        Args:
            ip: IP地址

        Returns:
            bool: 是否被阻止
        """
        blocked_key = f"penetration:blocked:{ip}"
        return redis_manager.exists(blocked_key)

    def _scan_vulnerabilities(self):
        """扫描系统漏洞"""
        while True:
            try:
                cheese_status = self.check_cheese_model()
                logger.info(f"奶酪模型状态: {cheese_status}")

                time.sleep(self.cheese_model['scan_interval'])
            except Exception as e:
                logger.error(f"漏洞扫描失败: {str(e)}")
                time.sleep(60)

    def _detect_penetration(self):
        """检测穿透尝试"""
        while True:
            try:
                with self.lock:
                    for ip, attempts in list(self.attack_attempts.items()):
                        if attempts >= self.penetration_protection['max_attempts']:
                            self._block_ip(ip, "穿透尝试次数过多")
                            del self.attack_attempts[ip]

                    for ip, triggers in list(self.honeypot_triggers.items()):
                        if len(triggers) > 5:
                            self._block_ip(ip, "多次触发蜜罐")
                            del self.honeypot_triggers[ip]

                time.sleep(60)
            except Exception as e:
                logger.error(f"穿透检测失败: {str(e)}")
                time.sleep(60)

    def generate_csrf_token(self, user_id):
        """
        生成CSRF令牌

        Args:
            user_id: 用户ID

        Returns:
            str: CSRF令牌
        """
        token = base64.b64encode(os.urandom(32)).decode('utf-8')
        csrf_key = f"csrf:{user_id}"
        redis_manager.set(csrf_key, token, expire=3600)
        return token

    def verify_csrf_token(self, user_id, token):
        """验证CSRF令牌"""
        csrf_key = f"csrf:{user_id}"
        stored_token = redis_manager.get(csrf_key)
        return stored_token == token

    def generate_session_token(self, user_id):
        """
        生成会话令牌

        Args:
            user_id: 用户ID

        Returns:
            str: 会话令牌
        """
        session_id = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        session_key = f"session:{session_id}"
        session_data = {
            'user_id': user_id,
            'created_at': datetime.now().isoformat(),
            'last_access': datetime.now().isoformat()
        }
        redis_manager.set(session_key, session_data, expire=86400)
        return session_id

    def _alert(self, message, level='warning'):
        """
        发送警报

        Args:
            message: 警报消息
            level: 警报级别
        """
        alert = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'level': level
        }
        alert_key = f"alert:{hashlib.md5(message.encode()).hexdigest()[:16]}"
        redis_manager.set(alert_key, alert, expire=86400)

        if level == 'high':
            logger.error(f"🚨 安全警报: {message}")
        elif level == 'warning':
            logger.warning(f"⚠️ 安全警告: {message}")
        else:
            logger.info(f"ℹ️ 安全信息: {message}")

    def generate_security_report(self, period='day'):
        """
        生成安全报告

        Args:
            period: 报告周期 (day, week, month)

        Returns:
            dict: 安全报告
        """
        report = {
            'generated_at': datetime.now().isoformat(),
            'period': period,
            'attack_attempts': len(self.attack_attempts),
            'honeypot_triggers': sum(len(triggers) for triggers in self.honeypot_triggers.values()),
            'blocked_ips': len(deep_protection.get_blocked_ips()),
            'recommendations': self._generate_security_recommendations()
        }

        return report

    def _generate_security_recommendations(self):
        """
        生成安全建议

        Returns:
            list: 安全建议列表
        """
        recommendations = []

        active_layers = [layer for layer in self.cheese_model['layers'] if layer['active']]
        if len(active_layers) < len(self.cheese_model['layers']):
            recommendations.append("激活所有安全层以提高系统安全性")

        if self.attack_attempts:
            recommendations.append("检测到攻击尝试,建议加强监控和访问控制")

        if self.honeypot_triggers:
            recommendations.append("蜜罐被频繁触发,建议检查系统漏洞")

        return recommendations


security_defense = SecurityDefenseSystem()
