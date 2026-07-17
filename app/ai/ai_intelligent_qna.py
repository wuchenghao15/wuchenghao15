#!/usr/bin/env python3
import os
import json
import sqlite3
import threading
import hashlib
import random
import re
from datetime import datetime
from collections import defaultdict

class AIIntelligentQNA:
    QUESTION_TYPES = ['factual', 'conceptual', 'procedural', 'analytical', 'evaluative', 'creative']
    ANSWER_SOURCES = ['knowledge_base', 'memory', 'reasoning', 'external', 'generated']
    CONFIDENCE_LEVELS = ['low', 'medium', 'high', 'very_high']
    
    def __init__(self):
        self.qa_cache = {}
        self._lock = threading.Lock()
        self._create_tables()
    
    def _create_tables(self):
        try:
            conn = sqlite3.connect('ai_qna.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS qa_pairs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    qa_id TEXT NOT NULL UNIQUE,
                    question TEXT NOT NULL,
                    question_type TEXT DEFAULT 'factual',
                    answer TEXT NOT NULL,
                    answer_source TEXT DEFAULT 'generated',
                    confidence REAL DEFAULT 0.0,
                    tags TEXT,
                    subject TEXT,
                    category TEXT,
                    views INTEGER DEFAULT 0,
                    likes INTEGER DEFAULT 0,
                    dislikes INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS qna_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL UNIQUE,
                    user_id TEXT,
                    subject TEXT,
                    started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    ended_at TEXT,
                    question_count INTEGER DEFAULT 0,
                    avg_response_time REAL DEFAULT 0.0,
                    metadata TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS qna_conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL UNIQUE,
                    session_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT,
                    question_type TEXT,
                    confidence REAL DEFAULT 0.0,
                    response_time REAL DEFAULT 0.0,
                    feedback INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS qna_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    feedback_id TEXT NOT NULL UNIQUE,
                    qa_id TEXT,
                    conversation_id TEXT,
                    user_id TEXT,
                    rating INTEGER DEFAULT 0,
                    comment TEXT,
                    useful BOOLEAN DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS qna_topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    description TEXT,
                    subject TEXT,
                    question_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[AI Intelligent QNA] 创建表失败: {e}")
    
    def _generate_id(self, prefix):
        return prefix + '_' + hashlib.md5((str(datetime.now().timestamp()) + str(random.random())).encode()).hexdigest()[:16]
    
    def add_qa_pair(self, question, answer, question_type='factual', answer_source='generated', 
                    confidence=0.8, tags=None, subject=None, category=None):
        qa_id = self._generate_id('qa')
        
        try:
            conn = sqlite3.connect('ai_qna.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO qa_pairs 
                (qa_id, question, question_type, answer, answer_source, confidence, tags, subject, category)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (qa_id, question, question_type, answer, answer_source, confidence, 
                  json.dumps(tags or []), subject, category))
            conn.commit()
            conn.close()
            
            return {'success': True, 'qa_id': qa_id}
        except Exception as e:
            print(f"[AI Intelligent QNA] 添加问答对失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_qa_pair(self, qa_id):
        try:
            conn = sqlite3.connect('ai_qna.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM qa_pairs WHERE qa_id = ?', (qa_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                result = dict(row)
                result['tags'] = json.loads(result.get('tags', '[]'))
                return result
            return None
        except Exception as e:
            print(f"[AI Intelligent QNA] 获取问答对失败: {e}")
            return None
    
    def search_qa_pairs(self, query, subject=None, question_type=None, limit=10):
        try:
            conn = sqlite3.connect('ai_qna.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            conditions = ['question LIKE ? OR answer LIKE ?']
            params = ['%' + query + '%', '%' + query + '%']
            
            if subject:
                conditions.append('subject = ?')
                params.append(subject)
            
            if question_type:
                conditions.append('question_type = ?')
                params.append(question_type)
            
            params.append(limit)
            
            cursor.execute(f'''
                SELECT * FROM qa_pairs 
                WHERE {' AND '.join(conditions)}
                ORDER BY confidence DESC, views DESC LIMIT ?
            ''', params)
            
            results = []
            for row in cursor.fetchall():
                qa = dict(row)
                qa['tags'] = json.loads(qa.get('tags', '[]'))
                results.append(qa)
            
            conn.close()
            return results
        except Exception as e:
            print(f"[AI Intelligent QNA] 搜索问答对失败: {e}")
            return []
    
    def _extract_keywords(self, question):
        stop_words = ['的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那个']
        
        cleaned = re.sub(r'[^\w\s]', '', question)
        words = cleaned.split()
        keywords = [word for word in words if word not in stop_words and len(word) > 1]
        
        return keywords[:10]
    
    def _calculate_similarity(self, question1, question2):
        keywords1 = set(self._extract_keywords(question1))
        keywords2 = set(self._extract_keywords(question2))
        
        if not keywords1 or not keywords2:
            return 0.0
        
        intersection = keywords1 & keywords2
        union = keywords1 | keywords2
        
        return len(intersection) / len(union)
    
    def answer_question(self, question, session_id=None, user_id=None):
        start_time = datetime.now()
        
        cached = self.qa_cache.get(question)
        if cached:
            return cached
        
        candidates = self.search_qa_pairs(question)
        
        best_match = None
        best_score = 0.0
        
        for candidate in candidates:
            score = self._calculate_similarity(question, candidate['question'])
            if score > best_score and score >= 0.3:
                best_score = score
                best_match = candidate
        
        if best_match:
            confidence = min(0.95, best_match['confidence'] * (0.7 + best_score * 0.3))
            
            try:
                conn = sqlite3.connect('ai_qna.db')
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE qa_pairs SET views = views + 1 WHERE qa_id = ?
                ''', (best_match['qa_id'],))
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"[AI Intelligent QNA] 更新浏览次数失败: {e}")
            
            conversation_id = self._generate_id('conv')
            response_time = (datetime.now() - start_time).total_seconds()
            
            try:
                conn = sqlite3.connect('ai_qna.db')
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO qna_conversations 
                    (conversation_id, session_id, question, answer, question_type, confidence, response_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (conversation_id, session_id, question, best_match['answer'], 
                      best_match['question_type'], confidence, response_time))
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"[AI Intelligent QNA] 保存对话失败: {e}")
            
            result = {
                'success': True,
                'answer': best_match['answer'],
                'question_type': best_match['question_type'],
                'confidence': round(confidence, 2),
                'source': best_match['answer_source'],
                'qa_id': best_match['qa_id'],
                'conversation_id': conversation_id,
                'response_time': round(response_time, 2),
                'similarity_score': round(best_score, 2),
                'tags': best_match.get('tags', []),
                'subject': best_match.get('subject'),
                'is_cached': False
            }
            
            self.qa_cache[question] = result
            
            return result
        
        generated_answer = self._generate_answer(question)
        response_time = (datetime.now() - start_time).total_seconds()
        
        conversation_id = self._generate_id('conv')
        
        try:
            conn = sqlite3.connect('ai_qna.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO qna_conversations 
                (conversation_id, session_id, question, answer, question_type, confidence, response_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (conversation_id, session_id, question, generated_answer['answer'], 
                  generated_answer['question_type'], generated_answer['confidence'], response_time))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[AI Intelligent QNA] 保存对话失败: {e}")
        
        result = {
            'success': True,
            'answer': generated_answer['answer'],
            'question_type': generated_answer['question_type'],
            'confidence': generated_answer['confidence'],
            'source': 'generated',
            'conversation_id': conversation_id,
            'response_time': round(response_time, 2),
            'similarity_score': 0.0,
            'is_cached': False,
            'explanation': '未找到匹配的问答对，已生成新答案'
        }
        
        return result
    
    def _generate_answer(self, question):
        keywords = self._extract_keywords(question)
        
        question_type = self._classify_question(question)
        
        answers = {
            'factual': f"根据您的问题，关于{'、'.join(keywords)}的基本信息如下：这是一个事实性问题，涉及具体的知识内容。",
            'conceptual': f"关于{'、'.join(keywords)}的概念理解：这是一个概念性问题，涉及对知识的深层理解和概念之间的关系。",
            'procedural': f"关于{'、'.join(keywords)}的操作步骤：这是一个程序性问题，涉及如何完成特定任务或解决问题的步骤。",
            'analytical': f"对{'、'.join(keywords)}的分析：这是一个分析性问题，需要深入分析和评估相关信息。",
            'evaluative': f"对{'、'.join(keywords)}的评价：这是一个评价性问题，需要基于标准进行判断和评估。",
            'creative': f"关于{'、'.join(keywords)}的创造性解答：这是一个创造性问题，需要创新性思维和解决方案。"
        }
        
        return {
            'answer': answers.get(question_type, f"关于{'、'.join(keywords)}的回答：这是一个综合性问题，需要从多个角度进行分析和解答。"),
            'question_type': question_type,
            'confidence': 0.65
        }
    
    def _classify_question(self, question):
        factual_patterns = ['是什么', '什么是', '定义', '解释', '说明', '含义', '概念', '包括', '包含']
        procedural_patterns = ['怎么', '如何', '步骤', '方法', '流程', '做法', '操作', '技巧']
        analytical_patterns = ['为什么', '原因', '分析', '比较', '区别', '差异', '联系']
        evaluative_patterns = ['评价', '评估', '好坏', '优劣', '建议', '推荐']
        creative_patterns = ['设计', '创作', '创新', '方案', '思路', '想法']
        
        question_lower = question.lower()
        
        if any(pattern in question_lower for pattern in creative_patterns):
            return 'creative'
        if any(pattern in question_lower for pattern in evaluative_patterns):
            return 'evaluative'
        if any(pattern in question_lower for pattern in analytical_patterns):
            return 'analytical'
        if any(pattern in question_lower for pattern in procedural_patterns):
            return 'procedural'
        if any(pattern in question_lower for pattern in factual_patterns):
            return 'factual'
        
        return 'conceptual'
    
    def create_session(self, user_id=None, subject=None):
        session_id = self._generate_id('session')
        
        try:
            conn = sqlite3.connect('ai_qna.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO qna_sessions 
                (session_id, user_id, subject)
                VALUES (?, ?, ?)
            ''', (session_id, user_id, subject))
            conn.commit()
            conn.close()
            
            return {'success': True, 'session_id': session_id}
        except Exception as e:
            print(f"[AI Intelligent QNA] 创建会话失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def end_session(self, session_id):
        try:
            conn = sqlite3.connect('ai_qna.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM qna_conversations WHERE session_id = ?', (session_id,))
            question_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT AVG(response_time) FROM qna_conversations WHERE session_id = ?', (session_id,))
            avg_response_time = cursor.fetchone()[0] or 0.0
            
            cursor.execute('''
                UPDATE qna_sessions 
                SET ended_at = ?, question_count = ?, avg_response_time = ?
                WHERE session_id = ?
            ''', (datetime.now().isoformat(), question_count, avg_response_time, session_id))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'question_count': question_count, 'avg_response_time': round(avg_response_time, 2)}
        except Exception as e:
            print(f"[AI Intelligent QNA] 结束会话失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_session_history(self, session_id):
        try:
            conn = sqlite3.connect('ai_qna.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM qna_conversations WHERE session_id = ? ORDER BY created_at', (session_id,))
            conversations = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            return conversations
        except Exception as e:
            print(f"[AI Intelligent QNA] 获取会话历史失败: {e}")
            return []
    
    def submit_feedback(self, conversation_id, user_id, rating, comment='', useful=True):
        feedback_id = self._generate_id('feedback')
        
        try:
            conn = sqlite3.connect('ai_qna.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO qna_feedback 
                (feedback_id, conversation_id, user_id, rating, comment, useful)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (feedback_id, conversation_id, user_id, rating, comment, useful))
            conn.commit()
            
            cursor.execute('''
                SELECT qa_id FROM qna_conversations WHERE conversation_id = ?
            ''', (conversation_id,))
            row = cursor.fetchone()
            if row and row['qa_id']:
                if useful:
                    cursor.execute('UPDATE qa_pairs SET likes = likes + 1 WHERE qa_id = ?', (row['qa_id'],))
                else:
                    cursor.execute('UPDATE qa_pairs SET dislikes = dislikes + 1 WHERE qa_id = ?', (row['qa_id'],))
                conn.commit()
            
            conn.close()
            
            return {'success': True, 'feedback_id': feedback_id}
        except Exception as e:
            print(f"[AI Intelligent QNA] 提交反馈失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def add_topic(self, name, description='', subject=None):
        topic_id = self._generate_id('topic')
        
        try:
            conn = sqlite3.connect('ai_qna.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO qna_topics 
                (topic_id, name, description, subject)
                VALUES (?, ?, ?, ?)
            ''', (topic_id, name, description, subject))
            conn.commit()
            conn.close()
            
            return {'success': True, 'topic_id': topic_id}
        except Exception as e:
            print(f"[AI Intelligent QNA] 添加主题失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_topics(self, subject=None):
        try:
            conn = sqlite3.connect('ai_qna.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if subject:
                cursor.execute('SELECT * FROM qna_topics WHERE subject = ? ORDER BY created_at DESC', (subject,))
            else:
                cursor.execute('SELECT * FROM qna_topics ORDER BY question_count DESC')
            
            topics = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return topics
        except Exception as e:
            print(f"[AI Intelligent QNA] 获取主题失败: {e}")
            return []
    
    def get_qna_statistics(self):
        try:
            conn = sqlite3.connect('ai_qna.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM qa_pairs')
            total_qa = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM qna_sessions')
            total_sessions = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM qna_conversations')
            total_conversations = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM qna_topics')
            total_topics = cursor.fetchone()[0]
            
            cursor.execute('SELECT AVG(confidence) FROM qa_pairs')
            avg_confidence = cursor.fetchone()[0] or 0.0
            
            cursor.execute('SELECT AVG(response_time) FROM qna_conversations')
            avg_response_time = cursor.fetchone()[0] or 0.0
            
            cursor.execute('SELECT SUM(likes) FROM qa_pairs')
            total_likes = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT SUM(dislikes) FROM qa_pairs')
            total_dislikes = cursor.fetchone()[0] or 0
            
            cursor.execute('''
                SELECT question_type, COUNT(*) as count 
                FROM qa_pairs 
                GROUP BY question_type
            ''')
            type_stats = []
            for row in cursor.fetchall():
                type_stats.append({
                    'question_type': row[0],
                    'count': row[1]
                })
            
            cursor.execute('''
                SELECT subject, COUNT(*) as count 
                FROM qa_pairs 
                GROUP BY subject 
                ORDER BY count DESC LIMIT 5
            ''')
            subject_stats = []
            for row in cursor.fetchall():
                subject_stats.append({
                    'subject': row[0],
                    'count': row[1]
                })
            
            conn.close()
            
            return {
                'total_qa_pairs': total_qa,
                'total_sessions': total_sessions,
                'total_conversations': total_conversations,
                'total_topics': total_topics,
                'avg_confidence': round(avg_confidence, 2),
                'avg_response_time': round(avg_response_time, 2),
                'total_likes': total_likes,
                'total_dislikes': total_dislikes,
                'type_statistics': type_stats,
                'subject_statistics': subject_stats
            }
        except Exception as e:
            print(f"[AI Intelligent QNA] 获取统计信息失败: {e}")
            return {
                'total_qa_pairs': 0,
                'total_sessions': 0,
                'total_conversations': 0,
                'total_topics': 0,
                'avg_confidence': 0.0,
                'avg_response_time': 0.0,
                'total_likes': 0,
                'total_dislikes': 0,
                'type_statistics': [],
                'subject_statistics': []
            }

    def list_sessions(self, user_id=None):
        try:
            conn = sqlite3.connect('ai_qna.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute('SELECT * FROM qna_sessions WHERE user_id = ? ORDER BY started_at DESC', (user_id,))
            else:
                cursor.execute('SELECT * FROM qna_sessions ORDER BY started_at DESC LIMIT 50')
            
            sessions = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return sessions
        except Exception as e:
            print(f"[AI Intelligent QNA] 获取会话列表失败: {e}")
            return []
    
    def get_hot_qa_pairs(self, limit=10):
        try:
            conn = sqlite3.connect('ai_qna.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM qa_pairs 
                ORDER BY views DESC, likes DESC LIMIT ?
            ''', (limit,))
            
            results = []
            for row in cursor.fetchall():
                qa = dict(row)
                qa['tags'] = json.loads(qa.get('tags', '[]'))
                results.append(qa)
            
            conn.close()
            return results
        except Exception as e:
            print(f"[AI Intelligent QNA] 获取热门问答失败: {e}")
            return []
    
    def list_qa_pairs(self, limit=20):
        try:
            conn = sqlite3.connect('ai_qna.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM qa_pairs ORDER BY created_at DESC LIMIT ?', (limit,))
            
            results = []
            for row in cursor.fetchall():
                qa = dict(row)
                qa['tags'] = json.loads(qa.get('tags', '[]'))
                results.append(qa)
            
            conn.close()
            return results
        except Exception as e:
            print(f"[AI Intelligent QNA] 列出问答对失败: {e}")
            return []
    
    def get_feedback_statistics(self):
        try:
            conn = sqlite3.connect('ai_qna.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM qna_feedback')
            total_feedback = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM qna_feedback WHERE useful = 1')
            positive_feedback = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM qna_feedback WHERE useful = 0')
            negative_feedback = cursor.fetchone()[0]
            
            cursor.execute('SELECT AVG(rating) FROM qna_feedback')
            avg_rating = cursor.fetchone()[0] or 0.0
            
            conn.close()
            
            return {
                'total_feedback': total_feedback,
                'positive_feedback': positive_feedback,
                'negative_feedback': negative_feedback,
                'positive_rate': round(positive_feedback / total_feedback * 100, 2) if total_feedback > 0 else 0.0,
                'avg_rating': round(avg_rating, 2)
            }
        except Exception as e:
            print(f"[AI Intelligent QNA] 获取反馈统计失败: {e}")
            return {
                'total_feedback': 0,
                'positive_feedback': 0,
                'negative_feedback': 0,
                'positive_rate': 0.0,
                'avg_rating': 0.0
            }

ai_intelligent_qna = AIIntelligentQNA()