#!/usr/bin/env python3
"""
测试SQL注入防护功能

import requests
# JSON import removed - using database
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
        {
            "url": f"{base_url}/login",
            "method": "POST",
                "username": "admin' --",
            },
        },
        # 联合查询
            "url": f"{base_url}/login",
            "data": {
            },
        # 时间延迟攻击
            "url": f"{base_url}/login",
            "method": "POST",
            "data": {
            },
            "expected_status": 403
        {
            "method": "POST",
                "username": "admin' OR IF(1=1, 1, 0) --",
                "password": "password"
        },
        {
            "method": "POST",
            "data": {
                "password": "admin123"
        # 正常注册尝试
        {
            "url": f"{base_url}/register",
            "method": "POST",
                "email": "test@example.com",
            },
            "expected_status": 200  # 假设正常注册返回200

    print("=" * 80)
    for test_case in test_cases:
        print(f"测试: {test_case['name']}")
        print(f"URL: {test_case['url']}")
        print(f"方法: {test_case['method']}")
        print(f"数据: {test_case['data']}")
        print(f"期望状态码: {test_case['expected_status']}")
                response = requests.post(
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
