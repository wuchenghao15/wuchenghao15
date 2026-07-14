#!/usr/bin/env python3
import os
import json
import sqlite3
import requests
import time

BASE_URL = 'http://localhost:8888'
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'app.db')

def test_api_endpoint(url, method='GET', data=None, headers=None):
    try:
        if method == 'POST':
            if headers is None:
                headers = {'Content-Type': 'application/json'}
            response = requests.post(url, json=data, headers=headers)
        else:
            response = requests.get(url)
        return response.status_code, response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
    except Exception as e:
        return None, str(e)

def check_database():
    issues = []
    try:
        if not os.path.exists(DATABASE_PATH):
            issues.append(f"数据库文件不存在: {DATABASE_PATH}")
            return issues
        
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [t[0] for t in cursor.fetchall()]
            
            required_tables = ['exams', 'questions', 'exam_papers', 'users']
            for table in required_tables:
                if table not in tables:
                    issues.append(f"缺少数据表: {table}")
            
            if 'exams' in tables:
                cursor.execute("SELECT COUNT(*) FROM exams;")
                count = cursor.fetchone()[0]
                if count == 0:
                    issues.append("exams 表为空")
            
            if 'questions' in tables:
                cursor.execute("SELECT COUNT(*) FROM questions;")
                count = cursor.fetchone()[0]
                if count == 0:
                    issues.append("questions 表为空")
            
            if 'exam_papers' in tables:
                cursor.execute("PRAGMA table_info(exam_papers);")
                columns = [c[1] for c in cursor.fetchall()]
                required_columns = ['id', 'user_id', 'exam_id', 'answers', 'status', 'scores', 'start_time', 'end_time']
                for col in required_columns:
                    if col not in columns:
                        issues.append(f"exam_papers 表缺少字段: {col}")
    
    except Exception as e:
        issues.append(f"数据库检查失败: {e}")
    
    return issues

def create_test_data():
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM exams WHERE id = 1;")
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO exams (id, title, description, subject, duration, total_points, status, created_at) VALUES (1, '听力测试', '增强版听力测试', '英语', 30, 100, 'active', datetime('now'));")
                print("✓ 创建测试考试")
            
            cursor.execute("SELECT COUNT(*) FROM questions WHERE exam_id = 1;")
            if cursor.fetchone()[0] == 0:
                questions = [
                    (1, 'q1', '英语听力 - 日常对话', 'M: Good morning! How can I help you today? W: I would like to book a flight to New York.', '{"A": "The man is booking a flight.", "B": "The woman wants to go to New York.", "C": "They are at the airport.", "D": "It is afternoon now."}', 'B', 10, 'listening'),
                    (2, 'q2', '英语听力 - 天气预报', 'Good evening. Tomorrow will be sunny with a high of 28 degrees Celsius.', '{"A": "Tomorrow will be rainy.", "B": "The high temperature is 28C.", "C": "Winds will be from the west.", "D": "It is morning now."}', 'B', 10, 'listening'),
                ]
                cursor.executemany("INSERT INTO questions (id, question_id, title, content, options, correct_answer, points, type) VALUES (?, ?, ?, ?, ?, ?, ?, ?);", questions)
                print("✓ 创建测试题目")
            
            conn.commit()
            return True
    except Exception as e:
        print(f"✗ 创建测试数据失败: {e}")
        return False

def run_tests():
    print("="*60)
    print("MTSCOS 考试系统测试")
    print("="*60)
    
    print("\n[1/3] 数据库检查")
    issues = check_database()
    if issues:
        for issue in issues:
            print(f"  ✗ {issue}")
        print("  → 正在创建测试数据...")
        create_test_data()
    else:
        print("  ✓ 数据库检查通过")
    
    print("\n[2/3] API路由测试")
    api_tests = [
        ('/api/health', 'GET', True),
        ('/audio/audio_q1_content.mp3', 'GET', True),
        ('/listen_enhanced', 'GET', True),
        ('/api/exams', 'GET', False),
        ('/api/exam/exams/1', 'GET', False),
        ('/api/exams/1/questions', 'GET', False),
    ]
    
    for path, method, should_succeed in api_tests:
        url = BASE_URL + path
        status, response = test_api_endpoint(url, method)
        if should_succeed:
            if status == 200:
                print(f"  ✓ {path}")
            elif status is None:
                print(f"  ✗ {path} - {response}")
            else:
                print(f"  ✗ {path} - HTTP {status}")
        else:
            if status == 401:
                print(f"  ✓ {path} (预期需要登录 - HTTP {status})")
            elif status == 200:
                print(f"  ✓ {path}")
            elif status is None:
                print(f"  ✗ {path} - {response}")
            else:
                print(f"  ⚠ {path} - HTTP {status}")
    
    print("\n[3/3] 提交功能测试")
    submit_url = BASE_URL + '/api/exam/submit'
    test_data = {
        'answers': {'q1': 1, 'q2': 1},
        'score': 100,
        'correct': 2,
        'total': 2,
        'speed': 1.0,
        'voice': 'aria',
        'topic': 'daily',
        'difficulty': '中级'
    }
    
    status, response = test_api_endpoint(submit_url, 'POST', test_data)
    if status == 200:
        print(f"  ✓ /api/exam/submit")
        if isinstance(response, dict) and response.get('success'):
            print(f"    → 提交数据: score={response['data']['score']}, accuracy={response['data']['accuracy']}")
    elif status is None:
        print(f"  ✗ /api/exam/submit - {response}")
    else:
        print(f"  ✗ /api/exam/submit - HTTP {status}")
        print(f"    → 响应: {response}")
    
    print("\n" + "="*60)

if __name__ == '__main__':
    run_tests()