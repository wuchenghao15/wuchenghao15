#!/usr/bin/env python3
"""
代码安全扫描器
================
扫描项目Python代码中的安全漏洞，输出结构化的漏洞报告。
支持检测：SQL注入、XSS、硬编码密码、危险函数、路径遍历、命令注入等。
"""
import os
import re
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 扫描时跳过的目录
SKIP_DIRS = {
    'data/snapshots', 'flask-app-old', 'flask-app/data/snapshots',
    'node_modules', '.git', '__pycache__', '.trae', '.sync_temp_dir',
    '.tmp', 'backups', 'recovery_images', 'iso_images', 'certs', 'keys',
    '.venv', '.project_history'
}

# 漏洞检测规则
SECURITY_RULES = [
    {
        'rule_id': 'RULE-SQL-001',
        'vuln_id': 'VULN-001',
        'name': 'SQL字符串拼接注入',
        'severity': 'critical',
        'pattern': r'execute\s*\(\s*f["\'].*\{.*\}.*["\']',
        'description': '使用f-string构建SQL查询，存在SQL注入风险',
        'fix_suggestion': '使用参数化查询 cursor.execute("SELECT ... WHERE id = ?", (id,))',
        'category': 'injection'
    },
    {
        'rule_id': 'RULE-SQL-002',
        'vuln_id': 'VULN-001',
        'name': 'SQL字符串格式化',
        'severity': 'critical',
        'pattern': r'execute\s*\(\s*["\'].*%s.*["\']\s*%\s*',
        'description': '使用%格式化构建SQL，存在SQL注入风险',
        'fix_suggestion': '使用参数化查询替代字符串格式化',
        'category': 'injection'
    },
    {
        'rule_id': 'RULE-SQL-003',
        'vuln_id': 'VULN-001',
        'name': 'SQL字符串拼接(加号)',
        'severity': 'high',
        'pattern': r'execute\s*\(\s*["\'].*["\']\s*\+',
        'description': '使用加号拼接SQL语句，存在SQL注入风险',
        'fix_suggestion': '使用参数化查询，避免字符串拼接',
        'category': 'injection'
    },
    {
        'rule_id': 'RULE-EVAL-001',
        'vuln_id': 'VULN-007',
        'name': 'eval危险函数',
        'severity': 'critical',
        'pattern': r'\beval\s*\(',
        'description': '使用eval函数执行任意代码，存在代码注入风险',
        'fix_suggestion': '使用ast.literal_eval或json.loads替代eval',
        'category': 'code_injection'
    },
    {
        'rule_id': 'RULE-EXEC-001',
        'vuln_id': 'VULN-007',
        'name': 'exec危险函数',
        'severity': 'critical',
        'pattern': r'\bexec\s*\(',
        'description': '使用exec函数执行任意代码',
        'fix_suggestion': '避免使用exec，使用安全的替代方案',
        'category': 'code_injection'
    },
    {
        'rule_id': 'RULE-CMD-001',
        'vuln_id': 'VULN-008',
        'name': 'os.system命令注入',
        'severity': 'high',
        'pattern': r'os\.system\s*\(',
        'description': '使用os.system执行命令，存在命令注入风险',
        'fix_suggestion': '使用subprocess.run with shell=False和参数列表',
        'category': 'command_injection'
    },
    {
        'rule_id': 'RULE-CMD-002',
        'vuln_id': 'VULN-008',
        'name': 'subprocess shell=True',
        'severity': 'high',
        'pattern': r'subprocess\..*shell\s*=\s*True',
        'description': '使用shell=True存在命令注入风险',
        'fix_suggestion': '使用shell=False并传入参数列表',
        'category': 'command_injection'
    },
    {
        'rule_id': 'RULE-SECRET-001',
        'vuln_id': 'VULN-004',
        'name': '硬编码密钥',
        'severity': 'high',
        'pattern': r'(?:SECRET_KEY|API_KEY|SECRET|TOKEN)\s*=\s*["\'][^"\']{8,}["\']',
        'description': '代码中硬编码了密钥或令牌',
        'fix_suggestion': '使用环境变量或配置文件管理密钥',
        'category': 'information_disclosure'
    },
    {
        'rule_id': 'RULE-SECRET-002',
        'vuln_id': 'VULN-004',
        'name': '硬编码密码',
        'severity': 'high',
        'pattern': r'(?:password|passwd|pwd)\s*=\s*["\'][^"\']{4,}["\']',
        'description': '代码中硬编码了密码',
        'fix_suggestion': '使用环境变量或密钥管理系统',
        'category': 'information_disclosure'
    },
    {
        'rule_id': 'RULE-PATH-001',
        'vuln_id': 'VULN-009',
        'name': '路径遍历风险',
        'severity': 'medium',
        'pattern': r'open\s*\(\s*.*\+.*\)',
        'description': '使用字符串拼接构建文件路径，存在路径遍历风险',
        'fix_suggestion': '使用os.path.join并验证路径在允许目录内',
        'category': 'path_traversal'
    },
    {
        'rule_id': 'RULE-XSS-001',
        'vuln_id': 'VULN-002',
        'name': 'XSSMarkupSafe绕过',
        'severity': 'high',
        'pattern': r'\|safe(?!\s*_)',
        'description': '使用|safe过滤器输出未转义内容，存在XSS风险',
        'fix_suggestion': '避免使用|safe，确保输出经过HTML编码',
        'category': 'xss'
    },
    {
        'rule_id': 'RULE-PICKLE-001',
        'vuln_id': 'VULN-007',
        'name': 'pickle反序列化',
        'severity': 'critical',
        'pattern': r'pickle\.loads?\s*\(',
        'description': '使用pickle反序列化存在代码执行风险',
        'fix_suggestion': '使用json替代pickle处理不可信数据',
        'category': 'code_injection'
    },
    {
        'rule_id': 'RULE-DEBUG-001',
        'vuln_id': 'VULN-004',
        'name': '生产环境debug模式',
        'severity': 'medium',
        'pattern': r'app\.run\s*\([^)]*debug\s*=\s*True',
        'description': '在生产环境中启用debug模式可能泄露敏感信息',
        'fix_suggestion': '通过环境变量控制debug模式',
        'category': 'information_disclosure'
    },
]


class CodeSecurityScanner:
    def __init__(self, project_root: str = PROJECT_ROOT):
        self.project_root = project_root
        self.findings: List[Dict[str, Any]] = []

    def _should_skip(self, file_path: str) -> bool:
        """检查文件是否应该跳过"""
        rel_path = os.path.relpath(file_path, self.project_root)
        for skip_dir in SKIP_DIRS:
            if rel_path.startswith(skip_dir):
                return True
        return False

    def scan_file(self, file_path: str) -> List[Dict[str, Any]]:
        """扫描单个文件"""
        if self._should_skip(file_path):
            return []

        findings = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            for line_no, line in enumerate(lines, 1):
                for rule in SECURITY_RULES:
                    # 跳过注释行
                    stripped = line.strip()
                    if stripped.startswith('#'):
                        continue

                    if re.search(rule['pattern'], line, re.IGNORECASE):
                        # 过滤掉明显的测试/修复示例代码
                        if 'fix_code' in line or 'fix_suggestion' in line:
                            continue
                        if 'pattern' in line and 'rule' in line.lower():
                            continue
                        if "'pattern':" in line or '"pattern":' in line:
                            continue

                        findings.append({
                            'finding_id': f"FIND-{uuid.uuid4().hex[:8].upper()}",
                            'rule_id': rule['rule_id'],
                            'vuln_id': rule['vuln_id'],
                            'file_path': os.path.relpath(file_path, self.project_root),
                            'line_number': line_no,
                            'vulnerability_name': rule['name'],
                            'severity': rule['severity'],
                            'category': rule['category'],
                            'description': rule['description'],
                            'code_snippet': line.strip()[:200],
                            'fix_suggestion': rule['fix_suggestion'],
                            'found_at': datetime.now().isoformat()
                        })
        except Exception as e:
            pass

        return findings

    def scan_project(self) -> Dict[str, Any]:
        """扫描整个项目"""
        self.findings = []
        files_scanned = 0

        for root, dirs, files in os.walk(self.project_root):
            # 过滤跳过目录
            dirs[:] = [d for d in dirs if not self._should_skip(os.path.join(root, d))]

            for filename in files:
                if filename.endswith('.py') or filename.endswith('.html'):
                    file_path = os.path.join(root, filename)
                    findings = self.scan_file(file_path)
                    self.findings.extend(findings)
                    files_scanned += 1

        # 统计
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        category_counts = {}
        for f in self.findings:
            sev = f['severity']
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
            cat = f['category']
            category_counts[cat] = category_counts.get(cat, 0) + 1

        return {
            'scan_id': f"CODESCAN-{uuid.uuid4().hex[:8].upper()}",
            'scan_time': datetime.now().isoformat(),
            'files_scanned': files_scanned,
            'total_findings': len(self.findings),
            'severity_breakdown': severity_counts,
            'category_breakdown': category_counts,
            'findings': self.findings
        }

    def save_findings_to_db(self, scan_result: Dict[str, Any]) -> Dict[str, Any]:
        """将扫描结果保存到数据库"""
        import sqlite3
        from security_vulnerability_service import DATABASE_PATH

        conn = sqlite3.connect(DATABASE_PATH, timeout=10)
        cursor = conn.cursor()

        scan_id = scan_result['scan_id']

        # 创建代码扫描结果表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS code_scan_findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                finding_id TEXT UNIQUE NOT NULL,
                scan_id TEXT NOT NULL,
                rule_id TEXT,
                vuln_id TEXT,
                file_path TEXT,
                line_number INTEGER,
                vulnerability_name TEXT,
                severity TEXT,
                category TEXT,
                description TEXT,
                code_snippet TEXT,
                fix_suggestion TEXT,
                status TEXT DEFAULT 'open',
                found_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 保存扫描摘要
        cursor.execute("""
            INSERT OR REPLACE INTO security_scans
            (scan_id, scan_name, scan_type, target, status, total_tests,
             tests_passed, tests_failed, vulnerabilities_found,
             started_at, completed_at, scan_duration_seconds,
             initiated_by, results_summary, created_at)
            VALUES (?, ?, ?, ?, 'completed', ?, 0, ?, ?, ?, ?, 0, ?, ?, CURRENT_TIMESTAMP)
        """, (
            scan_id, '代码安全扫描', 'code_scan', self.project_root,
            scan_result['files_scanned'], scan_result['total_findings'],
            scan_result['total_findings'], scan_result['scan_time'],
            scan_result['scan_time'], 'code_scanner',
            json.dumps({
                'severity_breakdown': scan_result['severity_breakdown'],
                'category_breakdown': scan_result['category_breakdown']
            })
        ))

        # 保存每个发现
        for finding in scan_result['findings']:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO code_scan_findings
                    (finding_id, scan_id, rule_id, vuln_id, file_path, line_number,
                     vulnerability_name, severity, category, description,
                     code_snippet, fix_suggestion, status, found_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?)
                """, (
                    finding['finding_id'], scan_id, finding['rule_id'],
                    finding['vuln_id'], finding['file_path'], finding['line_number'],
                    finding['vulnerability_name'], finding['severity'],
                    finding['category'], finding['description'],
                    finding['code_snippet'], finding['fix_suggestion'],
                    finding['found_at']
                ))
            except Exception:
                pass

        conn.commit()
        conn.close()

        return {
            'success': True,
            'scan_id': scan_id,
            'saved_findings': len(scan_result['findings'])
        }


scanner = CodeSecurityScanner()
