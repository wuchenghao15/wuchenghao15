#!/usr/bin/env python3
"""
检查系统配置表结构
"""

import sqlite3

def check_table_structure():
    """检查系统配置表结构"""
    # 连接到数据库
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # 检查表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='system_config'")
    table_exists = cursor.fetchone() is not None
    
    if table_exists:
        print("[INFO] system_config表已存在")
        
        # 检查表结构
        cursor.execute("PRAGMA table_info(system_config)")
        columns = cursor.fetchall()
        print("[INFO] 表结构:")
        for column in columns:
            print(f"  ID: {column[0]}, 名称: {column[1]}, 类型: {column[2]}, 非空: {column[3]}, 默认值: {column[4]}, 主键: {column[5]}")
        
        # 查询现有数据
        cursor.execute("SELECT COUNT(*) FROM system_config")
        count = cursor.fetchone()[0]
        print(f"[INFO] 表中现有记录数: {count}")
    else:
        print("[INFO] system_config表不存在")
    
    # 关闭连接
    conn.close()

if __name__ == "__main__":
    check_table_structure()
