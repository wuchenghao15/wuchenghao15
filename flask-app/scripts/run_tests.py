# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
智能集成测试脚本 - 使用requests库进行系统测试
"""

import os
import sys
import uuid
import json
import time
import sqlite3
import requests
import base64
import hashlib
from datetime import datetime
from typing import Dict, List
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.test_ai_system import TestAISystem, db_connection

BASE_URL = 'http://localhost:8888'
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')

# 测试系统实例
test_system = TestAISystem()


def create_session_with_retries():
    """创建带重试的HTTP会话"""
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1)
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))
    return session


def create_test_accounts_simple():
    """简化版创建测试账号"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    accounts = [
        ('testStu', 'Stu0123', '学生'),
        ('testAmd', 'testAmd', '管理员')
    ]
    
    created = []
    for username, password, group in accounts:
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if not cursor.fetchone():
            hashed_pw = hashlib.pbkdf2_hmac('sha256', password.encode(), b'mtscos_salt', 100000)
            hashed_pw_b64 = base64.b64encode(hashed_pw).decode()
            
            cursor.execute('''
                INSERT OR IGNORE INTO users (username, password, user_group, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, hashed_pw_b64, group, 
                  datetime.now().isoformat(), datetime.now().isoformat()))
            created.append(username)
            print(f"✅ 创建测试账号: {username}")
    
    conn.commit()
    conn.close()
    return created


def test_login(session, username: str, password: str) -> Dict:
    """测试登录功能"""
    try:
        response = session.post(
            f'{BASE_URL}/auth/login',
            data={'username': username, 'password': password},
            allow_redirects=True,
            timeout=10
        )
        return {
            'success': response.status_code == 200,
            'status_code': response.status_code,
            'content': response.text[:200]
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


def test_page_access(session, page_path: str) -> Dict:
    """测试页面访问"""
    try:
        response = session.get(f'{BASE_URL}{page_path}', timeout=10)
        return {
            'success': response.status_code == 200,
            'status_code': response.status_code,
            'has_content': len(response.text) > 0
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


def run_account_test(account: str, password: str, user_group: str):
    """运行完整的账号测试流程"""
    print(f"\n{'='*60}")
    print(f"开始测试账号: {account} ({user_group})")
    print(f"{'='*60}")
    
    session_id = test_system.create_test_session(account, user_group)
    http_session = create_session_with_retries()
    
    # 1. 测试登录
    test_system.log('INFO', f'测试账号登录: {account}')
    result = test_system.run_test(
        session_id,
        '登录功能测试',
        'authentication',
        lambda: test_login(http_session, account, password)
    )
    
    passed = 1 if result else 0
    failed = 0 if result else 1
    total = 1
    
    # 2. 测试主页访问
    test_system.log('INFO', '测试主页访问')
    pages = ['/', '/test', '/exam', '/matrix_management']
    
    for page in pages:
        result = test_system.run_test(
            session_id,
            f'页面访问测试: {page}',
            'page_access',
            lambda p=page: test_page_access(http_session, p),
            url=page
        )
        total +=1
        if result:
            passed +=1
        else:
            failed +=1
        time.sleep(0.5)
    
    # 3. 测试API接口
    test_system.log('INFO', '测试API接口')
    apis = ['/api/server-time', '/test', '/api/matrix/matrix-types', '/api/matrix/knowledge-points']
    
    for api in apis:
        result = test_system.run_test(
            session_id,
            f'API访问测试: {api}',
            'api_access',
            lambda a=api: test_page_access(http_session, a),
            url=api
        )
        total +=1
        if result:
            passed +=1
        else:
            failed +=1
        time.sleep(0.3)
    
    # 更新测试会话
    test_system.update_test_session(
        session_id,
        end_time=datetime.now().isoformat(),
        status='completed',
        total_tests=total,
        passed_tests=passed,
        failed_tests=failed
    )
    
    print(f"\n✅ 账号 {account} 测试完成: {passed}/{total} 通过")
    
    return {
        'session_id': session_id,
        'total': total,
        'passed': passed,
        'failed': failed,
        'bugs_found': test_system.bugs_found,
        'repairs_made': test_system.repairs_made
    }


def main():
    print(f"{'='*60}")
    print("MTSCOS AI 系统测试系统 - 自动化测试")
    print(f"{'='*60}")
    
    # 确保服务器正在运行
    print("\n📋 检查服务器状态...")
    try:
        resp = requests.get(f'{BASE_URL}/test', timeout=5)
        if resp.status_code != 200:
            print("⚠️ 服务器响应异常")
    except Exception:
        print("❌ 服务器未启动,无法进行测试")
        return
    
    print("✅ 服务器运行正常\n")
    
    # 创建测试账号
    print("📋 初始化测试账号...")
    created = create_test_accounts_simple()
    print(f"创建账号数量: {len(created)}")
    
    # 测试学生账号
    student_result = run_account_test('testStu', 'Stu0123', '学生')
    
    # 重置测试系统实例
    global test_system
    test_system = TestAISystem()
    
    # 测试管理员账号
    admin_result = run_account_test('testAmd', 'testAmd', '管理员')
    
    # 生成总结报告
    print(f"\n{'='*60}")
    print("📊 测试总结")
    print(f"{'='*60}")
    print(f"学生账号测试: {student_result['passed']}/{student_result['total']} 通过")
    print(f"管理员账号测试: {admin_result['passed']}/{admin_result['total']} 通过")
    print(f"发现Bug数量: {len(student_result['bugs_found'])} + {len(admin_result['bugs_found'])}")
    print(f"修复记录数量: {len(student_result['repairs_made'])} + {len(admin_result['repairs_made'])}")
    
    # 保存测试报告到数据库
    print("\n✅ 测试报告已保存到数据库")


if __name__ == '__main__':
    main()
