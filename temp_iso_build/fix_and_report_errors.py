#!/usr/bin/env python3
import sqlite3
import subprocess
import os
from datetime import datetime

def check_database():
    conn = sqlite3.connect('flask-app/app.db')
    cursor = conn.cursor()
    
    # 检查必要的表
    required_tables = ['users', 'system_settings', 'settings_approval', 'scheduled_tasks', 'hardware_devices']
    missing_tables = []
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [t[0] for t in cursor.fetchall()]
    
    for table in required_tables:
        if table not in existing_tables:
            missing_tables.append(table)
    
    conn.close()
    return missing_tables

def create_missing_tables():
    conn = sqlite3.connect('flask-app/app.db')
    cursor = conn.cursor()
    
    # 创建settings_approval表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings_approval (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key TEXT NOT NULL,
            new_value TEXT NOT NULL,
            old_value TEXT,
            requester_id INTEGER,
            requester_role TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            approver_id INTEGER,
            approver_role TEXT,
            approved_at TEXT,
            effective_date TEXT,
            created_at TEXT,
            expires_at TEXT,
            revoked_at TEXT,
            executed_at TEXT
        )
    ''')
    
    # 创建scheduled_tasks表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scheduled_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            approval_id INTEGER,
            setting_key TEXT,
            new_value TEXT,
            execute_time TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT
        )
    ''')
    
    # 创建hardware_devices表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hardware_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_name TEXT NOT NULL,
            device_type TEXT,
            ip_address TEXT,
            status TEXT DEFAULT 'online',
            cpu_usage REAL DEFAULT 0,
            memory_usage REAL DEFAULT 0,
            storage_usage REAL DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    # 创建system_settings表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key TEXT UNIQUE NOT NULL,
            value TEXT,
            approval_status TEXT DEFAULT 'active',
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    # 创建api_test_logs表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_test_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_time TEXT,
            endpoint TEXT,
            method TEXT,
            status_code INTEGER,
            success INTEGER,
            error TEXT
        )
    ''')
    
    # 创建error_reports表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS error_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            error_type TEXT,
            error_message TEXT,
            file_path TEXT,
            line_number INTEGER,
            timestamp TEXT,
            fixed INTEGER DEFAULT 0,
            fix_description TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print('数据库表检查和创建完成')

def report_error(error_type, message, file_path=None, line_number=None, fixed=False, fix_desc=None):
    conn = sqlite3.connect('flask-app/app.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO error_reports 
        (error_type, error_message, file_path, line_number, timestamp, fixed, fix_description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (error_type, message, file_path, line_number, datetime.now().isoformat(), 
          1 if fixed else 0, fix_desc))
    conn.commit()
    conn.close()
    print(f'错误已上报: {error_type} - {message}')

def check_python_syntax():
    errors = []
    files_to_check = [
        'flask-app/hardware_app.py',
        'flask-app/app.py',
        'start_project.py',
        'fix_system_login.py'
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            try:
                subprocess.run(['python3', '-m', 'py_compile', file_path], 
                              check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                errors.append({
                    'type': 'SyntaxError',
                    'message': e.stderr.decode(),
                    'file': file_path
                })
    
    return errors

def main():
    print('=== 后端工程师AI - 代码错误检查和修复 ===')
    print(f'时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
    
    # 1. 检查数据库表
    print('1. 检查数据库表结构...')
    missing = check_database()
    if missing:
        print(f'   缺失表: {missing}')
        create_missing_tables()
        report_error('DatabaseError', f'缺失表已创建: {missing}', fixed=True, fix_desc='自动创建缺失的数据库表')
    else:
        print('   ✅ 所有必要表已存在')
    
    # 2. 检查Python语法
    print('\n2. 检查Python代码语法...')
    syntax_errors = check_python_syntax()
    if syntax_errors:
        for err in syntax_errors:
            print(f'   ❌ {err["file"]}: {err["message"][:50]}')
            report_error(err['type'], err['message'], err['file'])
    else:
        print('   ✅ 所有Python文件语法正确')
    
    # 3. 验证关键表数据
    print('\n3. 验证关键数据...')
    conn = sqlite3.connect('flask-app/app.db')
    cursor = conn.cursor()
    
    # 检查用户表
    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]
    print(f'   用户数量: {user_count}')
    
    # 检查审批表
    cursor.execute('SELECT COUNT(*) FROM settings_approval')
    approval_count = cursor.fetchone()[0]
    print(f'   审批记录: {approval_count}')
    
    conn.close()
    
    print('\n=== 检查完成 ===')

if __name__ == '__main__':
    main()