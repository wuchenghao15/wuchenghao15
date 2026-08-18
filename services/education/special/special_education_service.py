from core.db_path import get_db_path as _mtscos_get_db_path
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS 特殊教育服务 (v15.8.0) ==================================== 提供特殊需求学生档案、个别化教育计划、资源教室、融合教育、康复训练、 特教教师管理、家校协同及成人特殊教育等综合管理服务。 本模块同时支持成人教育和K12教育的差异化需求。  核心能力： 1. 特殊需求学生档案 - 残障类型、学习障碍、超常学生、档案管理 2. 个别化教育计划(IEP) - 计划制定、目标管理、进度追踪、周期评估 3. 资源教室管理 - 教室登记、设备配置、使用预约 4. 融合教育支持 - 随班就读、特教班、融合活动 5. 康复训练 - 训练计划、训练记录、效果评估 6. 特教教师管理 - 资质、专长、培训、师生配对 7. 家校协同 - 家庭康复指导、家长培训、沟通记录 8. 成人特殊教育 - 职业康复、残障成人支持、就业辅导 """
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'special_education_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SpecialEducation')


# ========== 特殊教育配置 ==========

# 残障类型
DISABILITY_TYPES = {
    'visual': {'name': '视觉障碍', 'support_level': 'high'},
    'auditory': {'name': '听觉障碍', 'support_level': 'high'},
    'intellectual': {'name': '智力障碍', 'support_level': 'high'},
    'physical': {'name': '肢体障碍', 'support_level': 'medium'},
    'speech': {'name': '语言障碍', 'support_level': 'medium'},
    'autism': {'name': '自闭症', 'support_level': 'high'},
    'learning_disorder': {'name': '学习障碍', 'support_level': 'medium'},
    'multiple': {'name': '多重障碍', 'support_level': 'high'}
}

# 学习障碍类型
LEARNING_DISORDERS = {
    'dyslexia': {'name': '阅读障碍', 'description': '字词识别与阅读理解困难'},
    'dyscalculia': {'name': '计算障碍', 'description': '数字理解与运算困难'},
    'dysgraphia': {'name': '书写障碍', 'description': '书写表达与字形构建困难'},
    'ADHD': {'name': '注意缺陷', 'description': '注意力不集中与多动冲动'},
    'adhd_executive': {'name': '执行功能', 'description': '计划组织与自我调节困难'}
}

# 超常学生类型
GIFTED_TYPES = {
    'academic': {'name': '学业超常'},
    'artistic': {'name': '艺术超常'},
    'leadership': {'name': '领导才能'},
    'creative': {'name': '创造才能'},
    'athletic': {'name': '体育超常'}
}

# IEP目标领域
IEP_GOAL_DOMAINS = {
    'academic': {'name': '学业能力'},
    'communication': {'name': '沟通能力'},
    'social_social': {'name': '社交能力'},
    'motor': {'name': '运动能力'},
    'self_care': {'name': '生活自理'},
    'behavior': {'name': '行为管理'}
}

# IEP状态
IEP_STATUS = {
    'draft': {'name': '草拟'},
    'active': {'name': '执行'},
    'review': {'name': '评审'},
    'completed': {'name': '完成'},
    'expired': {'name': '过期'}
}

# 服务方式
SERVICE_MODES = {
    'inclusion': {'name': '随班就读', 'location': '普通班级'},
    'resource_room': {'name': '资源教室', 'location': '资源教室'},
    'self_contained': {'name': '特教班', 'location': '特教班级'},
    'homebound': {'name': '送教上门', 'location': '学生家中'},
    'hospital': {'name': '住院教学', 'location': '医院病房'}
}

# 康复训练类型
REHABILITATION_TYPES = {
    'speech_language': {'name': '言语语言训练', 'weekly_sessions': 3},
    'occupational': {'name': '作业治疗', 'weekly_sessions': 2},
    'physical': {'name': '物理治疗', 'weekly_sessions': 3},
    'psychological': {'name': '心理辅导', 'weekly_sessions': 1},
    'behavioral': {'name': '行为训练', 'weekly_sessions': 4},
    'educational': {'name': '教育康复', 'weekly_sessions': 5}
}

# 特教教师职称
SPECIAL_ED_TEACHER_TITLES = {
    'assistant': {'name': '辅助教师', 'level': 1, 'required_cert': '特教辅助证书'},
    'teacher': {'name': '特教教师', 'level': 2, 'required_cert': '特教教师资格证'},
    'senior': {'name': '高级特教教师', 'level': 3, 'required_cert': '高级特教教师证'},
    'specialist': {'name': '特教专家', 'level': 4, 'required_cert': '特教专家资格证'},
    'master': {'name': '特级教师', 'level': 5, 'required_cert': '特级教师证书'}
}


class SpecialEducationService:
    """特殊教育管理服务"""

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
                cursor.execute(''' CREATE TABLE IF NOT EXISTS special_students ( student_id TEXT PRIMARY KEY, user_id TEXT, name TEXT NOT NULL, gender TEXT, birth_date TEXT, education_type TEXT, grade_level TEXT, disability_type TEXT, disability_level TEXT, disability_desc TEXT, learning_disorder TEXT, gifted_type TEXT, service_mode TEXT, enrollment_date TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS iep_plans ( plan_id TEXT PRIMARY KEY, student_id TEXT NOT NULL, plan_year INTEGER, semester TEXT, start_date TEXT, end_date TEXT, status TEXT DEFAULT 'draft', review_cycle TEXT, created_by TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS iep_goals ( goal_id TEXT PRIMARY KEY, plan_id TEXT NOT NULL, domain TEXT, goal_desc TEXT, baseline TEXT, target TEXT, measurement TEXT, responsible_teacher TEXT, due_date TEXT, progress REAL DEFAULT 0, status TEXT DEFAULT 'active', created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS iep_progress_records ( id INTEGER PRIMARY KEY AUTOINCREMENT, goal_id TEXT NOT NULL, record_date TEXT, progress_value REAL, observation TEXT, recorded_by TEXT, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS resource_rooms ( room_id TEXT PRIMARY KEY, room_name TEXT NOT NULL, location TEXT, area REAL, capacity INTEGER, equipment TEXT, responsible_teacher TEXT, schedule TEXT, status TEXT DEFAULT 'available', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS resource_room_bookings ( id INTEGER PRIMARY KEY AUTOINCREMENT, room_id TEXT NOT NULL, student_id TEXT NOT NULL, teacher_id TEXT NOT NULL, booking_date TEXT, start_time TEXT, end_time TEXT, purpose TEXT, status TEXT DEFAULT 'booked', created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS rehabilitation_plans ( rehab_id TEXT PRIMARY KEY, student_id TEXT NOT NULL, rehab_type TEXT, therapist TEXT, frequency TEXT, duration_weeks INTEGER, goals TEXT, start_date TEXT, end_date TEXT, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS rehabilitation_records ( id INTEGER PRIMARY KEY AUTOINCREMENT, rehab_id TEXT NOT NULL, student_id TEXT NOT NULL, session_date TEXT, duration INTEGER, content TEXT, response TEXT, progress_note TEXT, therapist TEXT, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS special_ed_teachers ( teacher_id TEXT PRIMARY KEY, user_id TEXT, name TEXT NOT NULL, title TEXT, certifications TEXT, specialties TEXT, max_students INTEGER DEFAULT 5, student_count INTEGER DEFAULT 0, is_active INTEGER DEFAULT 1, training_hours REAL DEFAULT 0, rating REAL DEFAULT 0, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS teacher_student_matching ( id INTEGER PRIMARY KEY AUTOINCREMENT, teacher_id TEXT NOT NULL, student_id TEXT NOT NULL, match_type TEXT, start_date TEXT, end_date TEXT, status TEXT DEFAULT 'active', notes TEXT, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS family_supports ( support_id TEXT PRIMARY KEY, student_id TEXT NOT NULL, support_type TEXT, topic TEXT, content TEXT, family_member TEXT, conducted_by TEXT, conducted_date TEXT, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS inclusion_activities ( activity_id TEXT PRIMARY KEY, activity_name TEXT NOT NULL, activity_type TEXT, description TEXT, participant_count INTEGER DEFAULT 0, special_student_count INTEGER DEFAULT 0, location TEXT, start_date TEXT, end_date TEXT, organizer TEXT, outcome TEXT, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS adult_vocational_rehab ( rehab_id TEXT PRIMARY KEY, student_id TEXT NOT NULL, vocational_goal TEXT, skill_assessment TEXT, training_program TEXT, workplace_match TEXT, job_coach TEXT, status TEXT DEFAULT 'planning', start_date TEXT, completion_date TEXT, employment_outcome TEXT, created_at TEXT, updated_at TEXT ) ''')
                conn.commit()
                logger.info('特殊教育服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 档案管理 ==========

    def register_special_student(self, name: str, disability_type: str,
                                  **kwargs) -> Dict[str, Any]:
        """注册特殊学生档案"""
        try:
            student_id = f"se_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO special_students ( student_id, user_id, name, gender, birth_date, education_type, grade_level, disability_type, disability_level, disability_desc, learning_disorder, gifted_type, service_mode, enrollment_date, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?) ''', (student_id, kwargs.get('user_id'), name,
                          kwargs.get('gender'), kwargs.get('birth_date'),
                          kwargs.get('education_type', 'k12'),
                          kwargs.get('grade_level'), disability_type,
                          kwargs.get('disability_level'),
                          kwargs.get('disability_desc'),
                          kwargs.get('learning_disorder'),
                          kwargs.get('gifted_type'),
                          kwargs.get('service_mode', 'inclusion'),
                          kwargs.get('enrollment_date', now[:10]), now, now))
                    conn.commit()
                    logger.info(f'注册特殊学生: {name} ({student_id})')
                    return {'success': True, 'student_id': student_id}
        except Exception as e:
            logger.error(f'注册特殊学生失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_special_student(self, student_id: str) -> Dict[str, Any]:
        """获取学生档案"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM special_students WHERE student_id = ?', (student_id,))
                row = cursor.fetchone()
                if row:
                    return {'success': True, 'student': dict(row)}
                return {'success': False, 'error': '学生档案不存在'}
        except Exception as e:
            logger.error(f'获取学生档案失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_special_student(self, student_id: str, **kwargs) -> Dict[str, Any]:
        """更新学生档案"""
        try:
            now = datetime.now().isoformat()
            allowed_fields = ['user_id', 'name', 'gender', 'birth_date', 'education_type',
                              'grade_level', 'disability_type', 'disability_level',
                              'disability_desc', 'learning_disorder', 'gifted_type',
                              'service_mode', 'status']
            updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
            if not updates:
                return {'success': False, 'error': '没有可更新字段'}
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
                    params = list(updates.values()) + [now, student_id]
                    cursor.execute(
                        f'UPDATE special_students SET {set_clause}, updated_at = ? WHERE student_id = ?',
                        params
                    )
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '学生档案不存在'}
        except Exception as e:
            logger.error(f'更新学生档案失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_special_students(self, page: int = 1, page_size: int = 20,
                                **filters) -> Dict[str, Any]:
        """分页查询学生档案"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM special_students WHERE 1=1'
                params = []
                if filters.get('disability_type'):
                    query += ' AND disability_type = ?'
                    params.append(filters['disability_type'])
                if filters.get('education_type'):
                    query += ' AND education_type = ?'
                    params.append(filters['education_type'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'查询学生档案失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== IEP管理 ==========

    def create_iep(self, student_id: str, plan_year: int,
                    semester: str, **kwargs) -> Dict[str, Any]:
        """创建个别化教育计划"""
        try:
            plan_id = f"iep_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO iep_plans ( plan_id, student_id, plan_year, semester, start_date, end_date, status, review_cycle, created_by, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?, ?) ''', (plan_id, student_id, plan_year, semester,
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('review_cycle', 'quarterly'),
                          kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建IEP: {plan_id} 学生 {student_id}')
                    return {'success': True, 'plan_id': plan_id}
        except Exception as e:
            logger.error(f'创建IEP失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_iep_goal(self, plan_id: str, domain: str,
                      goal_desc: str, **kwargs) -> Dict[str, Any]:
        """添加IEP目标"""
        try:
            goal_id = f"gl_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO iep_goals ( goal_id, plan_id, domain, goal_desc, baseline, target, measurement, responsible_teacher, due_date, progress, status, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'active', ?) ''', (goal_id, plan_id, domain, goal_desc,
                          kwargs.get('baseline'), kwargs.get('target'),
                          kwargs.get('measurement'),
                          kwargs.get('responsible_teacher'),
                          kwargs.get('due_date'), now))
                    conn.commit()
                    logger.info(f'添加IEP目标: {goal_id} 计划 {plan_id}')
                    return {'success': True, 'goal_id': goal_id}
        except Exception as e:
            logger.error(f'添加IEP目标失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_iep_progress(self, goal_id: str, progress_value: float,
                             **kwargs) -> Dict[str, Any]:
        """记录IEP目标进度"""
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO iep_progress_records ( goal_id, record_date, progress_value, observation, recorded_by, created_at ) VALUES (?, ?, ?, ?, ?, ?) ''', (goal_id, kwargs.get('record_date', now[:10]),
                          progress_value, kwargs.get('observation'),
                          kwargs.get('recorded_by'), now))
                    cursor.execute('UPDATE iep_goals SET progress = ?, status = ? WHERE goal_id = ?',
                                 (progress_value,
                                  'completed' if progress_value >= 100 else 'active',
                                  goal_id))
                    conn.commit()
                    logger.info(f'记录IEP进度: 目标 {goal_id} 进度 {progress_value}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'记录IEP进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_iep(self, plan_id: str) -> Dict[str, Any]:
        """获取IEP详情（含目标列表）"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM iep_plans WHERE plan_id = ?', (plan_id,))
                plan = cursor.fetchone()
                if not plan:
                    return {'success': False, 'error': 'IEP不存在'}
                cursor.execute('SELECT * FROM iep_goals WHERE plan_id = ? ORDER BY created_at', (plan_id,))
                goals = [dict(g) for g in cursor.fetchall()]
                for goal in goals:
                    cursor.execute('SELECT * FROM iep_progress_records WHERE goal_id = ? ORDER BY record_date DESC',
                    (goal['goal_id'],))
                    goal['progress_records'] = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'plan': dict(plan), 'goals': goals}
        except Exception as e:
            logger.error(f'获取IEP详情失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_ieps(self, student_id: str = None, page: int = 1,
                   page_size: int = 20) -> Dict[str, Any]:
        """IEP列表"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM iep_plans WHERE 1=1'
                params = []
                if student_id:
                    query += ' AND student_id = ?'
                    params.append(student_id)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'查询IEP列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def review_iep(self, plan_id: str, **kwargs) -> Dict[str, Any]:
        """IEP评审"""
        try:
            now = datetime.now().isoformat()
            new_status = kwargs.get('status', 'review')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE iep_plans SET status = ?, updated_at = ? WHERE plan_id = ?',
                                 (new_status, now, plan_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'IEP评审: {plan_id} 状态 {new_status}')
                        return {'success': True, 'status': new_status}
                    return {'success': False, 'error': 'IEP不存在'}
        except Exception as e:
            logger.error(f'IEP评审失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 资源教室 ==========

    def register_resource_room(self, room_name: str, location: str,
                                **kwargs) -> Dict[str, Any]:
        """注册资源教室"""
        try:
            room_id = f"rr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            equipment = kwargs.get('equipment')
            if isinstance(equipment, (list, dict)):
                equipment = json.dumps(equipment, ensure_ascii=False)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO resource_rooms ( room_id, room_name, location, area, capacity, equipment, responsible_teacher, schedule, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'available', ?, ?) ''', (room_id, room_name, location,
                          kwargs.get('area'), kwargs.get('capacity'),
                          equipment, kwargs.get('responsible_teacher'),
                          kwargs.get('schedule'), now, now))
                    conn.commit()
                    logger.info(f'注册资源教室: {room_name} ({room_id})')
                    return {'success': True, 'room_id': room_id}
        except Exception as e:
            logger.error(f'注册资源教室失败: {e}')
            return {'success': False, 'error': str(e)}

    def book_resource_room(self, room_id: str, student_id: str,
                            teacher_id: str, **kwargs) -> Dict[str, Any]:
        """预约资源教室"""
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM resource_rooms WHERE room_id = ?', (room_id,))
                    room = cursor.fetchone()
                    if not room:
                        return {'success': False, 'error': '资源教室不存在'}
                    if room[0] != 'available':
                        return {'success': False, 'error': '资源教室不可用'}
                    cursor.execute(''' INSERT INTO resource_room_bookings ( room_id, student_id, teacher_id, booking_date, start_time, end_time, purpose, status, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, 'booked', ?) ''', (room_id, student_id, teacher_id,
                          kwargs.get('booking_date', now[:10]),
                          kwargs.get('start_time'), kwargs.get('end_time'),
                          kwargs.get('purpose'), now))
                    conn.commit()
                    logger.info(f'预约资源教室: {room_id} 学生 {student_id}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'预约资源教室失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_resource_rooms(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """资源教室列表"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM resource_rooms WHERE 1=1'
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})')
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                cursor.execute(query, [page_size, (page - 1) * page_size])
                items = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'查询资源教室列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 康复训练 ==========

    def create_rehabilitation_plan(self, student_id: str, rehab_type: str,
                                    **kwargs) -> Dict[str, Any]:
        """创建康复训练计划"""
        try:
            rehab_id = f"rh_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = REHABILITATION_TYPES.get(rehab_type, {})
            goals = kwargs.get('goals')
            if isinstance(goals, (list, dict)):
                goals = json.dumps(goals, ensure_ascii=False)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO rehabilitation_plans ( rehab_id, student_id, rehab_type, therapist, frequency, duration_weeks, goals, start_date, end_date, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?) ''', (rehab_id, student_id, rehab_type,
                          kwargs.get('therapist'),
                          kwargs.get('frequency', f"{config.get('weekly_sessions', 2)}次/周"),
                          kwargs.get('duration_weeks', 12), goals,
                          kwargs.get('start_date', now[:10]),
                          kwargs.get('end_date'), now, now))
                    conn.commit()
                    logger.info(f'创建康复计划: {rehab_id} 学生 {student_id}')
                    return {'success': True, 'rehab_id': rehab_id}
        except Exception as e:
            logger.error(f'创建康复计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_rehab_session(self, rehab_id: str, **kwargs) -> Dict[str, Any]:
        """记录康复训练"""
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT student_id FROM rehabilitation_plans WHERE rehab_id = ?', (rehab_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '康复计划不存在'}
                    student_id = row[0]
                    cursor.execute(''' INSERT INTO rehabilitation_records ( rehab_id, student_id, session_date, duration, content, response, progress_note, therapist, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (rehab_id, student_id,
                          kwargs.get('session_date', now[:10]),
                          kwargs.get('duration', 45),
                          kwargs.get('content'), kwargs.get('response'),
                          kwargs.get('progress_note'),
                          kwargs.get('therapist'), now))
                    conn.commit()
                    logger.info(f'记录康复训练: {rehab_id}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'记录康复训练失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_rehab_progress(self, student_id: str) -> Dict[str, Any]:
        """获取学生康复进度"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM rehabilitation_plans WHERE student_id = ? ORDER BY created_at DESC',
                (student_id,))
                plans = [dict(p) for p in cursor.fetchall()]
                for plan in plans:
                    cursor.execute('SELECT * FROM rehabilitation_records WHERE rehab_id = ? ORDER BY session_date DESC',
                    (plan['rehab_id'],))
                    plan['sessions'] = [dict(r) for r in cursor.fetchall()]
                    plan['session_count'] = len(plan['sessions'])
                return {'success': True, 'student_id': student_id, 'plans': plans}
        except Exception as e:
            logger.error(f'获取康复进度失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 教师管理 ==========

    def register_special_ed_teacher(self, name: str, title: str,
                                     **kwargs) -> Dict[str, Any]:
        """注册特教教师"""
        try:
            teacher_id = f"set_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            certifications = kwargs.get('certifications')
            if isinstance(certifications, (list, dict)):
                certifications = json.dumps(certifications, ensure_ascii=False)
            specialties = kwargs.get('specialties')
            if isinstance(specialties, (list, dict)):
                specialties = json.dumps(specialties, ensure_ascii=False)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO special_ed_teachers ( teacher_id, user_id, name, title, certifications, specialties, max_students, student_count, is_active, training_hours, rating, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 1, ?, 0, ?, ?) ''', (teacher_id, kwargs.get('user_id'), name, title,
                          certifications, specialties,
                          kwargs.get('max_students', 5),
                          kwargs.get('training_hours', 0), now, now))
                    conn.commit()
                    logger.info(f'注册特教教师: {name} ({teacher_id})')
                    return {'success': True, 'teacher_id': teacher_id}
        except Exception as e:
            logger.error(f'注册特教教师失败: {e}')
            return {'success': False, 'error': str(e)}

    def match_teacher_student(self, teacher_id: str, student_id: str,
                               **kwargs) -> Dict[str, Any]:
        """师生配对"""
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_students, student_count FROM special_ed_teachers WHERE teacher_id = ?',
                    (teacher_id,))
                    teacher = cursor.fetchone()
                    if not teacher:
                        return {'success': False, 'error': '特教教师不存在'}
                    if teacher[0] and teacher[1] >= teacher[0]:
                        return {'success': False, 'error': '教师学生数已满'}
                    cursor.execute(''' INSERT INTO teacher_student_matching ( teacher_id, student_id, match_type, start_date, end_date, status, notes, created_at ) VALUES (?, ?, ?, ?, ?, 'active', ?, ?) ''', (teacher_id, student_id,
                          kwargs.get('match_type', 'primary'),
                          kwargs.get('start_date', now[:10]),
                          kwargs.get('end_date'),
                          kwargs.get('notes'), now))
                    cursor.execute('UPDATE special_ed_teachers SET student_count = student_count + 1, updated_at = ? WHERE teacher_id = ?',
                                 (now, teacher_id))
                    conn.commit()
                    logger.info(f'师生配对: 教师 {teacher_id} 学生 {student_id}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'师生配对失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_teachers(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """教师列表"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM special_ed_teachers WHERE 1=1'
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})')
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                cursor.execute(query, [page_size, (page - 1) * page_size])
                items = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'查询教师列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 家庭支持与融合 ==========

    def record_family_support(self, student_id: str, support_type: str,
                               topic: str, **kwargs) -> Dict[str, Any]:
        """记录家庭支持"""
        try:
            support_id = f"fs_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO family_supports ( support_id, student_id, support_type, topic, content, family_member, conducted_by, conducted_date, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (support_id, student_id, support_type, topic,
                          kwargs.get('content'),
                          kwargs.get('family_member'),
                          kwargs.get('conducted_by'),
                          kwargs.get('conducted_date', now[:10]), now))
                    conn.commit()
                    logger.info(f'记录家庭支持: {support_id} 学生 {student_id}')
                    return {'success': True, 'support_id': support_id}
        except Exception as e:
            logger.error(f'记录家庭支持失败: {e}')
            return {'success': False, 'error': str(e)}

    def organize_inclusion_activity(self, activity_name: str, **kwargs) -> Dict[str, Any]:
        """组织融合活动"""
        try:
            activity_id = f"ia_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO inclusion_activities ( activity_id, activity_name, activity_type, description, participant_count, special_student_count, location, start_date, end_date, organizer, outcome, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (activity_id, activity_name,
                          kwargs.get('activity_type'),
                          kwargs.get('description'),
                          kwargs.get('participant_count', 0),
                          kwargs.get('special_student_count', 0),
                          kwargs.get('location'),
                          kwargs.get('start_date'),
                          kwargs.get('end_date'),
                          kwargs.get('organizer'),
                          kwargs.get('outcome'), now))
                    conn.commit()
                    logger.info(f'组织融合活动: {activity_name} ({activity_id})')
                    return {'success': True, 'activity_id': activity_id}
        except Exception as e:
            logger.error(f'组织融合活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_inclusion_activities(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """融合活动列表"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM inclusion_activities WHERE 1=1'
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})')
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                cursor.execute(query, [page_size, (page - 1) * page_size])
                items = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'查询融合活动列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 成人职业康复 ==========

    def create_vocational_rehab(self, student_id: str, vocational_goal: str,
                                 **kwargs) -> Dict[str, Any]:
        """创建成人职业康复"""
        try:
            rehab_id = f"vr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO adult_vocational_rehab ( rehab_id, student_id, vocational_goal, skill_assessment, training_program, workplace_match, job_coach, status, start_date, completion_date, employment_outcome, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, 'planning', ?, ?, NULL, ?, ?) ''', (rehab_id, student_id, vocational_goal,
                          kwargs.get('skill_assessment'),
                          kwargs.get('training_program'),
                          kwargs.get('workplace_match'),
                          kwargs.get('job_coach'),
                          kwargs.get('start_date', now[:10]),
                          kwargs.get('completion_date'), now, now))
                    conn.commit()
                    logger.info(f'创建职业康复: {rehab_id} 学生 {student_id}')
                    return {'success': True, 'rehab_id': rehab_id}
        except Exception as e:
            logger.error(f'创建职业康复失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_vocational_rehab(self, rehab_id: str, **kwargs) -> Dict[str, Any]:
        """更新职业康复"""
        try:
            now = datetime.now().isoformat()
            allowed_fields = ['vocational_goal', 'skill_assessment', 'training_program',
                              'workplace_match', 'job_coach', 'status',
                              'start_date', 'completion_date', 'employment_outcome']
            updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
            if not updates:
                return {'success': False, 'error': '没有可更新字段'}
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
                    params = list(updates.values()) + [now, rehab_id]
                    cursor.execute(
                        f'UPDATE adult_vocational_rehab SET {set_clause}, updated_at = ? WHERE rehab_id = ?',
                        params
                    )
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '职业康复记录不存在'}
        except Exception as e:
            logger.error(f'更新职业康复失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_vocational_rehab(self, rehab_id: str) -> Dict[str, Any]:
        """获取职业康复详情"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM adult_vocational_rehab WHERE rehab_id = ?', (rehab_id,))
                row = cursor.fetchone()
                if row:
                    return {'success': True, 'rehab': dict(row)}
                return {'success': False, 'error': '职业康复记录不存在'}
        except Exception as e:
            logger.error(f'获取职业康复详情失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_statistics(self, education_type: str = None) -> Dict[str, Any]:
        """获取特殊教育统计数据"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cond = ' WHERE education_type = ?' if education_type else ''
                params = [education_type] if education_type else []

                # 学生类型分布（按残障类型）
                disability_dist = {}
                cursor.execute(
                    f'SELECT disability_type, COUNT(*) FROM special_students{cond} GROUP BY disability_type',
                    params
                )
                for row in cursor.fetchall():
                    disability_dist[row[0] or 'unknown'] = row[1]

                # IEP状态分布
                iep_status_dist = {}
                iep_query = 'SELECT p.status, COUNT(*) FROM iep_plans p'
                if education_type:
                    iep_query += ' JOIN special_students s ON p.student_id = s.student_id WHERE s.education_type = ?'
                iep_query += ' GROUP BY p.status'
                cursor.execute(iep_query, params)
                for row in cursor.fetchall():
                    iep_status_dist[row[0] or 'unknown'] = row[1]

                # 服务方式分布
                service_mode_dist = {}
                cursor.execute(
                    f'SELECT service_mode, COUNT(*) FROM special_students{cond} GROUP BY service_mode',
                    params
                )
                for row in cursor.fetchall():
                    service_mode_dist[row[0] or 'unknown'] = row[1]

                # 教师数量
                cursor.execute('SELECT COUNT(*) FROM special_ed_teachers WHERE is_active = 1')
                teacher_count = cursor.fetchone()[0]

                # 康复类型分布
                rehab_type_dist = {}
                rehab_query = 'SELECT r.rehab_type, COUNT(*) FROM rehabilitation_plans r'
                if education_type:
                    rehab_query += ' JOIN special_students s ON r.student_id = s.student_id WHERE s.education_type = ?'
                rehab_query += ' GROUP BY r.rehab_type'
                cursor.execute(rehab_query, params)
                for row in cursor.fetchall():
                    rehab_type_dist[row[0] or 'unknown'] = row[1]

                # 学生总数
                cursor.execute(f'SELECT COUNT(*) FROM special_students{cond}', params)
                student_total = cursor.fetchone()[0]

                return {'success': True, 'education_type': education_type,
                        'student_total': student_total,
                        'disability_distribution': disability_dist,
                        'iep_status_distribution': iep_status_dist,
                        'service_mode_distribution': service_mode_dist,
                        'teacher_count': teacher_count,
                        'rehab_type_distribution': rehab_type_dist}
        except Exception as e:
            logger.error(f'获取统计数据失败: {e}')
            return {'success': False, 'error': str(e)}


if __name__ == '__main__':
    service = SpecialEducationService()
    print('特殊教育服务初始化完成')
    stats = service.get_statistics()
    print(f'统计: {stats}')
