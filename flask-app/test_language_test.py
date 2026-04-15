#!/usr/bin/env python3
"""
测试语言测试系统功能的脚本
"""

import requests

# 测试配置
BASE_URL = 'http://localhost:8888'
TEST_USERNAME = 'caopw'  # 学生账户
TEST_PASSWORD = 'xuxu4pipo'  # 正确密码

def test_login():
    """测试用户登录"""
    print("=== 测试用户登录 ===")
    login_url = f"{BASE_URL}/auth/login"
    
    # 准备登录数据
    login_data = {
        'username': TEST_USERNAME,
        'password': TEST_PASSWORD
    }
    
    # 发送登录请求，允许重定向
    response = requests.post(login_url, data=login_data, allow_redirects=True)
    
    print(f"登录状态码: {response.status_code}")
    print(f"最终URL: {response.url}")
    
    # 检查是否登录成功
    if response.status_code == 200 and 'language-test' in response.url:
        print("✅ 登录成功，自动跳转到语言测试系统")
        return response.cookies
    else:
        print("❌ 登录失败")
        print(f"响应内容: {response.text[:500]}...")
        return None

def test_language_test_start(cookies):
    """测试开始语言测试"""
    print("\n=== 测试开始语言测试 ===")
    start_url = f"{BASE_URL}/language-test/start"
    
    # 发送开始测试请求
    response = requests.post(start_url, cookies=cookies, allow_redirects=False)
    
    print(f"开始测试状态码: {response.status_code}")
    print(f"开始测试响应头: {dict(response.headers)}")
    
    # 检查是否成功重定向到测试页面
    if response.status_code == 302 and 'language-test/take' in response.headers.get('Location', ''):
        print("✅ 开始测试成功，准备进入测试页面")
        return True
    else:
        print("❌ 开始测试失败")
        print(f"响应内容: {response.text}")
        return False

def test_database_records():
    """测试数据库记录是否生成"""
    print("\n=== 测试数据库记录 ===")
    import sqlite3
    
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # 检查测试记录
    cursor.execute('SELECT COUNT(*) FROM tests')
    tests_count = cursor.fetchone()[0]
    print(f"数据库测试记录数: {tests_count}")
    
    # 检查测试题目记录
    cursor.execute('SELECT COUNT(*) FROM test_questions')
    test_questions_count = cursor.fetchone()[0]
    print(f"数据库测试题目记录数: {test_questions_count}")
    
    # 检查题库数量
    cursor.execute('SELECT COUNT(*) FROM questions')
    questions_count = cursor.fetchone()[0]
    print(f"数据库题库数量: {questions_count}")
    
    conn.close()
    
    if tests_count > 0 and test_questions_count > 0:
        print("✅ 数据库记录生成成功")
        return True
    else:
        print("❌ 数据库记录生成失败")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试语言测试系统功能")
    
    # 1. 测试登录
    cookies = test_login()
    if cookies:
        print("✅ 登录成功，继续测试")
    else:
        print("❌ 登录失败，测试终止")
        return
    
    # 2. 测试开始语言测试
    test_language_test_start(cookies)
    
    # 3. 测试数据库记录
    test_database_records()
    
    print("\n🎉 语言测试系统功能测试完成！")

if __name__ == "__main__":
    main()
