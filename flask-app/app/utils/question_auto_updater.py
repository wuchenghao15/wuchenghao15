import logging
logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
#!/usr/bin/env python3
import sqlite3
import json
import random
from datetime import datetime, timedelta
import os
import sys

DATABASE_PATH = '/Users/wuchenghao/Library/CloudStorage/OneDrive-个人/文档/MTSCOS_AI_Project/flask-app/app.db'

class QuestionAutoUpdater:
    """题库自动更新器"""
    
    def __init__(self):
        self.last_update_time = None
        self.update_interval_hours = 24
        self.update_trigger_count = 0
        self.trigger_threshold = 10  # 每10次访问触发一次检查
    
    def should_update(self):
        """判断是否需要更新题库"""
        # 检查访问次数
        self.update_trigger_count += 1
        
        if self.update_trigger_count >= self.trigger_threshold:
            self.update_trigger_count = 0
            
            # 检查时间间隔
            if self.last_update_time:
                now = datetime.now()
                time_diff = (now - self.last_update_time).total_seconds() / 3600
                if time_diff >= self.update_interval_hours:
                    return True
            
            # 如果从未更新过,也进行更新
            if not self.last_update_time:
                return True
        
        return False
    
    def generate_new_questions(self, count=5):
        """生成新题目(模拟从外部API获取)"""
        categories = ['programming', 'math', 'language', 'computer_science', 'ai']
        question_templates = {
            'programming': [
                {
                    "question_text": "Python中,以下哪个关键字用于定义函数?",
                    "question_type": "multiple_choice",
                    "options": ["function", "def", "func", "define"],
                    "correct_answer": "def",
                    "explanation": "在Python中,使用def关键字定义函数",
                    "difficulty": "easy"
                },
                {
                    "question_text": "Python中,列表(List)和元组(Tuple)的主要区别是什么?",
                    "question_type": "multiple_choice",
                    "options": ["大小不同", "列表可变,元组不可变", "速度不同", "语法不同"],
                    "correct_answer": "列表可变,元组不可变",
                    "explanation": "列表是可变的(mutable),元组是不可变的(immutable)",
                    "difficulty": "medium"
                },
                {
                    "question_text": "以下哪个不是Python的内置数据类型?",
                    "question_type": "multiple_choice",
                    "options": ["int", "string", "array", "dict"],
                    "correct_answer": "array",
                    "explanation": "array不是Python内置类型,需要导入array模块",
                    "difficulty": "easy"
                }
            ],
            'math': [
                {
                    "question_text": "如果 f(x) = 2x + 3,那么 f(5) = ?",
                    "question_type": "single_choice",
                    "options": ["10", "13", "7", "8"],
                    "correct_answer": "13",
                    "explanation": "f(5) = 2*5 + 3 = 10 + 3 = 13",
                    "difficulty": "easy"
                },
                {
                    "question_text": "一个正方形的面积是64,它的边长是多少?",
                    "question_type": "single_choice",
                    "options": ["8", "16", "32", "4"],
                    "correct_answer": "8",
                    "explanation": "正方形面积 = 边长^2,所以边长 = sqrt(64) = 8",
                    "difficulty": "easy"
                },
                {
                    "question_text": "2^10 的值是多少?",
                    "question_type": "single_choice",
                    "options": ["512", "1024", "256", "2048"],
                    "correct_answer": "1024",
                    "explanation": "2^10 = 1024",
                    "difficulty": "easy"
                }
            ],
            'language': [
                {
                    "question_text": "The opposite of 'happy' is:",
                    "question_type": "multiple_choice",
                    "options": ["sad", "angry", "tired", "hungry"],
                    "correct_answer": "sad",
                    "explanation": "happy的反义词是sad",
                    "difficulty": "easy"
                },
                {
                    "question_text": "Choose the correct spelling:",
                    "question_type": "multiple_choice",
                    "options": ["accomodate", "accommodate", "acommodate", "acomodate"],
                    "correct_answer": "accommodate",
                    "explanation": "正确拼写是accommodate",
                    "difficulty": "medium"
                },
                {
                    "question_text": "What is the plural form of 'child'?",
                    "question_type": "multiple_choice",
                    "options": ["childs", "childes", "children", "childrens"],
                    "correct_answer": "children",
                    "explanation": "child的复数形式是children",
                    "difficulty": "easy"
                }
            ],
            'computer_science': [
                {
                    "question_text": "以下哪种排序算法的平均时间复杂度是O(n log n)?",
                    "question_type": "multiple_choice",
                    "options": ["冒泡排序", "插入排序", "快速排序", "选择排序"],
                    "correct_answer": "快速排序",
                    "explanation": "快速排序的平均时间复杂度是O(n log n)",
                    "difficulty": "medium"
                },
                {
                    "question_text": "HTTP协议默认使用的端口号是?",
                    "question_type": "single_choice",
                    "options": ["21", "22", "80", "443"],
                    "correct_answer": "80",
                    "explanation": "HTTP默认端口是80,HTTPS是443",
                    "difficulty": "easy"
                },
                {
                    "question_text": "TCP协议属于OSI模型的哪一层?",
                    "question_type": "multiple_choice",
                    "options": ["物理层", "网络层", "传输层", "应用层"],
                    "correct_answer": "传输层",
                    "explanation": "TCP是传输层协议",
                    "difficulty": "medium"
                }
            ],
            'ai': [
                {
                    "question_text": "深度学习是机器学习的一个分支,主要使用什么模型?",
                    "question_type": "multiple_choice",
                    "options": ["决策树", "神经网络", "支持向量机", "随机森林"],
                    "correct_answer": "神经网络",
                    "explanation": "深度学习主要使用神经网络模型",
                    "difficulty": "easy"
                },
                {
                    "question_text": "以下哪个不是常见的激活函数?",
                    "question_type": "multiple_choice",
                    "options": ["ReLU", "Sigmoid", "Tanh", "Linear"],
                    "correct_answer": "Linear",
                    "explanation": "Linear不是激活函数,它只是线性变换",
                    "difficulty": "medium"
                },
                {
                    "question_text": "监督学习和无监督学习的主要区别是什么?",
                    "question_type": "multiple_choice",
                    "options": ["计算速度", "是否有标签", "数据量", "算法复杂度"],
                    "correct_answer": "是否有标签",
                    "explanation": "监督学习需要标注数据,无监督学习不需要",
                    "difficulty": "medium"
                }
            ]
        }
        
        new_questions = []
        for _ in range(count):
            category = random.choice(categories)
            templates = question_templates[category]
            template = random.choice(templates)
            new_questions.append({
                **template,
                'category': category,
                'points': random.randint(5, 15)
            })
        
        return new_questions
    
    def update_question_bank(self):
        """更新题库"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                # 生成新题目
                new_questions = self.generate_new_questions()
                
                # 检查重复并添加新题目
                added_count = 0
                for q in new_questions:
                    # 检查是否已存在相同题目
                    cursor.execute("SELECT id FROM questions WHERE question_text = ?", (q['question_text'],))
                    exists = cursor.fetchone()
                    
                    if not exists:
                        cursor.execute('''
                            INSERT INTO questions 
                            (question_text, question_type, options, correct_answer, 
                             explanation, difficulty, category, points)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            q['question_text'],
                            q['question_type'],
                            json.dumps(q['options']),
                            q['correct_answer'],
                            q['explanation'],
                            q['difficulty'],
                            q['category'],
                            q['points']
                        ))
                        added_count += 1
                
                conn.commit()
                self.last_update_time = datetime.now()
                
                # 记录更新日志
                self.log_update(added_count)
                
                return {'success': True, 'added': added_count, 'message': f'Successfully added {added_count} new questions'}
                
        except Exception as e:
            self.log_update(0, str(e))
            return {'success': False, 'added': 0, 'message': str(e)}
    
    def log_update(self, added_count, error_message=None):
        """记录更新日志"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO system_events 
                    (event_type, description, component, details, occurred_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    'QUESTION_BANK_UPDATE',
                    f'题库更新: 添加了 {added_count} 道新题目',
                    'question_auto_updater',
                    json.dumps({
                        'added_count': added_count,
                        'error': error_message,
                        'update_time': datetime.now().isoformat()
                    }),
                    datetime.now().isoformat()
                ))
                
                conn.commit()
        except Exception:
            pass
    
    def get_update_status(self):
        """获取更新状态"""
        return {
            'last_update_time': self.last_update_time.isoformat() if self.last_update_time else None,
            'update_interval_hours': self.update_interval_hours,
            'trigger_count': self.update_trigger_count,
            'trigger_threshold': self.trigger_threshold,
            'next_update_estimated': (self.last_update_time + 
                                     timedelta(hours=self.update_interval_hours)).isoformat() 
                                     if self.last_update_time else None
        }

# 创建单例
question_auto_updater = QuestionAutoUpdater()

def auto_update_on_access():
    """在访问时自动检查并更新题库"""
    if question_auto_updater.should_update():
        result = question_auto_updater.update_question_bank()
        return result
    return None

if __name__ == '__main__':
    updater = QuestionAutoUpdater()
    print("Testing question auto updater...")
    
    # 模拟多次访问触发更新
    for i in range(12):
        result = updater.should_update()
        print(f"访问 {i+1}: 需要更新 = {result}")
        
        if result:
            update_result = updater.update_question_bank()
            print(f"更新结果: {update_result}")
    
    logger.info("\n更新状态:", updater.get_update_status())
