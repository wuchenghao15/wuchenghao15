#!/usr/bin/env python3
import os
import ast
import sqlite3

conn = sqlite3.connect('mtscos.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('SELECT file_path FROM syntax_repair_logs WHERE fix_status = "failed"')
failed_files = [row['file_path'] for row in cursor.fetchall()]

conn.close()

print(f'待诊断文件: {len(failed_files)}')
print('=' * 120)

error_patterns = {}

for file_path in failed_files:
    if not os.path.exists(file_path):
        continue
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        try:
            ast.parse(content)
            print(f'✅ {os.path.basename(file_path)} - 语法正确')
            continue
        except SyntaxError as e:
            line_num = e.lineno
            error_msg = str(e)
            
            if line_num <= len(lines):
                error_line = lines[line_num - 1]
                indent = len(error_line) - len(error_line.lstrip())
                stripped = error_line.strip()
                
                context_start = max(0, line_num - 3)
                context_end = min(len(lines), line_num + 3)
                
                print(f'\n❌ {os.path.basename(file_path)}')
                print(f'   错误行: {line_num}')
                print(f'   错误信息: {error_msg}')
                print(f'   错误内容: {repr(stripped)}')
                print(f'   缩进: {indent}')
                
                if context_start < line_num - 1:
                    print(f'   上下文:')
                    for i in range(context_start, line_num):
                        prefix = '   ' if i != line_num - 1 else '>>> '
                        print(f'{prefix}行{i+1}: {repr(lines[i].strip())}')
                
                if stripped not in error_patterns:
                    error_patterns[stripped] = []
                error_patterns[stripped].append(os.path.basename(file_path))
    
    except Exception as e:
        print(f'\n❌ {os.path.basename(file_path)} - 读取失败: {e}')

print('\n' + '=' * 120)
print(f'错误模式统计 ({len(error_patterns)}种):')
print('=' * 120)

for pattern, files in sorted(error_patterns.items(), key=lambda x: len(x[1]), reverse=True):
    print(f'\n模式: {repr(pattern)}')
    print(f'出现次数: {len(files)}')
    print(f'涉及文件: {", ".join(files[:5])}{"..." if len(files) > 5 else ""}')
