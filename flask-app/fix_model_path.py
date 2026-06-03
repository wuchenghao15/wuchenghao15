# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
修复MODEL_PATH环境变量的脚本
在导入AI模块之前设置MODEL_PATH环境变量,避免KeyError

import logging
logger = logging.getLogger(__name__)
import os
import sys

# 首先设置MODEL_PATH环境变量
print("设置MODEL_PATH环境变量...")
os.environ['MODEL_PATH'] = './models'
print(f"MODEL_PATH已设置为: {os.environ['MODEL_PATH']}")

# 然后修改sys.path,确保能找到app模块
print("修改sys.path...")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
print(f"sys.path: {sys.path[:3]}")

# 现在尝试导入app模块
print("尝试导入app模块...")
try:
    # 先导入config模块,确保配置正确
    from app.config import Config
    print("Config模块导入成功")

    # 检查Config类是否有MODEL_PATH属性
    if hasattr(Config, 'MODEL_PATH'):
        print(f"Config.MODEL_PATH: {Config.MODEL_PATH}")
    else:
        print("Config类没有MODEL_PATH属性,添加它...")
        Config.MODEL_PATH = './models'
        print(f"Config.MODEL_PATH已添加: {Config.MODEL_PATH}")

    # 现在尝试导入app模块
    print("修复完成,可以正常启动服务器了.")
except Exception as e:
    print(f"导入app模块时出错: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

"""