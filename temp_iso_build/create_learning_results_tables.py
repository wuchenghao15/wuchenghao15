#!/usr/bin/env python3
"""
创建学习结果相关表的脚本

import sqlite3

def create_learning_results_tables():
    """创建学习结果相关的数据库表"""
    conn = sqlite3.connect('flask-app/app.db')
    cursor = conn.cursor()

    try:
        # 创建AI学习结果表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_learning_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            iteration INTEGER,
            results TEXT,
            average_score REAL,
            generated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 创建AI学习内容表
        cursor.execute('''
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

        conn.commit()
    except Exception as e:
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_learning_results_tables()
