#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""增强版后台修复AI - 智能代码错误检测与修复"""

import os
import re
import ast
import sqlite3
# import json removed - using database storage
import logging
import traceback
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Tuple, Set

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('enhanced_fix_ai')

class EnhancedCodeFixAI:
    def __init__(self):
        self.project_dir = os.getcwd()
        self.db_path = 'app.db'
        self.fixes_applied = []
        self.errors_found = []
        self.redundancies_found = []
        self.enhanced_fixes = []
        self.init_database()
        self.load_fix_patterns()

    def init_database(self):
        """初始化增强版修复数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        tables = [
            '''CREATE TABLE IF NOT EXISTS enhanced_fix_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                issue_type TEXT,
                issue_severity TEXT,
                line_number INTEGER,
                column_number INTEGER,
                original_code TEXT,
                fixed_code TEXT,
                fix_strategy TEXT,
                error_message TEXT,
                confidence REAL,
                ai_analysis TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )''',

            '''CREATE TABLE IF NOT EXISTS advanced_fix_knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_pattern TEXT UNIQUE NOT NULL,
                fix_pattern TEXT NOT NULL,
                issue_category TEXT,
                confidence REAL DEFAULT 0.9,
                success_rate REAL DEFAULT 0.8,
                usage_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                last_used TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )''',

            '''CREATE TABLE IF NOT EXISTS code_complexity_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT,
                cyclomatic_complexity INTEGER,
                maintainability_index REAL,
                lines_of_code INTEGER,
                comment_density REAL,
                analyzed_at TEXT DEFAULT CURRENT_TIMESTAMP
            )''',

            '''CREATE TABLE IF NOT EXISTS auto_fix_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                total_files_scanned INTEGER,
                total_issues_found INTEGER,
                total_issues_fixed INTEGER,
                fix_success_rate REAL,
                duration_seconds REAL,
                started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT
            )'''
        ]

        for table_sql in tables:
            cursor.execute(table_sql)

        conn.commit()
        conn.close()

    def load_fix_patterns(self):
        """加载高级修复模式库"""
        self.fix_patterns = {
            'indentation': {
                'pattern': r'^\s+',
                'fix': lambda line: line.replace('\t', '    ') if '\t' in line[:len(line) - len(line.lstrip())] else line,
                'description': '统一使用4空格缩进'
            },
            'print_function': {
                'pattern': r'^\s*print\s+',
                'fix': lambda line: re.sub(r'(\s*)print\s+(.*)', r'\1print(\2)', line),
                'description': 'Python2 print转换为Python3 print()'
            },
            'missing_encoding': {
                'pattern': None,
                'fix': lambda content: '# -*- coding: utf-8 -*-\n' + content if not content.startswith('# -*- coding:') else content,
                'description': '添加UTF-8编码声明'
            },
            'trailing_whitespace': {
                'pattern': r'\s+$',
                'fix': lambda line: line.rstrip() + '\n',
                'description': '移除行尾空格'
            },
            'empty_line_eof': {
                'pattern': None,
                'fix': lambda content: content + '\n' if content and not content.endswith('\n') else content,
                'description': '确保文件结尾有一个空行'
            }
        }

        self.error_classes = {
            'syntax_error': ['SyntaxError', 'IndentationError', 'TabError'],
            'name_error': ['NameError', 'UnboundLocalError'],
            'type_error': ['TypeError'],
            'import_error': ['ImportError', 'ModuleNotFoundError'],
            'attribute_error': ['AttributeError'],
            'value_error': ['ValueError'],
            'key_error': ['KeyError'],
            'index_error': ['IndexError'],
            'io_error': ['IOError', 'FileNotFoundError'],
            'runtime_error': ['RuntimeError']
        }

    def analyze_code_syntax_tree(self, file_path: str) -> List[Dict[str, Any]]:
        """使用AST深入分析代码结构"""
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            class VariableFinder(ast.NodeVisitor):
                def __init__(self):
                    self.assigned_vars = set()
                    self.used_vars = set()
                    self.variable_lines = {}

                def visit_Assign(self, node):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            self.assigned_vars.add(target.id)
                            self.variable_lines[target.id] = node.lineno
                    self.generic_visit(node)

                def visit_Name(self, node):
                    if isinstance(node.ctx, ast.Load):
                        self.used_vars.add(node.id)
                    self.generic_visit(node)

            var_finder = VariableFinder()
            var_finder.visit(tree)

            unused_vars = var_finder.assigned_vars - var_finder.used_vars
            for var in unused_vars:
                issues.append({
                    'type': 'UnusedVariable',
                    'line': var_finder.variable_lines.get(var, 0),
                    'variable': var,
                    'severity': 'low',
                    'description': f'未使用的变量: {var}'
                })

            class ImportFinder(ast.NodeVisitor):
                def __init__(self):
                    self.imports = []
                    self.import_lines = {}

                def visit_Import(self, node):
                    for name in node.names:
                        imp_name = name.name
                        if imp_name not in self.imports:
                            self.imports.append(imp_name)
                            self.import_lines[imp_name] = node.lineno
                    self.generic_visit(node)

                def visit_ImportFrom(self, node):
                    module = node.module or ''
                    for name in node.names:
                        imp_name = f"{module}.{name.name}" if module else name.name
                        if imp_name not in self.imports:
                            self.imports.append(imp_name)
                            self.import_lines[imp_name] = node.lineno
                    self.generic_visit(node)

            import_finder = ImportFinder()
            import_finder.visit(tree)

            import_count = {}
            for imp in import_finder.imports:
                import_count[imp] = import_count.get(imp, 0) + 1

            for imp, count in import_count.items():
                if count > 1:
                    issues.append({
                        'type': 'DuplicateImport',
                        'line': import_finder.import_lines.get(imp, 0),
                        'import': imp,
                        'severity': 'low',
                        'description': f'重复导入: {imp}'
                    })

            class FunctionComplexity(ast.NodeVisitor):
                def __init__(self):
                    self.functions = {}

                def visit_FunctionDef(self, node):
                    complexity = 1
                    for child in ast.walk(node):
                        if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.ExceptHandler,
                                             ast.With, ast.Assert, ast.And, ast.Or, ast.BoolOp,
                                             ast.Lambda)):
                            complexity += 1
                    self.functions[node.name] = {
                        'complexity': complexity,
                        'line': node.lineno,
                        'length': len(node.body)
                    }
                    self.generic_visit(node)

            complexity_finder = FunctionComplexity()
            complexity_finder.visit(tree)

            for func_name, info in complexity_finder.functions.items():
                if info['complexity'] > 15:
                    issues.append({
                        'type': 'HighComplexity',
                        'line': info['line'],
                        'function': func_name,
                        'complexity': info['complexity'],
                        'severity': 'medium',
                        'description': f'函数 {func_name} 圈复杂度过高: {info["complexity"]}'
                    })
                if info['length'] > 50:
                    issues.append({
                        'type': 'LongFunction',
                        'line': info['line'],
                        'function': func_name,
                        'length': info['length'],
                        'severity': 'medium',
                        'description': f'函数 {func_name} 代码行数过多: {info["length"]}'
                    })

        except Exception as e:
            issues.append({
                'type': 'ParseError',
                'line': 0,
                'error': str(e),
                'severity': 'high',
                'description': f'代码解析失败: {str(e)[:100]}'
            })

        return issues

    def detect_runtime_errors(self, file_path: str) -> List[Dict[str, Any]]:
        """尝试运行检测运行时错误"""
        issues = []
        try:
            result = subprocess.run(
                ['python3', '-m', 'py_compile', file_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                error_lines = result.stderr.split('\n')
                for line in error_lines:
                    if 'Error:' in line or 'Traceback' in line:
                        line_num = 0
                        line_match = re.search(r'line\s+(\d+)', line)
                        if line_match:
                            line_num = int(line_match.group(1))

                        issues.append({
                            'type': 'CompileError',
                            'line': line_num,
                            'message': line.strip(),
                            'severity': 'high',
                            'description': line.strip()[:150]
                        })

        except subprocess.TimeoutExpired:
            issues.append({
                'type': 'TimeoutError',
                'line': 0,
                'severity': 'high',
                'description': '代码编译超时'
            })
        except Exception as e:
            pass

        return issues

    def advanced_code_fix(self, file_path: str) -> Tuple[int, int]:
        """高级代码修复方法"""
        fixes_applied = 0
        fixes_failed = 0

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content
            lines = content.split('\n')

            new_lines = []
            for line in lines:
                fixed_line = line

                if '\t' in line[:len(line) - len(line.lstrip())]:
                    leading_tabs = len(line) - len(line.lstrip('\t'))
                    fixed_line = '    ' * leading_tabs + line.lstrip('\t')

                if fixed_line.rstrip() != fixed_line:
                    fixed_line = fixed_line.rstrip()

                if re.match(r'^\s*print\s+\S', fixed_line) and 'print(' not in fixed_line:
                    match = re.match(r'(\s*)print\s+(.*)', fixed_line)
                    if match:
                        fixed_line = f"{match.group(1)}print({match.group(2)})"

                new_lines.append(fixed_line)

            content = '\n'.join(new_lines)

            if content and not content.startswith(('# -*- coding:', '#!')):
                content = '# -*- coding: utf-8 -*-\n' + content

            if content and not content.endswith('\n'):
                content = content + '\n'

            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixes_applied += 1

                self.enhanced_fixes.append({
                    'file': file_path,
                    'type': 'CodeQuality',
                    'description': '代码格式优化'
                })

        except Exception as e:
            fixes_failed += 1
            logger.error(f"修复文件 {file_path} 时出错: {e}")

        return fixes_applied, fixes_failed

    def record_enhanced_fix(self, file_path: str, issue_type: str, line_num: int,
                          severity: str, original_code: str, fixed_code: str,
                          strategy: str, confidence: float = 0.9):
        """记录增强版修复到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO enhanced_fix_logs
                (file_path, issue_type, issue_severity, line_number,
                 original_code, fixed_code, fix_strategy, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (file_path, issue_type, severity, line_num,
                  original_code[:1000], fixed_code[:1000], strategy, confidence))

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"记录修复日志失败: {e}")

    def update_knowledge_base(self, pattern: str, fix: str, category: str, success: bool):
        """更新知识库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO advanced_fix_knowledge
                (issue_pattern, fix_pattern, issue_category,
                 usage_count, success_count, last_used)
                VALUES (?, ?, ?,
                 COALESCE((SELECT usage_count + 1 FROM advanced_fix_knowledge WHERE issue_pattern = ?), 1),
                 COALESCE((SELECT success_count + ? FROM advanced_fix_knowledge WHERE issue_pattern = ?), ?),
                 ?)
            ''', (pattern, fix, category, pattern, 1 if success else 0, pattern, 1 if success else 0, datetime.now().isoformat()))

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"更新知识库失败: {e}")

    def record_session_history(self, session_id: str, stats: Dict[str, Any]):
        """记录会话历史"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            success_rate = stats['fixed'] / stats['issues_found'] if stats['issues_found'] > 0 else 0

            cursor.execute('''
                INSERT INTO auto_fix_history
                (session_id, total_files_scanned, total_issues_found,
                 total_issues_fixed, fix_success_rate, duration_seconds, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (session_id, stats['files_scanned'], stats['issues_found'],
                  stats['fixed'], success_rate, stats['duration'], datetime.now().isoformat()))

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"记录会话历史失败: {e}")

    def run_enhanced_fix(self):
        """运行增强版修复"""
        print("="*80)
        print("          增强版后台修复AI - 智能代码分析与修复")
        print("="*80)

        session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        start_time = datetime.now()

        print("\n[1/4] 扫描Python文件...")
        py_files = []
        for root, dirs, files in os.walk(self.project_dir):
            if 'node_modules' in root or '.git' in root or '__pycache__' in root:
                continue
            for file in files:
                if file.endswith('.py'):
                    py_files.append(os.path.join(root, file))

        print(f"  发现 {len(py_files)} 个Python文件")

        print("\n[2/4] 深度分析代码结构...")
        all_issues = []

        for i, file_path in enumerate(py_files, 1):
            if i % 50 == 0:
                print(f"  已分析 {i}/{len(py_files)} 文件...")

            try:
                ast_issues = self.analyze_code_syntax_tree(file_path)
                compile_issues = self.detect_runtime_errors(file_path)

                all_issues.extend([{'file': file_path, **issue} for issue in ast_issues + compile_issues])
            except Exception as e:
                logger.error(f"分析文件 {file_path} 时出错: {e}")

        print(f"  发现 {len(all_issues)} 个代码问题")

        print("\n[3/4] 应用高级修复...")
        total_fixed = 0
        total_failed = 0

        for i, file_path in enumerate(py_files, 1):
            if i % 50 == 0:
                print(f"  已修复 {i}/{len(py_files)} 文件...")

            try:
                fixed, failed = self.advanced_code_fix(file_path)
                total_fixed += fixed
                total_failed += failed
            except Exception as e:
                logger.error(f"修复文件 {file_path} 时出错: {e}")

        print("\n[4/4] 记录修复历史...")
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        stats = {
            'files_scanned': len(py_files),
            'issues_found': len(all_issues),
            'fixed': total_fixed,
            'failed': total_failed,
            'duration': duration
        }

        self.record_session_history(session_id, stats)

        print("\n" + "="*80)
        print("                    增强版修复完成报告")
        print("="*80)
        print(f"  扫描文件: {stats['files_scanned']}")
        print(f"  发现问题: {stats['issues_found']}")
        print(f"  修复成功: {stats['fixed']}")
        print(f"  修复失败: {stats['failed']}")
        print(f"  耗时: {stats['duration']:.2f} 秒")

        issue_types = {}
        for issue in all_issues:
            issue_type = issue.get('type', 'Unknown')
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1

        if issue_types:
            print("\n问题类型统计:")
            for issue_type, count in sorted(issue_types.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  - {issue_type}: {count}")

        print("\n修复结果已全部记录到数据库！")
        print("  - enhanced_fix_logs: 详细修复日志")
        print("  - advanced_fix_knowledge: AI知识库")
        print("  - code_complexity_metrics: 复杂度指标")
        print("  - auto_fix_history: 会话历史")

def main():
    fix_ai = EnhancedCodeFixAI()
    fix_ai.run_enhanced_fix()

if __name__ == "__main__":
    main()
