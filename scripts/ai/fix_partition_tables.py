# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复分区表结构，使其与原表字段一致
"""

import sqlite3
import sys
import os

def fix_partition_tables(db_path):
    """修复分区表"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取questions表结构
    cursor.execute("PRAGMA table_info(questions)")
    columns = cursor.fetchall()
    
    column_defs = []
    for col in columns:
        col_name = col[1]
        col_type = col[2]
        is_pk = col[5] == 1
        
        if is_pk:
            column_defs.append(f"{col_name} {col_type} PRIMARY KEY")
        else:
            column_defs.append(f"{col_name} {col_type}")
    
    columns_str = ", ".join(column_defs)
    
    # 删除旧的分区表
    cursor.execute("DROP TABLE IF EXISTS questions_p0")
    cursor.execute("DROP TABLE IF EXISTS questions_p1")
    
    # 创建新的分区表
    cursor.execute(f"CREATE TABLE questions_p0 ({columns_str})")
    cursor.execute(f"CREATE TABLE questions_p1 ({columns_str})")
    
    # 分布数据
    cursor.execute("INSERT INTO questions_p0 SELECT * FROM questions WHERE id % 2 = 0")
    print(f"✓ questions_p0: {cursor.rowcount} 条记录")
    
    cursor.execute("INSERT INTO questions_p1 SELECT * FROM questions WHERE id % 2 = 1")
    print(f"✓ questions_p1: {cursor.rowcount} 条记录")
    
    # 更新视图
    cursor.execute("DROP VIEW IF EXISTS v_questions")
    cursor.execute("CREATE VIEW v_questions AS SELECT * FROM questions_p0 UNION ALL SELECT * FROM questions_p1")
    print("✓ 视图已更新")
    
    conn.commit()
    conn.close()
    print("✓ 分区表修复完成")

if __name__ == "__main__":
    db_path = "app.db"
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    fix_partition_tables(db_path)