# -*- coding: utf-8 -*-
#!/usr/bin/env python3
import logging
logger = logging.getLogger(__name__)
import sqlite3
from contextlib import contextmanager
import os

def check_database():
    """检查数据库结构"""
    conn = sqlite3.connect('data/mtscos_ai_project.db')
    cursor = conn.cursor()
    
    # 获取所有表名
    print("数据库表:")
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
    tables = cursor.fetchall()
    for table in tables:
        print(f"- {table[0]}")
    
    # 检查questions表结构
    print("\nquestions表结构:")
    cursor.execute('PRAGMA table_info(questions)')
    columns = cursor.fetchall()
    for column in columns:
        print(f"- {column[1]}: {column[2]}")
    
    # 关闭连接
    conn.close()

if __name__ == '__main__':
    check_database()
