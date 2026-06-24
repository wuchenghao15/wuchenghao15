#!/usr/bin/env python3
"""批量修复整个项目 sqlite3.connect(...) 嵌套错误"""
import os
import re
import subprocess

base_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app'

# 查找所有 .py 文件
result = subprocess.run(
    ['find', base_path, '-name', '*.py', '-type', 'f'],
    capture_output=True, text=True
)
files = result.stdout.strip().split('\n')

fixed_count = 0
fixed_files = []

pattern = re.compile(r'sqlite3\.connect\(\s*sqlite3\.connect\(\s*([^)]+?)\s*\)\s*\)')

for f in files:
    with open(f, 'r') as file:
        content = file.read()

    new_content, n = pattern.subn(r'sqlite3.connect(\1)', content)

    if n > 0:
        with open(f, 'w') as file:
            file.write(new_content)
        rel_path = os.path.relpath(f, base_path)
        print(f"✅ {rel_path}: 修复了 {n} 处")
        fixed_count += n
        fixed_files.append((rel_path, n))

print(f"\n总计修复: {fixed_count} 处 in {len(fixed_files)} 文件")