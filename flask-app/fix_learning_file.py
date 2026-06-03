# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# 直接修改learning.py文件,修复MODEL_PATH KeyError问题
import logging
logger = logging.getLogger(__name__)
import os
import re

file_path = os.path.join(os.path.dirname(__file__), 'app', 'ai', 'learning.py')

print(f"正在修复文件: {file_path}")

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    print("文件读取成功")
except Exception as e:
    print(f"文件读取失败: {e}")
    exit(1)

pattern = r"\['MODEL_PATH'\]"
replacement = "['MODEL_PATH'] if 'MODEL_PATH' in config else 'models/'"

if re.search(pattern, content):
    modified_content = re.sub(pattern, replacement, content)
    print("找到并替换了MODEL_PATH访问模式")
else:
    lines = content.split('\n')
    if len(lines) >= 16:
        print("文件至少有16行,正在检查第16行")
        print(f"第15行: {lines[14] if 14 < len(lines) else '无'}")
        print(f"第16行: {lines[15] if 15 < len(lines) else '无'}")
        print(f"第17行: {lines[16] if 16 < len(lines) else '无'}")
        
        lines[15] = lines[15].replace("config['MODEL_PATH']", "config.get('MODEL_PATH', 'models/')")
        modified_content = '\n'.join(lines)
        print("已修改第16行,添加了get()方法")
    else:
        print("文件行数不足16行,无法确定修改位置")
        modified_content = content

try:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(modified_content)
    print("文件修改成功")
except Exception as e:
    print(f"文件写入失败: {e}")
    exit(1)
