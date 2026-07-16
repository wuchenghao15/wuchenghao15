#!/usr/bin/env python3
"""
MTSCOS AI 系统全面测试脚本
测试所有页面、API、数据库连接和功能模块
"""

import os
import sys
import json
import requests
import sqlite3
import time
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

class MTSCOSTester:
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
                        f"内容不匹配，期望包含: {expected_content[:50]}")
                else:
                    self.add_result("页面访问", test_name, "PASS", 
                        f"状态码: {resp.status_code}, 内容长度: {len(resp.text)}")
            elif expected_status in [301, 302] and resp.status_code in [301, 302]:
                self.add_result("页面访问", test_name, "PASS", 
                    f"状态码: {resp.status_code} (重定向)")
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
                response_str = json.dumps(response_data)[:200]
            except:
                response_data = resp.text[:200]
                response_str = response_data[:200]
            
            test_name = description or f"{method} {path}"
            if resp.status_code == expected_status:
                self.add_result("API测试", test_name, "PASS", 
                    f"状态码: {resp.status_code}")
            elif expected_status in [401, 403] and resp.status_code in [401, 403]:
                self.add_result("API测试", test_name, "PASS", 
                    f"状态码: {resp.status_code} (权限控制正常)")
            else:
                self.add_result("API测试", test_name, "FAIL", 
                    f"状态码: {resp.status_code}, 期望: {expected_status}")
            return resp
        except Exception as e:
            self.add_result("API测试", test_name or f"{method} {path}", "ERROR", error=e)
            return None
    
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
    
    def test_login(self, username, password):
        try:
            resp = self.session.post(f"{BASE_URL}/api/auth/login", 
                json={"username": username, "password": password},
                timeout=TIMEOUT)
            try:
                data = resp.json()
                if resp.status_code == 200 and data.get('success'):
                    self.add_result("登录测试", f"登录 {username}", "PASS", 
                        f"登录成功")
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
    
    def test_admin_app_pages(self):
        print("\n--- 管理员App页面测试 ---")
        admin_pages = [
            '/admin_app', '/admin_app/login', '/admin_app/dashboard',
            '/admin_app/users', '/admin_app/exams', '/admin_app/monitor',
            '/admin_app/courses', '/admin_app/assignments', '/admin_app/notifications',
            '/admin_app/resource_manager', '/admin_app/data_analysis', '/admin_app/user_auth',
            '/admin_app/learning_paths', '/admin_app/student_analytics', '/admin_app/exam_analysis',
            '/admin_app/wrong_book'
        ]
        
        for page in admin_pages:
            self.test_page(page, expected_status=200, description=f"Admin页面: {page}")
    
    def test_frontend_pages(self):
        print("\n--- 前端页面测试 ---")
        frontend_pages = [
            ('/', 200), ('/login', 200), ('/register', 200), ('/forgot_password', 200),
            ('/dashboard', 200), ('/exam_system', 401), ('/exam_system/exams', 401),
            ('/student_portal', 200), ('/student_dashboard', 200),
            ('/teacher', 401), ('/designer', 200), ('/ai-chat', 200),
            ('/learning_system', 200), ('/wrong_questions', 200), ('/daily_practice', 200),
            ('/k12', 200), ('/language_test', 200), ('/english_test', 200), ('/japanese_test', 200),
            ('/mobile', 200), ('/mobile/login', 200), ('/mobile/home', 200)
        ]
        
        for page, expected_status in frontend_pages:
            self.test_page(page, expected_status=expected_status, description=f"前端页面: {page}")
    
    def test_all_apis(self):
        print("\n--- API端点测试 ---")
        public_apis = [
            ('/api/health', 'GET', 200, '健康检查API'),
            ('/api/server-time', 'GET', 200, '服务器时间API'),
            ('/api/system/status', 'GET', 200, '系统状态API'),
            ('/api/routes/list', 'GET', 200, '路由列表API'),
            ('/api/role/list', 'GET', 200, '角色列表API'),
            ('/api/local-agents/list', 'GET', 200, '本地代理列表API'),
            ('/api/system_params/list', 'GET', 200, '系统参数API'),
            ('/api/monitoring/health', 'GET', 200, '监控健康API'),
            ('/api/questions/categories', 'GET', 200, '题目分类API'),
            ('/api/questions/tags', 'GET', 200, '题目标签API'),
        ]
        
        auth_apis = [
            ('/api/user/info', 'GET', 401, '用户信息API(未登录)'),
            ('/api/ai-distributed-db/status', 'GET', 401, '分布式DB状态API'),
            ('/api/notification/send', 'POST', 401, '发送通知API'),
            ('/api/system/notices/marquee/toggle', 'POST', 401, '通知开关API'),
        ]
        
        for api in public_apis:
            self.test_api(api[0], method=api[1], expected_status=api[2], description=api[3])
        
        for api in auth_apis:
            self.test_api(api[0], method=api[1], expected_status=api[2], description=api[3])
    
    def test_database_tables(self):
        print("\n--- 数据库测试 ---")
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_files = [
            'mtscos_db.sqlite', 'app.db', 
        ]
        
        for db_file in db_files:
            db_path = os.path.join(base_dir, db_file)
            if os.path.exists(db_path):
                self.test_database(db_path, f"数据库: {db_file}")
            else:
                self.add_result("数据库", f"数据库: {db_file}", "FAIL", "文件不存在")
        
        databases_dir = os.path.join(base_dir, "databases")
        if os.path.exists(databases_dir):
            for db_file in os.listdir(databases_dir):
                if db_file.endswith('.db'):
                    db_path = os.path.join(databases_dir, db_file)
                    self.test_database(db_path, f"分片数据库: {db_file}")
    
    def test_static_resources(self):
        print("\n--- 静态资源测试 ---")
        static_resources = [
            '/assets/css/mtscos-design-system.css',
            '/assets/font-awesome/css/all.min.css',
            '/assets/tailwind.min.css',
            '/assets/all.min.css',
            '/assets/layout_adapter.js',
            '/static/css/style.css',
        ]
        
        for resource in static_resources:
            try:
                time.sleep(self.request_delay)
                resp = self.session.get(f"{BASE_URL}{resource}", timeout=TIMEOUT)
                if resp.status_code == 200:
                    self.add_result("静态资源", f"获取 {resource}", "PASS", 
                        f"大小: {len(resp.content)} bytes")
                else:
                    self.add_result("静态资源", f"获取 {resource}", "FAIL", 
                        f"状态码: {resp.status_code}")
            except Exception as e:
                self.add_result("静态资源", f"获取 {resource}", "ERROR", error=e)
    
    def test_data_services(self):
        print("\n--- 数据服务测试 ---")
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from app.services.page_data_service import (
                get_user_stats, get_exam_stats, get_course_stats,
                get_assignment_stats, get_notification_stats, get_system_stats,
                get_resource_stats, get_analysis_stats, get_auth_stats,
                get_path_stats, get_student_stats, get_planner_stats
            )
            
            stats_funcs = [
                (get_user_stats, '用户统计'),
                (get_exam_stats, '考试统计'),
                (get_course_stats, '课程统计'),
                (get_assignment_stats, '作业统计'),
                (get_notification_stats, '通知统计'),
                (get_system_stats, '系统统计'),
                (get_resource_stats, '资源统计'),
                (get_analysis_stats, '分析统计'),
                (get_auth_stats, '认证统计'),
                (get_path_stats, '路径统计'),
                (get_student_stats, '学生统计'),
                (get_planner_stats, '计划统计'),
            ]
            
            for func, name in stats_funcs:
                try:
                    result = func()
                    if isinstance(result, dict) and len(result) > 0:
                        self.add_result("数据服务", name, "PASS", 
                            f"返回 {len(result)} 个统计项")
                    else:
                        self.add_result("数据服务", name, "FAIL", "返回数据为空")
                except Exception as e:
                    self.add_result("数据服务", name, "ERROR", error=e)
        except Exception as e:
            self.add_result("数据服务", "模块导入", "ERROR", error=e)
    
    def test_template_rendering(self):
        print("\n--- 模板渲染测试 ---")
        templates = [
            ('/admin_app/dashboard', '管理首页'),
            ('/admin_app/users', '用户管理'),
            ('/admin_app/exams', '考试管理'),
            ('/admin_app/courses', '课程管理'),
        ]
        
        for path, name in templates:
            try:
                time.sleep(self.request_delay)
                resp = self.session.get(f"{BASE_URL}{path}", timeout=TIMEOUT)
                if resp.status_code == 200:
                    if 'html' in resp.headers.get('Content-Type', ''):
                        self.add_result("模板渲染", name, "PASS", "HTML渲染正常")
                    else:
                        self.add_result("模板渲染", name, "FAIL", "非HTML响应")
                else:
                    self.add_result("模板渲染", name, "FAIL", f"状态码: {resp.status_code}")
            except Exception as e:
                self.add_result("模板渲染", name, "ERROR", error=e)
    
    def run_all_tests(self):
        print("\n" + "="*80)
        print("MTSCOS AI 系统全面测试")
        print("="*80 + "\n")
        
        print("\n--- 1. 前端页面测试 ---")
        self.test_frontend_pages()
        
        print("\n--- 2. 管理员App页面测试 ---")
        self.test_admin_app_pages()
        
        print("\n--- 3. API端点测试 ---")
        self.test_all_apis()
        
        print("\n--- 4. 静态资源测试 ---")
        self.test_static_resources()
        
        print("\n--- 5. 数据库测试 ---")
        self.test_database_tables()
        
        print("\n--- 6. 数据服务测试 ---")
        self.test_data_services()
        
        print("\n--- 7. 模板渲染测试 ---")
        self.test_template_rendering()
        
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
                    print(f"  [{r.category}] {r.test_name}: {r.status} - {r.message or str(r.error)[:100]}")
        
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
            'failed_tests': [r.to_dict() for r in self.failed_tests]
        }
        
        report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_results.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n测试报告已保存: {report_path}")
        
        return report

if __name__ == "__main__":
    tester = MTSCOSTester()
    try:
        report = tester.run_all_tests()
    except Exception as e:
        print(f"\n测试执行异常: {e}")
        traceback.print_exc()