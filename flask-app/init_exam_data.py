#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
考试数据初始化脚本 - 将考试列表数据插入数据库
"""

import sqlite3
import os

DB_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'

exam_data = [
    {
        'name': '日语能力测试 N2',
        'description': '日本语能力测试N2级别，考察中级日语能力',
        'duration': 120,
        'total_questions': 100,
        'passing_score': 60.0,
        'language': '日语',
        'difficulty_level': '中级',
        'exam_type': 'standard',
        'audio_type': '关东腔'
    },
    {
        'name': '英语听力测试 (美式发音)',
        'description': '美式英语听力测试，考察美式发音听力理解能力',
        'duration': 60,
        'total_questions': 50,
        'passing_score': 60.0,
        'language': '英语',
        'difficulty_level': '初级',
        'exam_type': 'listening',
        'audio_type': '美式发音'
    },
    {
        'name': '英语听力测试 (英式发音)',
        'description': '英式英语听力测试，考察英式发音听力理解能力',
        'duration': 60,
        'total_questions': 50,
        'passing_score': 60.0,
        'language': '英语',
        'difficulty_level': '中级',
        'exam_type': 'listening',
        'audio_type': '英式发音'
    },
    {
        'name': '英语听力测试 (澳式发音)',
        'description': '澳大利亚英语听力测试，考察澳式发音听力理解能力',
        'duration': 60,
        'total_questions': 50,
        'passing_score': 60.0,
        'language': '英语',
        'difficulty_level': '中级',
        'exam_type': 'listening',
        'audio_type': '澳式发音'
    },
    {
        'name': '日语关西腔听力测试',
        'description': '日本关西腔方言听力测试，考察关西腔理解能力',
        'duration': 45,
        'total_questions': 30,
        'passing_score': 60.0,
        'language': '日语',
        'difficulty_level': '高级',
        'exam_type': 'listening',
        'audio_type': '关西腔'
    },
    {
        'name': '日语关东腔听力测试',
        'description': '日本关东腔标准日语听力测试',
        'duration': 45,
        'total_questions': 35,
        'passing_score': 60.0,
        'language': '日语',
        'difficulty_level': '中级',
        'exam_type': 'listening',
        'audio_type': '关东腔'
    },
    {
        'name': '摸底测试 - 综合能力评估',
        'description': '自适应摸底测试，全面评估学习者综合能力水平',
        'duration': 90,
        'total_questions': 80,
        'passing_score': 0.0,
        'language': '中文',
        'difficulty_level': '自适应',
        'exam_type': 'placement',
        'audio_type': None
    },
    {
        'name': '日语能力测试 N1',
        'description': '日本语能力测试N1级别，考察高级日语能力',
        'duration': 180,
        'total_questions': 110,
        'passing_score': 60.0,
        'language': '日语',
        'difficulty_level': '高级',
        'exam_type': 'standard',
        'audio_type': '关东腔'
    },
    {
        'name': '日语能力测试 N3',
        'description': '日本语能力测试N3级别，考察初中级日语能力',
        'duration': 90,
        'total_questions': 70,
        'passing_score': 60.0,
        'language': '日语',
        'difficulty_level': '初级',
        'exam_type': 'standard',
        'audio_type': '关东腔'
    },
    {
        'name': '英语综合能力测试',
        'description': '英语综合能力评估，包括听力、阅读、语法',
        'duration': 120,
        'total_questions': 80,
        'passing_score': 60.0,
        'language': '英语',
        'difficulty_level': '中级',
        'exam_type': 'comprehensive',
        'audio_type': '美式发音'
    }
]

def init_exam_data():
    """初始化考试数据"""
    print("=== 初始化考试数据 ===")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 检查并添加必要的列
    cursor.execute("PRAGMA table_info(t_a4394fa841fb07b4)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'language' not in columns:
        cursor.execute("ALTER TABLE t_a4394fa841fb07b4 ADD COLUMN language TEXT")
        print("✓ 添加 language 列")
    
    if 'difficulty_level' not in columns:
        cursor.execute("ALTER TABLE t_a4394fa841fb07b4 ADD COLUMN difficulty_level TEXT")
        print("✓ 添加 difficulty_level 列")
    
    if 'exam_type' not in columns:
        cursor.execute("ALTER TABLE t_a4394fa841fb07b4 ADD COLUMN exam_type TEXT")
        print("✓ 添加 exam_type 列")
    
    if 'audio_type' not in columns:
        cursor.execute("ALTER TABLE t_a4394fa841fb07b4 ADD COLUMN audio_type TEXT")
        print("✓ 添加 audio_type 列")
    
    conn.commit()
    
    # 插入考试数据
    inserted = 0
    for exam in exam_data:
        cursor.execute("SELECT id FROM t_a4394fa841fb07b4 WHERE name = ?", (exam['name'],))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO t_a4394fa841fb07b4 
                (name, description, duration, total_questions, passing_score, is_active, language, difficulty_level, exam_type, audio_type)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
            ''', (
                exam['name'],
                exam['description'],
                exam['duration'],
                exam['total_questions'],
                exam['passing_score'],
                exam['language'],
                exam['difficulty_level'],
                exam['exam_type'],
                exam['audio_type']
            ))
            inserted += 1
    
    conn.commit()
    conn.close()
    
    print(f"✓ 成功插入 {inserted} 条考试数据")
    print("=== 考试数据初始化完成 ===")

if __name__ == '__main__':
    init_exam_data()