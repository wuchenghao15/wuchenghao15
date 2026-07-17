# -*- coding: utf-8 -*-
"""
学习预测分析引擎
提供成绩预测、退学预警、学习风险评估、趋势分析等功能
基于历史数据进行预测性分析
"""

import os
import sys
import json
import time
import sqlite3
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('learning_prediction_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('LearningPredictionEngine')

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')


class LearningPredictionEngine:
    """学习预测分析引擎 - 基于历史数据预测学习表现"""

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._lock = threading.RLock()
        self._init_database()
        self._initialized = True
        logger.info("LearningPredictionEngine 初始化完成")

    def _init_database(self):
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS prediction_models (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        model_name TEXT NOT NULL,
                        model_type TEXT NOT NULL,
                        version TEXT DEFAULT '1.0',
                        parameters TEXT DEFAULT '{}',
                        accuracy REAL DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(model_name, model_type)
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS score_predictions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        subject TEXT,
                        predicted_score REAL,
                        confidence REAL,
                        prediction_horizon TEXT,
                        factors TEXT,
                        model_used TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS dropout_risk_assessments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        risk_level TEXT,
                        risk_score REAL,
                        risk_factors TEXT,
                        recommendations TEXT,
                        assessed_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_trends (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        subject TEXT,
                        trend_type TEXT,
                        trend_direction TEXT,
                        trend_data TEXT,
                        slope REAL,
                        r_squared REAL,
                        analyzed_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS prediction_alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        alert_type TEXT,
                        severity TEXT,
                        title TEXT,
                        description TEXT,
                        recommended_action TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                cursor.execute('CREATE INDEX IF NOT EXISTS idx_sp_user ON score_predictions(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_dr_user ON dropout_risk_assessments(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_lt_user ON learning_trends(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_pa_user ON prediction_alerts(user_id)')

                conn.commit()
        except Exception as e:
            logger.error(f"初始化预测引擎数据库失败: {e}")

    def _get_user_scores(self, user_id: str, subject: str = None, limit: int = 20) -> List[Dict]:
        """获取用户历史成绩（关联 exams 表获取科目）"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                # exam_results 表使用 total_score/created_at，关联 exams 表获取 subject
                sql = '''
                    SELECT er.total_score, COALESCE(e.subject, '未知'),
                           er.created_at, er.total_count, er.correct_count
                    FROM exam_results er
                    LEFT JOIN exams e ON er.exam_id = e.id
                    WHERE er.user_id = ?
                '''
                params = [user_id]
                if subject:
                    sql += ' AND e.subject = ?'
                    params.append(subject)
                sql += ' ORDER BY er.created_at ASC LIMIT ?'
                params.append(limit)

                try:
                    cursor.execute(sql, params)
                    return [{'score': r[0], 'subject': r[1], 'date': r[2],
                             'total': r[3], 'correct': r[4]} for r in cursor.fetchall()]
                except Exception:
                    return []
        except Exception:
            return []

    def _get_user_activity(self, user_id: str, days: int = 30) -> Dict:
        """获取用户活动数据"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                since = (datetime.now() - timedelta(days=days)).isoformat()

                cursor.execute('''
                    SELECT COUNT(*) FROM exam_results
                    WHERE user_id = ? AND created_at > ?
                ''', (user_id, since))
                exam_count = cursor.fetchone()[0]

                cursor.execute('''
                    SELECT COUNT(*) FROM wrong_questions
                    WHERE user_id = ? AND created_at > ?
                ''', (user_id, since))
                wrong_count = cursor.fetchone()[0]

                cursor.execute('''
                    SELECT COUNT(*) FROM point_transactions
                    WHERE user_id = ? AND created_at > ?
                ''', (user_id, since))
                activity_count = cursor.fetchone()[0]

                cursor.execute('''
                    SELECT consecutive_days, last_login_date
                    FROM user_points WHERE user_id = ?
                ''', (user_id,))
                login_row = cursor.fetchone()
                consecutive = login_row[0] if login_row else 0
                last_login = login_row[1] if login_row else None

            return {
                'exam_count_30d': exam_count,
                'wrong_count_30d': wrong_count,
                'activity_count_30d': activity_count,
                'consecutive_days': consecutive,
                'last_login_date': last_login,
                'days_since_last_login': self._days_since(last_login)
            }
        except Exception as e:
            logger.error(f"获取用户活动数据失败: {e}")
            return {
                'exam_count_30d': 0, 'wrong_count_30d': 0, 'activity_count_30d': 0,
                'consecutive_days': 0, 'last_login_date': None, 'days_since_last_login': 999
            }

    def _days_since(self, date_str: str) -> int:
        if not date_str:
            return 999
        try:
            d = datetime.fromisoformat(date_str.split(' ')[0])
            return (datetime.now() - d).days
        except Exception:
            return 999

    def predict_score(self, user_id: str, subject: str = None,
                      horizon: str = 'next_exam') -> Dict[str, Any]:
        """预测下次考试成绩 - 基于线性回归"""
        with self._lock:
            try:
                scores = self._get_user_scores(user_id, subject, 20)

                if len(scores) < 3:
                    return {
                        'success': True,
                        'prediction_available': False,
                        'message': '历史数据不足，至少需要3次考试记录',
                        'data_points': len(scores)
                    }

                score_values = [s['score'] for s in scores]
                n = len(score_values)
                x = list(range(n))

                x_mean = sum(x) / n
                y_mean = sum(score_values) / n

                numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, score_values))
                denominator = sum((xi - x_mean) ** 2 for xi in x)

                if denominator == 0:
                    slope = 0
                    intercept = y_mean
                else:
                    slope = numerator / denominator
                    intercept = y_mean - slope * x_mean

                y_pred = [slope * xi + intercept for xi in x]
                ss_res = sum((yi - yp) ** 2 for yi, yp in zip(score_values, y_pred))
                ss_tot = sum((yi - y_mean) ** 2 for yi in score_values)
                r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

                next_x = n
                predicted = max(0, min(100, slope * next_x + intercept))

                confidence = max(0.3, min(0.95, r_squared * 0.7 + (n / 20) * 0.3))

                trend_direction = '上升' if slope > 1 else ('下降' if slope < -1 else '稳定')
                avg_score = sum(score_values) / n
                last_score = score_values[-1]
                score_std = (sum((s - y_mean) ** 2 for s in score_values) / n) ** 0.5

                factors = {
                    'historical_avg': round(avg_score, 1),
                    'last_score': last_score,
                    'trend_slope': round(slope, 2),
                    'trend_direction': trend_direction,
                    'score_stability': round(score_std, 1),
                    'data_points': n,
                    'r_squared': round(r_squared, 3)
                }

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO score_predictions
                        (user_id, subject, predicted_score, confidence,
                         prediction_horizon, factors, model_used)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (user_id, subject or 'all', round(predicted, 1),
                          round(confidence, 2), horizon,
                          json.dumps(factors, ensure_ascii=False),
                          'linear_regression_v1'))
                    conn.commit()

                return {
                    'success': True,
                    'prediction_available': True,
                    'user_id': user_id,
                    'subject': subject or 'all',
                    'predicted_score': round(predicted, 1),
                    'confidence': round(confidence, 2),
                    'confidence_level': 'high' if confidence > 0.7 else ('medium' if confidence > 0.5 else 'low'),
                    'prediction_horizon': horizon,
                    'factors': factors,
                    'trend': {
                        'direction': trend_direction,
                        'slope': round(slope, 2),
                        'r_squared': round(r_squared, 3)
                    }
                }
            except Exception as e:
                logger.error(f"成绩预测失败: {e}")
                return {'success': False, 'error': str(e)}

    def assess_dropout_risk(self, user_id: str) -> Dict[str, Any]:
        """评估退学风险"""
        with self._lock:
            try:
                activity = self._get_user_activity(user_id, 30)
                scores = self._get_user_scores(user_id, None, 10)

                risk_factors = []
                risk_score = 0

                if activity['days_since_last_login'] > 14:
                    risk_factors.append({
                        'factor': 'long_absence',
                        'description': f'已经 {activity["days_since_last_login"]} 天未登录',
                        'weight': 30
                    })
                    risk_score += 30
                elif activity['days_since_last_login'] > 7:
                    risk_factors.append({
                        'factor': 'medium_absence',
                        'description': f'已经 {activity["days_since_last_login"]} 天未登录',
                        'weight': 15
                    })
                    risk_score += 15

                if activity['consecutive_days'] == 0:
                    risk_factors.append({
                        'factor': 'no_streak',
                        'description': '无连续学习记录',
                        'weight': 10
                    })
                    risk_score += 10

                if activity['exam_count_30d'] == 0:
                    risk_factors.append({
                        'factor': 'no_exams',
                        'description': '30天内无考试记录',
                        'weight': 20
                    })
                    risk_score += 20

                if activity['activity_count_30d'] < 5:
                    risk_factors.append({
                        'factor': 'low_activity',
                        'description': f'30天内活动仅 {activity["activity_count_30d"]} 次',
                        'weight': 15
                    })
                    risk_score += 15

                if scores:
                    recent_scores = [s['score'] for s in scores[-3:]]
                    avg_recent = sum(recent_scores) / len(recent_scores)
                    if avg_recent < 50:
                        risk_factors.append({
                            'factor': 'low_scores',
                            'description': f'近期平均分仅 {avg_recent:.0f} 分',
                            'weight': 20
                        })
                        risk_score += 20

                    if len(scores) >= 4:
                        first_half = sum(s['score'] for s in scores[:len(scores)//2]) / (len(scores)//2)
                        second_half = sum(s['score'] for s in scores[len(scores)//2:]) / (len(scores) - len(scores)//2)
                        if second_half < first_half - 10:
                            risk_factors.append({
                                'factor': 'declining_performance',
                                'description': f'成绩下降 ({first_half:.0f} → {second_half:.0f})',
                                'weight': 15
                            })
                            risk_score += 15

                risk_score = min(risk_score, 100)

                if risk_score >= 60:
                    risk_level = 'critical'
                    recommendations = [
                        '立即联系学生了解情况',
                        '安排一对一辅导',
                        '调整学习难度，从基础内容开始',
                        '通知家长关注学生状态'
                    ]
                elif risk_score >= 40:
                    risk_level = 'high'
                    recommendations = [
                        '发送鼓励消息',
                        '推荐复习基础知识点',
                        '降低学习强度，避免压力过大',
                        '安排同伴互助学习'
                    ]
                elif risk_score >= 20:
                    risk_level = 'medium'
                    recommendations = [
                        '关注学习进度',
                        '推送个性化学习建议',
                        '鼓励坚持每日学习'
                    ]
                else:
                    risk_level = 'low'
                    recommendations = ['继续保持良好的学习习惯']

                recommendations_json = json.dumps(recommendations, ensure_ascii=False)
                factors_json = json.dumps(risk_factors, ensure_ascii=False)

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO dropout_risk_assessments
                        (user_id, risk_level, risk_score, risk_factors, recommendations)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (user_id, risk_level, risk_score, factors_json, recommendations_json))

                    if risk_level in ['critical', 'high']:
                        cursor.execute('''
                            INSERT INTO prediction_alerts
                            (user_id, alert_type, severity, title, description, recommended_action)
                            VALUES (?, 'dropout_risk', ?, '退学风险预警',
                                    ?, ?)
                        ''', (user_id, risk_level,
                              f'用户 {user_id} 退学风险评分: {risk_score} ({risk_level})',
                              ' '.join(recommendations[:2])))

                    conn.commit()

                return {
                    'success': True,
                    'user_id': user_id,
                    'risk_level': risk_level,
                    'risk_score': risk_score,
                    'risk_factors': risk_factors,
                    'recommendations': recommendations,
                    'activity_summary': activity
                }
            except Exception as e:
                logger.error(f"退学风险评估失败: {e}")
                return {'success': False, 'error': str(e)}

    def analyze_trend(self, user_id: str, subject: str = None,
                       metric: str = 'score') -> Dict[str, Any]:
        """分析学习趋势"""
        with self._lock:
            try:
                scores = self._get_user_scores(user_id, subject, 30)

                if len(scores) < 2:
                    return {
                        'success': True,
                        'trend_available': False,
                        'message': '数据不足，无法分析趋势',
                        'data_points': len(scores)
                    }

                values = [s['score'] for s in scores]
                n = len(values)
                x = list(range(n))

                x_mean = sum(x) / n
                y_mean = sum(values) / n

                numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, values))
                denominator = sum((xi - x_mean) ** 2 for xi in x)

                slope = numerator / denominator if denominator > 0 else 0
                intercept = y_mean - slope * x_mean

                y_pred = [slope * xi + intercept for xi in x]
                ss_res = sum((yi - yp) ** 2 for yi, yp in zip(values, y_pred))
                ss_tot = sum((yi - y_mean) ** 2 for yi in values)
                r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

                if slope > 1:
                    direction = 'improving'
                    direction_text = '上升'
                elif slope < -1:
                    direction = 'declining'
                    direction_text = '下降'
                else:
                    direction = 'stable'
                    direction_text = '稳定'

                volatility = (sum((yi - y_mean) ** 2 for yi in values) / n) ** 0.5

                trend_data = {
                    'data_points': n,
                    'first_value': values[0],
                    'last_value': values[-1],
                    'avg_value': round(y_mean, 1),
                    'max_value': max(values),
                    'min_value': min(values),
                    'volatility': round(volatility, 2),
                    'improvement': round(values[-1] - values[0], 1)
                }

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO learning_trends
                        (user_id, subject, trend_type, trend_direction,
                         trend_data, slope, r_squared)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (user_id, subject or 'all', metric, direction,
                          json.dumps(trend_data, ensure_ascii=False),
                          round(slope, 3), round(r_squared, 3)))
                    conn.commit()

                return {
                    'success': True,
                    'trend_available': True,
                    'user_id': user_id,
                    'subject': subject or 'all',
                    'metric': metric,
                    'direction': direction,
                    'direction_text': direction_text,
                    'slope': round(slope, 3),
                    'r_squared': round(r_squared, 3),
                    'trend_data': trend_data,
                    'interpretation': self._interpret_trend(direction, slope, r_squared, volatility)
                }
            except Exception as e:
                logger.error(f"趋势分析失败: {e}")
                return {'success': False, 'error': str(e)}

    def _interpret_trend(self, direction: str, slope: float,
                          r_squared: float, volatility: float) -> str:
        if direction == 'improving':
            if r_squared > 0.7:
                return f'成绩稳定上升，平均每次提升 {slope:.1f} 分，进步明显'
            else:
                return f'整体上升但波动较大，建议保持学习节奏'
        elif direction == 'declining':
            if r_squared > 0.7:
                return f'成绩持续下降，平均每次降低 {abs(slope):.1f} 分，需要重点关注'
            else:
                return f'整体略有下降但波动较大，建议分析具体原因'
        else:
            if volatility < 5:
                return f'成绩稳定，平均 {100-abs(slope)*10:.0f} 分左右'
            else:
                return f'成绩波动较大（标准差 {volatility:.1f}），稳定性需要提升'

    def get_user_predictions(self, user_id: str) -> Dict[str, Any]:
        """获取用户的所有预测数据"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT subject, predicted_score, confidence, prediction_horizon,
                           factors, created_at
                    FROM score_predictions WHERE user_id = ?
                    ORDER BY created_at DESC LIMIT 10
                ''', (user_id,))
                predictions = [{
                    'subject': r[0],
                    'predicted_score': r[1],
                    'confidence': r[2],
                    'horizon': r[3],
                    'factors': json.loads(r[4]) if r[4] else {},
                    'created_at': r[5]
                } for r in cursor.fetchall()]

                cursor.execute('''
                    SELECT risk_level, risk_score, assessed_at
                    FROM dropout_risk_assessments WHERE user_id = ?
                    ORDER BY assessed_at DESC LIMIT 5
                ''', (user_id,))
                risks = [{
                    'risk_level': r[0],
                    'risk_score': r[1],
                    'assessed_at': r[2]
                } for r in cursor.fetchall()]

                cursor.execute('''
                    SELECT alert_type, severity, title, description, status, created_at
                    FROM prediction_alerts WHERE user_id = ?
                    ORDER BY created_at DESC LIMIT 10
                ''', (user_id,))
                alerts = [{
                    'alert_type': r[0],
                    'severity': r[1],
                    'title': r[2],
                    'description': r[3],
                    'status': r[4],
                    'created_at': r[5]
                } for r in cursor.fetchall()]

            return {
                'success': True,
                'user_id': user_id,
                'predictions': predictions,
                'risk_assessments': risks,
                'alerts': alerts,
                'has_alerts': len(alerts) > 0
            }
        except Exception as e:
            logger.error(f"获取用户预测数据失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_high_risk_users(self, threshold: str = 'high') -> Dict[str, Any]:
        """获取高风险用户列表"""
        try:
            levels = ['critical'] if threshold == 'critical' else ['critical', 'high']
            placeholders = ','.join('?' * len(levels))

            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(f'''
                    SELECT user_id, risk_level, risk_score, assessed_at
                    FROM dropout_risk_assessments
                    WHERE risk_level IN ({placeholders})
                    AND assessed_at = (
                        SELECT MAX(assessed_at) FROM dropout_risk_assessments d2
                        WHERE d2.user_id = dropout_risk_assessments.user_id
                    )
                    ORDER BY risk_score DESC
                ''', levels)
                rows = cursor.fetchall()

            users = [{
                'user_id': r[0],
                'risk_level': r[1],
                'risk_score': r[2],
                'assessed_at': r[3]
            } for r in rows]

            return {
                'success': True,
                'threshold': threshold,
                'total_high_risk': len(users),
                'users': users
            }
        except Exception as e:
            logger.error(f"获取高风险用户失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_statistics(self) -> Dict[str, Any]:
        """获取预测引擎统计"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM score_predictions')
                total_predictions = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(DISTINCT user_id) FROM score_predictions')
                predicted_users = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM dropout_risk_assessments')
                total_assessments = cursor.fetchone()[0]
                cursor.execute('SELECT risk_level, COUNT(*) FROM dropout_risk_assessments GROUP BY risk_level')
                by_risk = dict(cursor.fetchall())
                cursor.execute('SELECT COUNT(*) FROM prediction_alerts WHERE status = ?', ('active',))
                active_alerts = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM learning_trends')
                total_trends = cursor.fetchone()[0]

            return {
                'success': True,
                'total_predictions': total_predictions,
                'predicted_users': predicted_users,
                'total_assessments': total_assessments,
                'by_risk_level': by_risk,
                'active_alerts': active_alerts,
                'total_trends': total_trends
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}


learning_prediction_engine = LearningPredictionEngine()
