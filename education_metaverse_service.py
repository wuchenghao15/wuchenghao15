#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育元宇宙服务 (v15.16.0)
================================
提供虚拟校园、沉浸式学习、VR/AR教育、虚拟实验、数字孪生、元宇宙社交、虚拟活动、数字藏品等综合管理服务。

核心能力：
1. 虚拟空间 - 虚拟校园/教室/实验室/图书馆/博物馆/运动场/会议室/演播室
2. 沉浸内容 - 虚拟课程/实验/场景/人物/物品/活动/展览/竞赛
3. 虚拟实验 - 实验管理/会话管理/数据采集/结果分析
4. VR/AR设备 - 设备管理/使用记录/状态监控/维护管理
5. 元宇宙社交 - 虚拟社交/会议/协作/展示/互动/角色扮演
6. 虚拟活动 - 课堂/讲座/会议/展览/比赛/庆典/研学/招聘
7. 数字藏品 - 虚拟证书/徽章/奖杯/纪念品/艺术品/道具
8. 数字孪生 - 孪生建模/数据同步/仿真分析/决策支持
9. 用户头像 - 头像创建/自定义/换装/社交展示
10. 统计分析 - 综合数据统计与报表生成

支持教育类型：成人教育、K12教育
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_metaverse_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationMetaverse')


# ========== 元宇宙配置 ==========

VIRTUAL_SPACES = {
    'campus': {'name': '虚拟校园', 'capacity': 10000, 'education_types': ['adult', 'k12']},
    'classroom': {'name': '虚拟教室', 'capacity': 60, 'education_types': ['adult', 'k12']},
    'laboratory': {'name': '虚拟实验室', 'capacity': 30, 'education_types': ['adult', 'k12']},
    'library': {'name': '虚拟图书馆', 'capacity': 500, 'education_types': ['adult', 'k12']},
    'museum': {'name': '虚拟博物馆', 'capacity': 2000, 'education_types': ['adult', 'k12']},
    'playground': {'name': '虚拟运动场', 'capacity': 5000, 'education_types': ['k12']},
    'meeting_room': {'name': '虚拟会议室', 'capacity': 50, 'education_types': ['adult', 'k12']},
    'studio': {'name': '虚拟演播室', 'capacity': 100, 'education_types': ['adult', 'k12']}
}

IMMERSIVE_TYPES = {
    'vr': {'name': 'VR沉浸', 'requires_headset': True, 'education_types': ['adult', 'k12']},
    'ar': {'name': 'AR增强', 'requires_headset': False, 'education_types': ['adult', 'k12']},
    'mr': {'name': 'MR混合', 'requires_headset': True, 'education_types': ['adult', 'k12']},
    'panorama360': {'name': '360全景', 'requires_headset': False, 'education_types': ['adult', 'k12']},
    'simulation': {'name': '虚拟仿真', 'requires_headset': False, 'education_types': ['adult', 'k12']},
    'digital_twin': {'name': '数字孪生', 'requires_headset': False, 'education_types': ['adult', 'k12']}
}

DEVICE_TYPES = {
    'vr_headset': {'name': 'VR头显', 'category': 'headset', 'education_types': ['adult', 'k12']},
    'ar_glasses': {'name': 'AR眼镜', 'category': 'headset', 'education_types': ['adult', 'k12']},
    'mr_device': {'name': 'MR设备', 'category': 'headset', 'education_types': ['adult', 'k12']},
    '3d_display': {'name': '3D显示器', 'category': 'display', 'education_types': ['adult', 'k12']},
    'motion_sensor': {'name': '体感设备', 'category': 'sensor', 'education_types': ['adult', 'k12']},
    'tracking_device': {'name': '追踪设备', 'category': 'sensor', 'education_types': ['adult', 'k12']},
    'interaction_device': {'name': '交互设备', 'category': 'input', 'education_types': ['adult', 'k12']}
}

CONTENT_TYPES = {
    'virtual_course': {'name': '虚拟课程', 'duration': 90, 'education_types': ['adult', 'k12']},
    'virtual_experiment': {'name': '虚拟实验', 'duration': 60, 'education_types': ['adult', 'k12']},
    'virtual_scene': {'name': '虚拟场景', 'duration': 30, 'education_types': ['adult', 'k12']},
    'virtual_character': {'name': '虚拟人物', 'duration': 0, 'education_types': ['adult', 'k12']},
    'virtual_item': {'name': '虚拟物品', 'duration': 0, 'education_types': ['adult', 'k12']},
    'virtual_activity': {'name': '虚拟活动', 'duration': 120, 'education_types': ['adult', 'k12']},
    'virtual_exhibition': {'name': '虚拟展览', 'duration': 180, 'education_types': ['adult', 'k12']},
    'virtual_competition': {'name': '虚拟竞赛', 'duration': 240, 'education_types': ['adult', 'k12']}
}

SOCIAL_FEATURES = {
    'virtual_social': {'name': '虚拟社交', 'max_users': 100, 'education_types': ['adult', 'k12']},
    'virtual_meeting': {'name': '虚拟会议', 'max_users': 50, 'education_types': ['adult']},
    'virtual_collaboration': {'name': '虚拟协作', 'max_users': 20, 'education_types': ['adult', 'k12']},
    'virtual_showcase': {'name': '虚拟展示', 'max_users': 500, 'education_types': ['adult', 'k12']},
    'virtual_interaction': {'name': '虚拟互动', 'max_users': 200, 'education_types': ['adult', 'k12']},
    'virtual_roleplay': {'name': '虚拟角色扮演', 'max_users': 30, 'education_types': ['k12']}
}

ACTIVITY_TYPES = {
    'virtual_class': {'name': '虚拟课堂', 'duration': 45, 'education_types': ['adult', 'k12']},
    'virtual_lecture': {'name': '虚拟讲座', 'duration': 90, 'education_types': ['adult', 'k12']},
    'virtual_conference': {'name': '虚拟会议', 'duration': 60, 'education_types': ['adult']},
    'virtual_exhibition': {'name': '虚拟展览', 'duration': 180, 'education_types': ['adult', 'k12']},
    'virtual_competition': {'name': '虚拟比赛', 'duration': 120, 'education_types': ['adult', 'k12']},
    'virtual_celebration': {'name': '虚拟庆典', 'duration': 240, 'education_types': ['adult', 'k12']},
    'virtual_study_tour': {'name': '虚拟研学', 'duration': 480, 'education_types': ['k12']},
    'virtual_recruitment': {'name': '虚拟招聘', 'duration': 360, 'education_types': ['adult']}
}

DIGITAL_ASSET_TYPES = {
    'virtual_certificate': {'name': '虚拟证书', 'rarity': 'common', 'education_types': ['adult', 'k12']},
    'virtual_badge': {'name': '虚拟徽章', 'rarity': 'common', 'education_types': ['adult', 'k12']},
    'virtual_trophy': {'name': '虚拟奖杯', 'rarity': 'rare', 'education_types': ['adult', 'k12']},
    'virtual_souvenir': {'name': '虚拟纪念品', 'rarity': 'uncommon', 'education_types': ['adult', 'k12']},
    'virtual_artwork': {'name': '虚拟艺术品', 'rarity': 'legendary', 'education_types': ['adult', 'k12']},
    'virtual_item': {'name': '虚拟道具', 'rarity': 'common', 'education_types': ['adult', 'k12']}
}

PLATFORM_TYPES = {
    'self_hosted': {'name': '自建平台', 'scalability': 'high', 'education_types': ['adult', 'k12']},
    'third_party': {'name': '第三方平台', 'scalability': 'medium', 'education_types': ['adult', 'k12']},
    'hybrid': {'name': '混合平台', 'scalability': 'high', 'education_types': ['adult', 'k12']},
    'open_platform': {'name': '开放平台', 'scalability': 'medium', 'education_types': ['adult', 'k12']}
}


class EducationMetaverseService:
    """教育元宇宙服务"""

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
                    CREATE TABLE IF NOT EXISTS virtual_spaces (
                        space_id TEXT PRIMARY KEY,
                        space_name TEXT NOT NULL,
                        space_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        capacity INTEGER DEFAULT 100,
                        current_users INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'available',
                        description TEXT,
                        scene_url TEXT,
                        thumbnail_url TEXT,
                        creator_id INTEGER,
                        creator_name TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS space_configurations (
                        config_id TEXT PRIMARY KEY,
                        space_id TEXT NOT NULL,
                        config_key TEXT NOT NULL,
                        config_value TEXT,
                        created_at TEXT,
                        UNIQUE(space_id, config_key)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS immersive_content (
                        content_id TEXT PRIMARY KEY,
                        content_name TEXT NOT NULL,
                        content_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        immersive_type TEXT,
                        duration INTEGER DEFAULT 0,
                        description TEXT,
                        scene_url TEXT,
                        thumbnail_url TEXT,
                        file_size INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'draft',
                        creator_id INTEGER,
                        creator_name TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS content_assets (
                        asset_id TEXT PRIMARY KEY,
                        content_id TEXT NOT NULL,
                        asset_name TEXT,
                        asset_type TEXT,
                        file_url TEXT,
                        file_size INTEGER DEFAULT 0,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS virtual_experiments (
                        experiment_id TEXT PRIMARY KEY,
                        experiment_name TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        subject TEXT,
                        grade_level INTEGER,
                        description TEXT,
                        duration INTEGER DEFAULT 60,
                        equipment_requirements TEXT,
                        safety_notes TEXT,
                        status TEXT DEFAULT 'draft',
                        creator_id INTEGER,
                        creator_name TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS experiment_sessions (
                        session_id TEXT PRIMARY KEY,
                        experiment_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        education_type TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        duration INTEGER DEFAULT 0,
                        data_collected TEXT,
                        results TEXT,
                        status TEXT DEFAULT 'running',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS vr_ar_devices (
                        device_id TEXT PRIMARY KEY,
                        device_name TEXT NOT NULL,
                        device_type TEXT NOT NULL,
                        education_type TEXT,
                        serial_number TEXT,
                        status TEXT DEFAULT 'available',
                        location TEXT,
                        last_maintenance TEXT,
                        next_maintenance TEXT,
                        assigned_user_id INTEGER,
                        assigned_user_name TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS device_usage (
                        usage_id TEXT PRIMARY KEY,
                        device_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        duration INTEGER DEFAULT 0,
                        usage_type TEXT,
                        content_id TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS virtual_social (
                        social_id TEXT PRIMARY KEY,
                        social_name TEXT NOT NULL,
                        social_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        max_users INTEGER DEFAULT 100,
                        current_users INTEGER DEFAULT 0,
                        description TEXT,
                        scene_url TEXT,
                        status TEXT DEFAULT 'available',
                        creator_id INTEGER,
                        creator_name TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS social_sessions (
                        session_id TEXT PRIMARY KEY,
                        social_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        education_type TEXT,
                        avatar_id TEXT,
                        join_time TEXT,
                        leave_time TEXT,
                        duration INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS virtual_events (
                        event_id TEXT PRIMARY KEY,
                        event_name TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        description TEXT,
                        location TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        max_participants INTEGER DEFAULT 100,
                        registered_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'scheduled',
                        cover_image TEXT,
                        organizer_id INTEGER,
                        organizer_name TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS event_participants (
                        participant_id TEXT PRIMARY KEY,
                        event_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        education_type TEXT,
                        avatar_id TEXT,
                        register_time TEXT,
                        status TEXT DEFAULT 'registered',
                        attended INTEGER DEFAULT 0,
                        created_at TEXT,
                        UNIQUE(event_id, user_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS digital_collectibles (
                        collectible_id TEXT PRIMARY KEY,
                        collectible_name TEXT NOT NULL,
                        collectible_type TEXT NOT NULL,
                        education_type TEXT,
                        rarity TEXT DEFAULT 'common',
                        description TEXT,
                        image_url TEXT,
                        metadata TEXT,
                        supply INTEGER DEFAULT 1,
                        issued INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        issuer_id INTEGER,
                        issuer_name TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS collectible_ownership (
                        ownership_id TEXT PRIMARY KEY,
                        collectible_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        education_type TEXT,
                        acquire_time TEXT,
                        acquire_method TEXT,
                        status TEXT DEFAULT 'owned',
                        created_at TEXT,
                        UNIQUE(collectible_id, user_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS digital_twin (
                        twin_id TEXT PRIMARY KEY,
                        twin_name TEXT NOT NULL,
                        education_type TEXT,
                        entity_type TEXT,
                        description TEXT,
                        model_url TEXT,
                        status TEXT DEFAULT 'syncing',
                        sync_interval INTEGER DEFAULT 60,
                        creator_id INTEGER,
                        creator_name TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS twin_data (
                        data_id TEXT PRIMARY KEY,
                        twin_id TEXT NOT NULL,
                        data_type TEXT,
                        data_value TEXT,
                        timestamp TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_avatars (
                        avatar_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        education_type TEXT,
                        avatar_name TEXT NOT NULL,
                        avatar_type TEXT DEFAULT 'human',
                        appearance TEXT,
                        accessories TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT,
                        UNIQUE(user_id, avatar_name)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS avatar_customization (
                        customization_id TEXT PRIMARY KEY,
                        avatar_id TEXT NOT NULL,
                        customization_type TEXT,
                        item_name TEXT,
                        item_value TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS metaverse_logs (
                        log_id TEXT PRIMARY KEY,
                        log_type TEXT,
                        user_id INTEGER,
                        user_name TEXT,
                        education_type TEXT,
                        action TEXT,
                        target_id TEXT,
                        target_type TEXT,
                        details TEXT,
                        timestamp TEXT,
                        created_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('教育元宇宙服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 虚拟空间 ==========

    def create_virtual_space(self, space_name: str, space_type: str,
                             education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            if education_type not in ['adult', 'k12']:
                return {'success': False, 'error': '教育类型无效'}
            config = VIRTUAL_SPACES.get(space_type)
            if not config:
                return {'success': False, 'error': '虚拟空间类型无效'}
            if education_type not in config.get('education_types', []):
                return {'success': False, 'error': f'{config["name"]}不支持{education_type}教育'}
            space_id = f"vsp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO virtual_spaces (
                            space_id, space_name, space_type, education_type,
                            capacity, current_users, status, description,
                            scene_url, thumbnail_url, creator_id, creator_name,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 0, 'available', ?, ?, ?, ?, ?, ?, ?)
                    ''', (space_id, space_name, space_type, education_type,
                          kwargs.get('capacity', config.get('capacity', 100)),
                          kwargs.get('description'), kwargs.get('scene_url'),
                          kwargs.get('thumbnail_url'), kwargs.get('creator_id'),
                          kwargs.get('creator_name'), now, now))
                    conn.commit()
                    logger.info(f'创建虚拟空间: {space_name} ({space_id})')
                    return {'success': True, 'space_id': space_id}
        except Exception as e:
            logger.error(f'创建虚拟空间失败: {e}')
            return {'success': False, 'error': str(e)}

    def enter_virtual_space(self, space_id: str, user_id: int,
                            user_name: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT capacity, current_users, status, education_type FROM virtual_spaces WHERE space_id = ?', (space_id,))
                    space = cursor.fetchone()
                    if not space:
                        return {'success': False, 'error': '虚拟空间不存在'}
                    if space[2] != 'available':
                        return {'success': False, 'error': '虚拟空间不可用'}
                    if space[0] and space[1] >= space[0]:
                        return {'success': False, 'error': '虚拟空间已满'}
                    cursor.execute('UPDATE virtual_spaces SET current_users = current_users + 1, updated_at = ? WHERE space_id = ?', (now, space_id))
                    conn.commit()
                    return {'success': True, 'education_type': space[3]}
        except Exception as e:
            logger.error(f'进入虚拟空间失败: {e}')
            return {'success': False, 'error': str(e)}

    def exit_virtual_space(self, space_id: str, user_id: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT current_users FROM virtual_spaces WHERE space_id = ?', (space_id,))
                    space = cursor.fetchone()
                    if not space:
                        return {'success': False, 'error': '虚拟空间不存在'}
                    if space[0] > 0:
                        cursor.execute('UPDATE virtual_spaces SET current_users = current_users - 1, updated_at = ? WHERE space_id = ?', (now, space_id))
                        conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'退出虚拟空间失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_virtual_spaces(self, space_type: str = None, education_type: str = None,
                            page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM virtual_spaces WHERE 1=1'
                params = []
                if space_type:
                    query += ' AND space_type = ?'
                    params.append(space_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                spaces = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'spaces': spaces, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取虚拟空间列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 沉浸内容 ==========

    def create_immersive_content(self, content_name: str, content_type: str,
                                  education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            if education_type not in ['adult', 'k12']:
                return {'success': False, 'error': '教育类型无效'}
            config = CONTENT_TYPES.get(content_type)
            if not config:
                return {'success': False, 'error': '内容类型无效'}
            if education_type not in config.get('education_types', []):
                return {'success': False, 'error': f'{config["name"]}不支持{education_type}教育'}
            content_id = f"imc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO immersive_content (
                            content_id, content_name, content_type, education_type,
                            immersive_type, duration, description, scene_url,
                            thumbnail_url, file_size, status, creator_id,
                            creator_name, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?, ?)
                    ''', (content_id, content_name, content_type, education_type,
                          kwargs.get('immersive_type'),
                          kwargs.get('duration', config.get('duration', 0)),
                          kwargs.get('description'), kwargs.get('scene_url'),
                          kwargs.get('thumbnail_url'), kwargs.get('file_size', 0),
                          kwargs.get('creator_id'), kwargs.get('creator_name'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建沉浸内容: {content_name} ({content_id})')
                    return {'success': True, 'content_id': content_id}
        except Exception as e:
            logger.error(f'创建沉浸内容失败: {e}')
            return {'success': False, 'error': str(e)}

    def publish_content(self, content_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE immersive_content SET status = ?, updated_at = ? WHERE content_id = ? AND status = ?',
                                 ('published', now, content_id, 'draft'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '内容状态不允许发布'}
        except Exception as e:
            logger.error(f'发布沉浸内容失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_content_asset(self, content_id: str, asset_name: str,
                           asset_type: str, file_url: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            asset_id = f"ast_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO content_assets (
                            asset_id, content_id, asset_name, asset_type,
                            file_url, file_size, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (asset_id, content_id, asset_name, asset_type,
                          file_url, kwargs.get('file_size', 0), now))
                    conn.commit()
                    return {'success': True, 'asset_id': asset_id}
        except Exception as e:
            logger.error(f'添加内容资源失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_immersive_content(self, content_type: str = None, education_type: str = None,
                                status: str = None, page: int = 1,
                                page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM immersive_content WHERE 1=1'
                params = []
                if content_type:
                    query += ' AND content_type = ?'
                    params.append(content_type)
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
                contents = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'contents': contents, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取沉浸内容列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 虚拟实验 ==========

    def create_virtual_experiment(self, experiment_name: str, education_type: str,
                                   **kwargs) -> Dict[str, Any]:
        try:
            if education_type not in ['adult', 'k12']:
                return {'success': False, 'error': '教育类型无效'}
            experiment_id = f"vxp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO virtual_experiments (
                            experiment_id, experiment_name, education_type,
                            subject, grade_level, description, duration,
                            equipment_requirements, safety_notes, status,
                            creator_id, creator_name, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?, ?)
                    ''', (experiment_id, experiment_name, education_type,
                          kwargs.get('subject'), kwargs.get('grade_level'),
                          kwargs.get('description'), kwargs.get('duration', 60),
                          kwargs.get('equipment_requirements'),
                          kwargs.get('safety_notes'), kwargs.get('creator_id'),
                          kwargs.get('creator_name'), now, now))
                    conn.commit()
                    logger.info(f'创建虚拟实验: {experiment_name} ({experiment_id})')
                    return {'success': True, 'experiment_id': experiment_id}
        except Exception as e:
            logger.error(f'创建虚拟实验失败: {e}')
            return {'success': False, 'error': str(e)}

    def start_experiment_session(self, experiment_id: str, user_id: int,
                                  user_name: str = None) -> Dict[str, Any]:
        try:
            session_id = f"exp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status, education_type FROM virtual_experiments WHERE experiment_id = ?', (experiment_id,))
                    experiment = cursor.fetchone()
                    if not experiment:
                        return {'success': False, 'error': '虚拟实验不存在'}
                    if experiment[0] != 'published':
                        return {'success': False, 'error': '实验未发布'}
                    cursor.execute('''
                        INSERT INTO experiment_sessions (
                            session_id, experiment_id, user_id, user_name,
                            education_type, start_time, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'running', ?)
                    ''', (session_id, experiment_id, user_id, user_name,
                          experiment[1], now, now))
                    conn.commit()
                    return {'success': True, 'session_id': session_id}
        except Exception as e:
            logger.error(f'开始实验会话失败: {e}')
            return {'success': False, 'error': str(e)}

    def end_experiment_session(self, session_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT start_time FROM experiment_sessions WHERE session_id = ? AND status = ?', (session_id, 'running'))
                    session = cursor.fetchone()
                    if not session:
                        return {'success': False, 'error': '会话不存在或已结束'}
                    start = datetime.fromisoformat(session[0])
                    duration = int((datetime.now() - start).total_seconds() / 60)
                    cursor.execute('''
                        UPDATE experiment_sessions SET
                            end_time = ?, duration = ?, data_collected = ?,
                            results = ?, status = 'completed'
                        WHERE session_id = ?
                    ''', (now, duration, kwargs.get('data_collected'),
                          kwargs.get('results'), session_id))
                    conn.commit()
                    return {'success': True, 'duration': duration}
        except Exception as e:
            logger.error(f'结束实验会话失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_experiment_results(self, experiment_id: str = None, user_id: int = None,
                               page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM experiment_sessions WHERE status = ?'
                params = ['completed']
                if experiment_id:
                    query += ' AND experiment_id = ?'
                    params.append(experiment_id)
                if user_id:
                    query += ' AND user_id = ?'
                    params.append(user_id)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                sessions = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'sessions': sessions, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取实验结果失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== VR/AR设备 ==========

    def register_device(self, device_name: str, device_type: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            config = DEVICE_TYPES.get(device_type)
            if not config:
                return {'success': False, 'error': '设备类型无效'}
            device_id = f"dev_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            next_maintenance = (datetime.now() + timedelta(days=30)).isoformat()[:10]
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO vr_ar_devices (
                            device_id, device_name, device_type, education_type,
                            serial_number, status, location, last_maintenance,
                            next_maintenance, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 'available', ?, NULL, ?, ?, ?)
                    ''', (device_id, device_name, device_type,
                          kwargs.get('education_type'), kwargs.get('serial_number'),
                          kwargs.get('location'), next_maintenance, now, now))
                    conn.commit()
                    logger.info(f'注册设备: {device_name} ({device_id})')
                    return {'success': True, 'device_id': device_id}
        except Exception as e:
            logger.error(f'注册设备失败: {e}')
            return {'success': False, 'error': str(e)}

    def assign_device(self, device_id: str, user_id: int,
                       user_name: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM vr_ar_devices WHERE device_id = ?', (device_id,))
                    device = cursor.fetchone()
                    if not device:
                        return {'success': False, 'error': '设备不存在'}
                    if device[0] != 'available':
                        return {'success': False, 'error': '设备不可用'}
                    cursor.execute('UPDATE vr_ar_devices SET status = ?, assigned_user_id = ?, assigned_user_name = ?, updated_at = ? WHERE device_id = ?',
                                 ('assigned', user_id, user_name, now, device_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'分配设备失败: {e}')
            return {'success': False, 'error': str(e)}

    def start_device_usage(self, device_id: str, user_id: int,
                            user_name: str = None, **kwargs) -> Dict[str, Any]:
        try:
            usage_id = f"dug_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM vr_ar_devices WHERE device_id = ?', (device_id,))
                    device = cursor.fetchone()
                    if not device:
                        return {'success': False, 'error': '设备不存在'}
                    cursor.execute('''
                        INSERT INTO device_usage (
                            usage_id, device_id, user_id, user_name,
                            start_time, usage_type, content_id, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (usage_id, device_id, user_id, user_name, now,
                          kwargs.get('usage_type'), kwargs.get('content_id'), now))
                    conn.commit()
                    return {'success': True, 'usage_id': usage_id}
        except Exception as e:
            logger.error(f'开始设备使用失败: {e}')
            return {'success': False, 'error': str(e)}

    def end_device_usage(self, usage_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT start_time, device_id FROM device_usage WHERE usage_id = ?', (usage_id,))
                    usage = cursor.fetchone()
                    if not usage:
                        return {'success': False, 'error': '使用记录不存在'}
                    start = datetime.fromisoformat(usage[0])
                    duration = int((datetime.now() - start).total_seconds() / 60)
                    cursor.execute('UPDATE device_usage SET end_time = ?, duration = ? WHERE usage_id = ?',
                                 (now, duration, usage_id))
                    cursor.execute('UPDATE vr_ar_devices SET status = ?, assigned_user_id = NULL, assigned_user_name = NULL, updated_at = ? WHERE device_id = ?',
                                 ('available', now, usage[1]))
                    conn.commit()
                    return {'success': True, 'duration': duration}
        except Exception as e:
            logger.error(f'结束设备使用失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 元宇宙社交 ==========

    def create_social_space(self, social_name: str, social_type: str,
                            education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            if education_type not in ['adult', 'k12']:
                return {'success': False, 'error': '教育类型无效'}
            config = SOCIAL_FEATURES.get(social_type)
            if not config:
                return {'success': False, 'error': '社交类型无效'}
            if education_type not in config.get('education_types', []):
                return {'success': False, 'error': f'{config["name"]}不支持{education_type}教育'}
            social_id = f"vsc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO virtual_social (
                            social_id, social_name, social_type, education_type,
                            max_users, current_users, description, scene_url,
                            status, creator_id, creator_name, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 0, ?, ?, 'available', ?, ?, ?, ?)
                    ''', (social_id, social_name, social_type, education_type,
                          kwargs.get('max_users', config.get('max_users', 100)),
                          kwargs.get('description'), kwargs.get('scene_url'),
                          kwargs.get('creator_id'), kwargs.get('creator_name'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建社交空间: {social_name} ({social_id})')
                    return {'success': True, 'social_id': social_id}
        except Exception as e:
            logger.error(f'创建社交空间失败: {e}')
            return {'success': False, 'error': str(e)}

    def join_social_session(self, social_id: str, user_id: int,
                            user_name: str = None, **kwargs) -> Dict[str, Any]:
        try:
            session_id = f"ssn_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_users, current_users, status, education_type FROM virtual_social WHERE social_id = ?', (social_id,))
                    social = cursor.fetchone()
                    if not social:
                        return {'success': False, 'error': '社交空间不存在'}
                    if social[2] != 'available':
                        return {'success': False, 'error': '社交空间不可用'}
                    if social[0] and social[1] >= social[0]:
                        return {'success': False, 'error': '社交空间已满'}
                    cursor.execute('UPDATE virtual_social SET current_users = current_users + 1, updated_at = ? WHERE social_id = ?', (now, social_id))
                    cursor.execute('''
                        INSERT INTO social_sessions (
                            session_id, social_id, user_id, user_name,
                            education_type, avatar_id, join_time, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?)
                    ''', (session_id, social_id, user_id, user_name,
                          social[3], kwargs.get('avatar_id'), now, now))
                    conn.commit()
                    return {'success': True, 'session_id': session_id}
        except Exception as e:
            logger.error(f'加入社交会话失败: {e}')
            return {'success': False, 'error': str(e)}

    def leave_social_session(self, session_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT social_id, join_time FROM social_sessions WHERE session_id = ? AND status = ?', (session_id, 'active'))
                    session = cursor.fetchone()
                    if not session:
                        return {'success': False, 'error': '会话不存在或已离开'}
                    start = datetime.fromisoformat(session[1])
                    duration = int((datetime.now() - start).total_seconds() / 60)
                    cursor.execute('UPDATE social_sessions SET leave_time = ?, duration = ?, status = ? WHERE session_id = ?',
                                 (now, duration, 'left', session_id))
                    cursor.execute('UPDATE virtual_social SET current_users = current_users - 1, updated_at = ? WHERE social_id = ?', (now, session[0]))
                    conn.commit()
                    return {'success': True, 'duration': duration}
        except Exception as e:
            logger.error(f'离开社交会话失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_social_sessions(self, social_id: str = None, user_id: int = None,
                             page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM social_sessions WHERE 1=1'
                params = []
                if social_id:
                    query += ' AND social_id = ?'
                    params.append(social_id)
                if user_id:
                    query += ' AND user_id = ?'
                    params.append(user_id)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                sessions = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'sessions': sessions, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取社交会话列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 虚拟活动 ==========

    def create_virtual_event(self, event_name: str, event_type: str,
                             education_type: str, start_date: str,
                             **kwargs) -> Dict[str, Any]:
        try:
            if education_type not in ['adult', 'k12']:
                return {'success': False, 'error': '教育类型无效'}
            config = ACTIVITY_TYPES.get(event_type)
            if not config:
                return {'success': False, 'error': '活动类型无效'}
            if education_type not in config.get('education_types', []):
                return {'success': False, 'error': f'{config["name"]}不支持{education_type}教育'}
            event_id = f"vev_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO virtual_events (
                            event_id, event_name, event_type, education_type,
                            description, location, start_date, end_date,
                            start_time, end_time, max_participants,
                            registered_count, status, cover_image,
                            organizer_id, organizer_name, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'scheduled', ?, ?, ?, ?, ?)
                    ''', (event_id, event_name, event_type, education_type,
                          kwargs.get('description'), kwargs.get('location'),
                          start_date, kwargs.get('end_date'),
                          kwargs.get('start_time', '09:00'),
                          kwargs.get('end_time', '12:00'),
                          kwargs.get('max_participants', config.get('max_users', 100)),
                          kwargs.get('cover_image'), kwargs.get('organizer_id'),
                          kwargs.get('organizer_name'), now, now))
                    conn.commit()
                    logger.info(f'创建虚拟活动: {event_name} ({event_id})')
                    return {'success': True, 'event_id': event_id}
        except Exception as e:
            logger.error(f'创建虚拟活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_event(self, event_id: str, user_id: int,
                       user_name: str = None, **kwargs) -> Dict[str, Any]:
        try:
            participant_id = f"ptc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, registered_count, status, education_type FROM virtual_events WHERE event_id = ?', (event_id,))
                    event = cursor.fetchone()
                    if not event:
                        return {'success': False, 'error': '活动不存在'}
                    if event[2] != 'scheduled':
                        return {'success': False, 'error': '活动状态不允许报名'}
                    if event[0] and event[1] >= event[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('INSERT OR IGNORE INTO event_participants (participant_id, event_id, user_id, user_name, education_type, avatar_id, register_time, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, \'registered\', ?)',
                                 (participant_id, event_id, user_id, user_name, event[3], kwargs.get('avatar_id'), now, now))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE virtual_events SET registered_count = registered_count + 1, updated_at = ? WHERE event_id = ?', (now, event_id))
                        conn.commit()
                        return {'success': True, 'participant_id': participant_id}
                    return {'success': False, 'error': '已报名该活动'}
        except Exception as e:
            logger.error(f'活动报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def attend_event(self, participant_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE event_participants SET attended = 1, status = ? WHERE participant_id = ? AND status = ?',
                                 ('attended', participant_id, 'registered'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '报名记录不存在或已签到'}
        except Exception as e:
            logger.error(f'活动签到失败: {e}')
            return {'success': False, 'error': str(e)}

    def cancel_event_registration(self, participant_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT event_id FROM event_participants WHERE participant_id = ? AND status = ?', (participant_id, 'registered'))
                    participant = cursor.fetchone()
                    if not participant:
                        return {'success': False, 'error': '报名记录不存在或已签到'}
                    cursor.execute('UPDATE event_participants SET status = ? WHERE participant_id = ?', ('cancelled', participant_id))
                    cursor.execute('UPDATE virtual_events SET registered_count = registered_count - 1, updated_at = ? WHERE event_id = ?', (now, participant[0]))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'取消活动报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_virtual_events(self, event_type: str = None, education_type: str = None,
                            status: str = None, page: int = 1,
                            page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM virtual_events WHERE 1=1'
                params = []
                if event_type:
                    query += ' AND event_type = ?'
                    params.append(event_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY start_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                events = [dict(e) for e in cursor.fetchall()]
                return {'success': True, 'events': events, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取虚拟活动列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 数字藏品 ==========

    def create_digital_collectible(self, collectible_name: str, collectible_type: str,
                                   **kwargs) -> Dict[str, Any]:
        try:
            config = DIGITAL_ASSET_TYPES.get(collectible_type)
            if not config:
                return {'success': False, 'error': '藏品类型无效'}
            collectible_id = f"dcl_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO digital_collectibles (
                            collectible_id, collectible_name, collectible_type,
                            education_type, rarity, description, image_url,
                            metadata, supply, issued, status, issuer_id,
                            issuer_name, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'active', ?, ?, ?, ?)
                    ''', (collectible_id, collectible_name, collectible_type,
                          kwargs.get('education_type'),
                          kwargs.get('rarity', config.get('rarity', 'common')),
                          kwargs.get('description'), kwargs.get('image_url'),
                          kwargs.get('metadata'), kwargs.get('supply', 1),
                          kwargs.get('issuer_id'), kwargs.get('issuer_name'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建数字藏品: {collectible_name} ({collectible_id})')
                    return {'success': True, 'collectible_id': collectible_id}
        except Exception as e:
            logger.error(f'创建数字藏品失败: {e}')
            return {'success': False, 'error': str(e)}

    def issue_collectible(self, collectible_id: str, user_id: int,
                          user_name: str = None, **kwargs) -> Dict[str, Any]:
        try:
            ownership_id = f"own_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT supply, issued, status, education_type FROM digital_collectibles WHERE collectible_id = ?', (collectible_id,))
                    collectible = cursor.fetchone()
                    if not collectible:
                        return {'success': False, 'error': '藏品不存在'}
                    if collectible[2] != 'active':
                        return {'success': False, 'error': '藏品已停用'}
                    if collectible[0] and collectible[1] >= collectible[0]:
                        return {'success': False, 'error': '藏品已发完'}
                    cursor.execute('INSERT OR IGNORE INTO collectible_ownership (ownership_id, collectible_id, user_id, user_name, education_type, acquire_time, acquire_method, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, \'owned\', ?)',
                                 (ownership_id, collectible_id, user_id, user_name, collectible[3], now, kwargs.get('acquire_method', 'issued'), now))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE digital_collectibles SET issued = issued + 1, updated_at = ? WHERE collectible_id = ?', (now, collectible_id))
                        conn.commit()
                        return {'success': True, 'ownership_id': ownership_id}
                    return {'success': False, 'error': '用户已拥有该藏品'}
        except Exception as e:
            logger.error(f'发放数字藏品失败: {e}')
            return {'success': False, 'error': str(e)}

    def transfer_collectible(self, ownership_id: str, to_user_id: int,
                             to_user_name: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT collectible_id, user_id, status FROM collectible_ownership WHERE ownership_id = ?', (ownership_id,))
                    ownership = cursor.fetchone()
                    if not ownership:
                        return {'success': False, 'error': '所有权记录不存在'}
                    if ownership[2] != 'owned':
                        return {'success': False, 'error': '藏品状态不允许转移'}
                    if ownership[1] == to_user_id:
                        return {'success': False, 'error': '不能转移给自己'}
                    cursor.execute('UPDATE collectible_ownership SET user_id = ?, user_name = ?, status = ? WHERE ownership_id = ?',
                                 (to_user_id, to_user_name, 'transferred', ownership_id))
                    new_ownership_id = f"own_{uuid.uuid4().hex[:12]}"
                    cursor.execute('INSERT INTO collectible_ownership (ownership_id, collectible_id, user_id, user_name, education_type, acquire_time, acquire_method, status, created_at) VALUES (?, ?, ?, ?, NULL, ?, ?, \'owned\', ?)',
                                 (new_ownership_id, ownership[0], to_user_id, to_user_name, now, 'transfer', now))
                    conn.commit()
                    return {'success': True, 'new_ownership_id': new_ownership_id}
        except Exception as e:
            logger.error(f'转移数字藏品失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_user_collectibles(self, user_id: int, education_type: str = None,
                               page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM collectible_ownership WHERE user_id = ? AND status = ?'
                params = [user_id, 'owned']
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY acquire_time DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                ownerships = [dict(o) for o in cursor.fetchall()]
                return {'success': True, 'collectibles': ownerships, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取用户藏品失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 数字孪生 ==========

    def create_digital_twin(self, twin_name: str, **kwargs) -> Dict[str, Any]:
        try:
            twin_id = f"dtw_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO digital_twin (
                            twin_id, twin_name, education_type, entity_type,
                            description, model_url, status, sync_interval,
                            creator_id, creator_name, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'syncing', ?, ?, ?, ?, ?)
                    ''', (twin_id, twin_name, kwargs.get('education_type'),
                          kwargs.get('entity_type'), kwargs.get('description'),
                          kwargs.get('model_url'), kwargs.get('sync_interval', 60),
                          kwargs.get('creator_id'), kwargs.get('creator_name'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建数字孪生: {twin_name} ({twin_id})')
                    return {'success': True, 'twin_id': twin_id}
        except Exception as e:
            logger.error(f'创建数字孪生失败: {e}')
            return {'success': False, 'error': str(e)}

    def sync_twin_data(self, twin_id: str, data_type: str,
                       data_value: str) -> Dict[str, Any]:
        try:
            data_id = f"twd_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM digital_twin WHERE twin_id = ?', (twin_id,))
                    twin = cursor.fetchone()
                    if not twin:
                        return {'success': False, 'error': '数字孪生不存在'}
                    cursor.execute('''
                        INSERT INTO twin_data (
                            data_id, twin_id, data_type, data_value,
                            timestamp, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (data_id, twin_id, data_type, data_value, now, now))
                    conn.commit()
                    return {'success': True, 'data_id': data_id}
        except Exception as e:
            logger.error(f'同步孪生数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_twin_data(self, twin_id: str, data_type: str = None,
                      page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM twin_data WHERE twin_id = ?'
                params = [twin_id]
                if data_type:
                    query += ' AND data_type = ?'
                    params.append(data_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                data = [dict(d) for d in cursor.fetchall()]
                return {'success': True, 'data': data, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取孪生数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_twin_status(self, twin_id: str, status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE digital_twin SET status = ?, updated_at = ? WHERE twin_id = ?',
                                 (status, now, twin_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '数字孪生不存在'}
        except Exception as e:
            logger.error(f'更新孪生状态失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 用户头像 ==========

    def create_user_avatar(self, user_id: int, avatar_name: str,
                           education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            if education_type not in ['adult', 'k12']:
                return {'success': False, 'error': '教育类型无效'}
            avatar_id = f"avt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO user_avatars (
                            avatar_id, user_id, user_name, education_type,
                            avatar_name, avatar_type, appearance, accessories,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (avatar_id, user_id, kwargs.get('user_name'), education_type,
                          avatar_name, kwargs.get('avatar_type', 'human'),
                          kwargs.get('appearance'), kwargs.get('accessories'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建用户头像: {avatar_name} ({avatar_id})')
                    return {'success': True, 'avatar_id': avatar_id}
        except sqlite3.IntegrityError:
            return {'success': False, 'error': '头像名称已存在'}
        except Exception as e:
            logger.error(f'创建用户头像失败: {e}')
            return {'success': False, 'error': str(e)}

    def customize_avatar(self, avatar_id: str, customization_type: str,
                         item_name: str, item_value: str) -> Dict[str, Any]:
        try:
            customization_id = f"cust_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM user_avatars WHERE avatar_id = ?', (avatar_id,))
                    avatar = cursor.fetchone()
                    if not avatar:
                        return {'success': False, 'error': '头像不存在'}
                    cursor.execute('''
                        INSERT INTO avatar_customization (
                            customization_id, avatar_id, customization_type,
                            item_name, item_value, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (customization_id, avatar_id, customization_type,
                          item_name, item_value, now))
                    conn.commit()
                    return {'success': True, 'customization_id': customization_id}
        except Exception as e:
            logger.error(f'自定义头像失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_avatar_appearance(self, avatar_id: str, appearance: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE user_avatars SET appearance = ?, updated_at = ? WHERE avatar_id = ?',
                                 (appearance, now, avatar_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '头像不存在'}
        except Exception as e:
            logger.error(f'更新头像外观失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_user_avatars(self, user_id: int, education_type: str = None,
                         page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM user_avatars WHERE user_id = ?'
                params = [user_id]
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                avatars = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'avatars': avatars, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取用户头像失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 ==========

    def get_metaverse_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                stats = {}
                base_query = ''
                base_params = []
                if education_type:
                    base_query = ' WHERE education_type = ?'
                    base_params = [education_type]

                cursor.execute(f'SELECT COUNT(*) FROM virtual_spaces{base_query}', base_params)
                stats['virtual_spaces_count'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM immersive_content WHERE status = ?{base_query}', ['published'] + base_params)
                stats['published_content_count'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM virtual_experiments{base_query}', base_params)
                stats['experiments_count'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM experiment_sessions WHERE status = ?', ['completed'])
                stats['completed_sessions'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM vr_ar_devices')
                stats['devices_count'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM vr_ar_devices WHERE status = ?', ['available'])
                stats['available_devices'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM virtual_social{base_query}', base_params)
                stats['social_spaces_count'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM virtual_events{base_query}', base_params)
                stats['events_count'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM digital_collectibles{base_query}', base_params)
                stats['collectibles_count'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM collectible_ownership WHERE status = ?', ['owned'])
                stats['ownership_count'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM digital_twin{base_query}', base_params)
                stats['digital_twins_count'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM user_avatars{base_query}', base_params)
                stats['avatars_count'] = cursor.fetchone()[0]

                return {'success': True, 'statistics': stats}
        except Exception as e:
            logger.error(f'获取元宇宙统计失败: {e}')
            return {'success': False, 'error': str(e)}