#!/usr/bin/env python3
"""
AI智能课堂互动系统
提供课堂实时互动、智能问答、课堂测验等功能
"""

import sqlite3
import hashlib
import json
import random
import os
from datetime import datetime
from typing import Dict, List, Optional

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app.db')

class AIClassroomInteraction:
    """AI课堂互动引擎"""
    
    INTERACTION_TYPES = {
        'question': {'name': '提问', 'color': '#2196F3'},
        'answer': {'name': '回答', 'color': '#4CAF50'},
        'quiz': {'name': '测验', 'color': '#FF9800'},
        'poll': {'name': '投票', 'color': '#9C27B0'},
        'discussion': {'name': '讨论', 'color': '#00BCD4'}
    }
    
    QUIZ_TYPES = ['single_choice', 'multiple_choice', 'true_false', 'fill_blank']
    
    ATTENDANCE_STATUS = {'present': '出勤', 'absent': '缺席', 'late': '迟到'}
    
    def __init__(self):
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS classroom_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                course_id TEXT NOT NULL,
                course_name TEXT,
                teacher_id TEXT NOT NULL,
                teacher_name TEXT,
                start_time TEXT DEFAULT CURRENT_TIMESTAMP,
                end_time TEXT,
                status TEXT DEFAULT 'active',
                metadata TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS classroom_attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attendance_id TEXT UNIQUE NOT NULL,
                session_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                user_name TEXT,
                status TEXT DEFAULT 'present',
                check_in_time TEXT,
                check_out_time TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS classroom_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interaction_id TEXT UNIQUE NOT NULL,
                session_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                user_name TEXT,
                interaction_type TEXT NOT NULL,
                content TEXT NOT NULL,
                parent_id TEXT,
                likes INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS classroom_quizzes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id TEXT UNIQUE NOT NULL,
                session_id TEXT NOT NULL,
                question TEXT NOT NULL,
                options TEXT,
                correct_answer TEXT,
                quiz_type TEXT DEFAULT 'single_choice',
                time_limit INTEGER DEFAULT 60,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quiz_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                response_id TEXT UNIQUE NOT NULL,
                quiz_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                answer TEXT NOT NULL,
                is_correct INTEGER DEFAULT 0,
                submitted_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS classroom_polls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                poll_id TEXT UNIQUE NOT NULL,
                session_id TEXT NOT NULL,
                question TEXT NOT NULL,
                options TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS poll_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                response_id TEXT UNIQUE NOT NULL,
                poll_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def start_classroom_session(self, course_id: str, course_name: str, 
                                teacher_id: str, teacher_name: str) -> Dict:
        """开始课堂会话"""
        session_id = hashlib.md5(f"{course_id}{teacher_id}{datetime.now()}".encode()).hexdigest()[:16]
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO classroom_sessions 
            (session_id, course_id, course_name, teacher_id, teacher_name, start_time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_id, course_id, course_name, teacher_id, teacher_name, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'session_id': session_id,
            'course_id': course_id,
            'course_name': course_name,
            'teacher_id': teacher_id,
            'teacher_name': teacher_name,
            'start_time': datetime.now().isoformat()
        }
    
    def end_classroom_session(self, session_id: str) -> Dict:
        """结束课堂会话"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE classroom_sessions 
            SET status = 'ended', end_time = ? 
            WHERE session_id = ? AND status = 'active'
        ''', (datetime.now().isoformat(), session_id))
        
        success = cursor.rowcount > 0
        
        cursor.execute('''
            SELECT course_name, teacher_name, start_time 
            FROM classroom_sessions 
            WHERE session_id = ?
        ''', (session_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if success and row:
            return {
                'success': True,
                'session_id': session_id,
                'course_name': row[0],
                'teacher_name': row[1],
                'start_time': row[2],
                'end_time': datetime.now().isoformat()
            }
        
        return {'success': False, 'error': '会话不存在或已结束'}
    
    def check_in(self, session_id: str, user_id: str, user_name: str) -> Dict:
        """课堂签到"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT status FROM classroom_sessions WHERE session_id = ?
        ''', (session_id,))
        
        session_row = cursor.fetchone()
        
        if not session_row or session_row[0] != 'active':
            conn.close()
            return {'success': False, 'error': '课堂会话不存在或已结束'}
        
        cursor.execute('''
            SELECT * FROM classroom_attendance 
            WHERE session_id = ? AND user_id = ?
        ''', (session_id, user_id))
        
        existing = cursor.fetchone()
        
        if existing:
            conn.close()
            return {'success': False, 'error': '已签到'}
        
        attendance_id = hashlib.md5(f"{session_id}{user_id}{datetime.now()}".encode()).hexdigest()[:16]
        
        cursor.execute('''
            INSERT INTO classroom_attendance 
            (attendance_id, session_id, user_id, user_name, status, check_in_time)
            VALUES (?, ?, ?, ?, 'present', ?)
        ''', (attendance_id, session_id, user_id, user_name, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'attendance_id': attendance_id,
            'session_id': session_id,
            'user_id': user_id,
            'user_name': user_name,
            'status': 'present',
            'check_in_time': datetime.now().isoformat()
        }
    
    def get_attendance(self, session_id: str) -> Dict:
        """获取签到信息"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM classroom_attendance WHERE session_id = ? ORDER BY check_in_time
        ''', (session_id,))
        
        rows = cursor.fetchall()
        
        present_count = 0
        absent_count = 0
        
        records = []
        for row in rows:
            status = row[5]
            if status == 'present':
                present_count += 1
            else:
                absent_count += 1
            
            records.append({
                'attendance_id': row[1],
                'user_id': row[3],
                'user_name': row[4],
                'status': status,
                'check_in_time': row[6],
                'check_out_time': row[7]
            })
        
        conn.close()
        
        return {
            'success': True,
            'session_id': session_id,
            'total_students': len(records),
            'present_count': present_count,
            'absent_count': absent_count,
            'records': records
        }
    
    def add_interaction(self, session_id: str, user_id: str, user_name: str,
                        interaction_type: str, content: str, parent_id: str = '') -> Dict:
        """添加互动"""
        interaction_id = hashlib.md5(f"{session_id}{user_id}{content}{datetime.now()}".encode()).hexdigest()[:16]
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO classroom_interactions 
            (interaction_id, session_id, user_id, user_name, interaction_type, content, parent_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (interaction_id, session_id, user_id, user_name, interaction_type, content, parent_id))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'interaction_id': interaction_id,
            'session_id': session_id,
            'user_id': user_id,
            'user_name': user_name,
            'interaction_type': interaction_type,
            'content': content,
            'created_at': datetime.now().isoformat()
        }
    
    def get_interactions(self, session_id: str, interaction_type: str = '') -> Dict:
        """获取互动列表"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        if interaction_type:
            cursor.execute('''
                SELECT * FROM classroom_interactions 
                WHERE session_id = ? AND interaction_type = ? 
                ORDER BY created_at DESC
            ''', (session_id, interaction_type))
        else:
            cursor.execute('''
                SELECT * FROM classroom_interactions 
                WHERE session_id = ? 
                ORDER BY created_at DESC
            ''', (session_id,))
        
        rows = cursor.fetchall()
        
        interactions = []
        for row in rows:
            interactions.append({
                'interaction_id': row[1],
                'user_id': row[3],
                'user_name': row[4],
                'interaction_type': row[5],
                'content': row[6],
                'parent_id': row[7],
                'likes': row[8],
                'created_at': row[9]
            })
        
        conn.close()
        
        return {'success': True, 'data': interactions}
    
    def create_quiz(self, session_id: str, question: str, options: List, 
                    correct_answer: str, quiz_type: str = 'single_choice', 
                    time_limit: int = 60) -> Dict:
        """创建测验"""
        quiz_id = hashlib.md5(f"{session_id}{question}{datetime.now()}".encode()).hexdigest()[:16]
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO classroom_quizzes 
            (quiz_id, session_id, question, options, correct_answer, quiz_type, time_limit)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (quiz_id, session_id, question, json.dumps(options, ensure_ascii=False), 
              correct_answer, quiz_type, time_limit))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'quiz_id': quiz_id,
            'session_id': session_id,
            'question': question,
            'options': options,
            'quiz_type': quiz_type,
            'time_limit': time_limit,
            'created_at': datetime.now().isoformat()
        }
    
    def answer_quiz(self, quiz_id: str, user_id: str, answer: str) -> Dict:
        """回答测验"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT correct_answer, quiz_type FROM classroom_quizzes WHERE quiz_id = ?
        ''', (quiz_id,))
        
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return {'success': False, 'error': '测验不存在'}
        
        correct_answer = row[0]
        is_correct = 1 if answer == correct_answer else 0
        
        response_id = hashlib.md5(f"{quiz_id}{user_id}{datetime.now()}".encode()).hexdigest()[:16]
        
        cursor.execute('''
            INSERT INTO quiz_responses 
            (response_id, quiz_id, user_id, answer, is_correct, submitted_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (response_id, quiz_id, user_id, answer, is_correct, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'response_id': response_id,
            'quiz_id': quiz_id,
            'user_id': user_id,
            'answer': answer,
            'is_correct': bool(is_correct),
            'correct_answer': correct_answer,
            'submitted_at': datetime.now().isoformat()
        }
    
    def get_quiz_results(self, quiz_id: str) -> Dict:
        """获取测验结果"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT question, options, correct_answer FROM classroom_quizzes WHERE quiz_id = ?
        ''', (quiz_id,))
        
        quiz_row = cursor.fetchone()
        
        if not quiz_row:
            conn.close()
            return {'success': False, 'error': '测验不存在'}
        
        cursor.execute('''
            SELECT * FROM quiz_responses WHERE quiz_id = ?
        ''', (quiz_id,))
        
        response_rows = cursor.fetchall()
        
        total_responses = len(response_rows)
        correct_count = sum(1 for r in response_rows if r[4] == 1)
        accuracy = round((correct_count / total_responses) * 100, 2) if total_responses > 0 else 0
        
        responses = []
        for row in response_rows:
            responses.append({
                'response_id': row[1],
                'user_id': row[3],
                'answer': row[4],
                'is_correct': bool(row[5]),
                'submitted_at': row[6]
            })
        
        conn.close()
        
        return {
            'success': True,
            'quiz_id': quiz_id,
            'question': quiz_row[0],
            'options': json.loads(quiz_row[1]),
            'correct_answer': quiz_row[2],
            'total_responses': total_responses,
            'correct_count': correct_count,
            'accuracy': accuracy,
            'responses': responses
        }
    
    def create_poll(self, session_id: str, question: str, options: List) -> Dict:
        """创建投票"""
        poll_id = hashlib.md5(f"{session_id}{question}{datetime.now()}".encode()).hexdigest()[:16]
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO classroom_polls 
            (poll_id, session_id, question, options)
            VALUES (?, ?, ?, ?)
        ''', (poll_id, session_id, question, json.dumps(options, ensure_ascii=False)))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'poll_id': poll_id,
            'session_id': session_id,
            'question': question,
            'options': options,
            'created_at': datetime.now().isoformat()
        }
    
    def vote_poll(self, poll_id: str, user_id: str, answer: str) -> Dict:
        """投票"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT status FROM classroom_polls WHERE poll_id = ?
        ''', (poll_id,))
        
        row = cursor.fetchone()
        
        if not row or row[0] != 'active':
            conn.close()
            return {'success': False, 'error': '投票不存在或已结束'}
        
        cursor.execute('''
            SELECT * FROM poll_responses WHERE poll_id = ? AND user_id = ?
        ''', (poll_id, user_id))
        
        existing = cursor.fetchone()
        
        if existing:
            conn.close()
            return {'success': False, 'error': '已投票'}
        
        response_id = hashlib.md5(f"{poll_id}{user_id}{datetime.now()}".encode()).hexdigest()[:16]
        
        cursor.execute('''
            INSERT INTO poll_responses 
            (response_id, poll_id, user_id, answer)
            VALUES (?, ?, ?, ?)
        ''', (response_id, poll_id, user_id, answer))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'response_id': response_id,
            'poll_id': poll_id,
            'user_id': user_id,
            'answer': answer,
            'created_at': datetime.now().isoformat()
        }
    
    def get_poll_results(self, poll_id: str) -> Dict:
        """获取投票结果"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT question, options FROM classroom_polls WHERE poll_id = ?
        ''', (poll_id,))
        
        poll_row = cursor.fetchone()
        
        if not poll_row:
            conn.close()
            return {'success': False, 'error': '投票不存在'}
        
        cursor.execute('''
            SELECT answer, COUNT(*) as count FROM poll_responses WHERE poll_id = ? GROUP BY answer
        ''', (poll_id,))
        
        response_rows = cursor.fetchall()
        
        total_votes = sum(r[1] for r in response_rows)
        
        results = {}
        for row in response_rows:
            percentage = round((row[1] / total_votes) * 100, 2) if total_votes > 0 else 0
            results[row[0]] = {'count': row[1], 'percentage': percentage}
        
        conn.close()
        
        return {
            'success': True,
            'poll_id': poll_id,
            'question': poll_row[0],
            'options': json.loads(poll_row[1]),
            'total_votes': total_votes,
            'results': results
        }
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """获取会话信息"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM classroom_sessions WHERE session_id = ?', (session_id,))
        row = cursor.fetchone()
        
        if row:
            cursor.execute('SELECT COUNT(*) FROM classroom_attendance WHERE session_id = ?', (session_id,))
            attendance_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM classroom_interactions WHERE session_id = ?', (session_id,))
            interaction_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'session_id': row[1],
                'course_id': row[2],
                'course_name': row[3],
                'teacher_id': row[4],
                'teacher_name': row[5],
                'start_time': row[6],
                'end_time': row[7],
                'status': row[8],
                'attendance_count': attendance_count,
                'interaction_count': interaction_count
            }
        
        conn.close()
        return None

ai_classroom_interaction = AIClassroomInteraction()