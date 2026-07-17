import requests
import json
import time

BASE_URL = "http://localhost:8888"

api_endpoints = [
    "/api/super_admin/overview",
    "/api/super_admin/resources",
    "/api/super_admin/logs?page=1",
    "/api/super_admin/users?page=1",
    "/api/super_admin/exams?page=1",
    "/api/super_admin/routes",
    "/api/super_admin/engines",
    "/api/super_admin/employees",
    "/api/super_admin/agents",
    "/api/super_admin/backups",
    "/api/super_admin/settings",
    "/api/super_admin/security/intrusion_stats",
    "/api/super_admin/security/audit_logs",
    "/api/super_admin/ai_analytics/learning",
    "/api/super_admin/ai_analytics/exam",
    "/api/super_admin/ai_analytics/user_behavior",
    "/api/super_admin/notifications?page=1",
    "/api/super_admin/announcements?page=1",
    "/api/super_admin/health/check",
    "/api/super_admin/health/history",
    "/api/super_admin/tasks",
    "/api/super_admin/tasks/logs",
    "/api/super_admin/sessions",
]

def test_api():
    session = requests.Session()
    session.headers.update({'Accept': 'application/json'})
    
    print("=" * 60)
    print("MTSCOS AI API 测试")
    print("=" * 60)
    
    print("\n[1/2] 登录系统...")
    login_data = {
        "username": "admin",
        "password": "superadmin123"
    }
    
    try:
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        response = session.post(f"{BASE_URL}/auth/login", json=login_data, headers=headers)
        print(f"登录响应: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容: '{response.text[:500]}'")
        
        if response.status_code == 200:
            if response.text.strip():
                try:
                    data = response.json()
                    if data.get('success'):
                        print("✓ 登录成功")
                        print(f"Session cookies: {dict(session.cookies)}")
                        print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)[:300]}")
                    else:
                        print(f"✗ 登录失败: {data.get('message', '未知错误')}")
                        return False
                except:
                    print(f"✗ 非JSON响应: {response.text[:200]}")
                    return False
            else:
                print("✗ 响应为空")
                return False
        else:
            print(f"✗ 登录失败: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"✗ 登录异常: {e}")
        return False
    
    print("\n[2/2] 测试API端点...")
    results = []
    
    for endpoint in api_endpoints:
        time.sleep(0.1)
        try:
            if endpoint == "/api/super_admin/health/check":
                response = session.post(f"{BASE_URL}{endpoint}", timeout=10)
            else:
                response = session.get(f"{BASE_URL}{endpoint}", timeout=10)
            try:
                data = response.json()
                code = data.get('code', data.get('success', 'unknown'))
                message = data.get('message', '')
                has_data = 'data' in data and data['data'] is not None
                
                if code == 200 or (isinstance(code, bool) and code):
                    status = "✅"
                    result_detail = f"code={code}, has_data={has_data}"
                else:
                    status = "⚠️"
                    result_detail = f"code={code}, msg={message[:50]}"
            except:
                status = "❌"
                result_detail = f"非JSON响应 ({response.status_code})"
            
            results.append((status, endpoint, result_detail))
            
        except Exception as e:
            results.append(("❌", endpoint, f"请求失败: {str(e)[:50]}"))
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    success_count = sum(1 for r in results if r[0] == "✅")
    warning_count = sum(1 for r in results if r[0] == "⚠️")
    error_count = sum(1 for r in results if r[0] == "❌")
    
    for status, endpoint, detail in results:
        print(f"{status} {endpoint:50} {detail}")
    
    print("\n" + "=" * 60)
    print(f"统计: ✅ {success_count} | ⚠️ {warning_count} | ❌ {error_count}")
    print(f"成功率: {(success_count / len(results)) * 100:.1f}%")
    print("=" * 60)
    
    return success_count > 0

if __name__ == "__main__":
    test_api()