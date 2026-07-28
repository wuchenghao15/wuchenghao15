#!/usr/bin/env python3
import sqlite3
from collections import Counter

conn = sqlite3.connect('mtscos.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('SELECT file_path, error_message FROM syntax_repair_logs WHERE fix_status = "failed"')
failed_records = cursor.fetchall()

print(f'总失败文件数: {len(failed_records)}')

snapshot_files = []
real_files = []

for record in failed_records:
    file_path = record['file_path']
    if 'data/snapshots/' in file_path:
        snapshot_files.append(file_path)
    else:
        real_files.append(record)

print(f'\n备份文件数 (data/snapshots/): {len(snapshot_files)}')
print(f'实际文件数: {len(real_files)}')

if snapshot_files:
    print('\n备份文件列表:')
    for fp in snapshot_files[:10]:
        print(f'  {fp}')
    if len(snapshot_files) > 10:
        print(f'  ... 还有 {len(snapshot_files) - 10} 个')

print('\n实际文件错误类型分布:')
error_types = Counter()
error_details = {}

for record in real_files:
    error_msg = record['error_message']
    
    if 'EOL' in error_msg or 'unexpected EOF' in error_msg:
        error_types['EOL字符串截断'] += 1
        error_details.setdefault('EOL字符串截断', []).append(record)
    elif 'indentation' in error_msg.lower() or 'unindent' in error_msg.lower():
        error_types['缩进错误'] += 1
        error_details.setdefault('缩进错误', []).append(record)
    elif 'invalid syntax' in error_msg.lower():
        error_types['无效语法'] += 1
        error_details.setdefault('无效语法', []).append(record)
    elif 'expected' in error_msg.lower():
        error_types['缺少符号'] += 1
        error_details.setdefault('缺少符号', []).append(record)
    elif 'unexpected' in error_msg.lower():
        error_types['意外符号'] += 1
        error_details.setdefault('意外符号', []).append(record)
    else:
        error_types['其他错误'] += 1
        error_details.setdefault('其他错误', []).append(record)

for error_type, count in error_types.most_common():
    print(f'  {error_type}: {count}')

print('\n各类型错误示例:')
for error_type, records in error_details.items():
    print(f'\n  {error_type}:')
    for record in records[:3]:
        print(f'    - {record["file_path"].split("/")[-1]}: {record["error_message"][:60]}')

conn.close()

print(f'\n{"="*80}')
print(f'建议:')
print(f'1. 跳过 {len(snapshot_files)} 个备份文件')
print(f'2. 针对 {len(real_files)} 个实际文件编写针对性修复器')
print(f'3. 优先处理: {error_types.most_common(3)[0][0]} ({error_types.most_common(3)[0][1]}个)')
