#!/usr/bin/env python3
import os
import json
import sqlite3
import threading
import hashlib
import random
from datetime import datetime, timedelta
from collections import defaultdict

class AILearningPrediction:
    PREDICTION_TYPES = ['score_prediction', 'completion_prediction', 'dropout_prediction', 'skill_growth_prediction',
    'knowledge_mastery_prediction']
    PREDICTION_STATUS = ['pending', 'analyzing', 'completed', 'validated']
    CONFIDENCE_LEVELS = ['low', 'medium', 'high', 'very_high']
    
    def __init__(self):
        self.prediction_cache = {}
        self._lock = threading.Lock()
        self._create_tables()
    
    def _create_tables(self):
        try:
            conn = sqlite3.connect('ai_prediction.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS prediction_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL UNIQUE,
                    prediction_type TEXT NOT NULL,
                    user_id TEXT,
                    subject TEXT,
                    input_data TEXT,
                    status TEXT DEFAULT 'pending',
                    confidence REAL DEFAULT 0.0,
                    prediction_result TEXT,
                    prediction_interval TEXT,
                    actual_result TEXT,
                    accuracy REAL DEFAULT 0.0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT,
                    validated_at TEXT,
                    metadata TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS prediction_features (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    feature_id TEXT NOT NULL UNIQUE,
                    user_id TEXT NOT NULL,
                    feature_name TEXT NOT NULL,
                    feature_value REAL DEFAULT 0.0,
                    feature_category TEXT,
                    source_system TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS prediction_models (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id TEXT NOT NULL UNIQUE,
                    model_name TEXT NOT NULL,
                    prediction_type TEXT NOT NULL,
                    features TEXT,
                    accuracy REAL DEFAULT 0.0,
                    trained_at TEXT,
                    last_used_at TEXT,
                    enabled BOOLEAN DEFAULT 1,
                    metadata TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS prediction_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    step_number INTEGER NOT NULL,
                    step_name TEXT NOT NULL,
                    feature_extraction TEXT,
                    model_used TEXT,
                    confidence REAL DEFAULT 0.0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"[AI Learning Prediction] 创建表失败: {e}")
    
    def _generate_id(self, prefix):
        return prefix + '_' + hashlib.md5((str(datetime.now().timestamp()) + str(random.random())).encode()).hexdigest(
        )[:16]
    
    def extract_features(self, user_id, subject=None):
        features = {
            'user_id': user_id,
            'subject': subject,
            'learning_features': {},
            'interaction_features': {},
            'performance_features': {},
            'temporal_features': {}
        }
        
        try:
            from app.ai.ai_adaptive_learning import ai_adaptive_learning
            
            profile = ai_adaptive_learning.get_or_create_profile(user_id)
            if profile:
                features['learning_features']['learning_style'] = profile.get('learning_style', 'visual')
                features['learning_features']['knowledge_level'] = profile.get('knowledge_level', 'novice')
                features['learning_features']['learning_speed'] = profile.get('learning_speed', 1.0)
            
            stats = ai_adaptive_learning.get_learning_statistics(user_id)
            features['performance_features']['total_interactions'] = stats.get('total_interactions', 0)
            features['performance_features']['success_rate'] = stats.get('success_rate', 0.0)
            features['performance_features']['avg_score'] = stats.get('avg_score', 0.0)
            
            gaps = ai_adaptive_learning.detect_knowledge_gaps(user_id, subject)
            features['learning_features']['knowledge_gaps'] = gaps.get('gaps_found', 0)
            
            paths = ai_adaptive_learning.get_user_paths(user_id)
            features['temporal_features']['total_paths'] = len(paths)
            features['temporal_features']['completed_paths'] = sum(1 for p in paths if p.get('status') == 'completed')
            
            progress = ai_adaptive_learning.get_user_progress(user_id)
            features['performance_features']['overall_progress'] = progress.get('overall_progress', 0)
            
        except Exception as e:
            logger.info(f"[AI Learning Prediction] 特征提取失败: {e}")
        
        try:
            conn = sqlite3.connect('ai_prediction.db')
            cursor = conn.cursor()
            
            for category, category_features in features.items():
                if isinstance(category_features, dict):
                    for name, value in category_features.items():
                        if isinstance(value, (int, float)):
                            feature_id = self._generate_id('feat')
                            cursor.execute('''
                                INSERT INTO prediction_features 
                                (feature_id, user_id, feature_name, feature_value, feature_category, source_system)
                                VALUES (?, ?, ?, ?, ?, ?)
                            ''', (feature_id, user_id, name, value, category, 'adaptive_learning'))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"[AI Learning Prediction] 保存特征失败: {e}")
        
        return features
    
    def predict(self, prediction_type, user_id, subject=None, prediction_interval='7d'):
        task_id = self._generate_id('prediction')
        start_time = datetime.now()
        
        try:
            conn = sqlite3.connect('ai_prediction.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO prediction_tasks 
                (task_id, prediction_type, user_id, subject, prediction_interval, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (task_id, prediction_type, user_id, subject, prediction_interval, 'analyzing'))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"[AI Learning Prediction] 创建预测任务失败: {e}")
        
        features = self.extract_features(user_id, subject)
        
        prediction_result = None
        confidence = 0.0
        
        if prediction_type == 'score_prediction':
            prediction_result, confidence = self._predict_score(user_id, features, prediction_interval)
        elif prediction_type == 'completion_prediction':
            prediction_result, confidence = self._predict_completion(user_id, features, prediction_interval)
        elif prediction_type == 'dropout_prediction':
            prediction_result, confidence = self._predict_dropout(user_id, features, prediction_interval)
        elif prediction_type == 'skill_growth_prediction':
            prediction_result, confidence = self._predict_skill_growth(user_id, features, prediction_interval)
        elif prediction_type == 'knowledge_mastery_prediction':
            prediction_result, confidence = self._predict_knowledge_mastery(user_id, features, prediction_interval)
        
        try:
            conn = sqlite3.connect('ai_prediction.db')
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE prediction_tasks 
                SET status = ?, confidence = ?, prediction_result = ?, completed_at = ?, duration = ?
                WHERE task_id = ?
            ''', (
                'completed', confidence, json.dumps(prediction_result),
                datetime.now().isoformat(),
                (datetime.now() - start_time).total_seconds(),
                task_id
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.info(f"[AI Learning Prediction] 保存预测结果失败: {e}")
        
        self.prediction_cache[task_id] = prediction_result
        
        return {
            'success': True,
            'task_id': task_id,
            'prediction_type': prediction_type,
            'user_id': user_id,
            'subject': subject,
            'prediction_interval': prediction_interval,
            'result': prediction_result,
            'confidence': round(confidence, 2),
            'duration': round((datetime.now() - start_time).total_seconds(), 2)
        }
    
    def _predict_score(self, user_id, features, interval):
        base_score = features.get('performance_features', {}).get('avg_score', 60)
        success_rate = features.get('performance_features', {}).get('success_rate', 50) / 100
        progress = features.get('performance_features', {}).get('overall_progress', 0) / 100
        gaps = features.get('learning_features', {}).get('knowledge_gaps', 0)
        
        interval_multiplier = {'1d': 1.0, '7d': 1.5, '30d': 2.0}.get(interval, 1.5)
        
        improvement_factor = success_rate * 0.3 + progress * 0.5
        gap_penalty = gaps * 2
        
        predicted_score = base_score + improvement_factor * 15 * interval_multiplier - gap_penalty
        predicted_score = max(0, min(100, predicted_score))
        
        confidence = min(0.95, 0.5 + success_rate * 0.3 + (1 - gaps / 10) * 0.2)
        
        return {
            'predicted_score': round(predicted_score, 2),
            'current_score': round(base_score, 2),
            'improvement': round(predicted_score - base_score, 2),
            'factors': {
                'success_rate': success_rate,
                'progress': progress,
                'knowledge_gaps': gaps,
                'interval_multiplier': interval_multiplier
            },
            'recommendations': [
                f"预计分数提升 {round(predicted_score - base_score, 1)} 分",
                f"建议修复 {gaps} 个知识漏洞以加速提升",
                "保持当前学习节奏，预计会有持续进步"
            ]
        }, confidence
    
    def _predict_completion(self, user_id, features, interval):
        total_paths = features.get('temporal_features', {}).get('total_paths', 0)
        completed_paths = features.get('temporal_features', {}).get('completed_paths', 0)
        current_progress = features.get('performance_features', {}).get('overall_progress', 0) / 100
        
        interval_days = {'1d': 1, '7d': 7, '30d': 30}.get(interval, 7)
        
        avg_completion_rate = completed_paths / total_paths if total_paths > 0 else 0.3
        
        days_per_path = 7 / avg_completion_rate if avg_completion_rate > 0 else 7
        remaining_paths = total_paths - completed_paths
        days_needed = remaining_paths * days_per_path
        
        completion_probability = min(1.0, interval_days / days_needed) if days_needed > 0 else 1.0
        
        expected_completion = current_progress + (1 - current_progress) * completion_probability * 0.8
        expected_completion = min(100, expected_completion)
        
        confidence = min(0.95, 0.5 + avg_completion_rate * 0.4)
        
        return {
            'predicted_completion_rate': round(expected_completion * 100, 2),
            'current_completion_rate': round(current_progress * 100, 2),
            'expected_completion_date': (datetime.now() + timedelta(days=days_needed)).isoformat(),
            'completion_probability': round(completion_probability * 100, 2),
            'factors': {
                'total_paths': total_paths,
                'completed_paths': completed_paths,
                'avg_completion_rate': round(avg_completion_rate, 2),
                'days_needed': round(days_needed, 1)
            },
            'recommendations': [
                f"预计完成率: {round(expected_completion * 100, 1)}%",
                f"预计还需 {round(days_needed, 1)} 天完成所有学习路径",
                f"在 {interval} 内完成的概率: {round(completion_probability * 100, 1)}%"
            ]
        }, confidence
    
    def _predict_dropout(self, user_id, features, interval):
        success_rate = features.get('performance_features', {}).get('success_rate', 50) / 100
        progress = features.get('performance_features', {}).get('overall_progress', 0) / 100
        gaps = features.get('learning_features', {}).get('knowledge_gaps', 0)
        total_interactions = features.get('performance_features', {}).get('total_interactions', 0)
        
        dropout_risk = 0.0
        
        if success_rate < 0.4:
            dropout_risk += 0.3
        if progress < 0.2 and total_interactions > 20:
            dropout_risk += 0.2
        if gaps >= 5:
            dropout_risk += 0.2
        if total_interactions < 5:
            dropout_risk += 0.15
        
        dropout_risk = min(1.0, dropout_risk)
        
        risk_level = 'low'
        if dropout_risk > 0.6:
            risk_level = 'high'
        elif dropout_risk > 0.3:
            risk_level = 'medium'
        
        confidence = min(0.95, 0.6 + (1 - dropout_risk) * 0.3)
        
        return {
            'dropout_risk': round(dropout_risk * 100, 2),
            'risk_level': risk_level,
            'factors': {
                'success_rate': success_rate,
                'progress': progress,
                'knowledge_gaps': gaps,
                'total_interactions': total_interactions
            },
            'warning': risk_level != 'low',
            'intervention_needed': dropout_risk > 0.5,
            'recommendations': [
                f"辍学风险: {risk_level} ({round(dropout_risk * 100, 1)}%)",
                "建议增加学习支持和鼓励",
                "针对知识漏洞进行专项辅导",
                "定期检查学习进度"
            ]
        }, confidence
    
    def _predict_skill_growth(self, user_id, features, interval):
        current_level = features.get('learning_features', {}).get('knowledge_level', 'novice')
        success_rate = features.get('performance_features', {}).get('success_rate', 50) / 100
        progress = features.get('performance_features', {}).get('overall_progress', 0) / 100
        
        level_order = ['novice', 'beginner', 'intermediate', 'advanced', 'expert']
        current_index = level_order.index(current_level) if current_level in level_order else 0
        
        growth_rate = success_rate * 0.4 + progress * 0.3
        
        interval_multiplier = {'1d': 0.1, '7d': 0.5, '30d': 1.0}.get(interval, 0.5)
        expected_growth = growth_rate * interval_multiplier
        
        expected_level_index = min(len(level_order) - 1, current_index + int(expected_growth * 2))
        expected_level = level_order[expected_level_index]
        
        confidence = min(0.95, 0.5 + growth_rate * 0.4)
        
        return {
            'current_skill_level': current_level,
            'predicted_skill_level': expected_level,
            'skill_growth_rate': round(growth_rate * 100, 2),
            'expected_level_up': expected_level != current_level,
            'factors': {
                'success_rate': success_rate,
                'progress': progress,
                'growth_rate': round(growth_rate, 2)
            },
            'recommendations': [
                f"当前技能水平: {current_level}",
                f"预计技能水平: {expected_level}",
                f"技能增长率: {round(growth_rate * 100, 1)}%",
                "保持良好的学习习惯，技能会持续提升"
            ]
        }, confidence
    
    def _predict_knowledge_mastery(self, user_id, features, interval):
        gaps = features.get('learning_features', {}).get('knowledge_gaps', 0)
        success_rate = features.get('performance_features', {}).get('success_rate', 50) / 100
        progress = features.get('performance_features', {}).get('overall_progress', 0) / 100
        
        current_mastery = min(100, (1 - gaps / 10) * 50 + success_rate * 30 + progress * 20)
        
        improvement_rate = success_rate * 0.3 + (1 - gaps / 10) * 0.4
        interval_multiplier = {'1d': 1.0, '7d': 3.0, '30d': 10.0}.get(interval, 3.0)
        
        predicted_mastery = current_mastery + improvement_rate * 15 * interval_multiplier
        predicted_mastery = min(100, predicted_mastery)
        
        mastery_level = 'basic'
        if predicted_mastery > 80:
            mastery_level = 'expert'
        elif predicted_mastery > 60:
            mastery_level = 'intermediate'
        elif predicted_mastery > 40:
            mastery_level = 'developing'
        
        confidence = min(0.95, 0.5 + (1 - gaps / 10) * 0.3 + success_rate * 0.2)
        
        return {
            'current_mastery': round(current_mastery, 2),
            'predicted_mastery': round(predicted_mastery, 2),
            'mastery_level': mastery_level,
            'improvement': round(predicted_mastery - current_mastery, 2),
            'factors': {
                'knowledge_gaps': gaps,
                'success_rate': success_rate,
                'progress': progress,
                'improvement_rate': round(improvement_rate, 2)
            },
            'recommendations': [
                f"当前知识掌握度: {round(current_mastery, 1)}%",
                f"预计知识掌握度: {round(predicted_mastery, 1)}%",
                f"掌握等级: {mastery_level}",
                f"预计提升: {round(predicted_mastery - current_mastery, 1)}%"
            ]
        }, confidence
    
    def validate_prediction(self, task_id, actual_result):
        try:
            conn = sqlite3.connect('ai_prediction.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM prediction_tasks WHERE task_id = ?', (task_id,))
            task = cursor.fetchone()
            
            if not task:
                conn.close()
                return {'success': False, 'error': '预测任务不存在'}
            
            if task['status'] == 'validated':
                conn.close()
                return {'success': False, 'error': '预测已验证'}
            
            prediction_result = json.loads(task.get('prediction_result', '{}'))
            
            accuracy = 0.0
            prediction_type = task['prediction_type']
            
            if prediction_type == 'score_prediction':
                predicted = prediction_result.get('predicted_score', 0)
                actual = actual_result.get('score', 0)
                accuracy = max(0, 100 - abs(predicted - actual))
            elif prediction_type == 'completion_prediction':
                predicted = prediction_result.get('predicted_completion_rate', 0)
                actual = actual_result.get('completion_rate', 0)
                accuracy = max(0, 100 - abs(predicted - actual))
            elif prediction_type == 'dropout_prediction':
                predicted_risk = prediction_result.get('dropout_risk', 0)
                actual_dropped = actual_result.get('dropped', False)
                if (predicted_risk > 50 and actual_dropped) or (predicted_risk <= 50 and not actual_dropped):
                    accuracy = 100
                else:
                    accuracy = 50
            elif prediction_type == 'skill_growth_prediction':
                predicted = prediction_result.get('predicted_skill_level', '')
                actual = actual_result.get('skill_level', '')
                accuracy = 100 if predicted == actual else 50
            elif prediction_type == 'knowledge_mastery_prediction':
                predicted = prediction_result.get('predicted_mastery', 0)
                actual = actual_result.get('mastery', 0)
                accuracy = max(0, 100 - abs(predicted - actual))
            
            cursor.execute('''
                UPDATE prediction_tasks 
                SET status = ?, actual_result = ?, accuracy = ?, validated_at = ?
                WHERE task_id = ?
            ''', ('validated', json.dumps(actual_result), accuracy, datetime.now().isoformat(), task_id))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'task_id': task_id,
                'prediction_type': prediction_type,
                'accuracy': round(accuracy, 2),
                'message': '预测验证完成'
            }
        except Exception as e:
            logger.info(f"[AI Learning Prediction] 验证预测失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_prediction_task(self, task_id):
        try:
            conn = sqlite3.connect('ai_prediction.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM prediction_tasks WHERE task_id = ?', (task_id,))
            row = cursor.fetchone()
            
            if row:
                result = dict(row)
                result['input_data'] = json.loads(result.get('input_data', '{}'))
                result['prediction_result'] = json.loads(result.get('prediction_result', '{}'))
                result['actual_result'] = json.loads(result.get('actual_result', '{}'))
                return result
            
            conn.close()
            return None
        except Exception as e:
            logger.info(f"[AI Learning Prediction] 获取预测任务失败: {e}")
            return None
    
    def list_prediction_tasks(self, prediction_type=None, user_id=None, limit=20):
        try:
            conn = sqlite3.connect('ai_prediction.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            conditions = []
            params = []
            
            if prediction_type:
                conditions.append('prediction_type = ?')
                params.append(prediction_type)
            
            if user_id:
                conditions.append('user_id = ?')
                params.append(user_id)
            
            params.append(limit)
            
            query = 'SELECT * FROM prediction_tasks'
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
            query += ' ORDER BY created_at DESC LIMIT ?'
            
            cursor.execute(query, params)
            
            results = []
            for row in cursor.fetchall():
                task = dict(row)
                task['prediction_result'] = json.loads(task.get('prediction_result', '{}'))
                results.append(task)
            
            conn.close()
            return results
        except Exception as e:
            logger.info(f"[AI Learning Prediction] 列出预测任务失败: {e}")
            return []
    
    def get_prediction_statistics(self):
        try:
            conn = sqlite3.connect('ai_prediction.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM prediction_tasks')
            total_tasks = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM prediction_tasks WHERE status = ?', ('completed',))
            completed_tasks = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM prediction_tasks WHERE status = ?', ('validated',))
            validated_tasks = cursor.fetchone()[0]
            
            cursor.execute('SELECT AVG(confidence) FROM prediction_tasks WHERE status = ?', ('completed',))
            avg_confidence = cursor.fetchone()[0] or 0.0
            
            cursor.execute('SELECT AVG(accuracy) FROM prediction_tasks WHERE status = ?', ('validated',))
            avg_accuracy = cursor.fetchone()[0] or 0.0
            
            cursor.execute('SELECT COUNT(*) FROM prediction_models')
            model_count = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT prediction_type, COUNT(*) as count, AVG(confidence) as avg_confidence,
                AVG(accuracy) as avg_accuracy
                FROM prediction_tasks WHERE status = 'completed'
                GROUP BY prediction_type
            ''')
            type_stats = []
            for row in cursor.fetchall():
                type_stats.append({
                    'prediction_type': row[0],
                    'count': row[1],
                    'avg_confidence': row[2] or 0.0,
                    'avg_accuracy': row[3] or 0.0
                })
            
            conn.close()
            
            return {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'validated_tasks': validated_tasks,
                'validation_rate': round(validated_tasks / completed_tasks * 100, 2) if completed_tasks > 0 else 0.0,
                'avg_confidence': round(avg_confidence, 2),
                'avg_accuracy': round(avg_accuracy, 2),
                'model_count': model_count,
                'type_statistics': type_stats
            }
        except Exception as e:
            logger.info(f"[AI Learning Prediction] 获取统计信息失败: {e}")
            return {
                'total_tasks': 0,
                'completed_tasks': 0,
                'validated_tasks': 0,
                'validation_rate': 0.0,
                'avg_confidence': 0.0,
                'avg_accuracy': 0.0,
                'model_count': 0,
                'type_statistics': []
            }

ai_learning_prediction = AILearningPrediction()