#!/usr/bin/env python3
"""
终端和网络监控系统 - 全面监控所有接入终端和请求

import os
import re
import time
# JSON import removed - using database
import socket
import struct
import threading
import logging
from datetime import datetime
from functools import wraps
from flask import request, g
from utils.db import db_manager
from utils.logging import logger

class TerminalMonitorConfig:
    """终端监控配置"""

    # 监控配置
    MONITOR_CONFIG = {
        'enable_terminal_monitoring': True,
        'enable_request_monitoring': True,
        'enable_protocol_monitoring': True,
        'enable_access_control': True,
        'enable_error_tracking': True,
        'log_retention_days': 90,
        'max_connections_per_ip': 100,
        'connection_timeout': 300,
        ' suspicious_threshold': 10
    }

    # 协议端口映射
    PROTOCOL_PORTS = {
        'HTTP': 80,
        'HTTPS': 443,
        'FTP': 21,
        'SSH': 22,
        'TELNET': 23,
        'SMTP': 25,
        'DNS': 53,
        'MYSQL': 3306,
        'POSTGRESQL': 5432,
        'REDIS': 6379,
        'MONGODB': 27017,
        'CUSTOM': 8888
    }
    # 已知危险端口
    DANGEROUS_PORTS = [23, 135, 139, 445, 1433, 3389, 5900]

    # 黑白名单配置
    WHITELIST_CONFIG = {
        'enabled': True,
        'auto_add_verified': True,
        'strict_mode': False
    }
    BLACKLIST_CONFIG = {
        'enabled': True,
        'auto_block_after_failures': 5,
        'block_duration': 3600,
    }
class TerminalMonitorDB:
    """终端监控数据库管理"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

        """初始化数据库"""
        self._create_tables()

    def _create_tables(self):
        """创建监控数据库表"""
        try:
            # 终端信息表
            db_manager.execute('''
                CREATE TABLE IF NOT EXISTS terminal_info (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    terminal_id TEXT UNIQUE NOT NULL,
                    ip_address TEXT NOT NULL,
                    mac_address TEXT,
                    hostname TEXT,
                    os_type TEXT,
                    browser_type TEXT,
                    username TEXT,
                    group_name TEXT,
                    first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_seen TEXT DEFAULT CURRENT_TIMESTAMP,
                    connection_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    trust_level TEXT DEFAULT 'unknown',
                    metadata TEXT
                )
            ''')

            # 请求日志表
            db_manager.execute('''
                CREATE TABLE IF NOT EXISTS request_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    terminal_id TEXT,
                    ip_address TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    method TEXT,
                    endpoint TEXT NOT NULL,
                    referer TEXT,
                    request_data TEXT,
                    response_time REAL,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    is_suspicious BOOLEAN DEFAULT 0,
                    threat_level TEXT DEFAULT 'none',
                    FOREIGN KEY (terminal_id) REFERENCES terminal_info(terminal_id)
                )
            ''')

            # 协议分析表
            db_manager.execute('''
                CREATE TABLE IF NOT EXISTS protocol_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    protocol_type TEXT NOT NULL,
                    bytes_received INTEGER DEFAULT 0,
                    first_packet_time TEXT,
                    duration INTEGER DEFAULT 0,
                    anomalies TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # 访问控制表
            db_manager.execute('''
                CREATE TABLE IF NOT EXISTS access_control (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT UNIQUE NOT NULL,
                    access_type TEXT NOT NULL,
                    rule_type TEXT NOT NULL,
                    added_by TEXT,
                    expires_at TEXT,
                )
            ''')

            # IP组别表
            db_manager.execute('''
                CREATE TABLE IF NOT EXISTS ip_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    permissions TEXT,
                    modified_at TEXT
                )
            ''')

            # 用户组别关联表
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    group_id INTEGER NOT NULL,
                    ip_address TEXT,
                    FOREIGN KEY (group_id) REFERENCES ip_groups(id)
                )
            ''')

            # 错误日志表
            db_manager.execute('''
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT NOT NULL,
                    error_type TEXT NOT NULL,
                    stack_trace TEXT,
                    source TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    request_data TEXT,
                    session_id TEXT,
                    user_id TEXT,
                    resolved BOOLEAN DEFAULT 0,
                    resolved_at TEXT,
                )
            ''')

                CREATE TABLE IF NOT EXISTS client_exception (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    terminal_id TEXT,
                    ip_address TEXT NOT NULL,
                    exception_type TEXT NOT NULL,
                    stack_trace TEXT,
                    network_logs TEXT,
                    browser_info TEXT,
                    device_info TEXT,
                    user_action TEXT,
                    page_url TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    resolved BOOLEAN DEFAULT 0,
                    resolved_at TEXT
                )
            # 数据库错误表
            db_manager.execute('''
                CREATE TABLE IF NOT EXISTS database_error (
                    ip_address TEXT NOT NULL,
                    error_type TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    sql_query TEXT,
                    table_name TEXT,
                    operation TEXT,
                    connection_id TEXT,
                    severity TEXT NOT NULL,
                    resolved BOOLEAN DEFAULT 0,
                    resolved_at TEXT
            ''')

            # 连接统计表
            db_manager.execute('''
                CREATE TABLE IF NOT EXISTS connection_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    port INTEGER NOT NULL,
                    protocol TEXT NOT NULL,
                    avg_response_time REAL DEFAULT 0,
                    last_connection TEXT,
                    peak_time TEXT,
                    threat_level TEXT DEFAULT 'none',
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # 创建索引
            db_manager.execute('CREATE INDEX IF NOT EXISTS idx_error_log_ip ON error_log(ip_address)')
            db_manager.execute('CREATE INDEX IF NOT EXISTS idx_access_control_ip ON access_control(ip_address)')
            db_manager.execute('CREATE INDEX IF NOT EXISTS idx_terminal_info_ip ON terminal_info(ip_address)')

        except Exception as e:
            logger.error(f"创建监控数据库表失败: {str(e)}")

    def record_terminal(self, terminal_data):
        """记录终端信息"""
            terminal_id = terminal_data.get('terminal_id')
            existing = db_manager.fetch_one(
            )

            if existing:
                db_manager.update('terminal_info', {
                    'last_seen': datetime.now().isoformat(),
                    'connection_count': existing['connection_count'] + 1,
                }, f'terminal_id = "{terminal_id}"')
                    'terminal_id': terminal_id,
                    'ip_address': ip_address,
                    'hostname': terminal_data.get('hostname'),
                    'os_type': terminal_data.get('os_type'),
                    'username': terminal_data.get('username'),
                    'group_name': terminal_data.get('group_name'),
                    'metadata': str(terminal_data)
                })

            return True
            logger.error(f"记录终端信息失败: {str(e)}")
            return False
    def record_request(self, request_data):
        """记录请求信息"""
        try:
            db_manager.insert('request_log', {
                'terminal_id': request_data.get('terminal_id'),
                'ip_address': request_data.get('ip_address'),
                'port': request_data.get('port'),
                'protocol': request_data.get('protocol'),
                'endpoint': request_data.get('endpoint'),
                'user_agent': request_data.get('user_agent'),
                'referer': request_data.get('referer'),
                'request_data': str(request_data.get('data', {})),
                'response_code': request_data.get('response_code'),
                'response_time': request_data.get('response_time'),
                'is_suspicious': request_data.get('is_suspicious', 0),
                'threat_level': request_data.get('threat_level', 'none')
            })
            return True
        except Exception as e:
            logger.error(f"记录请求信息失败: {str(e)}")
            return False

    def record_error(self, error_data):
        """记录错误信息"""
        try:
            error_type = error_data.get('error_type', 'unknown')

            if error_type in ['database', 'sql']:
                table_name = 'database_error'
            elif error_type in ['client', 'javascript', 'console']:
            else:
                table_name = 'error_log'

            db_manager.insert(table_name, error_data)
            return True
        except Exception as e:
            logger.error(f"记录错误信息失败: {str(e)}")
            return False

    def check_access_control(self, ip_address):
        """检查访问控制"""
        try:
            # 检查是否在黑名单
            blacklisted = db_manager.fetch_one(
                'SELECT * FROM access_control WHERE ip_address = ? AND access_type = ?',
                (ip_address, 'blacklist')
            )
            if blacklisted:
                expires_at = blacklisted.get('expires_at')
                if expires_at and datetime.fromisoformat(expires_at) < datetime.now():
                    return 'expired'
                return 'blocked'

            # 检查是否在白名单
            whitelisted = db_manager.fetch_one(
                'SELECT * FROM access_control WHERE ip_address = ? AND access_type = ?',
            )

            if whitelisted:
                return 'allowed'

            return 'unknown'
        except Exception as e:
            logger.error(f"检查访问控制失败: {str(e)}")
            return 'unknown'

    def add_to_blacklist(self, ip_address, reason, duration=None):
        """添加到黑名单"""
        try:
            expires_at = None
            if duration:
                from datetime import timedelta
                expires_at = (datetime.now() + timedelta(seconds=duration)).isoformat()

                'DELETE FROM access_control WHERE ip_address = ? AND access_type = ?',
                (ip_address, 'blacklist')
            )

            db_manager.insert('access_control', {
                'ip_address': ip_address,
                'access_type': 'blacklist',
                'reason': reason,
                'expires_at': expires_at
            })

            logger.warning(f"IP {ip_address} 已添加到黑名单: {reason}")
            return True
        except Exception as e:
            logger.error(f"添加黑名单失败: {str(e)}")
            return False

    def add_to_whitelist(self, ip_address, reason):
        """添加到白名单"""
        try:
            db_manager.execute(
                'DELETE FROM access_control WHERE ip_address = ? AND access_type = ?',
                (ip_address, 'whitelist')
            )

                'ip_address': ip_address,
                'access_type': 'whitelist',
                'rule_type': 'manual',
                'reason': reason
            })

            logger.info(f"IP {ip_address} 已添加到白名单: {reason}")
            return True
        except Exception as e:
            logger.error(f"添加白名单失败: {str(e)}")
            return False

    def get_all_terminals(self):
        """获取所有终端信息"""
        try:
            return db_manager.fetch_all('SELECT * FROM terminal_info ORDER BY last_seen DESC')
        except Exception as e:
            logger.error(f"获取终端信息失败: {str(e)}")
            return []

        """获取所有错误信息"""
        try:
            errors = []
                result = db_manager.fetch_all(f'SELECT * FROM {table} ORDER BY timestamp DESC LIMIT ?', (limit,))
                for item in result:
                    item['source_table'] = table
            return sorted(errors, key=lambda x: x['timestamp'], reverse=True)[:limit]
        except Exception as e:
            logger.error(f"获取错误信息失败: {str(e)}")
            return []

    def get_access_stats(self):
        """获取访问统计"""
            stats = {
                'total_terminals': 0,
                'active_terminals': 0,
                'blocked_ips': 0,
                'whitelisted_ips': 0,
                'suspicious_requests': 0,
                'total_errors': 0,
                'unresolved_errors': 0
            }
            stats['total_terminals'] = db_manager.fetch_one('SELECT COUNT(*) as count FROM terminal_info')['count']
            stats['active_terminals'] = db_manager.fetch_one("SELECT COUNT(*) as count FROM terminal_info WHERE status = 'active'")['count']
            stats['blocked_ips'] = db_manager.fetch_one("SELECT COUNT(*) as count FROM access_control WHERE access_type = 'blacklist'")['count']
            stats['whitelisted_ips'] = db_manager.fetch_one("SELECT COUNT(*) as count FROM access_control WHERE access_type = 'whitelist'")['count']
            stats['suspicious_requests'] = db_manager.fetch_one('SELECT COUNT(*) as count FROM request_log WHERE is_suspicious = 1')['count']
            stats['total_errors'] = db_manager.fetch_one('SELECT COUNT(*) as count FROM error_log')['count']
            stats['unresolved_errors'] = db_manager.fetch_one('SELECT COUNT(*) as count FROM error_log WHERE resolved = 0')['count']

            return stats
            logger.error(f"获取访问统计失败: {str(e)}")
            return stats

class TerminalMonitorService:
    """终端监控服务"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                    cls._instance = super().__new__(cls)
        return cls._instance

        self.failed_attempts = {}
        # 启动后台监控线程
        self._start_monitoring_threads()
        logger.info("终端监控服务初始化成功")
        cleanup_thread = threading.Thread(target=self._cleanup_old_records, daemon=True)

        # 威胁检测线程
        threat_thread = threading.Thread(target=self._detect_threats, daemon=True)
        threat_thread.start()

        logger.info("终端监控线程启动成功")

    def _cleanup_old_records(self):
        """清理旧记录"""
        while self.monitoring_enabled:
            try:
                retention_days = self.config.MONITOR_CONFIG['log_retention_days']

                db_manager.execute(
                    f"DELETE FROM request_log WHERE timestamp < datetime('now', '-{retention_days} days')"
                )
                db_manager.execute(
                    f"DELETE FROM error_log WHERE timestamp < datetime('now', '-{retention_days} days')"
                )
                db_manager.execute(
                    f"DELETE FROM client_exception WHERE timestamp < datetime('now', '-{retention_days} days')"
                )
                db_manager.execute(
                    f"DELETE FROM database_error WHERE timestamp < datetime('now', '-{retention_days} days')"
                )

                time.sleep(3600)  # 每小时清理一次
                logger.error(f"清理旧记录失败: {str(e)}")
                time.sleep(3600)

    def _detect_threats(self):
        """检测威胁"""
            try:
                time.sleep(60)  # 每分钟检测一次

                # 检测异常请求模式
                suspicious_ips = db_manager.fetch_all(
                    'SELECT ip_address, COUNT(*) as count FROM request_log WHERE is_suspicious = 1 GROUP BY ip_address'
                )

                for record in suspicious_ips:
                    ip = record['ip_address']
                    count = record['count']

                    if count > self.config.MONITOR_CONFIG['suspicious_threshold']:
                        if ip not in self.failed_attempts:
                            self.failed_attempts[ip] = 0
                        self.failed_attempts[ip] += count

                            self.db.add_to_blacklist(
                                ip,
                                f"检测到异常请求模式: {count}次可疑请求",
                                self.config.BLACKLIST_CONFIG['block_duration']
                            )
                            self.failed_attempts[ip] = 0

            except Exception as e:
                logger.error(f"威胁检测失败: {str(e)}")

    def generate_terminal_id(self, request):
        user_agent = request.headers.get('User-Agent', '')
        ip_address = self.get_client_ip(request)
        return f"{ip_address}_{hash(user_agent) % 100000}"

    def get_client_ip(self, request):
        """获取客户端IP"""
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        else:
            return request.remote_addr

    def record_request(self, request, response=None, response_time=0):
        """记录请求"""
        try:
            terminal_id = getattr(g, 'terminal_id', self.generate_terminal_id(request))
            ip_address = self.get_client_ip(request)

            # 检查访问控制
            access_status = self.db.check_access_control(ip_address)

            # 记录终端信息
            terminal_data = {
                'terminal_id': terminal_id,
                'ip_address': ip_address,
                'username': getattr(g, 'username', None),
                'user_agent': request.headers.get('User-Agent'),
                'os_type': self._detect_os(request.headers.get('User-Agent', '')),
                'browser_type': self._detect_browser(request.headers.get('User-Agent', ''))
            }

            is_suspicious, threat_level = self._analyze_request(request)

            # 构建请求数据
            request_data = {
                'terminal_id': terminal_id,
                'ip_address': ip_address,
                'port': request.environ.get('SERVER_PORT'),
                'protocol': request.scheme.upper(),
                'method': request.method,
                'endpoint': request.path,
                'user_agent': request.headers.get('User-Agent'),
                'referer': request.headers.get('Referer'),
                'response_code': response.status_code if response else None,
                'response_time': response_time,
                'is_suspicious': is_suspicious,
                'threat_level': threat_level
            }
            self.db.record_request(request_data)

            # 如果被阻止，返回警告
            if access_status == 'blocked':
                return False, "IP已被阻止"

            return True, "请求记录成功"

        except Exception as e:
            logger.error(f"记录请求失败: {str(e)}")
            return False, str(e)

    def record_error(self, error_type, error_message, severity='medium', source='server', request=None, **kwargs):
        """记录错误"""
        try:
            ip_address = 'unknown'
            terminal_id = 'unknown'
            if request:
                ip_address = self.get_client_ip(request)
                terminal_id = getattr(g, 'terminal_id', self.generate_terminal_id(request))

            error_data = {
                'terminal_id': terminal_id,
                'ip_address': ip_address,
                'error_type': error_type,
                'error_message': error_message,
                'severity': severity,
                'source': source,
                'request_data': str(dict(request.args)) if request else None
            }
            error_data.update(kwargs)


            logger.error(f"错误记录: [{error_type}] {error_message} (来源: {source}, IP: {ip_address})")

            return True
        except Exception as e:
            logger.error(f"记录错误失败: {str(e)}")
            return False

    def _analyze_request(self, request):
        is_suspicious = False
        threat_level = 'none'

        # 检查SQL注入
        sql_patterns = [
            r"(\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b|\bEXEC\b|\bEXECUTE\b)",
            r"(--|;|'|\"|\\|\*|\bOR\b|\bAND\b)"
        ]

        request_text = f"{request.path} {request.query_string.decode()}"

        for pattern in sql_patterns:
            if re.search(pattern, request_text, re.IGNORECASE):
                is_suspicious = True
                threat_level = 'high'
                break

        # 检查XSS
            r"(<script|javascript:|onerror=|onload=)",
        ]

        for pattern in xss_patterns:
            if re.search(pattern, request_text, re.IGNORECASE):
                is_suspicious = True
                    threat_level = 'medium'
                break

        # 检查路径遍历
        path_traversal_patterns = [
            r"(/etc/passwd|/windows/system32)"
        ]
        for pattern in path_traversal_patterns:
            if re.search(pattern, request_text, re.IGNORECASE):
                is_suspicious = True
                threat_level = 'high'
                break

        return is_suspicious, threat_level

    def _detect_os(self, user_agent):
        """检测操作系统"""
        if 'Windows' in user_agent:
            return 'Windows'
        elif 'Mac' in user_agent:
            return 'macOS'
        elif 'Linux' in user_agent:
            return 'Linux'
        elif 'iOS' in user_agent:
            return 'iOS'
        elif 'Android' in user_agent:
            return 'Android'
            return 'Unknown'

    def _detect_browser(self, user_agent):
        """检测浏览器"""
        if 'Chrome' in user_agent:
            return 'Chrome'
        elif 'Firefox' in user_agent:
            return 'Firefox'
        elif 'Safari' in user_agent:
            return 'Safari'
        elif 'Edge' in user_agent:
            return 'Edge'
            return 'IE'
        else:
            return 'Unknown'
    def get_terminals(self):
        """获取所有终端"""
        return self.db.get_all_terminals()

    def get_errors(self, limit=100):
        """获取所有错误"""
        return self.db.get_all_errors(limit)

    def get_access_stats(self):
        """获取访问统计"""

    def block_ip(self, ip_address, reason):
        return self.db.add_to_blacklist(ip_address, reason)

    def unblock_ip(self, ip_address):
        """解除IP阻止"""
        try:
            db_manager.execute(
                'DELETE FROM access_control WHERE ip_address = ? AND access_type = ?',
                (ip_address, 'blacklist')
            )
            logger.info(f"IP {ip_address} 已从黑名单移除")
            return True
        except Exception as e:
            logger.error(f"解除IP阻止失败: {str(e)}")
            return False

    def whitelist_ip(self, ip_address, reason):
        """白名单IP"""
        return self.db.add_to_whitelist(ip_address, reason)

# 创建终端监控服务实例
terminal_monitor = TerminalMonitorService()

def monitor_request(f):
    """请求监控装饰器"""
    def decorated_function(*args, **kwargs):
        start_time = time.time()

        try:
            response = f(*args, **kwargs)
            response_time = time.time() - start_time

            # 记录请求
            if hasattr(g, 'request'):
                terminal_monitor.record_request(g.request, response, response_time)

            return response
        except Exception as e:
            response_time = time.time() - start_time
            terminal_monitor.record_error(
                'exception',
                str(e),
                severity='high',
                source='server',
                request=getattr(g, 'request', None),
                stack_trace=traceback.format_exc()
            )
            raise
    return decorated_function
