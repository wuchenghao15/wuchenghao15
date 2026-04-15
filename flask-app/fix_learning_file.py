#!/usr/bin/env python3
# 直接修改learning.py文件，修复MODEL_PATH KeyError问题
import os
import re

# 获取learning.py文件的完整路径
file_path = os.path.join(os.path.dirname(__file__), 'app', 'ai', 'learning.py')

print(f"正在修复文件: {file_path}")

# 读取文件内容
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    print("文件读取成功")
except Exception as e:
    print(f"文件读取失败: {e}")
    exit(1)

# 使用正则表达式查找并替换第16行附近的代码
# 查找模式：任何包含'MODEL_PATH'的字典访问，如 config['MODEL_PATH'] 或类似形式
pattern = r"\['MODEL_PATH'\]"
replacement = "['MODEL_PATH'] if 'MODEL_PATH' in config else 'models/'"

# 检查是否包含目标模式
if re.search(pattern, content):
    modified_content = re.sub(pattern, replacement, content)
    print("找到并替换了MODEL_PATH访问模式")
else:
    # 尝试另一种模式：直接查找第16行附近的代码
    lines = content.split('\n')
    if len(lines) >= 16:
        # 获取第16行及其前后几行
        print("文件至少有16行，正在检查第16行")
        print(f"第15行: {lines[14] if 14 < len(lines) else '无'}")
        print(f"第16行: {lines[15] if 15 < len(lines) else '无'}")
        print(f"第17行: {lines[16] if 16 < len(lines) else '无'}")
        
        # 直接修改第16行，添加安全访问
        # 假设第16行是类似 self.model_path = config['MODEL_PATH'] 的代码
        lines[15] = lines[15].replace("config['MODEL_PATH']", "config.get('MODEL_PATH', 'models/')")
        modified_content = '\n'.join(lines)
        print("已修改第16行，添加了get()方法")
    else:
        print("文件行数不足16行，无法确定修改位置")
        exit(1)

# 写入修改后的内容
try:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(modified_content)
    print("文件修改成功")
except Exception as e:
    print(f"文件修改失败: {e}")
    exit(1)

print("修复完成！")
