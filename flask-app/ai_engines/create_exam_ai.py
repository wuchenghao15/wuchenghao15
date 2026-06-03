# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
创建考试系统AI
负责考试系统的管理和优化,集成本地AI自动填充功能

"""
import logging
logger = logging.getLogger(__name__)
import os
import sys
import sqlite3
from contextlib import contextmanager
# JSON import removed - using database
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_exam_ai():
    """创建考试系统AI"""
    db_path = "app.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 创建考试系统AI
        exam_ai = {
            "ai_name": "exam_ai",
            "instance_id": "exam_ai",
            "collection_id": "main_ai_ensemble",
            "ai_type": "exam",
            "name": "考试系统AI",
            "description": "负责考试系统的管理和优化,集成本地AI自动填充功能,提供智能考试服务",
            "functions": str([
                "exam_management",
                "auto_fill",
                "question_generation",
                "exam_analysis",
                "personalization",
                "performance_tracking",
                "adaptive_testing",
                "cheat_detection"
            ]),
            "responsibilities": str([
                "考试系统管理",
                "智能自动填充",
                "题目生成",
                "考试分析",
                "个性化考试",
                "性能跟踪",
                "自适应测试",
                "作弊检测"
            ]),
            "config": str({
                "auto_fill": {
                    "enabled": True,
                    "fields": ["answer", "essay", "short_answer"],
                    "context_aware": True,
                    "learning_rate": 0.1
                },
                "adaptive_testing": {
                    "enabled": True,
                    "difficulty_adjustment": True,
                },
                "cheat_detection": {
                    "enabled": True,
                }
            }),
            "status": "active",
            "bound_user": "admin"
        }

        # 插入考试系统AI
        sql = """
        INSERT OR REPLACE INTO ai_instances
        (ai_name, instance_id, collection_id, ai_type, name, description, functions, responsibilities, status, config, bound_user, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """

        params = (
            exam_ai["ai_name"],
            exam_ai["instance_id"],
            exam_ai["collection_id"],
            exam_ai["ai_type"],
            exam_ai["name"],
            exam_ai["description"],
            exam_ai["functions"],
            exam_ai["responsibilities"],
            exam_ai["status"],
            exam_ai["config"],
            exam_ai["bound_user"]
        )

        cursor.execute(sql, params)
        conn.commit()

        print("考试系统AI创建成功!")
        print(f"AI名称: {exam_ai['name']}")
        print(f"类型: {exam_ai['ai_type']}")
        print(f"状态: {exam_ai['status']}")

        # 创建考试相关的表
        create_exam_tables(cursor)

        conn.close()
        return True

    except Exception as e:
        print(f"创建考试系统AI失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def create_exam_tables(cursor):
    """创建考试相关的表"""
    # 考试自动填充数据表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS exam_auto_fill (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        exam_id INTEGER,
        question_id INTEGER,
        field_name TEXT NOT NULL,
        field_value TEXT NOT NULL,
        context TEXT,
        usage_count INTEGER DEFAULT 0,
        last_used DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 考试性能数据表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS exam_performance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        exam_id INTEGER NOT NULL,
        score REAL NOT NULL,
        time_spent INTEGER, -- 秒
        total_questions INTEGER,
        difficulty_level REAL,
        weaknesses TEXT, -- JSON格式
    )
    ''')

    # 考试设置表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS exam_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        setting_key TEXT NOT NULL,
        setting_value TEXT NOT NULL,
        category TEXT,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, setting_key)
    )
    ''')

    # 考试行为数据表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS exam_behavior (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        exam_id INTEGER NOT NULL,
        question_id INTEGER NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        time_spent INTEGER -- 秒
    )
    ''')
    print("考试相关表创建成功!")

if __name__ == "__main__":
    create_exam_ai()
