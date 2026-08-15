#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育社交学习服务 (v15.24.0)
====================================
提供学习社区、学习小组、学习互动、知识分享、协作学习、同伴互助、社交评价和学习社交网络等综合服务。

核心能力：
1. 学习社区 - 社区创建、成员管理、社区活动、社区讨论
2. 学习小组 - 小组创建、成员管理、小组任务、小组讨论
3. 学习互动 - 讨论交流、问答互动、分享展示、协作创作
4. 知识分享 - 知识发布、资源分享、经验交流、成果展示、方法分享
5. 协作学习 - 项目协作、课题协作、作业协作、竞赛协作
6. 同伴互助 - 同伴辅导、同伴评价、同伴激励、同伴监督
7. 社交评价 - 评价管理、互评互教、反馈收集、综合评价
8. 学习网络 - 关系管理、知识图谱、社交图谱、推荐系统
9. 预警管理 - 学习预警、行为预警、成绩预警、干预措施
10. 统计分析 - 学习数据分析与报告
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_social_learning_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationSocialLearning')


# ========== 教育社交学习配置 ==========

COMMUNITY_TYPES = {
    'subject': {'name': '学科社区', 'description': '围绕特定学科建立的学习社区', 'k12': True, 'adult': True},
    'interest': {'name': '兴趣社区', 'description': '基于共同兴趣爱好的学习社区', 'k12': True, 'adult': True},
    'grade': {'name': '年级社区', 'description': '同年级学生组成的学习社区', 'k12': True, 'adult': False},
    'school': {'name': '学校社区', 'description': '同一学校师生组成的学习社区', 'k12': True, 'adult': True},
    'major': {'name': '专业社区', 'description': '同专业学生组成的学习社区', 'k12': False, 'adult': True},
    'career': {'name': '职业社区', 'description': '同职业从业者组成的学习社区', 'k12': False, 'adult': True},
    'region': {'name': '地区社区', 'description': '特定地区学习者组成的学习社区', 'k12': True, 'adult': True},
    'global': {'name': '全球社区', 'description': '跨地域的全球性学习社区', 'k12': True, 'adult': True}
}

GROUP_TYPES = {
    'study': {'name': '学习小组', 'description': '围绕课程学习组建的小组', 'k12': True, 'adult': True},
    'discussion': {'name': '讨论小组', 'description': '针对特定话题讨论的小组', 'k12': True, 'adult': True},
    'project': {'name': '项目小组', 'description': '共同完成项目的小组', 'k12': True, 'adult': True},
    'interest': {'name': '兴趣小组', 'description': '基于兴趣爱好的小组', 'k12': True, 'adult': True},
    'competition': {'name': '竞赛小组', 'description': '准备各类竞赛的小组', 'k12': True, 'adult': True},
    'research': {'name': '研究小组', 'description': '开展研究性学习的小组', 'k12': True, 'adult': True},
    'practice': {'name': '实践小组', 'description': '进行实践活动的小组', 'k12': True, 'adult': True},
    'mutual': {'name': '互助小组', 'description': '同伴互助学习的小组', 'k12': True, 'adult': True}
}

INTERACTION_TYPES = {
    'discussion': {'name': '讨论交流', 'description': '主题讨论与观点交流', 'k12': True, 'adult': True},
    'qa': {'name': '问答互动', 'description': '提问与回答互动', 'k12': True, 'adult': True},
    'sharing': {'name': '分享展示', 'description': '学习成果分享与展示', 'k12': True, 'adult': True},
    'collaboration': {'name': '协作创作', 'description': '共同创作与协作', 'k12': True, 'adult': True},
    'peer_review': {'name': '互评互教', 'description': '同伴之间相互评价与教学', 'k12': True, 'adult': True},
    'feedback': {'name': '同伴反馈', 'description': '同伴之间的学习反馈', 'k12': True, 'adult': True},
    'online': {'name': '在线讨论', 'description': '线上实时讨论活动', 'k12': True, 'adult': True},
    'offline': {'name': '线下活动', 'description': '线下学习交流活动', 'k12': True, 'adult': True}
}

SHARING_TYPES = {
    'knowledge': {'name': '知识分享', 'description': '专业知识与理论分享', 'k12': True, 'adult': True},
    'experience': {'name': '经验分享', 'description': '学习经验与心得分享', 'k12': True, 'adult': True},
    'resource': {'name': '资源分享', 'description': '学习资料与资源分享', 'k12': True, 'adult': True},
    'achievement': {'name': '成果分享', 'description': '学习成果与作品分享', 'k12': True, 'adult': True},
    'method': {'name': '方法分享', 'description': '学习方法与技巧分享', 'k12': True, 'adult': True},
    'insight': {'name': '心得分享', 'description': '学习心得与感悟分享', 'k12': True, 'adult': True},
    'case': {'name': '案例分享', 'description': '教学案例与实践案例分享', 'k12': True, 'adult': True},
    'tool': {'name': '工具分享', 'description': '学习工具与软件分享', 'k12': True, 'adult': True}
}

COLLABORATION_TYPES = {
    'project': {'name': '项目协作', 'description': '共同完成学习项目', 'k12': True, 'adult': True},
    'topic': {'name': '课题协作', 'description': '合作开展课题研究', 'k12': True, 'adult': True},
    'assignment': {'name': '作业协作', 'description': '小组作业协作完成', 'k12': True, 'adult': True},
    'competition': {'name': '竞赛协作', 'description': '共同准备各类竞赛', 'k12': True, 'adult': True},
    'research': {'name': '研究协作', 'description': '合作进行学术研究', 'k12': False, 'adult': True},
    'creation': {'name': '创作协作', 'description': '共同创作学习作品', 'k12': True, 'adult': True},
    'practice': {'name': '实践协作', 'description': '合作开展实践活动', 'k12': True, 'adult': True},
    'team': {'name': '团队协作', 'description': '团队形式的协作学习', 'k12': True, 'adult': True}
}

PEER_SUPPORT_TYPES = {
    'tutoring': {'name': '同伴辅导', 'description': '优秀学生辅导学习困难同学', 'k12': True, 'adult': True},
    'evaluation': {'name': '同伴评价', 'description': '同伴之间相互评价', 'k12': True, 'adult': True},
    'motivation': {'name': '同伴激励', 'description': '同伴之间相互鼓励', 'k12': True, 'adult': True},
    'supervision': {'name': '同伴监督', 'description': '同伴之间相互监督学习', 'k12': True, 'adult': True},
    'learning': {'name': '同伴学习', 'description': '同伴之间相互学习', 'k12': True, 'adult': True},
    'discussion': {'name': '同伴讨论', 'description': '同伴之间深入讨论', 'k12': True, 'adult': True},
    'sharing': {'name': '同伴分享', 'description': '同伴之间分享学习资源', 'k12': True, 'adult': True},
    'feedback': {'name': '同伴反馈', 'description': '同伴之间提供学习反馈', 'k12': True, 'adult': True}
}

EVALUATION_TYPES = {
    'peer': {'name': '同伴评价', 'description': '来自同伴的评价', 'k12': True, 'adult': True},
    'self': {'name': '自我评价', 'description': '学习者自我评估', 'k12': True, 'adult': True},
    'teacher': {'name': '教师评价', 'description': '来自教师的评价', 'k12': True, 'adult': True},
    'expert': {'name': '专家评价', 'description': '来自领域专家的评价', 'k12': False, 'adult': True},
    'community': {'name': '社区评价', 'description': '来自学习社区的评价', 'k12': True, 'adult': True},
    'anonymous': {'name': '匿名评价', 'description': '匿名方式的评价', 'k12': True, 'adult': True},
    'public': {'name': '公开评价', 'description': '公开可见的评价', 'k12': True, 'adult': True},
    'comprehensive': {'name': '综合评价', 'description': '多维度综合评价', 'k12': True, 'adult': True}
}

NETWORK_TYPES = {
    'learning': {'name': '学习关系网', 'description': '基于学习互动形成的关系网络', 'k12': True, 'adult': True},
    'knowledge': {'name': '知识图谱', 'description': '知识节点与关联关系图谱', 'k12': True, 'adult': True},
    'social': {'name': '社交图谱', 'description': '学习者社交关系图谱', 'k12': True, 'adult': True},
    'interest': {'name': '兴趣图谱', 'description': '基于兴趣爱好的图谱', 'k12': True, 'adult': True},
    'collaboration': {'name': '协作网络', 'description': '协作学习形成的网络', 'k12': True, 'adult': True},
    'mentor': {'name': '导师网络', 'description': '导师与学员关系网络', 'k12': True, 'adult': True},
    'alumni': {'name': '校友网络', 'description': '校友之间的联系网络', 'k12': False, 'adult': True},
    'career': {'name': '职业网络', 'description': '职业发展相关的网络', 'k12': False, 'adult': True}
}


class EducationSocialLearningService:
    """教育社交学习服务"""

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
                    CREATE TABLE IF NOT EXISTS learning_communities (
                        community_id TEXT PRIMARY KEY,
                        community_name TEXT NOT NULL,
                        community_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        description TEXT,
                        owner_id INTEGER,
                        owner_name TEXT,
                        member_count INTEGER DEFAULT 1,
                        topic_count INTEGER DEFAULT 0,
                        post_count INTEGER DEFAULT 0,
                        is_active INTEGER DEFAULT 1,
                        cover_image TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS community_members (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        community_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        role TEXT DEFAULT 'member',
                        join_date TEXT,
                        last_active_date TEXT,
                        contribution_score INTEGER DEFAULT 0,
                        UNIQUE(community_id, user_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_groups (
                        group_id TEXT PRIMARY KEY,
                        group_name TEXT NOT NULL,
                        group_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        description TEXT,
                        leader_id INTEGER,
                        leader_name TEXT,
                        member_count INTEGER DEFAULT 1,
                        task_count INTEGER DEFAULT 0,
                        discussion_count INTEGER DEFAULT 0,
                        max_members INTEGER DEFAULT 20,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS group_members (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        group_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        role TEXT DEFAULT 'member',
                        join_date TEXT,
                        contribution_score INTEGER DEFAULT 0,
                        UNIQUE(group_id, user_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_interactions (
                        interaction_id TEXT PRIMARY KEY,
                        interaction_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        title TEXT,
                        description TEXT,
                        initiator_id INTEGER,
                        initiator_name TEXT,
                        community_id TEXT,
                        group_id TEXT,
                        participant_count INTEGER DEFAULT 0,
                        comment_count INTEGER DEFAULT 0,
                        like_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS interaction_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        interaction_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        action_type TEXT,
                        content TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge_sharing (
                        sharing_id TEXT PRIMARY KEY,
                        sharing_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        content TEXT,
                        author_id INTEGER,
                        author_name TEXT,
                        community_id TEXT,
                        group_id TEXT,
                        tags TEXT,
                        view_count INTEGER DEFAULT 0,
                        download_count INTEGER DEFAULT 0,
                        like_count INTEGER DEFAULT 0,
                        comment_count INTEGER DEFAULT 0,
                        file_url TEXT,
                        status TEXT DEFAULT 'published',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sharing_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sharing_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        action_type TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS collaborative_learning (
                        collaboration_id TEXT PRIMARY KEY,
                        collaboration_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        leader_id INTEGER,
                        leader_name TEXT,
                        group_id TEXT,
                        progress INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        start_date TEXT,
                        end_date TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS collaboration_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        collaboration_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        role TEXT,
                        contribution TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS peer_support (
                        support_id TEXT PRIMARY KEY,
                        support_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        title TEXT,
                        description TEXT,
                        requester_id INTEGER,
                        requester_name TEXT,
                        supporter_id INTEGER,
                        supporter_name TEXT,
                        community_id TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS support_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        support_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        action_type TEXT,
                        content TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS social_evaluation (
                        evaluation_id TEXT PRIMARY KEY,
                        evaluation_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        target_id INTEGER,
                        target_name TEXT,
                        evaluator_id INTEGER,
                        evaluator_name TEXT,
                        score REAL,
                        comment TEXT,
                        is_anonymous INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'completed',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS evaluation_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        evaluation_id TEXT NOT NULL,
                        dimension TEXT,
                        score REAL,
                        weight REAL,
                        feedback TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_network (
                        network_id TEXT PRIMARY KEY,
                        network_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        name TEXT,
                        description TEXT,
                        node_count INTEGER DEFAULT 0,
                        edge_count INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS network_relations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        network_id TEXT NOT NULL,
                        source_id INTEGER NOT NULL,
                        target_id INTEGER NOT NULL,
                        relation_type TEXT,
                        weight REAL DEFAULT 1.0,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS social_alerts (
                        alert_id TEXT PRIMARY KEY,
                        alert_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        title TEXT,
                        description TEXT,
                        target_user_id INTEGER,
                        trigger_condition TEXT,
                        severity TEXT DEFAULT 'medium',
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alert_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        alert_id TEXT NOT NULL,
                        user_id INTEGER,
                        message TEXT,
                        status TEXT DEFAULT 'sent',
                        sent_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('教育社交学习服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 学习社区 ==========

    def create_community(self, community_name: str, community_type: str,
                          education_type: str, owner_id: int,
                          owner_name: str, **kwargs) -> Dict[str, Any]:
        try:
            config = COMMUNITY_TYPES.get(community_type)
            if not config:
                return {'success': False, 'error': '无效的社区类型'}
            if education_type == 'k12' and not config.get('k12', False):
                return {'success': False, 'error': '该社区类型不适用于K12教育'}
            if education_type == 'adult' and not config.get('adult', False):
                return {'success': False, 'error': '该社区类型不适用于成人教育'}
            community_id = f"com_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO learning_communities (
                            community_id, community_name, community_type,
                            education_type, description, owner_id, owner_name,
                            member_count, topic_count, post_count, is_active,
                            cover_image, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, 0, 0, 1, ?, ?, ?)
                    ''', (community_id, community_name, community_type,
                          education_type, kwargs.get('description'),
                          owner_id, owner_name, kwargs.get('cover_image'),
                          now, now))
                    cursor.execute('''
                        INSERT INTO community_members (
                            community_id, user_id, user_name, role, join_date,
                            last_active_date, contribution_score
                        ) VALUES (?, ?, ?, 'owner', ?, ?, 0)
                    ''', (community_id, owner_id, owner_name, now[:10], now[:10]))
                    conn.commit()
                    logger.info(f'创建学习社区: {community_name} ({community_id})')
                    return {'success': True, 'community_id': community_id}
        except Exception as e:
            logger.error(f'创建学习社区失败: {e}')
            return {'success': False, 'error': str(e)}

    def join_community(self, community_id: str, user_id: int,
                        user_name: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT is_active FROM learning_communities WHERE community_id = ?', (community_id,))
                    community = cursor.fetchone()
                    if not community:
                        return {'success': False, 'error': '社区不存在'}
                    if community[0] != 1:
                        return {'success': False, 'error': '社区已关闭'}
                    cursor.execute('''
                        INSERT OR IGNORE INTO community_members (
                            community_id, user_id, user_name, role, join_date,
                            last_active_date, contribution_score
                        ) VALUES (?, ?, ?, 'member', ?, ?, 0)
                    ''', (community_id, user_id, user_name, now[:10], now[:10]))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE learning_communities SET member_count = member_count + 1, updated_at = ? WHERE community_id = ?', (now, community_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已加入该社区'}
        except Exception as e:
            logger.error(f'加入学习社区失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_community_topic(self, community_id: str, title: str,
                                content: str, user_id: int,
                                user_name: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT is_active FROM learning_communities WHERE community_id = ?', (community_id,))
                    community = cursor.fetchone()
                    if not community:
                        return {'success': False, 'error': '社区不存在'}
                    cursor.execute('UPDATE learning_communities SET topic_count = topic_count + 1, post_count = post_count + 1, updated_at = ? WHERE community_id = ?', (now, community_id))
                    cursor.execute('UPDATE community_members SET contribution_score = contribution_score + 1, last_active_date = ? WHERE community_id = ? AND user_id = ?', (now[:10], community_id, user_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'创建社区话题失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_communities(self, education_type: str = None,
                          community_type: str = None, page: int = 1,
                          page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM learning_communities WHERE is_active = 1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if community_type:
                    query += ' AND community_type = ?'
                    params.append(community_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY member_count DESC, created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                communities = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'communities': communities, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取社区列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 学习小组 ==========

    def create_group(self, group_name: str, group_type: str,
                      education_type: str, leader_id: int,
                      leader_name: str, **kwargs) -> Dict[str, Any]:
        try:
            config = GROUP_TYPES.get(group_type)
            if not config:
                return {'success': False, 'error': '无效的小组类型'}
            if education_type == 'k12' and not config.get('k12', False):
                return {'success': False, 'error': '该小组类型不适用于K12教育'}
            if education_type == 'adult' and not config.get('adult', False):
                return {'success': False, 'error': '该小组类型不适用于成人教育'}
            group_id = f"grp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO learning_groups (
                            group_id, group_name, group_type, education_type,
                            description, leader_id, leader_name, member_count,
                            task_count, discussion_count, max_members, is_active,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, 0, 0, ?, 1, ?, ?)
                    ''', (group_id, group_name, group_type, education_type,
                          kwargs.get('description'), leader_id, leader_name,
                          kwargs.get('max_members', 20), now, now))
                    cursor.execute('''
                        INSERT INTO group_members (
                            group_id, user_id, user_name, role, join_date,
                            contribution_score
                        ) VALUES (?, ?, ?, 'leader', ?, 0)
                    ''', (group_id, leader_id, leader_name, now[:10]))
                    conn.commit()
                    logger.info(f'创建学习小组: {group_name} ({group_id})')
                    return {'success': True, 'group_id': group_id}
        except Exception as e:
            logger.error(f'创建学习小组失败: {e}')
            return {'success': False, 'error': str(e)}

    def join_group(self, group_id: str, user_id: int, user_name: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT is_active, max_members, member_count FROM learning_groups WHERE group_id = ?', (group_id,))
                    group = cursor.fetchone()
                    if not group:
                        return {'success': False, 'error': '小组不存在'}
                    if group[0] != 1:
                        return {'success': False, 'error': '小组已关闭'}
                    if group[1] and group[2] >= group[1]:
                        return {'success': False, 'error': '小组名额已满'}
                    cursor.execute('''
                        INSERT OR IGNORE INTO group_members (
                            group_id, user_id, user_name, role, join_date,
                            contribution_score
                        ) VALUES (?, ?, ?, 'member', ?, 0)
                    ''', (group_id, user_id, user_name, now[:10]))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE learning_groups SET member_count = member_count + 1, updated_at = ? WHERE group_id = ?', (now, group_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已加入该小组'}
        except Exception as e:
            logger.error(f'加入学习小组失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_group_task(self, group_id: str, title: str, description: str,
                          user_id: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT is_active FROM learning_groups WHERE group_id = ?', (group_id,))
                    group = cursor.fetchone()
                    if not group:
                        return {'success': False, 'error': '小组不存在'}
                    cursor.execute('UPDATE learning_groups SET task_count = task_count + 1, updated_at = ? WHERE group_id = ?', (now, group_id))
                    cursor.execute('UPDATE group_members SET contribution_score = contribution_score + 1 WHERE group_id = ? AND user_id = ?', (group_id, user_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'创建小组任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_groups(self, education_type: str = None, group_type: str = None,
                     page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM learning_groups WHERE is_active = 1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if group_type:
                    query += ' AND group_type = ?'
                    params.append(group_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY member_count DESC, created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                groups = [dict(g) for g in cursor.fetchall()]
                return {'success': True, 'groups': groups, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取小组列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 学习互动 ==========

    def create_interaction(self, interaction_type: str, education_type: str,
                            title: str, initiator_id: int,
                            initiator_name: str, **kwargs) -> Dict[str, Any]:
        try:
            config = INTERACTION_TYPES.get(interaction_type)
            if not config:
                return {'success': False, 'error': '无效的互动类型'}
            if education_type == 'k12' and not config.get('k12', False):
                return {'success': False, 'error': '该互动类型不适用于K12教育'}
            if education_type == 'adult' and not config.get('adult', False):
                return {'success': False, 'error': '该互动类型不适用于成人教育'}
            interaction_id = f"int_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO learning_interactions (
                            interaction_id, interaction_type, education_type,
                            title, description, initiator_id, initiator_name,
                            community_id, group_id, participant_count,
                            comment_count, like_count, status, created_at,
                            updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0, 0, 'active', ?, ?)
                    ''', (interaction_id, interaction_type, education_type,
                          title, kwargs.get('description'), initiator_id,
                          initiator_name, kwargs.get('community_id'),
                          kwargs.get('group_id'), now, now))
                    cursor.execute('''
                        INSERT INTO interaction_records (
                            interaction_id, user_id, user_name, action_type,
                            content, created_at
                        ) VALUES (?, ?, ?, 'initiate', ?, ?)
                    ''', (interaction_id, initiator_id, initiator_name, title, now))
                    conn.commit()
                    logger.info(f'创建学习互动: {title} ({interaction_id})')
                    return {'success': True, 'interaction_id': interaction_id}
        except Exception as e:
            logger.error(f'创建学习互动失败: {e}')
            return {'success': False, 'error': str(e)}

    def participate_interaction(self, interaction_id: str, user_id: int,
                                 user_name: str, content: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM learning_interactions WHERE interaction_id = ?', (interaction_id,))
                    interaction = cursor.fetchone()
                    if not interaction:
                        return {'success': False, 'error': '互动不存在'}
                    if interaction[0] != 'active':
                        return {'success': False, 'error': '互动已结束'}
                    cursor.execute('UPDATE learning_interactions SET participant_count = participant_count + 1, updated_at = ? WHERE interaction_id = ?', (now, interaction_id))
                    cursor.execute('''
                        INSERT INTO interaction_records (
                            interaction_id, user_id, user_name, action_type,
                            content, created_at
                        ) VALUES (?, ?, ?, 'participate', ?, ?)
                    ''', (interaction_id, user_id, user_name, content or '', now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'参与学习互动失败: {e}')
            return {'success': False, 'error': str(e)}

    def comment_interaction(self, interaction_id: str, user_id: int,
                             user_name: str, content: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE learning_interactions SET comment_count = comment_count + 1, updated_at = ? WHERE interaction_id = ?', (now, interaction_id))
                    cursor.execute('''
                        INSERT INTO interaction_records (
                            interaction_id, user_id, user_name, action_type,
                            content, created_at
                        ) VALUES (?, ?, ?, 'comment', ?, ?)
                    ''', (interaction_id, user_id, user_name, content, now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'评论互动失败: {e}')
            return {'success': False, 'error': str(e)}

    def like_interaction(self, interaction_id: str, user_id: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE learning_interactions SET like_count = like_count + 1, updated_at = ? WHERE interaction_id = ?', (now, interaction_id))
                    cursor.execute('''
                        INSERT INTO interaction_records (
                            interaction_id, user_id, user_name, action_type,
                            content, created_at
                        ) VALUES (?, ?, ?, 'like', '', ?)
                    ''', (interaction_id, user_id, '', now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'点赞互动失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 知识分享 ==========

    def publish_knowledge(self, sharing_type: str, education_type: str,
                           title: str, content: str, author_id: int,
                           author_name: str, **kwargs) -> Dict[str, Any]:
        try:
            config = SHARING_TYPES.get(sharing_type)
            if not config:
                return {'success': False, 'error': '无效的分享类型'}
            if education_type == 'k12' and not config.get('k12', False):
                return {'success': False, 'error': '该分享类型不适用于K12教育'}
            if education_type == 'adult' and not config.get('adult', False):
                return {'success': False, 'error': '该分享类型不适用于成人教育'}
            sharing_id = f"sha_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO knowledge_sharing (
                            sharing_id, sharing_type, education_type, title,
                            content, author_id, author_name, community_id,
                            group_id, tags, view_count, download_count,
                            like_count, comment_count, file_url, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, 0, ?, 'published', ?, ?)
                    ''', (sharing_id, sharing_type, education_type, title,
                          content, author_id, author_name,
                          kwargs.get('community_id'), kwargs.get('group_id'),
                          kwargs.get('tags'), kwargs.get('file_url'), now, now))
                    conn.commit()
                    logger.info(f'发布知识分享: {title} ({sharing_id})')
                    return {'success': True, 'sharing_id': sharing_id}
        except Exception as e:
            logger.error(f'发布知识分享失败: {e}')
            return {'success': False, 'error': str(e)}

    def view_knowledge(self, sharing_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE knowledge_sharing SET view_count = view_count + 1, updated_at = ? WHERE sharing_id = ?', (now, sharing_id))
                conn.commit()
                return {'success': True}
        except Exception as e:
            logger.error(f'记录知识浏览失败: {e}')
            return {'success': False, 'error': str(e)}

    def download_knowledge(self, sharing_id: str, user_id: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE knowledge_sharing SET download_count = download_count + 1, updated_at = ? WHERE sharing_id = ?', (now, sharing_id))
                    cursor.execute('INSERT INTO sharing_records (sharing_id, user_id, user_name, action_type, created_at) VALUES (?, ?, ?, \'download\', ?)',
                                 (sharing_id, user_id, '', now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'下载知识资源失败: {e}')
            return {'success': False, 'error': str(e)}

    def like_knowledge(self, sharing_id: str, user_id: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE knowledge_sharing SET like_count = like_count + 1, updated_at = ? WHERE sharing_id = ?', (now, sharing_id))
                    cursor.execute('INSERT INTO sharing_records (sharing_id, user_id, user_name, action_type, created_at) VALUES (?, ?, ?, \'like\', ?)',
                                 (sharing_id, user_id, '', now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'点赞知识分享失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_knowledge(self, sharing_type: str = None, education_type: str = None,
                        page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM knowledge_sharing WHERE status = ?'
                params = ['published']
                if sharing_type:
                    query += ' AND sharing_type = ?'
                    params.append(sharing_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY view_count DESC, created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(i) for i in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取知识分享列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 协作学习 ==========

    def create_collaboration(self, collaboration_type: str, education_type: str,
                              title: str, leader_id: int, leader_name: str,
                              **kwargs) -> Dict[str, Any]:
        try:
            config = COLLABORATION_TYPES.get(collaboration_type)
            if not config:
                return {'success': False, 'error': '无效的协作类型'}
            if education_type == 'k12' and not config.get('k12', False):
                return {'success': False, 'error': '该协作类型不适用于K12教育'}
            if education_type == 'adult' and not config.get('adult', False):
                return {'success': False, 'error': '该协作类型不适用于成人教育'}
            collaboration_id = f"col_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO collaborative_learning (
                            collaboration_id, collaboration_type, education_type,
                            title, description, leader_id, leader_name,
                            group_id, progress, status, start_date, end_date,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 'active', ?, ?, ?, ?)
                    ''', (collaboration_id, collaboration_type, education_type,
                          title, kwargs.get('description'), leader_id,
                          leader_name, kwargs.get('group_id'),
                          kwargs.get('start_date', now[:10]),
                          kwargs.get('end_date'), now, now))
                    cursor.execute('''
                        INSERT INTO collaboration_records (
                            collaboration_id, user_id, user_name, role,
                            contribution, created_at
                        ) VALUES (?, ?, ?, 'leader', ?, ?)
                    ''', (collaboration_id, leader_id, leader_name, '', now))
                    conn.commit()
                    logger.info(f'创建协作学习: {title} ({collaboration_id})')
                    return {'success': True, 'collaboration_id': collaboration_id}
        except Exception as e:
            logger.error(f'创建协作学习失败: {e}')
            return {'success': False, 'error': str(e)}

    def join_collaboration(self, collaboration_id: str, user_id: int,
                            user_name: str, role: str = 'member') -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM collaborative_learning WHERE collaboration_id = ?', (collaboration_id,))
                    collab = cursor.fetchone()
                    if not collab:
                        return {'success': False, 'error': '协作项目不存在'}
                    if collab[0] != 'active':
                        return {'success': False, 'error': '协作项目已结束'}
                    cursor.execute('''
                        INSERT OR IGNORE INTO collaboration_records (
                            collaboration_id, user_id, user_name, role,
                            contribution, created_at
                        ) VALUES (?, ?, ?, ?, '', ?)
                    ''', (collaboration_id, user_id, user_name, role, now))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已加入该协作项目'}
        except Exception as e:
            logger.error(f'加入协作学习失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_collaboration_progress(self, collaboration_id: str,
                                       progress: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    status = 'completed' if progress >= 100 else 'active'
                    cursor.execute('UPDATE collaborative_learning SET progress = ?, status = ?, updated_at = ? WHERE collaboration_id = ?',
                                 (progress, status, now, collaboration_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '协作项目不存在'}
        except Exception as e:
            logger.error(f'更新协作进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_collaboration_contribution(self, collaboration_id: str,
                                          user_id: int, contribution: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE collaboration_records SET contribution = ? WHERE collaboration_id = ? AND user_id = ?',
                                 (contribution, collaboration_id, user_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '协作记录不存在'}
        except Exception as e:
            logger.error(f'记录协作贡献失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 同伴互助 ==========

    def request_peer_support(self, support_type: str, education_type: str,
                              title: str, description: str, requester_id: int,
                              requester_name: str, **kwargs) -> Dict[str, Any]:
        try:
            config = PEER_SUPPORT_TYPES.get(support_type)
            if not config:
                return {'success': False, 'error': '无效的互助类型'}
            if education_type == 'k12' and not config.get('k12', False):
                return {'success': False, 'error': '该互助类型不适用于K12教育'}
            if education_type == 'adult' and not config.get('adult', False):
                return {'success': False, 'error': '该互助类型不适用于成人教育'}
            support_id = f"sup_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO peer_support (
                            support_id, support_type, education_type, title,
                            description, requester_id, requester_name,
                            supporter_id, supporter_name, community_id,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, 'pending', ?, ?)
                    ''', (support_id, support_type, education_type, title,
                          description, requester_id, requester_name,
                          kwargs.get('community_id'), now, now))
                    conn.commit()
                    logger.info(f'发起同伴互助请求: {title} ({support_id})')
                    return {'success': True, 'support_id': support_id}
        except Exception as e:
            logger.error(f'发起同伴互助请求失败: {e}')
            return {'success': False, 'error': str(e)}

    def accept_peer_support(self, support_id: str, supporter_id: int,
                             supporter_name: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE peer_support SET supporter_id = ?, supporter_name = ?, status = ?, updated_at = ? WHERE support_id = ? AND status = ?',
                                 (supporter_id, supporter_name, 'accepted', now, support_id, 'pending'))
                    if cursor.rowcount > 0:
                        cursor.execute('INSERT INTO support_records (support_id, user_id, user_name, action_type, content, created_at) VALUES (?, ?, ?, \'accept\', \'\', ?)',
                                     (support_id, supporter_id, supporter_name, now))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '互助请求状态不允许'}
        except Exception as e:
            logger.error(f'接受同伴互助请求失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_peer_support(self, support_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE peer_support SET status = ?, updated_at = ? WHERE support_id = ? AND status = ?',
                                 ('completed', now, support_id, 'accepted'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '互助请求状态不允许'}
        except Exception as e:
            logger.error(f'完成同伴互助失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_peer_support(self, support_type: str = None, education_type: str = None,
                           status: str = 'pending', page: int = 1,
                           page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM peer_support WHERE 1=1'
                params = []
                if support_type:
                    query += ' AND support_type = ?'
                    params.append(support_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(i) for i in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取同伴互助列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 社交评价 ==========

    def create_evaluation(self, evaluation_type: str, education_type: str,
                           target_id: int, target_name: str, evaluator_id: int,
                           evaluator_name: str, score: float, **kwargs) -> Dict[str, Any]:
        try:
            config = EVALUATION_TYPES.get(evaluation_type)
            if not config:
                return {'success': False, 'error': '无效的评价类型'}
            if education_type == 'k12' and not config.get('k12', False):
                return {'success': False, 'error': '该评价类型不适用于K12教育'}
            if education_type == 'adult' and not config.get('adult', False):
                return {'success': False, 'error': '该评价类型不适用于成人教育'}
            evaluation_id = f"eva_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO social_evaluation (
                            evaluation_id, evaluation_type, education_type,
                            target_id, target_name, evaluator_id,
                            evaluator_name, score, comment, is_anonymous,
                            status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'completed', ?)
                    ''', (evaluation_id, evaluation_type, education_type,
                          target_id, target_name, evaluator_id,
                          evaluator_name, score, kwargs.get('comment', ''),
                          1 if kwargs.get('is_anonymous', False) else 0, now))
                    dimensions = kwargs.get('dimensions', [])
                    for dim in dimensions:
                        cursor.execute('INSERT INTO evaluation_results (evaluation_id, dimension, score, weight, feedback) VALUES (?, ?, ?, ?, ?)',
                                     (evaluation_id, dim.get('dimension'), dim.get('score'), dim.get('weight', 1.0), dim.get('feedback', '')))
                    conn.commit()
                    logger.info(f'创建社交评价: {evaluation_id}')
                    return {'success': True, 'evaluation_id': evaluation_id}
        except Exception as e:
            logger.error(f'创建社交评价失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_evaluations_by_target(self, target_id: int, education_type: str = None,
                                   page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM social_evaluation WHERE target_id = ?'
                params = [target_id]
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                evaluations = [dict(e) for e in cursor.fetchall()]
                return {'success': True, 'evaluations': evaluations, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取目标评价列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_evaluation_results(self, evaluation_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM social_evaluation WHERE evaluation_id = ?', (evaluation_id,))
                evaluation = cursor.fetchone()
                if not evaluation:
                    return {'success': False, 'error': '评价不存在'}
                cursor.execute('SELECT * FROM evaluation_results WHERE evaluation_id = ?', (evaluation_id,))
                results = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'evaluation': dict(evaluation), 'results': results}
        except Exception as e:
            logger.error(f'获取评价结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def calculate_comprehensive_score(self, target_id: int, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = 'SELECT AVG(score) as avg_score, COUNT(*) as eval_count FROM social_evaluation WHERE target_id = ?'
                params = [target_id]
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                result = cursor.fetchone()
                avg_score = round(result[0], 2) if result[0] else 0
                eval_count = result[1] or 0
                return {'success': True, 'average_score': avg_score, 'evaluation_count': eval_count}
        except Exception as e:
            logger.error(f'计算综合评分失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 学习网络 ==========

    def create_network(self, network_type: str, education_type: str,
                       name: str, **kwargs) -> Dict[str, Any]:
        try:
            config = NETWORK_TYPES.get(network_type)
            if not config:
                return {'success': False, 'error': '无效的网络类型'}
            if education_type == 'k12' and not config.get('k12', False):
                return {'success': False, 'error': '该网络类型不适用于K12教育'}
            if education_type == 'adult' and not config.get('adult', False):
                return {'success': False, 'error': '该网络类型不适用于成人教育'}
            network_id = f"net_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO learning_network (
                            network_id, network_type, education_type, name,
                            description, node_count, edge_count, created_at,
                            updated_at
                        ) VALUES (?, ?, ?, ?, ?, 0, 0, ?, ?)
                    ''', (network_id, network_type, education_type, name,
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建学习网络: {name} ({network_id})')
                    return {'success': True, 'network_id': network_id}
        except Exception as e:
            logger.error(f'创建学习网络失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_network_relation(self, network_id: str, source_id: int,
                              target_id: int, relation_type: str,
                              weight: float = 1.0) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT node_count, edge_count FROM learning_network WHERE network_id = ?', (network_id,))
                    network = cursor.fetchone()
                    if not network:
                        return {'success': False, 'error': '网络不存在'}
                    cursor.execute('''
                        INSERT OR REPLACE INTO network_relations (
                            network_id, source_id, target_id, relation_type,
                            weight, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (network_id, source_id, target_id, relation_type, weight, now))
                    cursor.execute('UPDATE learning_network SET edge_count = ?, updated_at = ? WHERE network_id = ?',
                                 (network[1] + 1, now, network_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加网络关系失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_network_relations(self, network_id: str, source_id: int = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM network_relations WHERE network_id = ?'
                params = [network_id]
                if source_id:
                    query += ' AND source_id = ?'
                    params.append(source_id)
                cursor.execute(query, params)
                relations = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'relations': relations}
        except Exception as e:
            logger.error(f'获取网络关系失败: {e}')
            return {'success': False, 'error': str(e)}

    def recommend_connections(self, user_id: int, education_type: str,
                               limit: int = 10) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT target_id, COUNT(*) as connection_count
                    FROM network_relations
                    WHERE source_id IN (
                        SELECT target_id FROM network_relations WHERE source_id = ?
                    ) AND target_id != ?
                    GROUP BY target_id
                    ORDER BY connection_count DESC
                    LIMIT ?
                ''', (user_id, user_id, limit))
                recommendations = [{'user_id': r[0], 'score': r[1]} for r in cursor.fetchall()]
                return {'success': True, 'recommendations': recommendations}
        except Exception as e:
            logger.error(f'推荐连接失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 预警管理 ==========

    def create_alert(self, alert_type: str, education_type: str, title: str,
                      description: str, target_user_id: int, **kwargs) -> Dict[str, Any]:
        try:
            alert_id = f"alt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO social_alerts (
                            alert_id, alert_type, education_type, title,
                            description, target_user_id, trigger_condition,
                            severity, is_active, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                    ''', (alert_id, alert_type, education_type, title,
                          description, target_user_id,
                          kwargs.get('trigger_condition'),
                          kwargs.get('severity', 'medium'), now, now))
                    conn.commit()
                    logger.info(f'创建学习预警: {title} ({alert_id})')
                    return {'success': True, 'alert_id': alert_id}
        except Exception as e:
            logger.error(f'创建学习预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def trigger_alert(self, alert_id: str, user_id: int, message: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT is_active FROM social_alerts WHERE alert_id = ?', (alert_id,))
                    alert = cursor.fetchone()
                    if not alert:
                        return {'success': False, 'error': '预警不存在'}
                    if alert[0] != 1:
                        return {'success': False, 'error': '预警已禁用'}
                    cursor.execute('INSERT INTO alert_history (alert_id, user_id, message, status, sent_at) VALUES (?, ?, ?, \'sent\', ?)',
                                 (alert_id, user_id, message, now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'触发预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_alert_status(self, alert_id: str, is_active: bool) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE social_alerts SET is_active = ?, updated_at = ? WHERE alert_id = ?',
                                 (1 if is_active else 0, now, alert_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '预警不存在'}
        except Exception as e:
            logger.error(f'更新预警状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_alerts(self, education_type: str = None, alert_type: str = None,
                    is_active: bool = True, page: int = 1,
                    page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM social_alerts WHERE is_active = ?'
                params = [1 if is_active else 0]
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if alert_type:
                    query += ' AND alert_type = ?'
                    params.append(alert_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                alerts = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'alerts': alerts, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取预警列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 =========

    def get_learning_statistics(self, education_type: str = None,
                                 period: str = 'all') -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                stats = {}

                cursor.execute('SELECT COUNT(*) FROM learning_communities WHERE education_type = ?', (education_type or 'k12',))
                stats['community_count'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM learning_groups WHERE education_type = ?', (education_type or 'k12',))
                stats['group_count'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM learning_interactions WHERE education_type = ?', (education_type or 'k12',))
                stats['interaction_count'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM knowledge_sharing WHERE education_type = ?', (education_type or 'k12',))
                stats['knowledge_count'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM collaborative_learning WHERE education_type = ?', (education_type or 'k12',))
                stats['collaboration_count'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM peer_support WHERE education_type = ?', (education_type or 'k12',))
                stats['support_count'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM social_evaluation WHERE education_type = ?', (education_type or 'k12',))
                stats['evaluation_count'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM learning_network WHERE education_type = ?', (education_type or 'k12',))
                stats['network_count'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM social_alerts WHERE education_type = ?', (education_type or 'k12',))
                stats['alert_count'] = cursor.fetchone()[0]

                return {'success': True, 'statistics': stats}
        except Exception as e:
            logger.error(f'获取学习统计数据失败: {e}')
            return {'success': False, 'error': str(e)}
