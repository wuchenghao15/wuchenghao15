#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育评估与认证服务 (v15.12.0)
====================================
提供学校认证、专业评估、课程认证、教师认证、质量保证、国际认证等综合管理服务。

核心能力：
1. 认证项目管理 - 项目创建、状态管理、流程配置、进度追踪
2. 认证标准 - 标准制定、维度管理、指标体系、版本控制
3. 学校认证 - 认证申请、资格审查、实地考察、评审决策、证书颁发
4. 专业认证 - 专业评估、达标审核、持续改进、周期复审
5. 课程认证 - 课程评估、质量认证、等级评定、有效期管理
6. 教师认证 - 资格认证、能力评估、培训记录、证书管理
7. 评估流程 - 申请受理、材料审核、专家评审、现场考察、结果公示
8. 证书管理 - 证书颁发、查询验证、有效期管理、补发换发
9. 国际认证 - 国际标准对接、国际机构合作、认证互认、国际化评估
10. 质量保证 - 质量管理体系、质量监控、质量改进、内审机制
11. 统计分析 - 认证数据统计、趋势分析、报表生成
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_accreditation_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationAccreditation')


# ========== 认证配置 ==========

ACCREDITATION_TYPES = {
    'school': {'name': '学校认证', 'education_types': ['k12', 'adult']},
    'program': {'name': '专业认证', 'education_types': ['k12', 'adult']},
    'course': {'name': '课程认证', 'education_types': ['k12', 'adult']},
    'teacher': {'name': '教师认证', 'education_types': ['k12', 'adult']},
    'project': {'name': '项目认证', 'education_types': ['k12', 'adult']},
    'international': {'name': '国际认证', 'education_types': ['k12', 'adult']}
}

ACCREDITATION_BODIES = {
    'education_dept': {'name': '教育部门', 'level': 'government'},
    'professional_association': {'name': '专业协会', 'level': 'industry'},
    'international_org': {'name': '国际组织', 'level': 'international'},
    'third_party': {'name': '第三方评估机构', 'level': 'independent'}
}

STANDARDS_LEVELS = {
    'national': {'name': '国家级', 'priority': 1},
    'provincial': {'name': '省级', 'priority': 2},
    'municipal': {'name': '市级', 'priority': 3},
    'industry': {'name': '行业标准', 'priority': 4},
    'international': {'name': '国际标准', 'priority': 0}
}

ASSESSMENT_DIMENSIONS = {
    'facilities': {'name': '办学条件', 'weight': 0.15, 'education_types': ['k12', 'adult']},
    'faculty': {'name': '师资力量', 'weight': 0.20, 'education_types': ['k12', 'adult']},
    'teaching_quality': {'name': '教学质量', 'weight': 0.25, 'education_types': ['k12', 'adult']},
    'research': {'name': '科研水平', 'weight': 0.12, 'education_types': ['adult']},
    'management': {'name': '管理水平', 'weight': 0.13, 'education_types': ['k12', 'adult']},
    'student_development': {'name': '学生发展', 'weight': 0.10, 'education_types': ['k12', 'adult']},
    'social_reputation': {'name': '社会声誉', 'weight': 0.05, 'education_types': ['k12', 'adult']}
}

ACCREDITATION_STATUS = {
    'unaccredited': {'name': '未认证', 'description': '尚未申请或未通过认证'},
    'applying': {'name': '申请中', 'description': '已提交认证申请，正在审核'},
    'accredited': {'name': '认证通过', 'description': '已获得认证资格'},
    'expired': {'name': '认证过期', 'description': '认证有效期已过'},
    'revoked': {'name': '认证撤销', 'description': '认证资格被撤销'},
    'reviewing': {'name': '复审中', 'description': '正在进行周期性复审'}
}

CERTIFICATION_TYPES = {
    'accreditation_certificate': {'name': '认证证书', 'validity_required': True},
    'assessment_report': {'name': '评估报告', 'validity_required': False},
    'qualification_proof': {'name': '合格证明', 'validity_required': True},
    'excellence_rating': {'name': '优秀等级', 'validity_required': True},
    'international_recognition': {'name': '国际认可', 'validity_required': True}
}

REVIEW_CYCLES = {
    '3y': {'name': '3年', 'description': '三年复审一次'},
    '5y': {'name': '5年', 'description': '五年复审一次'},
    '6y': {'name': '6年', 'description': '六年复审一次'},
    '8y': {'name': '8年', 'description': '八年复审一次'},
    '10y': {'name': '10年', 'description': '十年复审一次'}
}


class EducationAccreditationService:
    """教育评估与认证服务"""

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
                    CREATE TABLE IF NOT EXISTS accreditation_programs (
                        program_id TEXT PRIMARY KEY,
                        program_name TEXT NOT NULL,
                        accreditation_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        description TEXT,
                        standards_level TEXT,
                        review_cycle TEXT DEFAULT '5y',
                        start_date TEXT,
                        end_date TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS accreditation_standards (
                        standard_id TEXT PRIMARY KEY,
                        standard_name TEXT NOT NULL,
                        standards_level TEXT,
                        education_type TEXT,
                        description TEXT,
                        dimensions TEXT,
                        version TEXT DEFAULT '1.0',
                        effective_date TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS assessment_criteria (
                        criteria_id TEXT PRIMARY KEY,
                        standard_id TEXT NOT NULL,
                        dimension TEXT NOT NULL,
                        criteria_name TEXT NOT NULL,
                        weight REAL DEFAULT 0.1,
                        passing_score REAL DEFAULT 60,
                        description TEXT,
                        education_type TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS school_accreditations (
                        accreditation_id TEXT PRIMARY KEY,
                        school_id INTEGER NOT NULL,
                        school_name TEXT,
                        program_id TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        application_date TEXT,
                        review_date TEXT,
                        decision_date TEXT,
                        status TEXT DEFAULT 'applying',
                        overall_score REAL,
                        decision TEXT,
                        certificate_no TEXT,
                        certificate_url TEXT,
                        valid_from TEXT,
                        valid_until TEXT,
                        next_review_date TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS program_accreditations (
                        accreditation_id TEXT PRIMARY KEY,
                        program_id TEXT NOT NULL,
                        program_name TEXT,
                        school_id INTEGER NOT NULL,
                        education_type TEXT NOT NULL,
                        application_date TEXT,
                        review_date TEXT,
                        decision_date TEXT,
                        status TEXT DEFAULT 'applying',
                        overall_score REAL,
                        decision TEXT,
                        certificate_no TEXT,
                        valid_from TEXT,
                        valid_until TEXT,
                        next_review_date TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS course_accreditations (
                        accreditation_id TEXT PRIMARY KEY,
                        course_id INTEGER NOT NULL,
                        course_name TEXT,
                        school_id INTEGER NOT NULL,
                        education_type TEXT NOT NULL,
                        application_date TEXT,
                        review_date TEXT,
                        decision_date TEXT,
                        status TEXT DEFAULT 'applying',
                        rating TEXT,
                        decision TEXT,
                        certificate_no TEXT,
                        valid_from TEXT,
                        valid_until TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS teacher_certifications (
                        certification_id TEXT PRIMARY KEY,
                        teacher_id INTEGER NOT NULL,
                        teacher_name TEXT,
                        school_id INTEGER NOT NULL,
                        education_type TEXT NOT NULL,
                        certification_type TEXT,
                        issue_date TEXT,
                        valid_until TEXT,
                        status TEXT DEFAULT 'active',
                        certificate_no TEXT,
                        certificate_url TEXT,
                        training_hours INTEGER DEFAULT 0,
                        last_renewal_date TEXT,
                        next_renewal_date TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS assessment_reports (
                        report_id TEXT PRIMARY KEY,
                        accreditation_id TEXT NOT NULL,
                        report_type TEXT,
                        assessor_id INTEGER,
                        assessor_name TEXT,
                        assessment_date TEXT,
                        overall_score REAL,
                        detailed_scores TEXT,
                        findings TEXT,
                        recommendations TEXT,
                        status TEXT DEFAULT 'draft',
                        approved INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS accreditation_teams (
                        team_id TEXT PRIMARY KEY,
                        team_name TEXT NOT NULL,
                        accreditation_type TEXT,
                        education_type TEXT,
                        leader_id INTEGER,
                        leader_name TEXT,
                        members TEXT,
                        expertise TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS site_visits (
                        visit_id TEXT PRIMARY KEY,
                        accreditation_id TEXT NOT NULL,
                        school_id INTEGER NOT NULL,
                        team_id TEXT,
                        visit_date TEXT,
                        duration INTEGER DEFAULT 1,
                        activities TEXT,
                        observations TEXT,
                        photos TEXT,
                        report_url TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS evidence_documents (
                        document_id TEXT PRIMARY KEY,
                        accreditation_id TEXT NOT NULL,
                        document_name TEXT NOT NULL,
                        document_type TEXT,
                        file_url TEXT,
                        uploaded_by INTEGER,
                        upload_date TEXT,
                        verified INTEGER DEFAULT 0,
                        verified_by INTEGER,
                        verified_date TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS accreditation_decisions (
                        decision_id TEXT PRIMARY KEY,
                        accreditation_id TEXT NOT NULL,
                        decision_type TEXT,
                        decision TEXT,
                        decision_date TEXT,
                        committee_name TEXT,
                        members TEXT,
                        remarks TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS certification_management (
                        cert_id TEXT PRIMARY KEY,
                        certificate_no TEXT UNIQUE NOT NULL,
                        certification_type TEXT,
                        holder_id INTEGER NOT NULL,
                        holder_name TEXT,
                        education_type TEXT,
                        issue_date TEXT,
                        valid_from TEXT,
                        valid_until TEXT,
                        status TEXT DEFAULT 'active',
                        revoked INTEGER DEFAULT 0,
                        revoked_reason TEXT,
                        reissued_from TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS international_accreditations (
                        acc_id TEXT PRIMARY KEY,
                        school_id INTEGER NOT NULL,
                        school_name TEXT,
                        education_type TEXT NOT NULL,
                        international_body TEXT,
                        accreditation_name TEXT,
                        application_date TEXT,
                        approval_date TEXT,
                        valid_until TEXT,
                        status TEXT DEFAULT 'applying',
                        recognition_level TEXT,
                        equivalence TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS quality_assurance_records (
                        record_id TEXT PRIMARY KEY,
                        school_id INTEGER NOT NULL,
                        education_type TEXT NOT NULL,
                        qa_type TEXT,
                        audit_date TEXT,
                        auditor_id INTEGER,
                        auditor_name TEXT,
                        findings TEXT,
                        corrective_actions TEXT,
                        status TEXT DEFAULT 'open',
                        completed_date TEXT,
                        created_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('教育评估与认证服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 认证项目管理 ==========

    def create_accreditation_program(self, program_name: str, accreditation_type: str,
                                      education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            if education_type not in ACCREDITATION_TYPES.get(accreditation_type, {}).get('education_types', []):
                return {'success': False, 'error': f'{education_type}教育不支持{accreditation_type}认证类型'}
            program_id = f"apr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO accreditation_programs (
                            program_id, program_name, accreditation_type,
                            education_type, description, standards_level,
                            review_cycle, start_date, end_date, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (program_id, program_name, accreditation_type, education_type,
                          kwargs.get('description'), kwargs.get('standards_level'),
                          kwargs.get('review_cycle', '5y'), kwargs.get('start_date'),
                          kwargs.get('end_date'), now, now))
                    conn.commit()
                    logger.info(f'创建认证项目: {program_name} ({program_id})')
                    return {'success': True, 'program_id': program_id}
        except Exception as e:
            logger.error(f'创建认证项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_program_status(self, program_id: str, status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE accreditation_programs SET status = ?, updated_at = ? WHERE program_id = ?',
                                 (status, now, program_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '认证项目不存在'}
        except Exception as e:
            logger.error(f'更新项目状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_program_detail(self, program_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM accreditation_programs WHERE program_id = ?', (program_id,))
                program = cursor.fetchone()
                if program:
                    return {'success': True, 'program': dict(program)}
                return {'success': False, 'error': '认证项目不存在'}
        except Exception as e:
            logger.error(f'获取项目详情失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_programs(self, accreditation_type: str = None, education_type: str = None,
                      status: str = 'active', page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM accreditation_programs WHERE 1=1'
                params = []
                if accreditation_type:
                    query += ' AND accreditation_type = ?'
                    params.append(accreditation_type)
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
            logger.error(f'获取项目列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 认证标准 ==========

    def create_standard(self, standard_name: str, education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            standard_id = f"std_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            dimensions = json.dumps([d for d in kwargs.get('dimensions', [])
                                    if education_type in ASSESSMENT_DIMENSIONS.get(d, {}).get('education_types', [])])
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO accreditation_standards (
                            standard_id, standard_name, standards_level,
                            education_type, description, dimensions,
                            version, effective_date, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (standard_id, standard_name, kwargs.get('standards_level'),
                          education_type, kwargs.get('description'), dimensions,
                          kwargs.get('version', '1.0'), kwargs.get('effective_date'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建认证标准: {standard_name} ({standard_id})')
                    return {'success': True, 'standard_id': standard_id}
        except Exception as e:
            logger.error(f'创建认证标准失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_criteria(self, standard_id: str, dimension: str, criteria_name: str,
                     **kwargs) -> Dict[str, Any]:
        try:
            criteria_id = f"crt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM accreditation_standards WHERE standard_id = ?', (standard_id,))
                    std = cursor.fetchone()
                    if not std:
                        return {'success': False, 'error': '认证标准不存在'}
                    if std[0] not in ASSESSMENT_DIMENSIONS.get(dimension, {}).get('education_types', []):
                        return {'success': False, 'error': f'{std[0]}教育不支持{dimension}评估维度'}
                    cursor.execute('''
                        INSERT INTO assessment_criteria (
                            criteria_id, standard_id, dimension, criteria_name,
                            weight, passing_score, description, education_type, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (criteria_id, standard_id, dimension, criteria_name,
                          kwargs.get('weight', 0.1), kwargs.get('passing_score', 60),
                          kwargs.get('description'), std[0], now))
                    conn.commit()
                    return {'success': True, 'criteria_id': criteria_id}
        except Exception as e:
            logger.error(f'添加评估指标失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_standard_criteria(self, standard_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM accreditation_standards WHERE standard_id = ?', (standard_id,))
                standard = cursor.fetchone()
                if not standard:
                    return {'success': False, 'error': '认证标准不存在'}
                cursor.execute('SELECT * FROM assessment_criteria WHERE standard_id = ? ORDER BY dimension, criteria_name', (standard_id,))
                criteria = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'standard': dict(standard), 'criteria': criteria}
        except Exception as e:
            logger.error(f'获取标准指标失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 学校认证 ==========

    def apply_school_accreditation(self, school_id: int, school_name: str,
                                    program_id: str, education_type: str) -> Dict[str, Any]:
        try:
            accreditation_id = f"sch_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT review_cycle FROM accreditation_programs WHERE program_id = ? AND education_type = ?',
                                 (program_id, education_type))
                    program = cursor.fetchone()
                    if not program:
                        return {'success': False, 'error': '认证项目不存在或不支持该教育类型'}
                    review_cycle = program[0]
                    cycle_years = int(review_cycle[:-1])
                    next_review = (datetime.now() + timedelta(days=cycle_years * 365)).strftime('%Y-%m-%d')
                    cursor.execute('''
                        INSERT INTO school_accreditations (
                            accreditation_id, school_id, school_name, program_id,
                            education_type, application_date, status, next_review_date,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'applying', ?, ?, ?)
                    ''', (accreditation_id, school_id, school_name, program_id,
                          education_type, now[:10], next_review, now, now))
                    conn.commit()
                    logger.info(f'学校认证申请: {school_name} ({accreditation_id})')
                    return {'success': True, 'accreditation_id': accreditation_id}
        except Exception as e:
            logger.error(f'学校认证申请失败: {e}')
            return {'success': False, 'error': str(e)}

    def review_school_accreditation(self, accreditation_id: str, overall_score: float,
                                     decision: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'accredited' if decision == 'approve' else 'revoked'
            certificate_no = f"SAC{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}" if decision == 'approve' else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT review_cycle, education_type FROM school_accreditations sa JOIN accreditation_programs ap ON sa.program_id = ap.program_id WHERE sa.accreditation_id = ?', (accreditation_id,))
                    record = cursor.fetchone()
                    if not record:
                        return {'success': False, 'error': '学校认证记录不存在'}
                    cycle_years = int(record[0][:-1])
                    valid_until = (datetime.now() + timedelta(days=cycle_years * 365)).strftime('%Y-%m-%d')
                    next_review = valid_until
                    cursor.execute('''
                        UPDATE school_accreditations SET
                            review_date = ?, decision_date = ?, status = ?,
                            overall_score = ?, decision = ?, certificate_no = ?,
                            valid_from = ?, valid_until = ?, next_review_date = ?,
                            updated_at = ?
                        WHERE accreditation_id = ?
                    ''', (now[:10], now[:10], status, overall_score, decision,
                          certificate_no, now[:10], valid_until, next_review, now, accreditation_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'certificate_no': certificate_no}
                    return {'success': False, 'error': '更新失败'}
        except Exception as e:
            logger.error(f'学校认证评审失败: {e}')
            return {'success': False, 'error': str(e)}

    def schedule_site_visit(self, accreditation_id: str, school_id: int,
                             visit_date: str, **kwargs) -> Dict[str, Any]:
        try:
            visit_id = f"svt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO site_visits (
                            visit_id, accreditation_id, school_id, team_id,
                            visit_date, duration, activities, observations,
                            photos, report_url, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (visit_id, accreditation_id, school_id, kwargs.get('team_id'),
                          visit_date, kwargs.get('duration', 1), kwargs.get('activities'),
                          kwargs.get('observations'), kwargs.get('photos'),
                          kwargs.get('report_url'), now))
                    conn.commit()
                    return {'success': True, 'visit_id': visit_id}
        except Exception as e:
            logger.error(f'安排实地考察失败: {e}')
            return {'success': False, 'error': str(e)}

    def upload_evidence(self, accreditation_id: str, document_name: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            document_id = f"evd_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO evidence_documents (
                            document_id, accreditation_id, document_name,
                            document_type, file_url, uploaded_by, upload_date,
                            created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (document_id, accreditation_id, document_name,
                          kwargs.get('document_type'), kwargs.get('file_url'),
                          kwargs.get('uploaded_by'), now[:10], now))
                    conn.commit()
                    return {'success': True, 'document_id': document_id}
        except Exception as e:
            logger.error(f'上传证明材料失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_school_accreditation_status(self, school_id: int, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM school_accreditations WHERE school_id = ?'
                params = [school_id]
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' ORDER BY created_at DESC LIMIT 1'
                cursor.execute(query, params)
                record = cursor.fetchone()
                if record:
                    return {'success': True, 'accreditation': dict(record)}
                return {'success': False, 'error': '学校认证记录不存在'}
        except Exception as e:
            logger.error(f'获取学校认证状态失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 专业认证 ==========

    def apply_program_accreditation(self, program_id: str, program_name: str,
                                     school_id: int, education_type: str) -> Dict[str, Any]:
        try:
            accreditation_id = f"pgr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO program_accreditations (
                            accreditation_id, program_id, program_name, school_id,
                            education_type, application_date, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'applying', ?, ?)
                    ''', (accreditation_id, program_id, program_name, school_id,
                          education_type, now[:10], now, now))
                    conn.commit()
                    logger.info(f'专业认证申请: {program_name} ({accreditation_id})')
                    return {'success': True, 'accreditation_id': accreditation_id}
        except Exception as e:
            logger.error(f'专业认证申请失败: {e}')
            return {'success': False, 'error': str(e)}

    def assess_program(self, accreditation_id: str, overall_score: float,
                       **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            decision = 'approve' if overall_score >= 60 else 'reject'
            status = 'accredited' if decision == 'approve' else 'revoked'
            certificate_no = f"PAC{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}" if decision == 'approve' else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE program_accreditations SET
                            review_date = ?, decision_date = ?, status = ?,
                            overall_score = ?, decision = ?, certificate_no = ?,
                            valid_from = ?, valid_until = ?, next_review_date = ?,
                            updated_at = ?
                        WHERE accreditation_id = ?
                    ''', (now[:10], now[:10], status, overall_score, decision,
                          certificate_no, now[:10], kwargs.get('valid_until'),
                          kwargs.get('next_review_date'), now, accreditation_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '更新失败'}
        except Exception as e:
            logger.error(f'专业评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def renew_program_accreditation(self, accreditation_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT valid_until FROM program_accreditations WHERE accreditation_id = ?', (accreditation_id,))
                    record = cursor.fetchone()
                    if not record:
                        return {'success': False, 'error': '专业认证记录不存在'}
                    new_valid_until = (datetime.now() + timedelta(days=5 * 365)).strftime('%Y-%m-%d')
                    cursor.execute('''
                        UPDATE program_accreditations SET
                            status = 'reviewing', valid_until = ?,
                            next_review_date = ?, updated_at = ?
                        WHERE accreditation_id = ?
                    ''', (new_valid_until, new_valid_until, now, accreditation_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'专业认证续期失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_program_accreditations(self, school_id: int = None, education_type: str = None,
                                     status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM program_accreditations WHERE 1=1'
                params = []
                if school_id:
                    query += ' AND school_id = ?'
                    params.append(school_id)
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
                accreditations = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'accreditations': accreditations, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取专业认证列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 课程认证 ==========

    def apply_course_accreditation(self, course_id: int, course_name: str,
                                    school_id: int, education_type: str) -> Dict[str, Any]:
        try:
            accreditation_id = f"cor_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO course_accreditations (
                            accreditation_id, course_id, course_name, school_id,
                            education_type, application_date, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'applying', ?, ?)
                    ''', (accreditation_id, course_id, course_name, school_id,
                          education_type, now[:10], now, now))
                    conn.commit()
                    logger.info(f'课程认证申请: {course_name} ({accreditation_id})')
                    return {'success': True, 'accreditation_id': accreditation_id}
        except Exception as e:
            logger.error(f'课程认证申请失败: {e}')
            return {'success': False, 'error': str(e)}

    def evaluate_course(self, accreditation_id: str, rating: str,
                        decision: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'accredited' if decision == 'approve' else 'revoked'
            certificate_no = f"CAC{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}" if decision == 'approve' else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE course_accreditations SET
                            review_date = ?, decision_date = ?, status = ?,
                            rating = ?, decision = ?, certificate_no = ?,
                            valid_from = ?, valid_until = ?, updated_at = ?
                        WHERE accreditation_id = ?
                    ''', (now[:10], now[:10], status, rating, decision,
                          certificate_no, now[:10], kwargs.get('valid_until'), now, accreditation_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '更新失败'}
        except Exception as e:
            logger.error(f'课程评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_course_accreditation(self, course_id: int, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM course_accreditations WHERE course_id = ?'
                params = [course_id]
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' ORDER BY created_at DESC LIMIT 1'
                cursor.execute(query, params)
                record = cursor.fetchone()
                if record:
                    return {'success': True, 'accreditation': dict(record)}
                return {'success': False, 'error': '课程认证记录不存在'}
        except Exception as e:
            logger.error(f'获取课程认证失败: {e}')
            return {'success': False, 'error': str(e)}

    def revoke_course_accreditation(self, accreditation_id: str, reason: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE course_accreditations SET status = ?, decision = ?, updated_at = ? WHERE accreditation_id = ?',
                                 ('revoked', reason, now, accreditation_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '课程认证记录不存在'}
        except Exception as e:
            logger.error(f'撤销课程认证失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 教师认证 ==========

    def issue_teacher_certification(self, teacher_id: int, teacher_name: str,
                                     school_id: int, education_type: str,
                                     certification_type: str) -> Dict[str, Any]:
        try:
            certification_id = f"tcr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            certificate_no = f"TEC{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
            valid_until = (datetime.now() + timedelta(days=5 * 365)).strftime('%Y-%m-%d')
            next_renewal = valid_until
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO teacher_certifications (
                            certification_id, teacher_id, teacher_name, school_id,
                            education_type, certification_type, issue_date,
                            valid_until, status, certificate_no, next_renewal_date,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?)
                    ''', (certification_id, teacher_id, teacher_name, school_id,
                          education_type, certification_type, now[:10],
                          valid_until, certificate_no, next_renewal, now, now))
                    conn.commit()
                    logger.info(f'颁发教师证书: {teacher_name} ({certification_id})')
                    return {'success': True, 'certification_id': certification_id, 'certificate_no': certificate_no}
        except Exception as e:
            logger.error(f'颁发教师证书失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_teacher_training(self, certification_id: str, training_hours: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE teacher_certifications SET training_hours = training_hours + ?, updated_at = ? WHERE certification_id = ?',
                                 (training_hours, now, certification_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '教师证书不存在'}
        except Exception as e:
            logger.error(f'更新培训学时失败: {e}')
            return {'success': False, 'error': str(e)}

    def renew_teacher_certification(self, certification_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            valid_until = (datetime.now() + timedelta(days=5 * 365)).strftime('%Y-%m-%d')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE teacher_certifications SET
                            valid_until = ?, last_renewal_date = ?,
                            next_renewal_date = ?, updated_at = ?
                        WHERE certification_id = ?
                    ''', (valid_until, now[:10], valid_until, now, certification_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '教师证书不存在'}
        except Exception as e:
            logger.error(f'教师证书续期失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_teacher_certifications(self, teacher_id: int, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM teacher_certifications WHERE teacher_id = ?'
                params = [teacher_id]
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' ORDER BY issue_date DESC'
                cursor.execute(query, params)
                certifications = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'certifications': certifications}
        except Exception as e:
            logger.error(f'获取教师证书失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 评估流程 ==========

    def create_assessment_report(self, accreditation_id: str, report_type: str,
                                  assessor_id: int, assessor_name: str,
                                  **kwargs) -> Dict[str, Any]:
        try:
            report_id = f"rep_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            detailed_scores = json.dumps(kwargs.get('detailed_scores', {}))
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO assessment_reports (
                            report_id, accreditation_id, report_type,
                            assessor_id, assessor_name, assessment_date,
                            overall_score, detailed_scores, findings,
                            recommendations, status, approved, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', 0, ?, ?)
                    ''', (report_id, accreditation_id, report_type, assessor_id,
                          assessor_name, now[:10], kwargs.get('overall_score'),
                          detailed_scores, kwargs.get('findings'),
                          kwargs.get('recommendations'), now, now))
                    conn.commit()
                    return {'success': True, 'report_id': report_id}
        except Exception as e:
            logger.error(f'创建评估报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_report(self, report_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE assessment_reports SET status = ?, approved = 1, updated_at = ? WHERE report_id = ?',
                                 ('approved', now, report_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '评估报告不存在'}
        except Exception as e:
            logger.error(f'审批评估报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_accreditation_team(self, team_name: str, accreditation_type: str,
                                   education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            team_id = f"atm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            members = json.dumps(kwargs.get('members', []))
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO accreditation_teams (
                            team_id, team_name, accreditation_type,
                            education_type, leader_id, leader_name,
                            members, expertise, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (team_id, team_name, accreditation_type, education_type,
                          kwargs.get('leader_id'), kwargs.get('leader_name'),
                          members, kwargs.get('expertise'), now, now))
                    conn.commit()
                    return {'success': True, 'team_id': team_id}
        except Exception as e:
            logger.error(f'创建评审团队失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_decision(self, accreditation_id: str, decision_type: str,
                         decision: str, **kwargs) -> Dict[str, Any]:
        try:
            decision_id = f"dcs_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            members = json.dumps(kwargs.get('members', []))
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO accreditation_decisions (
                            decision_id, accreditation_id, decision_type,
                            decision, decision_date, committee_name,
                            members, remarks, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (decision_id, accreditation_id, decision_type, decision,
                          now[:10], kwargs.get('committee_name'), members,
                          kwargs.get('remarks'), now))
                    conn.commit()
                    return {'success': True, 'decision_id': decision_id}
        except Exception as e:
            logger.error(f'记录评审决策失败: {e}')
            return {'success': False, 'error': str(e)}

    def verify_evidence(self, document_id: str, verified_by: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE evidence_documents SET verified = 1, verified_by = ?, verified_date = ? WHERE document_id = ?',
                                 (verified_by, now[:10], document_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '证明材料不存在'}
        except Exception as e:
            logger.error(f'验证证明材料失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 证书管理 ==========

    def issue_certificate(self, certification_type: str, holder_id: int,
                           holder_name: str, education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            cert_id = f"cmg_{uuid.uuid4().hex[:12]}"
            certificate_no = f"CERT{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
            now = datetime.now().isoformat()
            valid_until = kwargs.get('valid_until')
            if CERTIFICATION_TYPES.get(certification_type, {}).get('validity_required') and not valid_until:
                valid_until = (datetime.now() + timedelta(days=5 * 365)).strftime('%Y-%m-%d')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO certification_management (
                            cert_id, certificate_no, certification_type,
                            holder_id, holder_name, education_type,
                            issue_date, valid_from, valid_until, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (cert_id, certificate_no, certification_type, holder_id,
                          holder_name, education_type, now[:10], now[:10],
                          valid_until, now, now))
                    conn.commit()
                    return {'success': True, 'cert_id': cert_id, 'certificate_no': certificate_no}
        except Exception as e:
            logger.error(f'颁发证书失败: {e}')
            return {'success': False, 'error': str(e)}

    def verify_certificate(self, certificate_no: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM certification_management WHERE certificate_no = ?', (certificate_no,))
                cert = cursor.fetchone()
                if cert:
                    is_valid = cert['status'] == 'active' and not cert['revoked']
                    return {'success': True, 'certificate': dict(cert), 'is_valid': is_valid}
                return {'success': False, 'error': '证书不存在'}
        except Exception as e:
            logger.error(f'验证证书失败: {e}')
            return {'success': False, 'error': str(e)}

    def revoke_certificate(self, certificate_no: str, reason: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE certification_management SET status = ?, revoked = 1, revoked_reason = ?, updated_at = ? WHERE certificate_no = ?',
                                 ('revoked', reason, now, certificate_no))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '证书不存在'}
        except Exception as e:
            logger.error(f'撤销证书失败: {e}')
            return {'success': False, 'error': str(e)}

    def reissue_certificate(self, certificate_no: str) -> Dict[str, Any]:
        try:
            new_certificate_no = f"CERT{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT cert_id, certification_type, holder_id, holder_name, education_type, valid_from, valid_until FROM certification_management WHERE certificate_no = ?', (certificate_no,))
                    cert = cursor.fetchone()
                    if not cert:
                        return {'success': False, 'error': '证书不存在'}
                    new_cert_id = f"cmg_{uuid.uuid4().hex[:12]}"
                    cursor.execute('''
                        INSERT INTO certification_management (
                            cert_id, certificate_no, certification_type,
                            holder_id, holder_name, education_type,
                            issue_date, valid_from, valid_until, status,
                            reissued_from, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
                    ''', (new_cert_id, new_certificate_no, cert[1], cert[2],
                          cert[3], cert[4], now[:10], cert[5], cert[6],
                          certificate_no, now, now))
                    cursor.execute('UPDATE certification_management SET status = ?, updated_at = ? WHERE certificate_no = ?',
                                 ('reissued', now, certificate_no))
                    conn.commit()
                    return {'success': True, 'new_certificate_no': new_certificate_no}
        except Exception as e:
            logger.error(f'补发证书失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 国际认证 ==========

    def apply_international_accreditation(self, school_id: int, school_name: str,
                                           education_type: str, international_body: str,
                                           **kwargs) -> Dict[str, Any]:
        try:
            acc_id = f"int_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO international_accreditations (
                            acc_id, school_id, school_name, education_type,
                            international_body, accreditation_name,
                            application_date, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'applying', ?, ?)
                    ''', (acc_id, school_id, school_name, education_type,
                          international_body, kwargs.get('accreditation_name'),
                          now[:10], now, now))
                    conn.commit()
                    logger.info(f'国际认证申请: {school_name} ({acc_id})')
                    return {'success': True, 'acc_id': acc_id}
        except Exception as e:
            logger.error(f'国际认证申请失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_international_accreditation(self, acc_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE international_accreditations SET
                            approval_date = ?, valid_until = ?, status = ?,
                            recognition_level = ?, equivalence = ?,
                            updated_at = ?
                        WHERE acc_id = ?
                    ''', (now[:10], kwargs.get('valid_until'), 'accredited',
                          kwargs.get('recognition_level'), kwargs.get('equivalence'),
                          now, acc_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '国际认证记录不存在'}
        except Exception as e:
            logger.error(f'国际认证审批失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_international_recognition(self, school_id: int, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM international_accreditations WHERE school_id = ?'
                params = [school_id]
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'accreditations': records}
        except Exception as e:
            logger.error(f'获取国际认证失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 质量保证 ==========

    def create_qa_audit(self, school_id: int, education_type: str, qa_type: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"qa_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO quality_assurance_records (
                            record_id, school_id, education_type, qa_type,
                            audit_date, auditor_id, auditor_name, findings,
                            corrective_actions, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?)
                    ''', (record_id, school_id, education_type, qa_type,
                          now[:10], kwargs.get('auditor_id'), kwargs.get('auditor_name'),
                          kwargs.get('findings'), kwargs.get('corrective_actions'), now))
                    conn.commit()
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'创建质量审计记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_qa_status(self, record_id: str, status: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE quality_assurance_records SET
                            status = ?, completed_date = ?, updated_at = ?
                        WHERE record_id = ?
                    ''', (status, kwargs.get('completed_date', now[:10]), now, record_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '质量保证记录不存在'}
        except Exception as e:
            logger.error(f'更新质量保证状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_qa_records(self, school_id: int, education_type: str = None,
                       status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM quality_assurance_records WHERE 1=1'
                params = []
                if school_id:
                    query += ' AND school_id = ?'
                    params.append(school_id)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY audit_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取质量保证记录失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 ==========

    def get_accreditation_statistics(self, education_type: str = None,
                                     period: str = 'all') -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                result = {}
                for acc_type, acc_info in ACCREDITATION_TYPES.items():
                    if education_type and education_type not in acc_info.get('education_types', []):
                        continue
                    table_map = {
                        'school': 'school_accreditations',
                        'program': 'program_accreditations',
                        'course': 'course_accreditations',
                        'teacher': 'teacher_certifications',
                        'international': 'international_accreditations'
                    }
                    table = table_map.get(acc_type)
                    if not table:
                        continue
                    query = f'SELECT status, COUNT(*) FROM {table} WHERE 1=1'
                    params = []
                    if education_type:
                        query += ' AND education_type = ?'
                        params.append(education_type)
                    query += ' GROUP BY status'
                    cursor.execute(query, params)
                    stats = cursor.fetchall()
                    result[acc_type] = {s[0]: s[1] for s in stats}
                query = 'SELECT COUNT(*) FROM certification_management WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                result['total_certificates'] = cursor.fetchone()[0]
                query = 'SELECT COUNT(*) FROM quality_assurance_records WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                result['total_qa_records'] = cursor.fetchone()[0]
                return {'success': True, 'statistics': result}
        except Exception as e:
            logger.error(f'获取认证统计失败: {e}')
            return {'success': False, 'error': str(e)}