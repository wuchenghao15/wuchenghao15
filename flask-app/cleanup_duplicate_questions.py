# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理数据库中的重复题目
"""

import logging
logger = logging.getLogger(__name__)
import sys
import os
import sqlite3
from contextlib import contextmanager

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app.config import Config

def cleanup_duplicate_questions():
    """清理数据库中的重复题目"""
    print("开始清理数据库中的重复题目...")

    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor = conn.cursor()

    try:
        print("查询重复题目...")
        cursor.execute('''
            SELECT content, language, category, COUNT(*) as count
            FROM questions
            GROUP BY LOWER(content), language, category
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        ''')

        duplicate_groups = cursor.fetchall()
        print(f"发现 {len(duplicate_groups)} 组重复题目")

        total_deleted = 0
        for content, language, category, count in duplicate_groups:
            print(f"\n处理重复题目: {content} (语言: {language}, 类别: {category}, 重复数量: {count})")

            cursor.execute('''
                SELECT id FROM questions
                WHERE LOWER(content) = LOWER(?) AND language = ? AND category = ?
                ORDER BY id
            ''', (content, language, category))
            question_ids = [row[0] for row in cursor.fetchall()]

            if len(question_ids) > 1:
                ids_to_delete = question_ids[1:]
                cursor.executemany('DELETE FROM questions WHERE id = ?', [(id,) for id in ids_to_delete])
                deleted_count = len(ids_to_delete)
                total_deleted += deleted_count
                print(f"  删除了 {deleted_count} 道重复题目,保留了ID为 {question_ids[0]} 的题目")

        conn.commit()
        print(f"\n清理完成,共删除了 {total_deleted} 道重复题目")

        cursor.execute('SELECT COUNT(*) FROM questions')
        total_questions = cursor.fetchone()[0]
        print(f"清理后数据库中共有 {total_questions} 道题目")

        cursor.execute('''
            SELECT content, language, category
            FROM questions
            GROUP BY LOWER(content), language, category
            HAVING COUNT(*) > 1
        ''')
        remaining_duplicates = cursor.fetchall()
        print(f"清理后剩余重复题目组数: {len(remaining_duplicates)}")
        return total_deleted
    finally:
        conn.close()

def optimize_database():
    """优化数据库"""
    print("\n开始优化数据库...")

    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('VACUUM')
        print("数据库优化完成")
    finally:
        conn.close()

if __name__ == "__main__":
    deleted_count = cleanup_duplicate_questions()
    if deleted_count > 0:
        optimize_database()
    else:
        print("没有发现重复题目,无需优化")
    print("\n清理工作完成!")
