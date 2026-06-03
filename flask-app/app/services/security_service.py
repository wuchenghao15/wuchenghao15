# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
安全服务模块
负责项目的数字安全, 数据库安全, 本地缓存数据安全和项目后门漏洞安全
"""

import logging
logger = logging.getLogger(__name__)
import os
import sys
import sqlite3
from contextlib import contextmanager
import time
import hashlib
import hmac
import base64
import re
import socket
import threading
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class SecurityService:
    """安全服务类"""

    def __init__(self, db_path="app.db"):
        """初始化安全服务"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.encryption_key = None
        self.scanning_interval = 300
        self.is_running = False
        self.scan_thread = None

        self.ddos_protection = {
            "enabled": True,
            "rate_limit": 100,
            "block_duration": 300,
            "request_history": {},
            "blocked_ips": {}
        }

        self.memory_monitoring = {
            "enabled": True,
            "check_interval": 60,
            "last_check": 0
        }

        self.load_config()

    def connect(self):
        """连接数据库"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            logger.error(f"连接数据库失败: {str(e)}")
            return False

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def load_config(self):
        """加载安全配置"""
        if not self.connect():
            return

        try:
            self.cursor.execute("SELECT config_value FROM security_configs WHERE config_key = 'encryption_key'")
            result = self.cursor.fetchone()
            if result:
                self.encryption_key = result[0].encode()

            self.cursor.execute("SELECT config_value FROM security_configs WHERE config_key = 'scan_interval'")
            result = self.cursor.fetchone()
            if result:
                self.scanning_interval = int(result[0])
        except Exception as e:
            logger.error(f"加载配置失败: {str(e)}")
        finally:
            self.close()

    def add_security_event(self, event_type, severity, message, source=None, ip_address=None, user_agent=None, details=None):
        """添加安全事件"""
        if not self.connect():
            return False

        try:
            self.cursor.execute('''
                INSERT INTO security_events 
                (event_type, severity, message, source, ip_address, user_agent, details, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (event_type, severity, message, source, ip_address, user_agent, details, datetime.now().isoformat()))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"添加安全事件失败: {str(e)}")
            return False
        finally:
            self.close()

    def start_scan(self, scan_type, target):
        """启动安全扫描"""
        if not self.connect():
            return None

        try:
            scan_id = hashlib.md5(f"{scan_type}{target}{time.time()}".encode()).hexdigest()
            self.cursor.execute('''
                INSERT INTO security_scans (scan_id, scan_type, target, status, start_time)
                VALUES (?, ?, ?, 'running', CURRENT_TIMESTAMP)
            ''', (scan_id, scan_type, target))
            self.conn.commit()

            findings = self._scan_vulnerabilities(target)
            severity = 'low'
            for finding in findings:
                if finding.get('severity') == 'high':
                    severity = 'high'
                elif finding.get('severity') == 'medium' and severity != 'high':
                    severity = 'medium'

            self._update_scan_result(scan_id, findings, severity)
            return scan_id
        except Exception as e:
            logger.error(f"启动扫描失败: {str(e)}")
            return None
        finally:
            self.close()

    def _scan_vulnerabilities(self, target):
        """扫描漏洞"""
        findings = []

        if target == "app":
            if not self._check_csrf_protection():
                findings.append({
                    "type": "CSRF",
                    "description": "CSRF保护未启用",
                    "severity": "medium",
                    "critical": False
                })

            if not self._check_xss_protection():
                findings.append({
                    "type": "XSS",
                    "description": "XSS保护未启用",
                    "severity": "medium",
                    "critical": False
                })

        return findings

    def _update_scan_result(self, scan_id, findings, severity):
        """更新扫描结果"""
        if not self.connect():
            return

        try:
            self.cursor.execute('''
                UPDATE security_scans 
                SET end_time = CURRENT_TIMESTAMP, status = 'completed', findings = ?, severity = ?
                WHERE id = ?
            ''', (str(findings), severity, scan_id))

            message = f"安全扫描发现 {len(findings)} 个问题"
            self.add_security_event(
                "scan",
                severity,
                message,
                source="security_service"
            )
        except Exception as e:
            logger.error(f"更新扫描结果失败: {str(e)}")
        finally:
            self.close()

    def _check_csrf_protection(self):
        """检查CSRF保护"""
        if not self.connect():
            return False

        try:
            self.cursor.execute("SELECT config_value FROM security_configs WHERE config_key = 'enable_csrf_protection'")
            result = self.cursor.fetchone()
            return result and result[0].lower() == 'true'
        except Exception as e:
            logger.error(f"检查CSRF保护失败: {str(e)}")
            return False
        finally:
            self.close()

    def _check_xss_protection(self):
        """检查XSS保护"""
        if not self.connect():
            return False

        try:
            self.cursor.execute("SELECT config_value FROM security_configs WHERE config_key = 'enable_xss_protection'")
            result = self.cursor.fetchone()
            return result and result[0].lower() == 'true'
        except Exception as e:
            logger.error(f"检查XSS保护失败: {str(e)}")
            return False
        finally:
            self.close()

    def encrypt_data(self, data):
        """加密数据"""
        try:
            if not self.encryption_key:
                self.load_config()

            if not self.encryption_key:
                return None

            if isinstance(data, dict) or isinstance(data, list):
                data = str(data)

            data = str(data)
            hashed = hmac.new(self.encryption_key, data.encode(), hashlib.sha256)
            return base64.b64encode(hashed.digest()).decode()
        except Exception as e:
            logger.error(f"加密数据失败: {str(e)}")
            return None

    def verify_data(self, data, signature):
        """验证数据签名"""
        try:
            if not self.encryption_key:
                self.load_config()

            if isinstance(data, dict) or isinstance(data, list):
                data = str(data)

            if isinstance(data, str):
                data = data.encode()

            hashed = hmac.new(self.encryption_key, data, hashlib.sha256)
            expected_signature = base64.b64encode(hashed.digest()).decode()

            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logger.error(f"验证数据失败: {str(e)}")
            return False

    def sanitize_input(self, input_str):
        """清理输入数据, 防止XSS攻击"""
        if not input_str:
            return input_str

        input_str = re.sub(r'<script.*?>.*?</script>', '', input_str, flags=re.IGNORECASE | re.DOTALL)
        input_str = re.sub(r'<.*?>', '', input_str)
        input_str = input_str.replace('&', '&amp;')
        input_str = input_str.replace('<', '&lt;')
        input_str = input_str.replace('>', '&gt;')
        input_str = input_str.replace('"', '&quot;')
        input_str = input_str.replace("'", '&#x27;')

        return input_str

    def detect_sql_injection(self, query):
        """检测SQL注入"""
        if not query:
            return False

        sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE)\b)",
            r"(--|\#|\/\*|\*\/)",
            r"(\bOR\b|\bAND\b).*?=",
            r"(\bunion\b.*?\bselect\b)",
            r"(\bexec\b|\bexecute\b)"
        ]

        for pattern in sql_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True

        return False

    def check_ddos_attack(self, ip_address):
        """检查DDoS攻击"""
        if not self.ddos_protection["enabled"]:
            return False, "DDoS保护已禁用"

        current_time = time.time()

        if ip_address in self.ddos_protection["blocked_ips"]:
            block_until = self.ddos_protection["blocked_ips"][ip_address]
            if current_time < block_until:
                return True, "IP已被阻止"
            else:
                del self.ddos_protection["blocked_ips"][ip_address]

        if ip_address not in self.ddos_protection["request_history"]:
            self.ddos_protection["request_history"][ip_address] = []

        self.ddos_protection["request_history"][ip_address].append(current_time)

        one_minute_ago = current_time - 60
        recent_requests = [
            t for t in self.ddos_protection["request_history"][ip_address]
            if t > one_minute_ago
        ]
        self.ddos_protection["request_history"][ip_address] = recent_requests

        if len(recent_requests) > self.ddos_protection["rate_limit"]:
            self.ddos_protection["blocked_ips"][ip_address] = current_time + self.ddos_protection["block_duration"]
            return True, "请求频率过高, 已阻止"

        return False, "正常"

    def start_monitoring(self):
        """启动安全监控"""
        if self.is_running:
            return

        self.is_running = True
        self.scan_thread = threading.Thread(target=self._monitoring_loop)
        self.scan_thread.daemon = True
        self.scan_thread.start()
        logger.info("安全监控服务已启动")

    def stop_monitoring(self):
        """停止安全监控"""
        self.is_running = False
        if self.scan_thread:
            self.scan_thread.join(timeout=5)
        logger.info("安全监控服务已停止")

    def _monitoring_loop(self):
        """监控循环"""
        while self.is_running:
            try:
                self.start_scan("vulnerability", "app")
                self.start_scan("database", "app.db")
                self.start_scan("cache", "app/cache")

                self._check_system_status()
                self.check_memory_overflow()

            except Exception as e:
                logger.error(f"监控循环出错: {str(e)}")

            for _ in range(self.scanning_interval):
                if not self.is_running:
                    break
                time.sleep(1)

    def _check_system_status(self):
        """检查系统状态"""
        try:
            disk_usage = os.statvfs('.')
            free_space = disk_usage.f_bavail * disk_usage.f_frsize / (1024 * 1024 * 1024)
            if free_space < 10:
                self.add_security_event(
                    "system",
                    "warning",
                    f"磁盘空间不足: {free_space:.2f} GB",
                    source="security_service"
                )
        except Exception as e:
            logger.error(f"检查系统状态失败: {str(e)}")

        try:
            with open('/proc/loadavg', 'r') as f:
                load_avg = f.read().split()[0]
                if float(load_avg) > 5:
                    self.add_security_event(
                        "system",
                        "warning",
                        f"系统负载过高: {load_avg}",
                        source="security_service"
                    )
        except Exception:
            pass

    def check_memory_overflow(self):
        """检查内存溢出"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                self.add_security_event(
                    "system",
                    "warning",
                    f"内存使用率过高: {memory.percent}%",
                    source="security_service"
                )
        except ImportError:
            pass
        except Exception as e:
            logger.error(f"检查内存溢出失败: {str(e)}")

    def get_security_events(self, limit=100):
        """获取安全事件"""
        if not self.connect():
            return []

        try:
            self.cursor.execute('''
                SELECT * FROM security_events 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"获取安全事件失败: {str(e)}")
            return []
        finally:
            self.close()


security_service = SecurityService()


def get_security_service():
    """获取安全服务实例"""
    return security_service
