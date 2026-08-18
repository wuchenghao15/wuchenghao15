from core.db_path import get_db_path as _mtscos_get_db_path
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS 教育内容管理服务 (v15.27.0) ================================= 提供教育内容的创作、审核、发布、版本、分类、标签、检索和推荐等综合管理服务。  核心能力： 1. 内容创作管理 - 在线创作、编辑、协作、AI辅助 2. 内容审核管理 - 多级审核、状态跟踪、修改反馈 3. 内容发布管理 - 多渠道发布、定时发布、状态管理 4. 内容版本管理 - 版本控制、历史记录、回退恢复 5. 内容分类管理 - 学科分类、学段分类、资源类型 6. 内容标签管理 - 知识点标签、难度标签、教学目标 7. 内容检索管理 - 全文搜索、筛选过滤、排序分页 8. 内容推荐管理 - 个性化推荐、智能推荐、热门推荐  差异化支持： - 成人教育 - 职业培训、继续教育、学历提升 - K12教育 - 基础教育、学科辅导、素质教育 """
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_content_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationContent')


# ========== 教育内容配置 ==========

CONTENT_TYPES = {
    'course_content': {'name': '课程内容', 'description': '系统化的课程教学内容', 'education_types': ['k12', 'adult']},
    'teaching_resource': {'name': '教学资源', 'description': '教案、课件、教学辅助材料', 'education_types': ['k12', 'adult']},
    'learning_material': {'name': '学习资料', 'description': '讲义、习题、参考资料', 'education_types': ['k12', 'adult']},
    'exam_question': {'name': '考试题库', 'description': '试题、试卷、标准答案', 'education_types': ['k12', 'adult']},
    'teaching_video': {'name': '教学视频', 'description': '微课、直播录播、教学片', 'education_types': ['k12', 'adult']},
    'teaching_audio': {'name': '教学音频', 'description': '有声读物、音频课程、播客', 'education_types': ['k12', 'adult']},
    'graphic_content': {'name': '图文资料', 'description': '图文并茂的学习内容', 'education_types': ['k12', 'adult']},
    'interactive_content': {'name': '互动内容', 'description': '在线测验、互动游戏、模拟实验', 'education_types': ['k12', 'adult']}
}

CREATION_TOOLS = {
    'online_editor': {'name': '在线编辑器', 'features': ['富文本', '实时保存', '多格式导出']},
    'rich_text_editor': {'name': '富文本编辑器', 'features': ['图文混排', '公式编辑', '多媒体嵌入']},
    'video_editor': {'name': '视频编辑器', 'features': ['剪辑', '字幕', '特效']},
    'audio_editor': {'name': '音频编辑器', 'features': ['录音', '剪辑', '降噪']},
    'mind_map': {'name': '思维导图', 'features': ['结构化展示', '关联分析', '协作编辑']},
    'collaboration_tool': {'name': '协作工具', 'features': ['多人协作', '版本同步', '评论批注']},
    'ai_assistant': {'name': 'AI辅助创作', 'features': ['智能生成', '内容优化', '自动摘要']},
    'template_library': {'name': '模板库', 'features': ['预设模板', '快速套用', '自定义模板']}
}

REVIEW_STAGES = {
    'submitted': {'name': '提交审核', 'order': 1},
    'first_review': {'name': '初审', 'order': 2},
    'second_review': {'name': '复审', 'order': 3},
    'final_review': {'name': '终审', 'order': 4},
    'revision': {'name': '修改', 'order': 5},
    'rejected': {'name': '驳回', 'order': 6},
    'approved': {'name': '通过', 'order': 7},
    'published': {'name': '发布', 'order': 8}
}

PUBLISH_CHANNELS = {
    'internal_platform': {'name': '校内平台', 'description': '学校内部学习平台', 'education_types': ['k12', 'adult']},
    'external_platform': {'name': '校外平台', 'description': '对外公开学习平台', 'education_types': ['k12', 'adult']},
    'mobile': {'name': '移动端', 'description': '手机APP、移动网页', 'education_types': ['k12', 'adult']},
    'pc': {'name': 'PC端', 'description': '电脑网页、桌面应用', 'education_types': ['k12', 'adult']},
    'mini_program': {'name': '小程序', 'description': '微信小程序、支付宝小程序', 'education_types': ['k12', 'adult']},
    'app': {'name': 'APP', 'description': '独立移动应用', 'education_types': ['k12', 'adult']},
    'website': {'name': '网站', 'description': '独立网站', 'education_types': ['adult']},
    'social_media': {'name': '社交媒体', 'description': '微信公众号、微博等', 'education_types': ['k12', 'adult']}
}

VERSION_STATUS = {
    'draft': {'name': '草稿', 'description': '未完成的内容草稿'},
    'beta': {'name': '测试版', 'description': '内部测试版本'},
    'official': {'name': '正式版', 'description': '正式发布版本'},
    'update': {'name': '更新版', 'description': '已更新的版本'},
    'historical': {'name': '历史版', 'description': '历史归档版本'},
    'archived': {'name': '归档版', 'description': '长期归档版本'},
    'deleted': {'name': '删除版', 'description': '已删除的版本'},
    'rolled_back': {'name': '回退版', 'description': '回退到的历史版本'}
}

CATEGORIES = {
    'subject': {'name': '学科分类', 'items': ['语文', '数学', '英语', '物理', '化学', '生物', '历史', '地理', '政治', '信息技术']},
    'school_stage': {'name': '学段分类', 'items': ['幼儿园', '小学', '初中', '高中', '大学', '研究生', '职业教育', '继续教育']},
    'grade': {'name': '年级分类', 'items': ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级', '初一', '初二', '初三', '高一', '高二', '高三']},
    'course': {'name': '课程分类', 'items': ['必修课程', '选修课程', '校本课程', '特色课程', '兴趣课程', '竞赛课程']},
    'theme': {'name': '主题分类', 'items': ['基础知识点', '拓展延伸', '综合应用', '实践活动', '专题讲座', '复习巩固']},
    'difficulty': {'name': '难度分类', 'items': ['入门级', '基础级', '进阶级', '提高级', '挑战级', '专业级']},
    'resource_type': {'name': '资源类型', 'items': ['文本', '图片', '视频', '音频', '文档', '课件', '软件', '数据']},
    'target_audience': {'name': '适用对象', 'items': ['学生', '教师', '家长', '管理人员', '社会人员', '专业人士']}
}

TAG_TYPES = {
    'subject_tag': {'name': '学科标签', 'description': '学科相关标签'},
    'knowledge_point': {'name': '知识点标签', 'description': '具体知识点'},
    'difficulty_tag': {'name': '难度标签', 'description': '难度等级'},
    'audience': {'name': '适用人群', 'description': '目标受众'},
    'teaching_objective': {'name': '教学目标', 'description': '教学目标/能力要求'},
    'learning_method': {'name': '学习方式', 'description': '学习方式/策略'},
    'resource_format': {'name': '资源格式', 'description': '资源文件格式'},
    'language': {'name': '语言', 'description': '内容语言'}
}

RECOMMENDATION_METHODS = {
    'personalized': {'name': '个性化推荐', 'description': '基于用户画像的推荐'},
    'popular': {'name': '热门推荐', 'description': '基于浏览量、点赞数'},
    'related': {'name': '相关推荐', 'description': '基于内容相关性'},
    'latest': {'name': '最新推荐', 'description': '基于发布时间'},
    'category': {'name': '分类推荐', 'description': '基于分类浏览'},
    'search': {'name': '搜索推荐', 'description': '基于搜索历史'},
    'collaborative': {'name': '协同推荐', 'description': '基于用户行为协同'},
    'intelligent': {'name': '智能推荐', 'description': '基于AI算法'}
}


class EducationContentService:
    """教育内容管理服务"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._lock = threading.RLock()
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' CREATE TABLE IF NOT EXISTS content_creation ( content_id TEXT PRIMARY KEY, content_title TEXT NOT NULL, content_type TEXT NOT NULL, education_type TEXT NOT NULL, creator_id INTEGER NOT NULL, creator_name TEXT, creation_tool TEXT, status TEXT DEFAULT 'draft', visibility TEXT DEFAULT 'private', version INTEGER DEFAULT 1, created_at TEXT, updated_at TEXT ) ''')
                    cursor.execute(''' CREATE TABLE IF NOT EXISTS creation_records ( record_id INTEGER PRIMARY KEY AUTOINCREMENT, content_id TEXT NOT NULL, action TEXT NOT NULL, action_type TEXT, user_id INTEGER, user_name TEXT, timestamp TEXT, details TEXT ) ''')
                    cursor.execute(''' CREATE TABLE IF NOT EXISTS content_review ( review_id TEXT PRIMARY KEY, content_id TEXT NOT NULL, current_stage TEXT DEFAULT 'submitted', reviewer_id INTEGER, reviewer_name TEXT, review_comments TEXT, review_score INTEGER, status TEXT DEFAULT 'pending', created_at TEXT, updated_at TEXT ) ''')
                    cursor.execute(''' CREATE TABLE IF NOT EXISTS review_records ( record_id INTEGER PRIMARY KEY AUTOINCREMENT, review_id TEXT NOT NULL, stage TEXT NOT NULL, action TEXT NOT NULL, reviewer_id INTEGER, reviewer_name TEXT, comments TEXT, timestamp TEXT ) ''')
                    cursor.execute(''' CREATE TABLE IF NOT EXISTS content_publish ( publish_id TEXT PRIMARY KEY, content_id TEXT NOT NULL, channel TEXT NOT NULL, status TEXT DEFAULT 'pending', publish_time TEXT, unpublish_time TEXT, publish_version INTEGER, created_at TEXT, updated_at TEXT ) ''')
                    cursor.execute(''' CREATE TABLE IF NOT EXISTS publish_records ( record_id INTEGER PRIMARY KEY AUTOINCREMENT, publish_id TEXT NOT NULL, action TEXT NOT NULL, user_id INTEGER, user_name TEXT, timestamp TEXT, details TEXT ) ''')
                    cursor.execute(''' CREATE TABLE IF NOT EXISTS content_version ( version_id TEXT PRIMARY KEY, content_id TEXT NOT NULL, version_number INTEGER NOT NULL, version_status TEXT DEFAULT 'draft', content_snapshot TEXT, change_log TEXT, creator_id INTEGER, creator_name TEXT, created_at TEXT ) ''')
                    cursor.execute(''' CREATE TABLE IF NOT EXISTS version_history ( history_id INTEGER PRIMARY KEY AUTOINCREMENT, content_id TEXT NOT NULL, version_id TEXT NOT NULL, action TEXT NOT NULL, user_id INTEGER, user_name TEXT, timestamp TEXT ) ''')
                    cursor.execute(''' CREATE TABLE IF NOT EXISTS content_category ( category_id TEXT PRIMARY KEY, category_type TEXT NOT NULL, category_name TEXT NOT NULL, parent_id TEXT, education_type TEXT, sort_order INTEGER DEFAULT 0, is_active INTEGER DEFAULT 1, created_at TEXT, updated_at TEXT ) ''')
                    cursor.execute(''' CREATE TABLE IF NOT EXISTS category_items ( item_id INTEGER PRIMARY KEY AUTOINCREMENT, category_id TEXT NOT NULL, content_id TEXT NOT NULL, added_by INTEGER, added_at TEXT, UNIQUE(category_id, content_id) ) ''')
                    cursor.execute(''' CREATE TABLE IF NOT EXISTS content_tags ( tag_id TEXT PRIMARY KEY, tag_name TEXT NOT NULL, tag_type TEXT NOT NULL, education_type TEXT, usage_count INTEGER DEFAULT 0, is_active INTEGER DEFAULT 1, created_at TEXT, updated_at TEXT ) ''')
                    cursor.execute(''' CREATE TABLE IF NOT EXISTS tag_items ( item_id INTEGER PRIMARY KEY AUTOINCREMENT, tag_id TEXT NOT NULL, content_id TEXT NOT NULL, added_by INTEGER, added_at TEXT, UNIQUE(tag_id, content_id) ) ''')
                    cursor.execute(''' CREATE TABLE IF NOT EXISTS content_search ( search_id TEXT PRIMARY KEY, keyword TEXT NOT NULL, education_type TEXT, content_type TEXT, category TEXT, results_count INTEGER DEFAULT 0, searched_at TEXT ) ''')
                    cursor.execute(''' CREATE TABLE IF NOT EXISTS search_records ( record_id INTEGER PRIMARY KEY AUTOINCREMENT, search_id TEXT NOT NULL, content_id TEXT NOT NULL, rank INTEGER, score REAL, clicked INTEGER DEFAULT 0, clicked_at TEXT ) ''')
                    cursor.execute(''' CREATE TABLE IF NOT EXISTS content_recommendation ( rec_id TEXT PRIMARY KEY, user_id INTEGER NOT NULL, method TEXT NOT NULL, content_id TEXT NOT NULL, score REAL DEFAULT 0, displayed INTEGER DEFAULT 0, clicked INTEGER DEFAULT 0, created_at TEXT, updated_at TEXT ) ''')
                    cursor.execute(''' CREATE TABLE IF NOT EXISTS recommendation_records ( record_id INTEGER PRIMARY KEY AUTOINCREMENT, rec_id TEXT NOT NULL, action TEXT NOT NULL, user_id INTEGER, timestamp TEXT, details TEXT ) ''')
                    conn.commit()
                    logger.info('教育内容管理服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 内容创作管理 ==========

    def create_content(self, content_title: str, content_type: str,
                       education_type: str, creator_id: int,
                       **kwargs) -> Dict[str, Any]:
        try:
            content_id = f"cnt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = CONTENT_TYPES.get(content_type, {})
            if education_type not in config.get('education_types', []):
                return {'success': False, 'error': f'该内容类型不支持{education_type}教育'}
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO content_creation ( content_id, content_title, content_type, education_type, creator_id, creator_name, creation_tool, status, visibility, version, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?) ''', (content_id, content_title, content_type,
                          education_type, creator_id, kwargs.get('creator_name'),
                          kwargs.get('creation_tool'), 'draft',
                          kwargs.get('visibility', 'private'), now, now))
                    cursor.execute(''' INSERT INTO creation_records (content_id, action, action_type, user_id, user_name, timestamp, details) VALUES (?, 'create', 'creation', ?, ?, ?, ?) ''', (content_id, creator_id, kwargs.get('creator_name'),
                          now, json.dumps({'title': content_title, 'type': content_type})))
                    conn.commit()
                    logger.info(f'创建内容: {content_title} ({content_id})')
                    return {'success': True, 'content_id': content_id}
        except Exception as e:
            logger.error(f'创建内容失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_content(self, content_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status, version FROM content_creation WHERE content_id = ?', (content_id,))
                    content = cursor.fetchone()
                    if not content:
                        return {'success': False, 'error': '内容不存在'}
                    updates = []
                    params = []
                    if 'content_title' in kwargs:
                        updates.append('content_title = ?')
                        params.append(kwargs['content_title'])
                    if 'creation_tool' in kwargs:
                        updates.append('creation_tool = ?')
                        params.append(kwargs['creation_tool'])
                    if 'visibility' in kwargs:
                        updates.append('visibility = ?')
                        params.append(kwargs['visibility'])
                    updates.append('version = ?')
                    params.append(content[1] + 1)
                    updates.append('updated_at = ?')
                    params.append(now)
                    params.append(content_id)
                    cursor.execute(f'UPDATE content_creation SET {", ".join(updates)} WHERE content_id = ?', params)
                    cursor.execute(''' INSERT INTO creation_records (content_id, action, action_type, user_id, user_name, timestamp, details) VALUES (?, 'update', 'modification', ?, ?, ?, ?) ''', (content_id, kwargs.get('user_id'), kwargs.get('user_name'),
                          now, json.dumps(kwargs)))
                    conn.commit()
                    return {'success': True, 'version': content[1] + 1}
        except Exception as e:
            logger.error(f'更新内容失败: {e}')
            return {'success': False, 'error': str(e)}

    def save_draft(self, content_id: str, content_snapshot: str,
                   **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT version FROM content_creation WHERE content_id = ?', (content_id,))
                    content = cursor.fetchone()
                    if not content:
                        return {'success': False, 'error': '内容不存在'}
                    version_id = f"ver_{uuid.uuid4().hex[:12]}"
                    cursor.execute(''' INSERT INTO content_version ( version_id, content_id, version_number, version_status, content_snapshot, change_log, creator_id, creator_name, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (version_id, content_id, content[0], 'draft',
                          content_snapshot, kwargs.get('change_log'),
                          kwargs.get('user_id'), kwargs.get('user_name'), now))
                    cursor.execute(''' INSERT INTO creation_records (content_id, action, action_type, user_id, user_name, timestamp, details) VALUES (?, 'save_draft', 'saving', ?, ?, ?, '草稿保存') ''', (content_id, kwargs.get('user_id'), kwargs.get('user_name'), now))
                    conn.commit()
                    return {'success': True, 'version_id': version_id}
        except Exception as e:
            logger.error(f'保存草稿失败: {e}')
            return {'success': False, 'error': str(e)}

    def submit_for_review(self, content_id: str, submitter_id: int,
                          **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type, content_type FROM content_creation WHERE content_id = ?',
                    (content_id,))
                    content = cursor.fetchone()
                    if not content:
                        return {'success': False, 'error': '内容不存在'}
                    cursor.execute('UPDATE content_creation SET status = ? WHERE content_id = ?', ('submitted',
                    content_id))
                    review_id = f"rev_{uuid.uuid4().hex[:12]}"
                    cursor.execute(''' INSERT INTO content_review ( review_id, content_id, current_stage, reviewer_id, reviewer_name, review_comments, review_score, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (review_id, content_id, 'submitted',
                          kwargs.get('reviewer_id'), kwargs.get('reviewer_name'),
                          '', 0, 'pending', now, now))
                    cursor.execute(''' INSERT INTO creation_records (content_id, action, action_type, user_id, user_name, timestamp, details) VALUES (?, 'submit', 'submission', ?, ?, ?, '提交审核') ''', (content_id, submitter_id, kwargs.get('submitter_name'), now))
                    conn.commit()
                    return {'success': True, 'review_id': review_id}
        except Exception as e:
            logger.error(f'提交审核失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 内容审核管理 ==========

    def review_content(self, review_id: str, stage: str, action: str,
                       reviewer_id: int, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT content_id, current_stage FROM content_review WHERE review_id = ?',
                    (review_id,))
                    review = cursor.fetchone()
                    if not review:
                        return {'success': False, 'error': '审核记录不存在'}
                    if REVIEW_STAGES.get(stage, {}).get('order', 0) <= REVIEW_STAGES.get(review[1], {}).get('order', 0):
                        return {'success': False, 'error': '审核阶段顺序错误'}
                    if action == 'approve':
                        next_stage = {
                            'first_review': 'second_review',
                            'second_review': 'final_review',
                            'final_review': 'approved'
                        }.get(stage, 'approved')
                        status = 'approved' if next_stage == 'approved' else 'pending'
                        if next_stage == 'approved':
                            cursor.execute('UPDATE content_creation SET status = ? WHERE content_id = ?', ('approved',
                            review[0]))
                    elif action == 'reject':
                        next_stage = 'rejected'
                        status = 'rejected'
                        cursor.execute('UPDATE content_creation SET status = ? WHERE content_id = ?', ('rejected',
                        review[0]))
                    elif action == 'revision':
                        next_stage = 'revision'
                        status = 'revision'
                        cursor.execute('UPDATE content_creation SET status = ? WHERE content_id = ?', ('revision',
                        review[0]))
                    else:
                        return {'success': False, 'error': '无效的审核动作'}
                    cursor.execute(''' UPDATE content_review SET current_stage = ?, reviewer_id = ?, reviewer_name = ?, review_comments = ?, review_score = ?, status = ?, updated_at = ? WHERE review_id = ? ''', (next_stage, reviewer_id, kwargs.get('reviewer_name'),
                          kwargs.get('comments', ''), kwargs.get('score', 0),
                          status, now, review_id))
                    cursor.execute(''' INSERT INTO review_records (review_id, stage, action, reviewer_id, reviewer_name, comments, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?) ''', (review_id, stage, action, reviewer_id,
                          kwargs.get('reviewer_name'), kwargs.get('comments', ''), now))
                    conn.commit()
                    return {'success': True, 'current_stage': next_stage, 'status': status}
        except Exception as e:
            logger.error(f'审核内容失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_review_status(self, content_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM content_review WHERE content_id = ? ORDER BY created_at DESC',
                (content_id,))
                review = cursor.fetchone()
                if not review:
                    return {'success': False, 'error': '审核记录不存在'}
                cursor.execute('SELECT * FROM review_records WHERE review_id = ? ORDER BY timestamp ASC',
                (review['review_id'],))
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'review': dict(review), 'records': records}
        except Exception as e:
            logger.error(f'获取审核状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_review_comments(self, review_id: str, comments: str,
                               reviewer_id: int, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE content_review SET review_comments = ?, updated_at = ? WHERE review_id = ?',
                                 (comments, now, review_id))
                    cursor.execute(''' INSERT INTO review_records (review_id, stage, action, reviewer_id, reviewer_name, comments, timestamp) VALUES (?, ?, 'comment', ?, ?, ?, ?) ''', (review_id, kwargs.get('stage', 'comment'), reviewer_id,
                          kwargs.get('reviewer_name'), comments, now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'更新审核意见失败: {e}')
            return {'success': False, 'error': str(e)}

    def cancel_review(self, review_id: str, canceler_id: int, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT content_id FROM content_review WHERE review_id = ?', (review_id,))
                    review = cursor.fetchone()
                    if not review:
                        return {'success': False, 'error': '审核记录不存在'}
                    cursor.execute('UPDATE content_review SET status = ? WHERE review_id = ?', ('cancelled', review_id))
                    cursor.execute('UPDATE content_creation SET status = ? WHERE content_id = ?', ('draft', review[0]))
                    cursor.execute(''' INSERT INTO review_records (review_id, stage, action, reviewer_id, reviewer_name, comments, timestamp) VALUES (?, ?, 'cancel', ?, ?, ?, ?) ''', (review_id, 'cancel', canceler_id, kwargs.get('canceler_name'),
                          kwargs.get('reason', '取消审核'), now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'取消审核失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 内容发布管理 ==========

    def publish_content(self, content_id: str, channel: str,
                        publisher_id: int, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            config = PUBLISH_CHANNELS.get(channel, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type, status, version FROM content_creation WHERE content_id = ?',
                    (content_id,))
                    content = cursor.fetchone()
                    if not content:
                        return {'success': False, 'error': '内容不存在'}
                    if content[1] != 'approved':
                        return {'success': False, 'error': '内容未通过审核'}
                    if content[0] not in config.get('education_types', ['k12', 'adult']):
                        return {'success': False, 'error': f'该渠道不支持{content[0]}教育'}
                    publish_id = f"pub_{uuid.uuid4().hex[:12]}"
                    cursor.execute(''' INSERT INTO content_publish ( publish_id, content_id, channel, status, publish_time, publish_version, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ''', (publish_id, content_id, channel, 'published',
                          kwargs.get('publish_time', now), content[2], now, now))
                    cursor.execute('UPDATE content_creation SET status = ? WHERE content_id = ?', ('published',
                    content_id))
                    cursor.execute(''' INSERT INTO publish_records (publish_id, action, user_id, user_name, timestamp, details) VALUES (?, 'publish', ?, ?, ?, ?) ''', (publish_id, publisher_id, kwargs.get('publisher_name'),
                          now, json.dumps({'channel': channel})))
                    conn.commit()
                    return {'success': True, 'publish_id': publish_id}
        except Exception as e:
            logger.error(f'发布内容失败: {e}')
            return {'success': False, 'error': str(e)}

    def unpublish_content(self, publish_id: str, unpublisher_id: int,
                          **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT content_id FROM content_publish WHERE publish_id = ?', (publish_id,))
                    publish = cursor.fetchone()
                    if not publish:
                        return {'success': False, 'error': '发布记录不存在'}
                    cursor.execute('UPDATE content_publish SET status = ?, unpublish_time = ?, updated_at = ? WHERE publish_id = ?',
                                 ('unpublished', now, now, publish_id))
                    cursor.execute(''' INSERT INTO publish_records (publish_id, action, user_id, user_name, timestamp, details) VALUES (?, 'unpublish', ?, ?, ?, ?) ''', (publish_id, unpublisher_id, kwargs.get('unpublisher_name'),
                          now, kwargs.get('reason', '下架')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'下架内容失败: {e}')
            return {'success': False, 'error': str(e)}

    def schedule_publish(self, content_id: str, channel: str,
                         publish_time: str, scheduler_id: int,
                         **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM content_creation WHERE content_id = ?', (content_id,))
                    content = cursor.fetchone()
                    if not content:
                        return {'success': False, 'error': '内容不存在'}
                    publish_id = f"pub_{uuid.uuid4().hex[:12]}"
                    cursor.execute(''' INSERT INTO content_publish ( publish_id, content_id, channel, status, publish_time, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?) ''', (publish_id, content_id, channel, 'scheduled',
                          publish_time, now, now))
                    cursor.execute(''' INSERT INTO publish_records (publish_id, action, user_id, user_name, timestamp, details) VALUES (?, 'schedule', ?, ?, ?, ?) ''', (publish_id, scheduler_id, kwargs.get('scheduler_name'),
                          now, json.dumps({'channel': channel, 'publish_time': publish_time})))
                    conn.commit()
                    return {'success': True, 'publish_id': publish_id}
        except Exception as e:
            logger.error(f'定时发布失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_publish_status(self, content_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM content_publish WHERE content_id = ? ORDER BY created_at DESC',
                (content_id,))
                publishes = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'publishes': publishes}
        except Exception as e:
            logger.error(f'获取发布状态失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 版本管理 ==========

    def create_version(self, content_id: str, creator_id: int,
                       **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT version FROM content_creation WHERE content_id = ?', (content_id,))
                    content = cursor.fetchone()
                    if not content:
                        return {'success': False, 'error': '内容不存在'}
                    new_version = content[0] + 1
                    version_id = f"ver_{uuid.uuid4().hex[:12]}"
                    cursor.execute(''' INSERT INTO content_version ( version_id, content_id, version_number, version_status, content_snapshot, change_log, creator_id, creator_name, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (version_id, content_id, new_version,
                          kwargs.get('version_status', 'draft'),
                          kwargs.get('content_snapshot'),
                          kwargs.get('change_log'),
                          creator_id, kwargs.get('creator_name'), now))
                    cursor.execute('UPDATE content_creation SET version = ?, updated_at = ? WHERE content_id = ?',
                                 (new_version, now, content_id))
                    cursor.execute(''' INSERT INTO version_history (content_id, version_id, action, user_id, user_name, timestamp) VALUES (?, ?, 'create', ?, ?, ?) ''', (content_id, version_id, creator_id, kwargs.get('creator_name'), now))
                    conn.commit()
                    return {'success': True, 'version_id': version_id, 'version_number': new_version}
        except Exception as e:
            logger.error(f'创建版本失败: {e}')
            return {'success': False, 'error': str(e)}

    def rollback_version(self, content_id: str, target_version: int,
                         user_id: int, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT version_id, content_snapshot FROM content_version WHERE content_id = ? AND version_number = ?',
                                 (content_id, target_version))
                    target = cursor.fetchone()
                    if not target:
                        return {'success': False, 'error': '目标版本不存在'}
                    cursor.execute('SELECT version FROM content_creation WHERE content_id = ?', (content_id,))
                    current = cursor.fetchone()
                    if not current:
                        return {'success': False, 'error': '内容不存在'}
                    new_version = current[0] + 1
                    version_id = f"ver_{uuid.uuid4().hex[:12]}"
                    cursor.execute(''' INSERT INTO content_version ( version_id, content_id, version_number, version_status, content_snapshot, change_log, creator_id, creator_name, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (version_id, content_id, new_version, 'rolled_back',
                          target[1], f'回退到版本 {target_version}',
                          user_id, kwargs.get('user_name'), now))
                    cursor.execute('UPDATE content_creation SET version = ?, updated_at = ? WHERE content_id = ?',
                                 (new_version, now, content_id))
                    cursor.execute(''' INSERT INTO version_history (content_id, version_id, action, user_id, user_name, timestamp) VALUES (?, ?, 'rollback', ?, ?, ?) ''', (content_id, version_id, user_id, kwargs.get('user_name'), now))
                    conn.commit()
                    return {'success': True, 'version_id': version_id, 'rolled_back_to': target_version}
        except Exception as e:
            logger.error(f'回退版本失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_versions(self, content_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM content_version WHERE content_id = ? ORDER BY version_number DESC',
                (content_id,))
                versions = [dict(v) for v in cursor.fetchall()]
                return {'success': True, 'versions': versions}
        except Exception as e:
            logger.error(f'获取版本列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def restore_version(self, content_id: str, version_id: str,
                        user_id: int, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT version_number, content_snapshot FROM content_version WHERE version_id = ?',
                    (version_id,))
                    version = cursor.fetchone()
                    if not version:
                        return {'success': False, 'error': '版本不存在'}
                    cursor.execute('SELECT version FROM content_creation WHERE content_id = ?', (content_id,))
                    current = cursor.fetchone()
                    if not current:
                        return {'success': False, 'error': '内容不存在'}
                    new_version = current[0] + 1
                    new_version_id = f"ver_{uuid.uuid4().hex[:12]}"
                    cursor.execute(''' INSERT INTO content_version ( version_id, content_id, version_number, version_status, content_snapshot, change_log, creator_id, creator_name, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (new_version_id, content_id, new_version, 'official',
                          version[1], f'从版本 {version[0]} 恢复',
                          user_id, kwargs.get('user_name'), now))
                    cursor.execute('UPDATE content_creation SET version = ?, updated_at = ? WHERE content_id = ?',
                                 (new_version, now, content_id))
                    cursor.execute(''' INSERT INTO version_history (content_id, version_id, action, user_id, user_name, timestamp) VALUES (?, ?, 'restore', ?, ?, ?) ''', (content_id, new_version_id, user_id, kwargs.get('user_name'), now))
                    conn.commit()
                    return {'success': True, 'version_id': new_version_id}
        except Exception as e:
            logger.error(f'恢复版本失败: {e}')
            return {'success': False, 'error': str(e)}

    def delete_version(self, version_id: str, user_id: int, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT content_id, version_status FROM content_version WHERE version_id = ?',
                    (version_id,))
                    version = cursor.fetchone()
                    if not version:
                        return {'success': False, 'error': '版本不存在'}
                    if version[1] == 'official':
                        return {'success': False, 'error': '无法删除正式版本'}
                    cursor.execute('UPDATE content_version SET version_status = ? WHERE version_id = ?', ('deleted',
                    version_id))
                    cursor.execute(''' INSERT INTO version_history (content_id, version_id, action, user_id, user_name, timestamp) VALUES (?, ?, 'delete', ?, ?, ?) ''', (version[0], version_id, user_id, kwargs.get('user_name'), now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'删除版本失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 分类管理 ==========

    def create_category(self, category_type: str, category_name: str,
                        education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            category_id = f"cat_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO content_category ( category_id, category_type, category_name, parent_id, education_type, sort_order, is_active, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (category_id, category_type, category_name,
                          kwargs.get('parent_id'), education_type,
                          kwargs.get('sort_order', 0), 1, now, now))
                    conn.commit()
                    return {'success': True, 'category_id': category_id}
        except Exception as e:
            logger.error(f'创建分类失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_content_to_category(self, category_id: str, content_id: str,
                                user_id: int, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM content_category WHERE category_id = ?', (category_id,))
                    category = cursor.fetchone()
                    if not category:
                        return {'success': False, 'error': '分类不存在'}
                    cursor.execute('SELECT education_type FROM content_creation WHERE content_id = ?', (content_id,))
                    content = cursor.fetchone()
                    if not content:
                        return {'success': False, 'error': '内容不存在'}
                    if category[0] != content[0]:
                        return {'success': False, 'error': '教育类型不匹配'}
                    cursor.execute('INSERT OR IGNORE INTO category_items (category_id, content_id, added_by, added_at) VALUES (?, ?, ?, ?)',
                                 (category_id, content_id, user_id, now))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '内容已在该分类中'}
        except Exception as e:
            logger.error(f'添加内容到分类失败: {e}')
            return {'success': False, 'error': str(e)}

    def remove_content_from_category(self, category_id: str, content_id: str,
                                     user_id: int) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM category_items WHERE category_id = ? AND content_id = ?', (category_id,
                    content_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '内容不在该分类中'}
        except Exception as e:
            logger.error(f'从分类移除内容失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_categories(self, category_type: str = None,
                        education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM content_category WHERE is_active = 1'
                params = []
                if category_type:
                    query += ' AND category_type = ?'
                    params.append(category_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' ORDER BY sort_order, created_at DESC'
                cursor.execute(query, params)
                categories = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'categories': categories}
        except Exception as e:
            logger.error(f'获取分类列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 标签管理 ==========

    def create_tag(self, tag_name: str, tag_type: str, education_type: str,
                   **kwargs) -> Dict[str, Any]:
        try:
            tag_id = f"tag_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT tag_id FROM content_tags WHERE tag_name = ? AND tag_type = ?', (tag_name,
                    tag_type))
                    if cursor.fetchone():
                        return {'success': False, 'error': '标签已存在'}
                    cursor.execute(''' INSERT INTO content_tags ( tag_id, tag_name, tag_type, education_type, usage_count, is_active, created_at, updated_at ) VALUES (?, ?, ?, ?, 0, 1, ?, ?) ''', (tag_id, tag_name, tag_type, education_type, now, now))
                    conn.commit()
                    return {'success': True, 'tag_id': tag_id}
        except Exception as e:
            logger.error(f'创建标签失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_tag_to_content(self, tag_id: str, content_id: str, user_id: int,
                           **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type, usage_count FROM content_tags WHERE tag_id = ?', (tag_id,))
                    tag = cursor.fetchone()
                    if not tag:
                        return {'success': False, 'error': '标签不存在'}
                    cursor.execute('SELECT education_type FROM content_creation WHERE content_id = ?', (content_id,))
                    content = cursor.fetchone()
                    if not content:
                        return {'success': False, 'error': '内容不存在'}
                    if tag[0] != content[0]:
                        return {'success': False, 'error': '教育类型不匹配'}
                    cursor.execute('INSERT OR IGNORE INTO tag_items (tag_id, content_id, added_by, added_at) VALUES (?, ?, ?, ?)',
                                 (tag_id, content_id, user_id, now))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE content_tags SET usage_count = ?, updated_at = ? WHERE tag_id = ?',
                                     (tag[1] + 1, now, tag_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '内容已添加该标签'}
        except Exception as e:
            logger.error(f'添加标签到内容失败: {e}')
            return {'success': False, 'error': str(e)}

    def remove_tag_from_content(self, tag_id: str, content_id: str,
                                user_id: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM tag_items WHERE tag_id = ? AND content_id = ?', (tag_id, content_id))
                    if cursor.rowcount > 0:
                        cursor.execute('SELECT usage_count FROM content_tags WHERE tag_id = ?', (tag_id,))
                        usage = cursor.fetchone()
                        if usage and usage[0] > 0:
                            cursor.execute('UPDATE content_tags SET usage_count = ?, updated_at = ? WHERE tag_id = ?',
                                         (usage[0] - 1, now, tag_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '内容未添加该标签'}
        except Exception as e:
            logger.error(f'从内容移除标签失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_tags(self, tag_type: str = None, education_type: str = None,
                  page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM content_tags WHERE is_active = 1'
                params = []
                if tag_type:
                    query += ' AND tag_type = ?'
                    params.append(tag_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY usage_count DESC, tag_name ASC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                tags = [dict(t) for t in cursor.fetchall()]
                return {'success': True, 'tags': tags, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取标签列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 检索管理 ==========

    def search_content(self, keyword: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            search_id = f"sch_{uuid.uuid4().hex[:12]}"
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    query = 'SELECT * FROM content_creation WHERE (content_title LIKE ? OR content_id LIKE ?)'
                    params = [f'%{keyword}%', f'%{keyword}%']
                    if kwargs.get('education_type'):
                        query += ' AND education_type = ?'
                        params.append(kwargs['education_type'])
                    if kwargs.get('content_type'):
                        query += ' AND content_type = ?'
                        params.append(kwargs['content_type'])
                    if kwargs.get('status'):
                        query += ' AND status = ?'
                        params.append(kwargs['status'])
                    query += ' ORDER BY created_at DESC'
                    cursor.execute(query, params)
                    results = [dict(r) for r in cursor.fetchall()]
                    cursor.execute(''' INSERT INTO content_search (search_id, keyword, education_type, content_type, results_count, searched_at) VALUES (?, ?, ?, ?, ?, ?) ''', (search_id, keyword, kwargs.get('education_type'),
                          kwargs.get('content_type'), len(results), now))
                    for i, result in enumerate(results):
                        cursor.execute(''' INSERT INTO search_records (search_id, content_id, rank, score) VALUES (?, ?, ?, ?) ''', (search_id, result['content_id'], i + 1, 1.0 - i * 0.01))
                    conn.commit()
                    return {'success': True, 'results': results, 'total': len(results), 'search_id': search_id}
        except Exception as e:
            logger.error(f'搜索内容失败: {e}')
            return {'success': False, 'error': str(e)}

    def filter_content(self, **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM content_creation WHERE 1=1'
                params = []
                if kwargs.get('education_type'):
                    query += ' AND education_type = ?'
                    params.append(kwargs['education_type'])
                if kwargs.get('content_type'):
                    query += ' AND content_type = ?'
                    params.append(kwargs['content_type'])
                if kwargs.get('status'):
                    query += ' AND status = ?'
                    params.append(kwargs['status'])
                if kwargs.get('visibility'):
                    query += ' AND visibility = ?'
                    params.append(kwargs['visibility'])
                if kwargs.get('creator_id'):
                    query += ' AND creator_id = ?'
                    params.append(kwargs['creator_id'])
                sort_by = kwargs.get('sort_by', 'created_at')
                sort_order = kwargs.get('sort_order', 'DESC')
                query += f' ORDER BY {sort_by} {sort_order}'
                cursor.execute(query, params)
                results = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'results': results, 'total': len(results)}
        except Exception as e:
            logger.error(f'筛选内容失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_content_detail(self, content_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM content_creation WHERE content_id = ?', (content_id,))
                content = cursor.fetchone()
                if not content:
                    return {'success': False, 'error': '内容不存在'}
                cursor.execute('SELECT tag_id, tag_name FROM content_tags JOIN tag_items ON content_tags.tag_id = tag_items.tag_id WHERE tag_items.content_id = ?', (content_id,))
                tags = [dict(t) for t in cursor.fetchall()]
                cursor.execute('SELECT category_id, category_name, category_type FROM content_category JOIN category_items ON content_category.category_id = category_items.category_id WHERE category_items.content_id = ?', (content_id,))
                categories = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'content': dict(content), 'tags': tags, 'categories': categories}
        except Exception as e:
            logger.error(f'获取内容详情失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_content(self, page: int = 1, page_size: int = 20, **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM content_creation WHERE 1=1'
                params = []
                if kwargs.get('education_type'):
                    query += ' AND education_type = ?'
                    params.append(kwargs['education_type'])
                if kwargs.get('content_type'):
                    query += ' AND content_type = ?'
                    params.append(kwargs['content_type'])
                if kwargs.get('status'):
                    query += ' AND status = ?'
                    params.append(kwargs['status'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                contents = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'contents': contents, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取内容列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 推荐管理 ==========

    def generate_recommendation(self, user_id: int, method: str,
                                **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            rec_id = f"rec_{uuid.uuid4().hex[:12]}"
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    query = 'SELECT content_id, content_title FROM content_creation WHERE status = ?'
                    params = ['published']
                    if kwargs.get('education_type'):
                        query += ' AND education_type = ?'
                        params.append(kwargs['education_type'])
                    query += ' ORDER BY RANDOM() LIMIT 10'
                    cursor.execute(query, params)
                    contents = cursor.fetchall()
                    for i, content in enumerate(contents):
                        score = round(1.0 - i * 0.05, 2)
                        cursor.execute(''' INSERT INTO content_recommendation ( rec_id, user_id, method, content_id, score, displayed, clicked, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, 0, 0, ?, ?) ''', (rec_id, user_id, method, content[0], score, now, now))
                    conn.commit()
                    return {'success': True, 'rec_id': rec_id, 'recommended_count': len(contents)}
        except Exception as e:
            logger.error(f'生成推荐失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_recommendations(self, user_id: int, method: str = None,
                            limit: int = 10) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = ''' SELECT cr.*, cc.content_title, cc.content_type, cc.education_type FROM content_recommendation cr JOIN content_creation cc ON cr.content_id = cc.content_id WHERE cr.user_id = ? AND cr.displayed = 0 '''
                params = [user_id]
                if method:
                    query += ' AND cr.method = ?'
                    params.append(method)
                query += ' ORDER BY cr.score DESC LIMIT ?'
                params.append(limit)
                cursor.execute(query, params)
                recommendations = [dict(r) for r in cursor.fetchall()]
                cursor.execute('UPDATE content_recommendation SET displayed = 1 WHERE user_id = ? AND displayed = 0',
                (user_id,))
                conn.commit()
                return {'success': True, 'recommendations': recommendations}
        except Exception as e:
            logger.error(f'获取推荐失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_recommendation_click(self, rec_id: str, content_id: str,
                                    user_id: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE content_recommendation SET clicked = 1, updated_at = ? WHERE rec_id = ? AND content_id = ? AND user_id = ?',
                                 (now, rec_id, content_id, user_id))
                    if cursor.rowcount > 0:
                        cursor.execute(''' INSERT INTO recommendation_records (rec_id, action, user_id, timestamp, details) VALUES (?, 'click', ?, ?, ?) ''', (rec_id, user_id, now, json.dumps({'content_id': content_id})))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '推荐记录不存在'}
        except Exception as e:
            logger.error(f'记录推荐点击失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_recommendation_stats(self, user_id: int = None, method: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = 'SELECT method, COUNT(*) as total, SUM(clicked) as clicked FROM content_recommendation WHERE 1=1'
                params = []
                if user_id:
                    query += ' AND user_id = ?'
                    params.append(user_id)
                if method:
                    query += ' AND method = ?'
                    params.append(method)
                query += ' GROUP BY method'
                cursor.execute(query, params)
                stats = []
                for row in cursor.fetchall():
                    stats.append({
                        'method': row[0],
                        'method_name': RECOMMENDATION_METHODS.get(row[0], {}).get('name', row[0]),
                        'total': row[1],
                        'clicked': row[2] or 0,
                        'click_rate': round((row[2] or 0) / max(row[1], 1) * 100, 2)
                    })
                return {'success': True, 'stats': stats}
        except Exception as e:
            logger.error(f'获取推荐统计失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计管理 ==========

    def get_content_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                where_clause = 'WHERE education_type = ?' if education_type else 'WHERE 1=1'
                params = [education_type] if education_type else []
                cursor.execute(f'SELECT COUNT(*) FROM content_creation {where_clause}', params)
                total = cursor.fetchone()[0]
                cursor.execute(f'SELECT COUNT(*) FROM content_creation {where_clause} AND status = "published"', params)
                published = cursor.fetchone()[0]
                cursor.execute(f'SELECT COUNT(*) FROM content_creation {where_clause} AND status = "approved"', params)
                approved = cursor.fetchone()[0]
                cursor.execute(f'SELECT COUNT(*) FROM content_creation {where_clause} AND status = "submitted"', params)
                submitted = cursor.fetchone()[0]
                cursor.execute(f'SELECT COUNT(*) FROM content_creation {where_clause} AND status = "draft"', params)
                draft = cursor.fetchone()[0]
                cursor.execute(f'SELECT content_type, COUNT(*) as cnt FROM content_creation {where_clause} GROUP BY content_type', params)
                by_type = []
                for row in cursor.fetchall():
                    by_type.append({
                        'content_type': row[0],
                        'name': CONTENT_TYPES.get(row[0], {}).get('name', row[0]),
                        'count': row[1]
                    })
                cursor.execute(f'SELECT COUNT(DISTINCT creator_id) FROM content_creation {where_clause}', params)
                creators = cursor.fetchone()[0]
                cursor.execute(f'SELECT COUNT(*) FROM content_version', params)
                versions = cursor.fetchone()[0]
                return {
                    'success': True,
                    'statistics': {
                        'total': total,
                        'published': published,
                        'approved': approved,
                        'submitted': submitted,
                        'draft': draft,
                        'by_type': by_type,
                        'creators': creators,
                        'versions': versions
                    }
                }
        except Exception as e:
            logger.error(f'获取内容统计失败: {e}')
            return {'success': False, 'error': str(e)}