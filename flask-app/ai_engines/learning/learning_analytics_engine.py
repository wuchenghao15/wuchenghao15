# -*- coding: utf-8 -*-
"""
学习分析仪表盘引擎
提供多维度学习画像、能力雷达图、跨引擎数据聚合、综合分析报告
聚合数据源：考试结果、错题本、奖励系统、协作学习、学习预测、知识图谱
"""

import os
import sys
import json
import time
import sqlite3
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('learning_analytics_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('LearningAnalyticsEngine')

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')

# 能力雷达图维度
RADAR_DIMENSIONS = [
    'knowledge_mastery',   # 知识掌握度
    'learning_activity',   # 学习活跃度
    'answer_accuracy',      # 答题正确率
    'progress_rate',        # 进步幅度
    'collaboration',        # 协作贡献
]


class LearningAnalyticsEngine:
    """学习分析仪表盘引擎 - 综合学习画像与多维度分析"""

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
        logger.info("LearningAnalyticsEngine 初始化完成")

    def _init_database(self):
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()

                # 学习画像快照（周期性保存）
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_profiles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        snapshot_date TEXT NOT NULL,
                        radar_data TEXT,
                        overall_score REAL,
                        level TEXT,
                        strengths TEXT,
                        weaknesses TEXT,
                        recommendations TEXT,
                        metrics TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, snapshot_date)
                    )
                ''')

                # 学习事件流（统一记录各类学习事件）
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        event_source TEXT NOT NULL,
                        subject TEXT,
                        description TEXT,
                        value REAL,
                        metadata TEXT,
                        occurred_at TEXT NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 学科能力评估
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS subject_proficiency (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        subject TEXT NOT NULL,
                        proficiency_score REAL DEFAULT 0,
                        total_questions INTEGER DEFAULT 0,
                        correct_questions INTEGER DEFAULT 0,
                        avg_score REAL DEFAULT 0,
                        trend TEXT DEFAULT 'stable',
                        last_updated TEXT,
                        UNIQUE(user_id, subject)
                    )
                ''')

                # 学习目标
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_goals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        goal_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        target_value REAL,
                        current_value REAL DEFAULT 0,
                        subject TEXT,
                        deadline TEXT,
                        status TEXT DEFAULT 'active',
                        progress REAL DEFAULT 0,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        completed_at TEXT
                    )
                ''')

                cursor.execute('CREATE INDEX IF NOT EXISTS idx_le_user ON learning_events(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_le_type ON learning_events(event_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_lp_user ON learning_profiles(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_sp_user ON subject_proficiency(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_lg_user ON learning_goals(user_id)')

                # 迁移：兼容旧版 learning_goals 表（可能只有 goal_content 而无 title 列）
                for col, col_type in [('title', 'TEXT'),
                                       ('target_value', 'REAL DEFAULT 100'),
                                       ('current_value', 'REAL DEFAULT 0'),
                                       ('subject', 'TEXT'),
                                       ('deadline', 'TEXT'),
                                       ('completed_at', 'TEXT')]:
                    try:
                        cursor.execute(f'ALTER TABLE learning_goals ADD COLUMN {col} {col_type}')
                    except Exception:
                        pass  # 列已存在
                # 旧表有 goal_content 列，迁移到 title
                try:
                    cursor.execute("SELECT COUNT(*) FROM pragma_table_info('learning_goals') WHERE name = 'goal_content'")
                    has_old = cursor.fetchone()[0] > 0
                    if has_old:
                        cursor.execute("UPDATE learning_goals SET title = goal_content WHERE title IS NULL")
                except Exception:
                    pass

                conn.commit()
        except Exception as e:
            logger.error(f"初始化分析引擎数据库失败: {e}")

    # ==================== 事件记录 ====================

    def record_event(self, user_id: str, event_type: str, event_source: str,
                     description: str = '', subject: str = None,
                     value: float = None, metadata: Dict = None) -> Dict[str, Any]:
        """记录学习事件（统一入口，供其他引擎调用）"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO learning_events
                        (user_id, event_type, event_source, subject, description,
                         value, metadata, occurred_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (user_id, event_type, event_source, subject, description,
                          value, json.dumps(metadata or {}, ensure_ascii=False),
                          datetime.now().isoformat()))
                    conn.commit()
                return {'success': True, 'message': '事件已记录'}
            except Exception as e:
                logger.error(f"记录事件失败: {e}")
                return {'success': False, 'error': str(e)}

    # ==================== 能力雷达图 ====================

    def get_radar_chart(self, user_id: str) -> Dict[str, Any]:
        """获取5维能力雷达图数据"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()

                # 1. 知识掌握度 - 基于科目平均得分
                cursor.execute('''
                    SELECT AVG(total_score) FROM exam_results WHERE user_id = ?
                ''', (user_id,))
                avg_exam = cursor.fetchone()[0]
                knowledge = min(100, (avg_exam or 0))

                # 2. 学习活跃度 - 基于近30天事件数
                since = (datetime.now() - timedelta(days=30)).isoformat()
                cursor.execute('''
                    SELECT COUNT(*) FROM learning_events
                    WHERE user_id = ? AND occurred_at > ?
                ''', (user_id, since))
                event_count = cursor.fetchone()[0]
                activity = min(100, event_count * 2)

                # 3. 答题正确率
                cursor.execute('''
                    SELECT SUM(correct_count), SUM(total_count) FROM exam_results
                    WHERE user_id = ?
                ''', (user_id,))
                row = cursor.fetchone()
                correct, total = (row[0] or 0), (row[1] or 0)
                accuracy = (correct / total * 100) if total > 0 else 0

                # 4. 进步幅度 - 最近5次 vs 之前5次
                cursor.execute('''
                    SELECT total_score FROM exam_results
                    WHERE user_id = ? ORDER BY created_at DESC LIMIT 10
                ''', (user_id,))
                scores = [r[0] for r in cursor.fetchall() if r[0] is not None]
                progress = 50  # 默认中等
                if len(scores) >= 6:
                    recent_avg = sum(scores[:5]) / 5
                    old_avg = sum(scores[5:]) / (len(scores) - 5)
                    diff = recent_avg - old_avg
                    progress = max(0, min(100, 50 + diff * 2))
                elif len(scores) >= 2:
                    diff = scores[0] - scores[-1]
                    progress = max(0, min(100, 50 + diff * 2))

                # 5. 协作贡献 - 基于知识分享 + 帮助他人
                try:
                    cursor.execute('''
                        SELECT COUNT(*) FROM knowledge_shares WHERE user_id = ?
                    ''', (user_id,))
                    shares = cursor.fetchone()[0]
                except Exception:
                    shares = 0
                try:
                    cursor.execute('''
                        SELECT COUNT(*) FROM peer_help_requests
                        WHERE helper_id = ? AND status = 'resolved'
                    ''', (user_id,))
                    helps = cursor.fetchone()[0]
                except Exception:
                    helps = 0
                collaboration = min(100, shares * 10 + helps * 15)

            radar = {
                'knowledge_mastery': round(knowledge, 1),
                'learning_activity': round(activity, 1),
                'answer_accuracy': round(accuracy, 1),
                'progress_rate': round(progress, 1),
                'collaboration': round(collaboration, 1)
            }
            overall = round(sum(radar.values()) / len(radar), 1)

            return {
                'success': True,
                'user_id': user_id,
                'dimensions': radar,
                'overall_score': overall,
                'level': self._score_to_level(overall),
                'generated_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"获取雷达图失败: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== 学科能力 ====================

    def update_subject_proficiency(self, user_id: str, subject: str,
                                    score: float, correct: int, total: int) -> Dict[str, Any]:
        """更新学科能力评估（考试完成时调用）"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT proficiency_score, total_questions, correct_questions, avg_score
                    FROM subject_proficiency WHERE user_id = ? AND subject = ?
                ''', (user_id, subject))
                row = cursor.fetchone()

                now = datetime.now().isoformat()
                if row:
                    old_prof, old_total, old_correct, old_avg = row
                    new_total = old_total + total
                    new_correct = old_correct + correct
                    # 滑动平均
                    new_avg = (old_avg * old_total + score) / new_total if new_total > 0 else score
                    new_prof = (new_correct / new_total * 100) if new_total > 0 else 0
                    # 趋势判断
                    trend = 'stable'
                    if score > old_avg * 1.05:
                        trend = 'improving'
                    elif score < old_avg * 0.95:
                        trend = 'declining'

                    cursor.execute('''
                        UPDATE subject_proficiency
                        SET proficiency_score = ?, total_questions = ?,
                            correct_questions = ?, avg_score = ?, trend = ?, last_updated = ?
                        WHERE user_id = ? AND subject = ?
                    ''', (new_prof, new_total, new_correct, new_avg, trend, now, user_id, subject))
                else:
                    new_prof = (correct / total * 100) if total > 0 else 0
                    cursor.execute('''
                        INSERT INTO subject_proficiency
                        (user_id, subject, proficiency_score, total_questions,
                         correct_questions, avg_score, trend, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?, 'stable', ?)
                    ''', (user_id, subject, new_prof, total, correct, score, now))

                conn.commit()

            return {
                'success': True,
                'user_id': user_id,
                'subject': subject,
                'proficiency': round(new_prof, 1)
            }
        except Exception as e:
            logger.error(f"更新学科能力失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_subject_proficiencies(self, user_id: str) -> Dict[str, Any]:
        """获取用户所有学科能力"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT subject, proficiency_score, total_questions,
                           correct_questions, avg_score, trend, last_updated
                    FROM subject_proficiency WHERE user_id = ?
                    ORDER BY proficiency_score DESC
                ''', (user_id,))
                subjects = [{
                    'subject': r[0],
                    'proficiency': round(r[1], 1),
                    'total_questions': r[2],
                    'correct_questions': r[3],
                    'avg_score': round(r[4], 1),
                    'trend': r[5],
                    'last_updated': r[6]
                } for r in cursor.fetchall()]

            return {
                'success': True,
                'user_id': user_id,
                'subjects': subjects,
                'total': len(subjects)
            }
        except Exception as e:
            logger.error(f"获取学科能力失败: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== 学习画像 ====================

    def generate_profile(self, user_id: str, save: bool = True) -> Dict[str, Any]:
        """生成完整学习画像（含雷达图+学科+优劣势+建议）"""
        with self._lock:
            try:
                radar = self.get_radar_chart(user_id)
                subjects = self.get_subject_proficiencies(user_id)

                # 优劣势分析
                dims = radar.get('dimensions', {})
                sorted_dims = sorted(dims.items(), key=lambda x: x[1], reverse=True)
                strengths = [{'dimension': k, 'score': v} for k, v in sorted_dims[:2]]
                weaknesses = [{'dimension': k, 'score': v} for k, v in sorted_dims[-2:]]

                # 学科优劣势
                subj_list = subjects.get('subjects', [])
                subj_sorted = sorted(subj_list, key=lambda x: x['proficiency'], reverse=True)
                strong_subjects = [s['subject'] for s in subj_sorted[:2] if s['proficiency'] >= 60]
                weak_subjects = [s['subject'] for s in subj_sorted[-2:] if s['proficiency'] < 60]

                # 智能建议
                recommendations = self._generate_recommendations(dims, subj_list, radar.get('overall_score', 0))

                profile = {
                    'user_id': user_id,
                    'snapshot_date': datetime.now().strftime('%Y-%m-%d'),
                    'radar': radar,
                    'subjects': subjects,
                    'strengths': {
                        'dimensions': strengths,
                        'subjects': strong_subjects
                    },
                    'weaknesses': {
                        'dimensions': weaknesses,
                        'subjects': weak_subjects
                    },
                    'recommendations': recommendations,
                    'overall_score': radar.get('overall_score', 0),
                    'level': radar.get('level', 'unknown'),
                    'generated_at': datetime.now().isoformat()
                }

                if save:
                    self._save_profile(user_id, profile)

                return {'success': True, 'profile': profile}
            except Exception as e:
                logger.error(f"生成画像失败: {e}")
                return {'success': False, 'error': str(e)}

    def _save_profile(self, user_id: str, profile: Dict):
        """保存画像快照"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO learning_profiles
                    (user_id, snapshot_date, radar_data, overall_score, level,
                     strengths, weaknesses, recommendations, metrics)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    profile['snapshot_date'],
                    json.dumps(profile.get('radar', {}), ensure_ascii=False),
                    profile.get('overall_score', 0),
                    profile.get('level', 'unknown'),
                    json.dumps(profile.get('strengths', {}), ensure_ascii=False),
                    json.dumps(profile.get('weaknesses', {}), ensure_ascii=False),
                    json.dumps(profile.get('recommendations', []), ensure_ascii=False),
                    json.dumps({}, ensure_ascii=False)
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"保存画像失败: {e}")

    def _generate_recommendations(self, dims: Dict, subjects: List, overall: float) -> List[Dict]:
        """基于画像数据生成智能建议"""
        recs = []

        # 整体建议
        if overall < 40:
            recs.append({
                'priority': 'high',
                'category': 'overall',
                'message': '整体学习表现偏低，建议制定每日学习计划，重点突破薄弱学科',
                'action': 'daily_plan'
            })
        elif overall >= 80:
            recs.append({
                'priority': 'low',
                'category': 'overall',
                'message': '学习表现优秀！建议挑战更高难度题目，参与竞赛提升',
                'action': 'challenge_advanced'
            })

        # 维度建议
        if dims.get('learning_activity', 0) < 30:
            recs.append({
                'priority': 'high',
                'category': 'activity',
                'message': '学习活跃度较低，建议每天至少完成1次练习',
                'action': 'increase_practice'
            })
        if dims.get('collaboration', 0) < 20:
            recs.append({
                'priority': 'medium',
                'category': 'collaboration',
                'message': '协作贡献较少，建议加入学习小组或帮助同学解答问题',
                'action': 'join_group'
            })
        if dims.get('progress_rate', 50) < 40:
            recs.append({
                'priority': 'high',
                'category': 'progress',
                'message': '近期成绩有所下滑，建议复盘错题本，针对性复习',
                'action': 'review_wrong_book'
            })
        if dims.get('answer_accuracy', 0) < 60:
            recs.append({
                'priority': 'high',
                'category': 'accuracy',
                'message': '答题正确率偏低，建议从基础知识巩固做起',
                'action': 'basic_review'
            })

        # 学科建议
        for subj in subjects[:3]:
            if subj.get('proficiency', 100) < 50:
                recs.append({
                    'priority': 'high',
                    'category': 'subject',
                    'subject': subj['subject'],
                    'message': f"{subj['subject']}掌握度偏低（{subj['proficiency']}%），建议专项训练",
                    'action': 'subject_training'
                })
            if subj.get('trend') == 'declining':
                recs.append({
                    'priority': 'medium',
                    'category': 'subject',
                    'subject': subj['subject'],
                    'message': f"{subj['subject']}成绩呈下降趋势，需及时调整学习策略",
                    'action': 'adjust_strategy'
                })

        return recs[:8]  # 最多8条建议

    # ==================== 学习目标管理 ====================

    def create_goal(self, user_id: str, goal_type: str, title: str,
                    target_value: float = 100, subject: str = None,
                    deadline: str = None) -> Dict[str, Any]:
        """创建学习目标（兼容旧版 learning_goals 表：goal_content NOT NULL 约束）"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                # 检测旧版 goal_content 列是否存在（旧表 NOT NULL，新表无此列）
                cursor.execute("SELECT COUNT(*) FROM pragma_table_info('learning_goals') WHERE name = 'goal_content'")
                has_old_col = cursor.fetchone()[0] > 0

                if has_old_col:
                    # 旧表：必须为 goal_content 提供值（NOT NULL）
                    cursor.execute('''
                        INSERT INTO learning_goals
                        (user_id, goal_type, title, target_value, subject, deadline, status, goal_content)
                        VALUES (?, ?, ?, ?, ?, ?, 'active', ?)
                    ''', (user_id, goal_type, title, target_value, subject, deadline, title))
                else:
                    cursor.execute('''
                        INSERT INTO learning_goals
                        (user_id, goal_type, title, target_value, subject, deadline, status)
                        VALUES (?, ?, ?, ?, ?, ?, 'active')
                    ''', (user_id, goal_type, title, target_value, subject, deadline))
                goal_id = cursor.lastrowid
                conn.commit()
            return {'success': True, 'goal_id': goal_id, 'message': '目标已创建'}
        except Exception as e:
            logger.error(f"创建目标失败: {e}")
            return {'success': False, 'error': str(e)}

    def update_goal_progress(self, goal_id: int, current_value: float) -> Dict[str, Any]:
        """更新目标进度"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT target_value FROM learning_goals WHERE id = ?', (goal_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'message': '目标不存在'}
                target = row[0] or 100
                progress = min(100, (current_value / target * 100)) if target > 0 else 0
                status = 'completed' if progress >= 100 else 'active'
                completed_at = datetime.now().isoformat() if status == 'completed' else None

                cursor.execute('''
                    UPDATE learning_goals
                    SET current_value = ?, progress = ?, status = ?, completed_at = COALESCE(?, completed_at)
                    WHERE id = ?
                ''', (current_value, progress, status, completed_at, goal_id))
                conn.commit()
            return {'success': True, 'goal_id': goal_id, 'progress': round(progress, 1), 'status': status}
        except Exception as e:
            logger.error(f"更新目标进度失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_user_goals(self, user_id: str, status: str = None) -> Dict[str, Any]:
        """获取用户学习目标"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                sql = 'SELECT id, goal_type, title, target_value, current_value, subject, deadline, status, progress, created_at, completed_at FROM learning_goals WHERE user_id = ?'
                params = [user_id]
                if status:
                    sql += ' AND status = ?'
                    params.append(status)
                sql += ' ORDER BY created_at DESC'
                cursor.execute(sql, params)
                goals = [{
                    'id': r[0], 'goal_type': r[1], 'title': r[2],
                    'target_value': r[3], 'current_value': r[4],
                    'subject': r[5], 'deadline': r[6], 'status': r[7],
                    'progress': round(r[8], 1) if r[8] else 0,
                    'created_at': r[9], 'completed_at': r[10]
                } for r in cursor.fetchall()]
            return {'success': True, 'goals': goals, 'total': len(goals)}
        except Exception as e:
            logger.error(f"获取目标失败: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== 学习事件流 ====================

    def get_event_stream(self, user_id: str, limit: int = 50,
                         event_type: str = None) -> Dict[str, Any]:
        """获取用户学习事件流"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                sql = 'SELECT event_type, event_source, subject, description, value, occurred_at FROM learning_events WHERE user_id = ?'
                params = [user_id]
                if event_type:
                    sql += ' AND event_type = ?'
                    params.append(event_type)
                sql += ' ORDER BY occurred_at DESC LIMIT ?'
                params.append(limit)
                cursor.execute(sql, params)
                events = [{
                    'event_type': r[0], 'source': r[1], 'subject': r[2],
                    'description': r[3], 'value': r[4], 'occurred_at': r[5]
                } for r in cursor.fetchall()]
            return {'success': True, 'events': events, 'total': len(events)}
        except Exception as e:
            logger.error(f"获取事件流失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_profile_history(self, user_id: str, limit: int = 30) -> Dict[str, Any]:
        """获取画像历史（趋势分析）"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT snapshot_date, overall_score, level, radar_data
                    FROM learning_profiles WHERE user_id = ?
                    ORDER BY snapshot_date DESC LIMIT ?
                ''', (user_id, limit))
                history = [{
                    'date': r[0], 'score': r[1], 'level': r[2],
                    'radar': json.loads(r[3]) if r[3] else {}
                } for r in cursor.fetchall()]
            return {'success': True, 'history': history, 'total': len(history)}
        except Exception as e:
            logger.error(f"获取画像历史失败: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== 统计 ====================

    def get_statistics(self) -> Dict[str, Any]:
        """获取分析引擎统计"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(DISTINCT user_id) FROM learning_events')
                tracked_users = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM learning_events')
                total_events = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM learning_profiles')
                total_profiles = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM subject_proficiency')
                total_prof = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM learning_goals WHERE status='active'")
                active_goals = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM learning_goals WHERE status='completed'")
                completed_goals = cursor.fetchone()[0]

                # 事件类型分布
                cursor.execute('''
                    SELECT event_type, COUNT(*) as cnt FROM learning_events
                    GROUP BY event_type ORDER BY cnt DESC LIMIT 10
                ''')
                event_dist = [{'type': r[0], 'count': r[1]} for r in cursor.fetchall()]

            return {
                'success': True,
                'tracked_users': tracked_users,
                'total_events': total_events,
                'total_profiles': total_profiles,
                'subject_proficiencies': total_prof,
                'active_goals': active_goals,
                'completed_goals': completed_goals,
                'event_distribution': event_dist
            }
        except Exception as e:
            logger.error(f"获取统计失败: {e}")
            return {'success': False, 'error': str(e)}

    def _score_to_level(self, score: float) -> str:
        if score >= 85:
            return 'excellent'
        elif score >= 70:
            return 'good'
        elif score >= 50:
            return 'average'
        elif score >= 30:
            return 'below_average'
        return 'needs_improvement'


learning_analytics_engine = LearningAnalyticsEngine()
