# -*- coding: utf-8 -*-
#!/usr/bin/env python3
import sqlite3
import sys

DATABASE_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'

def check_table_structure():
    """检查并显示表结构"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("当前数据库中的表:")
        for (table_name,) in tables:
            print(f"\n  {table_name}:")
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            for col in columns:
                print(f"    {col[1]} ({col[2]})")

def rebuild_exam_tables():
    """重建考试系统表"""
    print("\n" + "="*70)
    print("🛠️  重建考试系统表")
    print("="*70)
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # 删除旧表(如果存在)
        tables_to_drop = ['exams', 'questions', 'exam_questions', 
                         'exam_sessions', 'exam_answers', 'exam_performance',
                         'system_test_results']
        
        for table in tables_to_drop:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                print(f"✅ 删除: {table}")
            except Exception:
                pass
        
        # 创建新的考试表
        cursor.execute('''
            CREATE TABLE exams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT DEFAULT 'general',
                duration INTEGER DEFAULT 60,
                question_count INTEGER DEFAULT 0,
                total_score INTEGER DEFAULT 100,
                passing_score INTEGER DEFAULT 60,
                status TEXT DEFAULT 'active',
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ 创建: exams")
        
        # 创建题目表
        cursor.execute('''
            CREATE TABLE questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_text TEXT NOT NULL,
                question_type TEXT DEFAULT 'multiple_choice',
                options TEXT,
                correct_answer TEXT,
                explanation TEXT,
                difficulty TEXT DEFAULT 'medium',
                category TEXT,
                points INTEGER DEFAULT 10,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ 创建: questions")
        
        # 创建考试-题目关联表
        cursor.execute('''
            CREATE TABLE exam_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                order_num INTEGER DEFAULT 0
            )
        ''')
        print("✅ 创建: exam_questions")
        
        # 创建考试会话表
        cursor.execute('''
            CREATE TABLE exam_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                exam_id INTEGER NOT NULL,
                start_time TEXT,
                end_time TEXT,
                duration_used INTEGER,
                status TEXT DEFAULT 'in_progress',
                score INTEGER,
                passed INTEGER DEFAULT 0
            )
        ''')
        print("✅ 创建: exam_sessions")
        
        # 创建考试答案表
        cursor.execute('''
            CREATE TABLE exam_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                user_answer TEXT,
                is_correct INTEGER DEFAULT 0,
                points_earned INTEGER DEFAULT 0,
                answer_time TEXT
            )
        ''')
        print("✅ 创建: exam_answers")
        
        # 创建考试表现表
        cursor.execute('''
            CREATE TABLE exam_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                exam_id INTEGER NOT NULL,
                session_id INTEGER,
                score INTEGER,
                total_questions INTEGER,
                correct_answers INTEGER,
                time_used INTEGER,
                passed INTEGER,
                completed_at TEXT
            )
        ''')
        print("✅ 创建: exam_performance")
        
        # 创建测试结果表
        cursor.execute('''
            CREATE TABLE system_test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_module TEXT NOT NULL,
                test_name TEXT NOT NULL,
                status TEXT NOT NULL,
                error_message TEXT,
                solution_provided TEXT,
                test_data TEXT,
                test_time TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ 创建: system_test_results")
        
        conn.commit()
        print("\n✅ 所有考试系统表重建完成!")

if __name__ == '__main__':
    check_table_structure()
    print("\n" + "="*70)
    rebuild_exam_tables()
