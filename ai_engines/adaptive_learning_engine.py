# -*- coding: utf-8 -*-
"""
自适应学习引擎
为学习系统提供个性化学习路径、知识点掌握度分析和智能推荐
"""

import os
import sys
import json
import logging
import threading
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('AdaptiveLearningEngine')

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')


class AdaptiveLearningEngine:
    """自适应学习引擎 - 单例模式"""

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
        self._initialized = True
        self._init_database()
        logger.info("AdaptiveLearningEngine 初始化完成")

    def _init_database(self):
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_knowledge_mastery (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT,
                        knowledge_point TEXT,
                        mastery_level REAL DEFAULT 0.0,
                        practice_count INTEGER DEFAULT 0,
                        correct_count INTEGER DEFAULT 0,
                        last_practiced TEXT,
                        updated_at TEXT,
                        UNIQUE(user_id, knowledge_point)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_paths (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT,
                        path_id TEXT UNIQUE,
                        subject TEXT,
                        current_level TEXT,
                        target_level TEXT,
                        path_data TEXT,
                        progress REAL DEFAULT 0.0,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_recommendations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT,
                        recommendation_type TEXT,
                        content TEXT,
                        reason TEXT,
                        priority INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                # 迁移：添加可能缺失的列（兼容旧表结构）
                for col, col_type in [('current_level', 'TEXT'), ('target_level', 'TEXT'),
                                       ('path_data', 'TEXT'), ('progress', 'REAL DEFAULT 0.0'),
                                       ('updated_at', 'TEXT')]:
                    try:
                        cursor.execute(f'ALTER TABLE learning_paths ADD COLUMN {col} {col_type}')
                    except Exception:
                        pass  # 列已存在
                conn.commit()
        except Exception as e:
            logger.error(f"初始化自适应学习引擎数据库失败: {e}")

    def update_mastery(self, user_id: str, knowledge_point: str, correct: bool) -> Dict[str, Any]:
        """更新用户知识点掌握度"""
        try:
            now = datetime.now().isoformat()
            correct_val = 1 if correct else 0
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                # 先查询是否已有记录
                cursor.execute('''
                    SELECT practice_count, correct_count FROM user_knowledge_mastery
                    WHERE user_id = ? AND knowledge_point = ?
                ''', (user_id, knowledge_point))
                row = cursor.fetchone()

                if row:
                    # 更新已有记录
                    old_practice = row[0]
                    old_correct = row[1]
                    new_practice = old_practice + 1
                    new_correct = old_correct + correct_val
                    new_mastery = round(new_correct / new_practice, 4)
                    cursor.execute('''
                        UPDATE user_knowledge_mastery
                        SET practice_count = ?, correct_count = ?, mastery_level = ?,
                            last_practiced = ?, updated_at = ?
                        WHERE user_id = ? AND knowledge_point = ?
                    ''', (new_practice, new_correct, new_mastery, now, now, user_id, knowledge_point))
                else:
                    # 插入新记录
                    cursor.execute('''
                        INSERT INTO user_knowledge_mastery
                        (user_id, knowledge_point, mastery_level, practice_count, correct_count, last_practiced, updated_at)
                        VALUES (?, ?, ?, 1, ?, ?, ?)
                    ''', (user_id, knowledge_point, float(correct_val), correct_val, now, now))
                conn.commit()

                # 获取更新后的状态
                cursor.execute('''
                    SELECT mastery_level, practice_count, correct_count FROM user_knowledge_mastery
                    WHERE user_id = ? AND knowledge_point = ?
                ''', (user_id, knowledge_point))
                row = cursor.fetchone()
                return {
                    'success': True,
                    'user_id': user_id,
                    'knowledge_point': knowledge_point,
                    'mastery_level': row[0] if row else 0,
                    'practice_count': row[1] if row else 0,
                    'correct_count': row[2] if row else 0
                }
        except Exception as e:
            logger.error(f"更新掌握度失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_user_mastery(self, user_id: str) -> Dict[str, Any]:
        """获取用户所有知识点掌握度"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT knowledge_point, mastery_level, practice_count, correct_count, last_practiced
                    FROM user_knowledge_mastery WHERE user_id = ?
                    ORDER BY mastery_level ASC
                ''', (user_id,))
                rows = cursor.fetchall()
                masteries = [{
                    'knowledge_point': r[0],
                    'mastery_level': round(r[1], 2),
                    'practice_count': r[2],
                    'correct_count': r[3],
                    'last_practiced': r[4]
                } for r in rows]

                weak_points = [m for m in masteries if m['mastery_level'] < 0.6]
                strong_points = [m for m in masteries if m['mastery_level'] >= 0.8]

                return {
                    'success': True,
                    'user_id': user_id,
                    'total_points': len(masteries),
                    'weak_points': weak_points,
                    'strong_points': strong_points,
                    'avg_mastery': round(sum(m['mastery_level'] for m in masteries) / max(len(masteries), 1), 2),
                    'masteries': masteries
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def generate_learning_path(self, user_id: str, subject: str,
                                target_level: str = 'advanced') -> Dict[str, Any]:
        """生成个性化学习路径"""
        try:
            mastery = self.get_user_mastery(user_id)
            weak = mastery.get('weak_points', [])

            # 构建学习路径：优先弱点，无弱点时取掌握度最低的5个作为"巩固提升"
            if weak:
                focus_points = weak[:10]
                path_mode = 'weakness_improvement'
            else:
                all_masteries = mastery.get('masteries', [])
                # 按掌握度升序，取最低的5个（如果不足5个则全取）
                focus_points = sorted(all_masteries, key=lambda m: m['mastery_level'])[:5]
                path_mode = 'consolidation_improvement'

            # 构建学习路径
            path_steps = []
            for i, wp in enumerate(focus_points):
                gap = max(0.0, 0.8 - wp['mastery_level'])
                # 巩固提升模式下，即使掌握度高也至少推荐3次练习
                rec_practice = max(5, int(gap * 20)) if weak else max(3, int(gap * 15))
                path_steps.append({
                    'step': i + 1,
                    'title': f'第{i+1}步: 巩固 {wp["knowledge_point"]}',
                    'knowledge_point': wp['knowledge_point'],
                    'current_mastery': wp['mastery_level'],
                    'target_mastery': 0.8,
                    'mastery_gap': round(gap, 3),
                    'recommended_practice': rec_practice,
                    'priority': 'high' if wp['mastery_level'] < 0.3 else ('medium' if wp['mastery_level'] < 0.6 else 'low'),
                    'estimated_minutes': max(10, int(gap * 60)) if gap > 0 else 10
                })

            path_id = f"path_{user_id}_{subject}_{int(datetime.now().timestamp())}"
            total_minutes = sum(s['estimated_minutes'] for s in path_steps)
            path_data = {
                'subject': subject,
                'target_level': target_level,
                'current_level': 'beginner' if mastery.get('avg_mastery', 0) < 0.4 else 'intermediate',
                'path_mode': path_mode,
                'steps': path_steps,
                'total_steps': len(path_steps),
                'estimated_time': f'{total_minutes}分钟',
                'weak_points_count': len(weak)
            }

            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO learning_paths
                    (user_id, path_id, subject, current_level, target_level, path_data, progress, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, 0.0, ?)
                ''', (
                    user_id, path_id, subject,
                    path_data['current_level'], target_level,
                    json.dumps(path_data, ensure_ascii=False),
                    datetime.now().isoformat()
                ))
                conn.commit()

            return {
                'success': True,
                'path_id': path_id,
                'user_id': user_id,
                'path': path_data
            }
        except Exception as e:
            logger.error(f"生成学习路径失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_recommendations(self, user_id: str) -> Dict[str, Any]:
        """获取个性化学习推荐"""
        try:
            mastery = self.get_user_mastery(user_id)
            recommendations = []

            weak_points = mastery.get('weak_points', [])
            strong_points = mastery.get('strong_points', [])

            for wp in weak_points[:5]:
                recommendations.append({
                    'type': 'practice_weak_point',
                    'content': f"重点练习: {wp['knowledge_point']}",
                    'reason': f"当前掌握度 {wp['mastery_level']*100:.0f}%，需要加强",
                    'priority': 100 - int(wp['mastery_level'] * 100)
                })

            for sp in strong_points[:3]:
                recommendations.append({
                    'type': 'advance_level',
                    'content': f"进阶学习: {sp['knowledge_point']}",
                    'reason': f"掌握度 {sp['mastery_level']*100:.0f}%，可以挑战更高难度",
                    'priority': 50
                })

            # 当无弱点也无强项时，从所有知识点中选掌握度最低的5个作为巩固推荐
            if not weak_points and not strong_points:
                all_masteries = mastery.get('masteries', [])
                # 按掌握度升序取最低5个
                lowest = sorted(all_masteries, key=lambda m: m['mastery_level'])[:5]
                for m in lowest:
                    recommendations.append({
                        'type': 'consolidate_practice',
                        'content': f"巩固练习: {m['knowledge_point']}",
                        'reason': f"当前掌握度 {m['mastery_level']*100:.0f}%，建议持续巩固",
                        'priority': 60 - int(m['mastery_level'] * 50)
                    })

            recommendations.sort(key=lambda x: -x['priority'])

            # 保存推荐
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                for rec in recommendations:
                    cursor.execute('''
                        INSERT INTO learning_recommendations
                        (user_id, recommendation_type, content, reason, priority)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (user_id, rec['type'], rec['content'], rec['reason'], rec['priority']))
                conn.commit()

            return {
                'success': True,
                'user_id': user_id,
                'recommendations': recommendations
            }
        except Exception as e:
            logger.error(f"获取推荐失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_statistics(self) -> Dict[str, Any]:
        """获取学习系统统计"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(DISTINCT user_id) FROM user_knowledge_mastery')
                users = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM user_knowledge_mastery')
                records = cursor.fetchone()[0]
                cursor.execute('SELECT AVG(mastery_level) FROM user_knowledge_mastery')
                avg = cursor.fetchone()[0] or 0
                cursor.execute('SELECT COUNT(*) FROM learning_paths')
                paths = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM learning_recommendations WHERE status = "pending"')
                pending = cursor.fetchone()[0]

                return {
                    'success': True,
                    'total_users': users,
                    'total_mastery_records': records,
                    'avg_mastery': round(avg, 2),
                    'learning_paths': paths,
                    'pending_recommendations': pending
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}


adaptive_learning_engine = AdaptiveLearningEngine()
