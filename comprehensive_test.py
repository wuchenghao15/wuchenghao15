#!/usr/bin/env python3
import sys
import json
import time
import requests
import sqlite3
import os
import traceback
import hashlib
import base64
from datetime import datetime

BASE_URL = "http://127.0.0.1:8888"
TIMEOUT = 15
DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'split_databases')

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

class TestFix:
    def __init__(self, category, test_name, error, fix_description, fix_code=None, fix_file=None):
        self.category = category
        self.test_name = test_name
        self.error = str(error)
        self.fix_description = fix_description
        self.fix_code = fix_code
        self.fix_file = fix_file
        self.timestamp = datetime.now().isoformat()

    def to_dict(self):
        return {
            'category': self.category,
            'test_name': self.test_name,
            'error': self.error,
            'fix_description': self.fix_description,
            'fix_code': self.fix_code,
            'fix_file': self.fix_file,
            'timestamp': self.timestamp
        }

class ComprehensiveTester:
    def __init__(self):
        self.results = []
        self.fixes = []
        self.session = requests.Session()
        self.request_delay = 0.05
    
    def add_result(self, category, test_name, status, message=None, error=None, response=None):
        result = TestResult(category, test_name, status, message, error, response)
        self.results.append(result)
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} [{category}] {test_name}: {message or (str(error)[:100] if error else 'OK')}")
        return result
    
    def add_fix(self, category, test_name, error, fix_description, fix_code=None, fix_file=None):
        fix = TestFix(category, test_name, error, fix_description, fix_code, fix_file)
        self.fixes.append(fix)
        print(f"   🛠️ 修复方案: {fix_description}")
        return fix
    
    def test_db_connection(self, db_name, db_path):
        try:
            conn = sqlite3.connect(db_path, timeout=30)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = cursor.fetchall()
            conn.close()
            self.add_result("数据库连接", f"连接 {db_name}.db", "PASS", f"{len(tables)} 个表")
            return tables
        except Exception as e:
            result = self.add_result("数据库连接", f"连接 {db_name}.db", "ERROR", error=e)
            self.add_fix("数据库连接", f"连接 {db_name}.db", e, 
                        f"检查文件是否存在: {db_path}, 检查文件权限", None, db_path)
            return None
    
    def test_db_query(self, db_name, db_path, table_name, query, params=None):
        try:
            conn = sqlite3.connect(db_path, timeout=30)
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            results = cursor.fetchall()
            conn.close()
            self.add_result("数据库查询", f"{db_name}.db 查询 {table_name}", "PASS", f"返回 {len(results)} 条记录")
            return results
        except Exception as e:
            result = self.add_result("数据库查询", f"{db_name}.db 查询 {table_name}", "ERROR", error=e)
            self.add_fix("数据库查询", f"{db_name}.db 查询 {table_name}", e,
                        f"检查SQL语法: {query}", query, db_path)
            return None
    
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
            response_str = ""
            try:
                response_data = resp.json()
                response_str = json.dumps(response_data)[:200]
            except:
                response_data = resp.text[:200]
                response_str = response_data[:200]
            
            test_name = description or f"{method} {path}"
            if resp.status_code == expected_status:
                self.add_result("API测试", test_name, "PASS", f"状态码: {resp.status_code}")
            else:
                result = self.add_result("API测试", test_name, "FAIL", 
                    f"状态码: {resp.status_code}, 期望: {expected_status}, 响应: {response_str}")
                self.add_fix("API测试", test_name, f"状态码不匹配",
                            f"检查路由配置和权限中间件", None, path)
            return resp
        except Exception as e:
            result = self.add_result("API测试", test_name or f"{method} {path}", "ERROR", error=e)
            self.add_fix("API测试", test_name or f"{method} {path}", e,
                        f"检查服务器是否运行, URL是否正确", None, path)
            return None
    
    def test_login(self, username, password, expected_role=None):
        try:
            resp = self.session.post(f"{BASE_URL}/auth/login", 
                json={"username": username, "password": password},
                timeout=TIMEOUT)
            try:
                data = resp.json()
                if resp.status_code == 200 and data.get('success'):
                    message = f"登录成功, 角色: {data.get('user', {}).get('role')}"
                    if expected_role and data.get('user', {}).get('role') != expected_role:
                        self.add_result("登录测试", f"登录 {username}", "FAIL", 
                            f"{message}, 期望角色: {expected_role}")
                    else:
                        self.add_result("登录测试", f"登录 {username}", "PASS", message)
                    return data
                else:
                    result = self.add_result("登录测试", f"登录 {username}", "FAIL", 
                        f"状态码: {resp.status_code}, 响应: {json.dumps(data)[:150]}")
                    self.add_fix("登录测试", f"登录 {username}", f"登录失败: {data.get('message')}",
                                f"检查密码是否正确, 检查用户是否存在", None, None)
            except:
                result = self.add_result("登录测试", f"登录 {username}", "FAIL", 
                    f"非JSON响应: {resp.text[:150]}")
                self.add_fix("登录测试", f"登录 {username}", "非JSON响应",
                            f"检查登录路由实现, 检查异常处理", None, None)
            return None
        except Exception as e:
            result = self.add_result("登录测试", f"登录 {username}", "ERROR", error=e)
            self.add_fix("登录测试", f"登录 {username}", e,
                        f"检查服务器是否运行, 检查登录API路径", None, None)
            return None
    
    def test_page(self, path, expected_status=200, expected_content=None, follow_redirects=True, description=None):
        try:
            time.sleep(self.request_delay)
            resp = self.session.get(f"{BASE_URL}{path}", timeout=TIMEOUT, allow_redirects=follow_redirects)
            test_name = description or f"访问 {path}"
            if resp.status_code == expected_status:
                if expected_content and expected_content not in resp.text:
                    self.add_result("页面测试", test_name, "FAIL", 
                        f"内容不匹配, 期望包含: {expected_content}")
                else:
                    self.add_result("页面测试", test_name, "PASS", 
                        f"状态码: {resp.status_code}, 内容长度: {len(resp.text)}")
            else:
                self.add_result("页面测试", test_name, "FAIL", 
                    f"状态码: {resp.status_code}, 期望: {expected_status}")
        except Exception as e:
            self.add_result("页面测试", test_name or f"访问 {path}", "ERROR", error=e)
    
    def run_all_tests(self):
        print("\n" + "="*80)
        print("MTSCOS AI v6.0.0 全面测试")
        print("="*80 + "\n")
        
        print("\n--- 1. 分布式数据库连接测试 ---")
        databases = {
            'auth': ['users', 'roles', 'permissions', 'role_permissions'],
            'exam': ['exams', 'exam_account_locks'],
            'question': ['questions'],
            'learning': ['learning_records'],
            'system': ['system_version', 'system_version_history'],
            'ai': ['ai_employees'],
            'admin': ['access_control_rules', 'admin_notifications'],
            'log': ['session_logs', 'generation_logs'],
        }
        
        for db_name, tables in databases.items():
            db_path = os.path.join(DB_DIR, f'{db_name}.db')
            if os.path.exists(db_path):
                tables_found = self.test_db_connection(db_name, db_path)
                if tables_found:
                    for table in tables:
                        self.test_db_query(db_name, db_path, table, f"SELECT COUNT(*) FROM {table}")
            else:
                self.add_result("数据库连接", f"连接 {db_name}.db", "FAIL", f"文件不存在: {db_path}")
        
        print("\n--- 2. 权限系统测试 ---")
        auth_db_path = os.path.join(DB_DIR, 'auth.db')
        self.test_db_query('auth', auth_db_path, 'roles', 'SELECT * FROM roles')
        self.test_db_query('auth', auth_db_path, 'permissions', 'SELECT * FROM permissions')
        self.test_db_query('auth', auth_db_path, 'role_permissions', 'SELECT * FROM role_permissions')
        self.test_db_query('auth', auth_db_path, 'permission_groups', 'SELECT * FROM permission_groups')
        
        print("\n--- 3. 题库系统测试 ---")
        question_db_path = os.path.join(DB_DIR, 'question.db')
        self.test_db_query('question', question_db_path, 'questions', 'SELECT COUNT(*) FROM questions')
        self.test_db_query('question', question_db_path, 'question_difficulty', 'SELECT * FROM question_difficulty')
        self.test_db_query('question', question_db_path, 'question_source', 'SELECT * FROM question_source')
        self.test_db_query('question', question_db_path, 'question_format', 'SELECT * FROM question_format')
        
        print("\n--- 4. 系统版本测试 ---")
        system_db_path = os.path.join(DB_DIR, 'system.db')
        self.test_db_query('system', system_db_path, 'system_version', 'SELECT * FROM system_version')
        self.test_db_query('system', system_db_path, 'system_version_history', 'SELECT * FROM system_version_history')
        
        print("\n--- 5. API健康检查 ---")
        self.test_api("/api/health", expected_status=200, description="健康检查")
        self.test_api("/api/server-time", expected_status=200, description="服务器时间")
        self.test_api("/api/system/status", expected_status=200, description="系统状态")
        
        print("\n--- 6. 登录API测试 ---")
        login_result = self.test_login("wuchenghao15", "LoginMe.1988", expected_role="hardware_admin")
        
        if login_result:
            print("\n--- 7. 登录后API测试 ---")
            token = login_result.get('token')
            headers = {'Authorization': f'Bearer {token}'} if token else {}
            self.test_api("/api/user/info", headers=headers, expected_status=200, description="用户信息")
            self.test_api("/api/system/status", headers=headers, expected_status=200, description="系统状态(登录)")
        
        print("\n--- 8. 页面访问测试 ---")
        self.test_page("/", expected_content="MTSCOS AI", description="首页")
        self.test_page("/login", expected_content="MTSCOS AI", description="登录页")
        self.test_page("/auth/login", expected_status=405, description="登录API页面(POST only)")
        
        print("\n--- 9. 路由检查 ---")
        routes = ['/', '/login', '/api/health', '/api/system/status']
        for route in routes:
            self.test_api(route, expected_status=200, description=f"路由 {route}")
        
        print("\n--- 10. db_manager模块测试 ---")
        try:
            from db_manager import connect, get_db_for_table, TABLE_TO_DB, build_table_mapping
            build_table_mapping()
            
            if len(TABLE_TO_DB) > 0:
                self.add_result("模块测试", "db_manager TABLE_TO_DB", "PASS", f"映射了 {len(TABLE_TO_DB)} 个表")
            else:
                self.add_result("模块测试", "db_manager TABLE_TO_DB", "FAIL", "表映射为空")
            
            conn = connect('auth')
            if conn:
                self.add_result("模块测试", "db_manager connect('auth')", "PASS", "连接成功")
                conn.close()
            else:
                self.add_result("模块测试", "db_manager connect('auth')", "FAIL", "连接失败")
            
            db_name = get_db_for_table('users')
            if db_name == 'auth':
                self.add_result("模块测试", "get_db_for_table('users')", "PASS", f"正确路由到 {db_name}")
            else:
                self.add_result("模块测试", "get_db_for_table('users')", "FAIL", f"期望 auth, 实际 {db_name}")
                
        except Exception as e:
            result = self.add_result("模块测试", "db_manager导入", "ERROR", error=e)
            self.add_fix("模块测试", "db_manager导入", e,
                        f"检查db_manager.py语法错误, 检查依赖", None, "db_manager.py")
        
        print("\n" + "="*80)
        return self.generate_report()
    
    def generate_report(self):
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
                    print(f"  [{r.category}] {r.test_name}: {r.status}")
                    if r.error:
                        print(f"      错误: {str(r.error)[:150]}")
        
        if self.fixes:
            print(f"\n修复方案 ({len(self.fixes)}个):")
            for fix in self.fixes:
                print(f"  [{fix.category}] {fix.test_name}:")
                print(f"      修复: {fix.fix_description}")
        
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
            'fixes': [f.to_dict() for f in self.fixes],
            'system_version': 'v6.0.0'
        }
        
        report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_report_v6.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n测试报告已保存: {report_path}")
        
        fixes_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_fixes_v6.json")
        with open(fixes_path, 'w', encoding='utf-8') as f:
            json.dump([fix.to_dict() for fix in self.fixes], f, ensure_ascii=False, indent=2)
        print(f"修复方案已保存: {fixes_path}")
        
        return report

if __name__ == "__main__":
    tester = ComprehensiveTester()
    try:
        report = tester.run_all_tests()
    except Exception as e:
        print(f"\n测试执行异常: {e}")
        traceback.print_exc()