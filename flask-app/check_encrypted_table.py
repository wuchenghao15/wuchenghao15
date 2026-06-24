# -*- coding: utf-8 -*-
#!/usr/bin/env python3
import logging
logger = logging.getLogger(__name__)
import sqlite3
from contextlib import contextmanager
import os

# 连接数据库
with sqlite3.connect('data/mtscos_ai_project.db') as conn:
    conn_cursor = conn.cursor()
    cursor = conn.cursor()
    
    # 检查加密表的结构
    encrypted_table_name = 't_de70b7adf040777a'
    print(f"加密表 {encrypted_table_name} 的结构:")
    cursor.execute(f'PRAGMA table_info({encrypted_table_name})')
    columns = cursor.fetchall()
    for column in columns:
        print(f"- {column[1]}: {column[2]}")
    
    # 关闭连接
