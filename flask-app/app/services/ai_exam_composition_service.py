# -*- coding: utf-8 -*-
"""
AI试卷自动组卷服务
根据科目、难度、题型自动从题库中选择题目组卷，确保知识覆盖率均衡
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


class AIExamCompositionService:
    """AI试卷自动组卷服务"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                   'split_databases/question.db')
        self.exam_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                         'split_databases/exam.db')
        
        self.subjects = ['语文', '数学', '英语', '物理', '化学', '生物', '历史', '地理', '政治', '科学', '日语']
        self.question_types = ['单选题', '多选题', '判断题', '填空题', '简答题', '论述题']
        self.difficulties = ['easy', 'medium', 'hard']
        
        self.knowledge_points = {
            '语文': ['文言文', '现代文阅读', '诗词鉴赏', '写作', '语言运用', '文学常识'],
            '数学': ['函数', '几何', '代数', '概率统计', '三角函数', '数列'],
            '英语': ['阅读理解', '完形填空', '语法填空', '翻译', '写作', '词汇'],
            '物理': ['力学', '电学', '光学', '热学', '波动', '原子物理'],
            '化学': ['无机化学', '有机化学', '化学反应', '溶液', '元素周期', '化学实验'],
            '生物': ['细胞生物学', '遗传学', '生态学', '代谢', '生物技术', '生命调节'],
            '历史': ['中国古代史', '中国近现代史', '世界史', '古代文明', '近代史', '现代史'],
            '地理': ['自然地理', '人文地理', '区域地理', '气候', '地形', '资源'],
            '政治': ['哲学', '经济学', '政治学', '法律', '道德', '社会'],
            '科学': ['生命科学', '物质科学', '地球与宇宙', '科学探究', '技术应用', '环境'],
            '日语': ['词汇', '语法', '听力', '阅读', '写作', '会话']
        }
        
        logger.info("[AI试卷组卷服务] 初始化完成")
    
    def get_questions_from_bank(self, subject: str, qtype: str, difficulty: str, count: int = 10) -> List[Dict]:
        """从题库中获取指定条件的题目"""
        questions = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = """
                    SELECT * FROM questions 
                    WHERE subject = ? AND question_type = ? AND difficulty = ? 
                    ORDER BY RANDOM() LIMIT ?
                """
                cursor.execute(query, (subject, qtype, difficulty, count))
                rows = cursor.fetchall()
                
                for row in rows:
                    questions.append(dict(row))
                    
        except Exception as e:
            logger.error(f"[组卷服务] 获取题库题目失败: {e}")
        
        return questions
    
    def get_question_count(self, subject: str, qtype: str = None, difficulty: str = None) -> int:
        """获取题库中满足条件的题目数量"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if qtype and difficulty:
                    cursor.execute("SELECT COUNT(*) FROM questions WHERE subject = ? AND question_type = ? AND difficulty = ?", 
                                  (subject, qtype, difficulty))
                elif qtype:
                    cursor.execute("SELECT COUNT(*) FROM questions WHERE subject = ? AND question_type = ?", 
                                  (subject, qtype))
                elif difficulty:
                    cursor.execute("SELECT COUNT(*) FROM questions WHERE subject = ? AND difficulty = ?", 
                                  (subject, difficulty))
                else:
                    cursor.execute("SELECT COUNT(*) FROM questions WHERE subject = ?", (subject,))
                
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"[组卷服务] 获取题目数量失败: {e}")
            return 0
    
    def calculate_difficulty_distribution(self, total_count: int, difficulty_ratio: Optional[Dict] = None) -> Dict:
        """计算难度分布"""
        if difficulty_ratio is None:
            difficulty_ratio = {'easy': 0.3, 'medium': 0.5, 'hard': 0.2}
        
        distribution = {}
        remaining = total_count
        
        for diff, ratio in difficulty_ratio.items():
            count = int(total_count * ratio)
            distribution[diff] = count
            remaining -= count
        
        distribution['medium'] += remaining
        return distribution
    
    def calculate_type_distribution(self, total_count: int, types: List[str], type_ratio: Optional[Dict] = None) -> Dict:
        """计算机型分布"""
        if type_ratio is None:
            type_ratio = {
                '单选题': 0.4,
                '多选题': 0.15,
                '判断题': 0.15,
                '填空题': 0.1,
                '简答题': 0.1,
                '论述题': 0.1
            }
        
        distribution = {}
        remaining = total_count
        
        for qtype in types:
            ratio = type_ratio.get(qtype, 1.0 / len(types))
            count = int(total_count * ratio)
            distribution[qtype] = count
            remaining -= count
        
        distribution[types[0]] += remaining
        return distribution
    
    def compose_exam(self, subject: str, total_questions: int = 50, 
                     types: Optional[List[str]] = None, 
                     difficulty_ratio: Optional[Dict] = None,
                     type_ratio: Optional[Dict] = None,
                     total_score: int = 100,
                     exam_name: str = None) -> Dict:
        """自动组卷"""
        if types is None:
            types = ['单选题', '多选题', '判断题', '填空题', '简答题', '论述题']
        
        diff_dist = self.calculate_difficulty_distribution(total_questions, difficulty_ratio)
        type_dist = self.calculate_type_distribution(total_questions, types, type_ratio)
        
        questions = []
        selected_ids = set()
        
        for qtype in types:
            type_count = type_dist.get(qtype, 0)
            if type_count <= 0:
                continue
            
            for diff in self.difficulties:
                needed = int(type_count * diff_dist.get(diff, 0) / total_questions * type_count)
                if needed <= 0:
                    continue
                
                available = self.get_questions_from_bank(subject, qtype, diff, needed)
                
                for q in available:
                    if q['id'] not in selected_ids and len(questions) < total_questions:
                        questions.append(q)
                        selected_ids.add(q['id'])
        
        if len(questions) < total_questions:
            for qtype in types:
                remaining = total_questions - len(questions)
                if remaining <= 0:
                    break
                
                available = self.get_questions_from_bank(subject, qtype, 'medium', remaining)
                for q in available:
                    if q['id'] not in selected_ids and len(questions) < total_questions:
                        questions.append(q)
                        selected_ids.add(q['id'])
        
        random.shuffle(questions)
        
        score_dist = self.calculate_score_distribution(len(questions), total_score, types)
        
        exam_questions = []
        current_score = 0
        for i, q in enumerate(questions):
            qtype = q['question_type']
            score = score_dist.get(qtype, 2)
            if current_score + score > total_score and i > 0:
                score = total_score - current_score
            current_score += score
            
            exam_questions.append({
                'question_id': q['id'],
                'question_type': qtype,
                'content': q['content'],
                'options': q.get('options', '[]'),
                'answer': q.get('answer', ''),
                'analysis': q.get('analysis', ''),
                'difficulty': q['difficulty'],
                'score': score,
                'order': i + 1
            })
        
        exam_data = {
            'exam_name': exam_name or f"{subject}测试试卷",
            'subject': subject,
            'total_questions': len(exam_questions),
            'total_score': total_score,
            'duration': self.calculate_duration(subject, len(exam_questions)),
            'difficulty_distribution': diff_dist,
            'type_distribution': type_dist,
            'questions': exam_questions,
            'generated_at': datetime.now().isoformat(),
            'knowledge_coverage': self.analyze_knowledge_coverage(exam_questions, subject),
            'quality_score': self.calculate_quality_score(exam_questions)
        }
        
        logger.info(f"[组卷服务] 成功生成试卷: {exam_data['exam_name']}, {len(exam_questions)}题")
        return exam_data
    
    def calculate_score_distribution(self, total_count: int, total_score: int, types: List[str]) -> Dict:
        """计算分数分布"""
        base_scores = {
            '单选题': 2,
            '多选题': 4,
            '判断题': 1,
            '填空题': 2,
            '简答题': 6,
            '论述题': 10
        }
        
        return base_scores
    
    def calculate_duration(self, subject: str, question_count: int) -> int:
        """计算考试时长(分钟)"""
        base_time = question_count * 2
        if subject in ['数学', '物理', '化学']:
            base_time = question_count * 2.5
        elif subject in ['语文', '英语']:
            base_time = question_count * 2.2
        
        return int(base_time)
    
    def analyze_knowledge_coverage(self, questions: List[Dict], subject: str) -> Dict:
        """分析知识覆盖率"""
        points = self.knowledge_points.get(subject, [])
        coverage = {point: 0 for point in points}
        
        for q in questions:
            content = q['content']
            for point in points:
                if point in content:
                    coverage[point] += 1
        
        total = len(questions)
        if total > 0:
            coverage = {k: round(v / total * 100, 2) for k, v in coverage.items()}
        
        return coverage
    
    def calculate_quality_score(self, questions: List[Dict]) -> float:
        """计算试卷质量分数"""
        if not questions:
            return 0.0
        
        difficulty_weights = {'easy': 1, 'medium': 2, 'hard': 3}
        type_weights = {'单选题': 1, '多选题': 2, '判断题': 1, '填空题': 2, '简答题': 3, '论述题': 4}
        
        total_weight = 0
        total_score = 0
        
        for q in questions:
            diff_weight = difficulty_weights.get(q['difficulty'], 1)
            type_weight = type_weights.get(q['question_type'], 1)
            total_weight += diff_weight + type_weight
            total_score += (diff_weight + type_weight) * 10
        
        return round(total_score / max(total_weight, 1), 2)
    
    def save_exam(self, exam_data: Dict, user_id: int = 0) -> int:
        """保存试卷到数据库"""
        try:
            with sqlite3.connect(self.exam_db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO exams (name, subject, total_questions, total_score, duration, 
                                      difficulty_distribution, type_distribution, knowledge_coverage,
                                      quality_score, generated_by, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    exam_data['exam_name'],
                    exam_data['subject'],
                    exam_data['total_questions'],
                    exam_data['total_score'],
                    exam_data['duration'],
                    json.dumps(exam_data['difficulty_distribution']),
                    json.dumps(exam_data['type_distribution']),
                    json.dumps(exam_data['knowledge_coverage']),
                    exam_data['quality_score'],
                    user_id,
                    datetime.now().isoformat()
                ))
                
                exam_id = cursor.lastrowid
                
                for q in exam_data['questions']:
                    cursor.execute("""
                        INSERT INTO exam_questions (exam_id, question_id, question_type, content, 
                                                   options, answer, analysis, difficulty, score, `order`)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        exam_id,
                        q['question_id'],
                        q['question_type'],
                        q['content'],
                        q['options'],
                        q['answer'],
                        q['analysis'],
                        q['difficulty'],
                        q['score'],
                        q['order']
                    ))
                
                conn.commit()
                logger.info(f"[组卷服务] 试卷保存成功: exam_id={exam_id}")
                return exam_id
        
        except Exception as e:
            logger.error(f"[组卷服务] 保存试卷失败: {e}")
            return -1
    
    def get_exam_statistics(self, subject: str = None) -> Dict:
        """获取组卷统计信息"""
        stats = {}
        
        if subject:
            stats['subject'] = subject
            stats['total_questions_in_bank'] = self.get_question_count(subject)
            
            for qtype in self.question_types:
                stats[f'{qtype}_count'] = self.get_question_count(subject, qtype=qtype)
            
            for diff in self.difficulties:
                stats[f'{diff}_count'] = self.get_question_count(subject, difficulty=diff)
        else:
            stats['total_subjects'] = len(self.subjects)
            stats['subject_question_counts'] = {}
            
            for subj in self.subjects:
                stats['subject_question_counts'][subj] = self.get_question_count(subj)
        
        return stats
    
    def preview_exam(self, exam_data: Dict) -> Dict:
        """预览试卷摘要"""
        return {
            'exam_name': exam_data['exam_name'],
            'subject': exam_data['subject'],
            'total_questions': exam_data['total_questions'],
            'total_score': exam_data['total_score'],
            'duration': exam_data['duration'],
            'difficulty_distribution': exam_data['difficulty_distribution'],
            'type_distribution': exam_data['type_distribution'],
            'knowledge_coverage': exam_data['knowledge_coverage'],
            'quality_score': exam_data['quality_score'],
            'question_preview': exam_data['questions'][:5]
        }