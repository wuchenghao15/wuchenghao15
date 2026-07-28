#!/usr/bin/env python3
"""
测试修复单个文件
"""

import re
import ast

file_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/ai_engines/smart_schedule_engine.py'

with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

print(f'第166行: {repr(lines[165])}')
print(f'第167行: {repr(lines[166])}')

line = lines[165].rstrip()
print(f'\n正则匹配测试:')
match = re.search(r'(""".*?""")(.*)$', line)
if match:
    print(f'  匹配成功')
    print(f'  分组1: {repr(match.group(1))}')
    print(f'  分组2: {repr(match.group(2))}')
else:
    print(f'  匹配失败')

match2 = re.search(r'"""(.*?)"""', line)
if match2:
    print(f'  简单匹配: {repr(match2.group(0))}')

fixed_line = re.sub(r'(""".*?""")(.*)$', r'\1\n\2', line)
print(f'\n修复后: {repr(fixed_line)}')
