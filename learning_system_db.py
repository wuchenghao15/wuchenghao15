#!/usr/bin/env python3
"""
学习系统数据库初始化脚本
创建学习相关的数据表和结构
"""

import sqlite3
import json
from datetime import datetime

def init_learning_database():
    """初始化学习系统数据库"""
    
    db_path = 'mtcos_system.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 80)
    print("MTSCOS 学习系统 - 数据库初始化")
    print("=" * 80)
    
    # 1. 创建学习进度表
    print("\n📊 创建学习进度表...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS learning_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            course_type TEXT NOT NULL,
            course_name TEXT NOT NULL,
            progress REAL DEFAULT 0.0,
            total_hours REAL DEFAULT 0.0,
            completed_lessons INTEGER DEFAULT 0,
            total_lessons INTEGER DEFAULT 0,
            last_learned TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, course_type, course_name)
        )
    ''')
    
    # 2. 创建学习笔记表
    print("📝 创建学习笔记表...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS learning_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            course_type TEXT,
            note_title TEXT NOT NULL,
            note_content TEXT,
            tags TEXT,
            is_favorite INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 3. 创建学习计划表
    print("📅 创建学习计划表...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS learning_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            schedule_date TEXT NOT NULL,
            task_title TEXT NOT NULL,
            task_description TEXT,
            expected_duration REAL,
            is_completed INTEGER DEFAULT 0,
            completed_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, schedule_date, task_title)
        )
    ''')
    
    # 4. 创建学习统计表
    print("📈 创建学习统计表...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS learning_statistics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            stat_date TEXT NOT NULL,
            study_minutes INTEGER DEFAULT 0,
            courses_completed INTEGER DEFAULT 0,
            notes_created INTEGER DEFAULT 0,
            reviews_done INTEGER DEFAULT 0,
            streak_days INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, stat_date)
        )
    ''')
    
    # 5. 创建学习资源表
    print("📚 创建学习资源表...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS learning_resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resource_type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            content_url TEXT,
            difficulty_level TEXT DEFAULT 'beginner',
            subject_area TEXT,
            estimated_time REAL,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 6. 创建AI辅导记录表
    print("🤖 创建AI辅导记录表...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_tutoring_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            ai_employee_id INTEGER,
            subject TEXT NOT NULL,
            session_type TEXT,
            question_text TEXT,
            ai_response TEXT,
            is_helpful INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ai_employee_id) REFERENCES ai_employees (id)
        )
    ''')
    
    # 7. 创建课程目录表（与考试系统对应）
    print("🎓 创建课程目录表...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS course_catalog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT NOT NULL,
            course_name TEXT NOT NULL,
            course_type TEXT NOT NULL,
            description TEXT,
            difficulty_level TEXT DEFAULT 'beginner',
            total_lessons INTEGER DEFAULT 0,
            total_hours REAL DEFAULT 0.0,
            subject_area TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(course_code)
        )
    ''')
    
    # 插入默认课程数据
    print("\n📦 初始化课程数据...")
    default_courses = [
        # 9年制教育课程
        ('MATH-JUNIOR-001', '初中数学基础', 'nine-year', '系统学习初中数学的核心知识点，包括代数、几何、函数等基础内容', 'intermediate', 24, 36, '数学'),
        ('CHINESE-READING-001', '语文阅读理解', 'nine-year', '提升阅读理解能力，掌握各类文体的阅读技巧和答题方法', 'intermediate', 18, 27, '语文'),
        ('CHEMISTRY-BASIC-001', '化学基础概念', 'nine-year', '掌握化学基本概念和原理，为深入学习打下坚实基础', 'beginner', 16, 24, '化学'),
        
        # 成人教育课程
        ('PYTHON-BASIC-001', 'Python编程基础', 'adult', '从零开始学习Python编程语言，掌握核心语法和编程思维', 'intermediate', 32, 48, '编程'),
        ('UI-DESIGN-001', 'UI/UX设计基础', 'adult', '学习用户界面和用户体验设计的基本原则和方法', 'intermediate', 24, 36, '设计'),
        ('AI-INTRO-001', 'AI人工智能导论', 'adult', '了解人工智能的基本概念、发展历史和应用领域', 'intermediate', 18, 27, '人工智能'),
        
        # 日语学习课程
        ('HIRAGANA-001', '五十音图入门', 'japanese', '系统学习日语五十音图，掌握平假名和片假名的读写', 'beginner', 8, 12, '日语'),
        ('JLPT-N5-001', '日语N5基础', 'japanese', 'JLPT N5级别日语学习，包括基础词汇、语法和日常会话', 'beginner', 30, 45, '日语'),
        ('JAPANESE-SPEAKING-001', '日语口语入门', 'japanese', '学习日常日语会话，掌握基本交流表达', 'beginner', 16, 24, '日语'),
        
        # 专业英语课程
        ('BUSINESS-WRITING-001', '商务英语写作', 'english', '学习商务英语写作技巧，提升职场沟通能力', 'intermediate', 20, 30, '英语'),
        ('ACADEMIC-READING-001', '学术英语阅读', 'english', '掌握学术英语阅读技巧，理解专业文献', 'advanced', 22, 33, '英语'),
        ('TOEFL-PREP-001', '托福备考指南', 'english', '系统学习托福考试技巧，提升应试能力', 'advanced', 28, 42, '英语')
    ]
    
    for course in default_courses:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO course_catalog 
                (course_code, course_name, course_type, description, difficulty_level, total_lessons, total_hours, subject_area)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', course)
        except Exception as e:
            print(f"  ⚠️  跳过课程 {course[1]}: {e}")
    
    # 插入默认学习资源
    print("🎬 初始化学习资源...")
    default_resources = [
        ('video', '代数基础入门视频', '通过视频讲解，轻松理解代数基础知识', '#', 'beginner', '数学', 0.75),
        ('video', 'Python变量与数据类型', '详细讲解Python编程的基础概念', '#', 'intermediate', '编程', 0.5),
        ('video', '日语问候语与日常用语', '学习基础日语问候和日常交流表达', '#', 'beginner', '日语', 0.3),
        ('article', '数学公式速查手册', '整理的数学重要公式和解题技巧', '#', 'intermediate', '数学', 0.25),
        ('article', 'Python编程要点总结', 'Python学习过程中的重要知识点总结', '#', 'intermediate', '编程', 0.25)
    ]
    
    for resource in default_resources:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO learning_resources 
                (resource_type, title, description, content_url, difficulty_level, subject_area, estimated_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', resource)
        except Exception as e:
            print(f"  ⚠️  跳过资源 {resource[1]}: {e}")
    
    conn.commit()
    
    # 显示统计信息
    print("\n📊 数据库统计:")
    print("-" * 80)
    
    tables = ['learning_progress', 'learning_notes', 'learning_schedule', 
              'learning_statistics', 'learning_resources', 'ai_tutoring_sessions', 'course_catalog']
    
    for table in tables:
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        print(f"  {table}: {count} 条记录")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ 学习系统数据库初始化完成！")
    print("=" * 80)
    print("\n📖 功能模块:")
    print("  📚 课程学习系统 - 9年制、成人教育、日语、英语")
    print("  📊 学习进度追踪 - 实时记录学习进度")
    print("  📝 学习笔记管理 - 支持标签、收藏功能")
    print("  📅 学习计划安排 - 日历式计划管理")
    print("  📈 学习统计分析 - 学习数据可视化")
    print("  🤖 AI智能辅导 - 个性化学习辅导")
    print("  🎬 学习资源库 - 视频、文章等资源")

if __name__ == '__main__':
    init_learning_database()
