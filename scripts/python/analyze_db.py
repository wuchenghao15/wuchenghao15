#!/usr/bin/env python3
import sqlite3
import os

db_path = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'

def analyze_database():
    logger.info(f"=== 数据库分析 ===")
    logger.info(f"数据库路径: {db_path}")
    logger.info(f"数据库大小: {os.path.getsize(db_path) / (1024 * 1024):.2f} MB")
    logger.info()
    
    conn = sqlite3.connect(db_path, timeout=30)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    logger.info(f"总表数: {len(tables)}")
    logger.info()
    
    table_info = []
    
    for (table_name,) in tables:
        cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
        row_count = cursor.fetchone()[0]
        
        cursor.execute(f"PRAGMA table_info([{table_name}])")
        columns = cursor.fetchall()
        col_count = len(columns)
        
        cursor.execute(f"PRAGMA index_list([{table_name}])")
        indexes = cursor.fetchall()
        idx_count = len(indexes)
        
        table_info.append({
            'name': table_name,
            'rows': row_count,
            'columns': col_count,
            'indexes': idx_count
        })
        
        logger.info(f"表: {table_name}")
        logger.info(f"  行数: {row_count:,}")
        logger.info(f"  列数: {col_count}")
        logger.info(f"  索引数: {idx_count}")
        logger.info()
    
    conn.close()
    
    return table_info

if __name__ == '__main__':
    analyze_database()