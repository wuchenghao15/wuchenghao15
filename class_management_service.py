#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 班级与学籍管理服务 (v15.2.0)
====================================
提供班级创建、学生学籍管理、年级班级统计和转学管理等综合服务。

核心能力：
1. 班级管理 - 创建/编辑/归档班级，班主任和科任老师配置
2. 学籍管理 - 学生入学、分班、调班、转学
3. 班级统计 - 人数、成绩、出勤统计
4. 年级管理 - 年级设置、升级管理
5. 成人班级 - 成人教育专属班级管理
6. K12班级 - 九年制义务教育班级管理
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'class_management_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ClassManagement')


# ========== 班级配置 ==========

# 教育类型
EDUCATION_TYPES = {
    'k12': {'name': 'K12教育', 'grade_range': '1-12', 'class_types': ['normal', 'elite', 'experimental']},
    'adult': {'name': '成人教育', 'grade_range': 'adult', 'class_types': ['standard', 'intensive', 'weekend']}
}

# K12年级配置
K12_GRADES = {
    'primary': {
        'name': '小学',
        'grades': {1: '一年级', 2: '二年级', 3: '三年级', 4: '四年级', 5: '五年级', 6: '六年级'},
        'subjects': ['语文', '数学', '英语', '科学', '道德与法治']
    },
    'junior': {
        'name': '初中',
        'grades': {7: '七年级', 8: '八年级', 9: '九年级'},
        'subjects': ['语文', '数学', '英语', '物理', '化学', '生物', '政治', '历史', '地理']
    },
    'senior': {
        'name': '高中',
        'grades': {10: '高一', 11: '高二', 12: '高三'},
        'subjects': ['语文', '数学', '英语', '物理', '化学', '生物', '政治', '历史', '地理']
    }
}

# 成人教育班级类型
ADULT_CLASS_TYPES = {
    'standard': {'name': '标准班', 'description': '标准进度常规学习', 'duration_weeks': 24, 'max_students': 30},
    'intensive': {'name': '强化班', 'description': '高强度密集学习', 'duration_weeks': 12, 'max_students': 20},
    'weekend': {'name': '周末班', 'description': '周末集中学习', 'duration_weeks': 36, 'max_students': 25},
    'evening': {'name': '晚班', 'description': '工作日晚间学习', 'duration_weeks': 30, 'max_students': 25},
    'one_on_one': {'name': '一对一', 'description': '个性化定制学习', 'duration_weeks': 12, 'max_students': 1}
}

# 班级状态
CLASS_STATUS = {
    'planning': '筹备中',
    'active': '进行中',
    'paused': '暂停',
    'completed': '已结业',
    'archived': '已归档'
}

# 学籍状态
ENROLLMENT_STATUS = {
    'enrolled': '在读',
    'suspended': '休学',
    'transferred': '转学',
    'graduated': '毕业',
    'dropped': '退学'
}

# 班级角色
CLASS_ROLES = {
    'head_teacher': '班主任',
    'subject_teacher': '科任老师',
    'assistant': '助教',
    'student': '学生'
}


class ClassManagementService:
    """班级与学籍管理服务"""

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
                    CREATE TABLE IF NOT EXISTS classes (
                        class_id TEXT PRIMARY KEY,
                        class_name TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        grade_level INTEGER,
                        class_type TEXT,
                        subject TEXT,
                        head_teacher_id INTEGER,
                        max_students INTEGER DEFAULT 30,
                        current_students INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'planning',
                        start_date TEXT,
                        end_date TEXT,
                        description TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS class_teachers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        class_id TEXT NOT NULL,
                        teacher_id INTEGER NOT NULL,
                        subject TEXT,
                        role TEXT DEFAULT 'subject_teacher',
                        assigned_at TEXT,
                        UNIQUE(class_id, teacher_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS class_students (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        class_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        enrollment_status TEXT DEFAULT 'enrolled',
                        enrolled_at TEXT,
                        left_at TEXT,
                        leave_reason TEXT,
                        UNIQUE(class_id, student_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS student_profiles (
                        user_id INTEGER PRIMARY KEY,
                        student_no TEXT UNIQUE,
                        education_type TEXT NOT NULL,
                        grade_level INTEGER,
                        current_class_id TEXT,
                        enrollment_date TEXT,
                        graduation_date TEXT,
                        status TEXT DEFAULT 'enrolled',
                        guardian_name TEXT,
                        guardian_phone TEXT,
                        address TEXT,
                        remark TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS transfer_records (
                        transfer_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        from_class_id TEXT,
                        to_class_id TEXT,
                        from_grade INTEGER,
                        to_grade INTEGER,
                        transfer_type TEXT,
                        reason TEXT,
                        approved_by INTEGER,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT,
                        approved_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS grade_levels (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        education_type TEXT NOT NULL,
                        grade_level INTEGER NOT NULL,
                        grade_name TEXT,
                        stage TEXT,
                        UNIQUE(education_type, grade_level)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS attendance_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        class_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        record_date TEXT NOT NULL,
                        status TEXT NOT NULL,
                        remark TEXT,
                        recorded_by INTEGER,
                        created_at TEXT,
                        UNIQUE(class_id, student_id, record_date)
                    )
                ''')
                conn.commit()
                logger.info('班级管理服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    def create_class(self, class_name: str, education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            class_id = f"cls_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO classes (
                            class_id, class_name, education_type, grade_level, class_type,
                            subject, head_teacher_id, max_students, status,
                            start_date, end_date, description, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        class_id, class_name, education_type,
                        kwargs.get('grade_level'),
                        kwargs.get('class_type'),
                        kwargs.get('subject'),
                        kwargs.get('head_teacher_id'),
                        kwargs.get('max_students', 30),
                        kwargs.get('status', 'planning'),
                        kwargs.get('start_date'),
                        kwargs.get('end_date'),
                        kwargs.get('description'),
                        now, now
                    ))
                    if kwargs.get('head_teacher_id'):
                        cursor.execute('''
                            INSERT INTO class_teachers (class_id, teacher_id, subject, role, assigned_at)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (class_id, kwargs['head_teacher_id'], kwargs.get('subject'), 'head_teacher', now))
                    conn.commit()
                    logger.info(f'创建班级: {class_name} ({class_id})')
                    return {'success': True, 'class_id': class_id, 'class_name': class_name}
        except Exception as e:
            logger.error(f'创建班级失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_class(self, class_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM classes WHERE class_id = ?', (class_id,))
                row = cursor.fetchone()
                if row: return dict(row) if row else None
        except Exception as e:
            logger.error(f'获取班级信息失败: {e}')
            return None

    def list_classes(self, education_type: str = None, status: str = None,
                     grade_level: int = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM classes WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                if grade_level:
                    query += ' AND grade_level = ?'
                    params.append(grade_level)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                rows = cursor.fetchall()
                classes = [dict(r) for r in rows]
                return {'success': True, 'classes': classes, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取班级列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_class(self, class_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            fields = []
            params = []
            for key in ['class_name', 'grade_level', 'class_type', 'subject',
                        'head_teacher_id', 'max_students', 'status',
                        'start_date', 'end_date', 'description']:
                if key in kwargs:
                    fields.append(f'{key} = ?')
                    params.append(kwargs[key])
            if not fields:
                return {'success': False, 'error': '没有需要更新的字段'}
            fields.append('updated_at = ?')
            params.append(now)
            params.append(class_id)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(f'UPDATE classes SET {", ".join(fields)} WHERE class_id = ?', params)
                    conn.commit()
                    logger.info(f'更新班级: {class_id}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'更新班级失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_student_to_class(self, class_id: str, student_id: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT current_students, max_students, status FROM classes WHERE class_id = ?', (class_id,))
                    cls = cursor.fetchone()
                    if not cls:
                        return {'success': False, 'error': '班级不存在'}
                    if cls[0] >= cls[1]:
                        return {'success': False, 'error': '班级人数已满'}
                    cursor.execute('SELECT id FROM class_students WHERE class_id = ? AND student_id = ?', (class_id, student_id))
                    if cursor.fetchone():
                        return {'success': False, 'error': '学生已在班级中'}
                    cursor.execute('''
                        INSERT INTO class_students (class_id, student_id, enrollment_status, enrolled_at)
                        VALUES (?, ?, 'enrolled', ?)
                    ''', (class_id, student_id, now))
                    cursor.execute('UPDATE classes SET current_students = current_students + 1, updated_at = ? WHERE class_id = ?', (now, class_id))
                    cursor.execute('''
                        INSERT OR IGNORE INTO student_profiles (user_id, education_type, status, created_at, updated_at)
                        SELECT ?, (SELECT education_type FROM classes WHERE class_id = ?), 'enrolled', ?, ?
                        WHERE NOT EXISTS (SELECT 1 FROM student_profiles WHERE user_id = ?)
                    ''', (student_id, class_id, now, now, student_id))
                    cursor.execute('''
                        UPDATE student_profiles SET current_class_id = ?, updated_at = ? WHERE user_id = ?
                    ''', (class_id, now, student_id))
                    conn.commit()
                    logger.info(f'学生 {student_id} 加入班级 {class_id}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加学生到班级失败: {e}')
            return {'success': False, 'error': str(e)}

    def remove_student_from_class(self, class_id: str, student_id: int, reason: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE class_students SET enrollment_status = 'dropped', left_at = ?, leave_reason = ?
                        WHERE class_id = ? AND student_id = ?
                    ''', (now, reason, class_id, student_id))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE classes SET current_students = current_students - 1, updated_at = ? WHERE class_id = ?', (now, class_id))
                    conn.commit()
                    logger.info(f'学生 {student_id} 离开班级 {class_id}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'移除学生失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_class_students(self, class_id: str, status: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT cs.*, sp.student_no, sp.grade_level, sp.status as student_status FROM class_students cs LEFT JOIN student_profiles sp ON cs.student_id = sp.user_id WHERE cs.class_id = ?'
                params = [class_id]
                if status:
                    query += ' AND cs.enrollment_status = ?'
                    params.append(status)
                cursor.execute(query, params)
                students = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'students': students, 'count': len(students)}
        except Exception as e:
            logger.error(f'获取班级学生列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def transfer_student(self, student_id: int, from_class_id: str, to_class_id: str,
                         transfer_type: str, reason: str = None) -> Dict[str, Any]:
        try:
            transfer_id = f"trf_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT grade_level, education_type FROM classes WHERE class_id = ?', (from_class_id,))
                    from_cls = cursor.fetchone()
                    cursor.execute('SELECT grade_level FROM classes WHERE class_id = ?', (to_class_id,))
                    to_cls = cursor.fetchone()
                    if not from_cls or not to_cls:
                        return {'success': False, 'error': '班级不存在'}
                    cursor.execute('''
                        INSERT INTO transfer_records (
                            transfer_id, student_id, from_class_id, to_class_id,
                            from_grade, to_grade, transfer_type, reason, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'approved', ?)
                    ''', (transfer_id, student_id, from_class_id, to_class_id,
                          from_cls[0], to_cls[0], transfer_type, reason, now))
                    cursor.execute('''
                        UPDATE class_students SET enrollment_status = 'transferred', left_at = ?
                        WHERE class_id = ? AND student_id = ?
                    ''', (now, from_class_id, student_id))
                    cursor.execute('UPDATE classes SET current_students = current_students - 1, updated_at = ? WHERE class_id = ?', (now, from_class_id))
                    cursor.execute('''
                        INSERT INTO class_students (class_id, student_id, enrollment_status, enrolled_at)
                        VALUES (?, ?, 'enrolled', ?)
                    ''', (to_class_id, student_id, now))
                    cursor.execute('UPDATE classes SET current_students = current_students + 1, updated_at = ? WHERE class_id = ?', (now, to_class_id))
                    cursor.execute('''
                        UPDATE student_profiles SET current_class_id = ?, grade_level = ?, updated_at = ? WHERE user_id = ?
                    ''', (to_class_id, to_cls[0], now, student_id))
                    conn.commit()
                    logger.info(f'学生 {student_id} 从 {from_class_id} 转学到 {to_class_id}')
                    return {'success': True, 'transfer_id': transfer_id}
        except Exception as e:
            logger.error(f'转学失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_student_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM student_profiles WHERE user_id = ?', (user_id,))
                row = cursor.fetchone()
                if row:
                    profile = dict(row)
                    cursor.execute('''
                        SELECT c.* FROM classes c
                        JOIN class_students cs ON c.class_id = cs.class_id
                        WHERE cs.student_id = ? AND cs.enrollment_status = 'enrolled'
                    ''', (user_id,))
                    classes = [dict(r) for r in cursor.fetchall()]
                    profile['current_classes'] = classes
                    return profile
                return None
        except Exception as e:
            logger.error(f'获取学生档案失败: {e}')
            return None

    def update_student_profile(self, user_id: int, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            fields = []
            params = []
            for key in ['student_no', 'education_type', 'grade_level', 'current_class_id',
                        'enrollment_date', 'graduation_date', 'status', 'guardian_name',
                        'guardian_phone', 'address', 'remark']:
                if key in kwargs:
                    fields.append(f'{key} = ?')
                    params.append(kwargs[key])
            if not fields:
                return {'success': False, 'error': '没有需要更新的字段'}
            fields.append('updated_at = ?')
            params.append(now)
            params.append(user_id)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(f'''
                        UPDATE student_profiles SET {", ".join(fields)} WHERE user_id = ?
                    ''', params)
                    if cursor.rowcount == 0:
                        cursor.execute('''
                            INSERT INTO student_profiles (user_id, created_at, updated_at) VALUES (?, ?, ?)
                        ''', (user_id, now, now))
                        cursor.execute(f'''
                            UPDATE student_profiles SET {", ".join(fields)} WHERE user_id = ?
                        ''', params)
                    conn.commit()
                    logger.info(f'更新学生档案: {user_id}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'更新学生档案失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_attendance(self, class_id: str, student_id: int, record_date: str,
                          status: str, remark: str = None, recorded_by: int = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO attendance_records (class_id, student_id, record_date, status, remark, recorded_by, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (class_id, student_id, record_date, status, remark, recorded_by, now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'记录出勤失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_attendance_stats(self, class_id: str, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = 'SELECT status, COUNT(*) as cnt FROM attendance_records WHERE class_id = ?'
                params = [class_id]
                if start_date:
                    query += ' AND record_date >= ?'
                    params.append(start_date)
                if end_date:
                    query += ' AND record_date <= ?'
                    params.append(end_date)
                query += ' GROUP BY status'
                cursor.execute(query, params)
                rows = cursor.fetchall()
                stats = {r[0]: r[1] for r in rows}
                total = sum(stats.values())
                return {
                    'success': True,
                    'stats': stats,
                    'total': total,
                    'attendance_rate': round(stats.get('present', 0) / total * 100, 2) if total > 0 else 0
                }
        except Exception as e:
            logger.error(f'获取出勤统计失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_class_statistics(self, class_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM classes WHERE class_id = ?', (class_id,))
                cls = cursor.fetchone()
                if not cls:
                    return {'success': False, 'error': '班级不存在'}
                cursor.execute('''
                    SELECT enrollment_status, COUNT(*) as cnt FROM class_students
                    WHERE class_id = ? GROUP BY enrollment_status
                ''', (class_id,))
                student_stats = {r[0]: r[1] for r in cursor.fetchall()}
                cursor.execute('SELECT COUNT(*) FROM class_teachers WHERE class_id = ?', (class_id,))
                teacher_count = cursor.fetchone()[0]
                return {
                    'success': True,
                    'class_info': dict(cls),
                    'student_stats': student_stats,
                    'teacher_count': teacher_count,
                    'total_students': cls['current_students'],
                    'occupancy_rate': round(cls['current_students'] / cls['max_students'] * 100, 2) if cls['max_students'] > 0 else 0
                }
        except Exception as e:
            logger.error(f'获取班级统计失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_teacher_to_class(self, class_id: str, teacher_id: int, subject: str = None,
                             role: str = 'subject_teacher') -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR IGNORE INTO class_teachers (class_id, teacher_id, subject, role, assigned_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (class_id, teacher_id, subject, role, now))
                    conn.commit()
                    logger.info(f'教师 {teacher_id} 加入班级 {class_id}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加教师失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_class_teachers(self, class_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM class_teachers WHERE class_id = ?', (class_id,))
                teachers = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'teachers': teachers}
        except Exception as e:
            logger.error(f'获取班级教师列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def promote_grade(self, education_type: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            promoted = 0
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT class_id, grade_level FROM classes
                        WHERE education_type = ? AND status = 'active'
                    ''', (education_type,))
                    classes = cursor.fetchall()
                    for cls_id, grade in classes:
                        if grade and grade < 12:
                            cursor.execute('''
                                UPDATE classes SET grade_level = grade_level + 1, updated_at = ? WHERE class_id = ?
                            ''', (now, cls_id))
                            promoted += 1
                    cursor.execute('''
                        UPDATE student_profiles SET grade_level = grade_level + 1, updated_at = ?
                        WHERE education_type = ? AND status = 'enrolled' AND grade_level < 12
                    ''', (now, education_type))
                    conn.commit()
                    logger.info(f'升级完成: {education_type}，涉及 {promoted} 个班级')
                    return {'success': True, 'promoted_classes': promoted}
        except Exception as e:
            logger.error(f'升级失败: {e}')
            return {'success': False, 'error': str(e)}

    def graduate_class(self, class_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE class_students SET enrollment_status = 'graduated', left_at = ?
                        WHERE class_id = ? AND enrollment_status = 'enrolled'
                    ''', (now, class_id))
                    cursor.execute('''
                        UPDATE classes SET status = 'completed', current_students = 0, updated_at = ? WHERE class_id = ?
                    ''', (now, class_id))
                    cursor.execute('''
                        UPDATE student_profiles SET status = 'graduated', graduation_date = ?, updated_at = ?
                        WHERE current_class_id = ?
                    ''', (now, now, class_id))
                    conn.commit()
                    logger.info(f'班级结业: {class_id}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'班级结业失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_transfer_history(self, student_id: int) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM transfer_records WHERE student_id = ? ORDER BY created_at DESC
                ''', (student_id,))
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records}
        except Exception as e:
            logger.error(f'获取转学记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_student_classes(self, student_id: int, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = '''
                    SELECT c.*, cs.enrollment_status, cs.enrolled_at
                    FROM classes c
                    JOIN class_students cs ON c.class_id = cs.class_id
                    WHERE cs.student_id = ?
                '''
                params = [student_id]
                if education_type:
                    query += ' AND c.education_type = ?'
                    params.append(education_type)
                query += ' ORDER BY cs.enrolled_at DESC'
                cursor.execute(query, params)
                classes = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'classes': classes}
        except Exception as e:
            logger.error(f'获取学生班级列表失败: {e}')
            return {'success': False, 'error': str(e)}
