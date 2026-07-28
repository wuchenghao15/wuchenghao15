#!/usr/bin/env python3
import os
import ast
import sqlite3

conn = sqlite3.connect('mtscos.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('SELECT file_path FROM syntax_repair_logs WHERE fix_status = "failed"')
failed_files = [row['file_path'] for row in cursor.fetchall()]

fixed_count = 0

for file_path in failed_files:
    if not os.path.exists(file_path):
        continue
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        ast.parse(content)
        
        cursor.execute('''
            UPDATE syntax_repair_logs SET 
                after_content = ?, 
                fix_status = "success",
                verified = 1
            WHERE file_path = ? AND fix_status = "failed"
        ''', (content, file_path))
        
        cursor.execute('''
            UPDATE syntax_errors SET status = "fixed" 
            WHERE file_path = ? AND status = "error"
        ''', (file_path,))
        
        fixed_count += 1
        print(f'✅ 已修复: {os.path.basename(file_path)}')
    except SyntaxError:
        print(f'❌ 仍有错误: {os.path.basename(file_path)}')

conn.commit()
conn.close()

print(f'\n成功修复: {fixed_count}')
