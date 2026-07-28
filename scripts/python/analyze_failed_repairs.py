#!/usr/bin/env python3
import sqlite3
from collections import Counter

conn = sqlite3.connect('mtscos.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('SELECT file_path, error_message, error_type FROM syntax_repair_logs WHERE fix_status = "failed"')
failed_records = cursor.fetchall()

print(f'失败修复文件总数: {len(failed_records)}')
print('=' * 80)

error_types = Counter()
file_paths = []

for record in failed_records:
    file_path = record['file_path']
    error_msg = record['error_message']
    error_type = record['error_type']
    
    file_paths.append(file_path)
    
    if 'EOL' in error_msg or 'unexpected EOF' in error_msg:
        error_types['EOL字符串截断'] += 1
    elif 'indentation' in error_msg.lower() or 'unindent' in error_msg.lower():
        error_types['缩进错误'] += 1
    elif 'invalid syntax' in error_msg.lower():
        error_types['无效语法'] += 1
    elif 'expected' in error_msg.lower() and ':' in error_msg:
        error_types['缺少冒号'] += 1
    elif 'unexpected' in error_msg.lower():
        error_types['意外符号'] += 1
    elif error_type:
        error_types[error_type] += 1
    else:
        error_types['其他错误'] += 1

print('\n错误类型分布:')
for error_type, count in error_types.most_common():
    print(f'  {error_type}: {count}')

print('\n失败文件列表:')
for i, record in enumerate(failed_records[:50], 1):
    print(f'  {i}. {record["file_path"]}')
    print(f'     错误: {record["error_message"][:120]}')

if len(failed_records) > 50:
    print(f'  ... 还有 {len(failed_records) - 50} 个文件')

conn.close()
