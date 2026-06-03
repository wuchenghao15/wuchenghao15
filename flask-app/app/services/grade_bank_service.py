# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
年级题库绑定服务 - 将年级与题库关联
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Optional

class GradeQuestionBankService:
    """年级题库绑定服务"""
    
    def __init__(self, db_path=None):
        if db_path is None:
            self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')
        else:
            self.db_path = db_path
        self._init_tables()
    
    def _connect(self):
        return sqlite3.connect(self.db_path)
    
    def _init_tables(self):
        """初始化数据库表"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            # 创建年级题库关联表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS grade_bank_mapping (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    grade TEXT NOT NULL,
                    bank_id TEXT NOT NULL,
                    bank_name TEXT NOT NULL,
                    subject TEXT,
                    weight INTEGER DEFAULT 1,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(grade, bank_id)
                )
            ''')
            
            # 创建题库元数据表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS question_banks (
                    bank_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    subject TEXT,
                    total_questions INTEGER DEFAULT 0,
                    difficulty_level TEXT DEFAULT 'mixed',
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            self._init_default_banks()
            self._init_default_mappings()
    
    def _init_default_banks(self):
        """初始化默认题库"""
        default_banks = [
            # 常规科目题库
            {'bank_id': 'math_primary', 'name': '小学数学题库', 'description': '小学1-6年级数学题目', 'subject': 'math', 'total_questions': 5000},
            {'bank_id': 'math_junior', 'name': '初中数学题库', 'description': '初中1-3年级数学题目', 'subject': 'math', 'total_questions': 6000},
            {'bank_id': 'math_high', 'name': '高中数学题库', 'description': '高中1-3年级数学题目', 'subject': 'math', 'total_questions': 8000},
            {'bank_id': 'math_college', 'name': '大学数学题库', 'description': '高等数学题目', 'subject': 'math', 'total_questions': 4000},
            
            {'bank_id': 'chinese_primary', 'name': '小学语文题库', 'description': '小学1-6年级语文题目', 'subject': 'chinese', 'total_questions': 4000},
            {'bank_id': 'chinese_junior', 'name': '初中语文题库', 'description': '初中1-3年级语文题目', 'subject': 'chinese', 'total_questions': 5000},
            {'bank_id': 'chinese_high', 'name': '高中语文题库', 'description': '高中1-3年级语文题目', 'subject': 'chinese', 'total_questions': 6000},
            
            {'bank_id': 'english_primary', 'name': '小学英语题库', 'description': '小学1-6年级英语题目', 'subject': 'english', 'total_questions': 3500},
            {'bank_id': 'english_junior', 'name': '初中英语题库', 'description': '初中1-3年级英语题目', 'subject': 'english', 'total_questions': 4500},
            {'bank_id': 'english_high', 'name': '高中英语题库', 'description': '高中1-3年级英语题目', 'subject': 'english', 'total_questions': 5500},
            
            {'bank_id': 'physics_junior', 'name': '初中物理题库', 'description': '初中物理题目', 'subject': 'physics', 'total_questions': 3000},
            {'bank_id': 'physics_high', 'name': '高中物理题库', 'description': '高中物理题目', 'subject': 'physics', 'total_questions': 4000},
            
            {'bank_id': 'chemistry_junior', 'name': '初中化学题库', 'description': '初中化学题目', 'subject': 'chemistry', 'total_questions': 2500},
            {'bank_id': 'chemistry_high', 'name': '高中化学题库', 'description': '高中化学题目', 'subject': 'chemistry', 'total_questions': 3500},
            
            {'bank_id': 'biology_junior', 'name': '初中生物题库', 'description': '初中生物题目', 'subject': 'biology', 'total_questions': 2000},
            {'bank_id': 'biology_high', 'name': '高中生物题库', 'description': '高中生物题目', 'subject': 'biology', 'total_questions': 3000},
            
            {'bank_id': 'history_primary', 'name': '小学历史题库', 'description': '小学历史题目', 'subject': 'history', 'total_questions': 1500},
            {'bank_id': 'history_junior', 'name': '初中历史题库', 'description': '初中历史题目', 'subject': 'history', 'total_questions': 2500},
            {'bank_id': 'history_high', 'name': '高中历史题库', 'description': '高中历史题目', 'subject': 'history', 'total_questions': 3500},
            
            {'bank_id': 'geography_junior', 'name': '初中地理题库', 'description': '初中地理题目', 'subject': 'geography', 'total_questions': 2000},
            {'bank_id': 'geography_high', 'name': '高中地理题库', 'description': '高中地理题目', 'subject': 'geography', 'total_questions': 3000},
            
            {'bank_id': 'politics_junior', 'name': '初中政治题库', 'description': '初中思想品德题目', 'subject': 'politics', 'total_questions': 1500},
            {'bank_id': 'politics_high', 'name': '高中政治题库', 'description': '高中政治题目', 'subject': 'politics', 'total_questions': 2500},
            
            # 成人教育题库
            {'bank_id': 'adult_college', 'name': '成人大学题库', 'description': '成人高等教育题目', 'subject': 'adult', 'total_questions': 3000},
            {'bank_id': 'japanese_n5', 'name': '日语N5题库', 'description': 'JLPT N5级别题目', 'subject': 'japanese', 'total_questions': 2000},
            {'bank_id': 'japanese_n4', 'name': '日语N4题库', 'description': 'JLPT N4级别题目', 'subject': 'japanese', 'total_questions': 2500},
            {'bank_id': 'japanese_n3', 'name': '日语N3题库', 'description': 'JLPT N3级别题目', 'subject': 'japanese', 'total_questions': 3000},
            {'bank_id': 'japanese_n2', 'name': '日语N2题库', 'description': 'JLPT N2级别题目', 'subject': 'japanese', 'total_questions': 3500},
            {'bank_id': 'japanese_n1', 'name': '日语N1题库', 'description': 'JLPT N1级别题目', 'subject': 'japanese', 'total_questions': 4000},
            
            # 雅思题库
            {'bank_id': 'ielts_listening', 'name': '雅思听力题库', 'description': 'IELTS听力题目', 'subject': 'ielts', 'total_questions': 2000},
            {'bank_id': 'ielts_reading', 'name': '雅思阅读题库', 'description': 'IELTS阅读题目', 'subject': 'ielts', 'total_questions': 2500},
            {'bank_id': 'ielts_writing', 'name': '雅思写作题库', 'description': 'IELTS写作题目', 'subject': 'ielts', 'total_questions': 1000},
            {'bank_id': 'ielts_speaking', 'name': '雅思口语题库', 'description': 'IELTS口语题目', 'subject': 'ielts', 'total_questions': 800},
            
            # 托福题库
            {'bank_id': 'toefl_listening', 'name': '托福听力题库', 'description': 'TOEFL听力题目', 'subject': 'toefl', 'total_questions': 2500},
            {'bank_id': 'toefl_reading', 'name': '托福阅读题库', 'description': 'TOEFL阅读题目', 'subject': 'toefl', 'total_questions': 2000},
            {'bank_id': 'toefl_speaking', 'name': '托福口语题库', 'description': 'TOEFL口语题目', 'subject': 'toefl', 'total_questions': 1500},
            {'bank_id': 'toefl_writing', 'name': '托福写作题库', 'description': 'TOEFL写作题目', 'subject': 'toefl', 'total_questions': 1000},
            
            # 数学竞赛题库
            {'bank_id': 'amc8', 'name': 'AMC8题库', 'description': 'AMC8数学竞赛题目', 'subject': 'math_competition', 'total_questions': 1500},
            {'bank_id': 'huaguang_primary', 'name': '华罗庚小学组题库', 'description': '华罗庚杯小学组题目', 'subject': 'math_competition', 'total_questions': 1000},
            {'bank_id': 'huaguang_junior', 'name': '华罗庚初中组题库', 'description': '华罗庚杯初中组题目', 'subject': 'math_competition', 'total_questions': 1200},
            {'bank_id': 'huaguang_high', 'name': '华罗庚高中组题库', 'description': '华罗庚杯高中组题目', 'subject': 'math_competition', 'total_questions': 1500},
        ]
        
        with self._connect() as conn:
            cursor = conn.cursor()
            for bank in default_banks:
                cursor.execute('SELECT COUNT(*) FROM question_banks WHERE bank_id = ?', (bank['bank_id'],))
                if cursor.fetchone()[0] == 0:
                    cursor.execute('''
                        INSERT INTO question_banks (bank_id, name, description, subject, total_questions)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (bank['bank_id'], bank['name'], bank['description'], bank['subject'], bank['total_questions']))
            conn.commit()
    
    def _init_default_mappings(self):
        """初始化年级与题库的默认映射"""
        mappings = [
            # 小学
            ('小学1年级', 'math_primary', '小学数学题库', 'math', 5),
            ('小学1年级', 'chinese_primary', '小学语文题库', 'chinese', 5),
            ('小学1年级', 'english_primary', '小学英语题库', 'english', 4),
            
            ('小学2年级', 'math_primary', '小学数学题库', 'math', 5),
            ('小学2年级', 'chinese_primary', '小学语文题库', 'chinese', 5),
            ('小学2年级', 'english_primary', '小学英语题库', 'english', 4),
            
            ('小学3年级', 'math_primary', '小学数学题库', 'math', 5),
            ('小学3年级', 'chinese_primary', '小学语文题库', 'chinese', 5),
            ('小学3年级', 'english_primary', '小学英语题库', 'english', 4),
            ('小学3年级', 'history_primary', '小学历史题库', 'history', 3),
            
            ('小学4年级', 'math_primary', '小学数学题库', 'math', 5),
            ('小学4年级', 'chinese_primary', '小学语文题库', 'chinese', 5),
            ('小学4年级', 'english_primary', '小学英语题库', 'english', 4),
            ('小学4年级', 'history_primary', '小学历史题库', 'history', 3),
            
            ('小学5年级', 'math_primary', '小学数学题库', 'math', 5),
            ('小学5年级', 'chinese_primary', '小学语文题库', 'chinese', 5),
            ('小学5年级', 'english_primary', '小学英语题库', 'english', 4),
            ('小学5年级', 'history_primary', '小学历史题库', 'history', 3),
            
            ('小学6年级', 'math_primary', '小学数学题库', 'math', 5),
            ('小学6年级', 'chinese_primary', '小学语文题库', 'chinese', 5),
            ('小学6年级', 'english_primary', '小学英语题库', 'english', 4),
            ('小学6年级', 'history_primary', '小学历史题库', 'history', 3),
            
            # 初中
            ('初中1年级', 'math_junior', '初中数学题库', 'math', 5),
            ('初中1年级', 'chinese_junior', '初中语文题库', 'chinese', 5),
            ('初中1年级', 'english_junior', '初中英语题库', 'english', 4),
            ('初中1年级', 'physics_junior', '初中物理题库', 'physics', 4),
            ('初中1年级', 'biology_junior', '初中生物题库', 'biology', 3),
            ('初中1年级', 'history_junior', '初中历史题库', 'history', 3),
            ('初中1年级', 'geography_junior', '初中地理题库', 'geography', 3),
            ('初中1年级', 'politics_junior', '初中政治题库', 'politics', 3),
            
            ('初中2年级', 'math_junior', '初中数学题库', 'math', 5),
            ('初中2年级', 'chinese_junior', '初中语文题库', 'chinese', 5),
            ('初中2年级', 'english_junior', '初中英语题库', 'english', 4),
            ('初中2年级', 'physics_junior', '初中物理题库', 'physics', 4),
            ('初中2年级', 'chemistry_junior', '初中化学题库', 'chemistry', 4),
            ('初中2年级', 'biology_junior', '初中生物题库', 'biology', 3),
            ('初中2年级', 'history_junior', '初中历史题库', 'history', 3),
            ('初中2年级', 'geography_junior', '初中地理题库', 'geography', 3),
            ('初中2年级', 'politics_junior', '初中政治题库', 'politics', 3),
            
            ('初中3年级', 'math_junior', '初中数学题库', 'math', 5),
            ('初中3年级', 'chinese_junior', '初中语文题库', 'chinese', 5),
            ('初中3年级', 'english_junior', '初中英语题库', 'english', 4),
            ('初中3年级', 'physics_junior', '初中物理题库', 'physics', 4),
            ('初中3年级', 'chemistry_junior', '初中化学题库', 'chemistry', 4),
            ('初中3年级', 'biology_junior', '初中生物题库', 'biology', 3),
            ('初中3年级', 'history_junior', '初中历史题库', 'history', 3),
            ('初中3年级', 'geography_junior', '初中地理题库', 'geography', 3),
            ('初中3年级', 'politics_junior', '初中政治题库', 'politics', 3),
            
            # 高中
            ('高中1年级', 'math_high', '高中数学题库', 'math', 5),
            ('高中1年级', 'chinese_high', '高中语文题库', 'chinese', 5),
            ('高中1年级', 'english_high', '高中英语题库', 'english', 4),
            ('高中1年级', 'physics_high', '高中物理题库', 'physics', 4),
            ('高中1年级', 'chemistry_high', '高中化学题库', 'chemistry', 4),
            ('高中1年级', 'biology_high', '高中生物题库', 'biology', 3),
            ('高中1年级', 'history_high', '高中历史题库', 'history', 3),
            ('高中1年级', 'geography_high', '高中地理题库', 'geography', 3),
            ('高中1年级', 'politics_high', '高中政治题库', 'politics', 3),
            
            ('高中2年级', 'math_high', '高中数学题库', 'math', 5),
            ('高中2年级', 'chinese_high', '高中语文题库', 'chinese', 5),
            ('高中2年级', 'english_high', '高中英语题库', 'english', 4),
            ('高中2年级', 'physics_high', '高中物理题库', 'physics', 4),
            ('高中2年级', 'chemistry_high', '高中化学题库', 'chemistry', 4),
            ('高中2年级', 'biology_high', '高中生物题库', 'biology', 3),
            ('高中2年级', 'history_high', '高中历史题库', 'history', 3),
            ('高中2年级', 'geography_high', '高中地理题库', 'geography', 3),
            ('高中2年级', 'politics_high', '高中政治题库', 'politics', 3),
            
            ('高中3年级', 'math_high', '高中数学题库', 'math', 5),
            ('高中3年级', 'chinese_high', '高中语文题库', 'chinese', 5),
            ('高中3年级', 'english_high', '高中英语题库', 'english', 4),
            ('高中3年级', 'physics_high', '高中物理题库', 'physics', 4),
            ('高中3年级', 'chemistry_high', '高中化学题库', 'chemistry', 4),
            ('高中3年级', 'biology_high', '高中生物题库', 'biology', 3),
            ('高中3年级', 'history_high', '高中历史题库', 'history', 3),
            ('高中3年级', 'geography_high', '高中地理题库', 'geography', 3),
            ('高中3年级', 'politics_high', '高中政治题库', 'politics', 3),
            
            # 大学
            ('大学1年级', 'math_college', '大学数学题库', 'math', 5),
            
            # 成人教育
            ('成人大学', 'adult_college', '成人大学题库', 'adult', 5),
            ('成人日语N5', 'japanese_n5', '日语N5题库', 'japanese', 5),
            ('成人日语N4', 'japanese_n4', '日语N4题库', 'japanese', 5),
            ('成人日语N3', 'japanese_n3', '日语N3题库', 'japanese', 5),
            ('成人日语N2', 'japanese_n2', '日语N2题库', 'japanese', 5),
            ('成人日语N1', 'japanese_n1', '日语N1题库', 'japanese', 5),
            
            # 雅思
            ('雅思4.0', 'ielts_listening', '雅思听力题库', 'ielts', 5),
            ('雅思4.0', 'ielts_reading', '雅思阅读题库', 'ielts', 5),
            ('雅思5.0', 'ielts_listening', '雅思听力题库', 'ielts', 5),
            ('雅思5.0', 'ielts_reading', '雅思阅读题库', 'ielts', 5),
            ('雅思5.5', 'ielts_listening', '雅思听力题库', 'ielts', 5),
            ('雅思5.5', 'ielts_reading', '雅思阅读题库', 'ielts', 5),
            ('雅思5.5', 'ielts_writing', '雅思写作题库', 'ielts', 4),
            ('雅思6.0', 'ielts_listening', '雅思听力题库', 'ielts', 5),
            ('雅思6.0', 'ielts_reading', '雅思阅读题库', 'ielts', 5),
            ('雅思6.0', 'ielts_writing', '雅思写作题库', 'ielts', 4),
            ('雅思6.0', 'ielts_speaking', '雅思口语题库', 'ielts', 4),
            ('雅思6.5', 'ielts_listening', '雅思听力题库', 'ielts', 5),
            ('雅思6.5', 'ielts_reading', '雅思阅读题库', 'ielts', 5),
            ('雅思6.5', 'ielts_writing', '雅思写作题库', 'ielts', 4),
            ('雅思6.5', 'ielts_speaking', '雅思口语题库', 'ielts', 4),
            ('雅思7.0+', 'ielts_listening', '雅思听力题库', 'ielts', 5),
            ('雅思7.0+', 'ielts_reading', '雅思阅读题库', 'ielts', 5),
            ('雅思7.0+', 'ielts_writing', '雅思写作题库', 'ielts', 5),
            ('雅思7.0+', 'ielts_speaking', '雅思口语题库', 'ielts', 5),
            
            # 托福
            ('托福60分', 'toefl_listening', '托福听力题库', 'toefl', 5),
            ('托福60分', 'toefl_reading', '托福阅读题库', 'toefl', 5),
            ('托福70分', 'toefl_listening', '托福听力题库', 'toefl', 5),
            ('托福70分', 'toefl_reading', '托福阅读题库', 'toefl', 5),
            ('托福80分', 'toefl_listening', '托福听力题库', 'toefl', 5),
            ('托福80分', 'toefl_reading', '托福阅读题库', 'toefl', 5),
            ('托福80分', 'toefl_speaking', '托福口语题库', 'toefl', 4),
            ('托福90分', 'toefl_listening', '托福听力题库', 'toefl', 5),
            ('托福90分', 'toefl_reading', '托福阅读题库', 'toefl', 5),
            ('托福90分', 'toefl_speaking', '托福口语题库', 'toefl', 4),
            ('托福90分', 'toefl_writing', '托福写作题库', 'toefl', 4),
            ('托福100分', 'toefl_listening', '托福听力题库', 'toefl', 5),
            ('托福100分', 'toefl_reading', '托福阅读题库', 'toefl', 5),
            ('托福100分', 'toefl_speaking', '托福口语题库', 'toefl', 5),
            ('托福100分', 'toefl_writing', '托福写作题库', 'toefl', 5),
            ('托福110+', 'toefl_listening', '托福听力题库', 'toefl', 5),
            ('托福110+', 'toefl_reading', '托福阅读题库', 'toefl', 5),
            ('托福110+', 'toefl_speaking', '托福口语题库', 'toefl', 5),
            ('托福110+', 'toefl_writing', '托福写作题库', 'toefl', 5),
            
            # 数学竞赛
            ('AMC8入门', 'amc8', 'AMC8题库', 'math_competition', 5),
            ('AMC8进阶', 'amc8', 'AMC8题库', 'math_competition', 5),
            ('AMC8冲刺', 'amc8', 'AMC8题库', 'math_competition', 5),
            ('华罗庚小学组', 'huaguang_primary', '华罗庚小学组题库', 'math_competition', 5),
            ('华罗庚初中组', 'huaguang_junior', '华罗庚初中组题库', 'math_competition', 5),
            ('华罗庚高中组', 'huaguang_high', '华罗庚高中组题库', 'math_competition', 5),
        ]
        
        with self._connect() as conn:
            cursor = conn.cursor()
            for grade, bank_id, bank_name, subject, weight in mappings:
                cursor.execute('SELECT COUNT(*) FROM grade_bank_mapping WHERE grade = ? AND bank_id = ?', (grade, bank_id))
                if cursor.fetchone()[0] == 0:
                    cursor.execute('''
                        INSERT INTO grade_bank_mapping (grade, bank_id, bank_name, subject, weight)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (grade, bank_id, bank_name, subject, weight))
            conn.commit()
    
    def get_banks_for_grade(self, grade: str) -> List[Dict]:
        """获取指定年级绑定的题库"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT gb.*, b.total_questions 
                FROM grade_bank_mapping gb
                LEFT JOIN question_banks b ON gb.bank_id = b.bank_id
                WHERE gb.grade = ? AND gb.is_active = 1
                ORDER BY gb.weight DESC, gb.created_at DESC
            ''', (grade,))
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_all_banks(self) -> List[Dict]:
        """获取所有题库"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM question_banks WHERE is_active = 1 ORDER BY subject, name')
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def bind_bank_to_grade(self, grade: str, bank_id: str, bank_name: str, subject: str, weight: int = 1) -> bool:
        """绑定题库到年级"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO grade_bank_mapping 
                (grade, bank_id, bank_name, subject, weight, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', (grade, bank_id, bank_name, subject, weight))
            conn.commit()
            return cursor.rowcount > 0
    
    def unbind_bank_from_grade(self, grade: str, bank_id: str) -> bool:
        """解绑年级的题库"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM grade_bank_mapping WHERE grade = ? AND bank_id = ?', (grade, bank_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_grade_bank_summary(self, grade: str) -> Dict:
        """获取年级题库摘要信息"""
        banks = self.get_banks_for_grade(grade)
        total_questions = sum(b.get('total_questions', 0) for b in banks)
        
        return {
            'grade': grade,
            'total_banks': len(banks),
            'total_questions': total_questions,
            'subjects': list(set(b['subject'] for b in banks)),
            'banks': banks
        }
    
    def update_bank_question_count(self, bank_id: str, count: int) -> bool:
        """更新题库题目数量"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE question_banks SET total_questions = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE bank_id = ?
            ''', (count, bank_id))
            conn.commit()
            return cursor.rowcount > 0

# 全局实例
grade_bank_service = None

def get_grade_bank_service():
    """获取年级题库绑定服务实例"""
    global grade_bank_service
    if grade_bank_service is None:
        grade_bank_service = GradeQuestionBankService()
    return grade_bank_service