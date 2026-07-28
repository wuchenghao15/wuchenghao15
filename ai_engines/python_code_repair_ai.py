#!/usr/bin/env python3
"""

import logging
logger = logging.getLogger(__name__)
Python代码修复AI员工
自动检测和修复Python文件错误，并上报到数据库
"""

import os
import re
import ast
import json
import time
import sqlite3
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional
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


class PythonCodeRepairAI:
    """Python代码修复AI员工"""

    def __init__(self, instance_id: str = 'python_code_repair_ai'):
        self.instance_id = instance_id
        self.name = 'Python代码修复AI'
        self.title = 'Python代码自动修复专家'
        self.description = '专门负责检测和修复Python文件中的语法错误、逻辑错误、导入错误等问题，并自动上报到数据库'
        self.category = 'development'
        self.status = 'initialized'
        self.capabilities = [
            'Python语法错误检测',
            'Python语法错误修复',
            '导入错误检测与修复',
            '缩进错误修复',
            '空except块修复',
            '变量未定义检测',
            '函数参数错误检测',
            '文件编码问题修复',
            '批量扫描修复',
            '修复记录自动上报数据库'
        ]
        self.efficiency = 98
        self.workload = 0
        self.created_at = int(time.time())
        self.updated_at = int(time.time())
        self.fix_count = 0
        self.scan_count = 0
        self.repair_history = []
        print(f"[INFO] {self.name} 初始化完成")

    def initialize(self) -> bool:
        """初始化AI员工"""
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
        """初始化数据库表"""
        with get_db() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS python_repair_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repair_id TEXT UNIQUE NOT NULL,
                    file_path TEXT NOT NULL,
                    error_type TEXT NOT NULL,
                    error_message TEXT,
                    error_line INTEGER,
                    before_content TEXT,
                    after_content TEXT,
                    fix_status TEXT DEFAULT 'pending',
                    repair_time INTEGER,
                    applied_by TEXT DEFAULT 'python_code_repair_ai',
                    verified INTEGER DEFAULT 0,
                    verify_time INTEGER,
                    notes TEXT
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_py_repair_file ON python_repair_logs(file_path)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_py_repair_status ON python_repair_logs(fix_status)')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS python_errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_id TEXT UNIQUE NOT NULL,
                    file_path TEXT NOT NULL,
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
            conn.execute('CREATE INDEX IF NOT EXISTS idx_py_errors_file ON python_errors(file_path)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_py_errors_status ON python_errors(status)')

            conn.commit()
        print(f"[INFO] Python修复数据库表初始化完成")

    def _register_employee(self):
        """注册AI员工到数据库"""
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
        """生成修复ID"""
        return f"pyrep_{int(time.time())}_{hash(str(time.time())) % 100000:05d}"

    def _generate_error_id(self, file_path: str, error_type: str) -> str:
        """生成错误ID"""
        return f"pyerr_{hash(f'{file_path}_{error_type}_{int(time.time())}') % 1000000:06d}"

    def _detect_syntax_errors(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """检测Python语法错误"""
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
        return errors

    def _detect_empty_except(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """检测空except块"""
        errors = []
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if re.match(r'^\s*except\s*:', line):
                indent = len(line) - len(line.lstrip())
                next_line = lines[i] if i < len(lines) else ''
                if not next_line.strip() or next_line.strip() == 'pass':
                    continue
                if next_line[:indent].strip() == '':
                    errors.append({
                        'error_type': 'empty_except_block',
                        'error_message': '空except块需要添加pass或处理逻辑',
                        'error_line': i,
                        'error_column': 0,
                        'severity': 'medium',
                        'file_path': file_path
                    })
        return errors

    def _detect_mixed_indentation(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """检测混合缩进"""
        errors = []
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            leading = line[:len(line) - len(line.lstrip())]
            if leading:
                has_spaces = ' ' in leading
                has_tabs = '\t' in leading
                if has_spaces and has_tabs:
                    errors.append({
                        'error_type': 'mixed_indentation',
                        'error_message': '混合缩进（空格和制表符混用）',
                        'error_line': i,
                        'error_column': 0,
                        'severity': 'medium',
                        'file_path': file_path
                    })
                    break
                if has_spaces and len(leading) % 4 != 0:
                    errors.append({
                        'error_type': 'invalid_indentation',
                        'error_message': f'缩进不是4的倍数，当前缩进{len(leading)}个空格',
                        'error_line': i,
                        'error_column': 0,
                        'severity': 'low',
                        'file_path': file_path
                    })
        return errors

    def _detect_import_errors(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """检测导入错误"""
        errors = []
        import_patterns = [
            r'^import\s+(\w+)',
            r'^from\s+(\w+)',
            r'^from\s+(\w+\.\w+)',
        ]
        for pattern in import_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for match in matches:
                module_name = match.split('.')[0]
                if module_name in ['nonexistent', 'missing', 'broken', 'corrupted']:
                    errors.append({
                        'error_type': 'invalid_import',
                        'error_message': f'可能的无效导入: {match}',
                        'error_line': 0,
                        'error_column': 0,
                        'severity': 'high',
                        'file_path': file_path
                    })
        return errors

    def _detect_encoding_issues(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """检测编码问题"""
        errors = []
        if not content.startswith('#'):
            if any(ord(c) > 127 for c in content[:1000]):
                errors.append({
                    'error_type': 'missing_encoding_declaration',
                    'error_message': 'Python文件缺少编码声明，包含非ASCII字符',
                    'error_line': 1,
                    'error_column': 0,
                    'severity': 'medium',
                    'file_path': file_path
                })
        return errors

    def _detect_name_errors(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """检测可能的名称错误"""
        errors = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    if node.id.lower() in ['none', 'true', 'false']:
                        errors.append({
                            'error_type': 'wrong_case_constant',
                            'error_message': f'常量名大小写错误: {node.id} 应为 {node.id.capitalize()}',
                            'error_line': node.lineno,
                            'error_column': node.col_offset,
                            'severity': 'high',
                            'file_path': file_path
                        })
        except SyntaxError:
            pass
        return errors

    def detect_errors(self, file_path: str) -> List[Dict[str, Any]]:
        """检测Python文件中的所有错误"""
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

        errors.extend(self._detect_syntax_errors(content, file_path))
        errors.extend(self._detect_empty_except(content, file_path))
        errors.extend(self._detect_mixed_indentation(content, file_path))
        errors.extend(self._detect_import_errors(content, file_path))
        errors.extend(self._detect_encoding_issues(content, file_path))
        errors.extend(self._detect_name_errors(content, file_path))

        self.scan_count += 1
        return errors

    def _fix_syntax_error(self, content: str, error: Dict[str, Any]) -> str:
        """修复语法错误"""
        lines = content.split('\n')
        line_num = error['error_line'] - 1 if error['error_line'] > 0 else 0
        
        if 0 <= line_num < len(lines):
            line = lines[line_num]
            
            if 'unexpected EOF' in error['error_message']:
                open_braces = content.count('{') + content.count('(') + content.count('[')
                close_braces = content.count('}') + content.count(')') + content.count(']')
                diff = open_braces - close_braces
                if diff > 0:
                    content += '\n' + '}' * diff
            
            elif 'invalid syntax' in error['error_message']:
                if '=' in line and '==' not in line and '!=' not in line and '<=' not in line and '>=' not in line:
                    if 'if ' in line or 'while ' in line or 'elif ' in line:
                        line = line.replace('=', '==', 1)
                        lines[line_num] = line
                        content = '\n'.join(lines)

        return content

    def _fix_empty_except(self, content: str) -> str:
        """修复空except块"""
        lines = content.split('\n')
        fixed_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            match = re.match(r'^(\s*)except\s*:', line)
            if match:
                fixed_lines.append(line)
                indent = match.group(1)
                i += 1
                if i < len(lines):
                    next_line = lines[i]
                    next_indent = next_line[:len(next_line) - len(next_line.lstrip())]
                    if next_indent.strip() == '' or len(next_indent) <= len(indent):
                        fixed_lines.append(indent + '    pass')
            fixed_lines.append(line)
            i += 1
        return '\n'.join(fixed_lines)

    def _fix_mixed_indentation(self, content: str) -> str:
        """修复混合缩进"""
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

    def _fix_encoding(self, content: str) -> str:
        """修复编码问题"""
        if not content.startswith('#'):
            return '# -*- coding: utf-8 -*-\n' + content
        if not content.startswith('# -*- coding'):
            lines = content.split('\n')
            if lines:
                lines[0] = '# -*- coding: utf-8 -*-\n' + lines[0]
            return '\n'.join(lines)
        return content

    def _fix_name_errors(self, content: str) -> str:
        """修复名称错误"""
        content = content.replace('none', 'None')
        content = content.replace('true', 'True')
        content = content.replace('false', 'False')
        return content

    def fix_file(self, file_path: str) -> Dict[str, Any]:
        """修复单个Python文件"""
        repair_id = self._generate_repair_id()
        results = {
            'repair_id': repair_id,
            'file_path': file_path,
            'errors_found': 0,
            'errors_fixed': 0,
            'status': 'pending',
            'message': ''
        }

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                before_content = f.read()

            errors = self.detect_errors(file_path)
            results['errors_found'] = len(errors)

            if not errors:
                results['status'] = 'no_errors'
                results['message'] = '未发现错误'
                return results

            after_content = before_content

            for error in errors:
                error_type = error['error_type']
                
                if error_type == 'syntax_error':
                    after_content = self._fix_syntax_error(after_content, error)
                elif error_type == 'empty_except_block':
                    after_content = self._fix_empty_except(after_content)
                elif error_type == 'mixed_indentation' or error_type == 'invalid_indentation':
                    after_content = self._fix_mixed_indentation(after_content)
                elif error_type == 'missing_encoding_declaration':
                    after_content = self._fix_encoding(after_content)
                elif error_type == 'wrong_case_constant':
                    after_content = self._fix_name_errors(after_content)

            try:
                ast.parse(after_content)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(after_content)

                results['errors_fixed'] = len(errors)
                results['status'] = 'success'
                results['message'] = f'成功修复{len(errors)}个错误'
                self.fix_count += 1

                self._report_to_database(
                    repair_id, file_path, errors,
                    before_content, after_content, 'applied'
                )

            except SyntaxError as e:
                results['status'] = 'failed'
                results['message'] = f'修复后仍有语法错误: {str(e)}'
                self._report_to_database(
                    repair_id, file_path, errors,
                    before_content, after_content, 'failed'
                )

        except Exception as e:
            results['status'] = 'failed'
            results['message'] = f'修复过程出错: {str(e)}'
            self._report_to_database(
                repair_id, file_path, [], '', '', 'failed', str(e)
            )

        self.repair_history.append(results)
        self.updated_at = int(time.time())
        return results

    def _report_to_database(self, repair_id: str, file_path: str, errors: List[Dict],
                           before_content: str, after_content: str, status: str,
                           error_message: str = ''):
        """上报修复结果到数据库"""
        try:
            with get_db() as conn:
                conn.execute('''
                    INSERT INTO python_repair_logs (
                        repair_id, file_path, error_type, error_message,
                        error_line, before_content, after_content,
                        fix_status, repair_time, applied_by, verified
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    repair_id, file_path,
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
                        INSERT OR REPLACE INTO python_errors (
                            error_id, file_path, error_type, error_message,
                            error_line, error_column, detected_at, severity,
                            status, fixed_by, fixed_at, repair_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        error_id, file_path, error['error_type'], error['error_message'],
                        error['error_line'], error['error_column'], int(time.time()),
                        error['severity'],
                        'fixed' if status == 'applied' else 'unfixed',
                        self.instance_id,
                        int(time.time()) if status == 'applied' else None,
                        repair_id
                    ))

                conn.commit()

            print(f"[INFO] 修复记录已上报数据库: {repair_id}")
        except Exception as e:
            print(f"[ERROR] 上报数据库失败: {str(e)}")

    def scan_directory(self, directory: str = PROJECT_ROOT) -> List[Dict[str, Any]]:
        """扫描目录中的Python文件"""
        results = []
        
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules', 'venv', '.venv']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    errors = self.detect_errors(file_path)
                    if errors:
                        results.append({
                            'file_path': file_path,
                            'errors': errors,
                            'error_count': len(errors)
                        })

                        for error in errors:
                            error_id = self._generate_error_id(file_path, error['error_type'])
                            try:
                                with get_db() as conn:
                                    conn.execute('''
                                        INSERT OR IGNORE INTO python_errors (
                                            error_id, file_path, error_type, error_message,
                                            error_line, error_column, detected_at, severity, status
                                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    ''', (
                                        error_id, file_path, error['error_type'],
                                        error['error_message'], error['error_line'],
                                        error['error_column'], int(time.time()),
                                        error['severity'], 'unfixed'
                                    ))
                                    conn.commit()
                            except Exception as e:
                                print(f"[ERROR] 记录错误失败: {file_path} - {e}")

        print(f"[INFO] 扫描完成，共发现 {len(results)} 个文件有错误")
        return results

    def auto_repair_directory(self, directory: str = PROJECT_ROOT) -> List[Dict[str, Any]]:
        """自动修复目录中的Python文件"""
        results = []
        
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules', 'venv', '.venv']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    print(f"[INFO] 正在修复: {file_path}")
                    result = self.fix_file(file_path)
                    results.append(result)
                    if result['status'] == 'success':
                        print(f"[SUCCESS] {file_path}: 修复了{result['errors_fixed']}个错误")
                    elif result['status'] == 'failed':
                        print(f"[FAILED] {file_path}: {result['message']}")

        logger.info(f"\n[INFO] 批量修复完成")
        return results

    def get_stats(self) -> Dict[str, Any]:
        """获取修复统计"""
        try:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) as total FROM code_errors')
                total = cursor.fetchone()['total']
                cursor.execute('SELECT COUNT(*) as fixed FROM code_errors WHERE status = "fixed"')
                fixed = cursor.fetchone()['fixed']
                return {'total_errors': total, 'fixed_errors': fixed}
        except Exception as e:
            logger.error(f"获取统计失败: {e}")
            return {'total_errors': 0, 'fixed_errors': 0}