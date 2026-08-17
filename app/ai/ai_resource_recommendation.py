#!/usr/bin/env python3
import os
import json
import sqlite3
import threading
import hashlib
import random
from datetime import datetime
from collections import defaultdict

class AIResourceRecommendation:
    RESOURCE_TYPES = ['video', 'article', 'exercise', 'quiz', 'document', 'course', 'tutorial', 'video_lecture']
    RECOMMENDATION_STRATEGIES = ['collaborative_filtering', 'content_based', 'hybrid', 'context_aware',
    'knowledge_based']
    RECOMMENDATION_STATUS = ['pending', 'generated', 'delivered', 'accepted', 'rejected']
    
    def __init__(self):
        self.recommendation_cache = {}
        self._lock = threading.Lock()
        self._create_tables()
    
    def _create_tables(self):
        try:
            conn = sqlite3.connect('ai_recommendation.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS resources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resource_id TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    subject TEXT,
                    category TEXT,
                    difficulty INTEGER DEFAULT 1,
                    duration REAL DEFAULT 0.0,
                    rating REAL DEFAULT 0.0,
                    views INTEGER DEFAULT 0,
                    likes INTEGER DEFAULT 0,
                    tags TEXT,
                    description TEXT,
                    url TEXT,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS recommendation_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL UNIQUE,
                    user_id TEXT NOT NULL,
                    strategy TEXT DEFAULT 'hybrid',
                    count INTEGER DEFAULT 10,
                    status TEXT DEFAULT 'pending',
                    recommendations TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    delivered_at TEXT,
                    metadata TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS resource_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    interaction_id TEXT NOT NULL UNIQUE,
                    user_id TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    duration REAL DEFAULT 0.0,
                    rating INTEGER DEFAULT 0,
                    completed BOOLEAN DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profile_id TEXT NOT NULL UNIQUE,
                    user_id TEXT NOT NULL UNIQUE,
                    preferred_types TEXT,
                    preferred_subjects TEXT,
                    skill_level TEXT DEFAULT 'beginner',
                    learning_goals TEXT,
                    interests TEXT,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS recommendation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    rank INTEGER NOT NULL,
                    score REAL DEFAULT 0.0,
                    strategy TEXT,
                    delivered BOOLEAN DEFAULT 0,
                    accepted BOOLEAN DEFAULT 0,
                    feedback TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"[AI Resource Recommendation] 创建表失败: {e}")
    
    def _generate_id(self, prefix):
        return prefix + '_' + hashlib.md5((str(datetime.now().timestamp()) + str(random.random())).encode()).hexdigest(
        )[:16]
    
    def add_resource(self, title, resource_type, subject=None, category=None, difficulty=1, 
                     duration=0.0, rating=0.0, tags=None, description='', url=''):
        resource_id = self._generate_id('resource')
        
        try:
            conn = sqlite3.connect('ai_recommendation.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO resources 
                (resource_id, title, resource_type, subject, category, difficulty, duration, 
                 rating, tags, description, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (resource_id, title, resource_type, subject, category, difficulty, duration,
                  rating, json.dumps(tags or []), description, url))
            conn.commit()
            conn.close()
            
            return {'success': True, 'resource_id': resource_id}
        except Exception as e:
            logger.info(f"[AI Resource Recommendation] 添加资源失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_resource(self, resource_id):
        try:
            conn = sqlite3.connect('ai_recommendation.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM resources WHERE resource_id = ?', (resource_id,))
            row = cursor.fetchone()
            
            if row:
                result = dict(row)
                result['tags'] = json.loads(result.get('tags', '[]'))
                return result
            
            conn.close()
            return None
        except Exception as e:
            logger.info(f"[AI Resource Recommendation] 获取资源失败: {e}")
            return None
    
    def search_resources(self, query='', subject=None, resource_type=None, difficulty=None, limit=20):
        try:
            conn = sqlite3.connect('ai_recommendation.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            conditions = []
            params = []
            
            if query:
                conditions.append('(title LIKE ? OR description LIKE ? OR category LIKE ?)')
                params.extend(['%' + query + '%', '%' + query + '%', '%' + query + '%'])
            
            if subject:
                conditions.append('subject = ?')
                params.append(subject)
            
            if resource_type:
                conditions.append('resource_type = ?')
                params.append(resource_type)
            
            if difficulty:
                conditions.append('difficulty = ?')
                params.append(difficulty)
            
            params.append(limit)
            
            query_str = 'SELECT * FROM resources'
            if conditions:
                query_str += ' WHERE ' + ' AND '.join(conditions)
            query_str += ' ORDER BY rating DESC, views DESC LIMIT ?'
            
            cursor.execute(query_str, params)
            
            results = []
            for row in cursor.fetchall():
                resource = dict(row)
                resource['tags'] = json.loads(resource.get('tags', '[]'))
                results.append(resource)
            
            conn.close()
            return results
        except Exception as e:
            logger.info(f"[AI Resource Recommendation] 搜索资源失败: {e}")
            return []
    
    def record_interaction(self, user_id, resource_id, action, duration=0.0, rating=0, completed=False):
        interaction_id = self._generate_id('interaction')
        
        try:
            conn = sqlite3.connect('ai_recommendation.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO resource_interactions 
                (interaction_id, user_id, resource_id, action, duration, rating, completed)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (interaction_id, user_id, resource_id, action, duration, rating, completed))
            
            if action == 'view':
                cursor.execute('UPDATE resources SET views = views + 1 WHERE resource_id = ?', (resource_id,))
            elif action == 'like':
                cursor.execute('UPDATE resources SET likes = likes + 1 WHERE resource_id = ?', (resource_id,))
            elif action == 'rate':
                cursor.execute('''
                    UPDATE resources 
                    SET rating = (rating * (views - 1) + ?) / views 
                    WHERE resource_id = ?
                ''', (rating, resource_id))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'interaction_id': interaction_id}
        except Exception as e:
            logger.info(f"[AI Resource Recommendation] 记录交互失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_or_create_profile(self, user_id):
        try:
            conn = sqlite3.connect('ai_recommendation.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM user_profiles WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            
            if row:
                conn.close()
                result = dict(row)
                result['preferred_types'] = json.loads(result.get('preferred_types', '[]'))
                result['preferred_subjects'] = json.loads(result.get('preferred_subjects', '[]'))
                result['learning_goals'] = json.loads(result.get('learning_goals', '[]'))
                result['interests'] = json.loads(result.get('interests', '[]'))
                return result
            
            profile_id = self._generate_id('profile')
            cursor.execute('''
                INSERT INTO user_profiles 
                (profile_id, user_id, skill_level)
                VALUES (?, ?, ?)
            ''', (profile_id, user_id, 'beginner'))
            conn.commit()
            conn.close()
            
            return {'profile_id': profile_id, 'user_id': user_id, 'skill_level': 'beginner',
                    'preferred_types': [], 'preferred_subjects': [], 'learning_goals': [], 'interests': []}
        except Exception as e:
            logger.info(f"[AI Resource Recommendation] 获取或创建用户档案失败: {e}")
            return None
    
    def update_profile(self, user_id, updates):
        try:
            conn = sqlite3.connect('ai_recommendation.db')
            cursor = conn.cursor()
            
            set_clause = []
            params = []
            
            for key, value in updates.items():
                if key in ['preferred_types', 'preferred_subjects', 'skill_level', 'learning_goals', 'interests',
                'metadata']:
                    if isinstance(value, list):
                        set_clause.append(f"{key} = ?")
                        params.append(json.dumps(value))
                    else:
                        set_clause.append(f"{key} = ?")
                        params.append(value)
            
            if set_clause:
                params.append(user_id)
                cursor.execute(f'''
                    UPDATE user_profiles SET {', '.join(set_clause)}, updated_at = ?
                    WHERE user_id = ?
                ''', params + [datetime.now().isoformat()])
                conn.commit()
            
            conn.close()
            return {'success': True}
        except Exception as e:
            logger.info(f"[AI Resource Recommendation] 更新用户档案失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_recommendations(self, user_id, count=10, strategy='hybrid'):
        task_id = self._generate_id('rec')
        
        try:
            conn = sqlite3.connect('ai_recommendation.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO recommendation_tasks 
                (task_id, user_id, strategy, count, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (task_id, user_id, strategy, count, 'generated'))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"[AI Resource Recommendation] 创建推荐任务失败: {e}")
        
        profile = self.get_or_create_profile(user_id)
        
        recommendations = []
        scores = []
        
        if strategy == 'content_based' or strategy == 'hybrid':
            content_recs = self._content_based_recommendation(user_id, profile, count)
            recommendations.extend(content_recs)
            scores.extend([0.8] * len(content_recs))
        
        if strategy == 'collaborative_filtering' or strategy == 'hybrid':
            collab_recs = self._collaborative_filtering_recommendation(user_id, count)
            recommendations.extend(collab_recs)
            scores.extend([0.7] * len(collab_recs))
        
        if strategy == 'context_aware' or strategy == 'hybrid':
            context_recs = self._context_aware_recommendation(user_id, profile, count)
            recommendations.extend(context_recs)
            scores.extend([0.9] * len(context_recs))
        
        if strategy == 'knowledge_based' or strategy == 'hybrid':
            knowledge_recs = self._knowledge_based_recommendation(user_id, profile, count)
            recommendations.extend(knowledge_recs)
            scores.extend([0.85] * len(knowledge_recs))
        
        ranked_recs = self._rank_recommendations(recommendations, scores, count)
        
        try:
            conn = sqlite3.connect('ai_recommendation.db')
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE recommendation_tasks 
                SET recommendations = ?, delivered_at = ?
                WHERE task_id = ?
            ''', (json.dumps(ranked_recs), datetime.now().isoformat(), task_id))
            
            for i, rec in enumerate(ranked_recs):
                cursor.execute('''
                    INSERT INTO recommendation_history 
                    (task_id, resource_id, rank, score, strategy)
                    VALUES (?, ?, ?, ?, ?)
                ''', (task_id, rec['resource_id'], i + 1, rec.get('score', 0.0), strategy))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"[AI Resource Recommendation] 保存推荐结果失败: {e}")
        
        self.recommendation_cache[task_id] = ranked_recs
        
        return {
            'success': True,
            'task_id': task_id,
            'user_id': user_id,
            'strategy': strategy,
            'recommendations': ranked_recs,
            'count': len(ranked_recs),
            'generated_at': datetime.now().isoformat()
        }
    
    def _content_based_recommendation(self, user_id, profile, count):
        preferred_types = profile.get('preferred_types', [])
        preferred_subjects = profile.get('preferred_subjects', [])
        interests = profile.get('interests', [])
        
        resources = self.search_resources()
        
        scored_resources = []
        for resource in resources:
            score = 0.0
            
            if resource['resource_type'] in preferred_types:
                score += 0.3
            
            if resource['subject'] in preferred_subjects:
                score += 0.3
            
            resource_tags = resource.get('tags', [])
            for interest in interests:
                if interest in resource_tags:
                    score += 0.1
            
            if score > 0:
                resource['score'] = score
                scored_resources.append(resource)
        
        scored_resources.sort(key=lambda x: x['score'], reverse=True)
        return scored_resources[:count]
    
    def _collaborative_filtering_recommendation(self, user_id, count):
        try:
            conn = sqlite3.connect('ai_recommendation.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT resource_id, action FROM resource_interactions 
                WHERE user_id = ? AND action IN ('like', 'rate', 'completed')
            ''', (user_id,))
            user_actions = [dict(row) for row in cursor.fetchall()]
            
            if not user_actions:
                conn.close()
                return []
            
            user_liked_resources = {a['resource_id'] for a in user_actions}
            
            cursor.execute('''
                SELECT user_id FROM resource_interactions 
                WHERE resource_id IN ({}) AND user_id != ?
                GROUP BY user_id 
                HAVING COUNT(DISTINCT resource_id) >= ?
            '''.format(','.join('?' * len(user_liked_resources))), 
                          list(user_liked_resources) + [user_id, min(2, len(user_liked_resources))])
            
            similar_users = [row['user_id'] for row in cursor.fetchall()]
            
            if not similar_users:
                conn.close()
                return []
            
            cursor.execute('''
                SELECT resource_id, COUNT(*) as cnt 
                FROM resource_interactions 
                WHERE user_id IN ({}) AND action IN ('like', 'completed')
                AND resource_id NOT IN ({})
                GROUP BY resource_id 
                ORDER BY cnt DESC LIMIT ?
            '''.format(','.join('?' * len(similar_users)), ','.join('?' * len(user_liked_resources))),
                          similar_users + list(user_liked_resources) + [count])
            
            recommended_resource_ids = [row['resource_id'] for row in cursor.fetchall()]
            
            recommendations = []
            for resource_id in recommended_resource_ids:
                resource = self.get_resource(resource_id)
                if resource:
                    resource['score'] = 0.7
                    recommendations.append(resource)
            
            conn.close()
            return recommendations
        except Exception as e:
            logger.info(f"[AI Resource Recommendation] 协同过滤推荐失败: {e}")
            return []
    
    def _context_aware_recommendation(self, user_id, profile, count):
        try:
            from app.ai.ai_adaptive_learning import ai_adaptive_learning
            
            gaps_result = ai_adaptive_learning.detect_knowledge_gaps(user_id)
            gaps = gaps_result.get('gaps', [])
            
            gap_topics = [gap['topic'] for gap in gaps[:5]]
            
            resources = self.search_resources()
            
            scored_resources = []
            for resource in resources:
                score = 0.5
                
                for topic in gap_topics:
                    if topic.lower() in resource['title'].lower() or topic.lower() in resource.get('description',
                    '').lower():
                        score += 0.2
                
                difficulty = resource['difficulty']
                if difficulty <= 2:
                    score += 0.1
                
                if score > 0.5:
                    resource['score'] = score
                    scored_resources.append(resource)
            
            scored_resources.sort(key=lambda x: x['score'], reverse=True)
            return scored_resources[:count]
        except Exception as e:
            logger.info(f"[AI Resource Recommendation] 上下文感知推荐失败: {e}")
            return []
    
    def _knowledge_based_recommendation(self, user_id, profile, count):
        try:
            from app.ai.ai_cognitive_reasoning import ai_cognitive_reasoning
            
            interests = profile.get('interests', [])
            
            knowledge_results = []
            for interest in interests[:5]:
                results = ai_cognitive_reasoning.search_knowledge(interest, limit=3)
                knowledge_results.extend(results)
            
            knowledge_topics = {kb['topic'] for kb in knowledge_results}
            
            resources = self.search_resources()
            
            scored_resources = []
            for resource in resources:
                score = 0.5
                
                for topic in knowledge_topics:
                    if topic.lower() in resource['title'].lower():
                        score += 0.15
                
                resource_tags = resource.get('tags', [])
                for interest in interests:
                    if interest in resource_tags:
                        score += 0.1
                
                if score > 0.5:
                    resource['score'] = score
                    scored_resources.append(resource)
            
            scored_resources.sort(key=lambda x: x['score'], reverse=True)
            return scored_resources[:count]
        except Exception as e:
            logger.info(f"[AI Resource Recommendation] 基于知识推荐失败: {e}")
            return []
    
    def _rank_recommendations(self, recommendations, scores, count):
        resource_scores = defaultdict(float)
        resource_counts = defaultdict(int)
        
        for i, rec in enumerate(recommendations):
            resource_id = rec['resource_id']
            resource_scores[resource_id] += scores[i] * rec.get('score', 0.5)
            resource_counts[resource_id] += 1
        
        for resource_id in resource_scores:
            resource_scores[resource_id] /= resource_counts[resource_id]
        
        unique_resources = {}
        for rec in recommendations:
            if rec['resource_id'] not in unique_resources:
                unique_resources[rec['resource_id']] = rec
        
        ranked = []
        for resource_id in sorted(resource_scores.keys(), key=lambda x: resource_scores[x], reverse=True):
            resource = unique_resources[resource_id]
            resource['score'] = round(resource_scores[resource_id], 2)
            ranked.append(resource)
        
        return ranked[:count]
    
    def get_recommendation_task(self, task_id):
        try:
            conn = sqlite3.connect('ai_recommendation.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM recommendation_tasks WHERE task_id = ?', (task_id,))
            row = cursor.fetchone()
            
            if row:
                result = dict(row)
                result['recommendations'] = json.loads(result.get('recommendations', '[]'))
                return result
            
            conn.close()
            return None
        except Exception as e:
            logger.info(f"[AI Resource Recommendation] 获取推荐任务失败: {e}")
            return None
    
    def list_recommendation_tasks(self, user_id=None, limit=20):
        try:
            conn = sqlite3.connect('ai_recommendation.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute('SELECT * FROM recommendation_tasks WHERE user_id = ? ORDER BY created_at DESC LIMIT ?',
                (user_id, limit))
            else:
                cursor.execute('SELECT * FROM recommendation_tasks ORDER BY created_at DESC LIMIT ?', (limit,))
            
            results = []
            for row in cursor.fetchall():
                task = dict(row)
                task['recommendations'] = json.loads(task.get('recommendations', '[]'))
                results.append(task)
            
            conn.close()
            return results
        except Exception as e:
            logger.info(f"[AI Resource Recommendation] 列出推荐任务失败: {e}")
            return []
    
    def submit_feedback(self, task_id, resource_id, accepted, feedback=''):
        try:
            conn = sqlite3.connect('ai_recommendation.db')
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE recommendation_history 
                SET accepted = ?, feedback = ?
                WHERE task_id = ? AND resource_id = ?
            ''', (accepted, feedback, task_id, resource_id))
            
            if accepted:
                cursor.execute('UPDATE resources SET likes = likes + 1 WHERE resource_id = ?', (resource_id,))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'message': '反馈已提交'}
        except Exception as e:
            logger.info(f"[AI Resource Recommendation] 提交反馈失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_recommendation_statistics(self):
        try:
            conn = sqlite3.connect('ai_recommendation.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM resources')
            total_resources = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM recommendation_tasks')
            total_tasks = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM resource_interactions')
            total_interactions = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM user_profiles')
            total_profiles = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM recommendation_history WHERE accepted = 1')
            accepted_recommendations = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM recommendation_history')
            total_recommendations = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT resource_type, COUNT(*) as count FROM resources GROUP BY resource_type
            ''')
            type_stats = []
            for row in cursor.fetchall():
                type_stats.append({
                    'resource_type': row[0],
                    'count': row[1]
                })
            
            cursor.execute('''
                SELECT subject, COUNT(*) as count FROM resources GROUP BY subject ORDER BY count DESC LIMIT 5
            ''')
            subject_stats = []
            for row in cursor.fetchall():
                subject_stats.append({
                    'subject': row[0],
                    'count': row[1]
                })
            
            conn.close()
            
            return {
                'total_resources': total_resources,
                'total_tasks': total_tasks,
                'total_interactions': total_interactions,
                'total_profiles': total_profiles,
                'accepted_recommendations': accepted_recommendations,
                'acceptance_rate': round(accepted_recommendations / total_recommendations * 100,
                2) if total_recommendations > 0 else 0.0,
                'type_statistics': type_stats,
                'subject_statistics': subject_stats
            }
        except Exception as e:
            logger.info(f"[AI Resource Recommendation] 获取统计信息失败: {e}")
            return {
                'total_resources': 0,
                'total_tasks': 0,
                'total_interactions': 0,
                'total_profiles': 0,
                'accepted_recommendations': 0,
                'acceptance_rate': 0.0,
                'type_statistics': [],
                'subject_statistics': []
            }

ai_resource_recommendation = AIResourceRecommendation()