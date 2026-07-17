#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 招生报名管理服务 (v15.4.0)
====================================
提供招生计划、在线报名、入学审核和录取管理等综合服务。

核心能力：
1. 招生计划 - 招生方案制定、名额管理
2. 在线报名 - 报名表单、材料提交
3. 入学审核 - 资格审核、材料审核
4. 录取管理 - 录取通知、分班
5. 招生统计 - 报名统计、录取率分析
6. 招生宣传 - 招生简章、专业介绍
7. 成人招生 - 成人教育招生管理
8. K12招生 - 九年制义务教育招生
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'enrollment_management_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EnrollmentManagement')


# ========== 招生配置 ==========

# 招生类型
ENROLLMENT_TYPES = {
    'new_student': {'name': '新生招生', 'description': '首次入学新生'},
    'transfer': {'name': '转学招生', 'description': '从其他学校转入'},
    'readmission': {'name': '复学招生', 'description': '休学后复学'},
    'adult_enrollment': {'name': '成人招生', 'description': '成人教育入学'},
    'spring': {'name': '春季招生', 'description': '春季入学'},
    'autumn': {'name': '秋季招生', 'description': '秋季入学'}
}

# 报名状态
APPLICATION_STATUS = {
    'draft': {'name': '草稿', 'color': '#d9d9d9'},
    'submitted': {'name': '已提交', 'color': '#1890ff'},
    'reviewing': {'name': '审核中', 'color': '#faad14'},
    'interview_scheduled': {'name': '待面试', 'color': '#722ed1'},
    'interviewed': {'name': '已面试', 'color': '#13c2c2'},
    'accepted': {'name': '已录取', 'color': '#52c41a'},
    'waitlisted': {'name': '候补', 'color': '#faad14'},
    'rejected': {'name': '未录取', 'color': '#f5222d'},
    'enrolled': {'name': '已注册', 'color': '#52c41a'},
    'withdrawn': {'name': '已撤回', 'color': '#8c8c8c'}
}

# 审核类型
REVIEW_TYPES = {
    'qualification': {'name': '资格审核', 'description': '报名资格验证'},
    'material': {'name': '材料审核', 'description': '报名材料审核'},
    'interview': {'name': '面试审核', 'description': '面试评估'},
    'exam': {'name': '考试审核', 'description': '入学考试评估'},
    'final': {'name': '终审', 'description': '最终录取审核'}
}

# 招生计划状态
PLAN_STATUS = {
    'draft': '草稿',
    'published': '已发布',
    'ongoing': '报名中',
    'closed': '已截止',
    'completed': '已完成',
    'archived': '已归档'
}

# 成人招生方向
ADULT_ENROLLMENT_DIRECTIONS = {
    'japanese_n5': {'name': '日语N5班', 'target': '零基础日语学习', 'max_students': 30},
    'japanese_n3': {'name': '日语N3班', 'target': '有一定基础，目标N3', 'max_students': 25},
    'japanese_n2': {'name': '日语N2班', 'target': '目标JLPT N2', 'max_students': 20},
    'business_japanese': {'name': '商务日语班', 'target': '职场日语提升', 'max_students': 20},
    'english_basic': {'name': '英语基础班', 'target': '零基础英语', 'max_students': 30},
    'english_intermediate': {'name': '英语进阶班', 'target': '中级英语提升', 'max_students': 25}
}

# K12招生年级
K12_ENROLLMENT_GRADES = {
    'grade_1': {'name': '小学一年级', 'age_range': '6-7岁', 'max_students': 45},
    'grade_7': {'name': '初中七年级', 'age_range': '12-13岁', 'max_students': 50},
    'grade_10': {'name': '高中高一', 'age_range': '15-16岁', 'max_students': 45}
}

# 报名材料类型
REQUIRED_DOCUMENTS = {
    'id_card': {'name': '身份证', 'required': True, 'format': 'image'},
    'photo': {'name': '证件照', 'required': True, 'format': 'image'},
    'diploma': {'name': '毕业证书', 'required': True, 'format': 'image'},
    'transcript': {'name': '成绩单', 'required': False, 'format': 'image'},
    'residence': {'name': '户口本', 'required': False, 'format': 'image'},
    'health_cert': {'name': '健康证明', 'required': False, 'format': 'image'},
    'recommendation': {'name': '推荐信', 'required': False, 'format': 'document'},
    'portfolio': {'name': '作品集', 'required': False, 'format': 'document'}
}


class EnrollmentManagementService:
    """招生报名管理服务"""

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
                    CREATE TABLE IF NOT EXISTS enrollment_plans (
                        plan_id TEXT PRIMARY KEY,
                        plan_name TEXT NOT NULL,
                        enrollment_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        semester TEXT,
        academic_year TEXT,
                        target_grade INTEGER,
                        target_direction TEXT,
                        max_students INTEGER DEFAULT 30,
                        current_applications INTEGER DEFAULT 0,
                        accepted_count INTEGER DEFAULT 0,
                        enrolled_count INTEGER DEFAULT 0,
                        start_date TEXT,
                        end_date TEXT,
                        requirements TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'draft',
                        created_by INTEGER,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS applications (
                        application_id TEXT PRIMARY KEY,
                        application_no TEXT UNIQUE,
                        plan_id TEXT NOT NULL,
                        applicant_name TEXT NOT NULL,
                        applicant_id_number TEXT,
                        gender TEXT,
                        birth_date TEXT,
                        phone TEXT,
                        email TEXT,
                        address TEXT,
                        education_type TEXT,
                        target_grade INTEGER,
                        target_direction TEXT,
                        previous_school TEXT,
                        gpa REAL,
                        application_data TEXT,
                        documents TEXT,
                        status TEXT DEFAULT 'draft',
                        submitted_at TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS application_reviews (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        application_id TEXT NOT NULL,
                        review_type TEXT NOT NULL,
                        reviewer_id INTEGER,
                        reviewer_name TEXT,
                        result TEXT,
                        score REAL,
                        comment TEXT,
                        reviewed_at TEXT,
                        UNIQUE(application_id, review_type)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS admission_notices (
                        notice_id TEXT PRIMARY KEY,
                        application_id TEXT NOT NULL,
                        student_id INTEGER,
                        plan_id TEXT,
                        notice_type TEXT DEFAULT 'admission',
                        title TEXT,
                        content TEXT,
                        class_id TEXT,
                        grade_level INTEGER,
                        registration_deadline TEXT,
                        requirements TEXT,
                        sent_at TEXT,
                        is_read INTEGER DEFAULT 0,
                        read_at TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS enrollment_promotions (
                        promotion_id TEXT PRIMARY KEY,
                        plan_id TEXT,
                        title TEXT NOT NULL,
                        content TEXT,
                        target_audience TEXT,
                        publish_channel TEXT,
                        views INTEGER DEFAULT 0,
                        clicks INTEGER DEFAULT 0,
                        is_published INTEGER DEFAULT 0,
                        published_at TEXT,
                        created_by INTEGER,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS interview_schedules (
                        interview_id TEXT PRIMARY KEY,
                        application_id TEXT NOT NULL,
                        plan_id TEXT,
                        interview_date TEXT,
                        interview_time TEXT,
                        location TEXT,
                        interviewer_id INTEGER,
                        interviewer_name TEXT,
                        duration_minutes INTEGER DEFAULT 30,
                        status TEXT DEFAULT 'scheduled',
                        result TEXT,
                        score REAL,
                        feedback TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('招生报名管理服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    def create_enrollment_plan(self, plan_name: str, enrollment_type: str,
                                education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            plan_id = f"enp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            requirements = json.dumps(kwargs.get('requirements'), ensure_ascii=False) if kwargs.get('requirements') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO enrollment_plans (
                            plan_id, plan_name, enrollment_type, education_type,
                            semester, academic_year, target_grade, target_direction,
                            max_students, current_applications, accepted_count, enrolled_count,
                            start_date, end_date, requirements, description,
                            status, created_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (plan_id, plan_name, enrollment_type, education_type,
                          kwargs.get('semester'), kwargs.get('academic_year'),
                          kwargs.get('target_grade'), kwargs.get('target_direction'),
                          kwargs.get('max_students', 30),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          requirements, kwargs.get('description'),
                          kwargs.get('status', 'draft'), kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建招生计划: {plan_name} ({plan_id})')
                    return {'success': True, 'plan_id': plan_id, 'plan_name': plan_name}
        except Exception as e:
            logger.error(f'创建招生计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM enrollment_plans WHERE plan_id = ?', (plan_id,))
                row = cursor.fetchone()
                if row:
                    plan = dict(row)
                    if plan.get('requirements'):
                        plan['requirements'] = json.loads(plan['requirements'])
                    return plan
                return None
        except Exception as e:
            logger.error(f'获取招生计划失败: {e}')
            return None

    def list_plans(self, education_type: str = None, enrollment_type: str = None,
                    status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM enrollment_plans WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if enrollment_type:
                    query += ' AND enrollment_type = ?'
                    params.append(enrollment_type)
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
            logger.error(f'获取招生计划列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def submit_application(self, plan_id: str, applicant_name: str, **kwargs) -> Dict[str, Any]:
        try:
            application_id = f"app_{uuid.uuid4().hex[:12]}"
            application_no = f"AP{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
            now = datetime.now().isoformat()
            app_data = json.dumps(kwargs.get('application_data'), ensure_ascii=False) if kwargs.get('application_data') else None
            documents = json.dumps(kwargs.get('documents'), ensure_ascii=False) if kwargs.get('documents') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_students, current_applications, status FROM enrollment_plans WHERE plan_id = ?', (plan_id,))
                    plan = cursor.fetchone()
                    if not plan:
                        return {'success': False, 'error': '招生计划不存在'}
                    if plan[2] not in ('published', 'ongoing'):
                        return {'success': False, 'error': f'招生计划状态不允许报名: {plan[2]}'}
                    if plan[0] and plan[1] >= plan[0]:
                        return {'success': False, 'error': '招生名额已满'}
                    cursor.execute('''
                        INSERT INTO applications (
                            application_id, application_no, plan_id, applicant_name,
                            applicant_id_number, gender, birth_date, phone, email,
                            address, education_type, target_grade, target_direction,
                            previous_school, gpa, application_data, documents,
                            status, submitted_at, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'submitted', ?, ?, ?)
                    ''', (application_id, application_no, plan_id, applicant_name,
                          kwargs.get('applicant_id_number'), kwargs.get('gender'),
                          kwargs.get('birth_date'), kwargs.get('phone'), kwargs.get('email'),
                          kwargs.get('address'), kwargs.get('education_type'),
                          kwargs.get('target_grade'), kwargs.get('target_direction'),
                          kwargs.get('previous_school'), kwargs.get('gpa'),
                          app_data, documents, now, now, now))
                    cursor.execute('UPDATE enrollment_plans SET current_applications = current_applications + 1, updated_at = ? WHERE plan_id = ?', (now, plan_id))
                    conn.commit()
                    logger.info(f'提交报名: {application_no} ({application_id})')
                    return {'success': True, 'application_id': application_id, 'application_no': application_no}
        except Exception as e:
            logger.error(f'提交报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_application(self, application_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM applications WHERE application_id = ?', (application_id,))
                row = cursor.fetchone()
                if row:
                    app = dict(row)
                    if app.get('application_data'):
                        app['application_data'] = json.loads(app['application_data'])
                    if app.get('documents'):
                        app['documents'] = json.loads(app['documents'])
                    cursor.execute('SELECT * FROM application_reviews WHERE application_id = ? ORDER BY reviewed_at', (application_id,))
                    app['reviews'] = [dict(r) for r in cursor.fetchall()]
                    return app
                return None
        except Exception as e:
            logger.error(f'获取报名信息失败: {e}')
            return None

    def list_applications(self, plan_id: str = None, status: str = None,
                           education_type: str = None, page: int = 1,
                           page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM applications WHERE 1=1'
                params = []
                if plan_id:
                    query += ' AND plan_id = ?'
                    params.append(plan_id)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY submitted_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                applications = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'applications': applications, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取报名列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def review_application(self, application_id: str, review_type: str,
                            result: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM applications WHERE application_id = ?', (application_id,))
                    app = cursor.fetchone()
                    if not app:
                        return {'success': False, 'error': '报名申请不存在'}
                    cursor.execute('''
                        INSERT OR REPLACE INTO application_reviews (
                            application_id, review_type, reviewer_id, reviewer_name,
                            result, score, comment, reviewed_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (application_id, review_type, kwargs.get('reviewer_id'),
                          kwargs.get('reviewer_name'), result, kwargs.get('score'),
                          kwargs.get('comment'), now))
                    status_map = {
                        'pass': 'reviewing' if review_type != 'final' else 'accepted',
                        'fail': 'rejected',
                        'pending': 'reviewing'
                    }
                    new_status = status_map.get(result, 'reviewing')
                    cursor.execute('UPDATE applications SET status = ?, updated_at = ? WHERE application_id = ?',
                                 (new_status, now, application_id))
                    if new_status == 'accepted':
                        cursor.execute('SELECT plan_id FROM applications WHERE application_id = ?', (application_id,))
                        plan_id = cursor.fetchone()[0]
                        cursor.execute('UPDATE enrollment_plans SET accepted_count = accepted_count + 1, updated_at = ? WHERE plan_id = ?', (now, plan_id))
                    conn.commit()
                    logger.info(f'审核报名: {application_id} -> {result} ({new_status})')
                    return {'success': True, 'new_status': new_status}
        except Exception as e:
            logger.error(f'审核报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def schedule_interview(self, application_id: str, interview_date: str,
                            interview_time: str, **kwargs) -> Dict[str, Any]:
        try:
            interview_id = f"iv_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO interview_schedules (
                            interview_id, application_id, plan_id, interview_date,
                            interview_time, location, interviewer_id, interviewer_name,
                            duration_minutes, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'scheduled', ?, ?)
                    ''', (interview_id, application_id, kwargs.get('plan_id'),
                          interview_date, interview_time, kwargs.get('location'),
                          kwargs.get('interviewer_id'), kwargs.get('interviewer_name'),
                          kwargs.get('duration_minutes', 30), now, now))
                    cursor.execute('UPDATE applications SET status = ?, updated_at = ? WHERE application_id = ?',
                                 ('interview_scheduled', now, application_id))
                    conn.commit()
                    logger.info(f'安排面试: {interview_id}')
                    return {'success': True, 'interview_id': interview_id}
        except Exception as e:
            logger.error(f'安排面试失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_interview_result(self, interview_id: str, result: str,
                                 score: float = None, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE interview_schedules SET
                            status = 'completed', result = ?, score = ?,
                            feedback = ?, updated_at = ?
                        WHERE interview_id = ? AND status = 'scheduled'
                    ''', (result, score, kwargs.get('feedback'), now, interview_id))
                    cursor.execute('SELECT application_id FROM interview_schedules WHERE interview_id = ?', (interview_id,))
                    row = cursor.fetchone()
                    if row:
                        cursor.execute('UPDATE applications SET status = ?, updated_at = ? WHERE application_id = ?',
                                     ('interviewed', now, row[0]))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'记录面试结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def issue_admission_notice(self, application_id: str, **kwargs) -> Dict[str, Any]:
        try:
            notice_id = f"adm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT plan_id, applicant_name FROM applications WHERE application_id = ? AND status = ?', (application_id, 'accepted'))
                    app = cursor.fetchone()
                    if not app:
                        return {'success': False, 'error': '报名申请不存在或未录取'}
                    cursor.execute('''
                        INSERT INTO admission_notices (
                            notice_id, application_id, plan_id, notice_type,
                            title, content, class_id, grade_level,
                            registration_deadline, requirements, sent_at, is_read, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                    ''', (notice_id, application_id, app[0],
                          kwargs.get('notice_type', 'admission'),
                          kwargs.get('title', '录取通知书'),
                          kwargs.get('content', f'恭喜您被录取！请于规定时间内完成注册。'),
                          kwargs.get('class_id'), kwargs.get('grade_level'),
                          kwargs.get('registration_deadline'),
                          kwargs.get('requirements'), now, now))
                    conn.commit()
                    logger.info(f'发放录取通知: {notice_id}')
                    return {'success': True, 'notice_id': notice_id}
        except Exception as e:
            logger.error(f'发放录取通知失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_student(self, application_id: str, student_id: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT plan_id FROM applications WHERE application_id = ? AND status = ?', (application_id, 'accepted'))
                    app = cursor.fetchone()
                    if not app:
                        return {'success': False, 'error': '申请不存在或未录取'}
                    cursor.execute('UPDATE applications SET status = ?, student_id = ?, updated_at = ? WHERE application_id = ?',
                                 ('enrolled', student_id, now, application_id))
                    cursor.execute('UPDATE enrollment_plans SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE plan_id = ?', (now, app[0]))
                    conn.commit()
                    logger.info(f'学生注册入学: {application_id} -> 学生{student_id}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'学生注册入学失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_enrollment_stats(self, plan_id: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if plan_id:
                    cursor.execute('SELECT max_students, current_applications, accepted_count, enrolled_count FROM enrollment_plans WHERE plan_id = ?', (plan_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '计划不存在'}
                    cursor.execute('SELECT status, COUNT(*) FROM applications WHERE plan_id = ? GROUP BY status', (plan_id,))
                    status_dist = {r[0]: r[1] for r in cursor.fetchall()}
                    return {
                        'success': True,
                        'stats': {
                            'max_students': row[0],
                            'total_applications': row[1],
                            'accepted': row[2],
                            'enrolled': row[3],
                            'acceptance_rate': round(row[2] / row[1] * 100, 2) if row[1] > 0 else 0,
                            'enrollment_rate': round(row[3] / row[2] * 100, 2) if row[2] > 0 else 0,
                            'status_distribution': status_dist
                        }
                    }
                else:
                    cursor.execute('''
                        SELECT
                            COUNT(DISTINCT plan_id) as total_plans,
                            SUM(current_applications) as total_applications,
                            SUM(accepted_count) as total_accepted,
                            SUM(enrolled_count) as total_enrolled
                        FROM enrollment_plans
                    ''')
                    row = cursor.fetchone()
                    return {
                        'success': True,
                        'stats': {
                            'total_plans': row[0] or 0,
                            'total_applications': row[1] or 0,
                            'total_accepted': row[2] or 0,
                            'total_enrolled': row[3] or 0,
                            'overall_acceptance_rate': round((row[2] or 0) / (row[1] or 1) * 100, 2)
                        }
                    }
        except Exception as e:
            logger.error(f'获取招生统计失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_promotion(self, plan_id: str, title: str, content: str,
                          **kwargs) -> Dict[str, Any]:
        try:
            promotion_id = f"pro_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO enrollment_promotions (
                            promotion_id, plan_id, title, content,
                            target_audience, publish_channel, views, clicks,
                            is_published, published_at, created_by, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 0, 0, 0, NULL, ?, ?)
                    ''', (promotion_id, plan_id, title, content,
                          kwargs.get('target_audience'), kwargs.get('publish_channel'),
                          kwargs.get('created_by'), now))
                    conn.commit()
                    logger.info(f'创建招生宣传: {title} ({promotion_id})')
                    return {'success': True, 'promotion_id': promotion_id}
        except Exception as e:
            logger.error(f'创建招生宣传失败: {e}')
            return {'success': False, 'error': str(e)}

    def publish_promotion(self, promotion_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE enrollment_promotions SET is_published = 1, published_at = ? WHERE promotion_id = ?', (now, promotion_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'发布招生宣传失败: {e}')
            return {'success': False, 'error': str(e)}

    def publish_plan(self, plan_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE enrollment_plans SET status = ?, updated_at = ? WHERE plan_id = ? AND status = ?',
                                 ('published', now, plan_id, 'draft'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'发布招生计划: {plan_id}')
                        return {'success': True}
                    return {'success': False, 'error': '计划状态不允许发布'}
        except Exception as e:
            logger.error(f'发布招生计划失败: {e}')
            return {'success': False, 'error': str(e)}
