#!/usr/bin/env python3
"""
创建考题生成AI
负责考题生成，集成本地AI自动填充拓展功能
"""

import os
import sys
import sqlite3
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_question_generator_ai():
    """创建考题生成AI"""
    db_path = "app.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建考题生成AI
        question_generator_ai = {
            "ai_name": "question_generator_ai",
            "instance_id": "question_generator_ai",
            "collection_id": "main_ai_ensemble",
            "ai_type": "question_generator",
            "name": "考题生成AI",
            "description": "负责考题生成，集成本地AI自动填充拓展功能，提供智能题目生成服务",
            "functions": json.dumps([
                "question_generation",
                "auto_fill",
                "difficulty_adjustment",
                "question_analysis",
                "personalization",
                "question_optimization",
                "adaptive_questioning",
                "quality_assurance"
            ]),
            "responsibilities": json.dumps([
                "考题生成",
                "智能自动填充",
                "难度调整",
                "题目分析",
                "个性化题目",
                "题目优化",
                "自适应出题",
                "质量保证"
            ]),
            "status": "active",
            "config": json.dumps({
                "auto_fill": {
                    "enabled": True,
                    "fields": ["question", "options", "answer", "explanation"],
                    "context_aware": True,
                    "learning_rate": 0.1
                },
                "question_generation": {
                    "enabled": True,
                    "types": ["multiple_choice", "fill_blank", "essay", "short_answer"],
                    "difficulty_levels": [1, 2, 3, 4, 5],
                    "adaptive": True
                },
                "quality_control": {
                    "enabled": True,
                    "duplicate_detection": True,
                    "difficulty_validation": True,
                    "answer_validation": True
                }
            }),
            "bound_user": "admin"
        }
        
        # 插入考题生成AI
        sql = """
        INSERT OR REPLACE INTO ai_instances 
        (ai_name, instance_id, collection_id, ai_type, name, description, 
         functions, responsibilities, status, config, bound_user, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """
        
        params = (
            question_generator_ai["ai_name"],
            question_generator_ai["instance_id"],
            question_generator_ai["collection_id"],
            question_generator_ai["ai_type"],
            question_generator_ai["name"],
            question_generator_ai["description"],
            question_generator_ai["functions"],
            question_generator_ai["responsibilities"],
            question_generator_ai["status"],
            question_generator_ai["config"],
            question_generator_ai["bound_user"]
        )
        
        cursor.execute(sql, params)
        conn.commit()
        
        print("考题生成AI创建成功！")
        print(f"AI名称: {question_generator_ai['name']}")
        print(f"类型: {question_generator_ai['ai_type']}")
        print(f"状态: {question_generator_ai['status']}")
        
        # 创建考题生成相关的表
        create_question_generator_tables(cursor)
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"创建考题生成AI失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def create_question_generator_tables(cursor):
    """创建考题生成相关的表"""
    # 考题生成模板表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS question_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_name TEXT NOT NULL,
        question_type TEXT NOT NULL,
        difficulty_level INTEGER NOT NULL,
        subject TEXT,
        template_content TEXT NOT NULL,
        variables TEXT, -- JSON格式
        usage_count INTEGER DEFAULT 0,
        success_rate REAL DEFAULT 0.0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 考题生成历史表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS question_generation_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        exam_id INTEGER,
        question_type TEXT NOT NULL,
        difficulty_level INTEGER,
        subject TEXT,
        generated_content TEXT NOT NULL,
        template_used INTEGER,
        quality_score REAL,
        user_feedback TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 考题自动填充数据表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS question_auto_fill (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        field_name TEXT NOT NULL,
        field_value TEXT NOT NULL,
        context TEXT, -- JSON格式
        question_type TEXT,
        subject TEXT,
        usage_count INTEGER DEFAULT 0,
        last_used DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 考题质量评估表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS question_quality (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER NOT NULL,
        clarity_score REAL,
        difficulty_accuracy REAL,
        answer_correctness REAL,
        overall_score REAL,
        feedback TEXT,
        evaluator TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    print("考题生成相关表创建成功！")

if __name__ == "__main__":
    create_question_generator_ai()
