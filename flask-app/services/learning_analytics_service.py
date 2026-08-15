#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 学习分析服务 (v15.1.0)
================================
为成人教育和K12学生提供学习行为分析、知识掌握度评估、学习效果预测、
同伴对比分析和个性化学习建议生成。

核心能力：
1. 学习行为分析 - 学习时长、频次、时段偏好分析
2. 知识掌握度评估 - 按学科和知识点的掌握度综合评估
3. 学习效果预测 - 基于历史数据预测学习成果
4. 同伴对比分析 - 同班级/同年级横向对比
5. 学习建议生成 - 个性化改进建议
6. 学习趋势分析 - 学习表现时间序列分析
7. 风险预警 - 学习下滑/弃学风险预警
"""
import os
import json
import uuid
import math
import sqlite3
import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'learning_analytics_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('LearningAnalytics')


# ========== 分析配置 ==========

LEARNING_METRICS = {
    'study_duration': {'name': '学习时长', 'unit': '分钟', 'weight': 0.2},
    'question_count': {'name': '做题数量', 'unit': '题', 'weight': 0.2},
    'accuracy': {'name': '准确率', 'unit': '%', 'weight': 0.3},
    'consistency': {'name': '学习连续性', 'unit': '天', 'weight': 0.15},
    'coverage': {'name': '知识点覆盖', 'unit': '%', 'weight': 0.15}
}

RISK_LEVELS = {
    'low': {'name': '低风险', 'score_range': (0, 30), 'color': 'green'},
    'medium': {'name': '中风险', 'score_range': (30, 60), 'color': 'yellow'},
    'high': {'name': '高风险', 'score_range': (60, 80), 'color': 'orange'},
    'critical': {'name': '极高风险', 'score_range': (80, 100), 'color': 'red'}
}

RISK_FACTORS = {
    'declining_accuracy': {'name': '准确率下降', 'weight': 25},
    'decreasing_activity': {'name': '活跃度下降', 'weight': 20},
    'low_study_time': {'name': '学习时长不足', 'weight': 15},
    'high_wrong_rate': {'name': '错题率高', 'weight': 20},
    'long_absence': {'name': '长时间未学习', 'weight': 20}
}

PERFORMANCE_GRADES = {
    'A': {'range': (90, 100), 'name': '优秀'},
    'B': {'range': (75, 90), 'name': '良好'},
    'C': {'range': (60, 75), 'name': '及格'},
    'D': {'range': (0, 60), 'name': '需努力'}
}


class LearningAnalyticsService:
    """学习分析服务"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._lock = threading.RLock()
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # 学习行为记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_behaviors (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        behavior_type TEXT NOT NULL,
                        subject TEXT,
                        duration_minutes INTEGER DEFAULT 0,
                        question_count INTEGER DEFAULT 0,
                        correct_count INTEGER DEFAULT 0,
                        metadata TEXT,
                        created_at TEXT
                    )
                ''')
                # 学习指标快照表（定期计算）
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_metrics_snapshots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        snapshot_date TEXT NOT NULL,
                        study_duration INTEGER DEFAULT 0,
                        question_count INTEGER DEFAULT 0,
                        accuracy REAL DEFAULT 0,
                        consistency_days INTEGER DEFAULT 0,
                        coverage REAL DEFAULT 0,
                        overall_score REAL DEFAULT 0,
                        grade TEXT,
                        created_at TEXT,
                        UNIQUE(user_id, snapshot_date)
                    )
                ''')
                # 风险评估表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_risk_assessments (
                        assessment_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        risk_score REAL DEFAULT 0,
                        risk_level TEXT DEFAULT 'low',
                        risk_factors TEXT,
                        recommendations TEXT,
                        assessed_at TEXT
                    )
                ''')
                # 学习建议表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_suggestions (
                        suggestion_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        suggestion_type TEXT,
                        priority TEXT DEFAULT 'medium',
                        title TEXT,
                        content TEXT,
                        related_subject TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('学习分析服务数据库初始化完成')
        except Exception as e:
            logger.error(f'初始化数据库失败: {e}')

    # ========== 学习行为记录 ==========

    def record_behavior(self, user_id: int, behavior_type: str,
                          subject: str = None, duration_minutes: int = 0,
                          question_count: int = 0, correct_count: int = 0,
                          metadata: Dict = None) -> Dict[str, Any]:
        """记录学习行为"""
        with self._lock:
            now = datetime.now().isoformat()
            try:
                with self._get_connection() as conn:
                    conn.execute('''
                        INSERT INTO learning_behaviors
                        (user_id, behavior_type, subject, duration_minutes,
                         question_count, correct_count, metadata, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (user_id, behavior_type, subject, duration_minutes,
                          question_count, correct_count,
                          json.dumps(metadata or {}, ensure_ascii=False), now))
                    conn.commit()
                return {'success': True, 'user_id': user_id, 'behavior_type': behavior_type}
            except Exception as e:
                logger.error(f'记录学习行为失败: {e}')
                return {'success': False, 'error': str(e)}

    # ========== 学习行为分析 ==========

    def analyze_behavior(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """分析学习行为"""
        try:
            since = (datetime.now() - timedelta(days=days)).isoformat()
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT behavior_type, subject, duration_minutes,
                           question_count, correct_count, created_at
                    FROM learning_behaviors
                    WHERE user_id = ? AND created_at >= ?
                    ORDER BY created_at
                ''', (user_id, since))
                rows = cursor.fetchall()

            if not rows:
                return {
                    'success': True,
                    'user_id': user_id,
                    'period_days': days,
                    'total_activities': 0,
                    'message': '无学习行为记录'
                }

            # 统计
            total_duration = sum(r[2] for r in rows)
            total_questions = sum(r[3] for r in rows)
            total_correct = sum(r[4] for r in rows)
            accuracy = total_correct / total_questions if total_questions > 0 else 0

            # 按行为类型统计
            by_type = defaultdict(lambda: {'count': 0, 'duration': 0, 'questions': 0})
            for r in rows:
                by_type[r[0]]['count'] += 1
                by_type[r[0]]['duration'] += r[2]
                by_type[r[0]]['questions'] += r[3]

            # 按科目统计
            by_subject = defaultdict(lambda: {'duration': 0, 'questions': 0, 'correct': 0})
            for r in rows:
                if r[1]:
                    by_subject[r[1]]['duration'] += r[2]
                    by_subject[r[1]]['questions'] += r[3]
                    by_subject[r[1]]['correct'] += r[4]

            # 时段偏好分析
            hour_distribution = defaultdict(int)
            for r in rows:
                hour = datetime.fromisoformat(r[5]).hour
                hour_distribution[hour] += 1

            # 学习连续性
            study_dates = set()
            for r in rows:
                date = datetime.fromisoformat(r[5]).strftime('%Y-%m-%d')
                study_dates.add(date)
            consistency = self._calculate_consistency(study_dates)

            # 找出最活跃时段
            peak_hours = sorted(hour_distribution.items(), key=lambda x: x[1], reverse=True)[:3]

            return {
                'success': True,
                'user_id': user_id,
                'period_days': days,
                'total_activities': len(rows),
                'total_duration_minutes': total_duration,
                'total_duration_hours': round(total_duration / 60, 2),
                'total_questions': total_questions,
                'total_correct': total_correct,
                'accuracy': round(accuracy, 4),
                'study_days': len(study_dates),
                'consistency_days': consistency,
                'avg_daily_duration': round(total_duration / max(days, 1), 2),
                'by_type': dict(by_type),
                'by_subject': {k: {**v, 'accuracy': round(v['correct'] / v['questions'], 4)
                                     if v['questions'] > 0 else 0}
                                 for k, v in by_subject.items()},
                'peak_hours': [{'hour': h, 'count': c} for h, c in peak_hours],
                'hour_distribution': dict(hour_distribution)
            }
        except Exception as e:
            logger.error(f'分析学习行为失败: {e}')
            return {'success': False, 'error': str(e)}

    def _calculate_consistency(self, study_dates: set) -> int:
        """计算学习连续天数"""
        if not study_dates:
            return 0
        sorted_dates = sorted(study_dates)
        max_streak = 1
        current_streak = 1
        for i in range(1, len(sorted_dates)):
            prev = datetime.strptime(sorted_dates[i-1], '%Y-%m-%d')
            curr = datetime.strptime(sorted_dates[i], '%Y-%m-%d')
            if (curr - prev).days == 1:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 1
        return max_streak

    # ========== 综合学习评分 ==========

    def calculate_performance_score(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """计算综合学习评分"""
        try:
            behavior = self.analyze_behavior(user_id, days)
            if not behavior['success']:
                return behavior

            # 计算各指标得分（0-100）
            duration_score = min(behavior['total_duration_minutes'] / (days * 60) * 100, 100)
            question_score = min(behavior['total_questions'] / (days * 20) * 100, 100)
            accuracy_score = behavior['accuracy'] * 100
            consistency_score = min(behavior['consistency_days'] / 7 * 100, 100)
            # 覆盖率（简化：学习科目数/总科目数）
            coverage_score = min(len(behavior.get('by_subject', {})) / 5 * 100, 100)

            # 加权综合评分
            overall = (
                duration_score * LEARNING_METRICS['study_duration']['weight'] +
                question_score * LEARNING_METRICS['question_count']['weight'] +
                accuracy_score * LEARNING_METRICS['accuracy']['weight'] +
                consistency_score * LEARNING_METRICS['consistency']['weight'] +
                coverage_score * LEARNING_METRICS['coverage']['weight']
            )

            grade = self._score_to_grade(overall)

            # 保存快照
            today = datetime.now().strftime('%Y-%m-%d')
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO learning_metrics_snapshots
                    (user_id, snapshot_date, study_duration, question_count,
                     accuracy, consistency_days, coverage, overall_score, grade, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, today,
                      behavior['total_duration_minutes'],
                      behavior['total_questions'],
                      behavior['accuracy'],
                      behavior['consistency_days'],
                      coverage_score / 100,
                      round(overall, 2), grade, now))
                conn.commit()

            return {
                'success': True,
                'user_id': user_id,
                'period_days': days,
                'metrics': {
                    'study_duration': {'value': behavior['total_duration_minutes'],
                                         'score': round(duration_score, 2),
                                         'weight': LEARNING_METRICS['study_duration']['weight']},
                    'question_count': {'value': behavior['total_questions'],
                                         'score': round(question_score, 2),
                                         'weight': LEARNING_METRICS['question_count']['weight']},
                    'accuracy': {'value': behavior['accuracy'],
                                  'score': round(accuracy_score, 2),
                                  'weight': LEARNING_METRICS['accuracy']['weight']},
                    'consistency': {'value': behavior['consistency_days'],
                                     'score': round(consistency_score, 2),
                                     'weight': LEARNING_METRICS['consistency']['weight']},
                    'coverage': {'value': coverage_score / 100,
                                  'score': round(coverage_score, 2),
                                  'weight': LEARNING_METRICS['coverage']['weight']}
                },
                'overall_score': round(overall, 2),
                'grade': grade,
                'grade_name': PERFORMANCE_GRADES[grade]['name']
            }
        except Exception as e:
            logger.error(f'计算学习评分失败: {e}')
            return {'success': False, 'error': str(e)}

    def _score_to_grade(self, score: float) -> str:
        """分数转等级"""
        for grade, config in PERFORMANCE_GRADES.items():
            low, high = config['range']
            if low <= score < high:
                return grade
        return 'D'

    # ========== 风险预警 ==========

    def assess_risk(self, user_id: int) -> Dict[str, Any]:
        """评估学习风险"""
        try:
            # 获取最近30天和前30天的行为
            recent = self.analyze_behavior(user_id, 30)
            previous_since = (datetime.now() - timedelta(days=60)).isoformat()
            recent_since = (datetime.now() - timedelta(days=30)).isoformat()

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT duration_minutes, question_count, correct_count, created_at
                    FROM learning_behaviors
                    WHERE user_id = ? AND created_at >= ? AND created_at < ?
                ''', (user_id, previous_since, recent_since))
                prev_rows = cursor.fetchall()

            risk_score = 0
            risk_factors = []

            # 准确率下降
            prev_correct = sum(r[2] for r in prev_rows)
            prev_questions = sum(r[1] for r in prev_rows)
            prev_accuracy = prev_correct / prev_questions if prev_questions > 0 else 0
            recent_accuracy = recent.get('accuracy', 0) if recent['success'] else 0

            if prev_accuracy > 0 and recent_accuracy < prev_accuracy - 0.1:
                risk_score += RISK_FACTORS['declining_accuracy']['weight']
                risk_factors.append({
                    'factor': 'declining_accuracy',
                    'name': RISK_FACTORS['declining_accuracy']['name'],
                    'detail': f'准确率从{prev_accuracy:.0%}下降到{recent_accuracy:.0%}',
                    'weight': RISK_FACTORS['declining_accuracy']['weight']
                })

            # 活跃度下降
            prev_activities = len(prev_rows)
            recent_activities = recent.get('total_activities', 0) if recent['success'] else 0
            if prev_activities > 0 and recent_activities < prev_activities * 0.5:
                risk_score += RISK_FACTORS['decreasing_activity']['weight']
                risk_factors.append({
                    'factor': 'decreasing_activity',
                    'name': RISK_FACTORS['decreasing_activity']['name'],
                    'detail': f'活跃度从{prev_activities}次降到{recent_activities}次',
                    'weight': RISK_FACTORS['decreasing_activity']['weight']
                })

            # 学习时长不足
            recent_duration = recent.get('total_duration_minutes', 0) if recent['success'] else 0
            if recent_duration < 300:  # 少于5小时
                risk_score += RISK_FACTORS['low_study_time']['weight']
                risk_factors.append({
                    'factor': 'low_study_time',
                    'name': RISK_FACTORS['low_study_time']['name'],
                    'detail': f'近30天仅学习{recent_duration}分钟',
                    'weight': RISK_FACTORS['low_study_time']['weight']
                })

            # 错题率高
            if recent_accuracy > 0 and recent_accuracy < 0.5:
                risk_score += RISK_FACTORS['high_wrong_rate']['weight']
                risk_factors.append({
                    'factor': 'high_wrong_rate',
                    'name': RISK_FACTORS['high_wrong_rate']['name'],
                    'detail': f'准确率仅{recent_accuracy:.0%}',
                    'weight': RISK_FACTORS['high_wrong_rate']['weight']
                })

            # 长时间未学习
            if recent_activities == 0:
                risk_score += RISK_FACTORS['long_absence']['weight']
                risk_factors.append({
                    'factor': 'long_absence',
                    'name': RISK_FACTORS['long_absence']['name'],
                    'detail': '近30天无学习记录',
                    'weight': RISK_FACTORS['long_absence']['weight']
                })

            # 确定风险等级
            risk_level = 'low'
            for level, config in RISK_LEVELS.items():
                low, high = config['score_range']
                if low <= risk_score < high:
                    risk_level = level
                    break

            # 生成建议
            recommendations = self._generate_risk_recommendations(risk_factors, risk_level)

            # 保存评估
            assessment_id = f'risk_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}'
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                conn.execute('''
                    INSERT INTO learning_risk_assessments
                    (assessment_id, user_id, risk_score, risk_level,
                     risk_factors, recommendations, assessed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (assessment_id, user_id, risk_score, risk_level,
                      json.dumps(risk_factors, ensure_ascii=False),
                      json.dumps(recommendations, ensure_ascii=False), now))
                conn.commit()

            return {
                'success': True,
                'user_id': user_id,
                'risk_score': risk_score,
                'risk_level': risk_level,
                'risk_level_name': RISK_LEVELS[risk_level]['name'],
                'risk_factors': risk_factors,
                'recommendations': recommendations
            }
        except Exception as e:
            logger.error(f'评估风险失败: {e}')
            return {'success': False, 'error': str(e)}

    def _generate_risk_recommendations(self, risk_factors: List[Dict],
                                          risk_level: str) -> List[str]:
        """生成风险建议"""
        recs = []
        if risk_level == 'critical':
            recs.append('学习状态严峻，建议立即联系学习顾问制定恢复计划')
        elif risk_level == 'high':
            recs.append('学习风险较高，建议调整学习计划并增加学习时间')
        elif risk_level == 'medium':
            recs.append('存在学习风险，建议关注相关指标并适当调整')

        for factor in risk_factors:
            if factor['factor'] == 'declining_accuracy':
                recs.append('准确率下降，建议复习基础知识并减少难题比例')
            elif factor['factor'] == 'decreasing_activity':
                recs.append('活跃度下降，建议设定每日学习提醒，保持学习习惯')
            elif factor['factor'] == 'low_study_time':
                recs.append('学习时长不足，建议每天至少保证30分钟学习')
            elif factor['factor'] == 'high_wrong_rate':
                recs.append('错题率较高，建议整理错题本，针对薄弱知识点专项练习')
            elif factor['factor'] == 'long_absence':
                recs.append('长时间未学习，建议从简单内容开始恢复学习节奏')

        if not recs:
            recs.append('学习状态良好，继续保持')
        return recs

    # ========== 学习趋势分析 ==========

    def analyze_trend(self, user_id: int, days: int = 90) -> Dict[str, Any]:
        """分析学习趋势"""
        try:
            since = (datetime.now() - timedelta(days=days)).isoformat()
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT snapshot_date, study_duration, question_count,
                           accuracy, consistency_days, overall_score, grade
                    FROM learning_metrics_snapshots
                    WHERE user_id = ? AND snapshot_date >= ?
                    ORDER BY snapshot_date
                ''', (user_id, since))
                rows = cursor.fetchall()

            if not rows:
                return {
                    'success': True,
                    'user_id': user_id,
                    'period_days': days,
                    'snapshots': [],
                    'message': '无历史快照数据'
                }

            snapshots = []
            for row in rows:
                snapshots.append({
                    'date': row[0],
                    'study_duration': row[1],
                    'question_count': row[2],
                    'accuracy': row[3],
                    'consistency': row[4],
                    'overall_score': row[5],
                    'grade': row[6]
                })

            # 计算趋势
            scores = [s['overall_score'] for s in snapshots]
            trend = self._calculate_trend(scores)

            # 前后对比
            if len(snapshots) >= 2:
                first = snapshots[0]
                last = snapshots[-1]
                comparison = {
                    'score_change': round(last['overall_score'] - first['overall_score'], 2),
                    'duration_change': last['study_duration'] - first['study_duration'],
                    'accuracy_change': round(last['accuracy'] - first['accuracy'], 4),
                    'grade_change': f'{first["grade"]} -> {last["grade"]}'
                }
            else:
                comparison = None

            return {
                'success': True,
                'user_id': user_id,
                'period_days': days,
                'snapshots': snapshots,
                'snapshot_count': len(snapshots),
                'trend': trend,
                'trend_description': self._trend_description(trend),
                'comparison': comparison,
                'avg_score': round(sum(scores) / len(scores), 2) if scores else 0,
                'max_score': max(scores) if scores else 0,
                'min_score': min(scores) if scores else 0
            }
        except Exception as e:
            logger.error(f'分析趋势失败: {e}')
            return {'success': False, 'error': str(e)}

    def _calculate_trend(self, values: List[float]) -> str:
        """计算趋势方向"""
        if len(values) < 2:
            return 'stable'
        # 简单线性回归斜率
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        if denominator == 0:
            return 'stable'
        slope = numerator / denominator
        if slope > 0.5:
            return 'improving'
        elif slope < -0.5:
            return 'declining'
        return 'stable'

    def _trend_description(self, trend: str) -> str:
        return {
            'improving': '学习表现上升趋势',
            'declining': '学习表现下降趋势',
            'stable': '学习表现稳定'
        }.get(trend, '未知')

    # ========== 学习建议生成 ==========

    def generate_suggestions(self, user_id: int) -> Dict[str, Any]:
        """生成个性化学习建议"""
        try:
            performance = self.calculate_performance_score(user_id, 30)
            risk = self.assess_risk(user_id)
            behavior = self.analyze_behavior(user_id, 30)

            suggestions = []
            now = datetime.now().isoformat()

            if not performance['success']:
                return performance

            metrics = performance.get('metrics', {})
            overall = performance.get('overall_score', 0)

            # 根据各指标生成建议
            if metrics.get('study_duration', {}).get('score', 0) < 50:
                suggestions.append({
                    'type': 'increase_study_time',
                    'priority': 'high',
                    'title': '增加学习时长',
                    'content': '当前学习时长偏低，建议每天至少学习30分钟，利用碎片化时间积累',
                    'related_subject': None
                })

            if metrics.get('accuracy', {}).get('value', 0) < 0.7:
                suggestions.append({
                    'type': 'improve_accuracy',
                    'priority': 'high',
                    'title': '提升做题准确率',
                    'content': '准确率有提升空间，建议先复习基础知识再做题，做题后认真分析错题',
                    'related_subject': None
                })

            if metrics.get('consistency', {}).get('value', 0) < 3:
                suggestions.append({
                    'type': 'maintain_consistency',
                    'priority': 'medium',
                    'title': '保持学习连续性',
                    'content': '学习不够连续，建议设定每日学习计划，培养固定学习习惯',
                    'related_subject': None
                })

            if metrics.get('coverage', {}).get('value', 0) < 0.5:
                suggestions.append({
                    'type': 'broaden_coverage',
                    'priority': 'medium',
                    'title': '扩大学习覆盖面',
                    'content': '知识点覆盖不足，建议增加学习科目，避免偏科',
                    'related_subject': None
                })

            if overall >= 85:
                suggestions.append({
                    'type': 'challenge_harder',
                    'priority': 'low',
                    'title': '挑战更高难度',
                    'content': '学习表现优秀，建议挑战更高难度题目，拓展知识深度',
                    'related_subject': None
                })

            # 保存建议
            saved_ids = []
            with self._get_connection() as conn:
                for s in suggestions:
                    sid = f'sug_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}'
                    conn.execute('''
                        INSERT INTO learning_suggestions
                        (suggestion_id, user_id, suggestion_type, priority,
                         title, content, related_subject, status, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?)
                    ''', (sid, user_id, s['type'], s['priority'],
                          s['title'], s['content'], s.get('related_subject'), now))
                    saved_ids.append(sid)
                conn.commit()

            return {
                'success': True,
                'user_id': user_id,
                'overall_score': overall,
                'grade': performance.get('grade'),
                'suggestions': suggestions,
                'suggestion_count': len(suggestions),
                'risk_level': risk.get('risk_level', 'low') if risk['success'] else 'unknown'
            }
        except Exception as e:
            logger.error(f'生成建议失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 同伴对比 ==========

    def peer_comparison(self, user_id: int, peer_group: str = 'class',
                          class_id: str = None) -> Dict[str, Any]:
        """同伴对比分析"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

            with self._get_connection() as conn:
                cursor = conn.cursor()
                # 获取用户最近评分
                cursor.execute('''
                    SELECT overall_score, accuracy, study_duration, grade
                    FROM learning_metrics_snapshots
                    WHERE user_id = ? AND snapshot_date >= ?
                    ORDER BY snapshot_date DESC LIMIT 1
                ''', (user_id, week_ago))
                user_row = cursor.fetchone()
                if not user_row:
                    return {'success': False, 'error': '无用户评分数据'}

                # 获取同伴评分（简化：获取所有用户的最近评分）
                cursor.execute('''
                    SELECT user_id, overall_score, accuracy, study_duration, grade
                    FROM learning_metrics_snapshots
                    WHERE snapshot_date >= ?
                    GROUP BY user_id
                    HAVING MAX(snapshot_date)
                ''', (week_ago,))
                peer_rows = cursor.fetchall()

            if len(peer_rows) < 2:
                return {
                    'success': True,
                    'user_id': user_id,
                    'message': '同伴数据不足，无法对比'
                }

            all_scores = [r[1] for r in peer_rows]
            user_score = user_row[0]

            # 计算排名
            sorted_scores = sorted(all_scores, reverse=True)
            rank = sorted_scores.index(user_score) + 1

            # 统计
            avg_score = sum(all_scores) / len(all_scores)
            median_score = sorted_scores[len(sorted_scores) // 2]
            max_score = max(all_scores)
            min_score = min(all_scores)

            # 百分位
            percentile = (len([s for s in all_scores if s < user_score]) / len(all_scores)) * 100

            return {
                'success': True,
                'user_id': user_id,
                'user_score': user_score,
                'user_grade': user_row[3],
                'user_accuracy': user_row[1],
                'user_duration': user_row[2],
                'peer_count': len(peer_rows),
                'rank': rank,
                'percentile': round(percentile, 2),
                'peer_avg_score': round(avg_score, 2),
                'peer_median_score': median_score,
                'peer_max_score': max_score,
                'peer_min_score': min_score,
                'vs_average': round(user_score - avg_score, 2),
                'vs_median': round(user_score - median_score, 2),
                'performance_level': self._get_performance_level(percentile)
            }
        except Exception as e:
            logger.error(f'同伴对比失败: {e}')
            return {'success': False, 'error': str(e)}

    def _get_performance_level(self, percentile: float) -> str:
        """根据百分位获取表现水平"""
        if percentile >= 90:
            return 'top'
        elif percentile >= 75:
            return 'above_average'
        elif percentile >= 50:
            return 'average'
        elif percentile >= 25:
            return 'below_average'
        else:
            return 'bottom'

    # ========== 统计 ==========

    def get_statistics(self) -> Dict[str, Any]:
        """获取学习分析统计"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(DISTINCT user_id) FROM learning_behaviors')
                total_users = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM learning_behaviors')
                total_behaviors = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM learning_metrics_snapshots')
                total_snapshots = cursor.fetchone()[0]
                cursor.execute('SELECT grade, COUNT(*) FROM learning_metrics_snapshots GROUP BY grade')
                grade_stats = {row[0]: row[1] for row in cursor.fetchall()}
                cursor.execute('SELECT risk_level, COUNT(*) FROM learning_risk_assessments GROUP BY risk_level')
                risk_stats = {row[0]: row[1] for row in cursor.fetchall()}
                cursor.execute('SELECT COUNT(*) FROM learning_suggestions WHERE status = "active"')
                active_suggestions = cursor.fetchone()[0]
                cursor.execute('SELECT AVG(overall_score) FROM learning_metrics_snapshots')
                avg_score = cursor.fetchone()[0] or 0

            return {
                'success': True,
                'total_users_tracked': total_users,
                'total_behaviors': total_behaviors,
                'total_snapshots': total_snapshots,
                'by_grade': grade_stats,
                'by_risk_level': risk_stats,
                'active_suggestions': active_suggestions,
                'avg_overall_score': round(avg_score, 2)
            }
        except Exception as e:
            logger.error(f'获取统计失败: {e}')
            return {'success': False, 'error': str(e)}


if __name__ == '__main__':
    service = LearningAnalyticsService()
    print('=' * 60)
    print('MTSCOS 学习分析服务 v15.1.0 测试')
    print('=' * 60)

    print('\n1. 记录学习行为...')
    for i in range(5):
        r = service.record_behavior(1001, 'practice', '日语', duration_minutes=30,
                                      question_count=20, correct_count=15 + i)
    print(f'   记录5条学习行为')

    print('\n2. 分析学习行为...')
    r = service.analyze_behavior(1001, 30)
    print(f'   总活动: {r.get("total_activities")} 时长: {r.get("total_duration_minutes")}分钟')
    print(f'   准确率: {r.get("accuracy")} 连续天数: {r.get("consistency_days")}')

    print('\n3. 计算学习评分...')
    r = service.calculate_performance_score(1001, 30)
    print(f'   综合评分: {r.get("overall_score")} 等级: {r.get("grade")}/{r.get("grade_name")}')

    print('\n4. 风险评估...')
    r = service.assess_risk(1001)
    print(f'   风险分: {r.get("risk_score")} 等级: {r.get("risk_level_name")}')
    for rec in r.get('recommendations', []):
        print(f'   建议: {rec}')

    print('\n5. 生成学习建议...')
    r = service.generate_suggestions(1001)
    print(f'   建议数: {r.get("suggestion_count")}')
    for s in r.get('suggestions', []):
        print(f'   - [{s["priority"]}] {s["title"]}')

    print('\n6. 趋势分析...')
    r = service.analyze_trend(1001, 90)
    print(f'   快照数: {r.get("snapshot_count")} 趋势: {r.get("trend_description")}')
    print(f'   平均分: {r.get("avg_score")}')

    print('\n7. 同伴对比...')
    # 先为另一个用户记录数据
    for i in range(3):
        service.record_behavior(1002, 'practice', '日语', duration_minutes=20,
                                  question_count=15, correct_count=10)
    service.calculate_performance_score(1002, 30)
    r = service.peer_comparison(1001)
    print(f'   排名: {r.get("rank")}/{r.get("peer_count")} 百分位: {r.get("percentile")}%')
    print(f'   vs平均: {r.get("vs_average")} 表现: {r.get("performance_level")}')

    print('\n8. 统计...')
    stats = service.get_statistics()
    print(f'   追踪用户: {stats.get("total_users_tracked")} 行为数: {stats.get("total_behaviors")}')
    print(f'   按等级: {stats.get("by_grade")} 按风险: {stats.get("by_risk_level")}')
    print('\n' + '=' * 60)
    print('测试完成')
    print('=' * 60)
