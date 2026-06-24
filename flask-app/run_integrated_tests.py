# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全自动测试运行器 - 集成测试AI、日志AI、自动修复上报
"""
import logging
logger = logging.getLogger(__name__)
import os
import sys
import sqlite3
from contextlib import contextmanager
import json
import requests
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'

sys.path.insert(0, PROJECT_ROOT)

from log_ai import LogAI, LogReporter
from test_ai_system import TestAI
from auto_fixer import AutoFixer

class IntegratedTestRunner:
    """集成测试运行器"""
    
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.base_url = 'http://localhost:8888'
        self.logger = LogAI()
        self.reporter = LogReporter()
        self.test_results = []
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
    def log(self, level: str, category: str, message: str, details: Dict = None):
        """统一日志记录"""
        self.logger.log(level, category, message, details)
    
    def run(self):
        """运行完整测试流程"""
        print("=" * 80)
        print("        全自动测试运行器 - 测试AI + 日志AI + 自动修复上报")
        print("=" * 80)
        print(f"会话ID: {self.session_id}")
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        self.reporter.report_system_event('测试开始', f'测试会话 {self.session_id} 开始', 'IntegratedTestRunner')
        
        try:
            self.step1_server_check()
            self.step2_database_check()
            self.step3_api_endpoints_check()
            self.step4_main_pages_check()
            self.step5_exam_system_check()
            self.step6_security_check()
            self.step7_file_organizer_check()
            self.step8_auto_fix()
            
            self.step9_save_test_session()
            self.step10_generate_report()
            
        except Exception as e:
            self.log('CRITICAL', '测试流程', f'测试流程异常终止: {str(e)}', {
                'exception': str(e),
                'traceback': traceback.format_exc()
            })
            self.reporter.report_test_anomaly(
                '测试流程',
                '流程异常',
                f'测试流程异常终止: {str(e)}',
                'high',
                {'traceback': traceback.format_exc()}
            )
        
        print("\n" + "=" * 80)
        print("                        测试流程完成!")
        print("=" * 80)
    
    def step1_server_check(self):
        """步骤1: 服务器状态检查"""
        print("\n" + "=" * 60)
        print("[步骤1] 服务器状态检查")
        print("=" * 60)
        
        self.log('INFO', '服务器检查', '开始服务器状态检查')
        
        try:
            response = requests.get(f'{self.base_url}/', timeout=5)
            if response.status_code == 200:
                self.log('INFO', '服务器检查', '服务器运行正常', {'status_code': 200})
                self.record_result('服务器状态', 'PASS', '服务器运行正常')
            else:
                self.log('WARNING', '服务器检查', f'服务器返回异常状态码: {response.status_code}', {'status_code': response.status_code})
                self.record_result('服务器状态', 'FAIL', f'返回状态码: {response.status_code}')
        except Exception as e:
            self.log('ERROR', '服务器检查', f'服务器连接失败: {str(e)}', {'exception': str(e)})
            self.record_result('服务器状态', 'FAIL', f'连接失败: {str(e)}')
            self.reporter.report_test_anomaly('服务器状态', '连接失败', str(e), 'high')
    
    def step2_database_check(self):
        """步骤2: 数据库连接检查"""
        print("\n" + "=" * 60)
        print("[步骤2] 数据库连接检查")
        print("=" * 60)
        
        self.log('INFO', '数据库检查', '开始数据库连接检查')
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn_cursor = conn.cursor()
                cursor = conn.cursor()
                cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
                tables = [row[0] for row in cursor.fetchall()]
                cursor.execute('SELECT COUNT(*) FROM sqlite_master')
            
            self.log('INFO', '数据库检查', f'数据库连接正常,包含 {len(tables)} 个表', {'tables': tables})
            self.record_result('数据库连接', 'PASS', f'包含 {len(tables)} 个表')
        except Exception as e:
            self.log('ERROR', '数据库检查', f'数据库连接失败: {str(e)}', {'exception': str(e)})
            self.record_result('数据库连接', 'FAIL', f'连接失败: {str(e)}')
            self.reporter.report_test_anomaly('数据库连接', '连接失败', str(e), 'high')
    
    def step3_api_endpoints_check(self):
        """步骤3: API端点检查"""
        print("\n" + "=" * 60)
        print("[步骤3] API端点检查")
        print("=" * 60)
        
        self.log('INFO', 'API检查', '开始API端点检查')
        
        endpoints = [
            '/api/file/categories',
            '/api/file/recommendations',
            '/api/exams',
            '/api/backup/status',
            '/api/system/stats',
            '/api/exam/start',
            '/api/file/fix-paths'
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f'{self.base_url}{endpoint}', timeout=10)
                if response.status_code == 200:
                    self.log('INFO', 'API检查', f'{endpoint} 正常', {'status_code': 200})
                    self.record_result(f'API {endpoint}', 'PASS', '正常')
                else:
                    self.log('WARNING', 'API检查', f'{endpoint} 返回异常状态码', {'endpoint': endpoint, 'status_code': response.status_code})
                    self.record_result(f'API {endpoint}', 'FAIL', f'状态码: {response.status_code}')
            except Exception as e:
                self.log('ERROR', 'API检查', f'{endpoint} 请求失败', {'endpoint': endpoint, 'exception': str(e)})
                self.record_result(f'API {endpoint}', 'FAIL', f'请求失败: {str(e)}')
    
    def step4_main_pages_check(self):
        """步骤4: 主要页面检查"""
        print("\n" + "=" * 60)
        print("[步骤4] 主要页面检查")
        print("=" * 60)
        
        self.log('INFO', '页面检查', '开始主要页面检查')
        
        pages = [
            '/exam_system',
            '/backup_manager',
            '/file_organizer',
            '/hardware_admin_dashboard',
            '/admin_center'
        ]
        
        for page in pages:
            try:
                response = requests.get(f'{self.base_url}{page}', timeout=10)
                if response.status_code == 200:
                    self.log('INFO', '页面检查', f'{page} 可访问', {'status_code': 200})
                    self.record_result(f'页面 {page}', 'PASS', '可访问')
                else:
                    self.log('WARNING', '页面检查', f'{page} 返回异常', {'page': page, 'status_code': response.status_code})
                    self.record_result(f'页面 {page}', 'FAIL', f'状态码: {response.status_code}')
            except Exception as e:
                self.log('ERROR', '页面检查', f'{page} 访问失败', {'page': page, 'exception': str(e)})
                self.record_result(f'页面 {page}', 'FAIL', f'访问失败')
    
    def step5_exam_system_check(self):
        """步骤5: 考试系统检查"""
        print("\n" + "=" * 60)
        print("[步骤5] 考试系统检查")
        print("=" * 60)
        
        self.log('INFO', '考试系统', '开始考试系统检查')
        
        try:
            response = requests.get(f'{self.base_url}/exam_system', timeout=10)
            if response.status_code == 200:
                if '考试' in response.text or 'exam' in response.text.lower():
                    self.log('INFO', '考试系统', '考试系统页面正常')
                    self.record_result('考试系统', 'PASS', '页面正常')
                else:
                    self.log('WARNING', '考试系统', '考试系统页面内容可能不完整')
                    self.record_result('考试系统', 'WARNING', '内容可能不完整')
            else:
                self.log('ERROR', '考试系统', '考试系统页面返回异常')
                self.record_result('考试系统', 'FAIL', f'状态码: {response.status_code}')
                self.reporter.report_test_anomaly('考试系统', '页面异常', f'返回状态码: {response.status_code}', 'medium')
        except Exception as e:
            self.log('ERROR', '考试系统', f'考试系统检查失败: {str(e)}')
            self.record_result('考试系统', 'FAIL', f'检查失败: {str(e)}')
            self.reporter.report_test_anomaly('考试系统', '检查失败', str(e), 'medium')
    
    def step6_security_check(self):
        """步骤6: 安全功能检查"""
        print("\n" + "=" * 60)
        print("[步骤6] 安全功能检查")
        print("=" * 60)
        
        self.log('INFO', '安全检查', '开始安全功能检查')
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn_cursor = conn.cursor()
                cursor = conn.cursor()
                
                security_tables = [
                't_aaef114130946f87',
                'login_attempts',
                'session_data',
                'permission_data'
                ]
                
                for table in security_tables:
                    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                    if cursor.fetchone():
                        self.log('INFO', '安全检查', f'安全表 {table} 存在')
                        self.record_result(f'安全-{table}', 'PASS', '存在')
                    else:
                        self.log('WARNING', '安全检查', f'安全表 {table} 不存在')
                        self.record_result(f'安全-{table}', 'WARNING', '不存在')
                
        except Exception as e:
            self.log('ERROR', '安全检查', f'安全检查失败: {str(e)}')
            self.record_result('安全检查', 'FAIL', f'检查失败: {str(e)}')
    
    def step7_file_organizer_check(self):
        """步骤7: 文件整理功能检查"""
        print("\n" + "=" * 60)
        print("[步骤7] 文件整理功能检查")
        print("=" * 60)
        
        self.log('INFO', '文件整理', '开始文件整理功能检查')
        
        try:
            response = requests.get(f'{self.base_url}/api/file/organize', timeout=120)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    output = data.get('output', '')
                    self.log('INFO', '文件整理', f'文件整理执行成功')
                    self.record_result('文件整理功能', 'PASS', '执行成功')
                else:
                    self.log('WARNING', '文件整理', f'文件整理执行失败: {data.get("message")}')
                    self.record_result('文件整理功能', 'FAIL', f"执行失败: {data.get('message')}")
            else:
                self.log('ERROR', '文件整理', f'文件整理请求失败,状态码: {response.status_code}')
                self.record_result('文件整理功能', 'FAIL', f'请求失败')
        except Exception as e:
            self.log('ERROR', '文件整理', f'文件整理执行异常: {str(e)}')
            self.record_result('文件整理功能', 'FAIL', f'执行异常: {str(e)}')
    
    def step8_auto_fix(self):
        """步骤8: 自动修复"""
        print("\n" + "=" * 60)
        print("[步骤8] 自动修复高优先级问题")
        print("=" * 60)
        
        self.log('INFO', '自动修复', '开始自动修复')
        
        try:
            fixer = AutoFixer()
            result = fixer.run()
            
            self.log('INFO', '自动修复', f'修复完成: 修复 {result["fixed"]} 项,跳过 {result["skipped"]} 项')
            self.record_result('自动修复', 'PASS', f'修复 {result["fixed"]} 项,跳过 {result["skipped"]} 项')
            
            self.reporter.report_system_event(
                '自动修复完成',
                f'修复 {result["fixed"]} 项,跳过 {result["skipped"]} 项',
                'AutoFixer',
                result
            )
        except Exception as e:
            self.log('ERROR', '自动修复', f'自动修复失败: {str(e)}')
            self.record_result('自动修复', 'FAIL', f'失败: {str(e)}')
    
    def step9_save_test_session(self):
        """步骤9: 保存测试会话"""
        print("\n" + "=" * 60)
        print("[步骤9] 保存测试会话到数据库")
        print("=" * 60)
        
        self.log('INFO', '会话保存', '开始保存测试会话')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
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
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_session_id TEXT,
                test_name TEXT,
                status TEXT,
                message TEXT,
                timestamp TEXT
            )
        ''')
        
        total = len(self.test_results)
        passed = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed = len([r for r in self.test_results if r['status'] == 'FAIL'])
        warnings = len([r for r in self.test_results if r['status'] == 'WARNING'])
        
        overall_status = 'PASS' if failed == 0 else ('WARNING' if warnings > 0 else 'FAIL')
        
        cursor.execute('''
            INSERT INTO test_sessions 
            (session_id, start_time, end_time, total_tests, pass_count, fail_count, warning_count, overall_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.session_id,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            total, passed, failed, warnings, overall_status
        ))
        
        for result in self.test_results:
            cursor.execute('''
                INSERT INTO test_results (test_session_id, test_name, status, message, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                self.session_id,
                result['test_name'],
                result['status'],
                result['message'],
                result['timestamp']
            ))
        
        conn.commit()
        conn.close()
        
        self.logger.flush_buffer()
        
        self.log('INFO', '会话保存', f'测试会话已保存: {self.session_id}', {
            'session_id': self.session_id,
            'total': total,
            'passed': passed,
            'failed': failed,
            'warnings': warnings
        })
        
        print(f"  会话ID: {self.session_id}")
        print(f"  总测试: {total}")
        print(f"  ✅ 通过: {passed}")
        print(f"  ❌ 失败: {failed}")
        print(f"  ⚠️ 警告: {warnings}")
    
    def step10_generate_report(self):
        """步骤10: 生成报告"""
        print("\n" + "=" * 60)
        print("[步骤10] 生成测试报告")
        print("=" * 60)
        
        self.log('INFO', '报告生成', '生成测试报告')
        
        report = {
            'session_id': self.session_id,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total': len(self.test_results),
                'passed': len([r for r in self.test_results if r['status'] == 'PASS']),
                'failed': len([r for r in self.test_results if r['status'] == 'FAIL']),
                'warnings': len([r for r in self.test_results if r['status'] == 'WARNING'])
            },
            'results': self.test_results
        }
        
        report_file = os.path.join(PROJECT_ROOT, f'test_report_{self.session_id}.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        self.log('INFO', '报告生成', f'测试报告已保存: {report_file}', {'report_file': report_file})
        
        anomaly_report = self.reporter.get_anomaly_report()
        
        print(f"\n📊 测试报告摘要:")
        print(f"  会话ID: {report['session_id']}")
        print(f"  生成时间: {report['generated_at']}")
        print(f"  总测试数: {report['summary']['total']}")
        print(f"  ✅ 通过: {report['summary']['passed']}")
        print(f"  ❌ 失败: {report['summary']['failed']}")
        print(f"  ⚠️ 警告: {report['summary']['warnings']}")
        print(f"  📁 报告文件: {report_file}")
        print(f"  📋 待处理异常: {anomaly_report['unresolved_count']}")
        
        self.reporter.report_system_event('测试完成', f'测试会话 {self.session_id} 完成', 'IntegratedTestRunner', report['summary'])
    
    def record_result(self, test_name: str, status: str, message: str):
        """记录测试结果"""
        self.test_results.append({
            'test_name': test_name,
            'status': status,
            'message': message,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

if __name__ == '__main__':
    runner = IntegratedTestRunner()
    runner.run()