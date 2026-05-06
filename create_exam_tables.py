#!/usr/bin/env python3
"""
创建试卷相关表的脚本

import sqlite3

def create_exam_tables():
    """创建试卷相关的数据库表"""
    conn = sqlite3.connect('flask-app/app.db')
    cursor = conn.cursor()

    try:
        # 创建试卷表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS exam_papers (
            id TEXT PRIMARY KEY,
            title TEXT,
            duration INTEGER,
            total_score INTEGER,
            language TEXT,
            difficulty_level TEXT,
            generated_at TEXT,
            version TEXT,
            total_questions INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 创建试卷部分表
        cursor.execute('''
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paper_id TEXT,
            type TEXT,
            title TEXT,
            total_questions INTEGER,
            score_per_question REAL,
        ''')

        # 创建试卷题目表
        cursor.execute('''
            paper_id TEXT,
            question_id TEXT,
            question_text TEXT,
            question_type TEXT,
            subtype TEXT,
            options TEXT,
            explanation TEXT,
            score REAL,
            audio_url TEXT,
            audio_type TEXT,
            audio_duration INTEGER,
            audio_speed TEXT,
            generated_by TEXT,
            source TEXT,
            passage TEXT,
            FOREIGN KEY (paper_id) REFERENCES exam_papers (id),
            FOREIGN KEY (section_id) REFERENCES exam_sections (id)
        )
        ''')

        conn.commit()
        print("试卷相关表创建成功")
    except Exception as e:
    finally:
        cursor.close()

if __name__ == "__main__":
    create_exam_tables()
