# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全扫描器模块
负责扫描项目安全漏洞和检测潜在安全问题
"""

import os
import re
import logging
import subprocess
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger('security_scanner')


class SecurityScanner:
    """安全扫描器类"""

    def __init__(self):
        """初始化安全扫描器"""
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.python_extensions = ['.py']
        self.ignored_dirs = ['__pycache__', 'venv', 'env', '.git', 'static', 'templates']
        logger.info("安全扫描器初始化完成")

    def scan_project(self) -> List[Dict[str, Any]]:
        """扫描整个项目的安全问题"""
        issues = []
        try:
            for root, dirs, files in os.walk(self.project_root):
                dirs[:] = [d for d in dirs if d not in self.ignored_dirs]

                for file in files:
                    if any(file.endswith(ext) for ext in self.python_extensions):
                        file_path = os.path.join(root, file)
                        file_issues = self.scan_file(file_path)
                        issues.extend(file_issues)

            logger.info(f"安全扫描完成, 发现 {len(issues)} 个问题")
        except Exception as e:
            logger.error(f"扫描项目时出错: {str(e)}")

        return issues

    def scan_file(self, file_path: str) -> List[Dict[str, Any]]:
        """扫描单个文件的安全问题"""
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                issues.extend(self._check_sql_injection(content, file_path))
                issues.extend(self._check_hardcoded_secrets(content, file_path))
        except Exception as e:
            logger.error(f"扫描文件时出错 {file_path}: {str(e)}")
        return issues

    def _check_sql_injection(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """检查SQL注入风险"""
        issues = []
        patterns = [
            r'execute\s*\(\s*f["\'].*\{.*\}.*["\']',
            r'cursor\.execute\s*\(\s*["\'].*%s.*["\'].*%'
        ]
        for pattern in patterns:
            if re.search(pattern, content):
                issues.append({
                    'file': file_path,
                    'type': 'sql_injection',
                    'severity': 'high',
                    'description': '潜在的SQL注入风险'
                })
        return issues

    def _check_hardcoded_secrets(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """检查硬编码的密钥"""
        issues = []
        patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'secret_key\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']'
        ]
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append({
                    'file': file_path,
                    'type': 'hardcoded_secret',
                    'severity': 'medium',
                    'description': '发现硬编码的敏感信息'
                })
        return issues
