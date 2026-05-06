#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
考试系统数据库初始化脚本
"""
import sqlite3
import os

DATABASE_PATH = 'app.db'

def init_exam_database():
    """初始化考试系统数据库"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    print('开始初始化考试系统数据库...')
    
    # AI生成的题目表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_generated_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER,
            question_type TEXT,
            language TEXT,
            difficulty TEXT,
            content TEXT,
            options TEXT,
            correct_answer TEXT,
            explanation TEXT,
            generated_by TEXT,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            used_count INTEGER DEFAULT 0
        )
    ''')
    print('✓ 创建表：ai_generated_questions')
    
    # 考试会话表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exam_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER,
            user_id INTEGER,
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_time TIMESTAMP,
            status TEXT DEFAULT 'in_progress',
            score REAL,
            ai_analysis TEXT
        )
    ''')
    print('✓ 创建表：exam_sessions')
    
    # 答题记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exam_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            question_id INTEGER,
            user_answer TEXT,
            correct_answer TEXT,
            is_correct BOOLEAN,
            answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print('✓ 创建表：exam_answers')
    
    # AI反馈表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            exam_id INTEGER,
            feedback_type TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            read_at TIMESTAMP
        )
    ''')
    print('✓ 创建表：ai_feedback')
    
    # 创建索引
    try:
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ai_q_exam_id ON ai_generated_questions(exam_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_exam_sessions_user_id ON exam_sessions(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_answers_session_id ON exam_answers(session_id)')
        print('✓ 创建索引完成')
    except Exception as e:
        print(f'索引创建（可能已存在）: {e}')
    
    conn.commit()
    conn.close()
    print('✅ 考试系统数据库初始化完成！')

if __name__ == '__main__':
    init_exam_database()
