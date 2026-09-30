# -*- coding: utf-8 -*-
"""
奖励成就引擎
提供积分系统、徽章系统、等级系统、成就系统等激励功能
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('reward_achievement_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('RewardAchievementEngine')

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')


class RewardAchievementEngine:
    """奖励成就引擎 - 管理用户积分、徽章、等级、成就"""

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
        self._level_config = self._init_level_config()
        self._badge_config = self._init_badge_config()
        self._achievement_config = self._init_achievement_config()
        self._init_database()
        self._initialized = True
        logger.info("RewardAchievementEngine 初始化完成")

    def _init_database(self):
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_points (
                        user_id TEXT PRIMARY KEY,
                        total_points INTEGER DEFAULT 0,
                        current_points INTEGER DEFAULT 0,
                        spent_points INTEGER DEFAULT 0,
                        level INTEGER DEFAULT 1,
                        title TEXT DEFAULT '新手学员',
                        consecutive_days INTEGER DEFAULT 0,
                        last_login_date TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS point_transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        points INTEGER NOT NULL,
                        transaction_type TEXT NOT NULL,
                        reason TEXT,
                        related_id TEXT,
                        balance_after INTEGER,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_badges (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        badge_id TEXT NOT NULL,
                        badge_name TEXT NOT NULL,
                        badge_icon TEXT,
                        rarity TEXT DEFAULT 'common',
                        earned_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, badge_id)
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_achievements (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        achievement_id TEXT NOT NULL,
                        achievement_name TEXT NOT NULL,
                        description TEXT,
                        progress REAL DEFAULT 0,
                        target REAL DEFAULT 100,
                        status TEXT DEFAULT 'in_progress',
                        completed_at TEXT,
                        points_reward INTEGER DEFAULT 0,
                        UNIQUE(user_id, achievement_id)
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS reward_config (
                        config_key TEXT PRIMARY KEY,
                        config_value TEXT,
                        config_type TEXT,
                        description TEXT,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_signin (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        signin_date TEXT NOT NULL,
                        points_earned INTEGER DEFAULT 10,
                        consecutive_day INTEGER DEFAULT 1,
                        bonus_points INTEGER DEFAULT 0,
                        UNIQUE(user_id, signin_date)
                    )
                ''')

                cursor.execute('CREATE INDEX IF NOT EXISTS idx_pt_user ON point_transactions(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_ub_user ON user_badges(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_ua_user ON user_achievements(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_us_user ON user_signin(user_id)')

                # 迁移：为旧版 user_points 表添加缺失列（兼容旧表结构）
                for col, col_type in [('total_points', 'INTEGER DEFAULT 0'),
                                       ('current_points', 'INTEGER DEFAULT 0'),
                                       ('spent_points', 'INTEGER DEFAULT 0'),
                                       ('level', 'INTEGER DEFAULT 1'),
                                       ('title', 'TEXT DEFAULT \'新手学员\''),
                                       ('consecutive_days', 'INTEGER DEFAULT 0'),
                                       ('last_login_date', 'TEXT')]:
                    try:
                        cursor.execute(f'ALTER TABLE user_points ADD COLUMN {col} {col_type}')
                    except Exception:
                        pass  # 列已存在

                # 旧表有 points 列，迁移到 current_points/total_points
                try:
                    cursor.execute("SELECT COUNT(*) FROM pragma_table_info('user_points') WHERE name = 'points'")
                    has_old_points = cursor.fetchone()[0] > 0
                    if has_old_points:
                        cursor.execute("UPDATE user_points SET current_points = points WHERE current_points = 0")
                        cursor.execute("UPDATE user_points SET total_points = points WHERE total_points = 0")
                except Exception:
                    pass

                conn.commit()
        except Exception as e:
            logger.error(f"初始化奖励系统数据库失败: {e}")

    def _init_level_config(self):
        return [
            {'level': 1, 'title': '新手学员', 'min_points': 0, 'icon': '🌱'},
            {'level': 2, 'title': '初学者', 'min_points': 100, 'icon': '🌿'},
            {'level': 3, 'title': '进阶者', 'min_points': 300, 'icon': '🌳'},
            {'level': 4, 'title': '学霸', 'min_points': 600, 'icon': '📚'},
            {'level': 5, 'title': '学神', 'min_points': 1000, 'icon': '🏆'},
            {'level': 6, 'title': '学习大师', 'min_points': 2000, 'icon': '👑'},
            {'level': 7, 'title': '知识王者', 'min_points': 4000, 'icon': '💎'},
            {'level': 8, 'title': '智慧宗师', 'min_points': 8000, 'icon': '🌟'},
            {'level': 9, 'title': '传奇学者', 'min_points': 15000, 'icon': '🔥'},
            {'level': 10, 'title': '至尊学圣', 'min_points': 30000, 'icon': '⚡'},
        ]

    def _init_badge_config(self):
        return {
            'first_exam': {'name': '初次考试', 'icon': '📝', 'rarity': 'common', 'description': '完成第一次考试'},
            'perfect_score': {'name': '满分达人', 'icon': '💯', 'rarity': 'legendary', 'description': '获得考试满分'},
            'speed_master': {'name': '速度之王', 'icon': '⚡', 'rarity': 'epic', 'description': '在规定时间一半内完成考试'},
            'streak_7': {'name': '七日达人', 'icon': '📅', 'rarity': 'rare', 'description': '连续学习7天'},
            'streak_30': {'name': '月度坚持者', 'icon': '🗓️', 'rarity': 'epic', 'description': '连续学习30天'},
            'streak_100': {'name': '百日传奇', 'icon': '🎯', 'rarity': 'legendary', 'description': '连续学习100天'},
            'knowledge_seeker': {'name': '求知若渴', 'icon': '🔍', 'rarity': 'rare', 'description': '搜索知识点50次'},
            'question_master': {'name': '出题高手', 'icon': '✏️', 'rarity': 'epic', 'description': '生成题目100道'},
            'top_scorer': {'name': '金榜题名', 'icon': '🥇', 'rarity': 'epic', 'description': '考试排名第一'},
            'helpful_hand': {'name': '乐于助人', 'icon': '🤝', 'rarity': 'rare', 'description': '帮助同学解答问题'},
            'night_owl': {'name': '夜猫子', 'icon': '🦉', 'rarity': 'common', 'description': '在22点后学习'},
            'early_bird': {'name': '早起鸟', 'icon': '🐦', 'rarity': 'common', 'description': '在6点前学习'},
            'all_rounder': {'name': '全能选手', 'icon': '🎪', 'rarity': 'epic', 'description': '5个科目都达到80分以上'},
            'math_genius': {'name': '数学天才', 'icon': '🧮', 'rarity': 'epic', 'description': '数学考试连续满分'},
            'literature_lover': {'name': '文学爱好者', 'icon': '📖', 'rarity': 'rare', 'description': '语文成绩优秀'},
        }

    def _init_achievement_config(self):
        return {
            'exam_10': {'name': '考试新手', 'description': '完成10次考试', 'target': 10, 'points': 100, 'category': 'exam'},
            'exam_50': {'name': '考试达人', 'description': '完成50次考试', 'target': 50, 'points': 500, 'category': 'exam'},
            'exam_100': {'name': '考试专家', 'description': '完成100次考试', 'target': 100, 'points': 1000, 'category': 'exam'},
            'score_90_10': {'name': '90分常客', 'description': '10次考试获得90分以上', 'target': 10, 'points': 200, 'category': 'score'},
            'score_100_5': {'name': '满分王者', 'description': '5次考试获得满分', 'target': 5, 'points': 500, 'category': 'score'},
            'study_7': {'name': '一周坚持', 'description': '连续学习7天', 'target': 7, 'points': 100, 'category': 'study'},
            'study_30': {'name': '月度达人', 'description': '连续学习30天', 'target': 30, 'points': 500, 'category': 'study'},
            'study_100': {'name': '百日坚持', 'description': '连续学习100天', 'target': 100, 'points': 2000, 'category': 'study'},
            'wrong_100': {'name': '错题收集者', 'description': '收集100道错题', 'target': 100, 'points': 200, 'category': 'practice'},
            'wrong_fixed_50': {'name': '错题克星', 'description': '订正50道错题', 'target': 50, 'points': 300, 'category': 'practice'},
            'search_100': {'name': '探索者', 'description': '搜索知识点100次', 'target': 100, 'points': 150, 'category': 'explore'},
            'question_100': {'name': '出题人', 'description': '生成100道题目', 'target': 100, 'points': 200, 'category': 'create'},
            'friend_10': {'name': '社交达人', 'description': '邀请10位好友加入', 'target': 10, 'points': 300, 'category': 'social'},
        }

    def add_points(self, user_id: str, points: int, reason: str,
                   transaction_type: str = 'earn', related_id: str = None) -> Dict[str, Any]:
        """添加积分"""
        with self._lock:
            try:
                if points == 0:
                    return {'success': False, 'message': '积分不能为0'}

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()

                    cursor.execute('SELECT current_points, total_points, level FROM user_points WHERE user_id = ?',
                                   (user_id,))
                    row = cursor.fetchone()

                    if not row:
                        cursor.execute('''
                            INSERT INTO user_points (user_id, total_points, current_points, level)
                            VALUES (?, 0, 0, 1)
                        ''', (user_id,))
                        current_points = 0
                        total_points = 0
                        current_level = 1
                    else:
                        current_points = row[0]
                        total_points = row[1]
                        current_level = row[2]

                    new_balance = current_points + points
                    new_total = total_points + max(0, points)

                    new_level = self._calculate_level(new_total)
                    leveled_up = new_level > current_level
                    new_title = self._get_title_for_level(new_level)

                    cursor.execute('''
                        UPDATE user_points
                        SET current_points = ?, total_points = ?, level = ?, title = ?, updated_at = ?
                        WHERE user_id = ?
                    ''', (new_balance, new_total, new_level, new_title,
                          datetime.now().isoformat(), user_id))

                    cursor.execute('''
                        INSERT INTO point_transactions
                        (user_id, points, transaction_type, reason, related_id, balance_after)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (user_id, points, transaction_type, reason, related_id, new_balance))

                    conn.commit()

                result = {
                    'success': True,
                    'points_added': points,
                    'new_balance': new_balance,
                    'total_points': new_total,
                    'level': new_level,
                    'title': new_title,
                    'leveled_up': leveled_up
                }

                if leveled_up:
                    result['level_up_info'] = {
                        'old_level': current_level,
                        'new_level': new_level,
                        'title': new_title
                    }

                return result
            except Exception as e:
                logger.error(f"添加积分失败: {e}")
                return {'success': False, 'error': str(e)}

    def _calculate_level(self, total_points: int) -> int:
        for lvl in reversed(self._level_config):
            if total_points >= lvl['min_points']:
                return lvl['level']
        return 1

    def _get_title_for_level(self, level: int) -> str:
        for lvl in self._level_config:
            if lvl['level'] == level:
                return lvl['title']
        return '新手学员'

    def get_user_points(self, user_id: str) -> Dict[str, Any]:
        """获取用户积分信息"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT user_id, total_points, current_points, spent_points,
                           level, title, consecutive_days, last_login_date
                    FROM user_points WHERE user_id = ?
                ''', (user_id,))
                row = cursor.fetchone()

                if not row:
                    return {
                        'success': True,
                        'user_id': user_id,
                        'total_points': 0,
                        'current_points': 0,
                        'spent_points': 0,
                        'level': 1,
                        'title': '新手学员',
                        'consecutive_days': 0,
                        'next_level_points': 100,
                        'progress_to_next': 0
                    }

                current_level = row[4]
                next_level_points = self._get_next_level_points(current_level)
                current_level_min = self._get_level_min_points(current_level)
                progress = 0
                if next_level_points > current_level_min:
                    progress = (row[1] - current_level_min) / (next_level_points - current_level_min) * 100
                    progress = min(progress, 100)

                cursor.execute('SELECT COUNT(*) FROM user_badges WHERE user_id = ?', (user_id,))
                badge_count = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM user_achievements WHERE user_id = ? AND status = ?',
                               (user_id, 'completed'))
                achievement_count = cursor.fetchone()[0]

            return {
                'success': True,
                'user_id': row[0],
                'total_points': row[1],
                'current_points': row[2],
                'spent_points': row[3],
                'level': row[4],
                'title': row[5],
                'consecutive_days': row[6] or 0,
                'last_login_date': row[7],
                'next_level_points': next_level_points,
                'progress_to_next': round(progress, 1),
                'badge_count': badge_count,
                'achievement_count': achievement_count,
                'level_icon': self._get_level_icon(row[4])
            }
        except Exception as e:
            logger.error(f"获取用户积分失败: {e}")
            return {'success': False, 'error': str(e)}

    def _get_next_level_points(self, current_level: int) -> int:
        for lvl in self._level_config:
            if lvl['level'] == current_level + 1:
                return lvl['min_points']
        return self._level_config[-1]['min_points'] * 2

    def _get_level_min_points(self, level: int) -> int:
        for lvl in self._level_config:
            if lvl['level'] == level:
                return lvl['min_points']
        return 0

    def _get_level_icon(self, level: int) -> str:
        for lvl in self._level_config:
            if lvl['level'] == level:
                return lvl['icon']
        return '🌱'

    def earn_badge(self, user_id: str, badge_id: str) -> Dict[str, Any]:
        """获得徽章"""
        with self._lock:
            try:
                badge = self._badge_config.get(badge_id)
                if not badge:
                    return {'success': False, 'message': f'徽章不存在: {badge_id}'}

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()

                    cursor.execute('SELECT id FROM user_badges WHERE user_id = ? AND badge_id = ?',
                                   (user_id, badge_id))
                    if cursor.fetchone():
                        return {'success': False, 'message': '已获得该徽章', 'already_had': True}

                    cursor.execute('''
                        INSERT INTO user_badges (user_id, badge_id, badge_name, badge_icon, rarity)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (user_id, badge_id, badge['name'], badge['icon'], badge['rarity']))
                    conn.commit()

                return {
                    'success': True,
                    'badge_id': badge_id,
                    'badge_name': badge['name'],
                    'badge_icon': badge['icon'],
                    'rarity': badge['rarity'],
                    'description': badge['description'],
                    'message': f'恭喜获得「{badge["name"]}」徽章！'
                }
            except Exception as e:
                logger.error(f"获得徽章失败: {e}")
                return {'success': False, 'error': str(e)}

    def get_user_badges(self, user_id: str) -> Dict[str, Any]:
        """获取用户所有徽章"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT badge_id, badge_name, badge_icon, rarity, earned_at
                    FROM user_badges WHERE user_id = ? ORDER BY earned_at DESC
                ''', (user_id,))
                badges = [{
                    'badge_id': r[0],
                    'name': r[1],
                    'icon': r[2],
                    'rarity': r[3],
                    'earned_at': r[4]
                } for r in cursor.fetchall()]

                by_rarity = {}
                for b in badges:
                    r = b['rarity']
                    by_rarity[r] = by_rarity.get(r, 0) + 1

                total_badges = len(self._badge_config)

            return {
                'success': True,
                'user_id': user_id,
                'badges': badges,
                'total_count': len(badges),
                'available_count': total_badges,
                'progress': round(len(badges) / max(total_badges, 1) * 100, 1),
                'by_rarity': by_rarity
            }
        except Exception as e:
            logger.error(f"获取用户徽章失败: {e}")
            return {'success': False, 'error': str(e)}

    def update_achievement_progress(self, user_id: str, achievement_id: str,
                                     progress_increment: float = 1) -> Dict[str, Any]:
        """更新成就进度"""
        with self._lock:
            try:
                ach_config = self._achievement_config.get(achievement_id)
                if not ach_config:
                    return {'success': False, 'message': f'成就不存在: {achievement_id}'}

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()

                    cursor.execute('''
                        SELECT id, progress, status FROM user_achievements
                        WHERE user_id = ? AND achievement_id = ?
                    ''', (user_id, achievement_id))
                    row = cursor.fetchone()

                    if not row:
                        cursor.execute('''
                            INSERT INTO user_achievements
                            (user_id, achievement_id, achievement_name, description,
                             progress, target, status, points_reward)
                            VALUES (?, ?, ?, ?, ?, ?, 'in_progress', ?)
                        ''', (user_id, achievement_id, ach_config['name'],
                              ach_config['description'], progress_increment,
                              ach_config['target'], ach_config['points']))
                        new_progress = progress_increment
                    else:
                        if row[2] == 'completed':
                            return {'success': False, 'message': '成就已完成', 'already_completed': True}
                        new_progress = row[1] + progress_increment
                        cursor.execute('''
                            UPDATE user_achievements SET progress = ?
                            WHERE user_id = ? AND achievement_id = ?
                        ''', (new_progress, user_id, achievement_id))

                    target = ach_config['target']
                    completed = new_progress >= target
                    result = {
                        'success': True,
                        'achievement_id': achievement_id,
                        'achievement_name': ach_config['name'],
                        'current_progress': min(new_progress, target),
                        'target': target,
                        'progress_percent': round(min(new_progress / target * 100, 100), 1),
                        'completed': completed
                    }

                    if completed and (not row or row[2] != 'completed'):
                        cursor.execute('''
                            UPDATE user_achievements
                            SET status = 'completed', completed_at = ?
                            WHERE user_id = ? AND achievement_id = ?
                        ''', (datetime.now().isoformat(), user_id, achievement_id))

                        points_result = self.add_points(
                            user_id, ach_config['points'],
                            f'完成成就「{ach_config["name"]}」',
                            'achievement_reward', achievement_id
                        )
                        result['points_rewarded'] = ach_config['points']
                        result['points_result'] = points_result

                    conn.commit()

                return result
            except Exception as e:
                logger.error(f"更新成就进度失败: {e}")
                return {'success': False, 'error': str(e)}

    def get_user_achievements(self, user_id: str, status: str = None) -> Dict[str, Any]:
        """获取用户成就列表"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                sql = '''
                    SELECT achievement_id, achievement_name, description, progress,
                           target, status, completed_at, points_reward
                    FROM user_achievements WHERE user_id = ?
                '''
                params = [user_id]
                if status:
                    sql += ' AND status = ?'
                    params.append(status)
                sql += ' ORDER BY CASE status WHEN "completed" THEN 0 ELSE 1 END, progress DESC'

                cursor.execute(sql, params)
                achievements = [{
                    'achievement_id': r[0],
                    'name': r[1],
                    'description': r[2],
                    'progress': r[3],
                    'target': r[4],
                    'status': r[5],
                    'completed_at': r[6],
                    'points_reward': r[7],
                    'progress_percent': round(min(r[3] / max(r[4], 1) * 100, 100), 1)
                } for r in cursor.fetchall()]

                cursor.execute('SELECT COUNT(*) FROM user_achievements WHERE user_id = ? AND status = ?',
                               (user_id, 'completed'))
                completed_count = cursor.fetchone()[0]

                total_achievements = len(self._achievement_config)

            return {
                'success': True,
                'user_id': user_id,
                'achievements': achievements,
                'completed_count': completed_count,
                'total_count': total_achievements,
                'progress': round(completed_count / max(total_achievements, 1) * 100, 1)
            }
        except Exception as e:
            logger.error(f"获取用户成就失败: {e}")
            return {'success': False, 'error': str(e)}

    def daily_signin(self, user_id: str) -> Dict[str, Any]:
        """每日签到"""
        with self._lock:
            try:
                today = datetime.now().strftime('%Y-%m-%d')

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()

                    cursor.execute('SELECT id FROM user_signin WHERE user_id = ? AND signin_date = ?',
                                   (user_id, today))
                    if cursor.fetchone():
                        return {'success': False, 'message': '今日已签到', 'already_signed': True}

                    cursor.execute('SELECT consecutive_days, last_login_date FROM user_points WHERE user_id = ?',
                                   (user_id,))
                    row = cursor.fetchone()

                    last_consecutive = row[0] if row else 0
                    last_login = row[1] if row else None

                    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                    if last_login == yesterday:
                        new_consecutive = last_consecutive + 1
                    elif last_login == today:
                        new_consecutive = last_consecutive
                    else:
                        new_consecutive = 1

                    base_points = 10
                    bonus_points = 0
                    if new_consecutive >= 7:
                        bonus_points += 20
                    if new_consecutive >= 30:
                        bonus_points += 50
                    if new_consecutive >= 100:
                        bonus_points += 100

                    total_points = base_points + bonus_points

                    cursor.execute('''
                        INSERT INTO user_signin
                        (user_id, signin_date, points_earned, consecutive_day, bonus_points)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (user_id, today, total_points, new_consecutive, bonus_points))

                    cursor.execute('''
                        INSERT OR REPLACE INTO user_points
                        (user_id, total_points, current_points, level, title,
                         consecutive_days, last_login_date, updated_at)
                        SELECT ?, COALESCE(total_points, 0) + ?,
                               COALESCE(current_points, 0) + ?,
                               COALESCE(level, 1), COALESCE(title, '新手学员'),
                               ?, ?, ?
                        FROM user_points WHERE user_id = ?
                    ''', (user_id, total_points, total_points,
                          new_consecutive, today, datetime.now().isoformat(), user_id))

                    if cursor.rowcount == 0:
                        cursor.execute('''
                            INSERT INTO user_points
                            (user_id, total_points, current_points, level, title,
                             consecutive_days, last_login_date)
                            VALUES (?, ?, ?, 1, '新手学员', ?, ?)
                        ''', (user_id, total_points, total_points, new_consecutive, today))

                    conn.commit()

                result = {
                    'success': True,
                    'points_earned': total_points,
                    'base_points': base_points,
                    'bonus_points': bonus_points,
                    'consecutive_days': new_consecutive,
                    'message': f'签到成功！获得 {total_points} 积分'
                }

                if new_consecutive in [7, 30, 100]:
                    self.earn_badge(user_id, f'streak_{new_consecutive}')

                return result
            except Exception as e:
                logger.error(f"每日签到失败: {e}")
                return {'success': False, 'error': str(e)}

    def get_leaderboard(self, type: str = 'points', limit: int = 20) -> Dict[str, Any]:
        """获取排行榜"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()

                if type == 'points':
                    cursor.execute('''
                        SELECT user_id, total_points, level, title
                        FROM user_points ORDER BY total_points DESC LIMIT ?
                    ''', (limit,))
                    rankings = [{
                        'user_id': r[0],
                        'total_points': r[1],
                        'level': r[2],
                        'title': r[3]
                    } for r in cursor.fetchall()]
                elif type == 'badges':
                    cursor.execute('''
                        SELECT ub.user_id, COUNT(*) as badge_count, up.level, up.title
                        FROM user_badges ub
                        LEFT JOIN user_points up ON ub.user_id = up.user_id
                        GROUP BY ub.user_id ORDER BY badge_count DESC LIMIT ?
                    ''', (limit,))
                    rankings = [{
                        'user_id': r[0],
                        'badge_count': r[1],
                        'level': r[2],
                        'title': r[3]
                    } for r in cursor.fetchall()]
                elif type == 'achievements':
                    cursor.execute('''
                        SELECT ua.user_id, COUNT(*) as ach_count, up.level, up.title
                        FROM user_achievements ua
                        LEFT JOIN user_points up ON ua.user_id = up.user_id
                        WHERE ua.status = 'completed'
                        GROUP BY ua.user_id ORDER BY ach_count DESC LIMIT ?
                    ''', (limit,))
                    rankings = [{
                        'user_id': r[0],
                        'achievement_count': r[1],
                        'level': r[2],
                        'title': r[3]
                    } for r in cursor.fetchall()]
                else:
                    return {'success': False, 'message': f'无效的排行榜类型: {type}'}

            return {
                'success': True,
                'type': type,
                'rankings': rankings,
                'total': len(rankings)
            }
        except Exception as e:
            logger.error(f"获取排行榜失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_statistics(self) -> Dict[str, Any]:
        """获取奖励系统统计"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM user_points')
                total_users = cursor.fetchone()[0]
                cursor.execute('SELECT SUM(total_points) FROM user_points')
                total_points = cursor.fetchone()[0] or 0
                cursor.execute('SELECT AVG(level) FROM user_points')
                avg_level = cursor.fetchone()[0] or 0
                cursor.execute('SELECT COUNT(*) FROM user_badges')
                total_badges_earned = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM user_achievements WHERE status = ?', ('completed',))
                total_achievements = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM point_transactions')
                total_transactions = cursor.fetchone()[0]

            return {
                'success': True,
                'total_users': total_users,
                'total_points_distributed': total_points,
                'average_level': round(avg_level, 1),
                'total_badges_earned': total_badges_earned,
                'total_achievements_completed': total_achievements,
                'total_transactions': total_transactions,
                'available_badges': len(self._badge_config),
                'available_achievements': len(self._achievement_config),
                'available_levels': len(self._level_config)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_all_badges(self) -> Dict[str, Any]:
        """获取所有徽章配置"""
        badges = []
        for bid, bconf in self._badge_config.items():
            badges.append({
                'badge_id': bid,
                'name': bconf['name'],
                'icon': bconf['icon'],
                'rarity': bconf['rarity'],
                'description': bconf['description']
            })
        return {'success': True, 'badges': badges, 'total': len(badges)}

    def get_all_achievements(self) -> Dict[str, Any]:
        """获取所有成就配置"""
        achievements = []
        for aid, aconf in self._achievement_config.items():
            achievements.append({
                'achievement_id': aid,
                'name': aconf['name'],
                'description': aconf['description'],
                'target': aconf['target'],
                'points_reward': aconf['points'],
                'category': aconf.get('category', 'general')
            })
        return {'success': True, 'achievements': achievements, 'total': len(achievements)}


reward_achievement_engine = RewardAchievementEngine()
