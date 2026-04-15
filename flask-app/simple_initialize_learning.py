#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版学习系统初始化脚本
直接初始化学习系统表结构，避免复杂依赖
"""

import sqlite3
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simple_initialize_learning.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SimpleInitializeLearning')

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

def initialize_tables():
    """初始化学习系统表结构"""
    logger.info("开始初始化学习系统表结构...")
    
    conn = None
    try:
        # 连接数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 创建课程表
        logger.info("创建课程表...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                language TEXT NOT NULL DEFAULT 'japanese',
                level TEXT NOT NULL DEFAULT 'beginner',
                category TEXT NOT NULL DEFAULT '日常对话',
                cover_image TEXT,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                is_public INTEGER DEFAULT 1,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')
        
        # 创建章节表
        logger.info("创建章节表...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lessons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                order_index INTEGER DEFAULT 0,
                content TEXT NOT NULL DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (course_id) REFERENCES courses(id)
            )
        ''')
        
        # 创建用户进度表
        logger.info("创建用户进度表...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                course_id INTEGER,
                lesson_id INTEGER,
                progress_type TEXT NOT NULL DEFAULT 'course',
                completed INTEGER DEFAULT 0,
                score REAL,
                last_accessed TEXT DEFAULT CURRENT_TIMESTAMP,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (course_id) REFERENCES courses(id),
                FOREIGN KEY (lesson_id) REFERENCES lessons(id)
            )
        ''')
        
        # 创建学习分析表
        logger.info("创建学习分析表...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                metric_type TEXT NOT NULL DEFAULT 'gauge',
                category TEXT NOT NULL DEFAULT 'learning',
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # 提交事务
        conn.commit()
        
        logger.info("学习系统表结构初始化完成！")
        return True
        
    except Exception as e:
        logger.error(f"初始化表结构失败: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def add_initial_data():
    """添加初始数据"""
    logger.info("开始添加初始数据...")
    
    conn = None
    try:
        # 连接数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 添加日语基础课程
        logger.info("添加日语基础入门课程...")
        cursor.execute('''
            INSERT INTO courses (title, description, language, level, category, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ("日语基础入门", "适合零基础学习者的日语入门课程，涵盖基本词汇、语法和日常对话。", "japanese", "beginner", "日常对话", 1))
        basic_japanese_id = cursor.lastrowid
        
        # 添加日语基础课程的章节
        logger.info("添加日语字母 - 平假名章节...")
        cursor.execute('''
            INSERT INTO lessons (course_id, title, description, order_index, content)
            VALUES (?, ?, ?, ?, ?)
        ''', (basic_japanese_id, "日语字母 - 平假名", "学习日语平假名的发音和书写", 1, 
              '{"sections": [{"title": "平假名简介", "content": "平假名是日语的基础字母之一。", "type": "text"}]}'))
        
        logger.info("添加日语字母 - 片假名章节...")
        cursor.execute('''
            INSERT INTO lessons (course_id, title, description, order_index, content)
            VALUES (?, ?, ?, ?, ?)
        ''', (basic_japanese_id, "日语字母 - 片假名", "学习日语片假名的发音和书写", 2, 
              '{"sections": [{"title": "片假名简介", "content": "片假名主要用于表示外来语、拟声词和强调。", "type": "text"}]}'))
        
        # 添加英语基础课程
        logger.info("添加英语基础入门课程...")
        cursor.execute('''
            INSERT INTO courses (title, description, language, level, category, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ("英语基础入门", "适合零基础学习者的英语入门课程，涵盖基本词汇、语法和日常对话。", "english", "beginner", "日常对话", 1))
        basic_english_id = cursor.lastrowid
        
        # 添加英语基础课程的章节
        logger.info("添加英语字母表章节...")
        cursor.execute('''
            INSERT INTO lessons (course_id, title, description, order_index, content)
            VALUES (?, ?, ?, ?, ?)
        ''', (basic_english_id, "英语字母表", "学习英语26个字母的发音和书写", 1, 
              '{"sections": [{"title": "字母表简介", "content": "英语使用拉丁字母表，共有26个字母。", "type": "text"}]}'))
        
        # 提交事务
        conn.commit()
        
        logger.info("初始数据添加完成！")
        return True
        
    except Exception as e:
        logger.error(f"添加初始数据失败: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def main():
    """主函数"""
    logger.info("开始初始化学习系统...")
    
    # 初始化表结构
    if initialize_tables():
        # 添加初始数据
        if add_initial_data():
            logger.info("学习系统初始化成功！")
            print("\n学习系统初始化成功！")
            print("\n已创建的表结构:")
            print("- courses: 课程表")
            print("- lessons: 章节表")
            print("- user_progress: 用户进度表")
            print("- learning_analytics: 学习分析表")
            
            print("\n已添加的初始数据:")
            print("1. 课程: 日语基础入门")
            print("   - 章节1: 日语字母 - 平假名")
            print("   - 章节2: 日语字母 - 片假名")
            print("2. 课程: 英语基础入门")
            print("   - 章节1: 英语字母表")
            
            print("\n学习系统API已注册，可通过以下路径访问:")
            print("- 获取课程列表: GET /api/learning/courses")
            print("- 获取课程详情: GET /api/learning/courses/<course_id>")
            print("- 获取课程章节: GET /api/learning/courses/<course_id>/lessons")
            print("- 获取用户进度: GET /api/learning/user/<user_id>/progress")
            print("- 更新用户进度: POST /api/learning/user/progress")
            print("- 获取用户学习摘要: GET /api/learning/user/<user_id>/summary")
            print("- 获取课程推荐: GET /api/learning/user/<user_id>/recommendations")
            return True
    
    logger.error("学习系统初始化失败！")
    print("\n学习系统初始化失败！")
    return False

if __name__ == "__main__":
    main()
