# -*- coding: utf-8 -*-
"""
学习游戏化引擎
游戏化学习体验、任务系统、挑战、排行榜、奖励、成就解锁、经验值、关卡、虚拟物品
"""

import os
import sys
import json
import time
import sqlite3
import logging
import threading
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gamification_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('GamificationEngine')

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')

# 等级系统配置（经验值阈值）
LEVEL_THRESHOLDS = [
    0, 100, 300, 600, 1000, 1500, 2200, 3000, 4000, 5500,
    7500, 10000, 13000, 17000, 22000, 28000, 36000, 46000, 58000, 72000,
    88000, 106000, 126000, 148000, 172000, 200000, 232000, 268000, 308000, 352000
]

# 任务难度配置
TASK_DIFFICULTY = {
    'easy': {'exp': 50, 'coins': 10, 'time': 300},
    'normal': {'exp': 100, 'coins': 25, 'time': 600},
    'hard': {'exp': 200, 'coins': 60, 'time': 1200},
    'expert': {'exp': 400, 'coins': 150, 'time': 1800},
    'legendary': {'exp': 800, 'coins': 400, 'time': 3600}
}


class GamificationEngine:
    """学习游戏化引擎 - 任务/挑战/排行榜/成就/虚拟物品"""

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
        logger.info("GamificationEngine 初始化完成")

    def _init_database(self):
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()

                # 1. 玩家档案表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS game_players (
                        player_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL UNIQUE,
                        nickname TEXT,
                        avatar TEXT,
                        level INTEGER DEFAULT 1,
                        exp_points INTEGER DEFAULT 0,
                        coins INTEGER DEFAULT 100,
                        gems INTEGER DEFAULT 0,
                        energy INTEGER DEFAULT 100,
                        max_energy INTEGER DEFAULT 100,
                        streak_days INTEGER DEFAULT 0,
                        last_active_date TEXT,
                        total_quests_completed INTEGER DEFAULT 0,
                        total_challenges_won INTEGER DEFAULT 0,
                        title TEXT,
                        bio TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 2. 任务系统表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS game_quests (
                        quest_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT,
                        quest_type TEXT DEFAULT 'daily',
                        difficulty TEXT DEFAULT 'normal',
                        category TEXT,
                        subject TEXT,
                        target_value INTEGER DEFAULT 1,
                        reward_exp INTEGER DEFAULT 100,
                        reward_coins INTEGER DEFAULT 25,
                        reward_badge TEXT,
                        prerequisites TEXT DEFAULT '[]',
                        time_limit INTEGER,
                        status TEXT DEFAULT 'active',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 3. 玩家任务进度表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS player_quest_progress (
                        progress_id TEXT PRIMARY KEY,
                        player_id TEXT NOT NULL,
                        quest_id TEXT NOT NULL,
                        current_value INTEGER DEFAULT 0,
                        target_value INTEGER,
                        status TEXT DEFAULT 'active',
                        accepted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        completed_at TEXT,
                        reward_claimed BOOLEAN DEFAULT 0,
                        UNIQUE(player_id, quest_id),
                        FOREIGN KEY (quest_id) REFERENCES game_quests(quest_id)
                    )
                ''')

                # 4. 排行榜表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS leaderboards (
                        leaderboard_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        scope TEXT DEFAULT 'global',
                        category TEXT DEFAULT 'exp',
                        period TEXT DEFAULT 'all_time',
                        target_group TEXT,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 5. 虚拟物品表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS game_items (
                        item_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        item_type TEXT,
                        rarity TEXT DEFAULT 'common',
                        icon TEXT,
                        price_coins INTEGER DEFAULT 0,
                        price_gems INTEGER DEFAULT 0,
                        effects TEXT DEFAULT '{}',
                        stackable BOOLEAN DEFAULT 0,
                        max_stack INTEGER DEFAULT 99,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 6. 玩家物品库存表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS player_inventory (
                        inventory_id TEXT PRIMARY KEY,
                        player_id TEXT NOT NULL,
                        item_id TEXT NOT NULL,
                        quantity INTEGER DEFAULT 1,
                        equipped BOOLEAN DEFAULT 0,
                        acquired_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(player_id, item_id),
                        FOREIGN KEY (item_id) REFERENCES game_items(item_id)
                    )
                ''')

                cursor.execute('CREATE INDEX IF NOT EXISTS idx_gp_user ON game_players(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_gp_level ON game_players(level DESC)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_gq_type ON game_quests(quest_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_pqp_player ON player_quest_progress(player_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_pi_player ON player_inventory(player_id)')

                self._init_default_quests(cursor)
                self._init_default_items(cursor)
                conn.commit()
        except Exception as e:
            logger.error(f"初始化游戏化数据库失败: {e}")

    def _init_default_quests(self, cursor):
        """初始化默认任务"""
        try:
            default_quests = [
                ('quest_daily_login', '每日签到', '每天登录获得奖励', 'daily', 'easy',
                 'login', None, 1, 50, 10, None, '[]', None),
                ('quest_daily_3questions', '答题达人', '完成3道题目', 'daily', 'normal',
                 'practice', None, 3, 100, 25, None, '[]', None),
                ('quest_daily_perfect', '满分挑战', '完成1次满分答题', 'daily', 'hard',
                 'practice', None, 1, 200, 60, None, '[]', None),
                ('quest_weekly_streak', '坚持不懈', '连续学习7天', 'weekly', 'normal',
                 'streak', None, 7, 300, 80, None, '[]', None),
                ('quest_subject_master', '学科大师', '完成某学科50道题', 'achievement', 'expert',
                 'mastery', None, 50, 400, 150, 'badge_subject_master', '[]', None),
            ]
            for q in default_quests:
                cursor.execute('SELECT COUNT(*) FROM game_quests WHERE quest_id = ?', (q[0],))
                if cursor.fetchone()[0] == 0:
                    cursor.execute('''
                        INSERT INTO game_quests
                        (quest_id, title, description, quest_type, difficulty,
                         category, subject, target_value, reward_exp, reward_coins,
                         reward_badge, prerequisites, time_limit)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', q)
        except Exception as e:
            logger.error(f"初始化默认任务失败: {e}")

    def _init_default_items(self, cursor):
        """初始化默认物品"""
        try:
            default_items = [
                ('item_exp_potion_s', '小型经验药水', '获得50经验值', 'consumable', 'common',
                 '🧪', 20, 0, '{"effect":"exp","value":50}', 1, 99),
                ('item_exp_potion_m', '中型经验药水', '获得200经验值', 'consumable', 'rare',
                 '⚗️', 80, 0, '{"effect":"exp","value":200}', 1, 99),
                ('item_energy_potion', '能量药水', '恢复50点能量', 'consumable', 'common',
                 '⚡', 30, 0, '{"effect":"energy","value":50}', 1, 99),
                ('item_avatar_gold', '金色头像框', '稀有头像框装饰', 'avatar', 'rare',
                 '👑', 0, 50, '{}', 0, 1),
                ('item_title_scholar', '学者称号', '显示"学者"称号', 'title', 'epic',
                 '🎓', 0, 100, '{}', 0, 1),
            ]
            for item in default_items:
                cursor.execute('SELECT COUNT(*) FROM game_items WHERE item_id = ?', (item[0],))
                if cursor.fetchone()[0] == 0:
                    cursor.execute('''
                        INSERT INTO game_items
                        (item_id, name, description, item_type, rarity,
                         icon, price_coins, price_gems, effects, stackable, max_stack)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', item)
        except Exception as e:
            logger.error(f"初始化默认物品失败: {e}")

    # ==================== 玩家档案 ====================

    def get_or_create_player(self, user_id: str, nickname: str = None) -> Dict[str, Any]:
        """获取或创建玩家档案"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM game_players WHERE user_id = ?', (user_id,))
                    row = cursor.fetchone()
                    if not row:
                        player_id = f"player_{int(time.time())}_{user_id[:8]}"
                        cursor.execute('''
                            INSERT INTO game_players
                            (player_id, user_id, nickname, coins, energy, max_energy)
                            VALUES (?, ?, ?, 100, 100, 100)
                        ''', (player_id, user_id, nickname or user_id))
                        conn.commit()
                        cursor.execute('SELECT * FROM game_players WHERE user_id = ?', (user_id,))
                        row = cursor.fetchone()

                    cols = ['player_id', 'user_id', 'nickname', 'avatar', 'level',
                            'exp_points', 'coins', 'gems', 'energy', 'max_energy',
                            'streak_days', 'last_active_date',
                            'total_quests_completed', 'total_challenges_won',
                            'title', 'bio', 'created_at', 'updated_at']
                    player = {cols[i]: row[i] for i in range(min(len(cols), len(row)))}
                    return {'success': True, 'player': player}
            except Exception as e:
                logger.error(f"获取玩家档案失败: {e}")
                return {'success': False, 'error': str(e)}

    def add_exp(self, user_id: str, exp: int, reason: str = None) -> Dict[str, Any]:
        """增加经验值（自动升级）"""
        with self._lock:
            try:
                result = self.get_or_create_player(user_id)
                if not result.get('success'):
                    return result

                player = result['player']
                old_level = player['level']
                new_exp = player['exp_points'] + exp
                new_level = self._exp_to_level(new_exp)

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE game_players
                        SET exp_points = ?, level = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    ''', (new_exp, new_level, user_id))
                    conn.commit()

                leveled_up = new_level > old_level
                return {
                    'success': True,
                    'exp_gained': exp,
                    'total_exp': new_exp,
                    'old_level': old_level,
                    'new_level': new_level,
                    'leveled_up': leveled_up,
                    'message': f"获得 {exp} 经验值" + (f"，升级到 Lv.{new_level}！" if leveled_up else "")
                }
            except Exception as e:
                logger.error(f"增加经验值失败: {e}")
                return {'success': False, 'error': str(e)}

    def add_coins(self, user_id: str, coins: int, reason: str = None) -> Dict[str, Any]:
        """增加金币"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE game_players SET coins = coins + ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?',
                                   (coins, user_id))
                    if cursor.rowcount == 0:
                        self.get_or_create_player(user_id)
                        cursor.execute('UPDATE game_players SET coins = coins + ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?',
                                       (coins, user_id))
                    cursor.execute('SELECT coins FROM game_players WHERE user_id = ?', (user_id,))
                    new_coins = cursor.fetchone()[0]
                    conn.commit()

                return {
                    'success': True,
                    'coins_gained': coins,
                    'total_coins': new_coins,
                    'message': f"获得 {coins} 金币"
                }
            except Exception as e:
                logger.error(f"增加金币失败: {e}")
                return {'success': False, 'error': str(e)}

    def _exp_to_level(self, exp: int) -> int:
        """经验值转等级"""
        for i, threshold in enumerate(LEVEL_THRESHOLDS):
            if exp < threshold:
                return max(1, i)
        return len(LEVEL_THRESHOLDS)

    def _level_to_exp(self, level: int) -> int:
        """等级转经验值阈值"""
        if level <= 0:
            return 0
        if level > len(LEVEL_THRESHOLDS):
            return LEVEL_THRESHOLDS[-1]
        return LEVEL_THRESHOLDS[level - 1]

    def get_level_progress(self, user_id: str) -> Dict[str, Any]:
        """获取等级进度"""
        try:
            result = self.get_or_create_player(user_id)
            if not result.get('success'):
                return result
            player = result['player']
            level = player['level']
            exp = player['exp_points']
            current_level_exp = self._level_to_exp(level)
            next_level_exp = self._level_to_exp(level + 1)
            progress = (exp - current_level_exp) / max(next_level_exp - current_level_exp, 1) * 100

            return {
                'success': True,
                'level': level,
                'exp': exp,
                'current_level_exp': current_level_exp,
                'next_level_exp': next_level_exp,
                'exp_to_next': next_level_exp - exp,
                'progress_percent': round(progress, 1)
            }
        except Exception as e:
            logger.error(f"获取等级进度失败: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== 任务系统 ====================

    def list_quests(self, quest_type: str = None, category: str = None) -> Dict[str, Any]:
        """列出可用任务"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                sql = '''SELECT quest_id, title, description, quest_type, difficulty,
                                category, subject, target_value, reward_exp, reward_coins,
                                reward_badge, time_limit, status
                         FROM game_quests WHERE status = 'active' '''
                params = []
                if quest_type:
                    sql += ' AND quest_type = ?'
                    params.append(quest_type)
                if category:
                    sql += ' AND category = ?'
                    params.append(category)
                sql += ' ORDER BY difficulty ASC'
                cursor.execute(sql, params)
                rows = cursor.fetchall()

                quests = [{
                    'quest_id': r[0], 'title': r[1], 'description': r[2],
                    'quest_type': r[3], 'difficulty': r[4], 'category': r[5],
                    'subject': r[6], 'target_value': r[7], 'reward_exp': r[8],
                    'reward_coins': r[9], 'reward_badge': r[10],
                    'time_limit': r[11], 'status': r[12]
                } for r in rows]

                return {'success': True, 'quests': quests, 'count': len(quests)}
        except Exception as e:
            logger.error(f"列出任务失败: {e}")
            return {'success': False, 'error': str(e)}

    def accept_quest(self, user_id: str, quest_id: str) -> Dict[str, Any]:
        """接受任务"""
        with self._lock:
            try:
                result = self.get_or_create_player(user_id)
                if not result.get('success'):
                    return result
                player_id = result['player']['player_id']

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT target_value, status FROM game_quests WHERE quest_id = ?', (quest_id,))
                    quest_row = cursor.fetchone()
                    if not quest_row:
                        return {'success': False, 'message': '任务不存在'}
                    if quest_row[1] != 'active':
                        return {'success': False, 'message': '任务不可用'}

                    progress_id = f"prog_{int(time.time())}_{player_id[:8]}_{quest_id[:8]}"
                    try:
                        cursor.execute('''
                            INSERT INTO player_quest_progress
                            (progress_id, player_id, quest_id, target_value)
                            VALUES (?, ?, ?, ?)
                        ''', (progress_id, player_id, quest_id, quest_row[0]))
                        conn.commit()
                    except sqlite3.IntegrityError:
                        return {'success': False, 'message': '已接受此任务'}

                return {'success': True, 'progress_id': progress_id, 'message': '任务已接受'}
            except Exception as e:
                logger.error(f"接受任务失败: {e}")
                return {'success': False, 'error': str(e)}

    def update_quest_progress(self, user_id: str, quest_id: str, value: int = 1) -> Dict[str, Any]:
        """更新任务进度"""
        with self._lock:
            try:
                result = self.get_or_create_player(user_id)
                if not result.get('success'):
                    return result
                player_id = result['player']['player_id']

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT progress_id, current_value, target_value, status
                        FROM player_quest_progress
                        WHERE player_id = ? AND quest_id = ?
                    ''', (player_id, quest_id))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'message': '未接受此任务'}
                    if row[3] != 'active':
                        return {'success': False, 'message': f'任务状态: {row[3]}'}

                    new_value = min(row[1] + value, row[2])
                    completed = new_value >= row[2]
                    new_status = 'completed' if completed else 'active'

                    cursor.execute('''
                        UPDATE player_quest_progress
                        SET current_value = ?, status = ?, completed_at = ?
                        WHERE progress_id = ?
                    ''', (new_value, new_status,
                          datetime.now().isoformat() if completed else None,
                          row[0]))
                    conn.commit()

                return {
                    'success': True,
                    'quest_id': quest_id,
                    'current_value': new_value,
                    'target_value': row[2],
                    'completed': completed,
                    'message': '任务已完成！' if completed else f'进度: {new_value}/{row[2]}'
                }
            except Exception as e:
                logger.error(f"更新任务进度失败: {e}")
                return {'success': False, 'error': str(e)}

    def claim_quest_reward(self, user_id: str, quest_id: str) -> Dict[str, Any]:
        """领取任务奖励"""
        with self._lock:
            try:
                result = self.get_or_create_player(user_id)
                if not result.get('success'):
                    return result
                player_id = result['player']['player_id']

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT pqp.progress_id, pqp.status, pqp.reward_claimed,
                               gq.reward_exp, gq.reward_coins, gq.title
                        FROM player_quest_progress pqp
                        JOIN game_quests gq ON pqp.quest_id = gq.quest_id
                        WHERE pqp.player_id = ? AND pqp.quest_id = ?
                    ''', (player_id, quest_id))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'message': '未接受此任务'}
                    if row[1] != 'completed':
                        return {'success': False, 'message': '任务尚未完成'}
                    if row[2]:
                        return {'success': False, 'message': '奖励已领取'}

                    # 发放奖励
                    exp_reward = row[3]
                    coins_reward = row[4]

                    cursor.execute('''
                        UPDATE player_quest_progress
                        SET reward_claimed = 1
                        WHERE progress_id = ?
                    ''', (row[0],))

                    cursor.execute('''
                        UPDATE game_players
                        SET exp_points = exp_points + ?,
                            coins = coins + ?,
                            total_quests_completed = total_quests_completed + 1,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE player_id = ?
                    ''', (exp_reward, coins_reward, player_id))
                    conn.commit()

                # 检查升级
                level_result = self.add_exp(user_id, 0)

                return {
                    'success': True,
                    'exp_gained': exp_reward,
                    'coins_gained': coins_reward,
                    'leveled_up': level_result.get('leveled_up', False),
                    'new_level': level_result.get('new_level'),
                    'message': f'领取奖励: {exp_reward}经验 + {coins_reward}金币'
                }
            except Exception as e:
                logger.error(f"领取奖励失败: {e}")
                return {'success': False, 'error': str(e)}

    def get_player_quests(self, user_id: str, status: str = None) -> Dict[str, Any]:
        """获取玩家任务列表"""
        try:
            result = self.get_or_create_player(user_id)
            if not result.get('success'):
                return result
            player_id = result['player']['player_id']

            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                sql = '''SELECT pqp.progress_id, pqp.quest_id, gq.title, gq.description,
                                gq.difficulty, pqp.current_value, pqp.target_value,
                                pqp.status, pqp.reward_claimed, gq.reward_exp, gq.reward_coins,
                                pqp.accepted_at, pqp.completed_at
                         FROM player_quest_progress pqp
                         JOIN game_quests gq ON pqp.quest_id = gq.quest_id
                         WHERE pqp.player_id = ?'''
                params = [player_id]
                if status:
                    sql += ' AND pqp.status = ?'
                    params.append(status)
                sql += ' ORDER BY pqp.accepted_at DESC'
                cursor.execute(sql, params)
                rows = cursor.fetchall()

                quests = [{
                    'progress_id': r[0], 'quest_id': r[1], 'title': r[2],
                    'description': r[3], 'difficulty': r[4],
                    'current_value': r[5], 'target_value': r[6],
                    'status': r[7], 'reward_claimed': bool(r[8]),
                    'reward_exp': r[9], 'reward_coins': r[10],
                    'accepted_at': r[11], 'completed_at': r[12]
                } for r in rows]

                return {'success': True, 'quests': quests, 'count': len(quests)}
        except Exception as e:
            logger.error(f"获取玩家任务失败: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== 排行榜 ====================

    def get_leaderboard(self, category: str = 'exp', scope: str = 'global',
                        limit: int = 50) -> Dict[str, Any]:
        """获取排行榜"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()

                if category == 'exp':
                    order_col = 'exp_points'
                elif category == 'coins':
                    order_col = 'coins'
                elif category == 'level':
                    order_col = 'level'
                elif category == 'quests':
                    order_col = 'total_quests_completed'
                else:
                    order_col = 'exp_points'

                cursor.execute(f'''
                    SELECT player_id, user_id, nickname, level, exp_points, coins,
                           total_quests_completed, title
                    FROM game_players
                    ORDER BY {order_col} DESC
                    LIMIT ?
                ''', (limit,))
                rows = cursor.fetchall()

                entries = [{
                    'rank': idx + 1,
                    'player_id': r[0], 'user_id': r[1], 'nickname': r[2],
                    'level': r[3], 'exp': r[4], 'coins': r[5],
                    'quests_completed': r[6], 'title': r[7]
                } for idx, r in enumerate(rows)]

                return {
                    'success': True,
                    'category': category,
                    'scope': scope,
                    'leaderboard': entries,
                    'count': len(entries)
                }
        except Exception as e:
            logger.error(f"获取排行榜失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_player_rank(self, user_id: str, category: str = 'exp') -> Dict[str, Any]:
        """获取玩家排名"""
        try:
            result = self.get_or_create_player(user_id)
            if not result.get('success'):
                return result

            leaderboard = self.get_leaderboard(category, 'global', 10000)
            if not leaderboard.get('success'):
                return leaderboard

            entries = leaderboard['leaderboard']
            for entry in entries:
                if entry['user_id'] == user_id:
                    return {
                        'success': True,
                        'rank': entry['rank'],
                        'category': category,
                        'total_players': len(entries)
                    }
            return {'success': False, 'message': '未在排行榜中找到'}
        except Exception as e:
            logger.error(f"获取玩家排名失败: {e}")
            return {'success': False, 'error': str(e)}

    # ==================== 物品商店 ====================

    def list_items(self, item_type: str = None) -> Dict[str, Any]:
        """列出商店物品"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                sql = '''SELECT item_id, name, description, item_type, rarity,
                                icon, price_coins, price_gems, effects
                         FROM game_items'''
                params = []
                if item_type:
                    sql += ' WHERE item_type = ?'
                    params.append(item_type)
                sql += ' ORDER BY price_coins ASC'
                cursor.execute(sql, params)
                rows = cursor.fetchall()

                items = []
                for r in rows:
                    effects = r[8]
                    try:
                        effects = json.loads(effects) if effects else {}
                    except Exception:
                        effects = {}
                    items.append({
                        'item_id': r[0], 'name': r[1], 'description': r[2],
                        'item_type': r[3], 'rarity': r[4], 'icon': r[5],
                        'price_coins': r[6], 'price_gems': r[7], 'effects': effects
                    })

                return {'success': True, 'items': items, 'count': len(items)}
        except Exception as e:
            logger.error(f"列出物品失败: {e}")
            return {'success': False, 'error': str(e)}

    def buy_item(self, user_id: str, item_id: str, quantity: int = 1) -> Dict[str, Any]:
        """购买物品"""
        with self._lock:
            try:
                result = self.get_or_create_player(user_id)
                if not result.get('success'):
                    return result
                player_id = result['player']['player_id']
                player_coins = result['player']['coins']
                player_gems = result['player']['gems']

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT name, price_coins, price_gems, stackable FROM game_items WHERE item_id = ?',
                                   (item_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'message': '物品不存在'}

                    total_coins = row[1] * quantity
                    total_gems = row[2] * quantity

                    if player_coins < total_coins or player_gems < total_gems:
                        return {'success': False, 'message': '金币或钻石不足'}

                    # 扣除金币和钻石
                    cursor.execute('''
                        UPDATE game_players
                        SET coins = coins - ?, gems = gems - ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE player_id = ?
                    ''', (total_coins, total_gems, player_id))

                    # 添加到库存
                    try:
                        cursor.execute('''
                            INSERT INTO player_inventory
                            (inventory_id, player_id, item_id, quantity)
                            VALUES (?, ?, ?, ?)
                        ''', (f"inv_{int(time.time())}_{player_id[:8]}",
                              player_id, item_id, quantity))
                    except sqlite3.IntegrityError:
                        if row[3]:  # stackable
                            cursor.execute('''
                                UPDATE player_inventory
                                SET quantity = quantity + ?
                                WHERE player_id = ? AND item_id = ?
                            ''', (quantity, player_id, item_id))
                        else:
                            return {'success': False, 'message': '已拥有此物品且不可堆叠'}

                    conn.commit()

                return {
                    'success': True,
                    'item_id': item_id,
                    'item_name': row[0],
                    'quantity': quantity,
                    'coins_spent': total_coins,
                    'gems_spent': total_gems,
                    'message': f'购买成功: {row[0]} x{quantity}'
                }
            except Exception as e:
                logger.error(f"购买物品失败: {e}")
                return {'success': False, 'error': str(e)}

    def get_inventory(self, user_id: str) -> Dict[str, Any]:
        """获取玩家库存"""
        try:
            result = self.get_or_create_player(user_id)
            if not result.get('success'):
                return result
            player_id = result['player']['player_id']

            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT pi.inventory_id, pi.item_id, gi.name, gi.description,
                           gi.item_type, gi.rarity, gi.icon, gi.effects,
                           pi.quantity, pi.equipped, pi.acquired_at
                    FROM player_inventory pi
                    JOIN game_items gi ON pi.item_id = gi.item_id
                    WHERE pi.player_id = ?
                    ORDER BY gi.rarity DESC, pi.acquired_at DESC
                ''', (player_id,))
                rows = cursor.fetchall()

                inventory = []
                for r in rows:
                    effects = r[7]
                    try:
                        effects = json.loads(effects) if effects else {}
                    except Exception:
                        effects = {}
                    inventory.append({
                        'inventory_id': r[0], 'item_id': r[1], 'name': r[2],
                        'description': r[3], 'item_type': r[4], 'rarity': r[5],
                        'icon': r[6], 'effects': effects,
                        'quantity': r[8], 'equipped': bool(r[9]),
                        'acquired_at': r[10]
                    })

                return {
                    'success': True,
                    'inventory': inventory,
                    'count': len(inventory)
                }
        except Exception as e:
            logger.error(f"获取库存失败: {e}")
            return {'success': False, 'error': str(e)}

    def use_item(self, user_id: str, item_id: str) -> Dict[str, Any]:
        """使用消耗品"""
        with self._lock:
            try:
                result = self.get_or_create_player(user_id)
                if not result.get('success'):
                    return result
                player_id = result['player']['player_id']

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT pi.inventory_id, pi.quantity, gi.name, gi.effects, gi.item_type
                        FROM player_inventory pi
                        JOIN game_items gi ON pi.item_id = gi.item_id
                        WHERE pi.player_id = ? AND pi.item_id = ?
                    ''', (player_id, item_id))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'message': '未拥有此物品'}
                    if row[1] <= 0:
                        return {'success': False, 'message': '物品数量不足'}

                    effects = json.loads(row[3]) if row[3] else {}
                    if row[4] != 'consumable':
                        return {'success': False, 'message': '此物品不可使用'}

                    # 应用效果
                    effect_msg = ''
                    if effects.get('effect') == 'exp':
                        exp_val = effects.get('value', 0)
                        cursor.execute('UPDATE game_players SET exp_points = exp_points + ? WHERE player_id = ?',
                                       (exp_val, player_id))
                        effect_msg = f'获得 {exp_val} 经验值'
                    elif effects.get('effect') == 'energy':
                        energy_val = effects.get('value', 0)
                        cursor.execute('UPDATE game_players SET energy = MIN(max_energy, energy + ?) WHERE player_id = ?',
                                       (energy_val, player_id))
                        effect_msg = f'恢复 {energy_val} 点能量'

                    # 减少数量
                    new_quantity = row[1] - 1
                    if new_quantity <= 0:
                        cursor.execute('DELETE FROM player_inventory WHERE inventory_id = ?', (row[0],))
                    else:
                        cursor.execute('UPDATE player_inventory SET quantity = ? WHERE inventory_id = ?',
                                       (new_quantity, row[0]))
                    conn.commit()

                return {
                    'success': True,
                    'item_name': row[2],
                    'effect': effect_msg,
                    'remaining': new_quantity,
                    'message': f'使用 {row[2]}: {effect_msg}'
                }
            except Exception as e:
                logger.error(f"使用物品失败: {e}")
                return {'success': False, 'error': str(e)}

    # ==================== 统计 ====================

    def get_statistics(self) -> Dict[str, Any]:
        """获取引擎统计"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM game_players')
                player_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM game_quests')
                quest_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM player_quest_progress')
                progress_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM player_quest_progress WHERE status = "completed"')
                completed_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM game_items')
                item_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM player_inventory')
                inventory_count = cursor.fetchone()[0]
                cursor.execute('SELECT AVG(level) FROM game_players')
                avg_level_row = cursor.fetchone()
                avg_level = avg_level_row[0] if avg_level_row and avg_level_row[0] else 0
                cursor.execute('SELECT MAX(level) FROM game_players')
                max_level_row = cursor.fetchone()
                max_level = max_level_row[0] if max_level_row and max_level_row[0] else 0

                return {
                    'success': True,
                    'players': player_count,
                    'quests': quest_count,
                    'quest_progress': progress_count,
                    'completed_quests': completed_count,
                    'items': item_count,
                    'inventory_records': inventory_count,
                    'avg_level': round(avg_level, 1),
                    'max_level': max_level
                }
        except Exception as e:
            logger.error(f"获取统计失败: {e}")
            return {'success': False, 'error': str(e)}


# 单例实例
gamification_engine = GamificationEngine()
