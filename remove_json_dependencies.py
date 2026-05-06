#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化移除项目中的JSON依赖，改用数据库存储
"""

import os
import re
import sys

# 需要处理的文件列表
target_files = [
    'ai_auto_generator.py',
    'ai_capability_enhancement.py',
    'api_integrator.py',
    'middleware_integrator.py',
    'sandbox_system.py',
    'session_cookie_manager.py',
    'system_integrator.py'
]

def process_file(filepath):
    """处理单个文件"""
    if not os.path.exists(filepath):
        print(f"警告: 文件不存在 {filepath}")
        return
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. 移除或替换 # import json removed - using database storage
    content = content.replace('# import json removed - using database storage\n', '# JSON support removed - using database\n')
    
    # 2. 替换 json.dumps 为 str()
    content = re.sub(r'json\.dumps\(([^)]+)\)', r'str(\1)', content)
    
    # 3. 替换 json.loads 为 eval() 或保持原样
    # 对于数据库读取，我们保持简单的字符串存储
    content = re.sub(r'json\.loads\(([^)]+)\)', r'\1', content)
    
    # 4. 添加存储管理器导入
    if 'from data_storage_manager' not in content:
        # 在文件开头添加导入（在其他导入之后）
        import_section = r'(import sys\s*)'
        content = re.sub(import_section, r'\1\n# 添加数据存储管理器导入\nsys.path.insert(0, os.path.join(os.path.dirname(__file__), \'flask-app/app\'))\nfrom data_storage_manager import storage_manager\n', content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"已处理: {filepath}")

def main():
    """主函数"""
    print("="*60)
    print("  自动化移除JSON依赖脚本")
    print("="*60)
    
    for filename in target_files:
        filepath = os.path.join(os.path.dirname(__file__), filename)
        process_file(filepath)
    
    print("\n" + "="*60)
    print("  JSON依赖移除完成")
    print("="*60)

if __name__ == "__main__":
    main()