# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
修复数据库架构问题,添加缺失的列
"""

import logging
logger = logging.getLogger(__name__)
import sqlite3
from contextlib import contextmanager
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def fix_db_schema():
    """修复数据库架构,添加缺失的列"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("检查ai_instances表结构...")

        cursor.execute("PRAGMA table_info(ai_instances)")
        columns = {col[1] for col in cursor.fetchall()}

        if 'instance_id' not in columns:
            print("添加instance_id列到ai_instances表...")
            cursor.execute("ALTER TABLE ai_instances ADD COLUMN instance_id TEXT")
            print("instance_id列添加成功")

        if 'collection_id' not in columns:
            print("添加collection_id列到ai_instances表...")
            cursor.execute("ALTER TABLE ai_instances ADD COLUMN collection_id TEXT")
            print("collection_id列添加成功")

        if 'ai_type' not in columns:
            print("添加ai_type列到ai_instances表...")
            cursor.execute("ALTER TABLE ai_instances ADD COLUMN ai_type TEXT")
            print("ai_type列添加成功")

        if 'functions' not in columns:
            print("添加functions列到ai_instances表...")
            cursor.execute("ALTER TABLE ai_instances ADD COLUMN functions TEXT")
            print("functions列添加成功")

        if 'responsibilities' not in columns:
            print("添加responsibilities列到ai_instances表...")
            cursor.execute("ALTER TABLE ai_instances ADD COLUMN responsibilities TEXT")
            print("responsibilities列添加成功")

        print("\n检查ai_plans表结构...")
        cursor.execute("PRAGMA table_info(ai_plans)")
        plan_columns = {col[1] for col in cursor.fetchall()}

        if 'tasks' not in plan_columns:
            print("添加tasks列到ai_plans表...")
            cursor.execute("ALTER TABLE ai_plans ADD COLUMN tasks TEXT")
            print("tasks列添加成功")

        conn.commit()
        print("\n数据库架构修复完成!")

    except Exception as e:
        print(f"修复数据库架构时出错: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    fix_db_schema()
