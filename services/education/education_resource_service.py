from core.db_path import get_db_path as _mtscos_get_db_path
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS 教育资源服务 (v15.27.0) ============================== 提供资源库管理、资源检索、资源共享、资源推荐等综合管理服务。  核心能力： 1. 资源库管理 - 库创建、配置管理、资源上传、资源管理 2. 资源检索服务 - 全文检索、分类检索、高级检索、语义检索 3. 资源共享服务 - 共享设置、权限控制、共享记录、版本管理 4. 资源推荐服务 - 个性化推荐、热门推荐、相似推荐、关联推荐 5. 资源评估服务 - 评估指标、评分管理、评估报告、质量监控 6. 资源统计服务 - 使用统计、访问分析、下载统计、趋势分析 7. 资源权限管理 - 用户权限、角色管理、访问控制、审计日志 8. 资源迁移服务 - 在线迁移、离线迁移、批量迁移、数据同步  差异化支持： - 成人教育：职业技能、继续教育、企业培训 - K12教育：课程资源、学习资料、教学素材 """
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_resource_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationResource')


# ========== 教育资源配置 ==========

RESOURCE_TYPES = {
    'course': {'name': '课程资源', 'description': '完整的课程内容', 'support_k12': True, 'support_adult': True},
    'teaching': {'name': '教学资源', 'description': '教案、课件、教学工具', 'support_k12': True, 'support_adult': True},
    'learning': {'name': '学习资源', 'description': '习题、试卷、学习指导', 'support_k12': True, 'support_adult': False},
    'research': {'name': '科研资源', 'description': '研究报告、论文、数据', 'support_k12': False, 'support_adult': True},
    'assessment': {'name': '评估资源', 'description': '评估工具、测评题库', 'support_k12': True, 'support_adult': True},
    'management': {'name': '管理资源', 'description': '管理文档、规章制度', 'support_k12': True, 'support_adult': True},
    'training': {'name': '培训资源', 'description': '培训课件、实操指南', 'support_k12': False, 'support_adult': True},
    'comprehensive': {'name': '综合资源', 'description': '多类型整合资源', 'support_k12': True, 'support_adult': True}
}

LIBRARY_TYPES = {
    'central': {'name': '中央资源库', 'scope': '全国', 'capacity': 'large'},
    'subject': {'name': '学科资源库', 'scope': '学科', 'capacity': 'medium'},
    'school': {'name': '校本资源库', 'scope': '学校', 'capacity': 'small'},
    'regional': {'name': '区域资源库', 'scope': '区域', 'capacity': 'medium'},
    'topic': {'name': '专题资源库', 'scope': '专题', 'capacity': 'small'},
    'personal': {'name': '个人资源库', 'scope': '个人', 'capacity': 'small'},
    'shared': {'name': '共享资源库', 'scope': '共享', 'capacity': 'medium'},
    'enterprise': {'name': '企业资源库', 'scope': '企业', 'capacity': 'large'}
}

SEARCH_METHODS = {
    'fulltext': {'name': '全文检索', 'description': '基于全文内容的检索', 'accuracy': 'high'},
    'category': {'name': '分类检索', 'description': '按资源类型分类检索', 'accuracy': 'medium'},
    'tag': {'name': '标签检索', 'description': '基于标签关键词检索', 'accuracy': 'medium'},
    'fuzzy': {'name': '模糊检索', 'description': '模糊匹配关键词', 'accuracy': 'low'},
    'advanced': {'name': '高级检索', 'description': '多条件组合检索', 'accuracy': 'high'},
    'semantic': {'name': '语义检索', 'description': '基于语义理解检索', 'accuracy': 'high'},
    'image': {'name': '图像检索', 'description': '基于图像内容检索', 'accuracy': 'medium'},
    'voice': {'name': '语音检索', 'description': '基于语音输入检索', 'accuracy': 'medium'}
}

SHARING_MODES = {
    'public': {'name': '公开共享', 'access': 'all', 'require_auth': False},
    'private': {'name': '私有共享', 'access': 'owner', 'require_auth': True},
    'specified': {'name': '指定共享', 'access': 'specified', 'require_auth': True},
    'paid': {'name': '付费共享', 'access': 'paid', 'require_auth': True},
    'copyright': {'name': '版权共享', 'access': 'licensed', 'require_auth': True},
    'collaborative': {'name': '协作共享', 'access': 'collaborators', 'require_auth': True},
    'anonymous': {'name': '匿名共享', 'access': 'anonymous', 'require_auth': False},
    'timed': {'name': '限时共享', 'access': 'temporary', 'require_auth': True}
}

RECOMMENDATION_TYPES = {
    'personalized': {'name': '个性化推荐', 'algorithm': 'user_based', 'accuracy': 'high'},
    'popular': {'name': '热门推荐', 'algorithm': 'trending', 'accuracy': 'medium'},
    'similar': {'name': '相似推荐', 'algorithm': 'content_based', 'accuracy': 'high'},
    'related': {'name': '关联推荐', 'algorithm': 'association', 'accuracy': 'medium'},
    'intelligent': {'name': '智能推荐', 'algorithm': 'ml_based', 'accuracy': 'high'},
    'manual': {'name': '人工推荐', 'algorithm': 'human', 'accuracy': 'medium'},
    'system': {'name': '系统推荐', 'algorithm': 'rule_based', 'accuracy': 'medium'},
    'hybrid': {'name': '混合推荐', 'algorithm': 'hybrid', 'accuracy': 'high'}
}

ASSESSMENT_CRITERIA = {
    'quality': {'name': '质量', 'weight': 0.2, 'description': '资源内容质量'},
    'applicability': {'name': '适用性', 'weight': 0.15, 'description': '适用范围和对象'},
    'timeliness': {'name': '时效性', 'weight': 0.1, 'description': '内容更新时效性'},
    'completeness': {'name': '完整性', 'weight': 0.15, 'description': '资源完整性'},
    'accuracy': {'name': '准确性', 'weight': 0.15, 'description': '内容准确性'},
    'innovation': {'name': '创新性', 'weight': 0.1, 'description': '创新程度'},
    'usability': {'name': '易用性', 'weight': 0.1, 'description': '使用便捷程度'},
    'value': {'name': '价值', 'weight': 0.05, 'description': '教育价值'}
}

PERMISSION_LEVELS = {
    'admin': {'name': '管理员', 'access': 'full', 'can_manage': True},
    'editor': {'name': '编辑', 'access': 'edit', 'can_manage': True},
    'reviewer': {'name': '审核', 'access': 'review', 'can_manage': False},
    'viewer': {'name': '查看', 'access': 'view', 'can_manage': False},
    'downloader': {'name': '下载', 'access': 'download', 'can_manage': False},
    'uploader': {'name': '上传', 'access': 'upload', 'can_manage': False},
    'deleter': {'name': '删除', 'access': 'delete', 'can_manage': False},
    'manager': {'name': '管理', 'access': 'manage', 'can_manage': True}
}

MIGRATION_METHODS = {
    'online': {'name': '在线迁移', 'mode': 'real-time', 'complexity': 'low'},
    'offline': {'name': '离线迁移', 'mode': 'batch', 'complexity': 'medium'},
    'batch': {'name': '批量迁移', 'mode': 'batch', 'complexity': 'medium'},
    'incremental': {'name': '增量迁移', 'mode': 'delta', 'complexity': 'high'},
    'full': {'name': '全量迁移', 'mode': 'full', 'complexity': 'high'},
    'cross_platform': {'name': '跨平台迁移', 'mode': 'cross', 'complexity': 'high'},
    'sync': {'name': '数据同步', 'mode': 'real-time', 'complexity': 'medium'},
    'backup': {'name': '数据备份', 'mode': 'batch', 'complexity': 'low'}
}


class EducationResourceService:
    """教育资源服务"""

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

                cursor.execute(''' CREATE TABLE IF NOT EXISTS resource_library ( library_id TEXT PRIMARY KEY, library_name TEXT NOT NULL, library_type TEXT NOT NULL, education_type TEXT NOT NULL, description TEXT, owner_id INTEGER, owner_name TEXT, status TEXT DEFAULT 'active', resource_count INTEGER DEFAULT 0, storage_size REAL DEFAULT 0, created_at TEXT, updated_at TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS library_config ( config_id TEXT PRIMARY KEY, library_id TEXT NOT NULL, config_key TEXT NOT NULL, config_value TEXT, config_type TEXT DEFAULT 'string', created_at TEXT, updated_at TEXT, UNIQUE(library_id, config_key) ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS resource_search ( resource_id TEXT PRIMARY KEY, library_id TEXT NOT NULL, resource_type TEXT NOT NULL, title TEXT NOT NULL, keywords TEXT, tags TEXT, content TEXT, metadata TEXT, education_type TEXT NOT NULL, grade_level TEXT, subject TEXT, language TEXT DEFAULT 'zh', file_format TEXT, file_size REAL, uploader_id INTEGER, uploader_name TEXT, upload_date TEXT, last_modified TEXT, status TEXT DEFAULT 'pending', view_count INTEGER DEFAULT 0, download_count INTEGER DEFAULT 0, share_count INTEGER DEFAULT 0, rating REAL DEFAULT 0, rating_count INTEGER DEFAULT 0, created_at TEXT, updated_at TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS search_logs ( log_id TEXT PRIMARY KEY, user_id INTEGER, search_method TEXT, search_query TEXT, search_time TEXT, result_count INTEGER DEFAULT 0, response_time REAL, education_type TEXT, library_id TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS resource_sharing ( share_id TEXT PRIMARY KEY, resource_id TEXT NOT NULL, library_id TEXT, sharing_mode TEXT NOT NULL, share_title TEXT, share_description TEXT, access_code TEXT, expire_date TEXT, share_count INTEGER DEFAULT 0, download_count INTEGER DEFAULT 0, status TEXT DEFAULT 'active', education_type TEXT, created_at TEXT, updated_at TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS sharing_records ( record_id TEXT PRIMARY KEY, share_id TEXT NOT NULL, user_id INTEGER, user_name TEXT, access_time TEXT, action TEXT, education_type TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS resource_recommendation ( rec_id TEXT PRIMARY KEY, user_id INTEGER, resource_id TEXT NOT NULL, recommendation_type TEXT NOT NULL, score REAL DEFAULT 0, reason TEXT, education_type TEXT, expires_at TEXT, clicked INTEGER DEFAULT 0, created_at TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS recommendation_data ( data_id TEXT PRIMARY KEY, user_id INTEGER, behavior_type TEXT, resource_id TEXT, score REAL, timestamp TEXT, education_type TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS resource_assessment ( assess_id TEXT PRIMARY KEY, resource_id TEXT NOT NULL, assessor_id INTEGER, assessor_name TEXT, criteria TEXT, scores TEXT, overall_score REAL DEFAULT 0, comments TEXT, assessment_date TEXT, education_type TEXT, status TEXT DEFAULT 'pending', created_at TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS assessment_results ( result_id TEXT PRIMARY KEY, resource_id TEXT NOT NULL, quality_score REAL DEFAULT 0, applicability_score REAL DEFAULT 0, timeliness_score REAL DEFAULT 0, completeness_score REAL DEFAULT 0, accuracy_score REAL DEFAULT 0, innovation_score REAL DEFAULT 0, usability_score REAL DEFAULT 0, value_score REAL DEFAULT 0, overall_score REAL DEFAULT 0, last_assessed TEXT, education_type TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS resource_statistics ( stat_id TEXT PRIMARY KEY, library_id TEXT, resource_type TEXT, education_type TEXT, stat_period TEXT, total_views INTEGER DEFAULT 0, total_downloads INTEGER DEFAULT 0, total_shares INTEGER DEFAULT 0, total_uploads INTEGER DEFAULT 0, average_rating REAL DEFAULT 0, active_users INTEGER DEFAULT 0, stat_date TEXT, created_at TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS stat_data ( data_id TEXT PRIMARY KEY, stat_id TEXT NOT NULL, metric_name TEXT NOT NULL, metric_value REAL, metric_unit TEXT, recorded_at TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS resource_permissions ( perm_id TEXT PRIMARY KEY, resource_id TEXT, library_id TEXT, user_id INTEGER, permission_level TEXT NOT NULL, granted_by INTEGER, granted_at TEXT, expire_date TEXT, status TEXT DEFAULT 'active', education_type TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS permission_records ( record_id TEXT PRIMARY KEY, perm_id TEXT NOT NULL, user_id INTEGER, action TEXT, action_time TEXT, resource_id TEXT, education_type TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS resource_migration ( migrate_id TEXT PRIMARY KEY, source_library TEXT NOT NULL, target_library TEXT NOT NULL, migration_method TEXT NOT NULL, status TEXT DEFAULT 'pending', total_count INTEGER DEFAULT 0, success_count INTEGER DEFAULT 0, failed_count INTEGER DEFAULT 0, start_time TEXT, end_time TEXT, error_message TEXT, education_type TEXT, created_at TEXT ) ''')

                cursor.execute(''' CREATE TABLE IF NOT EXISTS migration_records ( record_id TEXT PRIMARY KEY, migrate_id TEXT NOT NULL, resource_id TEXT, status TEXT DEFAULT 'pending', error_message TEXT, migrated_at TEXT ) ''')

                conn.commit()
                logger.info('教育资源服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 资源库管理 ==========

    def create_library(self, library_name: str, library_type: str,
                       education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            if education_type not in ['adult', 'k12']:
                return {'success': False, 'error': '教育类型无效，必须为 adult 或 k12'}
            if library_type not in LIBRARY_TYPES:
                return {'success': False, 'error': '库类型无效'}

            library_id = f"lib_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO resource_library ( library_id, library_name, library_type, education_type, description, owner_id, owner_name, status, resource_count, storage_size, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', 0, 0, ?, ?) ''', (library_id, library_name, library_type, education_type,
                          kwargs.get('description'), kwargs.get('owner_id'),
                          kwargs.get('owner_name'), now, now))
                    conn.commit()
                    logger.info(f'创建资源库: {library_name} ({library_id}) [{education_type}]')
                    return {'success': True, 'library_id': library_id}
        except Exception as e:
            logger.error(f'创建资源库失败: {e}')
            return {'success': False, 'error': str(e)}

    def configure_library(self, library_id: str, configs: Dict[str, Any]) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    for key, value in configs.items():
                        config_id = f"cfg_{uuid.uuid4().hex[:8]}"
                        cursor.execute('INSERT OR REPLACE INTO library_config (config_id, library_id, config_key, config_value, config_type, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                     (config_id, library_id, key, str(value),
                                      type(value).__name__, now, now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'配置资源库失败: {e}')
            return {'success': False, 'error': str(e)}

    def upload_resource(self, library_id: str, title: str, resource_type: str,
                        education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            if education_type not in ['adult', 'k12']:
                return {'success': False, 'error': '教育类型无效，必须为 adult 或 k12'}
            if resource_type not in RESOURCE_TYPES:
                return {'success': False, 'error': '资源类型无效'}

            resource_id = f"res_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO resource_search ( resource_id, library_id, resource_type, title, keywords, tags, content, metadata, education_type, grade_level, subject, language, file_format, file_size, uploader_id, uploader_name, upload_date, last_modified, status, view_count, download_count, share_count, rating, rating_count, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', 0, 0, 0, 0, 0, ?, ?) ''', (resource_id, library_id, resource_type, title,
                          kwargs.get('keywords'), kwargs.get('tags'),
                          kwargs.get('content'), kwargs.get('metadata'),
                          education_type, kwargs.get('grade_level'),
                          kwargs.get('subject'), kwargs.get('language', 'zh'),
                          kwargs.get('file_format'), kwargs.get('file_size', 0),
                          kwargs.get('uploader_id'), kwargs.get('uploader_name'),
                          now[:10], now, now, now))
                    cursor.execute('UPDATE resource_library SET resource_count = resource_count + 1, updated_at = ? WHERE library_id = ?',
                                 (now, library_id))
                    conn.commit()
                    logger.info(f'上传资源: {title} ({resource_id}) [{education_type}]')
                    return {'success': True, 'resource_id': resource_id}
        except Exception as e:
            logger.error(f'上传资源失败: {e}')
            return {'success': False, 'error': str(e)}

    def delete_resource(self, resource_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT library_id FROM resource_search WHERE resource_id = ?', (resource_id,))
                    result = cursor.fetchone()
                    if not result:
                        return {'success': False, 'error': '资源不存在'}
                    library_id = result[0]
                    cursor.execute('DELETE FROM resource_search WHERE resource_id = ?', (resource_id,))
                    cursor.execute(
                    'UPDATE resource_library SET resource_count = resource_count - 1 WHERE library_id = ?', (library_id,
                    ))
                    conn.commit()
                    logger.info(f'删除资源: {resource_id}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'删除资源失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 资源检索服务 ==========

    def search_fulltext(self, query: str, education_type: str = None,
                        **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            log_id = f"log_{uuid.uuid4().hex[:10]}"
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query_sql = 'SELECT * FROM resource_search WHERE status = ? AND ( title LIKE ? OR keywords LIKE ? OR content LIKE ?)'
                params = ['approved', f'%{query}%', f'%{query}%', f'%{query}%']
                if education_type:
                    query_sql += ' AND education_type = ?'
                    params.append(education_type)
                if kwargs.get('resource_type'):
                    query_sql += ' AND resource_type = ?'
                    params.append(kwargs['resource_type'])
                cursor.execute(query_sql, params)
                results = [dict(r) for r in cursor.fetchall()]
                cursor.execute('INSERT INTO search_logs (log_id, user_id, search_method, search_query, search_time, result_count, education_type) VALUES (?, ?, ?, ?, ?, ?, ?)',
                             (log_id, kwargs.get('user_id'), 'fulltext', query, now, len(results), education_type))
                conn.commit()
                return {'success': True, 'results': results, 'total': len(results)}
        except Exception as e:
            logger.error(f'全文检索失败: {e}')
            return {'success': False, 'error': str(e)}

    def search_category(self, resource_type: str, education_type: str = None,
                        **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            log_id = f"log_{uuid.uuid4().hex[:10]}"
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query_sql = 'SELECT * FROM resource_search WHERE status = ? AND resource_type = ?'
                params = ['approved', resource_type]
                if education_type:
                    query_sql += ' AND education_type = ?'
                    params.append(education_type)
                if kwargs.get('subject'):
                    query_sql += ' AND subject = ?'
                    params.append(kwargs['subject'])
                query_sql += ' ORDER BY upload_date DESC LIMIT ? OFFSET ?'
                params.extend([kwargs.get('limit', 20), kwargs.get('offset', 0)])
                cursor.execute(query_sql, params)
                results = [dict(r) for r in cursor.fetchall()]
                cursor.execute('INSERT INTO search_logs (log_id, user_id, search_method, search_query, search_time, result_count, education_type) VALUES (?, ?, ?, ?, ?, ?, ?)',
                             (log_id, kwargs.get('user_id'), 'category', resource_type, now, len(results),
                             education_type))
                conn.commit()
                return {'success': True, 'results': results, 'total': len(results)}
        except Exception as e:
            logger.error(f'分类检索失败: {e}')
            return {'success': False, 'error': str(e)}

    def search_advanced(self, filters: Dict[str, Any], education_type: str = None,
                        **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            log_id = f"log_{uuid.uuid4().hex[:10]}"
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query_sql = 'SELECT * FROM resource_search WHERE status = ?'
                params = ['approved']
                if education_type:
                    query_sql += ' AND education_type = ?'
                    params.append(education_type)
                for key, value in filters.items():
                    if key in ['title', 'keywords', 'tags']:
                        query_sql += f' AND {key} LIKE ?'
                        params.append(f'%{value}%')
                    elif key in ['resource_type', 'subject', 'language', 'file_format']:
                        query_sql += f' AND {key} = ?'
                        params.append(value)
                    elif key in ['grade_level']:
                        query_sql += f' AND {key} = ?'
                        params.append(value)
                    elif key in ['min_file_size', 'max_file_size']:
                        op = '>=' if key.startswith('min') else '<='
                        query_sql += f' AND file_size {op} ?'
                        params.append(value)
                query_sql += ' ORDER BY upload_date DESC LIMIT ? OFFSET ?'
                params.extend([kwargs.get('limit', 20), kwargs.get('offset', 0)])
                cursor.execute(query_sql, params)
                results = [dict(r) for r in cursor.fetchall()]
                cursor.execute('INSERT INTO search_logs (log_id, user_id, search_method, search_query, search_time, result_count, education_type) VALUES (?, ?, ?, ?, ?, ?, ?)',
                             (log_id, kwargs.get('user_id'), 'advanced', json.dumps(filters), now, len(results),
                             education_type))
                conn.commit()
                return {'success': True, 'results': results, 'total': len(results)}
        except Exception as e:
            logger.error(f'高级检索失败: {e}')
            return {'success': False, 'error': str(e)}

    def search_semantic(self, query: str, education_type: str = None,
                        **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            log_id = f"log_{uuid.uuid4().hex[:10]}"
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query_sql = 'SELECT * FROM resource_search WHERE status = ? AND ( title LIKE ? OR keywords LIKE ? OR tags LIKE ? OR content LIKE ?)'
                params = ['approved', f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%']
                if education_type:
                    query_sql += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query_sql, params)
                results = [dict(r) for r in cursor.fetchall()]
                cursor.execute('INSERT INTO search_logs (log_id, user_id, search_method, search_query, search_time, result_count, education_type) VALUES (?, ?, ?, ?, ?, ?, ?)',
                             (log_id, kwargs.get('user_id'), 'semantic', query, now, len(results), education_type))
                conn.commit()
                return {'success': True, 'results': results, 'total': len(results)}
        except Exception as e:
            logger.error(f'语义检索失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 资源共享服务 ==========

    def create_share(self, resource_id: str, sharing_mode: str,
                     education_type: str = None, **kwargs) -> Dict[str, Any]:
        try:
            if sharing_mode not in SHARING_MODES:
                return {'success': False, 'error': '共享模式无效'}

            share_id = f"shr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            access_code = f"ACC{uuid.uuid4().hex[:8].upper()}" if sharing_mode in ['specified', 'paid'] else None
            expire_date = None
            if sharing_mode == 'timed':
                expire_days = kwargs.get('expire_days', 7)
                expire_date = (datetime.now() + timedelta(days=expire_days)).isoformat()[:10]

            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO resource_sharing ( share_id, resource_id, library_id, sharing_mode, share_title, share_description, access_code, expire_date, share_count, download_count, status, education_type, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 'active', ?, ?, ?) ''', (share_id, resource_id, kwargs.get('library_id'), sharing_mode,
                          kwargs.get('share_title'), kwargs.get('share_description'),
                          access_code, expire_date, education_type, now, now))
                    cursor.execute('UPDATE resource_search SET share_count = share_count + 1, updated_at = ? WHERE resource_id = ?',
                                 (now, resource_id))
                    conn.commit()
                    logger.info(f'创建共享: {share_id} ({sharing_mode})')
                    return {'success': True, 'share_id': share_id, 'access_code': access_code}
        except Exception as e:
            logger.error(f'创建共享失败: {e}')
            return {'success': False, 'error': str(e)}

    def access_shared_resource(self, share_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM resource_sharing WHERE share_id = ? AND status = ?', (share_id,
                    'active'))
                    share = cursor.fetchone()
                    if not share:
                        return {'success': False, 'error': '共享链接不存在或已失效'}
                    if share[7] and share[7] < now[:10]:
                        cursor.execute('UPDATE resource_sharing SET status = ? WHERE share_id = ?', ('expired',
                        share_id))
                        conn.commit()
                        return {'success': False, 'error': '共享链接已过期'}
                    if share[6] and kwargs.get('access_code') != share[6]:
                        return {'success': False, 'error': '访问码不正确'}
                    cursor.execute('UPDATE resource_sharing SET share_count = share_count + 1, updated_at = ? WHERE share_id = ?',
                                 (now, share_id))
                    record_id = f"rec_{uuid.uuid4().hex[:10]}"
                    cursor.execute('INSERT INTO sharing_records (record_id, share_id, user_id, user_name, access_time, action, education_type) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                 (record_id, share_id, kwargs.get('user_id'), kwargs.get('user_name'), now, 'view',
                                 share[11]))
                    conn.commit()
                    return {'success': True, 'resource_id': share[1]}
        except Exception as e:
            logger.error(f'访问共享资源失败: {e}')
            return {'success': False, 'error': str(e)}

    def download_shared_resource(self, share_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM resource_sharing WHERE share_id = ? AND status = ?', (share_id,
                    'active'))
                    share = cursor.fetchone()
                    if not share:
                        return {'success': False, 'error': '共享链接不存在或已失效'}
                    cursor.execute('UPDATE resource_sharing SET download_count = download_count + 1, updated_at = ? WHERE share_id = ?',
                                 (now, share_id))
                    cursor.execute('UPDATE resource_search SET download_count = download_count + 1, updated_at = ? WHERE resource_id = ?',
                                 (now, share[1]))
                    record_id = f"rec_{uuid.uuid4().hex[:10]}"
                    cursor.execute('INSERT INTO sharing_records (record_id, share_id, user_id, user_name, access_time, action, education_type) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                 (record_id, share_id, kwargs.get('user_id'), kwargs.get('user_name'), now, 'download',
                                 share[11]))
                    conn.commit()
                    return {'success': True, 'resource_id': share[1]}
        except Exception as e:
            logger.error(f'下载共享资源失败: {e}')
            return {'success': False, 'error': str(e)}

    def revoke_share(self, share_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE resource_sharing SET status = ? WHERE share_id = ?', ('revoked', share_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '共享链接不存在'}
        except Exception as e:
            logger.error(f'撤销共享失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 资源推荐服务 ==========

    def generate_personalized_recommendations(self, user_id: int, education_type: str,
                                              count: int = 10) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(''' SELECT rs.*, rd.score as behavior_score FROM resource_search rs LEFT JOIN recommendation_data rd ON rs.resource_id = rd.resource_id AND rd.user_id = ? WHERE rs.status = ? AND rs.education_type = ? ORDER BY COALESCE(rd.score, 0) DESC, rs.view_count DESC LIMIT ? ''', (user_id, 'approved', education_type, count))
                results = [dict(r) for r in cursor.fetchall()]
                for res in results:
                    rec_id = f"rec_{uuid.uuid4().hex[:10]}"
                    score = res.get('behavior_score', 0) * 0.7 + res.get('view_count', 0) * 0.01
                    cursor.execute(''' INSERT INTO resource_recommendation (rec_id, user_id, resource_id, recommendation_type, score, reason, education_type, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ''', (rec_id, user_id, res['resource_id'], 'personalized', score, '基于用户行为推荐', education_type, now))
                conn.commit()
                return {'success': True, 'recommendations': results}
        except Exception as e:
            logger.error(f'生成个性化推荐失败: {e}')
            return {'success': False, 'error': str(e)}

    def generate_popular_recommendations(self, education_type: str, count: int = 10,
                                         period: str = 'month') -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query_sql = ''' SELECT * FROM resource_search WHERE status = ? AND education_type = ? ORDER BY view_count DESC, download_count DESC LIMIT ? '''
                cursor.execute(query_sql, ('approved', education_type, count))
                results = [dict(r) for r in cursor.fetchall()]
                for res in results:
                    rec_id = f"rec_{uuid.uuid4().hex[:10]}"
                    score = res.get('view_count', 0) * 0.5 + res.get('download_count', 0) * 0.3 + res.get('share_count',
                    0) * 0.2
                    cursor.execute(''' INSERT INTO resource_recommendation (rec_id, user_id, resource_id, recommendation_type, score, reason, education_type, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ''', (rec_id, None, res['resource_id'], 'popular', score, '热门资源推荐', education_type, now))
                conn.commit()
                return {'success': True, 'recommendations': results}
        except Exception as e:
            logger.error(f'生成热门推荐失败: {e}')
            return {'success': False, 'error': str(e)}

    def generate_similar_recommendations(self, resource_id: str, education_type: str,
                                         count: int = 10) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT resource_type, subject, tags FROM resource_search WHERE resource_id = ?',
                (resource_id,))
                source = cursor.fetchone()
                if not source:
                    return {'success': False, 'error': '资源不存在'}
                query_sql = ''' SELECT * FROM resource_search WHERE status = ? AND education_type = ? AND resource_id != ? AND resource_type = ? '''
                params = ['approved', education_type, resource_id, source[0]]
                if source[1]:
                    query_sql += ' AND subject = ?'
                    params.append(source[1])
                if source[2]:
                    query_sql += ' AND tags LIKE ?'
                    params.append(f'%{source[2]}%')
                query_sql += ' ORDER BY rating DESC LIMIT ?'
                params.append(count)
                cursor.execute(query_sql, params)
                results = [dict(r) for r in cursor.fetchall()]
                for res in results:
                    rec_id = f"rec_{uuid.uuid4().hex[:10]}"
                    score = res.get('rating', 0) * 0.8 + res.get('view_count', 0) * 0.01
                    cursor.execute(''' INSERT INTO resource_recommendation (rec_id, user_id, resource_id, recommendation_type, score, reason, education_type, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ''', (rec_id, None, res['resource_id'], 'similar', score, '相似资源推荐', education_type, now))
                conn.commit()
                return {'success': True, 'recommendations': results}
        except Exception as e:
            logger.error(f'生成相似推荐失败: {e}')
            return {'success': False, 'error': str(e)}

    def generate_related_recommendations(self, resource_id: str, education_type: str,
                                         count: int = 10) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT subject, grade_level FROM resource_search WHERE resource_id = ?', (resource_id,))
                source = cursor.fetchone()
                if not source:
                    return {'success': False, 'error': '资源不存在'}
                query_sql = ''' SELECT * FROM resource_search WHERE status = ? AND education_type = ? AND resource_id != ? '''
                params = ['approved', education_type, resource_id]
                if source[0]:
                    query_sql += ' AND subject = ?'
                    params.append(source[0])
                if source[1]:
                    query_sql += ' AND grade_level = ?'
                    params.append(source[1])
                query_sql += ' ORDER BY download_count DESC LIMIT ?'
                params.append(count)
                cursor.execute(query_sql, params)
                results = [dict(r) for r in cursor.fetchall()]
                for res in results:
                    rec_id = f"rec_{uuid.uuid4().hex[:10]}"
                    score = res.get('download_count', 0) * 0.6 + res.get('share_count', 0) * 0.4
                    cursor.execute(''' INSERT INTO resource_recommendation (rec_id, user_id, resource_id, recommendation_type, score, reason, education_type, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ''', (rec_id, None, res['resource_id'], 'related', score, '关联资源推荐', education_type, now))
                conn.commit()
                return {'success': True, 'recommendations': results}
        except Exception as e:
            logger.error(f'生成关联推荐失败: {e}')
            return {'success': False, 'error': str(e)}

    def track_recommendation_click(self, rec_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE resource_recommendation SET clicked = clicked + 1 WHERE rec_id = ?', (rec_id,
                    ))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '推荐记录不存在'}
        except Exception as e:
            logger.error(f'追踪推荐点击失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 资源评估服务 ==========

    def create_assessment(self, resource_id: str, assessor_id: int,
                          education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            assess_id = f"ass_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            scores = {}
            for criteria in ASSESSMENT_CRITERIA:
                scores[criteria] = kwargs.get(f'{criteria}_score', 0)
            overall_score = sum(score * ASSESSMENT_CRITERIA[criteria]['weight']
                               for criteria, score in scores.items())
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO resource_assessment ( assess_id, resource_id, assessor_id, assessor_name, criteria, scores, overall_score, comments, assessment_date, education_type, status, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?) ''', (assess_id, resource_id, assessor_id, kwargs.get('assessor_name'),
                          json.dumps(list(ASSESSMENT_CRITERIA.keys())),
                          json.dumps(scores), round(overall_score, 2),
                          kwargs.get('comments'), now[:10], education_type, now))
                    conn.commit()
                    return {'success': True, 'assess_id': assess_id, 'overall_score': round(overall_score, 2)}
        except Exception as e:
            logger.error(f'创建评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_assessment(self, assess_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM resource_assessment WHERE assess_id = ? AND status = ?', (assess_id,
                    'pending'))
                    assessment = cursor.fetchone()
                    if not assessment:
                        return {'success': False, 'error': '评估不存在或状态不允许审核'}
                    scores = json.loads(assessment[5]) if assessment[5] else {}
                    cursor.execute(''' INSERT OR REPLACE INTO assessment_results ( result_id, resource_id, quality_score, applicability_score, timeliness_score, completeness_score, accuracy_score, innovation_score, usability_score, value_score, overall_score, last_assessed, education_type ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (f"rst_{uuid.uuid4().hex[:10]}", assessment[1],
                          scores.get('quality', 0), scores.get('applicability', 0),
                          scores.get('timeliness', 0), scores.get('completeness', 0),
                          scores.get('accuracy', 0), scores.get('innovation', 0),
                          scores.get('usability', 0), scores.get('value', 0),
                          assessment[6], now[:10], assessment[9]))
                    cursor.execute('UPDATE resource_assessment SET status = ? WHERE assess_id = ?', ('approved',
                    assess_id))
                    cursor.execute('UPDATE resource_search SET rating = ? WHERE resource_id = ?', (assessment[6],
                    assessment[1]))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'审核评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_assessment_report(self, resource_id: str, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query_sql = ''' SELECT ar.*, ra.overall_score as latest_score, ra.last_assessed FROM resource_assessment ar LEFT JOIN assessment_results ra ON ar.resource_id = ra.resource_id WHERE ar.resource_id = ? '''
                params = [resource_id]
                if education_type:
                    query_sql += ' AND ar.education_type = ?'
                    params.append(education_type)
                query_sql += ' ORDER BY ar.created_at DESC'
                cursor.execute(query_sql, params)
                results = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'assessments': results, 'total': len(results)}
        except Exception as e:
            logger.error(f'获取评估报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_quality_summary(self, library_id: str = None, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query_sql = ''' SELECT education_type, AVG(overall_score) as avg_score, COUNT(*) as assess_count, MIN(overall_score) as min_score, MAX(overall_score) as max_score FROM assessment_results WHERE 1=1 '''
                params = []
                if library_id:
                    query_sql += ' AND resource_id IN (SELECT resource_id FROM resource_search WHERE library_id = ?)'
                    params.append(library_id)
                if education_type:
                    query_sql += ' AND education_type = ?'
                    params.append(education_type)
                query_sql += ' GROUP BY education_type'
                cursor.execute(query_sql, params)
                results = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'quality_summary': results}
        except Exception as e:
            logger.error(f'获取质量汇总失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 资源统计服务 ==========

    def get_usage_statistics(self, library_id: str = None, education_type: str = None,
                             period: str = 'month') -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query_sql = ''' SELECT education_type, SUM(view_count) as total_views, SUM(download_count) as total_downloads, SUM(share_count) as total_shares, COUNT(*) as resource_count FROM resource_search WHERE status = ? '''
                params = ['approved']
                if library_id:
                    query_sql += ' AND library_id = ?'
                    params.append(library_id)
                if education_type:
                    query_sql += ' AND education_type = ?'
                    params.append(education_type)
                query_sql += ' GROUP BY education_type'
                cursor.execute(query_sql, params)
                results = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'statistics': results}
        except Exception as e:
            logger.error(f'获取使用统计失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_access_analysis(self, resource_id: str = None, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query_sql = ''' SELECT rs.resource_id, rs.title, rs.education_type, rs.view_count, rs.download_count, rs.share_count, rs.upload_date FROM resource_search rs WHERE rs.status = ? '''
                params = ['approved']
                if resource_id:
                    query_sql += ' AND rs.resource_id = ?'
                    params.append(resource_id)
                if education_type:
                    query_sql += ' AND rs.education_type = ?'
                    params.append(education_type)
                query_sql += ' ORDER BY rs.view_count DESC LIMIT 50'
                cursor.execute(query_sql, params)
                results = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'access_data': results}
        except Exception as e:
            logger.error(f'获取访问分析失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_download_statistics(self, education_type: str = None, period: str = 'month') -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query_sql = ''' SELECT rs.resource_type, rt.name as type_name, SUM(rs.download_count) as total_downloads, COUNT(*) as resource_count FROM resource_search rs LEFT JOIN (SELECT * FROM (VALUES ('course', '课程资源'), ('teaching', '教学资源'), ('learning', '学习资源'), ('research', '科研资源'), ('assessment', '评估资源'), ('management', '管理资源'), ('training', '培训资源'), ('comprehensive', '综合资源') )) rt(code, name) ON rs.resource_type = rt.code WHERE rs.status = ? '''
                params = ['approved']
                if education_type:
                    query_sql += ' AND rs.education_type = ?'
                    params.append(education_type)
                query_sql += ' GROUP BY rs.resource_type, rt.name'
                cursor.execute(query_sql, params)
                results = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'download_stats': results}
        except Exception as e:
            logger.error(f'获取下载统计失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_trend_analysis(self, education_type: str = None, days: int = 30) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query_sql = ''' SELECT DATE(rs.upload_date) as date, rs.education_type, COUNT(*) as upload_count, SUM(rs.view_count) as total_views, SUM(rs.download_count) as total_downloads FROM resource_search rs WHERE rs.status = ? AND rs.upload_date >= ? '''
                params = ['approved', (datetime.now() - timedelta(days=days)).isoformat()[:10]]
                if education_type:
                    query_sql += ' AND rs.education_type = ?'
                    params.append(education_type)
                query_sql += ' GROUP BY date, education_type ORDER BY date'
                cursor.execute(query_sql, params)
                results = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'trend_data': results}
        except Exception as e:
            logger.error(f'获取趋势分析失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 资源权限管理 ==========

    def grant_permission(self, resource_id: str, user_id: int, permission_level: str,
                         education_type: str = None, **kwargs) -> Dict[str, Any]:
        try:
            if permission_level not in PERMISSION_LEVELS:
                return {'success': False, 'error': '权限级别无效'}

            perm_id = f"prm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            expire_date = None
            if kwargs.get('expire_days'):
                expire_date = (datetime.now() + timedelta(days=kwargs['expire_days'])).isoformat()[:10]
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO resource_permissions ( perm_id, resource_id, library_id, user_id, permission_level, granted_by, granted_at, expire_date, status, education_type ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?) ''', (perm_id, resource_id, kwargs.get('library_id'), user_id,
                          permission_level, kwargs.get('granted_by'), now,
                          expire_date, education_type))
                    record_id = f"rec_{uuid.uuid4().hex[:10]}"
                    cursor.execute('INSERT INTO permission_records (record_id, perm_id, user_id, action, action_time, resource_id, education_type) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                 (record_id, perm_id, user_id, 'grant', now, resource_id, education_type))
                    conn.commit()
                    return {'success': True, 'perm_id': perm_id}
        except Exception as e:
            logger.error(f'授予权限失败: {e}')
            return {'success': False, 'error': str(e)}

    def revoke_permission(self, perm_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE resource_permissions SET status = ? WHERE perm_id = ?', ('revoked', perm_id))
                    if cursor.rowcount > 0:
                        record_id = f"rec_{uuid.uuid4().hex[:10]}"
                        cursor.execute('INSERT INTO permission_records (record_id, perm_id, user_id, action, action_time) SELECT ?, ?, user_id, ?, ? FROM resource_permissions WHERE perm_id = ?',
                                     (record_id, perm_id, 'revoke', datetime.now().isoformat(), perm_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '权限记录不存在'}
        except Exception as e:
            logger.error(f'撤销权限失败: {e}')
            return {'success': False, 'error': str(e)}

    def check_permission(self, resource_id: str, user_id: int, action: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(''' SELECT rp.permission_level, rp.status, rp.expire_date FROM resource_permissions rp WHERE rp.resource_id = ? AND rp.user_id = ? AND rp.status = ? ''', (resource_id, user_id, 'active'))
                perm = cursor.fetchone()
                if not perm:
                    return {'success': True, 'has_permission': False, 'message': '无权限'}
                if perm[2] and perm[2] < datetime.now().isoformat()[:10]:
                    cursor.execute(
                    'UPDATE resource_permissions SET status = ? WHERE permission_level = ? AND user_id = ?', ('expired',
                    perm[0], user_id))
                    conn.commit()
                    return {'success': True, 'has_permission': False, 'message': '权限已过期'}
                perm_config = PERMISSION_LEVELS.get(perm[0], {})
                access_map = {'admin': ['view', 'download', 'edit', 'delete', 'manage'],
                              'editor': ['view', 'download', 'edit'],
                              'reviewer': ['view', 'download'],
                              'viewer': ['view'],
                              'downloader': ['view', 'download'],
                              'uploader': ['upload'],
                              'deleter': ['delete'],
                              'manager': ['view', 'download', 'edit', 'manage']}
                has_access = action in access_map.get(perm[0], [])
                return {'success': True, 'has_permission': has_access,
                        'permission_level': perm_config.get('name'), 'message': '有权限' if has_access else '权限不足'}
        except Exception as e:
            logger.error(f'检查权限失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_permission_logs(self, user_id: int = None, resource_id: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query_sql = 'SELECT * FROM permission_records WHERE 1=1'
                params = []
                if user_id:
                    query_sql += ' AND user_id = ?'
                    params.append(user_id)
                if resource_id:
                    query_sql += ' AND resource_id = ?'
                    params.append(resource_id)
                query_sql += ' ORDER BY action_time DESC LIMIT 100'
                cursor.execute(query_sql, params)
                results = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'logs': results}
        except Exception as e:
            logger.error(f'获取权限日志失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 资源迁移服务 ==========

    def create_migration(self, source_library: str, target_library: str,
                         migration_method: str, education_type: str = None,
                         **kwargs) -> Dict[str, Any]:
        try:
            if migration_method not in MIGRATION_METHODS:
                return {'success': False, 'error': '迁移方法无效'}

            migrate_id = f"mig_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT COUNT(*) FROM resource_search WHERE library_id = ? AND education_type = ?',
                                 (source_library, education_type))
                    total_count = cursor.fetchone()[0]
                    cursor.execute(''' INSERT INTO resource_migration ( migrate_id, source_library, target_library, migration_method, status, total_count, success_count, failed_count, start_time, error_message, education_type, created_at ) VALUES (?, ?, ?, ?, 'pending', ?, 0, 0, ?, ?, ?, ?) ''', (migrate_id, source_library, target_library, migration_method,
                          total_count, now, kwargs.get('error_message'), education_type, now))
                    conn.commit()
                    return {'success': True, 'migrate_id': migrate_id, 'total_count': total_count}
        except Exception as e:
            logger.error(f'创建迁移任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def execute_migration(self, migrate_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM resource_migration WHERE migrate_id = ? AND status = ?', (migrate_id,
                    'pending'))
                    migration = cursor.fetchone()
                    if not migration:
                        return {'success': False, 'error': '迁移任务不存在或已执行'}
                    cursor.execute('UPDATE resource_migration SET status = ?, start_time = ? WHERE migrate_id = ?',
                                 ('running', now, migrate_id))
                    cursor.execute(
                    'SELECT resource_id FROM resource_search WHERE library_id = ? AND education_type = ?',
                                 (migration[1], migration[11]))
                    resources = cursor.fetchall()
                    success_count = 0
                    failed_count = 0
                    for res in resources:
                        record_id = f"mrc_{uuid.uuid4().hex[:10]}"
                        try:
                            cursor.execute('UPDATE resource_search SET library_id = ? WHERE resource_id = ?',
                                         (migration[2], res[0]))
                            cursor.execute('INSERT INTO migration_records (record_id, migrate_id, resource_id, status) VALUES (?, ?, ?, ?)',
                                         (record_id, migrate_id, res[0], 'success'))
                            success_count += 1
                        except Exception as me:
                            cursor.execute('INSERT INTO migration_records (record_id, migrate_id, resource_id, status, error_message) VALUES (?, ?, ?, ?, ?)',
                                         (record_id, migrate_id, res[0], 'failed', str(me)))
                            failed_count += 1
                    cursor.execute('UPDATE resource_migration SET status = ?, success_count = ?, failed_count = ?, end_time = ? WHERE migrate_id = ?',
                                 ('completed', success_count, failed_count, now, migrate_id))
                    conn.commit()
                    return {'success': True, 'success_count': success_count, 'failed_count': failed_count}
        except Exception as e:
            logger.error(f'执行迁移失败: {e}')
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE resource_migration SET status = ?, error_message = ?, end_time = ? WHERE migrate_id = ?',
                             ('failed', str(e), datetime.now().isoformat(), migrate_id))
                conn.commit()
            return {'success': False, 'error': str(e)}

    def get_migration_status(self, migrate_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM resource_migration WHERE migrate_id = ?', (migrate_id,))
                migration = cursor.fetchone()
                if not migration:
                    return {'success': False, 'error': '迁移任务不存在'}
                cursor.execute('SELECT COUNT(*) as total, SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as success, SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as failed FROM migration_records WHERE migrate_id = ?',
                             ('success', 'failed', migrate_id))
                records = cursor.fetchone()
                return {'success': True, 'migration': dict(migration), 'records': dict(records) if records else None}
        except Exception as e:
            logger.error(f'获取迁移状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def cancel_migration(self, migrate_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE resource_migration SET status = ? WHERE migrate_id = ? AND status = ?',
                                 ('cancelled', migrate_id, 'pending'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '迁移任务不存在或状态不允许取消'}
        except Exception as e:
            logger.error(f'取消迁移失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计服务 ==========

    def get_comprehensive_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                stats = {}
                query_sql = ''' SELECT education_type, COUNT(*) as total, SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as approved, SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as pending FROM resource_search WHERE 1=1 '''
                params = ['approved', 'pending']
                if education_type:
                    query_sql += ' AND education_type = ?'
                    params.append(education_type)
                query_sql += ' GROUP BY education_type'
                cursor.execute(query_sql, params)
                stats['resources'] = [dict(r) for r in cursor.fetchall()]
                query_sql = ''' SELECT education_type, COUNT(*) as total, SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as active, SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as revoked FROM resource_permissions WHERE 1=1 '''
                params = ['active', 'revoked']
                if education_type:
                    query_sql += ' AND education_type = ?'
                    params.append(education_type)
                query_sql += ' GROUP BY education_type'
                cursor.execute(query_sql, params)
                stats['permissions'] = [dict(r) for r in cursor.fetchall()]
                query_sql = ''' SELECT education_type, COUNT(*) as total, SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as completed, SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as failed FROM resource_migration WHERE 1=1 '''
                params = ['completed', 'failed']
                if education_type:
                    query_sql += ' AND education_type = ?'
                    params.append(education_type)
                query_sql += ' GROUP BY education_type'
                cursor.execute(query_sql, params)
                stats['migrations'] = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'statistics': stats}
        except Exception as e:
            logger.error(f'获取综合统计失败: {e}')
            return {'success': False, 'error': str(e)}















































































































































