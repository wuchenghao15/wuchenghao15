#!/usr/bin/env python3
"""
测试修复单个文件
"""

import re
import ast

file_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/ai_engines/smart_schedule_engine.py'

with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

try:
    ast.parse(content)
    print('文件语法正确')
except SyntaxError as e:
    print(f'语法错误: {e}')

lines = content.split('\n')
for i, line in enumerate(lines):
    if '"""' in line:
        match = re.search(r'(""".*?""")(.*)$', line)
        if match:
            print(f'第{i+1}行: 找到合并行')
            print(f'  原文: {repr(line)}')
            print(f'  分组1: {repr(match.group(1))}')
            print(f'  分组2: {repr(match.group(2))}')
            break
