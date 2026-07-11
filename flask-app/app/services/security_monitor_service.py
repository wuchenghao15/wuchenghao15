# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
系统安全监控服务
负责漏洞扫描、安全评分、威胁检测和自动修复
"""

import os
import sys
import json
import time
import subprocess
import threading
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class SecurityMonitorService:
    """系统安全监控服务"""

    _instance = None
    _lock = threading.RLock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return

        self._initialized = True
        self._enabled = True
        self._scan_interval = 3600
        self._auto_fix_enabled = True
        self._alerts_enabled = True
        self._is_running = False
        self._scan_thread = None
        self._last_scan_time = None
        self._security_score = 100
        self._scan_history = []
        self._current_threat_level = 'low'

        self._db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
        self._init_database()

        logger.info("✅ 安全监控服务初始化完成")

    def _init_database(self):
        """初始化安全监控数据库表"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_scan_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_time TEXT NOT NULL,
                    scan_type TEXT NOT NULL,
                    total_vulnerabilities INTEGER DEFAULT 0,
                    critical_count INTEGER DEFAULT 0,
                    high_count INTEGER DEFAULT 0,
                    medium_count INTEGER DEFAULT 0,
                    low_count INTEGER DEFAULT 0,
                    security_score INTEGER DEFAULT 100,
                    threat_level TEXT DEFAULT 'low',
                    findings TEXT,
                    status TEXT DEFAULT 'completed',
                    duration REAL DEFAULT 0
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_vulnerabilities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id INTEGER,
                    cve_id TEXT,
                    package_name TEXT,
                    package_version TEXT,
                    fixed_version TEXT,
                    severity TEXT,
                    description TEXT,
                    references TEXT,
                    status TEXT DEFAULT 'open',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (scan_id) REFERENCES security_scan_results(id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT,
                    details TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    acknowledged_at TEXT
                )
            ''')

            conn.commit()
            logger.info("安全监控数据库表初始化完成")

    @staticmethod
    def _get_db_connection():
        """获取数据库连接"""
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def enable(self):
        """启用安全监控"""
        self._enabled = True
        logger.info("安全监控已启用")

    def disable(self):
        """禁用安全监控"""
        self._enabled = False
        self.stop_scanner()
        logger.info("安全监控已禁用")

    def start_scanner(self):
        """启动安全扫描器"""
        if not self._enabled:
            logger.warning("安全监控已禁用，无法启动扫描器")
            return

        if self._is_running:
            logger.info("安全扫描器已在运行中")
            return

        self._is_running = True
        self._scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
        self._scan_thread.start()
        logger.info("安全扫描器已启动")

    def stop_scanner(self):
        """停止安全扫描器"""
        self._is_running = False
        if self._scan_thread:
            self._scan_thread.join(timeout=5)
        logger.info("安全扫描器已停止")

    def _scan_loop(self):
        """扫描循环"""
        self._run_full_scan()

        while self._is_running:
            try:
                time.sleep(self._scan_interval)
                if self._is_running:
                    self._run_full_scan()
            except Exception as e:
                logger.error(f"扫描循环出错: {str(e)}")

    def _run_full_scan(self):
        """执行完整安全扫描"""
        if not self._enabled:
            return

        start_time = datetime.now()
        logger.info("开始执行安全扫描...")

        try:
            results = {
                'dependency_scan': self._scan_dependencies(),
                'file_scan': self._scan_files(),
                'config_scan': self._scan_configs()
            }

            vulnerabilities = []
            for scan_type, scan_result in results.items():
                if scan_result.get('vulnerabilities'):
                    vulnerabilities.extend(scan_result['vulnerabilities'])

            self._calculate_security_score(vulnerabilities)
            self._determine_threat_level(vulnerabilities)
            self._save_scan_results(vulnerabilities, start_time)

            if self._auto_fix_enabled and vulnerabilities:
                self._auto_fix_vulnerabilities(vulnerabilities)

            if self._alerts_enabled and self._current_threat_level in ['high', 'critical']:
                self._generate_alerts(vulnerabilities)

            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"安全扫描完成，耗时 {duration:.2f} 秒，发现 {len(vulnerabilities)} 个漏洞")

        except Exception as e:
            logger.error(f"安全扫描失败: {str(e)}")

    def _scan_dependencies(self) -> Dict[str, Any]:
        """扫描依赖漏洞"""
        vulnerabilities = []
        findings = []

        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--format=json'],
                capture_output=True, text=True, timeout=60
            )

            if result.returncode == 0:
                packages = json.loads(result.stdout)

                for pkg in packages:
                    name = pkg.get('name', '')
                    version = pkg.get('version', '')

                    check_result = self._check_package_vulnerability(name, version)
                    if check_result.get('vulnerable'):
                        vulnerabilities.append({
                            'type': 'dependency',
                            'package_name': name,
                            'package_version': version,
                            **check_result
                        })
                        findings.append({
                            'type': 'dependency',
                            'package': name,
                            'version': version,
                            'severity': check_result.get('severity', 'unknown'),
                            'description': check_result.get('description', '')
                        })

        except Exception as e:
            logger.error(f"依赖扫描失败: {str(e)}")

        return {
            'type': 'dependency',
            'vulnerabilities': vulnerabilities,
            'findings': findings,
            'total': len(vulnerabilities)
        }

    def _check_package_vulnerability(self, package_name: str, version: str) -> Dict[str, Any]:
        """检查单个包的漏洞"""
        known_vulnerabilities = {
            'flask': {
                'vulnerable_versions': ['<2.3.0'],
                'severity': 'high',
                'description': '存在安全漏洞，建议升级到最新版本'
            },
            'jinja2': {
                'vulnerable_versions': ['<3.1.2'],
                'severity': 'high',
                'description': '存在模板注入漏洞'
            },
            'werkzeug': {
                'vulnerable_versions': ['<2.3.0'],
                'severity': 'medium',
                'description': '存在安全漏洞'
            },
            'requests': {
                'vulnerable_versions': ['<2.31.0'],
                'severity': 'medium',
                'description': '存在SSL/TLS相关漏洞'
            },
            'numpy': {
                'vulnerable_versions': ['<1.24.0'],
                'severity': 'medium',
                'description': '存在安全漏洞'
            },
            'scikit-learn': {
                'vulnerable_versions': ['<1.2.0'],
                'severity': 'low',
                'description': '存在安全漏洞'
            }
        }

        pkg_info = known_vulnerabilities.get(package_name.lower())
        if not pkg_info:
            return {'vulnerable': False}

        for version_range in pkg_info['vulnerable_versions']:
            if self._version_less_than(version, version_range[1:]):
                return {
                    'vulnerable': True,
                    'severity': pkg_info['severity'],
                    'description': pkg_info['description'],
                    'fixed_version': version_range[1:]
                }

        return {'vulnerable': False}

    def _version_less_than(self, current_version: str, target_version: str) -> bool:
        """比较版本号"""
        try:
            current_parts = list(map(int, current_version.split('.')[:3]))
            target_parts = list(map(int, target_version.split('.')[:3]))

            while len(current_parts) < 3:
                current_parts.append(0)
            while len(target_parts) < 3:
                target_parts.append(0)

            return current_parts < target_parts
        except:
            return False

    def _scan_files(self) -> Dict[str, Any]:
        """扫描敏感文件"""
        vulnerabilities = []
        findings = []

        sensitive_patterns = [
            (r'password\s*=\s*["\'].*["\']', '硬编码密码', 'critical'),
            (r'secret[_-]?key\s*=\s*["\'].*["\']', '硬编码密钥', 'critical'),
            (r'api[_-]?key\s*=\s*["\'].*["\']', '硬编码API密钥', 'high'),
            (r'token\s*=\s*["\'].*["\']', '硬编码Token', 'high'),
            (r'private[_-]?key\s*=\s*["\'].*["\']', '硬编码私钥', 'critical')
        ]

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        exclude_dirs = ['__pycache__', '.git', 'node_modules', 'venv', '.env']

        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file in files:
                if file.endswith('.py') or file.endswith('.env'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()

                        for pattern, description, severity in sensitive_patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                vulnerabilities.append({
                                    'type': 'file',
                                    'file_path': file_path,
                                    'pattern': pattern,
                                    'description': description,
                                    'severity': severity
                                })
                                findings.append({
                                    'type': 'file',
                                    'file': file,
                                    'severity': severity,
                                    'description': description
                                })

                    except Exception:
                        pass

        return {
            'type': 'file',
            'vulnerabilities': vulnerabilities,
            'findings': findings,
            'total': len(vulnerabilities)
        }

    def _scan_configs(self) -> Dict[str, Any]:
        """扫描配置安全"""
        vulnerabilities = []
        findings = []

        config_checks = [
            ('SECRET_KEY', self._check_secret_key_strength, 'high'),
            ('DEBUG', self._check_debug_mode, 'high'),
            ('SQLALCHEMY_DATABASE_URI', self._check_database_config, 'medium')
        ]

        for config_key, check_func, severity in config_checks:
            result = check_func(config_key)
            if not result.get('secure', True):
                vulnerabilities.append({
                    'type': 'config',
                    'config_key': config_key,
                    'severity': severity,
                    'description': result.get('message', '')
                })
                findings.append({
                    'type': 'config',
                    'key': config_key,
                    'severity': severity,
                    'description': result.get('message', '')
                })

        return {
            'type': 'config',
            'vulnerabilities': vulnerabilities,
            'findings': findings,
            'total': len(vulnerabilities)
        }

    def _check_secret_key_strength(self, key: str) -> Dict[str, Any]:
        """检查SECRET_KEY强度"""
        secret_key = os.environ.get(key)
        if not secret_key:
            return {'secure': False, 'message': 'SECRET_KEY未设置'}
        if len(secret_key) < 32:
            return {'secure': False, 'message': 'SECRET_KEY长度不足（建议至少32字符）'}
        return {'secure': True}

    def _check_debug_mode(self, key: str) -> Dict[str, Any]:
        """检查DEBUG模式"""
        debug_mode = os.environ.get(key, 'false').lower()
        if debug_mode == 'true':
            return {'secure': False, 'message': 'DEBUG模式已启用，生产环境应禁用'}
        return {'secure': True}

    def _check_database_config(self, key: str) -> Dict[str, Any]:
        """检查数据库配置"""
        db_uri = os.environ.get(key, '')
        if 'localhost' not in db_uri and '127.0.0.1' not in db_uri and 'sqlite' not in db_uri:
            return {'secure': False, 'message': '数据库连接地址可能存在安全风险'}
        return {'secure': True}

    def _calculate_security_score(self, vulnerabilities: List[Dict]) -> int:
        """计算安全评分"""
        score = 100

        severity_weights = {
            'critical': 20,
            'high': 10,
            'medium': 5,
            'low': 2
        }

        for vuln in vulnerabilities:
            severity = vuln.get('severity', 'low')
            weight = severity_weights.get(severity, 2)
            score -= weight

        self._security_score = max(0, score)
        logger.info(f"安全评分: {self._security_score}/100")
        return self._security_score

    def _determine_threat_level(self, vulnerabilities: List[Dict]) -> str:
        """确定威胁级别"""
        critical_count = sum(1 for v in vulnerabilities if v.get('severity') == 'critical')
        high_count = sum(1 for v in vulnerabilities if v.get('severity') == 'high')

        if critical_count > 0:
            self._current_threat_level = 'critical'
        elif high_count >= 3:
            self._current_threat_level = 'high'
        elif high_count >= 1 or len(vulnerabilities) >= 5:
            self._current_threat_level = 'medium'
        else:
            self._current_threat_level = 'low'

        logger.info(f"威胁级别: {self._current_threat_level}")
        return self._current_threat_level

    def _save_scan_results(self, vulnerabilities: List[Dict], start_time: datetime):
        """保存扫描结果"""
        duration = (datetime.now() - start_time).total_seconds()

        critical_count = sum(1 for v in vulnerabilities if v.get('severity') == 'critical')
        high_count = sum(1 for v in vulnerabilities if v.get('severity') == 'high')
        medium_count = sum(1 for v in vulnerabilities if v.get('severity') == 'medium')
        low_count = sum(1 for v in vulnerabilities if v.get('severity') == 'low')

        with self._get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO security_scan_results 
                (scan_time, scan_type, total_vulnerabilities, critical_count, high_count,
                 medium_count, low_count, security_score, threat_level, findings, duration)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                start_time.isoformat(),
                'full',
                len(vulnerabilities),
                critical_count,
                high_count,
                medium_count,
                low_count,
                self._security_score,
                self._current_threat_level,
                json.dumps(vulnerabilities, ensure_ascii=False),
                duration
            ))

            scan_id = cursor.lastrowid

            for vuln in vulnerabilities:
                cursor.execute('''
                    INSERT INTO security_vulnerabilities
                    (scan_id, package_name, package_version, fixed_version,
                     severity, description, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    scan_id,
                    vuln.get('package_name', ''),
                    vuln.get('package_version', ''),
                    vuln.get('fixed_version', ''),
                    vuln.get('severity', 'low'),
                    vuln.get('description', ''),
                    'open'
                ))

            conn.commit()

        self._last_scan_time = start_time
        self._scan_history.append({
            'time': start_time.isoformat(),
            'score': self._security_score,
            'threat_level': self._current_threat_level,
            'total_vulnerabilities': len(vulnerabilities)
        })

        if len(self._scan_history) > 50:
            self._scan_history = self._scan_history[-50:]

    def _auto_fix_vulnerabilities(self, vulnerabilities: List[Dict]):
        """自动修复漏洞"""
        for vuln in vulnerabilities:
            if vuln.get('type') == 'dependency' and vuln.get('fixed_version'):
                package_name = vuln.get('package_name', '')
                fixed_version = vuln.get('fixed_version', '')

                try:
                    logger.info(f"尝试自动修复: {package_name} -> {fixed_version}")
                    result = subprocess.run(
                        [sys.executable, '-m', 'pip', 'install', f'{package_name}>={fixed_version}'],
                        capture_output=True, text=True, timeout=120
                    )

                    if result.returncode == 0:
                        logger.info(f"自动修复成功: {package_name}")
                        self._mark_vulnerability_fixed(package_name)
                    else:
                        logger.warning(f"自动修复失败: {package_name}, 错误: {result.stderr}")

                except Exception as e:
                    logger.error(f"自动修复异常: {package_name}, 错误: {str(e)}")

    def _mark_vulnerability_fixed(self, package_name: str):
        """标记漏洞已修复"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE security_vulnerabilities SET status = ? WHERE package_name = ? AND status = ?',
                ('fixed', package_name, 'open')
            )
            conn.commit()

    def _generate_alerts(self, vulnerabilities: List[Dict]):
        """生成安全警报"""
        critical_vulns = [v for v in vulnerabilities if v.get('severity') in ['critical', 'high']]

        for vuln in critical_vulns:
            title = f"安全警报: {vuln.get('severity').upper()}级别漏洞"
            message = vuln.get('description', '')

            if vuln.get('package_name'):
                message += f"\n包名: {vuln.get('package_name')}"
                message += f"\n当前版本: {vuln.get('package_version')}"
                if vuln.get('fixed_version'):
                    message += f"\n建议版本: {vuln.get('fixed_version')}"

            self._add_alert(vuln.get('severity', 'high'), title, message)

    def _add_alert(self, severity: str, title: str, message: str):
        """添加安全警报"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO security_alerts (alert_type, severity, title, message)
                VALUES (?, ?, ?, ?)
            ''', ('vulnerability', severity, title, message))
            conn.commit()

        logger.warning(f"安全警报: {title}")

    def get_security_status(self) -> Dict[str, Any]:
        """获取安全状态"""
        return {
            'enabled': self._enabled,
            'is_running': self._is_running,
            'security_score': self._security_score,
            'threat_level': self._current_threat_level,
            'last_scan_time': self._last_scan_time.isoformat() if self._last_scan_time else None,
            'scan_interval': self._scan_interval,
            'auto_fix_enabled': self._auto_fix_enabled,
            'alerts_enabled': self._alerts_enabled
        }

    def get_scan_history(self, limit: int = 20) -> List[Dict]:
        """获取扫描历史"""
        return self._scan_history[-limit:]

    def get_recent_vulnerabilities(self, limit: int = 50) -> List[Dict]:
        """获取最近的漏洞"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM security_vulnerabilities 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_alerts(self, status: str = None) -> List[Dict]:
        """获取安全警报"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute('''
                    SELECT * FROM security_alerts 
                    WHERE status = ? 
                    ORDER BY created_at DESC
                ''', (status,))
            else:
                cursor.execute('''
                    SELECT * FROM security_alerts 
                    ORDER BY created_at DESC
                ''')
            return [dict(row) for row in cursor.fetchall()]

    def acknowledge_alert(self, alert_id: int):
        """确认警报"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE security_alerts SET status = ?, acknowledged_at = ? WHERE id = ?',
                ('acknowledged', datetime.now().isoformat(), alert_id)
            )
            conn.commit()

    def run_manual_scan(self) -> Dict[str, Any]:
        """手动执行扫描"""
        start_time = datetime.now()
        logger.info("手动安全扫描开始...")

        results = {
            'dependency_scan': self._scan_dependencies(),
            'file_scan': self._scan_files(),
            'config_scan': self._scan_configs()
        }

        vulnerabilities = []
        for scan_type, scan_result in results.items():
            if scan_result.get('vulnerabilities'):
                vulnerabilities.extend(scan_result['vulnerabilities'])

        self._calculate_security_score(vulnerabilities)
        self._determine_threat_level(vulnerabilities)
        self._save_scan_results(vulnerabilities, start_time)

        duration = (datetime.now() - start_time).total_seconds()

        return {
            'success': True,
            'scan_time': start_time.isoformat(),
            'duration': duration,
            'security_score': self._security_score,
            'threat_level': self._current_threat_level,
            'total_vulnerabilities': len(vulnerabilities),
            'results': results
        }

    def update_config(self, config: Dict[str, Any]):
        """更新配置"""
        if 'scan_interval' in config:
            self._scan_interval = int(config['scan_interval'])
        if 'auto_fix_enabled' in config:
            self._auto_fix_enabled = bool(config['auto_fix_enabled'])
        if 'alerts_enabled' in config:
            self._alerts_enabled = bool(config['alerts_enabled'])
        logger.info("安全监控配置已更新")


import re

security_monitor_service = SecurityMonitorService()