#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""后台修复AI - 自动检测和修复代码错误与冗余"""

import os
import re
import ast
import sqlite3
# import json removed - using database storage
import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('code_fix_ai')

class CodeFixAI:
    def __init__(self):
        self.project_dir = os.getcwd()
        self.db_path = 'app.db'
        self.fixes_applied = []
        self.errors_found = []
        self.redundancies_found = []
        self.init_database()

    def init_database(self):
        """初始化修复日志表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS code_fix_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT,
                issue_type TEXT,
                issue_description TEXT,
                line_number INTEGER,
                original_code TEXT,
                fixed_code TEXT,
                fix_strategy TEXT,
                confidence REAL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

            CREATE TABLE IF NOT EXISTS ai_fix_knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fix_pattern TEXT,
                issue_type TEXT,
                confidence REAL DEFAULT 0.8,
                last_used TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_count INTEGER,
                redundancy_count INTEGER,
                analyzed_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

        """检测语法错误"""
        errors = []
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            try:
                ast.parse(content)
            except SyntaxError as e:
                errors.append({
                    'type': 'SyntaxError',
                    'line': e.lineno,
                    'column': e.offset,
                    'message': str(e),
                    'context': e.text.strip() if e.text else '',
                    'severity': 'high'

            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                # 检测混合缩进
                has_spaces = line.startswith(' ')
                has_tabs = line.startswith('\t')
                if has_spaces and '\t' in line[:len(line) - len(line.lstrip())]:
                    errors.append({
                        'type': 'MixedIndentation',
                        'line': i,
                        'message': '混合使用空格和制表符缩进',
                        'context': line[:50],
                        'severity': 'medium'
                    })

                # 检测过长行
                if len(line) > 120:
                    errors.append({
                        'line': i,
                        'message': f'行长度超过120字符 ({len(line)} chars)',
                        'context': line[:50],
                        'severity': 'low'
                    })

                if line != line.rstrip():
                    errors.append({
                        'line': i,
                        'message': '行尾有多余空格',
                        'context': line[:30],
                        'severity': 'low'

                # 检测未使用的导入模式
                # 检测 print 语句 (Python2语法)
                if re.match(r'^\s*print\s+\S', line) and 'print(' not in line:
                    errors.append({
                        'type': 'Python2Print',
                        'line': i,
                        'message': '发现Python2 print语句',
                        'severity': 'medium'

        except Exception as e:
            errors.append({
                'type': 'FileReadError',
                'context': '',
                'severity': 'high'
            })

        return errors

    def detect_redundancies(self, file_path: str) -> List[Dict[str, Any]]:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.split('\n')
            line_counts = {}
            for i, line in enumerate(lines, 1):
                    redundancies.append({
                        'lines': positions,
                        'message': f'发现重复代码行',
                        'context': line_content[:50],
                        'count': len(positions)
                    })

            # 检测未使用的变量模式
            var_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*='
            assigned_vars = set()
            used_vars = set()

            for line in lines:
                for match in re.finditer(var_pattern, line):
                    assigned_vars.add(match.group(1))
                for var in assigned_vars:
                    if var in line and f'{var}=' not in line:
                        used_vars.add(var)
            unused_vars = assigned_vars - used_vars
            if unused_vars:
                redundancies.append({
                    'type': 'UnusedVariables',
                    'lines': [],
                    'message': f'发现未使用的变量: {", ".join(unused_vars)}',
                    'count': len(unused_vars)
                })

            # 检测重复导入
            imports = []
            for line in lines:
                if line.startswith('import ') or line.startswith('from '):
                    imports.append(line.strip())

            import_counts = {}
            for imp in imports:
                import_counts[imp] = import_counts.get(imp, 0) + 1

            for imp, count in import_counts.items():
                if count > 1:
                    redundancies.append({
                        'type': 'DuplicateImports',
                        'lines': [],
                        'message': f'重复导入: {imp}',
                        'context': imp,
                        'count': count
                    })
        except Exception as e:
            pass

        return redundancies

    def fix_syntax_error(self, file_path: str, error: Dict[str, Any]) -> Tuple[bool, str]:
        """修复语法错误"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:

            original_line = lines[error['line'] - 1] if error['line'] > 0 else ''
            fixed_line = original_line
            fix_strategy = ''

            if error['type'] == 'MixedIndentation':
                # 转换为4空格缩进
                fixed_line = '    ' * leading_tabs + error['context'].lstrip('\t') + '\n'
                fix_strategy = '将制表符转换为4空格缩进'
                fixed_line = original_line.rstrip() + '\n'

            elif error['type'] == 'Python2Print':
                match = re.match(r'(\s*)print\s+(.*)', original_line)
                if match:
                    fixed_line = f"{match.group(1)}print({match.group(2)})"
                    if not fixed_line.endswith('\n'):
                        fixed_line += '\n'
                    fix_strategy = 'Python2 print转换为Python3 print()'
            if fixed_line != original_line:
                lines[error['line'] - 1] = fixed_line
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)

            return False, '无法修复'
        except Exception as e:
            return False, str(e)

    def fix_redundancy(self, file_path: str, redundancy: Dict[str, Any]) -> Tuple[bool, str]:
        """修复代码冗余"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            fix_strategy = ''

            if redundancy['type'] == 'DuplicateLines':
                # 保留第一行，删除其余重复行
                lines_to_remove = sorted(redundancy['lines'][1:], reverse=True)
                for line_num in lines_to_remove:
                fix_strategy = f'删除 {len(lines_to_remove)} 行重复代码'

            elif redundancy['type'] == 'DuplicateImports':
                # 移除重复导入
                first_occurrence = True
                new_lines = []
                removed_count = 0

                for line in lines:
                    if line.strip() == import_line:
                        if first_occurrence:
                            new_lines.append(line)
                            first_occurrence = False
                        else:
                            removed_count += 1
                    else:
                        new_lines.append(line)

                lines = new_lines
                fix_strategy = f'移除 {removed_count} 个重复导入'

            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)

            return True, fix_strategy
        except Exception as e:
            return False, str(e)

    def record_fix(self, file_path: str, issue_type: str, line_num: int,
                   original_code: str, fixed_code: str, fix_strategy: str, confidence: float = 0.9):
        """记录修复到数据库"""
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO code_fix_logs
             original_code, fixed_code, fix_strategy, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (file_path, issue_type, fix_strategy, line_num,
              original_code[:500], fixed_code[:500], fix_strategy, confidence))

        conn.close()

    def update_knowledge(self, issue_pattern: str, fix_pattern: str, issue_type: str):
        """更新AI脑库知识"""
        cursor = conn.cursor()

            INSERT OR REPLACE INTO ai_fix_knowledge
            (issue_pattern, fix_pattern, issue_type, usage_count, last_used)
            VALUES (?, ?, ?, COALESCE((SELECT usage_count + 1 FROM ai_fix_knowledge WHERE issue_pattern = ?), 1), ?)

        conn.commit()
        conn.close()
    def analyze_file(self, file_path: str):
        logger.info(f"分析文件: {file_path}")

        errors = self.detect_syntax_errors(file_path)
        redundancies = self.detect_redundancies(file_path)

        self.errors_found.extend([{'file': file_path, **e} for e in errors])
        self.redundancies_found.extend([{'file': file_path, **r} for r in redundancies])

        return errors, redundancies


            success, strategy = self.fix_syntax_error(file_path, error)
            if success:
                self.fixes_applied.append({
                    'type': 'error',
                    'line': error['line'],
                    'strategy': strategy
                self.record_fix(file_path, error['type'], error['line'],
                               error.get('context', ''), '', strategy)
                self.update_knowledge(error['type'], strategy, 'syntax')
        for redundancy in redundancies:
            success, strategy = self.fix_redundancy(file_path, redundancy)
            if success:
                lines_list = redundancy.get('lines', [])
                line_num = lines_list[0] if lines_list else 0
                self.fixes_applied.append({
                    'file': file_path,
                    'type': 'redundancy',
                    'issue_type': redundancy['type'],
                    'line': line_num,
                    'strategy': strategy
                })
                self.record_fix(file_path, redundancy['type'], line_num,
                               redundancy.get('context', ''), '', strategy)
                self.update_knowledge(redundancy['type'], strategy, 'redundancy')

    def run_full_analysis(self):
        """运行完整分析"""
        print("="*70)
        print("          后台修复AI - 代码错误和冗余检测")
        print("="*70)

        print("\n[1/2] 分析项目代码...")
        py_files = []

        for root, dirs, files in os.walk(self.project_dir):
            if 'node_modules' in root or '.git' in root or '__pycache__' in root:
                continue
                if file.endswith('.py'):
                    py_files.append(os.path.join(root, file))

        print(f"  发现 {len(py_files)} 个Python文件")

        for i, file_path in enumerate(py_files, 1):
            if i % 50 == 0:
                print(f"  已分析 {i}/{len(py_files)} 文件...")
            self.analyze_file(file_path)

        print(f"\n[2/2] 修复代码问题...")
        for i, file_path in enumerate(py_files, 1):
            if i % 50 == 0:
                print(f"  已修复 {i}/{len(py_files)} 文件...")
            self.fix_file(file_path)
        self.generate_report()

    def generate_report(self):
        """生成修复报告"""
        print("\n" + "="*70)
        print("                    修复完成报告")
        print("="*70)
        print(f"  发现错误: {len(self.errors_found)}")
        print(f"  发现冗余: {len(self.redundancies_found)}")
        print(f"  应用修复: {len(self.fixes_applied)}")

        # 按类型统计
        error_types = {}
        for fix in self.fixes_applied:
            error_types[fix['issue_type']] = error_types.get(fix['issue_type'], 0) + 1

        if error_types:
            print("\n修复类型统计:")
            for issue_type, count in error_types.items():
                print(f"  - {issue_type}: {count} 次")

        # 记录到数据库
        for file in set(f['file'] for f in self.fixes_applied):
            with open(file, 'r', encoding='utf-8') as f:

            cursor = conn.cursor()
            cursor.execute('''
                VALUES (?, ?, ?, ?, ?)
            conn.commit()

        print("\n修复报告已记录到数据库")

        """获取修复知识"""
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM ai_fix_knowledge ORDER BY usage_count DESC')
        knowledge = [dict(row) for row in cursor.fetchall()]
        conn.close()

def main():
    fix_ai = CodeFixAI()
    fix_ai.run_full_analysis()

    print(f"\n修复AI运行完成！")
    print(f"  修复记录: {len(fix_ai.fixes_applied)}")
    print(f"  知识条目: {len(fix_ai.get_fix_knowledge())}")
if __name__ == "__main__":
    main()
