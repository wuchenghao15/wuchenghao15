#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 职业资格认证服务 (v15.8.0)
====================================
提供职业资格认证、技能等级考核、语言能力考试及培训机构等综合管理服务。
同时支持成人职业教育与 K12 职业启蒙教育的差异化需求。

核心能力：
1. 证书目录管理 - 职业资格、技能等级、语言能力证书目录维护
2. 报名管理 - 报考条件、在线报名、资格审核、缴费
3. 考点管理 - 考点登记、考场配置、容量管理
4. 考试安排 - 考试计划、场次编排、准考证发放
5. 成绩与证书 - 成绩录入、合格判定、证书发放
6. 证书验证 - 在线验证、防伪查询、有效性检查
7. 培训机构 - 机构管理、培训课程、师资管理
8. 成人职业资格与 K12 职业启蒙差异化支持
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vocational_certification_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('VocationalCertification')


# ========== 职业资格认证配置 ==========

# 证书大类
CERTIFICATION_CATEGORIES = {
    'language': {'name': '语言类', 'description': '外语及母语能力等级证书'},
    'professional': {'name': '职业资格', 'description': '国家职业资格证书'},
    'skill': {'name': '技能等级', 'description': '职业技能等级证书'},
    'vocational': {'name': '学历职业', 'description': '学历教育相关职业证书'},
    'computer': {'name': '计算机', 'description': '计算机技术与软件证书'},
    'finance': {'name': '金融', 'description': '金融财会类证书'},
    'education': {'name': '教育', 'description': '教育教学类证书'},
    'medical': {'name': '医疗', 'description': '医疗卫生类证书'}
}

# 语言类证书
LANGUAGE_CERTS = {
    'jlpt': {'name': '日语能力测试', 'organization': '日本国际交流基金会', 'levels': ['N5', 'N4', 'N3', 'N2', 'N1'], 'validity_period': '长期有效'},
    'j_test': {'name': '实用日本语考试', 'organization': '日本语鉴定协会', 'levels': ['A-D', 'E-F'], 'validity_period': '长期有效'},
    'toeic': {'name': '托业', 'organization': 'ETS', 'levels': ['听读', '说写'], 'validity_period': 2},
    'toefl': {'name': '托福', 'organization': 'ETS', 'levels': ['iBT', 'ITP'], 'validity_period': 2},
    'ielts': {'name': '雅思', 'organization': '剑桥大学考试委员会', 'levels': ['A类', 'G类'], 'validity_period': 2},
    'hsk': {'name': '汉语水平考试', 'organization': '汉办', 'levels': 6, 'validity_period': '长期有效'},
    'cet': {'name': '大学英语', 'organization': '教育部考试中心', 'levels': ['CET-4', 'CET-6'], 'validity_period': '长期有效'}
}

# 职业资格证书
PROFESSIONAL_CERTS = {
    'accountant': {'name': '会计', 'level': '初级/中级/高级', 'issuing_authority': '财政部'},
    'teacher': {'name': '教师', 'level': '初级/中级/高级', 'issuing_authority': '教育部'},
    'lawyer': {'name': '律师', 'level': '高级', 'issuing_authority': '司法部'},
    'engineer': {'name': '工程师', 'level': '初级/中级/高级', 'issuing_authority': '人社部'},
    'pharmacist': {'name': '药师', 'level': '初级/中级/高级', 'issuing_authority': '国家药监局'},
    'nurse': {'name': '护士', 'level': '初级', 'issuing_authority': '卫健委'},
    'tour_guide': {'name': '导游', 'level': '初级/中级/高级', 'issuing_authority': '文旅部'},
    'hr': {'name': '人力资源', 'level': '初级/中级/高级', 'issuing_authority': '人社部'}
}

# 技能等级
SKILL_LEVELS = {
    'primary': {'name': '初级', 'level': 1},
    'intermediate': {'name': '中级', 'level': 2},
    'advanced': {'name': '高级', 'level': 3},
    'technician': {'name': '技师', 'level': 4},
    'senior_technician': {'name': '高级技师', 'level': 5}
}

# 考试状态
EXAM_STATUS = {
    'scheduled': '已安排',
    'registration': '报名中',
    'closed': '报名截止',
    'in_progress': '进行中',
    'completed': '已完成',
    'cancelled': '已取消'
}

# 报名状态
REGISTRATION_STATUS = {
    'pending': '待审核',
    'approved': '已通过',
    'rejected': '已驳回',
    'paid': '已缴费',
    'cancelled': '已取消'
}

# 证书状态
CERTIFICATE_STATUS = {
    'issued': '已发放',
    'valid': '有效',
    'expired': '已过期',
    'revoked': '已撤销',
    'lost': '挂失'
}

# 培训机构类型
TRAINING_ORG_TYPES = {
    'public': {'name': '公办'},
    'private': {'name': '民办'},
    'enterprise': {'name': '企业办'},
    'online': {'name': '线上'},
    'mixed': {'name': '混合'}
}

# 证书类别前缀（用于证书编号生成）
CATEGORY_PREFIX = {
    'language': 'LANG',
    'professional': 'PROF',
    'skill': 'SKIL',
    'vocational': 'VOC',
    'computer': 'COMP',
    'finance': 'FIN',
    'education': 'EDU',
    'medical': 'MED'
}


class VocationalCertificationService:
    """职业资格认证服务"""

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
                # 证书目录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS certifications (
                        cert_id TEXT PRIMARY KEY,
                        cert_name TEXT NOT NULL,
                        category TEXT NOT NULL,
                        sub_category TEXT,
                        issuing_authority TEXT,
                        level TEXT,
                        validity_period TEXT,
                        exam_fee REAL DEFAULT 0,
                        prerequisite TEXT,
                        description TEXT,
                        education_type TEXT DEFAULT 'common',
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 考点表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS exam_centers (
                        center_id TEXT PRIMARY KEY,
                        center_name TEXT NOT NULL,
                        center_code TEXT,
                        address TEXT,
                        city TEXT,
                        contact_phone TEXT,
                        contact_email TEXT,
                        capacity INTEGER DEFAULT 0,
                        room_count INTEGER DEFAULT 0,
                        facilities TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 考场表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS exam_rooms (
                        room_id TEXT PRIMARY KEY,
                        center_id TEXT NOT NULL,
                        room_name TEXT NOT NULL,
                        room_code TEXT,
                        seat_count INTEGER DEFAULT 0,
                        facilities TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT
                    )
                ''')
                # 考试安排表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS exam_schedules (
                        schedule_id TEXT PRIMARY KEY,
                        cert_id TEXT NOT NULL,
                        exam_name TEXT NOT NULL,
                        exam_date TEXT,
                        registration_deadline TEXT,
                        center_id TEXT,
                        fee REAL DEFAULT 0,
                        max_candidates INTEGER DEFAULT 0,
                        registered_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'scheduled',
                        description TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 报名记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS registrations (
                        reg_id TEXT PRIMARY KEY,
                        schedule_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        candidate_name TEXT,
                        id_number TEXT,
                        phone TEXT,
                        email TEXT,
                        education_type TEXT DEFAULT 'adult',
                        current_level TEXT,
                        status TEXT DEFAULT 'pending',
                        apply_level TEXT,
                        fee_paid REAL DEFAULT 0,
                        paid_at TEXT,
                        review_note TEXT,
                        reviewed_by TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 准考证表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS admission_tickets (
                        ticket_id TEXT PRIMARY KEY,
                        reg_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        candidate_name TEXT,
                        schedule_id TEXT NOT NULL,
                        center_id TEXT,
                        room_id TEXT,
                        seat_number TEXT,
                        exam_date TEXT,
                        exam_time TEXT,
                        ticket_code TEXT,
                        issued_at TEXT
                    )
                ''')
                # 成绩记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS exam_scores (
                        score_id TEXT PRIMARY KEY,
                        reg_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        schedule_id TEXT NOT NULL,
                        cert_id TEXT NOT NULL,
                        total_score REAL,
                        section_scores TEXT,
                        pass_threshold REAL,
                        is_passed INTEGER,
                        rank INTEGER,
                        graded_at TEXT,
                        graded_by TEXT,
                        created_at TEXT
                    )
                ''')
                # 证书表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS certificates (
                        certificate_id TEXT PRIMARY KEY,
                        cert_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        candidate_name TEXT,
                        cert_number TEXT UNIQUE,
                        issue_date TEXT,
                        expiry_date TEXT,
                        score_id TEXT,
                        level_achieved TEXT,
                        status TEXT DEFAULT 'issued',
                        issued_by TEXT,
                        verification_code TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 培训机构表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS training_organizations (
                        org_id TEXT PRIMARY KEY,
                        org_name TEXT NOT NULL,
                        org_type TEXT,
                        license_number TEXT,
                        legal_person TEXT,
                        address TEXT,
                        contact_phone TEXT,
                        courses INTEGER DEFAULT 0,
                        teacher_count INTEGER DEFAULT 0,
                        rating REAL DEFAULT 0,
                        is_approved INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 培训课程表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS training_courses (
                        course_id TEXT PRIMARY KEY,
                        org_id TEXT NOT NULL,
                        cert_id TEXT,
                        course_name TEXT NOT NULL,
                        duration_hours INTEGER DEFAULT 0,
                        tuition REAL DEFAULT 0,
                        schedule TEXT,
                        max_students INTEGER DEFAULT 0,
                        enrolled_count INTEGER DEFAULT 0,
                        description TEXT,
                        teacher TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 课程报名表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS course_enrollments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        course_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        student_name TEXT,
                        enroll_date TEXT,
                        progress REAL DEFAULT 0,
                        completion_status TEXT DEFAULT 'enrolled',
                        score REAL,
                        created_at TEXT
                    )
                ''')
                # 证书验证记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cert_verifications (
                        verify_id TEXT PRIMARY KEY,
                        certificate_id TEXT,
                        cert_number TEXT,
                        verification_code TEXT,
                        verify_time TEXT,
                        verify_ip TEXT,
                        verify_result TEXT,
                        verifier_info TEXT,
                        created_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('职业资格认证服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 证书目录管理 ==========

    def register_certification(self, cert_name: str, category: str,
                               **kwargs) -> Dict[str, Any]:
        """注册证书到目录"""
        try:
            cert_id = f"vc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO certifications (
                            cert_id, cert_name, category, sub_category,
                            issuing_authority, level, validity_period,
                            exam_fee, prerequisite, description, education_type,
                            is_active, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (cert_id, cert_name, category,
                          kwargs.get('sub_category'),
                          kwargs.get('issuing_authority'),
                          kwargs.get('level'),
                          kwargs.get('validity_period'),
                          kwargs.get('exam_fee', 0),
                          kwargs.get('prerequisite'),
                          kwargs.get('description'),
                          kwargs.get('education_type', 'common'),
                          kwargs.get('is_active', 1), now, now))
                    conn.commit()
                    logger.info(f'注册证书: {cert_name} ({cert_id})')
                    return {'success': True, 'cert_id': cert_id}
        except Exception as e:
            logger.error(f'注册证书失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_certification(self, cert_id: str) -> Dict[str, Any]:
        """获取证书详情"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM certifications WHERE cert_id = ?', (cert_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '证书不存在'}
                return {'success': True, 'certification': dict(row)}
        except Exception as e:
            logger.error(f'获取证书详情失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_certifications(self, page: int = 1, page_size: int = 20,
                            **filters) -> Dict[str, Any]:
        """证书列表，支持 category/education_type/is_active 筛选"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM certifications WHERE 1=1'
                params = []
                if filters.get('category'):
                    query += ' AND category = ?'
                    params.append(filters['category'])
                if filters.get('education_type'):
                    query += ' AND education_type = ?'
                    params.append(filters['education_type'])
                if filters.get('is_active') is not None:
                    query += ' AND is_active = ?'
                    params.append(1 if filters['is_active'] else 0)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取证书列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_certification(self, cert_id: str, **kwargs) -> Dict[str, Any]:
        """更新证书信息"""
        try:
            now = datetime.now().isoformat()
            allowed = ['cert_name', 'category', 'sub_category', 'issuing_authority',
                       'level', 'validity_period', 'exam_fee', 'prerequisite',
                       'description', 'education_type', 'is_active']
            fields = [k for k in kwargs.keys() if k in allowed]
            if not fields:
                return {'success': False, 'error': '无有效更新字段'}
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    sets = ', '.join([f'{f} = ?' for f in fields])
                    values = [kwargs[f] for f in fields]
                    values.extend([now, cert_id])
                    cursor.execute(f'UPDATE certifications SET {sets}, updated_at = ? WHERE cert_id = ?', values)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '证书不存在'}
        except Exception as e:
            logger.error(f'更新证书失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 考点管理 ==========

    def register_exam_center(self, center_name: str, **kwargs) -> Dict[str, Any]:
        """注册考点"""
        try:
            center_id = f"ec_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO exam_centers (
                            center_id, center_name, center_code, address, city,
                            contact_phone, contact_email, capacity, room_count,
                            facilities, is_active, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
                    ''', (center_id, center_name,
                          kwargs.get('center_code'),
                          kwargs.get('address'), kwargs.get('city'),
                          kwargs.get('contact_phone'), kwargs.get('contact_email'),
                          kwargs.get('capacity', 0),
                          kwargs.get('facilities'),
                          kwargs.get('is_active', 1), now, now))
                    conn.commit()
                    logger.info(f'注册考点: {center_name} ({center_id})')
                    return {'success': True, 'center_id': center_id}
        except Exception as e:
            logger.error(f'注册考点失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_exam_room(self, center_id: str, room_name: str,
                      **kwargs) -> Dict[str, Any]:
        """添加考场"""
        try:
            room_id = f"er_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT center_id FROM exam_centers WHERE center_id = ?', (center_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '考点不存在'}
                    cursor.execute('''
                        INSERT INTO exam_rooms (
                            room_id, center_id, room_name, room_code,
                            seat_count, facilities, is_active, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (room_id, center_id, room_name,
                          kwargs.get('room_code'),
                          kwargs.get('seat_count', 30),
                          kwargs.get('facilities'),
                          kwargs.get('is_active', 1), now))
                    cursor.execute('UPDATE exam_centers SET room_count = room_count + 1, updated_at = ? WHERE center_id = ?',
                                 (now, center_id))
                    conn.commit()
                    logger.info(f'添加考场: {room_name} ({room_id})')
                    return {'success': True, 'room_id': room_id}
        except Exception as e:
            logger.error(f'添加考场失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_exam_centers(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """考点列表"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM exam_centers WHERE 1=1'
                params = []
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取考点列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 考试安排与报名 ==========

    def create_exam_schedule(self, cert_id: str, exam_name: str,
                              exam_date: str, center_id: str,
                              **kwargs) -> Dict[str, Any]:
        """创建考试安排"""
        try:
            schedule_id = f"es_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT cert_id, exam_fee FROM certifications WHERE cert_id = ?', (cert_id,))
                    cert = cursor.fetchone()
                    if not cert:
                        return {'success': False, 'error': '证书不存在'}
                    fee = kwargs.get('fee', cert[1] if cert[1] else 0)
                    cursor.execute('''
                        INSERT INTO exam_schedules (
                            schedule_id, cert_id, exam_name, exam_date,
                            registration_deadline, center_id, fee, max_candidates,
                            registered_count, status, description, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
                    ''', (schedule_id, cert_id, exam_name, exam_date,
                          kwargs.get('registration_deadline'),
                          center_id, fee,
                          kwargs.get('max_candidates', 100),
                          kwargs.get('status', 'registration'),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建考试安排: {exam_name} ({schedule_id})')
                    return {'success': True, 'schedule_id': schedule_id}
        except Exception as e:
            logger.error(f'创建考试安排失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_for_exam(self, schedule_id: str, user_id: str,
                          candidate_name: str, **kwargs) -> Dict[str, Any]:
        """报名考试，含名额检查和报名截止检查"""
        try:
            reg_id = f"rg_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_candidates, registered_count, status, fee, registration_deadline FROM exam_schedules WHERE schedule_id = ?', (schedule_id,))
                    schedule = cursor.fetchone()
                    if not schedule:
                        return {'success': False, 'error': '考试安排不存在'}
                    if schedule[2] not in ('registration', 'scheduled'):
                        return {'success': False, 'error': '当前状态不允许报名'}
                    if schedule[0] and schedule[1] >= schedule[0]:
                        return {'success': False, 'error': '名额已满'}
                    # 报名截止时间检查
                    if schedule[4]:
                        try:
                            deadline = datetime.fromisoformat(schedule[4])
                            if datetime.now() > deadline:
                                return {'success': False, 'error': '报名已截止'}
                        except (ValueError, TypeError):
                            pass
                    # 重复报名检查
                    cursor.execute('SELECT reg_id FROM registrations WHERE schedule_id = ? AND user_id = ? AND status != ?',
                                 (schedule_id, user_id, 'cancelled'))
                    if cursor.fetchone():
                        return {'success': False, 'error': '已报名该考试'}
                    cursor.execute('''
                        INSERT INTO registrations (
                            reg_id, schedule_id, user_id, candidate_name,
                            id_number, phone, email, education_type, current_level,
                            status, apply_level, fee_paid, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, 0, ?, ?)
                    ''', (reg_id, schedule_id, user_id, candidate_name,
                          kwargs.get('id_number'), kwargs.get('phone'),
                          kwargs.get('email'),
                          kwargs.get('education_type', 'adult'),
                          kwargs.get('current_level'),
                          kwargs.get('apply_level'), now, now))
                    cursor.execute('UPDATE exam_schedules SET registered_count = registered_count + 1, updated_at = ? WHERE schedule_id = ?',
                                 (now, schedule_id))
                    conn.commit()
                    logger.info(f'报名考试: {candidate_name} -> {schedule_id}')
                    return {'success': True, 'reg_id': reg_id, 'fee': schedule[3]}
        except Exception as e:
            logger.error(f'考试报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def review_registration(self, reg_id: str, approved: bool,
                            **kwargs) -> Dict[str, Any]:
        """审核报名"""
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE registrations SET status = ?, review_note = ?, reviewed_by = ?, updated_at = ? WHERE reg_id = ? AND status = ?',
                                 (status, kwargs.get('review_note'),
                                  kwargs.get('reviewed_by'), now, reg_id, 'pending'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'审核报名 {reg_id}: {status}')
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '报名记录不存在或状态不允许审核'}
        except Exception as e:
            logger.error(f'审核报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def pay_registration_fee(self, reg_id: str, **kwargs) -> Dict[str, Any]:
        """缴费"""
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT r.fee_paid, e.fee FROM registrations r JOIN exam_schedules e ON r.schedule_id = e.schedule_id WHERE r.reg_id = ? AND r.status = ?',
                                 (reg_id, 'approved'))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '报名记录不存在或未通过审核'}
                    fee = kwargs.get('amount', row[1] or 0)
                    cursor.execute('UPDATE registrations SET fee_paid = ?, paid_at = ?, status = ?, updated_at = ? WHERE reg_id = ?',
                                 (fee, now, 'paid', now, reg_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'缴费成功: {reg_id}')
                        return {'success': True, 'fee_paid': fee}
                    return {'success': False, 'error': '缴费失败'}
        except Exception as e:
            logger.error(f'缴费失败: {e}')
            return {'success': False, 'error': str(e)}

    def issue_admission_ticket(self, reg_id: str) -> Dict[str, Any]:
        """发放准考证"""
        try:
            ticket_id = f"at_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT r.reg_id, r.user_id, r.candidate_name, r.schedule_id,
                               e.center_id, e.exam_date
                        FROM registrations r
                        JOIN exam_schedules e ON r.schedule_id = e.schedule_id
                        WHERE r.reg_id = ? AND r.status = ?
                    ''', (reg_id, 'paid'))
                    reg = cursor.fetchone()
                    if not reg:
                        return {'success': False, 'error': '报名记录不存在或未缴费'}
                    # 分配考场与座位
                    cursor.execute('SELECT room_id FROM exam_rooms WHERE center_id = ? AND is_active = 1 ORDER BY seat_count DESC LIMIT 1', (reg[4],))
                    room = cursor.fetchone()
                    room_id = room[0] if room else None
                    cursor.execute('SELECT COUNT(*) FROM admission_tickets WHERE schedule_id = ? AND room_id = ?', (reg[3], room_id))
                    seat_no = (cursor.fetchone()[0] or 0) + 1
                    ticket_code = f"ADT{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
                    cursor.execute('''
                        INSERT INTO admission_tickets (
                            ticket_id, reg_id, user_id, candidate_name,
                            schedule_id, center_id, room_id, seat_number,
                            exam_date, exam_time, ticket_code, issued_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (ticket_id, reg_id, reg[1], reg[2], reg[3], reg[4],
                          room_id, str(seat_no), reg[5], '09:00-11:00',
                          ticket_code, now))
                    conn.commit()
                    logger.info(f'发放准考证: {reg_id} ({ticket_code})')
                    return {'success': True, 'ticket_id': ticket_id,
                            'ticket_code': ticket_code, 'seat_number': str(seat_no)}
        except Exception as e:
            logger.error(f'发放准考证失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_exam_schedule(self, schedule_id: str) -> Dict[str, Any]:
        """获取考试安排"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM exam_schedules WHERE schedule_id = ?', (schedule_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '考试安排不存在'}
                return {'success': True, 'schedule': dict(row)}
        except Exception as e:
            logger.error(f'获取考试安排失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_exam_schedules(self, page: int = 1, page_size: int = 20,
                            **filters) -> Dict[str, Any]:
        """考试安排列表，支持 cert_id/center_id/status 筛选"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM exam_schedules WHERE 1=1'
                params = []
                if filters.get('cert_id'):
                    query += ' AND cert_id = ?'
                    params.append(filters['cert_id'])
                if filters.get('center_id'):
                    query += ' AND center_id = ?'
                    params.append(filters['center_id'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY exam_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取考试安排列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 成绩与证书 ==========

    def record_exam_score(self, reg_id: str, total_score: float,
                          **kwargs) -> Dict[str, Any]:
        """录入成绩，自动判定合格"""
        try:
            score_id = f"sc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT r.schedule_id, e.cert_id FROM registrations r JOIN exam_schedules e ON r.schedule_id = e.schedule_id WHERE r.reg_id = ?', (reg_id,))
                    reg = cursor.fetchone()
                    if not reg:
                        return {'success': False, 'error': '报名记录不存在'}
                    pass_threshold = kwargs.get('pass_threshold', 60.0)
                    section_scores = kwargs.get('section_scores')
                    is_passed = 1 if total_score >= pass_threshold else 0
                    cursor.execute('''
                        INSERT INTO exam_scores (
                            score_id, reg_id, user_id, schedule_id, cert_id,
                            total_score, section_scores, pass_threshold,
                            is_passed, rank, graded_at, graded_by, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (score_id, reg_id,
                          kwargs.get('user_id'),
                          reg[0], reg[1], total_score,
                          json.dumps(section_scores, ensure_ascii=False) if section_scores else None,
                          pass_threshold, is_passed,
                          kwargs.get('rank'), now,
                          kwargs.get('graded_by'), now))
                    conn.commit()
                    logger.info(f'录入成绩: {reg_id} 分数={total_score} 合格={is_passed}')
                    return {'success': True, 'score_id': score_id,
                            'is_passed': bool(is_passed)}
        except Exception as e:
            logger.error(f'录入成绩失败: {e}')
            return {'success': False, 'error': str(e)}

    def issue_certificate(self, user_id: str, cert_id: str,
                           **kwargs) -> Dict[str, Any]:
        """发放证书，生成唯一证书编号和验证码"""
        try:
            certificate_id = f"ct_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            today = datetime.now().strftime('%Y%m%d')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT cert_name, category, validity_period, level FROM certifications WHERE cert_id = ?', (cert_id,))
                    cert = cursor.fetchone()
                    if not cert:
                        return {'success': False, 'error': '证书不存在'}
                    # 证书编号: 类别前缀 + 年月日 + 6位序列号
                    prefix = CATEGORY_PREFIX.get(cert[1], 'CERT')
                    cursor.execute('SELECT COUNT(*) FROM certificates WHERE cert_number LIKE ?', (f'{prefix}-{today}-%',))
                    seq = (cursor.fetchone()[0] or 0) + 1
                    cert_number = f"{prefix}-{today}-{seq:06d}"
                    # 计算有效期
                    issue_date = kwargs.get('issue_date', now[:10])
                    expiry_date = kwargs.get('expiry_date')
                    if not expiry_date and cert[2]:
                        try:
                            years = int(cert[2])
                            issue_dt = datetime.strptime(issue_date, '%Y-%m-%d')
                            expiry_date = (issue_dt + timedelta(days=365 * years)).strftime('%Y-%m-%d')
                        except (ValueError, TypeError):
                            pass
                    verification_code = uuid.uuid4().hex[:8].upper()
                    cursor.execute('''
                        INSERT INTO certificates (
                            certificate_id, cert_id, user_id, candidate_name,
                            cert_number, issue_date, expiry_date, score_id,
                            level_achieved, status, issued_by, verification_code,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'issued', ?, ?, ?, ?)
                    ''', (certificate_id, cert_id, user_id,
                          kwargs.get('candidate_name'), cert_number,
                          issue_date, expiry_date,
                          kwargs.get('score_id'),
                          kwargs.get('level_achieved', cert[3]),
                          kwargs.get('issued_by'),
                          verification_code, now, now))
                    conn.commit()
                    logger.info(f'发放证书: {cert_number} ({certificate_id})')
                    return {'success': True, 'certificate_id': certificate_id,
                            'cert_number': cert_number,
                            'verification_code': verification_code}
        except Exception as e:
            logger.error(f'发放证书失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_certificate(self, certificate_id: str) -> Dict[str, Any]:
        """获取证书"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM certificates WHERE certificate_id = ?', (certificate_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '证书不存在'}
                return {'success': True, 'certificate': dict(row)}
        except Exception as e:
            logger.error(f'获取证书失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_user_certificates(self, user_id: str) -> Dict[str, Any]:
        """用户证书列表"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM certificates WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
                items = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': len(items)}
        except Exception as e:
            logger.error(f'获取用户证书列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 证书验证 ==========

    def verify_certificate(self, cert_number: str,
                            verification_code: str) -> Dict[str, Any]:
        """验证证书，记录验证日志"""
        try:
            verify_id = f"vf_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT certificate_id, cert_number, verification_code, status, expiry_date FROM certificates WHERE cert_number = ?', (cert_number,))
                    cert = cursor.fetchone()
                    if not cert:
                        result = 'not_found'
                    elif cert['verification_code'] != verification_code:
                        result = 'code_mismatch'
                    elif cert['status'] == 'revoked':
                        result = 'revoked'
                    elif cert['status'] == 'lost':
                        result = 'lost'
                    elif cert['status'] == 'expired' or (cert['expiry_date'] and cert['expiry_date'] < now[:10]):
                        result = 'expired'
                    else:
                        result = 'valid'
                    certificate_id = cert['certificate_id'] if cert else None
                    cursor.execute('''
                        INSERT INTO cert_verifications (
                            verify_id, certificate_id, cert_number,
                            verification_code, verify_time, verify_ip,
                            verify_result, verifier_info, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (verify_id, certificate_id, cert_number,
                          verification_code, now, '', result, '', now))
                    conn.commit()
                    logger.info(f'证书验证: {cert_number} 结果={result}')
                    return {'success': True, 'verify_result': result,
                            'valid': result == 'valid'}
        except Exception as e:
            logger.error(f'证书验证失败: {e}')
            return {'success': False, 'error': str(e)}

    def revoke_certificate(self, certificate_id: str, reason: str) -> Dict[str, Any]:
        """撤销证书"""
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE certificates SET status = ?, updated_at = ? WHERE certificate_id = ? AND status NOT IN (?, ?)',
                                 ('revoked', now, certificate_id, 'revoked', 'expired'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'撤销证书: {certificate_id} 原因={reason}')
                        return {'success': True, 'reason': reason}
                    return {'success': False, 'error': '证书不存在或已撤销/过期'}
        except Exception as e:
            logger.error(f'撤销证书失败: {e}')
            return {'success': False, 'error': str(e)}

    def renew_certificate(self, certificate_id: str, **kwargs) -> Dict[str, Any]:
        """证书续期"""
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT certificate_id, expiry_date FROM certificates WHERE certificate_id = ?', (certificate_id,))
                    cert = cursor.fetchone()
                    if not cert:
                        return {'success': False, 'error': '证书不存在'}
                    new_expiry = kwargs.get('expiry_date')
                    if not new_expiry:
                        years = kwargs.get('years', 3)
                        try:
                            base = datetime.strptime(kwargs.get('issue_date', now[:10]), '%Y-%m-%d')
                            new_expiry = (base + timedelta(days=365 * years)).strftime('%Y-%m-%d')
                        except (ValueError, TypeError):
                            new_expiry = (datetime.now() + timedelta(days=365 * 3)).strftime('%Y-%m-%d')
                    cursor.execute('UPDATE certificates SET status = ?, expiry_date = ?, updated_at = ? WHERE certificate_id = ?',
                                 ('valid', new_expiry, now, certificate_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'证书续期: {certificate_id} 新有效期={new_expiry}')
                        return {'success': True, 'expiry_date': new_expiry}
                    return {'success': False, 'error': '证书续期失败'}
        except Exception as e:
            logger.error(f'证书续期失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 培训机构 ==========

    def register_training_org(self, org_name: str, org_type: str,
                               **kwargs) -> Dict[str, Any]:
        """注册培训机构"""
        try:
            org_id = f"to_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO training_organizations (
                            org_id, org_name, org_type, license_number,
                            legal_person, address, contact_phone, courses,
                            teacher_count, rating, is_approved, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?)
                    ''', (org_id, org_name, org_type,
                          kwargs.get('license_number'),
                          kwargs.get('legal_person'),
                          kwargs.get('address'),
                          kwargs.get('contact_phone'),
                          kwargs.get('teacher_count', 0),
                          kwargs.get('rating', 0),
                          kwargs.get('is_approved', 0), now, now))
                    conn.commit()
                    logger.info(f'注册培训机构: {org_name} ({org_id})')
                    return {'success': True, 'org_id': org_id}
        except Exception as e:
            logger.error(f'注册培训机构失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_training_course(self, org_id: str, cert_id: str,
                            course_name: str, **kwargs) -> Dict[str, Any]:
        """添加培训课程"""
        try:
            course_id = f"tc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT org_id FROM training_organizations WHERE org_id = ?', (org_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '培训机构不存在'}
                    cursor.execute('''
                        INSERT INTO training_courses (
                            course_id, org_id, cert_id, course_name,
                            duration_hours, tuition, schedule, max_students,
                            enrolled_count, description, teacher, is_active,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?)
                    ''', (course_id, org_id, cert_id, course_name,
                          kwargs.get('duration_hours', 0),
                          kwargs.get('tuition', 0),
                          kwargs.get('schedule'),
                          kwargs.get('max_students', 30),
                          kwargs.get('description'),
                          kwargs.get('teacher'),
                          kwargs.get('is_active', 1), now, now))
                    cursor.execute('UPDATE training_organizations SET courses = courses + 1, updated_at = ? WHERE org_id = ?',
                                 (now, org_id))
                    conn.commit()
                    logger.info(f'添加培训课程: {course_name} ({course_id})')
                    return {'success': True, 'course_id': course_id}
        except Exception as e:
            logger.error(f'添加培训课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_training_course(self, course_id: str, user_id: str,
                                student_name: str) -> Dict[str, Any]:
        """报名培训课程"""
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_students, enrolled_count, is_active FROM training_courses WHERE course_id = ?', (course_id,))
                    course = cursor.fetchone()
                    if not course:
                        return {'success': False, 'error': '课程不存在'}
                    if not course[2]:
                        return {'success': False, 'error': '课程已停用'}
                    if course[0] and course[1] >= course[0]:
                        return {'success': False, 'error': '课程名额已满'}
                    cursor.execute('SELECT id FROM course_enrollments WHERE course_id = ? AND user_id = ?', (course_id, user_id))
                    if cursor.fetchone():
                        return {'success': False, 'error': '已报名该课程'}
                    cursor.execute('''
                        INSERT INTO course_enrollments (course_id, user_id, student_name, enroll_date, progress, completion_status, created_at)
                        VALUES (?, ?, ?, ?, 0, 'enrolled', ?)
                    ''', (course_id, user_id, student_name, now[:10], now))
                    cursor.execute('UPDATE training_courses SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE course_id = ?',
                                 (now, course_id))
                    conn.commit()
                    logger.info(f'报名培训课程: {student_name} -> {course_id}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'报名培训课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_training_orgs(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """培训机构列表"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM training_organizations WHERE 1=1'
                params = []
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(o) for o in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取培训机构列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_statistics(self, education_type: str = None) -> Dict[str, Any]:
        """返回统计信息（证书分类分布/考试状态分布/通过率/报名趋势/机构数量）"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                et_cond = ' AND education_type = ?' if education_type else ''
                params = [education_type] if education_type else []
                # 证书分类分布
                cursor.execute(f'SELECT category, COUNT(*) as cnt FROM certifications WHERE 1=1{et_cond} GROUP BY category', params)
                category_dist = {row[0]: row[1] for row in cursor.fetchall()}
                # 考试状态分布
                cursor.execute('SELECT status, COUNT(*) as cnt FROM exam_schedules GROUP BY status')
                exam_status_dist = {row[0]: row[1] for row in cursor.fetchall()}
                # 通过率统计
                cursor.execute('SELECT COUNT(*) FROM exam_scores WHERE is_passed = 1')
                passed = cursor.fetchone()[0] or 0
                cursor.execute('SELECT COUNT(*) FROM exam_scores')
                total_scores = cursor.fetchone()[0] or 0
                pass_rate = round(passed / total_scores, 4) if total_scores else 0
                # 报名趋势（近12个月）
                reg_cond = ' AND education_type = ?' if education_type else ''
                reg_params = [education_type] if education_type else []
                cursor.execute(f"SELECT substr(created_at, 1, 7) as month, COUNT(*) as cnt FROM registrations WHERE 1=1{reg_cond} GROUP BY month ORDER BY month DESC LIMIT 12", reg_params)
                reg_trend = [{'month': row[0], 'count': row[1]} for row in cursor.fetchall()]
                # 机构数量
                cursor.execute('SELECT COUNT(*) FROM training_organizations')
                org_count = cursor.fetchone()[0] or 0
                cursor.execute('SELECT COUNT(*) FROM training_organizations WHERE is_approved = 1')
                approved_orgs = cursor.fetchone()[0] or 0
                return {'success': True, 'statistics': {
                    'category_distribution': category_dist,
                    'exam_status_distribution': exam_status_dist,
                    'pass_rate': pass_rate,
                    'passed_count': passed,
                    'total_scores': total_scores,
                    'registration_trend': reg_trend,
                    'org_count': org_count,
                    'approved_org_count': approved_orgs
                }}
        except Exception as e:
            logger.error(f'获取统计信息失败: {e}')
            return {'success': False, 'error': str(e)}


if __name__ == '__main__':
    service = VocationalCertificationService()
    print('职业资格认证服务初始化完成')
    stats = service.get_statistics()
    print(f'统计: {stats}')
