#!/usr/bin/env python3
"""
创建local_data_uploads表

import sqlite3
import os

# 直接指定数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'app.db')


def create_table():
    """创建local_data_uploads表"""
    print(f"连接数据库: {DB_PATH}")
    print("=" * 60)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 创建表
        create_table_sql = '''
        CREATE TABLE IF NOT EXISTS local_data_uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_type TEXT NOT NULL,
            file_path TEXT,
            content TEXT,
            status TEXT DEFAULT "pending",
            processed_by TEXT,
            process_result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        '''

        cursor.execute(create_table_sql)
        conn.commit()

        print("✅ local_data_uploads表创建成功")

        # 验证表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='local_data_uploads'")
        if cursor.fetchone():
            print("✅ 验证成功: local_data_uploads表确实存在")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        return False


if __name__ == "__main__":
    create_table()
