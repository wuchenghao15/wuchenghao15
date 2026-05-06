#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试脚本，直接执行SQL查询，查看数据库中的实际数据

import sys
import os
import sqlite3

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.question import Question


def debug_database():
    """调试数据库"""
    print("=== 调试数据库 ===")

    # 直接连接数据库
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
    print(f"数据库路径: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 测试1：查看表结构
    print("\n=== 查看表结构 ===")
    cursor.execute("PRAGMA table_info(questions)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]}: {col[2]} {'PRIMARY KEY' if col[5] else ''}")

    # 测试2：查看前10行数据
    print("\n=== 查看前10行数据 ===")
    cursor.execute("SELECT id, content, question_type, level, category FROM questions LIMIT 10")
    rows = cursor.fetchall()
    for row in rows:
        print(f"  id: {row[0]}, content: {row[1][:30]}..., type: {row[2]}, level: {row[3]}, category: {row[4]}")

    # 测试3：查看id的分布
    print("\n=== 查看id的分布 ===")
    cursor.execute("SELECT MIN(id), MAX(id), COUNT(DISTINCT id), COUNT(*) FROM questions")
    min_id, max_id, distinct_count, total_count = cursor.fetchone()
    print(f"  最小id: {min_id}")
    print(f"  最大id: {max_id}")
    print(f"  不同id数量: {distinct_count}")
    print(f"  总记录数: {total_count}")

    # 测试4：查看具体的id=1的记录
    print("\n=== 查看id=1的记录 ===")
    cursor.execute("SELECT id, content, question_type, level, category FROM questions WHERE id = 1 LIMIT 5")
    rows = cursor.fetchall()
        print(f"  id: {row[0]}, content: {row[1][:30]}..., type: {row[2]}, level: {row[3]}, category: {row[4]}")
    # 测试5：测试查询带有id的记录
    cursor.execute("SELECT id FROM questions ORDER BY RANDOM() LIMIT 5")
    rows = cursor.fetchall()

    # 关闭连接
    conn.close()

    # 测试6：测试Question.get_questions_by_filters返回的对象
    print("\n=== 测试Question.get_questions_by_filters返回的对象 ===")
    questions = Question.get_questions_by_filters(limit=5)
    for i, q in enumerate(questions):
        print(f"  问题 {i+1}:")
        print(f"    id: {q.question_id}")
        print(f"    content: {q.content[:30]}...")
        print(f"    type: {q.question_type}")
        print(f"    对象ID: {id(q)}")


if __name__ == "__main__":
    debug_database()
