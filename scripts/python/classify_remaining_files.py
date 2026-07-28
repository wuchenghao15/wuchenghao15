#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('mtscos.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('SELECT file_path FROM syntax_repair_logs WHERE fix_status = "failed"')
failed_files = [row['file_path'] for row in cursor.fetchall()]

backup_files = []
real_files = []

for file_path in failed_files:
    if 'flask-app-old/backups/' in file_path:
        backup_files.append(file_path)
    elif 'flask-app-old/' in file_path:
        backup_files.append(file_path)
    else:
        real_files.append(file_path)

print(f'总失败文件数: {len(failed_files)}')
print(f'备份文件数 (flask-app-old/): {len(backup_files)}')
print(f'实际源文件数: {len(real_files)}')

print('\n备份文件列表:')
for fp in backup_files:
    print(f'  {fp}')

print('\n实际源文件列表:')
for fp in real_files:
    print(f'  {fp}')

conn.close()

print(f'\n{"="*80}')
print(f'建议:')
print(f'1. 将 {len(backup_files)} 个备份文件标记为 "skipped"')
print(f'2. 针对 {len(real_files)} 个实际源文件开发智能修复器')
