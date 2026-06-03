# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码分析器模块
负责分析项目代码质量和检测潜在问题
"""

import os
import re
import ast
import logging
from typing import List, Dict, Any

logger = logging.getLogger('code_analyzer')


class CodeAnalyzer:
    """代码分析器类"""

    def __init__(self):
        """初始化代码分析器"""
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.python_extensions = ['.py']
        self.ignored_dirs = ['__pycache__', 'venv', 'env', '.git', 'static', 'templates']
        logger.info("代码分析器初始化完成")

    def analyze_project(self) -> List[Dict[str, Any]]:
        """分析整个项目的代码"""
        issues = []
        try:
            for root, dirs, files in os.walk(self.project_root):
                dirs[:] = [d for d in dirs if d not in self.ignored_dirs]

                for file in files:
                    if any(file.endswith(ext) for ext in self.python_extensions):
                        file_path = os.path.join(root, file)
                        file_issues = self.analyze_file(file_path)
                        issues.extend(file_issues)

            logger.info(f"代码分析完成, 发现 {len(issues)} 个问题")
        except Exception as e:
            logger.error(f"分析项目时出错: {str(e)}")

        return issues

    def analyze_file(self, file_path: str) -> List[Dict[str, Any]]:
        """分析单个文件"""
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                issues.extend(self._check_syntax(content, file_path))
                issues.extend(self._check_code_style(content, file_path))
        except Exception as e:
            logger.error(f"分析文件时出错 {file_path}: {str(e)}")
        return issues

    def _check_syntax(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """检查语法错误"""
        issues = []
        try:
            ast.parse(content)
        except SyntaxError as e:
            issues.append({
                'file': file_path,
                'line': e.lineno,
                'type': 'syntax_error',
                'severity': 'high',
                'description': str(e.msg)
            })
        return issues

    def _check_code_style(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """检查代码风格"""
        issues = []
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                issues.append({
                    'file': file_path,
                    'line': i,
                    'type': 'line_too_long',
                    'severity': 'low',
                    'description': f'行长度超过120字符 ({len(line)}字符)'
                })
        return issues
