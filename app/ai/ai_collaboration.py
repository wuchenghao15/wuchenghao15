#!/usr/bin/env python3
import os
import json
import time
import sqlite3
import threading
import uuid
from datetime import datetime
from collections import defaultdict

class AICollaborationSystem:
    def __init__(self):
        self.sessions = {}
        self.tasks = {}
        self.knowledge_base = {}
        self.worker_registry = {}
        self._lock = threading.Lock()
        self._create_tables()
    
    def _create_tables(self):
        try:
            conn = sqlite3.connect('ai_collaboration.db')
            cursor = conn.cursor()
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS collaboration_sessions ( id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL UNIQUE, session_name TEXT, purpose TEXT, status TEXT DEFAULT 'active', created_by TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, completed_at TEXT ) ''')
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS collaboration_tasks ( id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL UNIQUE, session_id TEXT NOT NULL, worker_id TEXT, worker_name TEXT, task_type TEXT, task_content TEXT, status TEXT DEFAULT 'pending', priority TEXT DEFAULT 'medium', assigned_at TEXT DEFAULT CURRENT_TIMESTAMP, started_at TEXT, completed_at TEXT, result TEXT, score REAL DEFAULT 0.0 ) ''')
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS knowledge_sharing ( id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, worker_id TEXT, knowledge_type TEXT, knowledge_content TEXT, shared_at TEXT DEFAULT CURRENT_TIMESTAMP, relevance_score REAL DEFAULT 0.0 ) ''')
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS registered_workers ( id INTEGER PRIMARY KEY AUTOINCREMENT, worker_id TEXT NOT NULL UNIQUE, worker_name TEXT NOT NULL, capabilities TEXT, status TEXT DEFAULT 'available', last_seen TEXT DEFAULT CURRENT_TIMESTAMP, avg_score REAL DEFAULT 0.0 ) ''')
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS collaboration_history ( id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, action_type TEXT, action_content TEXT, actor_id TEXT, actor_name TEXT, timestamp TEXT DEFAULT CURRENT_TIMESTAMP ) ''')
            
            conn.commit()
            conn.close()
            logger.info("[AI Collaboration] 数据库表创建完成")
        except Exception as e:
            logger.info(f"[AI Collaboration] 创建表失败: {e}")
    
    def create_session(self, session_name, purpose, created_by):
        session_id = str(uuid.uuid4())[:8]
        
        try:
            conn = sqlite3.connect('ai_collaboration.db')
            cursor = conn.cursor()
            cursor.execute(''' INSERT INTO collaboration_sessions (session_id, session_name, purpose, created_by) VALUES (?, ?, ?, ?) ''', (session_id, session_name, purpose, created_by))
            conn.commit()
            conn.close()
            
            self.sessions[session_id] = {
                'name': session_name,
                'purpose': purpose,
                'status': 'active',
                'created_by': created_by,
                'created_at': datetime.now().isoformat(),
                'tasks': []
            }
            
            self._record_history(session_id, 'session_created', f"创建协作会话: {session_name}", created_by)
            
            return session_id
        except Exception as e:
            logger.info(f"[AI Collaboration] 创建会话失败: {e}")
            return None
    
    def assign_task(self, session_id, task_type, task_content, priority='medium'):
        available_workers = self.get_available_workers()
        
        if not available_workers:
            return {'error': '没有可用的AI员工'}
        
        best_worker = self._select_best_worker(available_workers, task_type)
        task_id = str(uuid.uuid4())[:8]
        
        try:
            conn = sqlite3.connect('ai_collaboration.db')
            cursor = conn.cursor()
            cursor.execute(''' INSERT INTO collaboration_tasks (task_id, session_id, worker_id, worker_name, task_type, task_content, priority) VALUES (?, ?, ?, ?, ?, ?, ?) ''', (task_id, session_id, best_worker['worker_id'], best_worker['worker_name'], task_type, task_content,
            priority))
            conn.commit()
            conn.close()
            
            self.tasks[task_id] = {
                'session_id': session_id,
                'worker_id': best_worker['worker_id'],
                'worker_name': best_worker['worker_name'],
                'type': task_type,
                'content': task_content,
                'status': 'assigned',
                'priority': priority,
                'assigned_at': datetime.now().isoformat()
            }
            
            if session_id in self.sessions:
                self.sessions[session_id]['tasks'].append(task_id)
            
            self._record_history(session_id, 'task_assigned', f"分配任务: {task_type} -> {best_worker['worker_name']}",
            best_worker['worker_id'])
            
            return {'task_id': task_id, 'worker_id': best_worker['worker_id'],
            'worker_name': best_worker['worker_name']}
        except Exception as e:
            logger.info(f"[AI Collaboration] 分配任务失败: {e}")
            return {'error': str(e)}
    
    def _select_best_worker(self, workers, task_type):
        best_worker = workers[0]
        best_score = -1
        
        for worker in workers:
            capabilities = json.loads(worker.get('capabilities', '[]'))
            if task_type in capabilities:
                score = worker.get('avg_score', 0) + 10
            else:
                score = worker.get('avg_score', 0)
            
            if score > best_score:
                best_score = score
                best_worker = worker
        
        return best_worker
    
    def start_task(self, task_id):
        try:
            conn = sqlite3.connect('ai_collaboration.db')
            cursor = conn.cursor()
            cursor.execute(''' UPDATE collaboration_tasks SET status = ?, started_at = ? WHERE task_id = ? ''', ('in_progress', datetime.now().isoformat(), task_id))
            conn.commit()
            conn.close()
            
            if task_id in self.tasks:
                self.tasks[task_id]['status'] = 'in_progress'
                self.tasks[task_id]['started_at'] = datetime.now().isoformat()
            
            return True
        except Exception as e:
            logger.info(f"[AI Collaboration] 开始任务失败: {e}")
            return False
    
    def complete_task(self, task_id, result, score=0.0):
        try:
            conn = sqlite3.connect('ai_collaboration.db')
            cursor = conn.cursor()
            cursor.execute(''' UPDATE collaboration_tasks SET status = ?, completed_at = ?, result = ?, score = ? WHERE task_id = ? ''', ('completed', datetime.now().isoformat(), result, score, task_id))
            conn.commit()
            
            cursor.execute('SELECT session_id, worker_id FROM collaboration_tasks WHERE task_id = ?', (task_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                session_id, worker_id = row
                self._record_history(session_id, 'task_completed', f"任务完成: {task_id}, 评分: {score}", worker_id)
            
            if task_id in self.tasks:
                self.tasks[task_id]['status'] = 'completed'
                self.tasks[task_id]['completed_at'] = datetime.now().isoformat()
                self.tasks[task_id]['result'] = result
                self.tasks[task_id]['score'] = score
            
            return True
        except Exception as e:
            logger.info(f"[AI Collaboration] 完成任务失败: {e}")
            return False
    
    def share_knowledge(self, session_id, worker_id, knowledge_type, knowledge_content):
        try:
            conn = sqlite3.connect('ai_collaboration.db')
            cursor = conn.cursor()
            cursor.execute(''' INSERT INTO knowledge_sharing (session_id, worker_id, knowledge_type, knowledge_content, relevance_score) VALUES (?, ?, ?, ?, ?) ''', (session_id, worker_id, knowledge_type, knowledge_content, self._calculate_relevance(knowledge_type,
            knowledge_content)))
            conn.commit()
            conn.close()
            
            self.knowledge_base.setdefault(session_id, []).append({
                'type': knowledge_type,
                'content': knowledge_content,
                'worker_id': worker_id,
                'shared_at': datetime.now().isoformat()
            })
            
            self._record_history(session_id, 'knowledge_shared', f"共享知识: {knowledge_type}", worker_id)
            
            return True
        except Exception as e:
            logger.info(f"[AI Collaboration] 共享知识失败: {e}")
            return False
    
    def _calculate_relevance(self, knowledge_type, content):
        keywords = ['分析', '优化', '预测', '智能', '学习', '决策', '推荐']
        score = 0.5
        for keyword in keywords:
            if keyword in content or keyword in knowledge_type:
                score += 0.1
        return min(1.0, score)
    
    def register_worker(self, worker_id, worker_name, capabilities):
        try:
            conn = sqlite3.connect('ai_collaboration.db')
            cursor = conn.cursor()
            cursor.execute(''' INSERT OR REPLACE INTO registered_workers (worker_id, worker_name, capabilities, status, last_seen) VALUES (?, ?, ?, ?, ?) ''', (worker_id, worker_name, json.dumps(capabilities), 'available', datetime.now().isoformat()))
            conn.commit()
            conn.close()
            
            self.worker_registry[worker_id] = {
                'name': worker_name,
                'capabilities': capabilities,
                'status': 'available',
                'last_seen': datetime.now().isoformat()
            }
            
            return True
        except Exception as e:
            logger.info(f"[AI Collaboration] 注册员工失败: {e}")
            return False
    
    def get_available_workers(self):
        try:
            conn = sqlite3.connect('ai_collaboration.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM registered_workers WHERE status = ?', ('available',))
            rows = cursor.fetchall()
            conn.close()
            
            workers = []
            for row in rows:
                workers.append({
                    'worker_id': row[1],
                    'worker_name': row[2],
                    'capabilities': json.loads(row[3]) if row[3] else [],
                    'status': row[4],
                    'avg_score': row[6]
                })
            
            return workers
        except Exception as e:
            logger.info(f"[AI Collaboration] 获取可用员工失败: {e}")
            return []
    
    def get_session_tasks(self, session_id):
        try:
            conn = sqlite3.connect('ai_collaboration.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM collaboration_tasks WHERE session_id = ? ORDER BY priority DESC, assigned_at ASC', (session_id,))
            rows = cursor.fetchall()
            conn.close()
            
            tasks = []
            for row in rows:
                tasks.append({
                    'task_id': row[1],
                    'worker_id': row[3],
                    'worker_name': row[4],
                    'task_type': row[5],
                    'task_content': row[6],
                    'status': row[7],
                    'priority': row[8],
                    'assigned_at': row[9],
                    'started_at': row[10],
                    'completed_at': row[11],
                    'result': row[12],
                    'score': row[13]
                })
            
            return tasks
        except Exception as e:
            logger.info(f"[AI Collaboration] 获取会话任务失败: {e}")
            return []
    
    def get_session_info(self, session_id):
        try:
            conn = sqlite3.connect('ai_collaboration.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM collaboration_sessions WHERE session_id = ?', (session_id,))
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return None
            
            session_info = {
                'session_id': row[1],
                'session_name': row[2],
                'purpose': row[3],
                'status': row[4],
                'created_by': row[5],
                'created_at': row[6],
                'completed_at': row[7]
            }
            
            cursor.execute('SELECT COUNT(*) FROM collaboration_tasks WHERE session_id = ?', (session_id,))
            total = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM collaboration_tasks WHERE session_id = ? AND status = ?', (session_id,
            'completed'))
            completed = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM knowledge_sharing WHERE session_id = ?', (session_id,))
            knowledge_count = cursor.fetchone()[0]
            
            conn.close()
            
            session_info['total_tasks'] = total
            session_info['completed_tasks'] = completed
            session_info['knowledge_shared'] = knowledge_count
            session_info['progress'] = (completed / total * 100) if total > 0 else 0
            
            return session_info
        except Exception as e:
            logger.info(f"[AI Collaboration] 获取会话信息失败: {e}")
            return None
    
    def get_all_sessions(self):
        try:
            conn = sqlite3.connect('ai_collaboration.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM collaboration_sessions ORDER BY created_at DESC')
            rows = cursor.fetchall()
            conn.close()
            
            sessions = []
            for row in rows:
                sessions.append({
                    'session_id': row[1],
                    'session_name': row[2],
                    'purpose': row[3],
                    'status': row[4],
                    'created_by': row[5],
                    'created_at': row[6]
                })
            
            return sessions
        except Exception as e:
            logger.info(f"[AI Collaboration] 获取所有会话失败: {e}")
            return []
    
    def get_session_knowledge(self, session_id):
        try:
            conn = sqlite3.connect('ai_collaboration.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM knowledge_sharing WHERE session_id = ? ORDER BY relevance_score DESC',
            (session_id,))
            rows = cursor.fetchall()
            conn.close()
            
            knowledge = []
            for row in rows:
                knowledge.append({
                    'knowledge_type': row[3],
                    'knowledge_content': row[4],
                    'worker_id': row[2],
                    'shared_at': row[5],
                    'relevance_score': row[6]
                })
            
            return knowledge
        except Exception as e:
            logger.info(f"[AI Collaboration] 获取会话知识失败: {e}")
            return []
    
    def _record_history(self, session_id, action_type, action_content, actor_id):
        try:
            conn = sqlite3.connect('ai_collaboration.db')
            cursor = conn.cursor()
            cursor.execute(''' INSERT INTO collaboration_history (session_id, action_type, action_content, actor_id) VALUES (?, ?, ?, ?) ''', (session_id, action_type, action_content, actor_id))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"[AI Collaboration] 记录历史失败: {e}")

collaboration_system = AICollaborationSystem()