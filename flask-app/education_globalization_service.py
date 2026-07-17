#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育全球化服务 (v15.17.0)
====================================
提供国际教育合作、跨国学分互认、国际课程认证、海外学历认证、
国际交流项目、全球教育联盟、国际人才培养、跨境教育服务等综合管理服务。

核心能力：
1. 国际合作 - 合作伙伴管理、合作协议、合作地区
2. 学分互认 - 学分体系、互认申请、互认记录
3. 课程认证 - 课程认证、认证记录、认证管理
4. 学历认证 - 学历验证、验证记录、证书管理
5. 交流项目 - 交换项目、项目申请、项目管理
6. 全球联盟 - 联盟管理、联盟成员、联盟活动
7. 人才培养 - 人才项目、人才记录、人才引进
8. 跨境服务 - 跨境咨询、签证服务、语言培训
9. 留学生管理 - 留学生信息、学习记录、学籍管理
10. 统计分析 - 国际化教育数据统计

差异化支持：成人教育 / K12教育
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


# ========== 国际化配置 ==========

INTERNATIONAL_PROGRAMS = {
    'exchange': {'name': '国际交换', 'duration': ['1学期', '2学期', '1学年']},
    'joint': {'name': '联合培养', 'degree_type': ['学士', '硕士', '博士']},
    'double_degree': {'name': '双学位', 'partners': 2},
    'study_abroad': {'name': '海外学习', 'locations': ['北美', '欧洲', '亚洲', '大洋洲']},
    'internship': {'name': '国际实习', 'duration': ['3个月', '6个月', '1年']},
    'summer_school': {'name': '暑期学校', 'duration': ['4周', '6周', '8周']},
    'short_term': {'name': '短期研修', 'duration': ['1周', '2周', '4周']},
    'online_international': {'name': '在线国际课程', 'format': 'online'}
}

PARTNER_REGIONS = {
    'north_america': {'name': '北美', 'countries': ['美国', '加拿大', '墨西哥']},
    'europe': {'name': '欧洲', 'countries': ['英国', '德国', '法国', '意大利', '西班牙']},
    'asia': {'name': '亚洲', 'countries': ['中国', '日本', '韩国', '新加坡', '印度']},
    'oceania': {'name': '大洋洲', 'countries': ['澳大利亚', '新西兰']},
    'south_america': {'name': '南美', 'countries': ['巴西', '阿根廷', '智利']},
    'africa': {'name': '非洲', 'countries': ['南非', '埃及', '尼日利亚']}
}

CREDIT_SYSTEMS = {
    'ects': {'name': 'ECTS', 'region': '欧洲', 'points_per_year': 60},
    'us': {'name': 'US学分', 'region': '北美', 'points_per_year': 30},
    'uk': {'name': 'UK学分', 'region': '英国', 'points_per_year': 120},
    'china': {'name': '中国学分', 'region': '中国', 'points_per_year': 30},
    'australia': {'name': '澳洲学分', 'region': '大洋洲', 'points_per_year': 24},
    'japan_korea': {'name': '日韩学分', 'region': '亚洲', 'points_per_year': 30}
}

CERTIFICATION_TYPES = {
    'school': {'name': '学校认证', 'authority': '教育部/认证机构'},
    'program': {'name': '专业认证', 'validity': '5年'},
    'course': {'name': '课程认证', 'validity': '3年'},
    'degree': {'name': '学历认证', 'authority': '中国留学服务中心'},
    'qualification': {'name': '资格认证', 'validity': '终身'},
    'quality': {'name': '质量认证', 'standard': 'ISO 9001'}
}

EXCHANGE_TYPES = {
    'student': {'name': '学生交换', 'participants': '学生'},
    'teacher': {'name': '教师交换', 'participants': '教师'},
    'research': {'name': '研究交换', 'participants': '研究人员'},
    'course': {'name': '课程交换', 'format': '在线/线下'},
    'culture': {'name': '文化交流', 'activities': ['文化体验', '语言学习']},
    'academic': {'name': '学术交流', 'activities': ['会议', '讲座', '合作研究']}
}

ALLIANCE_TYPES = {
    'university': {'name': '国际大学联盟', 'members': '高校'},
    'discipline': {'name': '学科联盟', 'focus': '特定学科领域'},
    'research': {'name': '研究联盟', 'activities': '联合研究'},
    'edtech': {'name': '教育科技联盟', 'focus': '教育技术创新'},
    'regional': {'name': '区域联盟', 'region': '特定地理区域'},
    'industry': {'name': '行业联盟', 'partners': '企业与高校'}
}

TALENT_PROGRAMS = {
    'international_training': {'name': '国际人才培养', 'target': '在校学生'},
    'overseas_recruitment': {'name': '海外人才引进', 'target': '海外人才'},
    'scholar': {'name': '国际学者计划', 'target': '知名学者'},
    'joint_phd': {'name': '联合培养博士', 'degree': '博士'},
    'postdoc': {'name': '博士后交流', 'duration': ['1年', '2年']},
    'competition': {'name': '国际竞赛', 'activities': ['学科竞赛', '创新创业']}
}

CROSS_BORDER_SERVICES = {
    'consulting': {'name': '跨境教育咨询', 'services': ['留学规划', '院校选择']},
    'admission': {'name': '海外升学指导', 'services': ['申请指导', '文书辅导']},
    'visa': {'name': '签证服务', 'services': ['签证办理', '材料准备']},
    'language': {'name': '语言培训', 'languages': ['英语', '日语', '韩语', '法语', '德语']},
    'culture': {'name': '文化适应', 'services': ['文化培训', '生活指导']},
    'career': {'name': '就业指导', 'services': ['职业规划', '就业推荐']}
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
                    CREATE TABLE IF NOT EXISTS international_partners (
                        partner_id TEXT PRIMARY KEY,
                        partner_name TEXT NOT NULL,
                        partner_type TEXT,
                        region TEXT,
                        country TEXT,
                        city TEXT,
                        education_type TEXT,
                        description TEXT,
                        contact_name TEXT,
                        contact_email TEXT,
                        contact_phone TEXT,
                        website TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS partner_profiles (
                        profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        partner_id TEXT NOT NULL,
                        field_name TEXT NOT NULL,
                        field_value TEXT,
                        UNIQUE(partner_id, field_name)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS international_agreements (
                        agreement_id TEXT PRIMARY KEY,
                        partner_id TEXT NOT NULL,
                        agreement_name TEXT,
                        agreement_type TEXT,
                        effective_date TEXT,
                        expiration_date TEXT,
                        education_type TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        signed_by TEXT,
                        signed_date TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS agreement_details (
                        detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        agreement_id TEXT NOT NULL,
                        detail_item TEXT NOT NULL,
                        detail_value TEXT,
                        detail_description TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS credit_recognition (
                        recognition_id TEXT PRIMARY KEY,
                        source_institution TEXT,
                        target_institution TEXT,
                        source_credit_system TEXT,
                        target_credit_system TEXT,
                        conversion_rate REAL,
                        education_type TEXT,
                        description TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS recognition_records (
                        record_id TEXT PRIMARY KEY,
                        recognition_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        source_course TEXT,
                        source_credits REAL,
                        target_course TEXT,
                        target_credits REAL,
                        status TEXT DEFAULT 'pending',
                        approved_by TEXT,
                        approved_date TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS course_certification (
                        certification_id TEXT PRIMARY KEY,
                        course_name TEXT NOT NULL,
                        course_code TEXT,
                        institution TEXT,
                        certification_type TEXT,
                        education_type TEXT,
                        description TEXT,
                        validity_period INTEGER DEFAULT 3,
                        is_certified INTEGER DEFAULT 0,
                        certified_date TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS certification_records (
                        record_id TEXT PRIMARY KEY,
                        certification_id TEXT NOT NULL,
                        certificate_no TEXT,
                        issued_date TEXT,
                        expiration_date TEXT,
                        status TEXT DEFAULT 'valid',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS degree_verification (
                        verification_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        institution TEXT,
                        country TEXT,
                        degree_level TEXT,
                        degree_name TEXT,
                        graduation_date TEXT,
                        education_type TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'pending',
                        verified_by TEXT,
                        verified_date TEXT,
                        verification_result TEXT,
                        certificate_url TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS verification_records (
                        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        verification_id TEXT NOT NULL,
                        document_type TEXT,
                        document_url TEXT,
                        verified INTEGER DEFAULT 0,
                        notes TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS exchange_programs (
                        program_id TEXT PRIMARY KEY,
                        program_name TEXT NOT NULL,
                        program_type TEXT,
                        partner_id TEXT,
                        exchange_type TEXT,
                        education_type TEXT,
                        duration TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        max_participants INTEGER DEFAULT 20,
                        participant_count INTEGER DEFAULT 0,
                        description TEXT,
                        eligibility TEXT,
                        application_deadline TEXT,
                        status TEXT DEFAULT 'open',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS program_applications (
                        application_id TEXT PRIMARY KEY,
                        program_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        education_type TEXT,
                        application_date TEXT,
                        status TEXT DEFAULT 'pending',
                        accepted_date TEXT,
                        rejected_reason TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS global_alliances (
                        alliance_id TEXT PRIMARY KEY,
                        alliance_name TEXT NOT NULL,
                        alliance_type TEXT,
                        description TEXT,
                        establishment_date TEXT,
                        headquarters TEXT,
                        member_count INTEGER DEFAULT 1,
                        status TEXT DEFAULT 'active',
                        logo_url TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alliance_members (
                        member_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        alliance_id TEXT NOT NULL,
                        institution_id TEXT NOT NULL,
                        institution_name TEXT,
                        join_date TEXT,
                        member_type TEXT DEFAULT 'regular',
                        UNIQUE(alliance_id, institution_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS talent_development (
                        talent_id TEXT PRIMARY KEY,
                        program_name TEXT NOT NULL,
                        program_type TEXT,
                        education_type TEXT,
                        description TEXT,
                        target_group TEXT,
                        duration TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        max_participants INTEGER DEFAULT 10,
                        participant_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'open',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS talent_records (
                        record_id TEXT PRIMARY KEY,
                        talent_id TEXT NOT NULL,
                        participant_id INTEGER NOT NULL,
                        participant_name TEXT,
                        education_type TEXT,
                        application_date TEXT,
                        status TEXT DEFAULT 'pending',
                        completed INTEGER DEFAULT 0,
                        completion_date TEXT,
                        achievements TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cross_border_services (
                        service_id TEXT PRIMARY KEY,
                        service_name TEXT NOT NULL,
                        service_type TEXT,
                        education_type TEXT,
                        description TEXT,
                        provider TEXT,
                        price REAL DEFAULT 0,
                        duration TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS service_orders (
                        order_id TEXT PRIMARY KEY,
                        service_id TEXT NOT NULL,
                        customer_id INTEGER NOT NULL,
                        customer_name TEXT,
                        education_type TEXT,
                        order_date TEXT,
                        status TEXT DEFAULT 'pending',
                        completed_date TEXT,
                        total_amount REAL DEFAULT 0,
                        notes TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS international_students (
                        student_id INTEGER PRIMARY KEY,
                        student_name TEXT NOT NULL,
                        english_name TEXT,
                        nationality TEXT,
                        country_of_origin TEXT,
                        education_type TEXT,
                        program TEXT,
                        enrollment_date TEXT,
                        expected_graduation_date TEXT,
                        status TEXT DEFAULT 'active',
                        advisor_id INTEGER,
                        advisor_name TEXT,
                        contact_email TEXT,
                        contact_phone TEXT,
                        address TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS student_records (
                        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id INTEGER NOT NULL,
                        record_type TEXT,
                        record_content TEXT,
                        record_date TEXT,
                        created_by TEXT,
                        created_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('教育全球化服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 国际合作 ==========

    def add_partner(self, partner_name: str, partner_type: str,
                     region: str, **kwargs) -> Dict[str, Any]:
        try:
            partner_id = f"ptn_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO international_partners (
                            partner_id, partner_name, partner_type, region,
                            country, city, education_type, description,
                            contact_name, contact_email, contact_phone,
                            website, is_active, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                    ''', (partner_id, partner_name, partner_type, region,
                          kwargs.get('country'), kwargs.get('city'),
                          kwargs.get('education_type'), kwargs.get('description'),
                          kwargs.get('contact_name'), kwargs.get('contact_email'),
                          kwargs.get('contact_phone'), kwargs.get('website'),
                          now, now))
                    conn.commit()
                    logger.info(f'添加国际合作伙伴: {partner_name} ({partner_id})')
                    return {'success': True, 'partner_id': partner_id}
        except Exception as e:
            logger.error(f'添加合作伙伴失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_agreement(self, partner_id: str, agreement_name: str,
                          agreement_type: str, **kwargs) -> Dict[str, Any]:
        try:
            agreement_id = f"agm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO international_agreements (
                            agreement_id, partner_id, agreement_name,
                            agreement_type, effective_date, expiration_date,
                            education_type, description, status, signed_by,
                            signed_date, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?)
                    ''', (agreement_id, partner_id, agreement_name, agreement_type,
                          kwargs.get('effective_date'), kwargs.get('expiration_date'),
                          kwargs.get('education_type'), kwargs.get('description'),
                          kwargs.get('signed_by'), kwargs.get('signed_date', now[:10]),
                          now, now))
                    conn.commit()
                    logger.info(f'创建国际合作协议: {agreement_name} ({agreement_id})')
                    return {'success': True, 'agreement_id': agreement_id}
        except Exception as e:
            logger.error(f'创建合作协议失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_agreement_detail(self, agreement_id: str, detail_item: str,
                              detail_value: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO agreement_details (agreement_id, detail_item, detail_value, detail_description)
                        VALUES (?, ?, ?, ?)
                    ''', (agreement_id, detail_item, detail_value, kwargs.get('detail_description')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加协议详情失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_partners(self, region: str = None, education_type: str = None,
                       page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM international_partners WHERE is_active = 1'
                params = []
                if region:
                    query += ' AND region = ?'
                    params.append(region)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                partners = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'partners': partners, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取合作伙伴列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 学分互认 ==========

    def create_credit_recognition(self, source_institution: str,
                                    target_institution: str, **kwargs) -> Dict[str, Any]:
        try:
            recognition_id = f"crr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO credit_recognition (
                            recognition_id, source_institution, target_institution,
                            source_credit_system, target_credit_system,
                            conversion_rate, education_type, description,
                            is_active, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                    ''', (recognition_id, source_institution, target_institution,
                          kwargs.get('source_credit_system'),
                          kwargs.get('target_credit_system'),
                          kwargs.get('conversion_rate', 1.0),
                          kwargs.get('education_type'), kwargs.get('description'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建学分互认规则: {source_institution} -> {target_institution}')
                    return {'success': True, 'recognition_id': recognition_id}
        except Exception as e:
            logger.error(f'创建学分互认规则失败: {e}')
            return {'success': False, 'error': str(e)}

    def apply_credit_recognition(self, recognition_id: str, student_id: int,
                                  student_name: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"crr_rec_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT is_active FROM credit_recognition WHERE recognition_id = ?', (recognition_id,))
                    rule = cursor.fetchone()
                    if not rule or rule[0] != 1:
                        return {'success': False, 'error': '学分互认规则不存在或已失效'}
                    cursor.execute('''
                        INSERT INTO recognition_records (
                            record_id, recognition_id, student_id, student_name,
                            source_course, source_credits, target_course,
                            target_credits, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                    ''', (record_id, recognition_id, student_id, student_name,
                          kwargs.get('source_course'), kwargs.get('source_credits'),
                          kwargs.get('target_course'), kwargs.get('target_credits'),
                          now))
                    conn.commit()
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'申请学分互认失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_credit_recognition(self, record_id: str, approved: bool,
                                    **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE recognition_records SET status = ?, approved_by = ?, approved_date = ? WHERE record_id = ? AND status = ?',
                                 (status, kwargs.get('approved_by'), now[:10], record_id, 'pending'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '记录状态不允许审核'}
        except Exception as e:
            logger.error(f'审核学分互认失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_recognition_records(self, student_id: int = None,
                                 status: str = None, page: int = 1,
                                 page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM recognition_records WHERE 1=1'
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
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取学分互认记录失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 课程认证 ==========

    def create_course_certification(self, course_name: str,
                                     certification_type: str, **kwargs) -> Dict[str, Any]:
        try:
            certification_id = f"ccf_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO course_certification (
                            certification_id, course_name, course_code, institution,
                            certification_type, education_type, description,
                            validity_period, is_certified, certified_date,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, NULL, ?, ?)
                    ''', (certification_id, course_name, kwargs.get('course_code'),
                          kwargs.get('institution'), certification_type,
                          kwargs.get('education_type'), kwargs.get('description'),
                          kwargs.get('validity_period', 3), now, now))
                    conn.commit()
                    logger.info(f'创建课程认证: {course_name} ({certification_id})')
                    return {'success': True, 'certification_id': certification_id}
        except Exception as e:
            logger.error(f'创建课程认证失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_course_certification(self, certification_id: str,
                                      approved: bool, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            is_certified = 1 if approved else 0
            certified_date = now[:10] if approved else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE course_certification SET is_certified = ?, certified_date = ?, updated_at = ? WHERE certification_id = ?',
                                 (is_certified, certified_date, now, certification_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'is_certified': is_certified}
                    return {'success': False, 'error': '认证不存在'}
        except Exception as e:
            logger.error(f'审核课程认证失败: {e}')
            return {'success': False, 'error': str(e)}

    def issue_certificate(self, certification_id: str) -> Dict[str, Any]:
        try:
            record_id = f"ccf_rec_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            certificate_no = f"CCF{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT is_certified, validity_period FROM course_certification WHERE certification_id = ?', (certification_id,))
                    cert = cursor.fetchone()
                    if not cert or cert[0] != 1:
                        return {'success': False, 'error': '课程未通过认证'}
                    expiration_date = (datetime.now() + timedelta(days=cert[1]*365)).strftime('%Y-%m-%d')
                    cursor.execute('''
                        INSERT INTO certification_records (
                            record_id, certification_id, certificate_no,
                            issued_date, expiration_date, status
                        ) VALUES (?, ?, ?, ?, ?, 'valid')
                    ''', (record_id, certification_id, certificate_no, now[:10], expiration_date))
                    conn.commit()
                    return {'success': True, 'certificate_no': certificate_no, 'expiration_date': expiration_date}
        except Exception as e:
            logger.error(f'颁发证书失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_course_certifications(self, institution: str = None,
                                    education_type: str = None, page: int = 1,
                                    page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM course_certification WHERE 1=1'
                params = []
                if institution:
                    query += ' AND institution = ?'
                    params.append(institution)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                certifications = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'certifications': certifications, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取课程认证列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 学历认证 ==========

    def create_verification(self, student_id: int, student_name: str,
                             institution: str, country: str, **kwargs) -> Dict[str, Any]:
        try:
            verification_id = f"dgv_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO degree_verification (
                            verification_id, student_id, student_name,
                            institution, country, degree_level, degree_name,
                            graduation_date, education_type, description,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                    ''', (verification_id, student_id, student_name, institution, country,
                          kwargs.get('degree_level'), kwargs.get('degree_name'),
                          kwargs.get('graduation_date'), kwargs.get('education_type'),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建学历认证申请: {student_name} ({verification_id})')
                    return {'success': True, 'verification_id': verification_id}
        except Exception as e:
            logger.error(f'创建学历认证申请失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_verification_document(self, verification_id: str, document_type: str,
                                   document_url: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO verification_records (
                            verification_id, document_type, document_url,
                            verified, notes, created_at
                        ) VALUES (?, ?, ?, 0, ?, ?)
                    ''', (verification_id, document_type, document_url,
                          kwargs.get('notes'), now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加认证材料失败: {e}')
            return {'success': False, 'error': str(e)}

    def verify_document(self, verification_id: str, document_type: str,
                         verified: bool) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE verification_records SET verified = ? WHERE verification_id = ? AND document_type = ?',
                                 (1 if verified else 0, verification_id, document_type))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '材料不存在'}
        except Exception as e:
            logger.error(f'验证材料失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_verification(self, verification_id: str, verification_result: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'completed'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE degree_verification SET
                            status = ?, verified_by = ?, verified_date = ?,
                            verification_result = ?, certificate_url = ?,
                            updated_at = ?
                        WHERE verification_id = ? AND status = ?
                    ''', (status, kwargs.get('verified_by'), now[:10],
                          verification_result, kwargs.get('certificate_url'),
                          now, verification_id, 'pending'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '认证状态不允许完成'}
        except Exception as e:
            logger.error(f'完成学历认证失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_verification_history(self, student_id: int, page: int = 1,
                                  page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM degree_verification WHERE student_id = ? ORDER BY created_at DESC'
                params = [student_id]
                cursor.execute('SELECT COUNT(*) as cnt FROM degree_verification WHERE student_id = ?', params)
                total = cursor.fetchone()['cnt']
                query += ' LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取学历认证历史失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 交流项目 ==========

    def create_exchange_program(self, program_name: str, program_type: str,
                                 partner_id: str, **kwargs) -> Dict[str, Any]:
        try:
            program_id = f"exp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO exchange_programs (
                            program_id, program_name, program_type,
                            partner_id, exchange_type, education_type,
                            duration, start_date, end_date, max_participants,
                            participant_count, description, eligibility,
                            application_deadline, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, 'open', ?, ?)
                    ''', (program_id, program_name, program_type, partner_id,
                          kwargs.get('exchange_type'), kwargs.get('education_type'),
                          kwargs.get('duration'), kwargs.get('start_date'),
                          kwargs.get('end_date'), kwargs.get('max_participants', 20),
                          kwargs.get('description'), kwargs.get('eligibility'),
                          kwargs.get('application_deadline'), now, now))
                    conn.commit()
                    logger.info(f'创建交流项目: {program_name} ({program_id})')
                    return {'success': True, 'program_id': program_id}
        except Exception as e:
            logger.error(f'创建交流项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def apply_program(self, program_id: str, student_id: int,
                       student_name: str, **kwargs) -> Dict[str, Any]:
        try:
            application_id = f"exp_app_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, participant_count, status, education_type FROM exchange_programs WHERE program_id = ?', (program_id,))
                    program = cursor.fetchone()
                    if not program:
                        return {'success': False, 'error': '项目不存在'}
                    if program[2] != 'open':
                        return {'success': False, 'error': '项目报名已关闭'}
                    if program[0] and program[1] >= program[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('''
                        INSERT INTO program_applications (
                            application_id, program_id, student_id, student_name,
                            education_type, application_date, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
                    ''', (application_id, program_id, student_id, student_name,
                          kwargs.get('education_type', program[3]), now[:10], now))
                    cursor.execute('UPDATE exchange_programs SET participant_count = participant_count + 1, updated_at = ? WHERE program_id = ?', (now, program_id))
                    conn.commit()
                    return {'success': True, 'application_id': application_id}
        except Exception as e:
            logger.error(f'项目申请失败: {e}')
            return {'success': False, 'error': str(e)}

    def process_application(self, application_id: str, accepted: bool,
                             **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'accepted' if accepted else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE program_applications SET
                            status = ?, accepted_date = ?, rejected_reason = ?
                        WHERE application_id = ? AND status = ?
                    ''', (status, now[:10] if accepted else None,
                          kwargs.get('rejected_reason'), application_id, 'pending'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '申请状态不允许处理'}
        except Exception as e:
            logger.error(f'处理项目申请失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_exchange_programs(self, education_type: str = None,
                                status: str = None, page: int = 1,
                                page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM exchange_programs WHERE 1=1'
                params = []
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
            logger.error(f'获取交流项目列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 全球联盟 ==========

    def create_alliance(self, alliance_name: str, alliance_type: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            alliance_id = f"all_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO global_alliances (
                            alliance_id, alliance_name, alliance_type,
                            description, establishment_date, headquarters,
                            member_count, status, logo_url, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 1, 'active', ?, ?, ?)
                    ''', (alliance_id, alliance_name, alliance_type,
                          kwargs.get('description'), kwargs.get('establishment_date', now[:10]),
                          kwargs.get('headquarters'), kwargs.get('logo_url'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建全球联盟: {alliance_name} ({alliance_id})')
                    return {'success': True, 'alliance_id': alliance_id}
        except Exception as e:
            logger.error(f'创建全球联盟失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_alliance_member(self, alliance_id: str, institution_id: str,
                             institution_name: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT OR IGNORE INTO alliance_members (alliance_id, institution_id, institution_name, join_date, member_type) VALUES (?, ?, ?, ?, ?)',
                                 (alliance_id, institution_id, institution_name, now[:10], kwargs.get('member_type', 'regular')))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE global_alliances SET member_count = member_count + 1, updated_at = ? WHERE alliance_id = ?', (now, alliance_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已加入该联盟'}
        except Exception as e:
            logger.error(f'添加联盟成员失败: {e}')
            return {'success': False, 'error': str(e)}

    def remove_alliance_member(self, alliance_id: str, institution_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM alliance_members WHERE alliance_id = ? AND institution_id = ?', (alliance_id, institution_id))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE global_alliances SET member_count = member_count - 1, updated_at = ? WHERE alliance_id = ?', (now, alliance_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '成员不存在'}
        except Exception as e:
            logger.error(f'移除联盟成员失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_alliances(self, alliance_type: str = None, page: int = 1,
                       page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM global_alliances WHERE status = ?'
                params = ['active']
                if alliance_type:
                    query += ' AND alliance_type = ?'
                    params.append(alliance_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                alliances = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'alliances': alliances, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取联盟列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 人才培养 ==========

    def create_talent_program(self, program_name: str, program_type: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            talent_id = f"tal_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO talent_development (
                            talent_id, program_name, program_type,
                            education_type, description, target_group,
                            duration, start_date, end_date, max_participants,
                            participant_count, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'open', ?, ?)
                    ''', (talent_id, program_name, program_type,
                          kwargs.get('education_type'), kwargs.get('description'),
                          kwargs.get('target_group'), kwargs.get('duration'),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('max_participants', 10), now, now))
                    conn.commit()
                    logger.info(f'创建人才项目: {program_name} ({talent_id})')
                    return {'success': True, 'talent_id': talent_id}
        except Exception as e:
            logger.error(f'创建人才项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_talent_program(self, talent_id: str, participant_id: int,
                               participant_name: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"tal_rec_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, participant_count, status, education_type FROM talent_development WHERE talent_id = ?', (talent_id,))
                    program = cursor.fetchone()
                    if not program:
                        return {'success': False, 'error': '项目不存在'}
                    if program[2] != 'open':
                        return {'success': False, 'error': '项目报名已关闭'}
                    if program[0] and program[1] >= program[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('''
                        INSERT INTO talent_records (
                            record_id, talent_id, participant_id, participant_name,
                            education_type, application_date, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
                    ''', (record_id, talent_id, participant_id, participant_name,
                          kwargs.get('education_type', program[3]), now[:10], now))
                    cursor.execute('UPDATE talent_development SET participant_count = participant_count + 1, updated_at = ? WHERE talent_id = ?', (now, talent_id))
                    conn.commit()
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'报名人才项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_talent_progress(self, record_id: str, completed: bool,
                                **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            completion_date = now[:10] if completed else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE talent_records SET completed = ?, completion_date = ?, achievements = ? WHERE record_id = ?',
                                 (1 if completed else 0, completion_date, kwargs.get('achievements'), record_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '记录不存在'}
        except Exception as e:
            logger.error(f'更新人才培养进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_talent_programs(self, education_type: str = None,
                              status: str = None, page: int = 1,
                              page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM talent_development WHERE 1=1'
                params = []
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
            logger.error(f'获取人才项目列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 跨境服务 ==========

    def create_cross_border_service(self, service_name: str, service_type: str,
                                     **kwargs) -> Dict[str, Any]:
        try:
            service_id = f"cbs_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO cross_border_services (
                            service_id, service_name, service_type,
                            education_type, description, provider,
                            price, duration, is_active, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                    ''', (service_id, service_name, service_type,
                          kwargs.get('education_type'), kwargs.get('description'),
                          kwargs.get('provider'), kwargs.get('price', 0),
                          kwargs.get('duration'), now, now))
                    conn.commit()
                    logger.info(f'创建跨境服务: {service_name} ({service_id})')
                    return {'success': True, 'service_id': service_id}
        except Exception as e:
            logger.error(f'创建跨境服务失败: {e}')
            return {'success': False, 'error': str(e)}

    def order_service(self, service_id: str, customer_id: int,
                       customer_name: str, **kwargs) -> Dict[str, Any]:
        try:
            order_id = f"cbs_ord_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT is_active, price, education_type FROM cross_border_services WHERE service_id = ?', (service_id,))
                    service = cursor.fetchone()
                    if not service or service[0] != 1:
                        return {'success': False, 'error': '服务不存在或已停用'}
                    cursor.execute('''
                        INSERT INTO service_orders (
                            order_id, service_id, customer_id, customer_name,
                            education_type, order_date, status,
                            total_amount, notes, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)
                    ''', (order_id, service_id, customer_id, customer_name,
                          kwargs.get('education_type', service[2]), now[:10],
                          kwargs.get('total_amount', service[1]),
                          kwargs.get('notes'), now))
                    conn.commit()
                    return {'success': True, 'order_id': order_id}
        except Exception as e:
            logger.error(f'下单跨境服务失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_service_order(self, order_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE service_orders SET status = ?, completed_date = ? WHERE order_id = ? AND status = ?',
                                 ('completed', now[:10], order_id, 'pending'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '订单状态不允许完成'}
        except Exception as e:
            logger.error(f'完成服务订单失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_cross_border_services(self, education_type: str = None,
                                    page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM cross_border_services WHERE is_active = 1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                services = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'services': services, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取跨境服务列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 留学生管理 ==========

    def register_international_student(self, student_id: int, student_name: str,
                                        nationality: str, country_of_origin: str,
                                        **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO international_students (
                            student_id, student_name, english_name,
                            nationality, country_of_origin, education_type,
                            program, enrollment_date, expected_graduation_date,
                            status, advisor_id, advisor_name,
                            contact_email, contact_phone, address,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?, ?, ?)
                    ''', (student_id, student_name, kwargs.get('english_name'),
                          nationality, country_of_origin, kwargs.get('education_type'),
                          kwargs.get('program'), kwargs.get('enrollment_date', now[:10]),
                          kwargs.get('expected_graduation_date'),
                          kwargs.get('advisor_id'), kwargs.get('advisor_name'),
                          kwargs.get('contact_email'), kwargs.get('contact_phone'),
                          kwargs.get('address'), now, now))
                    conn.commit()
                    logger.info(f'注册留学生: {student_name} ({student_id})')
                    return {'success': True}
        except Exception as e:
            logger.error(f'注册留学生失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_student_status(self, student_id: int, status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE international_students SET status = ?, updated_at = ? WHERE student_id = ?',
                                 (status, now, student_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '学生不存在'}
        except Exception as e:
            logger.error(f'更新留学生状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_student_record(self, student_id: int, record_type: str,
                            record_content: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO student_records (
                            student_id, record_type, record_content,
                            record_date, created_by, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (student_id, record_type, record_content,
                          kwargs.get('record_date', now[:10]),
                          kwargs.get('created_by'), now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加学生记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_international_students(self, education_type: str = None,
                                     status: str = None, page: int = 1,
                                     page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM international_students WHERE 1=1'
                params = []
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
                students = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'students': students, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取留学生列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 ==========

    def get_globalization_stats(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                where_clause = f"AND education_type = '{education_type}'" if education_type else ""
                stats = {}

                cursor.execute(f'SELECT COUNT(*) FROM international_partners WHERE is_active = 1 {where_clause}')
                stats['partner_count'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM international_agreements WHERE status = "active" {where_clause}')
                stats['agreement_count'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM exchange_programs WHERE status = "open" {where_clause}')
                stats['active_programs'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT SUM(participant_count) FROM exchange_programs WHERE status = "open" {where_clause}')
                stats['program_participants'] = cursor.fetchone()[0] or 0

                cursor.execute(f'SELECT COUNT(*) FROM recognition_records WHERE status = "approved" {where_clause}')
                stats['approved_recognitions'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM course_certification WHERE is_certified = 1 {where_clause}')
                stats['certified_courses'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM degree_verification WHERE status = "completed" {where_clause}')
                stats['completed_verifications'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM global_alliances WHERE status = "active"')
                stats['alliance_count'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM talent_records WHERE completed = 1 {where_clause}')
                stats['completed_talent_programs'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM service_orders WHERE status = "completed" {where_clause}')
                stats['completed_services'] = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM international_students WHERE status = "active" {where_clause}')
                stats['active_students'] = cursor.fetchone()[0]

                stats['education_type'] = education_type or 'all'
                stats['generated_at'] = datetime.now().isoformat()

                return {'success': True, 'stats': stats}
        except Exception as e:
            logger.error(f'获取全球化统计数据失败: {e}')
            return {'success': False, 'error': str(e)}