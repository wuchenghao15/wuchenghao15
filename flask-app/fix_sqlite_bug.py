#!/usr/bin/env python3
"""批量修复 sqlite3.connect(...) 嵌套错误"""
import os
import re

files = [
    'app/utils/system_monitor.py',
    'app/routes/settings_routes.py',
    'app/services/learning_group_service.py'
]

base_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app'

fixed_count = 0
for f in files:
    full_path = os.path.join(base_path, f)
    if not os.path.exists(full_path):
        print(f"❌ 文件不存在: {f}")
        continue

    with open(full_path, 'r') as file:
        content = file.read()

    # 修复 sqlite3.connect(...) 模式
    # 模式: sqlite3.connect(X)
    # 替换为: sqlite3.connect(X)
    pattern = r'sqlite3\.connect\(\s*sqlite3\.connect\(\s*([^)]+?)\s*\)\s*\)'
    new_content, n = re.subn(pattern, r'sqlite3.connect(\1)', content)

    if n > 0:
        with open(full_path, 'w') as file:
            file.write(new_content)
        print(f"✅ {f}: 修复了 {n} 处")
        fixed_count += n
    else:
        print(f"⏭️  {f}: 无需修复")

print(f"\n总计修复: {fixed_count} 处")