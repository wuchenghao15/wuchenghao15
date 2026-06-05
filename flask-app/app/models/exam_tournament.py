#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
考试锦标赛系统 - 大奖赛、金牌杯、大师杯等非官方学术技能考试活动
"""

from app.utils.logging import logger
from datetime import datetime


class Tournament:
    """锦标赛模型"""
    
    def __init__(self, tournament_id=None, name=None, description=None, 
                 tournament_type=None, start_date=None, end_date=None,
                 max_participants=None, prize_type=None, status=None,
                 created_at=None, created_by=None):
        self.tournament_id = tournament_id
        self.name = name
        self.description = description
        self.tournament_type = tournament_type  # 'gold_cup', 'master_cup', 'grand_prix', 'challenge'
        self.start_date = start_date
        self.end_date = end_date
        self.max_participants = max_participants
        self.prize_type = prize_type  # 'points', 'badge', 'certificate', 'ranking'
        self.status = status  # 'upcoming', 'active', 'ended', 'cancelled'
        self.created_at = created_at
        self.created_by = created_by

    @staticmethod
    def create_table():
        """创建锦标赛表"""
        try:
            from app.utils.db import db_manager
            db_manager.execute('''
                CREATE TABLE IF NOT EXISTS tournaments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    tournament_type TEXT NOT NULL,
                    start_date TIMESTAMP,
                    end_date TIMESTAMP,
                    max_participants INTEGER DEFAULT 100,
                    prize_type TEXT,
                    status TEXT DEFAULT 'upcoming',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    FOREIGN KEY (created_by) REFERENCES users(id)
                )
            ''')
            logger.info("锦标赛表创建成功")
            return True
        except Exception as e:
            logger.error(f"创建锦标赛表失败: {str(e)}")
            return False

    @staticmethod
    def init_default_tournaments():
        """初始化默认锦标赛"""
        try:
            from app.utils.db import db_manager
            
            default_tournaments = [
                ('金牌杯数学挑战赛', '展现你的数学才华，争夺金牌荣誉！', 'gold_cup', 50, 'badge'),
                ('大师杯英语能力赛', '英语技能大考验，成为真正的语言大师！', 'master_cup', 100, 'certificate'),
                ('编程大奖赛', '代码的艺术，算法的挑战！', 'grand_prix', 80, 'points'),
                ('综合知识挑战赛', '全面知识大比拼！', 'challenge', 200, 'ranking'),
                ('日语能力挑战赛', '日语能力的终极考验！', 'gold_cup', 60, 'badge'),
                ('AI技能大师杯', '人工智能技能的巅峰对决！', 'master_cup', 40, 'certificate'),
            ]
            
            for name, desc, t_type, max_part, prize in default_tournaments:
                existing = db_manager.fetch_one(
                    'SELECT id FROM tournaments WHERE name = ?',
                    (name,)
                )
                if not existing:
                    db_manager.execute(
                        'INSERT INTO tournaments (name, description, tournament_type, max_participants, prize_type, status) VALUES (?, ?, ?, ?, ?, ?)',
                        (name, desc, t_type, max_part, prize, 'upcoming')
                    )
            logger.info("默认锦标赛初始化完成")
            return True
        except Exception as e:
            logger.error(f"初始化默认锦标赛失败: {str(e)}")
            return False

    def save(self):
        """保存锦标赛"""
        try:
            from app.utils.db import db_manager
            if self.tournament_id:
                db_manager.execute('''
                    UPDATE tournaments 
                    SET name=?, description=?, tournament_type=?, 
                        start_date=?, end_date=?, max_participants=?, 
                        prize_type=?, status=?
                    WHERE id=?
                ''', (self.name, self.description, self.tournament_type,
                      self.start_date, self.end_date, self.max_participants,
                      self.prize_type, self.status, self.tournament_id))
                logger.info(f"更新锦标赛: {self.name}")
            else:
                db_manager.execute('''
                    INSERT INTO tournaments 
                    (name, description, tournament_type, start_date, end_date, 
                     max_participants, prize_type, status, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (self.name, self.description, self.tournament_type,
                      self.start_date, self.end_date, self.max_participants,
                      self.prize_type, self.status, self.created_by))
                self.tournament_id = db_manager.lastrowid
                logger.info(f"创建锦标赛: {self.name}")
            return True
        except Exception as e:
            logger.error(f"保存锦标赛失败: {str(e)}")
            return False

    @staticmethod
    def get_all(status=None):
        """获取所有锦标赛"""
        try:
            from app.utils.db import db_manager
            query = 'SELECT * FROM tournaments'
            params = []
            if status:
                query += ' WHERE status = ?'
                params.append(status)
            query += ' ORDER BY created_at DESC'
            tournaments = db_manager.fetch_all(query, params)
            return tournaments
        except Exception as e:
            logger.error(f"获取锦标赛失败: {str(e)}")
            return []

    @staticmethod
    def get_by_id(tournament_id):
        """根据ID获取锦标赛"""
        try:
            from app.utils.db import db_manager
            result = db_manager.fetch_one(
                'SELECT * FROM tournaments WHERE id = ?',
                (tournament_id,)
            )
            return result
        except Exception as e:
            logger.error(f"获取锦标赛失败: {str(e)}")
            return None

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.tournament_id,
            'name': self.name,
            'description': self.description,
            'tournament_type': self.tournament_type,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'max_participants': self.max_participants,
            'prize_type': self.prize_type,
            'status': self.status,
            'created_at': self.created_at
        }


class TournamentParticipant:
    """锦标赛参赛者模型"""
    
    def __init__(self, participant_id=None, tournament_id=None, 
                 user_id=None, status=None, registered_at=None):
        self.participant_id = participant_id
        self.tournament_id = tournament_id
        self.user_id = user_id
        self.status = status  # 'registered', 'completed', 'withdrawn'
        self.registered_at = registered_at

    @staticmethod
    def create_table():
        """创建参赛者表"""
        try:
            from app.utils.db import db_manager
            db_manager.execute('''
                CREATE TABLE IF NOT EXISTS tournament_participants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tournament_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'registered',
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (tournament_id) REFERENCES tournaments(id),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE(tournament_id, user_id)
                )
            ''')
            logger.info("锦标赛参赛者表创建成功")
            return True
        except Exception as e:
            logger.error(f"创建参赛者表失败: {str(e)}")
            return False

    def save(self):
        """保存参赛者"""
        try:
            from app.utils.db import db_manager
            if self.participant_id:
                db_manager.execute('''
                    UPDATE tournament_participants 
                    SET status=? WHERE id=?
                ''', (self.status, self.participant_id))
            else:
                db_manager.execute('''
                    INSERT OR IGNORE INTO tournament_participants 
                    (tournament_id, user_id, status) VALUES (?, ?, ?)
                ''', (self.tournament_id, self.user_id, self.status))
                self.participant_id = db_manager.lastrowid
            return True
        except Exception as e:
            logger.error(f"保存参赛者失败: {str(e)}")
            return False

    @staticmethod
    def get_participants(tournament_id):
        """获取锦标赛参赛者"""
        try:
            from app.utils.db import db_manager
            participants = db_manager.fetch_all('''
                SELECT tp.*, u.username, u.email 
                FROM tournament_participants tp
                LEFT JOIN users u ON tp.user_id = u.id
                WHERE tp.tournament_id = ?
                ORDER BY tp.registered_at DESC
            ''', (tournament_id,))
            return participants
        except Exception as e:
            logger.error(f"获取参赛者失败: {str(e)}")
            return []

    @staticmethod
    def get_participant_count(tournament_id):
        """获取参赛者数量"""
        try:
            from app.utils.db import db_manager
            result = db_manager.fetch_one('''
                SELECT COUNT(*) as count FROM tournament_participants 
                WHERE tournament_id = ? AND status = 'registered'
            ''', (tournament_id,))
            return result['count'] if isinstance(result, dict) else (result[0] if result else 0)
        except Exception as e:
            logger.error(f"获取参赛者数量失败: {str(e)}")
            return 0


class TournamentRecord:
    """锦标赛记录模型"""
    
    def __init__(self, record_id=None, tournament_id=None, user_id=None,
                 score=None, rank=None, completed_at=None):
        self.record_id = record_id
        self.tournament_id = tournament_id
        self.user_id = user_id
        self.score = score
        self.rank = rank
        self.completed_at = completed_at

    @staticmethod
    def create_table():
        """创建锦标赛记录表"""
        try:
            from app.utils.db import db_manager
            db_manager.execute('''
                CREATE TABLE IF NOT EXISTS tournament_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tournament_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    score REAL,
                    rank INTEGER,
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (tournament_id) REFERENCES tournaments(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            logger.info("锦标赛记录表创建成功")
            return True
        except Exception as e:
            logger.error(f"创建锦标赛记录表失败: {str(e)}")
            return False

    def save(self):
        """保存记录"""
        try:
            from app.utils.db import db_manager
            if self.record_id:
                db_manager.execute('''
                    UPDATE tournament_records 
                    SET score=?, rank=? WHERE id=?
                ''', (self.score, self.rank, self.record_id))
            else:
                db_manager.execute('''
                    INSERT INTO tournament_records 
                    (tournament_id, user_id, score, rank) VALUES (?, ?, ?, ?)
                ''', (self.tournament_id, self.user_id, self.score, self.rank))
                self.record_id = db_manager.lastrowid
            return True
        except Exception as e:
            logger.error(f"保存记录失败: {str(e)}")
            return False

    @staticmethod
    def get_leaderboard(tournament_id, limit=10):
        """获取锦标赛排行榜"""
        try:
            from app.utils.db import db_manager
            leaderboard = db_manager.fetch_all('''
                SELECT tr.*, u.username, u.email 
                FROM tournament_records tr
                LEFT JOIN users u ON tr.user_id = u.id
                WHERE tr.tournament_id = ?
                ORDER BY tr.score DESC, tr.completed_at ASC
                LIMIT ?
            ''', (tournament_id, limit))
            return leaderboard
        except Exception as e:
            logger.error(f"获取排行榜失败: {str(e)}")
            return []


def init_tournament_system():
    """初始化锦标赛系统"""
    Tournament.create_table()
    TournamentParticipant.create_table()
    TournamentRecord.create_table()
    Tournament.init_default_tournaments()
    logger.info("锦标赛系统初始化完成")
    return True