#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
题库数据库升级脚本
用于创建和升级题库相关表结构

import sqlite3
import os
# JSON import removed - using database
# 获取数据库路径
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'mtscos_ai.db')

print(f"数据库路径: {DATABASE_PATH}")
print("=" * 60)

# 确保instance目录存在
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

try:
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    print("✅ 成功连接到数据库")

    # 1. 创建题目表
    print("\n1. 创建/更新题目表 (questions):")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            language TEXT NOT NULL,
            level TEXT NOT NULL,
            category TEXT NOT NULL,
            content TEXT NOT NULL,
            options TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            explanation TEXT,
            source TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            usage_count INTEGER DEFAULT 0,
            last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            accuracy REAL DEFAULT NULL,
            question_type TEXT DEFAULT 'multiple_choice' NOT NULL
        )
    ''')
    print("   ✅ 题目表创建/更新成功")

    # 2. 创建题目统计信息表
    print("\n2. 创建/更新题目统计信息表 (question_stats):")
    cursor.execute('''
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT NOT NULL,
            question_type TEXT NOT NULL,
            used_count INTEGER DEFAULT 0,
            avg_accuracy REAL DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(level, category, question_type)
        )
    ''')
    print("   ✅ 题目统计信息表创建/更新成功")

    # 3. 创建用户答题记录表
    cursor.execute('''
            user_id TEXT NOT NULL,
            question_id INTEGER NOT NULL,
            is_correct INTEGER DEFAULT 0,
            time_spent INTEGER DEFAULT 0,
            answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
        )
    ''')
    print("   ✅ 用户答题记录表创建/更新成功")

    # 4. 创建索引以优化查询性能
    print("\n4. 创建索引:")
    # 题目表索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_questions_category ON questions(category)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_questions_type ON questions(question_type)')

    # 用户答题表索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_answers_user ON user_answers(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_answers_question ON user_answers(question_id)')

    print("   ✅ 索引创建成功")

    # 5. 初始化示例题目数据
    print("\n5. 初始化示例题目数据:")

    # 检查是否已有题目数据
    cursor.execute("SELECT COUNT(*) FROM questions")
    existing_count = cursor.fetchone()[0]

    if existing_count == 0:
        # 示例日语题目数据
        sample_questions = [
            {
                "language": "japanese",
                "level": "beginner",
                "category": "日常对话",
                "content": "こんにちは」とは何の意味ですか？",
                "options": ["再见", "你好", "谢谢", "对不起"],
                "correct_answer": "1",
                "explanation": "「こんにちは」は昼間の挨拶で、中国語の「你好」に相当します。",
                "source": "ai_generated",
                "question_type": "multiple_choice"
            },
            {
                "language": "japanese",
                "level": "beginner",
                "category": "日常对话",
                "content": "「ありがとう」とは何の意味ですか？",
                "options": ["谢谢", "再见", "你好", "对不起"],
                "correct_answer": "0",
                "explanation": "「ありがとう」は感謝を表す言葉で、中国語の「谢谢」に相当します。",
                "source": "ai_generated",
                "question_type": "multiple_choice"
            },
                "language": "japanese",
                "category": "语法",
                "options": ["～を～ます", "～は～を～ました", "～に～を～ます", "～で～を～ます"],
                "explanation": "この文は過去形の他動詞文で、「～は～を～ました」の文型です。",
                "source": "ai_generated",
                "question_type": "multiple_choice"
            }

            cursor.execute('''
            ''', (
                str(q['options']), q['correct_answer'],
                q['explanation'], q['source'], q['question_type']
            ))
            print(f"   ✅ 插入示例题目 {i}/{len(sample_questions)}")
        print(f"   ✅ 共插入 {len(sample_questions)} 道示例题目")
    else:

    # 6. 初始化题目统计信息
    cursor.execute('''
        SELECT
            level,
            category,
            question_type,
            COUNT(*) as total_count,
            COALESCE(SUM(usage_count), 0) as used_count,
            0 as correct_rate,
            COALESCE(AVG(accuracy), 0) as avg_accuracy
        FROM questions
        GROUP BY level, category, question_type
    ''')
    print("   ✅ 题目统计信息初始化成功")

    # 7. 提交所有更改
    conn.commit()
    print("\n✅ 所有更改已提交到数据库")

    # 8. 显示最终状态
    print("\n" + "=" * 60)
    print("📊 数据库升级完成，当前状态:")

    cursor.execute("SELECT COUNT(*) FROM questions")
    question_count = cursor.fetchone()[0]
    print(f"   题目数量: {question_count}")

    # 表结构验证
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"   表数量: {len(tables)}")
    for table in tables:
        print(f"   - {table[0]}")

    conn.close()
    print("\n🎉 题库数据库升级成功完成！")

    print(f"\n❌ 数据库升级失败: {e}")
    exit(1)

"""