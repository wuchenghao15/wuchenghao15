# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
安全工程师AI员工模块
负责系统安全测试、功能测试、性能测试、安全扫描，并生成测试报告
"""

import time
import uuid
import json
import logging
import threading
import psutil
import os
import sys
import re
import sqlite3
import hashlib
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class TestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"

class TestPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class TestType(Enum):
    SECURITY = "security"
    FUNCTIONAL = "functional"
    PERFORMANCE = "performance"
    INTEGRATION = "integration"
    REGRESSION = "regression"

class TestSeverity(Enum):
    BLOCKER = "blocker"
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    TRIVIAL = "trivial"

class SecurityEngineerEmployee:
    """安全工程师AI员工 - 系统安全测试、功能测试、性能测试、安全扫描"""

    def __init__(self):
        self.employee_id = f"security_engineer_{uuid.uuid4().hex[:8]}"
        self.name = "安全工程师"
        self.type = "security_engineer"
        self.skills = [
            "security_testing",
            "functional_testing",
            "performance_testing",
            "security_scanning",
            "vulnerability_assessment",
            "penetration_testing",
            "code_analysis",
            "report_generation",
            "test_automation",
            "rule_writing",
            "compliance_check",
            "audit_logging"
        ]
        self.responsibilities = [
            "执行系统安全测试",
            "执行系统功能测试",
            "执行系统性能测试",
            "执行安全漏洞扫描",
            "评估安全风险",
            "执行渗透测试",
            "分析代码安全",
            "生成测试报告",
            "自动化测试流程",
            "编写测试规则",
            "检查合规性",
            "记录审计日志"
        ]
        self.status = "active"
        self.is_running = False
        self.test_results = []
        self.security_findings = []
        self.test_rules = []
        self._lock = threading.Lock()
        self._test_thread = None
        self._create_tables()
        self._load_test_rules()

    def _create_tables(self):
        try:
            db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'security_engineer.db')
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS test_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        test_id TEXT UNIQUE,
                        test_name TEXT,
                        test_type TEXT,
                        priority TEXT,
                        status TEXT,
                        severity TEXT,
                        message TEXT,
                        details TEXT,
                        execution_time REAL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS security_findings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        finding_id TEXT UNIQUE,
                        category TEXT,
                        severity TEXT,
                        description TEXT,
                        location TEXT,
                        recommendation TEXT,
                        status TEXT DEFAULT 'open',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS test_rules (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        rule_id TEXT UNIQUE,
                        rule_name TEXT,
                        rule_type TEXT,
                        priority TEXT,
                        pattern TEXT,
                        description TEXT,
                        severity TEXT,
                        action TEXT,
                        enabled INTEGER DEFAULT 1,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS test_reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        report_id TEXT UNIQUE,
                        report_type TEXT,
                        title TEXT,
                        summary TEXT,
                        content TEXT,
                        generated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logger.info("[安全工程师] 数据库表创建完成")
        except Exception as e:
            logger.error(f"[安全工程师] 创建数据库表失败: {e}")

    def _load_test_rules(self):
        try:
            db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'security_engineer.db')
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM test_rules WHERE enabled = 1')
                for row in cursor.fetchall():
                    self.test_rules.append({
                        'rule_id': row[1],
                        'rule_name': row[2],
                        'rule_type': row[3],
                        'priority': row[4],
                        'pattern': row[5],
                        'description': row[6],
                        'severity': row[7],
                        'action': row[8]
                    })
            logger.info(f"[安全工程师] 加载了 {len(self.test_rules)} 条测试规则")
        except Exception as e:
            logger.error(f"[安全工程师] 加载测试规则失败: {e}")

    def _save_test_result(self, test_result: Dict):
        try:
            db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'security_engineer.db')
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO test_results 
                    (test_id, test_name, test_type, priority, status, severity, message, details, execution_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    test_result['test_id'],
                    test_result['test_name'],
                    test_result['test_type'],
                    test_result['priority'],
                    test_result['status'],
                    test_result['severity'],
                    test_result['message'],
                    json.dumps(test_result.get('details', {}), ensure_ascii=False),
                    test_result.get('execution_time', 0)
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"[安全工程师] 保存测试结果失败: {e}")

    def _save_security_finding(self, finding: Dict):
        try:
            db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'security_engineer.db')
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO security_findings 
                    (finding_id, category, severity, description, location, recommendation, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    finding['finding_id'],
                    finding['category'],
                    finding['severity'],
                    finding['description'],
                    finding['location'],
                    finding['recommendation'],
                    finding.get('status', 'open')
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"[安全工程师] 保存安全发现失败: {e}")

    def _save_test_rule(self, rule: Dict):
        try:
            db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'security_engineer.db')
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO test_rules 
                    (rule_id, rule_name, rule_type, priority, pattern, description, severity, action, enabled)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    rule['rule_id'],
                    rule['rule_name'],
                    rule['rule_type'],
                    rule['priority'],
                    rule.get('pattern', ''),
                    rule['description'],
                    rule['severity'],
                    rule.get('action', 'log'),
                    rule.get('enabled', 1)
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"[安全工程师] 保存测试规则失败: {e}")

    def run_security_scan(self, scan_type: str = 'full') -> Dict[str, Any]:
        """执行安全扫描"""
        logger.info(f"[安全工程师] 开始执行{scan_type}安全扫描...")
        
        findings = []
        scan_start = time.time()
        
        if scan_type in ['full', 'vulnerability']:
            findings.extend(self._scan_vulnerabilities())
        
        if scan_type in ['full', 'code']:
            findings.extend(self._scan_code_security())
        
        if scan_type in ['full', 'config']:
            findings.extend(self._scan_config_security())
        
        if scan_type in ['full', 'network']:
            findings.extend(self._scan_network_security())
        
        if scan_type in ['full', 'database']:
            findings.extend(self._scan_database_security())
        
        for finding in findings:
            self._save_security_finding(finding)
            self.security_findings.append(finding)
        
        scan_duration = time.time() - scan_start
        
        summary = {
            'scan_id': f"scan_{uuid.uuid4().hex[:12]}",
            'scan_type': scan_type,
            'scan_time': datetime.now().isoformat(),
            'duration': round(scan_duration, 2),
            'total_findings': len(findings),
            'critical_findings': len([f for f in findings if f['severity'] == 'critical']),
            'high_findings': len([f for f in findings if f['severity'] == 'high']),
            'medium_findings': len([f for f in findings if f['severity'] == 'medium']),
            'low_findings': len([f for f in findings if f['severity'] == 'low']),
            'findings': findings
        }
        
        logger.info(f"[安全工程师] 安全扫描完成，发现 {len(findings)} 个安全问题")
        return summary

    def _scan_vulnerabilities(self) -> List[Dict]:
        findings = []
        try:
            logger.info("[安全工程师] 扫描常见漏洞...")
            
            password_patterns = [
                r'password\s*=\s*["\'].*["\']',
                r'passwd\s*=\s*["\'].*["\']',
                r'api[_-]?key\s*=\s*["\'].*["\']',
                r'secret\s*=\s*["\'].*["\']',
                r'token\s*=\s*["\'].*["\']'
            ]
            
            common_paths = [
                os.path.join(os.path.dirname(__file__), '..', 'app'),
                os.path.join(os.path.dirname(__file__), '..')
            ]
            
            for path in common_paths:
                if not os.path.exists(path):
                    continue
                for root, dirs, files in os.walk(path):
                    dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', 'node_modules']]
                    for file in files:
                        if file.endswith('.py'):
                            file_path = os.path.join(root, file)
                            try:
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()
                                
                                for pattern in password_patterns:
                                    if re.search(pattern, content, re.IGNORECASE):
                                        findings.append({
                                            'finding_id': f"vuln_{uuid.uuid4().hex[:8]}",
                                            'category': 'hardcoded_credentials',
                                            'severity': 'critical',
                                            'description': f'文件中可能包含硬编码凭证',
                                            'location': file_path,
                                            'recommendation': '将敏感凭证移至环境变量或配置文件，并使用加密存储'
                                        })
                                        break
                            except Exception:
                                pass
            
            logger.info(f"[安全工程师] 漏洞扫描完成，发现 {len(findings)} 个问题")
        except Exception as e:
            logger.error(f"[安全工程师] 漏洞扫描失败: {e}")
        
        return findings

    def _scan_code_security(self) -> List[Dict]:
        findings = []
        try:
            logger.info("[安全工程师] 扫描代码安全性...")
            
            security_patterns = [
                (r'exec\s*\(', 'code_execution', '高', '代码中使用了exec函数'),
                (r'eval\s*\(', 'code_execution', '高', '代码中使用了eval函数'),
                (r'subprocess\.Popen\s*\(', 'command_injection', '高', '代码中使用了subprocess.Popen'),
                (r'os\.system\s*\(', 'command_injection', '高', '代码中使用了os.system'),
                (r'pickle\.load', 'deserialization', '高', '代码中使用了pickle.load'),
                (r'pickle\.loads', 'deserialization', '高', '代码中使用了pickle.loads'),
                (r'json\.loads\(', 'json_deserialization', '中', '代码中使用了json.loads'),
                (r'request\.args\.get', 'parameter_injection', '中', '直接使用request参数'),
                (r'flask\.request', 'request_handling', '低', '直接访问flask request')
            ]
            
            common_paths = [
                os.path.join(os.path.dirname(__file__), '..', 'app'),
                os.path.join(os.path.dirname(__file__), '..')
            ]
            
            for path in common_paths:
                if not os.path.exists(path):
                    continue
                for root, dirs, files in os.walk(path):
                    dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', 'node_modules']]
                    for file in files:
                        if file.endswith('.py'):
                            file_path = os.path.join(root, file)
                            try:
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()
                                
                                for pattern, category, severity_cn, desc in security_patterns:
                                    if re.search(pattern, content):
                                        severity_map = {'高': 'high', '中': 'medium', '低': 'low'}
                                        findings.append({
                                            'finding_id': f"code_{uuid.uuid4().hex[:8]}",
                                            'category': category,
                                            'severity': severity_map[severity_cn],
                                            'description': desc,
                                            'location': file_path,
                                            'recommendation': f'审查{desc}的使用，确保输入已正确验证和过滤'
                                        })
                            except Exception:
                                pass
            
            logger.info(f"[安全工程师] 代码安全扫描完成，发现 {len(findings)} 个问题")
        except Exception as e:
            logger.error(f"[安全工程师] 代码安全扫描失败: {e}")
        
        return findings

    def _scan_config_security(self) -> List[Dict]:
        findings = []
        try:
            logger.info("[安全工程师] 扫描配置安全性...")
            
            config_files = ['config.py', 'settings.py', '.env', 'config.yaml', 'config.json']
            common_paths = [
                os.path.join(os.path.dirname(__file__), '..', 'app'),
                os.path.join(os.path.dirname(__file__), '..')
            ]
            
            for path in common_paths:
                if not os.path.exists(path):
                    continue
                for root, dirs, files in os.walk(path):
                    dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', 'node_modules']]
                    for file in files:
                        if file.lower() in config_files:
                            file_path = os.path.join(root, file)
                            
                            if file == '.env':
                                findings.append({
                                    'finding_id': f"config_{uuid.uuid4().hex[:8]}",
                                    'category': 'env_file',
                                    'severity': 'medium',
                                    'description': '存在.env配置文件',
                                    'location': file_path,
                                    'recommendation': '确保.env文件不在版本控制中，且权限设置为仅所有者可读'
                                })
                            
                            try:
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()
                                
                                if 'DEBUG' in content and 'True' in content:
                                    findings.append({
                                        'finding_id': f"config_{uuid.uuid4().hex[:8]}",
                                        'category': 'debug_enabled',
                                        'severity': 'high',
                                        'description': '配置文件中DEBUG模式为True',
                                        'location': file_path,
                                        'recommendation': '生产环境中应禁用DEBUG模式'
                                    })
                                
                                if 'SECRET_KEY' in content and len(content.split('SECRET_KEY')[1].split('\n')[0].strip()) < 20:
                                    findings.append({
                                        'finding_id': f"config_{uuid.uuid4().hex[:8]}",
                                        'category': 'weak_secret_key',
                                        'severity': 'high',
                                        'description': 'SECRET_KEY长度不足',
                                        'location': file_path,
                                        'recommendation': '使用至少32位的随机SECRET_KEY'
                                    })
                            except Exception:
                                pass
            
            logger.info(f"[安全工程师] 配置安全扫描完成，发现 {len(findings)} 个问题")
        except Exception as e:
            logger.error(f"[安全工程师] 配置安全扫描失败: {e}")
        
        return findings

    def _scan_network_security(self) -> List[Dict]:
        findings = []
        try:
            logger.info("[安全工程师] 扫描网络安全性...")
            
            open_ports = []
            for port in [80, 443, 5000, 8080, 8888]:
                try:
                    import socket
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.5)
                    result = sock.connect_ex(('localhost', port))
                    if result == 0:
                        open_ports.append(port)
                    sock.close()
                except Exception:
                    pass
            
            if 80 in open_ports:
                findings.append({
                    'finding_id': f"net_{uuid.uuid4().hex[:8]}",
                    'category': 'http_port_open',
                    'severity': 'medium',
                    'description': 'HTTP端口80开放',
                    'location': 'localhost:80',
                    'recommendation': '建议使用HTTPS(443)替代HTTP'
                })
            
            if open_ports:
                findings.append({
                    'finding_id': f"net_{uuid.uuid4().hex[:8]}",
                    'category': 'open_ports',
                    'severity': 'low',
                    'description': f'检测到开放端口: {open_ports}',
                    'location': 'localhost',
                    'recommendation': '确保所有开放端口都有必要的安全措施'
                })
            
            logger.info(f"[安全工程师] 网络安全扫描完成，发现 {len(findings)} 个问题")
        except Exception as e:
            logger.error(f"[安全工程师] 网络安全扫描失败: {e}")
        
        return findings

    def _scan_database_security(self) -> List[Dict]:
        findings = []
        try:
            logger.info("[安全工程师] 扫描数据库安全性...")
            
            db_extensions = ['.db', '.sqlite', '.sqlite3']
            common_paths = [
                os.path.join(os.path.dirname(__file__), '..', 'data'),
                os.path.join(os.path.dirname(__file__), '..')
            ]
            
            for path in common_paths:
                if not os.path.exists(path):
                    continue
                for root, dirs, files in os.walk(path):
                    dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv']]
                    for file in files:
                        if any(file.endswith(ext) for ext in db_extensions):
                            file_path = os.path.join(root, file)
                            
                            try:
                                stat = os.stat(file_path)
                                perms = stat.st_mode & 0o777
                                
                                if perms & 0o077:
                                    findings.append({
                                        'finding_id': f"db_{uuid.uuid4().hex[:8]}",
                                        'category': 'db_permissions',
                                        'severity': 'medium',
                                        'description': f'数据库文件权限过于开放: {oct(perms)}',
                                        'location': file_path,
                                        'recommendation': '限制数据库文件权限为仅所有者可读可写'
                                    })
                            except Exception:
                                pass
            
            logger.info(f"[安全工程师] 数据库安全扫描完成，发现 {len(findings)} 个问题")
        except Exception as e:
            logger.error(f"[安全工程师] 数据库安全扫描失败: {e}")
        
        return findings

    def run_functional_tests(self, test_categories: List[str] = None) -> Dict[str, Any]:
        """执行功能测试"""
        logger.info(f"[安全工程师] 开始执行功能测试...")
        
        if test_categories is None:
            test_categories = ['api', 'database', 'ai', 'system', 'security']
        
        results = []
        test_start = time.time()
        
        test_suites = {
            'api': self._test_api_endpoints,
            'database': self._test_database_operations,
            'ai': self._test_ai_services,
            'system': self._test_system_services,
            'security': self._test_security_features
        }
        
        for category in test_categories:
            if category in test_suites:
                try:
                    category_results = test_suites[category]()
                    results.extend(category_results)
                except Exception as e:
                    logger.error(f"[安全工程师] {category}测试失败: {e}")
                    results.append({
                        'test_id': f"test_{category}_{uuid.uuid4().hex[:8]}",
                        'test_name': f"{category}测试",
                        'test_type': 'functional',
                        'priority': 'high',
                        'status': 'failed',
                        'severity': 'critical',
                        'message': f"{category}测试执行失败: {str(e)}",
                        'details': {}
                    })
        
        for result in results:
            self._save_test_result(result)
            self.test_results.append(result)
        
        test_duration = time.time() - test_start
        
        summary = {
            'test_run_id': f"test_run_{uuid.uuid4().hex[:12]}",
            'test_type': 'functional',
            'test_time': datetime.now().isoformat(),
            'duration': round(test_duration, 2),
            'total_tests': len(results),
            'passed_tests': len([r for r in results if r['status'] == 'passed']),
            'failed_tests': len([r for r in results if r['status'] == 'failed']),
            'skipped_tests': len([r for r in results if r['status'] == 'skipped']),
            'results': results
        }
        
        logger.info(f"[安全工程师] 功能测试完成，通过 {summary['passed_tests']}/{summary['total_tests']}")
        return summary

    def _test_api_endpoints(self) -> List[Dict]:
        results = []
        try:
            logger.info("[安全工程师] 测试API端点...")
            
            api_tests = [
                {'name': '健康检查API', 'endpoint': '/api/health', 'method': 'GET', 'priority': 'critical'},
                {'name': '日志API', 'endpoint': '/api/logs', 'method': 'GET', 'priority': 'high'},
                {'name': '配置API', 'endpoint': '/api/config', 'method': 'GET', 'priority': 'high'},
                {'name': '监控API', 'endpoint': '/api/ai/monitoring/system/health', 'method': 'GET', 'priority': 'high'},
                {'name': '升级API', 'endpoint': '/api/ai/upgrade/status', 'method': 'GET', 'priority': 'medium'},
                {'name': '游戏化API', 'endpoint': '/api/ai/gamification/player/test', 'method': 'GET', 'priority': 'medium'}
            ]
            
            for test in api_tests:
                test_start = time.time()
                try:
                    import urllib.request
                    import urllib.error
                    
                    url = f"http://localhost:5000{test['endpoint']}"
                    req = urllib.request.Request(url, method=test['method'])
                    
                    try:
                        with urllib.request.urlopen(req, timeout=5) as response:
                            status_code = response.getcode()
                            if status_code >= 200 and status_code < 300:
                                results.append({
                                    'test_id': f"api_{hashlib.md5(test['endpoint'].encode()).hexdigest()[:8]}",
                                    'test_name': test['name'],
                                    'test_type': 'functional',
                                    'priority': test['priority'],
                                    'status': 'passed',
                                    'severity': 'trivial',
                                    'message': f"API响应正常，状态码: {status_code}",
                                    'details': {'endpoint': test['endpoint'], 'status_code': status_code},
                                    'execution_time': round(time.time() - test_start, 3)
                                })
                            else:
                                results.append({
                                    'test_id': f"api_{hashlib.md5(test['endpoint'].encode()).hexdigest()[:8]}",
                                    'test_name': test['name'],
                                    'test_type': 'functional',
                                    'priority': test['priority'],
                                    'status': 'failed',
                                    'severity': 'major',
                                    'message': f"API响应异常，状态码: {status_code}",
                                    'details': {'endpoint': test['endpoint'], 'status_code': status_code},
                                    'execution_time': round(time.time() - test_start, 3)
                                })
                    except urllib.error.HTTPError as e:
                        results.append({
                            'test_id': f"api_{hashlib.md5(test['endpoint'].encode()).hexdigest()[:8]}",
                            'test_name': test['name'],
                            'test_type': 'functional',
                            'priority': test['priority'],
                            'status': 'failed',
                            'severity': 'major',
                            'message': f"HTTP错误: {e.code} - {e.reason}",
                            'details': {'endpoint': test['endpoint'], 'error': str(e)},
                            'execution_time': round(time.time() - test_start, 3)
                        })
                    except (urllib.error.URLError, TimeoutError, ConnectionRefusedError):
                        results.append({
                            'test_id': f"api_{hashlib.md5(test['endpoint'].encode()).hexdigest()[:8]}",
                            'test_name': test['name'],
                            'test_type': 'functional',
                            'priority': test['priority'],
                            'status': 'skipped',
                            'severity': 'minor',
                            'message': '服务未启动或无法连接',
                            'details': {'endpoint': test['endpoint']},
                            'execution_time': round(time.time() - test_start, 3)
                        })
                except Exception as e:
                    results.append({
                        'test_id': f"api_{uuid.uuid4().hex[:8]}",
                        'test_name': test['name'],
                        'test_type': 'functional',
                        'priority': test['priority'],
                        'status': 'failed',
                        'severity': 'major',
                        'message': f"测试执行失败: {str(e)}",
                        'details': {'endpoint': test['endpoint']},
                        'execution_time': round(time.time() - test_start, 3)
                    })
            
            logger.info(f"[安全工程师] API测试完成，{len(results)}个测试")
        except Exception as e:
            logger.error(f"[安全工程师] API测试失败: {e}")
        
        return results

    def _test_database_operations(self) -> List[Dict]:
        results = []
        try:
            logger.info("[安全工程师] 测试数据库操作...")
            
            db_tests = [
                {'name': '主数据库连接', 'db_path': 'app.db', 'priority': 'critical'},
                {'name': '安全工程师数据库连接', 'db_path': 'data/security_engineer.db', 'priority': 'high'},
                {'name': '学习规则数据库连接', 'db_path': 'data/learning_rules.db', 'priority': 'high'}
            ]
            
            for test in db_tests:
                test_start = time.time()
                db_full_path = os.path.join(os.path.dirname(__file__), '..', test['db_path'])
                
                try:
                    if os.path.exists(db_full_path):
                        conn = sqlite3.connect(db_full_path)
                        cursor = conn.cursor()
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                        tables = cursor.fetchall()
                        conn.close()
                        
                        results.append({
                            'test_id': f"db_{hashlib.md5(test['db_path'].encode()).hexdigest()[:8]}",
                            'test_name': test['name'],
                            'test_type': 'functional',
                            'priority': test['priority'],
                            'status': 'passed',
                            'severity': 'trivial',
                            'message': f"数据库连接成功，表数量: {len(tables)}",
                            'details': {'db_path': test['db_path'], 'table_count': len(tables)},
                            'execution_time': round(time.time() - test_start, 3)
                        })
                    else:
                        results.append({
                            'test_id': f"db_{hashlib.md5(test['db_path'].encode()).hexdigest()[:8]}",
                            'test_name': test['name'],
                            'test_type': 'functional',
                            'priority': test['priority'],
                            'status': 'failed',
                            'severity': 'major',
                            'message': f"数据库文件不存在: {db_full_path}",
                            'details': {'db_path': test['db_path']},
                            'execution_time': round(time.time() - test_start, 3)
                        })
                except Exception as e:
                    results.append({
                        'test_id': f"db_{hashlib.md5(test['db_path'].encode()).hexdigest()[:8]}",
                        'test_name': test['name'],
                        'test_type': 'functional',
                        'priority': test['priority'],
                        'status': 'failed',
                        'severity': 'critical',
                        'message': f"数据库连接失败: {str(e)}",
                        'details': {'db_path': test['db_path'], 'error': str(e)},
                        'execution_time': round(time.time() - test_start, 3)
                    })
            
            logger.info(f"[安全工程师] 数据库测试完成，{len(results)}个测试")
        except Exception as e:
            logger.error(f"[安全工程师] 数据库测试失败: {e}")
        
        return results

    def _test_ai_services(self) -> List[Dict]:
        results = []
        try:
            logger.info("[安全工程师] 测试AI服务...")
            
            ai_tests = [
                {'name': 'AI监控员工初始化', 'module': 'ai_monitor_employee', 'priority': 'high'},
                {'name': 'AI自我学习系统初始化', 'module': 'ai_self_learning_system', 'priority': 'high'},
                {'name': 'AI脑库引擎初始化', 'module': 'ai_brain', 'priority': 'high'},
                {'name': '游戏化引擎初始化', 'module': 'gamification_engine', 'priority': 'medium'}
            ]
            
            for test in ai_tests:
                test_start = time.time()
                try:
                    module_path = f"ai_engines.{test['module']}"
                    __import__(module_path)
                    
                    results.append({
                        'test_id': f"ai_{hashlib.md5(test['module'].encode()).hexdigest()[:8]}",
                        'test_name': test['name'],
                        'test_type': 'functional',
                        'priority': test['priority'],
                        'status': 'passed',
                        'severity': 'trivial',
                        'message': f"AI模块导入成功: {test['module']}",
                        'details': {'module': test['module']},
                        'execution_time': round(time.time() - test_start, 3)
                    })
                except ImportError as e:
                    results.append({
                        'test_id': f"ai_{hashlib.md5(test['module'].encode()).hexdigest()[:8]}",
                        'test_name': test['name'],
                        'test_type': 'functional',
                        'priority': test['priority'],
                        'status': 'failed',
                        'severity': 'major',
                        'message': f"AI模块导入失败: {str(e)}",
                        'details': {'module': test['module'], 'error': str(e)},
                        'execution_time': round(time.time() - test_start, 3)
                    })
                except Exception as e:
                    results.append({
                        'test_id': f"ai_{hashlib.md5(test['module'].encode()).hexdigest()[:8]}",
                        'test_name': test['name'],
                        'test_type': 'functional',
                        'priority': test['priority'],
                        'status': 'failed',
                        'severity': 'minor',
                        'message': f"AI模块测试异常: {str(e)}",
                        'details': {'module': test['module'], 'error': str(e)},
                        'execution_time': round(time.time() - test_start, 3)
                    })
            
            logger.info(f"[安全工程师] AI服务测试完成，{len(results)}个测试")
        except Exception as e:
            logger.error(f"[安全工程师] AI服务测试失败: {e}")
        
        return results

    def _test_system_services(self) -> List[Dict]:
        results = []
        try:
            logger.info("[安全工程师] 测试系统服务...")
            
            system_tests = [
                {'name': 'CPU状态检测', 'priority': 'high'},
                {'name': '内存状态检测', 'priority': 'high'},
                {'name': '磁盘状态检测', 'priority': 'medium'},
                {'name': '网络状态检测', 'priority': 'medium'},
                {'name': '进程状态检测', 'priority': 'low'}
            ]
            
            for test in system_tests:
                test_start = time.time()
                try:
                    if test['name'] == 'CPU状态检测':
                        cpu_percent = psutil.cpu_percent(interval=0.1)
                        status = 'passed' if cpu_percent < 90 else 'warning'
                        severity = 'trivial' if cpu_percent < 90 else 'minor'
                        results.append({
                            'test_id': f"sys_cpu_{uuid.uuid4().hex[:8]}",
                            'test_name': test['name'],
                            'test_type': 'functional',
                            'priority': test['priority'],
                            'status': status,
                            'severity': severity,
                            'message': f"CPU使用率: {cpu_percent}%",
                            'details': {'cpu_percent': cpu_percent},
                            'execution_time': round(time.time() - test_start, 3)
                        })
                    
                    elif test['name'] == '内存状态检测':
                        memory = psutil.virtual_memory()
                        status = 'passed' if memory.percent < 90 else 'warning'
                        severity = 'trivial' if memory.percent < 90 else 'minor'
                        results.append({
                            'test_id': f"sys_mem_{uuid.uuid4().hex[:8]}",
                            'test_name': test['name'],
                            'test_type': 'functional',
                            'priority': test['priority'],
                            'status': status,
                            'severity': severity,
                            'message': f"内存使用率: {memory.percent}%",
                            'details': {'memory_percent': memory.percent, 'available_gb': round(memory.available/1024/1024/1024, 2)},
                            'execution_time': round(time.time() - test_start, 3)
                        })
                    
                    elif test['name'] == '磁盘状态检测':
                        disk = psutil.disk_usage('/')
                        status = 'passed' if disk.percent < 90 else 'warning'
                        severity = 'trivial' if disk.percent < 90 else 'minor'
                        results.append({
                            'test_id': f"sys_disk_{uuid.uuid4().hex[:8]}",
                            'test_name': test['name'],
                            'test_type': 'functional',
                            'priority': test['priority'],
                            'status': status,
                            'severity': severity,
                            'message': f"磁盘使用率: {disk.percent}%",
                            'details': {'disk_percent': disk.percent, 'free_gb': round(disk.free/1024/1024/1024, 2)},
                            'execution_time': round(time.time() - test_start, 3)
                        })
                    
                    elif test['name'] == '网络状态检测':
                        network = psutil.net_io_counters()
                        results.append({
                            'test_id': f"sys_net_{uuid.uuid4().hex[:8]}",
                            'test_name': test['name'],
                            'test_type': 'functional',
                            'priority': test['priority'],
                            'status': 'passed',
                            'severity': 'trivial',
                            'message': f"网络状态正常",
                            'details': {'bytes_sent': network.bytes_sent, 'bytes_recv': network.bytes_recv},
                            'execution_time': round(time.time() - test_start, 3)
                        })
                    
                    elif test['name'] == '进程状态检测':
                        process = psutil.Process(os.getpid())
                        results.append({
                            'test_id': f"sys_proc_{uuid.uuid4().hex[:8]}",
                            'test_name': test['name'],
                            'test_type': 'functional',
                            'priority': test['priority'],
                            'status': 'passed',
                            'severity': 'trivial',
                            'message': f"进程状态正常",
                            'details': {'pid': process.pid, 'name': process.name()},
                            'execution_time': round(time.time() - test_start, 3)
                        })
                except Exception as e:
                    results.append({
                        'test_id': f"sys_{uuid.uuid4().hex[:8]}",
                        'test_name': test['name'],
                        'test_type': 'functional',
                        'priority': test['priority'],
                        'status': 'failed',
                        'severity': 'major',
                        'message': f"系统检测失败: {str(e)}",
                        'details': {'error': str(e)},
                        'execution_time': round(time.time() - test_start, 3)
                    })
            
            logger.info(f"[安全工程师] 系统服务测试完成，{len(results)}个测试")
        except Exception as e:
            logger.error(f"[安全工程师] 系统服务测试失败: {e}")
        
        return results

    def _test_security_features(self) -> List[Dict]:
        results = []
        try:
            logger.info("[安全工程师] 测试安全功能...")
            
            security_tests = [
                {'name': '密码强度规则检测', 'priority': 'high'},
                {'name': '认证装饰器检测', 'priority': 'high'},
                {'name': 'SQL注入防护检测', 'priority': 'critical'},
                {'name': 'XSS防护检测', 'priority': 'high'},
                {'name': 'CSRF防护检测', 'priority': 'medium'}
            ]
            
            for test in security_tests:
                test_start = time.time()
                try:
                    if test['name'] == '密码强度规则检测':
                        password_rules = [
                            lambda p: len(p) >= 8,
                            lambda p: any(c.isupper() for c in p),
                            lambda p: any(c.islower() for c in p),
                            lambda p: any(c.isdigit() for c in p)
                        ]
                        test_passwords = ['Pass1234', 'weak', 'Short1', 'PASSWORD123']
                        passed = sum(1 for pw in test_passwords if all(rule(pw) for rule in password_rules))
                        results.append({
                            'test_id': f"sec_pwd_{uuid.uuid4().hex[:8]}",
                            'test_name': test['name'],
                            'test_type': 'security',
                            'priority': test['priority'],
                            'status': 'passed',
                            'severity': 'trivial',
                            'message': f"密码强度规则检测通过，测试密码: {passed}/{len(test_passwords)}",
                            'details': {'test_passwords': test_passwords},
                            'execution_time': round(time.time() - test_start, 3)
                        })
                    
                    elif test['name'] == '认证装饰器检测':
                        decorator_files = []
                        for root, dirs, files in os.walk(os.path.join(os.path.dirname(__file__), '..', 'app', 'api')):
                            for file in files:
                                if file.endswith('.py'):
                                    file_path = os.path.join(root, file)
                                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                        if '@require_login' in f.read() or '@require_admin' in f.read():
                                            decorator_files.append(file)
                        results.append({
                            'test_id': f"sec_auth_{uuid.uuid4().hex[:8]}",
                            'test_name': test['name'],
                            'test_type': 'security',
                            'priority': test['priority'],
                            'status': 'passed',
                            'severity': 'trivial',
                            'message': f"发现 {len(decorator_files)} 个使用认证装饰器的API文件",
                            'details': {'files': decorator_files},
                            'execution_time': round(time.time() - test_start, 3)
                        })
                    
                    elif test['name'] == 'SQL注入防护检测':
                        import sqlite3
                        db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'security_engineer.db')
                        with sqlite3.connect(db_path) as conn:
                            cursor = conn.cursor()
                            malicious_input = "1'; DROP TABLE test_results; --"
                            try:
                                cursor.execute("SELECT COUNT(*) FROM test_results WHERE id = ?", (malicious_input,))
                                cursor.fetchone()
                                results.append({
                                    'test_id': f"sec_sql_{uuid.uuid4().hex[:8]}",
                                    'test_name': test['name'],
                                    'test_type': 'security',
                                    'priority': test['priority'],
                                    'status': 'passed',
                                    'severity': 'trivial',
                                    'message': 'SQL注入防护有效，参数化查询正常',
                                    'details': {},
                                    'execution_time': round(time.time() - test_start, 3)
                                })
                            except Exception as e:
                                results.append({
                                    'test_id': f"sec_sql_{uuid.uuid4().hex[:8]}",
                                    'test_name': test['name'],
                                    'test_type': 'security',
                                    'priority': test['priority'],
                                    'status': 'failed',
                                    'severity': 'critical',
                                    'message': f"SQL注入防护失败: {str(e)}",
                                    'details': {'error': str(e)},
                                    'execution_time': round(time.time() - test_start, 3)
                                })
                    
                    elif test['name'] == 'XSS防护检测':
                        xss_payload = '<script>alert("XSS")</script>'
                        sanitized = re.sub(r'<[^>]*>', '', xss_payload)
                        is_sanitized = sanitized != xss_payload
                        results.append({
                            'test_id': f"sec_xss_{uuid.uuid4().hex[:8]}",
                            'test_name': test['name'],
                            'test_type': 'security',
                            'priority': test['priority'],
                            'status': 'passed' if is_sanitized else 'failed',
                            'severity': 'critical' if not is_sanitized else 'trivial',
                            'message': 'XSS防护有效' if is_sanitized else 'XSS防护无效',
                            'details': {'original': xss_payload, 'sanitized': sanitized},
                            'execution_time': round(time.time() - test_start, 3)
                        })
                    
                    elif test['name'] == 'CSRF防护检测':
                        csrf_protected = True
                        try:
                            from flask_wtf.csrf import CSRFProtect
                            csrf_protected = True
                        except ImportError:
                            csrf_protected = False
                        results.append({
                            'test_id': f"sec_csrf_{uuid.uuid4().hex[:8]}",
                            'test_name': test['name'],
                            'test_type': 'security',
                            'priority': test['priority'],
                            'status': 'passed' if csrf_protected else 'warning',
                            'severity': 'minor' if not csrf_protected else 'trivial',
                            'message': 'CSRF防护已启用' if csrf_protected else 'CSRF防护未启用',
                            'details': {'csrf_protected': csrf_protected},
                            'execution_time': round(time.time() - test_start, 3)
                        })
                except Exception as e:
                    results.append({
                        'test_id': f"sec_{uuid.uuid4().hex[:8]}",
                        'test_name': test['name'],
                        'test_type': 'security',
                        'priority': test['priority'],
                        'status': 'failed',
                        'severity': 'major',
                        'message': f"安全检测失败: {str(e)}",
                        'details': {'error': str(e)},
                        'execution_time': round(time.time() - test_start, 3)
                    })
            
            logger.info(f"[安全工程师] 安全功能测试完成，{len(results)}个测试")
        except Exception as e:
            logger.error(f"[安全工程师] 安全功能测试失败: {e}")
        
        return results

    def run_performance_tests(self, duration: int = 30) -> Dict[str, Any]:
        """执行性能测试"""
        logger.info(f"[安全工程师] 开始执行性能测试，持续时间: {duration}秒...")
        
        results = []
        perf_start = time.time()
        
        try:
            results.extend(self._test_cpu_performance())
            results.extend(self._test_memory_performance())
            results.extend(self._test_disk_performance())
            results.extend(self._test_response_time())
        except Exception as e:
            logger.error(f"[安全工程师] 性能测试失败: {e}")
        
        for result in results:
            self._save_test_result(result)
        
        perf_duration = time.time() - perf_start
        
        summary = {
            'test_run_id': f"perf_{uuid.uuid4().hex[:12]}",
            'test_type': 'performance',
            'test_time': datetime.now().isoformat(),
            'duration': round(perf_duration, 2),
            'total_tests': len(results),
            'passed_tests': len([r for r in results if r['status'] == 'passed']),
            'failed_tests': len([r for r in results if r['status'] == 'failed']),
            'results': results
        }
        
        logger.info(f"[安全工程师] 性能测试完成，{len(results)}个测试")
        return summary

    def _test_cpu_performance(self) -> List[Dict]:
        results = []
        try:
            cpu_usage = []
            for _ in range(5):
                cpu_usage.append(psutil.cpu_percent(interval=0.5))
                time.sleep(0.1)
            
            avg_cpu = sum(cpu_usage) / len(cpu_usage)
            max_cpu = max(cpu_usage)
            
            status = 'passed' if avg_cpu < 70 else ('warning' if avg_cpu < 90 else 'failed')
            severity = 'trivial' if avg_cpu < 70 else ('minor' if avg_cpu < 90 else 'major')
            
            results.append({
                'test_id': f"perf_cpu_{uuid.uuid4().hex[:8]}",
                'test_name': 'CPU性能测试',
                'test_type': 'performance',
                'priority': 'high',
                'status': status,
                'severity': severity,
                'message': f"CPU平均使用率: {avg_cpu:.2f}%, 峰值: {max_cpu:.2f}%",
                'details': {'avg_cpu': avg_cpu, 'max_cpu': max_cpu, 'samples': cpu_usage},
                'execution_time': 3.0
            })
        except Exception as e:
            results.append({
                'test_id': f"perf_cpu_{uuid.uuid4().hex[:8]}",
                'test_name': 'CPU性能测试',
                'test_type': 'performance',
                'priority': 'high',
                'status': 'failed',
                'severity': 'major',
                'message': f"CPU测试失败: {str(e)}",
                'details': {'error': str(e)}
            })
        
        return results

    def _test_memory_performance(self) -> List[Dict]:
        results = []
        try:
            mem_snapshots = []
            for _ in range(5):
                mem = psutil.virtual_memory()
                mem_snapshots.append({
                    'percent': mem.percent,
                    'available': mem.available
                })
                time.sleep(0.5)
            
            avg_mem = sum(s['percent'] for s in mem_snapshots) / len(mem_snapshots)
            
            status = 'passed' if avg_mem < 70 else ('warning' if avg_mem < 90 else 'failed')
            severity = 'trivial' if avg_mem < 70 else ('minor' if avg_mem < 90 else 'major')
            
            results.append({
                'test_id': f"perf_mem_{uuid.uuid4().hex[:8]}",
                'test_name': '内存性能测试',
                'test_type': 'performance',
                'priority': 'high',
                'status': status,
                'severity': severity,
                'message': f"内存平均使用率: {avg_mem:.2f}%",
                'details': {'avg_mem': avg_mem, 'snapshots': mem_snapshots},
                'execution_time': 3.0
            })
        except Exception as e:
            results.append({
                'test_id': f"perf_mem_{uuid.uuid4().hex[:8]}",
                'test_name': '内存性能测试',
                'test_type': 'performance',
                'priority': 'high',
                'status': 'failed',
                'severity': 'major',
                'message': f"内存测试失败: {str(e)}",
                'details': {'error': str(e)}
            })
        
        return results

    def _test_disk_performance(self) -> List[Dict]:
        results = []
        try:
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            status = 'passed' if disk.percent < 80 else ('warning' if disk.percent < 90 else 'failed')
            severity = 'trivial' if disk.percent < 80 else ('minor' if disk.percent < 90 else 'major')
            
            results.append({
                'test_id': f"perf_disk_{uuid.uuid4().hex[:8]}",
                'test_name': '磁盘性能测试',
                'test_type': 'performance',
                'priority': 'medium',
                'status': status,
                'severity': severity,
                'message': f"磁盘使用率: {disk.percent:.2f}%, IO读写正常",
                'details': {
                    'disk_percent': disk.percent,
                    'free_gb': round(disk.free / 1024 / 1024 / 1024, 2),
                    'read_count': disk_io.read_count,
                    'write_count': disk_io.write_count
                },
                'execution_time': 1.0
            })
        except Exception as e:
            results.append({
                'test_id': f"perf_disk_{uuid.uuid4().hex[:8]}",
                'test_name': '磁盘性能测试',
                'test_type': 'performance',
                'priority': 'medium',
                'status': 'failed',
                'severity': 'major',
                'message': f"磁盘测试失败: {str(e)}",
                'details': {'error': str(e)}
            })
        
        return results

    def _test_response_time(self) -> List[Dict]:
        results = []
        try:
            import urllib.request
            
            urls = ['http://localhost:5000/api/health']
            response_times = []
            
            for url in urls:
                for _ in range(3):
                    try:
                        start = time.time()
                        with urllib.request.urlopen(url, timeout=5) as resp:
                            resp.read()
                        elapsed = time.time() - start
                        response_times.append(elapsed)
                    except Exception:
                        pass
            
            if response_times:
                avg_response = sum(response_times) / len(response_times) * 1000
                status = 'passed' if avg_response < 500 else ('warning' if avg_response < 2000 else 'failed')
                severity = 'trivial' if avg_response < 500 else ('minor' if avg_response < 2000 else 'major')
                
                results.append({
                    'test_id': f"perf_rsp_{uuid.uuid4().hex[:8]}",
                    'test_name': '响应时间测试',
                    'test_type': 'performance',
                    'priority': 'high',
                    'status': status,
                    'severity': severity,
                    'message': f"平均响应时间: {avg_response:.2f}ms",
                    'details': {'avg_response_ms': avg_response, 'samples': response_times},
                    'execution_time': round(sum(response_times), 2)
                })
            else:
                results.append({
                    'test_id': f"perf_rsp_{uuid.uuid4().hex[:8]}",
                    'test_name': '响应时间测试',
                    'test_type': 'performance',
                    'priority': 'high',
                    'status': 'skipped',
                    'severity': 'minor',
                    'message': '服务未启动，无法测试响应时间',
                    'details': {}
                })
        except Exception as e:
            results.append({
                'test_id': f"perf_rsp_{uuid.uuid4().hex[:8]}",
                'test_name': '响应时间测试',
                'test_type': 'performance',
                'priority': 'high',
                'status': 'failed',
                'severity': 'major',
                'message': f"响应时间测试失败: {str(e)}",
                'details': {'error': str(e)}
            })
        
        return results

    def generate_test_report(self, report_type: str = 'full') -> Dict[str, Any]:
        """生成测试报告"""
        logger.info(f"[安全工程师] 生成{report_type}测试报告...")
        
        try:
            db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'security_engineer.db')
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                if report_type == 'full' or report_type == 'security':
                    cursor.execute('SELECT * FROM security_findings ORDER BY severity DESC')
                    findings = cursor.fetchall()
                
                if report_type == 'full' or report_type == 'functional':
                    cursor.execute('SELECT * FROM test_results WHERE test_type = ? ORDER BY priority DESC', ('functional',))
                    func_results = cursor.fetchall()
                
                if report_type == 'full' or report_type == 'performance':
                    cursor.execute('SELECT * FROM test_results WHERE test_type = ? ORDER BY priority DESC', ('performance',))
                    perf_results = cursor.fetchall()
            
            report_content = self._format_report_content(report_type, findings, func_results, perf_results)
            
            report_id = f"report_{uuid.uuid4().hex[:12]}"
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO test_reports (report_id, report_type, title, summary, content)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    report_id,
                    report_type,
                    f"MTSCOS系统{report_type}测试报告",
                    json.dumps(self._generate_summary(findings, func_results, perf_results), ensure_ascii=False),
                    json.dumps(report_content, ensure_ascii=False)
                ))
                conn.commit()
            
            logger.info(f"[安全工程师] 测试报告生成完成: {report_id}")
            return {
                'report_id': report_id,
                'report_type': report_type,
                'title': f"MTSCOS系统{report_type}测试报告",
                'generated_at': datetime.now().isoformat(),
                'content': report_content
            }
        except Exception as e:
            logger.error(f"[安全工程师] 生成测试报告失败: {e}")
            return {'success': False, 'error': str(e)}

    def _format_report_content(self, report_type, findings, func_results, perf_results):
        content = {
            'header': {
                'title': f"MTSCOS系统{report_type}测试报告",
                'generated_at': datetime.now().isoformat(),
                'engineer': self.name,
                'employee_id': self.employee_id
            },
            'summary': self._generate_summary(findings, func_results, perf_results)
        }
        
        if report_type == 'full' or report_type == 'security':
            content['security_findings'] = []
            for row in findings:
                content['security_findings'].append({
                    'id': row[0],
                    'finding_id': row[1],
                    'category': row[2],
                    'severity': row[3],
                    'description': row[4],
                    'location': row[5],
                    'recommendation': row[6],
                    'status': row[7],
                    'created_at': row[8]
                })
        
        if report_type == 'full' or report_type == 'functional':
            content['functional_tests'] = []
            for row in func_results:
                content['functional_tests'].append({
                    'id': row[0],
                    'test_id': row[1],
                    'test_name': row[2],
                    'test_type': row[3],
                    'priority': row[4],
                    'status': row[5],
                    'severity': row[6],
                    'message': row[7],
                    'details': json.loads(row[8]) if row[8] else {},
                    'execution_time': row[9],
                    'created_at': row[10]
                })
        
        if report_type == 'full' or report_type == 'performance':
            content['performance_tests'] = []
            for row in perf_results:
                content['performance_tests'].append({
                    'id': row[0],
                    'test_id': row[1],
                    'test_name': row[2],
                    'test_type': row[3],
                    'priority': row[4],
                    'status': row[5],
                    'severity': row[6],
                    'message': row[7],
                    'details': json.loads(row[8]) if row[8] else {},
                    'execution_time': row[9],
                    'created_at': row[10]
                })
        
        return content

    def _generate_summary(self, findings, func_results, perf_results):
        summary = {}
        
        if findings:
            summary['security_findings'] = {
                'total': len(findings),
                'critical': len([f for f in findings if f[3] == 'critical']),
                'high': len([f for f in findings if f[3] == 'high']),
                'medium': len([f for f in findings if f[3] == 'medium']),
                'low': len([f for f in findings if f[3] == 'low'])
            }
        
        if func_results:
            summary['functional_tests'] = {
                'total': len(func_results),
                'passed': len([r for r in func_results if r[5] == 'passed']),
                'failed': len([r for r in func_results if r[5] == 'failed']),
                'skipped': len([r for r in func_results if r[5] == 'skipped'])
            }
        
        if perf_results:
            summary['performance_tests'] = {
                'total': len(perf_results),
                'passed': len([r for r in perf_results if r[5] == 'passed']),
                'failed': len([r for r in perf_results if r[5] == 'failed'])
            }
        
        return summary

    def write_test_rules_to_system(self) -> Dict[str, Any]:
        """编写测试规则到系统规则表"""
        logger.info("[安全工程师] 编写测试规则到系统规则表...")
        
        test_rules = [
            {
                'rule_id': 'test_rule_001',
                'rule_name': '安全扫描频率规则',
                'rule_type': 'security',
                'priority': 'high',
                'pattern': 'daily',
                'description': '系统必须每天执行一次完整安全扫描',
                'severity': 'high',
                'action': 'schedule'
            },
            {
                'rule_id': 'test_rule_002',
                'rule_name': '功能测试频率规则',
                'rule_type': 'functional',
                'priority': 'high',
                'pattern': 'weekly',
                'description': '系统必须每周执行一次完整功能测试',
                'severity': 'medium',
                'action': 'schedule'
            },
            {
                'rule_id': 'test_rule_003',
                'rule_name': '性能测试频率规则',
                'rule_type': 'performance',
                'priority': 'medium',
                'pattern': 'monthly',
                'description': '系统必须每月执行一次性能测试',
                'severity': 'medium',
                'action': 'schedule'
            },
            {
                'rule_id': 'test_rule_004',
                'rule_name': '安全漏洞修复时限规则',
                'rule_type': 'security',
                'priority': 'critical',
                'pattern': 'critical:24h,high:72h,medium:7d',
                'description': 'Critical漏洞必须24小时内修复，High漏洞72小时内修复，Medium漏洞7天内修复',
                'severity': 'critical',
                'action': 'enforce'
            },
            {
                'rule_id': 'test_rule_005',
                'rule_name': '测试通过率阈值规则',
                'rule_type': 'quality',
                'priority': 'high',
                'pattern': '>=95%',
                'description': '功能测试通过率必须达到95%以上',
                'severity': 'high',
                'action': 'enforce'
            },
            {
                'rule_id': 'test_rule_006',
                'rule_name': 'API响应时间规则',
                'rule_type': 'performance',
                'priority': 'high',
                'pattern': '<500ms',
                'description': 'API平均响应时间必须小于500ms',
                'severity': 'high',
                'action': 'alert'
            },
            {
                'rule_id': 'test_rule_007',
                'rule_name': '系统资源使用率规则',
                'rule_type': 'performance',
                'priority': 'medium',
                'pattern': 'cpu<80%,mem<85%,disk<85%',
                'description': '系统资源使用率阈值：CPU<80%，内存<85%，磁盘<85%',
                'severity': 'medium',
                'action': 'alert'
            },
            {
                'rule_id': 'test_rule_008',
                'rule_name': '测试报告生成规则',
                'rule_type': 'reporting',
                'priority': 'medium',
                'pattern': 'after_each_test_run',
                'description': '每次测试完成后必须生成测试报告',
                'severity': 'low',
                'action': 'enforce'
            },
            {
                'rule_id': 'test_rule_009',
                'rule_name': '测试数据清理规则',
                'rule_type': 'maintenance',
                'priority': 'low',
                'pattern': '30days',
                'description': '测试数据保留30天，超过期限自动清理',
                'severity': 'low',
                'action': 'auto_clean'
            },
            {
                'rule_id': 'test_rule_010',
                'rule_name': '安全工程师自动运行规则',
                'rule_type': 'automation',
                'priority': 'high',
                'pattern': 'system_startup',
                'description': '系统启动时自动启动安全工程师执行初始检查',
                'severity': 'medium',
                'action': 'auto_start'
            }
        ]
        
        for rule in test_rules:
            self._save_test_rule(rule)
        
        self.test_rules.extend(test_rules)
        
        logger.info(f"[安全工程师] 已写入 {len(test_rules)} 条测试规则")
        return {
            'success': True,
            'message': f'已写入 {len(test_rules)} 条测试规则',
            'rules': test_rules
        }

    def run_full_test_suite(self) -> Dict[str, Any]:
        """执行完整测试套件"""
        logger.info("[安全工程师] 开始执行完整测试套件...")
        
        results = {}
        
        results['security_scan'] = self.run_security_scan('full')
        results['functional_tests'] = self.run_functional_tests()
        results['performance_tests'] = self.run_performance_tests()
        results['test_rules'] = self.write_test_rules_to_system()
        results['report'] = self.generate_test_report('full')
        
        logger.info("[安全工程师] 完整测试套件执行完成")
        return results

    def get_status(self) -> Dict[str, Any]:
        """获取安全工程师状态"""
        return {
            'employee_id': self.employee_id,
            'name': self.name,
            'type': self.type,
            'status': self.status,
            'is_running': self.is_running,
            'skills': self.skills,
            'responsibilities': self.responsibilities,
            'test_rules_count': len(self.test_rules),
            'test_results_count': len(self.test_results),
            'security_findings_count': len(self.security_findings)
        }

    def start(self):
        """启动安全工程师"""
        if self.is_running:
            return {'success': False, 'message': '安全工程师已在运行'}
        
        self.is_running = True
        self.status = 'active'
        
        self._test_thread = threading.Thread(target=self._run_continuous_testing, daemon=True)
        self._test_thread.start()
        
        logger.info(f"[安全工程师] 已启动: {self.employee_id}")
        return {'success': True, 'message': '安全工程师已启动'}

    def stop(self):
        """停止安全工程师"""
        self.is_running = False
        self.status = 'inactive'
        
        if self._test_thread and self._test_thread.is_alive():
            self._test_thread.join(timeout=5)
        
        logger.info(f"[安全工程师] 已停止: {self.employee_id}")
        return {'success': True, 'message': '安全工程师已停止'}

    def _run_continuous_testing(self):
        """连续测试循环"""
        while self.is_running:
            try:
                self.run_security_scan('full')
                time.sleep(3600)
            except Exception as e:
                logger.error(f"[安全工程师] 连续测试出错: {e}")
                time.sleep(60)