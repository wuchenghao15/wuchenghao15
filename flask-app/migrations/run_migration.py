# -*- coding: utf-8 -*-
"""
安全执行数据库迁移脚本
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')

def get_columns(cursor, table_name):
    """获取表的所有列名"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]

def run_migration():
    print("开始数据库迁移...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    columns = get_columns(cursor, 'exam_results')
    if 'score' not in columns:
        print("添加 score 字段到 exam_results...")
        cursor.execute('ALTER TABLE exam_results ADD COLUMN score REAL DEFAULT 0.0')
    
    if 'subject' not in columns:
        print("添加 subject 字段到 exam_results...")
        cursor.execute('ALTER TABLE exam_results ADD COLUMN subject TEXT')
    
    if 'status' not in columns:
        print("添加 status 字段到 exam_results...")
        cursor.execute('ALTER TABLE exam_results ADD COLUMN status TEXT DEFAULT "completed"')
    
    columns = get_columns(cursor, 'learning_records')
    if 'activity_type' not in columns:
        print("添加 activity_type 字段到 learning_records...")
        cursor.execute('ALTER TABLE learning_records ADD COLUMN activity_type TEXT')
    
    if 'user_id' not in columns:
        print("添加 user_id 字段到 learning_records...")
        cursor.execute('ALTER TABLE learning_records ADD COLUMN user_id INTEGER')
    
    if 'duration' not in columns:
        print("添加 duration 字段到 learning_records...")
        cursor.execute('ALTER TABLE learning_records ADD COLUMN duration REAL')
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_answers'")
    if not cursor.fetchone():
        print("创建 user_answers 表...")
        cursor.execute('''
            CREATE TABLE user_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                question_id INTEGER,
                answer TEXT,
                is_wrong INTEGER DEFAULT 0,
                exam_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    else:
        print("user_answers 表已存在")
    
    columns = get_columns(cursor, 'questions')
    if 'knowledge_point' not in columns:
        print("添加 knowledge_point 字段到 questions...")
        cursor.execute('ALTER TABLE questions ADD COLUMN knowledge_point TEXT')
    
    cursor.execute('UPDATE exam_results SET score = total_score WHERE score IS NULL')
    print(f"更新 {cursor.rowcount} 条记录的 score 字段")
    
    cursor.execute('UPDATE exam_results SET status = "completed" WHERE status IS NULL')
    print(f"更新 {cursor.rowcount} 条记录的 status 字段")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_exam_results_subject'")
    if not cursor.fetchone():
        print("创建 idx_exam_results_subject 索引...")
        cursor.execute('CREATE INDEX idx_exam_results_subject ON exam_results(subject)')
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_exam_results_status'")
    if not cursor.fetchone():
        print("创建 idx_exam_results_status 索引...")
        cursor.execute('CREATE INDEX idx_exam_results_status ON exam_results(status)')
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_user_answers_question_id'")
    if not cursor.fetchone():
        print("创建 idx_user_answers_question_id 索引...")
        cursor.execute('CREATE INDEX idx_user_answers_question_id ON user_answers(question_id)')
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_user_answers_is_wrong'")
    if not cursor.fetchone():
        print("创建 idx_user_answers_is_wrong 索引...")
        cursor.execute('CREATE INDEX idx_user_answers_is_wrong ON user_answers(is_wrong)')
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_questions_knowledge_point'")
    if not cursor.fetchone():
        print("创建 idx_questions_knowledge_point 索引...")
        cursor.execute('CREATE INDEX idx_questions_knowledge_point ON questions(knowledge_point)')
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name='v_student_analytics'")
    if not cursor.fetchone():
        print("创建 v_student_analytics 视图...")
        cursor.execute('''
            CREATE VIEW v_student_analytics AS
            SELECT 
                u.id as user_id,
                u.username,
                AVG(er.score) as avg_score,
                COUNT(er.id) as exam_count,
                SUM(CASE WHEN er.score >= 60 THEN 1 ELSE 0 END) as passed_count,
                SUM(CASE WHEN er.score < 60 THEN 1 ELSE 0 END) as failed_count
            FROM users u
            LEFT JOIN exam_results er ON u.id = er.user_id AND er.status = 'completed'
            WHERE u.role = 'student'
            GROUP BY u.id
        ''')
    
    conn.commit()
    conn.close()
    
    print("\n迁移完成!")

if __name__ == '__main__':
    run_migration()
