#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI驱动的错误检测、修复与学习系统"""

import os
import re
import ast
# JSON import removed - using database
import sqlite3
import traceback
from datetime import datetime
from pathlib import Path

class AIErrorFixer:
    def __init__(self, project_dir=None):
        self.project_dir = project_dir or os.getcwd()
        self.db_path = 'app.db'
        self.fixed_issues = []
        self.error_patterns = self._load_error_patterns()

    def _load_error_patterns(self):
        """加载错误模式库"""
        return [
            {
                'name': 'SyntaxError',
                'pattern': r'SyntaxError: (.+)',
                'fix_type': 'syntax',
                'severity': 'high'
            },
                'name': 'IndentationError',
                'pattern': r'IndentationError: (.+)',
                'fix_type': 'indentation',
                'severity': 'high'
                'name': 'NameError',
                'fix_type': 'variable',
                'severity': 'high'
            },
                'pattern': r"AttributeError: '(.+)' object has no attribute '(.+)'",
                'fix_type': 'attribute',
            },
                'name': 'TypeError',
                'fix_type': 'type',
                'severity': 'medium'
            },
                'pattern': r"ImportError: (.+)",
                'fix_type': 'import',
                'severity': 'high'
            },
                'name': 'ModuleNotFoundError',
                'fix_type': 'import',
            },
                'name': 'table_no_column',
                'pattern': r"table (.+) has no column named (.+)",
                'fix_type': 'database',
                'name': 'missing_argument',
                'pattern': r"missing required argument: '(.+)'",
                'fix_type': 'argument',
                'severity': 'high'
            },
                'fix_type': 'syntax',
                'severity': 'high'
            }
    def connect_db(self):
        return sqlite3.connect(self.db_path)

        """分析Python文件检测错误"""

        try:
                content = f.read()

            # 语法检查
            try:
                ast.parse(content)
            except SyntaxError as e:
                errors.append({
                    'file': file_path,
                    'line': e.lineno,
                    'error_type': 'SyntaxError',
                    'message': str(e),
                    'severity': 'high',
                    'context': e.text.strip() if e.text else ''
                })

            # 缩进检查
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                stripped = line.lstrip()
                if stripped and not line.startswith((' ', '\t')):
                    # 检查函数/类定义后的缩进
                    if stripped.startswith(('def ', 'class ', 'if ', 'for ', 'while ', 'with ', 'try:', 'except:')):
                        next_line_idx = i
                        while next_line_idx < len(lines):
                            next_line = lines[next_line_idx]
                            if next_line.strip() and not next_line.startswith((' ', '\t')):
                                if not stripped.endswith(':'):
                                    errors.append({
                                        'file': file_path,
                                        'line': i,
                                        'message': f"可能缺少冒号或缩进问题",
                                        'severity': 'high',
                                        'context': stripped[:50]
                                    })
                                break
                            next_line_idx += 1

            # 检查常见代码问题
            if 'print ' in content and 'print(' not in content:
                errors.append({
                    'file': file_path,
                    'line': 0,
                    'error_type': 'Python2Syntax',
                    'message': '发现Python 2语法的print语句',
                    'severity': 'medium',
                    'context': 'print语句'
                })

            # 检查编码声明
            if not content.startswith('# -*- coding:') and not content.startswith('#!/usr/bin/env'):
                errors.append({
                    'file': file_path,
                    'line': 1,
                    'error_type': 'EncodingWarning',
                    'severity': 'low',
                })

        except Exception as e:
            errors.append({
                'line': 0,
                'error_type': 'FileReadError',
                'severity': 'medium',
                'context': ''

        return errors
    def analyze_log_files(self):
        """分析日志文件检测错误"""
        errors = []
        log_patterns = [
            (r'ERROR', 'Error'),
            (r'WARNING', 'Warning'),
            (r'CRITICAL', 'Critical'),
            (r'Traceback', 'Traceback'),
        ]
        for root, dirs, files in os.walk(self.project_dir):
            for file in files:
                if file.endswith('.log'):
                    file_path = os.path.join(root, file)
                    try:
                            for i, line in enumerate(f, 1):
                                for pattern, error_type in log_patterns:
                                    if pattern in line:
                                        errors.append({
                                            'error_type': error_type,
                                            'message': line.strip()[:200],
                                            'severity': 'high' if pattern in ('ERROR', 'CRITICAL', 'Traceback') else 'medium',
                                            'context': line.strip()[:100]
                                        })

        return errors
    def fix_indentation(self, file_path):
        try:
                content = f.read()
            # 使用4空格缩进
            lines = content.split('\n')
            fixed_lines = []
            in_multi_line_string = False

                if '"""' in line or "'''" in line:
                    in_multi_line_string = not in_multi_line_string

                if not in_multi_line_string and line.strip():
                    # 检测混合缩进
                    leading_spaces = len(line) - len(line.lstrip(' '))

                    if leading_tabs > 0:
                        # 转换tab为4空格
                        fixed_line = '    ' * leading_tabs + line.lstrip('\t')
                        fixed_lines.append(fixed_line)
                        fixed_lines.append(line)
                else:
                    fixed_lines.append(line)

            fixed_content = '\n'.join(fixed_lines)

                f.write(fixed_content)

            return True, '缩进已标准化为4空格'
            return False, str(e)
    def fix_python2_print(self, file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 将 print xxx 转换为 print(xxx)
            # 使用正则处理简单情况
            content = re.sub(r'^(\s*)print\s+(.+)$', r'\1print(\2)', content, flags=re.MULTILINE)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return True, 'Python2 print语句已转换为Python3语法'
            return False, str(e)

    def add_encoding_declaration(self, file_path):
        """添加编码声明"""
        try:
                lines = f.readlines()

            if lines and (lines[0].startswith('#!/usr/bin/env') or lines[0].startswith('# -*- coding:')):
                return True, '编码声明已存在'

            # 在文件开头添加编码声明
            if lines and lines[0].startswith('#!'):
                new_lines = [lines[0], '# -*- coding: utf-8 -*-\n'] + lines[1:]
            else:
                new_lines = ['# -*- coding: utf-8 -*-\n'] + lines
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)

            return True, '已添加UTF-8编码声明'
            return False, str(e)

        """修复数据库缺少列的问题"""
        try:
            conn = self.connect_db()
            cursor = conn.cursor()

            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]

                conn.commit()
                conn.close()
                return True, f"已为表 {table_name} 添加列 {column_name}"

            return True, f"列 {column_name} 已存在"
        except Exception as e:
            return False, str(e)

    def record_fix_to_brain(self, fix_record):
        """记录修复方案到脑库"""
        try:
            conn = self.connect_db()
            cursor = conn.cursor()

            # 确保脑库表存在
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_brain_knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_type TEXT NOT NULL,
                    fix_strategy TEXT,
                    fix_code TEXT,
                    severity TEXT,
                    confidence REAL DEFAULT 0.8,
                    usage_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            ''')

            cursor.execute('''
                INSERT INTO ai_brain_knowledge
                (error_type, error_pattern, fix_strategy, fix_code, affected_file, severity, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                fix_record['error_type'],
                fix_record.get('error_pattern', ''),
                fix_record['fix_strategy'],
                fix_record['affected_file'],
                fix_record['severity'],
                fix_record.get('confidence', 0.8)
            ))

            conn.close()
            return True
        except Exception as e:
            print(f"记录到脑库失败: {e}")
            return False

        """记录修复日志"""
        try:
            conn = self.connect_db()
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fix_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_type TEXT,
                    file_path TEXT,
                    line_number INTEGER,
                    fix_strategy TEXT,
                    fix_result TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    ai_version TEXT DEFAULT '1.0'
                )
            ''')

                (error_type, file_path, line_number, fix_strategy, fix_result)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                fix_record['error_type'],
                fix_record['affected_file'],
                fix_record.get('line', 0),
                fix_record['fix_strategy'],
            ))
            conn.close()
            return True
        except Exception as e:
            print(f"记录日志失败: {e}")
            return False

    def run_error_detection(self):
        """运行完整的错误检测"""
        print("="*70)
        print("           AI驱动的错误检测与修复系统")
        print("="*70)

        all_errors = []

        print("\n[1/3] 分析Python文件...")
        for root, dirs, files in os.walk(self.project_dir):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    errors = self.analyze_python_file(file_path)
                    if errors:
                        print(f"  发现 {len(errors)} 个问题: {file}")

        print(f"\n[2/3] 分析日志文件...")
        log_errors = self.analyze_log_files()
        all_errors.extend(log_errors)
        print(f"  发现 {len(log_errors)} 个日志错误")

        return all_errors

    def run_fix(self, errors):
        """执行修复"""
        fixed_count = 0

        for error in errors:
            file_path = error['file']
            error_type = error['error_type']
            success = False

            try:
                    success, message = self.fix_indentation(file_path)
                elif error_type == 'Python2Syntax':
                    success, message = self.fix_python2_print(file_path)
                elif error_type == 'EncodingWarning':
                    success, message = self.add_encoding_declaration(file_path)
                elif 'DatabaseColumnError' in error_type:
                    if match:
                        success, message = self.fix_database_column(match.group(1), match.group(2))

                    fixed_count += 1
                    print(f"  ✅ 修复成功 [{error_type}]: {os.path.basename(file_path)} - {message}")

                    # 记录到脑库和日志
                        'error_type': error_type,
                        'error_pattern': error.get('context', ''),
                        'fix_strategy': message,
                        'severity': error['severity'],
                        'result': 'success',
                    }
                    self.record_fix_to_brain(fix_record)
                    self.log_fix(fix_record)
                    failed_count += 1
            except Exception as e:
                failed_count += 1
        print(f"\n修复完成: {fixed_count} 个成功, {failed_count} 个失败")
        """生成修复报告"""
            'total_fixes': len(self.fixed_issues),
                'by_severity': {},
                'by_type': {}
            },
        }

        for issue in self.fixed_issues:
            severity = issue.get('severity', 'unknown')
            report['summary']['by_severity'][severity] = report['summary']['by_severity'].get(severity, 0) + 1
            report['summary']['by_type'][error_type] = report['summary']['by_type'].get(error_type, 0) + 1

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return report_file

def main():
    # 检测错误
    errors = fixer.run_error_detection()
    print(f"\n总计发现 {len(errors)} 个问题")

    # 执行修复
    if errors:
        result = fixer.run_fix(errors)

        # 生成报告
        report_file = fixer.generate_report()
    else:
        print("\n未发现需要修复的问题")

if __name__ == "__main__":
    main()
