#!/usr/bin/env python3
"""
简单的URL生成测试脚本
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, url_for

# 创建Flask应用实例
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'

# 注册蓝图
from app.views import register_blueprints
register_blueprints(app)

# 在应用上下文内测试URL生成
with app.app_context():
    print("=== URL生成测试 ===")
    try:
        # 测试auth.login URL生成
        login_url = url_for('auth.login')
        print(f"auth.login URL: {login_url}")
        
        # 测试main.index URL生成
        index_url = url_for('main.index')
        print(f"main.index URL: {index_url}")
        
        # 测试language_tests.test_system URL生成
        test_system_url = url_for('language_tests.test_system')
        print(f"language_tests.test_system URL: {test_system_url}")
        
        print("\n=== 测试通过！所有URL都能正确生成 ===")
        
    except Exception as e:
        print(f"✗ URL生成失败: {e}")
        import traceback
        traceback.print_exc()