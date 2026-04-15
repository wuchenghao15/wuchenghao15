# -*- coding: utf-8 -*-
"""
检查数据库表结构
"""

import sqlite3

def check_db_tables():
    """检查数据库中的表"""
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    print("数据库表列表:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    for table in tables:
        print(f"  - {table[0]}")
    
    # 检查是否有AI脑库相关的表
    ai_tables = [table[0] for table in tables if 'ai' in table[0].lower() or 'brain' in table[0].lower() or 'knowledge' in table[0].lower()]
    
    print("\nAI相关表:")
    for table in ai_tables:
        print(f"  - {table}")
    
    conn.close()

if __name__ == "__main__":
    check_db_tables()
