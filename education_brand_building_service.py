#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育品牌建设服务 (v15.14.0)
====================================
提供学校品牌管理、形象设计、宣传推广、品牌评估、品牌传播、
品牌保护、品牌合作、品牌活动等综合管理服务。

核心能力：
1. 品牌管理 - 品牌元素、品牌层级、品牌定位、品牌战略
2. 形象设计 - VI系统、视觉规范、标识设计、宣传物料
3. 宣传推广 - 推广渠道、营销活动、内容营销、媒体投放
4. 媒体关系 - 媒体资源、新闻发布、媒体报道、媒体监测
5. 品牌评估 - 品牌价值、评估维度、评估模型、评估报告
6. 品牌保护 - 商标注册、域名保护、版权保护、侵权维权
7. 品牌合作 - 合作洽谈、合作协议、合作执行、合作评估
8. 品牌活动 - 校庆活动、开放日、研讨会、公益活动
9. 品牌故事 - 故事创作、故事传播、故事沉淀
10. 统计分析 - 品牌数据、效果分析、趋势报告

支持教育类型：
- 成人教育 (adult)
- K12教育 (k12)
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_brand_building_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationBrand')


# ========== 品牌配置 ==========

BRAND_ELEMENTS = {
    'emblem': {'name': '校徽', 'required': True, 'description': '学校核心标识'},
    'motto': {'name': '校训', 'required': True, 'description': '学校精神理念'},
    'anthem': {'name': '校歌', 'required': False, 'description': '学校主题歌曲'},
    'uniform': {'name': '校服', 'required': False, 'description': '学生着装规范'},
    'mascot': {'name': '吉祥物', 'required': False, 'description': '学校形象代表'},
    'color': {'name': '品牌色', 'required': True, 'description': '品牌主色调'},
    'font': {'name': '品牌字体', 'required': True, 'description': '品牌标准字体'},
    'slogan': {'name': '品牌口号', 'required': True, 'description': '品牌宣传语'}
}

BRAND_LEVELS = {
    'school': {'name': '学校品牌', 'priority': 1, 'scope': '全校'},
    'faculty': {'name': '院系品牌', 'priority': 2, 'scope': '学院/系'},
    'major': {'name': '专业品牌', 'priority': 3, 'scope': '专业/学科'},
    'project': {'name': '项目品牌', 'priority': 4, 'scope': '项目/课程'},
    'activity': {'name': '活动品牌', 'priority': 5, 'scope': '活动/赛事'}
}

PROMOTION_CHANNELS = {
    'official_website': {'name': '官网', 'type': 'digital', 'cost': 'low'},
    'social_media': {'name': '社交媒体', 'type': 'digital', 'cost': 'medium'},
    'news_media': {'name': '新闻媒体', 'type': 'traditional', 'cost': 'high'},
    'short_video': {'name': '短视频', 'type': 'digital', 'cost': 'medium'},
    'live_stream': {'name': '直播', 'type': 'digital', 'cost': 'medium'},
    'exhibition': {'name': '展会', 'type': 'offline', 'cost': 'high'},
    'open_day': {'name': '校园开放日', 'type': 'offline', 'cost': 'medium'},
    'education_fair': {'name': '教育博览会', 'type': 'offline', 'cost': 'high'}
}

BRAND_ASSETS = {
    'vi_system': {'name': 'VI系统', 'category': 'design', 'format': 'pdf/ai'},
    'promotional_materials': {'name': '宣传素材', 'category': 'design', 'format': 'jpg/png/pdf'},
    'video_materials': {'name': '视频资料', 'category': 'multimedia', 'format': 'mp4/mov'},
    'image_library': {'name': '图片库', 'category': 'multimedia', 'format': 'jpg/png'},
    'press_releases': {'name': '新闻稿', 'category': 'content', 'format': 'docx/pdf'},
    'brand_stories': {'name': '品牌故事', 'category': 'content', 'format': 'txt/docx'}
}

MEDIA_TYPES = {
    'newspaper': {'name': '报纸', 'influence': 'high', 'audience': 'general'},
    'magazine': {'name': '杂志', 'influence': 'medium', 'audience': 'professional'},
    'tv': {'name': '电视台', 'influence': 'high', 'audience': 'general'},
    'radio': {'name': '电台', 'influence': 'medium', 'audience': 'general'},
    'online_media': {'name': '网络媒体', 'influence': 'medium', 'audience': 'digital'},
    'we_media': {'name': '自媒体', 'influence': 'low', 'audience': 'targeted'},
    'social_media': {'name': '社交媒体', 'influence': 'medium', 'audience': 'young'},
    'kol': {'name': 'KOL', 'influence': 'medium', 'audience': 'targeted'}
}

EVALUATION_DIMENSIONS = {
    'awareness': {'name': '知名度', 'weight': 0.15, 'description': '公众认知程度'},
    'reputation': {'name': '美誉度', 'weight': 0.15, 'description': '公众好感度'},
    'loyalty': {'name': '忠诚度', 'weight': 0.15, 'description': '师生/校友粘性'},
    'influence': {'name': '影响力', 'weight': 0.15, 'description': '行业话语权'},
    'competitiveness': {'name': '竞争力', 'weight': 0.15, 'description': '市场竞争优势'},
    'innovation': {'name': '创新力', 'weight': 0.1, 'description': '创新发展能力'},
    'social_responsibility': {'name': '社会责任', 'weight': 0.15, 'description': '公益贡献'}
}

PROTECTION_MEASURES = {
    'trademark_registration': {'name': '商标注册', 'priority': 'high', 'scope': '全国/国际'},
    'domain_protection': {'name': '域名保护', 'priority': 'high', 'scope': '主要域名'},
    'copyright_protection': {'name': '版权保护', 'priority': 'medium', 'scope': '原创作品'},
    'brand_monitoring': {'name': '品牌监测', 'priority': 'medium', 'scope': '全网'},
    'infringement_enforcement': {'name': '侵权维权', 'priority': 'high', 'scope': '法律途径'}
}

BRAND_ACTIVITIES = {
    'anniversary': {'name': '校庆', 'frequency': 'annual', 'scale': 'large'},
    'open_day': {'name': '开放日', 'frequency': 'quarterly', 'scale': 'medium'},
    'seminar': {'name': '研讨会', 'frequency': 'monthly', 'scale': 'small'},
    'forum': {'name': '论坛', 'frequency': 'quarterly', 'scale': 'large'},
    'competition': {'name': '比赛', 'frequency': 'semiannual', 'scale': 'medium'},
    'exhibition': {'name': '展览', 'frequency': 'quarterly', 'scale': 'medium'},
    'press_conference': {'name': '发布会', 'frequency': 'as_needed', 'scale': 'medium'},
    'charity': {'name': '公益活动', 'frequency': 'quarterly', 'scale': 'medium'}
}


class EducationBrandBuildingService:
    """教育品牌建设服务"""

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
                    CREATE TABLE IF NOT EXISTS brand_elements (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        school_id INTEGER NOT NULL,
                        element_type TEXT NOT NULL,
                        element_name TEXT,
                        content TEXT,
                        file_url TEXT,
                        description TEXT,
                        education_type TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS brand_identity (
                        identity_id TEXT PRIMARY KEY,
                        school_id INTEGER NOT NULL,
                        brand_level TEXT,
                        brand_name TEXT,
                        brand_slogan TEXT,
                        brand_positioning TEXT,
                        target_audience TEXT,
                        core_values TEXT,
                        education_type TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS brand_assets (
                        asset_id TEXT PRIMARY KEY,
                        school_id INTEGER NOT NULL,
                        asset_type TEXT,
                        asset_name TEXT,
                        file_url TEXT,
                        file_size INTEGER,
                        format TEXT,
                        description TEXT,
                        usage_scope TEXT,
                        education_type TEXT,
                        uploaded_by INTEGER,
                        uploaded_at TEXT,
                        is_approved INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS brand_guidelines (
                        guideline_id TEXT PRIMARY KEY,
                        school_id INTEGER NOT NULL,
                        guideline_name TEXT,
                        version TEXT,
                        content TEXT,
                        file_url TEXT,
                        applicable_level TEXT,
                        education_type TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS promotion_campaigns (
                        campaign_id TEXT PRIMARY KEY,
                        school_id INTEGER NOT NULL,
                        campaign_name TEXT,
                        campaign_type TEXT,
                        channels TEXT,
                        target_audience TEXT,
                        budget REAL DEFAULT 0,
                        start_date TEXT,
                        end_date TEXT,
                        education_type TEXT,
                        status TEXT DEFAULT 'planning',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS media_relations (
                        relation_id TEXT PRIMARY KEY,
                        school_id INTEGER NOT NULL,
                        media_name TEXT,
                        media_type TEXT,
                        contact_name TEXT,
                        contact_phone TEXT,
                        contact_email TEXT,
                        relationship_level TEXT DEFAULT 'general',
                        last_contact_date TEXT,
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS media_coverage (
                        coverage_id TEXT PRIMARY KEY,
                        school_id INTEGER NOT NULL,
                        media_name TEXT,
                        media_type TEXT,
                        coverage_date TEXT,
                        headline TEXT,
                        content TEXT,
                        url TEXT,
                        coverage_type TEXT,
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS brand_evaluations (
                        evaluation_id TEXT PRIMARY KEY,
                        school_id INTEGER NOT NULL,
                        evaluation_name TEXT,
                        evaluation_period TEXT,
                        dimensions TEXT,
                        methodology TEXT,
                        education_type TEXT,
                        status TEXT DEFAULT 'planning',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS evaluation_results (
                        result_id TEXT PRIMARY KEY,
                        evaluation_id TEXT NOT NULL,
                        dimension TEXT,
                        score REAL,
                        weight REAL,
                        weighted_score REAL,
                        comment TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS brand_protection (
                        protection_id TEXT PRIMARY KEY,
                        school_id INTEGER NOT NULL,
                        protection_type TEXT,
                        protection_name TEXT,
                        status TEXT DEFAULT 'pending',
                        registration_number TEXT,
                        registration_date TEXT,
                        expiration_date TEXT,
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS trademark_records (
                        record_id TEXT PRIMARY KEY,
                        protection_id TEXT NOT NULL,
                        trademark_name TEXT,
                        trademark_class INTEGER,
                        registration_date TEXT,
                        expiration_date TEXT,
                        status TEXT DEFAULT 'pending',
                        application_number TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS brand_collaborations (
                        collaboration_id TEXT PRIMARY KEY,
                        school_id INTEGER NOT NULL,
                        partner_name TEXT,
                        partner_type TEXT,
                        collaboration_type TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        description TEXT,
                        education_type TEXT,
                        status TEXT DEFAULT 'negotiating',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS collaboration_records (
                        record_id TEXT PRIMARY KEY,
                        collaboration_id TEXT NOT NULL,
                        activity_name TEXT,
                        activity_date TEXT,
                        description TEXT,
                        outcome TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS brand_activities (
                        activity_id TEXT PRIMARY KEY,
                        school_id INTEGER NOT NULL,
                        activity_name TEXT,
                        activity_type TEXT,
                        location TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        max_participants INTEGER DEFAULT 100,
                        registered_count INTEGER DEFAULT 0,
                        description TEXT,
                        education_type TEXT,
                        status TEXT DEFAULT 'planned',
                        cover_image TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS activity_participants (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        activity_id TEXT NOT NULL,
                        participant_id INTEGER,
                        participant_name TEXT,
                        participant_type TEXT,
                        register_time TEXT,
                        status TEXT DEFAULT 'registered',
                        attended INTEGER DEFAULT 0,
                        education_type TEXT,
                        UNIQUE(activity_id, participant_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS brand_stories (
                        story_id TEXT PRIMARY KEY,
                        school_id INTEGER NOT NULL,
                        story_title TEXT,
                        story_content TEXT,
                        story_type TEXT,
                        featured_image TEXT,
                        education_type TEXT,
                        is_published INTEGER DEFAULT 0,
                        view_count INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS brand_monitoring (
                        monitoring_id TEXT PRIMARY KEY,
                        school_id INTEGER NOT NULL,
                        monitor_type TEXT,
                        monitor_keyword TEXT,
                        source TEXT,
                        sentiment TEXT,
                        content TEXT,
                        url TEXT,
                        monitor_date TEXT,
                        education_type TEXT,
                        created_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('教育品牌建设服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 品牌管理 ==========

    def create_brand_identity(self, school_id: int, brand_name: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            identity_id = f"bid_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO brand_identity (
                            identity_id, school_id, brand_level, brand_name,
                            brand_slogan, brand_positioning, target_audience,
                            core_values, education_type, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (identity_id, school_id,
                          kwargs.get('brand_level', 'school'), brand_name,
                          kwargs.get('brand_slogan'), kwargs.get('brand_positioning'),
                          kwargs.get('target_audience'), kwargs.get('core_values'),
                          kwargs.get('education_type'), now, now))
                    conn.commit()
                    logger.info(f'创建品牌标识: {brand_name} ({identity_id})')
                    return {'success': True, 'identity_id': identity_id}
        except Exception as e:
            logger.error(f'创建品牌标识失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_brand_identity(self, identity_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    fields = []
                    params = []
                    if 'brand_name' in kwargs:
                        fields.append('brand_name = ?')
                        params.append(kwargs['brand_name'])
                    if 'brand_slogan' in kwargs:
                        fields.append('brand_slogan = ?')
                        params.append(kwargs['brand_slogan'])
                    if 'brand_positioning' in kwargs:
                        fields.append('brand_positioning = ?')
                        params.append(kwargs['brand_positioning'])
                    if 'target_audience' in kwargs:
                        fields.append('target_audience = ?')
                        params.append(kwargs['target_audience'])
                    if 'core_values' in kwargs:
                        fields.append('core_values = ?')
                        params.append(kwargs['core_values'])
                    if 'status' in kwargs:
                        fields.append('status = ?')
                        params.append(kwargs['status'])
                    if not fields:
                        return {'success': False, 'error': '未提供更新字段'}
                    fields.append('updated_at = ?')
                    params.append(now)
                    params.append(identity_id)
                    query = f'UPDATE brand_identity SET {", ".join(fields)} WHERE identity_id = ?'
                    cursor.execute(query, params)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '品牌标识不存在'}
        except Exception as e:
            logger.error(f'更新品牌标识失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_brand_element(self, school_id: int, element_type: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO brand_elements (
                            school_id, element_type, element_name, content,
                            file_url, description, education_type, is_active,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                    ''', (school_id, element_type, kwargs.get('element_name'),
                          kwargs.get('content'), kwargs.get('file_url'),
                          kwargs.get('description'), kwargs.get('education_type'),
                          now, now))
                    conn.commit()
                    logger.info(f'添加品牌元素: {element_type}')
                    return {'success': True, 'id': cursor.lastrowid}
        except Exception as e:
            logger.error(f'添加品牌元素失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_brand_elements(self, school_id: int, element_type: str = None,
                             education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM brand_elements WHERE school_id = ?'
                params = [school_id]
                if element_type:
                    query += ' AND element_type = ?'
                    params.append(element_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' ORDER BY created_at DESC'
                cursor.execute(query, params)
                elements = [dict(e) for e in cursor.fetchall()]
                return {'success': True, 'elements': elements}
        except Exception as e:
            logger.error(f'获取品牌元素列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 形象设计 ==========

    def upload_brand_asset(self, school_id: int, asset_type: str,
                            asset_name: str, **kwargs) -> Dict[str, Any]:
        try:
            asset_id = f"bas_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO brand_assets (
                            asset_id, school_id, asset_type, asset_name,
                            file_url, file_size, format, description,
                            usage_scope, education_type, uploaded_by,
                            uploaded_at, is_approved, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                    ''', (asset_id, school_id, asset_type, asset_name,
                          kwargs.get('file_url'), kwargs.get('file_size'),
                          kwargs.get('format'), kwargs.get('description'),
                          kwargs.get('usage_scope'), kwargs.get('education_type'),
                          kwargs.get('uploaded_by'), now[:10], now, now))
                    conn.commit()
                    logger.info(f'上传品牌资产: {asset_name} ({asset_id})')
                    return {'success': True, 'asset_id': asset_id}
        except Exception as e:
            logger.error(f'上传品牌资产失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_brand_asset(self, asset_id: str, approved: bool) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE brand_assets SET is_approved = ?, updated_at = ? WHERE asset_id = ?',
                                 (1 if approved else 0, now, asset_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'approved': approved}
                    return {'success': False, 'error': '品牌资产不存在'}
        except Exception as e:
            logger.error(f'审核品牌资产失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_brand_guideline(self, school_id: int, guideline_name: str,
                                **kwargs) -> Dict[str, Any]:
        try:
            guideline_id = f"bgd_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO brand_guidelines (
                            guideline_id, school_id, guideline_name, version,
                            content, file_url, applicable_level, education_type,
                            is_active, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                    ''', (guideline_id, school_id, guideline_name,
                          kwargs.get('version', '1.0'), kwargs.get('content'),
                          kwargs.get('file_url'), kwargs.get('applicable_level'),
                          kwargs.get('education_type'), now, now))
                    conn.commit()
                    logger.info(f'创建品牌规范: {guideline_name} ({guideline_id})')
                    return {'success': True, 'guideline_id': guideline_id}
        except Exception as e:
            logger.error(f'创建品牌规范失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_brand_assets(self, school_id: int, asset_type: str = None,
                           education_type: str = None, is_approved: bool = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM brand_assets WHERE school_id = ?'
                params = [school_id]
                if asset_type:
                    query += ' AND asset_type = ?'
                    params.append(asset_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if is_approved is not None:
                    query += ' AND is_approved = ?'
                    params.append(1 if is_approved else 0)
                query += ' ORDER BY uploaded_at DESC'
                cursor.execute(query, params)
                assets = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'assets': assets}
        except Exception as e:
            logger.error(f'获取品牌资产列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 宣传推广 ==========

    def create_promotion_campaign(self, school_id: int, campaign_name: str,
                                   campaign_type: str, **kwargs) -> Dict[str, Any]:
        try:
            campaign_id = f"pcm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO promotion_campaigns (
                            campaign_id, school_id, campaign_name, campaign_type,
                            channels, target_audience, budget, start_date,
                            end_date, education_type, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'planning', ?, ?)
                    ''', (campaign_id, school_id, campaign_name, campaign_type,
                          kwargs.get('channels'), kwargs.get('target_audience'),
                          kwargs.get('budget', 0), kwargs.get('start_date'),
                          kwargs.get('end_date'), kwargs.get('education_type'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建推广活动: {campaign_name} ({campaign_id})')
                    return {'success': True, 'campaign_id': campaign_id}
        except Exception as e:
            logger.error(f'创建推广活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_campaign_status(self, campaign_id: str, status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            valid_statuses = ['planning', 'active', 'completed', 'cancelled']
            if status not in valid_statuses:
                return {'success': False, 'error': f'无效状态，可选值: {valid_statuses}'}
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE promotion_campaigns SET status = ?, updated_at = ? WHERE campaign_id = ?',
                                 (status, now, campaign_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '推广活动不存在'}
        except Exception as e:
            logger.error(f'更新推广活动状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_promotion_channel(self, campaign_id: str, channel: str) -> Dict[str, Any]:
        try:
            if channel not in PROMOTION_CHANNELS:
                return {'success': False, 'error': f'无效渠道，可选值: {list(PROMOTION_CHANNELS.keys())}'}
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT channels FROM promotion_campaigns WHERE campaign_id = ?', (campaign_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '推广活动不存在'}
                    current_channels = json.loads(row[0]) if row[0] else []
                    if channel not in current_channels:
                        current_channels.append(channel)
                        cursor.execute('UPDATE promotion_campaigns SET channels = ? WHERE campaign_id = ?',
                                     (json.dumps(current_channels), campaign_id))
                        conn.commit()
                        return {'success': True, 'channels': current_channels}
                    return {'success': False, 'error': '渠道已存在'}
        except Exception as e:
            logger.error(f'添加推广渠道失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_promotion_campaigns(self, school_id: int, status: str = None,
                                  education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM promotion_campaigns WHERE school_id = ?'
                params = [school_id]
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' ORDER BY created_at DESC'
                cursor.execute(query, params)
                campaigns = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'campaigns': campaigns}
        except Exception as e:
            logger.error(f'获取推广活动列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 媒体关系 ==========

    def add_media_relation(self, school_id: int, media_name: str,
                            media_type: str, **kwargs) -> Dict[str, Any]:
        try:
            relation_id = f"mrl_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO media_relations (
                            relation_id, school_id, media_name, media_type,
                            contact_name, contact_phone, contact_email,
                            relationship_level, last_contact_date, education_type,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (relation_id, school_id, media_name, media_type,
                          kwargs.get('contact_name'), kwargs.get('contact_phone'),
                          kwargs.get('contact_email'), kwargs.get('relationship_level', 'general'),
                          kwargs.get('last_contact_date'), kwargs.get('education_type'),
                          now, now))
                    conn.commit()
                    logger.info(f'添加媒体关系: {media_name} ({relation_id})')
                    return {'success': True, 'relation_id': relation_id}
        except Exception as e:
            logger.error(f'添加媒体关系失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_media_coverage(self, school_id: int, media_name: str,
                               headline: str, **kwargs) -> Dict[str, Any]:
        try:
            coverage_id = f"mco_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO media_coverage (
                            coverage_id, school_id, media_name, media_type,
                            coverage_date, headline, content, url,
                            coverage_type, education_type, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (coverage_id, school_id, media_name, kwargs.get('media_type'),
                          kwargs.get('coverage_date', now[:10]), headline,
                          kwargs.get('content'), kwargs.get('url'),
                          kwargs.get('coverage_type'), kwargs.get('education_type'),
                          now, now))
                    conn.commit()
                    logger.info(f'记录媒体报道: {headline} ({coverage_id})')
                    return {'success': True, 'coverage_id': coverage_id}
        except Exception as e:
            logger.error(f'记录媒体报道失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_media_relations(self, school_id: int, media_type: str = None,
                              education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM media_relations WHERE school_id = ?'
                params = [school_id]
                if media_type:
                    query += ' AND media_type = ?'
                    params.append(media_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' ORDER BY created_at DESC'
                cursor.execute(query, params)
                relations = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'relations': relations}
        except Exception as e:
            logger.error(f'获取媒体关系列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_media_coverage(self, school_id: int, media_type: str = None,
                             education_type: str = None, coverage_date: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM media_coverage WHERE school_id = ?'
                params = [school_id]
                if media_type:
                    query += ' AND media_type = ?'
                    params.append(media_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if coverage_date:
                    query += ' AND coverage_date = ?'
                    params.append(coverage_date)
                query += ' ORDER BY coverage_date DESC'
                cursor.execute(query, params)
                coverage = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'coverage': coverage}
        except Exception as e:
            logger.error(f'获取媒体报道列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 品牌评估 ==========

    def create_brand_evaluation(self, school_id: int, evaluation_name: str,
                                 **kwargs) -> Dict[str, Any]:
        try:
            evaluation_id = f"bev_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            dimensions = kwargs.get('dimensions', json.dumps(list(EVALUATION_DIMENSIONS.keys())))
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO brand_evaluations (
                            evaluation_id, school_id, evaluation_name,
                            evaluation_period, dimensions, methodology,
                            education_type, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'planning', ?, ?)
                    ''', (evaluation_id, school_id, evaluation_name,
                          kwargs.get('evaluation_period'), dimensions,
                          kwargs.get('methodology'), kwargs.get('education_type'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建品牌评估: {evaluation_name} ({evaluation_id})')
                    return {'success': True, 'evaluation_id': evaluation_id}
        except Exception as e:
            logger.error(f'创建品牌评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_evaluation_result(self, evaluation_id: str, dimension: str,
                                  score: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            dim_config = EVALUATION_DIMENSIONS.get(dimension)
            if not dim_config:
                return {'success': False, 'error': f'无效评估维度，可选值: {list(EVALUATION_DIMENSIONS.keys())}'}
            weight = kwargs.get('weight', dim_config.get('weight', 0.15))
            weighted_score = score * weight
            result_id = f"ers_{uuid.uuid4().hex[:12]}"
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO evaluation_results (
                            result_id, evaluation_id, dimension, score,
                            weight, weighted_score, comment, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (result_id, evaluation_id, dimension, score,
                          weight, weighted_score, kwargs.get('comment'), now))
                    conn.commit()
                    return {'success': True, 'result_id': result_id, 'weighted_score': weighted_score}
        except Exception as e:
            logger.error(f'记录评估结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def calculate_brand_score(self, evaluation_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT SUM(weighted_score), COUNT(*) FROM evaluation_results WHERE evaluation_id = ?', (evaluation_id,))
                result = cursor.fetchone()
                if not result or not result[1]:
                    return {'success': False, 'error': '暂无评估结果'}
                total_score = round(result[0], 2) if result[0] else 0
                dimension_count = result[1]
                cursor.execute('UPDATE brand_evaluations SET status = ? WHERE evaluation_id = ?', ('completed', evaluation_id))
                conn.commit()
                return {'success': True, 'brand_score': total_score, 'dimension_count': dimension_count}
        except Exception as e:
            logger.error(f'计算品牌得分失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_evaluation_report(self, evaluation_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM brand_evaluations WHERE evaluation_id = ?', (evaluation_id,))
                evaluation = cursor.fetchone()
                if not evaluation:
                    return {'success': False, 'error': '评估不存在'}
                cursor.execute('SELECT * FROM evaluation_results WHERE evaluation_id = ?', (evaluation_id,))
                results = [dict(r) for r in cursor.fetchall()]
                return {
                    'success': True,
                    'evaluation': dict(evaluation),
                    'results': results,
                    'total_score': round(sum(r['weighted_score'] for r in results), 2) if results else 0
                }
        except Exception as e:
            logger.error(f'获取评估报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_brand_evaluations(self, school_id: int, status: str = None,
                                education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM brand_evaluations WHERE school_id = ?'
                params = [school_id]
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' ORDER BY created_at DESC'
                cursor.execute(query, params)
                evaluations = [dict(e) for e in cursor.fetchall()]
                return {'success': True, 'evaluations': evaluations}
        except Exception as e:
            logger.error(f'获取品牌评估列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 品牌保护 ==========

    def create_protection_record(self, school_id: int, protection_type: str,
                                  protection_name: str, **kwargs) -> Dict[str, Any]:
        try:
            protection_id = f"bpr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO brand_protection (
                            protection_id, school_id, protection_type,
                            protection_name, status, registration_number,
                            registration_date, expiration_date, education_type,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, ?, ?, ?)
                    ''', (protection_id, school_id, protection_type, protection_name,
                          kwargs.get('registration_number'), kwargs.get('registration_date'),
                          kwargs.get('expiration_date'), kwargs.get('education_type'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建品牌保护记录: {protection_name} ({protection_id})')
                    return {'success': True, 'protection_id': protection_id}
        except Exception as e:
            logger.error(f'创建品牌保护记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_trademark_record(self, protection_id: str, trademark_name: str,
                              trademark_class: int, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"tmr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT protection_id FROM brand_protection WHERE protection_id = ?', (protection_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '保护记录不存在'}
                    cursor.execute('''
                        INSERT INTO trademark_records (
                            record_id, protection_id, trademark_name,
                            trademark_class, registration_date, expiration_date,
                            status, application_number, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                    ''', (record_id, protection_id, trademark_name, trademark_class,
                          kwargs.get('registration_date'), kwargs.get('expiration_date'),
                          kwargs.get('application_number'), now))
                    conn.commit()
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'添加商标记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_protection_status(self, protection_id: str, status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            valid_statuses = ['pending', 'processing', 'approved', 'expired']
            if status not in valid_statuses:
                return {'success': False, 'error': f'无效状态，可选值: {valid_statuses}'}
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE brand_protection SET status = ?, updated_at = ? WHERE protection_id = ?',
                                 (status, now, protection_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '保护记录不存在'}
        except Exception as e:
            logger.error(f'更新保护状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_protection_records(self, school_id: int, protection_type: str = None,
                                 education_type: str = None, status: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM brand_protection WHERE school_id = ?'
                params = [school_id]
                if protection_type:
                    query += ' AND protection_type = ?'
                    params.append(protection_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                query += ' ORDER BY created_at DESC'
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records}
        except Exception as e:
            logger.error(f'获取保护记录列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 品牌合作 ==========

    def create_collaboration(self, school_id: int, partner_name: str,
                              collaboration_type: str, **kwargs) -> Dict[str, Any]:
        try:
            collaboration_id = f"bcl_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO brand_collaborations (
                            collaboration_id, school_id, partner_name,
                            partner_type, collaboration_type, start_date,
                            end_date, description, education_type, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'negotiating', ?, ?)
                    ''', (collaboration_id, school_id, partner_name,
                          kwargs.get('partner_type'), collaboration_type,
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('description'), kwargs.get('education_type'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建品牌合作: {partner_name} ({collaboration_id})')
                    return {'success': True, 'collaboration_id': collaboration_id}
        except Exception as e:
            logger.error(f'创建品牌合作失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_collaboration_status(self, collaboration_id: str, status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            valid_statuses = ['negotiating', 'active', 'completed', 'terminated']
            if status not in valid_statuses:
                return {'success': False, 'error': f'无效状态，可选值: {valid_statuses}'}
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE brand_collaborations SET status = ?, updated_at = ? WHERE collaboration_id = ?',
                                 (status, now, collaboration_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '合作记录不存在'}
        except Exception as e:
            logger.error(f'更新合作状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_collaboration_record(self, collaboration_id: str, activity_name: str,
                                  activity_date: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"clr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT collaboration_id FROM brand_collaborations WHERE collaboration_id = ?', (collaboration_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '合作记录不存在'}
                    cursor.execute('''
                        INSERT INTO collaboration_records (
                            record_id, collaboration_id, activity_name,
                            activity_date, description, outcome, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (record_id, collaboration_id, activity_name, activity_date,
                          kwargs.get('description'), kwargs.get('outcome'), now))
                    conn.commit()
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'添加合作记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_collaborations(self, school_id: int, collaboration_type: str = None,
                             education_type: str = None, status: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM brand_collaborations WHERE school_id = ?'
                params = [school_id]
                if collaboration_type:
                    query += ' AND collaboration_type = ?'
                    params.append(collaboration_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                query += ' ORDER BY created_at DESC'
                cursor.execute(query, params)
                collaborations = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'collaborations': collaborations}
        except Exception as e:
            logger.error(f'获取合作列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 品牌活动 ==========

    def create_brand_activity(self, school_id: int, activity_name: str,
                               activity_type: str, **kwargs) -> Dict[str, Any]:
        try:
            activity_id = f"bav_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO brand_activities (
                            activity_id, school_id, activity_name,
                            activity_type, location, start_date, end_date,
                            start_time, end_time, max_participants,
                            registered_count, description, education_type,
                            status, cover_image, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, 'planned', ?, ?, ?)
                    ''', (activity_id, school_id, activity_name, activity_type,
                          kwargs.get('location'), kwargs.get('start_date'),
                          kwargs.get('end_date'), kwargs.get('start_time', '09:00'),
                          kwargs.get('end_time', '17:00'), kwargs.get('max_participants', 100),
                          kwargs.get('description'), kwargs.get('education_type'),
                          kwargs.get('cover_image'), now, now))
                    conn.commit()
                    logger.info(f'创建品牌活动: {activity_name} ({activity_id})')
                    return {'success': True, 'activity_id': activity_id}
        except Exception as e:
            logger.error(f'创建品牌活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_activity(self, activity_id: str, participant_id: int,
                           participant_name: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, registered_count, status FROM brand_activities WHERE activity_id = ?', (activity_id,))
                    activity = cursor.fetchone()
                    if not activity:
                        return {'success': False, 'error': '活动不存在'}
                    if activity[2] != 'planned':
                        return {'success': False, 'error': '活动状态不允许报名'}
                    if activity[0] and activity[1] >= activity[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('''
                        INSERT OR IGNORE INTO activity_participants (
                            activity_id, participant_id, participant_name,
                            participant_type, register_time, status
                        ) VALUES (?, ?, ?, ?, ?, 'registered')
                    ''', (activity_id, participant_id, participant_name,
                          kwargs.get('participant_type', 'student'), now))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE brand_activities SET registered_count = registered_count + 1, updated_at = ? WHERE activity_id = ?', (now, activity_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已报名该活动'}
        except Exception as e:
            logger.error(f'活动报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_activity_status(self, activity_id: str, status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            valid_statuses = ['planned', 'active', 'completed', 'cancelled']
            if status not in valid_statuses:
                return {'success': False, 'error': f'无效状态，可选值: {valid_statuses}'}
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE brand_activities SET status = ?, updated_at = ? WHERE activity_id = ?',
                                 (status, now, activity_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '活动不存在'}
        except Exception as e:
            logger.error(f'更新活动状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_brand_activities(self, school_id: int, activity_type: str = None,
                               education_type: str = None, status: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM brand_activities WHERE school_id = ?'
                params = [school_id]
                if activity_type:
                    query += ' AND activity_type = ?'
                    params.append(activity_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                query += ' ORDER BY start_date DESC'
                cursor.execute(query, params)
                activities = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'activities': activities}
        except Exception as e:
            logger.error(f'获取品牌活动列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 品牌故事 ==========

    def create_brand_story(self, school_id: int, story_title: str,
                            story_content: str, **kwargs) -> Dict[str, Any]:
        try:
            story_id = f"bst_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO brand_stories (
                            story_id, school_id, story_title, story_content,
                            story_type, featured_image, education_type,
                            is_published, view_count, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?)
                    ''', (story_id, school_id, story_title, story_content,
                          kwargs.get('story_type', 'culture'),
                          kwargs.get('featured_image'), kwargs.get('education_type'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建品牌故事: {story_title} ({story_id})')
                    return {'success': True, 'story_id': story_id}
        except Exception as e:
            logger.error(f'创建品牌故事失败: {e}')
            return {'success': False, 'error': str(e)}

    def publish_brand_story(self, story_id: str, published: bool) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE brand_stories SET is_published = ?, updated_at = ? WHERE story_id = ?',
                                 (1 if published else 0, now, story_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'published': published}
                    return {'success': False, 'error': '品牌故事不存在'}
        except Exception as e:
            logger.error(f'发布品牌故事失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_brand_stories(self, school_id: int, story_type: str = None,
                            education_type: str = None, is_published: bool = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM brand_stories WHERE school_id = ?'
                params = [school_id]
                if story_type:
                    query += ' AND story_type = ?'
                    params.append(story_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if is_published is not None:
                    query += ' AND is_published = ?'
                    params.append(1 if is_published else 0)
                query += ' ORDER BY created_at DESC'
                cursor.execute(query, params)
                stories = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'stories': stories}
        except Exception as e:
            logger.error(f'获取品牌故事列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 ==========

    def get_brand_statistics(self, school_id: int, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                where_clause = 'WHERE school_id = ?'
                params = [school_id]
                if education_type:
                    where_clause += ' AND education_type = ?'
                    params.append(education_type)

                cursor.execute(f'SELECT COUNT(*) FROM brand_elements {where_clause}', params)
                element_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM brand_activities {where_clause}', params)
                activity_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM promotion_campaigns {where_clause}', params)
                campaign_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM media_coverage {where_clause}', params)
                coverage_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM brand_evaluations {where_clause}', params)
                evaluation_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM brand_protection {where_clause}', params)
                protection_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM brand_collaborations {where_clause}', params)
                collaboration_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM brand_stories WHERE school_id = ? {"" if education_type else ""}',
                              [school_id] + ([education_type] if education_type else []))
                story_count = cursor.fetchone()[0]

                return {
                    'success': True,
                    'school_id': school_id,
                    'education_type': education_type,
                    'statistics': {
                        'brand_elements': element_count,
                        'brand_activities': activity_count,
                        'promotion_campaigns': campaign_count,
                        'media_coverage': coverage_count,
                        'brand_evaluations': evaluation_count,
                        'brand_protection': protection_count,
                        'brand_collaborations': collaboration_count,
                        'brand_stories': story_count
                    }
                }
        except Exception as e:
            logger.error(f'获取品牌统计失败: {e}')
            return {'success': False, 'error': str(e)}