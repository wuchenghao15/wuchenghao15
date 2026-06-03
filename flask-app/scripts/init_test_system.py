#!/usr/bin/env python3
"""
智能测试系统数据库初始化
"""

import sqlite3
import os
import json
from datetime import datetime

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')


def init_test_system_tables():
    """初始化测试系统数据库表"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # 测试会话表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_sessions (
            id TEXT PRIMARY KEY,
            test_account TEXT NOT NULL,
            user_group TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            status TEXT NOT NULL,
            total_tests INTEGER DEFAULT 0,
            passed_tests INTEGER DEFAULT 0,
            failed_tests INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 测试用例表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_cases (
            id TEXT PRIMARY KEY,
            test_session_id TEXT NOT NULL,
            test_name TEXT NOT NULL,
            test_category TEXT NOT NULL,
            test_url TEXT,
            test_steps TEXT,
            expected_result TEXT,
            actual_result TEXT,
            status TEXT NOT NULL,
            error_message TEXT,
            execution_time REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (test_session_id) REFERENCES test_sessions(id)
        )
    ''')
    
    # Bug记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bug_records (
            id TEXT PRIMARY KEY,
            test_case_id TEXT,
            bug_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            description TEXT NOT NULL,
            reproduction_steps TEXT,
            url TEXT,
            status TEXT DEFAULT 'open',
            detected_at TEXT DEFAULT CURRENT_TIMESTAMP,
            fixed_at TEXT,
            fix_method TEXT,
            FOREIGN KEY (test_case_id) REFERENCES test_cases(id)
        )
    ''')
    
    # 修复记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS repair_records (
            id TEXT PRIMARY KEY,
            bug_id TEXT NOT NULL,
            repair_type TEXT NOT NULL,
            description TEXT NOT NULL,
            files_modified TEXT,
            code_changes TEXT,
            result TEXT NOT NULL,
            repaired_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (bug_id) REFERENCES bug_records(id)
        )
    ''')
    
    # AI学习特征库
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_learning_features (
            id TEXT PRIMARY KEY,
            bug_type TEXT NOT NULL,
            error_pattern TEXT,
            fix_pattern TEXT,
            frequency INTEGER DEFAULT 1,
            success_rate REAL DEFAULT 0.0,
            features TEXT,
            last_used TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 测试日志表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_logs (
            id TEXT PRIMARY KEY,
            test_session_id TEXT,
            log_level TEXT NOT NULL,
            log_message TEXT NOT NULL,
            log_data TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (test_session_id) REFERENCES test_sessions(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    
    print("✅ 测试系统数据库表创建成功")


def create_test_accounts():
    """创建测试账号"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # 检查账号是否存在
    accounts = [
        ('testStu', 'Stu0123', '学生'),
        ('testAmd', 'testAmd', '管理员')
    ]
    
    for username, password, user_group in accounts:
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if not cursor.fetchone():
            # 创建新用户
            import hashlib
            import base64
            
            hashed_pw = hashlib.pbkdf2_hmac('sha256', password.encode(), b'mtscos_salt', 100000)
            hashed_pw_b64 = base64.b64encode(hashed_pw).decode()
            
            cursor.execute('''
                INSERT INTO users (username, password, user_group, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, hashed_pw_b64, user_group, 
                  datetime.now().isoformat(), datetime.now().isoformat()))
            
            print(f"✅ 创建测试账号: {username} ({user_group})")
    
    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_test_system_tables()
    create_test_accounts()
