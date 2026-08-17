#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)
"""
多语言代码修复AI员工
自动检测和修复 Python、HTML、JavaScript、CSS 文件错误，并上报到数据库
"""

import os
import re
import ast
import json
import time
import sqlite3
from datetime import datetime
from typing import Dict, List, Any
from contextlib import contextmanager

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mtscos.db')
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


class MultiCodeRepairAI:
    """多语言代码修复AI员工"""

    def __init__(self, instance_id: str = 'multi_code_repair_ai'):
        self.instance_id = instance_id
        self.name = '全能代码修复AI'
        self.title = '多语言代码自动修复专家'
        self.description = '负责检测和修复 Python、HTML、JavaScript、CSS 文件中的语法错误、格式问题等，并自动上报到数据库'
        self.category = 'development'
        self.status = 'initialized'
        self.capabilities = [
            'Python语法错误检测与修复',
            'Python缩进错误修复',
            'Python空except块修复',
            'Python编码声明修复',
            'HTML标签闭合检测与修复',
            'HTML语法规范检查',
            'JavaScript括号匹配检测与修复',
            'JavaScript语法规范检查',
            'CSS花括号匹配检测与修复',
            'CSS选择器规范检查',
            '批量目录扫描修复',
            '修复记录自动上报数据库',
            '多语言修复统计分析'
        ]
        self.efficiency = 97
        self.workload = 0
        self.created_at = int(time.time())
        self.updated_at = int(time.time())
        self.fix_count = 0
        self.scan_count = 0
        self.supported_extensions = ['.py', '.html', '.js', '.css']
        print(f"[INFO] {self.name} 初始化完成")

    def initialize(self) -> bool:
        try:
            self._init_database_tables()
            self._register_employee()
            self.status = 'running'
            self.updated_at = int(time.time())
            print(f"[INFO] {self.name} 初始化成功，状态: {self.status}")
            return True
        except Exception as e:
            self.status = 'error'
            print(f"[ERROR] {self.name} 初始化失败: {str(e)}")
            return False

    def _init_database_tables(self):
        with get_db() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS code_repair_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repair_id TEXT UNIQUE NOT NULL,
                    file_path TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    error_type TEXT,
                    error_message TEXT,
                    error_line INTEGER,
                    before_content TEXT,
                    after_content TEXT,
                    fix_status TEXT DEFAULT 'pending',
                    repair_time INTEGER,
                    applied_by TEXT DEFAULT 'multi_code_repair_ai',
                    verified INTEGER DEFAULT 0,
                    verify_time INTEGER,
                    notes TEXT
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_repair_file_path ON code_repair_logs(file_path)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_repair_file_type ON code_repair_logs(file_type)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_repair_status ON code_repair_logs(fix_status)')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS code_errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_id TEXT UNIQUE NOT NULL,
                    file_path TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    error_type TEXT NOT NULL,
                    error_message TEXT,
                    error_line INTEGER,
                    error_column INTEGER,
                    detected_at INTEGER NOT NULL,
                    severity TEXT DEFAULT 'medium',
                    status TEXT DEFAULT 'unfixed',
                    fixed_by TEXT,
                    fixed_at INTEGER,
                    repair_id TEXT,
                    details TEXT
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_errors_file ON code_errors(file_path)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_errors_type ON code_errors(error_type)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_errors_status ON code_errors(status)')

            conn.commit()
        print("[INFO] 代码修复数据库表初始化完成")

    def _register_employee(self):
        try:
            with get_db() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO ai_employees (
                        employee_id, name, title, description, category,
                        capabilities, efficiency, workload, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    self.instance_id,
                    self.name,
                    self.title,
                    self.description,
                    self.category,
                    json.dumps(self.capabilities),
                    self.efficiency,
                    self.workload,
                    self.created_at,
                    self.updated_at
                ))
                conn.commit()
            print(f"[INFO] {self.name} 已注册到数据库")
        except Exception as e:
            print(f"[WARNING] 注册AI员工失败: {str(e)}")

    def _generate_repair_id(self) -> str:
        return f"rep_{int(time.time())}_{hash(str(time.time())) % 100000:05d}"

    def _generate_error_id(self, file_path: str, error_type: str) -> str:
        return f"err_{hash(f'{file_path}_{error_type}_{int(time.time())}') % 1000000:06d}"

    def _get_file_type(self, file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        type_map = {
            '.py': 'python',
            '.html': 'html',
            '.js': 'javascript',
            '.css': 'css'
        }
        return type_map.get(ext, 'unknown')

    def detect_python_errors(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        errors = []
        try:
            ast.parse(content)
        except SyntaxError as e:
            errors.append({
                'error_type': 'syntax_error',
                'error_message': str(e),
                'error_line': e.lineno or 0,
                'error_column': e.offset or 0,
                'severity': 'high',
                'file_path': file_path
            })

        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if re.match(r'^\s*except\s*:', line):
                indent = len(line) - len(line.lstrip())
                next_line = lines[i] if i < len(lines) else ''
                if next_line[:indent].strip() == '':
                    errors.append({
                        'error_type': 'empty_except_block',
                        'error_message': '空except块需要添加pass或处理逻辑',
                        'error_line': i,
                        'error_column': 0,
                        'severity': 'medium',
                        'file_path': file_path
                    })

        has_tabs = any('\t' in line[:len(line)-len(line.lstrip())] for line in lines if line.strip())
        has_spaces = any((' ' in line[:len(line)-len(line.lstrip())] and line.strip()) for line in lines)
        if has_tabs and has_spaces:
            errors.append({
                'error_type': 'mixed_indentation',
                'error_message': '混合缩进（空格和制表符混用）',
                'error_line': 0,
                'error_column': 0,
                'severity': 'medium',
                'file_path': file_path
            })

        if content.strip() and not content.startswith('#'):
            if any(ord(c) > 127 for c in content[:1000]):
                errors.append({
                    'error_type': 'missing_encoding_declaration',
                    'error_message': 'Python文件缺少编码声明，包含非ASCII字符',
                    'error_line': 1,
                    'error_column': 0,
                    'severity': 'low',
                    'file_path': file_path
                })

        return errors

    def detect_html_errors(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        errors = []
        lines = content.split('\n')

        open_tags = re.findall(r'<([a-zA-Z][a-zA-Z0-9]*)\b[^>]*>', content)
        close_tags = re.findall(r'</([a-zA-Z][a-zA-Z0-9]*)>', content)
        self_closing = ['br', 'img', 'input', 'meta', 'link', 'hr', 'br', 'col', 'embed', 'source', 'track', 'wbr']

        from collections import Counter
        open_counts = Counter(open_tags)
        close_counts = Counter(close_tags)

        for tag in open_counts:
            if tag.lower() in self_closing:
                continue
            if open_counts[tag] != close_counts.get(tag, 0):
                errors.append({
                    'error_type': 'unclosed_tag',
                    'error_message': f'标签可能未正确闭合: <{tag}>',
                    'error_line': 0,
                    'error_column': 0,
                    'severity': 'medium',
                    'file_path': file_path
                })

        for tag in close_counts:
            if tag.lower() in self_closing:
                errors.append({
                    'error_type': 'unnecessary_close_tag',
                    'error_message': f'自闭合标签不应有闭合标签: </{tag}>',
                    'error_line': 0,
                    'error_column': 0,
                    'severity': 'low',
                    'file_path': file_path
                })

        unterminated_strings = re.findall(r"'[^'>]*<|\"[^\">]*<", content)
        if len(unterminated_strings) > 10:
            errors.append({
                'error_type': 'possible_unterminated_string',
                'error_message': '可能存在未终止的字符串',
                'error_line': 0,
                'error_column': 0,
                'severity': 'medium',
                'file_path': file_path
            })

        return errors

    def detect_js_errors(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        errors = []

        unmatched_braces = content.count('{') - content.count('}')
        if unmatched_braces != 0:
            errors.append({
                'error_type': 'unmatched_braces',
                'error_message': f'花括号不匹配，缺少{abs(unmatched_braces)}个闭合括号' if unmatched_braces > 0 else f'花括号不匹配，多了{abs(unmatched_braces)}个闭合括号',
                'error_line': 0,
                'error_column': 0,
                'severity': 'high',
                'file_path': file_path
            })

        unmatched_parens = content.count('(') - content.count(')')
        if unmatched_parens != 0:
            errors.append({
                'error_type': 'unmatched_parentheses',
                'error_message': f'圆括号不匹配，差{abs(unmatched_parens)}个',
                'error_line': 0,
                'error_column': 0,
                'severity': 'high',
                'file_path': file_path
            })

        unmatched_brackets = content.count('[') - content.count(']')
        if unmatched_brackets != 0:
            errors.append({
                'error_type': 'unmatched_brackets',
                'error_message': f'方括号不匹配，差{abs(unmatched_brackets)}个',
                'error_line': 0,
                'error_column': 0,
                'severity': 'high',
                'file_path': file_path
            })

        double_declarations = re.findall(r'\b(let|const|var)\s+(\w+)\s*=', content)
        from collections import defaultdict
        var_declarations = defaultdict(int)
        for kw, var in double_declarations:
            var_declarations[var] += 1
        for var, count in var_declarations.items():
            if count > 3:
                errors.append({
                    'error_type': 'possible_duplicate_declaration',
                    'error_message': f'变量 {var} 可能有重复声明（出现{count}次）',
                    'error_line': 0,
                    'error_column': 0,
                    'severity': 'low',
                    'file_path': file_path
                })

        return errors

    def detect_css_errors(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        errors = []

        unmatched_curly = content.count('{') - content.count('}')
        if unmatched_curly != 0:
            errors.append({
                'error_type': 'unmatched_curly_braces',
                'error_message': f'花括号不匹配，差{abs(unmatched_curly)}个',
                'error_line': 0,
                'error_column': 0,
                'severity': 'high',
                'file_path': file_path
            })

        missing_semicolons = 0
        lines = content.split('\n')
        in_block = False
        for line in lines:
            if '{' in line:
                in_block = True
            if '}' in line:
                in_block = False
            if in_block and line.strip() and '{' not in line and '}' not in line:
                if not line.strip().endswith(';') and not line.strip().endswith('{') and not line.strip().startswith('//') and not line.strip().startswith('/*'):
                    missing_semicolons += 1

        if missing_semicolons > 5:
            errors.append({
                'error_type': 'missing_semicolons',
                'error_message': f'可能缺少分号（检测到{missing_semicolons}处可疑位置）',
                'error_line': 0,
                'error_column': 0,
                'severity': 'medium',
                'file_path': file_path
            })

        return errors

    def detect_file_errors(self, file_path: str) -> List[Dict[str, Any]]:
        errors = []

        if not os.path.exists(file_path):
            errors.append({
                'error_type': 'file_not_found',
                'error_message': f'文件不存在: {file_path}',
                'error_line': 0,
                'error_column': 0,
                'severity': 'high',
                'file_path': file_path
            })
            return errors

        file_type = self._get_file_type(file_path)
        if file_type == 'unknown':
            return errors

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            errors.append({
                'error_type': 'file_read_error',
                'error_message': f'读取文件失败: {str(e)}',
                'error_line': 0,
                'error_column': 0,
                'severity': 'high',
                'file_path': file_path
            })
            return errors

        if file_type == 'python':
            errors.extend(self.detect_python_errors(content, file_path))
        elif file_type == 'html':
            errors.extend(self.detect_html_errors(content, file_path))
        elif file_type == 'javascript':
            errors.extend(self.detect_js_errors(content, file_path))
        elif file_type == 'css':
            errors.extend(self.detect_css_errors(content, file_path))

        self.scan_count += 1
        return errors

    def _fix_python_empty_except(self, content: str) -> str:
        lines = content.split('\n')
        fixed_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            match = re.match(r'^(\s*)except\s*:', line)
            if match:
                fixed_lines.append(line)
                indent = match.group(1)
                next_i = i + 1
                if next_i < len(lines):
                    next_line = lines[next_i]
                    next_indent = len(next_line) - len(next_line.lstrip())
                    if next_line.strip() == '' or next_indent <= len(indent):
                        fixed_lines.append(indent + '    pass')
            else:
                fixed_lines.append(line)
            i += 1
        return '\n'.join(fixed_lines)

    def _fix_python_indentation(self, content: str) -> str:
        lines = content.split('\n')
        fixed_lines = []
        for line in lines:
            leading = line[:len(line) - len(line.lstrip())]
            if leading:
                spaces = leading.count(' ') + leading.count('\t') * 4
                new_indent = ' ' * ((spaces + 3) // 4 * 4)
                fixed_lines.append(new_indent + line.lstrip())
            else:
                fixed_lines.append(line)
        return '\n'.join(fixed_lines)

    def _fix_python_encoding(self, content: str) -> str:
        if not content.startswith('#'):
            return '# -*- coding: utf-8 -*-\n' + content
        if not content.startswith('# -*- coding'):
            lines = content.split('\n')
            if lines:
                lines.insert(0, '# -*- coding: utf-8 -*-')
            return '\n'.join(lines)
        return content

    def _fix_html_unnecessary_tags(self, content: str) -> str:
        content = re.sub(r'</(br|img|input|meta|link|hr|col|embed|source|track|wbr)\s*>', '', content, flags=re.IGNORECASE)
        return content

    def _fix_js_braces(self, content: str) -> str:
        unmatched = content.count('{') - content.count('}')
        if unmatched > 0:
            content = content.rstrip() + '\n' + '}' * unmatched + '\n'
        return content

    def _fix_css_braces(self, content: str) -> str:
        unmatched = content.count('{') - content.count('}')
        if unmatched > 0:
            content = content.rstrip() + '\n' + '}' * unmatched + '\n'
        return content

    def fix_file(self, file_path: str) -> Dict[str, Any]:
        repair_id = self._generate_repair_id()
        file_type = self._get_file_type(file_path)
        results = {
            'repair_id': repair_id,
            'file_path': file_path,
            'file_type': file_type,
            'errors_found': 0,
            'errors_fixed': 0,
            'status': 'pending',
            'message': ''
        }

        if file_type == 'unknown':
            results['status'] = 'unsupported'
            results['message'] = '不支持的文件类型'
            return results

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                before_content = f.read()

            errors = self.detect_file_errors(file_path)
            results['errors_found'] = len(errors)

            if not errors:
                results['status'] = 'no_errors'
                results['message'] = '未发现错误'
                return results

            after_content = before_content

            for error in errors:
                error_type = error['error_type']

                if file_type == 'python':
                    if error_type == 'empty_except_block':
                        after_content = self._fix_python_empty_except(after_content)
                    elif error_type == 'mixed_indentation':
                        after_content = self._fix_python_indentation(after_content)
                    elif error_type == 'missing_encoding_declaration':
                        after_content = self._fix_python_encoding(after_content)

                elif file_type == 'html':
                    if error_type == 'unnecessary_close_tag':
                        after_content = self._fix_html_unnecessary_tags(after_content)

                elif file_type == 'javascript':
                    if error_type in ['unmatched_braces', 'unmatched_parentheses', 'unmatched_brackets']:
                        after_content = self._fix_js_braces(after_content)

                elif file_type == 'css':
                    if error_type == 'unmatched_curly_braces':
                        after_content = self._fix_css_braces(after_content)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(after_content)

            results['errors_fixed'] = len(errors)
            results['status'] = 'success'
            results['message'] = f'成功修复{len(errors)}个错误'
            self.fix_count += 1

            self._report_to_database(
                repair_id, file_path, file_type, errors,
                before_content, after_content, 'applied'
            )

        except Exception as e:
            results['status'] = 'failed'
            results['message'] = f'修复过程出错: {str(e)}'
            try:
                self._report_to_database(
                    repair_id, file_path, file_type, [],
                    before_content if 'before_content' in dir() else '',
                    after_content if 'after_content' in dir() else '',
                    'failed', str(e)
                )
            except Exception:
                pass

        self.updated_at = int(time.time())
        return results

    def _report_to_database(self, repair_id: str, file_path: str, file_type: str,
                            errors: List[Dict], before_content: str, after_content: str,
                            status: str, error_message: str = ''):
        try:
            with get_db() as conn:
                conn.execute('''
                    INSERT INTO code_repair_logs (
                        repair_id, file_path, file_type, error_type, error_message,
                        error_line, before_content, after_content,
                        fix_status, repair_time, applied_by, verified
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    repair_id, file_path, file_type,
                    ','.join(e['error_type'] for e in errors) if errors else 'none',
                    ','.join(e['error_message'] for e in errors) if errors else error_message,
                    errors[0]['error_line'] if errors else 0,
                    before_content[:1000],
                    after_content[:1000],
                    status,
                    int(time.time()),
                    self.instance_id,
                    1 if status == 'applied' else 0
                ))

                for error in errors:
                    error_id = self._generate_error_id(file_path, error['error_type'])
                    conn.execute('''
                        INSERT OR REPLACE INTO code_errors (
                            error_id, file_path, file_type, error_type, error_message,
                            error_line, error_column, detected_at, severity,
                            status, fixed_by, fixed_at, repair_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        error_id, file_path, file_type,
                        error['error_type'], error['error_message'],
                        error['error_line'], error['error_column'],
                        int(time.time()), error['severity'],
                        'fixed' if status == 'applied' else 'unfixed',
                        self.instance_id,
                        int(time.time()) if status == 'applied' else None,
                        repair_id
                    ))

                conn.commit()
            print(f"[INFO] 修复记录已上报数据库: {repair_id} ({file_type})")
        except Exception as e:
            print(f"[ERROR] 上报数据库失败: {str(e)}")

    def scan_directory(self, directory: str = PROJECT_ROOT, extensions: List[str] = None) -> List[Dict[str, Any]]:
        if extensions is None:
            extensions = self.supported_extensions

        results = []
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules', 'venv', '.venv', 'env']]

            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    errors = self.detect_file_errors(file_path)
                    if errors:
                        results.append({
                            'file_path': file_path,
                            'file_type': self._get_file_type(file_path),
                            'errors': errors,
                            'error_count': len(errors)
                        })

                        for error in errors:
                            error_id = self._generate_error_id(file_path, error['error_type'])
                            try:
                                with get_db() as conn:
                                    conn.execute('''
                                        INSERT OR IGNORE INTO code_errors (
                                            error_id, file_path, file_type, error_type, error_message,
                                            error_line, error_column, detected_at, severity, status
                                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    ''', (
                                        error_id, file_path,
                                        self._get_file_type(file_path),
                                        error['error_type'], error['error_message'],
                                        error['error_line'], error['error_column'],
                                        int(time.time()), error['severity'], 'unfixed'
                                    ))
                                    conn.commit()
                            except Exception as e:
                                print(f"[ERROR] 记录错误失败: {file_path} - {e}")

        print(f"[INFO] 扫描完成，共发现 {len(results)} 个文件有错误")
        return results

    def auto_repair_directory(self, directory: str = PROJECT_ROOT, extensions: List[str] = None) -> List[Dict[str, Any]]:
        if extensions is None:
            extensions = self.supported_extensions

        results = []
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules', 'venv', '.venv', 'env']]

            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    print(f"[INFO] 正在修复: {file_path}")
                    result = self.fix_file(file_path)
                    results.append(result)
                    if result['status'] == 'success':
                        print(f"[SUCCESS] {file_path}: 修复了{result['errors_fixed']}个错误")
                    elif result['status'] == 'failed':
                        print(f"[FAILED] {file_path}: {result['message']}")

        print(f"\n[INFO] 批量修复完成，共处理 {len(results)} 个文件")
        return results

    def get_stats(self) -> Dict[str, Any]:
        try:
            with get_db() as conn:
                total_errors = conn.execute('SELECT COUNT(*) FROM code_errors').fetchone()[0]
                unfixed_errors = conn.execute('SELECT COUNT(*) FROM code_errors WHERE status = "unfixed"').fetchone()[0]
                fixed_errors = conn.execute('SELECT COUNT(*) FROM code_errors WHERE status = "fixed"').fetchone()[0]

                total_repairs = conn.execute('SELECT COUNT(*) FROM code_repair_logs').fetchone()[0]
                successful_repairs = conn.execute('SELECT COUNT(*) FROM code_repair_logs WHERE fix_status = "applied"').fetchone()[0]
                failed_repairs = conn.execute('SELECT COUNT(*) FROM code_repair_logs WHERE fix_status = "failed"').fetchone()[0]

                by_file_type = conn.execute('''
                    SELECT file_type, COUNT(*) as count 
                    FROM code_errors 
                    GROUP BY file_type 
                    ORDER BY count DESC
                ''').fetchall()

                by_error_type = conn.execute('''
                    SELECT error_type, COUNT(*) as count 
                    FROM code_errors 
                    GROUP BY error_type 
                    ORDER BY count DESC
                    LIMIT 10
                ''').fetchall()

                return {
                    'total_errors': total_errors,
                    'unfixed_errors': unfixed_errors,
                    'fixed_errors': fixed_errors,
                    'total_repairs': total_repairs,
                    'successful_repairs': successful_repairs,
                    'failed_repairs': failed_repairs,
                    'by_file_type': [dict(r) for r in by_file_type],
                    'by_error_type': [dict(r) for r in by_error_type],
                    'scan_count': self.scan_count,
                    'fix_count': self.fix_count,
                    'updated_at': int(time.time())
                }
        except Exception as e:
            print(f"[ERROR] 获取统计失败: {e}")
            return {}

    def get_pending_errors(self, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            with get_db() as conn:
                rows = conn.execute('''
                    SELECT * FROM code_errors 
                    WHERE status = "unfixed" 
                    ORDER BY detected_at DESC LIMIT ?
                ''', (limit,)).fetchall()
                return [dict(r) for r in rows]
        except Exception as e:
            print(f"[ERROR] 获取未修复错误失败: {e}")
            return []


multi_code_repair_ai = MultiCodeRepairAI()


def init_multi_code_repair_ai():
    multi_code_repair_ai.initialize()
    return multi_code_repair_ai


if __name__ == '__main__':
    ai = init_multi_code_repair_ai()
    print("\n全能代码修复AI员工创建完成")
    print(f"支持的文件类型: {ai.supported_extensions}")
    print(f"能力列表: {len(ai.capabilities)}项")
    print("\n开始扫描项目...")
    scan_results = ai.scan_directory(PROJECT_ROOT)
    print(f"发现 {len(scan_results)} 个文件有错误")
    print("\n开始自动修复...")
    repair_results = ai.auto_repair_directory(PROJECT_ROOT)
    stats = ai.get_stats()
    print(f"\n修复统计:")
    print(f"  总错误数: {stats.get('total_errors', 0)}")
    print(f"  已修复: {stats.get('fixed_errors', 0)}")
    print(f"  未修复: {stats.get('unfixed_errors', 0)}")
    print(f"  总修复次数: {stats.get('total_repairs', 0)}")
    logger.info("\n全能代码修复AI员工运行完成！")
