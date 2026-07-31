#!/usr/bin/env python3
"""
AI智能答疑系统
基于知识库和学习资料，为学生提供智能问答服务
"""

import sqlite3
import json
import hashlib
from datetime import datetime, timedelta

class AIIntelligentQNA:
    KNOWLEDGE_BASE = {
        '数学': {
            '函数': {
                '定义': '函数是一种对应关系，将一个集合中的每个元素映射到另一个集合中的唯一元素',
                '定义域': '函数中自变量x的取值范围称为定义域',
                '值域': '函数中因变量y的取值范围称为值域',
                '单调性': '如果对于定义域内的任意x1<x2，都有f(x1)<f(x2)，则函数单调递增',
                '奇偶性': '如果f(-x)=f(x)，则函数为偶函数；如果f(-x)=-f(x)，则函数为奇函数'
            },
            '导数': {
                '定义': '导数表示函数在某点处的变化率，f\'(x) = lim(Δx→0) [f(x+Δx)-f(x)]/Δx',
                '求导公式': '常见求导公式：(x^n)\' = nx^(n-1)，(sin x)\' = cos x，(cos x)\' = -sin x',
                '应用': '导数可用于求函数的极值、单调性、切线方程等'
            },
            '概率': {
                '定义': '概率是事件发生可能性的度量，取值范围为[0, 1]',
                '加法公式': 'P(A∪B) = P(A) + P(B) - P(A∩B)',
                '乘法公式': 'P(A∩B) = P(A) × P(B|A)'
            }
        },
        '英语': {
            '语法': {
                '时态': '英语时态包括一般现在时、一般过去时、一般将来时、现在进行时等',
                '语态': '语态分为主动语态和被动语态，被动语态结构为be+过去分词',
                '从句': '从句包括名词性从句、定语从句、状语从句等'
            },
            '词汇': {
                '词根词缀': '通过词根词缀可以推测单词含义，如un-表示否定，-tion表示名词',
                '近义词辨析': '注意区分近义词的细微差别，如affect和effect'
            }
        },
        '物理': {
            '力学': {
                '牛顿定律': '牛顿第一定律：物体静止或匀速直线运动；第二定律：F=ma；第三定律：作用力等于反作用力',
                '能量守恒': '能量既不会创生也不会消失，只会从一种形式转化为另一种形式'
            },
            '电磁学': {
                '欧姆定律': 'I = U/R，电流等于电压除以电阻',
                '电路分析': '串联电路电流相等，并联电路电压相等'
            }
        }
    }
    
    def __init__(self):
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect('ai_qna.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qna_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL UNIQUE,
                user_id TEXT NOT NULL,
                subject TEXT,
                messages TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qna_faq (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                subject TEXT,
                views INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qna_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                question TEXT,
                answer TEXT,
                subject TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self._init_faq(cursor)
        
        conn.commit()
        conn.close()
    
    def _init_faq(self, cursor):
        """初始化FAQ数据"""
        cursor.execute('SELECT COUNT(*) FROM qna_faq')
        if cursor.fetchone()[0] == 0:
            faq_items = [
                ('什么是函数？', '函数是一种对应关系，将一个集合中的每个元素映射到另一个集合中的唯一元素', '数学'),
                ('导数怎么求？', '导数表示函数在某点处的变化率，可以使用求导公式或极限定义来计算', '数学'),
                ('英语时态有哪些？', '英语时态包括一般现在时、一般过去时、一般将来时、现在进行时、现在完成时等', '英语'),
                ('牛顿第二定律是什么？', '牛顿第二定律：F=ma，力等于质量乘以加速度', '物理'),
                ('欧姆定律是什么？', '欧姆定律：I = U/R，电流等于电压除以电阻', '物理'),
                ('什么是概率？', '概率是事件发生可能性的度量，取值范围为[0, 1]', '数学'),
                ('被动语态怎么构成？', '被动语态结构为be+过去分词，如：The book was written by him', '英语')
            ]
            
            for question, answer, subject in faq_items:
                cursor.execute('''
                    INSERT INTO qna_faq (question, answer, subject)
                    VALUES (?, ?, ?)
                ''', (question, answer, subject))
    
    def _match_knowledge(self, question, subject):
        """匹配知识库"""
        knowledge = self.KNOWLEDGE_BASE.get(subject, {})
        
        for topic, items in knowledge.items():
            for key, value in items.items():
                if key in question or topic in question:
                    return value
        
        return None
    
    def _search_faq(self, question, subject):
        """搜索FAQ"""
        conn = sqlite3.connect('ai_qna.db')
        cursor = conn.cursor()
        
        query = 'SELECT answer FROM qna_faq WHERE question LIKE ?'
        params = [f'%{question}%']
        
        if subject:
            query += ' AND subject = ?'
            params.append(subject)
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return result[0]
        return None
    
    def _generate_answer(self, question, subject):
        """生成答案"""
        faq_answer = self._search_faq(question, subject)
        if faq_answer:
            return faq_answer
        
        knowledge_answer = self._match_knowledge(question, subject)
        if knowledge_answer:
            return knowledge_answer
        
        default_answers = {
            '数学': '这是一个数学问题。建议你回顾相关知识点，或者尝试使用不同的方法来解决这个问题。如果遇到困难，可以参考教材中的例题或向老师请教。',
            '英语': '这是一个英语问题。建议你多阅读、多练习，积累词汇和语法知识。可以尝试通过上下文来理解词义，或者使用词典查询。',
            '物理': '这是一个物理问题。建议你分析问题中的物理过程，应用相关公式和定律。注意单位的统一和计算的准确性。',
            '化学': '这是一个化学问题。建议你回顾元素周期表、化学反应方程式等基础知识。注意物质的性质和反应条件。',
            '语文': '这是一个语文问题。建议你多读经典作品，积累文学知识。注意理解文章的主旨和作者的意图。'
        }
        
        return default_answers.get(subject, '抱歉，我暂时无法回答这个问题。建议你查阅相关教材或咨询老师。')
    
    def ask_question(self, user_id, question, subject=None):
        """提问"""
        answer = self._generate_answer(question, subject)
        
        conn = sqlite3.connect('ai_qna.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO qna_history (user_id, question, answer, subject)
            VALUES (?, ?, ?, ?)
        ''', (str(user_id), question, answer, subject))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'user_id': user_id,
            'question': question,
            'subject': subject,
            'answer': answer,
            'created_at': datetime.now().isoformat()
        }
    
    def create_conversation(self, user_id, subject=None):
        """创建对话"""
        conversation_id = hashlib.md5(f"{user_id}{datetime.now()}".encode()).hexdigest()[:16]
        
        conn = sqlite3.connect('ai_qna.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO qna_conversations (conversation_id, user_id, subject, messages)
            VALUES (?, ?, ?, ?)
        ''', (conversation_id, str(user_id), subject, json.dumps([])))
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'conversation_id': conversation_id,
            'user_id': user_id,
            'subject': subject,
            'created_at': datetime.now().isoformat()
        }
    
    def send_message(self, conversation_id, user_id, message, subject=None):
        """发送消息"""
        conn = sqlite3.connect('ai_qna.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT messages FROM qna_conversations WHERE conversation_id = ?', (conversation_id,))
        record = cursor.fetchone()
        
        if not record:
            conn.close()
            return {'success': False, 'error': '对话不存在'}
        
        messages = json.loads(record[0]) if record[0] else []
        
        answer = self._generate_answer(message, subject)
        
        messages.append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat()
        })
        messages.append({
            'role': 'assistant',
            'content': answer,
            'timestamp': datetime.now().isoformat()
        })
        
        cursor.execute('''
            UPDATE qna_conversations 
            SET messages = ?, updated_at = ?, subject = ?
            WHERE conversation_id = ?
        ''', (json.dumps(messages), datetime.now().isoformat(), subject or '', conversation_id))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'conversation_id': conversation_id,
            'message': message,
            'answer': answer,
            'messages': messages
        }
    
    def get_conversation(self, conversation_id):
        """获取对话"""
        conn = sqlite3.connect('ai_qna.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM qna_conversations WHERE conversation_id = ?', (conversation_id,))
        record = cursor.fetchone()
        
        if record:
            conn.close()
            return {
                'success': True,
                'conversation_id': record[1],
                'user_id': record[2],
                'subject': record[3],
                'messages': json.loads(record[4]) if record[4] else [],
                'created_at': record[5],
                'updated_at': record[6]
            }
        
        conn.close()
        return {'success': False, 'error': '对话不存在'}
    
    def get_faq(self, subject=None):
        """获取FAQ"""
        conn = sqlite3.connect('ai_qna.db')
        cursor = conn.cursor()
        
        query = 'SELECT * FROM qna_faq'
        params = []
        
        if subject:
            query += ' WHERE subject = ?'
            params.append(subject)
        
        cursor.execute(query, params)
        records = cursor.fetchall()
        
        faq = []
        for r in records:
            faq.append({
                'id': r[0],
                'question': r[1],
                'answer': r[2],
                'subject': r[3],
                'views': r[4]
            })
        
        conn.close()
        return {'success': True, 'faq': faq}

ai_intelligent_qna = AIIntelligentQNA()