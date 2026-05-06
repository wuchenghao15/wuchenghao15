#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AI系统 - 全自动测试系统功能并记录结果
"""
import os
import sys
import sqlite3
import json
import requests
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'

class TestAI:
    """测试AI系统"""
    
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.base_url = 'http://localhost:8888'
        self.test_results = []
        self.test_count = 0
        self.pass_count = 0
        self.fail_count = 0
        self.warning_count = 0
        
    def log_test(self, test_name: str, status: str, message: str, details: Optional[Dict] = None):
        """记录测试结果"""
        self.test_results.append({
            'test_name': test_name,
            'status': status,
            'message': message,
            'details': details or {},
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        self.test_count += 1
        if status == 'PASS':
            self.pass_count += 1
            print(f"  ✅ {test_name}: {message}")
        elif status == 'FAIL':
            self.fail_count += 1
            print(f"  ❌ {test_name}: {message}")
        else:
            self.warning_count += 1
            print(f"  ⚠️ {test_name}: {message}")
    
    def test_server_status(self):
        """测试服务器状态"""
        print("\n[测试1] 服务器状态测试...")
        try:
            response = requests.get(f'{self.base_url}/', timeout=5)
            if response.status_code == 200:
                self.log_test('服务器状态', 'PASS', '服务器运行正常')
            else:
                self.log_test('服务器状态', 'FAIL', f'服务器返回状态码: {response.status_code}')
        except Exception as e:
            self.log_test('服务器状态', 'FAIL', f'服务器连接失败: {str(e)}')
    
    def test_database_connection(self):
        """测试数据库连接"""
        print("\n[测试2] 数据库连接测试...")
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM sqlite_master')
            cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            self.log_test('数据库连接', 'PASS', f'数据库连接正常，包含 {len(tables)} 个表')
        except Exception as e:
            self.log_test('数据库连接', 'FAIL', f'数据库连接失败: {str(e)}')
    
    def test_api_endpoints(self):
        """测试API端点"""
        print("\n[测试3] API端点测试...")
        
        endpoints = [
            ('/api/file/categories', 'GET'),
            ('/api/file/recommendations', 'GET'),
            ('/api/exams', 'GET'),
            ('/api/backup/status', 'GET'),
            ('/api/system/stats', 'GET'),
        ]
        
        for endpoint, method in endpoints:
            try:
                response = requests.request(method, f'{self.base_url}{endpoint}', timeout=10)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        self.log_test(f'API {endpoint}', 'PASS', f'返回状态码: {response.status_code}')
                    except:
                        self.log_test(f'API {endpoint}', 'WARNING', f'返回非JSON格式')
                else:
                    self.log_test(f'API {endpoint}', 'FAIL', f'返回状态码: {response.status_code}')
            except Exception as e:
                self.log_test(f'API {endpoint}', 'FAIL', f'请求失败: {str(e)}')
    
    def test_file_organizer(self):
        """测试文件整理功能"""
        print("\n[测试4] 文件整理功能测试...")
        try:
            response = requests.get(f'{self.base_url}/api/file/organize', timeout=60)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_test('文件整理功能', 'PASS', '文件整理执行成功')
                else:
                    self.log_test('文件整理功能', 'FAIL', f"执行失败: {data.get('message')}")
            else:
                self.log_test('文件整理功能', 'FAIL', f'返回状态码: {response.status_code}')
        except Exception as e:
            self.log_test('文件整理功能', 'FAIL', f'执行失败: {str(e)}')
    
    def test_exam_system(self):
        """测试考试系统"""
        print("\n[测试5] 考试系统测试...")
        try:
            response = requests.get(f'{self.base_url}/exam_system', timeout=10)
            if response.status_code == 200:
                if '考试系统' in response.text or 'exam' in response.text.lower():
                    self.log_test('考试系统', 'PASS', '考试系统页面可正常访问')
                else:
                    self.log_test('考试系统', 'WARNING', '页面返回但内容可能不完整')
            else:
                self.log_test('考试系统', 'FAIL', f'返回状态码: {response.status_code}')
        except Exception as e:
            self.log_test('考试系统', 'FAIL', f'访问失败: {str(e)}')
    
    def test_backup_manager(self):
        """测试备份管理器"""
        print("\n[测试6] 备份管理器测试...")
        try:
            response = requests.get(f'{self.base_url}/backup_manager', timeout=10)
            if response.status_code == 200:
                self.log_test('备份管理器', 'PASS', '备份管理器页面可正常访问')
            else:
                self.log_test('备份管理器', 'FAIL', f'返回状态码: {response.status_code}')
        except Exception as e:
            self.log_test('备份管理器', 'FAIL', f'访问失败: {str(e)}')
    
    def test_login_system(self):
        """测试登录系统"""
        print("\n[测试7] 登录系统测试...")
        try:
            response = requests.post(
                f'{self.base_url}/auth/login',
                json={'username': 'wuchenghao15', 'password': 'LoginMe.1988'},
                timeout=10
            )
            if response.status_code in [200, 401, 302]:
                self.log_test('登录系统', 'PASS', '登录接口可正常访问')
            else:
                self.log_test('登录系统', 'FAIL', f'返回状态码: {response.status_code}')
        except Exception as e:
            self.log_test('登录系统', 'FAIL', f'访问失败: {str(e)}')
    
    def test_ai_modules(self):
        """测试AI模块"""
        print("\n[测试8] AI模块测试...")
        
        ai_modules = [
            ('app.ai.question_generator', '题目生成AI'),
            ('app.ai.audio_manager', '音频管理AI'),
            ('app.ai.exam_expert_generator', '考试专家AI'),
        ]
        
        for module_name, module_desc in ai_modules:
            try:
                module_path = os.path.join(PROJECT_ROOT, module_name.replace('.', '/') + '.py')
                if os.path.exists(module_path):
                    self.log_test(f'AI模块-{module_desc}', 'PASS', f'模块文件存在')
                else:
                    self.log_test(f'AI模块-{module_desc}', 'WARNING', f'模块文件不存在')
            except Exception as e:
                self.log_test(f'AI模块-{module_desc}', 'FAIL', f'检查失败: {str(e)}')
    
    def test_security_features(self):
        """测试安全功能"""
        print("\n[测试9] 安全功能测试...")
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='t_aaef114130946f87'")
            if cursor.fetchone():
                self.log_test('安全-加密表', 'PASS', '加密用户表存在')
            else:
                self.log_test('安全-加密表', 'WARNING', '加密用户表不存在')
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='login_attempts'")
            if cursor.fetchone():
                self.log_test('安全-登录限制', 'PASS', '登录尝试限制表存在')
            else:
                self.log_test('安全-登录限制', 'WARNING', '登录尝试限制表不存在')
            
            conn.close()
        except Exception as e:
            self.log_test('安全功能', 'FAIL', f'检查失败: {str(e)}')
    
    def test_path_fixer(self):
        """测试路径修复功能"""
        print("\n[测试10] 路径修复功能测试...")
        try:
            response = requests.get(f'{self.base_url}/api/file/fix-paths', timeout=60)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_test('路径修复功能', 'PASS', '路径修复执行成功')
                else:
                    self.log_test('路径修复功能', 'FAIL', f"执行失败: {data.get('message')}")
            else:
                self.log_test('路径修复功能', 'FAIL', f'返回状态码: {response.status_code}')
        except Exception as e:
            self.log_test('路径修复功能', 'FAIL', f'执行失败: {str(e)}')
    
    def save_test_results(self):
        """保存测试结果到数据库"""
        print("\n[保存] 正在保存测试结果到数据库...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_name TEXT,
                status TEXT,
                message TEXT,
                details TEXT,
                timestamp TEXT,
                test_session_id TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE,
                start_time TEXT,
                end_time TEXT,
                total_tests INTEGER,
                pass_count INTEGER,
                fail_count INTEGER,
                warning_count INTEGER,
                overall_status TEXT
            )
        ''')
        
        session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        overall_status = 'PASS'
        if self.fail_count > 0:
            overall_status = 'FAIL'
        elif self.warning_count > 0:
            overall_status = 'WARNING'
        
        cursor.execute('''
            INSERT INTO test_sessions 
            (session_id, start_time, total_tests, pass_count, fail_count, warning_count, overall_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id,
            self.test_results[0]['timestamp'] if self.test_results else datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            self.test_count,
            self.pass_count,
            self.fail_count,
            self.warning_count,
            overall_status
        ))
        
        for result in self.test_results:
            cursor.execute('''
                INSERT INTO test_results 
                (test_name, status, message, details, timestamp, test_session_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                result['test_name'],
                result['status'],
                result['message'],
                json.dumps(result['details'], ensure_ascii=False),
                result['timestamp'],
                session_id
            ))
        
        conn.commit()
        conn.close()
        
        print(f"  已保存 {self.test_count} 条测试结果")
        return session_id
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 70)
        print("                    测试AI系统 - 全自动系统测试")
        print("=" * 70)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"测试地址: {self.base_url}")
        print("=" * 70)
        
        self.test_server_status()
        self.test_database_connection()
        self.test_api_endpoints()
        self.test_exam_system()
        self.test_backup_manager()
        self.test_login_system()
        self.test_ai_modules()
        self.test_security_features()
        self.test_file_organizer()
        self.test_path_fixer()
        
        session_id = self.save_test_results()
        
        print("\n" + "=" * 70)
        print("                    测试完成！")
        print("=" * 70)
        print(f"总会话ID: {session_id}")
        print(f"总测试数: {self.test_count}")
        print(f"✅ 通过: {self.pass_count}")
        print(f"❌ 失败: {self.fail_count}")
        print(f"⚠️ 警告: {self.warning_count}")
        print("=" * 70)
        
        return {
            'session_id': session_id,
            'total': self.test_count,
            'passed': self.pass_count,
            'failed': self.fail_count,
            'warnings': self.warning_count,
            'results': self.test_results
        }

if __name__ == '__main__':
    tester = TestAI()
    result = tester.run_all_tests()
    print(json.dumps(result, ensure_ascii=False, indent=2))