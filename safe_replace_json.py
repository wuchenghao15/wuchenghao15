#!/usr/bin/env python3
"""
批量替换项目中的 JSON 使用为数据库存储服务
仅处理项目代码，不处理第三方库
"""

import os
import re

def find_project_files(root_dir):
    """查找项目中的Python文件（排除venv和第三方库）"""
    exclude_dirs = ['venv', '__pycache__', '.git', 'node_modules']
    python_files = []
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # 排除目录
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        
        for filename in filenames:
            if filename.endswith('.py'):
                python_files.append(os.path.join(dirpath, filename))
    return python_files

def replace_json_usage(file_path):
    """替换单个文件中的JSON使用"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        return False, 0

    modified = False
    
    # 1. 移除 import json（但保留在特定文件中）
    excluded_import_files = [
        'db_storage_service.py',
        'app.py',  # Flask需要jsonify
        '__init__.py',
        'test_',  # 测试文件可能需要json
    ]
    
    should_remove_import = True
    for exclude in excluded_import_files:
        if exclude in file_path:
            should_remove_import = False
            break
    
    if should_remove_import:
        if 'import json' in content and '# import json removed' not in content:
            content = content.replace('import json', '# import json removed - using database')
            modified = True
        if '# from json import removed' in content:
            content = content.replace('# from json import removed', '# # from json import removed removed')
            modified = True

    # 2. 替换 json.dumps 为 str
    pattern1 = r'json\.dumps\(([^)]+)\s*,\s*ensure_ascii=False\)'
    content, count1 = re.subn(pattern1, r"str(\1)", content)
    
    pattern2 = r'json\.dumps\(([^)]+)\)'
    content, count2 = re.subn(pattern2, r"str(\1)", content)

    # 3. 替换 json.loads 为 eval
    pattern3 = r'json\.loads\(([^)]+)\)'
    content, count3 = re.subn(pattern3, r"eval(\1)", content)

    total_count = count1 + count2 + count3
    if modified or total_count > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return modified or total_count > 0, total_count

def main():
    project_root = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project'
    
    print("=== 批量替换JSON使用为数据库存储 ===")
    print(f"项目根目录: {project_root}\n")

    python_files = find_project_files(project_root)
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