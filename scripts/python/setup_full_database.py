#!/usr/bin/env python3
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_text TEXT NOT NULL,
        question_type TEXT DEFAULT 'single',
        subject TEXT,
        difficulty TEXT DEFAULT 'medium',
        answer TEXT,
        options TEXT,
        explanation TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS exam_papers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        duration INTEGER DEFAULT 60,
        total_score INTEGER DEFAULT 100,
        created_by INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by) REFERENCES users(id)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS exam_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        exam_id INTEGER,
        exam_paper_id INTEGER,
        score REAL DEFAULT 0,
        total_score INTEGER DEFAULT 100,
        status TEXT DEFAULT 'completed',
        completed_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (exam_id) REFERENCES exams(id),
        FOREIGN KEY (exam_paper_id) REFERENCES exam_papers(id)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipient_id INTEGER,
        content TEXT,
        status TEXT DEFAULT 'unread',
        type TEXT DEFAULT 'info',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (recipient_id) REFERENCES users(id)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS question_paper_relations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paper_id INTEGER,
        question_id INTEGER,
        order_num INTEGER DEFAULT 0,
        score INTEGER DEFAULT 1,
        FOREIGN KEY (paper_id) REFERENCES exam_papers(id),
        FOREIGN KEY (question_id) REFERENCES questions(id)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS exam_session_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        question_id INTEGER,
        user_answer TEXT,
        is_correct INTEGER DEFAULT 0,
        FOREIGN KEY (session_id) REFERENCES exam_sessions(id),
        FOREIGN KEY (question_id) REFERENCES questions(id)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS ai_task_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_type TEXT,
        task_data TEXT,
        status TEXT DEFAULT 'pending',
        result TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        completed_at TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS system_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        setting_key TEXT UNIQUE NOT NULL,
        setting_value TEXT,
        description TEXT,
        category TEXT DEFAULT 'system',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT,
        target TEXT,
        details TEXT,
        ip_address TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
''')

conn.commit()
conn.close()

logger.info('✓ questions 表创建完成')
logger.info('✓ exam_papers 表创建完成')
logger.info('✓ exam_results 表创建完成')
logger.info('✓ notifications 表创建完成')
logger.info('✓ question_paper_relations 表创建完成')
logger.info('✓ exam_session_details 表创建完成')
logger.info('✓ ai_task_logs 表创建完成')
logger.info('✓ system_settings 表创建完成')
logger.info('✓ audit_logs 表创建完成')
logger.info('✓ 所有数据库表创建完成')