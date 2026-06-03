# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
创建日语考试脚本
"""

import sqlite3
import json
import random

DATABASE_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'

def create_japanese_exam():
    """创建日语考试"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # 创建日语入门考试
        cursor.execute('''
            INSERT INTO exams 
            (name, description, category, duration, question_count, total_score, passing_score, status, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            '日语入门测试',
            '测试日语基础知识,包括五十音图、基础词汇、日常会话等',
            'japanese',
            30,
            20,
            100,
            60,
            'active',
            1
        ))
        
        exam_id = cursor.lastrowid
        print(f"创建日语入门考试成功,ID: {exam_id}")
        
        # 创建日语进阶考试
        cursor.execute('''
            INSERT INTO exams 
            (name, description, category, duration, question_count, total_score, passing_score, status, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            '日语进阶测试',
            '测试日语进阶知识,包括动词变形、语法结构、阅读理解等',
            'japanese',
            45,
            25,
            120,
            72,
            'active',
            1
        ))
        
        exam_id_advanced = cursor.lastrowid
        print(f"创建日语进阶考试成功,ID: {exam_id_advanced}")
        
        # 查询日语题目
        cursor.execute('SELECT id FROM questions WHERE category = "日语" ORDER BY RANDOM() LIMIT 50')
        japanese_questions = [row[0] for row in cursor.fetchall()]
        
        print(f"找到 {len(japanese_questions)} 道日语题目")
        
        # 关联题目到入门考试
        if len(japanese_questions) >= 20:
            for i, q_id in enumerate(japanese_questions[:20]):
                cursor.execute('''
                    INSERT INTO exam_questions (exam_id, question_id, order_num)
                    VALUES (?, ?, ?)
                ''', (exam_id, q_id, i + 1))
            print(f"已关联20道题目到日语入门考试")
        
        # 关联题目到进阶考试
        if len(japanese_questions) >= 45:
            for i, q_id in enumerate(japanese_questions[20:45]):
                cursor.execute('''
                    INSERT INTO exam_questions (exam_id, question_id, order_num)
                    VALUES (?, ?, ?)
                ''', (exam_id_advanced, q_id, i + 1))
            print(f"已关联25道题目到日语进阶考试")
        
        conn.commit()
        print("\n✅ 日语考试创建完成!")

if __name__ == "__main__":
    create_japanese_exam()
