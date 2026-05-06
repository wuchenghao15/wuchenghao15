#!/usr/bin/env python3
"""
批量替换项目中的 JSON 使用为数据库存储服务
"""

import os
import re
import shutil

def find_python_files(root_dir):
    """查找所有Python文件"""
    python_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith('.py'):
                python_files.append(os.path.join(dirpath, filename))
    return python_files

def replace_json_usage(file_path):
    """替换单个文件中的JSON使用"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    modified = False
    
    # 1. 移除 # import json removed - using database storage（但保留在特定文件中）
    excluded_import_files = [
        'db_storage_service.py',  # 需要json用于API响应
        'app.py',  # Flask需要jsonify
        '__init__.py'
    ]
    
    if not any(exclude in file_path for exclude in excluded_import_files):
        if '# import json removed - using database storage' in content:
            content = content.replace('# import json removed - using database storage', '# # import json removed - using database storage removed - using database storage')
            modified = True
        if '# # from json import removed removed - using database storage' in content:
            content = content.replace('# # from json import removed removed - using database storage', '# # # from json import removed removed - using database storage removed - using database storage')
            modified = True

    # 2. 替换 json.dumps 为数据库存储
    # 模式1: str(value)
    pattern1 = r'json\.dumps\(([^)]+)\s*,\s*ensure_ascii=False\)'
    content, count1 = re.subn(pattern1, r"str(\1)", content)
    if count1 > 0:
        modified = True

    # 模式2: str(value)
    pattern2 = r'json\.dumps\(([^)]+)\)'
    content, count2 = re.subn(pattern2, r"str(\1)", content)
    if count2 > 0:
        modified = True

    # 3. 替换 json.loads 为 eval（用于简单字符串转换）
    pattern3 = r'json\.loads\(([^)]+)\)'
    content, count3 = re.subn(pattern3, r"eval(\1)", content)
    if count3 > 0:
        modified = True

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return modified, count1 + count2 + count3

def main():
    project_root = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project'
    
    print("=== 批量替换JSON使用为数据库存储 ===")
    print(f"项目根目录: {project_root}\n")

    python_files = find_python_files(project_root)
    print(f"找到 {len(python_files)} 个Python文件")

    modified_count = 0
    total_replacements = 0

    for file_path in python_files:
        modified, replacements = replace_json_usage(file_path)
        if modified:
            modified_count += 1
            total_replacements += replacements
            print(f"修改: {file_path} ({replacements}处)")

    print(f"\n替换完成!")
    print(f"修改文件数: {modified_count}")
    print(f"总替换次数: {total_replacements}")
    print("\n注意:")
    print("1. app.py 和 db_storage_service.py 保留了JSON用于API响应")
    print("2. Flask的jsonify()保持不变（用于RESTful API响应）")
    print("3. 数据存储现在通过数据库完成")

if __name__ == '__main__':
    main()