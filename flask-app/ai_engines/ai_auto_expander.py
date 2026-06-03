# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
AI驱动的自动功能拓展系统
功能:
5. 学习和优化改进过程
"""

import os
import sys
import json
import logging
import time
import random
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_auto_expander.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AI_Auto_Expander')

class AIAutoExpander:
    def __init__(self, project_root=None):
        self.project_root = project_root or os.getcwd()
        self.knowledge_base_path = os.path.join(self.project_root, 'knowledge_base.json')
        self.improvement_history = os.path.join(self.project_root, 'ai_improvement_history.json')

        if not os.path.exists(self.improvement_history):
            with open(self.improvement_history, 'w', encoding='utf-8') as f:
                json.dump({'improvements': []}, f, ensure_ascii=False, indent=2)

        self.improvement_categories = {
            'security': self.improve_security,
            'performance': self.improve_performance,
            'usability': self.improve_usability,
            'scalability': self.improve_scalability,
            'maintainability': self.improve_maintainability
        }

        logger.info("AI自动功能拓展系统初始化完成")

    def load_improvement_history(self) -> Dict:
        try:
            with open(self.improvement_history, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载改进历史失败: {e}")
            return {'improvements': []}

    def save_improvement(self, improvement: Dict):
        history = self.load_improvement_history()
        history['improvements'].append(improvement)

        try:
            with open(self.improvement_history, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            logger.info(f"保存改进记录成功: {improvement['improvement_id']}")
        except Exception as e:
            logger.error(f"保存改进记录失败: {e}")

    def identify_improvements(self) -> List[Dict]:
        logger.info("开始识别可改进功能")
        improvements = []

        todo_comments = self._find_todo_comments()
        if todo_comments:
            improvements.append({
                'type': 'code_quality',
                'priority': 'medium',
                'description': f"修复代码中的TODO/FIXME注释 ({len(todo_comments)} 处)",
                'details': todo_comments
            })

        duplicate_code = self._find_duplicate_code()
        if duplicate_code:
            improvements.append({
                'type': 'maintainability',
                'priority': 'high',
                'description': f"发现重复代码 ({len(duplicate_code)} 处)",
                'details': duplicate_code
            })

        security_issues = self._find_security_issues()
        if security_issues:
            improvements.append({
                'type': 'security',
                'priority': 'critical',
                'description': f"发现安全漏洞 ({len(security_issues)} 处)",
                'details': security_issues
            })

        performance_issues = self._find_performance_issues()
        if performance_issues:
            improvements.append({
                'type': 'performance',
                'priority': 'medium',
                'description': f"发现性能问题 ({len(performance_issues)} 处)",
                'details': performance_issues
            })

        logger.info(f"识别到 {len(improvements)} 项可改进功能")
        return improvements

    def _find_todo_comments(self) -> List[Dict]:
        todo_files = []
        try:
            result = subprocess.run(
                ['grep', '-r', '-n', '-E', '--include=*.py', 'TODO|FIXME', self.project_root],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line:
                        parts = line.split(':', 2)
                        if len(parts) == 3:
                            todo_files.append({
                                'file': parts[0],
                                'line': int(parts[1]),
                                'comment': parts[2].strip()
                            })
        except Exception as e:
            logger.error(f"查找TODO注释失败: {e}")

        return todo_files

    def _find_duplicate_code(self) -> List[Dict]:
        duplicate_candidates = []
        try:
            result = subprocess.run(
                ['grep', '-r', '-n', '--include=*.py', 'def ', self.project_root],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            if result.returncode == 0:
                function_count = {}
                for line in result.stdout.split('\n'):
                    if line and 'def ' in line:
                        func_name = line.split('def ')[1].split('(')[0]
                        function_count[func_name] = function_count.get(func_name, 0) + 1

                for func_name, count in function_count.items():
                    if count > 1:
                        duplicate_candidates.append({
                            'function': func_name,
                            'count': count
                        })
        except Exception as e:
            logger.error(f"查找重复代码失败: {e}")

        return duplicate_candidates

    def _find_security_issues(self) -> List[Dict]:
        security_issues = []
        try:
            result = subprocess.run(
                ['grep', '-r', '-n', '-i', '--include=*.py', '--include=*.env', '-E', 'password|secret|key|token', self.project_root],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line and any(kw in line.lower() for kw in ['password', 'secret', 'key', 'token']):
                        if not any(ignore in line.lower() for ignore in ['__secret_key__', 'generate', 'random', 'token_', 'secrets.']):
                            parts = line.split(':', 2)
                            if len(parts) == 3:
                                security_issues.append({
                                    'file': parts[0],
                                    'line': int(parts[1]),
                                    'issue': 'potential_hardcoded_secret',
                                    'description': parts[2].strip()
                                })
        except Exception as e:
            logger.error(f"查找安全漏洞失败: {e}")

        return security_issues

    def _find_performance_issues(self) -> List[Dict]:
        performance_issues = []
        try:
            result = subprocess.run(
                ['grep', '-r', '-n', '--include=*.py', '-E', 'for.*in.*\\..*all\\(\\)|N\\+1|slow_query', self.project_root],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line:
                        parts = line.split(':', 2)
                        if len(parts) == 3:
                            performance_issues.append({
                                'file': parts[0],
                                'line': int(parts[1]),
                                'issue': 'potential_performance_bottleneck',
                                'description': parts[2].strip()
                            })
        except Exception as e:
            logger.error(f"查找性能问题失败: {e}")

        return performance_issues

    def improve_security(self) -> bool:
        logger.info("开始改进系统安全性")
        success = True

        password_files = self._find_password_handling_files()
        for file_path in password_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                if 'bcrypt' not in content and 'scrypt' not in content and 'argon2' not in content:
                    if 'from werkzeug.security import generate_password_hash, check_password_hash' in content:
                        continue
                    if 'import hashlib' in content:
                        content = content.replace(
                            'import hashlib',
                            'import hashlib\nfrom werkzeug.security import generate_password_hash, check_password_hash'
                        )
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
            except Exception as e:
                logger.error(f"改进 {file_path} 安全性失败: {e}")
                success = False

        return success

    def improve_performance(self) -> bool:
        logger.info("开始改进系统性能")
        success = True

        api_files = self._find_api_files()
        for file_path in api_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                if 'cache' not in content.lower():
                    logger.info(f"为 {file_path} 添加缓存机制")
                    if '@app.route' in content and 'from functools import lru_cache' not in content:
                        content = content.replace(
                            'from flask import',
                            'from flask import\nfrom functools import lru_cache'
                        )
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
            except Exception as e:
                logger.error(f"改进 {file_path} 性能失败: {e}")
                success = False

        return success

    def improve_usability(self) -> bool:
        logger.info("开始改进用户体验")
        success = True

        form_files = self._find_form_files()
        for file_path in form_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                if 'validate' in content.lower() and 'wtforms' not in content.lower():
                    logger.info(f"增强 {file_path} 中的表单验证")
                    if 'from flask import' in content:
                        content = content.replace(
                            'from flask import',
                            'from flask import\nfrom flask_wtf import FlaskForm, CSRFProtect'
                        )
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
            except Exception as e:
                logger.error(f"改进 {file_path} 用户体验失败: {e}")
                success = False

        return success

    def improve_scalability(self) -> bool:
        logger.info("开始改进系统可扩展性")
        success = True

        async_files = self._find_async_candidates()
        for file_path in async_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                if 'async def' not in content and 'await' not in content:
                    logger.info(f"为 {file_path} 添加异步处理支持")
                    if '@app.route' in content and 'from flask import Flask' in content:
                        content = content.replace(
                            'from flask import Flask',
                            'from flask import Flask\nimport asyncio'
                        )
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
            except Exception as e:
                logger.error(f"改进 {file_path} 可扩展性失败: {e}")
                success = False

        return success

    def improve_maintainability(self) -> bool:
        logger.info("开始改进系统可维护性")
        success = True

        long_functions = self._find_long_functions()
        for func in long_functions:
            try:
                file_path, line_num, func_name, line_count = func
                logger.warning(f"发现长函数: {func_name} 在 {file_path}:{line_num} ({line_count} 行)")
            except Exception as e:
                logger.error(f"重构长函数失败: {e}")
                success = False

        return success

    def _find_password_handling_files(self) -> List[str]:
        try:
            result = subprocess.run(
                ['grep', '-r', '-l', '--include=*.py', '-E', 'password|login|register', self.project_root],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            if result.returncode == 0:
                return result.stdout.strip().split('\n')
        except Exception as e:
            logger.error(f"查找密码处理文件失败: {e}")
        return []

    def _find_api_files(self) -> List[str]:
        try:
            result = subprocess.run(
                ['grep', '-r', '-l', '--include=*.py', '-E', '@app.route|@api.route', self.project_root],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            if result.returncode == 0:
                return result.stdout.strip().split('\n')
        except Exception as e:
            logger.error(f"查找API文件失败: {e}")
        return []

    def _find_form_files(self) -> List[str]:
        try:
            result = subprocess.run(
                ['grep', '-r', '-l', '--include=*.py', '-E', 'Form|WTForm|wtforms', self.project_root],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            if result.returncode == 0:
                return result.stdout.strip().split('\n')
        except Exception as e:
            logger.error(f"查找表单文件失败: {e}")
        return []

    def _find_async_candidates(self) -> List[str]:
        try:
            result = subprocess.run(
                ['grep', '-r', '-l', '--include=*.py', '-E', 'requests\\.get|time\\.sleep|subprocess\\.run', self.project_root],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            if result.returncode == 0:
                return result.stdout.strip().split('\n')
        except Exception as e:
            logger.error(f"查找异步处理候选文件失败: {e}")
        return []

    def _find_long_functions(self) -> List[tuple]:
        long_functions = []
        try:
            result = subprocess.run(
                ['grep', '-r', '-n', '--include=*.py', 'def ', self.project_root],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line:
                        parts = line.split(':', 2)
                        if len(parts) == 3:
                            file_path = parts[0]
                            line_num = int(parts[1])
                            func_name = parts[2].strip().split('def ')[1].split('(')[0]
                            line_count = self._count_function_lines(file_path, line_num)
                            if line_count > 50:
                                long_functions.append((file_path, line_num, func_name, line_count))
        except Exception as e:
            logger.error(f"查找长函数失败: {e}")
        return long_functions

    def _count_function_lines(self, file_path: str, start_line: int) -> int:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            if start_line > len(lines):
                return 0

            line_count = 0
            indent_level = None

            for i in range(start_line - 1, len(lines)):
                line = lines[i]
                stripped = line.strip()

                if indent_level is None and stripped:
                    line_count += 1
                    indent_level = len(line) - len(stripped)
                    continue

                if not stripped or stripped.startswith('#'):
                    continue

                current_indent = len(line) - len(stripped)

                if current_indent <= indent_level and stripped:
                    break

                line_count += 1
        except Exception as e:
            logger.error(f"计算函数行数失败: {e}")
            return 0

        return line_count

    def run_auto_expansion(self):
        logger.info("开始执行自动功能拓展")
        improvements = self.identify_improvements()

        improvement_plan = self._generate_improvement_plan(improvements)

        for improvement in improvement_plan:
            improvement_id = f"impr_{int(time.time())}_{random.randint(1000, 9999)}"
            improvement['improvement_id'] = improvement_id
            improvement['start_time'] = time.time()
            logger.info(f"开始实施改进: {improvement['description']} (ID: {improvement_id})")

            try:
                success = False
                if improvement['type'] in self.improvement_categories:
                    success = self.improvement_categories[improvement['type']]()

                improvement['end_time'] = time.time()
                improvement['success'] = success
                improvement['duration'] = improvement['end_time'] - improvement['start_time']

                self.save_improvement(improvement)
            except Exception as e:
                logger.error(f"实施改进时发生错误: {e}")
                improvement['end_time'] = time.time()
                improvement['success'] = False
                improvement['error'] = str(e)
                improvement['duration'] = improvement['end_time'] - improvement['start_time']
                self.save_improvement(improvement)

        logger.info("自动功能拓展执行完成")

    def _generate_improvement_plan(self, improvements: List[Dict]) -> List[Dict]:
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        improvements.sort(key=lambda x: priority_order.get(x['priority'], 3))
        return improvements[:5]

if __name__ == "__main__":
    expander = AIAutoExpander()
    expander.run_auto_expansion()
