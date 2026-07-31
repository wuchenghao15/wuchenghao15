#!/usr/bin/env python3
import os
import json
import sqlite3
import threading
from datetime import datetime, timedelta
from collections import defaultdict

class AIEmotionAnalysisSystem:
    EMOTION_TYPES = ['happy', 'sad', 'angry', 'anxious', 'confused', 'motivated', 'frustrated', 'bored', 'excited',
    'neutral']
    EMOTION_LEVELS = ['low', 'medium', 'high', 'extreme']
    ANALYSIS_SOURCES = ['text', 'behavior', 'interaction', 'performance', 'survey']
    
    def __init__(self):
        self.emotions = {}
        self._lock = threading.Lock()
        self._create_tables()
    
    def _create_tables(self):
        try:
            conn = sqlite3.connect('emotion_analysis.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS emotion_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_id TEXT NOT NULL UNIQUE,
                    user_id TEXT NOT NULL,
                    emotion_type TEXT NOT NULL,
                    emotion_level TEXT DEFAULT 'medium',
                    confidence REAL DEFAULT 0.0,
                    source TEXT NOT NULL,
                    context TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    duration_minutes INTEGER DEFAULT 0,
                    metadata TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_emotion_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL UNIQUE,
                    baseline_emotion TEXT DEFAULT 'neutral',
                    emotion_pattern TEXT,
                    emotional_triggers TEXT,
                    intervention_history TEXT,
                    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS emotion_interventions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    intervention_id TEXT NOT NULL UNIQUE,
                    user_id TEXT NOT NULL,
                    emotion_type TEXT NOT NULL,
                    intervention_type TEXT NOT NULL,
                    intervention_content TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    executed_at TEXT,
                    effectiveness REAL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS emotion_trends (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    emotion_type TEXT NOT NULL,
                    date TEXT NOT NULL,
                    frequency INTEGER DEFAULT 0,
                    avg_level REAL DEFAULT 0.0,
                    UNIQUE(user_id, emotion_type, date)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS emotion_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT NOT NULL UNIQUE,
                    user_id TEXT NOT NULL,
                    emotion_type TEXT NOT NULL,
                    alert_level TEXT DEFAULT 'warning',
                    threshold_trigger TEXT,
                    message TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("[AI Emotion Analysis] 数据库表创建完成")
        except Exception as e:
            logger.info(f"[AI Emotion Analysis] 创建表失败: {e}")
    
    def detect_emotion(self, user_id, text_content=None, behavior_data=None, source='text'):
        record_id = f"EMO{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        emotion_type, level, confidence = self._analyze_emotion(text_content, behavior_data)
        
        try:
            conn = sqlite3.connect('emotion_analysis.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO emotion_records
                (record_id, user_id, emotion_type, emotion_level, confidence, source, context)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                record_id,
                user_id,
                emotion_type,
                level,
                confidence,
                source,
                json.dumps({'text': text_content, 'behavior': behavior_data}) if text_content or behavior_data else ''
            ))
            
            self._update_emotion_trend(conn, user_id, emotion_type, level)
            self._check_alerts(conn, user_id, emotion_type, level, confidence)
            
            conn.commit()
            conn.close()
            
            self.emotions[record_id] = {
                'user_id': user_id,
                'emotion': emotion_type,
                'level': level,
                'confidence': confidence,
                'timestamp': datetime.now().isoformat()
            }
            
            return {
                'success': True,
                'record_id': record_id,
                'emotion_type': emotion_type,
                'emotion_level': level,
                'confidence': confidence,
                'source': source
            }
        except Exception as e:
            logger.info(f"[AI Emotion Analysis] 检测情感失败: {e}")
            return {'error': str(e)}
    
    def _analyze_emotion(self, text_content, behavior_data):
        text = text_content or ''
        behavior = behavior_data or {}
        
        scores = defaultdict(float)
        
        positive_words = ['高兴', '开心', '快乐', '兴奋', '喜欢', '好', '棒', '优秀', '进步', '成功', '有趣', '轻松']
        negative_words = ['难过', '伤心', '生气', '焦虑', '困惑', '挫败', '烦', '难', '累', '无聊', '压力', '担心']
        anxious_words = ['担心', '焦虑', '紧张', '害怕', '恐惧', '不安', '心慌']
        frustrated_words = ['挫败', '失败', '不行', '不会', '太难', '放弃']
        
        text_lower = text.lower()
        
        for word in positive_words:
            if word in text_lower:
                scores['happy'] += 2
                scores['motivated'] += 1
        
        for word in negative_words:
            if word in text_lower:
                scores['sad'] += 2
                scores['frustrated'] += 1
        
        for word in anxious_words:
            if word in text_lower:
                scores['anxious'] += 3
        
        for word in frustrated_words:
            if word in text_lower:
                scores['frustrated'] += 3
        
        learning_duration = behavior.get('learning_duration', 0)
        if learning_duration > 180:
            scores['tired'] = 1
        elif learning_duration < 10:
            scores['bored'] = 2
        
        task_completion = behavior.get('task_completion_rate', 0)
        if task_completion < 0.3:
            scores['frustrated'] += 2
        elif task_completion > 0.8:
            scores['happy'] += 2
        
        error_count = behavior.get('error_count', 0)
        if error_count > 5:
            scores['frustrated'] += 3
            scores['confused'] += 2
        
        interaction_count = behavior.get('interaction_count', 0)
        if interaction_count > 10:
            scores['excited'] += 2
        
        if not scores:
            emotion_type = 'neutral'
        else:
            emotion_type = max(scores, key=scores.get)
        
        total_score = sum(scores.values())
        if total_score == 0:
            confidence = 0.3
            level = 'low'
        elif total_score < 5:
            confidence = 0.5
            level = 'low'
        elif total_score < 10:
            confidence = 0.7
            level = 'medium'
        else:
            confidence = 0.9
            level = 'high'
        
        return emotion_type, level, round(confidence, 2)
    
    def _update_emotion_trend(self, conn, user_id, emotion_type, level):
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        
        level_score = {'low': 1, 'medium': 2, 'high': 3, 'extreme': 4}.get(level, 2)
        
        cursor.execute('''
            INSERT OR IGNORE INTO emotion_trends (user_id, emotion_type, date, frequency, avg_level)
            VALUES (?, ?, ?, 0, 0)
        ''', (user_id, emotion_type, today))
        
        cursor.execute('''
            UPDATE emotion_trends 
            SET frequency = frequency + 1, 
                avg_level = (avg_level * (frequency) + ?) / (frequency + 1)
            WHERE user_id = ? AND emotion_type = ? AND date = ?
        ''', (level_score, user_id, emotion_type, today))
    
    def _check_alerts(self, conn, user_id, emotion_type, level, confidence):
        cursor = conn.cursor()
        
        alert_triggers = {
            'sad': {'level': 'high', 'confidence': 0.7},
            'anxious': {'level': 'high', 'confidence': 0.7},
            'frustrated': {'level': 'high', 'confidence': 0.7},
            'angry': {'level': 'medium', 'confidence': 0.6}
        }
        
        trigger = alert_triggers.get(emotion_type)
        if trigger:
            level_score = {'low': 1, 'medium': 2, 'high': 3, 'extreme': 4}.get(level, 2)
            trigger_level_score = {'low': 1, 'medium': 2, 'high': 3, 'extreme': 4}.get(trigger['level'], 2)
            
            if level_score >= trigger_level_score and confidence >= trigger['confidence']:
                alert_id = f"ALT{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                cursor.execute('''
                    INSERT INTO emotion_alerts
                    (alert_id, user_id, emotion_type, alert_level, threshold_trigger, message)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    alert_id,
                    user_id,
                    emotion_type,
                    'warning' if level_score == 3 else 'critical',
                    f"emotion={emotion_type}, level={level}, confidence={confidence}",
                    f"检测到用户 {user_id} 情绪异常: {emotion_type} ({level})"
                ))
    
    def get_user_emotion_history(self, user_id, days=7):
        try:
            conn = sqlite3.connect('emotion_analysis.db')
            cursor = conn.cursor()
            
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            cursor.execute('''
                SELECT * FROM emotion_records 
                WHERE user_id = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            ''', (user_id, start_date))
            
            rows = cursor.fetchall()
            conn.close()
            
            history = []
            for row in rows:
                history.append({
                    'record_id': row[1],
                    'emotion_type': row[3],
                    'emotion_level': row[4],
                    'confidence': row[5],
                    'source': row[6],
                    'context': row[7],
                    'timestamp': row[8]
                })
            
            return {'success': True, 'history': history, 'count': len(history)}
        except Exception as e:
            logger.info(f"[AI Emotion Analysis] 获取用户情感历史失败: {e}")
            return {'error': str(e)}
    
    def get_user_emotion_profile(self, user_id):
        try:
            conn = sqlite3.connect('emotion_analysis.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM user_emotion_profiles WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            
            if row:
                conn.close()
                return {
                    'user_id': row[1],
                    'baseline_emotion': row[2],
                    'emotion_pattern': json.loads(row[3]) if row[3] else {},
                    'emotional_triggers': json.loads(row[4]) if row[4] else [],
                    'intervention_history': json.loads(row[5]) if row[5] else [],
                    'last_updated': row[6]
                }
            
            profile = self._build_emotion_profile(conn, user_id)
            conn.close()
            return profile
        except Exception as e:
            logger.info(f"[AI Emotion Analysis] 获取用户情感档案失败: {e}")
            return {'error': str(e)}
    
    def _build_emotion_profile(self, conn, user_id):
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT emotion_type, COUNT(*) as count, AVG(confidence) as avg_confidence
            FROM emotion_records WHERE user_id = ?
            GROUP BY emotion_type ORDER BY count DESC
        ''', (user_id,))
        
        emotion_counts = {}
        for row in cursor.fetchall():
            emotion_counts[row[0]] = {'count': row[1], 'avg_confidence': row[2]}
        
        baseline = 'neutral'
        if emotion_counts:
            baseline = max(emotion_counts, key=lambda k: emotion_counts[k]['count'])
        
        cursor.execute('''
            SELECT emotion_type, date, frequency
            FROM emotion_trends WHERE user_id = ? ORDER BY date
        ''', (user_id,))
        
        patterns = []
        for row in cursor.fetchall():
            patterns.append({'emotion': row[0], 'date': row[1], 'frequency': row[2]})
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_emotion_profiles
            (user_id, baseline_emotion, emotion_pattern, emotional_triggers, last_updated)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            user_id,
            baseline,
            json.dumps(patterns),
            json.dumps([]),
            datetime.now().isoformat()
        ))
        conn.commit()
        
        return {
            'user_id': user_id,
            'baseline_emotion': baseline,
            'emotion_pattern': patterns,
            'emotional_triggers': [],
            'intervention_history': [],
            'last_updated': datetime.now().isoformat()
        }
    
    def generate_intervention(self, user_id, emotion_type):
        intervention_id = f"INT{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        interventions = {
            'sad': {
                'type': 'emotional_support',
                'content': '建议与学生进行一对一沟通，了解其情绪低落的原因，给予情感支持和鼓励。'
            },
            'anxious': {
                'type': 'relaxation',
                'content': '建议引导学生进行深呼吸练习或短暂休息，帮助缓解焦虑情绪。'
            },
            'frustrated': {
                'type': 'task_adjustment',
                'content': '建议调整学习任务难度，分解复杂任务，逐步建立学生的成就感。'
            },
            'angry': {
                'type': 'cool_down',
                'content': '建议先让学生冷静下来，避免冲突，之后再进行理性沟通。'
            },
            'confused': {
                'type': 'clarification',
                'content': '建议提供更详细的讲解或示例，帮助学生理解困惑的知识点。'
            },
            'bored': {
                'type': 'engagement',
                'content': '建议引入互动式学习活动或游戏化元素，提高学生的学习兴趣。'
            },
            'motivated': {
                'type': 'challenge',
                'content': '建议提供进阶学习内容，满足学生的学习动力和求知欲。'
            }
        }
        
        intervention = interventions.get(emotion_type, {
            'type': 'monitoring',
            'content': f'持续关注学生的 {emotion_type} 情绪状态。'
        })
        
        try:
            conn = sqlite3.connect('emotion_analysis.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO emotion_interventions
                (intervention_id, user_id, emotion_type, intervention_type, intervention_content)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                intervention_id,
                user_id,
                emotion_type,
                intervention['type'],
                intervention['content']
            ))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'intervention_id': intervention_id,
                'user_id': user_id,
                'emotion_type': emotion_type,
                'intervention_type': intervention['type'],
                'intervention_content': intervention['content']
            }
        except Exception as e:
            logger.info(f"[AI Emotion Analysis] 生成干预建议失败: {e}")
            return {'error': str(e)}
    
    def execute_intervention(self, intervention_id):
        try:
            conn = sqlite3.connect('emotion_analysis.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE emotion_interventions 
                SET status = ?, executed_at = ? 
                WHERE intervention_id = ?
            ''', ('executed', datetime.now().isoformat(), intervention_id))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'intervention_id': intervention_id}
        except Exception as e:
            logger.info(f"[AI Emotion Analysis] 执行干预失败: {e}")
            return {'error': str(e)}
    
    def get_emotion_summary(self):
        try:
            conn = sqlite3.connect('emotion_analysis.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM emotion_records')
            total_records = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(DISTINCT user_id) FROM emotion_records')
            total_users = cursor.fetchone()[0]
            
            cursor.execute('SELECT emotion_type, COUNT(*) FROM emotion_records GROUP BY emotion_type')
            emotion_distribution = {}
            for row in cursor.fetchall():
                emotion_distribution[row[0]] = row[1]
            
            cursor.execute('SELECT COUNT(*) FROM emotion_alerts WHERE status = "active"')
            active_alerts = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM emotion_interventions WHERE status = "executed"')
            executed_interventions = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_records': total_records,
                'total_users': total_users,
                'emotion_distribution': emotion_distribution,
                'active_alerts': active_alerts,
                'executed_interventions': executed_interventions
            }
        except Exception as e:
            logger.info(f"[AI Emotion Analysis] 获取情感摘要失败: {e}")
            return {}
    
    def get_emotion_alerts(self, status='active'):
        try:
            conn = sqlite3.connect('emotion_analysis.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM emotion_alerts WHERE status = ? ORDER BY created_at DESC', (status,))
            rows = cursor.fetchall()
            conn.close()
            
            alerts = []
            for row in rows:
                alerts.append({
                    'alert_id': row[1],
                    'user_id': row[2],
                    'emotion_type': row[3],
                    'alert_level': row[4],
                    'threshold_trigger': row[5],
                    'message': row[6],
                    'status': row[7],
                    'created_at': row[8],
                    'resolved_at': row[9]
                })
            
            return alerts
        except Exception as e:
            logger.info(f"[AI Emotion Analysis] 获取情感预警失败: {e}")
            return []
    
    def resolve_alert(self, alert_id):
        try:
            conn = sqlite3.connect('emotion_analysis.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE emotion_alerts 
                SET status = ?, resolved_at = ? 
                WHERE alert_id = ?
            ''', ('resolved', datetime.now().isoformat(), alert_id))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'alert_id': alert_id}
        except Exception as e:
            logger.info(f"[AI Emotion Analysis] 解决预警失败: {e}")
            return {'error': str(e)}

emotion_analysis_system = AIEmotionAnalysisSystem()