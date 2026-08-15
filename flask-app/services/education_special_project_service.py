#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育特色项目服务 (v15.14.0)
====================================
提供特色课程、校本课程、项目学习、特色活动、特色基地、特色社团、特色竞赛、特色评估等综合管理服务。

核心能力：
1. 特色项目 - 项目管理、项目详情、项目状态、项目归档
2. 课程设计 - 校本课程、特色课程、项目课程、跨学科课程
3. 项目学习 - 学习小组、学习记录、成果提交、成果展示
4. 特色活动 - 活动组织、活动参与、活动评估、活动记录
5. 特色基地 - 基地管理、合作管理、资源共享、基地评估
6. 特色社团 - 社团管理、成员管理、活动记录、成果管理
7. 特色竞赛 - 竞赛管理、报名管理、成绩管理、奖项管理
8. 特色评估 - 评估体系、评估记录、评估报告、改进建议
9. 项目展示 - 展示管理、展示内容、展示统计
10. 推广管理 - 推广计划、推广执行、推广效果
11. 统计分析 - 综合统计、趋势分析、对比分析
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_special_project_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SpecialProject')


# ========== 特色项目配置 ==========

SPECIAL_PROJECT_TYPES = {
    'subject': {'name': '学科特色', 'description': '学科领域特色项目'},
    'art': {'name': '艺术特色', 'description': '艺术教育特色项目'},
    'sports': {'name': '体育特色', 'description': '体育教育特色项目'},
    'tech': {'name': '科技特色', 'description': '科技创新特色项目'},
    'humanities': {'name': '人文特色', 'description': '人文教育特色项目'},
    'international': {'name': '国际特色', 'description': '国际教育特色项目'},
    'practice': {'name': '实践特色', 'description': '实践教育特色项目'},
    'innovation': {'name': '创新特色', 'description': '创新教育特色项目'}
}

CURRICULUM_TYPES = {
    'school_based': {'name': '校本课程', 'duration': '学期', 'credits': 2},
    'special': {'name': '特色课程', 'duration': '学年', 'credits': 4},
    'project': {'name': '项目课程', 'duration': '项目周期', 'credits': 3},
    'comprehensive': {'name': '综合实践', 'duration': '学期', 'credits': 2},
    'inquiry': {'name': '探究学习', 'duration': '单元', 'credits': 1},
    'theme': {'name': '主题课程', 'duration': '学期', 'credits': 2},
    'interdisciplinary': {'name': '跨学科课程', 'duration': '学年', 'credits': 4},
    'elective': {'name': '选修课程', 'duration': '学期', 'credits': 1}
}

PROJECT_STAGES = {
    'planning': {'name': '策划', 'order': 1, 'duration_days': 30},
    'design': {'name': '设计', 'order': 2, 'duration_days': 20},
    'implementation': {'name': '实施', 'order': 3, 'duration_days': 90},
    'assessment': {'name': '评估', 'order': 4, 'duration_days': 15},
    'showcase': {'name': '展示', 'order': 5, 'duration_days': 10},
    'summary': {'name': '总结', 'order': 6, 'duration_days': 10},
    'promotion': {'name': '推广', 'order': 7, 'duration_days': 30},
    'iteration': {'name': '迭代', 'order': 8, 'duration_days': 30}
}

ACTIVITY_CATEGORIES = {
    'subject': {'name': '学科活动', 'requires_preparation': True},
    'art': {'name': '艺术活动', 'requires_preparation': True},
    'sports': {'name': '体育活动', 'requires_preparation': True},
    'tech': {'name': '科技活动', 'requires_preparation': True},
    'social': {'name': '社会实践', 'requires_preparation': True},
    'culture': {'name': '文化活动', 'requires_preparation': False},
    'international': {'name': '国际交流', 'requires_preparation': True},
    'volunteer': {'name': '志愿服务', 'requires_preparation': False}
}

BASE_TYPES = {
    'practice': {'name': '实践基地', 'capacity': 100},
    'innovation': {'name': '创新基地', 'capacity': 50},
    'research': {'name': '研学基地', 'capacity': 80},
    'labor': {'name': '劳动基地', 'capacity': 60},
    'culture': {'name': '文化基地', 'capacity': 120},
    'sports': {'name': '体育基地', 'capacity': 200},
    'tech': {'name': '科技基地', 'capacity': 50},
    'art': {'name': '艺术基地', 'capacity': 80}
}

COMPETITION_TYPES = {
    'subject': {'name': '学科竞赛', 'has_ranking': True},
    'tech': {'name': '科技创新', 'has_ranking': True},
    'art': {'name': '艺术比赛', 'has_ranking': False},
    'sports': {'name': '体育竞赛', 'has_ranking': True},
    'comprehensive': {'name': '综合实践', 'has_ranking': False},
    'maker': {'name': '创客大赛', 'has_ranking': True},
    'robot': {'name': '机器人竞赛', 'has_ranking': True},
    'coding': {'name': '编程竞赛', 'has_ranking': True}
}

ASSESSMENT_DIMENSIONS = {
    'specialization': {'name': '特色程度', 'weight': 0.15},
    'effectiveness': {'name': '教育效果', 'weight': 0.20},
    'student_development': {'name': '学生发展', 'weight': 0.20},
    'social_impact': {'name': '社会影响', 'weight': 0.10},
    'sustainability': {'name': '可持续性', 'weight': 0.10},
    'innovation': {'name': '创新度', 'weight': 0.15},
    'participation': {'name': '参与度', 'weight': 0.05},
    'satisfaction': {'name': '满意度', 'weight': 0.05}
}

SPECIALIZATION_LEVELS = {
    'school': {'name': '校级特色', 'threshold': 60},
    'city': {'name': '市级特色', 'threshold': 70},
    'province': {'name': '省级特色', 'threshold': 80},
    'national': {'name': '国家级特色', 'threshold': 90},
    'international': {'name': '国际特色', 'threshold': 95}
}


class EducationSpecialProjectService:
    """教育特色项目服务"""

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
                    CREATE TABLE IF NOT EXISTS special_projects (
                        project_id TEXT PRIMARY KEY,
                        project_name TEXT NOT NULL,
                        project_type TEXT,
                        education_type TEXT,
                        specialization_level TEXT,
                        status TEXT DEFAULT 'planning',
                        start_date TEXT,
                        end_date TEXT,
                        budget REAL DEFAULT 0,
                        funding_source TEXT,
                        leader_id INTEGER,
                        leader_name TEXT,
                        description TEXT,
                        objectives TEXT,
                        target_participants INTEGER DEFAULT 0,
                        actual_participants INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS project_details (
                        detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id TEXT NOT NULL,
                        stage TEXT,
                        stage_start_date TEXT,
                        stage_end_date TEXT,
                        responsible_person TEXT,
                        status TEXT DEFAULT 'pending',
                        progress REAL DEFAULT 0,
                        notes TEXT,
                        FOREIGN KEY (project_id) REFERENCES special_projects(project_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS curriculum_design (
                        curriculum_id TEXT PRIMARY KEY,
                        curriculum_name TEXT NOT NULL,
                        curriculum_type TEXT,
                        education_type TEXT,
                        project_id TEXT,
                        subject TEXT,
                        grade_level TEXT,
                        credits INTEGER DEFAULT 2,
                        duration TEXT,
                        objectives TEXT,
                        content TEXT,
                        teaching_methods TEXT,
                        assessment_methods TEXT,
                        materials TEXT,
                        teacher_id INTEGER,
                        teacher_name TEXT,
                        status TEXT DEFAULT 'draft',
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY (project_id) REFERENCES special_projects(project_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS project_learning (
                        learning_id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        curriculum_id TEXT,
                        education_type TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'in_progress',
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY (project_id) REFERENCES special_projects(project_id),
                        FOREIGN KEY (curriculum_id) REFERENCES curriculum_design(curriculum_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS learning_groups (
                        group_id TEXT PRIMARY KEY,
                        learning_id TEXT NOT NULL,
                        group_name TEXT,
                        member_count INTEGER DEFAULT 0,
                        leader_id INTEGER,
                        leader_name TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        FOREIGN KEY (learning_id) REFERENCES project_learning(learning_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS project_deliverables (
                        deliverable_id TEXT PRIMARY KEY,
                        learning_id TEXT NOT NULL,
                        group_id TEXT,
                        title TEXT,
                        description TEXT,
                        file_url TEXT,
                        status TEXT DEFAULT 'submitted',
                        score REAL,
                        feedback TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY (learning_id) REFERENCES project_learning(learning_id),
                        FOREIGN KEY (group_id) REFERENCES learning_groups(group_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS special_activities (
                        activity_id TEXT PRIMARY KEY,
                        activity_name TEXT NOT NULL,
                        category TEXT,
                        education_type TEXT,
                        project_id TEXT,
                        location TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        max_participants INTEGER DEFAULT 100,
                        registered_count INTEGER DEFAULT 0,
                        organizer TEXT,
                        description TEXT,
                        budget REAL DEFAULT 0,
                        status TEXT DEFAULT 'planned',
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY (project_id) REFERENCES special_projects(project_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS activity_participants (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        activity_id TEXT NOT NULL,
                        participant_id INTEGER,
                        participant_name TEXT,
                        participant_type TEXT DEFAULT 'student',
                        register_time TEXT,
                        attended INTEGER DEFAULT 0,
                        feedback TEXT,
                        FOREIGN KEY (activity_id) REFERENCES special_activities(activity_id),
                        UNIQUE(activity_id, participant_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS special_bases (
                        base_id TEXT PRIMARY KEY,
                        base_name TEXT NOT NULL,
                        base_type TEXT,
                        education_type TEXT,
                        location TEXT,
                        capacity INTEGER DEFAULT 100,
                        description TEXT,
                        facilities TEXT,
                        contact_person TEXT,
                        contact_phone TEXT,
                        cooperation_status TEXT DEFAULT 'pending',
                        established_date TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS base_cooperations (
                        cooperation_id TEXT PRIMARY KEY,
                        base_id TEXT NOT NULL,
                        project_id TEXT,
                        cooperation_type TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        FOREIGN KEY (base_id) REFERENCES special_bases(base_id),
                        FOREIGN KEY (project_id) REFERENCES special_projects(project_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS special_clubs (
                        club_id TEXT PRIMARY KEY,
                        club_name TEXT NOT NULL,
                        club_type TEXT,
                        education_type TEXT,
                        project_id TEXT,
                        description TEXT,
                        leader_id INTEGER,
                        leader_name TEXT,
                        advisor_id INTEGER,
                        advisor_name TEXT,
                        member_count INTEGER DEFAULT 0,
                        meeting_frequency TEXT DEFAULT 'weekly',
                        status TEXT DEFAULT 'active',
                        founded_date TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY (project_id) REFERENCES special_projects(project_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS club_achievements (
                        achievement_id TEXT PRIMARY KEY,
                        club_id TEXT NOT NULL,
                        title TEXT,
                        description TEXT,
                        date TEXT,
                        level TEXT,
                        evidence_url TEXT,
                        created_at TEXT,
                        FOREIGN KEY (club_id) REFERENCES special_clubs(club_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS special_competitions (
                        competition_id TEXT PRIMARY KEY,
                        competition_name TEXT NOT NULL,
                        competition_type TEXT,
                        education_type TEXT,
                        project_id TEXT,
                        organizer TEXT,
                        location TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        registration_deadline TEXT,
                        max_participants INTEGER DEFAULT 200,
                        registered_count INTEGER DEFAULT 0,
                        has_ranking INTEGER DEFAULT 1,
                        description TEXT,
                        status TEXT DEFAULT 'open',
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY (project_id) REFERENCES special_projects(project_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS competition_results (
                        result_id TEXT PRIMARY KEY,
                        competition_id TEXT NOT NULL,
                        participant_id INTEGER,
                        participant_name TEXT,
                        team_name TEXT,
                        category TEXT,
                        rank INTEGER,
                        score REAL,
                        award TEXT,
                        certificate_no TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT,
                        FOREIGN KEY (competition_id) REFERENCES special_competitions(competition_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS project_assessments (
                        assessment_id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        assessment_type TEXT,
                        education_type TEXT,
                        assessor_id INTEGER,
                        assessor_name TEXT,
                        assessment_date TEXT,
                        overall_score REAL,
                        specialization_level TEXT,
                        status TEXT DEFAULT 'in_progress',
                        created_at TEXT,
                        FOREIGN KEY (project_id) REFERENCES special_projects(project_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS assessment_records (
                        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        assessment_id TEXT NOT NULL,
                        dimension TEXT,
                        score REAL,
                        weight REAL,
                        comment TEXT,
                        FOREIGN KEY (assessment_id) REFERENCES project_assessments(assessment_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS project_showcases (
                        showcase_id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        showcase_name TEXT,
                        education_type TEXT,
                        location TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        description TEXT,
                        visitor_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'planned',
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY (project_id) REFERENCES special_projects(project_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS showcase_items (
                        item_id TEXT PRIMARY KEY,
                        showcase_id TEXT NOT NULL,
                        item_type TEXT,
                        title TEXT,
                        description TEXT,
                        media_url TEXT,
                        order_num INTEGER DEFAULT 0,
                        FOREIGN KEY (showcase_id) REFERENCES project_showcases(showcase_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS promotion_records (
                        promotion_id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        channel TEXT,
                        content TEXT,
                        target_audience TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        reach_count INTEGER DEFAULT 0,
                        engagement_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        FOREIGN KEY (project_id) REFERENCES special_projects(project_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS project_archives (
                        archive_id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        archive_name TEXT,
                        archive_type TEXT,
                        file_url TEXT,
                        description TEXT,
                        archived_at TEXT,
                        FOREIGN KEY (project_id) REFERENCES special_projects(project_id)
                    )
                ''')
                conn.commit()
                logger.info('教育特色项目服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 特色项目 ==========

    def create_special_project(self, project_name: str, project_type: str,
                               education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            project_id = f"sp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = SPECIAL_PROJECT_TYPES.get(project_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO special_projects (
                            project_id, project_name, project_type, education_type,
                            specialization_level, status, start_date, end_date,
                            budget, funding_source, leader_id, leader_name,
                            description, objectives, target_participants,
                            actual_participants, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, NULL, 'planning', ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                    ''', (project_id, project_name, project_type, education_type,
                          kwargs.get('start_date', now[:10]), kwargs.get('end_date'),
                          kwargs.get('budget', 0), kwargs.get('funding_source'),
                          kwargs.get('leader_id'), kwargs.get('leader_name'),
                          kwargs.get('description'), kwargs.get('objectives'),
                          kwargs.get('target_participants', 0), now, now))
                    for stage_key, stage_config in PROJECT_STAGES.items():
                        cursor.execute('''
                            INSERT INTO project_details (project_id, stage, stage_start_date, stage_end_date, status)
                            VALUES (?, ?, NULL, NULL, 'pending')
                        ''', (project_id, stage_key))
                    conn.commit()
                    logger.info(f'创建特色项目: {project_name} ({project_id})')
                    return {'success': True, 'project_id': project_id}
        except Exception as e:
            logger.error(f'创建特色项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_project_stage(self, project_id: str, stage: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            if stage not in PROJECT_STAGES:
                return {'success': False, 'error': '无效的项目阶段'}
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE project_details SET stage_start_date = ?, stage_end_date = ?,
                            responsible_person = ?, status = ?, progress = ?, notes = ?
                        WHERE project_id = ? AND stage = ?
                    ''', (kwargs.get('stage_start_date'), kwargs.get('stage_end_date'),
                          kwargs.get('responsible_person'), kwargs.get('status', 'in_progress'),
                          kwargs.get('progress', 0), kwargs.get('notes'), project_id, stage))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE special_projects SET status = ?, updated_at = ? WHERE project_id = ?',
                                     (stage, now, project_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '项目阶段记录不存在'}
        except Exception as e:
            logger.error(f'更新项目阶段失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_project_details(self, project_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM special_projects WHERE project_id = ?', (project_id,))
                project = cursor.fetchone()
                if not project:
                    return {'success': False, 'error': '项目不存在'}
                cursor.execute('SELECT * FROM project_details WHERE project_id = ? ORDER BY stage', (project_id,))
                stages = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'project': dict(project), 'stages': stages}
        except Exception as e:
            logger.error(f'获取项目详情失败: {e}')
            return {'success': False, 'error': str(e)}

    def archive_project(self, project_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            archive_id = f"arc_{uuid.uuid4().hex[:12]}"
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT project_name FROM special_projects WHERE project_id = ?', (project_id,))
                    project = cursor.fetchone()
                    if not project:
                        return {'success': False, 'error': '项目不存在'}
                    cursor.execute('UPDATE special_projects SET status = ? WHERE project_id = ?',
                                 ('archived', project_id))
                    cursor.execute('''
                        INSERT INTO project_archives (archive_id, project_id, archive_name, archive_type, description, archived_at)
                        VALUES (?, ?, ?, 'project', ?, ?)
                    ''', (archive_id, project_id, project[0], kwargs.get('description', '项目归档'), now))
                    conn.commit()
                    return {'success': True, 'archive_id': archive_id}
        except Exception as e:
            logger.error(f'归档项目失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 课程设计 ==========

    def create_curriculum(self, curriculum_name: str, curriculum_type: str,
                          education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            curriculum_id = f"cur_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = CURRICULUM_TYPES.get(curriculum_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO curriculum_design (
                            curriculum_id, curriculum_name, curriculum_type,
                            education_type, project_id, subject, grade_level,
                            credits, duration, objectives, content,
                            teaching_methods, assessment_methods, materials,
                            teacher_id, teacher_name, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?)
                    ''', (curriculum_id, curriculum_name, curriculum_type, education_type,
                          kwargs.get('project_id'), kwargs.get('subject'),
                          kwargs.get('grade_level'), kwargs.get('credits', config.get('credits', 2)),
                          kwargs.get('duration', config.get('duration', '学期')),
                          kwargs.get('objectives'), kwargs.get('content'),
                          kwargs.get('teaching_methods'), kwargs.get('assessment_methods'),
                          kwargs.get('materials'), kwargs.get('teacher_id'),
                          kwargs.get('teacher_name'), now, now))
                    conn.commit()
                    logger.info(f'创建课程设计: {curriculum_name} ({curriculum_id})')
                    return {'success': True, 'curriculum_id': curriculum_id}
        except Exception as e:
            logger.error(f'创建课程设计失败: {e}')
            return {'success': False, 'error': str(e)}

    def publish_curriculum(self, curriculum_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE curriculum_design SET status = ?, updated_at = ? WHERE curriculum_id = ? AND status = ?',
                                 ('published', now, curriculum_id, 'draft'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '课程状态不允许发布'}
        except Exception as e:
            logger.error(f'发布课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_curriculum(self, education_type: str = None, curriculum_type: str = None,
                        status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM curriculum_design WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if curriculum_type:
                    query += ' AND curriculum_type = ?'
                    params.append(curriculum_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                curricula = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'curricula': curricula, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取课程列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_curriculum(self, curriculum_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    fields = []
                    values = []
                    for key in ['curriculum_name', 'curriculum_type', 'subject', 'grade_level',
                                'credits', 'duration', 'objectives', 'content', 'teaching_methods',
                                'assessment_methods', 'materials', 'teacher_id', 'teacher_name']:
                        if key in kwargs:
                            fields.append(f"{key} = ?")
                            values.append(kwargs[key])
                    if not fields:
                        return {'success': False, 'error': '没有需要更新的字段'}
                    fields.append("updated_at = ?")
                    values.append(now)
                    values.append(curriculum_id)
                    cursor.execute(f'UPDATE curriculum_design SET {", ".join(fields)} WHERE curriculum_id = ?', values)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '课程不存在'}
        except Exception as e:
            logger.error(f'更新课程失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 项目学习 ==========

    def create_project_learning(self, project_id: str, education_type: str,
                                **kwargs) -> Dict[str, Any]:
        try:
            learning_id = f"pln_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO project_learning (
                            learning_id, project_id, curriculum_id, education_type,
                            start_date, end_date, description, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'in_progress', ?, ?)
                    ''', (learning_id, project_id, kwargs.get('curriculum_id'), education_type,
                          kwargs.get('start_date', now[:10]), kwargs.get('end_date'),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建项目学习: {project_id} ({learning_id})')
                    return {'success': True, 'learning_id': learning_id}
        except Exception as e:
            logger.error(f'创建项目学习失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_learning_group(self, learning_id: str, group_name: str,
                              **kwargs) -> Dict[str, Any]:
        try:
            group_id = f"grp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO learning_groups (
                            group_id, learning_id, group_name, member_count,
                            leader_id, leader_name, status, created_at
                        ) VALUES (?, ?, ?, 0, ?, ?, 'active', ?)
                    ''', (group_id, learning_id, group_name, kwargs.get('leader_id'),
                          kwargs.get('leader_name'), now))
                    conn.commit()
                    return {'success': True, 'group_id': group_id}
        except Exception as e:
            logger.error(f'创建学习小组失败: {e}')
            return {'success': False, 'error': str(e)}

    def submit_deliverable(self, learning_id: str, group_id: str, title: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            deliverable_id = f"dlv_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO project_deliverables (
                            deliverable_id, learning_id, group_id, title,
                            description, file_url, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'submitted', ?, ?)
                    ''', (deliverable_id, learning_id, group_id, title,
                          kwargs.get('description'), kwargs.get('file_url'), now, now))
                    conn.commit()
                    return {'success': True, 'deliverable_id': deliverable_id}
        except Exception as e:
            logger.error(f'提交成果失败: {e}')
            return {'success': False, 'error': str(e)}

    def evaluate_deliverable(self, deliverable_id: str, score: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE project_deliverables SET score = ?, feedback = ?, status = ?, updated_at = ? WHERE deliverable_id = ?',
                                 (score, kwargs.get('feedback'), 'evaluated', now, deliverable_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '成果不存在'}
        except Exception as e:
            logger.error(f'评估成果失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 特色活动 ==========

    def create_special_activity(self, activity_name: str, category: str,
                                education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            activity_id = f"act_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = ACTIVITY_CATEGORIES.get(category, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO special_activities (
                            activity_id, activity_name, category, education_type,
                            project_id, location, start_date, end_date,
                            max_participants, registered_count, organizer,
                            description, budget, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, 'planned', ?, ?)
                    ''', (activity_id, activity_name, category, education_type,
                          kwargs.get('project_id'), kwargs.get('location'),
                          kwargs.get('start_date', now[:10]), kwargs.get('end_date'),
                          kwargs.get('max_participants', 100), kwargs.get('organizer'),
                          kwargs.get('description'), kwargs.get('budget', 0), now, now))
                    conn.commit()
                    logger.info(f'创建特色活动: {activity_name} ({activity_id})')
                    return {'success': True, 'activity_id': activity_id}
        except Exception as e:
            logger.error(f'创建特色活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_activity(self, activity_id: str, participant_id: int,
                          participant_name: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, registered_count, status FROM special_activities WHERE activity_id = ?', (activity_id,))
                    activity = cursor.fetchone()
                    if not activity:
                        return {'success': False, 'error': '活动不存在'}
                    if activity[2] != 'planned':
                        return {'success': False, 'error': '活动状态不允许报名'}
                    if activity[0] and activity[1] >= activity[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('''
                        INSERT OR IGNORE INTO activity_participants (activity_id, participant_id, participant_name, participant_type, register_time)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (activity_id, participant_id, participant_name,
                          kwargs.get('participant_type', 'student'), now))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE special_activities SET registered_count = registered_count + 1, updated_at = ? WHERE activity_id = ?', (now, activity_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已报名该活动'}
        except Exception as e:
            logger.error(f'活动报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_activity_attendance(self, activity_id: str, participant_id: int,
                                   attended: bool = True) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE activity_participants SET attended = ? WHERE activity_id = ? AND participant_id = ?',
                                 (1 if attended else 0, activity_id, participant_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '报名记录不存在'}
        except Exception as e:
            logger.error(f'记录活动出席失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_activity(self, activity_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE special_activities SET status = ?, updated_at = ? WHERE activity_id = ?',
                                 ('completed', now, activity_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '活动不存在'}
        except Exception as e:
            logger.error(f'完成活动失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 特色基地 ==========

    def create_special_base(self, base_name: str, base_type: str,
                            education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            base_id = f"bs_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = BASE_TYPES.get(base_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO special_bases (
                            base_id, base_name, base_type, education_type,
                            location, capacity, description, facilities,
                            contact_person, contact_phone, cooperation_status,
                            established_date, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, 'active', ?, ?)
                    ''', (base_id, base_name, base_type, education_type,
                          kwargs.get('location'), kwargs.get('capacity', config.get('capacity', 100)),
                          kwargs.get('description'), kwargs.get('facilities'),
                          kwargs.get('contact_person'), kwargs.get('contact_phone'),
                          kwargs.get('established_date', now[:10]), now, now))
                    conn.commit()
                    logger.info(f'创建特色基地: {base_name} ({base_id})')
                    return {'success': True, 'base_id': base_id}
        except Exception as e:
            logger.error(f'创建特色基地失败: {e}')
            return {'success': False, 'error': str(e)}

    def establish_cooperation(self, base_id: str, project_id: str,
                              cooperation_type: str, **kwargs) -> Dict[str, Any]:
        try:
            cooperation_id = f"coop_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO base_cooperations (
                            cooperation_id, base_id, project_id, cooperation_type,
                            start_date, end_date, description, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?)
                    ''', (cooperation_id, base_id, project_id, cooperation_type,
                          kwargs.get('start_date', now[:10]), kwargs.get('end_date'),
                          kwargs.get('description'), now))
                    cursor.execute('UPDATE special_bases SET cooperation_status = ? WHERE base_id = ?',
                                 ('cooperating', base_id))
                    conn.commit()
                    return {'success': True, 'cooperation_id': cooperation_id}
        except Exception as e:
            logger.error(f'建立合作关系失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_base_status(self, base_id: str, status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE special_bases SET status = ?, updated_at = ? WHERE base_id = ?',
                                 (status, now, base_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '基地不存在'}
        except Exception as e:
            logger.error(f'更新基地状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_bases(self, education_type: str = None, base_type: str = None,
                   status: str = 'active', page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM special_bases WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if base_type:
                    query += ' AND base_type = ?'
                    params.append(base_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                bases = [dict(b) for b in cursor.fetchall()]
                return {'success': True, 'bases': bases, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取基地列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 特色社团 ==========

    def create_special_club(self, club_name: str, club_type: str,
                            education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            club_id = f"clb_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO special_clubs (
                            club_id, club_name, club_type, education_type,
                            project_id, description, leader_id, leader_name,
                            advisor_id, advisor_name, member_count,
                            meeting_frequency, status, founded_date,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 'active', ?, ?, ?)
                    ''', (club_id, club_name, club_type, education_type,
                          kwargs.get('project_id'), kwargs.get('description'),
                          kwargs.get('leader_id'), kwargs.get('leader_name'),
                          kwargs.get('advisor_id'), kwargs.get('advisor_name'),
                          kwargs.get('meeting_frequency', 'weekly'),
                          kwargs.get('founded_date', now[:10]), now, now))
                    conn.commit()
                    logger.info(f'创建特色社团: {club_name} ({club_id})')
                    return {'success': True, 'club_id': club_id}
        except Exception as e:
            logger.error(f'创建特色社团失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_club_member(self, club_id: str, student_id: int,
                        student_name: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT OR IGNORE INTO club_members (club_id, student_id, student_name, role, joined_at) VALUES (?, ?, ?, ?, ?)',
                                 (club_id, student_id, student_name, kwargs.get('role', 'member'), now))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE special_clubs SET member_count = member_count + 1, updated_at = ? WHERE club_id = ?', (now, club_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已加入该社团'}
        except Exception as e:
            logger.error(f'添加社团成员失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_club_achievement(self, club_id: str, title: str, **kwargs) -> Dict[str, Any]:
        try:
            achievement_id = f"ach_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO club_achievements (
                            achievement_id, club_id, title, description,
                            date, level, evidence_url, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (achievement_id, club_id, title, kwargs.get('description'),
                          kwargs.get('date', now[:10]), kwargs.get('level', 'school'),
                          kwargs.get('evidence_url'), now))
                    conn.commit()
                    return {'success': True, 'achievement_id': achievement_id}
        except Exception as e:
            logger.error(f'记录社团成果失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_clubs(self, education_type: str = None, club_type: str = None,
                   status: str = 'active', page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM special_clubs WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if club_type:
                    query += ' AND club_type = ?'
                    params.append(club_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                clubs = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'clubs': clubs, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取社团列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 特色竞赛 ==========

    def create_competition(self, competition_name: str, competition_type: str,
                           education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            competition_id = f"cmp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = COMPETITION_TYPES.get(competition_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO special_competitions (
                            competition_id, competition_name, competition_type,
                            education_type, project_id, organizer, location,
                            start_date, end_date, registration_deadline,
                            max_participants, registered_count, has_ranking,
                            description, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, 'open', ?, ?)
                    ''', (competition_id, competition_name, competition_type, education_type,
                          kwargs.get('project_id'), kwargs.get('organizer'),
                          kwargs.get('location'), kwargs.get('start_date'),
                          kwargs.get('end_date'), kwargs.get('registration_deadline'),
                          kwargs.get('max_participants', 200), 1 if config.get('has_ranking') else 0,
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建特色竞赛: {competition_name} ({competition_id})')
                    return {'success': True, 'competition_id': competition_id}
        except Exception as e:
            logger.error(f'创建特色竞赛失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_competition(self, competition_id: str, participant_id: int,
                             participant_name: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, registered_count, status, registration_deadline FROM special_competitions WHERE competition_id = ?', (competition_id,))
                    competition = cursor.fetchone()
                    if not competition:
                        return {'success': False, 'error': '竞赛不存在'}
                    if competition[2] != 'open':
                        return {'success': False, 'error': '竞赛报名已关闭'}
                    if competition[0] and competition[1] >= competition[0]:
                        return {'success': False, 'error': '名额已满'}
                    if competition[3] and now[:10] > competition[3]:
                        return {'success': False, 'error': '报名已截止'}
                    cursor.execute('SELECT result_id FROM competition_results WHERE competition_id = ? AND participant_id = ?', (competition_id, participant_id))
                    if cursor.fetchone():
                        return {'success': False, 'error': '已报名该竞赛'}
                    result_id = f"crs_{uuid.uuid4().hex[:12]}"
                    cursor.execute('''
                        INSERT INTO competition_results (result_id, competition_id, participant_id, participant_name, team_name, category, status)
                        VALUES (?, ?, ?, ?, ?, ?, 'pending')
                    ''', (result_id, competition_id, participant_id, participant_name,
                          kwargs.get('team_name'), kwargs.get('category')))
                    cursor.execute('UPDATE special_competitions SET registered_count = registered_count + 1, updated_at = ? WHERE competition_id = ?', (now, competition_id))
                    conn.commit()
                    return {'success': True, 'result_id': result_id}
        except Exception as e:
            logger.error(f'竞赛报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_competition_result(self, result_id: str, score: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            certificate_no = f"CC{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}" if kwargs.get('award') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE competition_results SET score = ?, rank = ?, award = ?, certificate_no = ?, status = ? WHERE result_id = ?
                    ''', (score, kwargs.get('rank'), kwargs.get('award'), certificate_no, 'completed', result_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'certificate_no': certificate_no}
                    return {'success': False, 'error': '竞赛结果记录不存在'}
        except Exception as e:
            logger.error(f'记录竞赛结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def close_competition(self, competition_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE special_competitions SET status = ?, updated_at = ? WHERE competition_id = ?',
                                 ('closed', now, competition_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '竞赛不存在'}
        except Exception as e:
            logger.error(f'关闭竞赛失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_competition_ranking(self, competition_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT has_ranking FROM special_competitions WHERE competition_id = ?', (competition_id,))
                competition = cursor.fetchone()
                if not competition:
                    return {'success': False, 'error': '竞赛不存在'}
                if not competition[0]:
                    return {'success': False, 'error': '该竞赛不设排名'}
                cursor.execute('''
                    SELECT participant_name, team_name, score, rank, award
                    FROM competition_results
                    WHERE competition_id = ? AND status = 'completed'
                    ORDER BY score DESC
                ''', (competition_id,))
                rankings = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'rankings': rankings}
        except Exception as e:
            logger.error(f'获取竞赛排名失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 特色评估 ==========

    def create_assessment(self, project_id: str, assessment_type: str,
                          education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            assessment_id = f"asm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO project_assessments (
                            assessment_id, project_id, assessment_type,
                            education_type, assessor_id, assessor_name,
                            assessment_date, overall_score, specialization_level,
                            status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, 'in_progress', ?)
                    ''', (assessment_id, project_id, assessment_type, education_type,
                          kwargs.get('assessor_id'), kwargs.get('assessor_name'),
                          kwargs.get('assessment_date', now[:10]), now))
                    for dim_key, dim_config in ASSESSMENT_DIMENSIONS.items():
                        cursor.execute('''
                            INSERT INTO assessment_records (assessment_id, dimension, score, weight)
                            VALUES (?, ?, NULL, ?)
                        ''', (assessment_id, dim_key, dim_config.get('weight', 0)))
                    conn.commit()
                    return {'success': True, 'assessment_id': assessment_id}
        except Exception as e:
            logger.error(f'创建评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_assessment_score(self, assessment_id: str, dimension: str,
                                score: float, **kwargs) -> Dict[str, Any]:
        try:
            if dimension not in ASSESSMENT_DIMENSIONS:
                return {'success': False, 'error': '无效的评估维度'}
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE assessment_records SET score = ?, comment = ? WHERE assessment_id = ? AND dimension = ?',
                                 (score, kwargs.get('comment'), assessment_id, dimension))
                    if cursor.rowcount > 0:
                        cursor.execute('SELECT SUM(score * weight) as total FROM assessment_records WHERE assessment_id = ? AND score IS NOT NULL', (assessment_id,))
                        total = cursor.fetchone()[0]
                        if total:
                            overall_score = round(total / sum(d.get('weight', 0) for d in ASSESSMENT_DIMENSIONS.values()), 2)
                            level = 'school'
                            for lvl_key, lvl_config in SPECIALIZATION_LEVELS.items():
                                if overall_score >= lvl_config.get('threshold', 0):
                                    level = lvl_key
                            cursor.execute('UPDATE project_assessments SET overall_score = ?, specialization_level = ? WHERE assessment_id = ?',
                                         (overall_score, level, assessment_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '评估维度记录不存在'}
        except Exception as e:
            logger.error(f'记录评估分数失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_assessment(self, assessment_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT overall_score, project_id FROM project_assessments WHERE assessment_id = ?', (assessment_id,))
                    assessment = cursor.fetchone()
                    if not assessment:
                        return {'success': False, 'error': '评估不存在'}
                    cursor.execute('UPDATE project_assessments SET status = ? WHERE assessment_id = ?',
                                 ('completed', assessment_id))
                    if assessment[0]:
                        cursor.execute('UPDATE special_projects SET specialization_level = ? WHERE project_id = ?',
                                     (assessment[1], assessment[0]))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'完成评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_assessment_report(self, project_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT a.*, ar.dimension, ar.score, ar.weight, ar.comment
                    FROM project_assessments a
                    LEFT JOIN assessment_records ar ON a.assessment_id = ar.assessment_id
                    WHERE a.project_id = ?
                    ORDER BY a.created_at DESC, ar.dimension
                ''', (project_id,))
                rows = cursor.fetchall()
                if not rows:
                    return {'success': False, 'error': '暂无评估记录'}
                reports = []
                current_assessment = None
                dimensions = []
                for row in rows:
                    if current_assessment != row['assessment_id']:
                        if current_assessment:
                            reports.append({'assessment': dict(assessment_data), 'dimensions': dimensions})
                        current_assessment = row['assessment_id']
                        assessment_data = {k: row[k] for k in ['assessment_id', 'project_id', 'assessment_type', 'assessor_name', 'assessment_date', 'overall_score', 'specialization_level', 'status']}
                        dimensions = []
                    dimensions.append({'dimension': row['dimension'], 'score': row['score'], 'weight': row['weight'], 'comment': row['comment']})
                reports.append({'assessment': dict(assessment_data), 'dimensions': dimensions})
                return {'success': True, 'reports': reports}
        except Exception as e:
            logger.error(f'获取评估报告失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 项目展示 ==========

    def create_showcase(self, project_id: str, showcase_name: str,
                        education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            showcase_id = f"shw_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO project_showcases (
                            showcase_id, project_id, showcase_name,
                            education_type, location, start_date,
                            end_date, description, visitor_count,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 'planned', ?, ?)
                    ''', (showcase_id, project_id, showcase_name, education_type,
                          kwargs.get('location'), kwargs.get('start_date', now[:10]),
                          kwargs.get('end_date'), kwargs.get('description'), now, now))
                    conn.commit()
                    return {'success': True, 'showcase_id': showcase_id}
        except Exception as e:
            logger.error(f'创建展示失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_showcase_item(self, showcase_id: str, item_type: str, title: str,
                          **kwargs) -> Dict[str, Any]:
        try:
            item_id = f"shitem_{uuid.uuid4().hex[:12]}"
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO showcase_items (
                            item_id, showcase_id, item_type, title,
                            description, media_url, order_num
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (item_id, showcase_id, item_type, title,
                          kwargs.get('description'), kwargs.get('media_url'),
                          kwargs.get('order_num', 0)))
                    conn.commit()
                    return {'success': True, 'item_id': item_id}
        except Exception as e:
            logger.error(f'添加展示内容失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_visitor_count(self, showcase_id: str, count: int = 1) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE project_showcases SET visitor_count = visitor_count + ? WHERE showcase_id = ?',
                                 (count, showcase_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '展示不存在'}
        except Exception as e:
            logger.error(f'更新访客数失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 推广管理 ==========

    def create_promotion(self, project_id: str, channel: str, content: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            promotion_id = f"prm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO promotion_records (
                            promotion_id, project_id, channel, content,
                            target_audience, start_date, end_date,
                            reach_count, engagement_count, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, 'active', ?)
                    ''', (promotion_id, project_id, channel, content,
                          kwargs.get('target_audience'),
                          kwargs.get('start_date', now[:10]),
                          kwargs.get('end_date'), now))
                    conn.commit()
                    return {'success': True, 'promotion_id': promotion_id}
        except Exception as e:
            logger.error(f'创建推广记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_promotion_stats(self, promotion_id: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    fields = []
                    values = []
                    for key in ['reach_count', 'engagement_count', 'status']:
                        if key in kwargs:
                            fields.append(f"{key} = ?")
                            values.append(kwargs[key])
                    if not fields:
                        return {'success': False, 'error': '没有需要更新的字段'}
                    values.append(promotion_id)
                    cursor.execute(f'UPDATE promotion_records SET {", ".join(fields)} WHERE promotion_id = ?', values)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '推广记录不存在'}
        except Exception as e:
            logger.error(f'更新推广统计失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_promotion_effect(self, project_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT channel, SUM(reach_count) as total_reach, SUM(engagement_count) as total_engagement
                    FROM promotion_records
                    WHERE project_id = ?
                    GROUP BY channel
                ''', (project_id,))
                effects = [dict(e) for e in cursor.fetchall()]
                cursor.execute('SELECT SUM(reach_count) as total, SUM(engagement_count) as engagement FROM promotion_records WHERE project_id = ?', (project_id,))
                overall = cursor.fetchone()
                return {'success': True, 'effects': effects, 'overall': dict(overall) if overall else {}}
        except Exception as e:
            logger.error(f'获取推广效果失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 ==========

    def get_project_statistics(self, education_type: str = None,
                               project_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT COUNT(*) as total FROM special_projects WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if project_type:
                    query += ' AND project_type = ?'
                    params.append(project_type)
                cursor.execute(query, params)
                total = cursor.fetchone()['total']

                query_status = 'SELECT status, COUNT(*) as count FROM special_projects WHERE 1=1'
                if education_type:
                    query_status += ' AND education_type = ?'
                if project_type:
                    query_status += ' AND project_type = ?'
                query_status += ' GROUP BY status'
                cursor.execute(query_status, params)
                status_dist = [dict(s) for s in cursor.fetchall()]

                query_level = 'SELECT specialization_level, COUNT(*) as count FROM special_projects WHERE specialization_level IS NOT NULL'
                if education_type:
                    query_level += ' AND education_type = ?'
                if project_type:
                    query_level += ' AND project_type = ?'
                query_level += ' GROUP BY specialization_level'
                cursor.execute(query_level, params)
                level_dist = [dict(l) for l in cursor.fetchall()]

                query_type = 'SELECT project_type, COUNT(*) as count FROM special_projects WHERE 1=1'
                if education_type:
                    query_type += ' AND education_type = ?'
                if project_type:
                    query_type += ' AND project_type = ?'
                query_type += ' GROUP BY project_type'
                cursor.execute(query_type, params)
                type_dist = [dict(t) for t in cursor.fetchall()]

                return {
                    'success': True,
                    'total_projects': total,
                    'status_distribution': status_dist,
                    'level_distribution': level_dist,
                    'type_distribution': type_dist
                }
        except Exception as e:
            logger.error(f'获取项目统计失败: {e}')
            return {'success': False, 'error': str(e)}