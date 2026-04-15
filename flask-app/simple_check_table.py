#!/usr/bin/env python3
"""
简单检查表脚本，不加载应用上下文
"""

import sqlite3
import os

# 直接指定数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'mtscos_ai.db')


def check_table():
    """检查local_data_uploads表是否存在"""
    print(f"检查数据库: {DB_PATH}")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查local_data_uploads表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='local_data_uploads'")
        if cursor.fetchone():
            print("✅ local_data_uploads表存在")
            
            # 显示表结构
            cursor.execute('PRAGMA table_info(local_data_uploads)')
            columns = cursor.fetchall()
            print("表结构:")
            for col in columns:
                print(f"  {col[1]}: {col[2]} (PK: {col[5]==1})")
        else:
            print("❌ local_data_uploads表不存在")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"检查失败: {e}")
        return False


if __name__ == "__main__":
    check_table()
