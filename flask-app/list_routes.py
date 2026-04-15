#!/usr/bin/env python3
"""
列出应用中所有注册的路由
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 禁用dotenv加载
os.environ['FLASK_SKIP_DOTENV'] = '1'

# 创建一个简单的Flask应用，只用于测试
from flask import Flask

# 创建Flask应用实例
test_app = Flask(__name__)

# 导入app，触发路由注册
with test_app.app_context():
    try:
        # 导入主应用
        from app import app
        
        # 打印所有路由
        print("应用中注册的路由:")
        for rule in app.url_map.iter_rules():
            print(f"  {rule}")
    except Exception as e:
        print(f"导入应用时出错: {str(e)}")
        import traceback
        traceback.print_exc()
