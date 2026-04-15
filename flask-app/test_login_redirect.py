#!/usr/bin/env python3
"""
测试登录重定向功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.views import register_blueprints

# 创建Flask应用实例
app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'dev-secret-key'

# 注册所有蓝图
register_blueprints(app)

print("=== 登录重定向测试 ===")

# 测试路由是否存在
try:
    with app.test_request_context():
        # 测试URL生成
        from flask import url_for
        login_url = url_for('auth.login')
        index_url = url_for('main.index')
        test_system_url = url_for('language_tests.test_system')
        
        print(f"✓ 路由生成成功")
        print(f"  auth.login URL: {login_url}")
        print(f"  main.index URL: {index_url}")
        print(f"  language_tests.test_system URL: {test_system_url}")
        
        # 测试会话设置和重定向
        with app.test_client() as client:
            # 设置会话为已登录状态
            with client.session_transaction() as sess:
                sess['logged_in'] = True
                sess['username'] = 'test_user'
                sess['user_level'] = 'user'
            
            # 测试访问首页是否会重定向到测试系统
            response = client.get('/', follow_redirects=False)
            print(f"\n✓ 测试已登录用户访问首页")
            print(f"  状态码: {response.status_code}")
            print(f"  重定向位置: {response.location}")
            
            # 检查是否重定向到了测试系统
            if response.status_code == 302 and '/test-system' in response.location:
                print(f"  ✅ 登录重定向修复成功！已登录用户访问首页会重定向到测试系统")
            else:
                print(f"  ❌ 登录重定向修复失败！已登录用户访问首页没有重定向到测试系统")
                
except Exception as e:
    print(f"❌ 测试失败: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n=== 测试完成 ===")
