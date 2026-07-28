#!/usr/bin/env python3
import ast
import os
import re
import sqlite3
import time
import json
from datetime import datetime
from typing import Dict, List, Any

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mtscos.db')
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_tables():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS syntax_repair_logs (
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
                applied_by TEXT DEFAULT 'syntax_fix_agent',
                verified INTEGER DEFAULT 0
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS syntax_errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_id TEXT UNIQUE NOT NULL,
                file_path TEXT NOT NULL,
                error_type TEXT NOT NULL,
                error_message TEXT,
                error_line INTEGER,
                detected_at INTEGER NOT NULL,
                status TEXT DEFAULT 'unfixed',
                fixed_by TEXT,
                fixed_at INTEGER,
                repair_id TEXT
            )
        ''')
        conn.commit()
    print("[INFO] 数据库表初始化完成")

def generate_id(prefix: str) -> str:
    return f"{prefix}_{int(time.time())}_{hash(str(time.time())) % 100000:05d}"

def detect_syntax_errors(file_path: str) -> List[Dict[str, Any]]:
    errors = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        ast.parse(content)
    except SyntaxError as e:
        errors.append({
            'error_type': 'syntax_error',
            'error_message': str(e),
            'error_line': e.lineno or 0,
            'error_column': e.offset or 0,
            'file_path': file_path
        })
    except Exception as e:
        errors.append({
            'error_type': 'read_error',
            'error_message': str(e),
            'error_line': 0,
            'error_column': 0,
            'file_path': file_path
        })
    return errors

def fix_eol_string(content: str) -> str:
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        if "'" in line or '"' in line:
            escaped_single = line.count("\\'")
            escaped_double = line.count('\\"')
            single_count = line.count("'") - escaped_single
            double_count = line.count('"') - escaped_double
            
            if single_count % 2 != 0:
                quote_type = "'"
                total_count = single_count
            elif double_count % 2 != 0:
                quote_type = '"'
                total_count = double_count
            else:
                fixed_lines.append(line)
                i += 1
                continue
            
            j = i + 1
            merged_line = line
            while j < len(lines):
                next_line = lines[j]
                escaped = next_line.count("\\'") if quote_type == "'" else next_line.count('\\"')
                next_count = next_line.count(quote_type) - escaped
                total_count += next_count
                merged_line += ' ' + next_line.strip()
                if total_count % 2 == 0:
                    break
                j += 1
            
            fixed_lines.append(merged_line)
            i = j + 1
            continue
        
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines)

def fix_multiline_sql(content: str) -> str:
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        sql_match = re.search(r"cursor\.execute\(['\"]", line)
        if sql_match:
            quote_char = line[sql_match.end() - 1]
            line_stripped = line.strip()
            
            if line_stripped.count(quote_char) == 1 and line_stripped.endswith(','):
                j = i + 1
                merged_lines = [line]
                
                while j < len(lines):
                    next_line = lines[j]
                    merged_lines.append(next_line)
                    
                    if quote_char in next_line:
                        break
                    j += 1
                
                if j < len(lines):
                    joined = ' '.join([l.strip() for l in merged_lines])
                    fixed_lines.append(joined)
                    i = j + 1
                    continue
        
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines)

def fix_file(file_path: str) -> Dict[str, Any]:
    repair_id = generate_id('fix')
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            before_content = f.read()
        
        errors = detect_syntax_errors(file_path)
        
        if not errors:
            return {'repair_id': repair_id, 'file_path': file_path, 'status': 'no_errors', 'errors_fixed': 0}
        
        after_content = before_content
        
        for error in errors:
            if 'EOL' in error['error_message']:
                after_content = fix_eol_string(after_content)
                after_content = fix_multiline_sql(after_content)
        
        try:
            ast.parse(after_content)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(after_content)
            
            report_to_db(repair_id, file_path, errors, before_content, after_content, 'success')
            
            return {
                'repair_id': repair_id,
                'file_path': file_path,
                'status': 'success',
                'errors_found': len(errors),
                'errors_fixed': len(errors)
            }
        except SyntaxError as e:
            report_to_db(repair_id, file_path, errors, before_content, after_content, 'failed', str(e))
            
            return {
                'repair_id': repair_id,
                'file_path': file_path,
                'status': 'failed',
                'errors_found': len(errors),
                'errors_fixed': 0,
                'message': str(e)
            }
    except Exception as e:
        return {
            'repair_id': repair_id,
            'file_path': file_path,
            'status': 'error',
            'errors_found': 0,
            'errors_fixed': 0,
            'message': str(e)
        }

def report_to_db(repair_id: str, file_path: str, errors: List[Dict],
                 before_content: str, after_content: str, status: str,
                 error_msg: str = ''):
    try:
        with get_db() as conn:
            conn.execute('''
                INSERT INTO syntax_repair_logs (
                    repair_id, file_path, error_type, error_message,
                    error_line, before_content, after_content,
                    fix_status, repair_time, applied_by, verified
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                repair_id, file_path,
                ','.join(e['error_type'] for e in errors) if errors else 'none',
                ','.join(e['error_message'] for e in errors) if errors else error_msg,
                errors[0]['error_line'] if errors else 0,
                before_content[:500],
                after_content[:500],
                status,
                int(time.time()),
                'syntax_fix_agent',
                1 if status == 'success' else 0
            ))
            
            for error in errors:
                error_id = generate_id('err')
                conn.execute('''
                    INSERT OR REPLACE INTO syntax_errors (
                        error_id, file_path, error_type, error_message,
                        error_line, detected_at, status, fixed_by, fixed_at, repair_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    error_id, file_path, error['error_type'], error['error_message'],
                    error['error_line'], int(time.time()),
                    'fixed' if status == 'success' else 'unfixed',
                    'syntax_fix_agent',
                    int(time.time()) if status == 'success' else None,
                    repair_id
                ))
            
            conn.commit()
    except Exception as e:
        print(f"[ERROR] 上报数据库失败: {e}")

def scan_and_fix(directory: str = PROJECT_ROOT):
    init_tables()
    
    error_files = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules', 'venv', '.venv', 'data']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                errors = detect_syntax_errors(file_path)
                if errors:
                    error_files.append((file_path, errors))
    
    print(f"[INFO] 共发现 {len(error_files)} 个有语法错误的文件")
    print(f"[INFO] 开始批量修复...")
    
    results = []
    success_count = 0
    fail_count = 0
    
    for file_path, errors in error_files:
        print(f"[INFO] 修复: {file_path}")
        result = fix_file(file_path)
        results.append(result)
        
        if result['status'] == 'success':
            success_count += 1
            print(f"[SUCCESS] 修复成功: {result['errors_fixed']}个错误")
        else:
            fail_count += 1
            print(f"[FAILED] 修复失败: {result.get('message', '未知错误')}")
    
    print(f"\n[INFO] 修复完成")
    print(f"[INFO] 成功: {success_count}")
    print(f"[INFO] 失败: {fail_count}")
    
    return results

if __name__ == '__main__':
    scan_and_fix()