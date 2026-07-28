#!/usr/bin/env python3
import sqlite3
import os
import hashlib
import base64
import string
import random

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        is_active INTEGER DEFAULT 1,
        super_admin_approved INTEGER DEFAULT 0,
        hardware_admin_approved INTEGER DEFAULT 0,
        avatar TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS login_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        login_time TEXT DEFAULT CURRENT_TIMESTAMP,
        login_ip TEXT,
        user_agent TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS system_notices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT,
        status TEXT DEFAULT 'active',
        priority INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS exam_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        exam_id INTEGER,
        status TEXT DEFAULT 'in_progress',
        started_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS exams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
''')

password = 'LoginMe.1988'
salt_chars = string.ascii_letters + string.digits + './'
salt = ''.join(random.choice(salt_chars) for _ in range(16))
iterations = 260000
hash_result = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), iterations)
hashed_password = 'pbkdf2:sha256:' + str(iterations) + '$' + salt + '$' + base64.b64encode(hash_result).decode()

logger.info(f'生成的密码格式: {hashed_password[:80]}...')

logger.info('✓ 用户表创建完成')
logger.info('✓ 登录日志表创建完成')
logger.info('✓ 系统公告表创建完成')
logger.info('✓ 考试会话表创建完成')
logger.info('✓ 考试表创建完成')