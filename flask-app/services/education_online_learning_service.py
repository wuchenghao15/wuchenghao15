#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育在线学习服务 (v15.30.0)
====================================
提供在线课程管理、学习平台管理、学习数据分析等综合学习服务。

核心能力：
1. 在线课程 - 课程管理、选课记录、学习进度、课程评价
2. 学习平台 - 平台管理、接入记录、平台统计、平台配置
3. 学习数据 - 数据采集、行为分析、效果评估、预测分析
4. 学习社区 - 讨论区、问答区、学习小组、知识分享、学习竞赛
5. 学习认证 - 证书管理、认证发放、证书查询、证书验证
6. 学习资源 - 资源管理、资源发布、资源共享、资源推荐
7. 学习支持 - 在线答疑、学习辅导、技术支持、就业指导
8. 学习评估 - 在线测验、作业评估、项目评估、综合评估
9. 统计分析 - 学习数据综合统计
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_online_learning_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationOnlineLearning')


# ========== 教育在线学习配置 ==========

COURSE_TYPES = {
    'mooc': {'name': 'MOOC', 'description': '大规模在线开放课程', 'suitable_for': ['adult', 'k12']},
    'spoc': {'name': 'SPOC', 'description': '小规模限制性在线课程', 'suitable_for': ['adult', 'k12']},
    'micro': {'name': '微课', 'description': '短时长微型课程', 'suitable_for': ['adult', 'k12']},
    'live': {'name': '直播课', 'description': '实时互动直播课程', 'suitable_for': ['adult', 'k12']},
    'recorded': {'name': '录播课', 'description': '录制回放课程', 'suitable_for': ['adult', 'k12']},
    'hybrid': {'name': '混合课程', 'description': '线上线下混合教学', 'suitable_for': ['adult', 'k12']},
    'flipped': {'name': '翻转课堂', 'description': '课前预习+课中研讨', 'suitable_for': ['k12']},
    'personalized': {'name': '个性化课程', 'description': '定制化学习路径', 'suitable_for': ['adult', 'k12']}
}

PLATFORM_TYPES = {
    'lms': {'name': 'LMS平台', 'description': '学习管理系统', 'features': ['课程管理', '学习跟踪', '成绩管理']},
    'online': {'name': '在线学习平台', 'description': '综合性在线学习平台', 'features': ['海量课程', '社交学习', '证书认证']},
    'learning': {'name': '学习管理系统', 'description': '企业/机构学习管理', 'features': ['员工培训', '能力评估', '进度监控']},
    'teaching': {'name': '教学平台', 'description': '面向教师的教学工具', 'features': ['备课工具', '教学互动', '作业批改']},
    'training': {'name': '培训平台', 'description': '职业技能培训平台', 'features': ['技能认证', '岗位培训', '企业内训']},
    'cloud': {'name': '教育云平台', 'description': '云端教育服务', 'features': ['资源共享', '协作学习', '数据分析']},
    'intelligent': {'name': '智能学习平台', 'description': 'AI驱动学习平台', 'features': ['个性化推荐', '智能辅导', '自适应学习']},
    'comprehensive': {'name': '综合教育平台', 'description': '全品类教育服务', 'features': ['K12教育', '职业教育', '素质教育']}
}

DATA_ANALYSIS = {
    'behavior': {'name': '学习行为分析', 'metrics': ['学习时长', '访问频率', '互动次数']},
    'effect': {'name': '学习效果分析', 'metrics': ['成绩变化', '知识掌握度', '能力提升']},
    'progress': {'name': '学习进度分析', 'metrics': ['课程完成率', '章节通过率', '学习速度']},
    'path': {'name': '学习路径分析', 'metrics': ['路径选择', '跳转模式', '学习顺序']},
    'pattern': {'name': '学习模式分析', 'metrics': ['学习时段', '学习节奏', '学习偏好']},
    'motivation': {'name': '学习动机分析', 'metrics': ['活跃度变化', '坚持度', '目标达成']},
    'difficulty': {'name': '学习困难分析', 'metrics': ['错题率', '停留时间', '求助频率']},
    'prediction': {'name': '学习预测分析', 'metrics': ['辍学风险', '成绩预测', '能力预测']}
}

COMMUNITY_FEATURES = {
    'discussion': {'name': '讨论区', 'description': '课程相关话题讨论', 'participant_limit': None},
    'qa': {'name': '问答区', 'description': '学习问题解答', 'expert_required': True},
    'group': {'name': '学习小组', 'description': '小组协作学习', 'participant_limit': 20},
    'partner': {'name': '学习伙伴', 'description': '一对一互助学习', 'participant_limit': 2},
    'sharing': {'name': '知识分享', 'description': '学习经验分享', 'participant_limit': None},
    'exchange': {'name': '经验交流', 'description': '学习心得交流', 'participant_limit': None},
    'competition': {'name': '学习竞赛', 'description': '技能比拼竞赛', 'participant_limit': 100},
    'mutual': {'name': '互助学习', 'description': '同学互助答疑', 'participant_limit': None}
}

CERTIFICATION_TYPES = {
    'course': {'name': '课程证书', 'description': '完成课程学习证明', 'validity': '永久', 'suitable_for': ['adult', 'k12']},
    'training': {'name': '培训证书', 'description': '完成培训项目证明', 'validity': '3年', 'suitable_for': ['adult']},
    'degree': {'name': '学历证书', 'description': '学历教育文凭', 'validity': '永久', 'suitable_for': ['adult']},
    'professional': {'name': '职业证书', 'description': '职业资格认证', 'validity': '5年', 'suitable_for': ['adult']},
    'qualification': {'name': '资格证书', 'description': '专业资格证明', 'validity': '3年', 'suitable_for': ['adult']},
    'skill': {'name': '技能证书', 'description': '特定技能认证', 'validity': '2年', 'suitable_for': ['adult', 'k12']},
    'ability': {'name': '能力证书', 'description': '综合能力评估证明', 'validity': '3年', 'suitable_for': ['adult', 'k12']},
    'achievement': {'name': '成果证书', 'description': '学习成果展示证明', 'validity': '永久', 'suitable_for': ['adult', 'k12']}
}

RESOURCE_TYPES = {
    'video': {'name': '视频资源', 'description': '教学视频内容', 'format': ['mp4', 'avi', 'mov', 'wmv']},
    'audio': {'name': '音频资源', 'description': '音频课程内容', 'format': ['mp3', 'wav', 'flac', 'aac']},
    'document': {'name': '文档资源', 'description': '教材讲义文档', 'format': ['pdf', 'doc', 'docx', 'ppt']},
    'interactive': {'name': '互动资源', 'description': '互动学习内容', 'format': ['html5', 'flash', 'scorm']},
    'simulation': {'name': '模拟资源', 'description': '仿真模拟训练', 'format': ['unity', 'unreal', 'webgl']},
    'practice': {'name': '实践资源', 'description': '实践操作内容', 'format': ['lab', 'exercise', 'project']},
    'case': {'name': '案例资源', 'description': '教学案例分析', 'format': ['pdf', 'video', 'doc']},
    'test': {'name': '测试资源', 'description': '测验考试题目', 'format': ['json', 'xml', 'quiz']}
}

SUPPORT_TYPES = {
    'qa': {'name': '在线答疑', 'description': '学习问题在线解答', 'response_time': '2小时'},
    'tutoring': {'name': '学习辅导', 'description': '一对一学习指导', 'response_time': '24小时'},
    'technical': {'name': '技术支持', 'description': '平台技术问题解决', 'response_time': '30分钟'},
    'psychological': {'name': '心理支持', 'description': '学习心理辅导', 'response_time': '48小时'},
    'employment': {'name': '就业支持', 'description': '职业规划与就业指导', 'response_time': '72小时'},
    'academic': {'name': '学术支持', 'description': '学术研究指导', 'response_time': '48小时'},
    'life': {'name': '生活支持', 'description': '生活相关问题帮助', 'response_time': '72小时'},
    'community': {'name': '社区支持', 'description': '学习社区管理与维护', 'response_time': '24小时'}
}

ASSESSMENT_METHODS = {
    'quiz': {'name': '在线测验', 'description': '选择题/判断题在线测试', 'duration': '30分钟', 'auto_grade': True},
    'assignment': {'name': '作业评估', 'description': '课后作业提交与批改', 'duration': '7天', 'auto_grade': False},
    'project': {'name': '项目评估', 'description': '综合项目实践评估', 'duration': '14天', 'auto_grade': False},
    'thesis': {'name': '论文评估', 'description': '学术论文撰写与答辩', 'duration': '30天', 'auto_grade': False},
    'practice': {'name': '实践评估', 'description': '实践操作能力评估', 'duration': '4小时', 'auto_grade': False},
    'comprehensive': {'name': '综合评估', 'description': '多维度综合评价', 'duration': '30天', 'auto_grade': False},
    'adaptive': {'name': '自适应评估', 'description': '根据能力动态调整', 'duration': '60分钟', 'auto_grade': True},
    'intelligent': {'name': '智能评估', 'description': 'AI驱动的智能评价', 'duration': '45分钟', 'auto_grade': True}
}


class EducationOnlineLearningService:
    """教育在线学习服务"""

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
                    CREATE TABLE IF NOT EXISTS online_courses (
                        course_id TEXT PRIMARY KEY,
                        course_name TEXT NOT NULL,
                        course_type TEXT NOT NULL,
                        education_type TEXT,
                        subject TEXT,
                        grade_level INTEGER,
                        teacher_id INTEGER,
                        teacher_name TEXT,
                        description TEXT,
                        duration INTEGER,
                        total_chapters INTEGER,
                        difficulty TEXT,
                        max_students INTEGER DEFAULT 1000,
                        enrolled_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS course_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        course_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        education_type TEXT,
                        enroll_date TEXT,
                        progress REAL DEFAULT 0,
                        completed_chapters INTEGER DEFAULT 0,
                        total_time REAL DEFAULT 0,
                        final_score REAL,
                        certificate_issued INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'learning',
                        UNIQUE(course_id, student_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_platform (
                        platform_id TEXT PRIMARY KEY,
                        platform_name TEXT NOT NULL,
                        platform_type TEXT NOT NULL,
                        education_type TEXT,
                        description TEXT,
                        url TEXT,
                        api_key TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS platform_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        platform_id TEXT NOT NULL,
                        user_id INTEGER,
                        user_name TEXT,
                        access_time TEXT,
                        duration REAL,
                        actions TEXT,
                        FOREIGN KEY(platform_id) REFERENCES learning_platform(platform_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_data (
                        data_id TEXT PRIMARY KEY,
                        analysis_type TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        education_type TEXT,
                        course_id TEXT,
                        metrics TEXT,
                        analysis_result TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS data_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        data_id TEXT NOT NULL,
                        record_type TEXT,
                        record_data TEXT,
                        timestamp TEXT,
                        FOREIGN KEY(data_id) REFERENCES learning_data(data_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_community (
                        community_id TEXT PRIMARY KEY,
                        community_type TEXT NOT NULL,
                        education_type TEXT,
                        name TEXT NOT NULL,
                        description TEXT,
                        course_id TEXT,
                        creator_id INTEGER,
                        creator_name TEXT,
                        member_count INTEGER DEFAULT 1,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS community_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        community_id TEXT NOT NULL,
                        user_id INTEGER,
                        user_name TEXT,
                        action_type TEXT,
                        content TEXT,
                        created_at TEXT,
                        FOREIGN KEY(community_id) REFERENCES learning_community(community_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_certification (
                        cert_id TEXT PRIMARY KEY,
                        cert_type TEXT NOT NULL,
                        education_type TEXT,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        course_id TEXT,
                        cert_no TEXT,
                        issue_date TEXT,
                        expiry_date TEXT,
                        status TEXT DEFAULT 'issued',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS certification_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cert_id TEXT NOT NULL,
                        record_type TEXT,
                        record_data TEXT,
                        created_at TEXT,
                        FOREIGN KEY(cert_id) REFERENCES learning_certification(cert_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_resources (
                        resource_id TEXT PRIMARY KEY,
                        resource_type TEXT NOT NULL,
                        education_type TEXT,
                        course_id TEXT,
                        title TEXT NOT NULL,
                        description TEXT,
                        file_url TEXT,
                        file_size INTEGER,
                        duration REAL,
                        uploader_id INTEGER,
                        uploader_name TEXT,
                        views INTEGER DEFAULT 0,
                        downloads INTEGER DEFAULT 0,
                        is_public INTEGER DEFAULT 1,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS resource_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        resource_id TEXT NOT NULL,
                        user_id INTEGER,
                        action_type TEXT,
                        timestamp TEXT,
                        FOREIGN KEY(resource_id) REFERENCES learning_resources(resource_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_support (
                        support_id TEXT PRIMARY KEY,
                        support_type TEXT NOT NULL,
                        education_type TEXT,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        course_id TEXT,
                        question TEXT,
                        answer TEXT,
                        status TEXT DEFAULT 'pending',
                        response_time TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS support_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        support_id TEXT NOT NULL,
                        action_type TEXT,
                        action_data TEXT,
                        created_at TEXT,
                        FOREIGN KEY(support_id) REFERENCES learning_support(support_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_assessment (
                        assessment_id TEXT PRIMARY KEY,
                        assessment_method TEXT NOT NULL,
                        education_type TEXT,
                        course_id TEXT,
                        title TEXT NOT NULL,
                        description TEXT,
                        duration INTEGER,
                        max_score REAL DEFAULT 100,
                        passing_score REAL DEFAULT 60,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS assessment_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        assessment_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        education_type TEXT,
                        score REAL,
                        status TEXT DEFAULT 'submitted',
                        submission_time TEXT,
                        feedback TEXT,
                        FOREIGN KEY(assessment_id) REFERENCES learning_assessment(assessment_id),
                        UNIQUE(assessment_id, student_id)
                    )
                ''')
                conn.commit()
                logger.info('教育在线学习服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 在线课程 ==========

    def create_course(self, course_name: str, course_type: str,
                       education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            course_id = f"crs_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = COURSE_TYPES.get(course_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO online_courses (
                            course_id, course_name, course_type, education_type,
                            subject, grade_level, teacher_id, teacher_name,
                            description, duration, total_chapters, difficulty,
                            max_students, enrolled_count, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'active', ?, ?)
                    ''', (course_id, course_name, course_type, education_type,
                          kwargs.get('subject'), kwargs.get('grade_level'),
                          kwargs.get('teacher_id'), kwargs.get('teacher_name'),
                          kwargs.get('description'), kwargs.get('duration'),
                          kwargs.get('total_chapters'), kwargs.get('difficulty'),
                          kwargs.get('max_students', 1000), now, now))
                    conn.commit()
                    logger.info(f'创建在线课程: {course_name} ({course_id})')
                    return {'success': True, 'course_id': course_id}
        except Exception as e:
            logger.error(f'创建在线课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_course(self, course_id: str, student_id: int,
                       student_name: str, education_type: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_students, enrolled_count, status, education_type FROM online_courses WHERE course_id = ?', (course_id,))
                    course = cursor.fetchone()
                    if not course:
                        return {'success': False, 'error': '课程不存在'}
                    if course[2] != 'active':
                        return {'success': False, 'error': '课程状态不允许选课'}
                    if course[0] and course[1] >= course[0]:
                        return {'success': False, 'error': '课程名额已满'}
                    if course[3] and course[3] != education_type:
                        return {'success': False, 'error': '课程类型与教育阶段不匹配'}
                    cursor.execute('INSERT OR IGNORE INTO course_records (course_id, student_id, student_name, education_type, enroll_date, status) VALUES (?, ?, ?, ?, ?, \'learning\')',
                                 (course_id, student_id, student_name, education_type, now[:10]))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE online_courses SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE course_id = ?', (now, course_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已选该课程'}
        except Exception as e:
            logger.error(f'选课失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_progress(self, course_id: str, student_id: int,
                         progress: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    status = 'completed' if progress >= 100 else 'learning'
                    cursor.execute('''
                        UPDATE course_records
                        SET progress = ?, completed_chapters = COALESCE(?, completed_chapters),
                            total_time = COALESCE(total_time + ?, total_time), status = ?
                        WHERE course_id = ? AND student_id = ?
                    ''', (progress, kwargs.get('completed_chapters'), kwargs.get('time_added', 0), status, course_id, student_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '选课记录不存在'}
        except Exception as e:
            logger.error(f'更新学习进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_course_score(self, course_id: str, student_id: int,
                             score: float) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE course_records SET final_score = ?, certificate_issued = 1, status = \'completed\' WHERE course_id = ? AND student_id = ?',
                                 (score, course_id, student_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'certificate_issued': True}
                    return {'success': False, 'error': '选课记录不存在'}
        except Exception as e:
            logger.error(f'记录课程成绩失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 学习平台 ==========

    def create_platform(self, platform_name: str, platform_type: str,
                         education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            platform_id = f"plt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = PLATFORM_TYPES.get(platform_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO learning_platform (
                            platform_id, platform_name, platform_type, education_type,
                            description, url, api_key, is_active,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                    ''', (platform_id, platform_name, platform_type, education_type,
                          kwargs.get('description', config.get('description', '')),
                          kwargs.get('url'), kwargs.get('api_key'), now, now))
                    conn.commit()
                    logger.info(f'创建学习平台: {platform_name} ({platform_id})')
                    return {'success': True, 'platform_id': platform_id}
        except Exception as e:
            logger.error(f'创建学习平台失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_platform_access(self, platform_id: str, user_id: int,
                                user_name: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT is_active FROM learning_platform WHERE platform_id = ?', (platform_id,))
                    platform = cursor.fetchone()
                    if not platform or platform[0] != 1:
                        return {'success': False, 'error': '平台未启用'}
                    cursor.execute('''
                        INSERT INTO platform_records (platform_id, user_id, user_name, access_time, duration, actions)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (platform_id, user_id, user_name, now, kwargs.get('duration', 0), kwargs.get('actions', '[]')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'记录平台访问失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_platform_stats(self, platform_id: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT COUNT(*) as total_access, SUM(duration) as total_duration
                    FROM platform_records WHERE platform_id = ?
                ''', (platform_id,))
                stats = cursor.fetchone()
                return {
                    'success': True,
                    'total_access': stats['total_access'],
                    'total_duration': stats['total_duration'] or 0
                }
        except Exception as e:
            logger.error(f'获取平台统计失败: {e}')
            return {'success': False, 'error': str(e)}

    def configure_platform(self, platform_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    updates = []
                    params = []
                    if 'url' in kwargs:
                        updates.append('url = ?')
                        params.append(kwargs['url'])
                    if 'api_key' in kwargs:
                        updates.append('api_key = ?')
                        params.append(kwargs['api_key'])
                    if 'is_active' in kwargs:
                        updates.append('is_active = ?')
                        params.append(1 if kwargs['is_active'] else 0)
                    if updates:
                        updates.append('updated_at = ?')
                        params.append(now)
                        params.append(platform_id)
                        cursor.execute(f'UPDATE learning_platform SET {", ".join(updates)} WHERE platform_id = ?', params)
                        conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'配置平台失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 学习数据 ==========

    def collect_learning_data(self, student_id: int, education_type: str,
                               analysis_type: str, **kwargs) -> Dict[str, Any]:
        try:
            data_id = f"dat_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = DATA_ANALYSIS.get(analysis_type, {})
            metrics = kwargs.get('metrics', {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO learning_data (
                            data_id, analysis_type, student_id, education_type,
                            course_id, metrics, analysis_result, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (data_id, analysis_type, student_id, education_type,
                          kwargs.get('course_id'), json.dumps(metrics), '', now))
                    conn.commit()
                    return {'success': True, 'data_id': data_id}
        except Exception as e:
            logger.error(f'采集学习数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def analyze_behavior(self, data_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT metrics, analysis_type FROM learning_data WHERE data_id = ?', (data_id,))
                    data = cursor.fetchone()
                    if not data:
                        return {'success': False, 'error': '数据不存在'}
                    metrics = json.loads(data[0]) if data[0] else {}
                    result = {}
                    if data[1] == 'behavior':
                        result = {'learning_hours': metrics.get('total_time', 0) / 3600,
                                  'access_frequency': metrics.get('access_count', 0),
                                  'interaction_level': 'high' if metrics.get('interactions', 0) > 100 else 'medium' if metrics.get('interactions', 0) > 50 else 'low'}
                    elif data[1] == 'effect':
                        result = {'score_improvement': metrics.get('score_change', 0),
                                  'knowledge_mastery': metrics.get('mastery_rate', 0),
                                  'skill_level': metrics.get('skill_level', 'beginner')}
                    elif data[1] == 'progress':
                        result = {'completion_rate': metrics.get('progress', 0),
                                  'chapter_pass_rate': metrics.get('chapter_pass', 0),
                                  'learning_speed': metrics.get('speed', 0)}
                    elif data[1] == 'prediction':
                        result = {'dropout_risk': 'low' if metrics.get('engagement', 0) > 80 else 'medium' if metrics.get('engagement', 0) > 50 else 'high',
                                  'expected_score': metrics.get('predicted_score', 0),
                                  'completion_probability': metrics.get('completion_prob', 0)}
                    cursor.execute('UPDATE learning_data SET analysis_result = ? WHERE data_id = ?', (json.dumps(result), data_id))
                    conn.commit()
                    return {'success': True, 'result': result}
        except Exception as e:
            logger.error(f'分析学习数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def evaluate_effect(self, student_id: int, course_id: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = '''
                    SELECT AVG(final_score) as avg_score, COUNT(*) as course_count,
                           SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_count
                    FROM course_records WHERE student_id = ?
                '''
                params = [student_id]
                if course_id:
                    query += ' AND course_id = ?'
                    params.append(course_id)
                cursor.execute(query, params)
                stats = cursor.fetchone()
                completion_rate = (stats['completed_count'] / stats['course_count'] * 100) if stats['course_count'] > 0 else 0
                return {
                    'success': True,
                    'average_score': stats['avg_score'] or 0,
                    'course_count': stats['course_count'],
                    'completed_count': stats['completed_count'],
                    'completion_rate': round(completion_rate, 1)
                }
        except Exception as e:
            logger.error(f'评估学习效果失败: {e}')
            return {'success': False, 'error': str(e)}

    def predict_learning(self, student_id: int, education_type: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT AVG(progress) as avg_progress, AVG(final_score) as avg_score,
                           COUNT(*) as total_courses
                    FROM course_records WHERE student_id = ? AND education_type = ?
                ''', (student_id, education_type))
                stats = cursor.fetchone()
                avg_progress = stats['avg_progress'] or 0
                avg_score = stats['avg_score'] or 0
                dropout_risk = 'low' if avg_progress > 70 else 'medium' if avg_progress > 40 else 'high'
                return {
                    'success': True,
                    'dropout_risk': dropout_risk,
                    'expected_completion_rate': min(100, avg_progress + 10),
                    'predicted_score': min(100, avg_score + 5),
                    'total_courses': stats['total_courses']
                }
        except Exception as e:
            logger.error(f'预测学习结果失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 学习社区 ==========

    def create_community(self, community_type: str, name: str,
                          education_type: str, creator_id: int,
                          creator_name: str, **kwargs) -> Dict[str, Any]:
        try:
            community_id = f"cmt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = COMMUNITY_FEATURES.get(community_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO learning_community (
                            community_id, community_type, education_type, name,
                            description, course_id, creator_id, creator_name,
                            member_count, is_active, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 1, ?, ?)
                    ''', (community_id, community_type, education_type, name,
                          kwargs.get('description', config.get('description', '')),
                          kwargs.get('course_id'), creator_id, creator_name, now, now))
                    conn.commit()
                    logger.info(f'创建学习社区: {name} ({community_id})')
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
                    cursor.execute('SELECT is_active, member_count, community_type FROM learning_community WHERE community_id = ?', (community_id,))
                    community = cursor.fetchone()
                    if not community or community[0] != 1:
                        return {'success': False, 'error': '社区未启用'}
                    config = COMMUNITY_FEATURES.get(community[2], {})
                    limit = config.get('participant_limit')
                    if limit and community[1] >= limit:
                        return {'success': False, 'error': '社区人数已满'}
                    cursor.execute('INSERT INTO community_records (community_id, user_id, user_name, action_type, content, created_at) VALUES (?, ?, ?, \'join\', \'\', ?)',
                                 (community_id, user_id, user_name, now))
                    cursor.execute('UPDATE learning_community SET member_count = member_count + 1, updated_at = ? WHERE community_id = ?', (now, community_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'加入社区失败: {e}')
            return {'success': False, 'error': str(e)}

    def post_discussion(self, community_id: str, user_id: int,
                         user_name: str, content: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT is_active FROM learning_community WHERE community_id = ?', (community_id,))
                    community = cursor.fetchone()
                    if not community or community[0] != 1:
                        return {'success': False, 'error': '社区未启用'}
                    cursor.execute('INSERT INTO community_records (community_id, user_id, user_name, action_type, content, created_at) VALUES (?, ?, ?, \'post\', ?, ?)',
                                 (community_id, user_id, user_name, content, now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'发布讨论失败: {e}')
            return {'success': False, 'error': str(e)}

    def ask_question(self, community_id: str, user_id: int,
                      user_name: str, question: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT is_active, community_type FROM learning_community WHERE community_id = ?', (community_id,))
                    community = cursor.fetchone()
                    if not community or community[0] != 1:
                        return {'success': False, 'error': '社区未启用'}
                    if community[1] != 'qa':
                        return {'success': False, 'error': '此社区不支持问答功能'}
                    cursor.execute('INSERT INTO community_records (community_id, user_id, user_name, action_type, content, created_at) VALUES (?, ?, ?, \'question\', ?, ?)',
                                 (community_id, user_id, user_name, question, now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'提问失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_community_stats(self, community_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM learning_community WHERE community_id = ?', (community_id,))
                community = cursor.fetchone()
                if not community:
                    return {'success': False, 'error': '社区不存在'}
                cursor.execute('SELECT COUNT(*) as post_count FROM community_records WHERE community_id = ? AND action_type = \'post\'', (community_id,))
                post_count = cursor.fetchone()['post_count']
                cursor.execute('SELECT COUNT(*) as question_count FROM community_records WHERE community_id = ? AND action_type = \'question\'', (community_id,))
                question_count = cursor.fetchone()['question_count']
                return {
                    'success': True,
                    'name': community['name'],
                    'type': community['community_type'],
                    'member_count': community['member_count'],
                    'post_count': post_count,
                    'question_count': question_count,
                    'is_active': bool(community['is_active'])
                }
        except Exception as e:
            logger.error(f'获取社区统计失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 学习认证 ==========

    def create_certification(self, cert_type: str, student_id: int,
                             student_name: str, education_type: str,
                             **kwargs) -> Dict[str, Any]:
        try:
            cert_id = f"crt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = CERTIFICATION_TYPES.get(cert_type, {})
            cert_no = f"CERT{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}"
            validity = config.get('validity', '永久')
            expiry_date = None
            if validity != '永久':
                years = int(validity.replace('年', ''))
                expiry_date = (datetime.now() + timedelta(days=years * 365)).isoformat()[:10]
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO learning_certification (
                            cert_id, cert_type, education_type, student_id,
                            student_name, course_id, cert_no, issue_date,
                            expiry_date, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'issued', ?)
                    ''', (cert_id, cert_type, education_type, student_id,
                          student_name, kwargs.get('course_id'), cert_no, now[:10],
                          expiry_date, now))
                    conn.commit()
                    logger.info(f'创建证书: {cert_type} ({cert_id})')
                    return {'success': True, 'cert_id': cert_id, 'cert_no': cert_no}
        except Exception as e:
            logger.error(f'创建证书失败: {e}')
            return {'success': False, 'error': str(e)}

    def issue_certificate(self, cert_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE learning_certification SET status = \'issued\', issue_date = ? WHERE cert_id = ? AND status = \'pending\'',
                                 (now[:10], cert_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '证书状态不允许发放'}
        except Exception as e:
            logger.error(f'发放证书失败: {e}')
            return {'success': False, 'error': str(e)}

    def query_certificate(self, cert_no: str = None, student_id: int = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM learning_certification WHERE 1=1'
                params = []
                if cert_no:
                    query += ' AND cert_no = ?'
                    params.append(cert_no)
                if student_id:
                    query += ' AND student_id = ?'
                    params.append(student_id)
                cursor.execute(query, params)
                certs = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'certificates': certs}
        except Exception as e:
            logger.error(f'查询证书失败: {e}')
            return {'success': False, 'error': str(e)}

    def verify_certificate(self, cert_no: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM learning_certification WHERE cert_no = ?', (cert_no,))
                cert = cursor.fetchone()
                if not cert:
                    return {'success': False, 'error': '证书不存在', 'valid': False}
                is_valid = cert['status'] == 'issued'
                if cert['expiry_date']:
                    is_valid = is_valid and cert['expiry_date'] > datetime.now().isoformat()[:10]
                return {
                    'success': True,
                    'valid': is_valid,
                    'cert_type': cert['cert_type'],
                    'student_name': cert['student_name'],
                    'issue_date': cert['issue_date'],
                    'expiry_date': cert['expiry_date']
                }
        except Exception as e:
            logger.error(f'验证证书失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 学习资源 ==========

    def upload_resource(self, resource_type: str, title: str,
                         education_type: str, uploader_id: int,
                         uploader_name: str, **kwargs) -> Dict[str, Any]:
        try:
            resource_id = f"res_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = RESOURCE_TYPES.get(resource_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO learning_resources (
                            resource_id, resource_type, education_type, course_id,
                            title, description, file_url, file_size,
                            duration, uploader_id, uploader_name,
                            views, downloads, is_public, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 1, 'active', ?, ?)
                    ''', (resource_id, resource_type, education_type,
                          kwargs.get('course_id'), title,
                          kwargs.get('description', config.get('description', '')),
                          kwargs.get('file_url'), kwargs.get('file_size'),
                          kwargs.get('duration'), uploader_id, uploader_name,
                          now, now))
                    conn.commit()
                    logger.info(f'上传资源: {title} ({resource_id})')
                    return {'success': True, 'resource_id': resource_id}
        except Exception as e:
            logger.error(f'上传资源失败: {e}')
            return {'success': False, 'error': str(e)}

    def share_resource(self, resource_id: str, is_public: bool) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE learning_resources SET is_public = ?, updated_at = ? WHERE resource_id = ?',
                                 (1 if is_public else 0, now, resource_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'is_public': is_public}
                    return {'success': False, 'error': '资源不存在'}
        except Exception as e:
            logger.error(f'分享资源失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_resource_access(self, resource_id: str, user_id: int,
                                action_type: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO resource_records (resource_id, user_id, action_type, timestamp) VALUES (?, ?, ?, ?)',
                                 (resource_id, user_id, action_type, now))
                    if action_type == 'view':
                        cursor.execute('UPDATE learning_resources SET views = views + 1 WHERE resource_id = ?', (resource_id,))
                    elif action_type == 'download':
                        cursor.execute('UPDATE learning_resources SET downloads = downloads + 1 WHERE resource_id = ?', (resource_id,))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'记录资源访问失败: {e}')
            return {'success': False, 'error': str(e)}

    def recommend_resources(self, student_id: int, education_type: str,
                             count: int = 5) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT r.* FROM learning_resources r
                    WHERE r.is_public = 1 AND r.status = 'active' AND r.education_type = ?
                    ORDER BY r.views DESC, r.downloads DESC
                    LIMIT ?
                ''', (education_type, count))
                resources = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'resources': resources}
        except Exception as e:
            logger.error(f'推荐资源失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 学习支持 ==========

    def create_support_ticket(self, support_type: str, student_id: int,
                               student_name: str, education_type: str,
                               question: str, **kwargs) -> Dict[str, Any]:
        try:
            support_id = f"sup_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = SUPPORT_TYPES.get(support_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO learning_support (
                            support_id, support_type, education_type, student_id,
                            student_name, course_id, question, answer,
                            status, response_time, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)
                    ''', (support_id, support_type, education_type, student_id,
                          student_name, kwargs.get('course_id'), question, '',
                          config.get('response_time', '24小时'), now, now))
                    conn.commit()
                    logger.info(f'创建支持工单: {support_type} ({support_id})')
                    return {'success': True, 'support_id': support_id}
        except Exception as e:
            logger.error(f'创建支持工单失败: {e}')
            return {'success': False, 'error': str(e)}

    def respond_to_ticket(self, support_id: str, answer: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE learning_support SET answer = ?, status = \'resolved\', response_time = ?, updated_at = ? WHERE support_id = ? AND status = \'pending\'',
                                 (answer, now[:19], now, support_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '工单状态不允许回复'}
        except Exception as e:
            logger.error(f'回复工单失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_support_status(self, support_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM learning_support WHERE support_id = ?', (support_id,))
                ticket = cursor.fetchone()
                if not ticket:
                    return {'success': False, 'error': '工单不存在'}
                return {
                    'success': True,
                    'support_type': ticket['support_type'],
                    'status': ticket['status'],
                    'question': ticket['question'],
                    'answer': ticket['answer'],
                    'response_time': ticket['response_time'],
                    'created_at': ticket['created_at']
                }
        except Exception as e:
            logger.error(f'获取工单状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_support_tickets(self, student_id: int = None,
                              status: str = None, page: int = 1,
                              page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM learning_support WHERE 1=1'
                params = []
                if student_id:
                    query += ' AND student_id = ?'
                    params.append(student_id)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                tickets = [dict(t) for t in cursor.fetchall()]
                return {'success': True, 'tickets': tickets, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取工单列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 学习评估 ==========

    def create_assessment(self, assessment_method: str, title: str,
                           education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            assessment_id = f"ast_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = ASSESSMENT_METHODS.get(assessment_method, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO learning_assessment (
                            assessment_id, assessment_method, education_type,
                            course_id, title, description, duration,
                            max_score, passing_score, is_active,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                    ''', (assessment_id, assessment_method, education_type,
                          kwargs.get('course_id'), title,
                          kwargs.get('description', config.get('description', '')),
                          kwargs.get('duration', config.get('duration', '30分钟')),
                          kwargs.get('max_score', 100),
                          kwargs.get('passing_score', 60), now, now))
                    conn.commit()
                    logger.info(f'创建评估: {title} ({assessment_id})')
                    return {'success': True, 'assessment_id': assessment_id}
        except Exception as e:
            logger.error(f'创建评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def submit_assessment(self, assessment_id: str, student_id: int,
                           student_name: str, education_type: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT is_active, auto_grade FROM learning_assessment WHERE assessment_id = ?', (assessment_id,))
                    assessment = cursor.fetchone()
                    if not assessment or assessment[0] != 1:
                        return {'success': False, 'error': '评估未启用'}
                    score = kwargs.get('score')
                    status = 'graded' if assessment[1] and score else 'submitted'
                    cursor.execute('INSERT OR REPLACE INTO assessment_records (assessment_id, student_id, student_name, education_type, score, status, submission_time) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                 (assessment_id, student_id, student_name, education_type, score, status, now))
                    conn.commit()
                    return {'success': True, 'status': status}
        except Exception as e:
            logger.error(f'提交评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def grade_assessment(self, assessment_id: str, student_id: int,
                          score: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT passing_score FROM learning_assessment WHERE assessment_id = ?', (assessment_id,))
                    assessment = cursor.fetchone()
                    if not assessment:
                        return {'success': False, 'error': '评估不存在'}
                    passed = score >= assessment[0]
                    cursor.execute('UPDATE assessment_records SET score = ?, status = \'graded\', feedback = ? WHERE assessment_id = ? AND student_id = ?',
                                 (score, kwargs.get('feedback'), assessment_id, student_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'passed': passed}
                    return {'success': False, 'error': '评估记录不存在'}
        except Exception as e:
            logger.error(f'评分失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_assessment_results(self, assessment_id: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT r.*, a.passing_score
                    FROM assessment_records r
                    JOIN learning_assessment a ON r.assessment_id = a.assessment_id
                    WHERE r.assessment_id = ?
                ''', (assessment_id,))
                results = []
                for row in cursor.fetchall():
                    result = dict(row)
                    result['passed'] = result['score'] >= result['passing_score'] if result['score'] else None
                    results.append(result)
                return {'success': True, 'results': results}
        except Exception as e:
            logger.error(f'获取评估结果失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 ==========

    def get_learning_statistics(self, education_type: str = None,
                                 **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query_parts = []
                params = []
                if education_type:
                    query_parts.append('education_type = ?')
                    params.append(education_type)
                where_clause = ' AND '.join(query_parts) if query_parts else '1=1'
                cursor.execute(f'''
                    SELECT COUNT(*) as total_courses FROM online_courses WHERE {where_clause}
                ''', params)
                total_courses = cursor.fetchone()['total_courses']
                cursor.execute(f'''
                    SELECT COUNT(*) as total_students FROM course_records WHERE {where_clause}
                ''', params)
                total_students = cursor.fetchone()['total_students']
                cursor.execute(f'''
                    SELECT AVG(progress) as avg_progress FROM course_records WHERE {where_clause}
                ''', params)
                avg_progress = cursor.fetchone()['avg_progress'] or 0
                cursor.execute(f'''
                    SELECT COUNT(*) as total_certificates FROM learning_certification WHERE {where_clause}
                ''', params)
                total_certificates = cursor.fetchone()['total_certificates']
                cursor.execute(f'''
                    SELECT COUNT(*) as total_resources FROM learning_resources WHERE {where_clause}
                ''', params)
                total_resources = cursor.fetchone()['total_resources']
                cursor.execute(f'''
                    SELECT COUNT(*) as total_communities FROM learning_community WHERE {where_clause}
                ''', params)
                total_communities = cursor.fetchone()['total_communities']
                cursor.execute(f'''
                    SELECT COUNT(*) as total_support_tickets FROM learning_support WHERE {where_clause}
                ''', params)
                total_support_tickets = cursor.fetchone()['total_support_tickets']
                cursor.execute(f'''
                    SELECT COUNT(*) as resolved_tickets FROM learning_support WHERE status = 'resolved' AND {where_clause}
                ''', params)
                resolved_tickets = cursor.fetchone()['resolved_tickets']
                return {
                    'success': True,
                    'total_courses': total_courses,
                    'total_students': total_students,
                    'average_progress': round(avg_progress, 1),
                    'total_certificates': total_certificates,
                    'total_resources': total_resources,
                    'total_communities': total_communities,
                    'total_support_tickets': total_support_tickets,
                    'resolved_tickets': resolved_tickets,
                    'support_resolution_rate': round(resolved_tickets / max(total_support_tickets, 1) * 100, 1),
                    'education_type': education_type or 'all'
                }
        except Exception as e:
            logger.error(f'获取学习统计失败: {e}')
            return {'success': False, 'error': str(e)}