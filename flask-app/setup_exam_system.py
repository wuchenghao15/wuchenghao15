# -*- coding: utf-8 -*-
#!/usr/bin/env python3
import sqlite3
import json
from datetime import datetime
import sys

DATABASE_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'

def log_test_result(test_module, test_name, status, error_message='', solution='', test_data=None):
    """记录测试结果"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO system_test_results 
            (test_module, test_name, status, error_message, solution_provided, test_data)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            test_module, test_name, status, error_message, 
            solution, json.dumps(test_data) if test_data else None
        ))
        
        conn.commit()

def init_sample_data():
    """初始化考试系统样本数据"""
    print("="*70)
    print("📝 初始化考试系统数据")
    print("="*70)
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # 创建示例考试
        exams = [
            {
                "name": "Python 基础入门测试",
                "description": "测试Python编程基础知识,包括变量、数据类型、循环和函数等",
                "category": "programming",
                "duration": 30,
                "question_count": 10,
                "total_score": 100,
                "passing_score": 60
            },
            {
                "name": "数学运算能力测试",
                "description": "基础数学运算、代数几何问题测试",
                "category": "math",
                "duration": 45,
                "question_count": 15,
                "total_score": 100,
                "passing_score": 70
            },
            {
                "name": "英语词汇测试",
                "description": "测试英语词汇量和阅读理解能力",
                "category": "language",
                "duration": 25,
                "question_count": 20,
                "total_score": 100,
                "passing_score": 65
            },
            {
                "name": "计算机科学基础",
                "description": "计算机科学基础概念、数据结构、算法入门",
                "category": "computer_science",
                "duration": 60,
                "question_count": 25,
                "total_score": 100,
                "passing_score": 60
            },
            {
                "name": "人工智能入门",
                "description": "AI基础概念、机器学习入门知识测试",
                "category": "ai",
                "duration": 40,
                "question_count": 12,
                "total_score": 100,
                "passing_score": 70
            }
        ]
        
        for exam in exams:
            cursor.execute('''
                INSERT INTO exams 
                (name, description, category, duration, question_count, total_score, passing_score, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'active')
            ''', (
                exam['name'], exam['description'], exam['category'],
                exam['duration'], exam['question_count'], exam['total_score'], exam['passing_score']
            ))
            print(f"✅ 创建: {exam['name']}")
        
        # 创建示例题目
        questions = [
            {
                "question_text": "Python中,以下哪个函数用于获取列表长度?",
                "question_type": "multiple_choice",
                "options": json.dumps(["count()", "length()", "len()", "size()"]),
                "correct_answer": "len()",
                "explanation": "len()函数返回对象的长度或项目个数",
                "difficulty": "easy",
                "category": "programming",
                "points": 10
            },
            {
                "question_text": "3 + 4 * 2 = ?",
                "question_type": "single_choice",
                "options": json.dumps(["14", "11", "24", "7"]),
                "correct_answer": "11",
                "explanation": "根据运算优先级,先乘后加:4*2=8,3+8=11",
                "difficulty": "easy",
                "category": "math",
                "points": 10
            },
            {
                "question_text": "What is the past tense of 'go'?",
                "question_type": "multiple_choice",
                "options": json.dumps(["goed", "went", "gone", "going"]),
                "correct_answer": "went",
                "explanation": "'go'的过去式是'went'",
                "difficulty": "easy",
                "category": "language",
                "points": 10
            },
            {
                "question_text": "以下哪个数据结构是先进先出(FIFO)?",
                "question_type": "multiple_choice",
                "options": json.dumps(["栈", "队列", "树", "图"]),
                "correct_answer": "队列",
                "explanation": "队列(Queue)是一种先进先出的数据结构",
                "difficulty": "medium",
                "category": "computer_science",
                "points": 10
            },
            {
                "question_text": "机器学习中,监督学习需要什么?",
                "question_type": "multiple_choice",
                "options": json.dumps(["标签数据", "无标签数据", "GPU", "大数据"]),
                "correct_answer": "标签数据",
                "explanation": "监督学习需要标记好的训练数据",
                "difficulty": "medium",
                "category": "ai",
                "points": 10
            }
        ]
        
        for q in questions:
            cursor.execute('''
                INSERT INTO questions 
                (question_text, question_type, options, correct_answer, explanation, difficulty, category, points)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                q['question_text'], q['question_type'], q['options'],
                q['correct_answer'], q['explanation'], q['difficulty'], q['category'], q['points']
            ))
        
        # 关联题目到考试
        cursor.execute("SELECT id FROM exams")
        exam_ids = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT id FROM questions")
        question_ids = [row[0] for row in cursor.fetchall()]
        
        for exam_id in exam_ids:
            for order_num, question_id in enumerate(question_ids, 1):
                cursor.execute('''
                    INSERT INTO exam_questions (exam_id, question_id, order_num)
                    VALUES (?, ?, ?)
                ''', (exam_id, question_id, order_num))
        
        conn.commit()
        log_test_result('exam_system', 'init_sample_data', 'success')
        print("\n✅ 考试系统数据初始化完成!")

def verify_integration():
    """验证考试系统集成"""
    print("\n" + "="*70)
    print("🔍 验证考试系统")
    print("="*70)
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # 检查考试数量
        cursor.execute("SELECT COUNT(*) FROM exams")
        exam_count = cursor.fetchone()[0]
        
        # 检查题目数量
        cursor.execute("SELECT COUNT(*) FROM questions")
        question_count = cursor.fetchone()[0]
        
        # 列出所有考试
        cursor.execute("SELECT id, name, category FROM exams")
        exam_list = cursor.fetchall()
        
        print(f"✅ 考试数量: {exam_count}")
        print(f"✅ 题目数量: {question_count}")
        print(f"\n📋 考试列表:")
        for exam in exam_list:
            print(f"   - ID: {exam[0]}, {exam[1]} ({exam[2]})")
        
        log_test_result('exam_system', 'verify_integration', 'success', test_data={
            'exam_count': exam_count,
            'question_count': question_count
        })
        
        return exam_count > 0

if __name__ == '__main__':
    init_sample_data()
    verify_integration()
    print("\n" + "="*70)
    print("✨ 考试系统集成完成!")
    print("="*70)
