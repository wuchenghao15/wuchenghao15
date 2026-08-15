#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育媒体服务 (v15.27.0)
=============================
提供多媒体内容管理、视频管理、音频管理、直播服务、流媒体服务、内容分发、媒体转码、媒体存储等综合管理服务。

核心能力：
1. 多媒体内容 - 内容上传、元数据管理、内容检索、内容分类
2. 视频管理 - 视频上传、视频编辑、视频发布、视频播放
3. 音频管理 - 音频上传、音频编辑、音频发布、音频播放
4. 直播服务 - 直播创建、直播推流、直播录制、直播回放、直播互动
5. 流媒体服务 - 流媒体配置、流媒体分发、流媒体监控、流媒体统计
6. 内容分发 - CDN分发、P2P分发、智能分发、边缘分发
7. 媒体转码 - 格式转换、分辨率调整、码率控制、批量转码
8. 媒体存储 - 存储管理、存储迁移、存储备份、存储清理

支持成人教育与K12教育差异化服务。
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_media_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationMedia')


# ========== 媒体配置 ==========

MEDIA_TYPES = {
    'video': {'name': '视频', 'description': '教学视频、课程录像、微课视频'},
    'audio': {'name': '音频', 'description': '有声读物、课程音频、播客'},
    'image': {'name': '图片', 'description': '课件图片、教材插图、教学素材'},
    'document': {'name': '文档', 'description': 'PDF文档、Word文档、PPT课件'},
    'animation': {'name': '动画', 'description': '教学动画、演示动画、互动动画'},
    'interactive': {'name': '互动内容', 'description': '互动课件、在线测验、虚拟实验'},
    '3d': {'name': '3D内容', 'description': '3D模型、虚拟场景、三维展示'},
    'vr': {'name': '虚拟现实', 'description': 'VR教学、虚拟仿真、沉浸式体验'}
}

VIDEO_FORMATS = {
    'mp4': {'name': 'MP4', 'codec': 'H.264/H.265', 'container': 'MPEG-4', 'quality': 'high'},
    'mov': {'name': 'MOV', 'codec': 'ProRes/H.264', 'container': 'QuickTime', 'quality': 'high'},
    'avi': {'name': 'AVI', 'codec': 'DivX/XviD', 'container': 'AVI', 'quality': 'medium'},
    'wmv': {'name': 'WMV', 'codec': 'WMV', 'container': 'ASF', 'quality': 'medium'},
    'flv': {'name': 'FLV', 'codec': 'VP6/H.264', 'container': 'FLV', 'quality': 'low'},
    'mpeg': {'name': 'MPEG', 'codec': 'MPEG-1/MPEG-2', 'container': 'MPEG', 'quality': 'medium'},
    'webm': {'name': 'WebM', 'codec': 'VP8/VP9', 'container': 'WebM', 'quality': 'high'},
    'mkv': {'name': 'MKV', 'codec': '多种编码', 'container': 'Matroska', 'quality': 'high'}
}

AUDIO_FORMATS = {
    'mp3': {'name': 'MP3', 'bitrate': '128-320kbps', 'quality': 'high', 'compression': 'lossy'},
    'wav': {'name': 'WAV', 'bitrate': '1411kbps', 'quality': 'lossless', 'compression': 'none'},
    'ogg': {'name': 'OGG', 'bitrate': '64-500kbps', 'quality': 'high', 'compression': 'lossy'},
    'aac': {'name': 'AAC', 'bitrate': '8-500kbps', 'quality': 'high', 'compression': 'lossy'},
    'flac': {'name': 'FLAC', 'bitrate': '可变', 'quality': 'lossless', 'compression': 'lossless'},
    'wma': {'name': 'WMA', 'bitrate': '48-384kbps', 'quality': 'medium', 'compression': 'lossy'},
    'm4a': {'name': 'M4A', 'codec': 'AAC/ALAC', 'quality': 'high', 'compression': 'lossy/lossless'},
    'aiff': {'name': 'AIFF', 'codec': 'PCM', 'quality': 'lossless', 'compression': 'none'}
}

LIVE_STREAMING = {
    'teaching': {'name': '教学直播', 'description': '实时教学课堂直播'},
    'activity': {'name': '活动直播', 'description': '校园活动、庆典直播'},
    'meeting': {'name': '会议直播', 'description': '学术会议、工作会议直播'},
    'lecture': {'name': '讲座直播', 'description': '专家讲座、学术报告直播'},
    'training': {'name': '培训直播', 'description': '教师培训、技能培训直播'},
    'competition': {'name': '赛事直播', 'description': '体育赛事、学科竞赛直播'},
    'conference': {'name': '发布会', 'description': '新品发布、成果展示直播'},
    'opencourse': {'name': '公开课', 'description': '公开课程、名师讲堂直播'}
}

STREAMING_PROTOCOLS = {
    'hls': {'name': 'HLS', 'type': 'HTTP', 'latency': '2-10秒', 'quality': '高', 'compatibility': '广泛'},
    'dash': {'name': 'DASH', 'type': 'HTTP', 'latency': '1-5秒', 'quality': '高', 'compatibility': '较好'},
    'rtmp': {'name': 'RTMP', 'type': 'RTMP', 'latency': '1-3秒', 'quality': '高', 'compatibility': '受限'},
    'webrtc': {'name': 'WebRTC', 'type': 'UDP', 'latency': '<1秒', 'quality': '高', 'compatibility': '较好'},
    'http': {'name': 'HTTP', 'type': 'HTTP', 'latency': '5-15秒', 'quality': '中等', 'compatibility': '广泛'},
    'rtsp': {'name': 'RTSP', 'type': 'RTSP', 'latency': '<1秒', 'quality': '高', 'compatibility': '受限'},
    'srt': {'name': 'SRT', 'type': 'UDP', 'latency': '<1秒', 'quality': '高', 'compatibility': '中等'},
    'quic': {'name': 'QUIC', 'type': 'UDP', 'latency': '<1秒', 'quality': '高', 'compatibility': '有限'}
}

DISTRIBUTION_CHANNELS = {
    'cdn': {'name': 'CDN分发', 'description': '内容分发网络加速', 'cost': '中等', 'speed': '快'},
    'p2p': {'name': 'P2P分发', 'description': '点对点传输', 'cost': '低', 'speed': '中等'},
    'live': {'name': '直播分发', 'description': '实时直播流分发', 'cost': '高', 'speed': '快'},
    'vod': {'name': 'VOD分发', 'description': '点播内容分发', 'cost': '低', 'speed': '快'},
    'mobile': {'name': '移动端分发', 'description': '移动设备优化分发', 'cost': '中等', 'speed': '快'},
    'smart': {'name': '智能分发', 'description': 'AI智能路由分发', 'cost': '中等', 'speed': '快'},
    'edge': {'name': '边缘分发', 'description': '边缘节点加速', 'cost': '中等', 'speed': '快'},
    'global': {'name': '全球分发', 'description': '跨国内容分发', 'cost': '高', 'speed': '中等'}
}

TRANSCODING_METHODS = {
    'hardware': {'name': '硬件转码', 'speed': '极快', 'quality': '高', 'cost': '高'},
    'software': {'name': '软件转码', 'speed': '中等', 'quality': '高', 'cost': '低'},
    'cloud': {'name': '云转码', 'speed': '快', 'quality': '高', 'cost': '中等'},
    'distributed': {'name': '分布式转码', 'speed': '极快', 'quality': '高', 'cost': '中等'},
    'realtime': {'name': '实时转码', 'speed': '快', 'quality': '中等', 'cost': '高'},
    'batch': {'name': '批量转码', 'speed': '快', 'quality': '高', 'cost': '低'},
    'adaptive': {'name': '自适应转码', 'speed': '中等', 'quality': '高', 'cost': '中等'},
    'hd': {'name': '高清转码', 'speed': '中等', 'quality': '极高', 'cost': '高'}
}

STORAGE_TYPES = {
    'local': {'name': '本地存储', 'capacity': '有限', 'cost': '低', 'access_speed': '快', 'redundancy': '无'},
    'cloud': {'name': '云存储', 'capacity': '无限', 'cost': '中等', 'access_speed': '中等', 'redundancy': '高'},
    'distributed': {'name': '分布式存储', 'capacity': '无限', 'cost': '中等', 'access_speed': '快', 'redundancy': '高'},
    'object': {'name': '对象存储', 'capacity': '无限', 'cost': '低', 'access_speed': '中等', 'redundancy': '高'},
    'hot': {'name': '热存储', 'capacity': '有限', 'cost': '高', 'access_speed': '极快', 'redundancy': '中等'},
    'cold': {'name': '冷存储', 'capacity': '无限', 'cost': '极低', 'access_speed': '慢', 'redundancy': '高'},
    'archive': {'name': '归档存储', 'capacity': '无限', 'cost': '极低', 'access_speed': '极慢', 'redundancy': '高'},
    'hybrid': {'name': '混合存储', 'capacity': '无限', 'cost': '中等', 'access_speed': '快', 'redundancy': '高'}
}


class EducationMediaService:
    """教育媒体服务"""

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
                    CREATE TABLE IF NOT EXISTS media_content (
                        content_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        media_type TEXT NOT NULL,
                        file_path TEXT,
                        file_name TEXT,
                        file_size INTEGER DEFAULT 0,
                        file_format TEXT,
                        duration INTEGER DEFAULT 0,
                        thumbnail_url TEXT,
                        education_type TEXT DEFAULT 'adult',
                        grade_level TEXT,
                        subject TEXT,
                        category TEXT,
                        tags TEXT,
                        description TEXT,
                        creator_id INTEGER,
                        creator_name TEXT,
                        status TEXT DEFAULT 'uploading',
                        view_count INTEGER DEFAULT 0,
                        download_count INTEGER DEFAULT 0,
                        is_published INTEGER DEFAULT 0,
                        published_at TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS content_metadata (
                        metadata_id TEXT PRIMARY KEY,
                        content_id TEXT NOT NULL,
                        key TEXT NOT NULL,
                        value TEXT,
                        created_at TEXT,
                        FOREIGN KEY(content_id) REFERENCES media_content(content_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS video_management (
                        video_id TEXT PRIMARY KEY,
                        content_id TEXT NOT NULL,
                        video_title TEXT NOT NULL,
                        duration INTEGER DEFAULT 0,
                        resolution TEXT,
                        bitrate INTEGER DEFAULT 0,
                        codec TEXT,
                        frame_rate INTEGER DEFAULT 25,
                        aspect_ratio TEXT DEFAULT '16:9',
                        chapters TEXT,
                        subtitles TEXT,
                        thumbnails TEXT,
                        education_type TEXT DEFAULT 'adult',
                        grade_level TEXT,
                        subject TEXT,
                        is_processed INTEGER DEFAULT 0,
                        processing_status TEXT DEFAULT 'pending',
                        status TEXT DEFAULT 'draft',
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY(content_id) REFERENCES media_content(content_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS video_records (
                        record_id TEXT PRIMARY KEY,
                        video_id TEXT NOT NULL,
                        action_type TEXT,
                        user_id INTEGER,
                        user_name TEXT,
                        timestamp TEXT,
                        details TEXT,
                        FOREIGN KEY(video_id) REFERENCES video_management(video_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS audio_management (
                        audio_id TEXT PRIMARY KEY,
                        content_id TEXT NOT NULL,
                        audio_title TEXT NOT NULL,
                        duration INTEGER DEFAULT 0,
                        sample_rate INTEGER DEFAULT 44100,
                        bitrate INTEGER DEFAULT 128000,
                        channels INTEGER DEFAULT 2,
                        codec TEXT,
                        audio_format TEXT,
                        cover_image TEXT,
                        lyrics TEXT,
                        education_type TEXT DEFAULT 'adult',
                        grade_level TEXT,
                        subject TEXT,
                        is_processed INTEGER DEFAULT 0,
                        processing_status TEXT DEFAULT 'pending',
                        status TEXT DEFAULT 'draft',
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY(content_id) REFERENCES media_content(content_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS audio_records (
                        record_id TEXT PRIMARY KEY,
                        audio_id TEXT NOT NULL,
                        action_type TEXT,
                        user_id INTEGER,
                        user_name TEXT,
                        timestamp TEXT,
                        details TEXT,
                        FOREIGN KEY(audio_id) REFERENCES audio_management(audio_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS live_streaming (
                        live_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        live_type TEXT,
                        description TEXT,
                        cover_image TEXT,
                        stream_url TEXT,
                        play_url TEXT,
                        protocol TEXT DEFAULT 'hls',
                        education_type TEXT DEFAULT 'adult',
                        grade_level TEXT,
                        subject TEXT,
                        host_id INTEGER,
                        host_name TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        duration INTEGER DEFAULT 0,
                        viewer_count INTEGER DEFAULT 0,
                        max_viewers INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'scheduled',
                        is_recorded INTEGER DEFAULT 1,
                        recording_path TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS streaming_records (
                        record_id TEXT PRIMARY KEY,
                        live_id TEXT NOT NULL,
                        viewer_id INTEGER,
                        viewer_name TEXT,
                        join_time TEXT,
                        leave_time TEXT,
                        duration INTEGER DEFAULT 0,
                        FOREIGN KEY(live_id) REFERENCES live_streaming(live_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS media_streaming (
                        stream_id TEXT PRIMARY KEY,
                        content_id TEXT NOT NULL,
                        stream_name TEXT,
                        protocol TEXT,
                        quality TEXT,
                        stream_url TEXT,
                        play_url TEXT,
                        bandwidth INTEGER DEFAULT 0,
                        latency REAL DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY(content_id) REFERENCES media_content(content_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS streaming_config (
                        config_id TEXT PRIMARY KEY,
                        protocol TEXT NOT NULL,
                        quality_levels TEXT,
                        bitrate_settings TEXT,
                        buffer_size INTEGER DEFAULT 3000,
                        latency_target REAL DEFAULT 3.0,
                        transcoding_preset TEXT,
                        adaptive_bitrate INTEGER DEFAULT 1,
                        drm_enabled INTEGER DEFAULT 0,
                        watermark_enabled INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS content_distribution (
                        distribution_id TEXT PRIMARY KEY,
                        content_id TEXT NOT NULL,
                        channel TEXT NOT NULL,
                        status TEXT DEFAULT 'pending',
                        url TEXT,
                        cdn_provider TEXT,
                        edge_locations TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        bandwidth_usage INTEGER DEFAULT 0,
                        cost REAL DEFAULT 0,
                        education_type TEXT DEFAULT 'adult',
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY(content_id) REFERENCES media_content(content_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS distribution_records (
                        record_id TEXT PRIMARY KEY,
                        distribution_id TEXT NOT NULL,
                        timestamp TEXT,
                        bandwidth INTEGER DEFAULT 0,
                        requests INTEGER DEFAULT 0,
                        cache_hit REAL DEFAULT 0,
                        latency REAL DEFAULT 0,
                        FOREIGN KEY(distribution_id) REFERENCES content_distribution(distribution_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS media_transcoding (
                        transcode_id TEXT PRIMARY KEY,
                        content_id TEXT NOT NULL,
                        source_format TEXT,
                        target_format TEXT,
                        transcoding_method TEXT,
                        quality TEXT,
                        resolution TEXT,
                        bitrate INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'pending',
                        progress INTEGER DEFAULT 0,
                        error_message TEXT,
                        output_path TEXT,
                        duration INTEGER DEFAULT 0,
                        start_time TEXT,
                        end_time TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY(content_id) REFERENCES media_content(content_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS transcoding_records (
                        record_id TEXT PRIMARY KEY,
                        transcode_id TEXT NOT NULL,
                        action_type TEXT,
                        timestamp TEXT,
                        progress INTEGER DEFAULT 0,
                        details TEXT,
                        FOREIGN KEY(transcode_id) REFERENCES media_transcoding(transcode_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS media_storage (
                        storage_id TEXT PRIMARY KEY,
                        content_id TEXT NOT NULL,
                        storage_type TEXT NOT NULL,
                        bucket_name TEXT,
                        file_path TEXT,
                        file_size INTEGER DEFAULT 0,
                        checksum TEXT,
                        upload_time TEXT,
                        last_access_time TEXT,
                        replication_status TEXT DEFAULT 'pending',
                        backup_count INTEGER DEFAULT 0,
                        is_archived INTEGER DEFAULT 0,
                        archive_time TEXT,
                        education_type TEXT DEFAULT 'adult',
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY(content_id) REFERENCES media_content(content_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS storage_records (
                        record_id TEXT PRIMARY KEY,
                        storage_id TEXT NOT NULL,
                        action_type TEXT,
                        timestamp TEXT,
                        size_change INTEGER DEFAULT 0,
                        details TEXT,
                        FOREIGN KEY(storage_id) REFERENCES media_storage(storage_id)
                    )
                ''')
                conn.commit()
                logger.info('教育媒体服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 多媒体内容管理 ==========

    def upload_media_content(self, title: str, media_type: str,
                             file_name: str, **kwargs) -> Dict[str, Any]:
        try:
            content_id = f"mct_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO media_content (
                            content_id, title, media_type, file_path,
                            file_name, file_size, file_format, duration,
                            thumbnail_url, education_type, grade_level,
                            subject, category, tags, description,
                            creator_id, creator_name, status, view_count,
                            download_count, is_published, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'uploading', 0, 0, 0, ?, ?)
                    ''', (content_id, title, media_type, kwargs.get('file_path'),
                          file_name, kwargs.get('file_size', 0), kwargs.get('file_format'),
                          kwargs.get('duration', 0), kwargs.get('thumbnail_url'),
                          kwargs.get('education_type', 'adult'), kwargs.get('grade_level'),
                          kwargs.get('subject'), kwargs.get('category'),
                          json.dumps(kwargs.get('tags', [])), kwargs.get('description'),
                          kwargs.get('creator_id'), kwargs.get('creator_name'),
                          now, now))
                    conn.commit()
                    logger.info(f'上传多媒体内容: {title} ({content_id})')
                    return {'success': True, 'content_id': content_id}
        except Exception as e:
            logger.error(f'上传多媒体内容失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_media_metadata(self, content_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    for key, value in metadata.items():
                        cursor.execute('''
                            INSERT OR REPLACE INTO content_metadata (metadata_id, content_id, key, value, created_at)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (f"mmd_{uuid.uuid4().hex[:8]}", content_id, key, str(value), now))
                    cursor.execute('UPDATE media_content SET updated_at = ? WHERE content_id = ?', (now, content_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'更新媒体元数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def search_media_content(self, keyword: str = None, media_type: str = None,
                             education_type: str = None, grade_level: str = None,
                             page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM media_content WHERE 1=1'
                params = []
                if keyword:
                    query += ' AND (title LIKE ? OR description LIKE ?)'
                    params.extend([f'%{keyword}%', f'%{keyword}%'])
                if media_type:
                    query += ' AND media_type = ?'
                    params.append(media_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if grade_level:
                    query += ' AND grade_level = ?'
                    params.append(grade_level)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                contents = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'contents': contents, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'搜索媒体内容失败: {e}')
            return {'success': False, 'error': str(e)}

    def publish_media_content(self, content_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE media_content SET status = ?, is_published = 1, published_at = ?, updated_at = ? WHERE content_id = ?',
                                 ('published', now, now, content_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'发布媒体内容: {content_id}')
                        return {'success': True}
                    return {'success': False, 'error': '内容不存在'}
        except Exception as e:
            logger.error(f'发布媒体内容失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 视频管理 ==========

    def upload_video(self, video_title: str, content_id: str, **kwargs) -> Dict[str, Any]:
        try:
            video_id = f"vid_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO video_management (
                            video_id, content_id, video_title, duration,
                            resolution, bitrate, codec, frame_rate,
                            aspect_ratio, chapters, subtitles, thumbnails,
                            education_type, grade_level, subject,
                            is_processed, processing_status, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'pending', 'draft', ?, ?)
                    ''', (video_id, content_id, video_title, kwargs.get('duration', 0),
                          kwargs.get('resolution'), kwargs.get('bitrate', 0),
                          kwargs.get('codec'), kwargs.get('frame_rate', 25),
                          kwargs.get('aspect_ratio', '16:9'),
                          json.dumps(kwargs.get('chapters', [])),
                          json.dumps(kwargs.get('subtitles', [])),
                          json.dumps(kwargs.get('thumbnails', [])),
                          kwargs.get('education_type', 'adult'),
                          kwargs.get('grade_level'), kwargs.get('subject'),
                          now, now))
                    cursor.execute('UPDATE media_content SET status = ? WHERE content_id = ?', ('processing', content_id))
                    conn.commit()
                    logger.info(f'上传视频: {video_title} ({video_id})')
                    return {'success': True, 'video_id': video_id}
        except Exception as e:
            logger.error(f'上传视频失败: {e}')
            return {'success': False, 'error': str(e)}

    def edit_video(self, video_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            fields = []
            params = []
            for key, value in kwargs.items():
                if key in ['video_title', 'duration', 'resolution', 'bitrate', 'codec',
                          'frame_rate', 'aspect_ratio', 'chapters', 'subtitles',
                          'thumbnails', 'education_type', 'grade_level', 'subject']:
                    fields.append(f'{key} = ?')
                    params.append(value if not isinstance(value, list) else json.dumps(value))
            if not fields:
                return {'success': False, 'error': '未提供可更新字段'}
            params.append(video_id)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(f'UPDATE video_management SET {", ".join(fields)}, updated_at = ? WHERE video_id = ?',
                                 params + [now])
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '视频不存在'}
        except Exception as e:
            logger.error(f'编辑视频失败: {e}')
            return {'success': False, 'error': str(e)}

    def publish_video(self, video_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT is_processed FROM video_management WHERE video_id = ?', (video_id,))
                    video = cursor.fetchone()
                    if not video:
                        return {'success': False, 'error': '视频不存在'}
                    if video[0] == 0:
                        return {'success': False, 'error': '视频未处理完成'}
                    cursor.execute('UPDATE video_management SET status = ?, updated_at = ? WHERE video_id = ?',
                                 ('published', now, video_id))
                    cursor.execute('UPDATE media_content SET status = ?, is_published = 1, published_at = ?, updated_at = ? WHERE content_id = (SELECT content_id FROM video_management WHERE video_id = ?)',
                                 ('published', now, now, video_id))
                    conn.commit()
                    logger.info(f'发布视频: {video_id}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'发布视频失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_video_playback(self, video_id: str, user_id: int = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT vm.*, mc.file_path, mc.view_count
                        FROM video_management vm
                        JOIN media_content mc ON vm.content_id = mc.content_id
                        WHERE vm.video_id = ?
                    ''', (video_id,))
                    video = cursor.fetchone()
                    if not video:
                        return {'success': False, 'error': '视频不存在'}
                    if video['status'] != 'published':
                        return {'success': False, 'error': '视频未发布'}
                    cursor.execute('UPDATE media_content SET view_count = view_count + 1, updated_at = ? WHERE content_id = ?',
                                 (now, video['content_id']))
                    cursor.execute('INSERT INTO video_records (record_id, video_id, action_type, user_id, user_name, timestamp, details) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                 (f"vrd_{uuid.uuid4().hex[:8]}", video_id, 'play', user_id, None, now, json.dumps({'action': 'playback_start'})))
                    conn.commit()
                    return {'success': True, 'video': dict(video)}
        except Exception as e:
            logger.error(f'获取视频播放失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 音频管理 ==========

    def upload_audio(self, audio_title: str, content_id: str, **kwargs) -> Dict[str, Any]:
        try:
            audio_id = f"aud_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO audio_management (
                            audio_id, content_id, audio_title, duration,
                            sample_rate, bitrate, channels, codec,
                            audio_format, cover_image, lyrics,
                            education_type, grade_level, subject,
                            is_processed, processing_status, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'pending', 'draft', ?, ?)
                    ''', (audio_id, content_id, audio_title, kwargs.get('duration', 0),
                          kwargs.get('sample_rate', 44100), kwargs.get('bitrate', 128000),
                          kwargs.get('channels', 2), kwargs.get('codec'),
                          kwargs.get('audio_format'), kwargs.get('cover_image'),
                          kwargs.get('lyrics'), kwargs.get('education_type', 'adult'),
                          kwargs.get('grade_level'), kwargs.get('subject'),
                          now, now))
                    cursor.execute('UPDATE media_content SET status = ? WHERE content_id = ?', ('processing', content_id))
                    conn.commit()
                    logger.info(f'上传音频: {audio_title} ({audio_id})')
                    return {'success': True, 'audio_id': audio_id}
        except Exception as e:
            logger.error(f'上传音频失败: {e}')
            return {'success': False, 'error': str(e)}

    def edit_audio(self, audio_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            fields = []
            params = []
            for key, value in kwargs.items():
                if key in ['audio_title', 'duration', 'sample_rate', 'bitrate', 'channels',
                          'codec', 'audio_format', 'cover_image', 'lyrics',
                          'education_type', 'grade_level', 'subject']:
                    fields.append(f'{key} = ?')
                    params.append(value)
            if not fields:
                return {'success': False, 'error': '未提供可更新字段'}
            params.append(audio_id)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(f'UPDATE audio_management SET {", ".join(fields)}, updated_at = ? WHERE audio_id = ?',
                                 params + [now])
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '音频不存在'}
        except Exception as e:
            logger.error(f'编辑音频失败: {e}')
            return {'success': False, 'error': str(e)}

    def publish_audio(self, audio_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT is_processed FROM audio_management WHERE audio_id = ?', (audio_id,))
                    audio = cursor.fetchone()
                    if not audio:
                        return {'success': False, 'error': '音频不存在'}
                    if audio[0] == 0:
                        return {'success': False, 'error': '音频未处理完成'}
                    cursor.execute('UPDATE audio_management SET status = ?, updated_at = ? WHERE audio_id = ?',
                                 ('published', now, audio_id))
                    cursor.execute('UPDATE media_content SET status = ?, is_published = 1, published_at = ?, updated_at = ? WHERE content_id = (SELECT content_id FROM audio_management WHERE audio_id = ?)',
                                 ('published', now, now, audio_id))
                    conn.commit()
                    logger.info(f'发布音频: {audio_id}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'发布音频失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_audio_playback(self, audio_id: str, user_id: int = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT am.*, mc.file_path, mc.view_count
                        FROM audio_management am
                        JOIN media_content mc ON am.content_id = mc.content_id
                        WHERE am.audio_id = ?
                    ''', (audio_id,))
                    audio = cursor.fetchone()
                    if not audio:
                        return {'success': False, 'error': '音频不存在'}
                    if audio['status'] != 'published':
                        return {'success': False, 'error': '音频未发布'}
                    cursor.execute('UPDATE media_content SET view_count = view_count + 1, updated_at = ? WHERE content_id = ?',
                                 (now, audio['content_id']))
                    cursor.execute('INSERT INTO audio_records (record_id, audio_id, action_type, user_id, user_name, timestamp, details) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                 (f"ard_{uuid.uuid4().hex[:8]}", audio_id, 'play', user_id, None, now, json.dumps({'action': 'playback_start'})))
                    conn.commit()
                    return {'success': True, 'audio': dict(audio)}
        except Exception as e:
            logger.error(f'获取音频播放失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 直播服务 ==========

    def create_live_stream(self, title: str, live_type: str, **kwargs) -> Dict[str, Any]:
        try:
            live_id = f"liv_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = LIVE_STREAMING.get(live_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO live_streaming (
                            live_id, title, live_type, description,
                            cover_image, stream_url, play_url, protocol,
                            education_type, grade_level, subject,
                            host_id, host_name, start_time, end_time,
                            duration, viewer_count, max_viewers, status,
                            is_recorded, recording_path, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, 'scheduled', ?, ?, ?, ?)
                    ''', (live_id, title, live_type, kwargs.get('description'),
                          kwargs.get('cover_image'), kwargs.get('stream_url'),
                          kwargs.get('play_url'), kwargs.get('protocol', 'hls'),
                          kwargs.get('education_type', 'adult'), kwargs.get('grade_level'),
                          kwargs.get('subject'), kwargs.get('host_id'),
                          kwargs.get('host_name'), kwargs.get('start_time'),
                          kwargs.get('end_time'), kwargs.get('is_recorded', 1),
                          kwargs.get('recording_path'), now, now))
                    conn.commit()
                    logger.info(f'创建直播: {title} ({live_id})')
                    return {'success': True, 'live_id': live_id}
        except Exception as e:
            logger.error(f'创建直播失败: {e}')
            return {'success': False, 'error': str(e)}

    def start_live_stream(self, live_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM live_streaming WHERE live_id = ?', (live_id,))
                    live = cursor.fetchone()
                    if not live:
                        return {'success': False, 'error': '直播不存在'}
                    if live[0] != 'scheduled':
                        return {'success': False, 'error': '直播状态不允许开始'}
                    cursor.execute('UPDATE live_streaming SET status = ?, start_time = ?, updated_at = ? WHERE live_id = ?',
                                 ('live', now, now, live_id))
                    conn.commit()
                    logger.info(f'开始直播: {live_id}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'开始直播失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_live_stream(self, live_id: str, recording_path: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT is_recorded, status FROM live_streaming WHERE live_id = ?', (live_id,))
                    live = cursor.fetchone()
                    if not live:
                        return {'success': False, 'error': '直播不存在'}
                    if live[1] != 'live':
                        return {'success': False, 'error': '直播未开始'}
                    if live[0] == 0:
                        return {'success': False, 'error': '未开启录制'}
                    cursor.execute('UPDATE live_streaming SET recording_path = ?, updated_at = ? WHERE live_id = ?',
                                 (recording_path, now, live_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'录制直播失败: {e}')
            return {'success': False, 'error': str(e)}

    def end_live_stream(self, live_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT start_time, status FROM live_streaming WHERE live_id = ?', (live_id,))
                    live = cursor.fetchone()
                    if not live:
                        return {'success': False, 'error': '直播不存在'}
                    if live[1] != 'live':
                        return {'success': False, 'error': '直播未进行中'}
                    duration = 0
                    if live[0]:
                        start = datetime.fromisoformat(live[0])
                        duration = int((datetime.now() - start).total_seconds())
                    cursor.execute('UPDATE live_streaming SET status = ?, end_time = ?, duration = ?, updated_at = ? WHERE live_id = ?',
                                 ('ended', now, duration, now, live_id))
                    conn.commit()
                    logger.info(f'结束直播: {live_id}, 时长: {duration}秒')
                    return {'success': True, 'duration': duration}
        except Exception as e:
            logger.error(f'结束直播失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_live_viewers(self, live_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT ls.viewer_count, ls.max_viewers, ls.status
                    FROM live_streaming ls
                    WHERE ls.live_id = ?
                ''', (live_id,))
                live = cursor.fetchone()
                if not live:
                    return {'success': False, 'error': '直播不存在'}
                cursor.execute('''
                    SELECT sr.viewer_id, sr.viewer_name, sr.join_time, sr.duration
                    FROM streaming_records sr
                    WHERE sr.live_id = ?
                    ORDER BY sr.join_time DESC
                ''', (live_id,))
                viewers = [dict(v) for v in cursor.fetchall()]
                return {'success': True, 'viewer_count': live['viewer_count'],
                        'max_viewers': live['max_viewers'], 'status': live['status'],
                        'viewers': viewers}
        except Exception as e:
            logger.error(f'获取直播观众失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 流媒体服务 ==========

    def configure_streaming(self, protocol: str, **kwargs) -> Dict[str, Any]:
        try:
            config_id = f"scf_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO streaming_config (
                            config_id, protocol, quality_levels,
                            bitrate_settings, buffer_size, latency_target,
                            transcoding_preset, adaptive_bitrate, drm_enabled,
                            watermark_enabled, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (config_id, protocol, json.dumps(kwargs.get('quality_levels', [])),
                          json.dumps(kwargs.get('bitrate_settings', {})),
                          kwargs.get('buffer_size', 3000), kwargs.get('latency_target', 3.0),
                          kwargs.get('transcoding_preset'), kwargs.get('adaptive_bitrate', 1),
                          kwargs.get('drm_enabled', 0), kwargs.get('watermark_enabled', 0),
                          now, now))
                    conn.commit()
                    logger.info(f'配置流媒体: {protocol} ({config_id})')
                    return {'success': True, 'config_id': config_id}
        except Exception as e:
            logger.error(f'配置流媒体失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_stream(self, content_id: str, stream_name: str, **kwargs) -> Dict[str, Any]:
        try:
            stream_id = f"str_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO media_streaming (
                            stream_id, content_id, stream_name, protocol,
                            quality, stream_url, play_url, bandwidth,
                            latency, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (stream_id, content_id, stream_name, kwargs.get('protocol', 'hls'),
                          kwargs.get('quality', 'high'), kwargs.get('stream_url'),
                          kwargs.get('play_url'), kwargs.get('bandwidth', 0),
                          kwargs.get('latency', 0), now, now))
                    conn.commit()
                    logger.info(f'创建流媒体: {stream_name} ({stream_id})')
                    return {'success': True, 'stream_id': stream_id}
        except Exception as e:
            logger.error(f'创建流媒体失败: {e}')
            return {'success': False, 'error': str(e)}

    def monitor_stream(self, stream_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT ms.*, mc.title, mc.media_type
                    FROM media_streaming ms
                    JOIN media_content mc ON ms.content_id = mc.content_id
                    WHERE ms.stream_id = ?
                ''', (stream_id,))
                stream = cursor.fetchone()
                if not stream:
                    return {'success': False, 'error': '流媒体不存在'}
                metrics = {
                    'bandwidth': stream['bandwidth'],
                    'latency': stream['latency'],
                    'status': stream['status'],
                    'view_count': 0
                }
                return {'success': True, 'stream': dict(stream), 'metrics': metrics}
        except Exception as e:
            logger.error(f'监控流媒体失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_stream_statistics(self, content_id: str = None, start_date: str = None,
                              end_date: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM media_streaming WHERE 1=1'
                params = []
                if content_id:
                    query += ' AND content_id = ?'
                    params.append(content_id)
                cursor.execute(query, params)
                streams = [dict(s) for s in cursor.fetchall()]
                total_bandwidth = sum(s['bandwidth'] for s in streams)
                avg_latency = sum(s['latency'] for s in streams) / len(streams) if streams else 0
                return {'success': True, 'streams': streams, 'total_bandwidth': total_bandwidth,
                        'avg_latency': round(avg_latency, 2), 'stream_count': len(streams)}
        except Exception as e:
            logger.error(f'获取流媒体统计失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 内容分发 ==========

    def distribute_content(self, content_id: str, channel: str, **kwargs) -> Dict[str, Any]:
        try:
            distribution_id = f"dst_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = DISTRIBUTION_CHANNELS.get(channel, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO content_distribution (
                            distribution_id, content_id, channel, status,
                            url, cdn_provider, edge_locations, start_time,
                            end_time, bandwidth_usage, cost, education_type,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, 'pending', ?, ?, ?, ?, ?, 0, 0, ?, ?, ?)
                    ''', (distribution_id, content_id, channel, kwargs.get('url'),
                          kwargs.get('cdn_provider'),
                          json.dumps(kwargs.get('edge_locations', [])),
                          kwargs.get('start_time'), kwargs.get('end_time'),
                          kwargs.get('education_type', 'adult'), now, now))
                    conn.commit()
                    logger.info(f'分发内容: {content_id} -> {channel} ({distribution_id})')
                    return {'success': True, 'distribution_id': distribution_id}
        except Exception as e:
            logger.error(f'分发内容失败: {e}')
            return {'success': False, 'error': str(e)}

    def start_distribution(self, distribution_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM content_distribution WHERE distribution_id = ?', (distribution_id,))
                    dist = cursor.fetchone()
                    if not dist:
                        return {'success': False, 'error': '分发任务不存在'}
                    if dist[0] != 'pending':
                        return {'success': False, 'error': '分发状态不允许启动'}
                    cursor.execute('UPDATE content_distribution SET status = ?, start_time = ?, updated_at = ? WHERE distribution_id = ?',
                                 ('active', now, now, distribution_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'启动分发失败: {e}')
            return {'success': False, 'error': str(e)}

    def stop_distribution(self, distribution_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM content_distribution WHERE distribution_id = ?', (distribution_id,))
                    dist = cursor.fetchone()
                    if not dist:
                        return {'success': False, 'error': '分发任务不存在'}
                    if dist[0] != 'active':
                        return {'success': False, 'error': '分发状态不允许停止'}
                    cursor.execute('UPDATE content_distribution SET status = ?, end_time = ?, updated_at = ? WHERE distribution_id = ?',
                                 ('stopped', now, now, distribution_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'停止分发失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_distribution_stats(self, distribution_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT cd.*, mc.title, mc.media_type
                    FROM content_distribution cd
                    JOIN media_content mc ON cd.content_id = mc.content_id
                    WHERE cd.distribution_id = ?
                ''', (distribution_id,))
                dist = cursor.fetchone()
                if not dist:
                    return {'success': False, 'error': '分发任务不存在'}
                cursor.execute('SELECT SUM(bandwidth) as total_bw, SUM(requests) as total_req, AVG(cache_hit) as avg_hit FROM distribution_records WHERE distribution_id = ?', (distribution_id,))
                stats = cursor.fetchone()
                return {'success': True, 'distribution': dict(dist),
                        'total_bandwidth': stats['total_bw'] or 0,
                        'total_requests': stats['total_req'] or 0,
                        'avg_cache_hit': round(stats['avg_hit'] or 0, 2)}
        except Exception as e:
            logger.error(f'获取分发统计失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 媒体转码 ==========

    def create_transcoding_task(self, content_id: str, source_format: str,
                                target_format: str, **kwargs) -> Dict[str, Any]:
        try:
            transcode_id = f"tcd_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO media_transcoding (
                            transcode_id, content_id, source_format,
                            target_format, transcoding_method, quality,
                            resolution, bitrate, status, progress,
                            error_message, output_path, duration,
                            start_time, end_time, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', 0, ?, ?, ?, ?, ?, ?, ?)
                    ''', (transcode_id, content_id, source_format, target_format,
                          kwargs.get('transcoding_method', 'software'),
                          kwargs.get('quality', 'high'), kwargs.get('resolution'),
                          kwargs.get('bitrate', 0), kwargs.get('error_message'),
                          kwargs.get('output_path'), kwargs.get('duration', 0),
                          None, None, now, now))
                    conn.commit()
                    logger.info(f'创建转码任务: {content_id} ({transcode_id})')
                    return {'success': True, 'transcode_id': transcode_id}
        except Exception as e:
            logger.error(f'创建转码任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def start_transcoding(self, transcode_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM media_transcoding WHERE transcode_id = ?', (transcode_id,))
                    task = cursor.fetchone()
                    if not task:
                        return {'success': False, 'error': '转码任务不存在'}
                    if task[0] != 'pending':
                        return {'success': False, 'error': '转码状态不允许启动'}
                    cursor.execute('UPDATE media_transcoding SET status = ?, start_time = ?, progress = 0, updated_at = ? WHERE transcode_id = ?',
                                 ('processing', now, now, transcode_id))
                    cursor.execute('INSERT INTO transcoding_records (record_id, transcode_id, action_type, timestamp, progress, details) VALUES (?, ?, ?, ?, ?, ?)',
                                 (f"trd_{uuid.uuid4().hex[:8]}", transcode_id, 'start', now, 0, json.dumps({'action': 'transcoding_start'})))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'启动转码失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_transcoding_progress(self, transcode_id: str, progress: int, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE media_transcoding SET progress = ?, updated_at = ? WHERE transcode_id = ?',
                                 (progress, now, transcode_id))
                    cursor.execute('INSERT INTO transcoding_records (record_id, transcode_id, action_type, timestamp, progress, details) VALUES (?, ?, ?, ?, ?, ?)',
                                 (f"trd_{uuid.uuid4().hex[:8]}", transcode_id, 'progress', now, progress,
                                  json.dumps({'progress': progress, 'details': kwargs.get('details', {})})))
                    if progress >= 100:
                        cursor.execute('UPDATE media_transcoding SET status = ?, end_time = ?, updated_at = ? WHERE transcode_id = ?',
                                     ('completed', now, now, transcode_id))
                        content_id = cursor.execute('SELECT content_id FROM media_transcoding WHERE transcode_id = ?', (transcode_id,)).fetchone()[0]
                        cursor.execute('UPDATE media_content SET status = ? WHERE content_id = ?', ('ready', content_id))
                        cursor.execute('UPDATE video_management SET is_processed = 1, processing_status = ? WHERE content_id = ?', ('completed', content_id))
                        cursor.execute('UPDATE audio_management SET is_processed = 1, processing_status = ? WHERE content_id = ?', ('completed', content_id))
                    conn.commit()
                    return {'success': True, 'progress': progress}
        except Exception as e:
            logger.error(f'更新转码进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_transcoding_status(self, transcode_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT mt.*, mc.title
                    FROM media_transcoding mt
                    JOIN media_content mc ON mt.content_id = mc.content_id
                    WHERE mt.transcode_id = ?
                ''', (transcode_id,))
                task = cursor.fetchone()
                if not task:
                    return {'success': False, 'error': '转码任务不存在'}
                cursor.execute('SELECT * FROM transcoding_records WHERE transcode_id = ? ORDER BY timestamp DESC LIMIT 10', (transcode_id,))
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'task': dict(task), 'records': records}
        except Exception as e:
            logger.error(f'获取转码状态失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 媒体存储 ==========

    def store_media(self, content_id: str, storage_type: str, **kwargs) -> Dict[str, Any]:
        try:
            storage_id = f"sto_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO media_storage (
                            storage_id, content_id, storage_type, bucket_name,
                            file_path, file_size, checksum, upload_time,
                            last_access_time, replication_status, backup_count,
                            is_archived, archive_time, education_type,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', 0, 0, ?, ?, ?, ?)
                    ''', (storage_id, content_id, storage_type, kwargs.get('bucket_name'),
                          kwargs.get('file_path'), kwargs.get('file_size', 0),
                          kwargs.get('checksum'), now, now, kwargs.get('archive_time'),
                          kwargs.get('education_type', 'adult'), now, now))
                    cursor.execute('INSERT INTO storage_records (record_id, storage_id, action_type, timestamp, size_change, details) VALUES (?, ?, ?, ?, ?, ?)',
                                 (f"srd_{uuid.uuid4().hex[:8]}", storage_id, 'upload', now, kwargs.get('file_size', 0),
                                  json.dumps({'action': 'storage_upload'})))
                    conn.commit()
                    logger.info(f'存储媒体: {content_id} ({storage_id})')
                    return {'success': True, 'storage_id': storage_id}
        except Exception as e:
            logger.error(f'存储媒体失败: {e}')
            return {'success': False, 'error': str(e)}

    def migrate_storage(self, storage_id: str, target_storage_type: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT storage_type, content_id FROM media_storage WHERE storage_id = ?', (storage_id,))
                    storage = cursor.fetchone()
                    if not storage:
                        return {'success': False, 'error': '存储记录不存在'}
                    cursor.execute('UPDATE media_storage SET storage_type = ?, updated_at = ? WHERE storage_id = ?',
                                 (target_storage_type, now, storage_id))
                    cursor.execute('INSERT INTO storage_records (record_id, storage_id, action_type, timestamp, size_change, details) VALUES (?, ?, ?, ?, ?, ?)',
                                 (f"srd_{uuid.uuid4().hex[:8]}", storage_id, 'migrate', now, 0,
                                  json.dumps({'from': storage[0], 'to': target_storage_type})))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'迁移存储失败: {e}')
            return {'success': False, 'error': str(e)}

    def backup_storage(self, storage_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT backup_count FROM media_storage WHERE storage_id = ?', (storage_id,))
                    storage = cursor.fetchone()
                    if not storage:
                        return {'success': False, 'error': '存储记录不存在'}
                    new_count = storage[0] + 1
                    cursor.execute('UPDATE media_storage SET backup_count = ?, updated_at = ? WHERE storage_id = ?',
                                 (new_count, now, storage_id))
                    cursor.execute('INSERT INTO storage_records (record_id, storage_id, action_type, timestamp, size_change, details) VALUES (?, ?, ?, ?, ?, ?)',
                                 (f"srd_{uuid.uuid4().hex[:8]}", storage_id, 'backup', now, 0,
                                  json.dumps({'backup_number': new_count})))
                    conn.commit()
                    return {'success': True, 'backup_count': new_count}
        except Exception as e:
            logger.error(f'备份存储失败: {e}')
            return {'success': False, 'error': str(e)}

    def archive_storage(self, storage_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT is_archived FROM media_storage WHERE storage_id = ?', (storage_id,))
                    storage = cursor.fetchone()
                    if not storage:
                        return {'success': False, 'error': '存储记录不存在'}
                    if storage[0] == 1:
                        return {'success': False, 'error': '已归档'}
                    cursor.execute('UPDATE media_storage SET is_archived = 1, archive_time = ?, storage_type = ?, updated_at = ? WHERE storage_id = ?',
                                 (now, 'archive', now, storage_id))
                    cursor.execute('INSERT INTO storage_records (record_id, storage_id, action_type, timestamp, size_change, details) VALUES (?, ?, ?, ?, ?, ?)',
                                 (f"srd_{uuid.uuid4().hex[:8]}", storage_id, 'archive', now, 0,
                                  json.dumps({'action': 'storage_archived'})))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'归档存储失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_media_statistics(self, education_type: str = None, date_range: Tuple[str, str] = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = 'SELECT COUNT(*) as total, SUM(view_count) as total_views, SUM(download_count) as total_downloads FROM media_content WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                content_stats = cursor.fetchone()
                query_videos = 'SELECT COUNT(*) as count FROM video_management WHERE 1=1'
                params_videos = []
                if education_type:
                    query_videos += ' AND education_type = ?'
                    params_videos.append(education_type)
                cursor.execute(query_videos, params_videos)
                video_stats = cursor.fetchone()
                query_audios = 'SELECT COUNT(*) as count FROM audio_management WHERE 1=1'
                params_audios = []
                if education_type:
                    query_audios += ' AND education_type = ?'
                    params_audios.append(education_type)
                cursor.execute(query_audios, params_audios)
                audio_stats = cursor.fetchone()
                cursor.execute('SELECT COUNT(*) as count, SUM(duration) as total_duration FROM live_streaming WHERE status = ?', ('ended',))
                live_stats = cursor.fetchone()
                cursor.execute('SELECT COUNT(*) as count FROM media_transcoding WHERE status = ?', ('completed',))
                transcode_stats = cursor.fetchone()
                return {'success': True,
                        'content': {'total': content_stats[0], 'views': content_stats[1] or 0, 'downloads': content_stats[2] or 0},
                        'videos': {'count': video_stats[0]},
                        'audios': {'count': audio_stats[0]},
                        'live_streams': {'count': live_stats[0], 'total_duration': live_stats[1] or 0},
                        'transcoding': {'completed': transcode_stats[0]}}
        except Exception as e:
            logger.error(f'获取媒体统计失败: {e}')
            return {'success': False, 'error': str(e)}