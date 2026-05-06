#!/usr/bin/env python3
"""
直接修改learning.py文件，修复MODEL_PATH KeyError问题
import os
import fileinput

# 获取learning.py文件的完整路径
file_path = os.path.join(os.path.dirname(__file__), 'app', 'ai', 'learning.py')

print(f"正在修复文件: {file_path}")

# 使用fileinput模块直接修改文件
with fileinput.FileInput(file_path, inplace=True, backup='.bak') as f:
    for line_num, line in enumerate(f, 1):
        # 检查是否是第16行
        if line_num == 16:
            print(f"正在修复第16行: {line.strip()}")
            # 将配置访问改为安全方式
            # 查找所有形式的config['MODEL_PATH']并替换为config.get('MODEL_PATH', 'models/')
            # 查找所有形式的config['MODEL_PATH']并替换为安全访问
            if "['MODEL_PATH']" in line:
                # 处理单引号形式
                line = line.replace("['MODEL_PATH']", ".get('MODEL_PATH', 'models/')")
            elif '["MODEL_PATH"]' in line:
                # 处理双引号形式
                line = line.replace('["MODEL_PATH"]', ".get('MODEL_PATH', 'models/')")
            print(line, end='')
        else:
            print(line, end='')
print("修复完成！")

"""