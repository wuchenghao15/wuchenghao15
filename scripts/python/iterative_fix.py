#!/usr/bin/env python3
"""
迭代式语法错误修复脚本
多次迭代直到文件语法正确或不再有变化
"""

import os
import sys
import re
import ast
import sqlite3
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

AI_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'split_databases', 'ai.db')
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def apply_fixes(content):
    """应用修复规则"""
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        if '"""' in line:
            idx = line.find('"""')
            if idx != -1:
                end_idx = line.find('"""', idx + 3)
                if end_idx != -1:
                    after_docstring = line[end_idx + 3:].strip()
                    if after_docstring:
                        fixed_lines.append(line[:end_idx + 3])
                        fixed_lines.append(after_docstring)
                        continue
        
        if "'''" in line:
            idx = line.find("'''")
            if idx != -1:
                end_idx = line.find("'''", idx + 3)
                if end_idx != -1:
                    after_docstring = line[end_idx + 3:].strip()
                    if after_docstring:
                        fixed_lines.append(line[:end_idx + 3])
                        fixed_lines.append(after_docstring)
                        continue
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def fix_file(file_path):
    """修复单个文件"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        try:
            ast.parse(content)
            return {'success': True, 'message': '无需修复', 'iterations': 0}
        except SyntaxError:
            pass
        
        iterations = 0
        max_iterations = 10
        last_content = content
        
        while iterations < max_iterations:
            content = apply_fixes(content)
            
            try:
                ast.parse(content)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return {'success': True, 'message': f'{iterations+1}次迭代后修复成功', 'iterations': iterations + 1}
            except SyntaxError:
                pass
            
            if content == last_content:
                break
            
            last_content = content
            iterations += 1
        
        return {'success': False, 'message': f'{iterations}次迭代后仍有错误', 'iterations': iterations}
    
    except Exception as e:
        return {'success': False, 'message': f'处理失败: {e}', 'iterations': 0}

def main():
    print('=' * 70)
    print('  MTSCOS项目语法错误迭代修复')
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
            print(f'   ✓ [{i+1}] {os.path.basename(file_path)} ({result["iterations"]}次)')
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
        CREATE TABLE IF NOT EXISTS iterative_fix_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_files INTEGER,
            success_count INTEGER,
            fail_count INTEGER,
            remaining_errors INTEGER,
            fixed_at TEXT
        )
    ''')
    
    cursor.execute('''
        INSERT INTO iterative_fix_logs (total_files, success_count, fail_count, remaining_errors, fixed_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (len(files_with_errors), success_count, fail_count, remaining, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    main()
