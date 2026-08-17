#!/usr/bin/env python3
import os
import json
import sqlite3
import threading
import hashlib
import random
from datetime import datetime, timedelta
from collections import defaultdict

class AIAdaptiveLearning:
    LEARNING_STYLES = ['visual', 'auditory', 'reading', 'kinesthetic']
    KNOWLEDGE_LEVELS = ['novice', 'beginner', 'intermediate', 'advanced', 'expert']
    LEARNING_STATES = ['learning', 'practicing', 'reviewing', 'testing', 'mastered']
    
    def __init__(self):
        self.learning_profiles = {}
        self._lock = threading.Lock()
        self._create_tables()
    
    def _create_tables(self):
        try:
            conn = sqlite3.connect('ai_adaptive_learning.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profile_id TEXT NOT NULL UNIQUE,
                    user_id TEXT NOT NULL,
                    learning_style TEXT DEFAULT 'visual',
                    knowledge_level TEXT DEFAULT 'novice',
                    learning_speed REAL DEFAULT 1.0,
                    preferred_subjects TEXT,
                    weak_subjects TEXT,
                    learning_history TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_paths (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path_id TEXT NOT NULL UNIQUE,
                    user_id TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    objectives TEXT,
                    current_progress REAL DEFAULT 0.0,
                    estimated_time REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'active',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_steps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    step_id TEXT NOT NULL UNIQUE,
                    path_id TEXT NOT NULL,
                    step_number INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    type TEXT NOT NULL,
                    duration REAL DEFAULT 0.0,
                    difficulty REAL DEFAULT 1.0,
                    completed BOOLEAN DEFAULT 0,
                    score REAL DEFAULT 0.0,
                    feedback TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    interaction_id TEXT NOT NULL UNIQUE,
                    user_id TEXT NOT NULL,
                    subject TEXT,
                    action TEXT NOT NULL,
                    content TEXT,
                    duration REAL DEFAULT 0.0,
                    success BOOLEAN DEFAULT 0,
                    score REAL DEFAULT 0.0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_gaps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    gap_id TEXT NOT NULL UNIQUE,
                    user_id TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    gap_level INTEGER DEFAULT 1,
                    suggested_actions TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recommendation_id TEXT NOT NULL UNIQUE,
                    user_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    priority INTEGER DEFAULT 1,
                    accepted BOOLEAN DEFAULT 0,
                    implemented BOOLEAN DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    accepted_at TEXT,
                    implemented_at TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"[AI Adaptive Learning] 创建表失败: {e}")
    
    def _generate_id(self, prefix):
        return prefix + '_' + hashlib.md5((str(datetime.now().timestamp()) + str(random.random())).encode()).hexdigest(
        )[:16]
    
    def get_or_create_profile(self, user_id):
        try:
            conn = sqlite3.connect('ai_adaptive_learning.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM learning_profiles WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            
            if row:
                conn.close()
                return dict(row)
            
            profile_id = self._generate_id('profile')
            cursor.execute('''
                INSERT INTO learning_profiles 
                (profile_id, user_id, learning_style, knowledge_level, learning_speed)
                VALUES (?, ?, ?, ?, ?)
            ''', (profile_id, user_id, 'visual', 'novice', 1.0))
            conn.commit()
            conn.close()
            
            return {'profile_id': profile_id, 'user_id': user_id, 'learning_style': 'visual',
            'knowledge_level': 'novice', 'learning_speed': 1.0}
        except Exception as e:
            logger.info(f"[AI Adaptive Learning] 获取或创建学习档案失败: {e}")
            return None
    
    def update_profile(self, user_id, updates):
        try:
            conn = sqlite3.connect('ai_adaptive_learning.db')
            cursor = conn.cursor()
            
            set_clause = []
            params = []
            for key, value in updates.items():
                if key in ['learning_style', 'knowledge_level', 'learning_speed', 'preferred_subjects', 'weak_subjects',
                'learning_history', 'metadata']:
                    set_clause.append(f"{key} = ?")
                    params.append(value)
            
            params.append(user_id)
            
            if set_clause:
                cursor.execute(f'''
                    UPDATE learning_profiles SET {', '.join(set_clause)}, updated_at = ?
                    WHERE user_id = ?
                ''', params + [datetime.now().isoformat()])
                conn.commit()
            
            conn.close()
            return {'success': True}
        except Exception as e:
            logger.info(f"[AI Adaptive Learning] 更新学习档案失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def analyze_learning_style(self, user_id, interactions):
        style_scores = {'visual': 0, 'auditory': 0, 'reading': 0, 'kinesthetic': 0}
        
        for interaction in interactions:
            action = interaction.get('action', '')
            content = interaction.get('content', '')
            
            if any(keyword in action.lower() for keyword in ['view', 'watch', 'see', 'visual', 'image', 'video']):
                style_scores['visual'] += 1
            elif any(keyword in action.lower() for keyword in ['listen', 'audio', 'hear', 'speak', 'talk']):
                style_scores['auditory'] += 1
            elif any(keyword in action.lower() for keyword in ['read', 'text', 'article', 'document']):
                style_scores['reading'] += 1
            elif any(keyword in action.lower() for keyword in ['practice', 'do', 'exercise', 'solve', 'interact']):
                style_scores['kinesthetic'] += 1
        
        dominant_style = max(style_scores, key=style_scores.get)
        total = sum(style_scores.values())
        
        if total > 0:
            for style in style_scores:
                style_scores[style] = style_scores[style] / total
        
        self.update_profile(user_id, {'learning_style': dominant_style})
        
        return {
            'success': True,
            'user_id': user_id,
            'learning_style': dominant_style,
            'style_scores': style_scores,
            'explanation': f'基于{len(interactions)}次学习交互分析，识别出主导学习风格为{dominant_style}'
        }
    
    def create_learning_path(self, user_id, subject, objectives):
        path_id = self._generate_id('path')
        
        try:
            conn = sqlite3.connect('ai_adaptive_learning.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO learning_paths 
                (path_id, user_id, subject, objectives, estimated_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (path_id, user_id, subject, json.dumps(objectives), len(objectives) * 30))
            conn.commit()
            conn.close()
            
            steps = self._generate_learning_steps(path_id, subject, objectives)
            
            return {
                'success': True,
                'path_id': path_id,
                'subject': subject,
                'objectives': objectives,
                'steps': steps
            }
        except Exception as e:
            logger.info(f"[AI Adaptive Learning] 创建学习路径失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def _generate_learning_steps(self, path_id, subject, objectives):
        steps = []
        
        for i, objective in enumerate(objectives):
            step_id = self._generate_id('step')
            step_type = 'learning' if i < len(objectives) - 1 else 'testing'
            
            try:
                conn = sqlite3.connect('ai_adaptive_learning.db')
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO learning_steps 
                    (step_id, path_id, step_number, content, type, difficulty, duration)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    step_id, path_id, i + 1,
                    f"学习目标: {objective}",
                    step_type,
                    min(5, i + 1),
                    20 + i * 5
                ))
                conn.commit()
                conn.close()
                
                steps.append({
                    'step_id': step_id,
                    'step_number': i + 1,
                    'content': objective,
                    'type': step_type,
                    'difficulty': min(5, i + 1),
                    'duration': 20 + i * 5
                })
            except Exception as e:
                logger.info(f"[AI Adaptive Learning] 创建学习步骤失败: {e}")
        
        return steps
    
    def update_learning_progress(self, user_id, path_id, step_id, score=None, completed=False):
        try:
            conn = sqlite3.connect('ai_adaptive_learning.db')
            cursor = conn.cursor()
            
            if completed:
                cursor.execute('''
                    UPDATE learning_steps 
                    SET completed = 1, completed_at = ?, score = ?
                    WHERE step_id = ?
                ''', (datetime.now().isoformat(), score or 0.0, step_id))
            elif score:
                cursor.execute('''
                    UPDATE learning_steps 
                    SET score = ?
                    WHERE step_id = ?
                ''', (score, step_id))
            
            conn.commit()
            
            cursor.execute('''
                SELECT COUNT(*) as total, SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed
                FROM learning_steps WHERE path_id = ?
            ''', (path_id,))
            row = cursor.fetchone()
            total_steps = row['total']
            completed_steps = row['completed'] or 0
            
            progress = completed_steps / total_steps if total_steps > 0 else 0.0
            
            cursor.execute('''
                UPDATE learning_paths 
                SET current_progress = ?, updated_at = ?
                WHERE path_id = ?
            ''', (progress, datetime.now().isoformat(), path_id))
            
            if progress >= 1.0:
                cursor.execute('''
                    UPDATE learning_paths 
                    SET status = ?, completed_at = ?
                    WHERE path_id = ?
                ''', ('completed', datetime.now().isoformat(), path_id))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'path_id': path_id,
                'progress': round(progress * 100, 2),
                'completed_steps': completed_steps,
                'total_steps': total_steps
            }
        except Exception as e:
            logger.info(f"[AI Adaptive Learning] 更新学习进度失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def detect_knowledge_gaps(self, user_id, subject=None):
        gaps = []
        
        try:
            conn = sqlite3.connect('ai_adaptive_learning.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if subject:
                cursor.execute('''
                    SELECT * FROM learning_interactions 
                    WHERE user_id = ? AND subject = ? AND success = 0
                    ORDER BY created_at DESC LIMIT 20
                ''', (user_id, subject))
            else:
                cursor.execute('''
                    SELECT * FROM learning_interactions 
                    WHERE user_id = ? AND success = 0
                    ORDER BY created_at DESC LIMIT 30
                ''', (user_id,))
            
            failed_interactions = [dict(row) for row in cursor.fetchall()]
            
            topic_failures = defaultdict(int)
            for interaction in failed_interactions:
                content = interaction.get('content', '')
                topic = content[:50] if len(content) > 50 else content
                topic_failures[topic] += 1
            
            for topic, count in sorted(topic_failures.items(), key=lambda x: x[1], reverse=True)[:5]:
                gap_id = self._generate_id('gap')
                gap_level = min(5, count)
                
                cursor.execute('''
                    INSERT OR IGNORE INTO knowledge_gaps 
                    (gap_id, user_id, subject, topic, gap_level, suggested_actions)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    gap_id, user_id, subject or 'general',
                    topic, gap_level,
                    json.dumps([f"复习相关知识点: {topic}", "增加练习次数", "查看讲解视频"])
                ))
                
                gaps.append({
                    'gap_id': gap_id,
                    'topic': topic,
                    'gap_level': gap_level,
                    'fail_count': count,
                    'suggested_actions': [f"复习相关知识点: {topic}", "增加练习次数", "查看讲解视频"]
                })
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"[AI Adaptive Learning] 检测知识漏洞失败: {e}")
        
        return {
            'success': True,
            'user_id': user_id,
            'gaps_found': len(gaps),
            'gaps': gaps
        }
    
    def generate_recommendations(self, user_id):
        recommendations = []
        
        try:
            conn = sqlite3.connect('ai_adaptive_learning.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM learning_profiles WHERE user_id = ?', (user_id,))
            profile = cursor.fetchone()
            
            if profile:
                learning_style = profile['learning_style']
                
                recommendations.append({
                    'type': 'learning_style',
                    'content': f"根据您的学习风格({learning_style})，建议使用视觉化学习材料",
                    'priority': 1
                })
            
            cursor.execute('SELECT * FROM knowledge_gaps WHERE user_id = ? AND status = ?', (user_id, 'active'))
            gaps = cursor.fetchall()
            
            for gap in gaps:
                recommendations.append({
                    'type': 'knowledge_gap',
                    'content': f"检测到知识漏洞: {gap['topic']}，建议进行针对性复习",
                    'priority': gap['gap_level']
                })
            
            cursor.execute('''
                SELECT subject, COUNT(*) as count 
                FROM learning_interactions 
                WHERE user_id = ? 
                GROUP BY subject 
                ORDER BY count DESC LIMIT 3
            ''', (user_id,))
            top_subjects = cursor.fetchall()
            
            for subject in top_subjects:
                recommendations.append({
                    'type': 'practice',
                    'content': f"您最近在{subject['subject']}上学习较多，建议继续深入学习",
                    'priority': 2
                })
            
            for rec in recommendations[:10]:
                rec_id = self._generate_id('rec')
                cursor.execute('''
                    INSERT INTO learning_recommendations 
                    (recommendation_id, user_id, type, content, priority)
                    VALUES (?, ?, ?, ?, ?)
                ''', (rec_id, user_id, rec['type'], rec['content'], rec['priority']))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"[AI Adaptive Learning] 生成推荐失败: {e}")
        
        return {
            'success': True,
            'user_id': user_id,
            'recommendations_count': len(recommendations),
            'recommendations': recommendations
        }
    
    def record_interaction(self, user_id, subject, action, content='', duration=0.0, success=False, score=0.0):
        interaction_id = self._generate_id('interaction')
        
        try:
            conn = sqlite3.connect('ai_adaptive_learning.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO learning_interactions 
                (interaction_id, user_id, subject, action, content, duration, success, score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (interaction_id, user_id, subject, action, content, duration, success, score))
            conn.commit()
            conn.close()
            
            self.analyze_learning_style(user_id, [{
                'action': action,
                'content': content
            }])
            
            return {'success': True, 'interaction_id': interaction_id}
        except Exception as e:
            logger.info(f"[AI Adaptive Learning] 记录交互失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_learning_path(self, path_id):
        try:
            conn = sqlite3.connect('ai_adaptive_learning.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM learning_paths WHERE path_id = ?', (path_id,))
            path = cursor.fetchone()
            
            if not path:
                conn.close()
                return None
            
            cursor.execute('SELECT * FROM learning_steps WHERE path_id = ? ORDER BY step_number', (path_id,))
            steps = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            
            result = dict(path)
            result['objectives'] = json.loads(result.get('objectives', '[]'))
            result['steps'] = steps
            
            return result
        except Exception as e:
            logger.info(f"[AI Adaptive Learning] 获取学习路径失败: {e}")
            return None
    
    def get_user_paths(self, user_id):
        try:
            conn = sqlite3.connect('ai_adaptive_learning.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM learning_paths WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
            paths = []
            
            for row in cursor.fetchall():
                path = dict(row)
                path['objectives'] = json.loads(path.get('objectives', '[]'))
                paths.append(path)
            
            conn.close()
            return paths
        except Exception as e:
            logger.info(f"[AI Adaptive Learning] 获取用户学习路径失败: {e}")
            return []
    
    def get_learning_statistics(self, user_id=None):
        try:
            conn = sqlite3.connect('ai_adaptive_learning.db')
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute('SELECT COUNT(*) FROM learning_paths WHERE user_id = ?', (user_id,))
                total_paths = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM learning_paths WHERE user_id = ? AND status = ?', (user_id,
                'completed'))
                completed_paths = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM learning_interactions WHERE user_id = ?', (user_id,))
                total_interactions = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM learning_interactions WHERE user_id = ? AND success = 1', (user_id,
                ))
                successful_interactions = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM knowledge_gaps WHERE user_id = ? AND status = ?', (user_id,
                'active'))
                active_gaps = cursor.fetchone()[0]
                
                cursor.execute('SELECT AVG(score) FROM learning_steps WHERE user_id = ? AND completed = 1', (user_id,))
                avg_score = cursor.fetchone()[0] or 0.0
            else:
                cursor.execute('SELECT COUNT(*) FROM learning_profiles')
                total_profiles = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM learning_paths')
                total_paths = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM learning_paths WHERE status = ?', ('completed',))
                completed_paths = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM learning_interactions')
                total_interactions = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM learning_interactions WHERE success = 1')
                successful_interactions = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM knowledge_gaps WHERE status = ?', ('active',))
                active_gaps = cursor.fetchone()[0]
                
                avg_score = 0.0
            
            conn.close()
            
            return {
                'total_profiles': total_profiles if not user_id else None,
                'total_paths': total_paths,
                'completed_paths': completed_paths,
                'path_completion_rate': round(completed_paths / total_paths * 100, 2) if total_paths > 0 else 0.0,
                'total_interactions': total_interactions,
                'successful_interactions': successful_interactions,
                'success_rate': round(successful_interactions / total_interactions * 100,
                2) if total_interactions > 0 else 0.0,
                'active_gaps': active_gaps,
                'avg_score': round(avg_score, 2)
            }
        except Exception as e:
            logger.info(f"[AI Adaptive Learning] 获取统计信息失败: {e}")
            return {
                'total_profiles': 0,
                'total_paths': 0,
                'completed_paths': 0,
                'path_completion_rate': 0.0,
                'total_interactions': 0,
                'successful_interactions': 0,
                'success_rate': 0.0,
                'active_gaps': 0,
                'avg_score': 0.0
            }

    def create_profile(self, user_id, learning_style=None, subject=None, objectives=None):
        try:
            conn = sqlite3.connect('ai_adaptive_learning.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM learning_profiles WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            
            if row:
                updates = {}
                if learning_style:
                    updates['learning_style'] = learning_style
                if subject:
                    current_subjects = json.loads(row.get('preferred_subjects', '[]'))
                    if subject not in current_subjects:
                        current_subjects.append(subject)
                        updates['preferred_subjects'] = json.dumps(current_subjects)
                
                if updates:
                    set_clause = []
                    params = []
                    for key, value in updates.items():
                        set_clause.append(f"{key} = ?")
                        params.append(value)
                    params.append(user_id)
                    cursor.execute(f'''
                        UPDATE learning_profiles SET {', '.join(set_clause)}, updated_at = ?
                        WHERE user_id = ?
                    ''', params + [datetime.now().isoformat()])
                    conn.commit()
                
                conn.close()
                return {'success': True, 'message': '学习档案已更新'}
            
            profile_id = self._generate_id('profile')
            cursor.execute('''
                INSERT INTO learning_profiles 
                (profile_id, user_id, learning_style, preferred_subjects, learning_history)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                profile_id, user_id, 
                learning_style or 'visual',
                json.dumps([subject]) if subject else '[]',
                json.dumps([{'objective': objectives, 'timestamp': datetime.now().isoformat()}]) if objectives else '[]'
            ))
            conn.commit()
            conn.close()
            
            return {'success': True, 'profile_id': profile_id}
        except Exception as e:
            logger.info(f"[AI Adaptive Learning] 创建学习档案失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def list_profiles(self, limit=50):
        try:
            conn = sqlite3.connect('ai_adaptive_learning.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM learning_profiles ORDER BY created_at DESC LIMIT ?', (limit,))
            
            profiles = []
            for row in cursor.fetchall():
                profile = dict(row)
                profile['preferred_subjects'] = json.loads(profile.get('preferred_subjects', '[]'))
                profiles.append(profile)
            
            conn.close()
            return profiles
        except Exception as e:
            logger.info(f"[AI Adaptive Learning] 列出学习档案失败: {e}")
            return []
    
    def get_user_progress(self, user_id):
        try:
            conn = sqlite3.connect('ai_adaptive_learning.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM learning_paths WHERE user_id = ?', (user_id,))
            paths = [dict(row) for row in cursor.fetchall()]
            
            overall_progress = 0.0
            subject_progress = {}
            
            if paths:
                total_progress = sum(p['current_progress'] for p in paths)
                overall_progress = round(total_progress / len(paths) * 100, 2)
                
                for path in paths:
                    subject = path['subject']
                    if subject not in subject_progress:
                        subject_progress[subject] = []
                    subject_progress[subject].append(path['current_progress'])
                
                for subject in subject_progress:
                    subject_progress[subject] = round(sum(subject_progress[subject]) / len(
                    subject_progress[subject]) * 100, 2)
            
            conn.close()
            
            return {
                'user_id': user_id,
                'overall_progress': overall_progress,
                'subject_progress': subject_progress,
                'total_paths': len(paths)
            }
        except Exception as e:
            logger.info(f"[AI Adaptive Learning] 获取用户进度失败: {e}")
            return {
                'user_id': user_id,
                'overall_progress': 0,
                'subject_progress': {},
                'total_paths': 0
            }

ai_adaptive_learning = AIAdaptiveLearning()