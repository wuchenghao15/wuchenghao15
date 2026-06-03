# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
考试数据管理器 - 支持多种考试类型
"""

import os
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

class ExamManager:
    """考试管理器"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.join(
            os.path.dirname(__file__), '..', '..', 'app.db'
        )
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 创建考试表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS exams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT NOT NULL,
                    subcategory TEXT,
                    difficulty TEXT DEFAULT 'medium',
                    duration INTEGER DEFAULT 60,
                    question_count INTEGER DEFAULT 20,
                    total_score INTEGER DEFAULT 100,
                    status TEXT DEFAULT 'active',
                    target_grade TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建题目表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exam_id INTEGER,
                    question_text TEXT NOT NULL,
                    option_a TEXT,
                    option_b TEXT,
                    option_c TEXT,
                    option_d TEXT,
                    correct_answer TEXT NOT NULL,
                    explanation TEXT,
                    difficulty TEXT DEFAULT 'medium',
                    score INTEGER DEFAULT 5,
                    FOREIGN KEY (exam_id) REFERENCES exams(id)
                )
            ''')
            
            conn.commit()
            self._init_default_exams()
    
    def _init_default_exams(self):
        """初始化默认考试数据"""
        default_exams = [
            # 成人教育
            {'name': '成人大学入学测试', 'description': '成人高等教育入学水平测试', 'category': '成人教育', 'subcategory': '成人大学', 'difficulty': 'medium', 'duration': 90, 'question_count': 30, 'total_score': 100, 'target_grade': '成人大学'},
            {'name': '成人日语N5模拟考', 'description': 'JLPT N5级别模拟考试', 'category': '成人教育', 'subcategory': '日语', 'difficulty': 'easy', 'duration': 60, 'question_count': 25, 'total_score': 100, 'target_grade': '成人日语N5'},
            {'name': '成人日语N4模拟考', 'description': 'JLPT N4级别模拟考试', 'category': '成人教育', 'subcategory': '日语', 'difficulty': 'easy', 'duration': 70, 'question_count': 30, 'total_score': 100, 'target_grade': '成人日语N4'},
            {'name': '成人日语N3模拟考', 'description': 'JLPT N3级别模拟考试', 'category': '成人教育', 'subcategory': '日语', 'difficulty': 'medium', 'duration': 90, 'question_count': 35, 'total_score': 100, 'target_grade': '成人日语N3'},
            {'name': '成人日语N2模拟考', 'description': 'JLPT N2级别模拟考试', 'category': '成人教育', 'subcategory': '日语', 'difficulty': 'hard', 'duration': 100, 'question_count': 40, 'total_score': 100, 'target_grade': '成人日语N2'},
            {'name': '成人日语N1模拟考', 'description': 'JLPT N1级别模拟考试', 'category': '成人教育', 'subcategory': '日语', 'difficulty': 'hard', 'duration': 110, 'question_count': 45, 'total_score': 100, 'target_grade': '成人日语N1'},
            
            # 雅思考试
            {'name': '雅思听力模拟', 'description': 'IELTS听力部分模拟', 'category': '雅思', 'subcategory': '听力', 'difficulty': 'medium', 'duration': 30, 'question_count': 40, 'total_score': 40, 'target_grade': '雅思4.0'},
            {'name': '雅思阅读模拟', 'description': 'IELTS阅读部分模拟', 'category': '雅思', 'subcategory': '阅读', 'difficulty': 'medium', 'duration': 60, 'question_count': 40, 'total_score': 40, 'target_grade': '雅思5.0'},
            {'name': '雅思写作练习', 'description': 'IELTS写作部分练习', 'category': '雅思', 'subcategory': '写作', 'difficulty': 'hard', 'duration': 60, 'question_count': 2, 'total_score': 9, 'target_grade': '雅思5.5'},
            {'name': '雅思口语练习', 'description': 'IELTS口语部分练习', 'category': '雅思', 'subcategory': '口语', 'difficulty': 'hard', 'duration': 15, 'question_count': 3, 'total_score': 9, 'target_grade': '雅思6.0'},
            {'name': '雅思全真模拟', 'description': '完整IELTS模拟考试', 'category': '雅思', 'subcategory': '综合', 'difficulty': 'hard', 'duration': 240, 'question_count': 82, 'total_score': 36, 'target_grade': '雅思6.5'},
            
            # 托福考试
            {'name': '托福听力模拟', 'description': 'TOEFL听力部分模拟', 'category': '托福', 'subcategory': '听力', 'difficulty': 'medium', 'duration': 60, 'question_count': 34, 'total_score': 30, 'target_grade': '托福60分'},
            {'name': '托福阅读模拟', 'description': 'TOEFL阅读部分模拟', 'category': '托福', 'subcategory': '阅读', 'difficulty': 'medium', 'duration': 60, 'question_count': 30, 'total_score': 30, 'target_grade': '托福70分'},
            {'name': '托福口语练习', 'description': 'TOEFL口语部分练习', 'category': '托福', 'subcategory': '口语', 'difficulty': 'hard', 'duration': 20, 'question_count': 6, 'total_score': 30, 'target_grade': '托福80分'},
            {'name': '托福写作练习', 'description': 'TOEFL写作部分练习', 'category': '托福', 'subcategory': '写作', 'difficulty': 'hard', 'duration': 50, 'question_count': 2, 'total_score': 30, 'target_grade': '托福90分'},
            {'name': '托福全真模拟', 'description': '完整TOEFL iBT模拟考试', 'category': '托福', 'subcategory': '综合', 'difficulty': 'hard', 'duration': 200, 'question_count': 72, 'total_score': 120, 'target_grade': '托福100分'},
            
            # AMC8数学竞赛
            {'name': 'AMC8入门练习', 'description': 'AMC8入门级数学竞赛练习', 'category': '数学竞赛', 'subcategory': 'AMC8', 'difficulty': 'easy', 'duration': 40, 'question_count': 15, 'total_score': 15, 'target_grade': 'AMC8入门'},
            {'name': 'AMC8进阶练习', 'description': 'AMC8进阶级数学竞赛练习', 'category': '数学竞赛', 'subcategory': 'AMC8', 'difficulty': 'medium', 'duration': 45, 'question_count': 20, 'total_score': 20, 'target_grade': 'AMC8进阶'},
            {'name': 'AMC8冲刺模拟', 'description': 'AMC8冲刺级模拟考试', 'category': '数学竞赛', 'subcategory': 'AMC8', 'difficulty': 'hard', 'duration': 40, 'question_count': 25, 'total_score': 25, 'target_grade': 'AMC8冲刺'},
            
            # 华罗庚数学竞赛
            {'name': '华罗庚杯小学组模拟', 'description': '华罗庚金杯少年数学邀请赛小学组', 'category': '数学竞赛', 'subcategory': '华罗庚', 'difficulty': 'medium', 'duration': 90, 'question_count': 12, 'total_score': 150, 'target_grade': '华罗庚小学组'},
            {'name': '华罗庚杯初中组模拟', 'description': '华罗庚金杯少年数学邀请赛初中组', 'category': '数学竞赛', 'subcategory': '华罗庚', 'difficulty': 'hard', 'duration': 120, 'question_count': 14, 'total_score': 150, 'target_grade': '华罗庚初中组'},
            {'name': '华罗庚杯高中组模拟', 'description': '华罗庚金杯少年数学邀请赛高中组', 'category': '数学竞赛', 'subcategory': '华罗庚', 'difficulty': 'hard', 'duration': 150, 'question_count': 15, 'total_score': 150, 'target_grade': '华罗庚高中组'},
        ]
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for exam in default_exams:
                cursor.execute('SELECT COUNT(*) FROM exams WHERE name = ?', (exam['name'],))
                if cursor.fetchone()[0] == 0:
                    cursor.execute('''
                        INSERT INTO exams (name, description, category, subcategory, difficulty, 
                                         duration, question_count, total_score, status, target_grade)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        exam['name'], exam['description'], exam['category'], exam['subcategory'],
                        exam['difficulty'], exam['duration'], exam['question_count'],
                        exam['total_score'], 'active', exam['target_grade']
                    ))
            
            conn.commit()
    
    def get_exams_by_category(self, category: str = None) -> List[Dict]:
        """按类别获取考试"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if category:
                cursor.execute('SELECT * FROM exams WHERE category = ? ORDER BY name', (category,))
            else:
                cursor.execute('SELECT * FROM exams ORDER BY category, name')
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            return [dict(zip(columns, row)) for row in rows]
    
    def get_exams_by_grade(self, grade: str) -> List[Dict]:
        """按年级获取考试"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 匹配目标年级
            cursor.execute('SELECT * FROM exams WHERE target_grade = ? ORDER BY name', (grade,))
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            return [dict(zip(columns, row)) for row in rows]
    
    def get_exam_by_id(self, exam_id: int) -> Optional[Dict]:
        """按ID获取考试"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM exams WHERE id = ?', (exam_id,))
            row = cursor.fetchone()
            
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None
    
    def get_all_categories(self) -> List[str]:
        """获取所有考试类别"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT category FROM exams ORDER BY category')
            return [row[0] for row in cursor.fetchall()]
    
    def get_category_info(self) -> Dict[str, List[Dict]]:
        """获取分类信息"""
        categories = self.get_all_categories()
        result = {}
        
        for category in categories:
            exams = self.get_exams_by_category(category)
            result[category] = exams
        
        return result

# 全局实例
exam_manager = ExamManager()