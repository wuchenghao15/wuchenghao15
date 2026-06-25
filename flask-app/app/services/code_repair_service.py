#!/usr/bin/env python3
"""
代码修复服务 - AI员工模块
自动监控异常和修复系统代码错误，支持多种文件类型
"""

import os
import re
import json
import ast
import time
import sqlite3
import tarfile
from datetime import datetime
from contextlib import contextmanager
from flask import request

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'mtscos.db')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_repair_tables():
    """初始化代码修复表"""
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
                applied_by TEXT DEFAULT 'system',
                verified INTEGER DEFAULT 0,
                verify_time INTEGER,
                notes TEXT
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_repair_file_path ON code_repair_logs(file_path)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_repair_type ON code_repair_logs(file_type)')
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
    print("[INFO] 代码修复表初始化完成")


def generate_repair_id():
    """生成修复ID"""
    return f"rep_{int(time.time())}_{hash(str(time.time())) % 10000}"


def generate_error_id(file_path, error_type):
    """生成错误ID"""
    return f"err_{hash(f'{file_path}_{error_type}_{int(time.time())}') % 1000000:06d}"


def detect_python_errors(file_path, content):
    """检测Python语法错误"""
    errors = []
    try:
        ast.parse(content)
    except SyntaxError as e:
        errors.append({
            'error_type': 'python_syntax_error',
            'error_message': str(e),
            'error_line': e.lineno or 0,
            'error_column': e.offset or 0,
            'severity': 'high'
        })
    
    except_blocks = re.findall(r'\nexcept\s*:', content)
    if except_blocks:
        errors.append({
            'error_type': 'empty_except_block',
            'error_message': '发现空except块，需要添加pass或处理逻辑',
            'error_line': 0,
            'error_column': 0,
            'severity': 'medium'
        })
    
    indentation_issues = re.findall(r'^(\s*)\S', content, re.MULTILINE)
    mixed_indent = any(len(s) > 0 and (s.count(' ') % 4 != 0 or ('\t' in s)) for s in indentation_issues)
    if mixed_indent:
        errors.append({
            'error_type': 'mixed_indentation',
            'error_message': '发现混合缩进（空格和制表符混用）',
            'error_line': 0,
            'error_column': 0,
            'severity': 'medium'
        })
    
    blue_patterns = ['Blue@', '= Bluelogger', 'register_blue']
    for pattern in blue_patterns:
        if pattern in content:
            errors.append({
                'error_type': 'corrupted_blueprint',
                'error_message': f'发现Blueprint损坏模式: {pattern}',
                'error_line': 0,
                'error_column': 0,
                'severity': 'high'
            })
    
    return errors


def detect_js_errors(file_path, content):
    """检测JavaScript语法错误"""
    errors = []
    
    unmatched_braces = content.count('{') - content.count('}')
    if unmatched_braces != 0:
        errors.append({
            'error_type': 'unmatched_braces',
            'error_message': f'花括号不匹配，差{abs(unmatched_braces)}个',
            'error_line': 0,
            'error_column': 0,
            'severity': 'high'
        })
    
    unmatched_parens = content.count('(') - content.count(')')
    if unmatched_parens != 0:
        errors.append({
            'error_type': 'unmatched_parentheses',
            'error_message': f'圆括号不匹配，差{abs(unmatched_parens)}个',
            'error_line': 0,
            'error_column': 0,
            'severity': 'high'
        })
    
    unmatched_brackets = content.count('[') - content.count(']')
    if unmatched_brackets != 0:
        errors.append({
            'error_type': 'unmatched_brackets',
            'error_message': f'方括号不匹配，差{abs(unmatched_brackets)}个',
            'error_line': 0,
            'error_column': 0,
            'severity': 'high'
        })
    
    unterminated_strings = re.findall(r"'[^']*$|\"[^\"]*$", content, re.MULTILINE)
    if unterminated_strings:
        errors.append({
            'error_type': 'unterminated_string',
            'error_message': '发现未终止的字符串',
            'error_line': 0,
            'error_column': 0,
            'severity': 'high'
        })
    
    return errors


def detect_json_errors(file_path, content):
    """检测JSON语法错误"""
    errors = []
    try:
        json.loads(content)
    except json.JSONDecodeError as e:
        errors.append({
            'error_type': 'json_parse_error',
            'error_message': str(e),
            'error_line': e.lineno or 0,
            'error_column': e.colno or 0,
            'severity': 'high'
        })
    
    return errors


def detect_sql_errors(file_path, content):
    """检测SQL语法错误"""
    errors = []
    
    missing_semicolon = not content.strip().endswith(';') if content.strip() else False
    if missing_semicolon:
        errors.append({
            'error_type': 'missing_semicolon',
            'error_message': 'SQL语句缺少分号结尾',
            'error_line': 0,
            'error_column': 0,
            'severity': 'medium'
        })
    
    keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'WHERE']
    for keyword in keywords:
        if re.search(rf'\b{keyword.lower()}\b', content):
            errors.append({
                'error_type': 'lowercase_keyword',
                'error_message': f'SQL关键字应大写: {keyword}',
                'error_line': 0,
                'error_column': 0,
                'severity': 'low'
            })
    
    return errors


def detect_html_errors(file_path, content):
    """检测HTML语法错误"""
    errors = []
    
    open_tags = re.findall(r'<([a-zA-Z][a-zA-Z0-9]*)\b[^>]*>', content)
    close_tags = re.findall(r'</([a-zA-Z][a-zA-Z0-9]*)>', content)
    
    from collections import Counter
    open_counts = Counter(open_tags)
    close_counts = Counter(close_tags)
    
    for tag in open_counts:
        if open_counts[tag] != close_counts.get(tag, 0):
            errors.append({
                'error_type': 'unclosed_tag',
                'error_message': f'标签未正确闭合: <{tag}>',
                'error_line': 0,
                'error_column': 0,
                'severity': 'medium'
            })
    
    self_closing_tags = ['br', 'img', 'input', 'meta', 'link', 'hr']
    for tag in close_counts:
        if tag in self_closing_tags:
            errors.append({
                'error_type': 'unnecessary_close_tag',
                'error_message': f'自闭合标签不应有闭合标签: </{tag}>',
                'error_line': 0,
                'error_column': 0,
                'severity': 'low'
            })
    
    return errors


def detect_css_errors(file_path, content):
    """检测CSS语法错误"""
    errors = []
    
    unmatched_curly = content.count('{') - content.count('}')
    if unmatched_curly != 0:
        errors.append({
            'error_type': 'unmatched_curly_braces',
            'error_message': f'花括号不匹配，差{abs(unmatched_curly)}个',
            'error_line': 0,
            'error_column': 0,
            'severity': 'high'
        })
    
    invalid_selectors = re.findall(r'^[^{}\s]+(?=\s*\{)', content, re.MULTILINE)
    for selector in invalid_selectors:
        if not re.match(r'^[a-zA-Z0-9#.\-_:[\]()*,>+~ ]+$', selector):
            errors.append({
                'error_type': 'invalid_selector',
                'error_message': f'无效的CSS选择器: {selector}',
                'error_line': 0,
                'error_column': 0,
                'severity': 'medium'
            })
    
    return errors


def detect_tar_errors(file_path):
    """检测tar文件错误"""
    errors = []
    try:
        with tarfile.open(file_path, 'r:*') as tar:
            tar.list()
    except Exception as e:
        errors.append({
            'error_type': 'tar_corrupted',
            'error_message': str(e),
            'error_line': 0,
            'error_column': 0,
            'severity': 'high'
        })
    return errors


def detect_file_errors(file_path):
    """检测文件错误"""
    errors = []
    
    if not os.path.exists(file_path):
        errors.append({
            'error_type': 'file_not_found',
            'error_message': f'文件不存在: {file_path}',
            'error_line': 0,
            'error_column': 0,
            'severity': 'high'
        })
        return errors
    
    file_type = os.path.splitext(file_path)[1].lower()[1:]
    
    try:
        if file_type in ['py', 'js', 'css', 'json', 'sql', 'html']:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if file_type == 'py':
                errors.extend(detect_python_errors(file_path, content))
            elif file_type == 'js':
                errors.extend(detect_js_errors(file_path, content))
            elif file_type == 'json':
                errors.extend(detect_json_errors(file_path, content))
            elif file_type == 'sql':
                errors.extend(detect_sql_errors(file_path, content))
            elif file_type == 'html':
                errors.extend(detect_html_errors(file_path, content))
            elif file_type == 'css':
                errors.extend(detect_css_errors(file_path, content))
        elif file_type == 'tar':
            errors.extend(detect_tar_errors(file_path))
        elif file_type == 'bak':
            errors.extend(detect_file_errors(file_path[:-4]))
        else:
            errors.append({
                'error_type': 'unsupported_type',
                'error_message': f'不支持的文件类型: {file_type}',
                'error_line': 0,
                'error_column': 0,
                'severity': 'low'
            })
    except Exception as e:
        errors.append({
            'error_type': 'file_read_error',
            'error_message': f'读取文件失败: {e}',
            'error_line': 0,
            'error_column': 0,
            'severity': 'high'
        })
    
    return errors


def fix_empty_except(content):
    """修复空except块"""
    lines = content.split('\n')
    fixed_lines = []
    for i, line in enumerate(lines):
        if re.match(r'^\s*except\s*:', line):
            fixed_lines.append(line)
            indent = ' ' * len(line) - len(line.lstrip())
            fixed_lines.append(' ' * indent + '    pass')
        else:
            fixed_lines.append(line)
    return '\n'.join(fixed_lines)


def fix_mixed_indentation(content):
    """修复混合缩进"""
    lines = content.split('\n')
    fixed_lines = []
    for line in lines:
        leading = len(line) - len(line.lstrip())
        if leading > 0:
            if '\t' in line[:leading]:
                spaces = line[:leading].count(' ') + line[:leading].count('\t') * 4
                fixed_lines.append(' ' * spaces + line.lstrip())
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    return '\n'.join(fixed_lines)


def fix_corrupted_blueprint(content):
    """修复损坏的Blueprint"""
    content = content.replace('Blue@', 'bp = ')
    content = re.sub(r'= Bluelogger\s*=\s*', '', content)
    content = content.replace('register_blue', 'app.register_blueprint')
    return content


def fix_json_syntax(content):
    """修复JSON语法"""
    try:
        json.loads(content)
        return content
    except Exception:
        content = content.replace("'", '"')
        content = re.sub(r',\s*}', '}', content)
        content = re.sub(r',\s*]', ']', content)
        try:
            json.loads(content)
            return content
        except Exception:
            return content


def fix_sql_syntax(content):
    """修复SQL语法"""
    content = content.strip()
    if not content.endswith(';'):
        content += ';'
    keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'WHERE', 
                'FROM', 'JOIN', 'ON', 'AND', 'OR', 'NOT', 'IN', 'LIKE', 'ORDER', 'BY', 'LIMIT']
    for keyword in keywords:
        content = re.sub(rf'\b{keyword.lower()}\b', keyword, content)
    return content


def fix_html_tags(content):
    """修复HTML标签"""
    content = re.sub(r'</(br|img|input|meta|link|hr)\s*>', '', content)
    return content


def fix_js_braces(content):
    """修复JS括号"""
    content = content.strip()
    if content and not content.endswith('}'):
        content += '}'
    return content


def fix_css_braces(content):
    """修复CSS花括号"""
    content = content.strip()
    if content and not content.endswith('}'):
        content += '}'
    return content


def fix_file_errors(file_path):
    """修复文件错误"""
    repair_id = generate_repair_id()
    file_type = os.path.splitext(file_path)[1].lower()[1:]
    before_content = ''
    after_content = ''
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            before_content = f.read()
        
        errors = detect_file_errors(file_path)
        
        if not errors:
            return repair_id, 'no_errors', '未发现错误'
        
        after_content = before_content
        
        for error in errors:
            error_type = error['error_type']
            
            if error_type == 'empty_except_block':
                after_content = fix_empty_except(after_content)
            elif error_type == 'mixed_indentation':
                after_content = fix_mixed_indentation(after_content)
            elif error_type == 'corrupted_blueprint':
                after_content = fix_corrupted_blueprint(after_content)
            elif error_type == 'json_parse_error':
                after_content = fix_json_syntax(after_content)
            elif error_type == 'missing_semicolon':
                after_content = fix_sql_syntax(after_content)
            elif error_type == 'unclosed_tag':
                after_content = fix_html_tags(after_content)
            elif error_type == 'unmatched_braces':
                after_content = fix_js_braces(after_content)
            elif error_type == 'unmatched_curly_braces':
                after_content = fix_css_braces(after_content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(after_content)
        
        for error in errors:
            error_id = generate_error_id(file_path, error['error_type'])
            with get_db() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO code_errors (
                        error_id, file_path, file_type, error_type, error_message,
                        error_line, error_column, detected_at, severity, status,
                        fixed_by, fixed_at, repair_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    error_id, file_path, file_type, error['error_type'], error['error_message'],
                    error['error_line'], error['error_column'], int(time.time()),
                    error['severity'], 'fixed', 'code_repair_ai', int(time.time()), repair_id
                ))
                conn.commit()
        
        with get_db() as conn:
            conn.execute('''
                INSERT INTO code_repair_logs (
                    repair_id, file_path, file_type, error_type, error_message,
                    error_line, before_content, after_content, fix_status,
                    repair_time, applied_by, verified
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                repair_id, file_path, file_type, 
                ','.join(e['error_type'] for e in errors),
                ','.join(e['error_message'] for e in errors),
                errors[0]['error_line'], before_content[:500], after_content[:500],
                'applied', int(time.time()), 'code_repair_ai', 1
            ))
            conn.commit()
        
        return repair_id, 'success', f'修复了{len(errors)}个错误'
    
    except Exception as e:
        with get_db() as conn:
            conn.execute('''
                INSERT INTO code_repair_logs (
                    repair_id, file_path, file_type, error_type, error_message,
                    before_content, after_content, fix_status, repair_time, applied_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                repair_id, file_path, file_type, 'repair_failed', str(e),
                before_content[:500], '', 'failed', int(time.time()), 'code_repair_ai'
            ))
            conn.commit()
        
        return repair_id, 'failed', str(e)


def scan_directory_for_errors(directory, extensions=['.py', '.js', '.css', '.json', '.sql', '.html', '.bak']):
    """扫描目录中的错误"""
    all_errors = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                try:
                    errors = detect_file_errors(file_path)
                    if errors:
                        all_errors.extend(errors)
                        for error in errors:
                            error_id = generate_error_id(file_path, error['error_type'])
                            with get_db() as conn:
                                conn.execute('''
                                    INSERT OR IGNORE INTO code_errors (
                                        error_id, file_path, file_type, error_type,
                                        error_message, error_line, error_column,
                                        detected_at, severity, status
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                ''', (
                                    error_id, file_path, os.path.splitext(file)[1].lower()[1:],
                                    error['error_type'], error['error_message'],
                                    error['error_line'], error['error_column'],
                                    int(time.time()), error['severity'], 'unfixed'
                                ))
                                conn.commit()
                except Exception as e:
                    print(f"[ERROR] 扫描文件失败: {file_path} - {e}")
    
    return all_errors


def auto_repair_directory(directory, extensions=['.py', '.js', '.css', '.json', '.sql', '.html', '.bak']):
    """自动修复目录中的错误"""
    repair_results = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                repair_id, status, message = fix_file_errors(file_path)
                repair_results.append({
                    'file_path': file_path,
                    'repair_id': repair_id,
                    'status': status,
                    'message': message
                })
    
    return repair_results


def get_repair_stats():
    """获取修复统计"""
    try:
        with get_db() as conn:
            total_errors = conn.execute('SELECT COUNT(*) FROM code_errors').fetchone()[0]
            unfixed_errors = conn.execute('SELECT COUNT(*) FROM code_errors WHERE status = "unfixed"').fetchone()[0]
            fixed_errors = conn.execute('SELECT COUNT(*) FROM code_errors WHERE status = "fixed"').fetchone()[0]
            
            total_repairs = conn.execute('SELECT COUNT(*) FROM code_repair_logs').fetchone()[0]
            successful_repairs = conn.execute('SELECT COUNT(*) FROM code_repair_logs WHERE fix_status = "applied"').fetchone()[0]
            failed_repairs = conn.execute('SELECT COUNT(*) FROM code_repair_logs WHERE fix_status = "failed"').fetchone()[0]
            
            error_by_type = conn.execute('''
                SELECT error_type, COUNT(*) as count 
                FROM code_errors 
                GROUP BY error_type 
                ORDER BY count DESC
            ''').fetchall()
            
            return {
                'total_errors': total_errors,
                'unfixed_errors': unfixed_errors,
                'fixed_errors': fixed_errors,
                'total_repairs': total_repairs,
                'successful_repairs': successful_repairs,
                'failed_repairs': failed_repairs,
                'error_by_type': [dict(r) for r in error_by_type],
                'updated_at': int(time.time())
            }
    except Exception as e:
        print(f"[ERROR] 获取修复统计失败: {e}")
        return {}


def get_pending_errors(limit=50):
    """获取未修复的错误"""
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


def create_repair_employee():
    """创建代码修复AI员工"""
    employee_id = 'emp_code_repair_ai'
    
    try:
        with get_db() as conn:
            conn.execute('''
                INSERT OR IGNORE INTO ai_employees (
                    employee_id, name, title, description, category,
                    capabilities, efficiency, workload, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                employee_id,
                '代码修复员',
                '系统代码自动修复专家',
                '负责监控系统代码异常，自动检测和修复Python、JavaScript、CSS、JSON、SQL、HTML等多种文件类型的错误',
                'development',
                json.dumps([
                    'Python语法错误检测与修复',
                    'JavaScript语法错误检测与修复',
                    'CSS语法错误检测与修复',
                    'JSON语法错误检测与修复',
                    'SQL语法错误检测与修复',
                    'HTML语法错误检测与修复',
                    'TAR文件完整性检测',
                    'BAK备份文件检测',
                    '目录批量扫描与修复',
                    '修复记录自动上传数据库',
                    '修复统计分析',
                    '实时错误告警'
                ]),
                95,
                0,
                int(time.time()),
                int(time.time())
            ))
            conn.commit()
        print("[INFO] 代码修复AI员工创建完成")
        return True
    except Exception as e:
        print(f"[ERROR] 创建代码修复AI员工失败: {e}")
        return False


def get_repair_employee():
    """获取代码修复AI员工信息"""
    try:
        with get_db() as conn:
            row = conn.execute(
                'SELECT * FROM ai_employees WHERE employee_id = ?', ('emp_code_repair_ai',)
            ).fetchone()
            return dict(row) if row else None
    except Exception as e:
        print(f"[ERROR] 获取代码修复AI员工失败: {e}")
        return None


if __name__ == '__main__':
    init_repair_tables()
    create_repair_employee()
    print("代码修复服务初始化完成")
