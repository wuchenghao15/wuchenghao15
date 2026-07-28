#!/usr/bin/env python3
import ast
import os
import re
import sqlite3
import time
from typing import Dict, List, Any

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mtscos.db')
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def fix_trailing_comma(content: str) -> str:
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.endswith(',') and not stripped.startswith('#'):
            prev_line = lines[i-1].strip() if i > 0 else ''
            if prev_line and not prev_line.startswith('#'):
                if prev_line.endswith('(') or prev_line.endswith('[') or prev_line.endswith('{'):
                    pass
                elif prev_line.endswith(','):
                    pass
                elif i + 1 < len(lines):
                    next_line = lines[i+1].strip()
                    if next_line and not next_line.startswith('#'):
                        if not next_line.startswith(')') and not next_line.startswith(']') and not next_line.startswith('}'):
                            line = line.rstrip(',') + line[len(line.rstrip(',')):]
                            if line.endswith(','):
                                line = line[:-1]
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def fix_line_breaks(content: str) -> str:
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        if stripped.endswith(',') and not stripped.startswith('#'):
            prev_line = lines[i-1].strip() if i > 0 else ''
            
            if prev_line and not prev_line.startswith('#'):
                if prev_line.endswith('(') or prev_line.endswith('[') or prev_line.endswith('{'):
                    j = i + 1
                    merged = [line]
                    
                    while j < len(lines):
                        next_line = lines[j].strip()
                        if not next_line or next_line.startswith('#'):
                            break
                        if next_line.startswith(')') or next_line.startswith(']') or next_line.startswith('}'):
                            break
                        merged.append(lines[j])
                        j += 1
                    
                    if j < len(lines):
                        joined = ' '.join([l.strip() for l in merged])
                        fixed_lines.append(joined)
                        i = j
                        continue
        
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines)

def fix_variable_break(content: str) -> str:
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        if stripped.endswith('+') or stripped.endswith('=') or stripped.endswith('*') or stripped.endswith('/'):
            if i + 1 < len(lines):
                j = i + 1
                merged = [line]
                
                while j < len(lines):
                    next_line = lines[j].strip()
                    if not next_line or next_line.startswith('#'):
                        break
                    if next_line.endswith('+') or next_line.endswith('=') or next_line.endswith('*') or next_line.endswith('/'):
                        merged.append(lines[j])
                        j += 1
                    else:
                        merged.append(lines[j])
                        break
                
                joined = ' '.join([l.strip() for l in merged])
                fixed_lines.append(joined)
                i = j + 1
                continue
        
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines)

def fix_import_break(content: str) -> str:
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        if stripped.startswith('from ') and stripped.endswith(','):
            j = i + 1
            merged = [line]
            
            while j < len(lines):
                next_line = lines[j].strip()
                if not next_line or next_line.startswith('#'):
                    break
                if not next_line.startswith('from ') and not next_line.startswith('import '):
                    merged.append(lines[j])
                else:
                    break
                j += 1
            
            joined = ' '.join([l.strip() for l in merged])
            fixed_lines.append(joined)
            i = j
            continue
        
        if stripped.startswith('import ') and stripped.endswith(','):
            j = i + 1
            merged = [line]
            
            while j < len(lines):
                next_line = lines[j].strip()
                if not next_line or next_line.startswith('#'):
                    break
                if not next_line.startswith('import ') and not next_line.startswith('from '):
                    merged.append(lines[j])
                else:
                    break
                j += 1
            
            joined = ' '.join([l.strip() for l in merged])
            fixed_lines.append(joined)
            i = j
            continue
        
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines)

def fix_comment_break(content: str) -> str:
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        if '# ' in stripped and stripped.count('"') % 2 != 0:
            j = i + 1
            merged = [line]
            
            while j < len(lines):
                next_line = lines[j].strip()
                if not next_line or not next_line.startswith('#'):
                    break
                merged.append(lines[j])
                if next_line.count('"') % 2 != 0:
                    break
                j += 1
            
            joined = ' '.join([l.strip() for l in merged])
            fixed_lines.append(joined)
            i = j + 1
            continue
        
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines)

def fix_file_enhanced(file_path: str) -> Dict[str, Any]:
    repair_id = f"fix_{int(time.time())}_{hash(str(time.time())) % 100000:05d}"
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            before_content = f.read()
        
        try:
            ast.parse(before_content)
            return {'repair_id': repair_id, 'file_path': file_path, 'status': 'no_errors', 'errors_fixed': 0}
        except SyntaxError as e:
            pass
        
        after_content = before_content
        
        error_messages = ['EOL', 'invalid syntax', 'unexpected indent', 'trailing comma', 'unmatched']
        
        for _ in range(3):
            try:
                ast.parse(after_content)
                break
            except SyntaxError:
                after_content = fix_line_breaks(after_content)
                after_content = fix_variable_break(after_content)
                after_content = fix_import_break(after_content)
                after_content = fix_comment_break(after_content)
                after_content = fix_trailing_comma(after_content)
        
        try:
            ast.parse(after_content)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(after_content)
            
            with get_db() as conn:
                conn.execute('''
                    INSERT INTO syntax_repair_logs (
                        repair_id, file_path, error_type, error_message,
                        error_line, before_content, after_content,
                        fix_status, repair_time, applied_by, verified
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    repair_id, file_path, 'enhanced_fix', 'Enhanced fix',
                    0, before_content[:500], after_content[:500],
                    'success', int(time.time()), 'enhanced_syntax_fix', 1
                ))
                conn.commit()
            
            return {
                'repair_id': repair_id,
                'file_path': file_path,
                'status': 'success',
                'errors_fixed': 1
            }
        except SyntaxError as e:
            return {
                'repair_id': repair_id,
                'file_path': file_path,
                'status': 'failed',
                'errors_fixed': 0,
                'message': str(e)
            }
    except Exception as e:
        return {
            'repair_id': repair_id,
            'file_path': file_path,
            'status': 'error',
            'errors_fixed': 0,
            'message': str(e)
        }

def scan_and_fix_failed():
    failed_files = []
    
    for root, dirs, files in os.walk(PROJECT_ROOT):
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules', 'venv', '.venv', 'data']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    ast.parse(content)
                except SyntaxError:
                    failed_files.append(file_path)
    
    print(f"[INFO] 发现 {len(failed_files)} 个仍有语法错误的文件")
    
    success_count = 0
    fail_count = 0
    
    for file_path in failed_files:
        print(f"[INFO] 修复: {file_path}")
        result = fix_file_enhanced(file_path)
        
        if result['status'] == 'success':
            success_count += 1
            print(f"[SUCCESS] 修复成功")
        else:
            fail_count += 1
            print(f"[FAILED] 修复失败: {result.get('message', '未知错误')}")
    
    print(f"\n[INFO] 增强修复完成")
    print(f"[INFO] 成功: {success_count}")
    print(f"[INFO] 失败: {fail_count}")

if __name__ == '__main__':
    scan_and_fix_failed()