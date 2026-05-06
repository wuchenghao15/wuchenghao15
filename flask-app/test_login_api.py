#!/usr/bin/env python3
"""
使用requests库测试登录API

import requests

# 测试登录功能
def test_login():
    """测试登录API"""
    # 登录URL
    login_url = "http://localhost:8888/auth/login"

    # 测试用户名和密码
    username = "testuser"
    password = "Test123!@#"

    print(f"\n🔍 测试登录API: {login_url}")
    print(f"   用户名: {username}")
    print(f"   密码: {password}")

    # 发送POST请求
    try:
        response = requests.post(login_url, data={
            "username": username,
            "password": password
        }, allow_redirects=False)

        print(f"\n📊 响应信息:")
        print(f"   状态码: {response.status_code}")
        print(f"   响应头: {dict(response.headers)}")
        print(f"   响应内容: {response.text[:200]}...")

        if response.status_code == 302:
            print(f"\n✅ 登录成功！重定向到: {response.headers.get('Location')}")
            return True
        else:
            print(f"\n❌ 登录失败！状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"\n💥 测试失败: {str(e)}")
        return False
def main():
    """主函数"""
    print("🚀 登录API测试脚本")
    print("=" * 50)

    # 测试登录
    test_login()

    print("\n🎉 测试完成！")

if __name__ == "__main__":
    main()
