#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
超简单启动脚本，直接使用app实例，固定端口8888
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Starting ultra simple Flask app...")
print(f"Current directory: {os.getcwd()}")

# 导入app实例
print("Importing app module...")
from app import app
print("App module imported successfully.")

# 打印app实例的信息
print(f"App instance: {app}")
print(f"App config: {app.config}")

# 显式设置端口为8888
PORT = 8888

print(f"About to run app on port {PORT}...")
try:
    app.run(host='0.0.0.0', port=PORT, debug=True)
except KeyboardInterrupt:
    print("App stopped by KeyboardInterrupt.")
except Exception as e:
    print(f"Error running app: {e}")
    import traceback
    traceback.print_exc()
