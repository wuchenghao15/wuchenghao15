#!/usr/bin/env python3
"""
直接修复语法错误
使用简单的状态机来处理字符串
"""

import os
import sys
import ast
import sqlite3
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

AI_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'split_databases', 'ai.db')
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def fix_file(file_path):
    """修复单个文件"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        try:
            ast.parse(content)
            return {'success': True, 'message': '无需修复', 'fixed': 0}
        except SyntaxError:
            pass
        
        lines = content.split('\n')
        fixed_lines = []
        i = 0
        fixed_count = 0
        
        while i < len(lines):
            line = lines[i]
            
            double_fstring = 'f"' in line
            single_fstring = "f'" in line
            double_quote = '"' in line and not double_fstring
            single_quote = "'" in line and not single_fstring and not double_fstring
            
            has_quote = double_fstring or single_fstring or double_quote or single_quote
            
            if has_quote:
                if double_fstring:
                    quote = '"'
                elif single_fstring:
                    quote = "'"
                elif double_quote:
                    quote = '"'
                else:
                    quote = "'"
                
                count = line.count(quote)
                if count % 2 != 0:
                    j = i + 1
                    while j < len(lines):
                        line += lines[j].strip()
                        count += lines[j].count(quote)
                        if count % 2 == 0:
                            break
                        j += 1
                    
                    fixed_lines.append(line)
                    i = j + 1
                    fixed_count += 1
                    continue
            
            fixed_lines.append(line)
            i += 1
        
        fixed_content = '\n'.join(fixed_lines)
        
        try:
            ast.parse(fixed_content)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            return {'success': True, 'message': f'修复了{fixed_count}个错误', 'fixed': fixed_count}
        except SyntaxError:
            return {'success': False, 'message': '修复后仍有错误', 'fixed': fixed_count}
    
    except Exception as e:
        return {'success': False, 'message': f'处理失败: {e}', 'fixed': 0}

def main():
    print('=' * 70)
    print('  MTSCOS项目语法错误直接修复')
    print('=' * 70)
    
    files_with_errors = []
    for root, dirs, files in os.walk(PROJECT_ROOT):
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules', 'venv', '.venv', 'split_databases']]
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    try:
                        ast.parse(content)
                    except SyntaxError:
                        files_with_errors.append(file_path)
                except Exception:
                    pass
    
    print(f'   发现 {len(files_with_errors)} 个文件有语法错误')
    
    success_count = 0
    fail_count = 0
    
    for i, file_path in enumerate(files_with_errors):
        result = fix_file(file_path)
        if result['success']:
            success_count += 1
            print(f'   ✓ [{i+1}] {os.path.basename(file_path)}')
        else:
            fail_count += 1
        
        if (i + 1) % 50 == 0:
            print(f'   进度: {i+1}/{len(files_with_errors)}')
    
    print(f'\n   修复成功: {success_count}, 修复失败: {fail_count}')
    
    remaining = 0
    for file_path in files_with_errors:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            try:
                ast.parse(content)
            except SyntaxError:
                remaining += 1
        except Exception:
            remaining += 1
    
    print(f'   修复后仍有错误: {remaining}')
    
    conn = sqlite3.connect(AI_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS direct_fix_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_files INTEGER,
            success_count INTEGER,
            fail_count INTEGER,
            remaining_errors INTEGER,
            fixed_at TEXT
        )
    ''')
    
    cursor.execute('''
        INSERT INTO direct_fix_logs (total_files, success_count, fail_count, remaining_errors, fixed_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (len(files_with_errors), success_count, fail_count, remaining, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    main()
