#!/usr/bin/env python3
""" AI智能组卷系统 根据教学大纲和考试要求自动生成试卷 """

import sqlite3
import hashlib
import json
import random
from datetime import datetime
from typing import Dict, List, Optional

class AIPaperGenerator:
    """AI智能组卷引擎"""
    
    SUBJECT_TOPICS = {
        '数学': ['函数基础', '导数', '三角函数', '概率统计', '立体几何', '数列', '解析几何'],
        '英语': ['词汇', '语法', '阅读理解', '完形填空', '写作', '听力理解'],
        '物理': ['力学', '电磁学', '热学', '光学', '原子物理', '波动'],
        '化学': ['无机化学', '有机化学', '化学反应原理', '化学实验', '元素周期律'],
        '语文': ['现代文阅读', '文言文', '诗歌鉴赏', '语言运用', '作文']
    }
    
    QUESTION_TYPES = {
        'choice': {'name': '选择题', 'score_per': 2, 'difficulty_weights': {'easy': 0.4, 'medium': 0.4, 'hard': 0.2}},
        'fill': {'name': '填空题', 'score_per': 3, 'difficulty_weights': {'easy': 0.3, 'medium': 0.5, 'hard': 0.2}},
        'short': {'name': '简答题', 'score_per': 5, 'difficulty_weights': {'easy': 0.2, 'medium': 0.5, 'hard': 0.3}},
        'calculation': {'name': '计算题', 'score_per': 10, 'difficulty_weights': {'easy': 0.1, 'medium': 0.4,
        'hard': 0.5}},
        'essay': {'name': '作文题', 'score_per': 50, 'difficulty_weights': {'easy': 0.1, 'medium': 0.6, 'hard': 0.3}}
    }
    
    def __init__(self):
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        cursor.execute(''' CREATE TABLE IF NOT EXISTS generated_papers ( id INTEGER PRIMARY KEY AUTOINCREMENT, paper_id TEXT UNIQUE NOT NULL, title TEXT NOT NULL, subject TEXT NOT NULL, total_score INTEGER DEFAULT 100, duration INTEGER DEFAULT 120, question_count INTEGER DEFAULT 0, difficulty_distribution TEXT, topic_distribution TEXT, content TEXT, created_by TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, used_count INTEGER DEFAULT 0 ) ''')
        
        cursor.execute(''' CREATE TABLE IF NOT EXISTS paper_questions ( id INTEGER PRIMARY KEY AUTOINCREMENT, paper_id TEXT NOT NULL, question_id TEXT NOT NULL, question_type TEXT NOT NULL, topic TEXT, difficulty TEXT, score INTEGER DEFAULT 0, content TEXT, options TEXT, answer TEXT, explanation TEXT, question_order INTEGER DEFAULT 0 ) ''')
        
        conn.commit()
        conn.close()
    
    def generate_paper(self, title: str, subject: str, total_score: int = 100, 
                       duration: int = 120, difficulty: str = 'balanced',
                       topics: List = None, question_types: List = None) -> Dict:
        """生成试卷"""
        paper_id = hashlib.md5(f"{title}{subject}{datetime.now()}".encode()).hexdigest()[:16]
        
        if topics is None:
            topics = self.SUBJECT_TOPICS.get(subject, [])
        
        if question_types is None:
            question_types = ['choice', 'fill', 'short', 'calculation']
            if subject == '语文':
                question_types.append('essay')
        
        questions = []
        difficulty_dist = {'easy': 0, 'medium': 0, 'hard': 0}
        topic_dist = {t: 0 for t in topics}
        
        remaining_score = total_score
        question_order = 0
        
        for q_type in question_types:
            q_config = self.QUESTION_TYPES.get(q_type)
            if not q_config:
                continue
            
            if q_type == 'essay' and subject == '语文':
                essay_score = min(remaining_score, q_config['score_per'])
                question = self._generate_question(subject, q_type, 'medium', essay_score)
                question['order'] = question_order
                questions.append(question)
                difficulty_dist['medium'] += 1
                topic_dist['作文'] = topic_dist.get('作文', 0) + 1
                remaining_score -= essay_score
                question_order += 1
                continue
            
            weights = q_config['difficulty_weights']
            q_count = self._calculate_question_count(q_type, remaining_score)
            
            for i in range(q_count):
                if remaining_score <= 0:
                    break
                
                diff = self._select_difficulty(weights)
                score = q_config['score_per']
                
                if remaining_score < score:
                    break
                
                topic = random.choice(topics)
                question = self._generate_question(subject, q_type, diff, score)
                question['order'] = question_order
                questions.append(question)
                
                difficulty_dist[diff] += 1
                topic_dist[topic] += 1
                remaining_score -= score
                question_order += 1
        
        if remaining_score > 0:
            last_q = questions[-1] if questions else None
            if last_q:
                last_q['score'] += remaining_score
        
        total_questions = len(questions)
        
        content = self._format_paper(title, subject, total_score, duration, questions)
        
        self._save_paper(paper_id, title, subject, total_score, duration, total_questions,
                         difficulty_dist, topic_dist, content)
        self._save_paper_questions(paper_id, questions)
        
        return {
            'success': True,
            'paper_id': paper_id,
            'title': title,
            'subject': subject,
            'total_score': total_score,
            'duration': duration,
            'question_count': total_questions,
            'difficulty_distribution': difficulty_dist,
            'topic_distribution': topic_dist,
            'questions': questions,
            'created_at': datetime.now().isoformat()
        }
    
    def _calculate_question_count(self, q_type: str, remaining_score: int) -> int:
        """计算题目数量"""
        score_per = self.QUESTION_TYPES[q_type]['score_per']
        return max(1, min(10, remaining_score // score_per))
    
    def _select_difficulty(self, weights: Dict) -> str:
        """根据权重选择难度"""
        rand = random.random()
        cumulative = 0
        
        for diff, weight in weights.items():
            cumulative += weight
            if rand <= cumulative:
                return diff
        
        return 'medium'
    
    def _generate_question(self, subject: str, q_type: str, difficulty: str, score: int) -> Dict:
        """生成单道题目"""
        question_id = hashlib.md5(f"{subject}{q_type}{difficulty}{datetime.now()}".encode()).hexdigest()[:16]
        
        templates = {
            'choice': [
                '下列关于{topic}的说法，正确的是：',
                '{topic}中，下列结论成立的是：',
                '已知条件，下列选项正确的是：',
                '{topic}相关的计算结果是：'
            ],
            'fill': [
                '{topic}中，若条件，则结果为______。',
                '已知条件，填空：______。',
                '{topic}的基本公式是______。',
                '计算结果为______。'
            ],
            'short': [
                '简述{topic}的基本概念和特点。',
                '说明{topic}在实际应用中的意义。',
                '分析{topic}的主要原理。',
                '解释{topic}相关现象的原因。'
            ],
            'calculation': [
                '已知条件，计算{topic}相关问题。',
                '求解{topic}中的具体问题。',
                '证明{topic}相关的定理。',
                '应用{topic}知识解决实际问题。'
            ],
            'essay': [
                '以"成长"为题，写一篇不少于600字的作文。',
                '围绕"学习的意义"，写一篇议论文。',
                '写一篇关于"生活中的感动"的记叙文。',
                '以"梦想与现实"为题，写一篇作文。'
            ]
        }
        
        topics = self.SUBJECT_TOPICS.get(subject, [])
        topic = random.choice(topics) if topics else '综合'
        
        template = random.choice(templates.get(q_type, ['请回答下列问题：']))
        question_text = template.format(topic=topic)
        
        options = []
        answer = ''
        explanation = ''
        
        if q_type == 'choice':
            options = [
                {'text': 'A. 选项A', 'is_correct': False},
                {'text': 'B. 选项B', 'is_correct': False},
                {'text': 'C. 选项C', 'is_correct': False},
                {'text': 'D. 选项D', 'is_correct': False}
            ]
            correct_idx = random.randint(0, 3)
            options[correct_idx]['is_correct'] = True
            answer = options[correct_idx]['text'][:2]
            explanation = '本题考查{topic}的基本概念，正确答案为{answer}。'.format(topic=topic, answer=answer)
        
        elif q_type == 'fill':
            answer = '参考答案'
            explanation = '本题考查{topic}的相关知识。'.format(topic=topic)
        
        elif q_type == 'short':
            answer = '本题答案要点：1. ... 2. ... 3. ...'
            explanation = '本题考查{topic}的理解和应用能力。'.format(topic=topic)
        
        elif q_type == 'calculation':
            answer = '计算过程：...\n最终答案：...'
            explanation = '本题考查{topic}的计算能力和应用能力。'.format(topic=topic)
        
        elif q_type == 'essay':
            answer = '评分标准：一类文（45-50分）...'
            explanation = '本题考查学生的写作能力和语言表达能力。'
        
        return {
            'question_id': question_id,
            'question_type': q_type,
            'question_type_name': self.QUESTION_TYPES[q_type]['name'],
            'topic': topic,
            'difficulty': difficulty,
            'score': score,
            'content': question_text,
            'options': options,
            'answer': answer,
            'explanation': explanation
        }
    
    def _format_paper(self, title: str, subject: str, total_score: int, duration: int, questions: List) -> str:
        """格式化试卷内容"""
        lines = []
        lines.append(f"# {title}")
        lines.append(f"**科目**: {subject}")
        lines.append(f"**总分**: {total_score}分")
        lines.append(f"**时间**: {duration}分钟")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        type_groups = {}
        for q in questions:
            q_type = q['question_type_name']
            if q_type not in type_groups:
                type_groups[q_type] = []
            type_groups[q_type].append(q)
        
        for q_type_name, q_list in type_groups.items():
            lines.append(f"## {q_type_name}")
            type_score = sum(q['score'] for q in q_list)
            lines.append(f"（共{len(q_list)}题，每题{q_list[0]['score']}分，共{type_score}分）")
            lines.append("")
            
            for q in q_list:
                lines.append(f"{q['order'] + 1}. {q['content']}（{q['score']}分）")
                if q['options']:
                    for opt in q['options']:
                        lines.append(f"   {opt['text']}")
                lines.append("")
        
        return '\n'.join(lines)
    
    def _save_paper(self, paper_id, title, subject, total_score, duration, question_count,
                    difficulty_dist, topic_dist, content):
        """保存试卷"""
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        cursor.execute(''' INSERT INTO generated_papers (paper_id, title, subject, total_score, duration, question_count, difficulty_distribution, topic_distribution, content) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (paper_id, title, subject, total_score, duration, question_count,
              json.dumps(difficulty_dist), json.dumps(topic_dist), content))
        
        conn.commit()
        conn.close()
    
    def _save_paper_questions(self, paper_id, questions):
        """保存试卷题目"""
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        for q in questions:
            cursor.execute(''' INSERT INTO paper_questions (paper_id, question_id, question_type, topic, difficulty, score, content, options, answer, explanation, question_order) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (paper_id, q['question_id'], q['question_type'], q['topic'], q['difficulty'],
                  q['score'], q['content'], json.dumps(q['options']), q['answer'],
                  q['explanation'], q['order']))
        
        conn.commit()
        conn.close()
    
    def get_paper(self, paper_id: str) -> Optional[Dict]:
        """获取试卷"""
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM generated_papers WHERE paper_id = ?', (paper_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        cursor.execute(''' SELECT * FROM paper_questions WHERE paper_id = ? ORDER BY question_order ''', (paper_id,))
        q_rows = cursor.fetchall()
        
        conn.close()
        
        questions = []
        for q_row in q_rows:
            questions.append({
                'question_id': q_row[2],
                'question_type': q_row[3],
                'question_type_name': self.QUESTION_TYPES.get(q_row[3], {}).get('name', q_row[3]),
                'topic': q_row[4],
                'difficulty': q_row[5],
                'score': q_row[6],
                'content': q_row[7],
                'options': json.loads(q_row[8]) if q_row[8] else [],
                'answer': q_row[9],
                'explanation': q_row[10],
                'order': q_row[11]
            })
        
        return {
            'paper_id': row[1],
            'title': row[2],
            'subject': row[3],
            'total_score': row[4],
            'duration': row[5],
            'question_count': row[6],
            'difficulty_distribution': json.loads(row[7]) if row[7] else {},
            'topic_distribution': json.loads(row[8]) if row[8] else {},
            'content': row[9],
            'created_by': row[10],
            'created_at': row[11],
            'used_count': row[12],
            'questions': questions
        }
    
    def list_papers(self, subject: str = None, limit: int = 10) -> List:
        """列出试卷"""
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        query = 'SELECT paper_id, title, subject, total_score, duration, question_count, created_at, used_count FROM generated_papers'
        params = []
        
        if subject:
            query += ' WHERE subject = ?'
            params.append(subject)
        
        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'paper_id': row[0],
            'title': row[1],
            'subject': row[2],
            'total_score': row[3],
            'duration': row[4],
            'question_count': row[5],
            'created_at': row[6],
            'used_count': row[7]
        } for row in rows]

ai_paper_generator = AIPaperGenerator()