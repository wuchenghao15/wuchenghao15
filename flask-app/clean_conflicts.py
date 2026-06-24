#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理HTML文件中的Git合并冲突标记
"""

import re

def clean_merge_conflicts(file_path):
    """清理文件中的合并冲突标记"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找所有冲突标记
    conflict_pattern = r'<<<<<<< Updated upstream.*?=======.*?>>>>>>> Stashed changes'
    
    # 替换冲突部分为第一个版本（保留 Updated upstream 部分）
    cleaned = re.sub(conflict_pattern, '', content, flags=re.DOTALL)
    
    # 清理孤立的标记
    cleaned = re.sub(r'<<<<<<< Updated upstream\n?', '', cleaned)
    cleaned = re.sub(r'=======\n?', '', cleaned)
    cleaned = re.sub(r'>>>>>>> Stashed changes\n?', '', cleaned)
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(cleaned)
    
    print(f"✅ 已清理文件: {file_path}")

if __name__ == '__main__':
    file_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app/templates/index.html'
    clean_merge_conflicts(file_path)
