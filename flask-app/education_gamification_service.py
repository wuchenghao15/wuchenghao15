#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育游戏化服务 (v15.24.0)
====================================
提供游戏化设计、积分系统、成就系统、排行榜、任务系统、徽章系统、虚拟货币和社交游戏等综合管理服务。

核心能力：
1. 游戏化设计 - 游戏元素配置、教育差异化设置
2. 积分系统 - 学习积分、行为积分、成就积分、任务积分、社交积分
3. 成就系统 - 学习成就、行为成就、社交成就、竞赛成就
4. 排行榜 - 总分排行、学习排行、竞赛排行、社交排行
5. 任务系统 - 日常任务、周任务、月任务、学习任务、社交任务
6. 徽章系统 - 学习徽章、行为徽章、社交徽章、竞赛徽章
7. 虚拟货币 - 学习币、成就币、社交币、奖励币
8. 社交游戏 - 对战游戏、合作游戏、竞赛游戏、互动游戏
9. 预警管理 - 游戏化预警规则、预警记录
10. 统计分析 - 游戏化数据统计

差异化支持：
- 成人教育：侧重职业技能提升、专业认证、学习成果转化
- K12教育：侧重兴趣培养、知识积累、综合素质发展
"""
import os
import json
import uuid
import sqlite3
import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_gamification_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationGamification')


# ========== 游戏化配置 ==========

GAME_ELEMENTS = {
    'points': {'name': '积分', 'description': '学习和行为奖励积分'},
    'achievements': {'name': '成就', 'description': '完成特定目标获得的荣誉'},
    'badges': {'name': '徽章', 'description': '可视化的成就标志'},
    'levels': {'name': '等级', 'description': '基于积分的等级系统'},
    'leaderboard': {'name': '排行榜', 'description': '玩家排名展示'},
    'tasks': {'name': '任务', 'description': '游戏化的学习任务'},
    'challenges': {'name': '挑战', 'description': '限时或难度较高的任务'},
    'rewards': {'name': '奖励', 'description': '完成任务获得的奖励'}
}

POINT_SYSTEMS = {
    'learning': {'name': '学习积分', 'multiplier': 1.0, 'description': '完成学习活动获得'},
    'behavior': {'name': '行为积分', 'multiplier': 0.8, 'description': '良好学习行为获得'},
    'achievement': {'name': '成就积分', 'multiplier': 2.0, 'description': '获得成就时奖励'},
    'task': {'name': '任务积分', 'multiplier': 1.5, 'description': '完成任务获得'},
    'social': {'name': '社交积分', 'multiplier': 1.2, 'description': '社交互动获得'},
    'competition': {'name': '竞赛积分', 'multiplier': 3.0, 'description': '竞赛获胜获得'},
    'continuous': {'name': '连续积分', 'multiplier': 1.3, 'description': '连续学习奖励'},
    'special': {'name': '特殊积分', 'multiplier': 5.0, 'description': '特殊活动奖励'}
}

ACHIEVEMENT_TYPES = {
    'learning': {'name': '学习成就', 'icon': '📚', 'description': '学习相关成就'},
    'behavior': {'name': '行为成就', 'icon': '✅', 'description': '行为习惯成就'},
    'social': {'name': '社交成就', 'icon': '👥', 'description': '社交互动成就'},
    'competition': {'name': '竞赛成就', 'icon': '🏆', 'description': '竞赛获胜成就'},
    'special': {'name': '特殊成就', 'icon': '⭐', 'description': '特殊活动成就'},
    'milestone': {'name': '里程碑成就', 'icon': '🎯', 'description': '重要里程碑'},
    'annual': {'name': '年度成就', 'icon': '📅', 'description': '年度目标达成'},
    'lifetime': {'name': '终身成就', 'icon': '💎', 'description': '终身学习成就'}
}

LEADERBOARD_TYPES = {
    'total': {'name': '总分排行', 'period': 'all_time', 'description': '所有积分总和排名'},
    'learning': {'name': '学习排行', 'period': 'monthly', 'description': '学习积分排名'},
    'competition': {'name': '竞赛排行', 'period': 'weekly', 'description': '竞赛积分排名'},
    'social': {'name': '社交排行', 'period': 'monthly', 'description': '社交积分排名'},
    'monthly': {'name': '月度排行', 'period': 'monthly', 'description': '月度总分排名'},
    'annual': {'name': '年度排行', 'period': 'yearly', 'description': '年度总分排名'},
    'weekly': {'name': '周排行', 'period': 'weekly', 'description': '周度总分排名'},
    'realtime': {'name': '实时排行', 'period': 'realtime', 'description': '实时积分排名'}
}

TASK_TYPES = {
    'daily': {'name': '日常任务', 'frequency': 'daily', 'refresh_time': '00:00', 'description': '每天刷新的任务'},
    'weekly': {'name': '周任务', 'frequency': 'weekly', 'refresh_day': 0, 'description': '每周刷新的任务'},
    'monthly': {'name': '月任务', 'frequency': 'monthly', 'refresh_day': 1, 'description': '每月刷新的任务'},
    'learning': {'name': '学习任务', 'frequency': 'ongoing', 'description': '学习相关任务'},
    'social': {'name': '社交任务', 'frequency': 'ongoing', 'description': '社交互动任务'},
    'challenge': {'name': '挑战任务', 'frequency': 'limited', 'description': '限时挑战任务'},
    'achievement': {'name': '成就任务', 'frequency': 'ongoing', 'description': '成就解锁任务'},
    'special': {'name': '特殊任务', 'frequency': 'event', 'description': '特殊活动任务'}
}

BADGE_TYPES = {
    'learning': {'name': '学习徽章', 'color': '#4CAF50', 'description': '学习表现徽章'},
    'behavior': {'name': '行为徽章', 'color': '#2196F3', 'description': '行为习惯徽章'},
    'social': {'name': '社交徽章', 'color': '#FF9800', 'description': '社交互动徽章'},
    'competition': {'name': '竞赛徽章', 'color': '#F44336', 'description': '竞赛表现徽章'},
    'level': {'name': '等级徽章', 'color': '#9C27B0', 'description': '等级解锁徽章'},
    'special': {'name': '特殊徽章', 'color': '#E91E63', 'description': '特殊活动徽章'},
    'limited': {'name': '限时徽章', 'color': '#00BCD4', 'description': '限时获取徽章'},
    'memorial': {'name': '纪念徽章', 'color': '#FF5722', 'description': '纪念意义徽章'}
}

CURRENCY_TYPES = {
    'learning': {'name': '学习币', 'symbol': '📚', 'exchange_rate': 1.0, 'description': '学习活动获得'},
    'achievement': {'name': '成就币', 'symbol': '🏅', 'exchange_rate': 2.0, 'description': '获得成就奖励'},
    'social': {'name': '社交币', 'symbol': '💬', 'exchange_rate': 1.5, 'description': '社交互动获得'},
    'reward': {'name': '奖励币', 'symbol': '🎁', 'exchange_rate': 3.0, 'description': '完成奖励任务获得'},
    'exchange': {'name': '兑换币', 'symbol': '💰', 'exchange_rate': 0.5, 'description': '可兑换实物奖励'},
    'points': {'name': '积分币', 'symbol': '⭐', 'exchange_rate': 1.0, 'description': '积分兑换货币'},
    'event': {'name': '活动币', 'symbol': '🎉', 'exchange_rate': 2.5, 'description': '活动期间获得'},
    'rare': {'name': '稀有币', 'symbol': '💎', 'exchange_rate': 10.0, 'description': '稀有活动获得'}
}

SOCIAL_GAME_TYPES = {
    'battle': {'name': '对战游戏', 'mode': 'pvp', 'description': '玩家对战游戏'},
    'cooperative': {'name': '合作游戏', 'mode': 'pve', 'description': '玩家合作游戏'},
    'competition': {'name': '竞赛游戏', 'mode': 'ranked', 'description': '排名竞赛游戏'},
    'interaction': {'name': '互动游戏', 'mode': 'social', 'description': '社交互动游戏'},
    'quiz': {'name': '知识问答', 'mode': 'quiz', 'description': '知识问答游戏'},
    'skill_challenge': {'name': '技能挑战', 'mode': 'challenge', 'description': '技能挑战游戏'},
    'roleplay': {'name': '角色扮演', 'mode': 'story', 'description': '角色扮演游戏'},
    'strategy': {'name': '策略游戏', 'mode': 'strategy', 'description': '策略类游戏'}
}


class EducationGamificationService:
    """教育游戏化服务"""

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
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS gamification_config (
                        config_id TEXT PRIMARY KEY,
                        config_name TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        elements TEXT,
                        point_rules TEXT,
                        achievement_rules TEXT,
                        task_rules TEXT,
                        badge_rules TEXT,
                        currency_rules TEXT,
                        leaderboard_rules TEXT,
                        social_game_rules TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS config_settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        config_id TEXT NOT NULL,
                        setting_key TEXT NOT NULL,
                        setting_value TEXT,
                        description TEXT,
                        FOREIGN KEY (config_id) REFERENCES gamification_config(config_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS point_system (
                        point_id TEXT PRIMARY KEY,
                        point_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        name TEXT,
                        multiplier REAL DEFAULT 1.0,
                        min_points INTEGER DEFAULT 0,
                        max_points INTEGER DEFAULT 100000,
                        description TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS point_records (
                        record_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        point_type TEXT NOT NULL,
                        education_type TEXT,
                        points INTEGER NOT NULL,
                        reason TEXT,
                        reference_id TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS achievement_system (
                        achievement_id TEXT PRIMARY KEY,
                        achievement_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        name TEXT NOT NULL,
                        icon TEXT,
                        description TEXT,
                        points_required INTEGER DEFAULT 0,
                        tasks_required INTEGER DEFAULT 0,
                        is_locked INTEGER DEFAULT 1,
                        is_secret INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS achievement_records (
                        record_id TEXT PRIMARY KEY,
                        achievement_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        unlocked_at TEXT,
                        progress INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'in_progress',
                        FOREIGN KEY (achievement_id) REFERENCES achievement_system(achievement_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS leaderboard (
                        board_id TEXT PRIMARY KEY,
                        board_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        name TEXT NOT NULL,
                        description TEXT,
                        period TEXT DEFAULT 'monthly',
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS leaderboard_data (
                        data_id TEXT PRIMARY KEY,
                        board_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        score INTEGER NOT NULL,
                        rank INTEGER DEFAULT 0,
                        period_start TEXT,
                        period_end TEXT,
                        created_at TEXT,
                        FOREIGN KEY (board_id) REFERENCES leaderboard(board_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS task_system (
                        task_id TEXT PRIMARY KEY,
                        task_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        name TEXT NOT NULL,
                        description TEXT,
                        points_reward INTEGER DEFAULT 0,
                        currency_reward TEXT,
                        badge_reward TEXT,
                        achievement_reward TEXT,
                        is_daily INTEGER DEFAULT 0,
                        is_repeatable INTEGER DEFAULT 0,
                        expires_at TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS task_records (
                        record_id TEXT PRIMARY KEY,
                        task_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        status TEXT DEFAULT 'pending',
                        progress INTEGER DEFAULT 0,
                        completed_at TEXT,
                        claimed_at TEXT,
                        FOREIGN KEY (task_id) REFERENCES task_system(task_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS badge_system (
                        badge_id TEXT PRIMARY KEY,
                        badge_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        name TEXT NOT NULL,
                        color TEXT DEFAULT '#4CAF50',
                        icon TEXT,
                        description TEXT,
                        rarity TEXT DEFAULT 'common',
                        unlock_condition TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS badge_records (
                        record_id TEXT PRIMARY KEY,
                        badge_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        unlocked_at TEXT,
                        status TEXT DEFAULT 'locked',
                        FOREIGN KEY (badge_id) REFERENCES badge_system(badge_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS virtual_currency (
                        currency_id TEXT PRIMARY KEY,
                        currency_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        name TEXT NOT NULL,
                        symbol TEXT,
                        exchange_rate REAL DEFAULT 1.0,
                        description TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS currency_transactions (
                        tx_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        currency_type TEXT NOT NULL,
                        education_type TEXT,
                        amount INTEGER NOT NULL,
                        transaction_type TEXT,
                        reason TEXT,
                        reference_id TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS social_games (
                        game_id TEXT PRIMARY KEY,
                        game_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        name TEXT NOT NULL,
                        description TEXT,
                        mode TEXT DEFAULT 'pvp',
                        max_players INTEGER DEFAULT 2,
                        min_players INTEGER DEFAULT 2,
                        duration_minutes INTEGER DEFAULT 15,
                        points_reward INTEGER DEFAULT 0,
                        currency_reward TEXT,
                        badge_reward TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS game_records (
                        record_id TEXT PRIMARY KEY,
                        game_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        score INTEGER DEFAULT 0,
                        result TEXT DEFAULT 'pending',
                        participants TEXT,
                        started_at TEXT,
                        ended_at TEXT,
                        FOREIGN KEY (game_id) REFERENCES social_games(game_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS gamification_alerts (
                        alert_id TEXT PRIMARY KEY,
                        alert_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        name TEXT NOT NULL,
                        description TEXT,
                        threshold INTEGER DEFAULT 0,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alert_history (
                        history_id TEXT PRIMARY KEY,
                        alert_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        triggered_at TEXT,
                        message TEXT,
                        status TEXT DEFAULT 'triggered',
                        FOREIGN KEY (alert_id) REFERENCES gamification_alerts(alert_id)
                    )
                ''')
                conn.commit()
                logger.info('教育游戏化服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 游戏化设计 ==========

    def create_gamification_config(self, config_name: str, education_type: str,
                                    **kwargs) -> Dict[str, Any]:
        try:
            config_id = f"gam_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            elements = json.dumps(kwargs.get('elements', list(GAME_ELEMENTS.keys())))
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO gamification_config (
                            config_id, config_name, education_type, elements,
                            point_rules, achievement_rules, task_rules,
                            badge_rules, currency_rules, leaderboard_rules,
                            social_game_rules, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (config_id, config_name, education_type, elements,
                          kwargs.get('point_rules'), kwargs.get('achievement_rules'),
                          kwargs.get('task_rules'), kwargs.get('badge_rules'),
                          kwargs.get('currency_rules'), kwargs.get('leaderboard_rules'),
                          kwargs.get('social_game_rules'), now, now))
                    conn.commit()
                    logger.info(f'创建游戏化配置: {config_name} ({config_id})')
                    return {'success': True, 'config_id': config_id}
        except Exception as e:
            logger.error(f'创建游戏化配置失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_gamification_config(self, config_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    updates = []
                    params = []
                    if 'elements' in kwargs:
                        updates.append('elements = ?')
                        params.append(json.dumps(kwargs['elements']))
                    if 'point_rules' in kwargs:
                        updates.append('point_rules = ?')
                        params.append(kwargs['point_rules'])
                    if 'achievement_rules' in kwargs:
                        updates.append('achievement_rules = ?')
                        params.append(kwargs['achievement_rules'])
                    if 'task_rules' in kwargs:
                        updates.append('task_rules = ?')
                        params.append(kwargs['task_rules'])
                    if 'badge_rules' in kwargs:
                        updates.append('badge_rules = ?')
                        params.append(kwargs['badge_rules'])
                    if 'currency_rules' in kwargs:
                        updates.append('currency_rules = ?')
                        params.append(kwargs['currency_rules'])
                    if 'leaderboard_rules' in kwargs:
                        updates.append('leaderboard_rules = ?')
                        params.append(kwargs['leaderboard_rules'])
                    if 'social_game_rules' in kwargs:
                        updates.append('social_game_rules = ?')
                        params.append(kwargs['social_game_rules'])
                    if 'config_name' in kwargs:
                        updates.append('config_name = ?')
                        params.append(kwargs['config_name'])
                    params.append(config_id)
                    if updates:
                        cursor.execute(f'UPDATE gamification_config SET {", ".join(updates)}, updated_at = ? WHERE config_id = ?',
                                     [now] + params)
                        conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'更新游戏化配置失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_gamification_config(self, config_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM gamification_config WHERE config_id = ?', (config_id,))
                config = cursor.fetchone()
                if not config:
                    return {'success': False, 'error': '配置不存在'}
                return {'success': True, 'config': dict(config)}
        except Exception as e:
            logger.error(f'获取游戏化配置失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_gamification_configs(self, education_type: str = None,
                                   page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM gamification_config WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                configs = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'configs': configs, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取游戏化配置列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 积分系统 ==========

    def add_points(self, user_id: int, point_type: str, points: int,
                   education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"prd_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = POINT_SYSTEMS.get(point_type, {})
            multiplier = config.get('multiplier', 1.0)
            actual_points = int(points * multiplier)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO point_records (
                            record_id, user_id, user_name, point_type,
                            education_type, points, reason, reference_id, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (record_id, user_id, kwargs.get('user_name'),
                          point_type, education_type, actual_points,
                          kwargs.get('reason'), kwargs.get('reference_id'), now))
                    conn.commit()
                    logger.info(f'用户 {user_id} 获得积分: {actual_points} ({point_type})')
                    return {'success': True, 'points_added': actual_points, 'record_id': record_id}
        except Exception as e:
            logger.error(f'添加积分失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_user_points(self, user_id: int, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = 'SELECT point_type, SUM(points) as total FROM point_records WHERE user_id = ?'
                params = [user_id]
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' GROUP BY point_type'
                cursor.execute(query, params)
                results = cursor.fetchall()
                points_by_type = {row[0]: row[1] or 0 for row in results}
                total_points = sum(points_by_type.values())
                return {'success': True, 'total_points': total_points, 'points_by_type': points_by_type}
        except Exception as e:
            logger.error(f'获取用户积分失败: {e}')
            return {'success': False, 'error': str(e)}

    def deduct_points(self, user_id: int, point_type: str, points: int,
                      education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"prd_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    query = 'SELECT SUM(points) as total FROM point_records WHERE user_id = ? AND point_type = ?'
                    params = [user_id, point_type]
                    if education_type:
                        query += ' AND education_type = ?'
                        params.append(education_type)
                    cursor.execute(query, params)
                    current = cursor.fetchone()[0] or 0
                    if current < points:
                        return {'success': False, 'error': '积分不足'}
                    cursor.execute('''
                        INSERT INTO point_records (
                            record_id, user_id, user_name, point_type,
                            education_type, points, reason, reference_id, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (record_id, user_id, kwargs.get('user_name'),
                          point_type, education_type, -points,
                          kwargs.get('reason', '积分扣除'), kwargs.get('reference_id'), now))
                    conn.commit()
                    return {'success': True, 'points_deducted': points, 'record_id': record_id}
        except Exception as e:
            logger.error(f'扣除积分失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_point_history(self, user_id: int, point_type: str = None,
                          page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM point_records WHERE user_id = ?'
                params = [user_id]
                if point_type:
                    query += ' AND point_type = ?'
                    params.append(point_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取积分历史失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 成就系统 ==========

    def create_achievement(self, achievement_type: str, education_type: str,
                           name: str, **kwargs) -> Dict[str, Any]:
        try:
            achievement_id = f"ach_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = ACHIEVEMENT_TYPES.get(achievement_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO achievement_system (
                            achievement_id, achievement_type, education_type,
                            name, icon, description, points_required,
                            tasks_required, is_locked, is_secret,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
                    ''', (achievement_id, achievement_type, education_type,
                          name, kwargs.get('icon', config.get('icon')),
                          kwargs.get('description', config.get('description')),
                          kwargs.get('points_required', 0),
                          kwargs.get('tasks_required', 0),
                          kwargs.get('is_secret', 0), now, now))
                    conn.commit()
                    logger.info(f'创建成就: {name} ({achievement_id})')
                    return {'success': True, 'achievement_id': achievement_id}
        except Exception as e:
            logger.error(f'创建成就失败: {e}')
            return {'success': False, 'error': str(e)}

    def unlock_achievement(self, achievement_id: str, user_id: int,
                           **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            record_id = f"acr_{uuid.uuid4().hex[:12]}"
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM achievement_system WHERE achievement_id = ?', (achievement_id,))
                    achievement = cursor.fetchone()
                    if not achievement:
                        return {'success': False, 'error': '成就不存在'}
                    cursor.execute('SELECT * FROM achievement_records WHERE achievement_id = ? AND user_id = ?',
                                 (achievement_id, user_id))
                    existing = cursor.fetchone()
                    if existing and existing[5] == 'unlocked':
                        return {'success': False, 'error': '成就已解锁'}
                    cursor.execute('''
                        INSERT OR REPLACE INTO achievement_records (
                            record_id, achievement_id, user_id, user_name,
                            unlocked_at, progress, status
                        ) VALUES (?, ?, ?, ?, ?, 100, 'unlocked')
                    ''', (record_id, achievement_id, user_id, kwargs.get('user_name'), now))
                    conn.commit()
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'解锁成就失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_achievement_progress(self, achievement_id: str, user_id: int,
                                     progress: int, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM achievement_system WHERE achievement_id = ?', (achievement_id,))
                    achievement = cursor.fetchone()
                    if not achievement:
                        return {'success': False, 'error': '成就不存在'}
                    cursor.execute('SELECT * FROM achievement_records WHERE achievement_id = ? AND user_id = ?',
                                 (achievement_id, user_id))
                    existing = cursor.fetchone()
                    record_id = existing[0] if existing else f"acr_{uuid.uuid4().hex[:12]}"
                    status = 'unlocked' if progress >= 100 else 'in_progress'
                    unlocked_at = now if progress >= 100 else (existing[4] if existing else None)
                    cursor.execute('''
                        INSERT OR REPLACE INTO achievement_records (
                            record_id, achievement_id, user_id, user_name,
                            unlocked_at, progress, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (record_id, achievement_id, user_id, kwargs.get('user_name'),
                          unlocked_at, progress, status))
                    conn.commit()
                    return {'success': True, 'progress': progress, 'status': status}
        except Exception as e:
            logger.error(f'更新成就进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_user_achievements(self, user_id: int, education_type: str = None,
                               status: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = '''
                    SELECT ar.*, asys.name, asys.icon, asys.description, asys.achievement_type
                    FROM achievement_records ar
                    JOIN achievement_system asys ON ar.achievement_id = asys.achievement_id
                    WHERE ar.user_id = ?
                '''
                params = [user_id]
                if education_type:
                    query += ' AND asys.education_type = ?'
                    params.append(education_type)
                if status:
                    query += ' AND ar.status = ?'
                    params.append(status)
                cursor.execute(query, params)
                achievements = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'achievements': achievements}
        except Exception as e:
            logger.error(f'获取用户成就失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 排行榜 ==========

    def create_leaderboard(self, board_type: str, education_type: str,
                            name: str, **kwargs) -> Dict[str, Any]:
        try:
            board_id = f"lbd_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = LEADERBOARD_TYPES.get(board_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO leaderboard (
                            board_id, board_type, education_type, name,
                            description, period, is_active, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
                    ''', (board_id, board_type, education_type, name,
                          kwargs.get('description', config.get('description')),
                          kwargs.get('period', config.get('period', 'monthly')),
                          now, now))
                    conn.commit()
                    logger.info(f'创建排行榜: {name} ({board_id})')
                    return {'success': True, 'board_id': board_id}
        except Exception as e:
            logger.error(f'创建排行榜失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_leaderboard_scores(self, board_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT board_type, period FROM leaderboard WHERE board_id = ?', (board_id,))
                    board = cursor.fetchone()
                    if not board:
                        return {'success': False, 'error': '排行榜不存在'}
                    period_start = datetime.now().replace(day=1, hour=0, minute=0, second=0).isoformat()[:10] if board[1] == 'monthly' else \
                                   (datetime.now() - timedelta(days=7)).isoformat()[:10] if board[1] == 'weekly' else \
                                   datetime.now().replace(month=1, day=1, hour=0, minute=0, second=0).isoformat()[:10] if board[1] == 'yearly' else \
                                   None
                    cursor.execute('''
                        SELECT user_id, user_name, SUM(points) as total
                        FROM point_records
                        WHERE point_type = ? OR ? = 'total'
                        GROUP BY user_id, user_name
                        ORDER BY total DESC
                        LIMIT 100
                    ''', (board[0], board[0]))
                    results = cursor.fetchall()
                    rank = 1
                    for row in results:
                        data_id = f"lbd_{uuid.uuid4().hex[:8]}"
                        cursor.execute('''
                            INSERT OR REPLACE INTO leaderboard_data (
                                data_id, board_id, user_id, user_name,
                                score, rank, period_start, period_end, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (data_id, board_id, row[0], row[1], row[2], rank,
                              period_start, datetime.now().isoformat()[:10], now))
                        rank += 1
                    conn.commit()
                    return {'success': True, 'updated_count': len(results)}
        except Exception as e:
            logger.error(f'更新排行榜分数失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_leaderboard(self, board_id: str, limit: int = 50) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM leaderboard WHERE board_id = ?', (board_id,))
                board = cursor.fetchone()
                if not board:
                    return {'success': False, 'error': '排行榜不存在'}
                cursor.execute('''
                    SELECT * FROM leaderboard_data
                    WHERE board_id = ?
                    ORDER BY rank ASC
                    LIMIT ?
                ''', (board_id, limit))
                data = [dict(d) for d in cursor.fetchall()]
                return {'success': True, 'board': dict(board), 'data': data}
        except Exception as e:
            logger.error(f'获取排行榜失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_user_rank(self, board_id: str, user_id: int) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM leaderboard_data WHERE board_id = ? AND user_id = ?',
                             (board_id, user_id))
                result = cursor.fetchone()
                if not result:
                    return {'success': False, 'error': '用户未上榜'}
                return {'success': True, 'rank': result[5], 'score': result[4]}
        except Exception as e:
            logger.error(f'获取用户排名失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_leaderboards(self, education_type: str = None,
                           page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM leaderboard WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                boards = [dict(b) for b in cursor.fetchall()]
                return {'success': True, 'boards': boards, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取排行榜列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 任务系统 ==========

    def create_task(self, task_type: str, education_type: str, name: str,
                    **kwargs) -> Dict[str, Any]:
        try:
            task_id = f"tsk_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = TASK_TYPES.get(task_type, {})
            is_daily = 1 if task_type == 'daily' else 0
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO task_system (
                            task_id, task_type, education_type, name,
                            description, points_reward, currency_reward,
                            badge_reward, achievement_reward, is_daily,
                            is_repeatable, expires_at, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (task_id, task_type, education_type, name,
                          kwargs.get('description', config.get('description')),
                          kwargs.get('points_reward', 0),
                          kwargs.get('currency_reward'),
                          kwargs.get('badge_reward'),
                          kwargs.get('achievement_reward'),
                          is_daily, kwargs.get('is_repeatable', 0),
                          kwargs.get('expires_at'), now, now))
                    conn.commit()
                    logger.info(f'创建任务: {name} ({task_id})')
                    return {'success': True, 'task_id': task_id}
        except Exception as e:
            logger.error(f'创建任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def assign_task(self, task_id: str, user_id: int, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"tsr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM task_system WHERE task_id = ?', (task_id,))
                    task = cursor.fetchone()
                    if not task:
                        return {'success': False, 'error': '任务不存在'}
                    cursor.execute('SELECT * FROM task_records WHERE task_id = ? AND user_id = ? AND status != ?',
                                 (task_id, user_id, 'completed'))
                    existing = cursor.fetchone()
                    if existing and not task[11]:
                        return {'success': False, 'error': '任务已分配'}
                    cursor.execute('''
                        INSERT INTO task_records (
                            record_id, task_id, user_id, user_name,
                            status, progress, completed_at, claimed_at
                        ) VALUES (?, ?, ?, ?, 'pending', 0, NULL, NULL)
                    ''', (record_id, task_id, user_id, kwargs.get('user_name')))
                    conn.commit()
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'分配任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_task(self, record_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM task_records WHERE record_id = ?', (record_id,))
                    record = cursor.fetchone()
                    if not record:
                        return {'success': False, 'error': '任务记录不存在'}
                    if record[4] == 'completed':
                        return {'success': False, 'error': '任务已完成'}
                    cursor.execute('UPDATE task_records SET status = ?, progress = 100, completed_at = ? WHERE record_id = ?',
                                 ('completed', now, record_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'完成任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def claim_task_reward(self, record_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT tr.*, ts.points_reward, ts.currency_reward, ts.badge_reward, ts.achievement_reward
                        FROM task_records tr
                        JOIN task_system ts ON tr.task_id = ts.task_id
                        WHERE tr.record_id = ?
                    ''', (record_id,))
                    result = cursor.fetchone()
                    if not result:
                        return {'success': False, 'error': '任务记录不存在'}
                    if result[4] != 'completed':
                        return {'success': False, 'error': '任务未完成'}
                    if result[7]:
                        return {'success': False, 'error': '奖励已领取'}
                    rewards = {}
                    if result[8]:
                        self.add_points(result[2], 'task', result[8], result[3], user_name=result[4], reason='任务奖励')
                        rewards['points'] = result[8]
                    cursor.execute('UPDATE task_records SET claimed_at = ? WHERE record_id = ?', (now, record_id))
                    conn.commit()
                    return {'success': True, 'rewards': rewards}
        except Exception as e:
            logger.error(f'领取任务奖励失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 徽章系统 ==========

    def create_badge(self, badge_type: str, education_type: str, name: str,
                     **kwargs) -> Dict[str, Any]:
        try:
            badge_id = f"bdg_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = BADGE_TYPES.get(badge_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO badge_system (
                            badge_id, badge_type, education_type, name,
                            color, icon, description, rarity,
                            unlock_condition, is_active, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                    ''', (badge_id, badge_type, education_type, name,
                          kwargs.get('color', config.get('color', '#4CAF50')),
                          kwargs.get('icon'), kwargs.get('description', config.get('description')),
                          kwargs.get('rarity', 'common'), kwargs.get('unlock_condition'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建徽章: {name} ({badge_id})')
                    return {'success': True, 'badge_id': badge_id}
        except Exception as e:
            logger.error(f'创建徽章失败: {e}')
            return {'success': False, 'error': str(e)}

    def award_badge(self, badge_id: str, user_id: int, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"bdr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM badge_system WHERE badge_id = ?', (badge_id,))
                    badge = cursor.fetchone()
                    if not badge:
                        return {'success': False, 'error': '徽章不存在'}
                    cursor.execute('SELECT * FROM badge_records WHERE badge_id = ? AND user_id = ? AND status = ?',
                                 (badge_id, user_id, 'unlocked'))
                    existing = cursor.fetchone()
                    if existing:
                        return {'success': False, 'error': '徽章已获得'}
                    cursor.execute('''
                        INSERT INTO badge_records (
                            record_id, badge_id, user_id, user_name,
                            unlocked_at, status
                        ) VALUES (?, ?, ?, ?, ?, 'unlocked')
                    ''', (record_id, badge_id, user_id, kwargs.get('user_name'), now))
                    conn.commit()
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'颁发徽章失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_user_badges(self, user_id: int, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = '''
                    SELECT br.*, bs.name, bs.color, bs.icon, bs.description, bs.badge_type, bs.rarity
                    FROM badge_records br
                    JOIN badge_system bs ON br.badge_id = bs.badge_id
                    WHERE br.user_id = ? AND br.status = 'unlocked'
                '''
                params = [user_id]
                if education_type:
                    query += ' AND bs.education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                badges = [dict(b) for b in cursor.fetchall()]
                return {'success': True, 'badges': badges}
        except Exception as e:
            logger.error(f'获取用户徽章失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_badges(self, badge_type: str = None, education_type: str = None,
                    page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM badge_system WHERE is_active = 1'
                params = []
                if badge_type:
                    query += ' AND badge_type = ?'
                    params.append(badge_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                badges = [dict(b) for b in cursor.fetchall()]
                return {'success': True, 'badges': badges, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取徽章列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 虚拟货币 ==========

    def create_currency(self, currency_type: str, education_type: str, name: str,
                        **kwargs) -> Dict[str, Any]:
        try:
            currency_id = f"cur_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = CURRENCY_TYPES.get(currency_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO virtual_currency (
                            currency_id, currency_type, education_type, name,
                            symbol, exchange_rate, description, is_active,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                    ''', (currency_id, currency_type, education_type, name,
                          kwargs.get('symbol', config.get('symbol')),
                          kwargs.get('exchange_rate', config.get('exchange_rate', 1.0)),
                          kwargs.get('description', config.get('description')),
                          now, now))
                    conn.commit()
                    logger.info(f'创建虚拟货币: {name} ({currency_id})')
                    return {'success': True, 'currency_id': currency_id}
        except Exception as e:
            logger.error(f'创建虚拟货币失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_currency(self, user_id: int, currency_type: str, amount: int,
                     education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            tx_id = f"ctx_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO currency_transactions (
                            tx_id, user_id, user_name, currency_type,
                            education_type, amount, transaction_type,
                            reason, reference_id, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'credit', ?, ?, ?)
                    ''', (tx_id, user_id, kwargs.get('user_name'),
                          currency_type, education_type, amount,
                          kwargs.get('reason'), kwargs.get('reference_id'), now))
                    conn.commit()
                    return {'success': True, 'amount_added': amount, 'tx_id': tx_id}
        except Exception as e:
            logger.error(f'添加虚拟货币失败: {e}')
            return {'success': False, 'error': str(e)}

    def deduct_currency(self, user_id: int, currency_type: str, amount: int,
                        education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            tx_id = f"ctx_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    query = 'SELECT SUM(amount) as balance FROM currency_transactions WHERE user_id = ? AND currency_type = ?'
                    params = [user_id, currency_type]
                    if education_type:
                        query += ' AND education_type = ?'
                        params.append(education_type)
                    cursor.execute(query, params)
                    balance = cursor.fetchone()[0] or 0
                    if balance < amount:
                        return {'success': False, 'error': '余额不足'}
                    cursor.execute('''
                        INSERT INTO currency_transactions (
                            tx_id, user_id, user_name, currency_type,
                            education_type, amount, transaction_type,
                            reason, reference_id, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'debit', ?, ?, ?)
                    ''', (tx_id, user_id, kwargs.get('user_name'),
                          currency_type, education_type, -amount,
                          kwargs.get('reason', '消费'), kwargs.get('reference_id'), now))
                    conn.commit()
                    return {'success': True, 'amount_deducted': amount, 'tx_id': tx_id}
        except Exception as e:
            logger.error(f'扣除虚拟货币失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_user_currency(self, user_id: int, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = 'SELECT currency_type, SUM(amount) as balance FROM currency_transactions WHERE user_id = ?'
                params = [user_id]
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' GROUP BY currency_type'
                cursor.execute(query, params)
                results = cursor.fetchall()
                balances = {row[0]: row[1] or 0 for row in results}
                return {'success': True, 'balances': balances}
        except Exception as e:
            logger.error(f'获取用户虚拟货币失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 社交游戏 ==========

    def create_social_game(self, game_type: str, education_type: str, name: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            game_id = f"soc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = SOCIAL_GAME_TYPES.get(game_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO social_games (
                            game_id, game_type, education_type, name,
                            description, mode, max_players, min_players,
                            duration_minutes, points_reward, currency_reward,
                            badge_reward, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (game_id, game_type, education_type, name,
                          kwargs.get('description', config.get('description')),
                          kwargs.get('mode', config.get('mode', 'pvp')),
                          kwargs.get('max_players', 2), kwargs.get('min_players', 2),
                          kwargs.get('duration_minutes', 15),
                          kwargs.get('points_reward', 0),
                          kwargs.get('currency_reward'),
                          kwargs.get('badge_reward'), now, now))
                    conn.commit()
                    logger.info(f'创建社交游戏: {name} ({game_id})')
                    return {'success': True, 'game_id': game_id}
        except Exception as e:
            logger.error(f'创建社交游戏失败: {e}')
            return {'success': False, 'error': str(e)}

    def start_game(self, game_id: str, user_id: int, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"gme_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM social_games WHERE game_id = ?', (game_id,))
                    game = cursor.fetchone()
                    if not game:
                        return {'success': False, 'error': '游戏不存在'}
                    cursor.execute('''
                        INSERT INTO game_records (
                            record_id, game_id, user_id, user_name,
                            score, result, participants, started_at, ended_at
                        ) VALUES (?, ?, ?, ?, 0, 'pending', ?, ?, NULL)
                    ''', (record_id, game_id, user_id, kwargs.get('user_name'),
                          json.dumps(kwargs.get('participants', [user_id])), now))
                    conn.commit()
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'开始游戏失败: {e}')
            return {'success': False, 'error': str(e)}

    def end_game(self, record_id: str, result: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT gr.*, sg.points_reward, sg.currency_reward, sg.badge_reward
                        FROM game_records gr
                        JOIN social_games sg ON gr.game_id = sg.game_id
                        WHERE gr.record_id = ?
                    ''', (record_id,))
                    result_row = cursor.fetchone()
                    if not result_row:
                        return {'success': False, 'error': '游戏记录不存在'}
                    cursor.execute('UPDATE game_records SET result = ?, score = ?, ended_at = ? WHERE record_id = ?',
                                 (result, kwargs.get('score', 0), now, record_id))
                    if result == 'win' and result_row[9]:
                        self.add_points(result_row[2], 'competition', result_row[9],
                                       result_row[1], user_name=result_row[3], reason='游戏胜利奖励')
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'结束游戏失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_game_history(self, user_id: int, game_type: str = None,
                         page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = '''
                    SELECT gr.*, sg.name, sg.mode
                    FROM game_records gr
                    JOIN social_games sg ON gr.game_id = sg.game_id
                    WHERE gr.user_id = ?
                '''
                params = [user_id]
                if game_type:
                    query += ' AND sg.game_type = ?'
                    params.append(game_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY gr.started_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取游戏历史失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 预警管理 ==========

    def create_alert(self, alert_type: str, education_type: str, name: str,
                     **kwargs) -> Dict[str, Any]:
        try:
            alert_id = f"alt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO gamification_alerts (
                            alert_id, alert_type, education_type, name,
                            description, threshold, is_active, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
                    ''', (alert_id, alert_type, education_type, name,
                          kwargs.get('description'), kwargs.get('threshold', 0),
                          now, now))
                    conn.commit()
                    logger.info(f'创建预警规则: {name} ({alert_id})')
                    return {'success': True, 'alert_id': alert_id}
        except Exception as e:
            logger.error(f'创建预警规则失败: {e}')
            return {'success': False, 'error': str(e)}

    def trigger_alert(self, alert_id: str, user_id: int, **kwargs) -> Dict[str, Any]:
        try:
            history_id = f"ath_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM gamification_alerts WHERE alert_id = ?', (alert_id,))
                    alert = cursor.fetchone()
                    if not alert:
                        return {'success': False, 'error': '预警规则不存在'}
                    cursor.execute('''
                        INSERT INTO alert_history (
                            history_id, alert_id, user_id, user_name,
                            triggered_at, message, status
                        ) VALUES (?, ?, ?, ?, ?, ?, 'triggered')
                    ''', (history_id, alert_id, user_id, kwargs.get('user_name'),
                          now, kwargs.get('message', alert[4])))
                    conn.commit()
                    return {'success': True, 'history_id': history_id}
        except Exception as e:
            logger.error(f'触发预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def resolve_alert(self, history_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE alert_history SET status = ?, triggered_at = ? WHERE history_id = ?',
                                 ('resolved', now, history_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '预警记录不存在'}
        except Exception as e:
            logger.error(f'解决预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_alert_history(self, user_id: int = None, alert_type: str = None,
                          status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM alert_history WHERE 1=1'
                params = []
                if user_id:
                    query += ' AND user_id = ?'
                    params.append(user_id)
                if alert_type:
                    query += ' AND alert_type = ?'
                    params.append(alert_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY triggered_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取预警历史失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 ==========

    def get_gamification_stats(self, user_id: int = None, education_type: str = None,
                               date_range: Tuple[str, str] = None) -> Dict[str, Any]:
        try:
            stats = {}
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if user_id:
                    query = 'SELECT SUM(points) as total FROM point_records WHERE user_id = ?'
                    params = [user_id]
                    if education_type:
                        query += ' AND education_type = ?'
                        params.append(education_type)
                    if date_range:
                        query += ' AND created_at BETWEEN ? AND ?'
                        params.extend(date_range)
                    cursor.execute(query, params)
                    stats['total_points'] = cursor.fetchone()[0] or 0
                    cursor.execute('SELECT COUNT(*) as count FROM achievement_records WHERE user_id = ? AND status = ?',
                                 (user_id, 'unlocked'))
                    stats['unlocked_achievements'] = cursor.fetchone()[0] or 0
                    cursor.execute('SELECT COUNT(*) as count FROM badge_records WHERE user_id = ? AND status = ?',
                                 (user_id, 'unlocked'))
                    stats['unlocked_badges'] = cursor.fetchone()[0] or 0
                    cursor.execute('SELECT COUNT(*) as count FROM task_records WHERE user_id = ? AND status = ?',
                                 (user_id, 'completed'))
                    stats['completed_tasks'] = cursor.fetchone()[0] or 0
                    cursor.execute('SELECT COUNT(*) as count FROM game_records WHERE user_id = ?', (user_id,))
                    stats['games_played'] = cursor.fetchone()[0] or 0
                else:
                    cursor.execute('SELECT COUNT(DISTINCT user_id) as count FROM point_records')
                    stats['active_users'] = cursor.fetchone()[0] or 0
                    cursor.execute('SELECT SUM(points) as total FROM point_records')
                    stats['total_points_issued'] = cursor.fetchone()[0] or 0
                    cursor.execute('SELECT COUNT(*) as count FROM achievement_records WHERE status = ?', ('unlocked',))
                    stats['total_achievements_unlocked'] = cursor.fetchone()[0] or 0
                    cursor.execute('SELECT COUNT(*) as count FROM badge_records WHERE status = ?', ('unlocked',))
                    stats['total_badges_awarded'] = cursor.fetchone()[0] or 0
                return {'success': True, 'stats': stats}
        except Exception as e:
            logger.error(f'获取游戏化统计失败: {e}')
            return {'success': False, 'error': str(e)}
