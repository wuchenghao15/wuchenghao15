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
            c.execute("""CREATE TABLE IF NOT EXISTS ai_inspection_red_wiggles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wiggle_id TEXT UNIQUE,
                run_id TEXT,
                source_tool TEXT,
                language TEXT,
                severity TEXT,
                severity_icon TEXT,
                file_path TEXT,
                line_number INTEGER,
                column_number INTEGER,
                end_line INTEGER,
                end_column INTEGER,
                error_code TEXT,
                rule_id TEXT,
                error_message TEXT,
                suggestion_message TEXT,
                confidence REAL DEFAULT 0.0,
                auto_fixable INTEGER DEFAULT 0,
                reported_at TEXT,
                fixed INTEGER DEFAULT 0,
                fix_method TEXT,
                fix_result TEXT,
                fixed_at TEXT
            )""")
            c.execute("""CREATE INDEX IF NOT EXISTS idx_inspection_issues_run ON ai_inspection_issues(run_id)""")
            c.execute("""CREATE INDEX IF NOT EXISTS idx_inspection_issues_type ON ai_inspection_issues(issue_type)""")
            c.execute("""CREATE INDEX IF NOT EXISTS idx_inspection_knowledge_hash ON ai_inspection_knowledge(pattern_hash)""")
            c.execute("""CREATE INDEX IF NOT EXISTS idx_console_errors_fixed ON ai_inspection_console_errors(fixed)""")
            c.execute("""CREATE INDEX IF NOT EXISTS idx_red_wiggles_file ON ai_inspection_red_wiggles(file_path)""")
            c.execute("""CREATE INDEX IF NOT EXISTS idx_red_wiggles_fixed ON ai_inspection_red_wiggles(fixed)""")
            c.execute("""CREATE INDEX IF NOT EXISTS idx_red_wiggles_severity ON ai_inspection_red_wiggles(severity)""")
            # 为 issues 表补充红色波浪线扩展列（如已存在跳过）
            try:
                c.execute("""ALTER TABLE ai_inspection_issues ADD COLUMN is_red_wiggle INTEGER DEFAULT 0""")
            except Exception:
                pass
            try:
                c.execute("""ALTER TABLE ai_inspection_issues ADD COLUMN wiggle_icon TEXT""")
            except Exception:
                pass
            try:
                c.execute("""ALTER TABLE ai_inspection_issues ADD COLUMN source_tool TEXT""")
            except Exception:
                pass
            try:
                c.execute("""ALTER TABLE ai_inspection_issues ADD COLUMN rule_id TEXT""")
            except Exception:
                pass
            try:
                c.execute("""ALTER TABLE ai_inspection_issues ADD COLUMN suggestion_message TEXT""")
            except Exception:
                pass
            try:
                c.execute("""ALTER TABLE ai_inspection_issues ADD COLUMN auto_fixable INTEGER DEFAULT 0""")
            except Exception:
                pass
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

        # 修复：内联 style 属性中的 Jinja2 模板语法（IDE 红色波浪线主因）
        if any(k in error_code for k in ('INLINE_STYLE_TEMPLATE', 'STYLE_TEMPLATE', 'CSS_NEW_SYNTAX', 'CSS_COLOR_MIX', 'CSS_CLAMP', 'EVENT_QUOTE')):
            try:
                fixed_content, method = cls._fix_inline_style_templates(content)
                if method and fixed_content != content:
                    content = fixed_content
                    fix_methods.append(method)
            except Exception:
                pass

        # 修复style块中的CSS问题
        if 'STYLE_BLOCK_CSS' in error_code or 'style' in error_msg.lower():
            try:
                fixed_content, method = cls._fix_style_blocks(content)
                if method and fixed_content != content:
                    content = fixed_content
                    fix_methods.append(method)
            except Exception:
                pass

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

    # 预定义的状态 → 颜色映射（与模板中 {% if %} 分支保持一致）
    _STATUS_COLOR_MAP = {
        'stable':   '#10b981',
        'release':  '#10b981',
        'ga':       '#10b981',
        '正式':      '#10b981',
        '生产':      '#10b981',
        'beta':     '#f59e0b',
        'rc':       '#f59e0b',
        '候选':      '#f59e0b',
        'dev':      '#6366f1',
        'alpha':    '#6366f1',
        '开发':      '#6366f1',
        '内测':      '#6366f1',
    }
    _STATUS_DEFAULT_COLOR = '#06b6d4'

    @classmethod
    def _color_for_status(cls, status_val: str) -> str:
        if not status_val:
            return cls._STATUS_DEFAULT_COLOR
        return cls._STATUS_COLOR_MAP.get((status_val or '').strip().lower(), cls._STATUS_DEFAULT_COLOR)

    @classmethod
    def _fix_inline_style_templates(cls, content: str) -> Tuple[str, str]:
        """
        自动修复：内联 style 属性中含 Jinja2 模板语法 / CSS 新语法 / 事件处理器引号嵌套
        策略：
          1) 若 style="background:{% if status %}#xxx{% elif %}#yyy{% endif %}" 模式
             → 提取为 class="eyebrow-dot eyebrow-dot-status-<动态>" + <style> 4 类
             + 一小段 <script> 读取 data-status 并动态应用颜色
          2) 通用兜底：把 style 中的 {% %}/ {{ }} 替换为 CSS var(..., 默认值)；
             同时注入脚本：渲染时把实际值写入 :root 的对应 CSS 变量
        """
        import hashlib as _hl
        fixed = content
        changed = 0
        # style 内是否含有模板语法的正则（用于精确替换）
        style_re = re.compile(
            r'style\s*=\s*(["\'])((?:\\.|(?!\1).)*)(\1)',
            re.DOTALL | re.IGNORECASE
        )
        # 1) 收集所有需要替换的 style="...{%... %}..."
        replacements = []  # List[Tuple(match_span_start, match_span_end, new_style_attr)]
        injected_vars = []  # 需要注入到 :root 的 CSS 变量名 + 默认值
        injected_scripts = []  # 需要追加到 </body> 前的脚本片段（若有）

        for m in style_re.finditer(content):
            quote = m.group(1)
            style_val = m.group(2)
            if ('{%' not in style_val) and ('{{' not in style_val):
                continue

            # 识别是否是 status → background 映射（项目中 L2228 的典型模式）
            # 关键词检测比硬正则更可靠：style 里有 background 且至少同时含 template 语法与 status 映射词
            is_status_bg_pattern = False
            low_val = style_val.lower()
            if 'background' in low_val and ('{%' in style_val or '{{' in style_val):
                bg_cues = sum(1 for w in (
                    'version_info.status', 'status', 'stable', 'release', 'ga',
                    '"正式"', "'正式'", '"生产"', "'生产'",
                    'beta', 'rc', '"候选"', "'候选'",
                    'dev', 'alpha', '"开发"', "'开发'", '"内测"', "'内测'"
                ) if w in style_val)
                # 至少命中 3 个 cues 才是 status→background 映射
                if bg_cues >= 3:
                    is_status_bg_pattern = True
            new_style_parts = []
            processed = False

            # ---- 专用策略 A：status-background 映射模式 ----
            if is_status_bg_pattern:
                # 去掉所有模板语法，改成 CSS 变量，默认值取 status=stable 的绿
                default_bg = cls._STATUS_DEFAULT_COLOR
                # 剥离 style_val 里的模板，并替换为 `background: var(--hero-eyebrow-dot-color, #默认) !important;`
                other_props = []
                for p in [x.strip() for x in style_val.split(';') if x.strip()]:
                    low = p.lower()
                    if low.startswith('background'):
                        continue  # 旧的 background 被模板语法包裹，完全丢弃重写
                    other_props.append(p)
                new_style_parts.extend(other_props)
                new_style_parts.append(f'background: var(--hero-eyebrow-dot-color, {default_bg}) !important')
                injected_vars.append(('--hero-eyebrow-dot-color', default_bg))
                injected_scripts.append('__style_fix_status_bg')
                processed = True

            # ---- 通用策略 B：任意模板语法包含在 style 中 ----
            if not processed:
                # 把所有 {%...%}/ {{...}} 片段替换成占位变量，保留字面量部分的默认值
                i = 0
                n = len(style_val)
                out = []
                var_idx = 0
                while i < n:
                    ch = style_val[i]
                    if ch == '{' and i + 1 < n and style_val[i + 1] in ('%', '{'):
                        # 找到匹配的结束
                        end_close = style_val.find('%}' if style_val[i + 1] == '%' else '}}', i + 2)
                        if end_close == -1:
                            out.append(ch)
                            i += 1
                            continue
                        # 尝试提取最后一个 if 分支里的默认色值（形如 {% else %}#06b6d4）
                        default_val = ''
                        else_m = re.search(r'%\}\s*else\s*%\}\s*([^%\{%]+)', style_val[i:end_close + 2])
                        if else_m:
                            default_val = else_m.group(1).strip().rstrip(';').strip()
                        if not default_val:
                            last_elif = re.findall(r'%\}\s*([^%\{%]+?)\s*%\}', style_val[i:end_close + 2])
                            if last_elif:
                                default_val = last_elif[-1].strip().rstrip(';').strip()
                        var_name = f'--style-fix-{_hl.md5(style_val.encode("utf-8")).hexdigest()[:7]}-{var_idx}'
                        var_idx += 1
                        injected_vars.append((var_name, default_val or 'inherit'))
                        out.append(f'var({var_name}, {default_val or "inherit"})')
                        i = end_close + 2
                    else:
                        out.append(ch)
                        i += 1
                new_style_val = ''.join(out).strip()
                if new_style_val and not new_style_val.endswith(';'):
                    new_style_val += ';'
                new_style_parts = [new_style_val]

            # 组装新的 style 属性（保持原有引号）
            final = ';'.join(new_style_parts).strip('; ').strip()
            # 清洗重复分号/空分号
            final = re.sub(r';\s*;+', ';', final)
            new_attr = f'style={quote}{final}{quote}'
            replacements.append((m.start(), m.end(), new_attr))
            changed += 1

        # 2) 执行所有替换（从后向前避免偏移）
        if replacements:
            parts = list(fixed)
            for s, e, new in reversed(replacements):
                parts[s:e] = list(new)
            fixed = ''.join(parts)

        # 3) 注入 <style> CSS 变量 + 类声明到 </head> 前
        if injected_vars:
            # 去重
            seen_vars = set()
            unique_vars = []
            for nm, dv in injected_vars:
                if nm in seen_vars:
                    continue
                seen_vars.add(nm)
                unique_vars.append((nm, dv))
            vars_block_lines = [':root {']
            for nm, dv in unique_vars:
                vars_block_lines.append(f'    {nm}: {dv};')
            vars_block_lines.append('}')
            # 额外：status 类
            status_cls_lines = [
                '/* -------- AI 自动修复：status → background 颜色（消除内联模板语法 IDE 红线） -------- */',
                '.eyebrow-dot { transition: background-color .2s ease; border-radius: 9999px; }',
            ]
            classes_block = '\n'.join(vars_block_lines + status_cls_lines)
            style_tag = f'\n<style data-inspection-auto-fix="inline-style-template">\n{classes_block}\n</style>\n'
            # 插入 </head> 前（若无 </head>，就插到最前面 content 开头）
            if re.search(r'</head>', fixed, re.IGNORECASE):
                fixed = re.sub(r'</head>', style_tag + '</head>', fixed, count=1, flags=re.IGNORECASE)
            else:
                fixed = style_tag + fixed

        # 4) 如果是 status-background 映射：追加脚本自动读取 data-status 应用颜色
        if '__style_fix_status_bg' in injected_scripts:
            script_body = (
                '\n<script data-inspection-auto-fix="inline-style-template">\n'
                '(function(){\n'
                '  function applyEyebrowDotColor(){\n'
                '    var eyebrow = document.getElementById("heroEyebrow");\n'
                '    var dot = document.getElementById("eyebrowDot");\n'
                '    if (!dot) return;\n'
                '    var status = eyebrow ? String(eyebrow.getAttribute("data-status") || "").toLowerCase() : "";\n'
                '    var COLORS = {\n'
                '      "stable":"#10b981","release":"#10b981","ga":"#10b981","正式":"#10b981","生产":"#10b981",\n'
                '      "beta":"#f59e0b","rc":"#f59e0b","候选":"#f59e0b",\n'
                '      "dev":"#6366f1","alpha":"#6366f1","开发":"#6366f1","内测":"#6366f1"\n'
                '    };\n'
                '    var color = COLORS[status] || "#06b6d4";\n'
                '    document.documentElement.style.setProperty("--hero-eyebrow-dot-color", color);\n'
                '    dot.style.background = color;\n'
                '  }\n'
                '  if (document.readyState === "loading") {\n'
                '    document.addEventListener("DOMContentLoaded", applyEyebrowDotColor);\n'
                '  } else {\n'
                '    applyEyebrowDotColor();\n'
                '  }\n'
                '})();\n'
                '</script>\n'
            )
            # 插入 </body> 前
            if re.search(r'</body>', fixed, re.IGNORECASE):
                fixed = re.sub(r'</body>', script_body + '</body>', fixed, count=1, flags=re.IGNORECASE)
            else:
                fixed = fixed + script_body
            changed += 1

        # 5) 修复 on* 事件处理器内引号嵌套问题（CSS_COLOR_MIX 模式里出现过 this.style.color='xxx'）
        ev_fix_n = 0
        def _fix_event_quotes(mm):
            nonlocal ev_fix_n
            name = mm.group(1)
            q = mm.group(2)
            body = mm.group(3)
            # 如果属性用双引号，且 body 里有未转义的双引号，就把 body 换成单引号嵌套
            if q == '"' and '"' in body and "'" not in body:
                # 转成外单 + 内双（但更安全是直接把双引号替换成 &#34; 实体）
                body_safe = body.replace('"', '&#34;')
                ev_fix_n += 1
                return f' on{name}={q}{body_safe}{q}'
            return mm.group(0)
        fixed = re.sub(
            r'\son(click|dblclick|mouse(?:over|out|down|up|move|enter|leave)|'
            r'key(?:down|up|press)|focus|blur|change|input|submit|load|error|scroll|resize|'
            r'drag(?:start|end|over)?|drop|touch(?:start|end|move)|contextmenu|copy|cut|paste)'
            r'\s*=\s*(["\'])((?:\\.|(?!\2).)*)\2',
            _fix_event_quotes,
            fixed,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if ev_fix_n > 0:
            changed += ev_fix_n

        # 6) 修复 style 属性 / on* 处理器中 color-mix() / clamp() 等新语法（IDE CSS 解析器不支持会触发红线）
        new_syntax_fix_n = 0

        def _parse_color(c: str):
            """解析常见颜色格式 → (r,g,b) 0-255"""
            c = c.strip()
            # 十六进制
            m = re.match(r'^#([0-9a-fA-F]{3,8})$', c)
            if m:
                h = m.group(1)
                if len(h) == 3:
                    h = h[0]*2 + h[1]*2 + h[2]*2
                if len(h) >= 6:
                    return (int(h[0:2],16), int(h[2:4],16), int(h[4:6],16))
            # rgb / rgba
            m = re.match(r'^rgba?\(\s*([\d.]+)\s*,?\s*([\d.]+)\s*,?\s*([\d.]+)', c, re.IGNORECASE)
            if m:
                return (max(0,min(255, int(float(m.group(1))))),
                        max(0,min(255, int(float(m.group(2))))),
                        max(0,min(255, int(float(m.group(3))))))
            # var(...)  fallback: 取第二个参数作为颜色
            m = re.match(r'^var\([^)]*,\s*(#[0-9a-fA-F]{3,8}|rgba?\([^)]*\))\s*\)$', c, re.IGNORECASE)
            if m:
                return _parse_color(m.group(1))
            return None

        def _mix_color(rgb1, rgb2, p1: float):
            """按百分比混合两个 RGB 颜色"""
            p2 = 1 - p1
            r = int(round(rgb1[0]*p1 + rgb2[0]*p2))
            g = int(round(rgb1[1]*p1 + rgb2[1]*p2))
            b = int(round(rgb1[2]*p1 + rgb2[2]*p2))
            return f'#{r:02x}{g:02x}{b:02x}'

        def _replace_color_mix(s: str):
            """把字符串中 color-mix(in srgb, color1 p1%, color2 p2%) 替换为近似色"""
            nonlocal new_syntax_fix_n
            pat = re.compile(
                r'color-mix\s*\(\s*in\s+srgb\s*,',
                re.IGNORECASE
            )
            out = []
            i = 0
            n = len(s)
            while i < n:
                m = pat.search(s, i)
                if not m:
                    out.append(s[i:])
                    break
                out.append(s[i:m.start()])
                pos = m.end()  # 跳过 'color-mix(in srgb,'

                def _skip_ws():
                    nonlocal pos
                    while pos < n and s[pos] in ' \t\n\r':
                        pos += 1

                def _read_balanced_token():
                    """读取一个颜色 token（允许括号内嵌），然后剥离尾部 ws+数字+%，为 _read_pct 留下数字"""
                    nonlocal pos
                    _skip_ws()
                    start = pos
                    depth = 0
                    while pos < n:
                        ch = s[pos]
                        if ch == '(':
                            depth += 1
                            pos += 1
                        elif ch == ')':
                            if depth == 0:
                                break
                            depth -= 1
                            pos += 1
                        elif ch == ',' and depth == 0:
                            break
                        else:
                            pos += 1
                    raw = s[start:pos]
                    # 剥离尾部：空白 + 数字 + 可选空白 + %
                    mm = re.search(r'[\s\xa0]+(\d+(?:\.\d+)?)\s*%\s*$', raw)
                    if mm:
                        # raw 的末尾是数字+%，要剥离去：颜色部分为 raw[:mm.start()]，数字的起点是 mm.start(1)
                        color_part = raw[:mm.start()].rstrip()
                        # 回溯 pos 到数字开头（相对于全局 start + mm.start(1)），这样 _read_pct 能读到数字%
                        pos = start + mm.start(1)
                    else:
                        color_part = raw
                    return color_part.strip()

                def _read_pct():
                    nonlocal pos
                    _skip_ws()
                    m2 = re.match(r'(\d+(?:\.\d+)?)\s*%', s[pos:])
                    if m2:
                        pos += len(m2.group(0))
                        return float(m2.group(1)) / 100.0
                    return None

                c1 = _read_balanced_token()
                p1 = _read_pct()
                # 跳过分隔逗号
                _skip_ws()
                if pos < n and s[pos] == ',':
                    pos += 1
                c2 = _read_balanced_token()
                p2 = _read_pct()
                # 跳过结尾 ')'
                _skip_ws()
                if pos < n and s[pos] == ')':
                    pos += 1
                rgb1 = _parse_color(c1) if c1 else None
                rgb2 = _parse_color(c2) if c2 else None
                if rgb1 and rgb2 and p1 is not None:
                    new_syntax_fix_n += 1
                    out.append(_mix_color(rgb1, rgb2, p1))
                else:
                    out.append(s[m.start():pos])
                i = pos
            return ''.join(out)

        # 扫描所有 style 属性，替换 color-mix
        def _replace_attr(match, attr_name):
            q = match.group(1)
            val = match.group(2)
            new_val = _replace_color_mix(val)
            if new_val != val:
                return f' {attr_name}={q}{new_val}{q}'
            return match.group(0)

        fixed_new = re.sub(
            r'\sstyle\s*=\s*(["\'])((?:\\.|(?!\1).)*)\1',
            lambda m: _replace_attr(m, 'style'),
            fixed,
            flags=re.DOTALL | re.IGNORECASE,
        )
        # 扫描所有 on* 事件处理器，替换其中的字符串赋值（this.style.color='...color-mix...'）
        fixed_new = re.sub(
            r'\son(click|dblclick|mouse(?:over|out|down|up|move|enter|leave)|'
            r'key(?:down|up|press)|focus|blur|change|input|submit|load|error|scroll|resize|'
            r'drag(?:start|end|over)?|drop|touch(?:start|end|move)|contextmenu|copy|cut|paste)'
            r'\s*=\s*(["\'])((?:\\.|(?!\2).)*)\2',
            lambda m: _replace_attr(m, 'on' + m.group(1)),
            fixed_new,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if fixed_new != fixed:
            fixed = fixed_new
            changed += new_syntax_fix_n or 1

        method_name = ''
        if changed:
            parts_name = []
            if replacements:
                parts_name.append(f'fix_inline_style_template_{len(replacements)}')
            if injected_vars:
                parts_name.append(f'inject_css_vars_{len(injected_vars)}')
            if '__style_fix_status_bg' in injected_scripts:
                parts_name.append('inject_status_bg_script')
            if ev_fix_n:
                parts_name.append(f'fix_event_quotes_{ev_fix_n}')
            if new_syntax_fix_n:
                parts_name.append(f'fix_css_new_syntax_{new_syntax_fix_n}')
            method_name = '+'.join(parts_name)
        return fixed, method_name


# ============== 扩展 Fixer 类（多文件类型） ==============
class MarkdownFixer:
    """Markdown / Markup 文件错误检测与修复器（支持 .md/.markdown）"""

    @classmethod
    def check_markdown(cls, fpath: str) -> Optional[Dict]:
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception:
            return None
        lines = content.split('\n')
        issues = []

        # 1. 标题等级跳跃（如 H1 直接跳到 H3）
        last_level = 0
        for i, ln in enumerate(lines, 1):
            m = re.match(r'^(#{1,6})\s+', ln)
            if m:
                lvl = len(m.group(1))
                if last_level and lvl > last_level + 1:
                    issues.append({
                        'code': 'MD_HEADING_SKIP',
                        'msg': f'标题等级跳跃：从H{last_level}直接到H{lvl}（建议按H1→H2→H3逐层递进）',
                        'severity': 'low', 'confidence': 0.65, 'line': i,
                    })
                last_level = lvl

        # 2. 未闭合的加粗/斜体标记（按行扫描）
        for i, ln in enumerate(lines, 1):
            clean = re.sub(r'`[^`]*`', '', ln)
            clean = re.sub(r'\[[^\]]*\]\([^)]*\)', '', clean)
            clean = re.sub(r'^```[\s\S]*?```', '', clean, flags=re.MULTILINE)
            # 粗体 **...**
            b = clean.count('**')
            if b % 2 != 0:
                issues.append({
                    'code': 'MD_UNCLOSED_BOLD',
                    'msg': f'检测到未闭合的粗体标记 **，红色波浪线提示级别（建议补齐成对）',
                    'severity': 'medium', 'confidence': 0.7, 'line': i,
                })
                break
            em = clean.count('*') - clean.count('**') * 2
            if em % 2 != 0 and clean.count('*') > 0:
                issues.append({
                    'code': 'MD_UNCLOSED_ITALIC',
                    'msg': '斜体标记 * 可能未闭合',
                    'severity': 'low', 'confidence': 0.45, 'line': i,
                })
                break

        # 3. 孤立的链接/图片语法（缺少 ] 或 )）
        for i, ln in enumerate(lines, 1):
            opens = len(re.findall(r'!\[|\[(?=\s*\])?', ln))
            closes_b = ln.count(']')
            if opens > closes_b:
                issues.append({
                    'code': 'MD_LINK_BRACKET',
                    'msg': '链接/图片语法中括号不匹配（] 数量少）',
                    'severity': 'medium', 'confidence': 0.75, 'line': i,
                })
                break
            opens_p = len(re.findall(r'\]\(', ln))
            closes_p = ln.count(')')
            if opens_p > 0 and closes_p < opens_p:
                issues.append({
                    'code': 'MD_LINK_PAREN',
                    'msg': '链接URL部分括号 ) 可能缺失',
                    'severity': 'high', 'confidence': 0.85, 'line': i,
                })
                break

        # 4. 中英文混排检测（空格缺失）—— 逻辑/排版建议
        bad_spacing = 0
        for ln in lines:
            if re.search(r'[\u4e00-\u9fff][A-Za-z0-9]|[A-Za-z0-9][\u4e00-\u9fff]', ln):
                bad_spacing += 1
            if bad_spacing >= 5:
                issues.append({
                    'code': 'MD_CJK_SPACING',
                    'msg': f'检测到 {bad_spacing}+ 处中英文/数字相邻未加空格（影响排版可读性）',
                    'severity': 'low', 'confidence': 0.55, 'line': 0,
                })
                break

        if not issues:
            return None
        issues.sort(key=lambda x: (
            {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}.get(x['severity'], 9),
            -x['confidence']
        ))
        top = issues[0]
        return {
            'issue_type': 'markdown_syntax_warning',
            'severity': top['severity'],
            'file_path': fpath,
            'line_number': top.get('line', 0),
            'error_message': top['msg'],
            'error_code': top['code'],
            'confidence': top['confidence'],
            '_all_md_issues': issues,
        }

    @classmethod
    def fix_file(cls, fpath: str, error_msg: str, error_code: str) -> Tuple[bool, str]:
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
        except Exception:
            return False, ''
        original = ''.join(lines)
        method = ''
        new_lines = list(lines)

        if error_code in ('MD_HEADING_SKIP',):
            # 将跳跃的标题降级一级（H4改成H3等）
            last_level = 0
            for i, ln in enumerate(new_lines):
                m = re.match(r'^(#{1,6})\s+(.*\n?)$', ln)
                if m:
                    lvl = len(m.group(1))
                    if last_level and lvl > last_level + 1:
                        new_lvl = last_level + 1
                        new_lines[i] = '#' * new_lvl + ' ' + m.group(2)
                        method = 'fix_heading_skip'
                    m2 = re.match(r'^(#{1,6})\s+', new_lines[i])
                    if m2:
                        last_level = len(m2.group(1))
        elif error_code in ('MD_UNCLOSED_BOLD', 'MD_UNCLOSED_ITALIC'):
            # 在行尾追加闭合符号
            for i in range(len(new_lines) - 1, -1, -1):
                if '**' in new_lines[i] and new_lines[i].count('**') % 2 != 0:
                    new_lines[i] = new_lines[i].rstrip('\n') + '**\n'
                    method = 'fix_unclosed_bold'
                    break
        elif error_code == 'MD_LINK_PAREN':
            # 为所有 ](... 补齐 )
            for i, ln in enumerate(new_lines):
                opens_p = len(re.findall(r'\]\(', ln))
                closes_p = ln.count(')')
                if opens_p > 0 and closes_p < opens_p:
                    need = opens_p - closes_p
                    new_lines[i] = ln.rstrip('\n') + ')' * need + '\n'
                    method = 'fix_link_paren_missing'
                    break
        elif error_code == 'MD_CJK_SPACING':
            # 中英文混排自动加空格
            for i, ln in enumerate(new_lines):
                new_ln = re.sub(r'([\u4e00-\u9fff])([A-Za-z0-9])', r'\1 \2', ln)
                new_ln = re.sub(r'([A-Za-z0-9])([\u4e00-\u9fff])', r'\1 \2', new_ln)
                if new_ln != ln:
                    new_lines[i] = new_ln
                    if not method:
                        method = 'fix_cjk_spacing'

        content = ''.join(new_lines)
        if content != original and method:
            try:
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True, method
            except Exception:
                return False, ''
        return False, ''


class SQLFixer:
    """SQL / .db 元数据文件错误检测与修复"""

    @classmethod
    def check_sql(cls, fpath: str) -> Optional[Dict]:
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception:
            return None
        issues = []
        lines = content.split('\n')

        # 1. 语句末尾缺少分号（以 CREATE/INSERT/UPDATE/DELETE/SELECT/ALTER/DROP 开头的语句）
        stmt_starts = [i for i, ln in enumerate(lines)
                       if re.match(r'^\s*(CREATE|INSERT|UPDATE|DELETE|SELECT|ALTER|DROP|TRUNCATE|REPLACE|MERGE)\b', ln, re.IGNORECASE)]
        if stmt_starts:
            for idx, si in enumerate(stmt_starts):
                end_i = stmt_starts[idx + 1] if idx + 1 < len(stmt_starts) else len(lines)
                seg = ' '.join(l.rstrip() for l in lines[si:end_i])
                # 去除字符串中的 ;
                seg_clean = re.sub(r"'[^']*'", "''", seg)
                seg_clean = re.sub(r'"[^"]*"', '""', seg_clean)
                if ';' not in seg_clean.rstrip().rstrip('\\'):
                    issues.append({
                        'code': 'SQL_MISSING_SEMICOLON',
                        'msg': f'SQL语句（行{si+1}起）末尾缺少分号; 属于语法错误（红色波浪线级别）',
                        'severity': 'high', 'confidence': 0.9, 'line': si + 1,
                    })
                    break

        # 2. SELECT * 被使用（逻辑/优化问题）
        for i, ln in enumerate(lines, 1):
            if re.search(r'\bSELECT\s+\*\s+FROM\b', ln, re.IGNORECASE):
                issues.append({
                    'code': 'SQL_SELECT_STAR',
                    'msg': '使用 SELECT *（建议显式列出字段，避免不必要列读取与兼容隐患）',
                    'severity': 'low', 'confidence': 0.65, 'line': i,
                })
                break

        # 3. 未参数化拼接痕迹（WHERE xxx='$var' 或 LIKE '%xxx$_GET'）
        for i, ln in enumerate(lines, 1):
            if re.search(r"['\"]\s*\.\s*\$[a-zA-Z_]|\{[a-zA-Z_][\w]*\}\s*['\"]|\$_(GET|POST|REQUEST|SERVER)\[", ln):
                issues.append({
                    'code': 'SQL_INJECT_RISK',
                    'msg': f'疑似SQL注入风险：检测到变量拼接（建议使用参数化查询/预处理语句）',
                    'severity': 'critical', 'confidence': 0.88, 'line': i,
                })
                break

        # 4. CREATE TABLE 缺失 PRIMARY KEY
        table_defs = re.findall(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`"\[]?\w+[`"\]]?\s*\(([^;]+)\)', content, flags=re.IGNORECASE | re.DOTALL)
        for td in table_defs:
            if not re.search(r'\bPRIMARY\s+KEY\b', td, re.IGNORECASE):
                issues.append({
                    'code': 'SQL_NO_PRIMARY_KEY',
                    'msg': 'CREATE TABLE 语句中未定义 PRIMARY KEY 主键（影响索引与更新定位）',
                    'severity': 'medium', 'confidence': 0.8, 'line': 0,
                })
                break

        if not issues:
            return None
        issues.sort(key=lambda x: (
            {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}.get(x['severity'], 9),
            -x['confidence']
        ))
        top = issues[0]
        return {
            'issue_type': 'sql_syntax_error',
            'severity': top['severity'],
            'file_path': fpath,
            'line_number': top.get('line', 0),
            'error_message': top['msg'],
            'error_code': top['code'],
            'confidence': top['confidence'],
            '_all_sql_issues': issues,
        }

    @classmethod
    def fix_file(cls, fpath: str, error_msg: str, error_code: str) -> Tuple[bool, str]:
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
        except Exception:
            return False, ''
        original = ''.join(lines)
        new_lines = list(lines)
        method = ''

        if error_code == 'SQL_MISSING_SEMICOLON':
            stmt_starts = [i for i, ln in enumerate(new_lines)
                           if re.match(r'^\s*(CREATE|INSERT|UPDATE|DELETE|SELECT|ALTER|DROP|TRUNCATE|REPLACE|MERGE)\b', ln, re.IGNORECASE)]
            if stmt_starts:
                last_start = stmt_starts[-1]
                # 找到下一条语句之前的最后一行非空，追加 ;
                end = len(new_lines)
                # 从 end-1 找到最后一个非空且不是注释的行
                for i in range(end - 1, last_start - 1, -1):
                    if new_lines[i].strip() and not new_lines[i].strip().startswith('--'):
                        stripped = new_lines[i].rstrip('\n').rstrip()
                        if not stripped.endswith(';'):
                            new_lines[i] = stripped + ';\n'
                            method = 'append_semicolon'
                        break
        elif error_code == 'SQL_NO_PRIMARY_KEY':
            # 保守修复：在 CREATE TABLE 的 ( 之后插入 id INTEGER PRIMARY KEY AUTOINCREMENT （若不存在）
            for i, ln in enumerate(new_lines):
                m = re.match(r'^(\s*CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`"\[]?\w+[`"\]]?\s*\(\s*)(\n?)$', ln, re.IGNORECASE)
                if m:
                    prefix = m.group(1)
                    newline = m.group(2) or '\n'
                    # 检查后续行是否已有主键
                    rest = ''.join(new_lines[i + 1: i + 6])
                    if not re.search(r'\bPRIMARY\s+KEY\b', rest, re.IGNORECASE):
                        new_lines[i] = prefix + newline
                        new_lines.insert(i + 1, '    id INTEGER PRIMARY KEY AUTOINCREMENT,\n')
                        method = 'add_primary_key_id'
                    break

        content = ''.join(new_lines)
        if content != original and method:
            try:
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True, method
            except Exception:
                return False, ''
        return False, ''


class PHPFixer:
    """PHP 语法检测与修复"""

    @classmethod
    def check_php(cls, fpath: str) -> Optional[Dict]:
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception:
            return None
        issues = []
        lines = content.split('\n')

        # 1. PHP 开始标签缺失（只含纯PHP代码时）
        if content.strip() and not re.match(r'\s*<\?php\b', content, re.IGNORECASE) and '?>' not in content[:300]:
            issues.append({
                'code': 'PHP_MISSING_OPEN_TAG',
                'msg': '缺少 <?php 开头标签（PHP 7+ 要求显式开始）',
                'severity': 'high', 'confidence': 0.85, 'line': 1,
            })

        # 2. 括号平衡 {} () []（忽略字符串中）
        pairs = [('{', '}', '大括号', 'BRACE'),
                 ('(', ')', '圆括号', 'PAREN'),
                 ('[', ']', '方括号', 'BRACKET')]
        clean = re.sub(r"'(?:[^'\\]|\\.)*'", "''", content)
        clean = re.sub(r'"(?:[^"\\]|\\.)*"', '""', clean)
        clean = re.sub(r'\/\/.*$', '', clean, flags=re.MULTILINE)
        clean = re.sub(r'/\*.*?\*/', '', clean, flags=re.DOTALL)
        for op, cl, name, code in pairs:
            if clean.count(op) != clean.count(cl):
                issues.append({
                    'code': f'PHP_{code}_MISMATCH',
                    'msg': f'{name}不平衡：开 {clean.count(op)} / 闭 {clean.count(cl)}（红色波浪线语法错误）',
                    'severity': 'high', 'confidence': 0.78, 'line': 0,
                })
                break

        # 3. 超全局直接未 isset 判断（逻辑隐患）
        for i, ln in enumerate(lines, 1):
            if re.search(r'\$_(GET|POST|REQUEST|SERVER|COOKIE|SESSION|FILES)\[[^\]]+\]\s*(?!\s*=)', ln):
                if not re.search(r'isset\s*\(\s*\$_', ln) and not re.search(r'!?(?:isset|empty)\s*\(', ln):
                    issues.append({
                        'code': 'PHP_UNCHECKED_SUPERGLOBAL',
                        'msg': '直接访问 $_GET/$_POST/$_SERVER 等超全局而未 isset 判断（可能产生未定义索引警告）',
                        'severity': 'medium', 'confidence': 0.75, 'line': i,
                    })
                    break

        # 4. SQL 注入痕迹：$conn->query("... $_GET[...]
        for i, ln in enumerate(lines, 1):
            if re.search(r'(mysqli_query|->query|pdo->query|mysql_query)\s*\([^)]*\$_(GET|POST|REQUEST)', ln, re.IGNORECASE):
                issues.append({
                    'code': 'PHP_SQL_INJECTION',
                    'msg': '检测到 SQL 查询与 $_GET/$_POST 直接拼接，存在严重 SQL 注入漏洞（CRITICAL 红色波浪线）',
                    'severity': 'critical', 'confidence': 0.92, 'line': i,
                })
                break

        if not issues:
            return None
        issues.sort(key=lambda x: (
            {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}.get(x['severity'], 9),
            -x['confidence']
        ))
        top = issues[0]
        return {
            'issue_type': 'php_syntax_error',
            'severity': top['severity'],
            'file_path': fpath,
            'line_number': top.get('line', 0),
            'error_message': top['msg'],
            'error_code': top['code'],
            'confidence': top['confidence'],
            '_all_php_issues': issues,
        }

    @classmethod
    def fix_file(cls, fpath: str, error_msg: str, code: str) -> Tuple[bool, str]:
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception:
            return False, ''
        original = content
        method = ''
        new_content = content

        if code == 'PHP_MISSING_OPEN_TAG':
            if not new_content.lstrip().startswith('<?php'):
                new_content = "<?php\n" + new_content.lstrip()
                method = 'prepend_php_open_tag'

        if new_content != original and method:
            try:
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return True, method
            except Exception:
                return False, ''
        return False, ''


class CSourceFixer:
    """.c / .h 源码错误检测与修复"""

    @classmethod
    def check_c_h(cls, fpath: str) -> Optional[Dict]:
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception:
            return None
        lines = content.split('\n')
        issues = []

        # 1. 括号/大括号平衡（移除字符串、注释）
        clean = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
        clean = re.sub(r'/\*.*?\*/', '', clean, flags=re.DOTALL)
        clean = re.sub(r'"(?:[^"\\]|\\.)*"', '""', clean)
        clean = re.sub(r"'(?:[^'\\]|\\.)*'", "''", clean)
        pairs = [('{', '}', '大括号', 'C_BRACE_MISMATCH', 'high'),
                 ('(', ')', '圆括号', 'C_PAREN_MISMATCH', 'high'),
                 ('[', ']', '方括号', 'C_BRACKET_MISMATCH', 'medium')]
        for op, cl, name, code, sev in pairs:
            oc = clean.count(op)
            cc = clean.count(cl)
            if oc != cc:
                issues.append({
                    'code': code,
                    'msg': f'{name}不平衡 开{oc} / 闭{cc}（语法错误红色波浪线）',
                    'severity': sev, 'confidence': 0.8, 'line': 0,
                })
                break

        # 2. 常见危险函数（strcpy/sprintf/gets/strcat）—— 逻辑与安全问题
        danger = {
            'strcpy': ('C_UNSAFE_STRCPY', '使用 strcpy（建议改用 strncpy_s / snprintf 或显式长度检查）', 'high'),
            'gets':   ('C_UNSAFE_GETS',   '使用 gets()，已从C标准移除，存在栈溢出风险（CRITICAL级）', 'critical'),
            'sprintf':('C_UNSAFE_SPRINTF','使用 sprintf（建议改用 snprintf）', 'medium'),
            'strcat': ('C_UNSAFE_STRCAT', '使用 strcat（建议改用 strncat 或计算长度后拼接）', 'medium'),
        }
        for i, ln in enumerate(lines, 1):
            for fn_name, (code, msg, sev) in danger.items():
                if re.search(r'\b' + fn_name + r'\s*\(', ln):
                    issues.append({
                        'code': code, 'msg': msg, 'severity': sev, 'confidence': 0.8, 'line': i,
                    })
                    break
            if len(issues) >= 3:
                break

        # 3. #include 引号不平衡（只在 include 行检查）
        for i, ln in enumerate(lines, 1):
            if re.match(r'^\s*#\s*include\s*[<"]', ln):
                has_open_b = '<' in ln
                has_close_b = '>' in ln
                has_open_q = '"' in ln and ln.count('"') >= 2
                if (has_open_b and not has_close_b) or (has_open_q and ln.count('"') < 2):
                    issues.append({
                        'code': 'C_INCLUDE_UNCLOSED',
                        'msg': '#include 语句中 < 或 " 未闭合（语法错误）',
                        'severity': 'high', 'confidence': 0.95, 'line': i,
                    })
                    break

        if not issues:
            return None
        issues.sort(key=lambda x: (
            {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}.get(x['severity'], 9),
            -x['confidence']
        ))
        top = issues[0]
        return {
            'issue_type': 'c_source_warning',
            'severity': top['severity'],
            'file_path': fpath,
            'line_number': top.get('line', 0),
            'error_message': top['msg'],
            'error_code': top['code'],
            'confidence': top['confidence'],
            '_all_c_issues': issues,
        }

    @classmethod
    def fix_file(cls, fpath: str, error_msg: str, code: str) -> Tuple[bool, str]:
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
        except Exception:
            return False, ''
        original = ''.join(lines)
        new_lines = list(lines)
        method = ''

        if code == 'C_BRACE_MISMATCH':
            # 在文件末尾追加缺少的 }（只补 1 个，保守策略）
            # 先计算 clean 中 { 与 } 计数差
            content = ''.join(new_lines)
            clean = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
            clean = re.sub(r'/\*.*?\*/', '', clean, flags=re.DOTALL)
            diff = clean.count('{') - clean.count('}')
            if diff > 0:
                # 找到最后一行非空非注释
                for i in range(len(new_lines) - 1, -1, -1):
                    if new_lines[i].strip():
                        suffix = '\n' if not new_lines[i].endswith('\n') else ''
                        new_lines[i] = new_lines[i].rstrip('\n') + '\n' + ('}' * diff) + '\n'
                        method = f'append_missing_{diff}_rbrace'
                        break
        elif code == 'C_INCLUDE_UNCLOSED':
            for i, ln in enumerate(new_lines):
                m = re.match(r'^(\s*#\s*include\s*)<([^>\n]+)(\s*)$', ln)
                if m:
                    new_lines[i] = f'{m.group(1)}<{m.group(2).strip()}>{m.group(3)}\n'
                    method = 'close_include_angle'
                    break
                m2 = re.match(r'^(\s*#\s*include\s*)"([^"\n]+)$', ln)
                if m2:
                    new_lines[i] = f'{m2.group(1)}"{m2.group(2).strip()}"\n'
                    method = 'close_include_quote'
                    break

        content = ''.join(new_lines)
        if content != original and method:
            try:
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True, method
            except Exception:
                return False, ''
        return False, ''


class BinaryScanner:
    """.dll / .lib / .db 二进制文件安全与结构扫描（只检测不自动修改内容）"""

    @classmethod
    def scan_binary(cls, fpath: str, ext: str) -> Optional[Dict]:
        try:
            size = os.path.getsize(fpath)
        except Exception:
            return None
        issues = []
        line_no = 0

        # 1. 空的二进制
        if size == 0:
            issues.append({
                'code': f'BIN_EMPTY_{ext.upper()}',
                'msg': f'{ext.upper()} 文件为空（0字节），可能是构建产物损坏或未正确生成',
                'severity': 'medium', 'confidence': 1.0,
            })

        # 2. 权限：世界可写（安全隐患）
        try:
            st = os.stat(fpath)
            import stat
            if st.st_mode & stat.S_IWOTH:
                issues.append({
                    'code': 'BIN_WORLD_WRITABLE',
                    'msg': f'二进制 {ext.upper()} 权限为“其他人可写”（o+w），有被篡改风险（红色波浪线警告）',
                    'severity': 'high', 'confidence': 0.95,
                })
        except Exception:
            pass

        # 3. DLL / LIB 文件魔数检查（Windows DLL / PE 头应该是 MZ）
        if ext.lower() in ('dll', 'lib'):
            try:
                with open(fpath, 'rb') as f:
                    head = f.read(4)
                if size >= 2 and head[:2] != b'MZ':
                    issues.append({
                        'code': 'BIN_INVALID_PE_MAGIC',
                        'msg': f'{ext.upper()} 文件缺少 "MZ" PE/DOS 签名头（可能是损坏的二进制或被误命名）',
                        'severity': 'high', 'confidence': 0.92,
                    })
            except Exception:
                pass

        # 4. .db 文件是否为合法 SQLite （应为 "SQLite format 3\0" 头）
        if ext.lower() == 'db' and size > 0:
            try:
                with open(fpath, 'rb') as f:
                    head = f.read(16)
                if not head.startswith(b'SQLite format 3'):
                    issues.append({
                        'code': 'DB_INVALID_SQLITE_MAGIC',
                        'msg': '.db 文件不含 "SQLite format 3" 头，可能不是 SQLite 数据库或已损坏',
                        'severity': 'medium', 'confidence': 0.9,
                    })
            except Exception:
                pass

        # 5. 异常大小判断
        if ext.lower() == 'db' and size > 0:
            # 如果 .db 很小（< 4KB）且不是 SQLite 头 - 则额外提示
            if size < 4096:
                issues.append({
                    'code': 'DB_SUSPICIOUS_SMALL',
                    'msg': f'.db 文件异常小（仅 {size} 字节），可能是空壳或未正确初始化',
                    'severity': 'low', 'confidence': 0.6,
                })
        if ext.lower() == 'dll' and 0 < size < 1024:
            issues.append({
                'code': 'BIN_SUSPICIOUS_SMALL_DLL',
                'msg': f'DLL 异常小（仅 {size} 字节），可能是占位文件或损坏',
                'severity': 'low', 'confidence': 0.55,
            })

        if not issues:
            return None
        issues.sort(key=lambda x: (
            {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}.get(x.get('severity', 'low'), 9),
            -x.get('confidence', 0)
        ))
        top = issues[0]
        return {
            'issue_type': 'binary_integrity_warning',
            'severity': top.get('severity', 'low'),
            'file_path': fpath,
            'line_number': 0,
            'error_message': top.get('msg', ''),
            'error_code': top.get('code', ''),
            'confidence': top.get('confidence', 0.5),
            '_all_bin_issues': issues,
        }

    @classmethod
    def fix_binary(cls, fpath: str, code: str) -> bool:
        """只修复权限，不修改二进制内容"""
        try:
            if code == 'BIN_WORLD_WRITABLE':
                import stat as _stat
                cur = os.stat(fpath).st_mode
                os.chmod(fpath, cur & ~_stat.S_IWOTH)
                return True
        except Exception:
            pass
        return False


class ASPJSPFixer:
    """.asp / .aspx / .jsp / .htm 等服务端与 HTML 变体文件的检测与修复"""

    @classmethod
    def check_markup(cls, fpath: str, ext: str) -> Optional[Dict]:
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception:
            return None
        lines = content.split('\n')
        issues = []

        # 1. 常见标签平衡检测
        for tag in ('html', 'head', 'body', 'div', 'table', 'tr', 'td', 'ul', 'ol', 'li', 'span', 'form', 'select', 'script', 'style'):
            oc = len(re.findall(rf'<{tag}\b', content, re.IGNORECASE))
            cc = len(re.findall(rf'</{tag}\s*>', content, re.IGNORECASE))
            if abs(oc - cc) > 2:
                issues.append({
                    'code': f'{ext.upper()}_TAG_{tag.upper()}_MISMATCH',
                    'msg': f'<{tag}> 标签不平衡 开{oc} / 闭{cc}（DOM结构问题导致渲染错位）',
                    'severity': 'medium', 'confidence': 0.35, 'line': 0,
                })
                break

        # 2. 服务端脚本块括号平衡（ASP <% %>, ASPX <%@ / <%# ...%>, JSP <% / <%@ ... %>）
        if ext.lower() in ('asp', 'aspx', 'jsp'):
            open_blocks = len(re.findall(r'<%[=:#@\s-]?', content))
            close_blocks = content.count('%>')
            if open_blocks != close_blocks:
                issues.append({
                    'code': f'{ext.upper()}_BLOCK_UNBALANCED',
                    'msg': f'{ext.upper()} 服务端脚本块 <% ... %> 不平衡：开{open_blocks} / 闭{close_blocks}（红色波浪线语法错误）',
                    'severity': 'high', 'confidence': 0.85, 'line': 0,
                })

        # 3. <script> 标签是否闭合（尤其是外部脚本）
        for i, ln in enumerate(lines, 1):
            if re.search(r'<script\b[^>]*src\s*=', ln, re.IGNORECASE):
                if '</script>' not in ln and '</script>' not in ''.join(lines[i:i + 2]):
                    # 只做保守判断
                    pass

        # 4. <form> 内缺失 action 或 method
        forms = re.findall(r'<form\b([^>]*)>', content, re.IGNORECASE)
        for i, fattr in enumerate(forms):
            has_action = re.search(r'\baction\s*=', fattr, re.IGNORECASE)
            has_method = re.search(r'\bmethod\s*=', fattr, re.IGNORECASE)
            if not has_action or not has_method:
                issues.append({
                    'code': 'FORM_ATTR_MISSING',
                    'msg': f'第{i+1}个<form>缺少 action 或 method 属性（可能导致 404 或 GET/POST 不明确）',
                    'severity': 'low', 'confidence': 0.6, 'line': 0,
                })
                break

        if not issues:
            return None
        issues.sort(key=lambda x: (
            {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}.get(x.get('severity', 'low'), 9),
            -x.get('confidence', 0)
        ))
        top = issues[0]
        return {
            'issue_type': f'{ext.lower()}_markup_warning',
            'severity': top.get('severity', 'low'),
            'file_path': fpath,
            'line_number': top.get('line', 0),
            'error_message': top.get('msg', ''),
            'error_code': top.get('code', ''),
            'confidence': top.get('confidence', 0.3),
            '_all_markup_issues': issues,
        }

    @classmethod
    def fix_file(cls, fpath: str, code: str) -> Tuple[bool, str]:
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception:
            return False, ''
        original = content
        method = ''
        new_content = content
        lower = code.upper() if isinstance(code, str) else ''
        if 'BLOCK_UNBALANCED' in lower:
            open_blocks = len(re.findall(r'<%[=:#@\s-]?', new_content))
            close_blocks = new_content.count('%>')
            diff = open_blocks - close_blocks
            if diff > 0:
                new_content = new_content.rstrip() + '\n' + ('%>\n' * diff)
                method = f'append_{diff}_server_block_close'
        if new_content != original and method:
            try:
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return True, method
            except Exception:
                return False, ''
        return False, ''


class TextLintFixer:
    """.txt 文本编码、BOM、尾空格、TAB宽度等问题检测"""

    @classmethod
    def check_text(cls, fpath: str) -> Optional[Dict]:
        try:
            with open(fpath, 'rb') as f:
                raw = f.read()
        except Exception:
            return None
        issues = []

        # BOM 检测（UTF-8 BOM 在 UNIX 环境通常不建议）
        if raw.startswith(b'\xef\xbb\xbf'):
            issues.append({
                'code': 'TXT_UTF8_BOM',
                'msg': '检测到 UTF-8 BOM（EF BB BF），部分脚本/工具会误解析为多余字符，建议移除',
                'severity': 'low', 'confidence': 0.9, 'line': 1,
            })

        # 行尾空格（超过 5 行判定）
        text = raw.decode('utf-8', errors='replace')
        lines = text.split('\n')
        trailing = sum(1 for l in lines if l.rstrip('\r') != l.rstrip('\r').rstrip())
        if trailing >= 5:
            issues.append({
                'code': 'TXT_TRAILING_SPACE',
                'msg': f'共 {trailing} 行存在行尾多余空格，建议清理（避免 diff 噪音）',
                'severity': 'low', 'confidence': 0.95, 'line': 0,
            })

        # Tab 与空格混用
        tab_count = sum(1 for l in lines if '\t' in l)
        space4 = sum(1 for l in lines if l.startswith('    '))
        if tab_count > 0 and space4 > 0:
            issues.append({
                'code': 'TXT_TAB_SPACE_MIX',
                'msg': f'TAB 行 {tab_count} / 4空格缩进行 {space4}，存在混用，建议统一缩进风格',
                'severity': 'medium', 'confidence': 0.9, 'line': 0,
            })

        # CR-only 或 CR+LF 混用（与项目其他文件统一）
        if '\r\n' in text and re.search(r'(?<!\r)\n(?!\r)', text):
            issues.append({
                'code': 'TXT_NEWLINE_MIX',
                'msg': '同时存在 CRLF 与 LF 换行符（建议同一文件内统一）',
                'severity': 'low', 'confidence': 0.9, 'line': 0,
            })

        if not issues:
            return None
        issues.sort(key=lambda x: (
            {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}.get(x['severity'], 9),
            -x['confidence']
        ))
        top = issues[0]
        return {
            'issue_type': 'text_lint_warning',
            'severity': top['severity'],
            'file_path': fpath,
            'line_number': top.get('line', 0),
            'error_message': top['msg'],
            'error_code': top['code'],
            'confidence': top['confidence'],
            '_all_text_issues': issues,
        }

    @classmethod
    def fix_file(cls, fpath: str, code: str) -> Tuple[bool, str]:
        try:
            with open(fpath, 'rb') as f:
                raw = f.read()
        except Exception:
            return False, ''
        original = raw
        new_raw = raw
        method = ''
        if code == 'TXT_UTF8_BOM' and new_raw.startswith(b'\xef\xbb\xbf'):
            new_raw = new_raw[3:]
            method = 'strip_utf8_bom'
        elif code == 'TXT_TRAILING_SPACE':
            text = new_raw.decode('utf-8', errors='replace')
            nl = '\r\n' if '\r\n' in text else '\n'
            cleaned_lines = []
            for ln in re.split(r'\r?\n', text):
                cleaned_lines.append(ln.rstrip())
            text_out = nl.join(cleaned_lines)
            if text and text[-1] in '\r\n':
                text_out += nl
            new_raw = text_out.encode('utf-8')
            method = 'strip_trailing_spaces'
        elif code == 'TXT_NEWLINE_MIX':
            text = new_raw.decode('utf-8', errors='replace')
            # 统一为 LF
            text = text.replace('\r\n', '\n').replace('\r', '\n')
            new_raw = text.encode('utf-8')
            method = 'normalize_newline_lf'
        elif code == 'TXT_TAB_SPACE_MIX':
            text = new_raw.decode('utf-8', errors='replace')
            lines = text.split('\n')
            lines2 = [ln.replace('\t', '    ') for ln in lines]
            if lines2 != lines:
                new_raw = '\n'.join(lines2).encode('utf-8')
                method = 'tabs_to_4spaces'

        if new_raw != original and method:
            try:
                with open(fpath, 'wb') as f:
                    f.write(new_raw)
                return True, method
            except Exception:
                return False, ''
        return False, ''


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

    # 控制台错误严重性评估规则（用于映射为红色波浪线级别）
    _CONSOLE_ERROR_SEVERITY_MAP = {
        # ---- 高严重度（红色波浪线 error 级） ----
        'SyntaxError': 'critical',
        'ReferenceError': 'high',
        'TypeError': 'high',
        'RangeError': 'high',
        'EvalError': 'high',
        'URIError': 'high',
        'InternalError': 'critical',
        'NetworkError': 'high',
        'ResourceError': 'high',
        'LoadFailed': 'high',
        'ChunksLoadError': 'critical',
        'UncaughtException': 'high',
        'unhandledrejection': 'high',
        'RuntimeError': 'high',
        'SecurityError': 'high',
        # ---- 中严重度（橙黄色波浪线 warning 级） ----
        'DeprecationWarning': 'medium',
        'ConsoleWarning': 'medium',
        'PermissionWarning': 'medium',
        'PerformanceWarning': 'medium',
        'CSPViolation': 'medium',
        'MixedContent': 'medium',
        # ---- 低严重度 ----
        'ConsoleInfo': 'low',
        'ConsoleLog': 'low',
        'Hint': 'low',
    }

    @classmethod
    def _classify_console_error(cls, error_data: Dict[str, Any]) -> Tuple[str, str, str]:
        """
        智能分类前端控制台错误，返回 (error_type, severity, ai_suggestion)
        用于红色波浪线级别的提示以及 AI 修复建议
        """
        msg = (error_data.get('message') or error_data.get('msg') or '').strip()
        src_type = error_data.get('type') or error_data.get('sourceType') or ''
        stack = error_data.get('stack') or ''

        error_type = src_type or 'unknown'
        severity = 'medium'
        suggestion = ''

        # 1. 尝试从消息中匹配标准 JS Error 类型
        for name in ('SyntaxError', 'ReferenceError', 'TypeError', 'RangeError',
                     'EvalError', 'URIError', 'InternalError', 'SecurityError'):
            if name in msg or name in stack or name == src_type:
                error_type = name
                severity = cls._CONSOLE_ERROR_SEVERITY_MAP.get(name, 'high')
                if name == 'SyntaxError':
                    suggestion = f'【红色波浪线：语法错误】建议检查 {error_data.get("filename","")} 第 {error_data.get("lineno",0)} 行附近的括号/分号/引号是否匹配，并依据 ESLint/TS 规则修复'
                elif name == 'ReferenceError':
                    suggestion = f'【红色波浪线：引用错误】"{msg[:60]}..." 所引用的变量/函数未定义，请先声明或导入后再使用'
                elif name == 'TypeError':
                    suggestion = f'【红色波浪线：类型错误】"{msg[:60]}"，建议为变量添加类型判空（?.）或类型校验'
                break

        # 2. unhandledrejection / Promise
        if not suggestion and ('unhandledrejection' == src_type or 'UnhandledPromiseRejection' in msg):
            error_type = 'unhandledrejection'
            severity = 'high'
            suggestion = '【红色波浪线：异步Promise异常】请为 Promise/async 函数补齐 .catch(err => ...) 或 try{ await ... }catch(e){}'

        # 3. 资源加载失败（CSS/JS/IMG/FONT）
        if not suggestion and ('Failed to load' in msg or 'LoadFailed' in msg or
                               'net::ERR' in msg or '404' in msg or 'Failed to fetch' in msg):
            error_type = 'ResourceError'
            severity = 'high'
            suggestion = f'【红色波浪线：资源加载失败】请检查静态资源路径/CDN/后端接口可达性，常见原因为：404、CORS、HTTPS混合内容'

        # 4. CSP / 安全违规
        if not suggestion and ('Content Security Policy' in msg or 'CSP' in msg):
            error_type = 'CSPViolation'
            severity = 'medium'
            suggestion = '【波浪线警告：CSP策略违规】请在响应头 Content-Security-Policy 中补充对应资源的 script-src/style-src/img-src 白名单'

        # 5. 废弃 API / 兼容性
        if not suggestion and ('deprecated' in msg.lower() or 'Deprecation' in msg):
            error_type = 'DeprecationWarning'
            severity = 'medium'
            suggestion = '【波浪线警告：废弃API】尽快替换为新API，避免浏览器升级后功能失效（可搜索 MDN 文档确认替代方案）'

        # 6. 兜底未知分类
        if error_type == 'unknown':
            if 'error' in msg.lower():
                error_type = 'RuntimeError'
                severity = 'high'
            elif 'warn' in msg.lower():
                error_type = 'ConsoleWarning'
                severity = 'medium'

        if not suggestion:
            suggestion = f'【控制台错误】类型={error_type}, 位置={error_data.get("filename","")}:{error_data.get("lineno",0)}, 请使用 Chrome DevTools 复现并查看完整堆栈后定位修复'

        return error_type, severity, suggestion

    def report_console_error(self, error_data: Dict[str, Any]) -> str:
        """上报前端控制台错误（含智能分类、严重性评估、红色波浪线级别的 AI 修复建议）"""
        raw_type = error_data.get('type', 'unknown')
        # 执行智能分类
        classified_type, severity, ai_suggestion = self._classify_console_error(error_data)
        # 为后续 AI 修复建议保留入口，写入扩展字段（先塞入 stack_trace 尾部 JSON）
        extra = {
            'severity': severity,
            'ai_suggestion': ai_suggestion,
            'raw_type': raw_type,
        }
        try:
            extra_str = '\n__AI_INSPECT__\n' + json.dumps(extra, ensure_ascii=False)
        except Exception:
            extra_str = ''

        error_id = f"CE-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hashlib.md5(json.dumps(error_data, sort_keys=True).encode()).hexdigest()[:8]}"

        try:
            with _get_conn() as conn:
                c = conn.cursor()
                now = datetime.now().isoformat()
                stack_combined = (str(error_data.get('stack', ''))[:2000] + extra_str)[:3999]
                c.execute(
                    """INSERT OR IGNORE INTO ai_inspection_console_errors
                       (error_id, source, error_type, error_message, stack_trace,
                        file_path, line_number, column_number, user_agent, url, reported_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        error_id,
                        error_data.get('source', 'frontend'),
                        classified_type,
                        (ai_suggestion + ' | DETAIL: ' + error_data.get('message', ''))[:500],
                        stack_combined,
                        error_data.get('filename', ''),
                        error_data.get('lineno', 0),
                        error_data.get('colno', 0),
                        error_data.get('userAgent', '')[:200],
                        error_data.get('url', '')[:300],
                        now,
                    )
                )
                conn.commit()

            # 同步写入巡检 issues 表（用于红色波浪线级别的总览统计 + 自动修复触发）
            try:
                run_id_now = f'console-{datetime.now().strftime("%Y%m%d%H%M%S")}'
                self._bulk_insert_issues(run_id_now, [{
                    'issue_type': 'console_error',
                    'severity': severity,
                    'file_path': error_data.get('filename', '') or error_data.get('url', ''),
                    'line_number': error_data.get('lineno', 0),
                    'error_message': (ai_suggestion + ' | ' + error_data.get('message', ''))[:300],
                    'error_code': f'CONSOLE_{classified_type}',
                    'confidence': 0.88 if severity in ('critical', 'high') else 0.6,
                    'detected_at': now,
                }])
            except Exception:
                pass

            # 上报计数（内存实时统计）
            key = f'console_{classified_type}'
            self._stats['console_errors'] = self._stats.get('console_errors', 0) + 1
            self._stats[key] = self._stats.get(key, 0) + 1
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

        # 将本次 run 中 ide_diagnostic（红色波浪线） 问题二次关联写入 red_wiggles 表（带真正 run_id）
        try:
            wiggle_list = []
            for iss in all_issues:
                if iss.get('issue_type') != 'ide_diagnostic':
                    continue
                if not iss.get('is_red_wiggle') and iss.get('severity') not in ('critical', 'high', 'medium'):
                    continue
                wiggle_list.append({
                    'source_tool': iss.get('source_tool', 'AIInspectionLoop'),
                    'language': {
                        'py': 'python', 'pyc': 'python',
                        'js': 'javascript', 'ts': 'typescript', 'jsx': 'javascript', 'tsx': 'typescript',
                        'css': 'css', 'scss': 'css', 'less': 'css',
                        'html': 'html', 'htm': 'html',
                    }.get(
                        (str(iss.get('file_path', '')).rsplit('.', 1)[-1].lower() if '.' in str(iss.get('file_path', '')) else ''),
                        'mixed'
                    ),
                    'severity': iss.get('severity', 'low'),
                    'severity_icon': iss.get('wiggle_icon') or (
                        '🔴' if iss.get('severity') in ('critical', 'high') else
                        '🟡' if iss.get('severity') == 'medium' else '🔵'
                    ),
                    'file_path': iss.get('file_path', ''),
                    'line_number': iss.get('line_number', 0),
                    'column_number': 0,
                    'end_line': 0,
                    'end_column': 0,
                    'error_code': iss.get('error_code', ''),
                    'rule_id': iss.get('rule_id', ''),
                    'error_message': iss.get('error_message', ''),
                    'suggestion_message': iss.get('suggestion_message', ''),
                    'confidence': iss.get('confidence', 0.0),
                    'auto_fixable': 1 if iss.get('auto_fixable') else 0,
                })
            if wiggle_list:
                self._bulk_insert_red_wiggles(run_id, wiggle_list)
        except Exception:
            pass

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

                # Markdown / Markup 文件
                elif fname.endswith(('.md', '.markdown')):
                    file_count += 1
                    issue = MarkdownFixer.check_markdown(fpath)
                    if issue:
                        issues.append(issue)

                # SQL 文件
                elif fname.endswith('.sql'):
                    file_count += 1
                    issue = SQLFixer.check_sql(fpath)
                    if issue:
                        issues.append(issue)

                # PHP 文件
                elif fname.endswith('.php'):
                    file_count += 1
                    issue = PHPFixer.check_php(fpath)
                    if issue:
                        issues.append(issue)

                # C / C++ 头文件与源文件
                elif fname.endswith(('.c', '.h')):
                    file_count += 1
                    issue = CSourceFixer.check_c_h(fpath)
                    if issue:
                        issues.append(issue)

                # 纯文本文件（文档/说明/配置）
                elif fname.endswith('.txt'):
                    # 跳过超大文本
                    try:
                        if os.path.getsize(fpath) > 2 * 1024 * 1024:
                            file_count += 1
                            continue
                    except Exception:
                        pass
                    file_count += 1
                    issue = TextLintFixer.check_text(fpath)
                    if issue:
                        issues.append(issue)

                # HTML 变体 + 服务端模板（htm/asp/aspx/jsp）
                elif fname.endswith(('.htm', '.asp', '.aspx', '.jsp')):
                    ext = fname.rsplit('.', 1)[-1].lower()
                    file_count += 1
                    issue = ASPJSPFixer.check_markup(fpath, ext)
                    if issue:
                        issues.append(issue)

                # 二进制文件：dll / lib / db （只检测，不读文本内容）
                elif fname.endswith(('.dll', '.lib', '.db')):
                    ext = fname.rsplit('.', 1)[-1].lower()
                    file_count += 1
                    # .db 排除 data/databases 下的运行时数据库（避免无意义扫描）
                    if ext == 'db' and ('data' + os.sep + 'databases') in fpath:
                        continue
                    issue = BinaryScanner.scan_binary(fpath, ext)
                    if issue:
                        issues.append(issue)

        # 扫描IDE诊断结果（basedpyright错误）
        ide_issues = self._scan_ide_diagnostics()
        issues.extend(ide_issues)

        return issues, file_count

    _WIGGLE_SEVERITY_ICON = {
        'critical': '🔴',
        'high': '🔴',
        'error': '🔴',
        'medium': '🟡',
        'warning': '🟡',
        'low': '🔵',
        'info': '🔵',
        'hint': '🟢',
        'information': '🔵',
    }

    def _scan_ide_diagnostics(self) -> List[Dict]:
        """
        扫描所有有红色/黄色波浪线提示的文件（IDE诊断级别）。
        支持：Python (basedpyright) + JS/TS(ESLint/回退到语法检查) + CSS(Stylelint/回退到CSSFixer) + HTML(HTMLFixer)
        扫描结果同步写入 issues + red_wiggles 两张表。
        """
        issues: List[Dict] = []
        wiggles: List[Dict] = []
        now_str = datetime.now().isoformat()
        skip_dirs = {'__pycache__', '.git', 'node_modules', 'venv', '.venv', 'flask-app-old', 'logs', 'data',
                     'cross_platform_node_modules', 'static', 'dist', 'build', 'exam_app_node_modules', 'backups', 'Backups'}

        # ----------- 1. Python：basedpyright 全项目扫描 -----------
        py_count, py_wiggles, py_issues = self._scan_python_diagnostics(skip_dirs, now_str)
        wiggles.extend(py_wiggles)
        issues.extend(py_issues)

        # ----------- 2. JS/TS：ESLint 或 JSFixer 回退扫描 -----------
        js_count, js_wiggles, js_issues = self._scan_js_diagnostics(skip_dirs, now_str)
        wiggles.extend(js_wiggles)
        issues.extend(js_issues)

        # ----------- 3. CSS：Stylelint 或 CSSFixer 回退扫描 -----------
        css_count, css_wiggles, css_issues = self._scan_css_diagnostics(skip_dirs, now_str)
        wiggles.extend(css_wiggles)
        issues.extend(css_issues)

        # ----------- 4. HTML：HTMLFixer 语法扫描 -----------
        html_count, html_wiggles, html_issues = self._scan_html_diagnostics(skip_dirs, now_str)
        wiggles.extend(html_wiggles)
        issues.extend(html_issues)

        # 一次性批量写入红色波浪线专门表（若 run_id 未知则用临时占位，主流程里会二次关联）
        try:
            # 临时 run_id；主流程 _full_inspection_cycle 里会在之后再次调用一次红色波浪线写入来关联真正 run_id
            self._bulk_insert_red_wiggles(f"wiggle-{datetime.now().strftime('%Y%m%d%H%M%S')}", wiggles)
        except Exception:
            pass

        # 实时统计写入内存计数器
        self._stats['wiggle_scan_py'] = py_count
        self._stats['wiggle_scan_js'] = js_count
        self._stats['wiggle_scan_css'] = css_count
        self._stats['wiggle_scan_html'] = html_count
        self._stats['wiggle_total'] = len(wiggles)
        self._stats['wiggle_red'] = sum(1 for w in wiggles if w.get('severity_icon') == '🔴')
        self._stats['wiggle_yellow'] = sum(1 for w in wiggles if w.get('severity_icon') == '🟡')

        return issues

    def _list_files(self, skip_dirs: set, exts: tuple) -> List[str]:
        """列出项目下所有指定扩展名的源文件"""
        result = []
        for root, dirs, files in os.walk(_PROJECT_ROOT):
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
            for fname in files:
                if fname.endswith(exts):
                    result.append(os.path.join(root, fname))
        return result

    def _to_wiggle_issue(self, *, source_tool, language, severity, file_path, line_no=0, col_no=0,
                         end_line=0, end_col=0, error_code='', rule_id='', error_message='',
                         suggestion_message='', confidence=0.8, auto_fixable=False, detected_at='',
                         extra=None) -> Tuple[Dict, Dict]:
        """构造统一的 (red_wiggle, issue) 二元组，带红色波浪线标记与图标"""
        sev = severity.lower() if isinstance(severity, str) else 'low'
        icon = self._WIGGLE_SEVERITY_ICON.get(sev, '🔵')
        is_red = icon == '🔴'
        issue_sev = 'critical' if sev == 'critical' else (
            'high' if sev in ('high', 'error') else
            'medium' if sev in ('medium', 'warning') else 'low'
        )
        wiggle = {
            'source_tool': source_tool,
            'language': language,
            'severity': issue_sev,
            'severity_icon': icon,
            'file_path': file_path,
            'line_number': line_no,
            'column_number': col_no,
            'end_line': end_line,
            'end_column': end_col,
            'error_code': error_code,
            'rule_id': rule_id,
            'error_message': error_message[:500],
            'suggestion_message': suggestion_message[:500],
            'confidence': confidence,
            'auto_fixable': auto_fixable,
            'detected_at': detected_at,
        }
        if extra:
            wiggle.update(extra)
        issue = {
            'issue_type': 'ide_diagnostic',
            'severity': issue_sev,
            'file_path': file_path,
            'line_number': line_no,
            'error_message': (f'【红色波浪线·{icon} {language}/{rule_id or error_code}】{error_message}' if is_red else f'【{icon}波浪线·{language}】{error_message}')[:500],
            'error_code': error_code or f'WIGGLE_{language.upper()}',
            'confidence': confidence,
            'is_red_wiggle': 1 if is_red else 0,
            'wiggle_icon': icon,
            'source_tool': source_tool,
            'rule_id': rule_id,
            'suggestion_message': suggestion_message,
            'auto_fixable': auto_fixable,
            'detected_at': detected_at,
        }
        return wiggle, issue

    def _scan_python_diagnostics(self, skip_dirs: set, now_str: str):
        """Python 红色波浪线扫描（优先 basedpyright -> 回退 PythonSyntaxFixer ast）"""
        import subprocess as _subp
        import json as _json
        wiggles, issues = [], []
        py_files = self._list_files(skip_dirs, ('.py',))
        # 限制最多 200 个 py 文件（超时保护）
        py_files = py_files[:200]

        for fpath in py_files:
            # 跳过根目录下的调试脚本与 fix 脚本（移动目录时的临时残留已处理，这里仅加保护）
            try:
                rel = os.path.relpath(fpath, _PROJECT_ROOT)
                if (rel.count(os.sep) == 0 and (
                    rel.startswith('_') or rel.startswith('fix_') or rel.endswith('_db.py')
                )):
                    continue
            except Exception:
                pass
            try:
                size = os.path.getsize(fpath)
                if size > 3 * 1024 * 1024:
                    continue
            except Exception:
                continue

            # 先 AST 语法检查（快速）
            ast_issue = self._check_python_syntax(fpath)
            if ast_issue is not None:
                w, i = self._to_wiggle_issue(
                    source_tool='py_ast', language='python',
                    severity=ast_issue.get('severity', 'high'),
                    file_path=fpath, line_no=ast_issue.get('line_number', 0),
                    error_code=ast_issue.get('error_code', 'PY_SYNTAX'),
                    error_message=ast_issue.get('error_message', ''),
                    suggestion_message='【红色波浪线·语法】建议修复括号/缩进/冒号，可用 PythonSyntaxFixer 自动修复',
                    confidence=1.0, auto_fixable=True, detected_at=now_str,
                )
                wiggles.append(w)
                issues.append(i)
                # AST 已报严重错误，不再跑 basedpyright
                continue

            # 再基于 basedpyright（限制单文件 20s 超时，失败静默跳过）
            try:
                r = _subp.run(
                    ['npx', 'basedpyright', '--outputjson', fpath],
                    cwd=_PROJECT_ROOT, capture_output=True, text=True, timeout=20
                )
                if not r.stdout:
                    continue
                try:
                    data = _json.loads(r.stdout)
                except _json.JSONDecodeError:
                    continue
                for diag in data.get('generalDiagnostics', []):
                    message = diag.get('message', '')
                    # 跳过仅“模块未找到”类纯环境问题
                    rule = diag.get('rule', '') or ''
                    if '无法从源码解析导入' in message or rule in ('reportMissingModuleSource',):
                        continue
                    severity = diag.get('severity', 'warning')
                    line = diag.get('range', {}).get('start', {}).get('line', 0)
                    col = diag.get('range', {}).get('start', {}).get('character', 0)
                    end_line = diag.get('range', {}).get('end', {}).get('line', line)
                    end_col = diag.get('range', {}).get('end', {}).get('character', col)
                    code = str(diag.get('code', '') or rule)
                    auto = rule in ('reportMissingImports',) and False  # 导入问题通常不自动修复
                    suggestion = ''
                    if '缩进' in message or 'Indentation' in message:
                        suggestion = '【红色波浪线建议】检查当前行缩进，统一使用 4 空格（不要混用 Tab）'
                    elif '类型' in message or 'Type' in message or 'is not' in message:
                        suggestion = '【波浪线建议】补充类型注解或使用 assert/cast，或者添加 # type: ignore 用于临时豁免'
                    elif '未使用' in message or 'Unused' in message:
                        suggestion = '【波浪线建议】若确有必要可改用 `_` 前缀变量名或添加 noqa 注释'
                    w, i = self._to_wiggle_issue(
                        source_tool='basedpyright', language='python',
                        severity=severity, file_path=fpath,
                        line_no=line + 1, col_no=col + 1,
                        end_line=end_line + 1, end_col=end_col + 1,
                        error_code=code or f'PY_{rule or "DIAG"}',
                        rule_id=rule,
                        error_message=message,
                        suggestion_message=suggestion or f'【波浪线建议】查阅 basedpyright 文档或修复：{message[:120]}',
                        confidence=0.92, auto_fixable=auto, detected_at=now_str,
                    )
                    wiggles.append(w)
                    issues.append(i)
            except (_subp.TimeoutExpired, Exception):
                continue
        return len(py_files), wiggles, issues

    def _scan_js_diagnostics(self, skip_dirs: set, now_str: str):
        """JS/TS 红色波浪线扫描（回退 JSFixer.check_js_syntax）"""
        wiggles, issues = [], []
        js_files = self._list_files(skip_dirs, ('.js', '.ts', '.jsx', '.tsx'))
        js_files = [f for f in js_files if not re.search(r'(\.min\.js|-[a-f0-9]{8,}\.js|index-\w+\.js)', os.path.basename(f))]
        # 过滤掉 > 500KB 的大文件
        filtered = []
        for f in js_files:
            try:
                if os.path.getsize(f) <= 500 * 1024:
                    filtered.append(f)
            except Exception:
                continue
        js_files = filtered[:300]
        for fpath in js_files:
            try:
                diag = JSFixer.check_js_syntax(fpath)
                if diag is None:
                    continue
                # 红色波浪线级别：MISSING_SEMICOLON/UNCLOSED 等为高，其余中
                code = diag.get('error_code', '')
                is_red = any(k in code for k in ('UNCLOSED', 'SYNTAX', 'PAREN', 'BRACE', 'BRACKET'))
                severity = 'high' if is_red else (
                    'medium' if code in ('MISSING_SEMICOLON', 'TRAILING_COMMA', 'EMPTY_BLOCK') else 'low'
                )
                w, i = self._to_wiggle_issue(
                    source_tool='JSFixer', language='javascript',
                    severity=severity, file_path=fpath,
                    line_no=diag.get('line_number', 0),
                    error_code=code,
                    error_message=diag.get('error_message', ''),
                    suggestion_message='【红色波浪线·JS】可通过 JSFixer 自动修复；或使用 ESLint --fix 再次收敛',
                    confidence=diag.get('confidence', 0.75),
                    auto_fixable=True, detected_at=now_str,
                )
                wiggles.append(w)
                issues.append(i)
                # 若有全部子问题（_all_js_issues）逐个补充
                extras = diag.get('_all_js_issues') or []
                for sub in extras[1:10]:
                    sub_code = sub.get('code', '')
                    is_red2 = any(k in sub_code for k in ('UNCLOSED', 'SYNTAX', 'PAREN', 'BRACE'))
                    sev2 = 'high' if is_red2 else 'medium'
                    w2, i2 = self._to_wiggle_issue(
                        source_tool='JSFixer', language='javascript',
                        severity=sev2, file_path=fpath,
                        line_no=sub.get('line', 0),
                        error_code=sub_code,
                        error_message=sub.get('msg', ''),
                        suggestion_message='【波浪线·JS】建议配合 ESLint 规则统一修复',
                        confidence=sub.get('confidence', 0.7),
                        auto_fixable=True, detected_at=now_str,
                    )
                    wiggles.append(w2)
                    issues.append(i2)
            except Exception:
                continue
        return len(js_files), wiggles, issues

    def _scan_css_diagnostics(self, skip_dirs: set, now_str: str):
        """CSS 红色波浪线扫描（回退 CSSFixer.check_css_syntax）"""
        wiggles, issues = [], []
        css_files = self._list_files(skip_dirs, ('.css', '.scss', '.less'))
        css_files = [f for f in css_files if not f.endswith('.min.css')]
        css_files = css_files[:200]
        for fpath in css_files:
            try:
                diag = CSSFixer.check_css_syntax(fpath)
                if diag is None:
                    continue
                code = diag.get('error_code', '')
                is_red = any(k in code for k in ('BRACE', 'UNCLOSED', 'SYNTAX'))
                severity = 'high' if is_red else (
                    'medium' if code in ('MISSING_SEMICOLON', 'EMPTY_SELECTOR') else 'low'
                )
                w, i = self._to_wiggle_issue(
                    source_tool='CSSFixer', language='css',
                    severity=severity, file_path=fpath,
                    line_no=diag.get('line_number', 0),
                    error_code=code,
                    error_message=diag.get('error_message', ''),
                    suggestion_message='【红色波浪线·CSS】可通过 CSSFixer 自动修复补全括号/分号',
                    confidence=diag.get('confidence', 0.8),
                    auto_fixable=True, detected_at=now_str,
                )
                wiggles.append(w)
                issues.append(i)
                extras = diag.get('_all_css_issues') or []
                for sub in extras[1:10]:
                    sub_code = sub.get('code', '')
                    sev2 = 'high' if any(k in sub_code for k in ('BRACE', 'UNCLOSED')) else 'medium'
                    w2, i2 = self._to_wiggle_issue(
                        source_tool='CSSFixer', language='css',
                        severity=sev2, file_path=fpath,
                        line_no=sub.get('line', 0), error_code=sub_code,
                        error_message=sub.get('msg', ''),
                        suggestion_message='【波浪线·CSS】建议配合 Stylelint 再次扫描',
                        confidence=sub.get('confidence', 0.7),
                        auto_fixable=True, detected_at=now_str,
                    )
                    wiggles.append(w2)
                    issues.append(i2)
            except Exception:
                continue
        return len(css_files), wiggles, issues

    def _scan_html_diagnostics(self, skip_dirs: set, now_str: str):
        """HTML/HTM/模板红色波浪线扫描（HTMLFixer._check_html_basic 内部方法复用）"""
        wiggles, issues = [], []
        html_files = self._list_files(skip_dirs, ('.html', '.htm'))
        html_files = html_files[:200]
        # 匹配到这些 code 即强制为 🔴 high（会直接触发 IDE 红色波浪线）
        HTML_FORCE_HIGH_CODES = {
            'INLINE_STYLE_TEMPLATE', 'INLINE_STYLE_TEMPLATE_AGG',
            'EVENT_QUOTE_MISMATCH', 'HTML_TAG_MISMATCH', 'STYLE_BLOCK_CSS',
            'SCRIPT_BRACKET', 'INLINE_CSS_PROP',
        }
        for fpath in html_files:
            try:
                diag = self._check_html_basic(fpath)
                if diag is None:
                    continue
                code = diag.get('error_code', '')
                # 优先使用 diag 自带 severity，其次根据 code 升级
                severity = diag.get('severity') or 'medium'
                if code in HTML_FORCE_HIGH_CODES or severity in ('critical', 'high'):
                    severity = 'high'
                w, i = self._to_wiggle_issue(
                    source_tool='HTMLFixer', language='html',
                    severity=severity, file_path=fpath,
                    line_no=diag.get('line_number', 0),
                    error_code=code,
                    error_message=diag.get('error_message', ''),
                    suggestion_message='【红色波浪线·HTML】可通过 HTMLFixer 自动修复闭合标签',
                    confidence=diag.get('confidence', 0.78),
                    auto_fixable=True, detected_at=now_str,
                )
                wiggles.append(w)
                issues.append(i)
                extras = diag.get('_all_html_issues') or []
                for sub in extras[1:15]:
                    sub_code = sub.get('code', '')
                    # force_code 优先级 > 子问题自带 severity
                    if sub_code in HTML_FORCE_HIGH_CODES:
                        sev2 = 'high'
                    else:
                        sev2 = sub.get('severity') or 'medium'
                    if sev2 not in ('critical', 'high', 'medium', 'low', 'warning', 'error'):
                        sev2 = 'medium'
                    w2, i2 = self._to_wiggle_issue(
                        source_tool='HTMLFixer', language='html',
                        severity=sev2, file_path=fpath,
                        line_no=sub.get('line', 0), error_code=sub_code,
                        error_message=sub.get('msg', ''),
                        suggestion_message='【波浪线·HTML】建议配合 htmlhint 或模板引擎语法再次扫描',
                        confidence=sub.get('confidence', 0.68),
                        auto_fixable=True, detected_at=now_str,
                    )
                    wiggles.append(w2)
                    issues.append(i2)
            except Exception:
                continue
        return len(html_files), wiggles, issues

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

    # 会触发 IDE CSS 红色波浪线的「现代 CSS 新语法」（IDE 内置 CSS 解析器不支持或支持不全）
    _CSS_NEW_SYNTAX_PATTERNS = [
        (re.compile(r'color-mix\s*\(\s*in\s+', re.IGNORECASE), 'CSS_COLOR_MIX', 'CSS Color 5 color-mix()，IDE 旧解析器会报「应为 @ 规则或选择器」'),
        (re.compile(r'\boklch\s*\(', re.IGNORECASE), 'CSS_OKLCH', 'CSS Color 5 oklch()，部分 CSS 解析器不支持'),
        (re.compile(r'\boklab\s*\(', re.IGNORECASE), 'CSS_OKLAB', 'CSS Color 5 oklab()，部分 CSS 解析器不支持'),
        (re.compile(r'\blch\s*\(', re.IGNORECASE), 'CSS_LCH', 'CSS Color 5 lch()，部分 CSS 解析器不支持'),
        (re.compile(r'\blab\s*\(', re.IGNORECASE), 'CSS_LAB', 'CSS Color 5 lab()，部分 CSS 解析器不支持'),
        (re.compile(r'\bcolor-contrast\s*\(', re.IGNORECASE), 'CSS_COLOR_CONTRAST', 'CSS Color 5 color-contrast()，极少浏览器/解析器支持'),
        (re.compile(r':is\s*\(', re.IGNORECASE), 'CSS_PSEUDO_IS', ':is() 伪类函数，旧 CSS 解析器会误报'),
        (re.compile(r':where\s*\(', re.IGNORECASE), 'CSS_PSEUDO_WHERE', ':where() 伪类函数，旧 CSS 解析器会误报'),
        (re.compile(r':has\s*\(', re.IGNORECASE), 'CSS_PSEUDO_HAS', ':has() 父级选择器，部分解析器会误报'),
        (re.compile(r'\bvar\s*\([^)]*var\s*\(', re.IGNORECASE), 'CSS_NESTED_VAR', '嵌套 var() 可能触发解析错误'),
        (re.compile(r'@container\b', re.IGNORECASE), 'CSS_CONTAINER', '@container 查询，部分 CSS 解析器会误报'),
        (re.compile(r'@property\b', re.IGNORECASE), 'CSS_PROPERTY', '@property 规则，少数 CSS 解析器不支持'),
        (re.compile(r'@layer\b', re.IGNORECASE), 'CSS_LAYER', '@layer 层叠层，少数 CSS 解析器不支持'),
        (re.compile(r'\bclamp\s*\(', re.IGNORECASE), 'CSS_CLAMP', 'clamp() 新函数，可能被误报为缺 }'),
        (re.compile(r'\bmin\s*\([^),]+,[^)]+,[^)]*\)', re.IGNORECASE), 'CSS_MIN_MULTI', 'min() 多参数 CSS 函数'),
        (re.compile(r'\bmax\s*\([^),]+,[^)]+,[^)]*\)', re.IGNORECASE), 'CSS_MAX_MULTI', 'max() 多参数 CSS 函数'),
    ]

    def _check_html_basic(self, fpath: str) -> Optional[Dict]:
        """HTML 全面检测 - 结构、内联CSS模板语法、内联事件、CSS新语法、style/script块等（带精确行号）"""
        try:
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception:
            return None

        all_issues = []
        is_template = bool(re.search(r'{%\s*(if|for|set|include|extends|macro)', content) or '{{' in content)
        conf_mult = 0.55 if is_template else 1.0

        # 先获取每行内容 & 累计行号偏移，便于回溯精确行/列
        lines = content.split('\n')
        line_offsets = [0]
        acc = 0
        for ln in lines:
            acc += len(ln) + 1
            line_offsets.append(acc)

        def _offset_to_line_col(offset):
            import bisect as _bs
            idx = _bs.bisect_right(line_offsets, offset) - 1
            if idx < 0:
                idx = 0
            if idx >= len(lines):
                idx = len(lines) - 1
            col = offset - line_offsets[idx]
            return idx + 1, max(0, col) + 1  # 行列 1-based

        # -------- 1. 行级扫描：style 属性、on* 事件处理器、模板语法、CSS 新语法 --------
        inline_style_template_count = 0
        inline_event_css_syntax_count = 0
        inline_css_prop_issues = 0
        inline_style_new_syntax_count = 0

        # 提取所有 style="..." 属性（含引号内跨越多行的情况）
        for m in re.finditer(r'style\s*=\s*(["\'])((?:\\.|(?!\1).)*)\1', content, re.DOTALL | re.IGNORECASE):
            quote = m.group(1)
            style_value = m.group(2)
            start_line, start_col = _offset_to_line_col(m.start())
            has_template = ('{%' in style_value) or ('{{' in style_value)
            # CSS 新语法扫描
            new_syntax_hits = []
            for rx, code, desc in self._CSS_NEW_SYNTAX_PATTERNS:
                if rx.search(style_value):
                    new_syntax_hits.append((code, desc, start_line, start_col))
            # 属性/冒号/分号 校验
            prop_ok = True
            props = [p.strip() for p in style_value.split(';') if p.strip()]
            for prop in props:
                if ':' not in prop:
                    prop_ok = False
                    break
                kv = prop.split(':', 1)
                if len(kv) == 2 and not kv[1].strip():
                    prop_ok = False
                    break
            if not prop_ok:
                inline_css_prop_issues += 1
                all_issues.append({
                    'code': 'INLINE_CSS_PROP',
                    'msg': f'内联 style 属性缺少「:」或「属性值为空」（可能触发 IDE CSS 红色波浪线：需要冒号/预期有标识符）',
                    'severity': 'medium', 'confidence': 0.78 * conf_mult,
                    'line': start_line, 'col': start_col,
                })
            if has_template:
                inline_style_template_count += 1
                markers = style_value.count('{%') + style_value.count('{{')
                all_issues.append({
                    'code': 'INLINE_STYLE_TEMPLATE',
                    'msg': '内联 style 属性中包含 Jinja2 模板语法（' + str(markers) + '处），'
                           'IDE CSS 解析器会报红：「预期有标识符 / 应为 @ 规则或选择器 / 应有 }」'
                           '（建议：将动态样式改为 CSS 类，在 <style> 或 .css 文件中通过 :root 变量切换）',
                    'severity': 'high', 'confidence': 0.92,
                    'line': start_line, 'col': start_col,
                })
            for code, desc, ln, col in new_syntax_hits:
                inline_style_new_syntax_count += 1
                all_issues.append({
                    'code': code,
                    'msg': f'内联 style 中包含 {desc}，可能触发 IDE CSS 解析器红色波浪线误报',
                    'severity': 'medium', 'confidence': 0.82,
                    'line': ln, 'col': col,
                })

        # 提取所有 on*="..." 事件处理器
        for m in re.finditer(
            r'\son(click|dblclick|mouse(?:over|out|down|up|move|enter|leave)|key(?:down|up|press)|'
            r'focus|blur|change|input|submit|load|error|scroll|resize|drag(?:start|end|over)?|'
            r'drop|touch(?:start|end|move)|contextmenu|copy|cut|paste)\s*=\s*(["\'])((?:\\.|(?!\2).)*)\2',
            content, re.DOTALL | re.IGNORECASE
        ):
            attr_name = m.group(1).lower()
            attr_value = m.group(3)
            start_line, start_col = _offset_to_line_col(m.start())
            inner_quote = '"' if m.group(2) == '"' else "'"
            raw = attr_value.replace('\\"', '').replace("\\'", '')
            if inner_quote in raw:
                all_issues.append({
                    'code': 'EVENT_QUOTE_MISMATCH',
                    'msg': f'on{attr_name} 事件处理器内再次使用属性级引号（{inner_quote}），可能导致 JS/CSS 解析异常与红色波浪线',
                    'severity': 'high', 'confidence': 0.88,
                    'line': start_line, 'col': start_col,
                })
            for rx, code, desc in self._CSS_NEW_SYNTAX_PATTERNS:
                if rx.search(attr_value):
                    inline_event_css_syntax_count += 1
                    all_issues.append({
                        'code': code,
                        'msg': f'on{attr_name} 事件处理器中包含 {desc}，与内联 style 叠加时可能放大 IDE 红色波浪线误报',
                        'severity': 'medium', 'confidence': 0.8,
                        'line': start_line, 'col': start_col,
                    })
                    break

        # -------- 2. 常见标签平衡检测 --------
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
                'confidence': 0.35 * conf_mult,
                'line': 1, 'col': 1,
            })

        # -------- 3. <style> 标签内 CSS 检测（含新语法） --------
        style_blocks = list(re.finditer(r'<style[^>]*>(.*?)</style>', content, re.DOTALL | re.IGNORECASE))
        for i, m in enumerate(style_blocks):
            style_content = m.group(1)
            start_line, _ = _offset_to_line_col(m.start())
            clean_css = style_content
            if is_template:
                clean_css = CSSFixer._strip_template_syntax(style_content)
            open_b = clean_css.count('{')
            close_b = clean_css.count('}')
            if open_b != close_b and abs(open_b - close_b) > 1:
                all_issues.append({
                    'code': 'STYLE_BLOCK_CSS',
                    'msg': f'第{i+1}个style块大括号不平衡({open_b}/{close_b})，可能触发 IDE 「应有 }}」红色波浪线',
                    'severity': 'medium',
                    'confidence': 0.55 * conf_mult,
                    'line': start_line,
                })
            for rx, code, desc in self._CSS_NEW_SYNTAX_PATTERNS:
                mm = rx.search(style_content)
                if mm:
                    ln_off = m.start(1) + mm.start()
                    ln, col = _offset_to_line_col(ln_off)
                    all_issues.append({
                        'code': code,
                        'msg': f'style 块内包含 {desc}，可能触发 IDE CSS 解析器红色波浪线误报',
                        'severity': 'medium', 'confidence': 0.8,
                        'line': ln, 'col': col,
                    })

        # -------- 4. <script> 标签检测 --------
        script_blocks = list(re.finditer(r'<script[^>]*>(.*?)</script>', content, re.DOTALL | re.IGNORECASE))
        for i, m in enumerate(script_blocks):
            script_content = m.group(1)
            if script_content.strip() == '':
                continue
            start_line, _ = _offset_to_line_col(m.start())
            clean_js = script_content
            if is_template:
                clean_js = re.sub(r'{%.*?%}', '', clean_js, flags=re.DOTALL)
                clean_js = re.sub(r'{{.*?}}', '""', clean_js)
            for open_c, close_c, name in [('{', '}', '大括号'), ('(', ')', '圆括号'), ('[', ']', '方括号')]:
                open_count = clean_js.count(open_c)
                close_count = clean_js.count(close_c)
                if open_count != close_count and abs(open_count - close_count) > 2:
                    all_issues.append({
                        'code': 'SCRIPT_BRACKET',
                        'msg': f'第{i+1}个script块{name}不平衡({open_count}/{close_count})，'
                               f'IDE JS 解析器会产生「预期标识符/应有 }}/未闭合的语句块」等红色波浪线',
                        'severity': 'medium',
                        'confidence': 0.5 * conf_mult,
                        'line': start_line,
                    })
                    break

        # -------- 5. 汇总统计性问题（聚合到总览） --------
        if inline_style_template_count > 0:
            all_issues.append({
                'code': 'INLINE_STYLE_TEMPLATE_AGG',
                'msg': f'文件中共发现 {inline_style_template_count} 处内联 style 含模板语法（IDE CSS 红色波浪线的最常见成因）',
                'severity': 'high', 'confidence': 0.95,
                'line': 1,
            })
        if inline_style_new_syntax_count > 0:
            all_issues.append({
                'code': 'INLINE_STYLE_NEW_SYNTAX_AGG',
                'msg': f'文件中共发现 {inline_style_new_syntax_count} 处 CSS Color 5 / 现代 CSS 函数（可能触发 IDE 解析器误报红色波浪线）',
                'severity': 'medium', 'confidence': 0.86,
                'line': 1,
            })
        if inline_event_css_syntax_count > 0:
            all_issues.append({
                'code': 'EVENT_CSS_SYNTAX_AGG',
                'msg': f'事件处理器中共 {inline_event_css_syntax_count} 处与 CSS 新语法叠加，可能放大红色波浪线',
                'severity': 'medium', 'confidence': 0.78,
                'line': 1,
            })

        if all_issues:
            all_issues.sort(key=lambda x: (
                {'critical': 5, 'high': 4, 'medium': 3, 'low': 2, 'info': 1}.get(x.get('severity', 'low'), 0),
                x.get('confidence', 0)
            ), reverse=True)
            top = all_issues[0]
            return {
                'issue_type': 'html_structure_warning',
                'severity': top.get('severity', 'low'),
                'file_path': fpath,
                'line_number': top.get('line', 0),
                'error_message': top.get('msg', ''),
                'error_code': top.get('code', 'HTML_WARN'),
                'confidence': top.get('confidence', 0.5),
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

            # Markdown 语法警告 - 使用 MarkdownFixer
            elif issue_type == 'markdown_syntax_warning' and issue.get('confidence', 0) >= 0.4:
                success = self._fix_markdown(issue)
                if success:
                    fixed += 1
                    self._mark_fixed(issue, issue.get('fix_method', 'auto_markdown_fix'), 'success')
                else:
                    failed += 1
                    self._mark_fixed(issue, 'auto_markdown_fix', 'failed')

            # SQL 语法错误 - 使用 SQLFixer
            elif issue_type == 'sql_syntax_error' and issue.get('confidence', 0) >= 0.6:
                success = self._fix_sql(issue)
                if success:
                    fixed += 1
                    self._mark_fixed(issue, issue.get('fix_method', 'auto_sql_fix'), 'success')
                else:
                    failed += 1
                    self._mark_fixed(issue, 'auto_sql_fix', 'failed')

            # PHP 语法错误 - 使用 PHPFixer
            elif issue_type == 'php_syntax_error' and issue.get('confidence', 0) >= 0.5:
                success = self._fix_php(issue)
                if success:
                    fixed += 1
                    self._mark_fixed(issue, issue.get('fix_method', 'auto_php_fix'), 'success')
                else:
                    failed += 1
                    self._mark_fixed(issue, 'auto_php_fix', 'failed')

            # C/C++ 源码警告 - 使用 CSourceFixer
            elif issue_type == 'c_source_warning' and issue.get('confidence', 0) >= 0.5:
                success = self._fix_c_source(issue)
                if success:
                    fixed += 1
                    self._mark_fixed(issue, issue.get('fix_method', 'auto_c_fix'), 'success')
                else:
                    failed += 1
                    self._mark_fixed(issue, 'auto_c_fix', 'failed')

            # 二进制完整性警告 - 使用 BinaryScanner（只修权限，不改内容）
            elif issue_type == 'binary_integrity_warning' and issue.get('confidence', 0) >= 0.8:
                success = self._fix_binary(issue)
                if success:
                    fixed += 1
                    self._mark_fixed(issue, issue.get('fix_method', 'auto_binary_fix'), 'success')
                else:
                    failed += 1
                    self._mark_fixed(issue, 'auto_binary_fix', 'failed')

            # ASP/ASPX/JSP/HTM 标记类警告 - 使用 ASPJSPFixer
            elif issue_type in ('htm_markup_warning', 'asp_markup_warning', 'aspx_markup_warning', 'jsp_markup_warning') and issue.get('confidence', 0) >= 0.4:
                success = self._fix_markup(issue)
                if success:
                    fixed += 1
                    self._mark_fixed(issue, issue.get('fix_method', 'auto_markup_fix'), 'success')
                else:
                    failed += 1
                    self._mark_fixed(issue, 'auto_markup_fix', 'failed')

            # 文本检查警告 - 使用 TextLintFixer（保守修复）
            elif issue_type == 'text_lint_warning' and issue.get('confidence', 0) >= 0.7:
                success = self._fix_text(issue)
                if success:
                    fixed += 1
                    self._mark_fixed(issue, issue.get('fix_method', 'auto_text_fix'), 'success')
                else:
                    failed += 1
                    self._mark_fixed(issue, 'auto_text_fix', 'failed')

            # IDE 诊断（红色/黄色波浪线）：按 source_tool + 文件后缀路由到对应修复器
            elif issue_type == 'ide_diagnostic' and issue.get('auto_fixable', True):
                fpath = issue.get('file_path', '')
                ext = (fpath.rsplit('.', 1)[-1].lower()) if '.' in fpath else ''
                success = False
                try:
                    if ext == 'py' or issue.get('source_tool') in ('basedpyright', 'py_ast'):
                        success = self._fix_python_syntax(issue)
                        if success:
                            method = issue.get('fix_method') or 'auto_py_wiggle_fix'
                    elif ext in ('js', 'ts', 'jsx', 'tsx') or issue.get('source_tool') == 'JSFixer':
                        success = self._fix_js_syntax(issue)
                        if success:
                            method = issue.get('fix_method') or 'auto_js_wiggle_fix'
                    elif ext in ('css', 'scss', 'less') or issue.get('source_tool') == 'CSSFixer':
                        success = self._fix_css_syntax(issue)
                        if success:
                            method = issue.get('fix_method') or 'auto_css_wiggle_fix'
                    elif ext in ('html', 'htm') or issue.get('source_tool') == 'HTMLFixer':
                        success = self._fix_html_structure(issue)
                        if success:
                            method = issue.get('fix_method') or 'auto_html_wiggle_fix'
                    else:
                        # 其他后缀/未知工具：按文件内容尝试路由
                        try:
                            with open(fpath, 'rb') as _fh:
                                head = _fh.read(4)
                            if head[:2] == b'#!' or ext == 'py':
                                success = self._fix_python_syntax(issue)
                        except Exception:
                            pass
                        method = issue.get('fix_method') or 'auto_wiggle_unknown'
                except Exception:
                    success = False
                    method = 'auto_wiggle_fix_error'

                if success:
                    fixed += 1
                    self._mark_fixed(issue, issue.get('fix_method', method), 'success')
                    # 同步更新 red_wiggles 表的修复状态
                    try:
                        self._mark_red_wiggle_fixed(issue, method, 'success')
                    except Exception:
                        pass
                else:
                    failed += 1
                    self._mark_fixed(issue, 'auto_wiggle_fix', 'failed')
                    try:
                        self._mark_red_wiggle_fixed(issue, 'auto_wiggle_fix', 'failed')
                    except Exception:
                        pass

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

    def _fix_markdown(self, issue: Dict) -> bool:
        """尝试修复 Markdown / .md 文件问题"""
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
            success, method = MarkdownFixer.fix_file(fpath, error_msg, error_code)
            if success:
                issue['fix_method'] = method
                return True
        except Exception:
            pass
        return False

    def _fix_sql(self, issue: Dict) -> bool:
        """尝试修复 SQL / .sql 文件语法问题"""
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
            success, method = SQLFixer.fix_file(fpath, error_msg, error_code)
            if success:
                issue['fix_method'] = method
                return True
        except Exception:
            pass
        return False

    def _fix_php(self, issue: Dict) -> bool:
        """尝试修复 PHP 源码语法问题"""
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
            code = issue.get('error_code', '')
            success, method = PHPFixer.fix_file(fpath, error_msg, code)
            if success:
                issue['fix_method'] = method
                return True
        except Exception:
            pass
        return False

    def _fix_c_source(self, issue: Dict) -> bool:
        """尝试修复 C/C++ 源码（.c/.h）问题"""
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
            code = issue.get('error_code', '')
            success, method = CSourceFixer.fix_file(fpath, error_msg, code)
            if success:
                issue['fix_method'] = method
                return True
        except Exception:
            pass
        return False

    def _fix_binary(self, issue: Dict) -> bool:
        """修复二进制（.dll/.lib/.db）权限问题，不修改二进制内容"""
        fpath = issue.get('file_path', '')
        if not fpath or not os.path.exists(fpath):
            return False
        try:
            code = issue.get('error_code', '')
            if BinaryScanner.fix_binary(fpath, code):
                issue['fix_method'] = 'chmod_remove_other_write'
                return True
        except Exception:
            pass
        return False

    def _fix_markup(self, issue: Dict) -> bool:
        """尝试修复 ASP/ASPX/JSP/HTM 标记与脚本问题"""
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
            code = issue.get('error_code', '')
            success, method = ASPJSPFixer.fix_file(fpath, code)
            if success:
                issue['fix_method'] = method
                return True
        except Exception:
            pass
        return False

    def _fix_text(self, issue: Dict) -> bool:
        """尝试修复 .txt 文本问题（保守策略）"""
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
            code = issue.get('error_code', '')
            success, method = TextLintFixer.fix_file(fpath, code)
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

    def _mark_red_wiggle_fixed(self, issue: Dict, method: str, result: str):
        """同步更新红色波浪线专门表的修复状态"""
        try:
            with _get_conn() as conn:
                conn.execute(
                    """UPDATE ai_inspection_red_wiggles
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

    def get_red_wiggle_summary(self) -> Dict[str, Any]:
        """获取红色波浪线汇总统计（用于上报、仪表盘展示、巡检报告）"""
        try:
            with _get_conn() as conn:
                c = conn.cursor()
                total = c.execute("SELECT COUNT(*) FROM ai_inspection_red_wiggles").fetchone()[0]
                fixed = c.execute("SELECT COUNT(*) FROM ai_inspection_red_wiggles WHERE fixed=1").fetchone()[0]
                red = c.execute("SELECT COUNT(*) FROM ai_inspection_red_wiggles WHERE severity_icon='🔴'").fetchone()[0]
                yellow = c.execute("SELECT COUNT(*) FROM ai_inspection_red_wiggles WHERE severity_icon='🟡'").fetchone()[0]
                top_files = []
                try:
                    cur = c.execute(
                        """SELECT file_path, COUNT(*) as c FROM ai_inspection_red_wiggles
                           WHERE fixed=0 GROUP BY file_path ORDER BY c DESC LIMIT 10"""
                    )
                    for r in cur.fetchall():
                        top_files.append({'file': r[0], 'count': r[1]})
                except Exception:
                    pass
                top_errors = []
                try:
                    cur = c.execute(
                        """SELECT error_code, severity_icon, COUNT(*) as c 
                           FROM ai_inspection_red_wiggles WHERE fixed=0 
                           GROUP BY error_code ORDER BY c DESC LIMIT 10"""
                    )
                    for r in cur.fetchall():
                        top_errors.append({'code': r[0], 'icon': r[1], 'count': r[2]})
                except Exception:
                    pass
                recent = []
                try:
                    cols = ['wiggle_id', 'severity_icon', 'language', 'file_path', 'line_number',
                            'error_code', 'rule_id', 'error_message', 'suggestion_message',
                            'auto_fixable', 'reported_at', 'fixed']
                    cur = c.execute(
                        f"SELECT {','.join(cols)} FROM ai_inspection_red_wiggles "
                        "ORDER BY id DESC LIMIT 20"
                    )
                    rows = cur.fetchall()
                    for r in rows:
                        recent.append({cols[i]: (r[i] if i < len(r) else None) for i in range(len(cols))})
                except Exception:
                    pass
                return {
                    'total': total,
                    'fixed': fixed,
                    'unfixed': total - fixed,
                    'red': red,
                    'yellow': yellow,
                    'blue': total - red - yellow,
                    'top_files': top_files,
                    'top_errors': top_errors,
                    'recent': recent,
                    'memory_stats': {
                        k: self._stats.get(k, 0) for k in
                        ('wiggle_scan_py', 'wiggle_scan_js', 'wiggle_scan_css', 'wiggle_scan_html',
                         'wiggle_total', 'wiggle_red', 'wiggle_yellow')
                    },
                    'reported_at': datetime.now().isoformat(),
                }
        except Exception as e:
            _logger.warning(f"红色波浪线汇总失败: {e}")
            return {'total': 0, 'fixed': 0, 'unfixed': 0, 'red': 0, 'yellow': 0, 'blue': 0,
                    'top_files': [], 'top_errors': [], 'recent': [], 'memory_stats': {}}

    # ============== 5. 数据库上报 ==============

    def _bulk_insert_red_wiggles(self, run_id: str, wiggles: List[Dict]):
        """批量写入红色波浪线专门表"""
        if not wiggles:
            return
        try:
            with _get_conn() as conn:
                c = conn.cursor()
                now = datetime.now().isoformat()
                for w in wiggles:
                    wiggle_id = w.get('wiggle_id') or (
                        'RW-' + hashlib.md5(
                            f"{w.get('file_path','')}|{w.get('line_number',0)}|{w.get('error_code','')}|{w.get('error_message','')[:80]}".encode()
                        ).hexdigest()[:12]
                    )
                    try:
                        c.execute(
                            """INSERT OR IGNORE INTO ai_inspection_red_wiggles
                               (wiggle_id, run_id, source_tool, language, severity, severity_icon,
                                file_path, line_number, column_number, end_line, end_column,
                                error_code, rule_id, error_message, suggestion_message,
                                confidence, auto_fixable, reported_at)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (
                                wiggle_id, run_id,
                                w.get('source_tool', ''),
                                w.get('language', ''),
                                w.get('severity', 'low'),
                                w.get('severity_icon', '🔵'),
                                w.get('file_path', ''),
                                w.get('line_number', 0),
                                w.get('column_number', 0),
                                w.get('end_line', 0),
                                w.get('end_column', 0),
                                w.get('error_code', ''),
                                w.get('rule_id', ''),
                                w.get('error_message', '')[:500],
                                w.get('suggestion_message', '')[:500],
                                w.get('confidence', 0.0),
                                1 if w.get('auto_fixable') else 0,
                                w.get('detected_at') or now,
                            )
                        )
                    except Exception:
                        pass
                conn.commit()
        except Exception as e:
            _logger.error(f"红色波浪线批量入库失败: {e}")

    def _bulk_insert_issues(self, run_id: str, issues: List[Dict]):
        """批量插入问题记录（含红色波浪线扩展列）"""
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
                            error_message, error_code, confidence, detected_at,
                            is_red_wiggle, wiggle_icon, source_tool, rule_id,
                            suggestion_message, auto_fixable)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (run_id,
                         issue.get('issue_type', 'unknown'),
                         issue.get('severity', 'low'),
                         issue.get('file_path', ''),
                         issue.get('line_number', 0),
                         issue.get('error_message', '')[:500],
                         issue.get('error_code', ''),
                         issue.get('confidence', 0.0),
                         issue.get('detected_at') or now,
                         1 if issue.get('is_red_wiggle') or issue.get('issue_type') == 'ide_diagnostic' or issue.get('severity') in ('critical', 'high') else 0,
                         issue.get('wiggle_icon') or ('🔴' if issue.get('severity') in ('critical', 'high') else '🟡' if issue.get('severity') == 'medium' else '🔵'),
                         issue.get('source_tool', ''),
                         issue.get('rule_id', ''),
                         (issue.get('suggestion_message') or '')[:500],
                         1 if issue.get('auto_fixable') else 0)
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
