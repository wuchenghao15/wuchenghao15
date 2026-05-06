#!/usr/bin/env python3
"""
初始化题库数据库表

import sqlite3
import logging
from datetime import datetime, UTC

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('init_question_db')

def init_question_database(db_path='flask-app/app.db'):
    """初始化题库数据库表"""
    logger.info(f"开始初始化题库数据库，路径: {db_path}")

    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 创建题目分类表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS question_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        ''')
        logger.info("已创建 question_categories 表")

        # 创建题目语种表
        cursor.execute('''
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL,
        )
        ''')

        cursor.execute('''
            name TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        ''')
        logger.info("已创建 question_levels 表")

        cursor.execute('''
            content TEXT NOT NULL,
            answer TEXT NOT NULL,
            language_id INTEGER,
            level_id INTEGER,
            options TEXT DEFAULT '[]',
            created_at TEXT NOT NULL,
            FOREIGN KEY (category_id) REFERENCES question_categories(id),
            FOREIGN KEY (language_id) REFERENCES question_languages(id),
            FOREIGN KEY (level_id) REFERENCES question_levels(id)
        )
        ''')
        logger.info("已创建 questions 表")

        # 插入初始数据

        # 插入分类
        cursor.execute('''
        ('词汇', '词汇相关题目', ?, ?),
        ('语法', '语法相关题目', ?, ?),
        ('阅读', '阅读相关题目', ?, ?),
        ('通用', '通用题目', ?, ?)
        ''', (now, now, now, now, now, now, now, now))
        logger.info("已插入初始分类数据")
        # 插入语种
        cursor.execute('''
        ('日语', 'ja', ?, ?),
        ('中文', 'zh', ?, ?)
        ''', (now, now, now, now, now, now))
        logger.info("已插入初始语种数据")

        # 插入等级
        for i in range(1, 6):
            cursor.execute('''
            (?, ?, ?, ?, ?)
            ''', (f"{i}级", i, f"{i}级难度题目", now, now))
        logger.info("已插入初始等级数据")

        # 提交事务
        conn.commit()
        logger.info("题库数据库初始化完成")

    except Exception as e:
        logger.error(f"初始化题库数据库失败: {str(e)}")
        conn.rollback()
        raise
    finally:
        # 关闭连接
        conn.close()

if __name__ == "__main__":
    init_question_database()
