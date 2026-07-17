#!/usr/bin/env python3
import sys
import json
import time
import requests
import sqlite3
import os
import traceback
from datetime import datetime

BASE_URL = "http://127.0.0.1:8888"
TIMEOUT = 15

class TestResult:
    def __init__(self, category, test_name, status, message=None, error=None, response=None):
        self.category = category
        self.test_name = test_name
        self.status = status
        self.message = message
        self.error = error
        self.response = response
        self.timestamp = datetime.now().isoformat()

    def to_dict(self):
        return {
            'category': self.category,
            'test_name': self.test_name,
            'status': self.status,
            'message': self.message,
            'error': str(self.error) if self.error else None,
            'response': self.response,
            'timestamp': self.timestamp
        }

class SystemTester:
    def __init__(self):
        self.results = []
        self.session = requests.Session()
        self.failed_tests = []
        self.request_delay = 0.05
    
    def add_result(self, category, test_name, status, message=None, error=None, response=None):
        result = TestResult(category, test_name, status, message, error, response)
        self.results.append(result)
        if status != "PASS":
            self.failed_tests.append(result)
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} [{category}] {test_name}: {message or (str(error)[:80] if error else 'OK')}")
    
    def test_page(self, path, expected_status=200, expected_content=None, follow_redirects=True, description=None):
        try:
            time.sleep(self.request_delay)
            resp = self.session.get(f"{BASE_URL}{path}", timeout=TIMEOUT, allow_redirects=follow_redirects)
            test_name = description or f"访问 {path}"
            if resp.status_code == expected_status:
                if expected_content and expected_content not in resp.text:
                    self.add_result("页面访问", test_name, "FAIL", 
                        f"内容不匹配，期望包含: {expected_content}, 实际状态码: {resp.status_code}")
                else:
                    self.add_result("页面访问", test_name, "PASS", 
                        f"状态码: {resp.status_code}, 内容长度: {len(resp.text)}")
            else:
                self.add_result("页面访问", test_name, "FAIL", 
                    f"状态码: {resp.status_code}, 期望: {expected_status}")
        except Exception as e:
            self.add_result("页面访问", test_name or f"访问 {path}", "ERROR", error=e)
    
    def test_api(self, path, method='GET', data=None, headers=None, expected_status=200, description=None):
        try:
            time.sleep(self.request_delay)
            url = f"{BASE_URL}{path}"
            if method == 'POST':
                resp = self.session.post(url, json=data, headers=headers, timeout=TIMEOUT)
            elif method == 'PUT':
                resp = self.session.put(url, json=data, headers=headers, timeout=TIMEOUT)
            elif method == 'DELETE':
                resp = self.session.delete(url, headers=headers, timeout=TIMEOUT)
            else:
                resp = self.session.get(url, headers=headers, timeout=TIMEOUT)
            
            response_data = None
            try:
                response_data = resp.json()
                response_str = json.dumps(response_data)[:150]
            except:
                response_data = resp.text[:150]
                response_str = response_data[:150]
            
            test_name = description or f"{method} {path}"
            if resp.status_code == expected_status:
                self.add_result("API测试", test_name, "PASS", 
                    f"状态码: {resp.status_code}")
            else:
                self.add_result("API测试", test_name, "FAIL", 
                    f"状态码: {resp.status_code}, 期望: {expected_status}, 响应: {response_str}")
            return resp
        except Exception as e:
            self.add_result("API测试", test_name or f"{method} {path}", "ERROR", error=e)
            return None
    
    def test_static_resource(self, path):
        try:
            time.sleep(self.request_delay)
            resp = self.session.get(f"{BASE_URL}{path}", timeout=TIMEOUT)
            if resp.status_code == 200:
                self.add_result("静态资源", f"获取 {path}", "PASS", 
                    f"大小: {len(resp.content)} bytes, Content-Type: {resp.headers.get('Content-Type', '')}")
            else:
                self.add_result("静态资源", f"获取 {path}", "FAIL", 
                    f"状态码: {resp.status_code}")
        except Exception as e:
            self.add_result("静态资源", f"获取 {path}", "ERROR", error=e)
    
    def test_database(self, db_path, description):
        try:
            conn = sqlite3.connect(db_path, timeout=30, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            conn.close()
            self.add_result("数据库", description, "PASS", f"表数量: {len(tables)}")
            return tables
        except Exception as e:
            self.add_result("数据库", description, "ERROR", error=e)
            return None
    
    def test_route_exists(self, path, method='GET', expected_status=200, follow_redirects=False):
        try:
            time.sleep(self.request_delay)
            url = f"{BASE_URL}{path}"
            if method == 'POST':
                resp = self.session.post(url, timeout=TIMEOUT, allow_redirects=follow_redirects)
            else:
                resp = self.session.get(url, timeout=TIMEOUT, allow_redirects=follow_redirects)
            
            if resp.status_code == expected_status or resp.status_code in [301, 302, 401, 403]:
                self.add_result("路由检测", f"{method} {path}", "PASS", 
                    f"状态码: {resp.status_code}")
            else:
                self.add_result("路由检测", f"{method} {path}", "FAIL", 
                    f"状态码: {resp.status_code}")
        except Exception as e:
            self.add_result("路由检测", f"{method} {path}", "ERROR", error=e)
    
    def test_login(self, username, password):
        try:
            resp = self.session.post(f"{BASE_URL}/api/auth/login", 
                json={"username": username, "password": password},
                timeout=TIMEOUT)
            try:
                data = resp.json()
                if resp.status_code == 200 and data.get('success'):
                    self.add_result("登录测试", f"登录 {username}", "PASS", 
                        f"登录成功, token: {data.get('token', '')[:20]}...")
                    return data.get('token')
                else:
                    self.add_result("登录测试", f"登录 {username}", "FAIL", 
                        f"状态码: {resp.status_code}, 响应: {json.dumps(data)[:100]}")
            except:
                self.add_result("登录测试", f"登录 {username}", "FAIL", 
                    f"非JSON响应: {resp.text[:100]}")
            return None
        except Exception as e:
            self.add_result("登录测试", f"登录 {username}", "ERROR", error=e)
            return None
    
    def test_component_health(self):
        try:
            from app import run_full_initialization
            from flask import Flask
            
            app = Flask(__name__)
            app.secret_key = 'test'
            
            import io
            old_stderr = sys.stderr
            sys.stderr = io.StringIO()
            
            try:
                results, app = run_full_initialization(app)
                stderr_output = sys.stderr.getvalue()
            finally:
                sys.stderr = old_stderr
            
            failed_components = []
            for line in stderr_output.split('\n'):
                if '~' in line and ('无可用初始化方式' in line or '模块未找到' in line or '类实例化失败' in line or 'Read-only' in line or 'ImportError' in line or 'ModuleNotFound' in line):
                    failed_components.append(line.strip())
            
            if failed_components:
                self.add_result("组件健康", "初始化检查", "FAIL", f"失败组件: {len(failed_components)}个")
                for comp in failed_components[:10]:
                    self.add_result("组件健康", f"失败: {comp[:60]}", "FAIL", comp)
            else:
                self.add_result("组件健康", "初始化检查", "PASS", "所有组件初始化成功")
            
            return failed_components
        except Exception as e:
            self.add_result("组件健康", "初始化检查", "ERROR", error=e)
            return []
    
    def run_all_tests(self):
        print("\n" + "="*80)
        print("MTSCOS AI 系统全面测试 - 完整版")
        print("="*80 + "\n")
        
        print("\n--- 1. 基础页面测试 ---")
        self.test_page("/", expected_content="用户登录", description="首页/登录页")
        self.test_page("/login", expected_content="用户登录", description="登录页面")
        self.test_page("/register", expected_content="用户注册", description="注册页面")
        self.test_page("/forgot_password", expected_content="忘记密码", description="忘记密码页面")
        self.test_page("/reset-password/test-token", expected_status=200, description="重置密码页面")
        self.test_page("/home", expected_status=302, follow_redirects=False, description="首页重定向")
        self.test_page("/nonexistent_page_xyz", expected_status=200, description="不存在页面(系统统一处理)")
        
        print("\n--- 2. API端点测试 (未登录) ---")
        self.test_api("/api/health", expected_status=200, description="健康检查API")
        self.test_api("/api/server-time", expected_status=200, description="服务器时间API")
        self.test_api("/api/system/status", expected_status=200, description="系统状态API")
        self.test_api("/api/routes/list", expected_status=200, description="路由列表API")
        self.test_api("/api/role/list", expected_status=200, description="角色列表API")
        self.test_api("/api/local-agents/list", expected_status=200, description="本地代理列表API")
        self.test_api("/api/ai-employee-enhanced/system/status", expected_status=200, description="AI员工增强API")
        self.test_api("/api/monitoring/health", expected_status=200, description="监控健康API")
        
        print("\n--- 3. 需要认证的API测试 ---")
        self.test_api("/api/user/info", expected_status=401, description="用户信息API(未登录)")
        self.test_api("/api/ai-distributed-db/status", expected_status=401, description="分布式DB状态API(未登录)")
        self.test_api("/api/ai-distributed-db/shards", expected_status=401, description="分布式DB分片API(未登录)")
        self.test_api("/api/ai-distributed-db/health", expected_status=401, description="分布式DB健康API(未登录)")
        self.test_api("/api/notifications", expected_status=404, description="通知API")
        
        print("\n--- 4. 静态资源测试 ---")
        self.test_static_resource("/assets/tailwind.min.css")
        self.test_static_resource("/assets/all.min.css")
        self.test_static_resource("/assets/layout_adapter.js")
        self.test_static_resource("/static/css/style.css")
        
        print("\n--- 5. 数据库测试 ---")
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.test_database(os.path.join(base_dir, "app.db"), "主数据库 app.db")
        self.test_database(os.path.join(base_dir, "ai_distributed_db.db"), "元数据库 ai_distributed_db.db")
        self.test_database(os.path.join(base_dir, "databases", "logs.db"), "日志分片库 logs.db")
        self.test_database(os.path.join(base_dir, "databases", "core.db"), "核心分片库 core.db")
        self.test_database(os.path.join(base_dir, "databases", "ai_engine.db"), "AI引擎分片库 ai_engine.db")
        
        print("\n--- 6. 路由完整性测试 ---")
        public_routes = [
            '/', '/login', '/register', '/forgot_password', '/reset_password',
            '/k12', '/k12/status',
            '/api/health', '/api/server-time', '/api/system/status',
            '/api/routes/list', '/api/routes/reload', '/api/routes/check'
        ]
        
        auth_routes = [
            '/dashboard', '/exam_system', '/exam_system/exams', '/exam_system/tests',
            '/student_portal', '/student_dashboard',
            '/admin_dashboard', '/super_admin_dashboard', '/settings',
            '/teacher', '/designer', '/hardware/dashboard',
            '/ai-chat', '/test_system', '/math_training',
            '/learning_system', '/wrong_questions', '/daily_practice',
            '/random_challenge', '/custom_practice',
            '/admin_app', '/admin_app/login',
            '/mobile', '/mobile/login', '/mobile/home'
        ]
        
        for route in public_routes:
            if route == '/api/routes/reload':
                self.test_route_exists(route, method='POST', expected_status=200)
            elif route == '/api/routes/check':
                self.test_api('/api/routes/check', method='POST', data={'route': '/dashboard', 'role': 'student'}, expected_status=200)
            else:
                self.test_route_exists(route, expected_status=200)
        
        for route in auth_routes:
            self.test_route_exists(route, expected_status=302)
        
        print("\n--- 7. 考试系统路由测试 ---")
        exam_routes = [
            '/exam_system', '/exam_system/exams', '/exam_system/tests',
            '/exam_system/custom_practice', '/exam_system/daily_practice',
            '/exam_system/random_challenge', '/exam_system/wrong_questions'
        ]
        for route in exam_routes:
            self.test_route_exists(route, expected_status=302)
        
        print("\n--- 8. K12系统路由测试 ---")
        k12_routes = [
            '/k12', '/k12/exam', '/k12/report', '/k12/subject/math',
            '/k12/practice', '/k12/set_grade'
        ]
        for route in k12_routes:
            self.test_route_exists(route)
        
        print("\n--- 9. 语言测试路由测试 ---")
        language_routes = [
            '/language_test', '/english_test', '/japanese_test',
            '/language_test/take', '/japanese_test_page'
        ]
        for route in language_routes:
            self.test_route_exists(route)
        
        print("\n--- 10. 管理后台路由测试 ---")
        admin_routes = [
            '/admin_dashboard', '/super_admin_dashboard', '/settings',
            '/admin_center', '/system_monitoring', '/log_management',
            '/user_system', '/permission_management', '/exam_management'
        ]
        for route in admin_routes:
            self.test_route_exists(route, expected_status=302)
        
        print("\n--- 11. 安全中间件测试 ---")
        resp = self.test_api("/test-csrf", method="POST", expected_status=403)
        if resp:
            try:
                data = resp.json()
                if 'CSRF' in data.get('message', ''):
                    self.add_result("安全测试", "CSRF保护", "PASS", "CSRF保护正常工作")
                else:
                    self.add_result("安全测试", "CSRF保护", "FAIL", f"响应: {data}")
            except:
                self.add_result("安全测试", "CSRF保护", "FAIL", "非JSON响应")
        
        print("\n--- 12. 组件健康检查 ---")
        failed_components = self.test_component_health()
        
        print("\n--- 13. AI员工API测试 ---")
        self.test_api("/api/ai-employee-enhanced/system/status", expected_status=200)
        self.test_api("/api/local-agents/list", expected_status=200)
        
        print("\n--- 14. 分布式数据库API测试 ---")
        self.test_api("/api/ai-distributed-db/status", expected_status=401)
        self.test_api("/api/ai-distributed-db/shards", expected_status=401)
        
        print("\n--- 15. 配置管理API测试 ---")
        self.test_api("/api/system_params/list", expected_status=200)
        
        print("\n" + "="*80)
        return self.generate_report(failed_components)
    
    def generate_report(self, failed_components=None):
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        errors = sum(1 for r in self.results if r.status == "ERROR")
        
        print(f"\n测试结果汇总:")
        print(f"  总数: {total}")
        print(f"  通过: {passed}")
        print(f"  失败: {failed}")
        print(f"  错误: {errors}")
        
        if failed > 0 or errors > 0:
            print("\n失败/错误详情:")
            for r in self.results:
                if r.status != "PASS":
                    print(f"  [{r.category}] {r.test_name}: {r.status} - {r.message or r.error}")
        
        report = {
            'summary': {
                'total': total,
                'passed': passed,
                'failed': failed,
                'errors': errors,
                'timestamp': datetime.now().isoformat(),
                'pass_rate': round(passed / total * 100, 2) if total > 0 else 0
            },
            'results': [r.to_dict() for r in self.results],
            'failed_components': failed_components or [],
            'failed_tests': [r.to_dict() for r in self.failed_tests]
        }
        
        report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n测试报告已保存: {report_path}")
        
        return report

if __name__ == "__main__":
    tester = SystemTester()
    try:
        report = tester.run_all_tests()
    except Exception as e:
        print(f"\n测试执行异常: {e}")
        traceback.print_exc()