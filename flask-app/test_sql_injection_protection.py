#!/usr/bin/env python3
"""
测试SQL注入防护功能
"""

import requests
import json
import time

def test_sql_injection_protection():
    """测试SQL注入防护功能"""
    base_url = "https://localhost:8443"
    
    # 测试用例
    test_cases = [
        # 基本的SQL注入尝试
        {
            "name": "基本SQL注入尝试",
            "url": f"{base_url}/login",
            "method": "POST",
            "data": {
                "username": "admin' OR '1'='1",
                "password": "password"
            },
            "expected_status": 403
        },
        # 注释注入
        {
            "name": "注释注入",
            "url": f"{base_url}/login",
            "method": "POST",
            "data": {
                "username": "admin' --",
                "password": "password"
            },
            "expected_status": 403
        },
        # 联合查询
        {
            "name": "联合查询注入",
            "url": f"{base_url}/login",
            "method": "POST",
            "data": {
                "username": "admin' UNION SELECT username, password FROM users --",
                "password": "password"
            },
            "expected_status": 403
        },
        # 时间延迟攻击
        {
            "name": "时间延迟攻击",
            "url": f"{base_url}/login",
            "method": "POST",
            "data": {
                "username": "admin' OR SLEEP(5) --",
                "password": "password"
            },
            "expected_status": 403
        },
        # 布尔盲注
        {
            "name": "布尔盲注",
            "url": f"{base_url}/login",
            "method": "POST",
            "data": {
                "username": "admin' OR IF(1=1, 1, 0) --",
                "password": "password"
            },
            "expected_status": 403
        },
        # 正常登录尝试
        {
            "name": "正常登录尝试",
            "url": f"{base_url}/login",
            "method": "POST",
            "data": {
                "username": "admin",
                "password": "admin123"
            },
            "expected_status": 200  # 假设正常登录返回200
        },
        # 正常注册尝试
        {
            "name": "正常注册尝试",
            "url": f"{base_url}/register",
            "method": "POST",
            "data": {
                "username": "testuser",
                "email": "test@example.com",
                "password": "Password123!"
            },
            "expected_status": 200  # 假设正常注册返回200
        }
    ]
    
    print("开始测试SQL注入防护功能...")
    print("=" * 80)
    
    for test_case in test_cases:
        print(f"测试: {test_case['name']}")
        print(f"URL: {test_case['url']}")
        print(f"方法: {test_case['method']}")
        print(f"数据: {test_case['data']}")
        print(f"期望状态码: {test_case['expected_status']}")
        
        try:
            if test_case['method'] == 'POST':
                response = requests.post(
                    test_case['url'],
                    data=test_case['data'],
                    verify=False  # 忽略SSL证书验证
                )
            elif test_case['method'] == 'GET':
                response = requests.get(
                    test_case['url'],
                    params=test_case['data'],
                    verify=False  # 忽略SSL证书验证
                )
            
            status_code = response.status_code
            print(f"实际状态码: {status_code}")
            
            if status_code == test_case['expected_status']:
                print("✓ 测试通过")
            else:
                print("✗ 测试失败")
                print(f"响应内容: {response.text[:200]}...")
                
        except Exception as e:
            print(f"✗ 测试失败: {str(e)}")
        
        print("-" * 80)
        time.sleep(1)  # 避免请求过快
    
    print("SQL注入防护测试完成！")

if __name__ == "__main__":
    test_sql_injection_protection()
