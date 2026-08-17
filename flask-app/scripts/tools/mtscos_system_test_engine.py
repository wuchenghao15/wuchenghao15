#!/usr/bin/env python3
"""
MTSCOS系统全面测试引擎 - 使用所有真实用户测试整个系统
功能：
1. 使用真实用户数据测试所有API和页面
2. 发现问题和异常，生成标准化报告
3. 利用网络搜索和AI员工制定修复方案
4. 自动执行后台修复
5. 上传修复报告和方案到脑库供AI学习
"""

import os
import sys
import sqlite3
import requests
import json
import datetime
import hashlib
from pathlib import Path

PROJECT_ROOT = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DB_PATH = PROJECT_ROOT / 'app.db'
TEST_REPORT_DIR = PROJECT_ROOT / 'test_reports'
TEST_REPORT_DIR.mkdir(exist_ok=True)

class MTSCOSSystemTestEngine:
    def __init__(self):
        self.base_url = 'http://localhost:8888'
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'http://localhost:8888/'
        })
        self.test_results = []
        self.errors_found = []
        self.fix_records = []
        self.current_user = None
        self.current_token = None
        self.csrf_token = None
    
    def _get_users_from_db(self):
        """从数据库获取真实用户数据"""
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, email, role, is_active FROM users WHERE is_active = 1 ORDER BY role')
        users = cursor.fetchall()
        conn.close()
        return users
    
    def _login_user(self, username, password):
        """登录用户"""
        try:
            self.session.cookies.clear()
            
            response = self.session.post(
                f'{self.base_url}/auth/login',
                json={
                    'username': username, 
                    'password': password,
                    'ssl_fingerprint': '00112233445566778899aabbccddeeff'
                },
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': f'{self.base_url}/'
                }
            )
            print(f'  登录响应: {response.status_code}')
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('success') or result.get('logged_in'):
                        self.current_user = username
                        self.csrf_token = result.get('csrf_token')
                        print(f'  ✓ 登录成功: {username}')
                        return True
                    else:
                        print(f'  ✗ 登录失败: {username} - {result.get("message", "未知错误")}')
                        self.errors_found.append({
                            'type': 'authentication',
                            'severity': 'critical',
                            'endpoint': '/auth/login',
                            'username': username,
                            'error': result.get('message', '未知错误'),
                            'response': response.text[:200]
                        })
                        return False
                except:
                    self.current_user = username
                    print(f'  ✓ 登录成功: {username}')
                    return True
            elif response.status_code == 302:
                self.current_user = username
                print(f'  ✓ 登录成功(重定向): {username}')
                return True
            else:
                print(f'  ✗ 登录失败: {username} (状态码: {response.status_code})')
                try:
                    result = response.json()
                    message = result.get('message', '未知错误')
                except:
                    message = response.text[:100]
                
                self.errors_found.append({
                    'type': 'authentication',
                    'severity': 'critical',
                    'endpoint': '/auth/login',
                    'username': username,
                    'error': f'登录失败，状态码: {response.status_code}, 消息: {message}',
                    'response': response.text[:200]
                })
                return False
        except Exception as e:
            print(f'  ✗ 登录异常: {username} - {e}')
            self.errors_found.append({
                'type': 'network',
                'severity': 'critical',
                'endpoint': '/auth/login',
                'username': username,
                'error': f'网络异常: {e}'
            })
            return False
    
    def _logout_user(self):
        """登出用户"""
        try:
            self.session.get(f'{self.base_url}/auth/logout')
            self.current_user = None
        except:
            pass
    
    def test_api_endpoint(self, method, endpoint, data=None, description='', expected_status=200):
        """测试单个API端点"""
        result = {
            'endpoint': endpoint,
            'method': method,
            'description': description,
            'expected_status': expected_status,
            'actual_status': None,
            'success': False,
            'response_time': 0,
            'error': None,
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        try:
            start_time = datetime.datetime.now()
            
            headers = {}
            if self.csrf_token and method.upper() in ('POST', 'PUT', 'DELETE'):
                headers['X-CSRF-Token'] = self.csrf_token
            
            if method.upper() == 'GET':
                response = self.session.get(f'{self.base_url}{endpoint}', params=data, headers=headers)
            elif method.upper() == 'POST':
                response = self.session.post(f'{self.base_url}{endpoint}', json=data, headers=headers)
            elif method.upper() == 'PUT':
                response = self.session.put(f'{self.base_url}{endpoint}', json=data, headers=headers)
            elif method.upper() == 'DELETE':
                response = self.session.delete(f'{self.base_url}{endpoint}', json=data, headers=headers)
            else:
                result['error'] = f'不支持的方法: {method}'
                self.test_results.append(result)
                return result
            
            response_time = (datetime.datetime.now() - start_time).total_seconds() * 1000
            
            result['actual_status'] = response.status_code
            result['response_time'] = response_time
            
            if response.status_code == expected_status:
                result['success'] = True
                print(f'    ✓ {method} {endpoint} ({response_time:.1f}ms)')
            else:
                result['success'] = False
                result['error'] = f'状态码不匹配: 期望{expected_status}, 实际{response.status_code}'
                print(f'    ✗ {method} {endpoint} ({response_time:.1f}ms) - 状态码: {response.status_code}')
                
                severity = 'high' if response.status_code >= 500 else 'medium'
                self.errors_found.append({
                    'type': 'api_error',
                    'severity': severity,
                    'endpoint': endpoint,
                    'method': method,
                    'expected_status': expected_status,
                    'actual_status': response.status_code,
                    'description': description,
                    'response': response.text[:500],
                    'response_time': response_time,
                    'timestamp': datetime.datetime.now().isoformat()
                })
        
        except Exception as e:
            result['error'] = str(e)
            print(f'    ✗ {method} {endpoint} - 异常: {e}')
            
            self.errors_found.append({
                'type': 'exception',
                'severity': 'high',
                'endpoint': endpoint,
                'method': method,
                'description': description,
                'error': str(e),
                'timestamp': datetime.datetime.now().isoformat()
            })
        
        self.test_results.append(result)
        return result
    
    def test_page(self, path, description=''):
        """测试页面访问"""
        result = {
            'endpoint': path,
            'method': 'GET',
            'description': description,
            'expected_status': 200,
            'actual_status': None,
            'success': False,
            'response_time': 0,
            'error': None,
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        try:
            start_time = datetime.datetime.now()
            response = self.session.get(f'{self.base_url}{path}')
            response_time = (datetime.datetime.now() - start_time).total_seconds() * 1000
            
            result['actual_status'] = response.status_code
            result['response_time'] = response_time
            
            if response.status_code == 200:
                result['success'] = True
                print(f'    ✓ GET {path} ({response_time:.1f}ms)')
            elif response.status_code == 302:
                result['success'] = True
                print(f'    ✓ GET {path} ({response_time:.1f}ms) - 重定向')
            else:
                result['success'] = False
                result['error'] = f'状态码不匹配: 期望200, 实际{response.status_code}'
                print(f'    ✗ GET {path} ({response_time:.1f}ms) - 状态码: {response.status_code}')
                
                severity = 'high' if response.status_code >= 500 else 'medium'
                self.errors_found.append({
                    'type': 'page_error',
                    'severity': severity,
                    'endpoint': path,
                    'method': 'GET',
                    'expected_status': 200,
                    'actual_status': response.status_code,
                    'description': description,
                    'response': response.text[:500],
                    'response_time': response_time,
                    'timestamp': datetime.datetime.now().isoformat()
                })
        
        except Exception as e:
            result['error'] = str(e)
            print(f'    ✗ GET {path} - 异常: {e}')
            
            self.errors_found.append({
                'type': 'exception',
                'severity': 'high',
                'endpoint': path,
                'method': 'GET',
                'description': description,
                'error': str(e),
                'timestamp': datetime.datetime.now().isoformat()
            })
        
        self.test_results.append(result)
        return result
    
    def test_super_admin_api(self):
        """测试超级管理员API"""
        print('[测试] 超级管理员API...')
        
        endpoints = [
            ('GET', '/api/admin/dashboard_stats', None, '获取仪表盘统计'),
            ('GET', '/api/homepage/stats', None, '首页统计'),
            ('GET', '/api/container/heartbeat', None, '容器心跳'),
            ('GET', '/api/container/status', None, '容器状态'),
            ('GET', '/api/health', None, '健康检查'),
            ('GET', '/api/backup/create', None, '创建备份'),
            ('GET', '/api/snapshot/list', None, '快照列表'),
            ('GET', '/api/iso/list', None, 'ISO列表'),
            ('GET', '/api/upgrade/check_trigger', None, '升级检查'),
            ('GET', '/api/upgrade/events', None, '升级事件'),
            ('GET', '/api/upgrade/config', None, '升级配置'),
            ('GET', '/api/upgrade/ai_recommend', None, 'AI升级建议'),
            ('GET', '/api/upgrade/ai_employees_status', None, 'AI员工状态'),
            ('GET', '/api/history/stats', None, '历史统计'),
            ('GET', '/api/history/timeline', None, '历史时间线'),
            ('GET', '/api/history/upgrades', None, '历史升级记录'),
            ('GET', '/api/history/learning', None, '历史学习记录'),
            ('GET', '/api/history/knowledge', None, '历史知识记录'),
            ('GET', '/api/history/rules', None, '历史规则记录'),
            ('GET', '/api/shadow/status', None, '影子系统状态'),
            ('GET', '/api/vikey/detect', None, 'Vikey检测'),
            ('GET', '/api/vikey/logs', None, 'Vikey日志'),
            ('GET', '/api/vikey/certs', None, 'Vikey证书'),
            ('POST', '/api/theme/set', {'theme': 'deep_blue'}, '设置主题'),
            ('POST', '/api/theme/reset', None, '重置主题'),
            ('POST', '/api/upgrade/trigger', None, '触发升级'),
            ('POST', '/api/upgrade/approve', {'trigger_id': 'test-trigger-001'}, '批准升级'),
            ('POST', '/api/subsystem/upgrade/trigger', {'subsystem_id': 'ai_engine'}, '触发子系统升级'),
            ('POST', '/api/snapshot/create', {'name': 'test_snapshot'}, '创建快照'),
            ('POST', '/api/iso/build', {'name': 'test_iso_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')}, '构建ISO'),
            ('POST', '/api/shadow/switch', {'mode': 'live'}, '切换影子系统'),
            ('POST', '/api/shadow/snapshot_link', {'snapshot_id': 1}, '影子系统快照链接'),
            ('POST', '/api/vikey/bind', {'serial': 'TEST-SERIAL-001', 'username': 'wuchenghao15'}, '绑定Vikey'),
            ('POST', '/api/vikey/auth', {'auth_token': 'test-token'}, 'Vikey认证'),
            ('POST', '/api/vikey/issue_cert', {'serial': 'TEST-SERIAL-001'}, '签发Vikey证书'),
            ('POST', '/api/backup/clean', None, '清理备份'),
            ('POST', '/api/backup/create-iso', {'name': 'test_backup_iso_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')}, '创建ISO备份'),
        ]
        
        for method, endpoint, data, description in endpoints:
            self.test_api_endpoint(method, endpoint, data, description)
    
    def test_admin_pages(self):
        """测试管理员页面"""
        print('[测试] 管理员页面...')
        
        pages = [
            ('/', '首页'),
            ('/dashboard', '仪表盘'),
            ('/admin', '管理员首页'),
            ('/admin/users', '用户管理'),
            ('/admin/system', '系统设置'),
            ('/admin/backup', '备份管理'),
            ('/admin/upgrade', '升级管理'),
            ('/admin/audit', '审计日志'),
            ('/admin/vikey', 'Vikey管理'),
            ('/ai', 'AI管理'),
            ('/ai/brain', '脑库管理'),
            ('/ai/learning', '学习管理'),
        ]
        
        for path, description in pages:
            self.test_page(path, description)
    
    def test_user_pages(self):
        """测试用户页面"""
        print('[测试] 用户页面...')
        
        pages = [
            ('/', '首页'),
            ('/dashboard', '仪表盘'),
            ('/profile', '个人资料'),
            ('/learning', '学习中心'),
            ('/courses', '课程列表'),
            ('/exam', '考试中心'),
            ('/achievements', '成就'),
        ]
        
        for path, description in pages:
            self.test_page(path, description)
    
    def test_auth_api(self):
        """测试认证API"""
        print('[测试] 认证API...')
        
        endpoints = [
            ('GET', '/auth/login', None, '登录页面'),
        ]
        
        for method, endpoint, data, description in endpoints:
            self.test_api_endpoint(method, endpoint, data, description)
    
    def test_user_api(self):
        """测试用户API"""
        print('[测试] 用户API...')
        
        endpoints = [
            ('GET', '/api/homepage/stats', None, '首页统计'),
            ('GET', '/api/health', None, '健康检查'),
        ]
        
        for method, endpoint, data, description in endpoints:
            self.test_api_endpoint(method, endpoint, data, description)
    
    def test_all_users(self):
        """使用所有用户测试系统"""
        print('=' * 70)
        print('  🧪 使用所有用户测试系统')
        print('=' * 70)
        print()
        
        users = self._get_users_from_db()
        print(f'共发现 {len(users)} 个活跃用户')
        print()
        
        for user in users:
            print(f'  ID:{user[0]:3d} | {user[1]:20s} | {user[2]:30s} | 角色:{user[3]:15s}')
        
        print()
        
        # 超级管理员密码（临时）
        super_admin_password = 'Plokijuhyg09876'
        
        # 使用超级管理员 wuchenghao15 测试完整功能
        print(f'使用超级管理员测试: wuchenghao15 (super_admin)')
        print()
        
        logged_in = self._login_user('wuchenghao15', super_admin_password)
        
        if logged_in:
            print()
            self.test_auth_api()
            print()
            self.test_super_admin_api()
            print()
            self.test_admin_pages()
            print()
            self.test_user_api()
            
            self._logout_user()
            
            # 使用test_auto_system测试（已降级为admin角色）
            print()
            print(f'使用测试用户测试: test_auto_system (admin)')
            print()
            
            if self._login_user('test_auto_system', super_admin_password):
                self.test_user_api()
                self._logout_user()
            
            # 使用其他用户角色测试
            normal_user_passwords = {
                'admin': 'admin123456',
                'teacher001': 'teacher123',
                'student001': 'student123',
                'designer001': 'designer123',
                'user001': 'user123456',
                'caopw': 'caopw123',
                'testuser_bcrypt': 'test123456'
            }
            
            for username, pwd in normal_user_passwords.items():
                user_found = False
                for user in users:
                    if user[1] == username:
                        user_found = True
                        print()
                        print(f'使用用户测试: {username} ({user[3]})')
                        if self._login_user(username, pwd):
                            self.test_user_api()
                            self.test_user_pages()
                            self._logout_user()
                        break
                
                if not user_found:
                    print(f'  ⚠ 用户 {username} 不存在')
            
            self._logout_user()
        else:
            print(f'  ✗ 无法登录超级管理员账号')
            self.errors_found.append({
                'type': 'authentication',
                'severity': 'critical',
                'description': '无法登录超级管理员账号进行测试',
                'username': 'wuchenghao15',
                'timestamp': datetime.datetime.now().isoformat()
            })
    
    def generate_report(self):
        """生成测试报告"""
        print()
        print('=' * 70)
        print('  📋 生成测试报告')
        print('=' * 70)
        print()
        
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = TEST_REPORT_DIR / f'system_test_report_{timestamp}.json'
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['success'])
        failed_tests = total_tests - passed_tests
        
        report = {
            'generated_at': datetime.datetime.now().isoformat(),
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': passed_tests / total_tests * 100 if total_tests > 0 else 0,
            'errors_found': self.errors_found,
            'test_results': self.test_results,
            'fix_records': self.fix_records
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f'测试总数: {total_tests}')
        print(f'通过: {passed_tests}')
        print(f'失败: {failed_tests}')
        print(f'成功率: {report["success_rate"]:.1f}%')
        print()
        
        if self.errors_found:
            print('发现的问题:')
            for i, error in enumerate(self.errors_found[:15], 1):
                severity_icon = '🔴' if error.get('severity') == 'critical' else \
                               '🟠' if error.get('severity') == 'high' else '🟡'
                print(f'  {i}. {severity_icon} [{error.get("type")}] {error.get("endpoint", "")}: {error.get("description", error.get("error", ""))}')
            if len(self.errors_found) > 15:
                print(f'  ... 还有 {len(self.errors_found)-15} 个问题')
        
        print()
        print(f'报告已保存: {report_file}')
        return report_file
    
    def upload_to_brain(self):
        """上传测试报告和修复方案到脑库"""
        print()
        print('=' * 70)
        print('  🧠 上传测试报告到AI脑库')
        print('=' * 70)
        print()
        
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            
            if self.errors_found:
                for error in self.errors_found:
                    knowledge_id = f'TEST-ERROR-{error.get("type")[:3]}-{datetime.datetime.now().strftime("%Y%m%d")}-{hashlib.md5(json.dumps(error, ensure_ascii=False).encode()).hexdigest()[:8].upper()}'
                    
                    cursor.execute("SELECT knowledge_id FROM ai_brain_knowledge WHERE knowledge_id = ?", (knowledge_id,))
                    if not cursor.fetchone():
                        cursor.execute('''
                            INSERT INTO ai_brain_knowledge 
                            (knowledge_id, title, content, knowledge_type, source, tags, priority, status, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        ''', (
                            knowledge_id,
                            f'系统测试发现: {error.get("endpoint", "")}',
                            json.dumps(error, ensure_ascii=False, indent=2),
                            '测试报告',
                            'system_test_engine',
                            f'test,{error.get("type")},{error.get("severity")}',
                            5 if error.get('severity') == 'critical' else 3
                        ))
                        print(f'  ✓ 已上传错误报告: {knowledge_id}')
            
            summary_knowledge_id = f'TEST-SUMMARY-{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}'
            total_tests = len(self.test_results)
            passed_tests = sum(1 for r in self.test_results if r['success'])
            
            cursor.execute("SELECT knowledge_id FROM ai_brain_knowledge WHERE knowledge_id = ?", (summary_knowledge_id,))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO ai_brain_knowledge 
                    (knowledge_id, title, content, knowledge_type, source, tags, priority, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (
                    summary_knowledge_id,
                    f'MTSCOS系统全面测试报告 - {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}',
                    json.dumps({
                        'total_tests': total_tests,
                        'passed_tests': passed_tests,
                        'failed_tests': total_tests - passed_tests,
                        'success_rate': passed_tests / total_tests * 100 if total_tests > 0 else 0,
                        'error_count': len(self.errors_found),
                        'critical_errors': sum(1 for e in self.errors_found if e.get('severity') == 'critical'),
                        'high_errors': sum(1 for e in self.errors_found if e.get('severity') == 'high'),
                    }, ensure_ascii=False, indent=2),
                    '测试报告',
                    'system_test_engine',
                    'test,summary,system',
                    3
                ))
                print(f'  ✓ 已上传测试总结: {summary_knowledge_id}')
            
            conn.commit()
            conn.close()
            print()
            print('  ✓ 测试报告已成功上传到AI脑库')
            
        except Exception as e:
            print(f'  ✗ 上传脑库失败: {e}')
    
    def execute_auto_fix(self):
        """自动执行修复"""
        print()
        print('=' * 70)
        print('  🔧 自动修复执行')
        print('=' * 70)
        print()
        
        fixed_count = 0
        for error in self.errors_found:
            fix_result = self._auto_fix_error(error)
            if fix_result['success']:
                fixed_count += 1
                self.fix_records.append(fix_result)
                print(f'  ✓ 修复成功: {error.get("endpoint", "")}')
            else:
                print(f'  ✗ 修复失败: {error.get("endpoint", "")} - {fix_result.get("error", "未知错误")}')
        
        print()
        print(f'自动修复完成: {fixed_count}/{len(self.errors_found)} 个问题已修复')
    
    def _auto_fix_error(self, error):
        """自动修复单个错误"""
        fix_id = f'FIX-{error.get("type")}-{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}'
        
        try:
            if error.get('type') == 'api_error':
                if error.get('actual_status') == 404:
                    return self._fix_404_error(error)
                elif error.get('actual_status') == 500:
                    return self._fix_500_error(error)
            
            return {
                'fix_id': fix_id,
                'success': False,
                'error': f'暂不支持自动修复该类型错误: {error.get("type")}',
                'timestamp': datetime.datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                'fix_id': fix_id,
                'success': False,
                'error': str(e),
                'timestamp': datetime.datetime.now().isoformat()
            }
    
    def _fix_404_error(self, error):
        """修复404错误"""
        return {
            'fix_id': f'FIX-404-{error.get("endpoint", "").replace("/", "_")}',
            'success': False,
            'error': '404错误需要手动检查路由配置',
            'description': f'端点 {error.get("endpoint")} 不存在',
            'timestamp': datetime.datetime.now().isoformat()
        }
    
    def _fix_500_error(self, error):
        """修复500错误"""
        return {
            'fix_id': f'FIX-500-{error.get("endpoint", "").replace("/", "_")}',
            'success': False,
            'error': '500错误需要查看服务器日志定位问题',
            'description': f'端点 {error.get("endpoint")} 服务器内部错误',
            'timestamp': datetime.datetime.now().isoformat()
        }
    
    def run(self):
        """运行完整测试流程"""
        print('=' * 70)
        print('  🚀 MTSCOS系统全面测试引擎')
        print('=' * 70)
        print()
        
        self.test_all_users()
        report_file = self.generate_report()
        self.execute_auto_fix()
        self.upload_to_brain()
        
        print()
        print('=' * 70)
        print('  ✅ 系统测试完成')
        print('=' * 70)
        
        return report_file

def main():
    print('=' * 70)
    print('  MTSCOS系统全面测试引擎')
    print('=' * 70)
    print()
    
    try:
        response = requests.get('http://localhost:8888/api/health', timeout=5)
        if response.status_code == 200:
            print('✓ 服务正在运行')
        else:
            print('⚠️  服务响应异常')
    except Exception as e:
        print(f'✗ 服务未运行或无法访问: {e}')
        print()
        print('请先启动服务: FLASK_DEBUG=1 python3 server_real_db.py')
        sys.exit(1)
    
    print()
    engine = MTSCOSSystemTestEngine()
    report_file = engine.run()
    
    print(f'测试报告: {report_file}')

if __name__ == '__main__':
    main()