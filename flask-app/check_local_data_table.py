#!/usr/bin/env python3
"""
检查本地数据上传表是否存在

import sqlite3
from app.config import Config


def check_local_data_table():
    """检查local_data_uploads表是否存在并显示表结构"""
    print(f"检查数据库: {Config.DATABASE_PATH}")
    print("=" * 60)

    # 连接数据库并检查表结构
    try:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()

        # 检查local_data_uploads表是否存在
        print("1. 检查local_data_uploads表:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='local_data_uploads'")
        if cursor.fetchone():
            print("   ✅ local_data_uploads表存在")

            # 查看表结构
            print("   表结构:")
            cursor.execute('PRAGMA table_info(local_data_uploads)')
            columns = cursor.fetchall()
            for col in columns:
                print(f"   {col[1]}: {col[2]} (PK: {col[5]==1})")

            # 查看当前记录数
            cursor.execute("SELECT COUNT(*) FROM local_data_uploads")
            count = cursor.fetchone()[0]
            print(f"   当前记录数: {count}")
        else:
            print("   ❌ local_data_uploads表不存在")

        conn.close()
        return True

    except Exception as e:
        print(f"检查数据库失败: {e}")
        return False


if __name__ == "__main__":
    check_local_data_table()
