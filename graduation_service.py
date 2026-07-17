#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 毕业与证书管理服务 (v15.5.0)
====================================
提供毕业审核、证书管理、结业认证和毕业统计等综合服务。

核心能力：
1. 毕业审核 - 毕业条件检查、批量审核
2. 证书管理 - 毕业证书、结业证书、资格证书
3. 成绩复核 - 最终成绩汇总、GPA计算
4. 毕业统计 - 毕业率、就业率统计
5. 证书模板 - 证书模板配置
6. 证书验证 - 在线证书验证
7. 成人结业 - 成人教育结业管理
8. K12毕业 - 九年制毕业升学管理
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'graduation_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('Graduation')


# ========== 毕业配置 ==========

# 毕业类型
GRADUATION_TYPES = {
    'graduation': {'name': '毕业', 'certificate_type': 'diploma'},
    'completion': {'name': '结业', 'certificate_type': 'completion'},
    'degree': {'name': '学位', 'certificate_type': 'degree'},
    'qualification': {'name': '资格证书', 'certificate_type': 'qualification'},
    'training': {'name': '培训证书', 'certificate_type': 'training'},
    'honor': {'name': '荣誉证书', 'certificate_type': 'honor'}
}

# 毕业审核状态
GRADUATION_STATUS = {
    'not_applied': {'name': '未申请', 'color': '#d9d9d9'},
    'applied': {'name': '已申请', 'color': '#1890ff'},
    'reviewing': {'name': '审核中', 'color': '#faad14'},
    'approved': {'name': '审核通过', 'color': '#52c41a'},
    'rejected': {'name': '审核未通过', 'color': '#f5222d'},
    'graduated': {'name': '已毕业', 'color': '#52c41a'},
    'certified': {'name': '已发证', 'color': '#722ed1'}
}

# 证书状态
CERTIFICATE_STATUS = {
    'pending': {'name': '待制作', 'color': '#d9d9d9'},
    'issued': {'name': '已签发', 'color': '#52c41a'},
    'printed': {'name': '已打印', 'color': '#1890ff'},
    'distributed': {'name': '已发放', 'color': '#722ed1'},
    'replaced': {'name': '已补发', 'color': '#faad14'},
    'revoked': {'name': '已撤销', 'color': '#f5222d'}
}

# 毕业条件类型
GRADUATION_CONDITIONS = {
    'credit_required': {'name': '学分要求', 'type': 'numeric', 'description': '达到最低学分要求'},
    'gpa_required': {'name': 'GPA要求', 'type': 'numeric', 'description': '达到最低GPA'},
    'course_completion': {'name': '课程完成', 'type': 'boolean', 'description': '完成必修课程'},
    'attendance_rate': {'name': '出勤率要求', 'type': 'numeric', 'description': '达到最低出勤率'},
    'thesis': {'name': '毕业论文', 'type': 'boolean', 'description': '通过毕业论文答辩'},
    'internship': {'name': '实习要求', 'type': 'boolean', 'description': '完成实习要求'},
    'community_service': {'name': '社区服务', 'type': 'numeric', 'description': '完成社区服务时长'},
    'examination_pass': {'name': '考试通过', 'type': 'boolean', 'description': '通过毕业考试'}
}

# 成人教育结业类型
ADULT_GRADUATION_TYPES = {
    'course_completion': {'name': '课程结业', 'requires': '完成课程学习'},
    'level_certificate': {'name': '等级证书', 'requires': '通过等级考试'},
    'diploma': {'name': '毕业文凭', 'requires': '完成全部学业'},
    'training_certificate': {'name': '培训合格', 'requires': '通过培训考核'}
}

# K12毕业类型
K12_GRADUATION_TYPES = {
    'primary_school': {'name': '小学毕业', 'grade': 6},
    'junior_high': {'name': '初中毕业', 'grade': 9},
    'senior_high': {'name': '高中毕业', 'grade': 12}
}

# 荣誉称号
HONOR_TITLES = {
    'excellent_graduate': {'name': '优秀毕业生', 'level': 'school'},
    'excellent_student': {'name': '三好学生', 'level': 'grade'},
    'excellent_cadre': {'name': '优秀学生干部', 'level': 'school'},
    'progress_award': {'name': '进步奖', 'level': 'class'},
    'specialty_award': {'name': '特长奖', 'level': 'school'},
    'academic_excellence': {'name': '学业优秀奖', 'level': 'grade'}
}


class GraduationService:
    """毕业与证书管理服务"""

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
                    CREATE TABLE IF NOT EXISTS graduation_plans (
                        plan_id TEXT PRIMARY KEY,
                        plan_name TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        graduation_type TEXT NOT NULL,
                        academic_year TEXT,
                        semester TEXT,
                        grade_level INTEGER,
                        class_id TEXT,
                        conditions TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        status TEXT DEFAULT 'draft',
                        total_students INTEGER DEFAULT 0,
                        approved_count INTEGER DEFAULT 0,
                        rejected_count INTEGER DEFAULT 0,
                        created_by INTEGER,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS graduation_applications (
                        application_id TEXT PRIMARY KEY,
                        plan_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        apply_date TEXT,
                        status TEXT DEFAULT 'applied',
                        review_stage TEXT DEFAULT 'initial',
                        reviewer_id INTEGER,
                        review_comment TEXT,
                        review_date TEXT,
                        credit_earned REAL DEFAULT 0,
                        credit_required REAL DEFAULT 0,
                        gpa REAL DEFAULT 0,
                        gpa_required REAL DEFAULT 0,
                        attendance_rate REAL DEFAULT 0,
                        conditions_met TEXT,
                        conditions_failed TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS certificates (
                        certificate_id TEXT PRIMARY KEY,
                        certificate_no TEXT UNIQUE,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        education_type TEXT,
                        certificate_type TEXT NOT NULL,
                        certificate_title TEXT,
                        plan_id TEXT,
                        issue_date TEXT,
                        valid_from TEXT,
                        valid_to TEXT,
                        issuer TEXT,
                        issuer_title TEXT,
                        status TEXT DEFAULT 'pending',
                        verification_code TEXT,
                        file_url TEXT,
                        grade_level INTEGER,
                        major TEXT,
                        honor_level TEXT,
                        issued_by INTEGER,
                        printed_at TEXT,
                        distributed_at TEXT,
                        distributed_to TEXT,
                        revoked_at TEXT,
                        revoke_reason TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS certificate_templates (
                        template_id TEXT PRIMARY KEY,
                        template_name TEXT NOT NULL,
                        certificate_type TEXT NOT NULL,
                        education_type TEXT,
                        template_content TEXT,
                        style_config TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_by INTEGER,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS graduation_statistics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        stat_year TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        total_students INTEGER DEFAULT 0,
                        graduated_count INTEGER DEFAULT 0,
                        graduation_rate REAL DEFAULT 0,
                        employment_rate REAL DEFAULT 0,
                        further_study_rate REAL DEFAULT 0,
                        average_gpa REAL DEFAULT 0,
                        top_score REAL DEFAULT 0,
                        honor_graduate_count INTEGER DEFAULT 0,
                        updated_at TEXT,
                        UNIQUE(stat_year, education_type)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS certificate_verification (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        certificate_id TEXT NOT NULL,
                        verification_code TEXT,
                        verify_count INTEGER DEFAULT 0,
                        last_verify_at TEXT,
                        verifier_info TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS reissue_records (
                        reissue_id TEXT PRIMARY KEY,
                        certificate_id TEXT NOT NULL,
                        student_id INTEGER,
                        apply_date TEXT,
                        reason TEXT,
                        status TEXT DEFAULT 'pending',
                        new_certificate_id TEXT,
                        approved_by INTEGER,
                        approved_at TEXT,
                        created_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('毕业与证书管理服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 毕业计划 ==========

    def create_graduation_plan(self, plan_name: str, education_type: str,
                                graduation_type: str, **kwargs) -> Dict[str, Any]:
        try:
            plan_id = f"grd_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            conditions = json.dumps(kwargs.get('conditions'), ensure_ascii=False) if kwargs.get('conditions') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO graduation_plans (
                            plan_id, plan_name, education_type, graduation_type,
                            academic_year, semester, grade_level, class_id,
                            conditions, start_date, end_date, status,
                            created_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?)
                    ''', (plan_id, plan_name, education_type, graduation_type,
                          kwargs.get('academic_year'), kwargs.get('semester'),
                          kwargs.get('grade_level'), kwargs.get('class_id'),
                          conditions, kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建毕业计划: {plan_name} ({plan_id})')
                    return {'success': True, 'plan_id': plan_id}
        except Exception as e:
            logger.error(f'创建毕业计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_graduation_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM graduation_plans WHERE plan_id = ?', (plan_id,))
                row = cursor.fetchone()
                if row:
                    plan = dict(row)
                    if plan.get('conditions'):
                        plan['conditions'] = json.loads(plan['conditions'])
                    return plan
                return None
        except Exception as e:
            logger.error(f'获取毕业计划失败: {e}')
            return None

    def list_graduation_plans(self, education_type: str = None, status: str = None,
                               page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM graduation_plans WHERE 1=1'
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
                plans = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'plans': plans, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取毕业计划列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def publish_plan(self, plan_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE graduation_plans SET status = 'published', updated_at = ?
                        WHERE plan_id = ? AND status = 'draft'
                    ''', (now, plan_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '计划状态不允许发布'}
        except Exception as e:
            logger.error(f'发布毕业计划失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 毕业申请 ==========

    def apply_graduation(self, plan_id: str, student_id: int, **kwargs) -> Dict[str, Any]:
        try:
            application_id = f"gap_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            conditions_met = json.dumps(kwargs.get('conditions_met'), ensure_ascii=False) if kwargs.get('conditions_met') else None
            conditions_failed = json.dumps(kwargs.get('conditions_failed'), ensure_ascii=False) if kwargs.get('conditions_failed') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM graduation_plans WHERE plan_id = ?', (plan_id,))
                    plan = cursor.fetchone()
                    if not plan or plan[0] != 'published':
                        return {'success': False, 'error': '毕业计划未发布或不存在'}
                    cursor.execute('''
                        SELECT application_id FROM graduation_applications
                        WHERE plan_id = ? AND student_id = ?
                    ''', (plan_id, student_id))
                    if cursor.fetchone():
                        return {'success': False, 'error': '已提交过毕业申请'}
                    cursor.execute('''
                        INSERT INTO graduation_applications (
                            application_id, plan_id, student_id, student_name,
                            apply_date, status, review_stage, credit_earned,
                            credit_required, gpa, gpa_required, attendance_rate,
                            conditions_met, conditions_failed, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 'applied', 'initial', ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (application_id, plan_id, student_id,
                          kwargs.get('student_name'), now[:10],
                          kwargs.get('credit_earned', 0), kwargs.get('credit_required', 0),
                          kwargs.get('gpa', 0), kwargs.get('gpa_required', 0),
                          kwargs.get('attendance_rate', 0),
                          conditions_met, conditions_failed, now, now))
                    cursor.execute('UPDATE graduation_plans SET total_students = total_students + 1, updated_at = ? WHERE plan_id = ?', (now, plan_id))
                    conn.commit()
                    logger.info(f'提交毕业申请: {application_id}')
                    return {'success': True, 'application_id': application_id}
        except Exception as e:
            logger.error(f'提交毕业申请失败: {e}')
            return {'success': False, 'error': str(e)}

    def review_application(self, application_id: str, approved: bool,
                            **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT plan_id FROM graduation_applications WHERE application_id = ?', (application_id,))
                    app = cursor.fetchone()
                    if not app:
                        return {'success': False, 'error': '申请不存在'}
                    cursor.execute('''
                        UPDATE graduation_applications SET
                            status = ?, review_stage = 'final',
                            reviewer_id = ?, review_comment = ?, review_date = ?, updated_at = ?
                        WHERE application_id = ? AND status IN (?, ?)
                    ''', (status, kwargs.get('reviewer_id'), kwargs.get('review_comment'),
                          now, now, application_id, 'applied', 'reviewing'))
                    if cursor.rowcount > 0:
                        if approved:
                            cursor.execute('UPDATE graduation_plans SET approved_count = approved_count + 1, updated_at = ? WHERE plan_id = ?', (now, app[0]))
                        else:
                            cursor.execute('UPDATE graduation_plans SET rejected_count = rejected_count + 1, updated_at = ? WHERE plan_id = ?', (now, app[0]))
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '申请状态不允许审核'}
        except Exception as e:
            logger.error(f'审核毕业申请失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_application(self, application_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM graduation_applications WHERE application_id = ?', (application_id,))
                row = cursor.fetchone()
                if row:
                    app = dict(row)
                    if app.get('conditions_met'):
                        app['conditions_met'] = json.loads(app['conditions_met'])
                    if app.get('conditions_failed'):
                        app['conditions_failed'] = json.loads(app['conditions_failed'])
                    return app
                return None
        except Exception as e:
            logger.error(f'获取毕业申请失败: {e}')
            return None

    def get_student_applications(self, student_id: int, plan_id: str = None,
                                   status: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM graduation_applications WHERE student_id = ?'
                params = [student_id]
                if plan_id:
                    query += ' AND plan_id = ?'
                    params.append(plan_id)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                query += ' ORDER BY created_at DESC'
                cursor.execute(query, params)
                applications = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'applications': applications}
        except Exception as e:
            logger.error(f'获取学生毕业申请失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 证书管理 ==========

    def issue_certificate(self, student_id: int, certificate_type: str,
                          certificate_title: str, **kwargs) -> Dict[str, Any]:
        try:
            certificate_id = f"crt_{uuid.uuid4().hex[:12]}"
            certificate_no = f"CERT{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
            verification_code = uuid.uuid4().hex[:8].upper()
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO certificates (
                            certificate_id, certificate_no, student_id, student_name,
                            education_type, certificate_type, certificate_title,
                            plan_id, issue_date, issuer, issuer_title,
                            status, verification_code, grade_level, major,
                            honor_level, issued_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'issued', ?, ?, ?, ?, ?, ?, ?)
                    ''', (certificate_id, certificate_no, student_id,
                          kwargs.get('student_name'), kwargs.get('education_type'),
                          certificate_type, certificate_title, kwargs.get('plan_id'),
                          kwargs.get('issue_date', now[:10]),
                          kwargs.get('issuer', ''), kwargs.get('issuer_title', ''),
                          verification_code, kwargs.get('grade_level'),
                          kwargs.get('major'), kwargs.get('honor_level'),
                          kwargs.get('issued_by'), now, now))
                    cursor.execute('''
                        INSERT INTO certificate_verification (certificate_id, verification_code, created_at)
                        VALUES (?, ?, ?)
                    ''', (certificate_id, verification_code, now))
                    conn.commit()
                    logger.info(f'签发证书: {certificate_no} ({certificate_id})')
                    return {'success': True, 'certificate_id': certificate_id,
                            'certificate_no': certificate_no, 'verification_code': verification_code}
        except Exception as e:
            logger.error(f'签发证书失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_certificate(self, certificate_id: str = None,
                         certificate_no: str = None,
                         verification_code: str = None) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                if certificate_id:
                    cursor.execute('SELECT * FROM certificates WHERE certificate_id = ?', (certificate_id,))
                elif certificate_no:
                    cursor.execute('SELECT * FROM certificates WHERE certificate_no = ?', (certificate_no,))
                elif verification_code:
                    cursor.execute('SELECT * FROM certificates WHERE verification_code = ?', (verification_code,))
                else:
                    return None
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f'获取证书失败: {e}')
            return None

    def verify_certificate(self, certificate_no: str,
                            verification_code: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT * FROM certificates
                        WHERE certificate_no = ? AND verification_code = ?
                    ''', (certificate_no, verification_code))
                    cert = cursor.fetchone()
                    now = datetime.now().isoformat()
                    if cert:
                        cert_dict = dict(cert)
                        cursor.execute('''
                            UPDATE certificate_verification SET
                                verify_count = verify_count + 1,
                                last_verify_at = ?
                            WHERE certificate_id = ?
                        ''', (now, cert_dict['certificate_id']))
                        conn.commit()
                        return {
                            'success': True,
                            'is_valid': cert_dict['status'] in ('issued', 'printed', 'distributed'),
                            'certificate': {
                                'certificate_no': cert_dict['certificate_no'],
                                'certificate_title': cert_dict['certificate_title'],
                                'student_name': cert_dict['student_name'],
                                'certificate_type': cert_dict['certificate_type'],
                                'issue_date': cert_dict['issue_date'],
                                'issuer': cert_dict['issuer'],
                                'status': cert_dict['status']
                            }
                        }
                    return {'success': True, 'is_valid': False}
        except Exception as e:
            logger.error(f'验证证书失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_certificates(self, student_id: int = None,
                           certificate_type: str = None,
                           status: str = None, page: int = 1,
                           page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM certificates WHERE 1=1'
                params = []
                if student_id:
                    query += ' AND student_id = ?'
                    params.append(student_id)
                if certificate_type:
                    query += ' AND certificate_type = ?'
                    params.append(certificate_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY issue_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                certificates = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'certificates': certificates, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取证书列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def reissue_certificate(self, certificate_id: str, reason: str,
                             **kwargs) -> Dict[str, Any]:
        try:
            reissue_id = f"rei_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT student_id, status FROM certificates WHERE certificate_id = ?', (certificate_id,))
                    cert = cursor.fetchone()
                    if not cert:
                        return {'success': False, 'error': '证书不存在'}
                    if cert[1] != 'issued' and cert[1] != 'distributed':
                        return {'success': False, 'error': f'证书状态不允许补发: {cert[1]}'}
                    cursor.execute('''
                        INSERT INTO reissue_records (
                            reissue_id, certificate_id, student_id, apply_date,
                            reason, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, 'pending', ?)
                    ''', (reissue_id, certificate_id, cert[0], now[:10], reason, now))
                    conn.commit()
                    logger.info(f'申请补发证书: {reissue_id}')
                    return {'success': True, 'reissue_id': reissue_id}
        except Exception as e:
            logger.error(f'申请补发证书失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_reissue(self, reissue_id: str, approved_by: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT certificate_id, student_id FROM reissue_records WHERE reissue_id = ? AND status = ?', (reissue_id, 'pending'))
                    record = cursor.fetchone()
                    if not record:
                        return {'success': False, 'error': '补发申请不存在或已处理'}
                    old_cert_id, student_id = record
                    cursor.execute('SELECT * FROM certificates WHERE certificate_id = ?', (old_cert_id,))
                    old_cert = cursor.fetchone()
                    if not old_cert:
                        return {'success': False, 'error': '原证书不存在'}
                    new_cert_id = f"crt_{uuid.uuid4().hex[:12]}"
                    new_cert_no = f"CERT{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
                    verification_code = uuid.uuid4().hex[:8].upper()
                    cursor.execute('''
                        INSERT INTO certificates (
                            certificate_id, certificate_no, student_id, student_name,
                            education_type, certificate_type, certificate_title,
                            issue_date, issuer, status, verification_code,
                            grade_level, major, issued_by, created_at, updated_at
                        ) SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, 'replaced', ?, ?, ?, ?, ?, ?
                        FROM certificates WHERE certificate_id = ?
                    ''', (new_cert_id, new_cert_no, student_id, old_cert[3],
                          old_cert[4], old_cert[5], old_cert[6],
                          old_cert[7], old_cert[9], verification_code,
                          old_cert[19], old_cert[20], approved_by, now, now,
                          old_cert_id))
                    cursor.execute('UPDATE certificates SET status = ? WHERE certificate_id = ?', ('replaced', old_cert_id))
                    cursor.execute('''
                        UPDATE reissue_records SET
                            status = 'approved', new_certificate_id = ?,
                            approved_by = ?, approved_at = ?
                        WHERE reissue_id = ?
                    ''', (new_cert_id, approved_by, now, reissue_id))
                    cursor.execute('''
                        INSERT INTO certificate_verification (certificate_id, verification_code, created_at)
                        VALUES (?, ?, ?)
                    ''', (new_cert_id, verification_code, now))
                    conn.commit()
                    return {'success': True, 'new_certificate_id': new_cert_id,
                            'new_certificate_no': new_cert_no}
        except Exception as e:
            logger.error(f'批准补发证书失败: {e}')
            return {'success': False, 'error': str(e)}

    def distribute_certificate(self, certificate_id: str,
                                distributed_to: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE certificates SET
                            status = 'distributed', distributed_at = ?,
                            distributed_to = ?, updated_at = ?
                        WHERE certificate_id = ? AND status = 'printed'
                    ''', (now, distributed_to, now, certificate_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '证书状态不允许发放'}
        except Exception as e:
            logger.error(f'发放证书失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 毕业统计 ==========

    def update_graduation_stats(self, stat_year: str, education_type: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT
                            COUNT(*) as total,
                            SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
                            AVG(gpa) as avg_gpa
                        FROM graduation_applications ga
                        JOIN graduation_plans gp ON ga.plan_id = gp.plan_id
                        WHERE gp.academic_year = ? AND gp.education_type = ?
                    ''', (stat_year, education_type))
                    row = cursor.fetchone()
                    total = row[0] or 0
                    approved = row[1] or 0
                    avg_gpa = row[2] or 0
                    grad_rate = round(approved / total * 100, 2) if total > 0 else 0
                    cursor.execute('''
                        INSERT INTO graduation_statistics (
                            stat_year, education_type, total_students,
                            graduated_count, graduation_rate, average_gpa, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(stat_year, education_type) DO UPDATE SET
                            total_students = excluded.total_students,
                            graduated_count = excluded.graduated_count,
                            graduation_rate = excluded.graduation_rate,
                            average_gpa = excluded.average_gpa,
                            updated_at = excluded.updated_at
                    ''', (stat_year, education_type, total, approved, grad_rate, avg_gpa, now))
                    conn.commit()
                    return {'success': True, 'graduation_rate': grad_rate}
        except Exception as e:
            logger.error(f'更新毕业统计失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_graduation_stats(self, stat_year: str = None,
                              education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM graduation_statistics WHERE 1=1'
                params = []
                if stat_year:
                    query += ' AND stat_year = ?'
                    params.append(stat_year)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' ORDER BY stat_year DESC'
                cursor.execute(query, params)
                stats = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'statistics': stats}
        except Exception as e:
            logger.error(f'获取毕业统计失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 证书模板 ==========

    def create_certificate_template(self, template_name: str,
                                      certificate_type: str, **kwargs) -> Dict[str, Any]:
        try:
            template_id = f"tpl_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            style_config = json.dumps(kwargs.get('style_config'), ensure_ascii=False) if kwargs.get('style_config') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO certificate_templates (
                            template_id, template_name, certificate_type,
                            education_type, template_content, style_config,
                            is_active, created_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
                    ''', (template_id, template_name, certificate_type,
                          kwargs.get('education_type'),
                          kwargs.get('template_content'), style_config,
                          kwargs.get('created_by'), now, now))
                    conn.commit()
                    return {'success': True, 'template_id': template_id}
        except Exception as e:
            logger.error(f'创建证书模板失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_certificate_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM certificate_templates WHERE template_id = ?', (template_id,))
                row = cursor.fetchone()
                if row:
                    tpl = dict(row)
                    if tpl.get('style_config'):
                        tpl['style_config'] = json.loads(tpl['style_config'])
                    return tpl
                return None
        except Exception as e:
            logger.error(f'获取证书模板失败: {e}')
            return None
