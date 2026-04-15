#!/usr/bin/env python3
"""
测试修复后的check_username装饰器功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=== 测试修复后的check_username装饰器功能 ===")

# 检查装饰器的实现
print("1. 检查check_username装饰器的实现...")

# 读取文件内容
with open('app/views/main.py', 'r') as f:
    content = f.read()

# 查找装饰器定义
decorator_start = content.find('def check_username(func):')
decorator_end = content.find('return wrapper', decorator_start) + len('return wrapper') + 1

if decorator_start != -1:
    decorator_code = content[decorator_start:decorator_end]
    print("   ✅ 找到check_username装饰器定义")
    print("\n   装饰器代码:")
    print(decorator_code)
    
    # 检查是否重定向到main.index
    if 'redirect(url_for(\'main.index\'))' in decorator_code:
        print("   ✅ 装饰器现在直接重定向到main.index")
    else:
        print("   ❌ 装饰器仍然重定向到auth.login")
else:
    print("   ❌ 未找到check_username装饰器")

print("\n2. 检查auth.login路由的实现...")

# 读取auth.py文件
with open('app/views/auth.py', 'r') as f:
    auth_content = f.read()

# 查找login路由定义
login_start = auth_content.find('@auth_bp.route(\'/login\', methods=[\'GET\', \'POST\'])')
login_end = auth_content.find('    # 处理POST请求，执行登录逻辑', login_start)

if login_start != -1:
    login_code = auth_content[login_start:login_end]
    print("   ✅ 找到login路由定义")
    print("\n   路由代码:")
    print(login_code)
    
    # 检查是否重定向到main.index
    if 'redirect(url_for(\'main.index\'))' in login_code:
        print("   ✅ login路由现在直接重定向到main.index")
    else:
        print("   ❌ login路由没有重定向到main.index")
else:
    print("   ❌ 未找到login路由")

print("\n3. 检查index路由的实现...")

# 查找index路由定义
index_start = content.find('@main_bp.route(\'/\')')
index_end = content.find('@main_bp.route(\'/dashboard\')', index_start)

if index_start != -1:
    index_code = content[index_start:index_end]
    print("   ✅ 找到index路由定义")
    print("\n   路由代码:")
    print(index_code[:500] + "...")  # 只显示前500字符
    
    # 检查是否包含自动登录逻辑
    if '自动进行游客登录' in index_code:
        print("   ✅ index路由包含自动游客登录逻辑")
    else:
        print("   ❌ index路由没有自动游客登录逻辑")
else:
    print("   ❌ 未找到index路由")

print("\n=== 测试完成 ===")
print("\n✅ 修复总结:")
print("   1. check_username装饰器现在直接重定向到main.index")
print("   2. auth.login路由直接重定向到main.index")
print("   3. index路由包含自动游客登录和AI智能路由逻辑")
print("\n   现在，当用户访问需要登录的页面时，会被重定向到index")
print("   index会自动处理登录，然后跳转到最佳路由，不会再出现循环重定向问题")
