# -*- coding: utf-8 -*-
"""
错题本智能引擎
提供错题收集、智能分析、薄弱点预测、智能重练等功能
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
        logging.FileHandler('wrong_book_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('WrongBookEngine')

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')


class WrongBookEngine:
    """错题本智能引擎 - 管理错题收集、分析和智能重练"""

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
        logger.info("WrongBookEngine 初始化完成")

    def _init_database(self):
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS wrong_questions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        question_id TEXT NOT NULL,
                        subject TEXT,
                        question_type TEXT,
                        content TEXT,
                        options TEXT,
                        correct_answer TEXT,
                        user_answer TEXT,
                        knowledge_points TEXT DEFAULT '[]',
                        difficulty INTEGER DEFAULT 3,
                        source TEXT,
                        source_id TEXT,
                        wrong_reason TEXT,
                        wrong_count INTEGER DEFAULT 1,
                        correct_count INTEGER DEFAULT 0,
                        mastery_level REAL DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        is_reviewed INTEGER DEFAULT 0,
                        last_wrong_time TEXT DEFAULT CURRENT_TIMESTAMP,
                        last_review_time TEXT,
                        next_review_time TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS wrong_review_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        wrong_id INTEGER NOT NULL,
                        question_id TEXT,
                        is_correct INTEGER DEFAULT 0,
                        user_answer TEXT,
                        review_time TEXT DEFAULT CURRENT_TIMESTAMP,
                        time_spent INTEGER,
                        notes TEXT
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS wrong_analysis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        subject TEXT,
                        analysis_type TEXT,
                        analysis_data TEXT,
                        weak_points TEXT DEFAULT '[]',
                        suggestions TEXT DEFAULT '[]',
                        generated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS wrong_review_plans (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        subject TEXT,
                        plan_name TEXT,
                        plan_type TEXT DEFAULT 'smart',
                        question_count INTEGER DEFAULT 10,
                        question_ids TEXT DEFAULT '[]',
                        status TEXT DEFAULT 'pending',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        started_at TEXT,
                        completed_at TEXT,
                        accuracy REAL
                    )
                ''')

                cursor.execute('CREATE INDEX IF NOT EXISTS idx_wq_user ON wrong_questions(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_wq_user_subject ON wrong_questions(user_id, subject)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_wr_user ON wrong_review_records(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_wr_wrong ON wrong_review_records(wrong_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_wa_user ON wrong_analysis(user_id)')

                conn.commit()
        except Exception as e:
            logger.error(f"初始化错题本数据库失败: {e}")

    def add_wrong_question(self, user_id: str, question_id: str,
                           subject: str = None, question_type: str = None,
                           content: str = None, options: List = None,
                           correct_answer: str = None, user_answer: str = None,
                           knowledge_points: List[str] = None,
                           difficulty: int = 3, source: str = None,
                           source_id: str = None, wrong_reason: str = None) -> Dict[str, Any]:
        """添加错题"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()

                    cursor.execute('''
                        SELECT id, wrong_count FROM wrong_questions
                        WHERE user_id = ? AND question_id = ?
                    ''', (user_id, question_id))
                    row = cursor.fetchone()

                    now = datetime.now()

                    if row:
                        wrong_id = row[0]
                        new_wrong_count = row[1] + 1
                        new_mastery = max(0.0, 1.0 - new_wrong_count * 0.2)
                        next_review = self._calculate_next_review(new_wrong_count, now)

                        cursor.execute('''
                            UPDATE wrong_questions
                            SET wrong_count = ?, user_answer = ?, last_wrong_time = ?,
                                next_review_time = ?, mastery_level = ?, status = 'active',
                                is_reviewed = 0, updated_at = ?
                            WHERE id = ?
                        ''', (new_wrong_count, user_answer, now.isoformat(),
                              next_review.isoformat(), new_mastery, now.isoformat(), wrong_id))

                        message = f'错题次数更新为 {new_wrong_count} 次'
                    else:
                        mastery = 0.8
                        next_review = self._calculate_next_review(1, now)

                        cursor.execute('''
                            INSERT INTO wrong_questions
                            (user_id, question_id, subject, question_type, content, options,
                             correct_answer, user_answer, knowledge_points, difficulty,
                             source, source_id, wrong_reason, next_review_time, mastery_level)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            user_id, question_id, subject, question_type, content,
                            json.dumps(options or [], ensure_ascii=False),
                            correct_answer, user_answer,
                            json.dumps(knowledge_points or [], ensure_ascii=False),
                            difficulty, source, source_id, wrong_reason,
                            next_review.isoformat(), mastery
                        ))
                        wrong_id = cursor.lastrowid
                        message = '错题已添加到错题本'

                    # 更新成就进度
                    try:
                        from ai_engines.reward_achievement_engine import reward_achievement_engine
                        reward_achievement_engine.update_achievement_progress(user_id, 'wrong_100', 1)
                    except Exception:
                        pass

                    conn.commit()

                return {
                    'success': True,
                    'wrong_id': wrong_id,
                    'message': message,
                    'wrong_count': new_wrong_count if row else 1
                }
            except Exception as e:
                logger.error(f"添加错题失败: {e}")
                return {'success': False, 'error': str(e)}

    def _calculate_next_review(self, wrong_count: int, base_time: datetime) -> datetime:
        """基于艾宾浩斯遗忘曲线计算下次复习时间"""
        intervals = [1, 2, 4, 7, 15, 30, 60, 120]
        idx = min(wrong_count - 1, len(intervals) - 1)
        return base_time + timedelta(days=intervals[idx])

    def review_wrong_question(self, wrong_id: int, user_id: str,
                              is_correct: bool, user_answer: str = None,
                              time_spent: int = None, notes: str = None) -> Dict[str, Any]:
        """复习错题"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()

                    cursor.execute('''
                        SELECT wrong_count, correct_count, mastery_level, question_id
                        FROM wrong_questions WHERE id = ? AND user_id = ?
                    ''', (wrong_id, user_id))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'message': '错题不存在'}

                    wrong_count, correct_count, mastery_level, question_id = row
                    new_correct = correct_count + (1 if is_correct else 0)

                    if is_correct:
                        new_mastery = min(1.0, mastery_level + 0.15)
                    else:
                        new_mastery = max(0.0, mastery_level - 0.1)
                        wrong_count += 1

                    now = datetime.now()
                    status = 'mastered' if new_mastery >= 0.9 else 'active'
                    next_review = self._calculate_next_review(
                        wrong_count, now
                    ) if status == 'active' else None

                    cursor.execute('''
                        UPDATE wrong_questions
                        SET correct_count = ?, wrong_count = ?, mastery_level = ?,
                            status = ?, last_review_time = ?, next_review_time = ?,
                            is_reviewed = 1, updated_at = ?
                        WHERE id = ?
                    ''', (
                        new_correct, wrong_count, new_mastery, status,
                        now.isoformat(),
                        next_review.isoformat() if next_review else None,
                        now.isoformat(), wrong_id
                    ))

                    cursor.execute('''
                        INSERT INTO wrong_review_records
                        (user_id, wrong_id, question_id, is_correct, user_answer, time_spent, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (user_id, wrong_id, question_id, 1 if is_correct else 0,
                          user_answer, time_spent, notes))

                    if is_correct:
                        try:
                            from ai_engines.reward_achievement_engine import reward_achievement_engine
                            reward_achievement_engine.update_achievement_progress(user_id, 'wrong_fixed_50', 1)
                        except Exception:
                            pass

                    conn.commit()

                return {
                    'success': True,
                    'is_correct': is_correct,
                    'new_mastery': round(new_mastery, 2),
                    'new_status': status,
                    'wrong_count': wrong_count,
                    'correct_count': new_correct
                }
            except Exception as e:
                logger.error(f"复习错题失败: {e}")
                return {'success': False, 'error': str(e)}

    def get_user_wrong_questions(self, user_id: str, subject: str = None,
                                  status: str = None, limit: int = 50,
                                  sort_by: str = 'wrong_count') -> Dict[str, Any]:
        """获取用户错题列表"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                sql = '''
                    SELECT id, question_id, subject, question_type, content,
                           correct_answer, user_answer, knowledge_points, difficulty,
                           wrong_count, correct_count, mastery_level, status,
                           last_wrong_time, next_review_time
                    FROM wrong_questions WHERE user_id = ?
                '''
                params = [user_id]

                if subject:
                    sql += ' AND subject = ?'
                    params.append(subject)
                if status:
                    sql += ' AND status = ?'
                    params.append(status)

                sort_map = {
                    'wrong_count': 'wrong_count DESC',
                    'mastery': 'mastery_level ASC',
                    'recent': 'last_wrong_time DESC',
                    'next_review': 'next_review_time ASC'
                }
                sort = sort_map.get(sort_by, 'wrong_count DESC')
                sql += f' ORDER BY {sort} LIMIT ?'
                params.append(limit)

                cursor.execute(sql, params)
                rows = cursor.fetchall()

                questions = []
                for r in rows:
                    questions.append({
                        'wrong_id': r[0],
                        'question_id': r[1],
                        'subject': r[2],
                        'question_type': r[3],
                        'content': r[4],
                        'correct_answer': r[5],
                        'user_answer': r[6],
                        'knowledge_points': json.loads(r[7]) if r[7] else [],
                        'difficulty': r[8],
                        'wrong_count': r[9],
                        'correct_count': r[10],
                        'mastery_level': r[11],
                        'status': r[12],
                        'last_wrong_time': r[13],
                        'next_review_time': r[14]
                    })

                cursor.execute('SELECT COUNT(*) FROM wrong_questions WHERE user_id = ?', (user_id,))
                total = cursor.fetchone()[0]

                cursor.execute('''
                    SELECT subject, COUNT(*) FROM wrong_questions
                    WHERE user_id = ? GROUP BY subject
                ''', (user_id,))
                by_subject = dict(cursor.fetchall())

            return {
                'success': True,
                'user_id': user_id,
                'total': total,
                'by_subject': by_subject,
                'questions': questions,
                'count': len(questions)
            }
        except Exception as e:
            logger.error(f"获取错题列表失败: {e}")
            return {'success': False, 'error': str(e)}

    def analyze_weak_points(self, user_id: str, subject: str = None) -> Dict[str, Any]:
        """分析用户薄弱知识点"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()

                sql = '''
                    SELECT knowledge_points, wrong_count, mastery_level, subject
                    FROM wrong_questions WHERE user_id = ? AND status = 'active'
                '''
                params = [user_id]
                if subject:
                    sql += ' AND subject = ?'
                    params.append(subject)

                cursor.execute(sql, params)
                rows = cursor.fetchall()

                kp_stats = defaultdict(lambda: {
                    'wrong_count': 0,
                    'total_mastery': 0,
                    'question_count': 0,
                    'subjects': set()
                })

                for kps_json, wrong_count, mastery, subj in rows:
                    try:
                        kps = json.loads(kps_json) if kps_json else []
                    except Exception:
                        kps = []
                    for kp in kps:
                        kp_stats[kp]['wrong_count'] += wrong_count
                        kp_stats[kp]['total_mastery'] += mastery
                        kp_stats[kp]['question_count'] += 1
                        kp_stats[kp]['subjects'].add(subj)

                weak_points = []
                for kp, stats in kp_stats.items():
                    avg_mastery = stats['total_mastery'] / max(stats['question_count'], 1)
                    risk_score = stats['wrong_count'] * (1 - avg_mastery)
                    weak_points.append({
                        'knowledge_point': kp,
                        'wrong_count': stats['wrong_count'],
                        'question_count': stats['question_count'],
                        'avg_mastery': round(avg_mastery, 3),
                        'risk_score': round(risk_score, 2),
                        'subjects': list(stats['subjects']),
                        'risk_level': 'high' if risk_score > 3 else ('medium' if risk_score > 1 else 'low')
                    })

                weak_points.sort(key=lambda x: -x['risk_score'])

                suggestions = self._generate_suggestions(weak_points)

                # 保存分析结果
                analysis_data = json.dumps({'weak_points': weak_points, 'suggestions': suggestions},
                                           ensure_ascii=False)
                cursor.execute('''
                    INSERT INTO wrong_analysis
                    (user_id, subject, analysis_type, analysis_data, weak_points, suggestions)
                    VALUES (?, ?, 'weak_point_analysis', ?, ?, ?)
                ''', (user_id, subject or 'all', analysis_data,
                      json.dumps([w['knowledge_point'] for w in weak_points[:10]], ensure_ascii=False),
                      json.dumps(suggestions[:5], ensure_ascii=False)))
                conn.commit()

            return {
                'success': True,
                'user_id': user_id,
                'weak_points_count': len(weak_points),
                'high_risk_count': len([w for w in weak_points if w['risk_level'] == 'high']),
                'medium_risk_count': len([w for w in weak_points if w['risk_level'] == 'medium']),
                'weak_points': weak_points[:20],
                'suggestions': suggestions
            }
        except Exception as e:
            logger.error(f"分析薄弱点失败: {e}")
            return {'success': False, 'error': str(e)}

    def _generate_suggestions(self, weak_points: List[Dict]) -> List[Dict]:
        """生成学习建议"""
        suggestions = []

        if not weak_points:
            return [{'type': 'excellent', 'content': '太棒了！当前没有明显的薄弱知识点，继续保持！', 'priority': 1}]

        high_risk = [w for w in weak_points if w['risk_level'] == 'high']
        medium_risk = [w for w in weak_points if w['risk_level'] == 'medium']

        if high_risk:
            top_high = high_risk[:3]
            for wp in top_high:
                suggestions.append({
                    'type': 'urgent',
                    'content': f'重点复习「{wp["knowledge_point"]}」',
                    'detail': f'该知识点已错 {wp["wrong_count"]} 次，掌握度仅 {wp["avg_mastery"]*100:.0f}%',
                    'priority': 100
                })

        if medium_risk:
            suggestions.append({
                'type': 'attention',
                'content': f'关注 {len(medium_risk)} 个中等风险知识点',
                'detail': '建议每周安排专项练习巩固',
                'priority': 70
            })

        total_wrong = sum(w['wrong_count'] for w in weak_points[:10])
        if total_wrong > 10:
            suggestions.append({
                'type': 'strategy',
                'content': '建议采用「间隔重复法」复习',
                'detail': '每天复习前一天的错题，每周回顾本周错题',
                'priority': 60
            })

        suggestions.sort(key=lambda x: -x['priority'])
        return suggestions

    def generate_review_plan(self, user_id: str, subject: str = None,
                              plan_type: str = 'smart', count: int = 10) -> Dict[str, Any]:
        """生成智能复习计划"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()

                    sql = '''
                        SELECT id, question_id, content, correct_answer, knowledge_points,
                               difficulty, wrong_count, mastery_level, next_review_time
                        FROM wrong_questions
                        WHERE user_id = ? AND status = 'active'
                    '''
                    params = [user_id]
                    if subject:
                        sql += ' AND subject = ?'
                        params.append(subject)

                    if plan_type == 'smart':
                        sql += ' ORDER BY mastery_level ASC, wrong_count DESC LIMIT ?'
                    elif plan_type == 'due':
                        sql += " AND next_review_time <= datetime('now') ORDER BY next_review_time ASC LIMIT ?"
                    elif plan_type == 'recent':
                        sql += ' ORDER BY last_wrong_time DESC LIMIT ?'
                    elif plan_type == 'hardest':
                        sql += ' ORDER BY difficulty DESC, wrong_count DESC LIMIT ?'
                    else:
                        sql += ' ORDER BY RANDOM() LIMIT ?'

                    params.append(count)

                    cursor.execute(sql, params)
                    rows = cursor.fetchall()

                    questions = []
                    for r in rows:
                        questions.append({
                            'wrong_id': r[0],
                            'question_id': r[1],
                            'content': r[2],
                            'correct_answer': r[3],
                            'knowledge_points': json.loads(r[4]) if r[4] else [],
                            'difficulty': r[5],
                            'wrong_count': r[6],
                            'mastery_level': r[7],
                            'next_review_time': r[8]
                        })

                    plan_name = self._get_plan_name(plan_type, subject)
                    q_ids_json = json.dumps([q['wrong_id'] for q in questions], ensure_ascii=False)

                    cursor.execute('''
                        INSERT INTO wrong_review_plans
                        (user_id, subject, plan_name, plan_type, question_count, question_ids)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (user_id, subject or 'all', plan_name, plan_type, len(questions), q_ids_json))
                    plan_id = cursor.lastrowid

                    conn.commit()

                return {
                    'success': True,
                    'plan_id': plan_id,
                    'plan_name': plan_name,
                    'plan_type': plan_type,
                    'question_count': len(questions),
                    'questions': questions
                }
            except Exception as e:
                logger.error(f"生成复习计划失败: {e}")
                return {'success': False, 'error': str(e)}

    def _get_plan_name(self, plan_type: str, subject: str = None) -> str:
        type_names = {
            'smart': '智能复习',
            'due': '到期复习',
            'recent': '近期错题',
            'hardest': '难题攻坚',
            'random': '随机复习'
        }
        base = type_names.get(plan_type, '复习计划')
        if subject:
            return f'{subject}-{base}'
        return f'{base}计划-{datetime.now().strftime("%m%d")}'

    def predict_weak_points(self, user_id: str, subject: str = None) -> Dict[str, Any]:
        """预测潜在薄弱点"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT knowledge_points, subject, mastery_level, wrong_count
                    FROM wrong_questions WHERE user_id = ?
                ''', (user_id,))
                rows = cursor.fetchall()

                kp_mastery = {}
                kp_subjects = defaultdict(set)

                for kps_json, subj, mastery, wrong_count in rows:
                    try:
                        kps = json.loads(kps_json) if kps_json else []
                    except Exception:
                        kps = []
                    for kp in kps:
                        if kp not in kp_mastery:
                            kp_mastery[kp] = []
                        kp_mastery[kp].append(mastery)
                        kp_subjects[kp].add(subj)

                predicted = []
                for kp, masteries in kp_mastery.items():
                    avg_mastery = sum(masteries) / len(masteries)
                    trend = 'declining' if len(masteries) > 2 and masteries[-1] < masteries[0] else 'stable'
                    risk_factors = len(masteries) * (1 - avg_mastery)

                    if avg_mastery < 0.7 and trend == 'declining':
                        predicted.append({
                            'knowledge_point': kp,
                            'current_mastery': round(avg_mastery, 3),
                            'trend': trend,
                            'risk_level': 'high',
                            'confidence': 0.85,
                            'subjects': list(kp_subjects[kp])
                        })
                    elif avg_mastery < 0.8:
                        predicted.append({
                            'knowledge_point': kp,
                            'current_mastery': round(avg_mastery, 3),
                            'trend': trend,
                            'risk_level': 'medium',
                            'confidence': 0.6,
                            'subjects': list(kp_subjects[kp])
                        })

                predicted.sort(key=lambda x: -x['confidence'] * (1 - x['current_mastery']))

            return {
                'success': True,
                'user_id': user_id,
                'predicted_weak_count': len(predicted),
                'high_risk_count': len([p for p in predicted if p['risk_level'] == 'high']),
                'predictions': predicted[:15]
            }
        except Exception as e:
            logger.error(f"预测薄弱点失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_statistics(self) -> Dict[str, Any]:
        """获取错题本统计信息"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM wrong_questions')
                total_wrong = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(DISTINCT user_id) FROM wrong_questions')
                total_users = cursor.fetchone()[0]
                cursor.execute('SELECT subject, COUNT(*) FROM wrong_questions GROUP BY subject')
                by_subject = dict(cursor.fetchall())
                cursor.execute('SELECT status, COUNT(*) FROM wrong_questions GROUP BY status')
                by_status = dict(cursor.fetchall())
                cursor.execute('SELECT AVG(wrong_count) FROM wrong_questions')
                avg_wrong = cursor.fetchone()[0] or 0
                cursor.execute('SELECT AVG(mastery_level) FROM wrong_questions')
                avg_mastery = cursor.fetchone()[0] or 0
                cursor.execute('SELECT COUNT(*) FROM wrong_review_records')
                total_reviews = cursor.fetchone()[0]

            return {
                'success': True,
                'total_wrong_questions': total_wrong,
                'total_users': total_users,
                'by_subject': by_subject,
                'by_status': by_status,
                'average_wrong_count': round(avg_wrong, 1),
                'average_mastery': round(avg_mastery, 3),
                'total_reviews': total_reviews
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}


wrong_book_engine = WrongBookEngine()
