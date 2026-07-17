#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育资源共享服务 (v15.13.0)
====================================
提供教育资源共享、校际协作、资源联盟、资源交易、知识产权等综合管理服务。

核心能力：
1. 教育资源共享 - 资源发布、下载、收藏、分享
2. 校际协作 - 联合教研、资源共建、课程共享、师资互聘
3. 资源联盟 - 区域联盟、学科联盟、校际联盟、国际联盟
4. 资源交易 - 付费下载、订阅服务、捐赠支持
5. 知识产权 - 版权登记、授权管理、合规审查
6. 共享空间 - 团队协作、资源库管理、权限控制
7. 资源评价 - 评分系统、评论管理、质量评估
8. 推荐系统 - 个性化推荐、智能匹配、热门排行

差异化支持：
- 成人教育：职业培训、继续教育、企业内训
- K12教育：基础教育、学科课程、素质教育
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'educational_resource_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationalResource')


# ========== 教育资源配置 ==========

RESOURCE_TYPES = {
    'course': {'name': '课程', 'description': '完整课程资源', 'education_types': ['adult', 'k12']},
    'textbook': {'name': '教材', 'description': '教科书及参考资料', 'education_types': ['adult', 'k12']},
    'lesson_plan': {'name': '教案', 'description': '教学方案设计', 'education_types': ['adult', 'k12']},
    'courseware': {'name': '课件', 'description': '教学演示文稿', 'education_types': ['adult', 'k12']},
    'question_bank': {'name': '题库', 'description': '试题及答案集合', 'education_types': ['adult', 'k12']},
    'video': {'name': '视频', 'description': '教学视频资源', 'education_types': ['adult', 'k12']},
    'audio': {'name': '音频', 'description': '教学音频资源', 'education_types': ['adult', 'k12']},
    'image': {'name': '图片', 'description': '教学图片资源', 'education_types': ['adult', 'k12']},
    'document': {'name': '文档', 'description': '教学文档资料', 'education_types': ['adult', 'k12']},
    'software': {'name': '软件', 'description': '教学软件工具', 'education_types': ['adult', 'k12']},
    'dataset': {'name': '数据集', 'description': '教学数据资源', 'education_types': ['adult']},
    'tool': {'name': '工具', 'description': '教学辅助工具', 'education_types': ['adult', 'k12']},
    'template': {'name': '模板', 'description': '教学模板资源', 'education_types': ['adult', 'k12']},
    'assessment': {'name': '评估', 'description': '评估与测试资源', 'education_types': ['adult', 'k12']}
}

SHARING_MODELS = {
    'free': {'name': '免费', 'description': '完全免费共享', 'requires_payment': False},
    'shared': {'name': '共享', 'description': '有条件共享', 'requires_payment': False},
    'authorized': {'name': '授权', 'description': '需获得授权', 'requires_payment': False},
    'transaction': {'name': '交易', 'description': '付费购买', 'requires_payment': True},
    'subscription': {'name': '订阅', 'description': '订阅制访问', 'requires_payment': True},
    'donation': {'name': '捐赠', 'description': '自愿捐赠支持', 'requires_payment': False}
}

ALLIANCE_TYPES = {
    'regional': {'name': '区域联盟', 'description': '同一地区学校联盟'},
    'subject': {'name': '学科联盟', 'description': '同一学科领域联盟'},
    'inter_school': {'name': '校际联盟', 'description': '跨校合作联盟'},
    'industry': {'name': '行业联盟', 'description': '教育与产业联盟'},
    'international': {'name': '国际联盟', 'description': '国际教育合作联盟'}
}

LICENSE_TYPES = {
    'CC-BY': {'name': 'CC-BY', 'description': '署名', 'commercial_use': True},
    'CC-BY-SA': {'name': 'CC-BY-SA', 'description': '署名-相同方式共享', 'commercial_use': True},
    'CC-BY-NC': {'name': 'CC-BY-NC', 'description': '署名-非商业', 'commercial_use': False},
    'CC-BY-NC-SA': {'name': 'CC-BY-NC-SA', 'description': '署名-非商业-相同方式共享', 'commercial_use': False},
    'CC0': {'name': 'CC0', 'description': '公有领域', 'commercial_use': True},
    'proprietary': {'name': '专有', 'description': '专有版权', 'commercial_use': False},
    'commercial': {'name': '商业', 'description': '商业授权', 'commercial_use': True}
}

RESOURCE_RATINGS = {1: '1星', 2: '2星', 3: '3星', 4: '4星', 5: '5星'}

RESOURCE_STATUS = {
    'draft': '草稿',
    'reviewing': '审核中',
    'published': '已发布',
    'offline': '下架',
    'deleted': '删除'
}

COLLABORATION_TYPES = {
    'joint_research': {'name': '联合教研', 'description': '多校联合教研活动'},
    'resource_co_build': {'name': '资源共建', 'description': '合作开发教育资源'},
    'course_sharing': {'name': '课程共享', 'description': '跨校课程互认共享'},
    'teacher_exchange': {'name': '师资互聘', 'description': '教师跨校交流任教'},
    'student_exchange': {'name': '学生交流', 'description': '学生跨校学习交流'},
    'project_cooperation': {'name': '项目合作', 'description': '联合开展教学项目'}
}


class EducationalResourceSharingService:
    """教育资源共享服务"""

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
                    CREATE TABLE IF NOT EXISTS shared_resources (
                        resource_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        resource_type TEXT NOT NULL,
                        education_type TEXT,
                        description TEXT,
                        file_url TEXT,
                        thumbnail_url TEXT,
                        file_size INTEGER DEFAULT 0,
                        sharing_model TEXT DEFAULT 'free',
                        price REAL DEFAULT 0,
                        subscription_period TEXT,
                        author_id INTEGER,
                        author_name TEXT,
                        institution_id INTEGER,
                        institution_name TEXT,
                        category_id TEXT,
                        tags TEXT,
                        license_type TEXT DEFAULT 'CC-BY',
                        status TEXT DEFAULT 'draft',
                        download_count INTEGER DEFAULT 0,
                        view_count INTEGER DEFAULT 0,
                        favorite_count INTEGER DEFAULT 0,
                        average_rating REAL DEFAULT 0,
                        rating_count INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS resource_categories (
                        category_id TEXT PRIMARY KEY,
                        category_name TEXT NOT NULL,
                        parent_id TEXT,
                        education_type TEXT,
                        description TEXT,
                        sort_order INTEGER DEFAULT 0,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS resource_tags (
                        tag_id TEXT PRIMARY KEY,
                        tag_name TEXT NOT NULL,
                        education_type TEXT,
                        usage_count INTEGER DEFAULT 0,
                        created_at TEXT,
                        UNIQUE(tag_name)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS resource_versions (
                        version_id TEXT PRIMARY KEY,
                        resource_id TEXT NOT NULL,
                        version_number TEXT NOT NULL,
                        change_log TEXT,
                        file_url TEXT,
                        file_size INTEGER DEFAULT 0,
                        author_id INTEGER,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS resource_downloads (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        resource_id TEXT NOT NULL,
                        user_id INTEGER,
                        user_name TEXT,
                        download_time TEXT,
                        education_type TEXT,
                        UNIQUE(resource_id, user_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS resource_favorites (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        resource_id TEXT NOT NULL,
                        user_id INTEGER,
                        user_name TEXT,
                        favorite_time TEXT,
                        UNIQUE(resource_id, user_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS resource_reviews (
                        review_id TEXT PRIMARY KEY,
                        resource_id TEXT NOT NULL,
                        reviewer_id INTEGER,
                        reviewer_name TEXT,
                        rating INTEGER DEFAULT 0,
                        comment TEXT,
                        helpful_count INTEGER DEFAULT 0,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sharing_agreements (
                        agreement_id TEXT PRIMARY KEY,
                        resource_id TEXT NOT NULL,
                        user_id INTEGER,
                        agreement_type TEXT,
                        accepted INTEGER DEFAULT 0,
                        accepted_at TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS resource_alliances (
                        alliance_id TEXT PRIMARY KEY,
                        alliance_name TEXT NOT NULL,
                        alliance_type TEXT,
                        description TEXT,
                        leader_id INTEGER,
                        leader_name TEXT,
                        institution_id INTEGER,
                        member_count INTEGER DEFAULT 1,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alliance_members (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        alliance_id TEXT NOT NULL,
                        institution_id INTEGER,
                        institution_name TEXT,
                        join_date TEXT,
                        role TEXT DEFAULT 'member',
                        UNIQUE(alliance_id, institution_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS collaboration_projects (
                        project_id TEXT PRIMARY KEY,
                        project_name TEXT NOT NULL,
                        collaboration_type TEXT,
                        description TEXT,
                        leader_id INTEGER,
                        leader_name TEXT,
                        institution_id INTEGER,
                        partner_ids TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        status TEXT DEFAULT 'planning',
                        resource_count INTEGER DEFAULT 0,
                        participant_count INTEGER DEFAULT 0,
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS resource_transactions (
                        transaction_id TEXT PRIMARY KEY,
                        resource_id TEXT NOT NULL,
                        buyer_id INTEGER,
                        buyer_name TEXT,
                        seller_id INTEGER,
                        seller_name TEXT,
                        transaction_type TEXT,
                        amount REAL DEFAULT 0,
                        currency TEXT DEFAULT 'CNY',
                        status TEXT DEFAULT 'pending',
                        payment_method TEXT,
                        completed_at TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS resource_licenses (
                        license_id TEXT PRIMARY KEY,
                        resource_id TEXT NOT NULL,
                        license_type TEXT,
                        license_key TEXT,
                        user_id INTEGER,
                        valid_from TEXT,
                        valid_until TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS intellectual_property (
                        ip_id TEXT PRIMARY KEY,
                        resource_id TEXT NOT NULL,
                        ip_type TEXT,
                        registration_number TEXT,
                        owner_id INTEGER,
                        owner_name TEXT,
                        institution_id INTEGER,
                        registration_date TEXT,
                        expiry_date TEXT,
                        status TEXT DEFAULT 'registered',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS shared_workspaces (
                        workspace_id TEXT PRIMARY KEY,
                        workspace_name TEXT NOT NULL,
                        description TEXT,
                        institution_id INTEGER,
                        owner_id INTEGER,
                        owner_name TEXT,
                        access_type TEXT DEFAULT 'private',
                        member_count INTEGER DEFAULT 1,
                        resource_count INTEGER DEFAULT 0,
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS workspace_members (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        workspace_id TEXT NOT NULL,
                        user_id INTEGER,
                        user_name TEXT,
                        role TEXT DEFAULT 'member',
                        join_date TEXT,
                        UNIQUE(workspace_id, user_id)
                    )
                ''')
                conn.commit()
                logger.info('教育资源共享服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 资源管理 ==========

    def publish_resource(self, title: str, resource_type: str,
                          author_id: int, author_name: str,
                          **kwargs) -> Dict[str, Any]:
        try:
            resource_id = f"res_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = RESOURCE_TYPES.get(resource_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO shared_resources (
                            resource_id, title, resource_type, education_type,
                            description, file_url, thumbnail_url, file_size,
                            sharing_model, price, subscription_period,
                            author_id, author_name, institution_id,
                            institution_name, category_id, tags,
                            license_type, status, download_count,
                            view_count, favorite_count, average_rating,
                            rating_count, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, 0, 0, ?, ?)
                    ''', (resource_id, title, resource_type,
                          kwargs.get('education_type', 'k12'),
                          kwargs.get('description'), kwargs.get('file_url'),
                          kwargs.get('thumbnail_url'), kwargs.get('file_size', 0),
                          kwargs.get('sharing_model', 'free'),
                          kwargs.get('price', 0), kwargs.get('subscription_period'),
                          author_id, author_name, kwargs.get('institution_id'),
                          kwargs.get('institution_name'), kwargs.get('category_id'),
                          json.dumps(kwargs.get('tags', [])),
                          kwargs.get('license_type', 'CC-BY'),
                          kwargs.get('status', 'draft'), now, now))
                    conn.commit()
                    logger.info(f'发布资源: {title} ({resource_id})')
                    return {'success': True, 'resource_id': resource_id}
        except Exception as e:
            logger.error(f'发布资源失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_resource(self, resource_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    updates = []
                    params = []
                    if 'title' in kwargs:
                        updates.append('title = ?')
                        params.append(kwargs['title'])
                    if 'description' in kwargs:
                        updates.append('description = ?')
                        params.append(kwargs['description'])
                    if 'file_url' in kwargs:
                        updates.append('file_url = ?')
                        params.append(kwargs['file_url'])
                    if 'sharing_model' in kwargs:
                        updates.append('sharing_model = ?')
                        params.append(kwargs['sharing_model'])
                    if 'price' in kwargs:
                        updates.append('price = ?')
                        params.append(kwargs['price'])
                    if 'status' in kwargs:
                        updates.append('status = ?')
                        params.append(kwargs['status'])
                    if 'tags' in kwargs:
                        updates.append('tags = ?')
                        params.append(json.dumps(kwargs['tags']))
                    if updates:
                        updates.append('updated_at = ?')
                        params.append(now)
                        params.append(resource_id)
                        cursor.execute(f'UPDATE shared_resources SET {", ".join(updates)} WHERE resource_id = ?', params)
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '没有可更新的字段'}
        except Exception as e:
            logger.error(f'更新资源失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_resource(self, resource_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM shared_resources WHERE resource_id = ?', (resource_id,))
                resource = cursor.fetchone()
                if resource:
                    resource_dict = dict(resource)
                    resource_dict['tags'] = json.loads(resource_dict.get('tags', '[]'))
                    return {'success': True, 'resource': resource_dict}
                return {'success': False, 'error': '资源不存在'}
        except Exception as e:
            logger.error(f'获取资源失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_resources(self, resource_type: str = None, education_type: str = None,
                       sharing_model: str = None, status: str = 'published',
                       page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM shared_resources WHERE 1=1'
                params = []
                if resource_type:
                    query += ' AND resource_type = ?'
                    params.append(resource_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if sharing_model:
                    query += ' AND sharing_model = ?'
                    params.append(sharing_model)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                resources = []
                for r in cursor.fetchall():
                    r_dict = dict(r)
                    r_dict['tags'] = json.loads(r_dict.get('tags', '[]'))
                    resources.append(r_dict)
                return {'success': True, 'resources': resources, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取资源列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 资源分类标签 ==========

    def create_category(self, category_name: str, **kwargs) -> Dict[str, Any]:
        try:
            category_id = f"cat_{uuid.uuid4().hex[:8]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO resource_categories (
                            category_id, category_name, parent_id,
                            education_type, description, sort_order, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (category_id, category_name, kwargs.get('parent_id'),
                          kwargs.get('education_type'), kwargs.get('description'),
                          kwargs.get('sort_order', 0), now))
                    conn.commit()
                    logger.info(f'创建分类: {category_name} ({category_id})')
                    return {'success': True, 'category_id': category_id}
        except Exception as e:
            logger.error(f'创建分类失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_tag(self, tag_name: str, education_type: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT OR IGNORE INTO resource_tags (tag_id, tag_name, education_type, usage_count, created_at) VALUES (?, ?, ?, 0, ?)',
                                 (f"tag_{uuid.uuid4().hex[:8]}", tag_name, education_type, now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加标签失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_category_tree(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM resource_categories WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' ORDER BY sort_order'
                cursor.execute(query, params)
                categories = [dict(c) for c in cursor.fetchall()]
                tree = {}
                for cat in categories:
                    parent_id = cat.get('parent_id')
                    if parent_id:
                        if parent_id not in tree:
                            tree[parent_id] = {'children': []}
                        tree[parent_id]['children'].append(cat)
                    else:
                        if cat['category_id'] not in tree:
                            tree[cat['category_id']] = cat
                            tree[cat['category_id']]['children'] = []
                return {'success': True, 'categories': list(tree.values())}
        except Exception as e:
            logger.error(f'获取分类树失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 资源版本 ==========

    def create_version(self, resource_id: str, version_number: str,
                        change_log: str, **kwargs) -> Dict[str, Any]:
        try:
            version_id = f"ver_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM shared_resources WHERE resource_id = ?', (resource_id,))
                    resource = cursor.fetchone()
                    if not resource:
                        return {'success': False, 'error': '资源不存在'}
                    cursor.execute('''
                        INSERT INTO resource_versions (
                            version_id, resource_id, version_number,
                            change_log, file_url, file_size, author_id, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (version_id, resource_id, version_number, change_log,
                          kwargs.get('file_url'), kwargs.get('file_size', 0),
                          kwargs.get('author_id'), now))
                    conn.commit()
                    logger.info(f'创建版本: {resource_id} v{version_number}')
                    return {'success': True, 'version_id': version_id}
        except Exception as e:
            logger.error(f'创建版本失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_versions(self, resource_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM resource_versions WHERE resource_id = ? ORDER BY created_at DESC', (resource_id,))
                versions = [dict(v) for v in cursor.fetchall()]
                return {'success': True, 'versions': versions}
        except Exception as e:
            logger.error(f'获取版本列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def rollback_version(self, resource_id: str, version_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT file_url, file_size FROM resource_versions WHERE version_id = ? AND resource_id = ?', (version_id, resource_id))
                    version = cursor.fetchone()
                    if not version:
                        return {'success': False, 'error': '版本不存在'}
                    cursor.execute('UPDATE shared_resources SET file_url = ?, file_size = ?, updated_at = ? WHERE resource_id = ?',
                                 (version[0], version[1], now, resource_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'回滚版本失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 共享联盟 ==========

    def create_alliance(self, alliance_name: str, alliance_type: str,
                         leader_id: int, leader_name: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            alliance_id = f"all_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO resource_alliances (
                            alliance_id, alliance_name, alliance_type,
                            description, leader_id, leader_name,
                            institution_id, member_count, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, 'active', ?, ?)
                    ''', (alliance_id, alliance_name, alliance_type,
                          kwargs.get('description'), leader_id, leader_name,
                          kwargs.get('institution_id'), now, now))
                    cursor.execute('INSERT INTO alliance_members (alliance_id, institution_id, institution_name, join_date, role) VALUES (?, ?, ?, ?, \'leader\')',
                                 (alliance_id, kwargs.get('institution_id'), kwargs.get('institution_name'), now))
                    conn.commit()
                    logger.info(f'创建联盟: {alliance_name} ({alliance_id})')
                    return {'success': True, 'alliance_id': alliance_id}
        except Exception as e:
            logger.error(f'创建联盟失败: {e}')
            return {'success': False, 'error': str(e)}

    def join_alliance(self, alliance_id: str, institution_id: int,
                       institution_name: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT OR IGNORE INTO alliance_members (alliance_id, institution_id, institution_name, join_date, role) VALUES (?, ?, ?, ?, \'member\')',
                                 (alliance_id, institution_id, institution_name, now))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE resource_alliances SET member_count = member_count + 1, updated_at = ? WHERE alliance_id = ?', (now, alliance_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已加入该联盟'}
        except Exception as e:
            logger.error(f'加入联盟失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_alliances(self, alliance_type: str = None, **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM resource_alliances WHERE 1=1'
                params = []
                if alliance_type:
                    query += ' AND alliance_type = ?'
                    params.append(alliance_type)
                query += ' ORDER BY created_at DESC'
                cursor.execute(query, params)
                alliances = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'alliances': alliances}
        except Exception as e:
            logger.error(f'获取联盟列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_alliance_resources(self, alliance_id: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT institution_id FROM alliance_members WHERE alliance_id = ?', (alliance_id,))
                members = cursor.fetchall()
                if not members:
                    return {'success': False, 'error': '联盟无成员'}
                institution_ids = [m['institution_id'] for m in members]
                placeholders = ','.join('?' * len(institution_ids))
                query = f'SELECT * FROM shared_resources WHERE institution_id IN ({placeholders}) AND status = "published"'
                cursor.execute(query, institution_ids)
                resources = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'resources': resources}
        except Exception as e:
            logger.error(f'获取联盟资源失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 校际协作 ==========

    def create_collaboration_project(self, project_name: str, collaboration_type: str,
                                      leader_id: int, leader_name: str,
                                      **kwargs) -> Dict[str, Any]:
        try:
            project_id = f"col_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO collaboration_projects (
                            project_id, project_name, collaboration_type,
                            description, leader_id, leader_name,
                            institution_id, partner_ids, start_date,
                            end_date, status, resource_count,
                            participant_count, education_type,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?, ?)
                    ''', (project_id, project_name, collaboration_type,
                          kwargs.get('description'), leader_id, leader_name,
                          kwargs.get('institution_id'),
                          json.dumps(kwargs.get('partner_ids', [])),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('status', 'planning'),
                          kwargs.get('education_type', 'k12'), now, now))
                    conn.commit()
                    logger.info(f'创建协作项目: {project_name} ({project_id})')
                    return {'success': True, 'project_id': project_id}
        except Exception as e:
            logger.error(f'创建协作项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_participant(self, project_id: str, user_id: int, user_name: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM collaboration_projects WHERE project_id = ?', (project_id,))
                    project = cursor.fetchone()
                    if not project:
                        return {'success': False, 'error': '项目不存在'}
                    cursor.execute('UPDATE collaboration_projects SET participant_count = participant_count + 1, updated_at = ? WHERE project_id = ?', (now, project_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加参与者失败: {e}')
            return {'success': False, 'error': str(e)}

    def link_resource_to_project(self, project_id: str, resource_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM collaboration_projects WHERE project_id = ?', (project_id,))
                    project = cursor.fetchone()
                    if not project:
                        return {'success': False, 'error': '项目不存在'}
                    cursor.execute('UPDATE collaboration_projects SET resource_count = resource_count + 1, updated_at = ? WHERE project_id = ?', (now, project_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'关联资源失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_collaboration_projects(self, collaboration_type: str = None,
                                     education_type: str = None, **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM collaboration_projects WHERE 1=1'
                params = []
                if collaboration_type:
                    query += ' AND collaboration_type = ?'
                    params.append(collaboration_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' ORDER BY created_at DESC'
                cursor.execute(query, params)
                projects = []
                for p in cursor.fetchall():
                    p_dict = dict(p)
                    p_dict['partner_ids'] = json.loads(p_dict.get('partner_ids', '[]'))
                    projects.append(p_dict)
                return {'success': True, 'projects': projects}
        except Exception as e:
            logger.error(f'获取协作项目列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 资源交易 ==========

    def create_transaction(self, resource_id: str, buyer_id: int,
                           buyer_name: str, **kwargs) -> Dict[str, Any]:
        try:
            transaction_id = f"txn_{uuid.uuid4().hex[:16]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT price, sharing_model, author_id, author_name FROM shared_resources WHERE resource_id = ?', (resource_id,))
                    resource = cursor.fetchone()
                    if not resource:
                        return {'success': False, 'error': '资源不存在'}
                    transaction_type = 'purchase' if resource[1] == 'transaction' else 'subscription'
                    cursor.execute('''
                        INSERT INTO resource_transactions (
                            transaction_id, resource_id, buyer_id,
                            buyer_name, seller_id, seller_name,
                            transaction_type, amount, currency,
                            status, payment_method, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (transaction_id, resource_id, buyer_id, buyer_name,
                          resource[2], resource[3], transaction_type,
                          resource[0], kwargs.get('currency', 'CNY'),
                          kwargs.get('status', 'pending'),
                          kwargs.get('payment_method'), now))
                    conn.commit()
                    return {'success': True, 'transaction_id': transaction_id}
        except Exception as e:
            logger.error(f'创建交易失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_transaction(self, transaction_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE resource_transactions SET status = ?, completed_at = ? WHERE transaction_id = ? AND status = ?',
                                 ('completed', now, transaction_id, 'pending'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '交易状态不允许完成'}
        except Exception as e:
            logger.error(f'完成交易失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_license(self, resource_id: str, user_id: int, **kwargs) -> Dict[str, Any]:
        try:
            license_id = f"lic_{uuid.uuid4().hex[:12]}"
            license_key = f"LIC{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}"
            now = datetime.now().isoformat()
            valid_until = (datetime.now() + timedelta(days=365)).isoformat() if kwargs.get('duration_days') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT license_type FROM shared_resources WHERE resource_id = ?', (resource_id,))
                    resource = cursor.fetchone()
                    if not resource:
                        return {'success': False, 'error': '资源不存在'}
                    cursor.execute('''
                        INSERT INTO resource_licenses (
                            license_id, resource_id, license_type,
                            license_key, user_id, valid_from,
                            valid_until, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?)
                    ''', (license_id, resource_id, resource[0], license_key,
                          user_id, now, valid_until, now))
                    conn.commit()
                    return {'success': True, 'license_id': license_id, 'license_key': license_key}
        except Exception as e:
            logger.error(f'创建授权失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_user_purchases(self, user_id: int) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM resource_transactions WHERE buyer_id = ? AND status = "completed" ORDER BY created_at DESC', (user_id,))
                purchases = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'purchases': purchases}
        except Exception as e:
            logger.error(f'获取用户购买记录失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 知识产权 ==========

    def register_ip(self, resource_id: str, ip_type: str, owner_id: int,
                     owner_name: str, **kwargs) -> Dict[str, Any]:
        try:
            ip_id = f"ip_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT title FROM shared_resources WHERE resource_id = ?', (resource_id,))
                    resource = cursor.fetchone()
                    if not resource:
                        return {'success': False, 'error': '资源不存在'}
                    cursor.execute('''
                        INSERT INTO intellectual_property (
                            ip_id, resource_id, ip_type, registration_number,
                            owner_id, owner_name, institution_id,
                            registration_date, expiry_date, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'registered', ?)
                    ''', (ip_id, resource_id, ip_type, kwargs.get('registration_number'),
                          owner_id, owner_name, kwargs.get('institution_id'),
                          kwargs.get('registration_date', now[:10]),
                          kwargs.get('expiry_date'), now))
                    conn.commit()
                    logger.info(f'注册知识产权: {ip_id}')
                    return {'success': True, 'ip_id': ip_id}
        except Exception as e:
            logger.error(f'注册知识产权失败: {e}')
            return {'success': False, 'error': str(e)}

    def verify_ip(self, ip_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM intellectual_property WHERE ip_id = ?', (ip_id,))
                ip = cursor.fetchone()
                if ip:
                    return {'success': True, 'ip': dict(ip)}
                return {'success': False, 'error': '知识产权记录不存在'}
        except Exception as e:
            logger.error(f'验证知识产权失败: {e}')
            return {'success': False, 'error': str(e)}

    def transfer_ip(self, ip_id: str, new_owner_id: int, new_owner_name: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE intellectual_property SET owner_id = ?, owner_name = ?, status = "transferred", updated_at = ? WHERE ip_id = ?',
                                 (new_owner_id, new_owner_name, now, ip_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '知识产权记录不存在'}
        except Exception as e:
            logger.error(f'转让知识产权失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_ip_records(self, owner_id: int = None, **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM intellectual_property WHERE 1=1'
                params = []
                if owner_id:
                    query += ' AND owner_id = ?'
                    params.append(owner_id)
                query += ' ORDER BY registration_date DESC'
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records}
        except Exception as e:
            logger.error(f'获取知识产权列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 共享空间 ==========

    def create_workspace(self, workspace_name: str, owner_id: int,
                         owner_name: str, **kwargs) -> Dict[str, Any]:
        try:
            workspace_id = f"wsp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO shared_workspaces (
                            workspace_id, workspace_name, description,
                            institution_id, owner_id, owner_name,
                            access_type, member_count, resource_count,
                            education_type, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, 0, ?, ?, ?)
                    ''', (workspace_id, workspace_name, kwargs.get('description'),
                          kwargs.get('institution_id'), owner_id, owner_name,
                          kwargs.get('access_type', 'private'),
                          kwargs.get('education_type', 'k12'), now, now))
                    cursor.execute('INSERT INTO workspace_members (workspace_id, user_id, user_name, role, join_date) VALUES (?, ?, ?, \'owner\', ?)',
                                 (workspace_id, owner_id, owner_name, now))
                    conn.commit()
                    logger.info(f'创建共享空间: {workspace_name} ({workspace_id})')
                    return {'success': True, 'workspace_id': workspace_id}
        except Exception as e:
            logger.error(f'创建共享空间失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_workspace_member(self, workspace_id: str, user_id: int,
                             user_name: str, role: str = 'member') -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT OR IGNORE INTO workspace_members (workspace_id, user_id, user_name, role, join_date) VALUES (?, ?, ?, ?, ?)',
                                 (workspace_id, user_id, user_name, role, now))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE shared_workspaces SET member_count = member_count + 1, updated_at = ? WHERE workspace_id = ?', (now, workspace_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已加入该空间'}
        except Exception as e:
            logger.error(f'添加空间成员失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_resource_to_workspace(self, workspace_id: str, resource_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE shared_workspaces SET resource_count = resource_count + 1, updated_at = ? WHERE workspace_id = ?', (now, workspace_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加资源到空间失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_workspaces(self, user_id: int = None, education_type: str = None,
                        **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                if user_id:
                    cursor.execute('SELECT w.* FROM shared_workspaces w JOIN workspace_members m ON w.workspace_id = m.workspace_id WHERE m.user_id = ? ORDER BY w.created_at DESC', (user_id,))
                else:
                    query = 'SELECT * FROM shared_workspaces WHERE 1=1'
                    params = []
                    if education_type:
                        query += ' AND education_type = ?'
                        params.append(education_type)
                    query += ' ORDER BY created_at DESC'
                    cursor.execute(query, params)
                workspaces = [dict(w) for w in cursor.fetchall()]
                return {'success': True, 'workspaces': workspaces}
        except Exception as e:
            logger.error(f'获取空间列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 资源评价 ==========

    def submit_review(self, resource_id: str, reviewer_id: int,
                       reviewer_name: str, rating: int, **kwargs) -> Dict[str, Any]:
        try:
            review_id = f"rev_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT OR REPLACE INTO resource_reviews (review_id, resource_id, reviewer_id, reviewer_name, rating, comment, helpful_count, created_at) VALUES (?, ?, ?, ?, ?, ?, 0, ?)',
                                 (review_id, resource_id, reviewer_id, reviewer_name, rating, kwargs.get('comment'), now))
                    cursor.execute('SELECT AVG(rating), COUNT(*) FROM resource_reviews WHERE resource_id = ?', (resource_id,))
                    stats = cursor.fetchone()
                    avg = round(stats[0], 1) if stats[0] else 0
                    count = stats[1] or 0
                    cursor.execute('UPDATE shared_resources SET average_rating = ?, rating_count = ?, updated_at = ? WHERE resource_id = ?',
                                 (avg, count, now, resource_id))
                    conn.commit()
                    return {'success': True, 'average_rating': avg, 'rating_count': count}
        except Exception as e:
            logger.error(f'提交评价失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_reviews(self, resource_id: str, page: int = 1,
                     page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM resource_reviews WHERE resource_id = ?'
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', (resource_id,))
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                cursor.execute(query, (resource_id, page_size, (page - 1) * page_size))
                reviews = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'reviews': reviews, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取评价列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def mark_review_helpful(self, review_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE resource_reviews SET helpful_count = helpful_count + 1 WHERE review_id = ?', (review_id,))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '评价不存在'}
        except Exception as e:
            logger.error(f'标记评价有用失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 推荐系统 ==========

    def get_recommendations(self, user_id: int, education_type: str = None,
                            limit: int = 10) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM shared_resources WHERE status = "published"'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' ORDER BY view_count DESC, download_count DESC LIMIT ?'
                params.append(limit)
                cursor.execute(query, params)
                recommendations = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'recommendations': recommendations}
        except Exception as e:
            logger.error(f'获取推荐失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_trending_resources(self, education_type: str = None,
                               limit: int = 10) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = '''
                    SELECT r.*, COUNT(d.id) as recent_downloads
                    FROM shared_resources r
                    LEFT JOIN resource_downloads d ON r.resource_id = d.resource_id AND d.download_time >= ?
                    WHERE r.status = "published"
                '''
                params = [(datetime.now() - timedelta(days=7)).isoformat()]
                if education_type:
                    query += ' AND r.education_type = ?'
                    params.append(education_type)
                query += ' GROUP BY r.resource_id ORDER BY recent_downloads DESC, r.view_count DESC LIMIT ?'
                params.append(limit)
                cursor.execute(query, params)
                trending = [dict(t) for t in cursor.fetchall()]
                return {'success': True, 'trending': trending}
        except Exception as e:
            logger.error(f'获取热门资源失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_similar_resources(self, resource_id: str, limit: int = 5) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT resource_type, category_id, tags FROM shared_resources WHERE resource_id = ?', (resource_id,))
                resource = cursor.fetchone()
                if not resource:
                    return {'success': False, 'error': '资源不存在'}
                query = 'SELECT * FROM shared_resources WHERE status = "published" AND resource_type = ? AND resource_id != ? ORDER BY average_rating DESC LIMIT ?'
                cursor.execute(query, (resource[0], resource_id, limit))
                similar = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'similar': similar}
        except Exception as e:
            logger.error(f'获取相似资源失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_resource_statistics(self, education_type: str = None,
                                period: str = 'all') -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = 'SELECT COUNT(*) as total, SUM(download_count) as total_downloads, SUM(view_count) as total_views FROM shared_resources WHERE status = "published"'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if period == 'month':
                    query += ' AND created_at >= ?'
                    params.append((datetime.now() - timedelta(days=30)).isoformat())
                elif period == 'week':
                    query += ' AND created_at >= ?'
                    params.append((datetime.now() - timedelta(days=7)).isoformat())
                cursor.execute(query, params)
                stats = cursor.fetchone()
                return {
                    'success': True,
                    'total_resources': stats[0] or 0,
                    'total_downloads': stats[1] or 0,
                    'total_views': stats[2] or 0
                }
        except Exception as e:
            logger.error(f'获取资源统计失败: {e}')
            return {'success': False, 'error': str(e)}