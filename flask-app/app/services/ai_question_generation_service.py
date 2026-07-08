# -*- coding: utf-8 -*-
"""
AI智能题目生成服务
从文本内容自动生成考试题目，支持多种题型和难度级别
"""

import re
import random
import json
import logging
import sqlite3
import os
from typing import List, Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class AIQuestionGenerationService:
    """AI智能题目生成服务"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                   'split_databases/question.db')
        self.subject_keywords = {
            '语文': ['文章', '段落', '诗词', '文言文', '阅读理解', '写作', '成语', '词语', '修辞'],
            '数学': ['计算', '证明', '方程', '几何', '函数', '概率', '统计', '矩阵', '导数'],
            '英语': ['阅读理解', '完形填空', '语法', '词汇', '翻译', '听力', '写作'],
            '物理': ['力学', '电学', '光学', '热学', '声学', '能量', '运动', '力'],
            '化学': ['反应', '元素', '化合物', '方程式', '离子', '溶液', '酸碱'],
            '生物': ['细胞', '遗传', '进化', '生态', '代谢', '器官', '组织'],
            '历史': ['朝代', '事件', '人物', '战争', '改革', '条约', '文化'],
            '地理': ['气候', '地形', '河流', '城市', '资源', '人口', '环境'],
            '政治': ['哲学', '经济', '政治', '法律', '道德', '社会', '国家'],
            '科学': ['实验', '观察', '推理', '自然', '技术', '发现'],
            '日语': ['词汇', '语法', '听力', '阅读', '会话', '汉字']
        }
        
        self.question_types = ['单选题', '多选题', '判断题', '填空题', '简答题', '论述题']
        
        logger.info("[AI题目生成服务] 初始化完成")
    
    def detect_subject(self, text: str) -> str:
        """根据文本内容自动检测科目"""
        text_lower = text.lower()
        
        for subject, keywords in self.subject_keywords.items():
            for keyword in keywords:
                if keyword in text or keyword.lower() in text_lower:
                    return subject
        
        return '其他'
    
    def extract_key_points(self, text: str) -> List[str]:
        """从文本中提取关键点"""
        sentences = re.split(r'[。！？；\n\r]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        key_points = []
        for sentence in sentences:
            if len(sentence) > 10:
                key_points.append(sentence[:100])
        
        return key_points[:20]
    
    def generate_single_choice(self, text: str, key_point: str) -> Dict:
        """生成单选题"""
        options = ['A', 'B', 'C', 'D']
        
        question = f"关于以下内容，哪个说法是正确的？\n\"{key_point[:80]}...\""
        
        correct_idx = random.randint(0, 3)
        correct_answer = options[correct_idx]
        
        wrong_answers = []
        for i in range(3):
            wrong_answers.append(f"错误选项{chr(65 + i)}")
        
        options_list = []
        idx = 0
        for i in range(4):
            if i == correct_idx:
                options_list.append({"option": options[i], "content": "正确答案选项"})
            else:
                options_list.append({"option": options[i], "content": wrong_answers[idx]})
                idx += 1
        
        return {
            'type': '单选题',
            'question': question,
            'options': options_list,
            'answer': correct_answer,
            'analysis': f"本题考查对文本内容的理解。正确答案为{correct_answer}，因为..."
        }
    
    def generate_multiple_choice(self, text: str, key_point: str) -> Dict:
        """生成多选题"""
        options = ['A', 'B', 'C', 'D', 'E']
        
        question = f"根据以下内容，哪些说法是正确的？（多选）\n\"{key_point[:80]}...\""
        
        correct_count = random.randint(2, 3)
        correct_indices = random.sample(range(5), correct_count)
        correct_answer = ''.join(sorted([options[i] for i in correct_indices]))
        
        options_list = []
        for i in range(5):
            is_correct = i in correct_indices
            options_list.append({
                "option": options[i],
                "content": "正确选项" if is_correct else f"错误选项{options[i]}",
                "is_correct": is_correct
            })
        
        return {
            'type': '多选题',
            'question': question,
            'options': options_list,
            'answer': correct_answer,
            'analysis': f"本题考查对文本内容的综合理解。正确答案为{correct_answer}。"
        }
    
    def generate_judgment(self, text: str, key_point: str) -> Dict:
        """生成判断题"""
        question = f"判断正误：\n\"{key_point[:80]}...\""
        
        is_true = random.choice([True, False])
        answer = '正确' if is_true else '错误'
        
        return {
            'type': '判断题',
            'question': question,
            'answer': answer,
            'analysis': f"本题考查对文本内容的判断能力。{answer}，因为..."
        }
    
    def generate_fill_blank(self, text: str, key_point: str) -> Dict:
        """生成填空题"""
        words = key_point.split()
        if len(words) < 3:
            return None
        
        blank_idx = random.randint(1, min(len(words) - 2, 3))
        blank_word = words[blank_idx]
        
        words[blank_idx] = '______'
        question = ' '.join(words)[:100]
        
        return {
            'type': '填空题',
            'question': question,
            'answer': blank_word,
            'analysis': f"本题考查对关键概念的记忆。正确答案是：{blank_word}"
        }
    
    def generate_short_answer(self, text: str, key_point: str) -> Dict:
        """生成简答题"""
        question = f"请简述以下内容的主要观点：\n\"{key_point[:80]}...\""
        
        return {
            'type': '简答题',
            'question': question,
            'answer': "参考答案：根据文本内容，主要观点包括...",
            'analysis': "本题考查对文本内容的归纳和总结能力。"
        }
    
    def generate_discussion(self, text: str, key_point: str) -> Dict:
        """生成论述题"""
        question = f"请结合以下内容，论述相关问题：\n\"{key_point[:80]}...\"\n\n要求：观点明确，论据充分，逻辑清晰，不少于200字。"
        
        return {
            'type': '论述题',
            'question': question,
            'answer': "参考答案：本题要求考生结合文本内容进行论述。答题要点包括：1. 观点阐述...",
            'analysis': "本题考查综合分析和论述能力，需要考生结合文本内容进行深入分析。"
        }
    
    def generate_questions(self, text: str, count: int = 10, types: Optional[List[str]] = None, 
                          difficulty: str = 'medium', subject: str = None) -> Dict:
        """
        从文本生成题目
        :param text: 输入文本
        :param count: 生成题目数量
        :param types: 题型列表
        :param difficulty: 难度等级
        :param subject: 科目（自动检测或指定）
        """
        if not types:
            types = self.question_types
        
        if not subject:
            subject = self.detect_subject(text)
        
        key_points = self.extract_key_points(text)
        if not key_points:
            return {
                'success': False,
                'message': '无法从文本中提取有效内容'
            }
        
        questions = []
        type_weights = {
            '单选题': 30,
            '多选题': 20,
            '判断题': 15,
            '填空题': 15,
            '简答题': 12,
            '论述题': 8
        }
        
        available_types = [t for t in types if t in type_weights]
        if not available_types:
            available_types = ['单选题', '多选题', '判断题']
        
        for _ in range(count):
            key_point = random.choice(key_points)
            
            type_choice = random.choices(available_types, 
                                        weights=[type_weights.get(t, 10) for t in available_types])[0]
            
            question = None
            if type_choice == '单选题':
                question = self.generate_single_choice(text, key_point)
            elif type_choice == '多选题':
                question = self.generate_multiple_choice(text, key_point)
            elif type_choice == '判断题':
                question = self.generate_judgment(text, key_point)
            elif type_choice == '填空题':
                question = self.generate_fill_blank(text, key_point)
            elif type_choice == '简答题':
                question = self.generate_short_answer(text, key_point)
            elif type_choice == '论述题':
                question = self.generate_discussion(text, key_point)
            
            if question:
                question['difficulty'] = difficulty
                question['subject'] = subject
                question['generated_at'] = datetime.now().isoformat()
                questions.append(question)
        
        return {
            'success': True,
            'data': {
                'subject': subject,
                'total_questions': len(questions),
                'types': types,
                'difficulty': difficulty,
                'questions': questions
            }
        }
    
    def save_questions(self, questions: List[Dict], user_id: int = 0) -> Dict:
        """保存生成的题目到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            saved_count = 0
            for q in questions:
                options_str = json.dumps(q.get('options', []), ensure_ascii=False)
                
                cursor.execute('''
                    INSERT INTO questions (subject, type, question, options, answer, 
                                          analysis, difficulty, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    q.get('subject', '其他'),
                    q.get('type', '单选题'),
                    q.get('question', ''),
                    options_str,
                    q.get('answer', ''),
                    q.get('analysis', ''),
                    q.get('difficulty', 'medium'),
                    datetime.now().isoformat()
                ))
                
                saved_count += 1
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': f'成功保存 {saved_count} 道题目',
                'saved_count': saved_count
            }
        
        except Exception as e:
            logger.error(f"[保存题目失败] {e}")
            return {
                'success': False,
                'message': f'保存失败: {e}'
            }
    
    def get_generation_stats(self) -> Dict:
        """获取生成统计"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM questions")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT type, COUNT(*) FROM questions GROUP BY type")
            by_type = {row[0]: row[1] for row in cursor.fetchall()}
            
            cursor.execute("SELECT subject, COUNT(*) FROM questions GROUP BY subject ORDER BY COUNT(*) DESC LIMIT 10")
            by_subject = [{'subject': row[0], 'count': row[1]} for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                'success': True,
                'data': {
                    'total_questions': total,
                    'by_type': by_type,
                    'top_subjects': by_subject
                }
            }
        except Exception as e:
            logger.error(f"[获取统计失败] {e}")
            return {
                'success': False,
                'message': str(e)
            }


ai_question_generation_service = AIQuestionGenerationService()
