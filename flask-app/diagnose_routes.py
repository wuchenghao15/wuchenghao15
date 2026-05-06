#!/usr/bin/env python3
"""
应用路由诊断脚本，用于分析登录跳转问题

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from app.views import register_blueprints

# 创建Flask应用实例
app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'dev-secret-key'

# 注册所有蓝图
print("=== 开始注册蓝图 ===")
register_blueprints(app)
print("=== 蓝图注册完成 ===")

# 打印所有注册的路由
print("\n=== 已注册路由列表 ===")
for rule in app.url_map.iter_rules():
    # 排除静态文件路由
    if 'static' not in str(rule):
        print(f"路由: {rule}")
        print(f"  端点: {rule.endpoint}")
        print(f"  方法: {', '.join(rule.methods)}")
        print()

# 检查特定端点是否存在
print("=== 关键端点检查 ===")
endpoints_to_check = [
    'auth.login',
    'auth.logout',
    'main.index',
    'language_tests.test_system'
]

for endpoint in endpoints_to_check:
    try:
        url = url_for(endpoint)
        print(f"✓ 端点 {endpoint} 存在，URL: {url}")
    except Exception as e:
        print(f"✗ 端点 {endpoint} 不存在: {e}")

# 测试URL生成
print("\n=== URL生成测试 ===")
try:
    login_url = url_for('auth.login')
    index_url = url_for('main.index')
    test_system_url = url_for('language_tests.test_system')

    print(f"auth.login URL: {login_url}")
    print(f"main.index URL: {index_url}")
    print(f"language_tests.test_system URL: {test_system_url}")
except Exception as e:
    print(f"URL生成失败: {e}")
    traceback.print_exc()

print("\n=== 诊断完成 ===")

"""