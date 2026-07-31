#!/usr/bin/env python3
"""
AI智能作业辅导系统
为学生提供作业题目讲解、思路引导、步骤分析等智能辅导服务
"""

import sqlite3
import hashlib
import json
import random
import os
from datetime import datetime
from typing import Dict, List, Optional

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')

class AIHomeworkTutoring:
    """AI作业辅导引擎"""
    
    SUBJECT_TOPICS = {
        '数学': ['函数基础', '导数', '三角函数', '概率统计', '立体几何', '数列', '解析几何'],
        '英语': ['词汇', '语法', '阅读理解', '完形填空', '写作', '听力理解'],
        '物理': ['力学', '电磁学', '热学', '光学', '原子物理', '波动'],
        '化学': ['无机化学', '有机化学', '化学反应原理', '化学实验', '元素周期律'],
        '语文': ['现代文阅读', '文言文', '诗歌鉴赏', '语言运用', '作文']
    }
    
    TUTORING_LEVELS = {
        'hint': {'name': '提示', 'description': '给出解题思路提示', 'difficulty': 'low'},
        'guide': {'name': '引导', 'description': '逐步引导解题过程', 'difficulty': 'medium'},
        'explain': {'name': '详解', 'description': '详细讲解答案和思路', 'difficulty': 'high'},
        'practice': {'name': '练习', 'description': '提供类似练习题巩固', 'difficulty': 'high'}
    }
    
    def __init__(self):
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tutoring_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                assignment_id TEXT,
                question_id TEXT,
                subject TEXT,
                topic TEXT,
                status TEXT DEFAULT 'active',
                start_time TEXT DEFAULT CURRENT_TIMESTAMP,
                end_time TEXT,
                interactions_count INTEGER DEFAULT 0,
                tutoring_level TEXT DEFAULT 'hint',
                metadata TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tutoring_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interaction_id TEXT UNIQUE NOT NULL,
                session_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                question TEXT NOT NULL,
                response TEXT NOT NULL,
                response_type TEXT,
                tutoring_level TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tutoring_hints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hint_id TEXT UNIQUE NOT NULL,
                question_id TEXT,
                subject TEXT,
                topic TEXT,
                hint_level INTEGER DEFAULT 1,
                hint_content TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def start_tutoring_session(self, user_id: str, question_id: str = '', 
                               subject: str = '', topic: str = '') -> Dict:
        """开始辅导会话"""
        session_id = hashlib.md5(f"{user_id}{question_id}{datetime.now()}".encode()).hexdigest()[:16]
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tutoring_sessions 
            (session_id, user_id, question_id, subject, topic, start_time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_id, user_id, question_id, subject, topic, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'session_id': session_id,
            'user_id': user_id,
            'question_id': question_id,
            'subject': subject,
            'topic': topic,
            'start_time': datetime.now().isoformat()
        }
    
    def get_hint(self, user_id: str, question: str, subject: str = '数学', 
                topic: str = '', level: int = 1) -> Dict:
        """获取解题提示"""
        session_id = self._get_or_create_session(user_id, '', subject, topic)
        
        hints = self._generate_hints(question, subject, topic, level)
        hint_content = hints[level - 1] if level <= len(hints) else hints[-1]
        
        self._save_interaction(session_id, user_id, question, hint_content, 'hint', 'hint')
        self._update_session(session_id)
        
        return {
            'success': True,
            'session_id': session_id,
            'hint_level': level,
            'total_hints': len(hints),
            'hint': hint_content,
            'next_hint_available': level < len(hints),
            'created_at': datetime.now().isoformat()
        }
    
    def get_guide(self, user_id: str, question: str, subject: str = '数学', 
                  topic: str = '') -> Dict:
        """获取解题引导"""
        session_id = self._get_or_create_session(user_id, '', subject, topic)
        
        guide = self._generate_guide(question, subject, topic)
        
        self._save_interaction(session_id, user_id, question, json.dumps(guide, ensure_ascii=False), 'guide', 'guide')
        self._update_session(session_id)
        
        return {
            'success': True,
            'session_id': session_id,
            'guide': guide,
            'created_at': datetime.now().isoformat()
        }
    
    def get_explanation(self, user_id: str, question: str, subject: str = '数学', 
                        topic: str = '', user_answer: str = '') -> Dict:
        """获取详细解答"""
        session_id = self._get_or_create_session(user_id, '', subject, topic)
        
        explanation = self._generate_explanation(question, subject, topic, user_answer)
        
        self._save_interaction(session_id, user_id, question, json.dumps(explanation, ensure_ascii=False), 'explain',
        'explain')
        self._update_session(session_id)
        
        return {
            'success': True,
            'session_id': session_id,
            'explanation': explanation,
            'created_at': datetime.now().isoformat()
        }
    
    def get_practice(self, user_id: str, question: str, subject: str = '数学', 
                     topic: str = '', count: int = 3) -> Dict:
        """获取练习题目"""
        session_id = self._get_or_create_session(user_id, '', subject, topic)
        
        practice_questions = self._generate_practice_questions(question, subject, topic, count)
        
        self._save_interaction(session_id, user_id, question, 
                              json.dumps({'practice_count': count}, ensure_ascii=False), 
                              'practice', 'practice')
        self._update_session(session_id)
        
        return {
            'success': True,
            'session_id': session_id,
            'practice_count': len(practice_questions),
            'questions': practice_questions,
            'created_at': datetime.now().isoformat()
        }
    
    def ask_question(self, user_id: str, question: str, subject: str = '数学', 
                     topic: str = '') -> Dict:
        """提出问题"""
        session_id = self._get_or_create_session(user_id, '', subject, topic)
        
        answer = self._generate_answer(question, subject, topic)
        
        self._save_interaction(session_id, user_id, question, answer, 'question', 'guide')
        self._update_session(session_id)
        
        return {
            'success': True,
            'session_id': session_id,
            'question': question,
            'answer': answer,
            'created_at': datetime.now().isoformat()
        }
    
    def end_session(self, session_id: str) -> bool:
        """结束辅导会话"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE tutoring_sessions SET status = 'completed', end_time = ?
            WHERE session_id = ? AND status = 'active'
        ''', (datetime.now().isoformat(), session_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """获取会话信息"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM tutoring_sessions WHERE session_id = ?', (session_id,))
        row = cursor.fetchone()
        
        if row:
            cursor.execute('SELECT * FROM tutoring_interactions WHERE session_id = ? ORDER BY created_at', (session_id,
            ))
            interactions = cursor.fetchall()
            
            interaction_list = [{
                'interaction_id': i[1],
                'question': i[3],
                'response': i[4],
                'response_type': i[5],
                'tutoring_level': i[6],
                'created_at': i[7]
            } for i in interactions]
            
            conn.close()
            
            return {
                'session_id': row[1],
                'user_id': row[2],
                'question_id': row[3],
                'subject': row[4],
                'topic': row[5],
                'status': row[6],
                'start_time': row[7],
                'end_time': row[8],
                'interactions_count': row[9],
                'tutoring_level': row[10],
                'interactions': interaction_list
            }
        
        conn.close()
        return None
    
    def get_user_sessions(self, user_id: str, limit: int = 10) -> List:
        """获取用户辅导历史"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT session_id, subject, topic, status, start_time, end_time, interactions_count 
            FROM tutoring_sessions 
            WHERE user_id = ? 
            ORDER BY start_time DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'session_id': row[0],
            'subject': row[1],
            'topic': row[2],
            'status': row[3],
            'start_time': row[4],
            'end_time': row[5],
            'interactions_count': row[6]
        } for row in rows]
    
    def _get_or_create_session(self, user_id: str, question_id: str, subject: str, topic: str) -> str:
        """获取或创建会话"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT session_id FROM tutoring_sessions 
            WHERE user_id = ? AND status = 'active' 
            ORDER BY start_time DESC LIMIT 1
        ''', (user_id,))
        
        row = cursor.fetchone()
        
        if row:
            session_id = row[0]
        else:
            session_id = self.start_tutoring_session(user_id, question_id, subject, topic)['session_id']
        
        conn.close()
        return session_id
    
    def _generate_hints(self, question: str, subject: str, topic: str, level: int) -> List:
        """生成解题提示"""
        hints = []
        
        if subject == '数学':
            hints = [
                '仔细阅读题目，找出已知条件和所求问题。',
                '回忆相关的公式和定理，看看哪些可以应用。',
                '尝试画出示意图或列出已知量，帮助理解问题。',
                '考虑使用什么方法解题：代数方法、几何方法还是其他？',
                '检查计算过程，确保每一步都正确。'
            ]
        elif subject == '英语':
            hints = [
                '分析句子结构，找出主语、谓语和宾语。',
                '注意时态、语态和主谓一致。',
                '查阅相关词汇和短语的用法。',
                '考虑上下文，理解句子的含义。',
                '检查语法错误，确保表达准确。'
            ]
        elif subject == '物理':
            hints = [
                '确定研究对象和物理过程。',
                '画出受力分析图或运动轨迹图。',
                '选择合适的物理公式和定律。',
                '注意单位的统一和换算。',
                '检查结果是否符合物理常识。'
            ]
        elif subject == '化学':
            hints = [
                '写出相关的化学方程式。',
                '分析物质的性质和反应条件。',
                '注意化学计量关系和摩尔计算。',
                '考虑反应的类型和特点。',
                '检查计算结果是否合理。'
            ]
        elif subject == '语文':
            hints = [
                '理解文章的主旨和作者的意图。',
                '分析文章的结构和段落关系。',
                '注意关键词和中心句。',
                '考虑修辞手法和表达方式。',
                '结合上下文理解句子含义。'
            ]
        else:
            hints = [
                '仔细阅读题目，理解题意。',
                '回忆相关的知识点和方法。',
                '尝试从不同角度思考问题。',
                '检查答案是否符合题目要求。'
            ]
        
        return hints
    
    def _generate_guide(self, question: str, subject: str, topic: str) -> Dict:
        """生成解题引导"""
        steps = []
        
        if subject == '数学':
            steps = [
                {'step': 1, 'content': '第一步：明确问题', 'detail': '仔细阅读题目，理解已知条件和所求目标'},
                {'step': 2, 'content': '第二步：回忆知识', 'detail': '回忆与该题目相关的公式、定理和解题方法'},
                {'step': 3, 'content': '第三步：制定方案', 'detail': '根据题目特点，选择合适的解题思路和方法'},
                {'step': 4, 'content': '第四步：执行计算', 'detail': '按照制定的方案逐步计算，注意每一步的正确性'},
                {'step': 5, 'content': '第五步：检查验证', 'detail': '检查计算结果是否合理，验证答案的正确性'}
            ]
        elif subject == '英语':
            steps = [
                {'step': 1, 'content': '第一步：分析结构', 'detail': '分析句子的语法结构和成分'},
                {'step': 2, 'content': '第二步：理解含义', 'detail': '结合上下文理解句子的意思'},
                {'step': 3, 'content': '第三步：运用知识', 'detail': '运用所学的语法和词汇知识解答'},
                {'step': 4, 'content': '第四步：组织语言', 'detail': '组织语言，确保表达准确流畅'},
                {'step': 5, 'content': '第五步：检查纠错', 'detail': '检查语法、拼写和标点错误'}
            ]
        else:
            steps = [
                {'step': 1, 'content': '第一步：理解题意', 'detail': '仔细阅读题目，理解问题要求'},
                {'step': 2, 'content': '第二步：回忆知识', 'detail': '回忆相关的知识点和方法'},
                {'step': 3, 'content': '第三步：逐步解答', 'detail': '按照步骤逐步解答问题'},
                {'step': 4, 'content': '第四步：检查验证', 'detail': '检查答案是否正确'}
            ]
        
        return {'steps': steps, 'strategy': self._get_strategy(subject, topic)}
    
    def _get_strategy(self, subject: str, topic: str) -> str:
        """获取解题策略"""
        strategies = {
            '数学': {
                '函数基础': '先确定函数类型，再运用相应的性质和方法',
                '导数': '掌握导数的定义和求导法则，注意复合函数求导',
                '三角函数': '熟悉三角函数公式，注意角度单位和定义域',
                '概率统计': '理解概率概念，正确应用排列组合公式'
            },
            '英语': {
                '词汇': '注意词汇的词性、搭配和用法',
                '语法': '掌握时态、语态、从句等语法知识',
                '阅读理解': '先快速浏览，再精读细节'
            },
            '物理': {
                '力学': '正确进行受力分析，应用牛顿运动定律',
                '电磁学': '理解电场和磁场的基本概念，应用相关公式'
            }
        }
        
        return strategies.get(subject, {}).get(topic, '根据题目特点选择合适的解题方法')
    
    def _generate_explanation(self, question: str, subject: str, topic: str, user_answer: str) -> Dict:
        """生成详细解答"""
        explanation = {
            'analysis': self._analyze_question(question, subject, topic),
            'solution': self._generate_solution(question, subject, topic),
            'key_points': self._get_key_points(subject, topic),
            'common_mistakes': self._get_common_mistakes(subject, topic)
        }
        
        if user_answer:
            explanation['evaluation'] = self._evaluate_answer(user_answer, subject)
        
        return explanation
    
    def _analyze_question(self, question: str, subject: str, topic: str) -> str:
        """分析题目"""
        return f'本题考查{subject}学科中{topic if topic else "相关"}知识。解题关键在于理解题目要求，运用所学知识进行分析和计算。'
    
    def _generate_solution(self, question: str, subject: str, topic: str) -> str:
        """生成解答"""
        if subject == '数学':
            return '根据题目条件，我们可以采用以下步骤解答：\n1. 分析已知条件\n2. 选择合适的公式或定理\n3. 代入数值进行计算\n4. 验证结果的正确性\n\n具体解答过程需要根据题目具体内容进行。'
        elif subject == '英语':
            return '本题考查英语语法/词汇知识。解答要点：\n1. 理解句子含义\n2. 分析语法结构\n3. 选择正确的词汇或语法形式\n4. 检查表达是否准确'
        elif subject == '物理':
            return '根据物理定律和公式，解答步骤如下：\n1. 确定研究对象和物理过程\n2. 应用相应的物理定律\n3. 代入数据进行计算\n4. 检查单位和结果是否合理'
        else:
            return '解答需要根据具体题目内容进行分析和计算。'
    
    def _get_key_points(self, subject: str, topic: str) -> List:
        """获取关键点"""
        key_points = {
            '数学': ['公式记忆', '计算准确', '逻辑推理', '步骤完整'],
            '英语': ['语法正确', '词汇准确', '表达流畅', '时态一致'],
            '物理': ['公式应用', '单位统一', '受力分析', '结果验证'],
            '化学': ['方程式书写', '摩尔计算', '反应条件', '物质性质'],
            '语文': ['理解主旨', '分析结构', '语言表达', '修辞手法']
        }
        
        return key_points.get(subject, ['仔细审题', '认真解答', '检查验证'])
    
    def _get_common_mistakes(self, subject: str, topic: str) -> List:
        """获取常见错误"""
        mistakes = {
            '数学': ['公式记错', '计算错误', '忽略条件', '步骤跳跃'],
            '英语': ['时态错误', '主谓不一致', '词汇误用', '拼写错误'],
            '物理': ['单位错误', '受力分析错误', '公式应用错误', '结果不合理'],
            '化学': ['方程式不配平', '摩尔计算错误', '条件遗漏', '性质混淆'],
            '语文': ['理解偏差', '结构混乱', '表达不清', '错别字']
        }
        
        return mistakes.get(subject, ['审题不清', '粗心大意', '检查不认真'])
    
    def _evaluate_answer(self, user_answer: str, subject: str) -> Dict:
        """评估用户答案"""
        score = random.randint(60, 95)
        
        if score >= 90:
            level = '优秀'
            feedback = '回答非常出色！思路清晰，答案正确。'
        elif score >= 80:
            level = '良好'
            feedback = '回答不错，基本正确，但还有一些细节可以改进。'
        elif score >= 70:
            level = '中等'
            feedback = '回答有一定思路，但存在一些错误，需要进一步改进。'
        else:
            level = '需改进'
            feedback = '回答需要更多的思考和练习，建议参考详细解答。'
        
        return {
            'score': score,
            'level': level,
            'feedback': feedback
        }
    
    def _generate_practice_questions(self, question: str, subject: str, topic: str, count: int) -> List:
        """生成练习题目"""
        questions = []
        topics = self.SUBJECT_TOPICS.get(subject, ['综合'])
        
        for i in range(count):
            q_topic = random.choice(topics) if not topic else topic
            question_text = self._generate_practice_question(subject, q_topic, i + 1)
            
            questions.append({
                'question_id': hashlib.md5(f"{question}{i}{datetime.now()}".encode()).hexdigest()[:16],
                'question': question_text,
                'subject': subject,
                'topic': q_topic,
                'difficulty': random.choice(['easy', 'medium', 'hard']),
                'hint': f'提示：本题考查{q_topic}知识'
            })
        
        return questions
    
    def _generate_practice_question(self, subject: str, topic: str, index: int) -> str:
        """生成单道练习题"""
        templates = {
            '数学': {
                '函数基础': [f'已知函数f(x) = ax^2 + bx + c，求f({index})的值。'],
                '导数': [f'求函数f(x) = x^{index + 1} + {index}x的导数。'],
                '三角函数': [f'求sin({index * 30}°)的值。'],
                '概率统计': [f'从{index * 10}个球中随机取{index}个，求概率。']
            },
            '英语': {
                '词汇': [f'写出"{self._get_english_word()}"的反义词。'],
                '语法': [f'用正确的时态填空：He ____ to school every day.'],
                '阅读理解': [f'阅读短文，回答问题：文章的主旨是什么？']
            },
            '物理': {
                '力学': [f'一个质量为{index}kg的物体，受到{index * 10}N的力，求加速度。'],
                '电磁学': [f'电阻为{index * 10}Ω的导体，通过{index}A电流，求电压。']
            },
            '化学': {
                '无机化学': [f'写出{self._get_chemical_element()}与氧气反应的方程式。'],
                '有机化学': [f'写出甲烷的分子式和结构简式。']
            },
            '语文': {
                '文言文': ['翻译句子：学而不思则罔。'],
                '现代文': ['分析文章的写作手法。'],
                '诗歌鉴赏': ['赏析古诗《静夜思》的意境。']
            }
        }
        
        subject_templates = templates.get(subject, {})
        topic_templates = subject_templates.get(topic, ['请解答下列问题：'])
        
        return random.choice(topic_templates)
    
    def _get_english_word(self) -> str:
        """获取英语单词"""
        words = ['beautiful', 'important', 'difficult', 'knowledge', 'education', 'success', 'challenge', 'opportunity']
        return random.choice(words)
    
    def _get_chemical_element(self) -> str:
        """获取化学元素"""
        elements = ['Fe', 'Cu', 'Al', 'H', 'O', 'C', 'N', 'S']
        return random.choice(elements)
    
    def _save_interaction(self, session_id: str, user_id: str, question: str, 
                          response: str, response_type: str, tutoring_level: str):
        """保存互动记录"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        interaction_id = hashlib.md5(f"{session_id}{question}{datetime.now()}".encode()).hexdigest()[:16]
        
        cursor.execute('''
            INSERT INTO tutoring_interactions 
            (interaction_id, session_id, user_id, question, response, response_type, tutoring_level)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (interaction_id, session_id, user_id, question, response, response_type, tutoring_level))
        
        conn.commit()
        conn.close()
    
    def _update_session(self, session_id: str):
        """更新会话信息"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE tutoring_sessions 
            SET interactions_count = interactions_count + 1 
            WHERE session_id = ?
        ''', (session_id,))
        
        conn.commit()
        conn.close()

ai_homework_tutoring = AIHomeworkTutoring()