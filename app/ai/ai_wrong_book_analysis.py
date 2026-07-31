#!/usr/bin/env python3
"""
AI错题本智能分析系统
分析学生错题记录，识别知识薄弱点，提供针对性改进建议
"""

import sqlite3
import json
import hashlib
from datetime import datetime, timedelta

class AIWrongBookAnalyzer:
    def __init__(self):
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect('ai_wrong_book.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wrong_analysis_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id TEXT NOT NULL UNIQUE,
                user_id TEXT NOT NULL,
                subject TEXT,
                total_wrong INTEGER DEFAULT 0,
                analysis_result TEXT,
                improvement_suggestions TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wrong_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id TEXT NOT NULL UNIQUE,
                user_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                pattern_type TEXT,
                pattern_description TEXT,
                related_topics TEXT,
                frequency INTEGER DEFAULT 1,
                last_detected TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _get_user_wrong_questions(self, user_id, subject=None):
        """获取用户错题记录"""
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        query = 'SELECT * FROM wrong_questions WHERE user_id = ?'
        params = [str(user_id)]
        
        if subject:
            query += ' AND subject = ?'
            params.append(subject)
        
        cursor.execute(query, params)
        records = cursor.fetchall()
        
        wrong_questions = []
        for r in records:
            wrong_questions.append({
                'id': r[0],
                'question_content': r[1],
                'subject': r[2],
                'user_id': r[3],
                'wrong_count': r[4],
                'last_wrong_date': r[5],
                'created_at': r[6]
            })
        
        conn.close()
        return wrong_questions
    
    def _analyze_wrong_patterns(self, wrong_questions):
        """分析错题模式"""
        patterns = {}
        
        subject_patterns = {}
        for q in wrong_questions:
            subject = q['subject']
            if subject not in subject_patterns:
                subject_patterns[subject] = []
            subject_patterns[subject].append(q)
        
        for subject, questions in subject_patterns.items():
            topic_patterns = self._identify_topic_patterns(questions)
            error_type_patterns = self._identify_error_types(questions)
            
            patterns[subject] = {
                'topic_patterns': topic_patterns,
                'error_type_patterns': error_type_patterns,
                'total_wrong': len(questions),
                'high_frequency_count': sum(1 for q in questions if q['wrong_count'] >= 3)
            }
        
        return patterns
    
    def _identify_topic_patterns(self, questions):
        """识别知识点模式"""
        topic_keywords = {
            '数学': {
                '函数': ['函数', '导数', '极限', '定义域', '值域', '单调性'],
                '几何': ['几何', '三角形', '圆形', '面积', '体积', '坐标'],
                '代数': ['方程', '不等式', '数列', '因式', '整式'],
                '概率': ['概率', '统计', '分布', '期望', '方差']
            },
            '英语': {
                '词汇': ['词', '词汇', '单词'],
                '语法': ['语法', '时态', '语态', '从句', '介词'],
                '阅读': ['阅读', '理解', '文章'],
                '写作': ['写作', '作文', '句子']
            },
            '物理': {
                '力学': ['力', '运动', '加速度', '动量', '能量'],
                '电磁': ['电', '磁', '电路', '电流', '电压'],
                '光学': ['光', '折射', '反射'],
                '热学': ['热', '温度', '热量']
            },
            '化学': {
                '无机': ['元素', '化合物', '反应'],
                '有机': ['有机', '烃', '醇', '酸'],
                '计算': ['计算', '浓度', '摩尔']
            },
            '语文': {
                '文言': ['文言', '虚词', '实词', '翻译'],
                '现代': ['现代文', '阅读', '理解'],
                '写作': ['写作', '作文', '文章']
            }
        }
        
        patterns = {}
        for q in questions:
            content = q['question_content']
            subject = q['subject']
            
            keywords = topic_keywords.get(subject, {})
            matched_topic = None
            
            for topic, keys in keywords.items():
                for key in keys:
                    if key in content:
                        matched_topic = topic
                        break
                if matched_topic:
                    break
            
            if matched_topic:
                if matched_topic not in patterns:
                    patterns[matched_topic] = {'count': 0, 'questions': []}
                patterns[matched_topic]['count'] += 1
                patterns[matched_topic]['questions'].append(q)
        
        return patterns
    
    def _identify_error_types(self, questions):
        """识别错误类型"""
        error_types = {
            '概念理解错误': ['概念', '定义', '理解', '认识'],
            '计算错误': ['计算', '运算', '求解', '求值'],
            '审题错误': ['题目', '条件', '要求', '题意'],
            '方法选择错误': ['方法', '思路', '策略', '技巧'],
            '公式记错': ['公式', '定理', '定律', '法则'],
            '粗心错误': ['粗心', '大意', '疏忽']
        }
        
        types = {}
        for q in questions:
            content = q['question_content']
            
            for error_type, keywords in error_types.items():
                for keyword in keywords:
                    if keyword in content:
                        if error_type not in types:
                            types[error_type] = 0
                        types[error_type] += 1
                        break
        
        return types
    
    def _generate_improvement_suggestions(self, patterns):
        """生成改进建议"""
        suggestions = []
        
        for subject, data in patterns.items():
            if data['high_frequency_count'] >= 3:
                suggestions.append({
                    'priority': 'high',
                    'subject': subject,
                    'title': f'{subject}高频错题重点关注',
                    'content': f'你在{subject}科目中有{data["high_frequency_count"]}道题目多次做错，建议重点复习相关知识点',
                    'topics': [t for t in data['topic_patterns'].keys()]
                })
            
            for topic, topic_data in data['topic_patterns'].items():
                if topic_data['count'] >= 3:
                    suggestions.append({
                        'priority': 'medium',
                        'subject': subject,
                        'title': f'{topic}知识点需加强',
                        'content': f'{topic}相关题目做错{topic_data["count"]}次，建议针对性练习',
                        'topics': [topic]
                    })
            
            if data['error_type_patterns']:
                main_error_type = max(data['error_type_patterns'], key=data['error_type_patterns'].get)
                suggestions.append({
                    'priority': 'low',
                    'subject': subject,
                    'title': '减少错误类型',
                    'content': f'你的主要错误类型是"{main_error_type}"，建议在做题时注意避免',
                    'topics': []
                })
        
        return sorted(suggestions, key=lambda x: {'high': 0, 'medium': 1, 'low': 2}[x['priority']])
    
    def analyze_wrong_book(self, user_id, subject=None):
        """分析错题本"""
        wrong_questions = self._get_user_wrong_questions(user_id, subject)
        
        if not wrong_questions:
            return {
                'success': True,
                'user_id': user_id,
                'subject': subject or '全部',
                'message': '暂无错题记录',
                'total_wrong': 0,
                'patterns': {},
                'suggestions': []
            }
        
        patterns = self._analyze_wrong_patterns(wrong_questions)
        suggestions = self._generate_improvement_suggestions(patterns)
        
        analysis_id = hashlib.md5(f"{user_id}{subject}{datetime.now()}".encode()).hexdigest()[:16]
        
        conn = sqlite3.connect('ai_wrong_book.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO wrong_analysis_records 
            (analysis_id, user_id, subject, total_wrong, analysis_result, improvement_suggestions)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (analysis_id, str(user_id), subject or '全部', len(wrong_questions),
              json.dumps(patterns), json.dumps(suggestions)))
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'analysis_id': analysis_id,
            'user_id': user_id,
            'subject': subject or '全部',
            'total_wrong': len(wrong_questions),
            'patterns': patterns,
            'suggestions': suggestions,
            'created_at': datetime.now().isoformat()
        }
    
    def get_analysis_record(self, analysis_id):
        """获取分析记录"""
        conn = sqlite3.connect('ai_wrong_book.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM wrong_analysis_records WHERE analysis_id = ?', (analysis_id,))
        record = cursor.fetchone()
        
        if record:
            conn.close()
            return {
                'success': True,
                'analysis_id': record[1],
                'user_id': record[2],
                'subject': record[3],
                'total_wrong': record[4],
                'patterns': json.loads(record[5]) if record[5] else {},
                'suggestions': json.loads(record[6]) if record[6] else [],
                'created_at': record[7]
            }
        
        conn.close()
        return {'success': False, 'error': '分析记录不存在'}
    
    def get_user_analysis_history(self, user_id, limit=10):
        """获取用户分析历史"""
        conn = sqlite3.connect('ai_wrong_book.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM wrong_analysis_records 
            WHERE user_id = ? ORDER BY created_at DESC LIMIT ?
        ''', (str(user_id), limit))
        records = cursor.fetchall()
        
        history = []
        for r in records:
            history.append({
                'analysis_id': r[1],
                'subject': r[3],
                'total_wrong': r[4],
                'created_at': r[7]
            })
        
        conn.close()
        return {'success': True, 'history': history}
    
    def get_wrong_patterns(self, user_id, subject=None):
        """获取错题模式"""
        conn = sqlite3.connect('ai_wrong_book.db')
        cursor = conn.cursor()
        
        query = 'SELECT * FROM wrong_patterns WHERE user_id = ?'
        params = [str(user_id)]
        
        if subject:
            query += ' AND subject = ?'
            params.append(subject)
        
        cursor.execute(query, params)
        records = cursor.fetchall()
        
        patterns = []
        for r in records:
            patterns.append({
                'pattern_id': r[1],
                'subject': r[3],
                'pattern_type': r[4],
                'pattern_description': r[5],
                'related_topics': json.loads(r[6]) if r[6] else [],
                'frequency': r[7],
                'last_detected': r[8]
            })
        
        conn.close()
        return {'success': True, 'patterns': patterns}

ai_wrong_book_analyzer = AIWrongBookAnalyzer()