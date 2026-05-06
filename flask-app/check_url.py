#!/usr/bin/env python3
"""
检查登录表单URL是否正确

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, url_for
from app.views import register_blueprints

# 创建Flask应用实例
app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'dev-secret-key'

# 注册所有蓝图
register_blueprints(app)

# 测试URL生成
print("=== URL生成测试 ===")
try:
    login_url = url_for('auth.login')
    index_url = url_for('main.index')
    test_system_url = url_for('language_tests.test_system')

    print(f"auth.login URL: {login_url}")
    print(f"main.index URL: {index_url}")
    print(f"language_tests.test_system URL: {test_system_url}")
except Exception as e:
    print(f"URL生成失败: {e}")
    import traceback
    traceback.print_exc()

# 检查硬编码的/auth/login是否正确
print("\n=== 硬编码URL检查 ===")
if login_url == '/auth/login':
    print("✓ 硬编码的/auth/login与auth.login端点匹配")
else:
    print(f"✗ 硬编码的/auth/login与auth.login端点不匹配，应该是: {login_url}")

# 检查所有注册的路由
print("\n=== 所有注册路由 ===")
for rule in app.url_map.iter_rules():
    if 'static' not in str(rule):
        print(f"{rule} -> {rule.endpoint}")

"""