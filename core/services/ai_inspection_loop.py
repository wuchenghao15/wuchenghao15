#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS AI 巡检闭环引擎
================================
自动巡检 → 自动修复 → 上报数据库/日志 → AI学习升级 → 形成完美闭环

七大闭环模块：
  1. 文件结构巡检     - 扫描项目目录，检测文件结构异常
  2. 语法错误巡检     - 检测 Python/JS/HTML/CSS/JSON 等语法错误
  3. 控制台错误巡检   - 捕获运行时错误、异常、告警
  4. 自动修复引擎     - 根据错误模式自动修复
  5. 数据库上报       - 所有巡检/修复结果写入数据库
  6. 日志记录         - 结构化日志输出
  7. AI自学习升级     - 从修复案例中学习，优化修复策略
"""

import os
import sys
import re
import ast
import json
import time
import sqlite3
import threading
import logging
import traceback
import hashlib
import tokenize
import io
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

# ============== 基础配置 ==============
_CORE_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_CORE_DIR))

try:
    from core.db_path import get_db_path
    _DB_PATH = get_db_path('app.db')
except Exception:
    _DB_PATH = os.path.join(_PROJECT_ROOT, 'data', 'app.db')

_LOG_PATH = os.path.join(_PROJECT_ROOT, 'logs', 'ai_inspection_loop.log')
os.makedirs(os.path.dirname(_LOG_PATH), exist_ok=True)

_logger = logging.getLogger('AIInspectionLoop')
_logger.setLevel(logging.INFO)
if not _logger.handlers:
    fh = logging.FileHandler(_LOG_PATH, encoding='utf-8')
    fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    _logger.addHandler(fh)
    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    _logger.addHandler(sh)


# ============== 工具函数 ==============
def _get_conn():
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_tables():
    """确保数据库表存在"""
    try:
        with _get_conn() as conn:
            c = conn.cursor()
            c.execute("""CREATE TABLE IF NOT EXISTS ai_inspection_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT UNIQUE,
                run_type TEXT,
                started_at TEXT,
                completed_at TEXT,
                files_scanned INTEGER DEFAULT 0,
                errors_found INTEGER DEFAULT 0,
                errors_fixed INTEGER DEFAULT 0,
                errors_failed INTEGER DEFAULT 0,
                knowledge_gained INTEGER DEFAULT 0,
                status TEXT DEFAULT 'running',
                duration_ms INTEGER DEFAULT 0
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS ai_inspection_issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                issue_type TEXT,
                severity TEXT,
                file_path TEXT,
                line_number INTEGER,
                error_message TEXT,
                error_code TEXT,
                fixed INTEGER DEFAULT 0,
                fix_method TEXT,
                fix_result TEXT,
                detected_at TEXT,
                fixed_at TEXT,
                confidence REAL DEFAULT 0.0
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS ai_inspection_knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_hash TEXT UNIQUE,
                error_type TEXT,
                error_pattern TEXT,
                fix_method TEXT,
                fix_template TEXT,
                success_count INTEGER DEFAULT 1,
                fail_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 1.0,
                first_seen TEXT,
                last_used TEXT,
                learned_from TEXT,
                confidence REAL DEFAULT 0.8
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS ai_inspection_console_errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_id TEXT UNIQUE,
                source TEXT,
                error_type TEXT,
                error_message TEXT,
                stack_trace TEXT,
                file_path TEXT,
                line_number INTEGER,
                column_number INTEGER,
                user_agent TEXT,
                url TEXT,
                reported_at TEXT,
                fixed INTEGER DEFAULT 0,
                fix_method TEXT,
                fixed_at TEXT
            )""")
            c.execute("""CREATE INDEX IF NOT EXISTS idx_inspection_issues_run ON ai_inspection_issues(run_id)""")
            c.execute("""CREATE INDEX IF NOT EXISTS idx_inspection_issues_type ON ai_inspection_issues(issue_type)""")
            c.execute("""CREATE INDEX IF NOT EXISTS idx_inspection_knowledge_hash ON ai_inspection_knowledge(pattern_hash)""")
            c.execute("""CREATE INDEX IF NOT EXISTS idx_console_errors_fixed ON ai_inspection_console_errors(fixed)""")
            conn.commit()
    except Exception as e:
        _logger.error(f"建表失败: {e}")


_ensure_tables()


# ============== Python 语法修复器 ==============
class PythonSyntaxFixer:
    """Python语法错误自动修复器 - 基于模式匹配的精准修复"""

    # 已知错误模式与修复方法
    ERROR_PATTERNS = [
        {
            'name': 'stmt_merged_after_call',
            'detect': lambda line: re.search(r'([\w\.]+\([^)]*\))\s*(return|if|for|while|with|try|except|raise|pass|break|continue|yield)', line),
            'fix': lambda line: re.sub(r'([\w\.]+\([^)]*\))\s*(return|if|for|while|with|try|except|raise|pass|break|continue|yield)', r'\1\n\2', line),
            'confidence': 0.85,
        },
        {
            'name': 'docstring_then_code',
            'detect': lambda line: re.search(r'""".*"""\s*(with|if|for|while|try|return|def|class|=)', line),
            'fix': lambda line: re.sub(r'(""".*?""")\s*(with|if|for|while|try|return|def|class|=)', r'\1\n\2', line),
            'confidence': 0.8,
        },
        {
            'name': 'colon_then_code',
            'detect': lambda line: re.search(r'(def|class|if|elif|else|for|while|try|except|finally|with)\s+[^:]*:\s*\S', line),
            'fix': lambda line: re.sub(r'((def|class|if|elif|else|for|while|try|except|finally|with)\s+[^:]*:)\s*(\S)', r'\1\n    \3', line),
            'confidence': 0.7,
        },
        {
            'name': 'enum_member_merged',
            'detect': lambda line: re.search(r'[A-Z_]+\s*=\s*["\'][^"\']*["\'][A-Z_]+\s*=', line),
            'fix': lambda line: re.sub(r'([A-Z_]+\s*=\s*["\'][^"\']*["\'])([A-Z_]+\s*=)', r'\1\n\2', line),
            'confidence': 0.75,
        },
        {
            'name': 'bracket_after_comment',
            'detect': lambda line: re.search(r'#.*?[}\]\)]\s*$', line) and not re.search(r'["\'].*#.*[}\]\)]', line),
            'fix': lambda line: '',
            'confidence': 0.5,
        },
    ]

    @classmethod
    def fix_file(cls, fpath: str, error_msg: str, error_line: int) -> Tuple[bool, str]:
        """尝试修复文件的语法错误，返回(是否成功, 修复方法)"""
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
        except Exception:
            return False, ''

        original_lines = list(lines)
        fix_method = ''

        # 策略1: 修复行末缺少换行导致的语句合并
        if error_line and 1 <= error_line <= len(lines):
            target_line = lines[error_line - 1]
            
            # 尝试各种修复模式
            for pattern in cls.ERROR_PATTERNS:
                try:
                    if pattern['detect'](target_line):
                        new_line = pattern['fix'](target_line)
                        if new_line and new_line != target_line:
                            lines[error_line - 1] = new_line
                            fix_method = pattern['name']
                            break
                except Exception:
                    continue

        # 策略2: 基于错误消息的精准修复
        if 'EOL while scanning string literal' in error_msg or 'unterminated string' in error_msg.lower():
            fixed, method = cls._fix_unterminated_string(lines, error_line)
            if fixed:
                fix_method = method or 'fix_unterminated_string'

        elif 'expected an indented block' in error_msg:
            fixed, method = cls._fix_indentation(lines, error_line)
            if fixed:
                fix_method = method or 'fix_indentation'

        elif 'invalid syntax' in error_msg:
            fixed, method = cls._fix_invalid_syntax(lines, error_line)
            if fixed:
                fix_method = method or 'fix_invalid_syntax'

        elif 'unexpected indent' in error_msg:
            fixed, method = cls._fix_unexpected_indent(lines, error_line)
            if fixed:
                fix_method = method or 'fix_unexpected_indent'

        # 验证修复
        if fix_method:
            new_source = ''.join(lines)
            try:
                ast.parse(new_source)
                # 写入文件
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(new_source)
                return True, fix_method
            except SyntaxError:
                pass

        # 策略3: 保守的迭代修复 - 只处理高置信度模式
        return cls._iterative_fix(fpath, lines)

    @classmethod
    def _fix_unterminated_string(cls, lines: List[str], error_line: int) -> Tuple[bool, str]:
        """修复未闭合的字符串"""
        if not error_line or error_line < 1 or error_line > len(lines):
            return False, ''
        
        line = lines[error_line - 1]
        
        # 统计单双引号
        single_quotes = line.count("'") - line.count("\\'")
        double_quotes = line.count('"') - line.count('\\"')
        
        if single_quotes % 2 != 0:
            lines[error_line - 1] = line.rstrip('\n') + "'\n"
            return True, 'add_single_quote'
        elif double_quotes % 2 != 0:
            lines[error_line - 1] = line.rstrip('\n') + '"\n'
            return True, 'add_double_quote'
        
        return False, ''

    @classmethod
    def _fix_indentation(cls, lines: List[str], error_line: int) -> Tuple[bool, str]:
        """修复缩进错误"""
        if not error_line or error_line < 1 or error_line > len(lines):
            return False, ''
        
        # 在错误行之前找最近的冒号行
        for i in range(error_line - 1, max(0, error_line - 20), -1):
            prev_line = lines[i]
            stripped = prev_line.strip()
            if stripped.endswith(':') and not stripped.startswith('#'):
                # 获取该行缩进
                indent = len(prev_line) - len(prev_line.lstrip())
                new_indent = indent + 4
                
                # 修复错误行及后续非空行
                for j in range(i + 1, min(len(lines), i + 10)):
                    next_line = lines[j]
                    if next_line.strip() == '':
                        continue
                    curr_indent = len(next_line) - len(next_line.lstrip())
                    if curr_indent < new_indent:
                        lines[j] = ' ' * new_indent + next_line.lstrip()
                    else:
                        break
                return True, 'add_indentation'
        
        return False, ''

    @classmethod
    def _fix_invalid_syntax(cls, lines: List[str], error_line: int) -> Tuple[bool, str]:
        """修复无效语法 - 处理常见模式"""
        if not error_line or error_line < 1 or error_line > len(lines):
            return False, ''
        
        line = lines[error_line - 1]
        
        # 模式: 括号在注释后面
        if re.search(r'#.*?[}\]\)]\s*$', line) and not re.search(r'["\'].*#', line):
            # 尝试将括号移到注释前
            m = re.search(r'^(.*?)([}\]\)])(\s*#.*)$', line)
            if m:
                lines[error_line - 1] = m.group(1) + m.group(3) + '\n'
                # 在前一行末尾添加括号
                prev_idx = error_line - 2
                while prev_idx >= 0 and lines[prev_idx].strip() == '':
                    prev_idx -= 1
                if prev_idx >= 0:
                    lines[prev_idx] = lines[prev_idx].rstrip('\n') + m.group(2) + '\n'
                return True, 'move_bracket_before_comment'
        
        # 模式: 语句合并（logger.error(...)return ...）
        merged_patterns = [
            (r'(\))\s*(return\s)', r'\1\n\2'),
            (r'(\))\s*(if\s)', r'\1\n\2'),
            (r'(\))\s*(for\s)', r'\1\n\2'),
            (r'(\))\s*(while\s)', r'\1\n\2'),
            (r'(\))\s*(with\s)', r'\1\n\2'),
            (r'(\))\s*(try:)', r'\1\n\2'),
            (r'(\))\s*(except\s)', r'\1\n\2'),
            (r'(\))\s*(raise\s)', r'\1\n\2'),
            (r'(\))\s*(pass)', r'\1\n\2'),
            (r'(\))\s*(break)', r'\1\n\2'),
            (r'(\))\s*(continue)', r'\1\n\2'),
            (r'(:)\s*(if\s)', r'\1\n    \2'),
            (r'(:)\s*(return\s)', r'\1\n    \2'),
            (r'(:)\s*(raise\s)', r'\1\n    \2'),
        ]
        
        for pattern, replacement in merged_patterns:
            if re.search(pattern, line):
                lines[error_line - 1] = re.sub(pattern, replacement, line)
                return True, 'split_merged_statements'
        
        return False, ''

    @classmethod
    def _fix_unexpected_indent(cls, lines: List[str], error_line: int) -> Tuple[bool, str]:
        """修复意外缩进"""
        if not error_line or error_line < 1 or error_line > len(lines):
            return False, ''
        
        line = lines[error_line - 1]
        stripped = line.lstrip()
        
        # 向前找正确的缩进级别
        target_indent = 0
        for i in range(error_line - 2, max(0, error_line - 30), -1):
            prev = lines[i]
            if prev.strip() == '' or prev.strip().startswith('#'):
                continue
            prev_stripped = prev.lstrip()
            if prev_stripped.endswith(':'):
                target_indent = len(prev) - len(prev.lstrip()) + 4
            else:
                target_indent = len(prev) - len(prev.lstrip())
            break
        
        current_indent = len(line) - len(line.lstrip())
        if current_indent != target_indent:
            lines[error_line - 1] = ' ' * target_indent + stripped
            return True, 'fix_unexpected_indent'
        
        return False, ''

    @classmethod
    def _iterative_fix(cls, fpath: str, lines: List[str]) -> Tuple[bool, str]:
        """迭代修复 - 尝试修复常见错误模式"""
        max_attempts = 5
        fixed = False
        fix_methods = []
        
        for attempt in range(max_attempts):
            source = ''.join(lines)
            try:
                ast.parse(source)
                fixed = True
                break
            except SyntaxError as e:
                err_line = e.lineno or 0
                err_msg = str(e.msg)
                
                if err_line < 1 or err_line > len(lines):
                    break
                
                # 尝试修复
                success = False
                
                # 模式1: 语句合并
                line = lines[err_line - 1]
                merged_patterns = [
                    (r'(\))\s*(return\s)', r'\1\n\2', 'split_return'),
                    (r'(\))\s*(if\s)', r'\1\n\2', 'split_if'),
                    (r'(\))\s*(for\s)', r'\1\n\2', 'split_for'),
                    (r'(\))\s*(def\s)', r'\1\n\2', 'split_def'),
                    (r'(\))\s*(class\s)', r'\1\n\2', 'split_class'),
                    (r'(""".*?""")\s*(with\s)', r'\1\n\2', 'split_docstring_with'),
                    (r'(""".*?""")\s*(if\s)', r'\1\n\2', 'split_docstring_if'),
                    (r'(""".*?""")\s*(return\s)', r'\1\n\2', 'split_docstring_return'),
                ]
                
                for pattern, replacement, method in merged_patterns:
                    if re.search(pattern, line):
                        lines[err_line - 1] = re.sub(pattern, replacement, line)
                        fix_methods.append(method)
                        success = True
                        break
                
                if not success:
                    break
        
        if fixed and fix_methods:
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(''.join(lines))
            return True, '+'.join(fix_methods)
        
        return False, ''


# ============== CSS 语法修复器 ==============
class CSSFixer:
    """CSS语法错误自动修复器 - 处理常见CSS语法错误"""

    ERROR_PATTERNS = [
        {
            'name': 'missing_lbrace',
            'detect_msg': lambda msg: 'lcurlyexpected' in msg.lower() or '应为 {' in msg or 'missing {' in msg.lower(),
            'confidence': 0.7,
        },
        {
            'name': 'missing_rbrace',
            'detect_msg': lambda msg: 'rcurlyexpected' in msg.lower() or '应有 }' in msg or 'missing }' in msg.lower(),
            'confidence': 0.7,
        },
        {
            'name': 'missing_selector',
            'detect_msg': lambda msg: 'ruleorselectorexpected' in msg.lower() or '预期有标识符' in msg or 'identifierexpected' in msg.lower(),
            'confidence': 0.6,
        },
        {
            'name': 'missing_colon',
            'detect_msg': lambda msg: 'semicolonexpected' in msg.lower() or '缺少分号' in msg,
            'confidence': 0.65,
        },
    ]

    @classmethod
    def check_css_syntax(cls, fpath: str) -> Optional[Dict]:
        """检测CSS文件语法错误"""
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception:
            return None

        issues = []
        
        # 跳过包含模板语法的CSS（Jinja2等）
        if re.search(r'{%\s*(if|for|set|include|extends|macro)', content) or '{{' in content:
            # 对于模板文件，只做基本检查，降低置信度
            issues = cls._basic_css_check(content, is_template=True)
        else:
            issues = cls._full_css_check(content)

        if issues:
            return {
                'issue_type': 'css_syntax_error',
                'severity': 'medium',
                'file_path': fpath,
                'line_number': issues[0].get('line', 0),
                'error_message': '; '.join([i['msg'] for i in issues[:3]]),
                'error_code': f'CSS_ERROR_{issues[0]["code"]}',
                'confidence': issues[0].get('confidence', 0.5),
                '_css_issues': issues,
            }
        return None

    @classmethod
    def _basic_css_check(cls, content: str, is_template: bool = False) -> List[Dict]:
        """基础CSS检查 - 适用于模板文件"""
        issues = []
        
        # 统计大括号（忽略模板语法中的括号）
        clean_content = cls._strip_template_syntax(content)
        
        open_braces = clean_content.count('{')
        close_braces = clean_content.count('}')
        
        if open_braces != close_braces:
            conf = 0.3 if is_template else 0.6
            issues.append({
                'code': 'BRACE_MISMATCH',
                'msg': f'大括号不平衡: 开{open_braces} 闭{close_braces}',
                'line': 0,
                'confidence': conf,
            })
        
        return issues

    @classmethod
    def _strip_template_syntax(cls, content: str) -> str:
        """移除模板语法标记，便于统计"""
        result = content
        result = re.sub(r'{%.*?%}', '', result, flags=re.DOTALL)
        result = re.sub(r'{{.*?}}', '', result)
        result = re.sub(r'{#.*?#}', '', result, flags=re.DOTALL)
        return result

    @classmethod
    def _full_css_check(cls, content: str) -> List[Dict]:
        """完整CSS语法检查"""
        issues = []
        lines = content.split('\n')
        
        # 1. 括号平衡检查
        open_braces = content.count('{')
        close_braces = content.count('}')
        if open_braces != close_braces:
            issues.append({
                'code': 'BRACE_MISMATCH',
                'msg': f'大括号不平衡: 开{open_braces} 闭{close_braces}',
                'line': 0,
                'confidence': 0.7,
            })
        
        # 2. 逐行检查常见错误
        in_comment = False
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # 跳过注释
            if '/*' in stripped:
                in_comment = True
            if '*/' in stripped:
                in_comment = False
                continue
            if in_comment or stripped.startswith('/*') or stripped == '':
                continue
            
            # 检测缺少分号的属性行（非最后一个属性且不是以}结尾）
            if ':' in stripped and not stripped.endswith(';') and not stripped.endswith('{') and not stripped.endswith('}') and not stripped.startswith('@'):
                # 排除一些特殊情况
                if not stripped.startswith('//') and not stripped.startswith('/*'):
                    issues.append({
                        'code': 'MISSING_SEMICOLON',
                        'msg': f'第{i}行可能缺少分号: {stripped[:50]}',
                        'line': i,
                        'confidence': 0.4,
                    })
        
        # 3. 检测无效的选择器
        selector_pattern = re.compile(r'^([^{]+)\{', re.MULTILINE)
        for match in selector_pattern.finditer(content):
            selector = match.group(1).strip()
            if selector == '':
                line_num = content[:match.start()].count('\n') + 1
                issues.append({
                    'code': 'EMPTY_SELECTOR',
                    'msg': f'第{line_num}行存在空选择器',
                    'line': line_num,
                    'confidence': 0.6,
                })
        
        return issues

    @classmethod
    def fix_file(cls, fpath: str, error_msg: str, error_code: str) -> Tuple[bool, str]:
        """尝试修复CSS文件错误 - 依次尝试多种修复方法"""
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception:
            return False, ''

        original = content
        fix_methods = []
        
        # 按优先级依次尝试修复
        fix_sequence = [
            ('MISSING_SEMICOLON', cls._fix_missing_semicolons, 'semicolon'),
            ('BRACE_MISMATCH', cls._fix_brace_mismatch, 'brace'),
            ('EMPTY_SELECTOR', cls._fix_empty_selectors, 'selector'),
        ]
        
        for code_key, fix_func, fix_name in fix_sequence:
            try:
                fixed_content, method = fix_func(content)
                if method and fixed_content != content:
                    content = fixed_content
                    fix_methods.append(method)
            except Exception:
                continue
        
        # 如果有修复，写回文件
        if fix_methods and content != original:
            try:
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True, '+'.join(fix_methods)
            except Exception:
                pass
        
        return False, ''

    @classmethod
    def _fix_brace_mismatch(cls, content: str) -> Tuple[str, str]:
        """修复大括号不平衡"""
        open_count = content.count('{')
        close_count = content.count('}')
        diff = open_count - close_count
        
        if diff > 0:
            # 缺少右括号，在末尾添加
            return content + '\n' + '}' * diff, 'add_missing_rbraces'
        elif diff < 0:
            # 缺少左括号，尝试在开头添加（不常用，保守处理）
            return '{' * (-diff) + '\n' + content, 'add_missing_lbraces'
        
        return content, ''

    @classmethod
    def _fix_missing_semicolons(cls, content: str) -> Tuple[str, str]:
        """修复缺少分号的属性行"""
        lines = content.split('\n')
        fixed_count = 0
        
        in_comment = False
        for i in range(len(lines)):
            line = lines[i]
            stripped = line.strip()
            
            if '/*' in stripped:
                in_comment = True
            if '*/' in stripped:
                in_comment = False
                continue
            if in_comment or stripped.startswith('/*') or stripped.startswith('//') or stripped == '':
                continue
            
            # 属性行：包含冒号，但不以分号、大括号、@开头
            if (':' in stripped and 
                not stripped.endswith(';') and 
                not stripped.endswith('{') and 
                not stripped.endswith('}') and 
                not stripped.startswith('@') and
                not stripped.startswith('$') and
                not stripped.startswith('//')):
                # 确认下一行不是选择器或闭合括号
                next_line = lines[i+1].strip() if i+1 < len(lines) else ''
                if not next_line.startswith('}') and not next_line.endswith('{'):
                    lines[i] = line.rstrip() + ';'
                    fixed_count += 1
        
        if fixed_count > 0:
            return '\n'.join(lines), f'fix_missing_semicolons_{fixed_count}'
        
        return content, ''

    @classmethod
    def _fix_empty_selectors(cls, content: str) -> Tuple[str, str]:
        """修复空选择器"""
        new_content = re.sub(r'\n\s*\{\s*\}', '', content)
        if new_content != content:
            return new_content, 'remove_empty_selectors'
        return content, ''


# ============== JavaScript 语法修复器 ==============
class JSFixer:
    """JavaScript语法错误自动修复器"""

    @classmethod
    def check_js_syntax(cls, fpath: str) -> Optional[Dict]:
        """检测JS语法问题"""
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception:
            return None

        issues = []
        
        # 1. 括号平衡检查
        for open_char, close_char, name, code in [
            ('{', '}', '大括号', 'BRACE'),
            ('(', ')', '圆括号', 'PAREN'),
            ('[', ']', '方括号', 'BRACKET'),
        ]:
            # 简单跳过字符串和注释中的括号
            clean = cls._strip_js_strings_and_comments(content)
            open_count = clean.count(open_char)
            close_count = clean.count(close_char)
            if open_count != close_count:
                issues.append({
                    'code': f'JS_{code}_MISMATCH',
                    'msg': f'{name}不平衡: 开{open_count} 闭{close_count}',
                    'severity': 'medium',
                    'confidence': 0.5,
                })
        
        if issues:
            return {
                'issue_type': 'js_syntax_warning',
                'severity': issues[0]['severity'],
                'file_path': fpath,
                'line_number': 0,
                'error_message': '; '.join([i['msg'] for i in issues[:3]]),
                'error_code': issues[0]['code'],
                'confidence': issues[0]['confidence'],
                '_all_js_issues': issues,
            }
        return None

    @classmethod
    def _strip_js_strings_and_comments(cls, content: str) -> str:
        """移除JS字符串和注释，便于统计括号"""
        result = content
        result = re.sub(r'//.*$', '', result, flags=re.MULTILINE)
        result = re.sub(r'/\*.*?\*/', '', result, flags=re.DOTALL)
        result = re.sub(r"'[^'\\]*(\\.[^'\\]*)*'", "''", result)
        result = re.sub(r'"[^"\\]*(\\.[^"\\]*)*"', '""', result)
        result = re.sub(r'`[^`\\]*(\\.[^`\\]*)*`', '``', result)
        return result

    @classmethod
    def fix_file(cls, fpath: str, error_msg: str, error_code: str) -> Tuple[bool, str]:
        """尝试修复JS文件错误"""
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception:
            return False, ''

        original = content
        fix_methods = []
        
        # 按优先级尝试修复
        fix_sequence = [
            ('BRACE', cls._fix_brace_mismatch, 'braces'),
            ('PAREN', cls._fix_paren_mismatch, 'parens'),
            ('BRACKET', cls._fix_bracket_mismatch, 'brackets'),
        ]
        
        for code_key, fix_func, fix_name in fix_sequence:
            if code_key in error_code or code_key.lower() in error_msg.lower():
                try:
                    fixed_content, method = fix_func(content)
                    if method and fixed_content != content:
                        content = fixed_content
                        fix_methods.append(method)
                except Exception:
                    continue
        
        if fix_methods and content != original:
            try:
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True, '+'.join(fix_methods)
            except Exception:
                pass
        
        return False, ''

    @classmethod
    def _fix_brace_mismatch(cls, content: str) -> Tuple[str, str]:
        """修复大括号不平衡"""
        clean = cls._strip_js_strings_and_comments(content)
        open_count = clean.count('{')
        close_count = clean.count('}')
        diff = open_count - close_count
        
        if diff > 0:
            return content + '\n' + '}' * diff, f'add_missing_rbraces_{diff}'
        elif diff < 0:
            return '{' * (-diff) + '\n' + content, f'add_missing_lbraces_{-diff}'
        
        return content, ''

    @classmethod
    def _fix_paren_mismatch(cls, content: str) -> Tuple[str, str]:
        """修复圆括号不平衡（保守处理）"""
        return content, ''

    @classmethod
    def _fix_bracket_mismatch(cls, content: str) -> Tuple[str, str]:
        """修复方括号不平衡（保守处理）"""
        return content, ''


# ============== HTML 修复器 ==============
class HTMLFixer:
    """HTML结构问题自动修复器"""

    @classmethod
    def fix_file(cls, fpath: str, error_msg: str, error_code: str) -> Tuple[bool, str]:
        """尝试修复HTML文件问题"""
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception:
            return False, ''

        original = content
        fix_methods = []
        
        # 修复style块中的CSS问题
        if 'STYLE_BLOCK_CSS' in error_code or 'style' in error_msg.lower():
            try:
                fixed_content, method = cls._fix_style_blocks(content)
                if method and fixed_content != content:
                    content = fixed_content
                    fix_methods.append(method)
            except Exception:
                pass
        
        # 修复内联CSS问题（保守处理，暂不自动修复）
        
        if fix_methods and content != original:
            try:
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True, '+'.join(fix_methods)
            except Exception:
                pass
        
        return False, ''

    @classmethod
    def _fix_style_blocks(cls, content: str) -> Tuple[str, str]:
        """修复HTML中style标签内的CSS问题"""
        fix_count = 0
        
        def replace_style(match):
            nonlocal fix_count
            style_content = match.group(1)
            clean = CSSFixer._strip_template_syntax(style_content)
            open_b = clean.count('{')
            close_b = clean.count('}')
            diff = open_b - close_b
            
            if diff > 0:
                fix_count += diff
                return f'<style{match.group(0)[len(match.group(1))+7:len(match.group(0))-len(style_content)-8]}>{style_content}' + '}' * diff + '</style>'
            
            return match.group(0)
        
        new_content = re.sub(
            r'<style[^>]*>(.*?)</style>',
            replace_style,
            content,
            flags=re.DOTALL | re.IGNORECASE
        )
        
        if fix_count > 0:
            return new_content, f'fix_style_blocks_{fix_count}'
        return content, ''


# ============== 主引擎类 ==============
class AIInspectionLoopEngine:
    """AI 巡检闭环引擎 - 完整闭环实现"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self._running = False
        self._thread = None
        self._interval = 300
        self._stats = {
            'total_runs': 0,
            'total_errors_found': 0,
            'total_errors_fixed': 0,
            'total_knowledge_gained': 0,
            'last_run_at': None,
            'current_status': 'idle',
        }
        self._console_errors_buffer = []
        self._console_lock = threading.Lock()
        _logger.info("AI巡检闭环引擎初始化完成")

    # ---------- 公共API ----------

    def start(self, interval: int = 300):
        """启动后台巡检循环"""
        if self._running:
            return False
        self._interval = interval
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="AI-Inspection-Loop")
        self._thread.start()
        _logger.info(f"AI巡检闭环引擎已启动，间隔 {interval}秒")
        return True

    def stop(self):
        """停止巡检循环"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        _logger.info("AI巡检闭环引擎已停止")

    def run_once(self, run_type: str = 'manual') -> Dict[str, Any]:
        """执行一次完整巡检闭环（手动触发）"""
        return self._full_inspection_cycle(run_type)

    def get_status(self) -> Dict[str, Any]:
        return dict(self._stats)

    def report_console_error(self, error_data: Dict[str, Any]) -> str:
        """上报前端控制台错误"""
        error_id = f"CE-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hashlib.md5(json.dumps(error_data, sort_keys=True).encode()).hexdigest()[:8]}"
        
        try:
            with _get_conn() as conn:
                c = conn.cursor()
                now = datetime.now().isoformat()
                c.execute(
                    """INSERT OR IGNORE INTO ai_inspection_console_errors
                       (error_id, source, error_type, error_message, stack_trace,
                        file_path, line_number, column_number, user_agent, url, reported_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        error_id,
                        error_data.get('source', 'frontend'),
                        error_data.get('type', 'unknown'),
                        error_data.get('message', '')[:500],
                        error_data.get('stack', '')[:2000],
                        error_data.get('filename', ''),
                        error_data.get('lineno', 0),
                        error_data.get('colno', 0),
                        error_data.get('userAgent', '')[:200],
                        error_data.get('url', '')[:300],
                        now,
                    )
                )
                conn.commit()
        except Exception as e:
            _logger.error(f"控制台错误上报失败: {e}")
        
        return error_id

    def get_recent_issues(self, limit: int = 20) -> List[Dict]:
        """获取最近的问题"""
        try:
            with _get_conn() as conn:
                c = conn.cursor()
                c.execute(
                    """SELECT * FROM ai_inspection_issues 
                       ORDER BY detected_at DESC LIMIT ?""",
                    (limit,)
                )
                return [dict(row) for row in c.fetchall()]
        except Exception:
            return []

    def get_knowledge_base(self, limit: int = 50) -> List[Dict]:
        """获取知识库"""
        try:
            with _get_conn() as conn:
                c = conn.cursor()
                c.execute(
                    """SELECT * FROM ai_inspection_knowledge 
                       ORDER BY success_count DESC, confidence DESC LIMIT ?""",
                    (limit,)
                )
                return [dict(row) for row in c.fetchall()]
        except Exception:
            return []

    # ---------- 核心闭环 ----------

    def _loop(self):
        """后台循环"""
        while self._running:
            try:
                self._stats['current_status'] = 'running'
                self._full_inspection_cycle('scheduled')
                self._stats['current_status'] = 'idle'
            except Exception as e:
                _logger.error(f"巡检循环异常: {e}\n{traceback.format_exc()}")
                self._stats['current_status'] = 'error'
            for _ in range(self._interval):
                if not self._running:
                    break
                time.sleep(1)

    def _full_inspection_cycle(self, run_type: str) -> Dict[str, Any]:
        """完整巡检闭环：扫描→检测→修复→上报→学习"""
        run_id = f"INS-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.getpid()}"
        start_time = time.time()
        _logger.info(f"===== 巡检闭环开始 [{run_id}] 类型: {run_type} =====")

        try:
            with _get_conn() as conn:
                conn.execute(
                    "INSERT INTO ai_inspection_runs (run_id, run_type, started_at, status) VALUES (?, ?, ?, 'running')",
                    (run_id, run_type, datetime.now().isoformat())
                )
                conn.commit()
        except Exception as e:
            _logger.error(f"写入巡检记录失败: {e}")

        all_issues = []
        files_scanned = 0

        # === 第1环：文件结构巡检 ===
        try:
            struct_issues, struct_files = self._scan_file_structure()
            all_issues.extend(struct_issues)
            files_scanned += struct_files
            _logger.info(f"[1/7] 文件结构巡检: 扫描 {struct_files} 文件, 发现 {len(struct_issues)} 个问题")
        except Exception as e:
            _logger.error(f"文件结构巡检失败: {e}")

        # === 第1.5环：备份目录巡检 ===
        try:
            backup_issues = self._scan_backup_directories()
            all_issues.extend(backup_issues)
            _logger.info(f"[1.5/7] 备份目录巡检: 发现 {len(backup_issues)} 个问题")
            
            # 自动清理旧备份
            if backup_issues:
                cleanup_result = self._auto_cleanup_backups()
                _logger.info(f"[1.5/7] 自动清理备份完成: 清理 {cleanup_result['cleaned_count']} 个文件, 释放 {cleanup_result['cleaned_size_mb']:.1f}MB")
        except Exception as e:
            _logger.error(f"备份目录巡检失败: {e}")

        # === 第1.6环：法律准则文件巡检 ===
        try:
            rules_issues = self._scan_rules_files()
            all_issues.extend(rules_issues)
            _logger.info(f"[1.6/7] 法律准则巡检: 发现 {len(rules_issues)} 个问题")
            
            # 自动更新规则文件
            if rules_issues:
                update_result = self._auto_update_rules()
                _logger.info(f"[1.6/7] 自动更新规则完成: 更新 {update_result['updated_count']} 个文件")
        except Exception as e:
            _logger.error(f"法律准则巡检失败: {e}")

        # === 第1.75环：根目录整理巡检 ===
        try:
            root_issues = self._scan_root_directory_organization()
            all_issues.extend(root_issues)
            _logger.info(f"[1.75/7] 根目录整理巡检: 发现 {len(root_issues)} 个问题")
            
            # 自动整理根目录
            if root_issues:
                organize_result = self._auto_organize_root_files()
                _logger.info(f"[1.75/7] 自动整理根目录完成: 整理 {organize_result['organized_count']} 个文件, 清理 {organize_result['cleaned_count']} 个临时目录")
        except Exception as e:
            _logger.error(f"根目录整理巡检失败: {e}")

        # === 第2环：语法错误巡检 ===
        try:
            syntax_issues, syntax_files = self._scan_syntax_errors()
            all_issues.extend(syntax_issues)
            files_scanned += syntax_files
            _logger.info(f"[2/7] 语法错误巡检: 扫描 {syntax_files} 文件, 发现 {len(syntax_issues)} 个问题")
        except Exception as e:
            _logger.error(f"语法错误巡检失败: {e}")

        # === 第3环：控制台/运行时错误巡检 ===
        try:
            runtime_issues = self._scan_runtime_errors()
            all_issues.extend(runtime_issues)
            _logger.info(f"[3/7] 运行时错误巡检: 发现 {len(runtime_issues)} 个问题")
        except Exception as e:
            _logger.error(f"运行时错误巡检失败: {e}")

        errors_found = len(all_issues)
        errors_fixed = 0
        errors_failed = 0

        # 批量写入问题
        self._bulk_insert_issues(run_id, all_issues)

        # === 第4环：自动修复 ===
        if errors_found > 0:
            _logger.info(f"[4/7] 自动修复开始: 共 {errors_found} 个待修复问题")
            fixed, failed = self._auto_fix_issues(run_id, all_issues)
            errors_fixed = fixed
            errors_failed = failed
            _logger.info(f"[4/7] 自动修复完成: 成功 {fixed}, 失败 {failed}")
        else:
            _logger.info("[4/7] 自动修复: 无待修复问题，跳过")

        # === 第5环：数据库上报 ===
        try:
            duration_ms = int((time.time() - start_time) * 1000)
            with _get_conn() as conn:
                conn.execute(
                    """UPDATE ai_inspection_runs 
                       SET completed_at=?, files_scanned=?, errors_found=?, 
                           errors_fixed=?, errors_failed=?, status='completed', duration_ms=?
                       WHERE run_id=?""",
                    (datetime.now().isoformat(), files_scanned, errors_found,
                     errors_fixed, errors_failed, duration_ms, run_id)
                )
                conn.commit()
            _logger.info(f"[5/7] 数据库上报完成: run_id={run_id}")
        except Exception as e:
            _logger.error(f"数据库上报失败: {e}")

        # === 第6环：日志记录 ===
        _logger.info(
            f"[6/7] 日志记录: 扫描{files_scanned}文件 | "
            f"发现{errors_found}错误 | 修复{errors_fixed} | 失败{errors_failed}"
        )

        # === 第7环：AI自学习升级 ===
        knowledge_gained = 0
        if errors_fixed > 0:
            try:
                knowledge_gained = self._learn_from_fixes(run_id)
                _logger.info(f"[7/7] AI学习升级: 新增/优化 {knowledge_gained} 条知识")
            except Exception as e:
                _logger.error(f"AI学习升级失败: {e}")
        else:
            _logger.info("[7/7] AI学习升级: 无新修复案例，跳过")

        # 更新统计
        self._stats['total_runs'] += 1
        self._stats['total_errors_found'] += errors_found
        self._stats['total_errors_fixed'] += errors_fixed
        self._stats['total_knowledge_gained'] += knowledge_gained
        self._stats['last_run_at'] = datetime.now().isoformat()

        duration = time.time() - start_time
        _logger.info(
            f"===== 巡检闭环完成 [{run_id}] 耗时 {duration:.2f}s | "
            f"扫描:{files_scanned} 发现:{errors_found} 修复:{errors_fixed} 学习:{knowledge_gained} ====="
        )

        return {
            'run_id': run_id,
            'files_scanned': files_scanned,
            'errors_found': errors_found,
            'errors_fixed': errors_fixed,
            'errors_failed': errors_failed,
            'knowledge_gained': knowledge_gained,
            'duration_ms': int(duration * 1000),
        }

    # ============== 1. 文件结构巡检 ==============

    def _scan_file_structure(self) -> Tuple[List[Dict], int]:
        """扫描项目文件结构，检测异常"""
        issues = []
        file_count = 0
        skip_dirs = {
            '__pycache__', '.git', 'node_modules', 'venv', '.venv',
            'flask-app-old', 'logs', 'data', '.idea', '.vscode',
            'dist', 'build', '.DS_Store',
        }

        for root, dirs, files in os.walk(_PROJECT_ROOT):
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]

            for fname in files:
                file_count += 1
                fpath = os.path.join(root, fname)

                # 检测空文件
                try:
                    if os.path.getsize(fpath) == 0:
                        issues.append({
                            'issue_type': 'empty_file',
                            'severity': 'low',
                            'file_path': fpath,
                            'line_number': 0,
                            'error_message': '空文件',
                            'error_code': 'EMPTY_FILE',
                            'confidence': 1.0,
                        })
                except Exception:
                    pass

                # 检测临时文件 / 备份文件
                if fname.endswith(('.tmp', '.bak', '.old', '~')) or fname.startswith('.~'):
                    issues.append({
                        'issue_type': 'temp_file',
                        'severity': 'low',
                        'file_path': fpath,
                        'line_number': 0,
                        'error_message': f'临时/备份文件: {fname}',
                        'error_code': 'TEMP_FILE',
                        'confidence': 0.9,
                    })

                # 检测大文件
                try:
                    size_mb = os.path.getsize(fpath) / (1024 * 1024)
                    if size_mb > 5 and fname.endswith(('.py', '.js', '.html', '.css', '.json', '.txt', '.md')):
                        issues.append({
                            'issue_type': 'large_file',
                            'severity': 'medium',
                            'file_path': fpath,
                            'line_number': 0,
                            'error_message': f'文件过大: {size_mb:.1f}MB',
                            'error_code': 'LARGE_FILE',
                            'confidence': 0.7,
                        })
                except Exception:
                    pass

                # 检测文件名包含中文标点等异常
                if re.search(r'[\u3000-\u303f\uff00-\uffef]', fname):
                    issues.append({
                        'issue_type': 'filename_special_chars',
                        'severity': 'low',
                        'file_path': fpath,
                        'line_number': 0,
                        'error_message': f'文件名包含特殊字符: {fname}',
                        'error_code': 'FILENAME_SPECIAL',
                        'confidence': 0.8,
                    })

        return issues, file_count

    def _scan_backup_directories(self) -> List[Dict]:
        """扫描备份目录，检测旧备份和大备份文件"""
        issues = []
        
        backup_dirs = [
            os.path.join(_PROJECT_ROOT, 'flask-app', 'backups'),
            os.path.join(_PROJECT_ROOT, 'data', 'backups'),
            os.path.join(_PROJECT_ROOT, 'Database', 'backups'),
            os.path.join(_PROJECT_ROOT, 'Backups'),
        ]
        
        max_backup_age_days = 7
        max_backup_files = 5
        max_backup_size_mb = 100
        
        for backup_dir in backup_dirs:
            if not os.path.isdir(backup_dir):
                continue
            
            backup_files = []
            for root, dirs, files in os.walk(backup_dir):
                for fname in files:
                    fpath = os.path.join(root, fname)
                    try:
                        mtime = os.path.getmtime(fpath)
                        size_mb = os.path.getsize(fpath) / (1024 * 1024)
                        backup_files.append({
                            'path': fpath,
                            'mtime': mtime,
                            'size_mb': size_mb,
                            'name': fname,
                        })
                    except Exception:
                        continue
                
                # 检查目录
                for dname in dirs:
                    dpath = os.path.join(root, dname)
                    try:
                        mtime = os.path.getmtime(dpath)
                        backup_files.append({
                            'path': dpath,
                            'mtime': mtime,
                            'size_mb': 0,
                            'name': dname,
                            'is_dir': True,
                        })
                    except Exception:
                        continue
            
            # 检查备份数量
            if len(backup_files) > max_backup_files:
                issues.append({
                    'issue_type': 'backup_excessive',
                    'severity': 'medium',
                    'file_path': backup_dir,
                    'line_number': 0,
                    'error_message': f'备份文件过多: {len(backup_files)}个，建议保留{max_backup_files}个以内',
                    'error_code': 'BACKUP_EXCESSIVE',
                    'confidence': 0.8,
                })
            
            # 检查旧备份
            now = time.time()
            old_backups = [bf for bf in backup_files if (now - bf['mtime']) / 86400 > max_backup_age_days]
            if old_backups:
                issues.append({
                    'issue_type': 'backup_old',
                    'severity': 'low',
                    'file_path': backup_dir,
                    'line_number': 0,
                    'error_message': f'发现{len(old_backups)}个过期备份（超过{max_backup_age_days}天）',
                    'error_code': 'BACKUP_OLD',
                    'confidence': 0.9,
                })
            
            # 检查备份大小
            total_size = sum(bf['size_mb'] for bf in backup_files)
            if total_size > max_backup_size_mb:
                issues.append({
                    'issue_type': 'backup_large',
                    'severity': 'medium',
                    'file_path': backup_dir,
                    'line_number': 0,
                    'error_message': f'备份总大小过大: {total_size:.1f}MB，超过{max_backup_size_mb}MB',
                    'error_code': 'BACKUP_LARGE',
                    'confidence': 0.8,
                })
        
        return issues

    def _auto_cleanup_backups(self) -> Dict[str, Any]:
        """自动清理旧备份文件"""
        result = {
            'cleaned_count': 0,
            'cleaned_size_mb': 0,
            'cleaned_files': [],
            'errors': [],
        }
        
        backup_dirs = [
            os.path.join(_PROJECT_ROOT, 'flask-app', 'backups'),
            os.path.join(_PROJECT_ROOT, 'data', 'backups'),
            os.path.join(_PROJECT_ROOT, 'Database', 'backups'),
            os.path.join(_PROJECT_ROOT, 'Backups'),
        ]
        
        max_backup_age_days = 7
        max_backup_files = 5
        
        now = time.time()
        
        for backup_dir in backup_dirs:
            if not os.path.isdir(backup_dir):
                continue
            
            backup_files = []
            for root, dirs, files in os.walk(backup_dir):
                for fname in files:
                    fpath = os.path.join(root, fname)
                    try:
                        mtime = os.path.getmtime(fpath)
                        size_mb = os.path.getsize(fpath) / (1024 * 1024)
                        backup_files.append({
                            'path': fpath,
                            'mtime': mtime,
                            'size_mb': size_mb,
                            'name': fname,
                            'is_dir': False,
                        })
                    except Exception:
                        continue
                
                for dname in dirs:
                    dpath = os.path.join(root, dname)
                    try:
                        mtime = os.path.getmtime(dpath)
                        backup_files.append({
                            'path': dpath,
                            'mtime': mtime,
                            'size_mb': 0,
                            'name': dname,
                            'is_dir': True,
                        })
                    except Exception:
                        continue
            
            # 按时间排序，最新的在前
            backup_files.sort(key=lambda x: x['mtime'], reverse=True)
            
            # 删除旧备份（超过max_backup_age_days天）
            for bf in backup_files:
                age_days = (now - bf['mtime']) / 86400
                if age_days > max_backup_age_days:
                    try:
                        if bf['is_dir']:
                            import shutil
                            shutil.rmtree(bf['path'])
                        else:
                            os.remove(bf['path'])
                        result['cleaned_count'] += 1
                        result['cleaned_size_mb'] += bf['size_mb']
                        result['cleaned_files'].append(bf['path'])
                        _logger.info(f'已清理旧备份: {bf["path"]} (年龄: {age_days:.1f}天)')
                    except Exception as e:
                        result['errors'].append(f'清理失败: {bf["path"]} - {e}')
            
            # 如果备份文件仍然过多，删除最旧的
            backup_files = []
            for root, dirs, files in os.walk(backup_dir):
                for fname in files:
                    fpath = os.path.join(root, fname)
                    try:
                        backup_files.append((os.path.getmtime(fpath), fpath, False))
                    except Exception:
                        continue
                for dname in dirs:
                    dpath = os.path.join(root, dname)
                    try:
                        backup_files.append((os.path.getmtime(dpath), dpath, True))
                    except Exception:
                        continue
            
            backup_files.sort(key=lambda x: x[0], reverse=True)
            
            # 保留最新的max_backup_files个
            for mtime, fpath, is_dir in backup_files[max_backup_files:]:
                try:
                    if is_dir:
                        import shutil
                        shutil.rmtree(fpath)
                    else:
                        os.remove(fpath)
                    result['cleaned_count'] += 1
                    result['cleaned_files'].append(fpath)
                    _logger.info(f'已清理多余备份: {fpath}')
                except Exception as e:
                    result['errors'].append(f'清理失败: {fpath} - {e}')
        
        return result

    # ============== 1.6. 法律准则文件巡检 ==============

    def _scan_rules_files(self) -> List[Dict]:
        """扫描法律准则文件，检测完整性、格式和版本一致性"""
        issues = []
        
        rules_dirs = [
            os.path.join(_PROJECT_ROOT, '.trae', 'rules'),
            os.path.join(_PROJECT_ROOT, 'wuchenghao15', '.trae', 'rules'),
        ]
        
        all_rules_dir = None
        for rd in rules_dirs:
            if os.path.isdir(rd):
                all_rules_dir = rd
                break
        
        if not all_rules_dir:
            issues.append({
                'issue_type': 'rules_dir_missing',
                'severity': 'high',
                'file_path': rules_dirs[0],
                'line_number': 0,
                'error_message': f'规则目录不存在: {rules_dirs}',
                'error_code': 'RULES_DIR_MISSING',
                'confidence': 1.0,
            })
            return issues
        
        rules_dir = all_rules_dir
        required_files = [
            'AI系统操作规范.md',
            '开发规则.md',
            '源码修改准则参考与思路方案.md',
            '系统操作规范.md',
        ]
        
        # 1. 检查规则目录是否存在
        if not os.path.isdir(rules_dir):
            issues.append({
                'issue_type': 'rules_dir_missing',
                'severity': 'high',
                'file_path': rules_dir,
                'line_number': 0,
                'error_message': f'规则目录不存在: {rules_dir}',
                'error_code': 'RULES_DIR_MISSING',
                'confidence': 1.0,
            })
            return issues
        
        # 2. 检查必需文件是否存在
        missing_files = []
        for fname in required_files:
            fpath = os.path.join(rules_dir, fname)
            if not os.path.exists(fpath):
                missing_files.append(fname)
        
        if missing_files:
            issues.append({
                'issue_type': 'rules_file_missing',
                'severity': 'high',
                'file_path': rules_dir,
                'line_number': 0,
                'error_message': f'缺少规则文件: {", ".join(missing_files)}',
                'error_code': 'RULES_FILE_MISSING',
                'confidence': 1.0,
            })
        
        # 3. 检查文件格式和内容
        for fname in required_files:
            fpath = os.path.join(rules_dir, fname)
            if not os.path.exists(fpath):
                continue
            
            try:
                with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                
                # 检查文件是否为空
                if not content.strip():
                    issues.append({
                        'issue_type': 'rules_file_empty',
                        'severity': 'medium',
                        'file_path': fpath,
                        'line_number': 0,
                        'error_message': f'规则文件为空: {fname}',
                        'error_code': 'RULES_FILE_EMPTY',
                        'confidence': 1.0,
                    })
                    continue
                
                # 检查是否包含必要的元数据
                if 'alwaysApply' not in content:
                    issues.append({
                        'issue_type': 'rules_metadata_missing',
                        'severity': 'low',
                        'file_path': fpath,
                        'line_number': 0,
                        'error_message': f'规则文件缺少元数据(alwaysApply): {fname}',
                        'error_code': 'RULES_METADATA_MISSING',
                        'confidence': 0.8,
                    })
                
                # 检查版本信息
                version_match = re.search(r'(规则版本|规范版本).*?v?([\d.]+)', content)
                if not version_match:
                    issues.append({
                        'issue_type': 'rules_version_missing',
                        'severity': 'low',
                        'file_path': fpath,
                        'line_number': 0,
                        'error_message': f'规则文件缺少版本信息: {fname}',
                        'error_code': 'RULES_VERSION_MISSING',
                        'confidence': 0.7,
                    })
                
                # 检查生效日期
                if '生效日期' not in content:
                    issues.append({
                        'issue_type': 'rules_effective_date_missing',
                        'severity': 'low',
                        'file_path': fpath,
                        'line_number': 0,
                        'error_message': f'规则文件缺少生效日期: {fname}',
                        'error_code': 'RULES_DATE_MISSING',
                        'confidence': 0.6,
                    })
                
                # 检查文件大小（过大可能有问题）
                if len(content) > 500000:
                    issues.append({
                        'issue_type': 'rules_file_large',
                        'severity': 'medium',
                        'file_path': fpath,
                        'line_number': 0,
                        'error_message': f'规则文件过大: {len(content)/1024:.1f}KB',
                        'error_code': 'RULES_FILE_LARGE',
                        'confidence': 0.7,
                    })
            
            except Exception as e:
                issues.append({
                    'issue_type': 'rules_file_read_error',
                    'severity': 'medium',
                    'file_path': fpath,
                    'line_number': 0,
                    'error_message': f'规则文件读取错误: {fname} - {str(e)[:50]}',
                    'error_code': 'RULES_FILE_READ_ERROR',
                    'confidence': 0.6,
                })
        
        # 4. 检查规则文件版本一致性
        versions = {}
        for fname in required_files:
            fpath = os.path.join(rules_dir, fname)
            if not os.path.exists(fpath):
                continue
            try:
                with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                version_match = re.search(r'(规则版本|规范版本).*?v?([\d.]+)', content)
                if version_match:
                    versions[fname] = version_match.group(2)
            except Exception:
                pass
        
        if versions and len(set(versions.values())) > 1:
            version_str = ', '.join([f'{k}: v{v}' for k, v in versions.items()])
            issues.append({
                'issue_type': 'rules_version_mismatch',
                'severity': 'medium',
                'file_path': rules_dir,
                'line_number': 0,
                'error_message': f'规则文件版本不一致: {version_str}',
                'error_code': 'RULES_VERSION_MISMATCH',
                'confidence': 0.8,
            })
        
        return issues

    def _auto_update_rules(self) -> Dict[str, Any]:
        """自动更新法律准则文件（版本同步、格式修复）"""
        result = {
            'updated_count': 0,
            'updated_files': [],
            'errors': [],
        }
        
        rules_dirs = [
            os.path.join(_PROJECT_ROOT, '.trae', 'rules'),
            os.path.join(_PROJECT_ROOT, 'wuchenghao15', '.trae', 'rules'),
        ]
        
        all_rules_dir = None
        for rd in rules_dirs:
            if os.path.isdir(rd):
                all_rules_dir = rd
                break
        
        if not all_rules_dir:
            return result
        
        rules_dir = all_rules_dir
        
        # 检查并修复元数据
        required_files = [
            'AI系统操作规范.md',
            '开发规则.md',
            '源码修改准则参考与思路方案.md',
            '系统操作规范.md',
        ]
        
        for fname in required_files:
            fpath = os.path.join(rules_dir, fname)
            if not os.path.exists(fpath):
                continue
            
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                needs_update = False
                new_content = content
                
                # 添加缺失的元数据
                if 'alwaysApply:' not in content:
                    front_matter = '---\nalwaysApply: true\n---\n'
                    if content.startswith('#'):
                        new_content = front_matter + content
                    else:
                        new_content = front_matter + '\n' + content
                    needs_update = True
                
                # 添加缺失的版本信息
                if '规则版本' not in content:
                    new_content = new_content + '\n\n---\n\n**规则版本**：v1.0\n**生效日期**：' + datetime.now().strftime('%Y-%m-%d')
                    needs_update = True
                
                if needs_update:
                    with open(fpath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    result['updated_count'] += 1
                    result['updated_files'].append(fname)
                    _logger.info(f'已更新规则文件: {fname}')
            
            except Exception as e:
                result['errors'].append(f'更新失败 {fname}: {e}')
        
        return result

    # ============== 1.75. 根目录整理巡检 ==============

    def _scan_root_directory_organization(self) -> List[Dict]:
        """检查根目录文件组织情况"""
        issues = []
        
        debug_count = len([f for f in os.listdir(_PROJECT_ROOT) 
                          if f.startswith('_') and f.endswith('.py')])
        fix_count = len([f for f in os.listdir(_PROJECT_ROOT) 
                         if f.startswith('fix_') and f.endswith('.py')])
        db_count = len([f for f in os.listdir(_PROJECT_ROOT) 
                       if f.endswith('.db') and not os.path.islink(os.path.join(_PROJECT_ROOT, f))])
        log_count = len([f for f in os.listdir(_PROJECT_ROOT) if f.endswith('.log')])
        temp_file_count = len([f for f in os.listdir(_PROJECT_ROOT) 
                              if f.endswith('.tmp') or f.endswith('.chk')])
        json_count = len([f for f in os.listdir(_PROJECT_ROOT) if f.endswith('.json')])
        
        if debug_count > 0:
            issues.append({
                'issue_type': 'root_debug_scripts',
                'severity': 'low',
                'file_path': _PROJECT_ROOT,
                'line_number': 0,
                'error_message': f'根目录有{debug_count}个调试脚本（_开头），建议整理到scripts/debug/',
                'error_code': 'ROOT_DEBUG_SCRIPTS',
                'confidence': 0.9,
            })
        
        if fix_count > 0:
            issues.append({
                'issue_type': 'root_fix_scripts',
                'severity': 'low',
                'file_path': _PROJECT_ROOT,
                'line_number': 0,
                'error_message': f'根目录有{fix_count}个修复脚本（fix_开头），建议整理到scripts/fix/',
                'error_code': 'ROOT_FIX_SCRIPTS',
                'confidence': 0.9,
            })
        
        if db_count > 0:
            issues.append({
                'issue_type': 'root_db_files',
                'severity': 'medium',
                'file_path': _PROJECT_ROOT,
                'line_number': 0,
                'error_message': f'根目录有{db_count}个数据库文件，建议整理到data/databases/',
                'error_code': 'ROOT_DB_FILES',
                'confidence': 0.8,
            })
        
        if log_count > 0:
            issues.append({
                'issue_type': 'root_log_files',
                'severity': 'low',
                'file_path': _PROJECT_ROOT,
                'line_number': 0,
                'error_message': f'根目录有{log_count}个日志文件，建议整理到logs/',
                'error_code': 'ROOT_LOG_FILES',
                'confidence': 0.8,
            })
        
        if temp_file_count > 0:
            issues.append({
                'issue_type': 'root_temp_files',
                'severity': 'medium',
                'file_path': _PROJECT_ROOT,
                'line_number': 0,
                'error_message': f'根目录有{temp_file_count}个临时文件（.tmp/.chk），建议删除',
                'error_code': 'ROOT_TEMP_FILES',
                'confidence': 0.9,
            })
        
        if json_count > 0:
            issues.append({
                'issue_type': 'root_json_files',
                'severity': 'low',
                'file_path': _PROJECT_ROOT,
                'line_number': 0,
                'error_message': f'根目录有{json_count}个JSON文件，建议同步到数据库',
                'error_code': 'ROOT_JSON_FILES',
                'confidence': 0.7,
            })
        
        temp_dirs = [d for d in ['.tmp', '.sync_temp_dir'] if os.path.isdir(os.path.join(_PROJECT_ROOT, d))]
        if temp_dirs:
            issues.append({
                'issue_type': 'root_temp_dirs',
                'severity': 'low',
                'file_path': _PROJECT_ROOT,
                'line_number': 0,
                'error_message': f'根目录有临时目录: {", ".join(temp_dirs)}',
                'error_code': 'ROOT_TEMP_DIRS',
                'confidence': 0.7,
            })
        
        empty_dirs = [d for d in ['Backups', 'ISO_Images', 'archive'] 
                     if os.path.isdir(os.path.join(_PROJECT_ROOT, d)) and not os.listdir(os.path.join(_PROJECT_ROOT, d))]
        if empty_dirs:
            issues.append({
                'issue_type': 'root_empty_dirs',
                'severity': 'low',
                'file_path': _PROJECT_ROOT,
                'line_number': 0,
                'error_message': f'根目录有空目录: {", ".join(empty_dirs)}',
                'error_code': 'ROOT_EMPTY_DIRS',
                'confidence': 0.8,
            })
        
        return issues

    def _auto_organize_root_files(self) -> Dict[str, Any]:
        """自动整理根目录文件"""
        result = {
            'organized_count': 0,
            'cleaned_count': 0,
            'removed_count': 0,
            'sync_count': 0,
            'organized_files': [],
            'cleaned_files': [],
            'removed_dirs': [],
            'synced_files': [],
            'errors': [],
        }
        
        import shutil
        
        os.makedirs(os.path.join(_PROJECT_ROOT, 'scripts/debug'), exist_ok=True)
        os.makedirs(os.path.join(_PROJECT_ROOT, 'scripts/fix'), exist_ok=True)
        os.makedirs(os.path.join(_PROJECT_ROOT, 'data/databases'), exist_ok=True)
        os.makedirs(os.path.join(_PROJECT_ROOT, 'logs'), exist_ok=True)
        
        # 整理调试脚本
        debug_scripts = sorted([f for f in os.listdir(_PROJECT_ROOT) 
                               if f.startswith('_') and f.endswith('.py')])
        for fname in debug_scripts:
            src = os.path.join(_PROJECT_ROOT, fname)
            dst = os.path.join(_PROJECT_ROOT, 'scripts/debug', fname)
            if os.path.exists(dst):
                fname_no_ext = os.path.splitext(fname)[0]
                dst = os.path.join(_PROJECT_ROOT, 'scripts/debug', f'{fname_no_ext}_{int(time.time())}.py')
            try:
                shutil.move(src, dst)
                result['organized_count'] += 1
                result['organized_files'].append(f'{fname} -> scripts/debug/')
                _logger.info(f'已整理: {fname} -> scripts/debug/')
            except Exception as e:
                result['errors'].append(f'整理失败 {fname}: {e}')
        
        # 整理fix脚本
        fix_scripts = sorted([f for f in os.listdir(_PROJECT_ROOT) 
                             if f.startswith('fix_') and f.endswith('.py')])
        for fname in fix_scripts:
            src = os.path.join(_PROJECT_ROOT, fname)
            dst = os.path.join(_PROJECT_ROOT, 'scripts/fix', fname)
            if os.path.exists(dst):
                fname_no_ext = os.path.splitext(fname)[0]
                dst = os.path.join(_PROJECT_ROOT, 'scripts/fix', f'{fname_no_ext}_{int(time.time())}.py')
            try:
                shutil.move(src, dst)
                result['organized_count'] += 1
                result['organized_files'].append(f'{fname} -> scripts/fix/')
                _logger.info(f'已整理: {fname} -> scripts/fix/')
            except Exception as e:
                result['errors'].append(f'整理失败 {fname}: {e}')
        
        # 整理数据库文件（排除符号链接）
        db_files = sorted([f for f in os.listdir(_PROJECT_ROOT) 
                          if f.endswith('.db') and not os.path.islink(os.path.join(_PROJECT_ROOT, f))])
        for fname in db_files:
            src = os.path.join(_PROJECT_ROOT, fname)
            dst = os.path.join(_PROJECT_ROOT, 'data/databases', fname)
            if os.path.exists(dst):
                fname_no_ext = os.path.splitext(fname)[0]
                dst = os.path.join(_PROJECT_ROOT, 'data/databases', f'{fname_no_ext}_{int(time.time())}.db')
            try:
                shutil.move(src, dst)
                result['organized_count'] += 1
                result['organized_files'].append(f'{fname} -> data/databases/')
                _logger.info(f'已整理: {fname} -> data/databases/')
            except Exception as e:
                result['errors'].append(f'整理失败 {fname}: {e}')
        
        # 整理日志文件
        log_files = sorted([f for f in os.listdir(_PROJECT_ROOT) if f.endswith('.log')])
        for fname in log_files:
            src = os.path.join(_PROJECT_ROOT, fname)
            dst = os.path.join(_PROJECT_ROOT, 'logs', fname)
            if os.path.exists(dst):
                fname_no_ext = os.path.splitext(fname)[0]
                dst = os.path.join(_PROJECT_ROOT, 'logs', f'{fname_no_ext}_{int(time.time())}.log')
            try:
                shutil.move(src, dst)
                result['organized_count'] += 1
                result['organized_files'].append(f'{fname} -> logs/')
                _logger.info(f'已整理: {fname} -> logs/')
            except Exception as e:
                result['errors'].append(f'整理失败 {fname}: {e}')
        
        # 清理临时文件（.tmp, .chk）
        temp_files = sorted([f for f in os.listdir(_PROJECT_ROOT) 
                            if f.endswith('.tmp') or f.endswith('.chk')])
        for fname in temp_files:
            fpath = os.path.join(_PROJECT_ROOT, fname)
            try:
                os.remove(fpath)
                result['cleaned_count'] += 1
                result['cleaned_files'].append(fname)
                _logger.info(f'已删除临时文件: {fname}')
            except Exception as e:
                result['errors'].append(f'删除失败 {fname}: {e}')
        
        # 清理临时目录
        temp_dirs = ['.tmp', '.sync_temp_dir']
        for dname in temp_dirs:
            dpath = os.path.join(_PROJECT_ROOT, dname)
            if os.path.isdir(dpath):
                try:
                    shutil.rmtree(dpath)
                    result['cleaned_count'] += 1
                    result['cleaned_files'].append(dname)
                    _logger.info(f'已删除临时目录: {dname}')
                except Exception as e:
                    result['errors'].append(f'删除失败 {dname}: {e}')
        
        # 清理空目录
        empty_dir_candidates = ['Backups', 'ISO_Images', 'archive']
        for dname in empty_dir_candidates:
            dpath = os.path.join(_PROJECT_ROOT, dname)
            if os.path.isdir(dpath):
                if not os.listdir(dpath):
                    try:
                        os.rmdir(dpath)
                        result['removed_count'] += 1
                        result['removed_dirs'].append(dname)
                        _logger.info(f'已删除空目录: {dname}')
                    except Exception as e:
                        result['errors'].append(f'删除失败 {dname}: {e}')
        
        # 同步JSON数据到数据库
        json_result = self._sync_json_to_database()
        result['sync_count'] += json_result['synced_count']
        result['synced_files'].extend(json_result['synced_files'])
        result['errors'].extend(json_result['errors'])
        
        return result

    def _sync_json_to_database(self) -> Dict[str, Any]:
        """自动上传同步JSON数据到数据库"""
        result = {
            'synced_count': 0,
            'synced_files': [],
            'errors': [],
        }
        
        import json
        import sqlite3
        
        json_files = sorted([f for f in os.listdir(_PROJECT_ROOT) if f.endswith('.json')])
        
        db_path = os.path.join(_PROJECT_ROOT, 'data/databases', 'app.db')
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS json_sync_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_name TEXT NOT NULL,
                    file_path TEXT,
                    record_count INTEGER DEFAULT 0,
                    sync_time TEXT DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending'
                )
            ''')
            conn.commit()
        except Exception as e:
            result['errors'].append(f'初始化数据库失败: {e}')
            return result
        
        for fname in json_files:
            fpath = os.path.join(_PROJECT_ROOT, fname)
            
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                record_count = len(data) if isinstance(data, list) else 1
                
                cursor.execute('''
                    INSERT INTO json_sync_logs (file_name, file_path, record_count, sync_time, status)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
                ''', (fname, fpath, record_count, 'success'))
                conn.commit()
                
                result['synced_count'] += 1
                result['synced_files'].append(f'{fname} (记录数: {record_count})')
                _logger.info(f'已同步JSON: {fname}')
            except Exception as e:
                result['errors'].append(f'同步失败 {fname}: {e}')
        
        conn.close()
        return result

    # ============== 2. 语法错误巡检 ==============

    def _scan_syntax_errors(self) -> Tuple[List[Dict], int]:
        """扫描各类文件的语法错误"""
        issues = []
        file_count = 0
        skip_dirs = {'__pycache__', '.git', 'node_modules', 'venv', '.venv', 'flask-app-old', 'logs', 'data',
                     'cross_platform_node_modules', 'static', 'dist', 'build'}

        for root, dirs, files in os.walk(_PROJECT_ROOT):
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]

            for fname in files:
                fpath = os.path.join(root, fname)

                # Python 文件
                if fname.endswith('.py'):
                    file_count += 1
                    issue = self._check_python_syntax(fpath)
                    if issue:
                        issues.append(issue)

                # JSON 文件
                elif fname.endswith('.json'):
                    file_count += 1
                    issue = self._check_json_syntax(fpath)
                    if issue:
                        issues.append(issue)

                # HTML 文件 - 模板文件
                elif fname.endswith('.html'):
                    file_count += 1
                    issue = self._check_html_basic(fpath)
                    if issue:
                        issues.append(issue)

                # JS 文件 - 跳过打包/压缩/第三方文件
                elif fname.endswith('.js'):
                    # 跳过打包文件、minified文件、第三方库
                    if re.search(r'(\.min\.js|-[a-f0-9]{8,}\.js|index-\w+\.js)', fname):
                        file_count += 1
                        continue
                    # 跳过大文件（> 500KB）
                    try:
                        if os.path.getsize(fpath) > 500 * 1024:
                            file_count += 1
                            continue
                    except Exception:
                        pass
                    file_count += 1
                    issue = self._check_js_basic(fpath)
                    if issue:
                        issues.append(issue)

                # CSS 文件
                elif fname.endswith('.css'):
                    # 跳过minified CSS
                    if fname.endswith('.min.css'):
                        file_count += 1
                        continue
                    file_count += 1
                    issue = self._check_css_basic(fpath)
                    if issue:
                        issues.append(issue)

        # 扫描IDE诊断结果（basedpyright错误）
        ide_issues = self._scan_ide_diagnostics()
        issues.extend(ide_issues)

        return issues, file_count

    def _scan_ide_diagnostics(self) -> List[Dict]:
        """扫描IDE诊断结果（basedpyright错误）"""
        issues = []
        
        try:
            import subprocess
            import json
            
            # 只扫描核心目录下的Python文件
            core_dirs = [
                os.path.join(_PROJECT_ROOT, 'ai_engines'),
                os.path.join(_PROJECT_ROOT, 'core'),
                os.path.join(_PROJECT_ROOT, 'app'),
                os.path.join(_PROJECT_ROOT, 'flask-app'),
            ]
            
            py_files = []
            for dir_path in core_dirs:
                if not os.path.isdir(dir_path):
                    continue
                for root, dirs, files in os.walk(dir_path):
                    dirs[:] = [d for d in dirs if d not in {'__pycache__', 'node_modules', 'exam_app_node_modules'}]
                    for fname in files:
                        if fname.endswith('.py'):
                            py_files.append(os.path.join(root, fname))
            
            # 限制扫描文件数量
            py_files = py_files[:50]
            
            # 逐个文件扫描
            for fpath in py_files:
                try:
                    result = subprocess.run(
                        ['npx', 'basedpyright', '--outputjson', fpath],
                        cwd=_PROJECT_ROOT,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.stdout:
                        try:
                            data = json.loads(result.stdout)
                            
                            for diag in data.get('generalDiagnostics', []):
                                file_path = diag.get('file', '')
                                if not file_path.startswith('file://'):
                                    file_path = 'file://' + file_path
                                
                                local_path = file_path.replace('file://', '')
                                
                                message = diag.get('message', '')
                                severity = diag.get('severity', 'error')
                                line = diag.get('range', {}).get('start', {}).get('line', 0)
                                code = diag.get('code', '')
                                rule = diag.get('rule', '')
                                
                                # 跳过第三方库导入问题（这些不是代码错误）
                                if '无法从源码解析导入' in message or 'reportMissingModuleSource' == rule:
                                    continue
                                
                                severity_map = {'error': 'high', 'warning': 'medium', 'information': 'low', 'hint': 'low'}
                                severity_level = severity_map.get(severity.lower(), 'medium')
                                
                                issues.append({
                                    'issue_type': 'ide_diagnostic',
                                    'severity': severity_level,
                                    'file_path': local_path,
                                    'line_number': line + 1,
                                    'error_message': message,
                                    'error_code': code,
                                    'confidence': 0.9
                                })
                        
                        except json.JSONDecodeError:
                            pass
                except subprocess.TimeoutExpired:
                    continue
                except Exception:
                    continue
        
        except Exception as e:
            _logger.warning(f"basedpyright扫描失败: {e}")
        
        return issues

    def _check_python_syntax(self, fpath: str) -> Optional[Dict]:
        """检测Python语法错误"""
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                source = f.read()
            ast.parse(source, filename=fpath)
            return None
        except SyntaxError as e:
            return {
                'issue_type': 'python_syntax_error',
                'severity': 'high',
                'file_path': fpath,
                'line_number': e.lineno or 0,
                'error_message': str(e.msg),
                'error_code': f'SYNTAX_{type(e).__name__}',
                'confidence': 1.0,
            }
        except Exception as e:
            return {
                'issue_type': 'python_parse_error',
                'severity': 'medium',
                'file_path': fpath,
                'line_number': 0,
                'error_message': str(e),
                'error_code': 'PARSE_ERROR',
                'confidence': 0.8,
            }

    def _check_json_syntax(self, fpath: str) -> Optional[Dict]:
        """检测JSON语法错误"""
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                json.load(f)
            return None
        except json.JSONDecodeError as e:
            return {
                'issue_type': 'json_syntax_error',
                'severity': 'high',
                'file_path': fpath,
                'line_number': e.lineno,
                'error_message': e.msg,
                'error_code': 'JSON_DECODE_ERROR',
                'confidence': 1.0,
            }
        except Exception:
            return None

    def _check_html_basic(self, fpath: str) -> Optional[Dict]:
        """HTML全面检测 - 结构、内联CSS、内联JS等"""
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception:
            return None

        all_issues = []
        
        is_template = bool(re.search(r'{%\s*(if|for|set|include|extends|macro)', content) or '{{' in content)
        conf_mult = 0.4 if is_template else 1.0
        
        # 1. 常见标签平衡检测（排除自闭合标签）
        self_closing_tags = {'input', 'br', 'img', 'meta', 'link', 'hr', 'area', 'base', 'col', 
                            'embed', 'keygen', 'param', 'source', 'track', 'wbr', '!DOCTYPE'}
        tags_to_check = ['div', 'span', 'p', 'ul', 'ol', 'li', 'table', 'tr', 'td', 'th',
                        'a', 'button', 'form', 'label', 'section', 'article',
                        'header', 'footer', 'nav', 'main', 'aside', 'select', 'option',
                        'textarea', 'script', 'style', 'head', 'body', 'html']
        
        tag_issues = []
        for tag in tags_to_check:
            open_count = len(re.findall(rf'<{tag}\b', content, re.IGNORECASE))
            close_count = len(re.findall(rf'</{tag}>', content, re.IGNORECASE))
            if open_count != close_count and abs(open_count - close_count) > 2:
                tag_issues.append(f'{tag}标签不平衡({open_count}/{close_count})')
        
        if tag_issues:
            all_issues.append({
                'code': 'HTML_TAG_MISMATCH',
                'msg': '; '.join(tag_issues[:3]),
                'severity': 'low',
                'confidence': 0.3 * conf_mult,
            })
        
        # 2. 内联CSS检测 (style属性)
        inline_styles = re.findall(r'style\s*=\s*["\']([^"\']+)["\']', content, re.IGNORECASE)
        css_issues_count = 0
        for style in inline_styles[:50]:
            props = [p.strip() for p in style.split(';') if p.strip()]
            for prop in props:
                if ':' not in prop:
                    css_issues_count += 1
                    break
                # 检查属性值是否为空
                key_val = prop.split(':', 1)
                if len(key_val) == 2 and not key_val[1].strip():
                    css_issues_count += 1
                    break
        
        if css_issues_count > 0:
            all_issues.append({
                'code': 'INLINE_CSS_WARN',
                'msg': f'发现{css_issues_count}处内联CSS可能有问题',
                'severity': 'low',
                'confidence': 0.3 * conf_mult,
            })
        
        # 3. <style>标签内CSS检测
        style_blocks = re.findall(r'<style[^>]*>(.*?)</style>', content, re.DOTALL | re.IGNORECASE)
        for i, style_content in enumerate(style_blocks):
            clean_css = style_content
            if is_template:
                clean_css = CSSFixer._strip_template_syntax(style_content)
            open_b = clean_css.count('{')
            close_b = clean_css.count('}')
            if open_b != close_b and abs(open_b - close_b) > 1:
                all_issues.append({
                    'code': 'STYLE_BLOCK_CSS',
                    'msg': f'第{i+1}个style块大括号不平衡({open_b}/{close_b})',
                    'severity': 'medium',
                    'confidence': 0.5 * conf_mult,
                })
        
        # 4. <script>标签检测
        script_blocks = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL | re.IGNORECASE)
        for i, script_content in enumerate(script_blocks):
            if script_content.strip() == '':
                continue
            clean_js = script_content
            if is_template:
                clean_js = re.sub(r'{%.*?%}', '', clean_js, flags=re.DOTALL)
                clean_js = re.sub(r'{{.*?}}', '""', clean_js)
            # 括号平衡
            for open_c, close_c, name in [('{', '}', '大括号'), ('(', ')', '圆括号'), ('[', ']', '方括号')]:
                open_count = clean_js.count(open_c)
                close_count = clean_js.count(close_c)
                if open_count != close_count and abs(open_count - close_count) > 2:
                    all_issues.append({
                        'code': 'SCRIPT_BRACKET',
                        'msg': f'第{i+1}个script块{name}不平衡({open_count}/{close_count})',
                        'severity': 'medium',
                        'confidence': 0.4 * conf_mult,
                    })
                    break
        
        # 5. 内联style包含模板语法检测（IDE CSS报错的常见原因）
        inline_style_templates = re.findall(r'style\s*=\s*["\']([^"\']*)\{%[^"\']*["\']', content, re.IGNORECASE)
        if inline_style_templates:
            all_issues.append({
                'code': 'INLINE_STYLE_TEMPLATE',
                'msg': f'发现{len(inline_style_templates)}处内联style包含模板语法（可能导致IDE CSS报错）',
                'severity': 'low',
                'confidence': 0.8 * conf_mult,
            })
        
        if all_issues:
            # 按置信度排序，取最高的
            all_issues.sort(key=lambda x: x['confidence'], reverse=True)
            top_issue = all_issues[0]
            return {
                'issue_type': 'html_structure_warning',
                'severity': top_issue['severity'],
                'file_path': fpath,
                'line_number': 0,
                'error_message': top_issue['msg'],
                'error_code': top_issue['code'],
                'confidence': top_issue['confidence'],
                '_all_html_issues': all_issues,
            }
        return None

    def _check_js_basic(self, fpath: str) -> Optional[Dict]:
        """JS增强检测 - 括号平衡、常见语法问题"""
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception:
            return None

        issues = []
        
        # 1. 括号平衡检查
        bracket_issues = []
        for open_char, close_char, name in [('{', '}', '大括号'), ('(', ')', '圆括号'), ('[', ']', '方括号')]:
            open_count = content.count(open_char)
            close_count = content.count(close_char)
            if open_count != close_count:
                bracket_issues.append(f'{name}不平衡: 开{open_count} 闭{close_count}')
        
        if bracket_issues:
            issues.append({
                'code': 'JS_BRACKET_MISMATCH',
                'msg': '; '.join(bracket_issues),
                'severity': 'medium',
                'confidence': 0.5,
            })
        
        # 2. 检测常见JS错误模式
        lines = content.split('\n')
        error_patterns = [
            (r'function\s+\w*\s*\([^)]*\)\s*\{[^}]*$', '函数可能缺少闭合括号', 'low', 0.3),
            (r'if\s*\([^)]*\)\s*\{[^}]*$', 'if语句可能缺少闭合括号', 'low', 0.3),
            (r'for\s*\([^)]*\)\s*\{[^}]*$', 'for循环可能缺少闭合括号', 'low', 0.3),
            (r'=\s*[{\[\(]\s*$', '赋值表达式可能缺少闭合', 'low', 0.25),
        ]
        
        pattern_issues = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('//') or stripped.startswith('*') or stripped == '':
                continue
            for pattern, desc, sev, conf in error_patterns:
                if re.search(pattern, stripped):
                    pattern_issues += 1
                    break
            if pattern_issues >= 5:
                break
        
        if pattern_issues > 0:
            issues.append({
                'code': 'JS_PATTERN_WARN',
                'msg': f'发现{pattern_issues}处可能的语法问题',
                'severity': 'low',
                'confidence': 0.3,
            })
        
        if issues:
            issues.sort(key=lambda x: x['confidence'], reverse=True)
            top = issues[0]
            return {
                'issue_type': 'js_syntax_warning',
                'severity': top['severity'],
                'file_path': fpath,
                'line_number': 0,
                'error_message': top['msg'],
                'error_code': top['code'],
                'confidence': top['confidence'],
                '_all_js_issues': issues,
            }
        return None

    def _check_css_basic(self, fpath: str) -> Optional[Dict]:
        """CSS语法检测 - 使用专业CSS修复器"""
        return CSSFixer.check_css_syntax(fpath)

    # ============== 3. 运行时错误巡检 ==============

    def _scan_runtime_errors(self) -> List[Dict]:
        """扫描日志和数据库中的运行时错误"""
        issues = []
        log_files = [
            _LOG_PATH,
            os.path.join(_PROJECT_ROOT, 'logs', 'error.log'),
            os.path.join(_PROJECT_ROOT, 'logs', 'app.log'),
        ]

        for log_file in log_files:
            if not os.path.exists(log_file):
                continue
            try:
                with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()[-300:]

                error_patterns = [
                    (r'ERROR.*?(.*?Error.*?:.*)', 'high'),
                    (r'Exception.*?:.*', 'high'),
                    (r'Traceback.*?\(most recent call last\)', 'critical'),
                    (r'CRITICAL.*', 'critical'),
                    (r'FATAL.*', 'critical'),
                ]

                seen = set()
                for line in lines:
                    for pattern, severity in error_patterns:
                        m = re.search(pattern, line)
                        if m:
                            msg = m.group(0)[:200]
                            msg_hash = hashlib.md5(msg[:80].encode('utf-8')).hexdigest()
                            if msg_hash not in seen:
                                seen.add(msg_hash)
                                issues.append({
                                    'issue_type': 'runtime_error',
                                    'severity': severity,
                                    'file_path': log_file,
                                    'line_number': 0,
                                    'error_message': msg,
                                    'error_code': 'RUNTIME_ERROR',
                                    'confidence': 0.9,
                                })
            except Exception:
                pass

        # 从数据库读取未修复的控制台错误
        try:
            with _get_conn() as conn:
                c = conn.cursor()
                c.execute(
                    """SELECT * FROM ai_inspection_console_errors 
                       WHERE fixed=0 ORDER BY reported_at DESC LIMIT 10"""
                )
                for row in c.fetchall():
                    issues.append({
                        'issue_type': 'console_error',
                        'severity': 'medium',
                        'file_path': row['file_path'] or row['url'],
                        'line_number': row['line_number'] or 0,
                        'error_message': row['error_message'][:200],
                        'error_code': f'CONSOLE_{row["error_type"]}',
                        'confidence': 0.85,
                    })
        except Exception:
            pass

        return issues[:30]

    # ============== 4. 自动修复 ==============

    def _auto_fix_issues(self, run_id: str, issues: List[Dict]) -> Tuple[int, int]:
        """自动修复问题，返回(成功数, 失败数)"""
        fixed = 0
        failed = 0

        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        sorted_issues = sorted(issues, key=lambda x: severity_order.get(x.get('severity', 'low'), 9))

        for issue in sorted_issues:
            issue_type = issue.get('issue_type', '')

            # Python语法错误 - 使用专业修复器
            if issue_type == 'python_syntax_error' and issue.get('confidence', 0) >= 0.9:
                success = self._fix_python_syntax(issue)
                if success:
                    fixed += 1
                    self._mark_fixed(issue, issue.get('fix_method', 'auto_python_fix'), 'success')
                else:
                    failed += 1
                    self._mark_fixed(issue, 'auto_python_fix', 'failed')

            # 临时文件清理
            elif issue_type == 'temp_file':
                try:
                    os.remove(issue['file_path'])
                    fixed += 1
                    self._mark_fixed(issue, 'deleted_temp_file', 'success')
                except Exception:
                    failed += 1
                    self._mark_fixed(issue, 'delete_temp_failed', 'failed')

            # JSON语法错误 - 尝试修复
            elif issue_type == 'json_syntax_error':
                success = self._fix_json_syntax(issue)
                if success:
                    fixed += 1
                    self._mark_fixed(issue, 'auto_json_fix', 'success')
                else:
                    failed += 1
                    self._mark_fixed(issue, 'auto_json_fix', 'failed')

            # CSS语法错误 - 使用专业修复器
            elif issue_type == 'css_syntax_error' and issue.get('confidence', 0) >= 0.5:
                success = self._fix_css_syntax(issue)
                if success:
                    fixed += 1
                    self._mark_fixed(issue, issue.get('fix_method', 'auto_css_fix'), 'success')
                else:
                    failed += 1
                    self._mark_fixed(issue, 'auto_css_fix', 'failed')

            # JS语法警告 - 使用JS修复器
            elif issue_type == 'js_syntax_warning' and issue.get('confidence', 0) >= 0.4:
                success = self._fix_js_syntax(issue)
                if success:
                    fixed += 1
                    self._mark_fixed(issue, issue.get('fix_method', 'auto_js_fix'), 'success')
                else:
                    failed += 1
                    self._mark_fixed(issue, 'auto_js_fix', 'failed')

            # HTML结构警告 - 使用HTML修复器
            elif issue_type == 'html_structure_warning' and issue.get('confidence', 0) >= 0.4:
                success = self._fix_html_structure(issue)
                if success:
                    fixed += 1
                    self._mark_fixed(issue, issue.get('fix_method', 'auto_html_fix'), 'success')
                else:
                    failed += 1
                    self._mark_fixed(issue, 'auto_html_fix', 'failed')

            # 其他类型跳过
            else:
                failed += 1
                self._mark_fixed(issue, 'no_fix_method', 'skipped')

        return fixed, failed

    def _fix_python_syntax(self, issue: Dict) -> bool:
        """尝试修复Python语法错误"""
        fpath = issue.get('file_path', '')
        if not fpath or not os.path.exists(fpath):
            return False

        error_msg = issue.get('error_message', '')
        error_line = issue.get('line_number', 0)

        # 先备份
        try:
            backup_path = fpath + '.inspect_bak'
            if not os.path.exists(backup_path):
                import shutil
                shutil.copy2(fpath, backup_path)
        except Exception:
            pass

        # 使用专业修复器
        try:
            success, method = PythonSyntaxFixer.fix_file(fpath, error_msg, error_line)
            if success:
                issue['fix_method'] = method
                return True
        except Exception:
            pass

        return False

    def _fix_json_syntax(self, issue: Dict) -> bool:
        """尝试修复JSON语法错误"""
        fpath = issue.get('file_path', '')
        if not fpath or not os.path.exists(fpath):
            return False

        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

            # 尝试常见修复
            fixed_content = content

            # 移除尾部逗号
            fixed_content = re.sub(r',\s*([}\]])', r'\1', fixed_content)

            # 替换单引号为双引号（简单处理）
            # 只替换键的单引号，避免替换值中的单引号
            fixed_content = re.sub(r"'([^']+)'\s*:", r'"\1":', fixed_content)

            try:
                json.loads(fixed_content)
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                return True
            except json.JSONDecodeError:
                pass

        except Exception:
            pass

        return False

    def _fix_css_syntax(self, issue: Dict) -> bool:
        """尝试修复CSS语法错误"""
        fpath = issue.get('file_path', '')
        if not fpath or not os.path.exists(fpath):
            return False

        # 先备份
        try:
            backup_path = fpath + '.inspect_bak'
            if not os.path.exists(backup_path):
                import shutil
                shutil.copy2(fpath, backup_path)
        except Exception:
            pass

        # 使用专业修复器
        try:
            error_msg = issue.get('error_message', '')
            error_code = issue.get('error_code', '')
            success, method = CSSFixer.fix_file(fpath, error_msg, error_code)
            if success:
                issue['fix_method'] = method
                return True
        except Exception:
            pass

        return False

    def _fix_js_syntax(self, issue: Dict) -> bool:
        """尝试修复JS语法问题"""
        fpath = issue.get('file_path', '')
        if not fpath or not os.path.exists(fpath):
            return False

        try:
            backup_path = fpath + '.inspect_bak'
            if not os.path.exists(backup_path):
                import shutil
                shutil.copy2(fpath, backup_path)
        except Exception:
            pass

        try:
            error_msg = issue.get('error_message', '')
            error_code = issue.get('error_code', '')
            success, method = JSFixer.fix_file(fpath, error_msg, error_code)
            if success:
                issue['fix_method'] = method
                return True
        except Exception:
            pass

        return False

    def _fix_html_structure(self, issue: Dict) -> bool:
        """尝试修复HTML结构问题"""
        fpath = issue.get('file_path', '')
        if not fpath or not os.path.exists(fpath):
            return False

        try:
            backup_path = fpath + '.inspect_bak'
            if not os.path.exists(backup_path):
                import shutil
                shutil.copy2(fpath, backup_path)
        except Exception:
            pass

        try:
            error_msg = issue.get('error_message', '')
            error_code = issue.get('error_code', '')
            success, method = HTMLFixer.fix_file(fpath, error_msg, error_code)
            if success:
                issue['fix_method'] = method
                return True
        except Exception:
            pass

        return False

    def _mark_fixed(self, issue: Dict, method: str, result: str):
        """更新问题修复状态"""
        try:
            with _get_conn() as conn:
                conn.execute(
                    """UPDATE ai_inspection_issues 
                       SET fixed=?, fix_method=?, fix_result=?, fixed_at=?
                       WHERE file_path=? AND error_code=? AND fixed=0
                       ORDER BY id DESC LIMIT 1""",
                    (1 if result == 'success' else 0, method, result,
                     datetime.now().isoformat(),
                     issue.get('file_path', ''), issue.get('error_code', ''))
                )
                conn.commit()
        except Exception:
            pass

    # ============== 5. 数据库上报 ==============

    def _bulk_insert_issues(self, run_id: str, issues: List[Dict]):
        """批量插入问题记录"""
        if not issues:
            return
        try:
            with _get_conn() as conn:
                c = conn.cursor()
                now = datetime.now().isoformat()
                for issue in issues:
                    c.execute(
                        """INSERT INTO ai_inspection_issues 
                           (run_id, issue_type, severity, file_path, line_number,
                            error_message, error_code, confidence, detected_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (run_id,
                         issue.get('issue_type', 'unknown'),
                         issue.get('severity', 'low'),
                         issue.get('file_path', ''),
                         issue.get('line_number', 0),
                         issue.get('error_message', '')[:500],
                         issue.get('error_code', ''),
                         issue.get('confidence', 0.0),
                         now)
                    )
                conn.commit()
        except Exception as e:
            _logger.error(f"批量插入问题失败: {e}")

    # ============== 7. AI自学习升级 ==============

    def _learn_from_fixes(self, run_id: str) -> int:
        """从修复案例中学习，更新知识库"""
        gained = 0
        try:
            with _get_conn() as conn:
                c = conn.cursor()
                c.execute(
                    """SELECT issue_type, error_code, error_message, fix_method 
                       FROM ai_inspection_issues 
                       WHERE run_id=? AND fixed=1 AND fix_result='success'""",
                    (run_id,)
                )
                rows = c.fetchall()

                for row in rows:
                    err_type = row['issue_type']
                    err_code = row['error_code']
                    err_msg = row['error_message'][:100]
                    fix_method = row['fix_method']

                    pattern_hash = f"{err_type}:{err_code}:{err_msg[:50]}"
                    pattern_hash = hashlib.md5(pattern_hash.encode('utf-8')).hexdigest()

                    c.execute("SELECT id, success_count, fail_count FROM ai_inspection_knowledge WHERE pattern_hash=?",
                              (pattern_hash,))
                    existing = c.fetchone()

                    now = datetime.now().isoformat()
                    if existing:
                        new_success = existing['success_count'] + 1
                        total = new_success + existing['fail_count']
                        new_rate = new_success / total if total > 0 else 1.0
                        c.execute(
                            """UPDATE ai_inspection_knowledge 
                               SET success_count=?, success_rate=?, last_used=?
                               WHERE id=?""",
                            (new_success, new_rate, now, existing['id'])
                        )
                    else:
                        c.execute(
                            """INSERT INTO ai_inspection_knowledge
                               (pattern_hash, error_type, error_pattern, fix_method, fix_template,
                                success_count, fail_count, success_rate, first_seen, last_used,
                                learned_from, confidence)
                               VALUES (?, ?, ?, ?, ?, 1, 0, 1.0, ?, ?, ?, 0.8)""",
                            (pattern_hash, err_type, err_msg, fix_method, '',
                             now, now, f'inspection:{run_id}')
                        )
                        gained += 1

                conn.commit()
        except Exception as e:
            _logger.error(f"AI学习失败: {e}")

        return gained

    def seed_knowledge_base(self):
        """初始化种子知识库"""
        seed_data = [
            {
                'error_type': 'python_syntax_error',
                'error_pattern': 'EOL while scanning string literal',
                'fix_method': 'fix_unterminated_string',
                'fix_template': 'add_missing_quote',
                'confidence': 0.7,
            },
            {
                'error_type': 'python_syntax_error',
                'error_pattern': 'expected an indented block',
                'fix_method': 'fix_indentation',
                'fix_template': 'add_indentation',
                'confidence': 0.6,
            },
            {
                'error_type': 'python_syntax_error',
                'error_pattern': 'invalid syntax',
                'fix_method': 'fix_invalid_syntax_patterns',
                'fix_template': 'pattern_based_fix',
                'confidence': 0.5,
            },
            {
                'error_type': 'python_syntax_error',
                'error_pattern': 'unexpected indent',
                'fix_method': 'fix_unexpected_indent',
                'fix_template': 'adjust_indentation',
                'confidence': 0.6,
            },
            {
                'error_type': 'css_syntax_error',
                'error_pattern': '大括号不平衡',
                'fix_method': 'fix_brace_mismatch',
                'fix_template': 'add_missing_braces',
                'confidence': 0.65,
            },
            {
                'error_type': 'css_syntax_error',
                'error_pattern': '缺少分号',
                'fix_method': 'fix_missing_semicolons',
                'fix_template': 'add_semicolons',
                'confidence': 0.55,
            },
            {
                'error_type': 'css_syntax_error',
                'error_pattern': '空选择器',
                'fix_method': 'fix_empty_selectors',
                'fix_template': 'remove_empty_selectors',
                'confidence': 0.6,
            },
            {
                'error_type': 'css_syntax_error',
                'error_pattern': 'BRACE_MISMATCH',
                'fix_method': 'fix_brace_mismatch',
                'fix_template': 'add_missing_braces',
                'confidence': 0.7,
            },
            {
                'error_type': 'css_syntax_error',
                'error_pattern': 'MISSING_SEMICOLON',
                'fix_method': 'fix_missing_semicolons',
                'fix_template': 'add_semicolons',
                'confidence': 0.6,
            },
            {
                'error_type': 'js_syntax_warning',
                'error_pattern': 'JS_BRACKET_MISMATCH',
                'fix_method': 'fix_js_bracket_mismatch',
                'fix_template': 'balance_brackets',
                'confidence': 0.4,
            },
            {
                'error_type': 'js_syntax_warning',
                'error_pattern': 'JS_PATTERN_WARN',
                'fix_method': 'fix_js_pattern_issues',
                'fix_template': 'pattern_based_fix',
                'confidence': 0.3,
            },
            {
                'error_type': 'html_structure_warning',
                'error_pattern': 'HTML_TAG_MISMATCH',
                'fix_method': 'fix_html_tag_mismatch',
                'fix_template': 'balance_tags',
                'confidence': 0.3,
            },
            {
                'error_type': 'html_structure_warning',
                'error_pattern': 'STYLE_BLOCK_CSS',
                'fix_method': 'fix_style_block_css',
                'fix_template': 'css_fixer',
                'confidence': 0.5,
            },
            {
                'error_type': 'html_structure_warning',
                'error_pattern': 'INLINE_CSS_WARN',
                'fix_method': 'fix_inline_css',
                'fix_template': 'inline_css_fix',
                'confidence': 0.3,
            },
            {
                'error_type': 'html_structure_warning',
                'error_pattern': 'SCRIPT_BRACKET',
                'fix_method': 'fix_script_bracket',
                'fix_template': 'script_bracket_fix',
                'confidence': 0.4,
            },
        ]

        count = 0
        try:
            with _get_conn() as conn:
                c = conn.cursor()
                now = datetime.now().isoformat()
                for seed in seed_data:
                    pattern_hash = hashlib.md5(
                        f"{seed['error_type']}:{seed['error_pattern']}".encode('utf-8')
                    ).hexdigest()
                    c.execute(
                        """INSERT OR IGNORE INTO ai_inspection_knowledge
                           (pattern_hash, error_type, error_pattern, fix_method, fix_template,
                            success_count, fail_count, success_rate, first_seen, last_used,
                            learned_from, confidence)
                           VALUES (?, ?, ?, ?, ?, 5, 1, 0.83, ?, ?, 'seed', ?)""",
                        (pattern_hash, seed['error_type'], seed['error_pattern'],
                         seed['fix_method'], seed['fix_template'], now, now, seed['confidence'])
                    )
                    if c.rowcount > 0:
                        count += 1
                conn.commit()
        except Exception as e:
            _logger.error(f"种子知识库初始化失败: {e}")

        return count


# ============== 全局单例 ==============
_inspection_engine = None
_engine_lock = threading.Lock()

def get_inspection_engine() -> AIInspectionLoopEngine:
    global _inspection_engine
    with _engine_lock:
        if _inspection_engine is None:
            _inspection_engine = AIInspectionLoopEngine()
            _inspection_engine.seed_knowledge_base()
    return _inspection_engine


# ============== 命令行测试 ==============
if __name__ == '__main__':
    engine = get_inspection_engine()
    print("启动单次巡检闭环测试...")
    result = engine.run_once('test')
    print(json.dumps(result, ensure_ascii=False, indent=2))
