#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI题目筛选和生成服务
负责自动过滤、筛选、匹配和校验题目到考卷
"""

import json
import random
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4

from app.utils.logging import logger


class AIQuestionFilterService:
    """AI题目筛选和生成服务"""
    
    def __init__(self):
        """初始化题目筛选服务"""
        self.question_validators = [
            self._validate_content,
            self._validate_options,
            self._validate_answer,
            self._validate_difficulty,
            self._validate_points
        ]
        
        self.quality_checks = [
            self._check_content_length,
            self._check_option_variety,
            self._check_answer_ambiguity,
            self._check_language_quality
        ]
        
        self.subject_knowledge = {
            'math': {
                'topics': ['代数', '几何', '函数', '概率', '统计', '三角函数', '数列', '不等式', '解析几何'],
                'keywords': ['方程', '求解', '证明', '计算', '推导', '化简', '求值', '判断'],
                'difficulty_map': {'easy': (1, 3), 'medium': (3, 5), 'hard': (5, 8)}
            },
            'chinese': {
                'topics': ['阅读理解', '写作', '语法', '诗词', '文言文', '现代文', '修辞', '文学常识'],
                'keywords': ['理解', '分析', '赏析', '翻译', '概括', '仿写', '填空', '选择'],
                'difficulty_map': {'easy': (1, 3), 'medium': (3, 5), 'hard': (5, 8)}
            },
            'english': {
                'topics': ['词汇', '语法', '阅读理解', '完形填空', '写作', '听力', '口语', '翻译'],
                'keywords': ['choose', 'fill', 'translate', 'read', 'write', 'complete', 'correct', 'select'],
                'difficulty_map': {'easy': (1, 3), 'medium': (3, 5), 'hard': (5, 8)}
            },
            'physics': {
                'topics': ['力学', '电学', '光学', '热学', '声学', '原子物理', '电磁学', '波动'],
                'keywords': ['计算', '证明', '分析', '推导', '求解', '判断', '实验', '现象'],
                'difficulty_map': {'easy': (2, 4), 'medium': (4, 6), 'hard': (6, 9)}
            },
            'chemistry': {
                'topics': ['无机化学', '有机化学', '化学反应', '元素周期', '溶液', '氧化还原', '化学平衡'],
                'keywords': ['反应', '计算', '判断', '写出', '解释', '分析', '配制', '检验'],
                'difficulty_map': {'easy': (2, 4), 'medium': (4, 6), 'hard': (6, 9)}
            },
            'biology': {
                'topics': ['细胞', '遗传', '生态', '代谢', '进化', '免疫', '植物', '动物'],
                'keywords': ['判断', '填空', '选择', '解释', '分析', '实验', '设计', '说明'],
                'difficulty_map': {'easy': (1, 3), 'medium': (3, 5), 'hard': (5, 8)}
            },
            'japanese': {
                'topics': ['词汇', '语法', '阅读', '听力', '写作', '汉字', '敬语', '会话'],
                'keywords': ['選択', '記入', '訳', '読解', '書', '聞', '答', '正しい'],
                'difficulty_map': {'easy': (1, 3), 'medium': (3, 5), 'hard': (5, 8)}
            }
        }
        
        logger.info("AI题目筛选服务初始化完成")
    
    def filter_and_generate_questions(self, exam_id: str, exam_data: Dict) -> List[Dict]:
        """筛选并生成考试题目"""
        try:
            language_to_subject = {
                'zh': 'chinese',
                'zh-cn': 'chinese',
                'chinese': 'chinese',
                'ja': 'japanese',
                'jp': 'japanese',
                'japanese': 'japanese',
                'en': 'english',
                'english': 'english'
            }
            
            language = exam_data.get('language', 'zh').lower()
            subject = exam_data.get('subject', language_to_subject.get(language, 'math')).lower()
            
            question_count = exam_data.get('question_count', 20)
            difficulty = exam_data.get('level', 'intermediate')
            duration = exam_data.get('duration', 60)
            
            questions = self._generate_questions(subject, question_count, difficulty, duration)
            
            validated_questions = []
            for question in questions:
                if self._validate_question(question) and self._check_question_quality(question):
                    validated_questions.append(question)
                    if len(validated_questions) >= question_count:
                        break
            
            if len(validated_questions) < question_count:
                additional = self._generate_fallback_questions(
                    subject, question_count - len(validated_questions), difficulty
                )
                validated_questions.extend(additional[:question_count - len(validated_questions)])
            
            for i, q in enumerate(validated_questions):
                q['id'] = f"Q_{exam_id[:8]}_{i+1}"
                q['exam_id'] = exam_id
                q['order_index'] = i + 1
            
            logger.info(f"为考试 {exam_id} 生成并验证了 {len(validated_questions)} 道题目")
            return validated_questions
            
        except Exception as e:
            logger.error(f"筛选和生成题目失败: {str(e)}")
            return self._generate_fallback_questions(subject, question_count, difficulty)
    
    def _generate_questions(self, subject: str, count: int, difficulty: str, duration: int) -> List[Dict]:
        """生成题目"""
        questions = []
        
        subject_info = self.subject_knowledge.get(subject, self.subject_knowledge['math'])
        topics = subject_info['topics']
        keywords = subject_info['keywords']
        
        difficulty_range = subject_info['difficulty_map'].get(difficulty, (2, 5))
        
        questions_per_topic = max(1, count // len(topics))
        
        for topic in topics:
            for _ in range(questions_per_topic):
                if len(questions) >= count:
                    break
                
                question = self._generate_single_question(subject, topic, keywords, difficulty_range)
                questions.append(question)
            
            if len(questions) >= count:
                break
        
        while len(questions) < count:
            topic = random.choice(topics)
            question = self._generate_single_question(subject, topic, keywords, difficulty_range)
            questions.append(question)
        
        random.shuffle(questions)
        return questions[:count]
    
    def _generate_single_question(self, subject: str, topic: str, keywords: list, difficulty_range: tuple) -> Dict:
        """生成单个题目"""
        question_type = 'single_choice'
        
        difficulty = random.randint(difficulty_range[0], difficulty_range[1])
        
        content, options, correct_answer = self._generate_question_content(subject, topic, question_type, difficulty)
        
        points = max(1, 10 - difficulty)
        
        question = {
            'id': str(uuid4())[:8],
            'type': question_type,
            'content': content,
            'options': options,
            'correct_answer': correct_answer,
            'difficulty': difficulty,
            'points': points,
            'tags': [subject, topic],
            'explanation': self._generate_explanation(content, correct_answer),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        return question
    
    def _generate_question_content(self, subject: str, topic: str, question_type: str, difficulty: int) -> tuple:
        """生成题目内容"""
        templates = {
            'single_choice': [
                f"关于{topic}，以下说法正确的是？",
                f"{topic}的主要特征是？",
                f"在{topic}中，{random.choice(['正确的', '错误的'])}描述是？",
                f"{topic}相关的概念，下列选项中{random.choice(['正确', '不准确'])}的是？"
            ],
            'multiple_choice': [
                f"以下关于{topic}的说法，正确的有？",
                f"{topic}的特点包括？",
                f"在{topic}中，下列描述{random.choice(['正确', '错误'])}的是？"
            ],
            'true_false': [
                f"{topic}的核心概念是{random.choice(['基础的', '复杂的'])}。",
                f"{topic}在{random.choice(['实际应用', '理论研究'])}中具有重要意义。",
                f"{topic}的{random.choice(['基本原理', '高级特性'])}适用于{random.choice(['大多数', '特定'])}情况。"
            ]
        }
        
        template = random.choice(templates.get(question_type, templates['single_choice']))
        
        if question_type == 'true_false':
            content = template
            correct_key = random.choice(['A', 'B'])
            options = [
                {'key': 'A', 'text': '正确', 'is_correct': (correct_key == 'A'), 'is_distractor': (correct_key != 'A')},
                {'key': 'B', 'text': '错误', 'is_correct': (correct_key == 'B'), 'is_distractor': (correct_key != 'B')}
            ]
            correct_answer = correct_key
        else:
            content = template
            options = self._generate_options(subject, topic, difficulty)
            
            correct_options = [opt for opt in options if opt.get('is_correct')]
            if question_type == 'multiple_choice':
                correct_answer = ','.join([opt['key'] for opt in correct_options])
            else:
                correct_answer = correct_options[0]['key'] if correct_options else options[0]['key']
        
        return content, options, correct_answer
    
    def _generate_options(self, subject: str, topic: str, difficulty: int) -> List[Dict]:
        """生成选项（包含正确选项和混淆选项）"""
        option_keys = ['A', 'B', 'C', 'D']
        
        subject_info = self.subject_knowledge.get(subject, self.subject_knowledge['math'])
        keywords = subject_info['keywords']
        
        correct_texts = [
            f"{topic}的{random.choice(['基本特征', '核心要素', '主要性质', '本质属性'])}是{random.choice(keywords)}",
            f"{topic}中，{random.choice(keywords)}指的是{topic}的{random.choice(['基本概念', '重要原理', '核心内容'])}",
            f"{topic}的{random.choice(['定义', '特点', '作用', '意义'])}是：{random.choice(keywords)}",
            f"关于{topic}，{random.choice(keywords)}是{random.choice(['正确的', '准确的', '符合要求的'])}描述"
        ]
        
        distractor_patterns = [
            (f"{topic}的{random.choice(['基础', '进阶', '高级', '特殊'])}概念", 
             f"{topic}的{random.choice(['初级', '中级', '高级', '特殊'])}概念与{random.choice(keywords)}相关"),
            (f"{topic}相关的{random.choice(['常见错误', '容易混淆', '类似'])}知识点", 
             f"{random.choice(['与', '关于', '涉及'])} {topic}的{random.choice(['错误理解', '常见误区', '混淆概念'])}"),
            (f"{topic}的{random.choice(['应用场景', '理论基础', '扩展内容'])}", 
             f"{topic}在{random.choice(['实际应用', '理论研究', '日常场景'])}中的{random.choice(['表现', '作用', '意义'])}"),
            (f"{random.choice(['与', '关于', '涉及'])} {topic}的{random.choice(['其他', '相关', '补充'])}知识", 
             f"{random.choice(['与', '关于', '涉及'])} {topic}的{random.choice(['边缘', '相关', '辅助'])}知识")
        ]
        
        options = []
        correct_index = random.randint(0, 3)
        
        for i, key in enumerate(option_keys):
            if i == correct_index:
                text = random.choice(correct_texts)
                is_correct = True
            else:
                pattern = distractor_patterns[i % len(distractor_patterns)]
                text = random.choice(pattern)
                is_correct = False
            
            options.append({
                'key': key,
                'text': text,
                'is_correct': is_correct,
                'is_distractor': not is_correct
            })
        
        if difficulty >= 4:
            random.shuffle(options)
        
        return options
    
    def _generate_explanation(self, content: str, answer: str) -> str:
        """生成题目解析"""
        return f"本题考查相关知识点。正确答案为{answer}，因为根据所学知识，该选项符合题目要求。"
    
    def _generate_fallback_questions(self, subject: str, count: int, difficulty: str) -> List[Dict]:
        """生成备选题目（当AI生成失败时使用）"""
        questions = []
        
        for i in range(count):
            correct_key = random.choice(['A', 'B', 'C', 'D'])
            question = {
                'id': f"FB_{i+1}",
                'type': 'single_choice',
                'content': f"{subject}测试题目 {i+1}：请选择正确的答案",
                'options': [
                    {'key': 'A', 'text': '选项A：正确答案', 'is_correct': (correct_key == 'A'), 'is_distractor': (correct_key != 'A')},
                    {'key': 'B', 'text': '选项B：混淆选项1', 'is_correct': (correct_key == 'B'), 'is_distractor': (correct_key != 'B')},
                    {'key': 'C', 'text': '选项C：混淆选项2', 'is_correct': (correct_key == 'C'), 'is_distractor': (correct_key != 'C')},
                    {'key': 'D', 'text': '选项D：混淆选项3', 'is_correct': (correct_key == 'D'), 'is_distractor': (correct_key != 'D')}
                ],
                'correct_answer': correct_key,
                'difficulty': 3,
                'points': 5,
                'tags': [subject],
                'explanation': '本题为系统生成的测试题目。',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            questions.append(question)
        
        return questions
    
    def _validate_question(self, question: Dict) -> bool:
        """验证题目"""
        for validator in self.question_validators:
            if not validator(question):
                return False
        return True
    
    def _validate_content(self, question: Dict) -> bool:
        """验证题目内容"""
        content = question.get('content', '')
        return len(content.strip()) > 5 and len(content.strip()) < 500
    
    def _validate_options(self, question: Dict) -> bool:
        """验证选项"""
        options = question.get('options', [])
        
        if question['type'] == 'true_false':
            return len(options) == 2
        
        if question['type'] == 'single_choice':
            return len(options) >= 2 and len(options) <= 6
        
        if question['type'] == 'multiple_choice':
            return len(options) >= 3 and len(options) <= 8
        
        return len(options) >= 2
    
    def _validate_answer(self, question: Dict) -> bool:
        """验证答案"""
        answer = question.get('correct_answer', '')
        options = question.get('options', [])
        
        if question['type'] == 'multiple_choice':
            answers = answer.split(',')
            for a in answers:
                if a.strip() not in [opt['key'] for opt in options]:
                    return False
            return len(answers) >= 1
        else:
            return answer in [opt['key'] for opt in options]
    
    def _validate_difficulty(self, question: Dict) -> bool:
        """验证难度"""
        difficulty = question.get('difficulty', 1)
        return 1 <= difficulty <= 10
    
    def _validate_points(self, question: Dict) -> bool:
        """验证分值"""
        points = question.get('points', 1)
        return 0.5 <= points <= 50
    
    def _check_question_quality(self, question: Dict) -> bool:
        """检查题目质量"""
        for checker in self.quality_checks:
            if not checker(question):
                return False
        return True
    
    def _check_content_length(self, question: Dict) -> bool:
        """检查内容长度"""
        content = question.get('content', '')
        return 10 <= len(content.strip()) <= 300
    
    def _check_option_variety(self, question: Dict) -> bool:
        """检查选项多样性"""
        options = question.get('options', [])
        option_texts = [opt['text'] for opt in options]
        
        unique_texts = set(option_texts)
        return len(unique_texts) == len(options)
    
    def _check_answer_ambiguity(self, question: Dict) -> bool:
        """检查答案是否明确"""
        content = question.get('content', '')
        answer = question.get('correct_answer', '')
        
        ambiguous_phrases = ['可能', '也许', '大概', '似乎', '好像', '应该']
        
        for phrase in ambiguous_phrases:
            if phrase in content:
                return False
        
        return True
    
    def _check_language_quality(self, question: Dict) -> bool:
        """检查语言质量"""
        content = question.get('content', '')
        
        errors = ['。。', '，，', '！！', '？？']
        for error in errors:
            if error in content:
                return False
        
        return True
    
    def match_questions_to_exam(self, questions: List[Dict], exam_data: Dict) -> List[Dict]:
        """将题目匹配到考试要求"""
        subject = exam_data.get('subject', 'math').lower()
        difficulty = exam_data.get('level', 'intermediate')
        question_count = exam_data.get('question_count', 20)
        
        filtered = []
        
        for question in questions:
            if len(filtered) >= question_count:
                break
            
            question_subject = question.get('subject', question.get('tags', [])[0] if question.get('tags') else '')
            if question_subject and question_subject.lower() != subject:
                continue
            
            question_difficulty = question.get('difficulty', 3)
            
            if difficulty == 'easy' and question_difficulty > 4:
                continue
            if difficulty == 'hard' and question_difficulty < 4:
                continue
            
            filtered.append(question)
        
        while len(filtered) < question_count:
            fallback = self._generate_fallback_questions(subject, 1, difficulty)
            filtered.extend(fallback)
        
        return filtered[:question_count]
    
    def save_questions_to_exam(self, exam_id: str, questions: List[Dict], db_manager=None) -> bool:
        """保存题目到考试"""
        try:
            import sqlite3
            import os
            
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'app.db')
            db_path = os.path.abspath(db_path)
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                for question in questions:
                    question['exam_id'] = exam_id
                    
                    options_json = json.dumps(question['options'], ensure_ascii=False)
                    tags_json = json.dumps(question.get('tags', []), ensure_ascii=False)
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO questions 
                        (id, exam_id, type, content, options, correct_answer, 
                         difficulty, points, tags, explanation, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                    question['id'],
                    question['exam_id'],
                    question['type'],
                    question['content'],
                    options_json,
                    question['correct_answer'],
                    question['difficulty'],
                    question['points'],
                    tags_json,
                    question.get('explanation', ''),
                    question.get('created_at', datetime.now().isoformat()),
                    question.get('updated_at', datetime.now().isoformat())
                ))
            
            conn.commit()
            logger.info(f"成功保存 {len(questions)} 道题目到考试 {exam_id}")
            return True
            
        except Exception as e:
            logger.error(f"保存题目失败: {str(e)}")
            return False


ai_question_filter_service = None

def get_ai_question_filter_service():
    """获取AI题目筛选服务实例"""
    global ai_question_filter_service
    if ai_question_filter_service is None:
        ai_question_filter_service = AIQuestionFilterService()
    return ai_question_filter_service