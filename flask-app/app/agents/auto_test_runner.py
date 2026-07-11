# -*- coding: utf-8 -*-
"""
自动化测试框架 - 单元测试、接口测试、页面校验、压测
测试结果上报数据库，与灰度发布系统联动
"""
import os
import json
import logging
import threading
import time
import subprocess
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class TestType(Enum):
    UNIT = 'unit'
    API = 'api'
    PAGE = 'page'
    STRESS = 'stress'


class AutoTestRunner:
    """自动化测试运行器"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._lock = threading.Lock()
        self._test_results: Dict[str, Dict] = {}
        from app.utils.db import DatabaseManager
        db = DatabaseManager()
        self._db_path = db.db_path
        
        self._api_endpoints = [
            '/api/auth/login',
            '/api/users/current',
            '/api/monitoring/health',
            '/api/monitoring/system',
            '/api/core-agents/agents',
            '/api/rule/engine/status',
            '/api/release/health',
            '/api/version/info'
        ]
        
        self._page_urls = [
            '/',
            '/exam_system',
            '/test_system',
            '/learning_system',
            '/admin_center'
        ]
        
        self._init_database()
        
        self._initialized = True
    
    def _init_database(self):
        """初始化数据库表"""
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_results (
                    test_id TEXT PRIMARY KEY,
                    test_type TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'running',
                    total_tests INTEGER DEFAULT 0,
                    passed_tests INTEGER DEFAULT 0,
                    failed_tests INTEGER DEFAULT 0,
                    skipped_tests INTEGER DEFAULT 0,
                    duration REAL DEFAULT 0,
                    error_rate REAL DEFAULT 0,
                    avg_response_time REAL DEFAULT 0,
                    max_response_time REAL DEFAULT 0,
                    throughput INTEGER DEFAULT 0,
                    details TEXT DEFAULT '{}',
                    created_at TEXT,
                    completed_at TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_details (
                    detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_id TEXT NOT NULL,
                    test_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    duration REAL DEFAULT 0,
                    error_message TEXT DEFAULT '',
                    response_code INTEGER DEFAULT 0,
                    response_time REAL DEFAULT 0,
                    FOREIGN KEY (test_id) REFERENCES test_results (test_id)
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("[测试框架] 数据库表初始化完成")
        except Exception as e:
            logger.error(f"[测试框架] 初始化数据库失败: {e}")
    
    def run_unit_tests(self, test_path: str = None) -> Dict:
        """运行单元测试"""
        test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}_unit"
        
        result = {
            'test_id': test_id,
            'test_type': 'unit',
            'status': 'running',
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'skipped_tests': 0,
            'duration': 0,
            'details': []
        }
        
        self._save_test_result(result)
        
        start_time = time.time()
        
        try:
            if test_path:
                cmd = ['python3', '-m', 'pytest', test_path, '-v', '--tb=short']
            else:
                cmd = ['python3', '-m', 'pytest', 'tests/', '-v', '--tb=short']
            
            result_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            result = subprocess.run(cmd, cwd=result_path, capture_output=True, 
                                  text=True, timeout=120)
            
            total = passed = failed = skipped = 0
            details = []
            
            for line in result.stdout.split('\n'):
                if 'test_' in line and '.py' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        status = parts[0]
                        test_name = ' '.join(parts[1:])
                        if status == 'PASSED':
                            passed += 1
                            details.append({'test_name': test_name, 'status': 'passed'})
                        elif status == 'FAILED':
                            failed += 1
                            details.append({'test_name': test_name, 'status': 'failed'})
                        elif status == 'SKIPPED':
                            skipped += 1
                            details.append({'test_name': test_name, 'status': 'skipped'})
            
            if 'passed' in result.stdout:
                import re
                match = re.search(r'(\d+) passed', result.stdout)
                if match:
                    passed = int(match.group(1))
                match = re.search(r'(\d+) failed', result.stdout)
                if match:
                    failed = int(match.group(1))
                match = re.search(r'(\d+) skipped', result.stdout)
                if match:
                    skipped = int(match.group(1))
                match = re.search(r'(\d+) tests', result.stdout)
                if match:
                    total = int(match.group(1))
            
            result = {
                'test_id': test_id,
                'test_type': 'unit',
                'status': 'completed' if failed == 0 else 'failed',
                'total_tests': total,
                'passed_tests': passed,
                'failed_tests': failed,
                'skipped_tests': skipped,
                'duration': round(time.time() - start_time, 2),
                'details': details,
                'created_at': datetime.now().isoformat(),
                'completed_at': datetime.now().isoformat()
            }
            
            self._save_test_result(result)
            self._save_test_details(test_id, details)
            
            logger.info(f"[测试框架] 单元测试完成: {passed}/{total} 通过")
            
        except subprocess.TimeoutExpired:
            result = {
                'test_id': test_id,
                'test_type': 'unit',
                'status': 'timeout',
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'skipped_tests': 0,
                'duration': round(time.time() - start_time, 2),
                'details': [{'error': '测试超时'}],
                'created_at': datetime.now().isoformat(),
                'completed_at': datetime.now().isoformat()
            }
            self._save_test_result(result)
            logger.error("[测试框架] 单元测试超时")
        
        except Exception as e:
            result = {
                'test_id': test_id,
                'test_type': 'unit',
                'status': 'error',
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'skipped_tests': 0,
                'duration': round(time.time() - start_time, 2),
                'details': [{'error': str(e)}],
                'created_at': datetime.now().isoformat(),
                'completed_at': datetime.now().isoformat()
            }
            self._save_test_result(result)
            logger.error(f"[测试框架] 单元测试失败: {e}")
        
        return result
    
    def run_api_tests(self, endpoints: List[str] = None) -> Dict:
        """运行接口测试"""
        test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}_api"
        
        endpoints = endpoints or self._api_endpoints
        
        result = {
            'test_id': test_id,
            'test_type': 'api',
            'status': 'running',
            'total_tests': len(endpoints),
            'passed_tests': 0,
            'failed_tests': 0,
            'skipped_tests': 0,
            'duration': 0,
            'avg_response_time': 0,
            'max_response_time': 0,
            'details': []
        }
        
        self._save_test_result(result)
        
        start_time = time.time()
        total_response_time = 0
        max_response_time = 0
        
        try:
            import requests
            
            for endpoint in endpoints:
                url = f"http://localhost:8888{endpoint}"
                try:
                    req_start = time.time()
                    response = requests.get(url, timeout=10)
                    req_duration = (time.time() - req_start) * 1000
                    
                    total_response_time += req_duration
                    if req_duration > max_response_time:
                        max_response_time = req_duration
                    
                    if response.status_code == 200:
                        result['passed_tests'] += 1
                        status = 'passed'
                    else:
                        result['failed_tests'] += 1
                        status = 'failed'
                    
                    result['details'].append({
                        'test_name': endpoint,
                        'status': status,
                        'response_code': response.status_code,
                        'response_time': round(req_duration, 2)
                    })
                    
                except Exception as e:
                    result['failed_tests'] += 1
                    result['details'].append({
                        'test_name': endpoint,
                        'status': 'error',
                        'error_message': str(e)
                    })
            
            result['duration'] = round(time.time() - start_time, 2)
            result['avg_response_time'] = round(total_response_time / len(endpoints), 2) if endpoints else 0
            result['max_response_time'] = round(max_response_time, 2)
            result['status'] = 'completed' if result['failed_tests'] == 0 else 'failed'
            result['created_at'] = datetime.now().isoformat()
            result['completed_at'] = datetime.now().isoformat()
            
            self._save_test_result(result)
            self._save_test_details(test_id, result['details'])
            
            logger.info(f"[测试框架] 接口测试完成: {result['passed_tests']}/{len(endpoints)} 通过, "
                       f"平均响应时间: {result['avg_response_time']}ms")
        
        except Exception as e:
            result['status'] = 'error'
            result['details'].append({'error': str(e)})
            result['duration'] = round(time.time() - start_time, 2)
            result['created_at'] = datetime.now().isoformat()
            result['completed_at'] = datetime.now().isoformat()
            self._save_test_result(result)
            logger.error(f"[测试框架] 接口测试失败: {e}")
        
        return result
    
    def run_page_tests(self, urls: List[str] = None) -> Dict:
        """运行页面访问校验"""
        test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}_page"
        
        urls = urls or self._page_urls
        
        result = {
            'test_id': test_id,
            'test_type': 'page',
            'status': 'running',
            'total_tests': len(urls),
            'passed_tests': 0,
            'failed_tests': 0,
            'skipped_tests': 0,
            'duration': 0,
            'avg_response_time': 0,
            'max_response_time': 0,
            'details': []
        }
        
        self._save_test_result(result)
        
        start_time = time.time()
        total_response_time = 0
        max_response_time = 0
        
        try:
            import requests
            
            for url in urls:
                full_url = f"http://localhost:8888{url}"
                try:
                    req_start = time.time()
                    response = requests.get(full_url, timeout=15)
                    req_duration = (time.time() - req_start) * 1000
                    
                    total_response_time += req_duration
                    if req_duration > max_response_time:
                        max_response_time = req_duration
                    
                    if response.status_code == 200:
                        result['passed_tests'] += 1
                        status = 'passed'
                    else:
                        result['failed_tests'] += 1
                        status = 'failed'
                    
                    result['details'].append({
                        'test_name': url,
                        'status': status,
                        'response_code': response.status_code,
                        'response_time': round(req_duration, 2),
                        'content_length': len(response.content)
                    })
                    
                except Exception as e:
                    result['failed_tests'] += 1
                    result['details'].append({
                        'test_name': url,
                        'status': 'error',
                        'error_message': str(e)
                    })
            
            result['duration'] = round(time.time() - start_time, 2)
            result['avg_response_time'] = round(total_response_time / len(urls), 2) if urls else 0
            result['max_response_time'] = round(max_response_time, 2)
            result['status'] = 'completed' if result['failed_tests'] == 0 else 'failed'
            result['created_at'] = datetime.now().isoformat()
            result['completed_at'] = datetime.now().isoformat()
            
            self._save_test_result(result)
            self._save_test_details(test_id, result['details'])
            
            logger.info(f"[测试框架] 页面测试完成: {result['passed_tests']}/{len(urls)} 通过")
        
        except Exception as e:
            result['status'] = 'error'
            result['details'].append({'error': str(e)})
            result['duration'] = round(time.time() - start_time, 2)
            result['created_at'] = datetime.now().isoformat()
            result['completed_at'] = datetime.now().isoformat()
            self._save_test_result(result)
            logger.error(f"[测试框架] 页面测试失败: {e}")
        
        return result
    
    def run_stress_test(self, endpoint: str = '/api/monitoring/health', 
                        concurrent: int = 10, requests: int = 100) -> Dict:
        """运行简易压力测试"""
        test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}_stress"
        
        result = {
            'test_id': test_id,
            'test_type': 'stress',
            'status': 'running',
            'total_tests': requests,
            'passed_tests': 0,
            'failed_tests': 0,
            'skipped_tests': 0,
            'duration': 0,
            'avg_response_time': 0,
            'max_response_time': 0,
            'throughput': 0,
            'error_rate': 0,
            'details': []
        }
        
        self._save_test_result(result)
        
        start_time = time.time()
        total_response_time = 0
        max_response_time = 0
        passed = 0
        failed = 0
        
        try:
            import requests
            import concurrent.futures
            
            url = f"http://localhost:8888{endpoint}"
            
            def make_request(_):
                nonlocal passed, failed, total_response_time, max_response_time
                try:
                    req_start = time.time()
                    response = requests.get(url, timeout=5)
                    req_duration = (time.time() - req_start) * 1000
                    
                    total_response_time += req_duration
                    if req_duration > max_response_time:
                        max_response_time = req_duration
                    
                    if response.status_code == 200:
                        passed += 1
                    else:
                        failed += 1
                except Exception:
                    failed += 1
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent):
                list(map(make_request, range(requests)))
            
            duration = time.time() - start_time
            
            result['passed_tests'] = passed
            result['failed_tests'] = failed
            result['duration'] = round(duration, 2)
            result['avg_response_time'] = round(total_response_time / requests, 2) if requests else 0
            result['max_response_time'] = round(max_response_time, 2)
            result['throughput'] = round(requests / duration, 2) if duration > 0 else 0
            result['error_rate'] = round(failed / requests * 100, 2) if requests > 0 else 0
            result['status'] = 'completed' if failed == 0 else 'warning' if failed < requests * 0.1 else 'failed'
            result['created_at'] = datetime.now().isoformat()
            result['completed_at'] = datetime.now().isoformat()
            
            self._save_test_result(result)
            
            logger.info(f"[测试框架] 压力测试完成: {passed}/{requests} 通过, "
                       f"吞吐量: {result['throughput']}/s, 错误率: {result['error_rate']}%")
        
        except Exception as e:
            result['status'] = 'error'
            result['details'].append({'error': str(e)})
            result['duration'] = round(time.time() - start_time, 2)
            result['created_at'] = datetime.now().isoformat()
            result['completed_at'] = datetime.now().isoformat()
            self._save_test_result(result)
            logger.error(f"[测试框架] 压力测试失败: {e}")
        
        return result
    
    def run_all_tests(self) -> Dict:
        """运行所有测试"""
        logger.info("[测试框架] 开始运行全部测试...")
        
        results = {
            'unit': self.run_unit_tests(),
            'api': self.run_api_tests(),
            'page': self.run_page_tests(),
            'stress': self.run_stress_test()
        }
        
        all_passed = all(r.get('status') == 'completed' for r in results.values())
        
        logger.info(f"[测试框架] 全部测试完成, 整体状态: {'通过' if all_passed else '部分失败'}")
        
        return {
            'overall_status': 'completed' if all_passed else 'failed',
            'results': results
        }
    
    def _save_test_result(self, result: Dict):
        """保存测试结果"""
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO test_results VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result['test_id'],
                result['test_type'],
                result.get('status', 'running'),
                result.get('total_tests', 0),
                result.get('passed_tests', 0),
                result.get('failed_tests', 0),
                result.get('skipped_tests', 0),
                result.get('duration', 0),
                result.get('error_rate', 0),
                result.get('avg_response_time', 0),
                result.get('max_response_time', 0),
                result.get('throughput', 0),
                json.dumps(result.get('details', [])),
                result.get('created_at'),
                result.get('completed_at')
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"[测试框架] 保存测试结果失败: {e}")
    
    def _save_test_details(self, test_id: str, details: List[Dict]):
        """保存测试详情"""
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            for detail in details:
                cursor.execute('''
                    INSERT INTO test_details (test_id, test_name, status, duration, 
                        error_message, response_code, response_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    test_id,
                    detail.get('test_name', ''),
                    detail.get('status', 'unknown'),
                    detail.get('duration', 0),
                    detail.get('error_message', ''),
                    detail.get('response_code', 0),
                    detail.get('response_time', 0)
                ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"[测试框架] 保存测试详情失败: {e}")
    
    def get_test_result(self, test_id: str) -> Optional[Dict]:
        """获取测试结果"""
        return self._test_results.get(test_id)
    
    def get_all_test_results(self) -> List[Dict]:
        """获取所有测试结果"""
        try:
            import sqlite3
            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM test_results ORDER BY created_at DESC LIMIT 20')
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    'test_id': row[0],
                    'test_type': row[1],
                    'status': row[2],
                    'total_tests': row[3],
                    'passed_tests': row[4],
                    'failed_tests': row[5],
                    'skipped_tests': row[6],
                    'duration': row[7],
                    'error_rate': row[8],
                    'avg_response_time': row[9],
                    'max_response_time': row[10],
                    'throughput': row[11],
                    'details': json.loads(row[12]) if row[12] else [],
                    'created_at': row[13],
                    'completed_at': row[14]
                })
            
            conn.close()
            return results
        
        except Exception as e:
            logger.error(f"[测试框架] 获取测试结果失败: {e}")
            return []


def get_test_runner() -> AutoTestRunner:
    """获取测试运行器单例"""
    return AutoTestRunner()


def init_test_system():
    """初始化测试系统"""
    runner = get_test_runner()
    logger.info("[测试框架] 自动化测试框架初始化完成")
    return runner


def init_test_runner():
    """初始化测试运行器"""
    runner = get_test_runner()
    logger.info("[测试框架] 自动化测试框架初始化完成")
    return runner