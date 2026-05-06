#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单脚本，用于检查数据库表结构

import sqlite3
import os

# 获取数据库路径
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'mtscos_ai.db')

print(f"检查数据库: {DATABASE_PATH}")
print("=" * 50)

# 连接数据库并检查表结构
try:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # 检查questions表结构
    print("1. 检查questions表结构:")
    cursor.execute('PRAGMA table_info(questions)')
    columns = cursor.fetchall()
    print(f"   列数: {len(columns)}")
    for col in columns:
        print(f"   {col[1]}: {col[2]} (PK: {col[5]==1})")

    # 检查是否存在题目统计信息表
    print("\n2. 检查question_stats表:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='question_stats'")
    if cursor.fetchone():
        print("   ✅ question_stats表存在")
        cursor.execute('PRAGMA table_info(question_stats)')
        stats_cols = cursor.fetchall()
        for col in stats_cols:
            print(f"   {col[1]}: {col[2]}")
    else:
        print("   ❌ question_stats表不存在")

    # 检查用户答题记录表
    print("\n3. 检查user_answers表:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_answers'")
    if cursor.fetchone():
    else:
        print("   ❌ user_answers表不存在")
    # 检查题目数量
    print("\n4. 检查题目数量:")
    cursor.execute("SELECT COUNT(*) FROM questions")
    question_count = cursor.fetchone()[0]
    print(f"   题目总数: {question_count}")

    conn.close()
    print("\n✅ 数据库检查完成")

except sqlite3.Error as e:
    print(f"\n❌ 数据库操作失败: {e}")
    exit(1)

"""