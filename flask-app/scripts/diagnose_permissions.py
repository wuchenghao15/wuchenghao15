# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
权限问题诊断和修复工具
"""

import os
import sys
import sqlite3
import hashlib
import base64
import requests
import json
from datetime import datetime

# 配置
BASE_URL = 'http://localhost:8888'
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')


def setup_user(username, password, role):
    """设置用户"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    hashed_pw = hashlib.sha256(password.encode()).digest()
    hashed_pw_b64 = base64.b64encode(hashed_pw).decode()
    
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    if cursor.fetchone():
        cursor.execute('UPDATE users SET password = ?, role = ? WHERE username = ?',
                     (hashed_pw_b64, role, username))
    else:
        cursor.execute('''
            INSERT INTO users (username, password, role, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, hashed_pw_b64, role, 
              datetime.now().isoformat(), datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    print(f"✅ 用户 {username} 已设置 (role={role})")


def test_login(username, password):
    """测试登录"""
    session = requests.Session()
    
    print(f"\n测试登录: {username}")
    print("-" * 50)
    
    # 执行登录
    resp = session.post(
        f'{BASE_URL}/auth/login',
        data={'username': username, 'password': password},
        timeout=10,
        allow_redirects=True
    )
    
    print(f"登录响应状态: {resp.status_code}")
    print(f"响应URL: {resp.url}")
    
    # 检查session cookies
    print(f"Session Cookies: {dict(session.cookies)}")
    
    # 尝试访问主页
    print(f"\n访问主页:")
    home_resp = session.get(f'{BASE_URL}/', timeout=10)
    print(f"  状态: {home_resp.status_code}")
    print(f"  URL: {home_resp.url}")
    print(f"  内容长度: {len(home_resp.text)} 字节")
    
    # 检查是否包含登录提示
    text_lower = home_resp.text.lower()
    if 'login' in text_lower or '请先登录' in home_resp.text:
        print(f"  ❌ 检测到登录提示,session可能未正确保存")
    else:
        print(f"  ✅ 未检测到登录提示,session正常")
    
    # 测试dashboard
    print(f"\n访问Dashboard:")
    dash_resp = session.get(f'{BASE_URL}/dashboard', timeout=10)
    print(f"  状态: {dash_resp.status_code}")
    print(f"  URL: {dash_resp.url}")
    
    # 测试exam
    print(f"\n访问Exam:")
    exam_resp = session.get(f'{BASE_URL}/exam', timeout=10)
    print(f"  状态: {exam_resp.status_code}")
    print(f"  URL: {exam_resp.url}")
    
    return session


def diagnose_permission_issues():
    """诊断权限问题"""
    print("\n" + "="*60)
    print("权限问题诊断")
    print("="*60)
    
    # 设置测试用户
    setup_user('testStu', 'Stu0123', 'user')
    setup_user('testAmd', 'testAmd', 'admin')
    
    # 测试学生账号
    print("\n" + "="*60)
    print("测试学生账号 (testStu)")
    print("="*60)
    session_stu = test_login('testStu', 'Stu0123')
    
    # 测试管理员账号
    print("\n" + "="*60)
    print("测试管理员账号 (testAmd)")
    print("="*60)
    session_admin = test_login('testAmd', 'testAmd')
    
    # 分析问题
    print("\n" + "="*60)
    print("问题分析")
    print("="*60)
    
    print("\n1. 检查路由配置:")
    
    # 检查app.py中的路由
    with open(os.path.join(os.path.dirname(DATABASE_PATH), 'app.py'), 'r') as f:
        app_content = f.read()
    
    routes_to_check = [
        ('/', '主页'),
        ('/dashboard', '仪表板'),
        ('/exam', '考试'),
        ('/admin_center', '管理员中心')
    ]
    
    for route, name in routes_to_check:
        if f"@app.route('{route}')" in app_content or f'@app.route("{route}")' in app_content:
            print(f"  ✅ {name} ({route}) - 路由已注册")
        else:
            print(f"  ❌ {name} ({route}) - 路由未注册")
    
    print("\n2. 检查权限装饰器:")
    
    decorators = [
        ('@require_login', '登录要求'),
        ('@require_admin', '管理员要求')
    ]
    
    for decorator, name in decorators:
        if decorator in app_content:
            print(f"  ✅ {name} - 装饰器已定义")
        else:
            print(f"  ❌ {name} - 装饰器未定义")
    
    print("\n3. 检查数据库:")
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # 检查users表
    cursor.execute('SELECT username, role FROM users WHERE username IN (?, ?)',
                 ('testStu', 'testAmd'))
    users = cursor.fetchall()
    print(f"\n测试用户:")
    for username, role in users:
        print(f"  {username}: role={role}")
    
    conn.close()
    
    print("\n4. 建议修复方案:")
    print("  - 确保登录后session正确保存")
    print("  - 检查require_login装饰器实现")
    print("  - 确认路由权限配置正确")
    
    print("\n" + "="*60)


if __name__ == '__main__':
    diagnose_permission_issues()
