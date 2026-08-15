#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 继续教育与终身学习服务 (v15.11.0)
==========================================
提供继续教育项目、课程、学员、证书、终身学习档案等综合管理服务。
主要服务成人继续教育用户，同时兼容 K12 终身学习启蒙理念。

核心能力：
1. 继续教育项目 - 学历继续教育、非学历培训、职业提升
2. 课程管理 - 继续教育课程、学习方式、学分认证
3. 学员管理 - 注册、学籍、学习计划
4. 证书管理 - 结业证书、学历证书、继续教育学分证明
5. 终身学习档案 - 学习历程、技能积累、成长轨迹
6. 学习成果认证 - 先前学习认证（RPL）、工作经验转换
7. 培训机构管理 - 合作机构、资质、课程供给
8. 成人继续教育与K12终身学习启蒙差异化
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'continuing_education_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ContinuingEducation')


# ========== 继续教育配置 ==========

# 项目类型
PROGRAM_TYPES = {
    'degree': {'name': '学历继续教育', 'awards_credential': True},
    'non_degree': {'name': '非学历培训', 'awards_credential': False},
    'certificate': {'name': '职业资格', 'awards_credential': True},
    'skill_training': {'name': '技能培训', 'awards_credential': False},
    'short_course': {'name': '短训', 'awards_credential': False},
    'community_education': {'name': '社区教育', 'awards_credential': False},
    'elderly_education': {'name': '老年教育', 'awards_credential': False}
}

# 学习方式
LEARNING_MODES = {
    'online_online': {'name': '线上', 'typical_schedule': '弹性时间'},
    'offline': {'name': '线下', 'typical_schedule': '固定面授'},
    'blended': {'name': '混合', 'typical_schedule': '线上+线下'},
    'self_paced': {'name': '自学', 'typical_schedule': '自主安排'},
    'tutorial': {'name': '辅导', 'typical_schedule': '导师指导'},
    'correspondence': {'name': '函授', 'typical_schedule': '集中面授+自学'}
}

# 学历层次
DEGREE_LEVELS = {
    'associate': {'name': '大专', 'duration_years': 3},
    'bachelor': {'name': '本科', 'duration_years': 4},
    'master': {'name': '硕士', 'duration_years': 3},
    'doctor': {'name': '博士', 'duration_years': 4},
    'non_degree': {'name': '非学历', 'duration_years': 0}
}

# 证书类型
CERTIFICATE_TYPES = {
    'completion': {'name': '结业', 'is_nationally_recognized': False},
    'degree': {'name': '学历', 'is_nationally_recognized': True},
    'credit_proof': {'name': '学分证明', 'is_nationally_recognized': False},
    'skill_certification': {'name': '技能认证', 'is_nationally_recognized': True},
    'continuing_education_credit': {'name': '继续教育学分', 'is_nationally_recognized': True}
}

# 学员状态
LEARNER_STATUS = {
    'active': {'name': '在读'}, 'completed': {'name': '已结业'},
    'graduated': {'name': '已毕业'}, 'withdrawn': {'name': '退学'},
    'suspended': {'name': '休学'}, 'transferred': {'name': '转出'}
}

# 先前学习认证类型
RPL_TYPES = {
    'work_experience': {'name': '工作经验', 'max_credits': 30},
    'previous_study': {'name': '先前学习', 'max_credits': 40},
    'military_service': {'name': '军旅经历', 'max_credits': 20},
    'volunteer_service': {'name': '志愿服务', 'max_credits': 10},
    'competition_award': {'name': '竞赛获奖', 'max_credits': 15},
    'self_study': {'name': '自学成果', 'max_credits': 25}
}

# 机构类型
INSTITUTION_TYPES = {
    'university': {'name': '高校', 'accreditation_required': True},
    'vocational': {'name': '职业院校', 'accreditation_required': True},
    'training_center': {'name': '培训中心', 'accreditation_required': True},
    'enterprise': {'name': '企业', 'accreditation_required': False},
    'industry_association': {'name': '行业协会', 'accreditation_required': True},
    'online_platform': {'name': '在线平台', 'accreditation_required': False},
    'community': {'name': '社区', 'accreditation_required': False}
}

# 终身学习等级
LIFELONG_LEARNING_LEVELS = {
    'bronze': {'name': '铜', 'min_hours': 50, 'min_courses': 3, 'badge': '🥉'},
    'silver': {'name': '银', 'min_hours': 200, 'min_courses': 8, 'badge': '🥈'},
    'gold': {'name': '金', 'min_hours': 500, 'min_courses': 15, 'badge': '🥇'},
    'platinum': {'name': '铂金', 'min_hours': 1000, 'min_courses': 25, 'badge': '💠'},
    'diamond': {'name': '钻', 'min_hours': 2000, 'min_courses': 40, 'badge': '💎'}
}


class ContinuingEducationService:
    """继续教育与终身学习服务"""

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
                # 继续教育项目
                cursor.execute('''CREATE TABLE IF NOT EXISTS ce_programs (
                    program_id TEXT PRIMARY KEY, program_name TEXT NOT NULL,
                    program_type TEXT, degree_level TEXT, description TEXT,
                    objectives TEXT, target_audience TEXT,
                    education_type TEXT DEFAULT 'adult', duration_months INTEGER,
                    total_credits REAL, total_hours INTEGER, tuition_fee REAL,
                    learning_mode TEXT, enrollment_quota INTEGER,
                    enrolled_count INTEGER DEFAULT 0, start_date TEXT, end_date TEXT,
                    status TEXT DEFAULT 'recruiting', partner_institution TEXT,
                    created_at TEXT, updated_at TEXT)''')
                # 继续教育课程
                cursor.execute('''CREATE TABLE IF NOT EXISTS ce_courses (
                    course_id TEXT PRIMARY KEY, program_id TEXT,
                    course_name TEXT NOT NULL, course_code TEXT, credit REAL,
                    hours INTEGER, learning_mode TEXT, instructor_id TEXT,
                    instructor_name TEXT, description TEXT, prerequisites TEXT,
                    assessment_method TEXT, is_required INTEGER DEFAULT 1,
                    max_students INTEGER DEFAULT 50, enrolled_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT)''')
                # 继续教育学员
                cursor.execute('''CREATE TABLE IF NOT EXISTS ce_learners (
                    learner_id TEXT PRIMARY KEY, user_id TEXT, name TEXT NOT NULL,
                    gender TEXT, birth_date TEXT, id_number TEXT, phone TEXT,
                    email TEXT, current_education_level TEXT, occupation TEXT,
                    work_unit TEXT, program_id TEXT, enroll_date TEXT,
                    expected_complete_date TEXT, status TEXT DEFAULT 'active',
                    total_credits REAL DEFAULT 0, completed_credits REAL DEFAULT 0,
                    gpa REAL DEFAULT 0, advisor_id TEXT, created_at TEXT, updated_at TEXT)''')
                # 课程选课
                cursor.execute('''CREATE TABLE IF NOT EXISTS ce_enrollments (
                    enrollment_id TEXT PRIMARY KEY, learner_id TEXT NOT NULL,
                    course_id TEXT NOT NULL, program_id TEXT, enroll_date TEXT,
                    complete_date TEXT, attendance_rate REAL, assignment_score REAL,
                    exam_score REAL, final_score REAL, credit_earned REAL DEFAULT 0,
                    status TEXT DEFAULT 'enrolled', created_at TEXT, updated_at TEXT)''')
                # 证书
                cursor.execute('''CREATE TABLE IF NOT EXISTS ce_certificates (
                    certificate_id TEXT PRIMARY KEY, learner_id TEXT NOT NULL,
                    learner_name TEXT, program_id TEXT, program_name TEXT,
                    certificate_type TEXT, certificate_number TEXT UNIQUE,
                    issue_date TEXT, expiry_date TEXT, credits REAL, gpa REAL,
                    degree_level TEXT, issued_by TEXT, verification_code TEXT,
                    status TEXT DEFAULT 'issued', created_at TEXT, updated_at TEXT)''')
                # 合作机构
                cursor.execute('''CREATE TABLE IF NOT EXISTS ce_institutions (
                    institution_id TEXT PRIMARY KEY, institution_name TEXT NOT NULL,
                    institution_type TEXT, accreditation_number TEXT, legal_person TEXT,
                    address TEXT, contact_phone TEXT, contact_email TEXT,
                    cooperation_type TEXT, provided_programs TEXT, rating REAL DEFAULT 0,
                    is_approved INTEGER DEFAULT 0, cooperation_start TEXT,
                    cooperation_end TEXT, created_at TEXT, updated_at TEXT)''')
                # 先前学习认证申请
                cursor.execute('''CREATE TABLE IF NOT EXISTS rpl_applications (
                    rpl_id TEXT PRIMARY KEY, learner_id TEXT NOT NULL,
                    learner_name TEXT, rpl_type TEXT, learning_description TEXT,
                    evidence TEXT, requested_credits REAL, assessed_credits REAL,
                    assessor_id TEXT, assessor_name TEXT, assessment_date TEXT,
                    assessment_result TEXT, status TEXT DEFAULT 'pending',
                    created_at TEXT, updated_at TEXT)''')
                # 终身学习档案
                cursor.execute('''CREATE TABLE IF NOT EXISTS lifelong_portfolios (
                    portfolio_id TEXT PRIMARY KEY, learner_id TEXT NOT NULL,
                    learner_name TEXT, total_learning_hours REAL DEFAULT 0,
                    total_courses INTEGER DEFAULT 0, total_credits REAL DEFAULT 0,
                    total_certificates INTEGER DEFAULT 0, skill_tags TEXT,
                    learning_history TEXT, level TEXT DEFAULT 'bronze', badges TEXT,
                    last_activity TEXT, created_at TEXT, updated_at TEXT)''')
                # 学习计划
                cursor.execute('''CREATE TABLE IF NOT EXISTS learning_plans (
                    plan_id TEXT PRIMARY KEY, learner_id TEXT NOT NULL,
                    learner_name TEXT, program_id TEXT, plan_name TEXT,
                    target_credits REAL, target_complete_date TEXT,
                    planned_courses TEXT, completed_courses TEXT,
                    progress_percent REAL DEFAULT 0, status TEXT DEFAULT 'active',
                    created_at TEXT, updated_at TEXT)''')
                # 考核记录
                cursor.execute('''CREATE TABLE IF NOT EXISTS ce_assessments (
                    assessment_id TEXT PRIMARY KEY, enrollment_id TEXT NOT NULL,
                    learner_id TEXT, course_id TEXT, assessment_type TEXT,
                    assessment_name TEXT, score REAL, max_score REAL DEFAULT 100,
                    weight REAL DEFAULT 0, weighted_score REAL DEFAULT 0,
                    assessed_date TEXT, assessed_by TEXT, created_at TEXT)''')
                # 学员进度
                cursor.execute('''CREATE TABLE IF NOT EXISTS learner_progress (
                    progress_id TEXT PRIMARY KEY, learner_id TEXT NOT NULL,
                    program_id TEXT, total_courses INTEGER DEFAULT 0,
                    completed_courses INTEGER DEFAULT 0, in_progress_courses INTEGER DEFAULT 0,
                    total_credits REAL DEFAULT 0, earned_credits REAL DEFAULT 0,
                    gpa REAL DEFAULT 0, completion_rate REAL DEFAULT 0,
                    last_activity TEXT, status TEXT DEFAULT 'active',
                    updated_at TEXT, created_at TEXT)''')
                conn.commit()
                logger.info('继续教育数据库初始化完成')
        except Exception as e:
            logger.error(f'初始化数据库失败: {e}')

    # ========== 项目与课程管理 ==========

    def create_program(self, program_name: str, program_type: str, **kwargs) -> Dict[str, Any]:
        try:
            program_id = f"ce_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            objectives = kwargs.get('objectives', [])
            objectives = json.dumps(objectives, ensure_ascii=False) if isinstance(objectives, (list, dict)) else objectives
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''INSERT INTO ce_programs (
                        program_id, program_name, program_type, degree_level, description,
                        objectives, target_audience, education_type, duration_months, total_credits,
                        total_hours, tuition_fee, learning_mode, enrollment_quota, enrolled_count,
                        start_date, end_date, status, partner_institution, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?)''',
                    (program_id, program_name, program_type, kwargs.get('degree_level'),
                          kwargs.get('description'), objectives, kwargs.get('target_audience'),
                          kwargs.get('education_type', 'adult'), kwargs.get('duration_months'),
                          kwargs.get('total_credits'), kwargs.get('total_hours'), kwargs.get('tuition_fee'),
                          kwargs.get('learning_mode'), kwargs.get('enrollment_quota'),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('status', 'recruiting'), kwargs.get('partner_institution'), now, now))
                    conn.commit()
                    logger.info(f'创建继续教育项目: {program_name} ({program_id})')
                    return {'success': True, 'program_id': program_id}
        except Exception as e:
            logger.error(f'创建继续教育项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_course(self, program_id: str, course_name: str, **kwargs) -> Dict[str, Any]:
        try:
            course_id = f"cec_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''INSERT INTO ce_courses (
                        course_id, program_id, course_name, course_code, credit, hours,
                        learning_mode, instructor_id, instructor_name, description,
                        prerequisites, assessment_method, is_required, max_students,
                        enrolled_count, status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'active', ?, ?)''',
                    (course_id, program_id, course_name, kwargs.get('course_code'),
                          kwargs.get('credit', 0), kwargs.get('hours', 0), kwargs.get('learning_mode'),
                          kwargs.get('instructor_id'), kwargs.get('instructor_name'),
                          kwargs.get('description'), kwargs.get('prerequisites'),
                          kwargs.get('assessment_method'), kwargs.get('is_required', 1),
                          kwargs.get('max_students', 50), now, now))
                    conn.commit()
                    logger.info(f'添加课程: {course_name} ({course_id})')
                    return {'success': True, 'course_id': course_id}
        except Exception as e:
            logger.error(f'添加课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_program(self, program_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM ce_programs WHERE program_id = ?', (program_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '项目不存在'}
                program = dict(row)
                try:
                    program['objectives'] = json.loads(program.get('objectives') or '[]')
                except (json.JSONDecodeError, TypeError):
                    program['objectives'] = []
                cursor.execute('SELECT * FROM ce_courses WHERE program_id = ? ORDER BY created_at DESC', (program_id,))
                program['courses'] = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'program': program}
        except Exception as e:
            logger.error(f'获取项目详情失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_programs(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM ce_programs WHERE 1=1'
                params = []
                if filters.get('program_type'):
                    query += ' AND program_type = ?'; params.append(filters['program_type'])
                if filters.get('degree_level'):
                    query += ' AND degree_level = ?'; params.append(filters['degree_level'])
                if filters.get('status'):
                    query += ' AND status = ?'; params.append(filters['status'])
                if filters.get('education_type'):
                    query += ' AND education_type = ?'; params.append(filters['education_type'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                programs = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'programs': programs, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取项目列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_courses(self, program_id: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM ce_courses WHERE 1=1'
                params = []
                if program_id:
                    query += ' AND program_id = ?'; params.append(program_id)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                courses = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'courses': courses, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取课程列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 学员管理 ==========

    def register_learner(self, name: str, **kwargs) -> Dict[str, Any]:
        try:
            learner_id = f"cel_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''INSERT INTO ce_learners (
                        learner_id, user_id, name, gender, birth_date, id_number, phone,
                        email, current_education_level, occupation, work_unit, program_id,
                        enroll_date, expected_complete_date, status, total_credits,
                        completed_credits, gpa, advisor_id, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, ?, ?, ?)''',
                    (learner_id, kwargs.get('user_id'), name, kwargs.get('gender'),
                          kwargs.get('birth_date'), kwargs.get('id_number'), kwargs.get('phone'),
                          kwargs.get('email'), kwargs.get('current_education_level'),
                          kwargs.get('occupation'), kwargs.get('work_unit'), kwargs.get('program_id'),
                          kwargs.get('enroll_date', now[:10]), kwargs.get('expected_complete_date'),
                          kwargs.get('status', 'active'), kwargs.get('advisor_id'), now, now))
                    conn.commit()
                    logger.info(f'注册学员: {name} ({learner_id})')
                    return {'success': True, 'learner_id': learner_id}
        except Exception as e:
            logger.error(f'注册学员失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_learner(self, learner_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM ce_learners WHERE learner_id = ?', (learner_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '学员不存在'}
                return {'success': True, 'learner': dict(row)}
        except Exception as e:
            logger.error(f'获取学员详情失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_learner(self, learner_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            allowed = ['name', 'gender', 'birth_date', 'id_number', 'phone', 'email',
                       'current_education_level', 'occupation', 'work_unit', 'program_id',
                       'expected_complete_date', 'status', 'total_credits',
                       'completed_credits', 'gpa', 'advisor_id']
            updates = {k: v for k, v in kwargs.items() if k in allowed}
            if not updates:
                return {'success': False, 'error': '没有可更新字段'}
            set_clause = ', '.join([f'{k} = ?' for k in updates])
            params = list(updates.values()) + [now, learner_id]
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(f'UPDATE ce_learners SET {set_clause}, updated_at = ? WHERE learner_id = ?', params)
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'更新学员: {learner_id}')
                        return {'success': True}
                    return {'success': False, 'error': '学员不存在'}
        except Exception as e:
            logger.error(f'更新学员失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_learners(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM ce_learners WHERE 1=1'
                params = []
                if filters.get('program_id'):
                    query += ' AND program_id = ?'; params.append(filters['program_id'])
                if filters.get('status'):
                    query += ' AND status = ?'; params.append(filters['status'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                learners = [dict(l) for l in cursor.fetchall()]
                return {'success': True, 'learners': learners, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取学员列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 选课与学习 ==========

    def enroll_course(self, learner_id: str, course_id: str, **kwargs) -> Dict[str, Any]:
        try:
            enrollment_id = f"cee_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_students, enrolled_count, status, program_id FROM ce_courses WHERE course_id = ?', (course_id,))
                    course = cursor.fetchone()
                    if not course:
                        return {'success': False, 'error': '课程不存在'}
                    if course[2] != 'active':
                        return {'success': False, 'error': '课程状态不允许选课'}
                    if course[0] and course[1] >= course[0]:
                        return {'success': False, 'error': '课程名额已满'}
                    cursor.execute('SELECT 1 FROM ce_enrollments WHERE learner_id = ? AND course_id = ?', (learner_id, course_id))
                    if cursor.fetchone():
                        return {'success': False, 'error': '已选该课程'}
                    cursor.execute('''INSERT INTO ce_enrollments (
                        enrollment_id, learner_id, course_id, program_id,
                        enroll_date, complete_date, attendance_rate, assignment_score,
                        exam_score, final_score, credit_earned, status,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, NULL, 0, 0, 0, 0, 0, 'enrolled', ?, ?)''',
                    (enrollment_id, learner_id, course_id,
                          kwargs.get('program_id', course[3]),
                          kwargs.get('enroll_date', now[:10]), now, now))
                    cursor.execute('UPDATE ce_courses SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE course_id = ?', (now, course_id))
                    conn.commit()
                    logger.info(f'选课成功: 学员 {learner_id} 课程 {course_id}')
                    return {'success': True, 'enrollment_id': enrollment_id}
        except Exception as e:
            logger.error(f'选课失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_assessment(self, enrollment_id: str, assessment_type: str,
                           score: float, **kwargs) -> Dict[str, Any]:
        try:
            assessment_id = f"cea_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            max_score = kwargs.get('max_score', 100)
            weight = kwargs.get('weight', 0.0)
            normalized = (score / max_score * 100) if max_score else 0
            weighted_score = normalized * weight
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT learner_id, course_id FROM ce_enrollments WHERE enrollment_id = ?', (enrollment_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '选课记录不存在'}
                    learner_id, course_id = row
                    cursor.execute('''INSERT INTO ce_assessments (
                        assessment_id, enrollment_id, learner_id, course_id,
                        assessment_type, assessment_name, score, max_score,
                        weight, weighted_score, assessed_date, assessed_by, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (assessment_id, enrollment_id, learner_id, course_id,
                          assessment_type, kwargs.get('assessment_name', assessment_type),
                          score, max_score, weight, weighted_score,
                          kwargs.get('assessed_date', now[:10]),
                          kwargs.get('assessed_by'), now))
                    # 同步更新选课汇总分数
                    if assessment_type == 'attendance':
                        cursor.execute('UPDATE ce_enrollments SET attendance_rate = ?, updated_at = ? WHERE enrollment_id = ?', (normalized, now, enrollment_id))
                    elif assessment_type == 'assignment':
                        cursor.execute('UPDATE ce_enrollments SET assignment_score = ?, updated_at = ? WHERE enrollment_id = ?', (normalized, now, enrollment_id))
                    elif assessment_type == 'exam':
                        cursor.execute('UPDATE ce_enrollments SET exam_score = ?, updated_at = ? WHERE enrollment_id = ?', (normalized, now, enrollment_id))
                    conn.commit()
                    logger.info(f'记录考核: {enrollment_id} 类型 {assessment_type} 分数 {score}')
                    return {'success': True, 'assessment_id': assessment_id, 'weighted_score': weighted_score}
        except Exception as e:
            logger.error(f'记录考核失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_course(self, enrollment_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM ce_enrollments WHERE enrollment_id = ?', (enrollment_id,))
                    enr = cursor.fetchone()
                    if not enr:
                        return {'success': False, 'error': '选课记录不存在'}
                    if dict(enr)['status'] == 'completed':
                        return {'success': False, 'error': '该课程已完成'}
                    enr = dict(enr)
                    # 最终成绩: 出勤20% + 作业30% + 考试50%
                    final_score = (enr.get('attendance_rate') or 0) * 0.2 + (enr.get('assignment_score') or 0) * 0.3 + (enr.get('exam_score') or 0) * 0.5
                    final_score = round(final_score, 2)
                    cursor.execute('SELECT credit FROM ce_courses WHERE course_id = ?', (enr['course_id'],))
                    course_row = cursor.fetchone()
                    course_credit = course_row['credit'] if course_row else 0
                    # 60 分及格授予学分
                    credit_earned = course_credit if final_score >= 60 else 0
                    cursor.execute('''UPDATE ce_enrollments SET final_score = ?, credit_earned = ?,
                        complete_date = ?, status = 'completed', updated_at = ?
                        WHERE enrollment_id = ?''',
                    (final_score, credit_earned, kwargs.get('complete_date', now[:10]), now, enrollment_id))
                    if credit_earned > 0:
                        cursor.execute('UPDATE ce_learners SET completed_credits = completed_credits + ?, total_credits = total_credits + ?, updated_at = ? WHERE learner_id = ?',
                                     (credit_earned, credit_earned, now, enr['learner_id']))
                    conn.commit()
                    logger.info(f'完成课程: {enrollment_id} 最终成绩 {final_score}')
                    return {'success': True, 'final_score': final_score,
                            'credit_earned': credit_earned, 'passed': final_score >= 60}
        except Exception as e:
            logger.error(f'完成课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_learner_progress(self, learner_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT program_id FROM ce_learners WHERE learner_id = ?', (learner_id,))
                learner_row = cursor.fetchone()
                if not learner_row:
                    return {'success': False, 'error': '学员不存在'}
                program_id = dict(learner_row)['program_id']
                cursor.execute('''SELECT COUNT(*) as total,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN status != 'completed' THEN 1 ELSE 0 END) as in_progress,
                    SUM(credit_earned) as earned,
                    AVG(CASE WHEN status = 'completed' THEN final_score END) as avg_score
                    FROM ce_enrollments WHERE learner_id = ?''', (learner_id,))
                row = dict(cursor.fetchone())
                total = row['total'] or 0
                completed = row['completed'] or 0
                in_progress = row['in_progress'] or 0
                earned = row['earned'] or 0
                gpa = round(row['avg_score'], 2) if row['avg_score'] else 0
                completion_rate = round(completed / total, 4) if total else 0
                cursor.execute('''SELECT COALESCE(SUM(c.credit), 0) as total_credits
                    FROM ce_enrollments e JOIN ce_courses c ON e.course_id = c.course_id
                    WHERE e.learner_id = ?''', (learner_id,))
                total_credits = dict(cursor.fetchone())['total_credits'] or 0
                progress_id = f"cep_{uuid.uuid4().hex[:12]}"
                now = datetime.now().isoformat()
                cursor.execute('SELECT progress_id FROM learner_progress WHERE learner_id = ?', (learner_id,))
                existing = cursor.fetchone()
                if existing:
                    cursor.execute('''UPDATE learner_progress SET total_courses = ?, completed_courses = ?,
                        in_progress_courses = ?, total_credits = ?, earned_credits = ?,
                        gpa = ?, completion_rate = ?, last_activity = ?, updated_at = ?
                        WHERE learner_id = ?''',
                    (total, completed, in_progress, total_credits, earned,
                          gpa, completion_rate, now, now, learner_id))
                else:
                    cursor.execute('''INSERT INTO learner_progress (
                        progress_id, learner_id, program_id, total_courses, completed_courses,
                        in_progress_courses, total_credits, earned_credits, gpa, completion_rate,
                        last_activity, status, updated_at, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)''',
                    (progress_id, learner_id, program_id, total, completed, in_progress,
                          total_credits, earned, gpa, completion_rate, now, now, now))
                conn.commit()
                return {'success': True, 'progress': {
                    'learner_id': learner_id, 'program_id': program_id,
                    'total_courses': total, 'completed_courses': completed,
                    'in_progress_courses': in_progress, 'total_credits': total_credits,
                    'earned_credits': earned, 'gpa': gpa, 'completion_rate': completion_rate
                }}
        except Exception as e:
            logger.error(f'获取学员进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_enrollments(self, learner_id: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM ce_enrollments WHERE 1=1'
                params = []
                if learner_id:
                    query += ' AND learner_id = ?'; params.append(learner_id)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                enrollments = [dict(e) for e in cursor.fetchall()]
                return {'success': True, 'enrollments': enrollments, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取选课列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 证书管理 ==========

    def issue_certificate(self, learner_id: str, program_id: str,
                           certificate_type: str, **kwargs) -> Dict[str, Any]:
        try:
            certificate_id = f"cecert_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            certificate_number = f"CEC{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
            verification_code = uuid.uuid4().hex[:8].upper()
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT name, gpa, total_credits FROM ce_learners WHERE learner_id = ?', (learner_id,))
                    learner_row = cursor.fetchone()
                    if not learner_row:
                        return {'success': False, 'error': '学员不存在'}
                    learner = dict(learner_row)
                    program_name = kwargs.get('program_name')
                    degree_level = kwargs.get('degree_level')
                    if program_id:
                        cursor.execute('SELECT program_name, degree_level FROM ce_programs WHERE program_id = ?', (program_id,))
                        prog = cursor.fetchone()
                        if prog:
                            program_name = program_name or dict(prog)['program_name']
                            degree_level = degree_level or dict(prog)['degree_level']
                    cursor.execute('''INSERT INTO ce_certificates (
                        certificate_id, learner_id, learner_name, program_id, program_name,
                        certificate_type, certificate_number, issue_date, expiry_date, credits,
                        gpa, degree_level, issued_by, verification_code, status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'issued', ?, ?)''',
                    (certificate_id, learner_id, learner['name'], program_id, program_name,
                          certificate_type, certificate_number, kwargs.get('issue_date', now[:10]),
                          kwargs.get('expiry_date'), kwargs.get('credits', learner['total_credits']),
                          kwargs.get('gpa', learner['gpa']), degree_level,
                          kwargs.get('issued_by'), verification_code, now, now))
                    conn.commit()
                    logger.info(f'发放证书: {certificate_number} 学员 {learner_id}')
                    return {'success': True, 'certificate_id': certificate_id,
                            'certificate_number': certificate_number,
                            'verification_code': verification_code}
        except Exception as e:
            logger.error(f'发放证书失败: {e}')
            return {'success': False, 'error': str(e)}

    def verify_certificate(self, certificate_number: str, verification_code: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM ce_certificates WHERE certificate_number = ? AND verification_code = ?',
                              (certificate_number, verification_code))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'valid': False, 'error': '证书编号或验证码错误'}
                cert = dict(row)
                valid = cert['status'] == 'issued'
                return {'success': True, 'valid': valid, 'certificate': cert}
        except Exception as e:
            logger.error(f'验证证书失败: {e}')
            return {'success': False, 'error': str(e)}

    def revoke_certificate(self, certificate_id: str, reason: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE ce_certificates SET status = ?, updated_at = ? WHERE certificate_id = ? AND status = ?',
                                 ('revoked', now, certificate_id, 'issued'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'撤销证书: {certificate_id} 原因: {reason}')
                        return {'success': True, 'reason': reason}
                    return {'success': False, 'error': '证书不存在或状态不允许撤销'}
        except Exception as e:
            logger.error(f'撤销证书失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_certificates(self, learner_id: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM ce_certificates WHERE 1=1'
                params = []
                if learner_id:
                    query += ' AND learner_id = ?'; params.append(learner_id)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                certificates = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'certificates': certificates, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取证书列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 先前学习认证 ==========

    def apply_rpl(self, learner_id: str, rpl_type: str, **kwargs) -> Dict[str, Any]:
        try:
            rpl_id = f"rpl_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            evidence = kwargs.get('evidence', [])
            evidence = json.dumps(evidence, ensure_ascii=False) if isinstance(evidence, (list, dict)) else evidence
            config = RPL_TYPES.get(rpl_type, {})
            requested = kwargs.get('requested_credits', config.get('max_credits', 0))
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT name FROM ce_learners WHERE learner_id = ?', (learner_id,))
                    row = cursor.fetchone()
                    learner_name = dict(row)['name'] if row else kwargs.get('learner_name')
                    cursor.execute('''INSERT INTO rpl_applications (
                        rpl_id, learner_id, learner_name, rpl_type, learning_description,
                        evidence, requested_credits, assessed_credits, assessor_id,
                        assessor_name, assessment_date, assessment_result, status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, NULL, NULL, NULL, NULL, 'pending', ?, ?)''',
                    (rpl_id, learner_id, learner_name, rpl_type,
                          kwargs.get('learning_description'), evidence, requested, now, now))
                    conn.commit()
                    logger.info(f'提交先前学习认证申请: {rpl_id} 学员 {learner_id}')
                    return {'success': True, 'rpl_id': rpl_id}
        except Exception as e:
            logger.error(f'申请先前学习认证失败: {e}')
            return {'success': False, 'error': str(e)}

    def assess_rpl(self, rpl_id: str, assessed_credits: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            result = kwargs.get('assessment_result', 'approved')
            status = 'approved' if result == 'approved' else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT learner_id, status FROM rpl_applications WHERE rpl_id = ?', (rpl_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '认证申请不存在'}
                    rpl = dict(row)
                    if rpl['status'] != 'pending':
                        return {'success': False, 'error': '该申请已处理'}
                    cursor.execute('''UPDATE rpl_applications SET assessed_credits = ?, assessor_id = ?,
                        assessor_name = ?, assessment_date = ?, assessment_result = ?,
                        status = ?, updated_at = ? WHERE rpl_id = ?''',
                    (assessed_credits, kwargs.get('assessor_id'),
                          kwargs.get('assessor_name'), kwargs.get('assessment_date', now[:10]),
                          result, status, now, rpl_id))
                    # 通过后自动转换学分到学员档案
                    if status == 'approved' and assessed_credits > 0:
                        cursor.execute('UPDATE ce_learners SET total_credits = total_credits + ?, completed_credits = completed_credits + ?, updated_at = ? WHERE learner_id = ?',
                                     (assessed_credits, assessed_credits, now, rpl['learner_id']))
                        cursor.execute('SELECT portfolio_id FROM lifelong_portfolios WHERE learner_id = ?', (rpl['learner_id'],))
                        pf = cursor.fetchone()
                        if pf:
                            cursor.execute('UPDATE lifelong_portfolios SET total_credits = total_credits + ?, updated_at = ? WHERE portfolio_id = ?',
                                         (assessed_credits, now, dict(pf)['portfolio_id']))
                    conn.commit()
                    logger.info(f'评估先前学习认证: {rpl_id} 结果 {status} 学分 {assessed_credits}')
                    return {'success': True, 'status': status, 'assessed_credits': assessed_credits}
        except Exception as e:
            logger.error(f'评估先前学习认证失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_rpl_applications(self, learner_id: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM rpl_applications WHERE 1=1'
                params = []
                if learner_id:
                    query += ' AND learner_id = ?'; params.append(learner_id)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                applications = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'applications': applications, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取认证申请列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 终身学习档案 ==========

    def create_lifelong_portfolio(self, learner_id: str, **kwargs) -> Dict[str, Any]:
        try:
            portfolio_id = f"lp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            skill_tags = kwargs.get('skill_tags', [])
            skill_tags = json.dumps(skill_tags, ensure_ascii=False) if isinstance(skill_tags, (list, dict)) else skill_tags
            learning_history = kwargs.get('learning_history', [])
            learning_history = json.dumps(learning_history, ensure_ascii=False) if isinstance(learning_history, (list, dict)) else learning_history
            badges = kwargs.get('badges', [])
            badges = json.dumps(badges, ensure_ascii=False) if isinstance(badges, (list, dict)) else badges
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT name FROM ce_learners WHERE learner_id = ?', (learner_id,))
                    row = cursor.fetchone()
                    learner_name = dict(row)['name'] if row else kwargs.get('learner_name')
                    cursor.execute('SELECT portfolio_id FROM lifelong_portfolios WHERE learner_id = ?', (learner_id,))
                    if cursor.fetchone():
                        return {'success': False, 'error': '该学员已存在终身学习档案'}
                    total_hours = kwargs.get('total_learning_hours', 0)
                    total_courses = kwargs.get('total_courses', 0)
                    cursor.execute('''INSERT INTO lifelong_portfolios (
                        portfolio_id, learner_id, learner_name, total_learning_hours,
                        total_courses, total_credits, total_certificates, skill_tags,
                        learning_history, level, badges, last_activity, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, 0, 0, ?, ?, 'bronze', ?, ?, ?, ?)''',
                    (portfolio_id, learner_id, learner_name, total_hours, total_courses,
                          skill_tags, learning_history, badges, kwargs.get('last_activity', now), now, now))
                    self._update_learning_level(cursor, portfolio_id, total_hours, total_courses)
                    conn.commit()
                    logger.info(f'创建终身学习档案: {portfolio_id} 学员 {learner_id}')
                    return {'success': True, 'portfolio_id': portfolio_id}
        except Exception as e:
            logger.error(f'创建终身学习档案失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_lifelong_portfolio(self, learner_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM lifelong_portfolios WHERE learner_id = ?', (learner_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '档案不存在'}
                    portfolio = dict(row)
                    portfolio_id = portfolio['portfolio_id']
                    total_hours = kwargs.get('total_learning_hours', portfolio['total_learning_hours'] or 0)
                    total_courses = kwargs.get('total_courses', portfolio['total_courses'] or 0)
                    total_credits = kwargs.get('total_credits', portfolio['total_credits'] or 0)
                    total_certificates = kwargs.get('total_certificates', portfolio['total_certificates'] or 0)
                    skill_tags = kwargs.get('skill_tags')
                    skill_tags = json.dumps(skill_tags, ensure_ascii=False) if isinstance(skill_tags, (list, dict)) else skill_tags
                    learning_history = kwargs.get('learning_history')
                    learning_history = json.dumps(learning_history, ensure_ascii=False) if isinstance(learning_history, (list, dict)) else learning_history
                    badges = kwargs.get('badges')
                    badges = json.dumps(badges, ensure_ascii=False) if isinstance(badges, (list, dict)) else badges
                    cursor.execute('''UPDATE lifelong_portfolios SET total_learning_hours = ?,
                        total_courses = ?, total_credits = ?, total_certificates = ?,
                        skill_tags = COALESCE(?, skill_tags),
                        learning_history = COALESCE(?, learning_history),
                        badges = COALESCE(?, badges), last_activity = ?, updated_at = ?
                        WHERE portfolio_id = ?''', (total_hours, total_courses, total_credits, total_certificates,
                          skill_tags, learning_history, badges,
                          kwargs.get('last_activity', now), now, portfolio_id))
                    self._update_learning_level(cursor, portfolio_id, total_hours, total_courses)
                    conn.commit()
                    logger.info(f'更新终身学习档案: 学员 {learner_id}')
                    return {'success': True, 'portfolio_id': portfolio_id}
        except Exception as e:
            logger.error(f'更新终身学习档案失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_lifelong_portfolio(self, learner_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM lifelong_portfolios WHERE learner_id = ?', (learner_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '档案不存在'}
                portfolio = dict(row)
                for field in ['skill_tags', 'learning_history', 'badges']:
                    try:
                        portfolio[field] = json.loads(portfolio.get(field) or '[]')
                    except (json.JSONDecodeError, TypeError):
                        portfolio[field] = []
                level_key = portfolio.get('level', 'bronze')
                portfolio['level_name'] = LIFELONG_LEARNING_LEVELS.get(level_key, {}).get('name')
                portfolio['badge'] = LIFELONG_LEARNING_LEVELS.get(level_key, {}).get('badge')
                return {'success': True, 'portfolio': portfolio}
        except Exception as e:
            logger.error(f'获取终身学习档案失败: {e}')
            return {'success': False, 'error': str(e)}

    def _update_learning_level(self, cursor, portfolio_id: str, total_hours: float, total_courses: int) -> str:
        """根据学习时长和课程数自动更新等级"""
        level = 'bronze'
        for key, cfg in LIFELONG_LEARNING_LEVELS.items():
            if total_hours >= cfg['min_hours'] and total_courses >= cfg['min_courses']:
                level = key
        cursor.execute('UPDATE lifelong_portfolios SET level = ?, updated_at = ? WHERE portfolio_id = ?',
                       (level, datetime.now().isoformat(), portfolio_id))
        return level

    # ========== 学习计划 ==========

    def create_learning_plan(self, learner_id: str, program_id: str, **kwargs) -> Dict[str, Any]:
        try:
            plan_id = f"lpn_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            planned_courses = kwargs.get('planned_courses', [])
            planned_courses = json.dumps(planned_courses, ensure_ascii=False) if isinstance(planned_courses, (list, dict)) else planned_courses
            completed_courses = kwargs.get('completed_courses', [])
            completed_courses = json.dumps(completed_courses, ensure_ascii=False) if isinstance(completed_courses, (list, dict)) else completed_courses
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT name FROM ce_learners WHERE learner_id = ?', (learner_id,))
                    row = cursor.fetchone()
                    learner_name = dict(row)['name'] if row else kwargs.get('learner_name')
                    cursor.execute('''INSERT INTO learning_plans (
                        plan_id, learner_id, learner_name, program_id, plan_name, target_credits,
                        target_complete_date, planned_courses, completed_courses, progress_percent,
                        status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'active', ?, ?)''',
                    (plan_id, learner_id, learner_name, program_id, kwargs.get('plan_name'),
                          kwargs.get('target_credits'), kwargs.get('target_complete_date'),
                          planned_courses, completed_courses, now, now))
                    conn.commit()
                    logger.info(f'创建学习计划: {plan_id} 学员 {learner_id}')
                    return {'success': True, 'plan_id': plan_id}
        except Exception as e:
            logger.error(f'创建学习计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_learning_plan(self, plan_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM learning_plans WHERE plan_id = ?', (plan_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '计划不存在'}
                    plan = dict(row)
                    planned = kwargs.get('planned_courses')
                    planned = json.dumps(planned, ensure_ascii=False) if isinstance(planned, (list, dict)) else planned
                    completed = kwargs.get('completed_courses')
                    completed = json.dumps(completed, ensure_ascii=False) if isinstance(completed, (list, dict)) else completed
                    progress = kwargs.get('progress_percent', plan['progress_percent'] or 0)
                    status = kwargs.get('status', plan['status'])
                    cursor.execute('''UPDATE learning_plans SET plan_name = COALESCE(?, plan_name),
                        target_credits = COALESCE(?, target_credits),
                        target_complete_date = COALESCE(?, target_complete_date),
                        planned_courses = COALESCE(?, planned_courses),
                        completed_courses = COALESCE(?, completed_courses),
                        progress_percent = ?, status = ?, updated_at = ? WHERE plan_id = ?''',
                    (kwargs.get('plan_name'), kwargs.get('target_credits'),
                          kwargs.get('target_complete_date'), planned, completed,
                          progress, status, now, plan_id))
                    conn.commit()
                    logger.info(f'更新学习计划: {plan_id}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'更新学习计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_learning_plans(self, learner_id: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM learning_plans WHERE 1=1'
                params = []
                if learner_id:
                    query += ' AND learner_id = ?'; params.append(learner_id)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                plans = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'plans': plans, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取学习计划列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 机构管理 ==========

    def register_institution(self, institution_name: str, institution_type: str, **kwargs) -> Dict[str, Any]:
        try:
            institution_id = f"inst_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            provided_programs = kwargs.get('provided_programs', [])
            provided_programs = json.dumps(provided_programs, ensure_ascii=False) if isinstance(provided_programs, (list, dict)) else provided_programs
            config = INSTITUTION_TYPES.get(institution_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''INSERT INTO ce_institutions (
                        institution_id, institution_name, institution_type, accreditation_number,
                        legal_person, address, contact_phone, contact_email, cooperation_type,
                        provided_programs, rating, is_approved, cooperation_start,
                        cooperation_end, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?)''',
                    (institution_id, institution_name, institution_type, kwargs.get('accreditation_number'),
                          kwargs.get('legal_person'), kwargs.get('address'), kwargs.get('contact_phone'),
                          kwargs.get('contact_email'), kwargs.get('cooperation_type'), provided_programs,
                          0 if config.get('accreditation_required') else 1,
                          kwargs.get('cooperation_start', now[:10]), kwargs.get('cooperation_end'), now, now))
                    conn.commit()
                    logger.info(f'注册机构: {institution_name} ({institution_id})')
                    return {'success': True, 'institution_id': institution_id}
        except Exception as e:
            logger.error(f'注册机构失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_institution(self, institution_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            is_approved = 1 if kwargs.get('approved', True) else 0
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE ce_institutions SET is_approved = ?, rating = COALESCE(?, rating), updated_at = ? WHERE institution_id = ?',
                                 (is_approved, kwargs.get('rating'), now, institution_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'审核机构: {institution_id} 通过 {is_approved}')
                        return {'success': True, 'is_approved': is_approved}
                    return {'success': False, 'error': '机构不存在'}
        except Exception as e:
            logger.error(f'审核机构失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_institutions(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM ce_institutions WHERE 1=1'
                params = []
                if filters.get('institution_type'):
                    query += ' AND institution_type = ?'; params.append(filters['institution_type'])
                if filters.get('is_approved') is not None:
                    query += ' AND is_approved = ?'; params.append(filters['is_approved'])
                if filters.get('cooperation_type'):
                    query += ' AND cooperation_type = ?'; params.append(filters['cooperation_type'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                institutions = [dict(i) for i in cursor.fetchall()]
                return {'success': True, 'institutions': institutions, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取机构列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                edu_cond = ''
                params = []
                if education_type:
                    edu_cond = ' AND education_type = ?'
                    params = [education_type]
                stats = {'education_type': education_type}
                # 项目数与类型分布
                stats['total_programs'] = cursor.execute(f'SELECT COUNT(*) FROM ce_programs WHERE 1=1{edu_cond}', params).fetchone()[0]
                stats['program_type_distribution'] = {r[0]: r[1] for r in cursor.execute(f'SELECT program_type, COUNT(*) FROM ce_programs WHERE 1=1{edu_cond} GROUP BY program_type', params).fetchall()}
                # 课程数
                stats['total_courses'] = cursor.execute('SELECT COUNT(*) FROM ce_courses').fetchone()[0]
                stats['active_courses'] = cursor.execute("SELECT COUNT(*) FROM ce_courses WHERE status = 'active'").fetchone()[0]
                # 学员数与状态分布
                stats['total_learners'] = cursor.execute('SELECT COUNT(*) FROM ce_learners').fetchone()[0]
                stats['learner_status_distribution'] = {r[0]: r[1] for r in cursor.execute('SELECT status, COUNT(*) FROM ce_learners GROUP BY status').fetchall()}
                # 课程完成率
                total_enrollments = cursor.execute('SELECT COUNT(*) FROM ce_enrollments').fetchone()[0]
                completed_enrollments = cursor.execute("SELECT COUNT(*) FROM ce_enrollments WHERE status = 'completed'").fetchone()[0]
                stats['course_completion_rate'] = round(completed_enrollments / total_enrollments, 4) if total_enrollments else 0
                stats['total_enrollments'] = total_enrollments
                # 证书数与类型分布
                stats['total_certificates'] = cursor.execute('SELECT COUNT(*) FROM ce_certificates').fetchone()[0]
                stats['certificate_type_distribution'] = {r[0]: r[1] for r in cursor.execute('SELECT certificate_type, COUNT(*) FROM ce_certificates GROUP BY certificate_type').fetchall()}
                # RPL 认证统计
                stats['total_rpl_applications'] = cursor.execute('SELECT COUNT(*) FROM rpl_applications').fetchone()[0]
                stats['rpl_status_distribution'] = {r[0]: r[1] for r in cursor.execute('SELECT status, COUNT(*) FROM rpl_applications GROUP BY status').fetchall()}
                stats['rpl_total_credits'] = cursor.execute("SELECT COALESCE(SUM(assessed_credits), 0) FROM rpl_applications WHERE status = 'approved'").fetchone()[0]
                # 机构数
                stats['total_institutions'] = cursor.execute('SELECT COUNT(*) FROM ce_institutions').fetchone()[0]
                stats['approved_institutions'] = cursor.execute('SELECT COUNT(*) FROM ce_institutions WHERE is_approved = 1').fetchone()[0]
                stats['institution_type_distribution'] = {r[0]: r[1] for r in cursor.execute('SELECT institution_type, COUNT(*) FROM ce_institutions GROUP BY institution_type').fetchall()}
                # 终身学习档案与等级分布
                stats['total_portfolios'] = cursor.execute('SELECT COUNT(*) FROM lifelong_portfolios').fetchone()[0]
                stats['lifelong_level_distribution'] = {r[0]: r[1] for r in cursor.execute('SELECT level, COUNT(*) FROM lifelong_portfolios GROUP BY level').fetchall()}
                # 学习计划数
                stats['total_learning_plans'] = cursor.execute('SELECT COUNT(*) FROM learning_plans').fetchone()[0]
                stats['active_learning_plans'] = cursor.execute("SELECT COUNT(*) FROM learning_plans WHERE status = 'active'").fetchone()[0]
                return {'success': True, 'statistics': stats}
        except Exception as e:
            logger.error(f'获取统计信息失败: {e}')
            return {'success': False, 'error': str(e)}


if __name__ == '__main__':
    service = ContinuingEducationService()
    print('继续教育与终身学习服务初始化完成')
    stats = service.get_statistics()
    print(f'统计: {stats}')
