#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育全球化服务 (v15.23.0)
=================================
提供国际交流合作、跨境教育服务、国际课程开发、国际认证评估、
国际人才流动、国际教育标准、全球教育网络、国际教育政策等综合管理服务。

核心能力：
1. 国际交流合作 - 学生交换、教师交换、学术交流、科研合作
2. 跨境教育服务 - 留学、中外合作办学、在线教育、学分互认
3. 国际课程开发 - 国际课程、双语课程、AP/A-Level/IB课程
4. 国际认证评估 - 国际认证、区域认证、专业认证、学位认证
5. 国际人才流动 - 人才引进、人才输出、国际招聘、海外派遣
6. 国际教育标准 - 学历标准、学分标准、质量标准、评估标准
7. 全球教育网络 - 国际联盟、学术网络、跨国合作、区域组织
8. 国际教育政策 - 留学政策、签证政策、认证政策、质量保障

支持教育类型：成人教育 / K12教育
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_globalization_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationGlobalization')


# ========== 教育全球化配置 ==========

EXCHANGE_TYPES = {
    'student_exchange': {'name': '学生交换', 'duration': ['1学期', '1学年', '短期']},
    'teacher_exchange': {'name': '教师交换', 'duration': ['1学期', '1学年', '短期访学']},
    'academic_exchange': {'name': '学术交流', 'duration': ['短期', '中长期']},
    'research_collab': {'name': '科研合作', 'duration': ['项目周期']},
    'joint_training': {'name': '联合培养', 'duration': ['2+2', '3+1', '1+1']},
    'short_program': {'name': '短期项目', 'duration': ['1-4周']},
    'summer_school': {'name': '暑期学校', 'duration': ['暑期']},
    'international_conference': {'name': '国际会议', 'duration': ['短期']}
}

EDUCATION_MODES = {
    'study_abroad': {'name': '留学', 'degree_types': ['本科', '硕士', '博士']},
    'sino_foreign': {'name': '中外合作办学', 'degree_types': ['本科', '硕士']},
    'online_education': {'name': '在线教育', 'degree_types': ['证书', '学位']},
    'credit_recognition': {'name': '学分互认', 'degree_types': ['本科', '硕士']},
    'degree_joint': {'name': '学位互授', 'degree_types': ['本科', '硕士', '博士']},
    'dual_degree': {'name': '双联学位', 'degree_types': ['本科', '硕士']},
    'crossborder': {'name': '跨境教育', 'degree_types': ['本科', '硕士']},
    'international_course': {'name': '国际课程', 'degree_types': ['证书', '学分']}
}

CURRICULUM_TYPES = {
    'international': {'name': '国际课程', 'provider': ['海外院校', '国际组织']},
    'bilingual': {'name': '双语课程', 'provider': ['国内院校', '中外合作机构']},
    'globalized': {'name': '国际化课程', 'provider': ['国内院校']},
    'certificate': {'name': '国际证书课程', 'provider': ['国际认证机构']},
    'ap': {'name': 'AP课程', 'provider': ['College Board']},
    'a_level': {'name': 'A-Level课程', 'provider': ['CIE', 'Edexcel']},
    'ib': {'name': 'IB课程', 'provider': ['IBO']},
    'foundation': {'name': '国际预科', 'provider': ['海外院校', '国内预科中心']}
}

CERTIFICATION_TYPES = {
    'international': {'name': '国际认证', 'scope': ['全球']},
    'regional': {'name': '区域认证', 'scope': ['区域']},
    'professional': {'name': '专业认证', 'scope': ['专业领域']},
    'degree': {'name': '学位认证', 'scope': ['学历学位']},
    'credit': {'name': '学分认证', 'scope': ['学分']},
    'quality': {'name': '质量认证', 'scope': ['机构质量']},
    'institution': {'name': '机构认证', 'scope': ['教育机构']},
    'course': {'name': '课程认证', 'scope': ['课程']}
}

TALENT_FLOW = {
    'talent_intro': {'name': '人才引进', 'direction': '引入'},
    'talent_export': {'name': '人才输出', 'direction': '输出'},
    'international_recruitment': {'name': '国际招聘', 'direction': '引入'},
    'overseas_assignment': {'name': '海外派遣', 'direction': '输出'},
    'return_service': {'name': '归国服务', 'direction': '引入'},
    'international_internship': {'name': '国际实习', 'direction': '双向'},
    'overseas_training': {'name': '海外研修', 'direction': '输出'},
    'international_cooperation': {'name': '国际合作', 'direction': '双向'}
}

STANDARD_TYPES = {
    'degree': {'name': '学历标准', 'applicable': ['学历教育']},
    'credit': {'name': '学分标准', 'applicable': ['学分体系']},
    'quality': {'name': '质量标准', 'applicable': ['教育质量']},
    'curriculum': {'name': '课程标准', 'applicable': ['课程设计']},
    'assessment': {'name': '评估标准', 'applicable': ['教学评估']},
    'certification': {'name': '认证标准', 'applicable': ['认证流程']},
    'qualification': {'name': '资格标准', 'applicable': ['职业资格']},
    'language': {'name': '语言标准', 'applicable': ['语言能力']}
}

NETWORK_TYPES = {
    'international_alliance': {'name': '国际教育联盟', 'members': ['高校', '教育机构']},
    'academic_network': {'name': '学术网络', 'members': ['学者', '研究机构']},
    'crossborder_cooperation': {'name': '跨国合作网络', 'members': ['院校', '企业']},
    'regional_organization': {'name': '区域教育组织', 'members': ['成员国']},
    'international_organization': {'name': '国际组织', 'members': ['会员国', '机构']},
    'industry_alliance': {'name': '行业联盟', 'members': ['行业企业', '院校']},
    'school_enterprise': {'name': '校企网络', 'members': ['学校', '企业']},
    'alumni_network': {'name': '校友网络', 'members': ['校友']}
}

POLICY_AREAS = {
    'study_abroad': {'name': '留学政策', 'impact': ['学生']},
    'visa': {'name': '签证政策', 'impact': ['学生', '教师']},
    'certification': {'name': '认证政策', 'impact': ['机构', '学生']},
    'quality_assurance': {'name': '质量保障政策', 'impact': ['机构']},
    'cooperation': {'name': '合作政策', 'impact': ['机构']},
    'talent': {'name': '人才政策', 'impact': ['教师', '研究人员']},
    'funding': {'name': '资助政策', 'impact': ['学生', '项目']},
    'regulation': {'name': '监管政策', 'impact': ['机构']}
}


class EducationGlobalizationService:
    """教育全球化服务"""

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
                    CREATE TABLE IF NOT EXISTS international_exchange (
                        exchange_id TEXT PRIMARY KEY,
                        exchange_type TEXT NOT NULL,
                        program_name TEXT NOT NULL,
                        partner_institution TEXT,
                        country TEXT,
                        education_type TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        duration TEXT,
                        max_participants INTEGER DEFAULT 50,
                        participant_count INTEGER DEFAULT 0,
                        description TEXT,
                        status TEXT DEFAULT 'open',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS exchange_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        exchange_id TEXT NOT NULL,
                        participant_id INTEGER NOT NULL,
                        participant_name TEXT,
                        participant_type TEXT,
                        education_type TEXT,
                        application_date TEXT,
                        approval_status TEXT DEFAULT 'pending',
                        departure_date TEXT,
                        return_date TEXT,
                        evaluation TEXT,
                        UNIQUE(exchange_id, participant_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS crossborder_education (
                        program_id TEXT PRIMARY KEY,
                        education_mode TEXT NOT NULL,
                        program_name TEXT NOT NULL,
                        host_institution TEXT,
                        partner_institution TEXT,
                        country TEXT,
                        education_type TEXT,
                        degree_type TEXT,
                        duration TEXT,
                        tuition_fee REAL,
                        application_deadline TEXT,
                        intake_season TEXT,
                        max_students INTEGER DEFAULT 100,
                        enrolled_count INTEGER DEFAULT 0,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS education_programs (
                        program_id TEXT PRIMARY KEY,
                        program_name TEXT NOT NULL,
                        education_mode TEXT,
                        provider TEXT,
                        country TEXT,
                        education_type TEXT,
                        level TEXT,
                        duration TEXT,
                        credits INTEGER,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS international_curriculum (
                        curriculum_id TEXT PRIMARY KEY,
                        curriculum_type TEXT NOT NULL,
                        course_name TEXT NOT NULL,
                        provider TEXT,
                        education_type TEXT,
                        level TEXT,
                        credits INTEGER DEFAULT 3,
                        duration_hours INTEGER DEFAULT 48,
                        language TEXT,
                        prerequisites TEXT,
                        syllabus TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS curriculum_versions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        curriculum_id TEXT NOT NULL,
                        version TEXT NOT NULL,
                        update_date TEXT,
                        changelog TEXT,
                        status TEXT DEFAULT 'current'
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS international_certification (
                        cert_id TEXT PRIMARY KEY,
                        certification_type TEXT NOT NULL,
                        cert_name TEXT NOT NULL,
                        issuing_body TEXT,
                        education_type TEXT,
                        valid_period TEXT,
                        application_fee REAL,
                        exam_date TEXT,
                        registration_deadline TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'open',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS certification_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cert_id TEXT NOT NULL,
                        applicant_id INTEGER NOT NULL,
                        applicant_name TEXT,
                        education_type TEXT,
                        application_date TEXT,
                        exam_score REAL,
                        result TEXT,
                        certificate_no TEXT,
                        certificate_url TEXT,
                        issue_date TEXT,
                        expiry_date TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS talent_flow (
                        flow_id TEXT PRIMARY KEY,
                        flow_type TEXT NOT NULL,
                        program_name TEXT NOT NULL,
                        country TEXT,
                        education_type TEXT,
                        direction TEXT,
                        max_talents INTEGER DEFAULT 20,
                        talent_count INTEGER DEFAULT 0,
                        description TEXT,
                        status TEXT DEFAULT 'open',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS flow_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        flow_id TEXT NOT NULL,
                        talent_id INTEGER NOT NULL,
                        talent_name TEXT,
                        talent_type TEXT,
                        education_type TEXT,
                        application_date TEXT,
                        approval_status TEXT DEFAULT 'pending',
                        start_date TEXT,
                        end_date TEXT,
                        evaluation TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS education_standards (
                        standard_id TEXT PRIMARY KEY,
                        standard_type TEXT NOT NULL,
                        standard_name TEXT NOT NULL,
                        education_type TEXT,
                        applicable_scope TEXT,
                        version TEXT DEFAULT '1.0',
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS standard_documents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        standard_id TEXT NOT NULL,
                        document_name TEXT NOT NULL,
                        document_url TEXT,
                        upload_date TEXT,
                        version TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS global_network (
                        network_id TEXT PRIMARY KEY,
                        network_type TEXT NOT NULL,
                        network_name TEXT NOT NULL,
                        education_type TEXT,
                        headquarters TEXT,
                        member_count INTEGER DEFAULT 0,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS network_members (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        network_id TEXT NOT NULL,
                        member_id INTEGER NOT NULL,
                        member_name TEXT,
                        member_type TEXT,
                        join_date TEXT,
                        status TEXT DEFAULT 'active',
                        UNIQUE(network_id, member_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS education_policy (
                        policy_id TEXT PRIMARY KEY,
                        policy_area TEXT NOT NULL,
                        policy_name TEXT NOT NULL,
                        issuing_authority TEXT,
                        education_type TEXT,
                        effective_date TEXT,
                        expiry_date TEXT,
                        policy_text TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS policy_documents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        policy_id TEXT NOT NULL,
                        document_name TEXT NOT NULL,
                        document_url TEXT,
                        upload_date TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS global_alerts (
                        alert_id TEXT PRIMARY KEY,
                        alert_type TEXT NOT NULL,
                        country TEXT,
                        education_type TEXT,
                        title TEXT NOT NULL,
                        content TEXT,
                        severity TEXT DEFAULT 'medium',
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alert_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        alert_id TEXT NOT NULL,
                        action TEXT,
                        action_date TEXT,
                        operator TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS global_stats (
                        stat_id TEXT PRIMARY KEY,
                        stat_name TEXT NOT NULL,
                        education_type TEXT,
                        country TEXT,
                        stat_value REAL,
                        stat_date TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS stat_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        stat_id TEXT NOT NULL,
                        data_key TEXT NOT NULL,
                        data_value TEXT,
                        record_date TEXT
                    )
                ''')
                conn.commit()
                logger.info('教育全球化服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 国际交流合作 ==========

    def create_exchange_program(self, exchange_type: str, program_name: str,
                                **kwargs) -> Dict[str, Any]:
        try:
            exchange_id = f"exc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = EXCHANGE_TYPES.get(exchange_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO international_exchange (
                            exchange_id, exchange_type, program_name,
                            partner_institution, country, education_type,
                            start_date, end_date, duration, max_participants,
                            participant_count, description, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 'open', ?, ?)
                    ''', (exchange_id, exchange_type, program_name,
                          kwargs.get('partner_institution'),
                          kwargs.get('country'), kwargs.get('education_type'),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('duration', config.get('duration', [''])[0]),
                          kwargs.get('max_participants', 50),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建国际交流项目: {program_name} ({exchange_id})')
                    return {'success': True, 'exchange_id': exchange_id}
        except Exception as e:
            logger.error(f'创建国际交流项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def apply_exchange(self, exchange_id: str, participant_id: int,
                       participant_name: str, participant_type: str,
                       **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, participant_count, status FROM international_exchange WHERE exchange_id = ?', (exchange_id,))
                    exchange = cursor.fetchone()
                    if not exchange:
                        return {'success': False, 'error': '交流项目不存在'}
                    if exchange[2] != 'open':
                        return {'success': False, 'error': '交流项目状态不允许报名'}
                    if exchange[0] and exchange[1] >= exchange[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('INSERT OR IGNORE INTO exchange_records (exchange_id, participant_id, participant_name, participant_type, education_type, application_date, approval_status) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                 (exchange_id, participant_id, participant_name, participant_type, kwargs.get('education_type'), now[:10], 'pending'))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE international_exchange SET participant_count = participant_count + 1, updated_at = ? WHERE exchange_id = ?', (now, exchange_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已申请该交流项目'}
        except Exception as e:
            logger.error(f'申请交流项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_exchange_application(self, exchange_id: str, participant_id: int,
                                     approved: bool) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE exchange_records SET approval_status = ? WHERE exchange_id = ? AND participant_id = ? AND approval_status = ?',
                                 (status, exchange_id, participant_id, 'pending'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '申请状态不允许审核'}
        except Exception as e:
            logger.error(f'审核交流申请失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_exchange_evaluation(self, exchange_id: str, participant_id: int,
                                    evaluation: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE exchange_records SET evaluation = ? WHERE exchange_id = ? AND participant_id = ?',
                                 (evaluation, exchange_id, participant_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '交流记录不存在'}
        except Exception as e:
            logger.error(f'记录交流评价失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 跨境教育服务 ==========

    def create_crossborder_program(self, education_mode: str, program_name: str,
                                    **kwargs) -> Dict[str, Any]:
        try:
            program_id = f"cbe_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = EDUCATION_MODES.get(education_mode, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO crossborder_education (
                            program_id, education_mode, program_name,
                            host_institution, partner_institution, country,
                            education_type, degree_type, duration, tuition_fee,
                            application_deadline, intake_season, max_students,
                            enrolled_count, description, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 'active', ?, ?)
                    ''', (program_id, education_mode, program_name,
                          kwargs.get('host_institution'),
                          kwargs.get('partner_institution'),
                          kwargs.get('country'), kwargs.get('education_type'),
                          kwargs.get('degree_type', config.get('degree_types', [''])[0]),
                          kwargs.get('duration'), kwargs.get('tuition_fee', 0),
                          kwargs.get('application_deadline'),
                          kwargs.get('intake_season'),
                          kwargs.get('max_students', 100),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建跨境教育项目: {program_name} ({program_id})')
                    return {'success': True, 'program_id': program_id}
        except Exception as e:
            logger.error(f'创建跨境教育项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def apply_crossborder_program(self, program_id: str, student_id: int,
                                   student_name: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_students, enrolled_count, status, application_deadline FROM crossborder_education WHERE program_id = ?', (program_id,))
                    program = cursor.fetchone()
                    if not program:
                        return {'success': False, 'error': '跨境教育项目不存在'}
                    if program[2] != 'active':
                        return {'success': False, 'error': '项目状态不允许申请'}
                    if program[0] and program[1] >= program[0]:
                        return {'success': False, 'error': '名额已满'}
                    if program[3] and now[:10] > program[3]:
                        return {'success': False, 'error': '申请已截止'}
                    cursor.execute('INSERT OR IGNORE INTO education_programs (program_id, program_name, education_mode, provider, country, education_type, level, duration, credits, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                                 (f"edp_{uuid.uuid4().hex[:12]}", kwargs.get('program_name'), kwargs.get('education_mode'), kwargs.get('provider'), kwargs.get('country'), kwargs.get('education_type'), kwargs.get('level'), kwargs.get('duration'), kwargs.get('credits', 0), kwargs.get('description')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'申请跨境教育项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_crossborder_program(self, program_id: str, student_id: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE crossborder_education SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE program_id = ?',
                                 (now, program_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '项目不存在'}
        except Exception as e:
            logger.error(f'跨境教育项目注册失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_crossborder_program_details(self, program_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM crossborder_education WHERE program_id = ?', (program_id,))
                program = cursor.fetchone()
                if not program:
                    return {'success': False, 'error': '项目不存在'}
                return {'success': True, 'program': dict(program)}
        except Exception as e:
            logger.error(f'获取跨境教育项目详情失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 国际课程开发 ==========

    def create_international_curriculum(self, curriculum_type: str, course_name: str,
                                         **kwargs) -> Dict[str, Any]:
        try:
            curriculum_id = f"cur_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = CURRICULUM_TYPES.get(curriculum_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO international_curriculum (
                            curriculum_id, curriculum_type, course_name,
                            provider, education_type, level, credits,
                            duration_hours, language, prerequisites,
                            syllabus, description, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (curriculum_id, curriculum_type, course_name,
                          kwargs.get('provider', config.get('provider', [''])[0]),
                          kwargs.get('education_type'), kwargs.get('level'),
                          kwargs.get('credits', 3), kwargs.get('duration_hours', 48),
                          kwargs.get('language', 'English'),
                          kwargs.get('prerequisites'), kwargs.get('syllabus'),
                          kwargs.get('description'), now, now))
                    cursor.execute('INSERT INTO curriculum_versions (curriculum_id, version, update_date, changelog) VALUES (?, ?, ?, ?)',
                                 (curriculum_id, '1.0', now[:10], 'Initial version'))
                    conn.commit()
                    logger.info(f'创建国际课程: {course_name} ({curriculum_id})')
                    return {'success': True, 'curriculum_id': curriculum_id}
        except Exception as e:
            logger.error(f'创建国际课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_curriculum_version(self, curriculum_id: str, version: str,
                                  changelog: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE curriculum_versions SET status = ? WHERE curriculum_id = ? AND status = ?',
                                 ('archived', curriculum_id, 'current'))
                    cursor.execute('INSERT INTO curriculum_versions (curriculum_id, version, update_date, changelog, status) VALUES (?, ?, ?, ?, ?)',
                                 (curriculum_id, version, now[:10], changelog, 'current'))
                    cursor.execute('UPDATE international_curriculum SET updated_at = ? WHERE curriculum_id = ?', (now, curriculum_id))
                    conn.commit()
                    return {'success': True, 'version': version}
        except Exception as e:
            logger.error(f'更新课程版本失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_curriculum_details(self, curriculum_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM international_curriculum WHERE curriculum_id = ?', (curriculum_id,))
                curriculum = cursor.fetchone()
                if not curriculum:
                    return {'success': False, 'error': '课程不存在'}
                cursor.execute('SELECT * FROM curriculum_versions WHERE curriculum_id = ? ORDER BY update_date DESC', (curriculum_id,))
                versions = [dict(v) for v in cursor.fetchall()]
                return {'success': True, 'curriculum': dict(curriculum), 'versions': versions}
        except Exception as e:
            logger.error(f'获取课程详情失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_curriculum(self, curriculum_type: str = None, education_type: str = None,
                        page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM international_curriculum WHERE 1=1'
                params = []
                if curriculum_type:
                    query += ' AND curriculum_type = ?'
                    params.append(curriculum_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
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

    # ========== 国际认证评估 ==========

    def create_certification(self, certification_type: str, cert_name: str,
                             **kwargs) -> Dict[str, Any]:
        try:
            cert_id = f"crt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = CERTIFICATION_TYPES.get(certification_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO international_certification (
                            cert_id, certification_type, cert_name,
                            issuing_body, education_type, valid_period,
                            application_fee, exam_date, registration_deadline,
                            description, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?, ?)
                    ''', (cert_id, certification_type, cert_name,
                          kwargs.get('issuing_body'), kwargs.get('education_type'),
                          kwargs.get('valid_period', '3年'),
                          kwargs.get('application_fee', 0),
                          kwargs.get('exam_date'), kwargs.get('registration_deadline'),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建国际认证: {cert_name} ({cert_id})')
                    return {'success': True, 'cert_id': cert_id}
        except Exception as e:
            logger.error(f'创建国际认证失败: {e}')
            return {'success': False, 'error': str(e)}

    def apply_certification(self, cert_id: str, applicant_id: int,
                            applicant_name: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status, registration_deadline FROM international_certification WHERE cert_id = ?', (cert_id,))
                    cert = cursor.fetchone()
                    if not cert:
                        return {'success': False, 'error': '认证不存在'}
                    if cert[0] != 'open':
                        return {'success': False, 'error': '认证状态不允许申请'}
                    if cert[1] and now[:10] > cert[1]:
                        return {'success': False, 'error': '报名已截止'}
                    cursor.execute('INSERT INTO certification_records (cert_id, applicant_id, applicant_name, education_type, application_date) VALUES (?, ?, ?, ?, ?)',
                                 (cert_id, applicant_id, applicant_name, kwargs.get('education_type'), now[:10]))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'申请认证失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_certification_result(self, cert_id: str, applicant_id: int,
                                     result: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            certificate_no = f"ICR{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}" if result == 'pass' else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE certification_records SET
                            exam_score = ?, result = ?, certificate_no = ?,
                            certificate_url = ?, issue_date = ?, expiry_date = ?
                        WHERE cert_id = ? AND applicant_id = ?
                    ''', (kwargs.get('exam_score'), result, certificate_no,
                          kwargs.get('certificate_url'), now[:10], kwargs.get('expiry_date'),
                          cert_id, applicant_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'certificate_no': certificate_no}
                    return {'success': False, 'error': '认证记录不存在'}
        except Exception as e:
            logger.error(f'记录认证结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def verify_certificate(self, certificate_no: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM certification_records WHERE certificate_no = ?', (certificate_no,))
                record = cursor.fetchone()
                if not record:
                    return {'success': False, 'error': '证书不存在'}
                return {'success': True, 'certificate': dict(record)}
        except Exception as e:
            logger.error(f'验证证书失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_certification_records(self, applicant_id: int = None, cert_id: str = None,
                                   page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM certification_records WHERE 1=1'
                params = []
                if applicant_id:
                    query += ' AND applicant_id = ?'
                    params.append(applicant_id)
                if cert_id:
                    query += ' AND cert_id = ?'
                    params.append(cert_id)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY application_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取认证记录失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 国际人才流动 ==========

    def create_talent_flow_program(self, flow_type: str, program_name: str,
                                    **kwargs) -> Dict[str, Any]:
        try:
            flow_id = f"tlf_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = TALENT_FLOW.get(flow_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO talent_flow (
                            flow_id, flow_type, program_name, country,
                            education_type, direction, max_talents,
                            talent_count, description, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, 'open', ?, ?)
                    ''', (flow_id, flow_type, program_name, kwargs.get('country'),
                          kwargs.get('education_type'),
                          kwargs.get('direction', config.get('direction')),
                          kwargs.get('max_talents', 20), kwargs.get('description'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建人才流动项目: {program_name} ({flow_id})')
                    return {'success': True, 'flow_id': flow_id}
        except Exception as e:
            logger.error(f'创建人才流动项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def apply_talent_flow(self, flow_id: str, talent_id: int, talent_name: str,
                          talent_type: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_talents, talent_count, status FROM talent_flow WHERE flow_id = ?', (flow_id,))
                    flow = cursor.fetchone()
                    if not flow:
                        return {'success': False, 'error': '人才流动项目不存在'}
                    if flow[2] != 'open':
                        return {'success': False, 'error': '项目状态不允许申请'}
                    if flow[0] and flow[1] >= flow[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('INSERT INTO flow_records (flow_id, talent_id, talent_name, talent_type, education_type, application_date, approval_status) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                 (flow_id, talent_id, talent_name, talent_type, kwargs.get('education_type'), now[:10], 'pending'))
                    cursor.execute('UPDATE talent_flow SET talent_count = talent_count + 1, updated_at = ? WHERE flow_id = ?', (now, flow_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'申请人才流动失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_talent_flow_application(self, flow_id: str, talent_id: int,
                                         approved: bool) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE flow_records SET approval_status = ? WHERE flow_id = ? AND talent_id = ? AND approval_status = ?',
                                 (status, flow_id, talent_id, 'pending'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '申请状态不允许审核'}
        except Exception as e:
            logger.error(f'审核人才流动申请失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_talent_flow_evaluation(self, flow_id: str, talent_id: int,
                                       evaluation: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE flow_records SET evaluation = ? WHERE flow_id = ? AND talent_id = ?',
                                 (evaluation, flow_id, talent_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '人才流动记录不存在'}
        except Exception as e:
            logger.error(f'记录人才流动评价失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 国际教育标准 ==========

    def create_education_standard(self, standard_type: str, standard_name: str,
                                   **kwargs) -> Dict[str, Any]:
        try:
            standard_id = f"std_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = STANDARD_TYPES.get(standard_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO education_standards (
                            standard_id, standard_type, standard_name,
                            education_type, applicable_scope, version,
                            description, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (standard_id, standard_type, standard_name,
                          kwargs.get('education_type'),
                          kwargs.get('applicable_scope', config.get('applicable', [''])[0]),
                          kwargs.get('version', '1.0'), kwargs.get('description'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建教育标准: {standard_name} ({standard_id})')
                    return {'success': True, 'standard_id': standard_id}
        except Exception as e:
            logger.error(f'创建教育标准失败: {e}')
            return {'success': False, 'error': str(e)}

    def upload_standard_document(self, standard_id: str, document_name: str,
                                  document_url: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO standard_documents (standard_id, document_name, document_url, upload_date, version) VALUES (?, ?, ?, ?, ?)',
                                 (standard_id, document_name, document_url, now[:10], kwargs.get('version')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'上传标准文档失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_standard_details(self, standard_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM education_standards WHERE standard_id = ?', (standard_id,))
                standard = cursor.fetchone()
                if not standard:
                    return {'success': False, 'error': '标准不存在'}
                cursor.execute('SELECT * FROM standard_documents WHERE standard_id = ?', (standard_id,))
                documents = [dict(d) for d in cursor.fetchall()]
                return {'success': True, 'standard': dict(standard), 'documents': documents}
        except Exception as e:
            logger.error(f'获取标准详情失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_education_standards(self, standard_type: str = None, education_type: str = None,
                                  page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM education_standards WHERE 1=1'
                params = []
                if standard_type:
                    query += ' AND standard_type = ?'
                    params.append(standard_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                standards = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'standards': standards, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取标准列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 全球教育网络 ==========

    def create_global_network(self, network_type: str, network_name: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            network_id = f"gln_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = NETWORK_TYPES.get(network_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO global_network (
                            network_id, network_type, network_name,
                            education_type, headquarters, member_count,
                            description, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 0, ?, 'active', ?, ?)
                    ''', (network_id, network_type, network_name,
                          kwargs.get('education_type'), kwargs.get('headquarters'),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建全球教育网络: {network_name} ({network_id})')
                    return {'success': True, 'network_id': network_id}
        except Exception as e:
            logger.error(f'创建全球教育网络失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_network_member(self, network_id: str, member_id: int, member_name: str,
                           member_type: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT OR IGNORE INTO network_members (network_id, member_id, member_name, member_type, join_date, status) VALUES (?, ?, ?, ?, ?, ?)',
                                 (network_id, member_id, member_name, member_type, now[:10], 'active'))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE global_network SET member_count = member_count + 1, updated_at = ? WHERE network_id = ?', (now, network_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已加入该网络'}
        except Exception as e:
            logger.error(f'添加网络成员失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_network_details(self, network_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM global_network WHERE network_id = ?', (network_id,))
                network = cursor.fetchone()
                if not network:
                    return {'success': False, 'error': '网络不存在'}
                cursor.execute('SELECT * FROM network_members WHERE network_id = ?', (network_id,))
                members = [dict(m) for m in cursor.fetchall()]
                return {'success': True, 'network': dict(network), 'members': members}
        except Exception as e:
            logger.error(f'获取网络详情失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_global_networks(self, network_type: str = None, education_type: str = None,
                              page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM global_network WHERE 1=1'
                params = []
                if network_type:
                    query += ' AND network_type = ?'
                    params.append(network_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                networks = [dict(n) for n in cursor.fetchall()]
                return {'success': True, 'networks': networks, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取网络列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 国际教育政策 ==========

    def create_education_policy(self, policy_area: str, policy_name: str,
                                 **kwargs) -> Dict[str, Any]:
        try:
            policy_id = f"pol_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO education_policy (
                            policy_id, policy_area, policy_name,
                            issuing_authority, education_type, effective_date,
                            expiry_date, policy_text, description, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (policy_id, policy_area, policy_name,
                          kwargs.get('issuing_authority'), kwargs.get('education_type'),
                          kwargs.get('effective_date'), kwargs.get('expiry_date'),
                          kwargs.get('policy_text'), kwargs.get('description'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建教育政策: {policy_name} ({policy_id})')
                    return {'success': True, 'policy_id': policy_id}
        except Exception as e:
            logger.error(f'创建教育政策失败: {e}')
            return {'success': False, 'error': str(e)}

    def upload_policy_document(self, policy_id: str, document_name: str,
                                document_url: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO policy_documents (policy_id, document_name, document_url, upload_date) VALUES (?, ?, ?, ?)',
                                 (policy_id, document_name, document_url, now[:10]))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'上传政策文档失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_policy_details(self, policy_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM education_policy WHERE policy_id = ?', (policy_id,))
                policy = cursor.fetchone()
                if not policy:
                    return {'success': False, 'error': '政策不存在'}
                cursor.execute('SELECT * FROM policy_documents WHERE policy_id = ?', (policy_id,))
                documents = [dict(d) for d in cursor.fetchall()]
                return {'success': True, 'policy': dict(policy), 'documents': documents}
        except Exception as e:
            logger.error(f'获取政策详情失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_education_policies(self, policy_area: str = None, education_type: str = None,
                                 page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM education_policy WHERE 1=1'
                params = []
                if policy_area:
                    query += ' AND policy_area = ?'
                    params.append(policy_area)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY effective_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                policies = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'policies': policies, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取政策列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 预警管理 ==========

    def create_global_alert(self, alert_type: str, country: str, title: str,
                            content: str, **kwargs) -> Dict[str, Any]:
        try:
            alert_id = f"alt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO global_alerts (
                            alert_id, alert_type, country, education_type,
                            title, content, severity, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (alert_id, alert_type, country, kwargs.get('education_type'),
                          title, content, kwargs.get('severity', 'medium'),
                          now, now))
                    cursor.execute('INSERT INTO alert_history (alert_id, action, action_date, operator) VALUES (?, ?, ?, ?)',
                                 (alert_id, 'created', now[:10], kwargs.get('operator', 'system')))
                    conn.commit()
                    logger.info(f'创建全球预警: {title} ({alert_id})')
                    return {'success': True, 'alert_id': alert_id}
        except Exception as e:
            logger.error(f'创建全球预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_alert_status(self, alert_id: str, status: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE global_alerts SET status = ?, updated_at = ? WHERE alert_id = ?',
                                 (status, now, alert_id))
                    cursor.execute('INSERT INTO alert_history (alert_id, action, action_date, operator) VALUES (?, ?, ?, ?)',
                                 (alert_id, f'status_update:{status}', now[:10], kwargs.get('operator', 'system')))
                    conn.commit()
                    return {'success': True, 'status': status}
        except Exception as e:
            logger.error(f'更新预警状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_alert_details(self, alert_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM global_alerts WHERE alert_id = ?', (alert_id,))
                alert = cursor.fetchone()
                if not alert:
                    return {'success': False, 'error': '预警不存在'}
                cursor.execute('SELECT * FROM alert_history WHERE alert_id = ? ORDER BY action_date DESC', (alert_id,))
                history = [dict(h) for h in cursor.fetchall()]
                return {'success': True, 'alert': dict(alert), 'history': history}
        except Exception as e:
            logger.error(f'获取预警详情失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_global_alerts(self, country: str = None, education_type: str = None,
                           severity: str = None, status: str = 'active',
                           page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM global_alerts WHERE 1=1'
                params = []
                if country:
                    query += ' AND country = ?'
                    params.append(country)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if severity:
                    query += ' AND severity = ?'
                    params.append(severity)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                alerts = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'alerts': alerts, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取预警列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计管理 ==========

    def get_global_education_stats(self, education_type: str = None, country: str = None,
                                    stat_date: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM global_stats WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if country:
                    query += ' AND country = ?'
                    params.append(country)
                if stat_date:
                    query += ' AND stat_date = ?'
                    params.append(stat_date)
                cursor.execute(query, params)
                stats = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'stats': stats}
        except Exception as e:
            logger.error(f'获取全球教育统计失败: {e}')
            return {'success': False, 'error': str(e)}