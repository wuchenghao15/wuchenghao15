from core.db_path import get_db_path as _mtscos_get_db_path
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 学习资源库服务 (v15.2.0)
====================================
提供学习资源管理、分类、检索、收藏和学习进度追踪等综合服务。

核心能力：
1. 资源管理 - 上传、编辑、删除学习资源
2. 资源分类 - 按科目、类型、难度、年级分类
3. 资源检索 - 关键词搜索、标签搜索、筛选
4. 资源收藏 - 收藏夹管理
5. 学习进度 - 资源学习进度追踪
6. 资源评价 - 评分、评论、推荐
7. 成人资源 - 成人教育专属资源库
8. K12资源 - 九年制义务教育资源库
"""
import os
import json
import uuid
import sqlite3
import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

DATABASE_PATH = _mtscos_get_db_path('app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'learning_resource_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('LearningResource')


# ========== 资源配置 ==========

# 资源类型
RESOURCE_TYPES = {
    'video': {'name': '视频课程', 'icon': 'video', 'extensions': ['.mp4', '.avi', '.mov', '.mkv']},
    'audio': {'name': '音频资料', 'icon': 'audio', 'extensions': ['.mp3', '.wav', '.m4a']},
    'document': {'name': '文档资料', 'icon': 'document', 'extensions': ['.pdf', '.doc', '.docx', '.ppt', '.pptx']},
    'text': {'name': '图文教程', 'icon': 'text', 'extensions': ['.txt', '.md', '.html']},
    'exercise': {'name': '习题集', 'icon': 'exercise', 'extensions': ['.pdf', '.doc', '.docx']},
    'exam': {'name': '试卷真题', 'icon': 'exam', 'extensions': ['.pdf', '.doc', '.docx']},
    'software': {'name': '软件工具', 'icon': 'software', 'extensions': ['.exe', '.dmg', '.zip', '.tar.gz']},
    'image': {'name': '图片素材', 'icon': 'image', 'extensions': ['.jpg', '.png', '.gif', '.svg']},
    'interactive': {'name': '互动课件', 'icon': 'interactive', 'extensions': ['.html', '.swf']},
    'courseware': {'name': '教学课件', 'icon': 'courseware', 'extensions': ['.ppt', '.pptx', '.pdf']}
}

# 资源难度
RESOURCE_DIFFICULTY = {
    1: {'name': '入门', 'color': '#52c41a'},
    2: {'name': '初级', 'color': '#73d13d'},
    3: {'name': '中级', 'color': '#faad14'},
    4: {'name': '高级', 'color': '#fa8c16'},
    5: {'name': '专家', 'color': '#f5222d'}
}

# 教育阶段
EDUCATION_STAGES = {
    'preschool': {'name': '学前', 'grades': '3-6岁'},
    'primary_low': {'name': '小学低年级', 'grades': '1-2年级'},
    'primary_high': {'name': '小学高年级', 'grades': '3-6年级'},
    'junior_high': {'name': '初中', 'grades': '7-9年级'},
    'senior_high': {'name': '高中', 'grades': '10-12年级'},
    'adult_beginner': {'name': '成人入门', 'description': '零基础成人学习者'},
    'adult_intermediate': {'name': '成人进阶', 'description': '有一定基础的成人学习者'},
    'adult_advanced': {'name': '成人高级', 'description': '高级水平成人学习者'},
    'adult_professional': {'name': '成人职业', 'description': '职业发展导向'}
}

# 资源质量评级
QUALITY_RATINGS = {
    1: '一星',
    2: '二星',
    3: '三星',
    4: '四星',
    5: '五星'
}

# 成人资源分类
ADULT_RESOURCE_CATEGORIES = {
    'language': {'name': '语言学习', 'subcategories': ['日语', '英语', '韩语', '其他语言']},
    'professional': {'name': '职业技能', 'subcategories': ['IT技术', '商务管理', '财务会计', '设计创意']},
    'exam': {'name': '考试考证', 'subcategories': ['JLPT', 'J.TEST', '托业', '其他证书']},
    'interest': {'name': '兴趣爱好', 'subcategories': ['文化', '历史', '艺术', '生活技能']},
    'academic': {'name': '学历提升', 'subcategories': ['成人高考', '自考', '考研', '公务员']}
}

# K12资源分类
K12_RESOURCE_CATEGORIES = {
    'chinese': {'name': '语文', 'subcategories': ['阅读', '写作', '文言文', '基础知识']},
    'math': {'name': '数学', 'subcategories': ['代数', '几何', '函数', '概率统计']},
    'english': {'name': '英语', 'subcategories': ['听力', '口语', '阅读', '写作', '语法']},
    'physics': {'name': '物理', 'subcategories': ['力学', '电磁学', '光学', '热学']},
    'chemistry': {'name': '化学', 'subcategories': ['无机化学', '有机化学', '实验']},
    'biology': {'name': '生物', 'subcategories': ['细胞', '遗传', '生态']},
    'politics': {'name': '政治', 'subcategories': ['经济', '政治', '文化', '哲学']},
    'history': {'name': '历史', 'subcategories': ['中国史', '世界史']},
    'geography': {'name': '地理', 'subcategories': ['自然地理', '人文地理', '区域地理']}
}


class LearningResourceService:
    """学习资源库服务"""

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
                    CREATE TABLE IF NOT EXISTS learning_resources (
                        resource_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT,
                        education_type TEXT NOT NULL,
                        subject TEXT,
                        category TEXT,
                        subcategory TEXT,
                        resource_type TEXT NOT NULL,
                        difficulty INTEGER DEFAULT 3,
                        grade_level TEXT,
                        content_url TEXT,
                        file_size INTEGER DEFAULT 0,
                        duration_seconds INTEGER DEFAULT 0,
                        thumbnail_url TEXT,
                        tags TEXT,
                        author_id INTEGER,
                        author_name TEXT,
                        quality_rating REAL DEFAULT 0,
                        rating_count INTEGER DEFAULT 0,
                        view_count INTEGER DEFAULT 0,
                        download_count INTEGER DEFAULT 0,
                        favorite_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'draft',
                        is_free INTEGER DEFAULT 1,
                        price REAL DEFAULT 0,
                        knowledge_points TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        published_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS resource_ratings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        resource_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        rating INTEGER NOT NULL,
                        comment TEXT,
                        created_at TEXT,
                        UNIQUE(resource_id, user_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS resource_favorites (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        resource_id TEXT NOT NULL,
                        folder_id TEXT,
                        created_at TEXT,
                        UNIQUE(user_id, resource_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS resource_folders (
                        folder_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        folder_name TEXT NOT NULL,
                        parent_id TEXT,
                        description TEXT,
                        resource_count INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS resource_progress (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        resource_id TEXT NOT NULL,
                        progress REAL DEFAULT 0,
                        last_position REAL DEFAULT 0,
                        total_duration INTEGER DEFAULT 0,
                        is_completed INTEGER DEFAULT 0,
                        first_view_at TEXT,
                        last_view_at TEXT,
                        view_count INTEGER DEFAULT 0,
                        UNIQUE(user_id, resource_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS resource_categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        education_type TEXT NOT NULL,
                        category_code TEXT NOT NULL,
                        category_name TEXT NOT NULL,
                        parent_code TEXT,
                        sort_order INTEGER DEFAULT 0,
                        is_active INTEGER DEFAULT 1,
                        UNIQUE(education_type, category_code)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS resource_comments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        resource_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        content TEXT NOT NULL,
                        parent_id INTEGER,
                        like_count INTEGER DEFAULT 0,
                        is_deleted INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('学习资源库服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    def add_resource(self, title: str, education_type: str, resource_type: str,
                     content_url: str, **kwargs) -> Dict[str, Any]:
        try:
            resource_id = f"res_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            tags = json.dumps(kwargs.get('tags'), ensure_ascii=False) if kwargs.get('tags') else None
            kps = json.dumps(kwargs.get('knowledge_points'),
            ensure_ascii=False) if kwargs.get('knowledge_points') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO learning_resources (
                            resource_id, title, description, education_type, subject,
                            category, subcategory, resource_type, difficulty, grade_level,
                            content_url, file_size, duration_seconds, thumbnail_url,
                            tags, author_id, author_name, status, is_free, price,
                            knowledge_points, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        resource_id, title, kwargs.get('description'), education_type,
                        kwargs.get('subject'), kwargs.get('category'), kwargs.get('subcategory'),
                        resource_type, kwargs.get('difficulty', 3), kwargs.get('grade_level'),
                        content_url, kwargs.get('file_size', 0), kwargs.get('duration_seconds', 0),
                        kwargs.get('thumbnail_url'), tags, kwargs.get('author_id'),
                        kwargs.get('author_name'), kwargs.get('status', 'draft'),
                        kwargs.get('is_free', 1), kwargs.get('price', 0), kps, now, now
                    ))
                    conn.commit()
                    logger.info(f'添加资源: {title} ({resource_id})')
                    return {'success': True, 'resource_id': resource_id, 'title': title}
        except Exception as e:
            logger.error(f'添加资源失败: {e}')
            return {'success': False, 'error': str(e)}

    def publish_resource(self, resource_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE learning_resources SET status = 'published', published_at = ?, updated_at = ?
                        WHERE resource_id = ? AND status = 'draft'
                    ''', (now, now, resource_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'发布资源: {resource_id}')
                        return {'success': True}
                    return {'success': False, 'error': '资源状态不允许发布'}
        except Exception as e:
            logger.error(f'发布资源失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_resource(self, resource_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM learning_resources WHERE resource_id = ?', (resource_id,))
                row = cursor.fetchone()
                if row:
                    resource = dict(row)
                    if resource.get('tags'):
                        resource['tags'] = json.loads(resource['tags'])
                    if resource.get('knowledge_points'):
                        resource['knowledge_points'] = json.loads(resource['knowledge_points'])
                    return resource
                return None
        except Exception as e:
            logger.error(f'获取资源信息失败: {e}')
            return None

    def search_resources(self, keyword: str = None, education_type: str = None,
                         subject: str = None, category: str = None,
                         resource_type: str = None, difficulty: int = None,
                         sort_by: str = 'latest', page: int = 1,
                         page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = "SELECT * FROM learning_resources WHERE status = 'published'"
                params = []
                if keyword:
                    query += ' AND (title LIKE ? OR description LIKE ? OR tags LIKE ?)'
                    like_pattern = f'%{keyword}%'
                    params.extend([like_pattern, like_pattern, like_pattern])
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if subject:
                    query += ' AND subject = ?'
                    params.append(subject)
                if category:
                    query += ' AND category = ?'
                    params.append(category)
                if resource_type:
                    query += ' AND resource_type = ?'
                    params.append(resource_type)
                if difficulty:
                    query += ' AND difficulty = ?'
                    params.append(difficulty)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                sort_map = {
                    'latest': 'created_at DESC',
                    'popular': 'view_count DESC',
                    'top_rated': 'quality_rating DESC',
                    'most_favorited': 'favorite_count DESC'
                }
                order = sort_map.get(sort_by, 'created_at DESC')
                query += f' ORDER BY {order} LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                resources = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'resources': resources, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'搜索资源失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_resources(self, education_type: str = None, subject: str = None,
                       category: str = None, resource_type: str = None,
                       status: str = 'published', page: int = 1,
                       page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM learning_resources WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if subject:
                    query += ' AND subject = ?'
                    params.append(subject)
                if category:
                    query += ' AND category = ?'
                    params.append(category)
                if resource_type:
                    query += ' AND resource_type = ?'
                    params.append(resource_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                resources = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'resources': resources, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取资源列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_resource(self, resource_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            fields = []
            params = []
            for key in ['title', 'description', 'subject', 'category', 'subcategory',
                        'resource_type', 'difficulty', 'grade_level', 'content_url',
                        'file_size', 'duration_seconds', 'thumbnail_url', 'status',
                        'is_free', 'price']:
                if key in kwargs:
                    fields.append(f'{key} = ?')
                    params.append(kwargs[key])
            if 'tags' in kwargs:
                fields.append('tags = ?')
                params.append(json.dumps(kwargs['tags'], ensure_ascii=False))
            if 'knowledge_points' in kwargs:
                fields.append('knowledge_points = ?')
                params.append(json.dumps(kwargs['knowledge_points'], ensure_ascii=False))
            if not fields:
                return {'success': False, 'error': '没有需要更新的字段'}
            fields.append('updated_at = ?')
            params.append(now)
            params.append(resource_id)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(f'UPDATE learning_resources SET {", ".join(fields)} WHERE resource_id = ?', params)
                    conn.commit()
                    logger.info(f'更新资源: {resource_id}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'更新资源失败: {e}')
            return {'success': False, 'error': str(e)}

    def increment_view(self, resource_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE learning_resources SET view_count = view_count + 1 WHERE resource_id = ?
                    ''', (resource_id,))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'增加浏览量失败: {e}')
            return {'success': False, 'error': str(e)}

    def increment_download(self, resource_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE learning_resources SET download_count = download_count + 1 WHERE resource_id = ?
                    ''', (resource_id,))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'增加下载量失败: {e}')
            return {'success': False, 'error': str(e)}

    def rate_resource(self, resource_id: str, user_id: int, rating: int,
                       comment: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            if rating < 1 or rating > 5:
                return {'success': False, 'error': '评分必须在1-5之间'}
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO resource_ratings (resource_id, user_id, rating, comment, created_at)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(resource_id, user_id) DO UPDATE SET
                            rating = excluded.rating,
                            comment = excluded.comment
                    ''', (resource_id, user_id, rating, comment, now))
                    cursor.execute('''
                        SELECT AVG(rating), COUNT(*) FROM resource_ratings WHERE resource_id = ?
                    ''', (resource_id,))
                    avg_rating, count = cursor.fetchone()
                    cursor.execute('''
                        UPDATE learning_resources SET quality_rating = ?, rating_count = ? WHERE resource_id = ?
                    ''', (round(avg_rating or 0, 2), count, resource_id))
                    conn.commit()
                    logger.info(f'用户 {user_id} 评分资源 {resource_id}: {rating}分')
                    return {'success': True, 'average_rating': round(avg_rating or 0, 2), 'rating_count': count}
        except Exception as e:
            logger.error(f'评分资源失败: {e}')
            return {'success': False, 'error': str(e)}

    def favorite_resource(self, user_id: int, resource_id: str,
                           folder_id: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR IGNORE INTO resource_favorites (user_id, resource_id, folder_id, created_at)
                        VALUES (?, ?, ?, ?)
                    ''', (user_id, resource_id, folder_id, now))
                    if cursor.rowcount > 0:
                        cursor.execute('''
                            UPDATE learning_resources SET favorite_count = favorite_count + 1 WHERE resource_id = ?
                        ''', (resource_id,))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'收藏资源失败: {e}')
            return {'success': False, 'error': str(e)}

    def unfavorite_resource(self, user_id: int, resource_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM resource_favorites WHERE user_id = ? AND resource_id = ?', (user_id,
                    resource_id))
                    if cursor.rowcount > 0:
                        cursor.execute('''
                            UPDATE learning_resources SET favorite_count = MAX(favorite_count - 1,
                            0) WHERE resource_id = ?
                        ''', (resource_id,))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'取消收藏失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_user_favorites(self, user_id: int, folder_id: str = None,
                            page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = '''
                    SELECT lr.*, rf.created_at as favorited_at, rf.folder_id
                    FROM resource_favorites rf
                    JOIN learning_resources lr ON rf.resource_id = lr.resource_id
                    WHERE rf.user_id = ?
                '''
                params = [user_id]
                if folder_id:
                    query += ' AND rf.folder_id = ?'
                    params.append(folder_id)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY rf.created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                favorites = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'favorites': favorites, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取收藏列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def is_favorited(self, user_id: int, resource_id: str) -> bool:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM resource_favorites WHERE user_id = ? AND resource_id = ?', (user_id,
                resource_id))
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f'检查收藏状态失败: {e}')
            return False

    def create_folder(self, user_id: int, folder_name: str, **kwargs) -> Dict[str, Any]:
        try:
            folder_id = f"fld_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO resource_folders (
                            folder_id, user_id, folder_name, parent_id, description, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (folder_id, user_id, folder_name, kwargs.get('parent_id'),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建收藏夹: {folder_name} ({folder_id})')
                    return {'success': True, 'folder_id': folder_id, 'folder_name': folder_name}
        except Exception as e:
            logger.error(f'创建收藏夹失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_progress(self, user_id: int, resource_id: str, progress: float,
                         last_position: float = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            is_completed = 1 if progress >= 100 else 0
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO resource_progress (
                            user_id, resource_id, progress, last_position,
                            is_completed, first_view_at, last_view_at, view_count
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                        ON CONFLICT(user_id, resource_id) DO UPDATE SET
                            progress = excluded.progress,
                            last_position = COALESCE(excluded.last_position, resource_progress.last_position),
                            is_completed = MAX(is_completed, excluded.is_completed),
                            last_view_at = excluded.last_view_at,
                            view_count = view_count + 1
                    ''', (user_id, resource_id, progress, last_position,
                          is_completed, now, now))
                    conn.commit()
                    return {'success': True, 'is_completed': is_completed}
        except Exception as e:
            logger.error(f'更新学习进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_user_progress(self, user_id: int, education_type: str = None,
                           page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = '''
                    SELECT rp.*, lr.title, lr.resource_type, lr.subject, lr.difficulty
                    FROM resource_progress rp
                    JOIN learning_resources lr ON rp.resource_id = lr.resource_id
                    WHERE rp.user_id = ?
                '''
                params = [user_id]
                if education_type:
                    query += ' AND lr.education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY rp.last_view_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                progress_list = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'progress_list': progress_list, 'total': total, 'page': page,
                'page_size': page_size}
        except Exception as e:
            logger.error(f'获取学习进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_comment(self, resource_id: str, user_id: int, content: str,
                     parent_id: int = None, user_name: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO resource_comments (
                            resource_id, user_id, user_name, content, parent_id, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (resource_id, user_id, user_name, content, parent_id, now, now))
                    comment_id = cursor.lastrowid
                    conn.commit()
                    logger.info(f'添加评论: {comment_id}')
                    return {'success': True, 'comment_id': comment_id}
        except Exception as e:
            logger.error(f'添加评论失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_comments(self, resource_id: str, page: int = 1,
                     page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT COUNT(*) as cnt FROM resource_comments
                    WHERE resource_id = ? AND is_deleted = 0 AND parent_id IS NULL
                ''', (resource_id,))
                total = cursor.fetchone()['cnt']
                cursor.execute('''
                    SELECT * FROM resource_comments
                    WHERE resource_id = ? AND is_deleted = 0 AND parent_id IS NULL
                    ORDER BY created_at DESC LIMIT ? OFFSET ?
                ''', (resource_id, page_size, (page - 1) * page_size))
                comments = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'comments': comments, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取评论列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_resource_statistics(self, resource_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT view_count, download_count, favorite_count, quality_rating, rating_count
                    FROM learning_resources WHERE resource_id = ?
                ''', (resource_id,))
                row = cursor.fetchone()
                if row:
                    cursor.execute('SELECT COUNT(*) FROM resource_progress WHERE resource_id = ? AND is_completed = 1',
                    (resource_id,))
                    completed_count = cursor.fetchone()[0]
                    cursor.execute('SELECT AVG(progress) FROM resource_progress WHERE resource_id = ?', (resource_id,))
                    avg_progress = cursor.fetchone()[0] or 0
                    return {
                        'success': True,
                        'stats': {
                            'view_count': row[0],
                            'download_count': row[1],
                            'favorite_count': row[2],
                            'quality_rating': row[3],
                            'rating_count': row[4],
                            'completed_count': completed_count,
                            'average_progress': round(avg_progress, 2)
                        }
                    }
                return {'success': False, 'error': '资源不存在'}
        except Exception as e:
            logger.error(f'获取资源统计失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_recommended_resources(self, education_type: str, subject: str = None,
                                   limit: int = 10) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = "SELECT * FROM learning_resources WHERE status = 'published' AND education_type = ?"
                params = [education_type]
                if subject:
                    query += ' AND subject = ?'
                    params.append(subject)
                query += ' ORDER BY (quality_rating * 0.4 + view_count * 0.3 + favorite_count * 0.3) DESC LIMIT ?'
                params.append(limit)
                cursor.execute(query, params)
                resources = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'resources': resources, 'count': len(resources)}
        except Exception as e:
            logger.error(f'获取推荐资源失败: {e}')
            return {'success': False, 'error': str(e)}

    def delete_resource(self, resource_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE learning_resources SET status = 'deleted' WHERE resource_id = ?",
                    (resource_id,))
                    conn.commit()
                    logger.info(f'删除资源: {resource_id}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'删除资源失败: {e}')
            return {'success': False, 'error': str(e)}






















