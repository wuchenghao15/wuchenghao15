#!/usr/bin/env python3
import sqlite3
import os
import hashlib
from datetime import datetime

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_missing_tables(conn):
    cursor = conn.cursor()
    
    tables = {
        'question_categories': """
            CREATE TABLE IF NOT EXISTS question_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                code TEXT UNIQUE,
                description TEXT,
                sort_order INTEGER DEFAULT 0,
                status INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """,
        'question_tags': """
            CREATE TABLE IF NOT EXISTS question_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                sort_order INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """,
        'courses': """
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                code TEXT UNIQUE,
                status TEXT DEFAULT 'active',
                category_id INTEGER,
                start_date TEXT,
                end_date TEXT,
                total_hours INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES question_categories (id)
            )
        """,
        'system_params': """
            CREATE TABLE IF NOT EXISTS system_params (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT,
                description TEXT,
                type TEXT DEFAULT 'string',
                constraints TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """,
    }
    
    for name, create_sql in tables.items():
        try:
            cursor.execute(create_sql)
            print(f"  表 {name} 创建/检查完成")
        except Exception as e:
            print(f"  创建表 {name} 失败: {e}")
    
    conn.commit()

def seed_users(conn):
    cursor = conn.cursor()
    users = [
        ('admin', 'admin@mtscos.com', hash_password('admin123'), 'super_admin'),
        ('teacher001', 'teacher@mtscos.com', hash_password('teacher123'), 'teacher'),
        ('student001', 'student@mtscos.com', hash_password('student123'), 'student'),
        ('designer001', 'designer@mtscos.com', hash_password('designer123'), 'designer'),
        ('user001', 'user@mtscos.com', hash_password('user123'), 'user'),
    ]
    
    for user in users:
        try:
            cursor.execute("INSERT OR IGNORE INTO users (username, email, password, role) VALUES (?, ?, ?, ?)", user)
        except Exception as e:
            print(f"  用户 {user[0]} 插入失败: {e}")
    
    conn.commit()
    print("  用户数据已填充")

def seed_categories(conn):
    cursor = conn.cursor()
    categories = [
        ('语文', 'Chinese', '语言文学', 1, 1),
        ('数学', 'Math', '数理逻辑', 2, 1),
        ('英语', 'English', '外语学习', 3, 1),
        ('物理', 'Physics', '物理科学', 4, 1),
        ('化学', 'Chemistry', '化学科学', 5, 1),
        ('生物', 'Biology', '生命科学', 6, 1),
        ('历史', 'History', '历史人文', 7, 1),
        ('地理', 'Geography', '地理环境', 8, 1),
    ]
    
    for cat in categories:
        try:
            cursor.execute("INSERT OR IGNORE INTO question_categories (name, code, description, sort_order, status) VALUES (?, ?, ?, ?, ?)", cat)
        except Exception as e:
            print(f"  分类 {cat[0]} 插入失败: {e}")
    
    conn.commit()
    print("  题目分类已填充")

def seed_tags(conn):
    cursor = conn.cursor()
    tags = [
        ('基础', '基础知识点', 1),
        ('进阶', '进阶难度', 2),
        ('难题', '高难度', 3),
        ('真题', '历年真题', 4),
        ('模拟', '模拟题目', 5),
        ('易错', '易错题目', 6),
        ('重点', '重点考点', 7),
        ('必考', '必考内容', 8),
    ]
    
    for tag in tags:
        try:
            cursor.execute("INSERT OR IGNORE INTO question_tags (name, description, sort_order) VALUES (?, ?, ?)", tag)
        except Exception as e:
            print(f"  标签 {tag[0]} 插入失败: {e}")
    
    conn.commit()
    print("  题目标签已填充")

def seed_exams(conn):
    cursor = conn.cursor()
    exams = [
        ('期中考试', '2026年春季期中考试'),
        ('期末考试', '2026年春季期末考试'),
        ('单元测试', '数学第一单元测试'),
        ('模拟考试', '高考模拟考试'),
    ]
    
    for exam in exams:
        try:
            cursor.execute("INSERT OR IGNORE INTO exams (title, description) VALUES (?, ?)", exam)
        except Exception as e:
            print(f"  考试 {exam[0]} 插入失败: {e}")
    
    conn.commit()
    print("  考试数据已填充")

def seed_courses(conn):
    cursor = conn.cursor()
    courses = [
        ('高中数学必修一', '函数与导数基础', 'math_1', 'active', 2),
        ('高中英语必修一', '语法与词汇', 'english_1', 'active', 3),
        ('高中物理必修一', '力学基础', 'physics_1', 'active', 4),
        ('初中数学', '代数与几何', 'math_junior', 'active', 2),
    ]
    
    for course in courses:
        try:
            cursor.execute("INSERT OR IGNORE INTO courses (name, description, code, status, category_id) VALUES (?, ?, ?, ?, ?)", course)
        except Exception as e:
            print(f"  课程 {course[0]} 插入失败: {e}")
    
    conn.commit()
    print("  课程数据已填充")

def seed_system_params(conn):
    cursor = conn.cursor()
    params = [
        ('system_name', 'MTSCOS AI系统', '系统名称', 'string', '{"max_length": 100}'),
        ('system_version', '1.0.0', '系统版本', 'string', '{"max_length": 50}'),
        ('session_timeout', '1800', '会话超时时间(秒)', 'integer', '{"min": 300, "max": 7200}'),
        ('max_login_attempts', '5', '最大登录尝试次数', 'integer', '{"min": 3, "max": 10}'),
        ('login_lock_duration', '3600', '登录锁定时长(秒)', 'integer', '{"min": 600, "max": 86400}'),
        ('enable_notifications', 'true', '启用通知', 'boolean', '{}'),
        ('enable_ai_features', 'true', '启用AI功能', 'boolean', '{}'),
        ('enable_tts', 'true', '启用语音合成', 'boolean', '{}'),
        ('tts_speed', '1.0', '语音速度', 'float', '{"min": 0.5, "max": 2.0}'),
        ('tts_volume', '1.0', '语音音量', 'float', '{"min": 0.0, "max": 1.0}'),
    ]
    
    for param in params:
        try:
            cursor.execute("INSERT OR IGNORE INTO system_params (key, value, description, type, constraints) VALUES (?, ?, ?, ?, ?)", param)
        except Exception as e:
            print(f"  参数 {param[0]} 插入失败: {e}")
    
    conn.commit()
    print("  系统参数已填充")

def seed_notifications(conn):
    cursor = conn.cursor()
    notifications = [
        ('MTSCOS AI系统正式上线！', 'active', 1),
        ('系统将于今晚22:00-00:00进行维护', 'active', 2),
        ('新增AI智能辅导功能', 'active', 1),
    ]
    
    for notice in notifications:
        try:
            cursor.execute("INSERT OR IGNORE INTO system_notices (content, status, priority) VALUES (?, ?, ?)", notice)
        except Exception as e:
            print(f"  通知插入失败: {e}")
    
    conn.commit()
    print("  系统通知已填充")

def seed_error_reports_table(conn):
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS error_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL,
                url TEXT,
                line INTEGER DEFAULT 0,
                column INTEGER DEFAULT 0,
                error TEXT,
                timestamp REAL,
                user_agent TEXT,
                user_id INTEGER,
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        conn.commit()
        print("  错误报告表已创建")
    except Exception as e:
        print(f"  创建错误报告表失败: {e}")

def seed_users_table_columns(conn):
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'failed_login_count' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN failed_login_count INTEGER DEFAULT 0")
            print("  添加 failed_login_count 列")
        
        if 'last_failed_login' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN last_failed_login TEXT")
            print("  添加 last_failed_login 列")
        
        if 'locked_until' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN locked_until TEXT")
            print("  添加 locked_until 列")
        
        conn.commit()
    except Exception as e:
        print(f"  更新用户表结构失败: {e}")

def audit_database(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"表数量: {len(tables)}")
    
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"  {table_name}: {count} 行")

def main():
    print("=== MTSCOS AI 数据库种子数据填充 ===")
    
    conn = sqlite3.connect(DATABASE_PATH)
    
    seed_users_table_columns(conn)
    seed_error_reports_table(conn)
    create_missing_tables(conn)
    
    print("\n=== 开始填充数据 ===")
    seed_users(conn)
    seed_categories(conn)
    seed_tags(conn)
    seed_exams(conn)
    seed_courses(conn)
    seed_system_params(conn)
    seed_notifications(conn)
    
    conn.close()
    
    print("\n=== 数据填充完成 ===")
    conn = sqlite3.connect(DATABASE_PATH)
    audit_database(conn)
    conn.close()

if __name__ == '__main__':
    main()