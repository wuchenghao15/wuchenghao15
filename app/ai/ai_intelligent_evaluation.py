#!/usr/bin/env python3
import os
import json
import sqlite3
import threading
from datetime import datetime
from collections import defaultdict

class AIIntelligentEvaluationSystem:
    EVALUATION_TYPES = ['knowledge', 'skill', 'behavior', 'progress', 'potential', 'overall']
    EVALUATION_METHODS = ['auto', 'manual', 'hybrid', 'peer']
    RATING_SCALE = [1, 2, 3, 4, 5]
    
    def __init__(self):
        self.evaluations = {}
        self._lock = threading.Lock()
        self._create_tables()
    
    def _create_tables(self):
        try:
            conn = sqlite3.connect('intelligent_evaluation.db')
            cursor = conn.cursor()
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS evaluations ( id INTEGER PRIMARY KEY AUTOINCREMENT, evaluation_id TEXT NOT NULL UNIQUE, user_id TEXT NOT NULL, evaluation_type TEXT NOT NULL, evaluation_method TEXT DEFAULT 'auto', score REAL DEFAULT 0.0, max_score REAL DEFAULT 100.0, grade TEXT, feedback TEXT, recommendations TEXT, confidence REAL DEFAULT 0.0, status TEXT DEFAULT 'completed', created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP, evaluator TEXT DEFAULT 'system', metadata TEXT ) ''')
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS evaluation_criteria ( id INTEGER PRIMARY KEY AUTOINCREMENT, criteria_id TEXT NOT NULL UNIQUE, criteria_name TEXT NOT NULL, evaluation_type TEXT NOT NULL, weight REAL DEFAULT 0.2, description TEXT, min_score REAL DEFAULT 0.0, max_score REAL DEFAULT 100.0, is_active INTEGER DEFAULT 1 ) ''')
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS evaluation_details ( id INTEGER PRIMARY KEY AUTOINCREMENT, evaluation_id TEXT NOT NULL, criteria_id TEXT NOT NULL, score REAL DEFAULT 0.0, feedback TEXT, weight REAL DEFAULT 0.2, normalized_score REAL DEFAULT 0.0 ) ''')
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS user_evaluation_history ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, evaluation_type TEXT NOT NULL, score REAL DEFAULT 0.0, grade TEXT, evaluation_date TEXT DEFAULT CURRENT_TIMESTAMP, trend TEXT DEFAULT 'stable' ) ''')
            
            cursor.execute(''' CREATE TABLE IF NOT EXISTS evaluation_templates ( id INTEGER PRIMARY KEY AUTOINCREMENT, template_id TEXT NOT NULL UNIQUE, template_name TEXT NOT NULL, evaluation_type TEXT NOT NULL, criteria_list TEXT, scoring_rules TEXT, description TEXT, is_active INTEGER DEFAULT 1 ) ''')
            
            conn.commit()
            
            self._init_default_criteria(conn)
            
            conn.close()
            logger.info("[AI Intelligent Evaluation] 数据库表创建完成")
        except Exception as e:
            logger.info(f"[AI Intelligent Evaluation] 创建表失败: {e}")
    
    def _init_default_criteria(self, conn):
        cursor = conn.cursor()
        
        default_criteria = [
            ('KNOW_001', '知识点掌握程度', 'knowledge', 0.3, '评估学生对核心知识点的理解和掌握情况', 0, 100, 1),
            ('KNOW_002', '知识应用能力', 'knowledge', 0.3, '评估学生将知识应用到实际问题的能力', 0, 100, 1),
            ('KNOW_003', '知识深度', 'knowledge', 0.2, '评估学生对知识的深入理解程度', 0, 100, 1),
            ('KNOW_004', '知识广度', 'knowledge', 0.2, '评估学生知识的覆盖面', 0, 100, 1),
            ('SKILL_001', '解题能力', 'skill', 0.3, '评估学生解决问题的能力', 0, 100, 1),
            ('SKILL_002', '学习方法', 'skill', 0.2, '评估学生的学习策略和方法', 0, 100, 1),
            ('SKILL_003', '时间管理', 'skill', 0.2, '评估学生的学习时间管理能力', 0, 100, 1),
            ('SKILL_004', '自主学习', 'skill', 0.3, '评估学生的自主学习能力', 0, 100, 1),
            ('BEHAV_001', '学习积极性', 'behavior', 0.3, '评估学生的学习主动性和积极性', 0, 100, 1),
            ('BEHAV_002', '课堂参与', 'behavior', 0.2, '评估学生的课堂互动和参与度', 0, 100, 1),
            ('BEHAV_003', '作业完成', 'behavior', 0.3, '评估学生的作业完成质量和及时性', 0, 100, 1),
            ('BEHAV_004', '合作学习', 'behavior', 0.2, '评估学生的团队合作能力', 0, 100, 1),
            ('PROG_001', '进步幅度', 'progress', 0.4, '评估学生的学习进步情况', 0, 100, 1),
            ('PROG_002', '学习速度', 'progress', 0.3, '评估学生的学习效率', 0, 100, 1),
            ('PROG_003', '稳定性', 'progress', 0.3, '评估学生学习表现的稳定性', 0, 100, 1),
            ('POTEN_001', '学习潜力', 'potential', 0.4, '评估学生的学习潜力和发展空间', 0, 100, 1),
            ('POTEN_002', '兴趣倾向', 'potential', 0.3, '评估学生的学习兴趣和方向', 0, 100, 1),
            ('POTEN_003', '创新能力', 'potential', 0.3, '评估学生的创新思维和能力', 0, 100, 1),
        ]
        
        for criteria in default_criteria:
            cursor.execute(''' INSERT OR IGNORE INTO evaluation_criteria (criteria_id, criteria_name, evaluation_type, weight, description, min_score, max_score, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ''', criteria)
        
        conn.commit()
    
    def evaluate(self, user_id, evaluation_type, data=None):
        evaluation_id = f"EVAL{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        data = data or {}
        scores, total_score, grade, feedback, recommendations = self._calculate_scores(evaluation_type, data)
        
        try:
            conn = sqlite3.connect('intelligent_evaluation.db')
            cursor = conn.cursor()
            
            cursor.execute(''' INSERT INTO evaluations (evaluation_id, user_id, evaluation_type, evaluation_method, score, max_score, grade, feedback, recommendations, confidence) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (
                evaluation_id,
                user_id,
                evaluation_type,
                'auto',
                total_score,
                100.0,
                grade,
                feedback,
                json.dumps(recommendations),
                self._calculate_confidence(data)
            ))
            
            cursor.execute('SELECT criteria_id, weight FROM evaluation_criteria WHERE evaluation_type = ? AND is_active = 1', (evaluation_type,))
            criteria_rows = cursor.fetchall()
            
            for criteria_id, weight in criteria_rows:
                score = scores.get(criteria_id, 0)
                normalized = score * weight
                cursor.execute(''' INSERT INTO evaluation_details (evaluation_id, criteria_id, score, weight, normalized_score) VALUES (?, ?, ?, ?, ?) ''', (evaluation_id, criteria_id, score, weight, normalized))
            
            self._update_user_history(conn, user_id, evaluation_type, total_score, grade)
            
            conn.commit()
            conn.close()
            
            self.evaluations[evaluation_id] = {
                'user_id': user_id,
                'type': evaluation_type,
                'score': total_score,
                'grade': grade,
                'timestamp': datetime.now().isoformat()
            }
            
            return {
                'success': True,
                'evaluation_id': evaluation_id,
                'user_id': user_id,
                'evaluation_type': evaluation_type,
                'score': round(total_score, 2),
                'grade': grade,
                'feedback': feedback,
                'recommendations': recommendations,
                'criteria_scores': {k: round(v, 2) for k, v in scores.items()}
            }
        except Exception as e:
            logger.info(f"[AI Intelligent Evaluation] 评估失败: {e}")
            return {'error': str(e)}
    
    def _calculate_scores(self, evaluation_type, data):
        scores = {}
        total_weight = 0
        
        conn = sqlite3.connect('intelligent_evaluation.db')
        cursor = conn.cursor()
        cursor.execute('SELECT criteria_id, criteria_name, weight FROM evaluation_criteria WHERE evaluation_type = ? AND is_active = 1', (evaluation_type,))
        criteria_list = cursor.fetchall()
        conn.close()
        
        for criteria_id, criteria_name, weight in criteria_list:
            scores[criteria_id] = self._score_criteria(criteria_id, criteria_name, data)
            total_weight += weight
        
        total_score = sum(scores[criteria_id] * weight for criteria_id, _, weight in criteria_list)
        total_score = total_score / total_weight if total_weight > 0 else 0
        
        grade = self._calculate_grade(total_score)
        feedback = self._generate_feedback(evaluation_type, total_score, scores)
        recommendations = self._generate_recommendations(evaluation_type, scores)
        
        return scores, total_score, grade, feedback, recommendations
    
    def _score_criteria(self, criteria_id, criteria_name, data):
        if criteria_id.startswith('KNOW'):
            return self._score_knowledge(criteria_id, data)
        elif criteria_id.startswith('SKILL'):
            return self._score_skill(criteria_id, data)
        elif criteria_id.startswith('BEHAV'):
            return self._score_behavior(criteria_id, data)
        elif criteria_id.startswith('PROG'):
            return self._score_progress(criteria_id, data)
        elif criteria_id.startswith('POTEN'):
            return self._score_potential(criteria_id, data)
        return 50
    
    def _score_knowledge(self, criteria_id, data):
        exam_scores = data.get('exam_scores', [])
        quiz_scores = data.get('quiz_scores', [])
        all_scores = exam_scores + quiz_scores
        
        if not all_scores:
            return 40
        
        avg_score = sum(all_scores) / len(all_scores)
        
        if criteria_id == 'KNOW_001':
            return min(100, avg_score + 10)
        elif criteria_id == 'KNOW_002':
            application_count = data.get('application_success_count', 0)
            return min(100, avg_score * 0.8 + application_count * 5)
        elif criteria_id == 'KNOW_003':
            depth_indicators = data.get('depth_indicators', [])
            return min(100, avg_score * 0.7 + len(depth_indicators) * 10)
        elif criteria_id == 'KNOW_004':
            breadth_indicators = data.get('breadth_indicators', [])
            return min(100, avg_score * 0.7 + len(breadth_indicators) * 8)
        return avg_score
    
    def _score_skill(self, criteria_id, data):
        completion_rate = data.get('task_completion_rate', 0.5)
        efficiency = data.get('learning_efficiency', 0.5)
        
        if criteria_id == 'SKILL_001':
            problem_solving_rate = data.get('problem_solving_rate', 0.5)
            return min(100, problem_solving_rate * 100)
        elif criteria_id == 'SKILL_002':
            strategy_count = data.get('learning_strategies_used', 2)
            return min(100, 50 + strategy_count * 15)
        elif criteria_id == 'SKILL_003':
            time_management_score = data.get('time_management_score', 0.5)
            return min(100, time_management_score * 100)
        elif criteria_id == 'SKILL_004':
            self_study_hours = data.get('self_study_hours', 5)
            return min(100, 30 + self_study_hours * 7)
        return completion_rate * 100
    
    def _score_behavior(self, criteria_id, data):
        activity_score = data.get('activity_score', 50)
        
        if criteria_id == 'BEHAV_001':
            participation_rate = data.get('participation_rate', 0.5)
            return min(100, participation_rate * 100)
        elif criteria_id == 'BEHAV_002':
            interaction_count = data.get('interaction_count', 5)
            return min(100, 30 + interaction_count * 7)
        elif criteria_id == 'BEHAV_003':
            homework_quality = data.get('homework_quality_score', 50)
            return min(100, homework_quality)
        elif criteria_id == 'BEHAV_004':
            collaboration_score = data.get('collaboration_score', 50)
            return min(100, collaboration_score)
        return activity_score
    
    def _score_progress(self, criteria_id, data):
        current_score = data.get('current_score', 50)
        baseline_score = data.get('baseline_score', 40)
        
        if criteria_id == 'PROG_001':
            improvement = current_score - baseline_score
            return min(100, 50 + improvement * 2)
        elif criteria_id == 'PROG_002':
            learning_days = data.get('learning_days', 30)
            progress_per_day = (current_score - baseline_score) / max(learning_days, 1)
            return min(100, 50 + progress_per_day * 10)
        elif criteria_id == 'PROG_003':
            score_variance = data.get('score_variance', 10)
            return min(100, 100 - score_variance)
        return (current_score + baseline_score) / 2
    
    def _score_potential(self, criteria_id, data):
        if criteria_id == 'POTEN_001':
            growth_rate = data.get('growth_rate', 0.1)
            return min(100, 50 + growth_rate * 500)
        elif criteria_id == 'POTEN_002':
            interest_tags = data.get('interest_tags', [])
            return min(100, 40 + len(interest_tags) * 12)
        elif criteria_id == 'POTEN_003':
            creative_projects = data.get('creative_projects', 0)
            return min(100, 30 + creative_projects * 17)
        return 50
    
    def _calculate_grade(self, score):
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def _generate_feedback(self, evaluation_type, score, scores):
        grade = self._calculate_grade(score)
        
        feedback_templates = {
            'knowledge': {
                'A': '知识掌握优秀，建议挑战更高难度的学习内容。',
                'B': '知识掌握良好，部分知识点需要加强复习。',
                'C': '知识掌握一般，建议重点复习薄弱环节。',
                'D': '知识掌握较差，需要系统性地补学基础知识。',
                'F': '知识掌握严重不足，建议寻求老师帮助进行针对性辅导。'
            },
            'skill': {
                'A': '学习技能优秀，能够高效地完成学习任务。',
                'B': '学习技能良好，有一定的学习方法和策略。',
                'C': '学习技能一般，建议学习更有效的学习方法。',
                'D': '学习技能较差，需要培养良好的学习习惯。',
                'F': '学习技能严重不足，建议从基础学习方法开始培养。'
            },
            'behavior': {
                'A': '学习行为表现优秀，积极主动，是其他同学的榜样。',
                'B': '学习行为表现良好，课堂参与度高。',
                'C': '学习行为表现一般，需要提高学习积极性。',
                'D': '学习行为表现较差，需要改善学习态度。',
                'F': '学习行为表现严重不足，建议与家长沟通共同改进。'
            },
            'progress': {
                'A': '进步非常显著，继续保持良好的学习状态！',
                'B': '进步明显，学习方法有效。',
                'C': '有一定进步，继续努力！',
                'D': '进步较慢，需要调整学习策略。',
                'F': '进步不明显或退步，建议分析原因并改进。'
            },
            'potential': {
                'A': '学习潜力巨大，未来发展空间广阔！',
                'B': '学习潜力良好，有较强的发展潜力。',
                'C': '学习潜力一般，需要挖掘和培养。',
                'D': '学习潜力有待开发，建议发现兴趣点。',
                'F': '学习潜力尚未充分展现，建议多角度尝试。'
            }
        }
        
        return feedback_templates.get(evaluation_type, {}).get(grade, '评估完成，请查看详细报告。')
    
    def _generate_recommendations(self, evaluation_type, scores):
        conn = sqlite3.connect('intelligent_evaluation.db')
        cursor = conn.cursor()
        cursor.execute('SELECT criteria_id, criteria_name FROM evaluation_criteria WHERE evaluation_type = ? AND is_active = 1', (evaluation_type,))
        criteria_list = cursor.fetchall()
        conn.close()
        
        recommendations = []
        
        for criteria_id, criteria_name in criteria_list:
            score = scores.get(criteria_id, 0)
            if score < 60:
                recommendations.append(f"加强 {criteria_name} 的训练和学习")
            elif score < 80:
                recommendations.append(f"继续提升 {criteria_name}")
        
        if not recommendations:
            recommendations.append("当前评估各项指标良好，建议保持并挑战更高目标。")
        
        return recommendations
    
    def _calculate_confidence(self, data):
        data_points = len(data) if isinstance(data, dict) else 0
        return min(1.0, 0.3 + data_points * 0.05)
    
    def _update_user_history(self, conn, user_id, evaluation_type, score, grade):
        cursor = conn.cursor()
        
        cursor.execute(''' SELECT score FROM user_evaluation_history WHERE user_id = ? AND evaluation_type = ? ORDER BY evaluation_date DESC LIMIT 1 ''', (user_id, evaluation_type))
        
        last_row = cursor.fetchone()
        trend = 'stable'
        
        if last_row:
            last_score = last_row[0]
            if score > last_score + 5:
                trend = 'improving'
            elif score < last_score - 5:
                trend = 'declining'
        
        cursor.execute(''' INSERT INTO user_evaluation_history (user_id, evaluation_type, score, grade, trend) VALUES (?, ?, ?, ?, ?) ''', (user_id, evaluation_type, score, grade, trend))
    
    def get_evaluation(self, evaluation_id):
        try:
            conn = sqlite3.connect('intelligent_evaluation.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM evaluations WHERE evaluation_id = ?', (evaluation_id,))
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return None
            
            cursor.execute('SELECT * FROM evaluation_details WHERE evaluation_id = ?', (evaluation_id,))
            detail_rows = cursor.fetchall()
            
            conn.close()
            
            details = []
            for dr in detail_rows:
                details.append({
                    'criteria_id': dr[2],
                    'score': dr[3],
                    'weight': dr[5],
                    'normalized_score': dr[6]
                })
            
            return {
                'evaluation_id': row[1],
                'user_id': row[2],
                'evaluation_type': row[3],
                'evaluation_method': row[4],
                'score': row[5],
                'max_score': row[6],
                'grade': row[7],
                'feedback': row[8],
                'recommendations': json.loads(row[9]) if row[9] else [],
                'confidence': row[10],
                'status': row[11],
                'created_at': row[12],
                'evaluator': row[14],
                'details': details
            }
        except Exception as e:
            logger.info(f"[AI Intelligent Evaluation] 获取评估失败: {e}")
            return None
    
    def get_user_evaluations(self, user_id, evaluation_type=None):
        try:
            conn = sqlite3.connect('intelligent_evaluation.db')
            cursor = conn.cursor()
            
            if evaluation_type:
                cursor.execute(
                'SELECT * FROM evaluations WHERE user_id = ? AND evaluation_type = ? ORDER BY created_at DESC',
                (user_id, evaluation_type))
            else:
                cursor.execute('SELECT * FROM evaluations WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            evaluations = []
            for row in rows:
                evaluations.append({
                    'evaluation_id': row[1],
                    'evaluation_type': row[3],
                    'score': row[5],
                    'grade': row[7],
                    'feedback': row[8],
                    'created_at': row[12]
                })
            
            return evaluations
        except Exception as e:
            logger.info(f"[AI Intelligent Evaluation] 获取用户评估失败: {e}")
            return []
    
    def get_evaluation_summary(self):
        try:
            conn = sqlite3.connect('intelligent_evaluation.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM evaluations')
            total = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(DISTINCT user_id) FROM evaluations')
            users = cursor.fetchone()[0]
            
            cursor.execute('SELECT evaluation_type, COUNT(*) FROM evaluations GROUP BY evaluation_type')
            type_counts = {}
            for row in cursor.fetchall():
                type_counts[row[0]] = row[1]
            
            cursor.execute('SELECT AVG(score) FROM evaluations')
            avg_score = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT grade, COUNT(*) FROM evaluations GROUP BY grade')
            grade_distribution = {}
            for row in cursor.fetchall():
                grade_distribution[row[0]] = row[1]
            
            conn.close()
            
            return {
                'total_evaluations': total,
                'total_users': users,
                'type_distribution': type_counts,
                'average_score': round(avg_score, 2),
                'grade_distribution': grade_distribution
            }
        except Exception as e:
            logger.info(f"[AI Intelligent Evaluation] 获取评估摘要失败: {e}")
            return {}
    
    def get_user_evaluation_trend(self, user_id, evaluation_type):
        try:
            conn = sqlite3.connect('intelligent_evaluation.db')
            cursor = conn.cursor()
            
            cursor.execute(''' SELECT evaluation_date, score, grade, trend FROM user_evaluation_history WHERE user_id = ? AND evaluation_type = ? ORDER BY evaluation_date DESC LIMIT 10 ''', (user_id, evaluation_type))
            
            rows = cursor.fetchall()
            conn.close()
            
            trend_data = []
            for row in rows:
                trend_data.append({
                    'date': row[0],
                    'score': row[1],
                    'grade': row[2],
                    'trend': row[3]
                })
            
            return trend_data[::-1]
        except Exception as e:
            logger.info(f"[AI Intelligent Evaluation] 获取评估趋势失败: {e}")
            return []

intelligent_evaluation_system = AIIntelligentEvaluationSystem()