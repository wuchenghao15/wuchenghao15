from core.db_path import get_db_path as _mtscos_get_db_path
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 国际交流服务 (v15.7.0)
====================================
提供留学项目、交换生、国际合作伙伴和外事管理等综合服务。

核心能力：
1. 留学项目 - 留学申请、院校推荐、材料管理
2. 交换生 - 交换项目、选派管理、学分转换
3. 国际合作 - 合作院校、协议管理、联合培养
4. 外事管理 - 出访审批、外宾接待、外事活动
5. 语言考试 - 托福/雅思/JLPT等考试管理
6. 奖学金 - 国际奖学金申请与管理
7. 成人国际 - 成人教育国际交流
8. K12国际 - 中小学国际交流项目
"""
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'international_exchange_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('IntlExchange')


# ========== 国际交流配置 ==========

# 留学类型
STUDY_ABROAD_TYPES = {
    'degree': {'name': '学位留学', 'duration': '2-4年', 'degree': True},
    'exchange': {'name': '交换留学', 'duration': '1学期-1年', 'degree': False},
    'short_term': {'name': '短期游学', 'duration': '2-12周', 'degree': False},
    'summer': {'name': '暑期项目', 'duration': '4-8周', 'degree': False},
    'winter': {'name': '寒假项目', 'duration': '2-4周', 'degree': False},
    'language': {'name': '语言研修', 'duration': '3-12个月', 'degree': False},
    'internship': {'name': '海外实习', 'duration': '3-6个月', 'degree': False},
    'joint_degree': {'name': '联合学位', 'duration': '2-3年', 'degree': True}
}

# 目标地区
REGIONS = {
    'north_america': {'name': '北美', 'countries': ['美国', '加拿大']},
    'europe': {'name': '欧洲', 'countries': ['英国', '德国', '法国', '荷兰', '瑞典']},
    'asia': {'name': '亚洲', 'countries': ['日本', '韩国', '新加坡', '马来西亚', '泰国']},
    'oceania': {'name': '大洋洲', 'countries': ['澳大利亚', '新西兰']},
    'other': {'name': '其他', 'countries': ['其他']}
}

# 合作类型
PARTNERSHIP_TYPES = {
    'sister_school': {'name': '姐妹学校', 'description': '全面合作关系'},
    'exchange': {'name': '交换项目', 'description': '学生交换协议'},
    'joint_degree': {'name': '联合学位', 'description': '双学位项目'},
    'research': {'name': '科研合作', 'description': '联合研究项目'},
    'language': {'name': '语言项目', 'description': '语言培训合作'},
    'teacher_exchange': {'name': '教师交流', 'description': '教师互访项目'},
    'articulation': {'name': '升学衔接', 'description': '课程衔接协议'}
}

# 申请状态
APPLICATION_STATUS = {
    'draft': {'name': '草稿', 'color': '#d9d9d9'},
    'submitted': {'name': '已提交', 'color': '#1890ff'},
    'reviewing': {'name': '审核中', 'color': '#faad14'},
    'nominated': {'name': '已推荐', 'color': '#1890ff'},
    'accepted': {'name': '已录取', 'color': '#52c41a'},
    'rejected': {'name': '未录取', 'color': '#f5222d'},
    'withdrawn': {'name': '已撤回', 'color': '#8c8c8c'},
    'enrolled': {'name': '已入学', 'color': '#52c41a'},
    'completed': {'name': '已完成', 'color': '#52c41a'}
}

# 语言考试类型
LANGUAGE_EXAMS = {
    'toefl': {'name': 'TOEFL', 'full_score': 120, 'valid_years': 2},
    'ielts': {'name': 'IELTS', 'full_score': 9, 'valid_years': 2},
    'jlpt': {'name': 'JLPT', 'levels': ['N5', 'N4', 'N3', 'N2', 'N1'], 'valid_years': 3},
    'jtest': {'name': 'J.TEST', 'full_score': 1000, 'valid_years': 3},
    'toeic': {'name': 'TOEIC', 'full_score': 990, 'valid_years': 2},
    'gre': {'name': 'GRE', 'full_score': 340, 'valid_years': 5},
    'gmat': {'name': 'GMAT', 'full_score': 800, 'valid_years': 5},
    'hsk': {'name': 'HSK', 'levels': ['1', '2', '3', '4', '5', '6'], 'valid_years': 3}
}

# 出访类型
VISIT_TYPES = {
    'conference': {'name': '学术会议', 'requires_approval': True},
    'research': {'name': '合作研究', 'requires_approval': True},
    'lecture': {'name': '讲学交流', 'requires_approval': True},
    'training': {'name': '培训进修', 'requires_approval': True},
    'competition': {'name': '国际竞赛', 'requires_approval': True},
    'exchange': {'name': '交换项目', 'requires_approval': True},
    'inspection': {'name': '考察访问', 'requires_approval': True},
    'other': {'name': '其他', 'requires_approval': True}
}

# 奖学金类型
SCHOLARSHIP_TYPES = {
    'csc': {'name': '国家留学基金', 'source': '政府', 'coverage': '全额'},
    'government': {'name': '外国政府奖学金', 'source': '外国政府', 'coverage': '全额'},
    'university': {'name': '院校奖学金', 'source': '目标院校', 'coverage': '部分/全额'},
    'enterprise': {'name': '企业奖学金', 'source': '企业', 'coverage': '部分'},
    'organization': {'name': '机构奖学金', 'source': '国际组织', 'coverage': '部分/全额'},
    'self_funded': {'name': '自费', 'source': '个人', 'coverage': '无'}
}


class InternationalExchangeService:
    """国际交流服务"""

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
                    CREATE TABLE IF NOT EXISTS partner_institutions (
                        partner_id TEXT PRIMARY KEY,
                        institution_name TEXT NOT NULL,
        country TEXT,
                        region TEXT,
                        partnership_type TEXT,
                        agreement_start TEXT,
                        agreement_end TEXT,
                        contact_person TEXT,
                        contact_email TEXT,
                        contact_phone TEXT,
                        website TEXT,
                        description TEXT,
                        quota_per_year INTEGER DEFAULT 5,
                        is_active INTEGER DEFAULT 1,
                        logo_url TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS study_programs (
                        program_id TEXT PRIMARY KEY,
                        program_name TEXT NOT NULL,
                        partner_id TEXT,
                        institution_name TEXT,
                        country TEXT,
                        program_type TEXT NOT NULL,
                        duration TEXT,
                        language TEXT,
                        tuition_fee REAL,
                        application_deadline TEXT,
                        start_date TEXT,
                        credits INTEGER,
                        description TEXT,
                        requirements TEXT,
                        education_type TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS exchange_applications (
                        application_id TEXT PRIMARY KEY,
                        program_id TEXT NOT NULL,
                        program_name TEXT,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        education_type TEXT,
                        study_type TEXT,
                        target_country TEXT,
                        target_institution TEXT,
                        apply_date TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        status TEXT DEFAULT 'draft',
                        statement TEXT,
                        transcript_url TEXT,
                        recommendation_url TEXT,
                        language_score TEXT,
                        language_exam_type TEXT,
                        reviewed_by INTEGER,
                        reviewed_at TEXT,
                        review_comment TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS language_exam_records (
                        record_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        exam_type TEXT NOT NULL,
                        exam_date TEXT,
                        score TEXT,
                        level TEXT,
                        valid_until TEXT,
                        certificate_url TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS outbound_visits (
                        visit_id TEXT PRIMARY KEY,
                        visitor_id INTEGER NOT NULL,
                        visitor_name TEXT,
        visitor_type TEXT,
                        visit_type TEXT,
                        destination_country TEXT,
                        destination_institution TEXT,
                        purpose TEXT,
                        departure_date TEXT,
                        return_date TEXT,
                        funding_source TEXT,
                        budget REAL,
                        status TEXT DEFAULT 'pending',
                        approved_by INTEGER,
                        approved_at TEXT,
                        report_url TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS inbound_visits (
                        visit_id TEXT PRIMARY KEY,
                        visitor_name TEXT NOT NULL,
                        visitor_title TEXT,
                        visitor_institution TEXT,
                        visitor_country TEXT,
                        visit_type TEXT,
                        purpose TEXT,
                        arrival_date TEXT,
                        departure_date TEXT,
                        host_id INTEGER,
                        host_name TEXT,
                        reception_plan TEXT,
                        status TEXT DEFAULT 'pending',
                        approved_by INTEGER,
                        approved_at TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS credit_transfers (
                        transfer_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        source_institution TEXT,
                        source_country TEXT,
                        program_type TEXT,
                        transfer_date TEXT,
                        courses TEXT,
                        total_credits INTEGER,
                        approved_credits INTEGER,
                        status TEXT DEFAULT 'pending',
                        reviewed_by INTEGER,
                        reviewed_at TEXT,
                        review_comment TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS scholarships (
                        scholarship_id TEXT PRIMARY KEY,
                        scholarship_name TEXT NOT NULL,
                        scholarship_type TEXT,
                        source TEXT,
                        coverage TEXT,
                        amount REAL,
                        target_country TEXT,
                        application_deadline TEXT,
                        requirements TEXT,
                        description TEXT,
                        quota INTEGER DEFAULT 1,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS scholarship_applications (
                        application_id TEXT PRIMARY KEY,
                        scholarship_id TEXT NOT NULL,
                        scholarship_name TEXT,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
        education_type TEXT,
                        apply_date TEXT,
                        status TEXT DEFAULT 'submitted',
                        materials TEXT,
                        statement TEXT,
                        awarded_amount REAL,
                        awarded_date TEXT,
                        reviewed_by INTEGER,
                        reviewed_at TEXT,
                        created_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('国际交流服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 合作院校 ==========

    def add_partner(self, institution_name: str, country: str,
                     partnership_type: str, **kwargs) -> Dict[str, Any]:
        try:
            partner_id = f"ptn_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO partner_institutions (
                            partner_id, institution_name, country, region,
                            partnership_type, agreement_start, agreement_end,
                            contact_person, contact_email, contact_phone,
                            website, description, quota_per_year, is_active,
                            logo_url, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
                    ''', (partner_id, institution_name, country,
                          kwargs.get('region'), partnership_type,
                          kwargs.get('agreement_start'), kwargs.get('agreement_end'),
                          kwargs.get('contact_person'), kwargs.get('contact_email'),
                          kwargs.get('contact_phone'), kwargs.get('website'),
                          kwargs.get('description'), kwargs.get('quota_per_year', 5),
                          kwargs.get('logo_url'), now, now))
                    conn.commit()
                    logger.info(f'添加合作院校: {institution_name} ({partner_id})')
                    return {'success': True, 'partner_id': partner_id}
        except Exception as e:
            logger.error(f'添加合作院校失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_partners(self, country: str = None, partnership_type: str = None,
                       is_active: bool = True, page: int = 1,
                       page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM partner_institutions WHERE 1=1'
                params = []
                if country:
                    query += ' AND country = ?'
                    params.append(country)
                if partnership_type:
                    query += ' AND partnership_type = ?'
                    params.append(partnership_type)
                if is_active is not None:
                    query += ' AND is_active = ?'
                    params.append(1 if is_active else 0)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                partners = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'partners': partners, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取合作院校列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 留学项目 ==========

    def create_program(self, program_name: str, program_type: str,
                        **kwargs) -> Dict[str, Any]:
        try:
            program_id = f"prg_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT institution_name FROM partner_institutions WHERE partner_id = ?',
                    (kwargs.get('partner_id'),))
                    partner = cursor.fetchone()
                    cursor.execute('''
                        INSERT INTO study_programs (
                            program_id, program_name, partner_id, institution_name,
                            country, program_type, duration, language, tuition_fee,
                            application_deadline, start_date, credits, description,
                            requirements, education_type, is_active, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                    ''', (program_id, program_name, kwargs.get('partner_id'),
                          partner[0] if partner else kwargs.get('institution_name'),
                          kwargs.get('country'), program_type,
                          kwargs.get('duration'), kwargs.get('language', '英语'),
                          kwargs.get('tuition_fee', 0), kwargs.get('application_deadline'),
                          kwargs.get('start_date'), kwargs.get('credits'),
                          kwargs.get('description'), kwargs.get('requirements'),
                          kwargs.get('education_type'), now, now))
                    conn.commit()
                    logger.info(f'创建留学项目: {program_name} ({program_id})')
                    return {'success': True, 'program_id': program_id}
        except Exception as e:
            logger.error(f'创建留学项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_programs(self, program_type: str = None, country: str = None,
                       education_type: str = None, page: int = 1,
                       page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM study_programs WHERE is_active = 1'
                params = []
                if program_type:
                    query += ' AND program_type = ?'
                    params.append(program_type)
                if country:
                    query += ' AND country = ?'
                    params.append(country)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
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

    # ========== 交换申请 ==========

    def apply_exchange(self, program_id: str, student_id: int,
                        **kwargs) -> Dict[str, Any]:
        try:
            application_id = f"exa_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT program_name, target_country FROM study_programs WHERE program_id = ?',
                    (program_id,))
                    prog = cursor.fetchone()
                    if not prog:
                        return {'success': False, 'error': '项目不存在'}
                    cursor.execute('''
                        INSERT INTO exchange_applications (
                            application_id, program_id, program_name,
                            student_id, student_name, education_type, study_type,
                            target_country, target_institution, apply_date,
                            start_date, end_date, status, statement,
                            transcript_url, recommendation_url, language_score,
                            language_exam_type, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'submitted', ?, ?, ?, ?, ?, ?, ?)
                    ''', (application_id, program_id, prog[0],
                          student_id, kwargs.get('student_name'),
                          kwargs.get('education_type'), kwargs.get('study_type'),
                          kwargs.get('target_country'), kwargs.get('target_institution'),
                          now[:10], kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('statement'), kwargs.get('transcript_url'),
                          kwargs.get('recommendation_url'),
                          kwargs.get('language_score'),
                          kwargs.get('language_exam_type'), now, now))
                    conn.commit()
                    logger.info(f'交换申请: {application_id}')
                    return {'success': True, 'application_id': application_id}
        except Exception as e:
            logger.error(f'交换申请失败: {e}')
            return {'success': False, 'error': str(e)}

    def review_exchange(self, application_id: str, approved: bool,
                        reviewed_by: int, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'nominated' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE exchange_applications SET
                            status = ?, reviewed_by = ?, reviewed_at = ?,
                            review_comment = ?, updated_at = ?
                        WHERE application_id = ? AND status = 'submitted'
                    ''', (status, reviewed_by, now,
                          kwargs.get('review_comment'), now, application_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '申请状态不允许审核'}
        except Exception as e:
            logger.error(f'审核交换申请失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 语言考试 ==========

    def record_language_exam(self, student_id: int, exam_type: str,
                              exam_date: str, score: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"ler_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = LANGUAGE_EXAMS.get(exam_type, {})
            valid_years = config.get('valid_years', 2)
            valid_until = (datetime.now() + timedelta(days=valid_years * 365)).strftime('%Y-%m-%d')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO language_exam_records (
                            record_id, student_id, student_name, exam_type,
                            exam_date, score, level, valid_until,
                            certificate_url, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (record_id, student_id, kwargs.get('student_name'),
                          exam_type, exam_date, score,
                          kwargs.get('level'), valid_until,
                          kwargs.get('certificate_url'), now))
                    conn.commit()
                    logger.info(f'语言考试成绩: {exam_type} - {score}')
                    return {'success': True, 'record_id': record_id, 'valid_until': valid_until}
        except Exception as e:
            logger.error(f'记录语言考试失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_student_language_records(self, student_id: int) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM language_exam_records WHERE student_id = ? ORDER BY exam_date DESC',
                (student_id,))
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records}
        except Exception as e:
            logger.error(f'获取语言考试记录失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 出访管理 ==========

    def apply_outbound_visit(self, visitor_id: int, visitor_name: str,
                              visit_type: str, destination_country: str,
                              **kwargs) -> Dict[str, Any]:
        try:
            visit_id = f"obv_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO outbound_visits (
                            visit_id, visitor_id, visitor_name, visitor_type,
                            visit_type, destination_country, destination_institution,
                            purpose, departure_date, return_date, funding_source,
                            budget, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                    ''', (visit_id, visitor_id, visitor_name,
                          kwargs.get('visitor_type', 'teacher'),
                          visit_type, destination_country,
                          kwargs.get('destination_institution'),
                          kwargs.get('purpose'),
                          kwargs.get('departure_date'),
                          kwargs.get('return_date'),
                          kwargs.get('funding_source', 'self_funded'),
                          kwargs.get('budget', 0), now, now))
                    conn.commit()
                    logger.info(f'出访申请: {visit_id}, 目的地: {destination_country}')
                    return {'success': True, 'visit_id': visit_id}
        except Exception as e:
            logger.error(f'出访申请失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_outbound_visit(self, visit_id: str, approved: bool,
                                approved_by: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE outbound_visits SET status = ?, approved_by = ?, approved_at = ?, updated_at = ?
                        WHERE visit_id = ? AND status = 'pending'
                    ''', (status, approved_by, now, now, visit_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '出访状态不允许审批'}
        except Exception as e:
            logger.error(f'审批出访失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 外宾接待 ==========

    def register_inbound_visit(self, visitor_name: str, visitor_institution: str,
                                visitor_country: str, arrival_date: str,
                                **kwargs) -> Dict[str, Any]:
        try:
            visit_id = f"ibv_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO inbound_visits (
                            visit_id, visitor_name, visitor_title, visitor_institution,
                            visitor_country, visit_type, purpose, arrival_date,
                            departure_date, host_id, host_name, reception_plan,
                            status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                    ''', (visit_id, visitor_name, kwargs.get('visitor_title'),
                          visitor_institution, visitor_country,
                          kwargs.get('visit_type', 'official'),
                          kwargs.get('purpose'), arrival_date,
                          kwargs.get('departure_date'),
                          kwargs.get('host_id'), kwargs.get('host_name'),
                          kwargs.get('reception_plan'), now))
                    conn.commit()
                    logger.info(f'外宾接待登记: {visitor_name} from {visitor_country}')
                    return {'success': True, 'visit_id': visit_id}
        except Exception as e:
            logger.error(f'外宾接待登记失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 学分转换 ==========

    def apply_credit_transfer(self, student_id: int, source_institution: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            transfer_id = f"crt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            courses = json.dumps(kwargs.get('courses'), ensure_ascii=False) if kwargs.get('courses') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO credit_transfers (
                            transfer_id, student_id, student_name,
                            source_institution, source_country, program_type,
                            transfer_date, courses, total_credits,
                            approved_credits, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'pending', ?)
                    ''', (transfer_id, student_id, kwargs.get('student_name'),
                          source_institution, kwargs.get('source_country'),
                          kwargs.get('program_type'), now[:10], courses,
                          kwargs.get('total_credits', 0), now))
                    conn.commit()
                    return {'success': True, 'transfer_id': transfer_id}
        except Exception as e:
            logger.error(f'学分转换申请失败: {e}')
            return {'success': False, 'error': str(e)}

    def review_credit_transfer(self, transfer_id: str, approved_credits: int,
                                reviewed_by: int, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE credit_transfers SET
                            approved_credits = ?, status = 'approved',
                            reviewed_by = ?, reviewed_at = ?, review_comment = ?
                        WHERE transfer_id = ? AND status = 'pending'
                    ''', (approved_credits, reviewed_by, now,
                          kwargs.get('review_comment'), transfer_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '转换申请状态不允许审核'}
        except Exception as e:
            logger.error(f'审核学分转换失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 奖学金 ==========

    def create_scholarship(self, scholarship_name: str, scholarship_type: str,
                            **kwargs) -> Dict[str, Any]:
        try:
            scholarship_id = f"scl_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO scholarships (
                            scholarship_id, scholarship_name, scholarship_type,
                            source, coverage, amount, target_country,
                            application_deadline, requirements, description,
                            quota, is_active, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                    ''', (scholarship_id, scholarship_name, scholarship_type,
                          kwargs.get('source'), kwargs.get('coverage', '部分'),
                          kwargs.get('amount', 0), kwargs.get('target_country'),
                          kwargs.get('application_deadline'),
                          kwargs.get('requirements'), kwargs.get('description'),
                          kwargs.get('quota', 1), now, now))
                    conn.commit()
                    return {'success': True, 'scholarship_id': scholarship_id}
        except Exception as e:
            logger.error(f'创建奖学金失败: {e}')
            return {'success': False, 'error': str(e)}

    def apply_scholarship(self, scholarship_id: str, student_id: int,
                           **kwargs) -> Dict[str, Any]:
        try:
            application_id = f"sca_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            materials = json.dumps(kwargs.get('materials'), ensure_ascii=False) if kwargs.get('materials') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT scholarship_name FROM scholarships WHERE scholarship_id = ?',
                    (scholarship_id,))
                    sc = cursor.fetchone()
                    if not sc:
                        return {'success': False, 'error': '奖学金不存在'}
                    cursor.execute('''
                        INSERT INTO scholarship_applications (
                            application_id, scholarship_id, scholarship_name,
                            student_id, student_name, education_type,
                            apply_date, status, materials, statement, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'submitted', ?, ?, ?)
                    ''', (application_id, scholarship_id, sc[0],
                          student_id, kwargs.get('student_name'),
                          kwargs.get('education_type'), now[:10],
                          materials, kwargs.get('statement'), now))
                    conn.commit()
                    return {'success': True, 'application_id': application_id}
        except Exception as e:
            logger.error(f'奖学金申请失败: {e}')
            return {'success': False, 'error': str(e)}

    def award_scholarship(self, application_id: str, awarded_amount: float,
                           reviewed_by: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE scholarship_applications SET
                            status = 'awarded', awarded_amount = ?,
                            awarded_date = ?, reviewed_by = ?, reviewed_at = ?
                        WHERE application_id = ? AND status = 'submitted'
                    ''', (awarded_amount, now[:10], reviewed_by, now, application_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '申请状态不允许审批'}
        except Exception as e:
            logger.error(f'奖学金审批失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_exchange_statistics(self, year: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = 'SELECT COUNT(*) FROM exchange_applications WHERE 1=1'
                params = []
                if year:
                    query += ' AND strftime("%Y", apply_date) = ?'
                    params.append(year)
                cursor.execute(query, params)
                total_apps = cursor.fetchone()[0]
                cursor.execute(f'SELECT status, COUNT(*) FROM ({query}) GROUP BY status', params)
                by_status = {r[0]: r[1] for r in cursor.fetchall()}
                cursor.execute(f'SELECT target_country, COUNT(*) FROM ({query}) GROUP BY target_country', params)
                by_country = {r[0]: r[1] for r in cursor.fetchall()}
                cursor.execute('SELECT COUNT(*) FROM partner_institutions WHERE is_active = 1')
                total_partners = cursor.fetchone()[0]
                return {
                    'success': True,
                    'stats': {
                        'total_partners': total_partners,
                        'total_applications': total_apps,
                        'by_status': by_status,
                        'by_country': by_country
                    }
                }
        except Exception as e:
            logger.error(f'获取交流统计失败: {e}')
            return {'success': False, 'error': str(e)}










