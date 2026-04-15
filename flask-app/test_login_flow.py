import requests

# 测试登录流程
def test_login_flow():
    base_url = "http://localhost:8889"
    
    print("=== 测试登录流程 ===")
    
    # 1. 测试GET登录页面
    print("\n1. 测试GET登录页面...")
    response = requests.get(f"{base_url}/auth/login")
    print(f"状态码: {response.status_code}")
    print(f"页面标题: {response.text.split('<title>')[1].split('</title>')[0] if '<title>' in response.text else '无标题'}")
    
    # 2. 测试POST登录（正确用户名密码）
    print("\n2. 测试POST登录（正确用户名密码）...")
    login_data = {
        "username": "test_user",
        "password": "Test123!"
    }
    response = requests.post(f"{base_url}/auth/login", data=login_data, allow_redirects=False)
    print(f"状态码: {response.status_code}")
    print(f"重定向位置: {response.headers.get('Location')}")
    
    # 3. 测试POST登录（错误用户名密码）
    print("\n3. 测试POST登录（错误用户名密码）...")
    wrong_login_data = {
        "username": "test_user",
        "password": "WrongPass123!"
    }
    response = requests.post(f"{base_url}/auth/login", data=wrong_login_data, allow_redirects=False)
    print(f"状态码: {response.status_code}")
    print(f"重定向位置: {response.headers.get('Location')}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_login_flow()