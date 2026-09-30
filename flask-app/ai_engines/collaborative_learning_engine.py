# -*- coding: utf-8 -*-
"""
协作学习引擎
提供学习小组、同伴互助、知识分享、协作项目等功能
"""

import os
import sys
import json
import time
import sqlite3
import logging
import threading
from datetime import datetime
from typing import Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('collaborative_learning_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('CollaborativeLearningEngine')

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.db')


class CollaborativeLearningEngine:
    """协作学习引擎 - 管理学习小组和同伴互助"""

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
        logger.info("CollaborativeLearningEngine 初始化完成")

    def _init_database(self):
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS study_groups (
                        group_id TEXT PRIMARY KEY,
                        group_name TEXT NOT NULL,
                        subject TEXT,
                        grade TEXT,
                        description TEXT,
                        creator_id TEXT NOT NULL,
                        max_members INTEGER DEFAULT 10,
                        current_members INTEGER DEFAULT 1,
                        privacy TEXT DEFAULT 'public',
                        invite_code TEXT,
                        min_level INTEGER DEFAULT 1,
                        tags TEXT DEFAULT '[]',
                        status TEXT DEFAULT 'active',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS study_group_members (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        group_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        role TEXT DEFAULT 'member',
                        joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        contribution_score REAL DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        UNIQUE(group_id, user_id),
                        FOREIGN KEY (group_id) REFERENCES study_groups(group_id)
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge_shares (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        group_id TEXT,
                        title TEXT NOT NULL,
                        content TEXT,
                        share_type TEXT DEFAULT 'note',
                        subject TEXT,
                        knowledge_points TEXT DEFAULT '[]',
                        attachments TEXT DEFAULT '[]',
                        upvotes INTEGER DEFAULT 0,
                        downvotes INTEGER DEFAULT 0,
                        views INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'published',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS peer_help_requests (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        requester_id TEXT NOT NULL,
                        group_id TEXT,
                        title TEXT NOT NULL,
                        description TEXT,
                        subject TEXT,
                        difficulty INTEGER DEFAULT 3,
                        reward_points INTEGER DEFAULT 10,
                        helper_id TEXT,
                        status TEXT DEFAULT 'open',
                        resolved_at TEXT,
                        rating INTEGER,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS collaborative_projects (
                        project_id TEXT PRIMARY KEY,
                        project_name TEXT NOT NULL,
                        subject TEXT,
                        description TEXT,
                        creator_id TEXT NOT NULL,
                        group_id TEXT,
                        target_completion TEXT,
                        status TEXT DEFAULT 'planning',
                        max_participants INTEGER DEFAULT 5,
                        current_participants INTEGER DEFAULT 1,
                        progress REAL DEFAULT 0,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS project_participants (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        role TEXT DEFAULT 'member',
                        contribution REAL DEFAULT 0,
                        joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(project_id, user_id)
                    )
                ''')

                cursor.execute('CREATE INDEX IF NOT EXISTS idx_sg_creator ON study_groups(creator_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_sgm_user ON study_group_members(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_ks_user ON knowledge_shares(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_phr_requester ON peer_help_requests(requester_id)')

                conn.commit()
        except Exception as e:
            logger.error(f"初始化协作学习数据库失败: {e}")

    def create_group(self, creator_id: str, group_name: str, subject: str = None,
                     grade: str = None, description: str = None, max_members: int = 10,
                     privacy: str = 'public', min_level: int = 1,
                     tags: list = None) -> Dict[str, Any]:
        """创建学习小组"""
        with self._lock:
            try:
                group_id = f"group_{int(time.time())}_{creator_id}"
                invite_code = self._generate_invite_code() if privacy == 'private' else None

                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO study_groups
                        (group_id, group_name, subject, grade, description, creator_id,
                         max_members, privacy, invite_code, min_level, tags)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (group_id, group_name, subject, grade, description,
                          creator_id, max_members, privacy, invite_code, min_level,
                          json.dumps(tags or [], ensure_ascii=False)))

                    cursor.execute('''
                        INSERT INTO study_group_members
                        (group_id, user_id, role)
                        VALUES (?, ?, 'creator')
                    ''', (group_id, creator_id))

                    conn.commit()

                return {
                    'success': True,
                    'group_id': group_id,
                    'group_name': group_name,
                    'invite_code': invite_code,
                    'message': '学习小组创建成功'
                }
            except Exception as e:
                logger.error(f"创建学习小组失败: {e}")
                return {'success': False, 'error': str(e)}

    def _generate_invite_code(self) -> str:
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    def join_group(self, group_id: str, user_id: str,
                   invite_code: str = None) -> Dict[str, Any]:
        """加入学习小组"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()

                    cursor.execute('''
                        SELECT group_name, max_members, current_members, privacy,
                               invite_code, min_level, status
                        FROM study_groups WHERE group_id = ?
                    ''', (group_id,))
                    group = cursor.fetchone()
                    if not group:
                        return {'success': False, 'message': '小组不存在'}

                    group_name, max_m, curr_m, privacy, inv_code, _min_lvl, status = group

                    if status != 'active':
                        return {'success': False, 'message': '小组已关闭'}

                    if curr_m >= max_m:
                        return {'success': False, 'message': '小组已满员'}

                    if privacy == 'private' and invite_code != inv_code:
                        return {'success': False, 'message': '邀请码无效'}

                    cursor.execute('''
                        SELECT id FROM study_group_members
                        WHERE group_id = ? AND user_id = ?
                    ''', (group_id, user_id))
                    if cursor.fetchone():
                        return {'success': False, 'message': '已是小组成员'}

                    cursor.execute('''
                        INSERT INTO study_group_members
                        (group_id, user_id, role)
                        VALUES (?, ?, 'member')
                    ''', (group_id, user_id))

                    cursor.execute('''
                        UPDATE study_groups
                        SET current_members = current_members + 1,
                            updated_at = ?
                        WHERE group_id = ?
                    ''', (datetime.now().isoformat(), group_id))

                    conn.commit()

                return {
                    'success': True,
                    'group_id': group_id,
                    'group_name': group_name,
                    'message': f'成功加入「{group_name}」小组'
                }
            except Exception as e:
                logger.error(f"加入学习小组失败: {e}")
                return {'success': False, 'error': str(e)}

    def get_group_info(self, group_id: str) -> Dict[str, Any]:
        """获取小组信息"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT group_id, group_name, subject, grade, description,
                           creator_id, max_members, current_members, privacy,
                           min_level, tags, status, created_at
                    FROM study_groups WHERE group_id = ?
                ''', (group_id,))
                group = cursor.fetchone()
                if not group:
                    return {'success': False, 'message': '小组不存在'}

                cursor.execute('''
                    SELECT user_id, role, joined_at, contribution_score
                    FROM study_group_members
                    WHERE group_id = ? AND status = 'active'
                    ORDER BY contribution_score DESC
                ''', (group_id,))
                members = [{
                    'user_id': r[0],
                    'role': r[1],
                    'joined_at': r[2],
                    'contribution': r[3]
                } for r in cursor.fetchall()]

            return {
                'success': True,
                'group': {
                    'group_id': group[0],
                    'group_name': group[1],
                    'subject': group[2],
                    'grade': group[3],
                    'description': group[4],
                    'creator_id': group[5],
                    'max_members': group[6],
                    'current_members': group[7],
                    'privacy': group[8],
                    'min_level': group[9],
                    'tags': json.loads(group[10]) if group[10] else [],
                    'status': group[11],
                    'created_at': group[12]
                },
                'members': members,
                'member_count': len(members)
            }
        except Exception as e:
            logger.error(f"获取小组信息失败: {e}")
            return {'success': False, 'error': str(e)}

    def share_knowledge(self, user_id: str, title: str, content: str,
                        share_type: str = 'note', subject: str = None,
                        group_id: str = None, knowledge_points: list = None) -> Dict[str, Any]:
        """分享知识"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO knowledge_shares
                        (user_id, group_id, title, content, share_type, subject, knowledge_points)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (user_id, group_id, title, content, share_type, subject,
                          json.dumps(knowledge_points or [], ensure_ascii=False)))
                    share_id = cursor.lastrowid

                    if group_id:
                        cursor.execute('''
                            UPDATE study_group_members
                            SET contribution_score = contribution_score + 5
                            WHERE group_id = ? AND user_id = ?
                        ''', (group_id, user_id))

                    conn.commit()

                return {
                    'success': True,
                    'share_id': share_id,
                    'title': title,
                    'message': '知识分享已发布'
                }
            except Exception as e:
                logger.error(f"分享知识失败: {e}")
                return {'success': False, 'error': str(e)}

    def vote_share(self, share_id: int, user_id: str, vote_type: str = 'up') -> Dict[str, Any]:
        """点赞/踩知识分享（同一用户对同一分享只能投一次票）"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    # 创建投票记录表（若不存在）
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS share_votes (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            share_id INTEGER NOT NULL,
                            user_id TEXT NOT NULL,
                            vote_type TEXT NOT NULL,
                            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(share_id, user_id)
                        )
                    ''')
                    # 防重复投票
                    cursor.execute('''
                        SELECT vote_type FROM share_votes
                        WHERE share_id = ? AND user_id = ?
                    ''', (share_id, user_id))
                    existing = cursor.fetchone()
                    if existing:
                        return {
                            'success': False,
                            'message': f'您已投过票（{existing[0]}）',
                            'share_id': share_id
                        }

                    column = 'upvotes' if vote_type == 'up' else 'downvotes'
                    cursor.execute(f'''
                        UPDATE knowledge_shares SET {column} = {column} + 1 WHERE id = ?
                    ''', (share_id,))

                    cursor.execute('''
                        INSERT INTO share_votes (share_id, user_id, vote_type)
                        VALUES (?, ?, ?)
                    ''', (share_id, user_id, vote_type))

                    cursor.execute('''
                        SELECT user_id FROM knowledge_shares WHERE id = ?
                    ''', (share_id,))
                    author = cursor.fetchone()
                    if author and vote_type == 'up':
                        cursor.execute('''
                            UPDATE study_group_members
                            SET contribution_score = contribution_score + 1
                            WHERE user_id = ? AND group_id = (
                                SELECT group_id FROM knowledge_shares WHERE id = ?
                            )
                        ''', (author[0], share_id))

                    conn.commit()

                return {
                    'success': True,
                    'share_id': share_id,
                    'vote_type': vote_type,
                    'message': f'已{"点赞" if vote_type == "up" else "踩"}'
                }
            except Exception as e:
                logger.error(f"投票失败: {e}")
                return {'success': False, 'error': str(e)}

    def create_help_request(self, requester_id: str, title: str, description: str,
                            subject: str = None, difficulty: int = 3,
                            reward_points: int = 10, group_id: str = None) -> Dict[str, Any]:
        """创建同伴求助"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO peer_help_requests
                        (requester_id, group_id, title, description, subject,
                         difficulty, reward_points)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (requester_id, group_id, title, description, subject,
                          difficulty, reward_points))
                    request_id = cursor.lastrowid
                    conn.commit()

                return {
                    'success': True,
                    'request_id': request_id,
                    'title': title,
                    'reward_points': reward_points,
                    'message': '求助已发布，等待同学帮助'
                }
            except Exception as e:
                logger.error(f"创建同伴求助失败: {e}")
                return {'success': False, 'error': str(e)}

    def accept_help_request(self, request_id: int, helper_id: str) -> Dict[str, Any]:
        """接受同伴求助"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT status, requester_id FROM peer_help_requests WHERE id = ?
                    ''', (request_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'message': '求助不存在'}
                    if row[0] != 'open':
                        return {'success': False, 'message': '求助已被接受或关闭'}

                    if row[1] == helper_id:
                        return {'success': False, 'message': '不能帮助自己的求助'}

                    cursor.execute('''
                        UPDATE peer_help_requests
                        SET helper_id = ?, status = 'in_progress'
                        WHERE id = ?
                    ''', (helper_id, request_id))
                    conn.commit()

                return {
                    'success': True,
                    'request_id': request_id,
                    'helper_id': helper_id,
                    'message': '已接受求助，请尽快解答'
                }
            except Exception as e:
                logger.error(f"接受同伴求助失败: {e}")
                return {'success': False, 'error': str(e)}

    def resolve_help_request(self, request_id: int, rating: int = 5) -> Dict[str, Any]:
        """完成求助并评分"""
        with self._lock:
            try:
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT helper_id, reward_points, requester_id
                        FROM peer_help_requests WHERE id = ?
                    ''', (request_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'message': '求助不存在'}

                    helper_id, reward, _requester_id = row

                    cursor.execute('''
                        UPDATE peer_help_requests
                        SET status = 'resolved', resolved_at = ?, rating = ?
                        WHERE id = ?
                    ''', (datetime.now().isoformat(), rating, request_id))

                    if helper_id and reward > 0:
                        try:
                            from ai_engines.reward_achievement_engine import reward_achievement_engine
                            reward_achievement_engine.add_points(
                                helper_id, reward,
                                f'帮助同学解答问题（评分: {rating}星）',
                                'peer_help', str(request_id)
                            )
                        except Exception:
                            pass

                    conn.commit()

                return {
                    'success': True,
                    'request_id': request_id,
                    'rating': rating,
                    'reward_granted': reward,
                    'message': '求助已完成，奖励已发放'
                }
            except Exception as e:
                logger.error(f"完成求助失败: {e}")
                return {'success': False, 'error': str(e)}

    def get_open_help_requests(self, subject: str = None, group_id: str = None,
                                limit: int = 20) -> Dict[str, Any]:
        """获取开放的求助列表"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                sql = '''
                    SELECT id, requester_id, title, description, subject,
                           difficulty, reward_points, created_at
                    FROM peer_help_requests WHERE status = 'open'
                '''
                params = []
                if subject:
                    sql += ' AND subject = ?'
                    params.append(subject)
                if group_id:
                    sql += ' AND group_id = ?'
                    params.append(group_id)
                sql += ' ORDER BY reward_points DESC, created_at DESC LIMIT ?'
                params.append(limit)

                cursor.execute(sql, params)
                requests = [{
                    'request_id': r[0],
                    'requester_id': r[1],
                    'title': r[2],
                    'description': r[3],
                    'subject': r[4],
                    'difficulty': r[5],
                    'reward_points': r[6],
                    'created_at': r[7]
                } for r in cursor.fetchall()]

            return {
                'success': True,
                'requests': requests,
                'total': len(requests)
            }
        except Exception as e:
            logger.error(f"获取求助列表失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_knowledge_feed(self, subject: str = None, group_id: str = None,
                            limit: int = 20) -> Dict[str, Any]:
        """获取知识分享流"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                sql = '''
                    SELECT id, user_id, title, content, share_type, subject,
                           knowledge_points, upvotes, downvotes, views, created_at
                    FROM knowledge_shares WHERE status = 'published'
                '''
                params = []
                if subject:
                    sql += ' AND subject = ?'
                    params.append(subject)
                if group_id:
                    sql += ' AND group_id = ?'
                    params.append(group_id)
                sql += ' ORDER BY upvotes DESC, created_at DESC LIMIT ?'
                params.append(limit)

                cursor.execute(sql, params)
                shares = [{
                    'share_id': r[0],
                    'user_id': r[1],
                    'title': r[2],
                    'content': r[3][:200] if r[3] else '',
                    'type': r[4],
                    'subject': r[5],
                    'knowledge_points': json.loads(r[6]) if r[6] else [],
                    'upvotes': r[7],
                    'downvotes': r[8],
                    'views': r[9],
                    'created_at': r[10],
                    'score': r[7] - r[8]
                } for r in cursor.fetchall()]

            return {
                'success': True,
                'shares': shares,
                'total': len(shares)
            }
        except Exception as e:
            logger.error(f"获取知识分享流失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_user_groups(self, user_id: str) -> Dict[str, Any]:
        """获取用户加入的所有小组"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT sg.group_id, sg.group_name, sg.subject, sg.grade,
                           sg.current_members, sg.max_members, sgm.role,
                           sgm.contribution_score, sg.status
                    FROM study_group_members sgm
                    JOIN study_groups sg ON sgm.group_id = sg.group_id
                    WHERE sgm.user_id = ? AND sgm.status = 'active'
                    ORDER BY sgm.contribution_score DESC
                ''', (user_id,))
                groups = [{
                    'group_id': r[0],
                    'group_name': r[1],
                    'subject': r[2],
                    'grade': r[3],
                    'current_members': r[4],
                    'max_members': r[5],
                    'role': r[6],
                    'contribution': r[7],
                    'status': r[8]
                } for r in cursor.fetchall()]

            return {
                'success': True,
                'user_id': user_id,
                'groups': groups,
                'total': len(groups)
            }
        except Exception as e:
            logger.error(f"获取用户小组失败: {e}")
            return {'success': False, 'error': str(e)}

    def get_statistics(self) -> Dict[str, Any]:
        """获取协作学习统计"""
        try:
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM study_groups')
                total_groups = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM study_group_members')
                total_memberships = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM knowledge_shares')
                total_shares = cursor.fetchone()[0]
                cursor.execute('SELECT SUM(upvotes) FROM knowledge_shares')
                total_upvotes = cursor.fetchone()[0] or 0
                cursor.execute('SELECT COUNT(*) FROM peer_help_requests')
                total_requests = cursor.fetchone()[0]
                cursor.execute('SELECT status, COUNT(*) FROM peer_help_requests GROUP BY status')
                requests_by_status = dict(cursor.fetchall())
                cursor.execute('SELECT COUNT(*) FROM collaborative_projects')
                total_projects = cursor.fetchone()[0]
                cursor.execute('SELECT AVG(contribution_score) FROM study_group_members')
                avg_contribution = cursor.fetchone()[0] or 0

            return {
                'success': True,
                'total_groups': total_groups,
                'total_memberships': total_memberships,
                'total_shares': total_shares,
                'total_upvotes': total_upvotes,
                'total_help_requests': total_requests,
                'requests_by_status': requests_by_status,
                'total_projects': total_projects,
                'average_contribution': round(avg_contribution, 2)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}


collaborative_learning_engine = CollaborativeLearningEngine()
