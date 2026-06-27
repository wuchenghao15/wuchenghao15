#!/usr/bin/env python3
"""
MTSCOS AI 教育管理系统 - 简化版课程拓展器
在单个数据库连接中完成所有操作，避免锁定问题
"""

import sqlite3
import json
import random
from datetime import datetime

class SimpleCourseExpander:
    """简化版课程和练习拓展器"""
    
    def __init__(self, db_path='simple_courses.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """建立单个数据库连接"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        print("数据库连接已建立")
        
    def close(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("数据库连接已关闭")
        
    def create_tables(self):
        """创建表结构"""
        print("创建表结构...")
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id TEXT UNIQUE NOT NULL,
                course_name TEXT NOT NULL,
                course_icon TEXT,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS exams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_id TEXT UNIQUE NOT NULL,
                course_id TEXT NOT NULL,
                exam_name TEXT NOT NULL,
                description TEXT,
                duration INTEGER DEFAULT 60,
                question_count INTEGER DEFAULT 20,
                total_score INTEGER DEFAULT 100,
                status TEXT DEFAULT 'available',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exercise_id TEXT UNIQUE NOT NULL,
                course_id TEXT NOT NULL,
                exercise_name TEXT NOT NULL,
                description TEXT,
                duration INTEGER DEFAULT 30,
                question_count INTEGER DEFAULT 15,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
        print("表结构创建完成")
        
    def insert_courses(self, course_data):
        """插入课程数据"""
        print("\n插入课程数据...")
        
        for course_id, info in course_data.items():
            try:
                self.cursor.execute('''
                    INSERT OR IGNORE INTO courses (course_id, course_name, course_icon, description)
                    VALUES (?, ?, ?, ?)
                ''', (course_id, info['name'], info['icon'], f"{info['name']}综合学习课程"))
                print(f"  ✓ {info['name']}")
            except Exception as e:
                print(f"  ✗ {info['name']}: {e}")
                
        self.conn.commit()
        print("课程插入完成")
        
    def insert_exams(self, course_data):
        """插入考试数据"""
        print("\n插入考试数据...")
        total = 0
        
        for course_id, info in course_data.items():
            for exam in info['exams']:
                try:
                    exam_id = f"{course_id}_{exam['name'][:10].replace(' ', '_').replace('（', '').replace('）', '')}"
                    self.cursor.execute('''
                        INSERT OR IGNORE INTO exams 
                        (exam_id, course_id, exam_name, description, duration, question_count, total_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (exam_id, course_id, exam['name'], exam['desc'], 
                          exam['duration'], exam['questions'], exam['score']))
                    total += 1
                except Exception as e:
                    print(f"  ✗ {exam['name']}: {e}")
                    
        self.conn.commit()
        print(f"考试插入完成: 共 {total} 个考试")
        
    def insert_exercises(self, exercise_data):
        """插入练习数据"""
        print("\n插入练习数据...")
        total = 0
        
        for course_id, info in exercise_data.items():
            if course_id not in ['ai', 'security', 'math', 'programming', 'english', 'japanese']:
                continue
                
            for exercise in info['exercises']:
                try:
                    ex_id = f"ex_{course_id}_{exercise['name'][:10].replace(' ', '_').replace('（', '').replace('）', '')}"
                    self.cursor.execute('''
                        INSERT OR IGNORE INTO exercises 
                        (exercise_id, course_id, exercise_name, description, duration, question_count)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (ex_id, course_id, exercise['name'], exercise['desc'],
                          exercise['duration'], exercise['questions']))
                    total += 1
                except Exception as e:
                    print(f"  ✗ {exercise['name']}: {e}")
                    
        self.conn.commit()
        print(f"练习插入完成: 共 {total} 个练习")
        
    def expand_all(self):
        """执行所有拓展操作"""
        print("=" * 80)
        print("开始简化版课程拓展...")
        print("=" * 80)
        
        try:
            self.connect()
            self.create_tables()
            
            course_data = self._load_course_data()
            self.insert_courses(course_data)
            self.insert_exams(course_data)
            
            exercise_data = self._load_exercise_data()
            self.insert_exercises(exercise_data)
            
            print("\n" + "=" * 80)
            print("拓展完成!")
            print("=" * 80)
            
            self.cursor.execute('SELECT COUNT(*) FROM courses')
            print(f"课程总数: {self.cursor.fetchone()[0]}")
            
            self.cursor.execute('SELECT COUNT(*) FROM exams')
            print(f"考试总数: {self.cursor.fetchone()[0]}")
            
            self.cursor.execute('SELECT COUNT(*) FROM exercises')
            print(f"练习总数: {self.cursor.fetchone()[0]}")
            
        finally:
            self.close()
            
    def _load_course_data(self):
        """加载课程数据"""
        return {
            "ai": {
                "name": "AI与机器学习", "icon": "🤖",
                "exams": [
                    {"name": "深度学习工程师认证", "duration": 120, "questions": 35, "score": 100, 
                     "desc": "深度学习、神经网络架构、优化算法和应用开发综合测试。"},
                    {"name": "自然语言处理工程师", "duration": 90, "questions": 30, "score": 100,
                     "desc": "NLP技术、文本处理、语言模型和对话系统应用测试。"},
                    {"name": "计算机视觉专家认证", "duration": 100, "questions": 32, "score": 100,
                     "desc": "图像处理、计算机视觉算法和深度学习应用测试。"},
                ]
            },
            "security": {
                "name": "数据安全", "icon": "🔒",
                "exams": [
                    {"name": "网络安全专家认证", "duration": 95, "questions": 30, "score": 100,
                     "desc": "网络攻防、漏洞分析和安全防护综合测试。"},
                    {"name": "云安全架构师", "duration": 80, "questions": 28, "score": 100,
                     "desc": "云平台安全、身份认证和数据保护测试。"},
                ]
            },
            "japanese": {
                "name": "日语学习", "icon": "🗾",
                "exams": [
                    {"name": "日语能力等级考试（JLPT N2）", "duration": 90, "questions": 35, "score": 100,
                     "desc": "日本语能力测试N2级别，包括词汇、语法、阅读和听力。"},
                    {"name": "日语能力等级考试（JLPT N1）", "duration": 110, "questions": 40, "score": 100,
                     "desc": "日本语能力测试最高级别，高级日语综合能力测试。"},
                    {"name": "日语会话能力测试", "duration": 60, "questions": 15, "score": 100,
                     "desc": "日常日语会话能力评估，包括听力理解和口语表达。"},
                ]
            }
        }
        
    def _load_exercise_data(self):
        """加载练习数据"""
        return {
            "ai": {
                "exercises": [
                    {"name": "机器学习算法实践", "duration": 60, "questions": 20,
                     "desc": "回归、分类、聚类等经典机器学习算法练习。"},
                    {"name": "深度学习模型搭建", "duration": 90, "questions": 15,
                     "desc": "神经网络、CNN、RNN等深度学习模型构建练习。"},
                ]
            },
            "japanese": {
                "exercises": [
                    {"name": "日语词汇练习", "duration": 30, "questions": 20,
                     "desc": "日语基础到高级词汇系统化练习。"},
                    {"name": "日语语法练习", "duration": 25, "questions": 15,
                     "desc": "日语语法点专项训练和应用练习。"},
                    {"name": "JLPT历年真题(N1-N5)", "duration": 120, "questions": 50,
                     "desc": "JLPT各级别历年真题完整练习。"},
                ]
            }
        }


if __name__ == '__main__':
    expander = SimpleCourseExpander()
    expander.expand_all()
