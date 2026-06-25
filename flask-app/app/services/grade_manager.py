# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
年级管理服务模块
负责年级管理,自动升级,考试权限控制
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, Optional

class GradeManager:
    """年级管理服务"""
    
    GRADE_LEVELS = [
        '小学1年级', '小学2年级', '小学3年级', '小学4年级', '小学5年级', '小学6年级',
        '初中1年级', '初中2年级', '初中3年级',
        '高中1年级', '高中2年级', '高中3年级',
        '大学1年级', '大学2年级', '大学3年级', '大学4年级',
        '研究生', '博士生',
        # 成人教育
        '成人大学', '成人日语N5', '成人日语N4', '成人日语N3', '成人日语N2', '成人日语N1',
        # 雅思考试
        '雅思4.0', '雅思5.0', '雅思5.5', '雅思6.0', '雅思6.5', '雅思7.0+',
        # 托福考试
        '托福60分', '托福70分', '托福80分', '托福90分', '托福100分', '托福110+',
        # 数学竞赛
        'AMC8入门', 'AMC8进阶', 'AMC8冲刺', 
        '华罗庚小学组', '华罗庚初中组', '华罗庚高中组'
    ]
    
    def __init__(self, db_path=None):
        if db_path is None:
            # 获取flask-app目录作为基准路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # app/services -> app -> flask-app
            flask_app_dir = os.path.dirname(os.path.dirname(current_dir))
            self.db_path = os.path.join(flask_app_dir, 'app.db')
        else:
            self.db_path = db_path
    
    def _connect(self):
        return sqlite3.connect(self.db_path)
    
    def get_user_grade(self, user_id: int) -> Optional[str]:
        """获取用户年级"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT grade FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            return row[0] if row else None
    
    def set_user_grade(self, user_id: int, grade: str) -> bool:
        """设置用户年级"""
        if grade not in self.GRADE_LEVELS:
            return False
        
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET grade = ? WHERE id = ?', (grade, user_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def upgrade_grades(self):
        """每年9月自动升级所有学生年级"""
        today = datetime.now()
        # 9月份进行升级
        if today.month != 9:
            return {'success': False, 'message': '未到升级时间(每年9月)'}
        
        with self._connect() as conn:
            cursor = conn.cursor()
            
            upgraded_count = 0
            for i, grade in enumerate(self.GRADE_LEVELS[:-2]):  # 排除研究生和博士生
                next_grade = self.GRADE_LEVELS[i + 1]
                cursor.execute('UPDATE users SET grade = ? WHERE grade = ?', (next_grade, grade))
                upgraded_count += cursor.rowcount
            
            conn.commit()
            
            return {
                'success': True,
                'upgraded_count': upgraded_count,
                'message': f'已为 {upgraded_count} 名学生升级年级'
            }
    
    def get_grade_index(self, grade: str) -> int:
        """获取年级索引"""
        return self.GRADE_LEVELS.index(grade) if grade in self.GRADE_LEVELS else -1
    
    def is_eligible_for_exam(self, user_id: int, category: str) -> Dict:
        """检查用户是否有资格参加某个类别的考试"""
        grade = self.get_user_grade(user_id)
        if not grade:
            return {'eligible': False, 'reason': '请先设置年级'}
        
        grade_index = self.get_grade_index(grade)
        
        # 定义各科目适合的最低年级
        category_min_grade = {
            'math': 0,           # 小学1年级
            'chinese': 0,        # 小学1年级
            'english': 0,        # 小学1年级
            'physics': 6,        # 初中1年级
            'chemistry': 7,      # 初中2年级
            'biology': 6,        # 初中1年级
            'history': 3,        # 小学4年级
            'geography': 6,      # 初中1年级
            'politics': 6,       # 初中1年级
            'programming': 6,    # 初中1年级
            'computer_science': 9, # 高中1年级
            'ai': 12,            # 大学1年级
            'japanese': 6,       # 初中1年级
        }
        
        min_index = category_min_grade.get(category, 0)
        
        if grade_index >= min_index:
            return {'eligible': True, 'reason': '符合年级要求'}
        else:
            min_grade = self.GRADE_LEVELS[min_index]
            return {'eligible': False, 'reason': f'需要至少{min_grade}才能参加'}
    
    def get_compatible_grades(self, grade: str) -> list:
        """获取向下兼容的年级列表(当前年级及以下)"""
        index = self.get_grade_index(grade)
        if index < 0:
            return []
        return self.GRADE_LEVELS[:index + 1]
    
    def is_college_level(self, grade: str) -> bool:
        """判断是否为大学及以上级别"""
        index = self.get_grade_index(grade)
        return index >= 12  # 大学1年级及以上
    
    def is_adult_education(self, grade: str) -> bool:
        """判断是否为成人教育"""
        return grade.startswith('成人')
    
    def is_ielts(self, grade: str) -> bool:
        """判断是否为雅思"""
        return grade.startswith('雅思')
    
    def is_toefl(self, grade: str) -> bool:
        """判断是否为托福"""
        return grade.startswith('托福')
    
    def is_math_competition(self, grade: str) -> bool:
        """判断是否为数学竞赛"""
        return grade.startswith('AMC') or grade.startswith('华罗庚')
    
    def has_completed_major_test(self, user_id: int) -> bool:
        """检查用户是否已完成专业摸底测试或成人摸底测试"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM placement_reports 
                WHERE user_id = ? AND (report_data LIKE ? OR report_data LIKE ?)
            ''', (user_id, '%专业摸底%', '%成人摸底%'))
            return cursor.fetchone()[0] > 0
    
    def create_major_placement_test(self, user_id: int, major: str) -> Dict:
        """创建专业摸底测试"""
        test_id = f"MT_{int(datetime.now().timestamp())}_{user_id}"
        
        with self._connect() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO placement_tests 
                (id, user_id, subject, status, created_at, estimated_duration, is_adaptive)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (test_id, user_id, f'专业摸底-{major}', 'created', datetime.now(), 60, True))
            
            conn.commit()
        
        return {
            'test_id': test_id,
            'user_id': user_id,
            'major': major,
            'status': 'created'
        }
    
    def create_adult_placement_test(self, user_id: int, subject: str) -> Dict:
        """创建成人教育摸底测试"""
        subject_name_map = {
            'japanese': '日语',
            'english': '英语',
            'adult_college': '成人大学',
            'ielts': '雅思',
            'toefl': '托福'
        }
        
        subject_name = subject_name_map.get(subject, subject)
        test_id = f"AT_{int(datetime.now().timestamp())}_{user_id}"
        
        with self._connect() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS placement_tests (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER,
                    subject TEXT,
                    status TEXT,
                    created_at TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    estimated_duration INTEGER,
                    actual_duration INTEGER,
                    is_adaptive BOOLEAN DEFAULT FALSE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS placement_test_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_id TEXT,
                    question_id INTEGER,
                    question_text TEXT,
                    options TEXT,
                    correct_answer TEXT,
                    difficulty INTEGER,
                    points REAL,
                    category TEXT,
                    order_index INTEGER,
                    user_answer TEXT,
                    is_correct BOOLEAN,
                    answered_at TIMESTAMP,
                    FOREIGN KEY (test_id) REFERENCES placement_tests(id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS placement_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_id TEXT,
                    user_id INTEGER,
                    report_data TEXT,
                    generated_at TIMESTAMP,
                    FOREIGN KEY (test_id) REFERENCES placement_tests(id)
                )
            ''')
            
            cursor.execute('''
                INSERT INTO placement_tests 
                (id, user_id, subject, status, created_at, estimated_duration, is_adaptive)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (test_id, user_id, f'成人摸底-{subject_name}', 'created', datetime.now(), 45, True))
            
            conn.commit()
        
        # 生成题目 - 调用placement_test_service
        try:
            from app.services.placement_test_service import get_placement_test_service
            service = get_placement_test_service()
            questions = service._generate_placement_questions(user_id, subject_name)
            
            # 质量保证:去重、验证选项、确保干扰项质量
            questions = service._ensure_question_quality(questions)
            
            service._save_test_questions(test_id, questions)
        except Exception as e:
            import logging
            logging.error(f"生成成人教育摸底测试题目失败: {e}")
        
        return {
            'test_id': test_id,
            'user_id': user_id,
            'subject': subject_name,
            'status': 'created'
        }
    
    def init_database(self):
        """初始化数据库"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            # 确保users表有grade字段
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'grade' not in columns:
                cursor.execute('ALTER TABLE users ADD COLUMN grade TEXT')
            
            conn.commit()

# 全局实例
grade_manager = None

def get_grade_manager():
    """获取年级管理器实例"""
    global grade_manager
    if grade_manager is None:
        grade_manager = GradeManager()
    return grade_manager

if __name__ == "__main__":
    manager = GradeManager()
    manager.init_database()
    print("年级管理器初始化完成")
    
    # 测试升级功能(模拟9月份)
    result = manager.upgrade_grades()
    logger.info(f"升级结果: {result}")
