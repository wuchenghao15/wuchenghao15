#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教师发展与培训服务 (v15.8.0)
====================================
提供教师档案、培训管理、教研管理、评聘管理、师德考核、教学竞赛、
导师制结对等综合管理服务，支持成人教育和K12教育的差异化需求。

核心能力：
1. 教师档案 - 基本信息管理、资质证书、教学履历
2. 培训管理 - 培训计划、课程、报名、记录、学分
3. 教研管理 - 教研活动、课题研究、成果管理
4. 评聘管理 - 职称评定、岗位聘任、晋升管理
5. 师德考核 - 师德评价、违规记录、考核结果
6. 教学竞赛 - 竞赛组织、报名、评审、获奖
7. 导师制 - 老带新结对、培养计划、考核
8. 成人教育教师与K12教师差异化发展
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'teacher_development_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('TeacherDevelopment')


# ========== 教师发展配置 ==========

# 教师职称
TEACHER_TITLES = {
    'intern': {'name': '见习教师', 'level': 1, 'min_years': 0, 'min_papers': 0},
    'assistant': {'name': '初级教师', 'level': 2, 'min_years': 1, 'min_papers': 0},
    'intermediate': {'name': '中级教师', 'level': 3, 'min_years': 4, 'min_papers': 1},
    'senior': {'name': '高级教师', 'level': 4, 'min_years': 8, 'min_papers': 3},
    'professor': {'name': '正高级教师', 'level': 5, 'min_years': 12, 'min_papers': 5},
    'special': {'name': '特级教师', 'level': 6, 'min_years': 15, 'min_papers': 8}
}

# 教师角色
TEACHER_ROLES = {
    'subject_teacher': {'name': '学科教师', 'level': 1},
    'head_teacher': {'name': '班主任', 'level': 2},
    'grade_leader': {'name': '年级组长', 'level': 3},
    'subject_leader': {'name': '教研组长', 'level': 3},
    'deputy_director': {'name': '副主任', 'level': 4},
    'director': {'name': '主任', 'level': 5},
    'vice_principal': {'name': '副校长', 'level': 6},
    'principal': {'name': '校长', 'level': 7}
}

# 培训类型
TRAINING_TYPES = {
    'induction': {'name': '入职培训', 'default_hours': 32},
    'on_job': {'name': '在岗培训', 'default_hours': 16},
    'special_topic': {'name': '专题培训', 'default_hours': 8},
    'academic': {'name': '学术培训', 'default_hours': 24},
    'leadership': {'name': '管理培训', 'default_hours': 40},
    'it': {'name': '信息技术培训', 'default_hours': 16},
    'language': {'name': '语言培训', 'default_hours': 20},
    'safety': {'name': '安全培训', 'default_hours': 8}
}

# 培训状态
TRAINING_STATUS = {
    'planned': {'name': '计划中'},
    'registration': {'name': '报名中'},
    'in_progress': {'name': '进行中'},
    'completed': {'name': '已完成'},
    'cancelled': {'name': '已取消'}
}

# 教研类型
RESEARCH_TYPES = {
    'teaching_research': {'name': '教学研究'},
    'curriculum': {'name': '课程开发'},
    'lesson_preparation': {'name': '集体备课'},
    'peer_observation': {'name': '互听互评'},
    'topic_research': {'name': '课题研究'},
    'exchange': {'name': '交流研讨'}
}

# 课题级别
RESEARCH_LEVELS = {
    'school': {'name': '校级', 'funding_max': 5000},
    'district': {'name': '区级', 'funding_max': 20000},
    'city': {'name': '市级', 'funding_max': 50000},
    'provincial': {'name': '省级', 'funding_max': 200000},
    'national': {'name': '国家级', 'funding_max': 1000000}
}

# 师德考核等级
ETHICS_GRADES = {
    'excellent': {'name': '优秀', 'score_range': '>=90'},
    'good': {'name': '良好', 'score_range': '>=80'},
    'qualified': {'name': '合格', 'score_range': '>=60'},
    'unqualified': {'name': '不合格', 'score_range': '<60'}
}

# 竞赛类型
COMPETITION_TYPES = {
    'teaching': {'name': '优质课竞赛'},
    'course_design': {'name': '教学设计竞赛'},
    'thesis': {'name': '论文竞赛'},
    'basics': {'name': '基本功竞赛'},
    'innovation': {'name': '创新竞赛'},
    'multimedia': {'name': '课件竞赛'}
}

# 获奖等级
AWARD_LEVELS = {
    'special': {'name': '特等奖', 'bonus': 3000},
    'first': {'name': '一等奖', 'bonus': 2000},
    'second': {'name': '二等奖', 'bonus': 1000},
    'third': {'name': '三等奖', 'bonus': 500},
    'excellence': {'name': '优秀奖', 'bonus': 200}
}

# 导师制状态
MENTORSHIP_STATUS = {
    'active': {'name': '培养中'},
    'completed': {'name': '已完成'},
    'terminated': {'name': '已终止'}
}


class TeacherDevelopmentService:
    """教师发展与培训服务"""

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
                # 教师档案
                cursor.execute('''CREATE TABLE IF NOT EXISTS teacher_profiles (
                    teacher_id TEXT PRIMARY KEY, user_id TEXT, name TEXT NOT NULL,
                    gender TEXT, birth_date TEXT, education_background TEXT,
                    graduation_school TEXT, major TEXT, title TEXT, role TEXT,
                    hire_date TEXT, education_type TEXT, subjects TEXT, certifications TEXT,
                    teaching_years INTEGER DEFAULT 0, total_training_hours REAL DEFAULT 0,
                    total_research_count INTEGER DEFAULT 0, total_awards INTEGER DEFAULT 0,
                    ethics_score REAL DEFAULT 100, status TEXT DEFAULT 'active',
                    created_at TEXT, updated_at TEXT)''')
                # 培训计划
                cursor.execute('''CREATE TABLE IF NOT EXISTS training_programs (
                    program_id TEXT PRIMARY KEY, program_name TEXT NOT NULL, training_type TEXT,
                    description TEXT, target_audience TEXT, instructor TEXT, location TEXT,
                    start_date TEXT, end_date TEXT, total_hours REAL DEFAULT 0,
                    credit_points REAL DEFAULT 0, max_participants INTEGER DEFAULT 50,
                    registered_count INTEGER DEFAULT 0, status TEXT DEFAULT 'planned',
                    created_at TEXT, updated_at TEXT)''')
                # 培训报名
                cursor.execute('''CREATE TABLE IF NOT EXISTS training_registrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, program_id TEXT NOT NULL,
                    teacher_id TEXT NOT NULL, teacher_name TEXT, register_date TEXT,
                    attendance_hours REAL DEFAULT 0, completion_status TEXT DEFAULT 'registered',
                    score REAL, credit_earned REAL DEFAULT 0, certificate_issued INTEGER DEFAULT 0,
                    created_at TEXT)''')
                # 培训课时
                cursor.execute('''CREATE TABLE IF NOT EXISTS training_sessions (
                    session_id TEXT PRIMARY KEY, program_id TEXT NOT NULL,
                    session_name TEXT NOT NULL, session_date TEXT, start_time TEXT,
                    end_time TEXT, duration_hours REAL DEFAULT 0, instructor TEXT,
                    location TEXT, content TEXT, created_at TEXT)''')
                # 教研活动
                cursor.execute('''CREATE TABLE IF NOT EXISTS research_activities (
                    activity_id TEXT PRIMARY KEY, activity_name TEXT NOT NULL, research_type TEXT,
                    organizer TEXT, description TEXT, location TEXT, start_date TEXT, end_date TEXT,
                    participants_count INTEGER DEFAULT 0, outcome TEXT, created_at TEXT, updated_at TEXT)''')
                # 课题研究
                cursor.execute('''CREATE TABLE IF NOT EXISTS research_topics (
                    topic_id TEXT PRIMARY KEY, topic_name TEXT NOT NULL, research_type TEXT,
                    level TEXT, leader_id TEXT, leader_name TEXT, members TEXT, start_date TEXT,
                    end_date TEXT, budget REAL DEFAULT 0, status TEXT DEFAULT 'ongoing',
                    findings TEXT, created_at TEXT, updated_at TEXT)''')
                # 教研成果
                cursor.execute('''CREATE TABLE IF NOT EXISTS research_achievements (
                    achievement_id TEXT PRIMARY KEY, topic_id TEXT, teacher_id TEXT NOT NULL,
                    achievement_type TEXT, title TEXT NOT NULL, publication TEXT,
                    publish_date TEXT, level TEXT, description TEXT, created_at TEXT)''')
                # 职称评定
                cursor.execute('''CREATE TABLE IF NOT EXISTS title_assessments (
                    assessment_id TEXT PRIMARY KEY, teacher_id TEXT NOT NULL, teacher_name TEXT,
                    current_title TEXT, target_title TEXT, application_date TEXT,
                    qualifications TEXT, review_status TEXT DEFAULT 'pending', review_score REAL,
                    review_comment TEXT, reviewed_by TEXT, reviewed_at TEXT,
                    created_at TEXT, updated_at TEXT)''')
                # 师德考核
                cursor.execute('''CREATE TABLE IF NOT EXISTS ethics_evaluations (
                    eval_id TEXT PRIMARY KEY, teacher_id TEXT NOT NULL, teacher_name TEXT,
                    eval_period TEXT, eval_year INTEGER, self_score REAL DEFAULT 0,
                    peer_score REAL DEFAULT 0, student_score REAL DEFAULT 0,
                    supervisor_score REAL DEFAULT 0, total_score REAL DEFAULT 0, grade TEXT,
                    evaluator TEXT, violations TEXT, created_at TEXT)''')
                # 师德违规记录
                cursor.execute('''CREATE TABLE IF NOT EXISTS ethics_violations (
                    violation_id TEXT PRIMARY KEY, teacher_id TEXT NOT NULL, teacher_name TEXT,
                    violation_type TEXT, violation_date TEXT, description TEXT, severity TEXT,
                    penalty TEXT, reporter TEXT, handled_by TEXT, status TEXT DEFAULT 'reported',
                    created_at TEXT)''')
                # 教学竞赛
                cursor.execute('''CREATE TABLE IF NOT EXISTS teaching_competitions (
                    competition_id TEXT PRIMARY KEY, competition_name TEXT NOT NULL,
                    competition_type TEXT, organizer TEXT, level TEXT, description TEXT,
                    start_date TEXT, end_date TEXT, registration_deadline TEXT,
                    max_participants INTEGER DEFAULT 50, registered_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'scheduled', created_at TEXT, updated_at TEXT)''')
                # 竞赛报名
                cursor.execute('''CREATE TABLE IF NOT EXISTS competition_registrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, competition_id TEXT NOT NULL,
                    teacher_id TEXT NOT NULL, teacher_name TEXT, category TEXT, work_title TEXT,
                    work_desc TEXT, submit_date TEXT, score REAL, award_level TEXT,
                    award_certificate TEXT, status TEXT DEFAULT 'registered', created_at TEXT)''')
                # 导师制结对
                cursor.execute('''CREATE TABLE IF NOT EXISTS mentorships (
                    mentorship_id TEXT PRIMARY KEY, mentor_id TEXT NOT NULL, mentor_name TEXT,
                    mentee_id TEXT NOT NULL, mentee_name TEXT, start_date TEXT, end_date TEXT,
                    plan_desc TEXT, goals TEXT, progress TEXT, mentor_eval REAL, mentee_eval REAL,
                    status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT)''')
                # 培养记录
                cursor.execute('''CREATE TABLE IF NOT EXISTS mentorship_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, mentorship_id TEXT NOT NULL,
                    record_date TEXT, activity_type TEXT, content TEXT, outcome TEXT,
                    mentor_feedback TEXT, mentee_reflection TEXT, created_at TEXT)''')
                conn.commit()
                logger.info('教师发展与培训服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 教师档案 ==========

    def register_teacher(self, name: str, **kwargs) -> Dict[str, Any]:
        try:
            teacher_id = f"td_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO teacher_profiles (
                            teacher_id, user_id, name, gender, birth_date,
                            education_background, graduation_school, major,
                            title, role, hire_date, education_type, subjects,
                            certifications, teaching_years, total_training_hours,
                            total_research_count, total_awards, ethics_score,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, 100, 'active', ?, ?)
                    ''', (teacher_id, kwargs.get('user_id'), name,
                          kwargs.get('gender'), kwargs.get('birth_date'),
                          kwargs.get('education_background'),
                          kwargs.get('graduation_school'), kwargs.get('major'),
                          kwargs.get('title', 'intern'),
                          kwargs.get('role', 'subject_teacher'),
                          kwargs.get('hire_date', now[:10]),
                          kwargs.get('education_type', 'common'),
                          json.dumps(kwargs.get('subjects', []), ensure_ascii=False),
                          json.dumps(kwargs.get('certifications', []), ensure_ascii=False),
                          kwargs.get('teaching_years', 0), now, now))
                    conn.commit()
                    logger.info(f'注册教师档案: {name} ({teacher_id})')
                    return {'success': True, 'teacher_id': teacher_id}
        except Exception as e:
            logger.error(f'注册教师档案失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_teacher(self, teacher_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM teacher_profiles WHERE teacher_id = ?', (teacher_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '教师不存在'}
                teacher = dict(row)
                teacher['subjects'] = json.loads(teacher.get('subjects') or '[]')
                teacher['certifications'] = json.loads(teacher.get('certifications') or '[]')
                return {'success': True, 'teacher': teacher}
        except Exception as e:
            logger.error(f'获取教师详情失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_teacher(self, teacher_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            allowed_fields = ['user_id', 'gender', 'birth_date', 'education_background',
                              'graduation_school', 'major', 'title', 'role', 'hire_date',
                              'education_type', 'teaching_years', 'status']
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT teacher_id FROM teacher_profiles WHERE teacher_id = ?', (teacher_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '教师不存在'}
                    updates = []
                    params = []
                    for field in allowed_fields:
                        if field in kwargs:
                            updates.append(f'{field} = ?')
                            params.append(kwargs[field])
                    if 'subjects' in kwargs:
                        updates.append('subjects = ?')
                        params.append(json.dumps(kwargs['subjects'], ensure_ascii=False))
                    if 'certifications' in kwargs:
                        updates.append('certifications = ?')
                        params.append(json.dumps(kwargs['certifications'], ensure_ascii=False))
                    if not updates:
                        return {'success': False, 'error': '无可更新字段'}
                    updates.append('updated_at = ?')
                    params.append(now)
                    params.append(teacher_id)
                    cursor.execute(f'UPDATE teacher_profiles SET {", ".join(updates)} WHERE teacher_id = ?', params)
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'更新教师档案失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_teachers(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM teacher_profiles WHERE 1=1'
                params = []
                if filters.get('title'):
                    query += ' AND title = ?'
                    params.append(filters['title'])
                if filters.get('education_type'):
                    query += ' AND education_type = ?'
                    params.append(filters['education_type'])
                if filters.get('role'):
                    query += ' AND role = ?'
                    params.append(filters['role'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                teachers = []
                for row in cursor.fetchall():
                    teacher = dict(row)
                    teacher['subjects'] = json.loads(teacher.get('subjects') or '[]')
                    teacher['certifications'] = json.loads(teacher.get('certifications') or '[]')
                    teachers.append(teacher)
                return {'success': True, 'teachers': teachers, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取教师列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 培训管理 ==========

    def create_training_program(self, program_name: str, training_type: str,
                                 **kwargs) -> Dict[str, Any]:
        try:
            program_id = f"tp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = TRAINING_TYPES.get(training_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO training_programs (
                            program_id, program_name, training_type, description,
                            target_audience, instructor, location, start_date,
                            end_date, total_hours, credit_points, max_participants,
                            registered_count, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
                    ''', (program_id, program_name, training_type,
                          kwargs.get('description'), kwargs.get('target_audience'),
                          kwargs.get('instructor'), kwargs.get('location'),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('total_hours', config.get('default_hours', 16)),
                          kwargs.get('credit_points', 0),
                          kwargs.get('max_participants', 50),
                          kwargs.get('status', 'planned'), now, now))
                    conn.commit()
                    logger.info(f'创建培训计划: {program_name} ({program_id})')
                    return {'success': True, 'program_id': program_id}
        except Exception as e:
            logger.error(f'创建培训计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_training(self, program_id: str, teacher_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, registered_count, status FROM training_programs WHERE program_id = ?', (program_id,))
                    program = cursor.fetchone()
                    if not program:
                        return {'success': False, 'error': '培训计划不存在'}
                    if program[2] not in ('registration', 'planned'):
                        return {'success': False, 'error': '培训状态不允许报名'}
                    if program[0] and program[1] >= program[0]:
                        return {'success': False, 'error': '培训名额已满'}
                    cursor.execute('SELECT id FROM training_registrations WHERE program_id = ? AND teacher_id = ?', (program_id, teacher_id))
                    if cursor.fetchone():
                        return {'success': False, 'error': '已报名该培训'}
                    cursor.execute('SELECT name FROM teacher_profiles WHERE teacher_id = ?', (teacher_id,))
                    teacher = cursor.fetchone()
                    teacher_name = teacher[0] if teacher else None
                    cursor.execute('''
                        INSERT INTO training_registrations (program_id, teacher_id, teacher_name, register_date, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (program_id, teacher_id, teacher_name, now[:10], now))
                    cursor.execute('UPDATE training_programs SET registered_count = registered_count + 1, updated_at = ? WHERE program_id = ?', (now, program_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'培训报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_training_session(self, program_id: str, session_name: str,
                                 **kwargs) -> Dict[str, Any]:
        try:
            session_id = f"ts_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO training_sessions (
                            session_id, program_id, session_name, session_date,
                            start_time, end_time, duration_hours, instructor,
                            location, content, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (session_id, program_id, session_name,
                          kwargs.get('session_date', now[:10]),
                          kwargs.get('start_time'), kwargs.get('end_time'),
                          kwargs.get('duration_hours', 0),
                          kwargs.get('instructor'), kwargs.get('location'),
                          kwargs.get('content'), now))
                    if kwargs.get('duration_hours'):
                        cursor.execute('SELECT id, teacher_id FROM training_registrations WHERE program_id = ?', (program_id,))
                        registrations = cursor.fetchall()
                        for reg in registrations:
                            cursor.execute('UPDATE training_registrations SET attendance_hours = attendance_hours + ? WHERE id = ?',
                                         (kwargs['duration_hours'], reg[0]))
                            cursor.execute('UPDATE teacher_profiles SET total_training_hours = total_training_hours + ? WHERE teacher_id = ?',
                                         (kwargs['duration_hours'], reg[1]))
                    conn.commit()
                    return {'success': True, 'session_id': session_id}
        except Exception as e:
            logger.error(f'记录培训课时失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_training_registration(self, reg_id: int, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT program_id, teacher_id FROM training_registrations WHERE id = ?', (reg_id,))
                    reg = cursor.fetchone()
                    if not reg:
                        return {'success': False, 'error': '培训报名记录不存在'}
                    score = kwargs.get('score')
                    credit_earned = kwargs.get('credit_earned', 0)
                    certificate_issued = 1 if kwargs.get('certificate_issued') else 0
                    cursor.execute('''
                        UPDATE training_registrations SET
                            completion_status = 'completed', score = ?,
                            credit_earned = ?, certificate_issued = ?
                        WHERE id = ?
                    ''', (score, credit_earned, certificate_issued, reg_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'完成培训失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_training_programs(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM training_programs WHERE 1=1'
                params = []
                if filters.get('training_type'):
                    query += ' AND training_type = ?'
                    params.append(filters['training_type'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                programs = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'programs': programs, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取培训列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 教研管理 ==========

    def organize_research_activity(self, activity_name: str, research_type: str,
                                    **kwargs) -> Dict[str, Any]:
        try:
            activity_id = f"ra_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO research_activities (
                            activity_id, activity_name, research_type, organizer,
                            description, location, start_date, end_date,
                            participants_count, outcome, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (activity_id, activity_name, research_type,
                          kwargs.get('organizer'), kwargs.get('description'),
                          kwargs.get('location'), kwargs.get('start_date'),
                          kwargs.get('end_date'),
                          kwargs.get('participants_count', 0),
                          kwargs.get('outcome'), now, now))
                    conn.commit()
                    logger.info(f'组织教研活动: {activity_name} ({activity_id})')
                    return {'success': True, 'activity_id': activity_id}
        except Exception as e:
            logger.error(f'组织教研活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_research_topic(self, topic_name: str, research_type: str,
                               level: str, **kwargs) -> Dict[str, Any]:
        try:
            topic_id = f"rt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO research_topics (
                            topic_id, topic_name, research_type, level,
                            leader_id, leader_name, members, start_date,
                            end_date, budget, status, findings, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (topic_id, topic_name, research_type, level,
                          kwargs.get('leader_id'), kwargs.get('leader_name'),
                          json.dumps(kwargs.get('members', []), ensure_ascii=False),
                          kwargs.get('start_date', now[:10]),
                          kwargs.get('end_date'),
                          kwargs.get('budget', 0),
                          kwargs.get('status', 'ongoing'),
                          kwargs.get('findings'), now, now))
                    if kwargs.get('leader_id'):
                        cursor.execute('UPDATE teacher_profiles SET total_research_count = total_research_count + 1 WHERE teacher_id = ?',
                                     (kwargs['leader_id'],))
                    conn.commit()
                    logger.info(f'创建课题研究: {topic_name} ({topic_id})')
                    return {'success': True, 'topic_id': topic_id}
        except Exception as e:
            logger.error(f'创建课题研究失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_research_achievement(self, topic_id: str, teacher_id: str,
                                     achievement_type: str, title: str,
                                     **kwargs) -> Dict[str, Any]:
        try:
            achievement_id = f"ach_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO research_achievements (
                            achievement_id, topic_id, teacher_id, achievement_type,
                            title, publication, publish_date, level, description, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (achievement_id, topic_id, teacher_id, achievement_type,
                          title, kwargs.get('publication'),
                          kwargs.get('publish_date', now[:10]),
                          kwargs.get('level'), kwargs.get('description'), now))
                    conn.commit()
                    logger.info(f'记录教研成果: {title} ({achievement_id})')
                    return {'success': True, 'achievement_id': achievement_id}
        except Exception as e:
            logger.error(f'记录教研成果失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_research_topics(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM research_topics WHERE 1=1'
                params = []
                if filters.get('research_type'):
                    query += ' AND research_type = ?'
                    params.append(filters['research_type'])
                if filters.get('level'):
                    query += ' AND level = ?'
                    params.append(filters['level'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                topics = []
                for row in cursor.fetchall():
                    topic = dict(row)
                    topic['members'] = json.loads(topic.get('members') or '[]')
                    topics.append(topic)
                return {'success': True, 'topics': topics, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取课题列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 评聘管理 ==========

    def submit_title_assessment(self, teacher_id: str, target_title: str,
                                 **kwargs) -> Dict[str, Any]:
        try:
            assessment_id = f"ta_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT name, title FROM teacher_profiles WHERE teacher_id = ?', (teacher_id,))
                    teacher = cursor.fetchone()
                    if not teacher:
                        return {'success': False, 'error': '教师不存在'}
                    current_title = teacher[1]
                    teacher_name = teacher[0]
                    cursor.execute('''
                        INSERT INTO title_assessments (
                            assessment_id, teacher_id, teacher_name, current_title,
                            target_title, application_date, qualifications,
                            review_status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                    ''', (assessment_id, teacher_id, teacher_name, current_title,
                          target_title, kwargs.get('application_date', now[:10]),
                          json.dumps(kwargs.get('qualifications', []), ensure_ascii=False),
                          now, now))
                    conn.commit()
                    logger.info(f'提交职称评定: {teacher_name} ({assessment_id})')
                    return {'success': True, 'assessment_id': assessment_id}
        except Exception as e:
            logger.error(f'提交职称评定失败: {e}')
            return {'success': False, 'error': str(e)}

    def review_title_assessment(self, assessment_id: str, approved: bool,
                                 **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            review_status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT teacher_id, target_title FROM title_assessments WHERE assessment_id = ? AND review_status = ?', (assessment_id, 'pending'))
                    assessment = cursor.fetchone()
                    if not assessment:
                        return {'success': False, 'error': '评定申请不存在或已审核'}
                    cursor.execute('''
                        UPDATE title_assessments SET
                            review_status = ?, review_score = ?,
                            review_comment = ?, reviewed_by = ?,
                            reviewed_at = ?, updated_at = ?
                        WHERE assessment_id = ?
                    ''', (review_status, kwargs.get('review_score'),
                          kwargs.get('review_comment'), kwargs.get('reviewed_by'),
                          now, now, assessment_id))
                    if approved:
                        cursor.execute('UPDATE teacher_profiles SET title = ?, updated_at = ? WHERE teacher_id = ?',
                                     (assessment[1], now, assessment[0]))
                    conn.commit()
                    return {'success': True, 'review_status': review_status}
        except Exception as e:
            logger.error(f'审核职称评定失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_title_assessments(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM title_assessments WHERE 1=1'
                params = []
                if filters.get('teacher_id'):
                    query += ' AND teacher_id = ?'
                    params.append(filters['teacher_id'])
                if filters.get('review_status'):
                    query += ' AND review_status = ?'
                    params.append(filters['review_status'])
                if filters.get('target_title'):
                    query += ' AND target_title = ?'
                    params.append(filters['target_title'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                assessments = []
                for row in cursor.fetchall():
                    a = dict(row)
                    a['qualifications'] = json.loads(a.get('qualifications') or '[]')
                    assessments.append(a)
                return {'success': True, 'assessments': assessments, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取评定列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 师德考核 ==========

    def create_ethics_evaluation(self, teacher_id: str, eval_period: str,
                                  eval_year: int, **kwargs) -> Dict[str, Any]:
        try:
            eval_id = f"ee_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            self_score = kwargs.get('self_score', 0)
            peer_score = kwargs.get('peer_score', 0)
            student_score = kwargs.get('student_score', 0)
            supervisor_score = kwargs.get('supervisor_score', 0)
            # 总分计算：自评10% + 同行30% + 学生40% + 上级20%
            total_score = round(self_score * 0.1 + peer_score * 0.3 + student_score * 0.4 + supervisor_score * 0.2, 1)
            # 等级判定
            if total_score >= 90:
                grade = 'excellent'
            elif total_score >= 80:
                grade = 'good'
            elif total_score >= 60:
                grade = 'qualified'
            else:
                grade = 'unqualified'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT name, ethics_score FROM teacher_profiles WHERE teacher_id = ?', (teacher_id,))
                    teacher = cursor.fetchone()
                    if not teacher:
                        return {'success': False, 'error': '教师不存在'}
                    teacher_name = teacher[0]
                    cursor.execute('''
                        INSERT INTO ethics_evaluations (
                            eval_id, teacher_id, teacher_name, eval_period,
                            eval_year, self_score, peer_score, student_score,
                            supervisor_score, total_score, grade, evaluator,
                            violations, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (eval_id, teacher_id, teacher_name, eval_period, eval_year,
                          self_score, peer_score, student_score, supervisor_score,
                          total_score, grade, kwargs.get('evaluator'),
                          json.dumps(kwargs.get('violations', []), ensure_ascii=False),
                          now))
                    cursor.execute('UPDATE teacher_profiles SET ethics_score = ?, updated_at = ? WHERE teacher_id = ?',
                                 (total_score, now, teacher_id))
                    conn.commit()
                    logger.info(f'创建师德考核: {teacher_name} ({eval_id}) 等级={grade}')
                    return {'success': True, 'eval_id': eval_id, 'total_score': total_score, 'grade': grade}
        except Exception as e:
            logger.error(f'创建师德考核失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_ethics_violation(self, teacher_id: str, violation_type: str,
                                 **kwargs) -> Dict[str, Any]:
        try:
            violation_id = f"ev_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            # 根据严重程度扣减师德分
            severity = kwargs.get('severity', 'minor')
            deduction = {'minor': 5, 'moderate': 15, 'major': 30, 'severe': 50}.get(severity, 5)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT name, ethics_score FROM teacher_profiles WHERE teacher_id = ?', (teacher_id,))
                    teacher = cursor.fetchone()
                    if not teacher:
                        return {'success': False, 'error': '教师不存在'}
                    teacher_name = teacher[0]
                    new_score = max(0, (teacher[1] or 100) - deduction)
                    cursor.execute('''
                        INSERT INTO ethics_violations (
                            violation_id, teacher_id, teacher_name, violation_type,
                            violation_date, description, severity, penalty,
                            reporter, handled_by, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (violation_id, teacher_id, teacher_name, violation_type,
                          kwargs.get('violation_date', now[:10]),
                          kwargs.get('description'), severity,
                          kwargs.get('penalty'), kwargs.get('reporter'),
                          kwargs.get('handled_by'),
                          kwargs.get('status', 'reported'), now))
                    cursor.execute('UPDATE teacher_profiles SET ethics_score = ?, updated_at = ? WHERE teacher_id = ?',
                                 (new_score, now, teacher_id))
                    conn.commit()
                    logger.info(f'记录师德违规: {teacher_name} ({violation_id}) 扣减{deduction}分')
                    return {'success': True, 'violation_id': violation_id,
                            'deduction': deduction, 'current_ethics_score': new_score}
        except Exception as e:
            logger.error(f'记录师德违规失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_ethics_evaluations(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM ethics_evaluations WHERE 1=1'
                params = []
                if filters.get('teacher_id'):
                    query += ' AND teacher_id = ?'
                    params.append(filters['teacher_id'])
                if filters.get('grade'):
                    query += ' AND grade = ?'
                    params.append(filters['grade'])
                if filters.get('eval_year'):
                    query += ' AND eval_year = ?'
                    params.append(filters['eval_year'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                evaluations = []
                for row in cursor.fetchall():
                    e = dict(row)
                    e['violations'] = json.loads(e.get('violations') or '[]')
                    evaluations.append(e)
                return {'success': True, 'evaluations': evaluations, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取师德考核列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 教学竞赛 ==========

    def organize_competition(self, competition_name: str, competition_type: str,
                              **kwargs) -> Dict[str, Any]:
        try:
            competition_id = f"cmp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO teaching_competitions (
                            competition_id, competition_name, competition_type,
                            organizer, level, description, start_date, end_date,
                            registration_deadline, max_participants,
                            registered_count, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
                    ''', (competition_id, competition_name, competition_type,
                          kwargs.get('organizer'), kwargs.get('level'),
                          kwargs.get('description'), kwargs.get('start_date'),
                          kwargs.get('end_date'),
                          kwargs.get('registration_deadline'),
                          kwargs.get('max_participants', 50),
                          kwargs.get('status', 'scheduled'), now, now))
                    conn.commit()
                    logger.info(f'组织教学竞赛: {competition_name} ({competition_id})')
                    return {'success': True, 'competition_id': competition_id}
        except Exception as e:
            logger.error(f'组织教学竞赛失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_competition(self, competition_id: str, teacher_id: str,
                              **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, registered_count, status FROM teaching_competitions WHERE competition_id = ?', (competition_id,))
                    competition = cursor.fetchone()
                    if not competition:
                        return {'success': False, 'error': '竞赛不存在'}
                    if competition[2] != 'scheduled':
                        return {'success': False, 'error': '竞赛状态不允许报名'}
                    if competition[0] and competition[1] >= competition[0]:
                        return {'success': False, 'error': '竞赛名额已满'}
                    cursor.execute('SELECT id FROM competition_registrations WHERE competition_id = ? AND teacher_id = ?', (competition_id, teacher_id))
                    if cursor.fetchone():
                        return {'success': False, 'error': '已报名该竞赛'}
                    cursor.execute('SELECT name FROM teacher_profiles WHERE teacher_id = ?', (teacher_id,))
                    teacher = cursor.fetchone()
                    teacher_name = teacher[0] if teacher else None
                    cursor.execute('''
                        INSERT INTO competition_registrations (
                            competition_id, teacher_id, teacher_name, category,
                            work_title, work_desc, submit_date, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'registered', ?)
                    ''', (competition_id, teacher_id, teacher_name,
                          kwargs.get('category'), kwargs.get('work_title'),
                          kwargs.get('work_desc'), now[:10], now))
                    cursor.execute('UPDATE teaching_competitions SET registered_count = registered_count + 1, updated_at = ? WHERE competition_id = ?', (now, competition_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'竞赛报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def score_competition(self, reg_id: int, score: float,
                           award_level: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            config = AWARD_LEVELS.get(award_level, {})
            certificate = kwargs.get('award_certificate') or (f"CER{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}" if award_level else None)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT competition_id, teacher_id FROM competition_registrations WHERE id = ?', (reg_id,))
                    reg = cursor.fetchone()
                    if not reg:
                        return {'success': False, 'error': '竞赛报名记录不存在'}
                    cursor.execute('''
                        UPDATE competition_registrations SET
                            score = ?, award_level = ?, award_certificate = ?,
                            status = 'scored'
                        WHERE id = ?
                    ''', (score, award_level, certificate, reg_id))
                    if award_level:
                        cursor.execute('UPDATE teacher_profiles SET total_awards = total_awards + 1, updated_at = ? WHERE teacher_id = ?',
                                     (now, reg[1]))
                    conn.commit()
                    logger.info(f'竞赛评分: reg_id={reg_id} 分数={score} 等级={config.get("name", award_level)}')
                    return {'success': True, 'award_certificate': certificate, 'bonus': config.get('bonus', 0)}
        except Exception as e:
            logger.error(f'竞赛评分失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_competitions(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM teaching_competitions WHERE 1=1'
                params = []
                if filters.get('competition_type'):
                    query += ' AND competition_type = ?'
                    params.append(filters['competition_type'])
                if filters.get('level'):
                    query += ' AND level = ?'
                    params.append(filters['level'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                competitions = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'competitions': competitions, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取竞赛列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 导师制 ==========

    def create_mentorship(self, mentor_id: str, mentee_id: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            mentorship_id = f"mt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT name FROM teacher_profiles WHERE teacher_id = ?', (mentor_id,))
                    mentor = cursor.fetchone()
                    cursor.execute('SELECT name FROM teacher_profiles WHERE teacher_id = ?', (mentee_id,))
                    mentee = cursor.fetchone()
                    if not mentor or not mentee:
                        return {'success': False, 'error': '导师或学员不存在'}
                    cursor.execute('''
                        INSERT INTO mentorships (
                            mentorship_id, mentor_id, mentor_name, mentee_id,
                            mentee_name, start_date, end_date, plan_desc,
                            goals, progress, mentor_eval, mentee_eval,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (mentorship_id, mentor_id, mentor[0], mentee_id, mentee[0],
                          kwargs.get('start_date', now[:10]),
                          kwargs.get('end_date'), kwargs.get('plan_desc'),
                          json.dumps(kwargs.get('goals', []), ensure_ascii=False),
                          kwargs.get('progress', ''), kwargs.get('mentor_eval'),
                          kwargs.get('mentee_eval'),
                          kwargs.get('status', 'active'), now, now))
                    conn.commit()
                    logger.info(f'建立导师制结对: {mentor[0]} -> {mentee[0]} ({mentorship_id})')
                    return {'success': True, 'mentorship_id': mentorship_id}
        except Exception as e:
            logger.error(f'建立导师制结对失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_mentorship_activity(self, mentorship_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT mentorship_id FROM mentorships WHERE mentorship_id = ?', (mentorship_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '导师制结对不存在'}
                    cursor.execute('''
                        INSERT INTO mentorship_records (
                            mentorship_id, record_date, activity_type, content,
                            outcome, mentor_feedback, mentee_reflection, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (mentorship_id, kwargs.get('record_date', now[:10]),
                          kwargs.get('activity_type'), kwargs.get('content'),
                          kwargs.get('outcome'), kwargs.get('mentor_feedback'),
                          kwargs.get('mentee_reflection'), now))
                    if kwargs.get('progress'):
                        cursor.execute('UPDATE mentorships SET progress = ?, updated_at = ? WHERE mentorship_id = ?',
                                     (kwargs['progress'], now, mentorship_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'记录培养活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_mentorship(self, mentorship_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT mentorship_id FROM mentorships WHERE mentorship_id = ? AND status = ?', (mentorship_id, 'active'))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '导师制结对不存在或已结束'}
                    cursor.execute('''
                        UPDATE mentorships SET
                            status = 'completed', end_date = ?,
                            mentor_eval = ?, mentee_eval = ?, progress = ?,
                            updated_at = ?
                        WHERE mentorship_id = ?
                    ''', (kwargs.get('end_date', now[:10]),
                          kwargs.get('mentor_eval'), kwargs.get('mentee_eval'),
                          kwargs.get('progress', '已完成'), now, mentorship_id))
                    conn.commit()
                    logger.info(f'完成导师制结对: {mentorship_id}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'完成导师制失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_mentorships(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM mentorships WHERE 1=1'
                params = []
                if filters.get('mentor_id'):
                    query += ' AND mentor_id = ?'
                    params.append(filters['mentor_id'])
                if filters.get('mentee_id'):
                    query += ' AND mentee_id = ?'
                    params.append(filters['mentee_id'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                mentorships = []
                for row in cursor.fetchall():
                    m = dict(row)
                    m['goals'] = json.loads(m.get('goals') or '[]')
                    mentorships.append(m)
                return {'success': True, 'mentorships': mentorships, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取导师制列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                teacher_filter = ' WHERE education_type = ?' if education_type else ''
                params = [education_type] if education_type else []
                # 教师职称分布
                cursor.execute(f'SELECT title, COUNT(*) FROM teacher_profiles{teacher_filter} GROUP BY title', params)
                title_dist = {row[0] or 'unknown': row[1] for row in cursor.fetchall()}
                # 培训完成情况
                cursor.execute('SELECT status, COUNT(*) FROM training_programs GROUP BY status')
                training_dist = {row[0]: row[1] for row in cursor.fetchall()}
                cursor.execute('SELECT COUNT(*) FROM training_registrations WHERE completion_status = ?', ('completed',))
                completed_training_count = cursor.fetchone()[0]
                # 课题级别分布
                cursor.execute('SELECT level, COUNT(*) FROM research_topics GROUP BY level')
                topic_level_dist = {row[0] or 'unknown': row[1] for row in cursor.fetchall()}
                # 师德考核分布
                cursor.execute('SELECT grade, COUNT(*) FROM ethics_evaluations GROUP BY grade')
                ethics_dist = {row[0] or 'unknown': row[1] for row in cursor.fetchall()}
                # 获奖统计
                cursor.execute('SELECT award_level, COUNT(*) FROM competition_registrations WHERE award_level IS NOT NULL GROUP BY award_level')
                award_dist = {row[0]: row[1] for row in cursor.fetchall()}
                cursor.execute('SELECT COUNT(*) FROM teacher_profiles' + teacher_filter, params)
                teacher_count = cursor.fetchone()[0]
                return {
                    'success': True,
                    'teacher_count': teacher_count,
                    'title_distribution': title_dist,
                    'training_status_distribution': training_dist,
                    'completed_training_count': completed_training_count,
                    'topic_level_distribution': topic_level_dist,
                    'ethics_grade_distribution': ethics_dist,
                    'award_distribution': award_dist
                }
        except Exception as e:
            logger.error(f'获取统计数据失败: {e}')
            return {'success': False, 'error': str(e)}


if __name__ == '__main__':
    service = TeacherDevelopmentService()
    print('教师发展与培训服务初始化完成')
    stats = service.get_statistics()
    print(f'统计: {stats}')
