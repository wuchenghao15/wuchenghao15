#!/usr/bin/env python3
import os
import ast
import sqlite3

conn = sqlite3.connect('mtscos.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('SELECT file_path FROM syntax_repair_logs WHERE fix_status = "failed"')
failed_files = [row['file_path'] for row in cursor.fetchall()]

print(f'待处理失败文件: {len(failed_files)}')

fixed_count = 0
still_failed = []

for file_path in failed_files:
    if not os.path.exists(file_path):
        print(f'❌ 文件不存在: {file_path}')
        still_failed.append((file_path, '文件不存在'))
        continue
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
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
            
            conn.commit()
            
            fixed_count += 1
            print(f'✅ 已修复: {file_path}')
            
        except SyntaxError as e:
            still_failed.append((file_path, str(e)))
            print(f'❌ {file_path} - {e}')
            
    except Exception as e:
        still_failed.append((file_path, str(e)))
        print(f'❌ 读取失败: {file_path} - {e}')

conn.commit()
conn.close()

print(f'\n{"="*80}')
print(f'修复结果:')
print(f'  已修复: {fixed_count}')
print(f'  仍失败: {len(still_failed)}')
