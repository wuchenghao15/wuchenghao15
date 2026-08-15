#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育国际化服务 (v15.14.0)
====================================
提供国际合作办学、国际课程、国际交流、留学生管理、国际考试、
海外升学、跨文化教育、国际认证等综合管理服务。

核心能力：
1. 国际项目 - 中外合作办学/双学位/交换生/留学预科/海外分校/联合培养/短期交流/暑期学校
2. 合作院校 - 学术合作/学生交流/教师互访/联合研究/课程共建/学分互认/学位互授/战略联盟
3. 国际课程 - 双语课程/国际认证课程/学分互认课程
4. 交换生 - 交换申请/录取管理/学分转换/成绩对接
5. 留学生 - 招生管理/学籍管理/签证办理/住宿安排/毕业管理
6. 国际考试 - TOEFL/IELTS/JLPT/GRE/GMAT/SAT/ACT/AP
7. 海外升学 - 升学指导/申请管理/录取跟踪/签证服务
8. 跨文化教育 - 文化体验/语言沉浸/学术交流/实习/志愿服务
9. 国际认证 - IB/A-Level/AP/BCA/国际文凭
10. 统计分析 - 国际化数据汇总与分析

差异化支持：
- 成人教育：职业导向、短期项目、灵活学习
- K12教育：课程衔接、语言准备、文化适应
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_internationalization_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationInternationalization')


# ========== 国际化配置 ==========

INTERNATIONAL_PROGRAMS = {
    'chinese_foreign': {'name': '中外合作办学', 'education_type': ['adult', 'k12', 'higher']},
    'dual_degree': {'name': '双学位', 'education_type': ['higher']},
    'exchange': {'name': '交换生', 'education_type': ['higher', 'k12']},
    'foundation': {'name': '留学预科', 'education_type': ['higher', 'k12']},
    'overseas_campus': {'name': '海外分校', 'education_type': ['higher']},
    'joint_training': {'name': '联合培养', 'education_type': ['higher']},
    'short_term': {'name': '短期交流', 'education_type': ['adult', 'higher', 'k12']},
    'summer_school': {'name': '暑期学校', 'education_type': ['higher', 'k12']}
}

PARTNER_TYPES = {
    'academic': {'name': '学术合作', 'description': '科研合作、学术交流'},
    'student_exchange': {'name': '学生交流', 'description': '交换生项目'},
    'faculty_exchange': {'name': '教师互访', 'description': '教师交流、联合授课'},
    'joint_research': {'name': '联合研究', 'description': '合作研究项目'},
    'course_development': {'name': '课程共建', 'description': '共同开发课程'},
    'credit_recognition': {'name': '学分互认', 'description': '学分转换协议'},
    'degree_recognition': {'name': '学位互授', 'description': '双学位项目'},
    'strategic_alliance': {'name': '战略联盟', 'description': '长期战略合作'}
}

LANGUAGE_PROGRAMS = {
    'english': {'name': '英语', 'levels': ['beginner', 'intermediate', 'advanced', 'proficiency']},
    'japanese': {'name': '日语', 'levels': ['N5', 'N4', 'N3', 'N2', 'N1']},
    'korean': {'name': '韩语', 'levels': ['TOPIK I', 'TOPIK II']},
    'french': {'name': '法语', 'levels': ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']},
    'german': {'name': '德语', 'levels': ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']},
    'spanish': {'name': '西班牙语', 'levels': ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']},
    'chinese_international': {'name': '汉语国际教育', 'levels': ['HSK 1-6']}
}

STUDENT_TYPES = {
    'undergraduate': {'name': '本科生', 'duration': '4 years'},
    'graduate': {'name': '研究生', 'duration': '2-3 years'},
    'exchange': {'name': '交换生', 'duration': '1 semester - 1 year'},
    'short_term': {'name': '短期生', 'duration': '< 1 semester'},
    'language': {'name': '语言生', 'duration': 'flexible'},
    'foundation': {'name': '预科生', 'duration': '1 year'}
}

EXAM_TYPES = {
    'TOEFL': {'name': '托福', 'format': 'iBT/ITP', 'score_range': '0-120', 'validity': '2 years'},
    'IELTS': {'name': '雅思', 'format': 'Academic/General', 'score_range': '0-9', 'validity': '2 years'},
    'JLPT': {'name': '日语能力考试', 'format': 'N1-N5', 'score_range': '0-180', 'validity': 'lifetime'},
    'GRE': {'name': 'GRE', 'format': 'General/Subject', 'score_range': '130-170', 'validity': '5 years'},
    'GMAT': {'name': 'GMAT', 'format': 'Computer Adaptive', 'score_range': '200-800', 'validity': '5 years'},
    'SAT': {'name': 'SAT', 'format': 'Paper', 'score_range': '400-1600', 'validity': '5 years'},
    'ACT': {'name': 'ACT', 'format': 'Paper', 'score_range': '1-36', 'validity': '5 years'},
    'AP': {'name': 'AP', 'format': 'Subject', 'score_range': '1-5', 'validity': 'flexible'}
}

DESTINATION_REGIONS = {
    'north_america': {'name': '北美', 'countries': ['美国', '加拿大']},
    'europe': {'name': '欧洲', 'countries': ['英国', '德国', '法国', '意大利', '西班牙']},
    'asia': {'name': '亚洲', 'countries': ['日本', '韩国', '新加坡', '中国香港', '澳大利亚']},
    'oceania': {'name': '大洋洲', 'countries': ['澳大利亚', '新西兰']},
    'south_america': {'name': '南美', 'countries': ['巴西', '阿根廷']},
    'africa': {'name': '非洲', 'countries': ['南非', '埃及']}
}

CULTURE_PROGRAMS = {
    'culture_experience': {'name': '文化体验', 'duration': '1-4 weeks'},
    'language_immersion': {'name': '语言沉浸', 'duration': '4-12 weeks'},
    'academic_exchange': {'name': '学术交流', 'duration': '1 semester'},
    'internship': {'name': '实习', 'duration': '3-6 months'},
    'volunteer': {'name': '志愿服务', 'duration': '2-8 weeks'}
}

INTERNATIONAL_CERTIFICATIONS = {
    'IB': {'name': '国际文凭', 'levels': ['DP', 'MYP', 'PYP'], 'age_range': '3-19'},
    'A-Level': {'name': '英国高中课程', 'levels': ['AS', 'A2'], 'age_range': '16-18'},
    'AP': {'name': '美国大学先修课程', 'levels': ['AP'], 'age_range': '10-12'},
    'BCA': {'name': '国际双语课程认证', 'levels': ['Primary', 'Secondary'], 'age_range': '6-18'},
    'international_diploma': {'name': '国际文凭认证', 'levels': ['Standard', 'Advanced'], 'age_range': '16-18'}
}


class EducationInternationalizationService:
    """教育国际化服务"""

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
                    CREATE TABLE IF NOT EXISTS international_programs (
                        program_id TEXT PRIMARY KEY,
                        program_name TEXT NOT NULL,
                        program_type TEXT NOT NULL,
                        education_type TEXT,
                        description TEXT,
                        partner_institution TEXT,
                        partner_id TEXT,
                        duration TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        max_students INTEGER DEFAULT 30,
                        enrolled_count INTEGER DEFAULT 0,
                        tuition_fee REAL,
                        language_requirement TEXT,
                        application_deadline TEXT,
                        eligibility TEXT,
                        status TEXT DEFAULT 'open',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS program_partners (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        program_id TEXT NOT NULL,
                        partner_id TEXT NOT NULL,
                        partnership_type TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        status TEXT DEFAULT 'active',
                        UNIQUE(program_id, partner_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS international_courses (
                        course_id TEXT PRIMARY KEY,
                        course_name TEXT NOT NULL,
                        course_code TEXT,
                        program_id TEXT,
                        education_type TEXT,
                        grade_level INTEGER,
                        language TEXT,
                        credits REAL,
                        instructor TEXT,
                        instructor_id INTEGER,
                        semester TEXT,
                        weekly_hours INTEGER DEFAULT 3,
                        max_students INTEGER DEFAULT 25,
                        enrolled_count INTEGER DEFAULT 0,
                        description TEXT,
                        is_credit_recognized INTEGER DEFAULT 0,
                        partner_institution TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS course_enrollments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        course_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        student_type TEXT,
                        education_type TEXT,
                        enroll_date TEXT,
                        final_score REAL,
                        grade TEXT,
                        credits_earned REAL,
                        status TEXT DEFAULT 'enrolled',
                        UNIQUE(course_id, student_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS exchange_students (
                        exchange_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        student_type TEXT,
                        education_type TEXT,
                        home_institution TEXT,
                        host_institution TEXT,
                        host_institution_id TEXT,
                        program_id TEXT,
                        exchange_type TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        duration TEXT,
                        language_level TEXT,
                        credits_transferred REAL,
                        status TEXT DEFAULT 'pending',
                        application_date TEXT,
                        acceptance_date TEXT,
                        departure_date TEXT,
                        return_date TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS exchange_applications (
                        application_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        program_id TEXT NOT NULL,
                        exchange_type TEXT,
                        host_institution TEXT,
                        personal_statement TEXT,
                        recommendation_letter TEXT,
                        academic_transcript TEXT,
                        language_proof TEXT,
                        application_status TEXT DEFAULT 'submitted',
                        review_comments TEXT,
                        submitted_at TEXT,
                        reviewed_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS international_exams (
                        exam_id TEXT PRIMARY KEY,
                        exam_type TEXT NOT NULL,
                        exam_name TEXT,
                        exam_date TEXT,
                        registration_deadline TEXT,
                        location TEXT,
                        fee REAL,
                        max_participants INTEGER DEFAULT 100,
                        registered_count INTEGER DEFAULT 0,
                        format TEXT,
                        score_range TEXT,
                        validity TEXT,
                        education_type TEXT,
                        status TEXT DEFAULT 'open',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS exam_registrations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        exam_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        education_type TEXT,
                        student_type TEXT,
                        register_date TEXT,
                        exam_fee_paid INTEGER DEFAULT 0,
                        score REAL,
                        score_report_url TEXT,
                        status TEXT DEFAULT 'registered',
                        UNIQUE(exam_id, student_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS overseas_students (
                        student_id INTEGER PRIMARY KEY,
                        student_name TEXT NOT NULL,
                        student_type TEXT,
                        education_type TEXT,
                        country TEXT,
                        region TEXT,
                        home_institution TEXT,
                        host_institution TEXT,
                        program_name TEXT,
                        program_id TEXT,
                        start_date TEXT,
                        expected_graduation_date TEXT,
                        visa_status TEXT,
                        visa_expiry_date TEXT,
                        accommodation TEXT,
                        emergency_contact TEXT,
                        health_insurance TEXT,
                        language_level TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS student_visas (
                        visa_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        visa_type TEXT,
                        country TEXT,
                        issue_date TEXT,
                        expiry_date TEXT,
                        application_status TEXT DEFAULT 'applied',
                        application_date TEXT,
                        approved_date TEXT,
                        rejection_reason TEXT,
                        documents TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS intercultural_programs (
                        program_id TEXT PRIMARY KEY,
                        program_name TEXT NOT NULL,
                        program_type TEXT,
                        education_type TEXT,
                        description TEXT,
                        location TEXT,
                        region TEXT,
                        duration TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        max_participants INTEGER DEFAULT 20,
                        enrolled_count INTEGER DEFAULT 0,
                        fee REAL,
                        language_requirement TEXT,
                        eligibility TEXT,
                        status TEXT DEFAULT 'open',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS program_participants (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        program_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        education_type TEXT,
                        student_type TEXT,
                        enroll_date TEXT,
                        completion_status TEXT DEFAULT 'participating',
                        completion_date TEXT,
                        evaluation TEXT,
                        UNIQUE(program_id, student_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS international_certifications (
                        cert_id TEXT PRIMARY KEY,
                        cert_type TEXT NOT NULL,
                        cert_name TEXT,
                        education_type TEXT,
                        grade_level INTEGER,
                        issuing_body TEXT,
                        valid_from TEXT,
                        valid_until TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS certification_records (
                        record_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        cert_id TEXT NOT NULL,
                        cert_type TEXT,
                        education_type TEXT,
                        exam_date TEXT,
                        result TEXT,
                        score REAL,
                        certificate_no TEXT,
                        certificate_url TEXT,
                        issued_date TEXT,
                        valid_until TEXT,
                        status TEXT DEFAULT 'completed',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS study_abroad (
                        application_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        education_type TEXT,
                        student_type TEXT,
                        target_region TEXT,
                        target_country TEXT,
                        target_institution TEXT,
                        target_program TEXT,
                        application_status TEXT DEFAULT 'planning',
                        test_scores TEXT,
                        transcripts TEXT,
                        letters_of_recommendation TEXT,
                        personal_statement TEXT,
                        application_date TEXT,
                        acceptance_date TEXT,
                        rejection_date TEXT,
                        visa_status TEXT,
                        departure_date TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS partner_institutions (
                        partner_id TEXT PRIMARY KEY,
                        institution_name TEXT NOT NULL,
                        country TEXT,
                        region TEXT,
                        institution_type TEXT,
                        accreditation TEXT,
                        partnership_type TEXT,
                        contact_person TEXT,
                        contact_email TEXT,
                        contact_phone TEXT,
                        website TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        established_date TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('教育国际化服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 国际项目 ==========

    def create_international_program(self, program_name: str, program_type: str,
                                      **kwargs) -> Dict[str, Any]:
        try:
            program_id = f"ipr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = INTERNATIONAL_PROGRAMS.get(program_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO international_programs (
                            program_id, program_name, program_type, education_type,
                            description, partner_institution, partner_id,
                            duration, start_date, end_date, max_students,
                            enrolled_count, tuition_fee, language_requirement,
                            application_deadline, eligibility, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, 'open', ?, ?)
                    ''', (program_id, program_name, program_type,
                          kwargs.get('education_type'), kwargs.get('description'),
                          kwargs.get('partner_institution'), kwargs.get('partner_id'),
                          kwargs.get('duration'), kwargs.get('start_date'),
                          kwargs.get('end_date'), kwargs.get('max_students', 30),
                          kwargs.get('tuition_fee'), kwargs.get('language_requirement'),
                          kwargs.get('application_deadline'), kwargs.get('eligibility'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建国际项目: {program_name} ({program_id})')
                    return {'success': True, 'program_id': program_id}
        except Exception as e:
            logger.error(f'创建国际项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_international_program(self, program_id: str, student_id: int,
                                      **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_students, enrolled_count, status FROM international_programs WHERE program_id = ?', (program_id,))
                    program = cursor.fetchone()
                    if not program:
                        return {'success': False, 'error': '项目不存在'}
                    if program[2] != 'open':
                        return {'success': False, 'error': '项目报名已关闭'}
                    if program[0] and program[1] >= program[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('INSERT OR IGNORE INTO program_participants (program_id, student_id, student_name, education_type, student_type, enroll_date) VALUES (?, ?, ?, ?, ?, ?)',
                                 (program_id, student_id, kwargs.get('student_name'),
                                  kwargs.get('education_type'), kwargs.get('student_type'), now[:10]))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE international_programs SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE program_id = ?', (now, program_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已报名该项目'}
        except Exception as e:
            logger.error(f'报名国际项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_international_programs(self, program_type: str = None,
                                     education_type: str = None,
                                     status: str = 'open', page: int = 1,
                                     page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM international_programs WHERE 1=1'
                params = []
                if program_type:
                    query += ' AND program_type = ?'
                    params.append(program_type)
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
                programs = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'programs': programs, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取国际项目列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_program_status(self, program_id: str, status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE international_programs SET status = ?, updated_at = ? WHERE program_id = ?',
                                 (status, now, program_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '项目不存在'}
        except Exception as e:
            logger.error(f'更新项目状态失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 合作院校 ==========

    def add_partner_institution(self, institution_name: str, country: str,
                                 **kwargs) -> Dict[str, Any]:
        try:
            partner_id = f"pni_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            region_config = {}
            for key, value in DESTINATION_REGIONS.items():
                if country in value.get('countries', []):
                    region_config = value
                    break
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO partner_institutions (
                            partner_id, institution_name, country, region,
                            institution_type, accreditation, partnership_type,
                            contact_person, contact_email, contact_phone,
                            website, description, status, established_date,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
                    ''', (partner_id, institution_name, country,
                          kwargs.get('region', region_config.get('name')),
                          kwargs.get('institution_type'), kwargs.get('accreditation'),
                          kwargs.get('partnership_type'), kwargs.get('contact_person'),
                          kwargs.get('contact_email'), kwargs.get('contact_phone'),
                          kwargs.get('website'), kwargs.get('description'),
                          kwargs.get('established_date'), now, now))
                    conn.commit()
                    logger.info(f'添加合作院校: {institution_name} ({partner_id})')
                    return {'success': True, 'partner_id': partner_id}
        except Exception as e:
            logger.error(f'添加合作院校失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_partner_institution(self, partner_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    updates = []
                    params = []
                    for key, value in kwargs.items():
                        if key != 'partner_id':
                            updates.append(f'{key} = ?')
                            params.append(value)
                    params.append(now)
                    params.append(partner_id)
                    updates.append('updated_at = ?')
                    cursor.execute(f'UPDATE partner_institutions SET {", ".join(updates)} WHERE partner_id = ?', params)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '合作院校不存在'}
        except Exception as e:
            logger.error(f'更新合作院校失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_partner_institutions(self, region: str = None, country: str = None,
                                   status: str = 'active', page: int = 1,
                                   page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM partner_institutions WHERE 1=1'
                params = []
                if region:
                    query += ' AND region = ?'
                    params.append(region)
                if country:
                    query += ' AND country = ?'
                    params.append(country)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                institutions = [dict(i) for i in cursor.fetchall()]
                return {'success': True, 'institutions': institutions, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取合作院校列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_partnership(self, program_id: str, partner_id: str,
                         partnership_type: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT OR IGNORE INTO program_partners (program_id, partner_id, partnership_type, start_date, end_date, status) VALUES (?, ?, ?, ?, ?, ?)',
                                 (program_id, partner_id, partnership_type,
                                  kwargs.get('start_date', now[:10]),
                                  kwargs.get('end_date'), 'active'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '合作关系已存在'}
        except Exception as e:
            logger.error(f'添加合作关系失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 国际课程 ==========

    def create_international_course(self, course_name: str, **kwargs) -> Dict[str, Any]:
        try:
            course_id = f"ico_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO international_courses (
                            course_id, course_name, course_code, program_id,
                            education_type, grade_level, language, credits,
                            instructor, instructor_id, semester, weekly_hours,
                            max_students, enrolled_count, description,
                            is_credit_recognized, partner_institution, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, 'active', ?, ?)
                    ''', (course_id, course_name, kwargs.get('course_code'),
                          kwargs.get('program_id'), kwargs.get('education_type'),
                          kwargs.get('grade_level'), kwargs.get('language'),
                          kwargs.get('credits', 3), kwargs.get('instructor'),
                          kwargs.get('instructor_id'), kwargs.get('semester'),
                          kwargs.get('weekly_hours', 3), kwargs.get('max_students', 25),
                          kwargs.get('description'), kwargs.get('is_credit_recognized', 0),
                          kwargs.get('partner_institution'), now, now))
                    conn.commit()
                    logger.info(f'创建国际课程: {course_name} ({course_id})')
                    return {'success': True, 'course_id': course_id}
        except Exception as e:
            logger.error(f'创建国际课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_international_course(self, course_id: str, student_id: int,
                                     **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_students, enrolled_count, status, credits FROM international_courses WHERE course_id = ?', (course_id,))
                    course = cursor.fetchone()
                    if not course:
                        return {'success': False, 'error': '课程不存在'}
                    if course[2] != 'active':
                        return {'success': False, 'error': '课程状态不允许选课'}
                    if course[0] and course[1] >= course[0]:
                        return {'success': False, 'error': '课程名额已满'}
                    cursor.execute('INSERT OR IGNORE INTO course_enrollments (course_id, student_id, student_name, student_type, education_type, enroll_date) VALUES (?, ?, ?, ?, ?, ?)',
                                 (course_id, student_id, kwargs.get('student_name'),
                                  kwargs.get('student_type'), kwargs.get('education_type'), now[:10]))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE international_courses SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE course_id = ?', (now, course_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已选该课程'}
        except Exception as e:
            logger.error(f'选课国际课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_course_score(self, course_id: str, student_id: int,
                             score: float) -> Dict[str, Any]:
        try:
            grade = 'A' if score >= 90 else ('B' if score >= 80 else ('C' if score >= 70 else ('D' if score >= 60 else 'F')))
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT credits FROM international_courses WHERE course_id = ?', (course_id,))
                    course = cursor.fetchone()
                    credits_earned = course[0] if course and score >= 60 else 0
                    cursor.execute('UPDATE course_enrollments SET final_score = ?, grade = ?, credits_earned = ? WHERE course_id = ? AND student_id = ?',
                                 (score, grade, credits_earned, course_id, student_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'grade': grade, 'credits_earned': credits_earned}
                    return {'success': False, 'error': '选课记录不存在'}
        except Exception as e:
            logger.error(f'记录课程成绩失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_international_courses(self, education_type: str = None,
                                    language: str = None, status: str = 'active',
                                    page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM international_courses WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if language:
                    query += ' AND language = ?'
                    params.append(language)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                courses = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'courses': courses, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取国际课程列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 交换生 ==========

    def submit_exchange_application(self, student_id: int, program_id: str,
                                     exchange_type: str, **kwargs) -> Dict[str, Any]:
        try:
            application_id = f"exa_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO exchange_applications (
                            application_id, student_id, program_id, exchange_type,
                            host_institution, personal_statement,
                            recommendation_letter, academic_transcript,
                            language_proof, application_status, submitted_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'submitted', ?)
                    ''', (application_id, student_id, program_id, exchange_type,
                          kwargs.get('host_institution'), kwargs.get('personal_statement'),
                          kwargs.get('recommendation_letter'), kwargs.get('academic_transcript'),
                          kwargs.get('language_proof'), now))
                    conn.commit()
                    logger.info(f'提交交换申请: {application_id}')
                    return {'success': True, 'application_id': application_id}
        except Exception as e:
            logger.error(f'提交交换申请失败: {e}')
            return {'success': False, 'error': str(e)}

    def review_exchange_application(self, application_id: str, approved: bool,
                                     **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE exchange_applications SET application_status = ?, review_comments = ?, reviewed_at = ? WHERE application_id = ? AND application_status = ?',
                                 (status, kwargs.get('review_comments'), now, application_id, 'submitted'))
                    if cursor.rowcount > 0:
                        if approved:
                            cursor.execute('SELECT student_id, program_id, exchange_type, host_institution FROM exchange_applications WHERE application_id = ?', (application_id,))
                            app = cursor.fetchone()
                            exchange_id = f"exc_{uuid.uuid4().hex[:12]}"
                            cursor.execute('''
                                INSERT INTO exchange_students (
                                    exchange_id, student_id, student_name,
                                    student_type, education_type,
                                    home_institution, host_institution,
                                    program_id, exchange_type,
                                    application_date, status
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'accepted')
                            ''', (exchange_id, app[0], kwargs.get('student_name'),
                                  kwargs.get('student_type'), kwargs.get('education_type'),
                                  kwargs.get('home_institution'), app[3],
                                  app[1], app[2], now[:10]))
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '申请状态不允许审核'}
        except Exception as e:
            logger.error(f'审核交换申请失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_exchange_status(self, exchange_id: str, status: str,
                                **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    updates = ['status = ?', 'updated_at = ?']
                    params = [status, now]
                    if status == 'departed':
                        updates.append('departure_date = ?')
                        params.append(kwargs.get('departure_date', now[:10]))
                    elif status == 'returned':
                        updates.append('return_date = ?')
                        params.append(kwargs.get('return_date', now[:10]))
                    params.append(exchange_id)
                    cursor.execute(f'UPDATE exchange_students SET {", ".join(updates)} WHERE exchange_id = ?', params)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '交换记录不存在'}
        except Exception as e:
            logger.error(f'更新交换状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_credit_transfer(self, exchange_id: str, credits_transferred: float,
                                **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE exchange_students SET credits_transferred = ?, updated_at = ? WHERE exchange_id = ?',
                                 (credits_transferred, now, exchange_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'credits_transferred': credits_transferred}
                    return {'success': False, 'error': '交换记录不存在'}
        except Exception as e:
            logger.error(f'记录学分转换失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 留学生 ==========

    def register_overseas_student(self, student_id: int, student_name: str,
                                   student_type: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO overseas_students (
                            student_id, student_name, student_type, education_type,
                            country, region, home_institution, host_institution,
                            program_name, program_id, start_date,
                            expected_graduation_date, visa_status,
                            visa_expiry_date, accommodation, emergency_contact,
                            health_insurance, language_level, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (student_id, student_name, student_type,
                          kwargs.get('education_type'), kwargs.get('country'),
                          kwargs.get('region'), kwargs.get('home_institution'),
                          kwargs.get('host_institution'), kwargs.get('program_name'),
                          kwargs.get('program_id'), kwargs.get('start_date'),
                          kwargs.get('expected_graduation_date'),
                          kwargs.get('visa_status', 'applied'),
                          kwargs.get('visa_expiry_date'), kwargs.get('accommodation'),
                          kwargs.get('emergency_contact'), kwargs.get('health_insurance'),
                          kwargs.get('language_level'), now, now))
                    conn.commit()
                    logger.info(f'注册留学生: {student_name} ({student_id})')
                    return {'success': True, 'student_id': student_id}
        except Exception as e:
            logger.error(f'注册留学生失败: {e}')
            return {'success': False, 'error': str(e)}

    def apply_student_visa(self, student_id: int, visa_type: str, country: str,
                            **kwargs) -> Dict[str, Any]:
        try:
            visa_id = f"vis_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO student_visas (
                            visa_id, student_id, visa_type, country,
                            issue_date, expiry_date, application_status,
                            application_date, documents
                        ) VALUES (?, ?, ?, ?, ?, ?, 'applied', ?, ?)
                    ''', (visa_id, student_id, visa_type, country,
                          kwargs.get('issue_date'), kwargs.get('expiry_date'),
                          now[:10], kwargs.get('documents')))
                    cursor.execute('UPDATE overseas_students SET visa_status = ? WHERE student_id = ?', ('applied', student_id))
                    conn.commit()
                    return {'success': True, 'visa_id': visa_id}
        except Exception as e:
            logger.error(f'申请学生签证失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_visa_status(self, visa_id: str, status: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    updates = ['application_status = ?', 'updated_at = ?']
                    params = [status, now]
                    if status == 'approved':
                        updates.append('approved_date = ?')
                        updates.append('issue_date = ?')
                        updates.append('expiry_date = ?')
                        params.extend([kwargs.get('approved_date', now[:10]),
                                      kwargs.get('issue_date'), kwargs.get('expiry_date')])
                    elif status == 'rejected':
                        updates.append('rejection_reason = ?')
                        params.append(kwargs.get('rejection_reason'))
                    params.append(visa_id)
                    cursor.execute(f'UPDATE student_visas SET {", ".join(updates)} WHERE visa_id = ?', params)
                    if cursor.rowcount > 0:
                        cursor.execute('SELECT student_id FROM student_visas WHERE visa_id = ?', (visa_id,))
                        student = cursor.fetchone()
                        if student:
                            cursor.execute('UPDATE overseas_students SET visa_status = ?, visa_expiry_date = ? WHERE student_id = ?',
                                         (status, kwargs.get('expiry_date'), student[0]))
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '签证记录不存在'}
        except Exception as e:
            logger.error(f'更新签证状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_student_accommodation(self, student_id: int, accommodation: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE overseas_students SET accommodation = ?, updated_at = ? WHERE student_id = ?',
                                 (accommodation, now, student_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '学生不存在'}
        except Exception as e:
            logger.error(f'更新住宿安排失败: {e}')
            return {'success': False, 'error': str(e)}

    def graduate_student(self, student_id: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE overseas_students SET status = ?, updated_at = ? WHERE student_id = ?',
                                 ('graduated', now, student_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '学生不存在'}
        except Exception as e:
            logger.error(f'处理学生毕业失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 国际考试 ==========

    def create_international_exam(self, exam_type: str, exam_date: str, **kwargs) -> Dict[str, Any]:
        try:
            exam_id = f"iex_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = EXAM_TYPES.get(exam_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO international_exams (
                            exam_id, exam_type, exam_name, exam_date,
                            registration_deadline, location, fee,
                            max_participants, registered_count, format,
                            score_range, validity, education_type, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, 'open', ?, ?)
                    ''', (exam_id, exam_type, kwargs.get('exam_name', config.get('name')),
                          exam_date, kwargs.get('registration_deadline'),
                          kwargs.get('location'), kwargs.get('fee', 0),
                          kwargs.get('max_participants', 100),
                          kwargs.get('format', config.get('format')),
                          kwargs.get('score_range', config.get('score_range')),
                          kwargs.get('validity', config.get('validity')),
                          kwargs.get('education_type'), now, now))
                    conn.commit()
                    return {'success': True, 'exam_id': exam_id}
        except Exception as e:
            logger.error(f'创建国际考试失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_international_exam(self, exam_id: str, student_id: int, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, registered_count, status FROM international_exams WHERE exam_id = ?', (exam_id,))
                    exam = cursor.fetchone()
                    if not exam:
                        return {'success': False, 'error': '考试不存在'}
                    if exam[2] != 'open':
                        return {'success': False, 'error': '考试报名已关闭'}
                    if exam[0] and exam[1] >= exam[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('INSERT OR IGNORE INTO exam_registrations (exam_id, student_id, student_name, education_type, student_type, register_date) VALUES (?, ?, ?, ?, ?, ?)',
                                 (exam_id, student_id, kwargs.get('student_name'),
                                  kwargs.get('education_type'), kwargs.get('student_type'), now[:10]))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE international_exams SET registered_count = registered_count + 1, updated_at = ? WHERE exam_id = ?', (now, exam_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已报名该考试'}
        except Exception as e:
            logger.error(f'报名国际考试失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_exam_score(self, exam_id: str, student_id: int, score: float,
                           **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE exam_registrations SET score = ?, score_report_url = ?, status = ? WHERE exam_id = ? AND student_id = ?',
                                 (score, kwargs.get('score_report_url'), 'completed', exam_id, student_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'score': score}
                    return {'success': False, 'error': '考试记录不存在'}
        except Exception as e:
            logger.error(f'记录考试成绩失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_international_exams(self, exam_type: str = None, education_type: str = None,
                                  status: str = 'open', page: int = 1,
                                  page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM international_exams WHERE 1=1'
                params = []
                if exam_type:
                    query += ' AND exam_type = ?'
                    params.append(exam_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY exam_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                exams = [dict(e) for e in cursor.fetchall()]
                return {'success': True, 'exams': exams, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取国际考试列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 海外升学 ==========

    def create_study_abroad_application(self, student_id: int, student_name: str,
                                         **kwargs) -> Dict[str, Any]:
        try:
            application_id = f"sab_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO study_abroad (
                            application_id, student_id, student_name,
                            education_type, student_type, target_region,
                            target_country, target_institution, target_program,
                            application_status, test_scores, transcripts,
                            letters_of_recommendation, personal_statement,
                            application_date, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'planning', ?, ?, ?, ?, ?, ?, ?)
                    ''', (application_id, student_id, student_name,
                          kwargs.get('education_type'), kwargs.get('student_type'),
                          kwargs.get('target_region'), kwargs.get('target_country'),
                          kwargs.get('target_institution'), kwargs.get('target_program'),
                          kwargs.get('test_scores'), kwargs.get('transcripts'),
                          kwargs.get('letters_of_recommendation'),
                          kwargs.get('personal_statement'),
                          kwargs.get('application_date', now[:10]), now, now))
                    conn.commit()
                    logger.info(f'创建海外升学申请: {application_id}')
                    return {'success': True, 'application_id': application_id}
        except Exception as e:
            logger.error(f'创建海外升学申请失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_application_status(self, application_id: str, status: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    updates = ['application_status = ?', 'updated_at = ?']
                    params = [status, now]
                    if status == 'submitted':
                        updates.append('application_date = ?')
                        params.append(kwargs.get('application_date', now[:10]))
                    elif status == 'accepted':
                        updates.append('acceptance_date = ?')
                        updates.append('visa_status = ?')
                        params.extend([kwargs.get('acceptance_date', now[:10]), 'pending'])
                    elif status == 'rejected':
                        updates.append('rejection_date = ?')
                        params.append(kwargs.get('rejection_date', now[:10]))
                    params.append(application_id)
                    cursor.execute(f'UPDATE study_abroad SET {", ".join(updates)} WHERE application_id = ?', params)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '申请不存在'}
        except Exception as e:
            logger.error(f'更新申请状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_visa_status_for_abroad(self, application_id: str, visa_status: str,
                                       **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    updates = ['visa_status = ?', 'updated_at = ?']
                    params = [visa_status, now]
                    if visa_status == 'approved':
                        updates.append('departure_date = ?')
                        params.append(kwargs.get('departure_date'))
                    params.append(application_id)
                    cursor.execute(f'UPDATE study_abroad SET {", ".join(updates)} WHERE application_id = ?', params)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'visa_status': visa_status}
                    return {'success': False, 'error': '申请不存在'}
        except Exception as e:
            logger.error(f'更新签证状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_study_abroad_applications(self, education_type: str = None,
                                        application_status: str = None,
                                        target_region: str = None, page: int = 1,
                                        page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM study_abroad WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if application_status:
                    query += ' AND application_status = ?'
                    params.append(application_status)
                if target_region:
                    query += ' AND target_region = ?'
                    params.append(target_region)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                applications = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'applications': applications, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取海外升学申请列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 跨文化教育 ==========

    def create_intercultural_program(self, program_name: str, program_type: str,
                                      **kwargs) -> Dict[str, Any]:
        try:
            program_id = f"icp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = CULTURE_PROGRAMS.get(program_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO intercultural_programs (
                            program_id, program_name, program_type,
                            education_type, description, location,
                            region, duration, start_date, end_date,
                            max_participants, enrolled_count, fee,
                            language_requirement, eligibility, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, 'open', ?, ?)
                    ''', (program_id, program_name, program_type,
                          kwargs.get('education_type'), kwargs.get('description'),
                          kwargs.get('location'), kwargs.get('region'),
                          kwargs.get('duration', config.get('duration')),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('max_participants', 20), kwargs.get('fee'),
                          kwargs.get('language_requirement'), kwargs.get('eligibility'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建跨文化项目: {program_name} ({program_id})')
                    return {'success': True, 'program_id': program_id}
        except Exception as e:
            logger.error(f'创建跨文化项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_intercultural_program(self, program_id: str, student_id: int, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, enrolled_count, status FROM intercultural_programs WHERE program_id = ?', (program_id,))
                    program = cursor.fetchone()
                    if not program:
                        return {'success': False, 'error': '项目不存在'}
                    if program[2] != 'open':
                        return {'success': False, 'error': '项目报名已关闭'}
                    if program[0] and program[1] >= program[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('INSERT OR IGNORE INTO program_participants (program_id, student_id, student_name, education_type, student_type, enroll_date) VALUES (?, ?, ?, ?, ?, ?)',
                                 (program_id, student_id, kwargs.get('student_name'),
                                  kwargs.get('education_type'), kwargs.get('student_type'), now[:10]))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE intercultural_programs SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE program_id = ?', (now, program_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已报名该项目'}
        except Exception as e:
            logger.error(f'报名跨文化项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_intercultural_program(self, program_id: str, student_id: int,
                                        **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE program_participants SET completion_status = ?, completion_date = ?, evaluation = ? WHERE program_id = ? AND student_id = ? AND completion_status = ?',
                                 ('completed', now[:10], kwargs.get('evaluation'), program_id, student_id, 'participating'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '参与记录不存在或已完成'}
        except Exception as e:
            logger.error(f'完成跨文化项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_intercultural_programs(self, program_type: str = None,
                                     education_type: str = None,
                                     region: str = None, page: int = 1,
                                     page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM intercultural_programs WHERE 1=1'
                params = []
                if program_type:
                    query += ' AND program_type = ?'
                    params.append(program_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if region:
                    query += ' AND region = ?'
                    params.append(region)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                programs = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'programs': programs, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取跨文化项目列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 国际认证 ==========

    def create_international_certification(self, cert_type: str, **kwargs) -> Dict[str, Any]:
        try:
            cert_id = f"icr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = INTERNATIONAL_CERTIFICATIONS.get(cert_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO international_certifications (
                            cert_id, cert_type, cert_name, education_type,
                            grade_level, issuing_body, valid_from,
                            valid_until, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (cert_id, cert_type, kwargs.get('cert_name', config.get('name')),
                          kwargs.get('education_type'), kwargs.get('grade_level'),
                          kwargs.get('issuing_body'), kwargs.get('valid_from', now[:10]),
                          kwargs.get('valid_until'), now, now))
                    conn.commit()
                    logger.info(f'创建国际认证: {cert_type} ({cert_id})')
                    return {'success': True, 'cert_id': cert_id}
        except Exception as e:
            logger.error(f'创建国际认证失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_certification_result(self, student_id: int, cert_id: str, cert_type: str,
                                     exam_date: str, result: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"crr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            certificate_no = f"ICC{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}" if result == 'pass' else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO certification_records (
                            record_id, student_id, cert_id, cert_type,
                            education_type, exam_date, result, score,
                            certificate_no, certificate_url, issued_date,
                            valid_until, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (record_id, student_id, cert_id, cert_type,
                          kwargs.get('education_type'), exam_date, result,
                          kwargs.get('score'), certificate_no,
                          kwargs.get('certificate_url'),
                          kwargs.get('issued_date', now[:10]) if result == 'pass' else None,
                          kwargs.get('valid_until'), 'completed'))
                    conn.commit()
                    return {'success': True, 'record_id': record_id, 'certificate_no': certificate_no}
        except Exception as e:
            logger.error(f'记录认证结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def verify_certification(self, certificate_no: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM certification_records WHERE certificate_no = ? AND result = ?', (certificate_no, 'pass'))
                record = cursor.fetchone()
                if record:
                    return {'success': True, 'valid': True, 'record': dict(record)}
                return {'success': True, 'valid': False, 'error': '证书不存在或已失效'}
        except Exception as e:
            logger.error(f'验证证书失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_certification_records(self, student_id: int = None, cert_type: str = None,
                                    education_type: str = None, page: int = 1,
                                    page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM certification_records WHERE 1=1'
                params = []
                if student_id:
                    query += ' AND student_id = ?'
                    params.append(student_id)
                if cert_type:
                    query += ' AND cert_type = ?'
                    params.append(cert_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY exam_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取认证记录列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 ==========

    def get_internationalization_stats(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                stats = {}
                if education_type:
                    cursor.execute('SELECT COUNT(*) FROM international_programs WHERE education_type = ?', (education_type,))
                    stats['total_programs'] = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM international_courses WHERE status = "active" AND education_type = ?', (education_type,))
                    stats['total_courses'] = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM exchange_students WHERE education_type = ?', (education_type,))
                    stats['total_exchange_students'] = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM overseas_students WHERE status = "active" AND education_type = ?', (education_type,))
                    stats['total_overseas_students'] = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM international_exams WHERE education_type = ?', (education_type,))
                    stats['total_exams'] = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM study_abroad WHERE education_type = ?', (education_type,))
                    stats['total_study_abroad'] = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM intercultural_programs WHERE education_type = ?', (education_type,))
                    stats['total_intercultural_programs'] = cursor.fetchone()[0]
                else:
                    cursor.execute('SELECT COUNT(*) FROM international_programs')
                    stats['total_programs'] = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM international_courses WHERE status = "active"')
                    stats['total_courses'] = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM exchange_students')
                    stats['total_exchange_students'] = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM overseas_students WHERE status = "active"')
                    stats['total_overseas_students'] = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM international_exams')
                    stats['total_exams'] = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM study_abroad')
                    stats['total_study_abroad'] = cursor.fetchone()[0]
                    cursor.execute('SELECT COUNT(*) FROM intercultural_programs')
                    stats['total_intercultural_programs'] = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM partner_institutions WHERE status = "active"')
                stats['total_partners'] = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM international_certifications WHERE status = "active"')
                stats['total_certifications'] = cursor.fetchone()[0]
                cursor.execute('SELECT target_region, COUNT(*) as cnt FROM study_abroad WHERE target_region IS NOT NULL GROUP BY target_region ORDER BY cnt DESC LIMIT 5')
                stats['top_regions'] = [{'region': r[0], 'count': r[1]} for r in cursor.fetchall()]
                cursor.execute('SELECT exam_type, COUNT(*) as cnt FROM exam_registrations WHERE status = "completed" GROUP BY exam_type ORDER BY cnt DESC LIMIT 5')
                stats['popular_exams'] = [{'exam_type': e[0], 'count': e[1]} for e in cursor.fetchall()]
                return {'success': True, 'stats': stats}
        except Exception as e:
            logger.error(f'获取国际化统计数据失败: {e}')
            return {'success': False, 'error': str(e)}
