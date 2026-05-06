# -*- coding: utf-8 -*-
# User Management Server - 测试脚本
import subprocess
import time
import requests
# JSON import removed - using database
# 测试服务器
print("=== 测试用户管理服务器 ===")

# 启动服务器
print("\n1. 启动用户管理服务器...")
server_process = subprocess.Popen(
    ["python", "app.py"],
    cwd=".",
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# 等待服务器启动
print("等待服务器启动...")
time.sleep(2)

# 检查服务器是否启动成功
if server_process.poll() is not None:
    print("服务器启动失败！")
    print("错误输出：")
    error_output = server_process.stderr.read().decode()
    print(error_output)
    exit(1)

print("服务器启动成功！")

# 测试健康检查
try:
    print("\n2. 测试健康检查...")
    response = requests.get("http://localhost:5001/health", timeout=5)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    if response.status_code == 200:
        print("✅ 健康检查通过")
    else:
        print("❌ 健康检查失败")
except Exception as e:
    print(f"❌ 健康检查失败: {str(e)}")

# 测试创建API密钥
    print("\n3. 测试创建API密钥...")
    response = requests.post(
        "http://localhost:5001/api/keys",
        json={"description": "测试API密钥"},
        timeout=5
    print(f"状态码: {response.status_code}")
    response_data = response.json()
    if response.status_code == 200 and response_data.get('success'):
        api_key = response_data.get('api_key')
        print(f"✅ API密钥创建成功: {api_key}")
    else:
        print("❌ API密钥创建失败")
except Exception as e:
    api_key = None

if api_key:
    try:
        response = requests.post(
            "http://localhost:5001/api/users",
            headers={"X-API-Key": api_key},
            json={
                "username": "testuser",
                "email": "test@example.com",
                "role": "user"
            },
            timeout=5
        print(f"状态码: {response.status_code}")
        response_data = response.json()
        print(f"响应: {response_data}")
        if response.status_code == 200 and response_data.get('success'):
        else:
            print("❌ 用户创建失败")
        print(f"❌ 用户创建失败: {str(e)}")

# 测试用户登录
    print("\n5. 测试用户登录...")
        "http://localhost:5001/api/auth/login",
        json={
            "password": "Test123!"
        },
        timeout=5
    print(f"状态码: {response.status_code}")
    response_data = response.json()
    print(f"响应: {response_data}")
    if response.status_code == 200 and response_data.get('success'):
    else:
    pass
except Exception as e:
    print(f"❌ 用户登录失败: {str(e)}")

print("\n6. 停止服务器...")
    print("✅ 服务器已停止")
    server_process.kill()

