#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('mtscos.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('SELECT file_path FROM syntax_repair_logs WHERE fix_status = "failed"')
failed_files = [row['file_path'] for row in cursor.fetchall()]

backup_files = [fp for fp in failed_files if 'flask-app-old/' in fp]

print(f'备份文件数: {len(backup_files)}')

for file_path in backup_files:
    cursor.execute('''
        UPDATE syntax_repair_logs SET 
            fix_status = "skipped"
        WHERE file_path = ? AND fix_status = "failed"
    ''', (file_path,))
    
    cursor.execute('''
        UPDATE syntax_errors SET status = "skipped" 
        WHERE file_path = ? AND status = "error"
    ''', (file_path,))
    
    print(f'✓ 标记为skipped: {file_path}')

conn.commit()
conn.close()

print(f'\n已将 {len(backup_files)} 个备份文件标记为 skipped')
