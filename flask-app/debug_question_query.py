# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试脚本,用于测试Question.get_questions_by_filters方法
"""

import logging
logger = logging.getLogger(__name__)
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.question import Question


def debug_question_query():
    """调试题目查询"""
    print("=== 调试题目查询 ===")

    total_count = Question.get_question_count()
    print(f"\n总题目数量: {total_count}")

    japanese_count = Question.get_question_count(language='japanese')
    print(f"日语题目数量: {japanese_count}")

    english_count = Question.get_question_count(language='english')
    print(f"英语题目数量: {english_count}")

    print("\n == 测试获取题目 ===")

    questions = Question.get_questions_by_filters(limit=5)
    print(f"无过滤条件获取题目数量: {len(questions)}")
    for q in questions[:3]:
        print(f"  - {q.question_id}: {q.content[:30]}... (type: {q.question_type})")

    japanese_questions = Question.get_questions_by_filters(language='japanese', limit=5)
    print(f"\n日语题目获取数量: {len(japanese_questions)}")
    for q in japanese_questions[:3]:
        print(f"  - {q.question_id}: {q.content[:30]}... (type: {q.question_type})")

    mc_questions = Question.get_questions_by_filters(question_type='multiple_choice', limit=5)
    print(f"\n选择题获取数量: {len(mc_questions)}")
    for q in mc_questions[:3]:
        print(f"  - {q.question_id}: {q.content[:30]}...")

    print("\n == 模拟试卷生成时的查询 ===")
    test_questions = Question.get_questions_by_filters(
        language='japanese',
        level='beginner',
        category='日常对话',
        limit=20
    )
    print(f"模拟查询获取题目数量: {len(test_questions)}")
    for q in test_questions[:5]:
        print(f"  - {q.question_id}: {q.content[:30]}... (type: {q.question_type}, level: {q.level}, category: {q.category})")

    print("\n == 测试所有题型 ===")
    conn = Question._connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT question_type FROM questions')
    question_types = [row[0] for row in cursor.fetchall()]
    conn.close()
    print(f"数据库中存在的题型: {question_types}")

    for q_type in question_types:
        count = Question.get_question_count(question_type=q_type)
        print(f"  {q_type}: {count}道")


if __name__ == "__main__":
    debug_question_query()
