# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""创建学习结果相关表的脚本"""

import sqlite3
import os

def create_learning_results_tables():
    """创建学习结果相关的数据库表"""
    conn = sqlite3.connect('flask-app/app.db');
    cursor = conn.cursor()

    try:
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_learning_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            iteration INTEGER,
            results TEXT,
            average_score REAL,
            generated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_learning_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            result_id INTEGER,
            content_type TEXT,
            question TEXT,
            options TEXT,
            correct_answer TEXT,
            explanation TEXT,
            difficulty INTEGER,
            generated_by TEXT,
            source TEXT,
            average_score REAL,
            FOREIGN KEY (result_id) REFERENCES ai_learning_results (id)
        )
        ''')

        conn.commit()
    except Exception as e:
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_learning_results_tables()
