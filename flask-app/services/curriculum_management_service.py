#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 课程与教学计划管理服务 (v15.3.0)
====================================
提供课程管理、教学计划、课表编排和教学进度追踪等综合服务。

核心能力：
1. 课程管理 - 课程创建、大纲管理、课程配置
2. 教学计划 - 学期/周/课时计划管理
3. 课表编排 - 自动排课、冲突检测
4. 教学进度 - 课时进度追踪、教学日志
5. 课程大纲 - 知识点体系、教学目标
6. 教学资源 - 课件、教案关联管理
7. 成人课程 - 成人教育课程管理
8. K12课程 - 九年制义务教育课程管理
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'curriculum_management_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('CurriculumManagement')


# ========== 课程配置 ==========

# 课程类型
COURSE_TYPES = {
    'compulsory': {'name': '必修课', 'color': '#f5222d', 'credit': 4},
    'elective': {'name': '选修课', 'color': '#1890ff', 'credit': 2},
    'general': {'name': '通识课', 'color': '#52c41a', 'credit': 1},
    'practical': {'name': '实践课', 'color': '#faad14', 'credit': 3},
    'activity': {'name': '活动课', 'color': '#722ed1', 'credit': 1},
    'project': {'name': '项目课', 'color': '#eb2f96', 'credit': 3}
}

# 教学计划类型
PLAN_TYPES = {
    'semester': {'name': '学期计划', 'description': '整学期教学规划'},
    'monthly': {'name': '月度计划', 'description': '月度教学安排'},
    'weekly': {'name': '周计划', 'description': '每周教学计划'},
    'daily': {'name': '课时计划', 'description': '单节课教学设计'},
    'unit': {'name': '单元计划', 'description': '单元教学设计'}
}

# 课表时段
TIME_SLOTS = {
    1: {'name': '第一节', 'start': '08:00', 'end': '08:45'},
    2: {'name': '第二节', 'start': '08:55', 'end': '09:40'},
    3: {'name': '第三节', 'start': '10:00', 'end': '10:45'},
    4: {'name': '第四节', 'start': '10:55', 'end': '11:40'},
    5: {'name': '第五节', 'start': '13:30', 'end': '14:15'},
    6: {'name': '第六节', 'start': '14:25', 'end': '15:10'},
    7: {'name': '第七节', 'start': '15:30', 'end': '16:15'},
    8: {'name': '第八节', 'start': '16:25', 'end': '17:10'},
    9: {'name': '第九节', 'start': '18:30', 'end': '19:15'},
    10: {'name': '第十节', 'start': '19:25', 'end': '20:10'}
}

# 星期
WEEKDAYS = {
    1: '周一', 2: '周二', 3: '周三', 4: '周四', 5: '周五', 6: '周六', 7: '周日'
}

# 课程状态
COURSE_STATUS = {
    'draft': '草稿',
    'published': '已发布',
    'ongoing': '进行中',
    'completed': '已完成',
    'archived': '已归档'
}

# 教学进度状态
PROGRESS_STATUS = {
    'not_started': '未开始',
    'in_progress': '进行中',
    'completed': '已完成',
    'delayed': '已延期',
    'skipped': '已跳过'
}

# 成人教育课程分类
ADULT_COURSE_CATEGORIES = {
    'language_basic': {'name': '语言基础', 'subjects': ['日语入门', '日语初级', '英语基础']},
    'language_intermediate': {'name': '语言进阶', 'subjects': ['日语中级', '日语高级', '英语进阶']},
    'listening': {'name': '听力训练', 'subjects': ['日语听力', '英语听力']},
    'professional': {'name': '职业技能', 'subjects': ['商务日语', 'IT日语', '翻译实务']},
    'exam_prep': {'name': '考试备考', 'subjects': ['JLPT备考', 'J.TEST备考', '托业备考']}
}

# K12课程分类
K12_COURSE_CATEGORIES = {
    'core': {'name': '核心课程', 'subjects': ['语文', '数学', '英语']},
    'science': {'name': '理科课程', 'subjects': ['物理', '化学', '生物']},
    'humanities': {'name': '文科课程', 'subjects': ['政治', '历史', '地理']},
    'arts': {'name': '艺术课程', 'subjects': ['音乐', '美术']},
    'pe': {'name': '体育课程', 'subjects': ['体育', '健康']},
    'it': {'name': '信息技术', 'subjects': ['信息技术', '编程入门']}
}


class CurriculumManagementService:
    """课程与教学计划管理服务"""

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
                    CREATE TABLE IF NOT EXISTS courses (
                        course_id TEXT PRIMARY KEY,
                        course_name TEXT NOT NULL,
                        course_code TEXT UNIQUE,
                        education_type TEXT NOT NULL,
                        subject TEXT,
                        category TEXT,
                        course_type TEXT DEFAULT 'compulsory',
                        grade_level INTEGER,
                        description TEXT,
                        objectives TEXT,
                        credit REAL DEFAULT 0,
                        total_hours INTEGER DEFAULT 36,
                        theory_hours INTEGER DEFAULT 30,
                        practice_hours INTEGER DEFAULT 6,
                        semester TEXT,
                        prerequisite TEXT,
                        status TEXT DEFAULT 'draft',
                        created_by INTEGER,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS course_syllabus (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        course_id TEXT NOT NULL,
                        chapter TEXT NOT NULL,
                        chapter_title TEXT NOT NULL,
                        section TEXT,
                        section_title TEXT,
                        knowledge_points TEXT,
                        teaching_objectives TEXT,
                        teaching_methods TEXT,
                        estimated_hours INTEGER DEFAULT 2,
                        difficulty INTEGER DEFAULT 3,
                        sort_order INTEGER DEFAULT 0,
                        UNIQUE(course_id, chapter, section)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS teaching_plans (
                        plan_id TEXT PRIMARY KEY,
                        plan_name TEXT NOT NULL,
                        plan_type TEXT DEFAULT 'semester',
                        course_id TEXT NOT NULL,
                        teacher_id INTEGER,
                        class_id TEXT,
                        education_type TEXT,
                        semester TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        total_weeks INTEGER DEFAULT 18,
                        weekly_hours INTEGER DEFAULT 2,
                        objectives TEXT,
                        content TEXT,
                        assessment_method TEXT,
                        status TEXT DEFAULT 'draft',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS plan_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        plan_id TEXT NOT NULL,
                        week_number INTEGER,
                        session_number INTEGER,
                        date TEXT,
                        topic TEXT NOT NULL,
                        content TEXT,
                        knowledge_points TEXT,
                        teaching_methods TEXT,
                        materials TEXT,
                        homework TEXT,
                        estimated_hours INTEGER DEFAULT 2,
                        status TEXT DEFAULT 'not_started',
                        completed_at TEXT,
                        remark TEXT,
                        UNIQUE(plan_id, week_number, session_number)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS schedules (
                        schedule_id TEXT PRIMARY KEY,
                        class_id TEXT NOT NULL,
                        course_id TEXT,
                        teacher_id INTEGER,
                        weekday INTEGER NOT NULL,
                        time_slot INTEGER NOT NULL,
                        subject TEXT,
                        classroom TEXT,
                        semester TEXT,
                        is_active INTEGER DEFAULT 1,
                        note TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        UNIQUE(class_id, weekday, time_slot, semester)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS teaching_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        plan_id TEXT,
                        plan_item_id TEXT,
                        course_id TEXT,
                        teacher_id INTEGER,
                        class_id TEXT,
        date TEXT NOT NULL,
                        topic TEXT,
                        content TEXT,
                        actual_hours REAL,
                        attendance_count INTEGER,
                        total_students INTEGER,
                        method_used TEXT,
                        effectiveness TEXT,
                        issues TEXT,
                        improvements TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS course_teachers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        course_id TEXT NOT NULL,
                        teacher_id INTEGER NOT NULL,
                        role TEXT DEFAULT 'primary',
                        assigned_at TEXT,
                        UNIQUE(course_id, teacher_id)
                    )
                ''')
                conn.commit()
                logger.info('课程与教学计划服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    def create_course(self, course_name: str, education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            course_id = f"crs_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            objectives = json.dumps(kwargs.get('objectives'), ensure_ascii=False) if kwargs.get('objectives') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO courses (
                            course_id, course_name, course_code, education_type, subject,
                            category, course_type, grade_level, description, objectives,
                            credit, total_hours, theory_hours, practice_hours,
                            semester, prerequisite, status, created_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        course_id, course_name, kwargs.get('course_code'),
                        education_type, kwargs.get('subject'), kwargs.get('category'),
                        kwargs.get('course_type', 'compulsory'), kwargs.get('grade_level'),
                        kwargs.get('description'), objectives,
                        kwargs.get('credit', 0), kwargs.get('total_hours', 36),
                        kwargs.get('theory_hours', 30), kwargs.get('practice_hours', 6),
                        kwargs.get('semester'), kwargs.get('prerequisite'),
                        kwargs.get('status', 'draft'), kwargs.get('created_by'), now, now
                    ))
                    conn.commit()
                    logger.info(f'创建课程: {course_name} ({course_id})')
                    return {'success': True, 'course_id': course_id, 'course_name': course_name}
        except Exception as e:
            logger.error(f'创建课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_course(self, course_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM courses WHERE course_id = ?', (course_id,))
                row = cursor.fetchone()
                if row:
                    course = dict(row)
                    if course.get('objectives'):
                        course['objectives'] = json.loads(course['objectives'])
                    cursor.execute('SELECT * FROM course_syllabus WHERE course_id = ? ORDER BY sort_order, chapter, section', (course_id,))
                    course['syllabus'] = [dict(s) for s in cursor.fetchall()]
                    return course
                return None
        except Exception as e:
            logger.error(f'获取课程失败: {e}')
            return None

    def list_courses(self, education_type: str = None, subject: str = None,
                     course_type: str = None, status: str = None,
                     page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM courses WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if subject:
                    query += ' AND subject = ?'
                    params.append(subject)
                if course_type:
                    query += ' AND course_type = ?'
                    params.append(course_type)
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
            logger.error(f'获取课程列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_syllabus_item(self, course_id: str, chapter: str, chapter_title: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            kps = json.dumps(kwargs.get('knowledge_points'), ensure_ascii=False) if kwargs.get('knowledge_points') else None
            objectives = json.dumps(kwargs.get('teaching_objectives'), ensure_ascii=False) if kwargs.get('teaching_objectives') else None
            methods = json.dumps(kwargs.get('teaching_methods'), ensure_ascii=False) if kwargs.get('teaching_methods') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO course_syllabus (
                            course_id, chapter, chapter_title, section, section_title,
                            knowledge_points, teaching_objectives, teaching_methods,
                            estimated_hours, difficulty, sort_order
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (course_id, chapter, chapter_title,
                          kwargs.get('section'), kwargs.get('section_title'),
                          kps, objectives, methods,
                          kwargs.get('estimated_hours', 2),
                          kwargs.get('difficulty', 3),
                          kwargs.get('sort_order', 0)))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加大纲项失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_teaching_plan(self, plan_name: str, course_id: str,
                              plan_type: str = 'semester', **kwargs) -> Dict[str, Any]:
        try:
            plan_id = f"plan_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            content = json.dumps(kwargs.get('content'), ensure_ascii=False) if kwargs.get('content') else None
            objectives = json.dumps(kwargs.get('objectives'), ensure_ascii=False) if kwargs.get('objectives') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO teaching_plans (
                            plan_id, plan_name, plan_type, course_id, teacher_id,
                            class_id, education_type, semester, start_date, end_date,
                            total_weeks, weekly_hours, objectives, content,
                            assessment_method, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (plan_id, plan_name, plan_type, course_id,
                          kwargs.get('teacher_id'), kwargs.get('class_id'),
                          kwargs.get('education_type'), kwargs.get('semester'),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('total_weeks', 18), kwargs.get('weekly_hours', 2),
                          objectives, content, kwargs.get('assessment_method'),
                          kwargs.get('status', 'draft'), now, now))
                    conn.commit()
                    logger.info(f'创建教学计划: {plan_name} ({plan_id})')
                    return {'success': True, 'plan_id': plan_id}
        except Exception as e:
            logger.error(f'创建教学计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_plan_item(self, plan_id: str, week_number: int, topic: str, **kwargs) -> Dict[str, Any]:
        try:
            kps = json.dumps(kwargs.get('knowledge_points'), ensure_ascii=False) if kwargs.get('knowledge_points') else None
            methods = json.dumps(kwargs.get('teaching_methods'), ensure_ascii=False) if kwargs.get('teaching_methods') else None
            materials = json.dumps(kwargs.get('materials'), ensure_ascii=False) if kwargs.get('materials') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO plan_items (
                            plan_id, week_number, session_number, date, topic,
                            content, knowledge_points, teaching_methods, materials,
                            homework, estimated_hours, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (plan_id, week_number, kwargs.get('session_number', 1),
                          kwargs.get('date'), topic, kwargs.get('content'),
                          kps, methods, materials, kwargs.get('homework'),
                          kwargs.get('estimated_hours', 2),
                          kwargs.get('status', 'not_started')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加计划项失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_plan_item_status(self, plan_id: str, week_number: int,
                                 session_number: int, status: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE plan_items SET status = ?, completed_at = ?, remark = ?
                        WHERE plan_id = ? AND week_number = ? AND session_number = ?
                    ''', (status, now if status == 'completed' else None,
                          kwargs.get('remark'), plan_id, week_number, session_number))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'更新计划项状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_teaching_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM teaching_plans WHERE plan_id = ?', (plan_id,))
                row = cursor.fetchone()
                if row:
                    plan = dict(row)
                    if plan.get('objectives'):
                        plan['objectives'] = json.loads(plan['objectives'])
                    if plan.get('content'):
                        plan['content'] = json.loads(plan['content'])
                    cursor.execute('SELECT * FROM plan_items WHERE plan_id = ? ORDER BY week_number, session_number', (plan_id,))
                    plan['items'] = [dict(i) for i in cursor.fetchall()]
                    return plan
                return None
        except Exception as e:
            logger.error(f'获取教学计划失败: {e}')
            return None

    def list_teaching_plans(self, course_id: str = None, teacher_id: int = None,
                             plan_type: str = None, semester: str = None,
                             page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM teaching_plans WHERE 1=1'
                params = []
                if course_id:
                    query += ' AND course_id = ?'
                    params.append(course_id)
                if teacher_id:
                    query += ' AND teacher_id = ?'
                    params.append(teacher_id)
                if plan_type:
                    query += ' AND plan_type = ?'
                    params.append(plan_type)
                if semester:
                    query += ' AND semester = ?'
                    params.append(semester)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                plans = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'plans': plans, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取教学计划列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_teaching_progress(self, plan_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT total_weeks, weekly_hours FROM teaching_plans WHERE plan_id = ?', (plan_id,))
                plan = cursor.fetchone()
                if not plan:
                    return {'success': False, 'error': '计划不存在'}
                cursor.execute('SELECT status, COUNT(*) FROM plan_items WHERE plan_id = ? GROUP BY status', (plan_id,))
                status_counts = {r[0]: r[1] for r in cursor.fetchall()}
                total_items = sum(status_counts.values())
                completed = status_counts.get('completed', 0)
                in_progress = status_counts.get('in_progress', 0)
                not_started = status_counts.get('not_started', 0)
                delayed = status_counts.get('delayed', 0)
                return {
                    'success': True,
                    'total_items': total_items,
                    'completed': completed,
                    'in_progress': in_progress,
                    'not_started': not_started,
                    'delayed': delayed,
                    'progress_rate': round(completed / total_items * 100, 2) if total_items > 0 else 0
                }
        except Exception as e:
            logger.error(f'获取教学进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_schedule(self, class_id: str, weekday: int, time_slot: int,
                     **kwargs) -> Dict[str, Any]:
        try:
            schedule_id = f"sch_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT schedule_id FROM schedules
                        WHERE class_id = ? AND weekday = ? AND time_slot = ?
                        AND semester = ? AND is_active = 1
                    ''', (class_id, weekday, time_slot, kwargs.get('semester')))
                    if cursor.fetchone():
                        return {'success': False, 'error': '该时段已有课程安排'}
                    if kwargs.get('teacher_id'):
                        cursor.execute('''
                            SELECT schedule_id FROM schedules
                            WHERE teacher_id = ? AND weekday = ? AND time_slot = ?
                            AND semester = ? AND is_active = 1
                        ''', (kwargs['teacher_id'], weekday, time_slot, kwargs.get('semester')))
                        if cursor.fetchone():
                            return {'success': False, 'error': '教师该时段已有课程'}
                    cursor.execute('''
                        INSERT INTO schedules (
                            schedule_id, class_id, course_id, teacher_id, weekday,
                            time_slot, subject, classroom, semester, is_active, note, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
                    ''', (schedule_id, class_id, kwargs.get('course_id'),
                          kwargs.get('teacher_id'), weekday, time_slot,
                          kwargs.get('subject'), kwargs.get('classroom'),
                          kwargs.get('semester'), kwargs.get('note'), now, now))
                    conn.commit()
                    logger.info(f'添加课表: {schedule_id}')
                    return {'success': True, 'schedule_id': schedule_id}
        except Exception as e:
            logger.error(f'添加课表失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_class_schedule(self, class_id: str, semester: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM schedules WHERE class_id = ? AND is_active = 1'
                params = [class_id]
                if semester:
                    query += ' AND semester = ?'
                    params.append(semester)
                query += ' ORDER BY weekday, time_slot'
                cursor.execute(query, params)
                schedules = [dict(s) for s in cursor.fetchall()]
                timetable = {}
                for s in schedules:
                    day = s['weekday']
                    slot = s['time_slot']
                    if day not in timetable:
                        timetable[day] = {}
                    timetable[day][slot] = s
                return {'success': True, 'timetable': timetable, 'raw': schedules}
        except Exception as e:
            logger.error(f'获取课表失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_teacher_schedule(self, teacher_id: int, semester: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM schedules WHERE teacher_id = ? AND is_active = 1'
                params = [teacher_id]
                if semester:
                    query += ' AND semester = ?'
                    params.append(semester)
                query += ' ORDER BY weekday, time_slot'
                cursor.execute(query, params)
                schedules = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'schedules': schedules}
        except Exception as e:
            logger.error(f'获取教师课表失败: {e}')
            return {'success': False, 'error': str(e)}

    def remove_schedule(self, schedule_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE schedules SET is_active = 0 WHERE schedule_id = ?', (schedule_id,))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'移除课表失败: {e}')
            return {'success': False, 'error': str(e)}

    def log_teaching(self, teacher_id: int, date: str, topic: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO teaching_logs (
                            plan_id, plan_item_id, course_id, teacher_id, class_id,
                            date, topic, content, actual_hours, attendance_count,
                            total_students, method_used, effectiveness, issues,
                            improvements, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (kwargs.get('plan_id'), kwargs.get('plan_item_id'),
                          kwargs.get('course_id'), teacher_id, kwargs.get('class_id'),
                          date, topic, kwargs.get('content'),
                          kwargs.get('actual_hours'), kwargs.get('attendance_count'),
                          kwargs.get('total_students'), kwargs.get('method_used'),
                          kwargs.get('effectiveness'), kwargs.get('issues'),
                          kwargs.get('improvements'), now))
                    log_id = cursor.lastrowid
                    conn.commit()
                    logger.info(f'记录教学日志: {log_id}')
                    return {'success': True, 'log_id': log_id}
        except Exception as e:
            logger.error(f'记录教学日志失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_teaching_logs(self, teacher_id: int = None, course_id: str = None,
                           class_id: str = None, start_date: str = None,
                           end_date: str = None, page: int = 1,
                           page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM teaching_logs WHERE 1=1'
                params = []
                if teacher_id:
                    query += ' AND teacher_id = ?'
                    params.append(teacher_id)
                if course_id:
                    query += ' AND course_id = ?'
                    params.append(course_id)
                if class_id:
                    query += ' AND class_id = ?'
                    params.append(class_id)
                if start_date:
                    query += ' AND date >= ?'
                    params.append(start_date)
                if end_date:
                    query += ' AND date <= ?'
                    params.append(end_date)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                logs = [dict(l) for l in cursor.fetchall()]
                return {'success': True, 'logs': logs, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取教学日志失败: {e}')
            return {'success': False, 'error': str(e)}

    def assign_teacher(self, course_id: str, teacher_id: int,
                        role: str = 'primary') -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR IGNORE INTO course_teachers (course_id, teacher_id, role, assigned_at)
                        VALUES (?, ?, ?, ?)
                    ''', (course_id, teacher_id, role, now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'分配教师失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_course_teachers(self, course_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM course_teachers WHERE course_id = ?', (course_id,))
                teachers = [dict(t) for t in cursor.fetchall()]
                return {'success': True, 'teachers': teachers}
        except Exception as e:
            logger.error(f'获取课程教师失败: {e}')
            return {'success': False, 'error': str(e)}
