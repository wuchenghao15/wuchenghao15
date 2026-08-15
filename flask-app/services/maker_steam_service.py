#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 创客与STEAM教育服务 (v15.9.0)
======================================
提供创客空间、STEAM课程、创新项目、机器人教育、3D打印、编程教育、
竞赛管理等综合服务，支持成人创新教育与K12 STEAM教育的差异化需求。

核心能力：
1. STEAM课程 - 科学/技术/工程/艺术/数学跨学科课程
2. 创客空间 - 创客实验室、设备工具、材料管理
3. 创新项目 - 项目式学习、创新挑战、创客马拉松
4. 机器人教育 - 机器人课程、编程、竞赛
5. 3D打印 - 3D建模、打印管理、作品库
6. 编程教育 - Scratch/Python/C++编程、算法
7. 竞赛管理 - STEAM竞赛、获奖记录
8. 成人创新与K12 STEAM差异化
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'maker_steam_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('MakerSteam')


# ========== STEAM教育配置 ==========

# STEAM学科
STEAM_DISCIPLINES = {
    'science': {'name': '科学', 'icon': '🔬'},
    'technology': {'name': '技术', 'icon': '💻'},
    'engineering': {'name': '工程', 'icon': '⚙️'},
    'arts': {'name': '艺术', 'icon': '🎨'},
    'math': {'name': '数学', 'icon': '📐'}
}

# STEAM课程类型
STEAM_COURSE_TYPES = {
    'interdisciplinary': {'name': '跨学科', 'target_age': '8-18'},
    'robotics': {'name': '机器人', 'target_age': '8-18'},
    'programming': {'name': '编程', 'target_age': '7-18'},
    '3d_printing': {'name': '3D打印', 'target_age': '10-18'},
    'electronics': {'name': '电子', 'target_age': '10-18'},
    'ai': {'name': '人工智能', 'target_age': '12-18'},
    'design': {'name': '设计', 'target_age': '8-18'},
    'maker': {'name': '创客', 'target_age': '8-18'}
}

# 创客空间类型
MAKER_SPACE_TYPES = {
    'digital': {'name': '数字创客空间', 'required_equipment': ['computer', '3d_printer', 'vr_device']},
    'physical': {'name': '实体创客空间', 'required_equipment': ['cnc', 'router', 'soldering']},
    'hybrid': {'name': '混合创客空间', 'required_equipment': ['computer', '3d_printer', 'laser_cutter']},
    'biology': {'name': '生物创客空间', 'required_equipment': ['computer', 'oscilloscope']},
    'food': {'name': '食品创客空间', 'required_equipment': ['computer']},
    'textile': {'name': '纺织创客空间', 'required_equipment': ['computer', 'soldering']}
}

# 设备类型
EQUIPMENT_TYPES = {
    '3d_printer': {'name': '3D打印机', 'status_field': 'operational'},
    'laser_cutter': {'name': '激光切割机', 'status_field': 'operational'},
    'cnc': {'name': '数控机床', 'status_field': 'operational'},
    'router': {'name': '雕刻机', 'status_field': 'operational'},
    'soldering': {'name': '焊接工具', 'status_field': 'operational'},
    'oscilloscope': {'name': '示波器', 'status_field': 'operational'},
    'drone': {'name': '无人机', 'status_field': 'operational'},
    'robot_kit': {'name': '机器人套件', 'status_field': 'operational'},
    'computer': {'name': '计算机', 'status_field': 'operational'},
    'vr_device': {'name': 'VR设备', 'status_field': 'operational'}
}

# 项目类型
PROJECT_TYPES = {
    'individual': {'name': '个人项目', 'max_members': 1},
    'team': {'name': '团队项目', 'max_members': 6},
    'class': {'name': '班级项目', 'max_members': 40},
    'competition': {'name': '竞赛项目', 'max_members': 6},
    'community': {'name': '社区项目', 'max_members': 20}
}

# 项目状态
PROJECT_STATUS = {
    'planning': {'name': '规划'},
    'in_progress': {'name': '进行中'},
    'completed': {'name': '已完成'},
    'exhibited': {'name': '已展示'},
    'awarded': {'name': '获奖'},
    'archived': {'name': '归档'}
}

# 编程语言
PROGRAMMING_LANGUAGES = {
    'scratch': {'name': 'Scratch', 'difficulty': 'beginner'},
    'python': {'name': 'Python', 'difficulty': 'intermediate'},
    'cpp': {'name': 'C++', 'difficulty': 'advanced'},
    'java': {'name': 'Java', 'difficulty': 'intermediate'},
    'javascript': {'name': 'JavaScript', 'difficulty': 'intermediate'},
    'arduino': {'name': 'Arduino', 'difficulty': 'intermediate'},
    'micropython': {'name': 'MicroPython', 'difficulty': 'intermediate'}
}

# 机器人类型
ROBOT_TYPES = {
    'lego': {'name': '乐高', 'suitable_age': '6-12'},
    'arduino': {'name': 'Arduino', 'suitable_age': '10-16'},
    'microbit': {'name': 'Micro:bit', 'suitable_age': '8-14'},
    'vex': {'name': 'VEX', 'suitable_age': '12-18'},
    'drone': {'name': '无人机', 'suitable_age': '12-18'},
    'humanoid': {'name': '人形机器人', 'suitable_age': '14-18'},
    'industrial': {'name': '工业机器人', 'suitable_age': '16+'}
}

# 竞赛级别
COMPETITION_LEVELS = {
    'school': {'name': '校级', 'level': 1},
    'city': {'name': '市级', 'level': 2},
    'provincial': {'name': '省级', 'level': 3},
    'national': {'name': '国家级', 'level': 4},
    'international': {'name': '国际', 'level': 5}
}

# 材料类别
MATERIAL_CATEGORIES = {
    'electronic': {'name': '电子材料'},
    'mechanical': {'name': '机械材料'},
    'consumable': {'name': '耗材'},
    'raw': {'name': '原材料'},
    'tool': {'name': '工具'},
    'safety': {'name': '安全用品'}
}


class MakerSteamService:
    """创客与STEAM教育管理服务"""

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
                # STEAM课程表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS steam_courses (
                        course_id TEXT PRIMARY KEY,
                        course_name TEXT NOT NULL,
                        course_type TEXT NOT NULL,
                        discipline TEXT,
                        education_type TEXT,
                        grade_level TEXT,
                        teacher_id TEXT,
                        teacher_name TEXT,
                        description TEXT,
                        objectives TEXT,
                        duration_hours INTEGER DEFAULT 32,
                        difficulty TEXT DEFAULT 'intermediate',
                        max_students INTEGER DEFAULT 30,
                        enrolled_count INTEGER DEFAULT 0,
                        materials_needed TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 课程课时表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS course_lessons_steam (
                        lesson_id TEXT PRIMARY KEY,
                        course_id TEXT NOT NULL,
                        lesson_name TEXT NOT NULL,
                        lesson_order INTEGER,
                        duration_minutes INTEGER DEFAULT 45,
                        content TEXT,
                        activity_type TEXT,
                        materials TEXT,
                        created_at TEXT
                    )
                ''')
                # 课程报名表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS steam_enrollments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        course_id TEXT NOT NULL,
                        student_id TEXT NOT NULL,
                        student_name TEXT,
                        enroll_date TEXT,
                        attendance_count INTEGER DEFAULT 0,
                        project_count INTEGER DEFAULT 0,
                        final_score REAL,
                        grade TEXT,
                        status TEXT DEFAULT 'enrolled',
                        created_at TEXT,
                        UNIQUE(course_id, student_id)
                    )
                ''')
                # 创客空间表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS maker_spaces (
                        space_id TEXT PRIMARY KEY,
                        space_name TEXT NOT NULL,
                        space_type TEXT,
                        location TEXT,
                        area REAL,
                        capacity INTEGER DEFAULT 30,
                        manager_id TEXT,
                        manager_name TEXT,
                        open_hours TEXT,
                        safety_rules TEXT,
                        status TEXT DEFAULT 'open',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 空间设备表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS space_equipment (
                        equipment_id TEXT PRIMARY KEY,
                        space_id TEXT NOT NULL,
                        equipment_name TEXT NOT NULL,
                        equipment_type TEXT,
                        brand TEXT,
                        model TEXT,
                        quantity INTEGER DEFAULT 1,
                        available_quantity INTEGER DEFAULT 1,
                        status TEXT DEFAULT 'operational',
                        purchase_date TEXT,
                        last_maintenance TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 设备预约表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS equipment_bookings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        equipment_id TEXT NOT NULL,
                        space_id TEXT,
                        user_id TEXT NOT NULL,
                        user_name TEXT,
                        booking_date TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        purpose TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT
                    )
                ''')
                # 材料库存表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS materials_inventory (
                        material_id TEXT PRIMARY KEY,
                        space_id TEXT,
                        material_name TEXT NOT NULL,
                        category TEXT,
                        unit TEXT DEFAULT '件',
                        quantity REAL DEFAULT 0,
                        min_quantity REAL DEFAULT 10,
                        unit_price REAL DEFAULT 0,
                        supplier TEXT,
                        last_restock TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 材料使用记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS material_usage (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        material_id TEXT NOT NULL,
                        space_id TEXT,
                        user_id TEXT,
                        user_name TEXT,
                        quantity_used REAL,
                        project_id TEXT,
                        usage_date TEXT,
                        purpose TEXT,
                        created_at TEXT
                    )
                ''')
                # 创新项目表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS innovation_projects (
                        project_id TEXT PRIMARY KEY,
                        project_name TEXT NOT NULL,
                        project_type TEXT,
                        discipline TEXT,
                        description TEXT,
                        objectives TEXT,
                        leader_id TEXT,
                        leader_name TEXT,
                        members TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        status TEXT DEFAULT 'planning',
                        budget REAL DEFAULT 0,
                        space_id TEXT,
                        outcome TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 项目里程碑表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS project_milestones (
                        milestone_id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        milestone_name TEXT NOT NULL,
                        target_date TEXT,
                        achieved_date TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT
                    )
                ''')
                # 项目成果表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS project_outcomes (
                        outcome_id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL,
                        outcome_type TEXT,
                        title TEXT NOT NULL,
                        description TEXT,
                        file_url TEXT,
                        rating REAL DEFAULT 0,
                        created_at TEXT
                    )
                ''')
                # 机器人项目表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS robot_projects (
                        robot_id TEXT PRIMARY KEY,
                        project_id TEXT,
                        robot_type TEXT,
                        robot_name TEXT NOT NULL,
                        controller TEXT,
                        sensors TEXT,
                        actuators TEXT,
                        program_language TEXT,
                        description TEXT,
                        performance_score REAL DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 3D打印任务表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS print_jobs (
                        job_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        user_name TEXT,
                        file_name TEXT NOT NULL,
                        file_url TEXT,
                        material TEXT,
                        color TEXT,
                        quality TEXT DEFAULT 'standard',
                        infill_percent INTEGER DEFAULT 20,
                        estimated_time INTEGER,
                        actual_time INTEGER,
                        status TEXT DEFAULT 'queued',
                        printer_id TEXT,
                        created_at TEXT,
                        completed_at TEXT
                    )
                ''')
                # STEAM竞赛表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS steam_competitions (
                        competition_id TEXT PRIMARY KEY,
                        competition_name TEXT NOT NULL,
                        competition_type TEXT,
                        level TEXT,
                        organizer TEXT,
                        description TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        registration_deadline TEXT,
                        max_participants INTEGER DEFAULT 50,
                        registered_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'open',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                # 竞赛获奖表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS competition_awards (
                        award_id TEXT PRIMARY KEY,
                        competition_id TEXT NOT NULL,
                        project_id TEXT,
                        user_id TEXT,
                        user_name TEXT,
                        award_level TEXT,
                        award_category TEXT,
                        certificate_url TEXT,
                        description TEXT,
                        awarded_date TEXT,
                        created_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('创客与STEAM教育服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== STEAM课程 ==========

    def create_course(self, course_name: str, course_type: str,
                      **kwargs) -> Dict[str, Any]:
        try:
            course_id = f"ms_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            discipline = kwargs.get('discipline')
            if isinstance(discipline, (list, dict)):
                discipline = json.dumps(discipline, ensure_ascii=False)
            objectives = kwargs.get('objectives')
            if isinstance(objectives, list):
                objectives = json.dumps(objectives, ensure_ascii=False)
            materials_needed = kwargs.get('materials_needed')
            if isinstance(materials_needed, list):
                materials_needed = json.dumps(materials_needed, ensure_ascii=False)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO steam_courses (
                            course_id, course_name, course_type, discipline,
                            education_type, grade_level, teacher_id, teacher_name,
                            description, objectives, duration_hours, difficulty,
                            max_students, enrolled_count, materials_needed,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 'active', ?, ?)
                    ''', (course_id, course_name, course_type, discipline,
                          kwargs.get('education_type'), kwargs.get('grade_level'),
                          kwargs.get('teacher_id'), kwargs.get('teacher_name'),
                          kwargs.get('description'), objectives,
                          kwargs.get('duration_hours', 32),
                          kwargs.get('difficulty', 'intermediate'),
                          kwargs.get('max_students', 30), materials_needed,
                          now, now))
                    conn.commit()
                    logger.info(f'创建STEAM课程: {course_name} ({course_id})')
                    return {'success': True, 'course_id': course_id}
        except Exception as e:
            logger.error(f'创建STEAM课程失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_lesson(self, course_id: str, lesson_name: str,
                   **kwargs) -> Dict[str, Any]:
        try:
            lesson_id = f"msl_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            materials = kwargs.get('materials')
            if isinstance(materials, list):
                materials = json.dumps(materials, ensure_ascii=False)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT COUNT(*) FROM course_lessons_steam WHERE course_id = ?', (course_id,))
                    order = (cursor.fetchone()[0] or 0) + 1
                    cursor.execute('''
                        INSERT INTO course_lessons_steam (
                            lesson_id, course_id, lesson_name, lesson_order,
                            duration_minutes, content, activity_type, materials, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (lesson_id, course_id, lesson_name, order,
                          kwargs.get('duration_minutes', 45),
                          kwargs.get('content'), kwargs.get('activity_type'),
                          materials, now))
                    conn.commit()
                    return {'success': True, 'lesson_id': lesson_id, 'lesson_order': order}
        except Exception as e:
            logger.error(f'添加课时失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_course(self, course_id: str, student_id: str,
                      **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_students, enrolled_count, status FROM steam_courses WHERE course_id = ?', (course_id,))
                    course = cursor.fetchone()
                    if not course:
                        return {'success': False, 'error': '课程不存在'}
                    if course[2] != 'active':
                        return {'success': False, 'error': '课程状态不允许报名'}
                    if course[0] and course[1] >= course[0]:
                        return {'success': False, 'error': '课程名额已满'}
                    cursor.execute('''
                        INSERT OR IGNORE INTO steam_enrollments (
                            course_id, student_id, student_name, enroll_date,
                            status, created_at
                        ) VALUES (?, ?, ?, ?, 'enrolled', ?)
                    ''', (course_id, student_id, kwargs.get('student_name'),
                          now[:10], now))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE steam_courses SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE course_id = ?',
                                     (now, course_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已报名该课程'}
        except Exception as e:
            logger.error(f'STEAM课程报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_course(self, course_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM steam_courses WHERE course_id = ?', (course_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '课程不存在'}
                course = dict(row)
                for key in ('discipline', 'objectives', 'materials_needed'):
                    if course.get(key):
                        try:
                            course[key] = json.loads(course[key])
                        except (json.JSONDecodeError, TypeError):
                            pass
                cursor.execute('SELECT * FROM course_lessons_steam WHERE course_id = ? ORDER BY lesson_order ASC', (course_id,))
                lessons = [dict(l) for l in cursor.fetchall()]
                course['lessons'] = lessons
                return {'success': True, 'course': course}
        except Exception as e:
            logger.error(f'获取STEAM课程详情失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_courses(self, page: int = 1, page_size: int = 20,
                     **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM steam_courses WHERE 1=1'
                params = []
                if filters.get('course_type'):
                    query += ' AND course_type = ?'
                    params.append(filters['course_type'])
                if filters.get('education_type'):
                    query += ' AND education_type = ?'
                    params.append(filters['education_type'])
                if filters.get('discipline'):
                    query += ' AND discipline LIKE ?'
                    params.append(f"%{filters['discipline']}%")
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取STEAM课程列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 创客空间 ==========

    def register_maker_space(self, space_name: str, space_type: str,
                             **kwargs) -> Dict[str, Any]:
        try:
            space_id = f"msp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO maker_spaces (
                            space_id, space_name, space_type, location,
                            area, capacity, manager_id, manager_name,
                            open_hours, safety_rules, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?, ?)
                    ''', (space_id, space_name, space_type,
                          kwargs.get('location'), kwargs.get('area'),
                          kwargs.get('capacity', 30),
                          kwargs.get('manager_id'), kwargs.get('manager_name'),
                          kwargs.get('open_hours'), kwargs.get('safety_rules'),
                          now, now))
                    conn.commit()
                    logger.info(f'注册创客空间: {space_name} ({space_id})')
                    return {'success': True, 'space_id': space_id}
        except Exception as e:
            logger.error(f'注册创客空间失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_equipment(self, space_id: str, equipment_name: str,
                      equipment_type: str, **kwargs) -> Dict[str, Any]:
        try:
            equipment_id = f"mse_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            qty = kwargs.get('quantity', 1)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO space_equipment (
                            equipment_id, space_id, equipment_name, equipment_type,
                            brand, model, quantity, available_quantity, status,
                            purchase_date, last_maintenance, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'operational', ?, ?, ?, ?)
                    ''', (equipment_id, space_id, equipment_name, equipment_type,
                          kwargs.get('brand'), kwargs.get('model'), qty, qty,
                          kwargs.get('purchase_date'),
                          kwargs.get('last_maintenance'), now, now))
                    conn.commit()
                    logger.info(f'添加设备: {equipment_name} ({equipment_id})')
                    return {'success': True, 'equipment_id': equipment_id}
        except Exception as e:
            logger.error(f'添加设备失败: {e}')
            return {'success': False, 'error': str(e)}

    def book_equipment(self, equipment_id: str, user_id: str,
                       **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT available_quantity, status, space_id FROM space_equipment WHERE equipment_id = ?', (equipment_id,))
                    equip = cursor.fetchone()
                    if not equip:
                        return {'success': False, 'error': '设备不存在'}
                    if equip[1] != 'operational':
                        return {'success': False, 'error': '设备不可用'}
                    if equip[0] <= 0:
                        return {'success': False, 'error': '设备库存不足'}
                    cursor.execute('''
                        INSERT INTO equipment_bookings (
                            equipment_id, space_id, user_id, user_name,
                            booking_date, start_time, end_time, purpose,
                            status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'approved', ?)
                    ''', (equipment_id, equip[2], user_id,
                          kwargs.get('user_name'),
                          kwargs.get('booking_date', now[:10]),
                          kwargs.get('start_time'), kwargs.get('end_time'),
                          kwargs.get('purpose'), now))
                    cursor.execute('UPDATE space_equipment SET available_quantity = available_quantity - 1, updated_at = ? WHERE equipment_id = ?',
                                 (now, equipment_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'预约设备失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_maker_spaces(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM maker_spaces WHERE 1=1'
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})')
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                cursor.execute(query, [page_size, (page - 1) * page_size])
                items = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取创客空间列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_equipment(self, space_id: str = None, page: int = 1,
                       page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM space_equipment WHERE 1=1'
                params = []
                if space_id:
                    query += ' AND space_id = ?'
                    params.append(space_id)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(e) for e in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取设备列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 材料管理 ==========

    def add_material(self, space_id: str, material_name: str, category: str,
                     **kwargs) -> Dict[str, Any]:
        try:
            material_id = f"msm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO materials_inventory (
                            material_id, space_id, material_name, category,
                            unit, quantity, min_quantity, unit_price,
                            supplier, last_restock, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (material_id, space_id, material_name, category,
                          kwargs.get('unit', '件'),
                          kwargs.get('quantity', 0),
                          kwargs.get('min_quantity', 10),
                          kwargs.get('unit_price', 0),
                          kwargs.get('supplier'),
                          kwargs.get('last_restock', now[:10]),
                          now, now))
                    conn.commit()
                    logger.info(f'添加材料: {material_name} ({material_id})')
                    return {'success': True, 'material_id': material_id}
        except Exception as e:
            logger.error(f'添加材料失败: {e}')
            return {'success': False, 'error': str(e)}

    def use_material(self, material_id: str, user_id: str, quantity: float,
                     **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT quantity, min_quantity, space_id, material_name FROM materials_inventory WHERE material_id = ?', (material_id,))
                    mat = cursor.fetchone()
                    if not mat:
                        return {'success': False, 'error': '材料不存在'}
                    if mat[0] < quantity:
                        return {'success': False, 'error': '库存不足'}
                    new_qty = mat[0] - quantity
                    cursor.execute('UPDATE materials_inventory SET quantity = ?, updated_at = ? WHERE material_id = ?',
                                 (new_qty, now, material_id))
                    cursor.execute('''
                        INSERT INTO material_usage (
                            material_id, space_id, user_id, user_name,
                            quantity_used, project_id, usage_date, purpose, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (material_id, mat[2], user_id, kwargs.get('user_name'),
                          quantity, kwargs.get('project_id'),
                          kwargs.get('usage_date', now[:10]),
                          kwargs.get('purpose'), now))
                    conn.commit()
                    warning = None
                    if new_qty <= mat[1]:
                        warning = f'材料[{mat[3]}]库存预警: 当前{new_qty}{",已达最低库存" + str(mat[1])}'
                    return {'success': True, 'remaining_quantity': new_qty,
                            'low_stock_warning': warning}
        except Exception as e:
            logger.error(f'使用材料失败: {e}')
            return {'success': False, 'error': str(e)}

    def restock_material(self, material_id: str, quantity: float,
                         **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT quantity FROM materials_inventory WHERE material_id = ?', (material_id,))
                    mat = cursor.fetchone()
                    if not mat:
                        return {'success': False, 'error': '材料不存在'}
                    new_qty = mat[0] + quantity
                    cursor.execute('UPDATE materials_inventory SET quantity = ?, last_restock = ?, supplier = COALESCE(?, supplier), updated_at = ? WHERE material_id = ?',
                                 (new_qty, kwargs.get('restock_date', now[:10]),
                                  kwargs.get('supplier'), now, material_id))
                    conn.commit()
                    return {'success': True, 'new_quantity': new_qty}
        except Exception as e:
            logger.error(f'补充库存失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_materials(self, space_id: str = None, page: int = 1,
                       page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM materials_inventory WHERE 1=1'
                params = []
                if space_id:
                    query += ' AND space_id = ?'
                    params.append(space_id)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(m) for m in cursor.fetchall()]
                low_stock = [m['material_name'] for m in items
                             if m['quantity'] <= m['min_quantity']]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size,
                        'low_stock_warning': low_stock if low_stock else None}
        except Exception as e:
            logger.error(f'获取材料列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 创新项目 ==========

    def create_project(self, project_name: str, project_type: str,
                       **kwargs) -> Dict[str, Any]:
        try:
            project_id = f"msp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            discipline = kwargs.get('discipline')
            if isinstance(discipline, list):
                discipline = json.dumps(discipline, ensure_ascii=False)
            members = kwargs.get('members')
            if isinstance(members, list):
                members = json.dumps(members, ensure_ascii=False)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO innovation_projects (
                            project_id, project_name, project_type, discipline,
                            description, objectives, leader_id, leader_name,
                            members, start_date, end_date, status, budget,
                            space_id, outcome, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'planning', ?, ?, NULL, ?, ?)
                    ''', (project_id, project_name, project_type, discipline,
                          kwargs.get('description'), kwargs.get('objectives'),
                          kwargs.get('leader_id'), kwargs.get('leader_name'),
                          members, kwargs.get('start_date', now[:10]),
                          kwargs.get('end_date'), kwargs.get('budget', 0),
                          kwargs.get('space_id'), now, now))
                    conn.commit()
                    logger.info(f'创建创新项目: {project_name} ({project_id})')
                    return {'success': True, 'project_id': project_id}
        except Exception as e:
            logger.error(f'创建创新项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_project_member(self, project_id: str, user_id: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT members, project_type FROM innovation_projects WHERE project_id = ?', (project_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '项目不存在'}
                    members_str = row[0] or '[]'
                    try:
                        members = json.loads(members_str)
                    except (json.JSONDecodeError, TypeError):
                        members = []
                    config = PROJECT_TYPES.get(row[1], {})
                    max_members = config.get('max_members', 6)
                    if len(members) >= max_members:
                        return {'success': False, 'error': f'成员已达上限({max_members})'}
                    new_member = {
                        'user_id': user_id,
                        'user_name': kwargs.get('user_name'),
                        'role': kwargs.get('role', 'member')
                    }
                    members.append(new_member)
                    cursor.execute('UPDATE innovation_projects SET members = ?, updated_at = ? WHERE project_id = ?',
                                 (json.dumps(members, ensure_ascii=False), now, project_id))
                    conn.commit()
                    return {'success': True, 'member_count': len(members)}
        except Exception as e:
            logger.error(f'添加项目成员失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_milestone(self, project_id: str, milestone_name: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            milestone_id = f"msm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO project_milestones (
                            milestone_id, project_id, milestone_name,
                            target_date, achieved_date, description, status, created_at
                        ) VALUES (?, ?, ?, ?, NULL, ?, 'pending', ?)
                    ''', (milestone_id, project_id, milestone_name,
                          kwargs.get('target_date'),
                          kwargs.get('description'), now))
                    conn.commit()
                    return {'success': True, 'milestone_id': milestone_id}
        except Exception as e:
            logger.error(f'创建里程碑失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_milestone(self, milestone_id: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE project_milestones
                        SET status = 'achieved', achieved_date = ?
                        WHERE milestone_id = ? AND status = 'pending'
                    ''', (kwargs.get('achieved_date', now[:10]), milestone_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '里程碑不存在或已完成'}
        except Exception as e:
            logger.error(f'完成里程碑失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_outcome(self, project_id: str, outcome_type: str, title: str,
                       **kwargs) -> Dict[str, Any]:
        try:
            outcome_id = f"mso_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO project_outcomes (
                            outcome_id, project_id, outcome_type, title,
                            description, file_url, rating, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (outcome_id, project_id, outcome_type, title,
                          kwargs.get('description'), kwargs.get('file_url'),
                          kwargs.get('rating', 0), now))
                    conn.commit()
                    logger.info(f'记录项目成果: {title} ({outcome_id})')
                    return {'success': True, 'outcome_id': outcome_id}
        except Exception as e:
            logger.error(f'记录项目成果失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_projects(self, page: int = 1, page_size: int = 20,
                      **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM innovation_projects WHERE 1=1'
                params = []
                if filters.get('project_type'):
                    query += ' AND project_type = ?'
                    params.append(filters['project_type'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                if filters.get('leader_id'):
                    query += ' AND leader_id = ?'
                    params.append(filters['leader_id'])
                if filters.get('discipline'):
                    query += ' AND discipline LIKE ?'
                    params.append(f"%{filters['discipline']}%")
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取项目列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_project(self, project_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM innovation_projects WHERE project_id = ?', (project_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '项目不存在'}
                project = dict(row)
                for key in ('discipline', 'members'):
                    if project.get(key):
                        try:
                            project[key] = json.loads(project[key])
                        except (json.JSONDecodeError, TypeError):
                            pass
                cursor.execute('SELECT * FROM project_milestones WHERE project_id = ? ORDER BY target_date ASC', (project_id,))
                project['milestones'] = [dict(m) for m in cursor.fetchall()]
                cursor.execute('SELECT * FROM project_outcomes WHERE project_id = ? ORDER BY created_at DESC', (project_id,))
                project['outcomes'] = [dict(o) for o in cursor.fetchall()]
                cursor.execute('SELECT * FROM robot_projects WHERE project_id = ?', (project_id,))
                project['robots'] = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'project': project}
        except Exception as e:
            logger.error(f'获取项目详情失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 机器人与3D打印 ==========

    def create_robot_project(self, project_id: str, robot_type: str,
                             **kwargs) -> Dict[str, Any]:
        try:
            robot_id = f"msr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            sensors = kwargs.get('sensors')
            if isinstance(sensors, list):
                sensors = json.dumps(sensors, ensure_ascii=False)
            actuators = kwargs.get('actuators')
            if isinstance(actuators, list):
                actuators = json.dumps(actuators, ensure_ascii=False)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO robot_projects (
                            robot_id, project_id, robot_type, robot_name,
                            controller, sensors, actuators, program_language,
                            description, performance_score, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (robot_id, project_id, robot_type,
                          kwargs.get('robot_name', '未命名机器人'),
                          kwargs.get('controller'), sensors, actuators,
                          kwargs.get('program_language', 'arduino'),
                          kwargs.get('description'),
                          kwargs.get('performance_score', 0), now, now))
                    conn.commit()
                    logger.info(f'创建机器人项目: {robot_type} ({robot_id})')
                    return {'success': True, 'robot_id': robot_id}
        except Exception as e:
            logger.error(f'创建机器人项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def submit_print_job(self, user_id: str, file_name: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            job_id = f"msj_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO print_jobs (
                            job_id, user_id, user_name, file_name, file_url,
                            material, color, quality, infill_percent,
                            estimated_time, actual_time, status, printer_id,
                            created_at, completed_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, 'queued', ?, ?, NULL)
                    ''', (job_id, user_id, kwargs.get('user_name'), file_name,
                          kwargs.get('file_url'), kwargs.get('material'),
                          kwargs.get('color'),
                          kwargs.get('quality', 'standard'),
                          kwargs.get('infill_percent', 20),
                          kwargs.get('estimated_time'),
                          kwargs.get('printer_id'), now))
                    conn.commit()
                    logger.info(f'提交3D打印任务: {file_name} ({job_id})')
                    return {'success': True, 'job_id': job_id}
        except Exception as e:
            logger.error(f'提交3D打印任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_print_status(self, job_id: str, status: str,
                            **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    if status == 'completed':
                        cursor.execute('''
                            UPDATE print_jobs
                            SET status = ?, actual_time = ?, completed_at = ?
                            WHERE job_id = ?
                        ''', (status, kwargs.get('actual_time'), now, job_id))
                    else:
                        cursor.execute('UPDATE print_jobs SET status = ? WHERE job_id = ?',
                                     (status, job_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '打印任务不存在'}
        except Exception as e:
            logger.error(f'更新打印状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_print_jobs(self, page: int = 1, page_size: int = 20,
                        **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM print_jobs WHERE 1=1'
                params = []
                if filters.get('user_id'):
                    query += ' AND user_id = ?'
                    params.append(filters['user_id'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                if filters.get('printer_id'):
                    query += ' AND printer_id = ?'
                    params.append(filters['printer_id'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(j) for j in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取打印任务列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 竞赛管理 ==========

    def create_competition(self, competition_name: str, competition_type: str,
                           level: str, **kwargs) -> Dict[str, Any]:
        try:
            competition_id = f"msc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO steam_competitions (
                            competition_id, competition_name, competition_type,
                            level, organizer, description, start_date, end_date,
                            registration_deadline, max_participants,
                            registered_count, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'open', ?, ?)
                    ''', (competition_id, competition_name, competition_type,
                          level, kwargs.get('organizer'),
                          kwargs.get('description'),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('registration_deadline'),
                          kwargs.get('max_participants', 50), now, now))
                    conn.commit()
                    logger.info(f'创建STEAM竞赛: {competition_name} ({competition_id})')
                    return {'success': True, 'competition_id': competition_id}
        except Exception as e:
            logger.error(f'创建STEAM竞赛失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_competition(self, competition_id: str, project_id: str,
                             **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, registered_count, status, registration_deadline FROM steam_competitions WHERE competition_id = ?', (competition_id,))
                    comp = cursor.fetchone()
                    if not comp:
                        return {'success': False, 'error': '竞赛不存在'}
                    if comp[2] != 'open':
                        return {'success': False, 'error': '竞赛报名已关闭'}
                    if comp[3] and now[:10] > comp[3]:
                        return {'success': False, 'error': '已过报名截止日期'}
                    if comp[0] and comp[1] >= comp[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('UPDATE steam_competitions SET registered_count = registered_count + 1, updated_at = ? WHERE competition_id = ?',
                                 (now, competition_id))
                    cursor.execute('UPDATE innovation_projects SET status = ? WHERE project_id = ?',
                                 ('in_progress', project_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'竞赛报名失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_award(self, competition_id: str, project_id: str, user_id: str,
                     award_level: str, **kwargs) -> Dict[str, Any]:
        try:
            award_id = f"msa_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO competition_awards (
                            award_id, competition_id, project_id, user_id,
                            user_name, award_level, award_category,
                            certificate_url, description, awarded_date, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (award_id, competition_id, project_id, user_id,
                          kwargs.get('user_name'), award_level,
                          kwargs.get('award_category'),
                          kwargs.get('certificate_url'),
                          kwargs.get('description'),
                          kwargs.get('awarded_date', now[:10]), now))
                    cursor.execute('UPDATE innovation_projects SET status = ? WHERE project_id = ?',
                                 ('awarded', project_id))
                    conn.commit()
                    logger.info(f'记录竞赛获奖: {award_level} ({award_id})')
                    return {'success': True, 'award_id': award_id}
        except Exception as e:
            logger.error(f'记录竞赛获奖失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_competitions(self, page: int = 1, page_size: int = 20,
                          **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM steam_competitions WHERE 1=1'
                params = []
                if filters.get('level'):
                    query += ' AND level = ?'
                    params.append(filters['level'])
                if filters.get('competition_type'):
                    query += ' AND competition_type = ?'
                    params.append(filters['competition_type'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取竞赛列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                # 课程类型分布
                course_query = 'SELECT course_type, COUNT(*) as cnt FROM steam_courses WHERE 1=1'
                params = []
                if education_type:
                    course_query += ' AND education_type = ?'
                    params.append(education_type)
                course_query += ' GROUP BY course_type'
                cursor.execute(course_query, params)
                course_type_dist = {row['course_type']: row['cnt'] for row in cursor.fetchall()}
                # 学科分布
                cursor.execute('SELECT discipline FROM steam_courses')
                discipline_dist = {}
                for row in cursor.fetchall():
                    disc = row['discipline']
                    if not disc:
                        continue
                    try:
                        disc_list = json.loads(disc) if isinstance(disc, str) else disc
                    except (json.JSONDecodeError, TypeError):
                        continue
                    if isinstance(disc_list, list):
                        for d in disc_list:
                            discipline_dist[d] = discipline_dist.get(d, 0) + 1
                # 项目状态分布
                cursor.execute('SELECT status, COUNT(*) as cnt FROM innovation_projects GROUP BY status')
                project_status_dist = {row['status']: row['cnt'] for row in cursor.fetchall()}
                # 设备使用率
                cursor.execute('SELECT equipment_type, quantity, available_quantity FROM space_equipment')
                equipment_usage = {}
                for row in cursor.fetchall():
                    etype = row['equipment_type']
                    if etype not in equipment_usage:
                        equipment_usage[etype] = {'total': 0, 'in_use': 0}
                    equipment_usage[etype]['total'] += row['quantity'] or 0
                    equipment_usage[etype]['in_use'] += (row['quantity'] or 0) - (row['available_quantity'] or 0)
                for etype, data in equipment_usage.items():
                    data['usage_rate'] = round(data['in_use'] / data['total'], 2) if data['total'] else 0
                # 材料库存预警
                cursor.execute('SELECT material_name, quantity, min_quantity FROM materials_inventory WHERE quantity <= min_quantity')
                low_stock = [{'material_name': row['material_name'],
                              'quantity': row['quantity'],
                              'min_quantity': row['min_quantity']} for row in cursor.fetchall()]
                # 竞赛获奖统计
                cursor.execute('SELECT award_level, COUNT(*) as cnt FROM competition_awards GROUP BY award_level')
                award_stats = {row['award_level']: row['cnt'] for row in cursor.fetchall()}
                # 综合统计
                cursor.execute('SELECT COUNT(*) as cnt FROM steam_courses')
                total_courses = cursor.fetchone()['cnt']
                cursor.execute('SELECT COUNT(*) as cnt FROM innovation_projects')
                total_projects = cursor.fetchone()['cnt']
                cursor.execute('SELECT COUNT(*) as cnt FROM maker_spaces')
                total_spaces = cursor.fetchone()['cnt']
                cursor.execute('SELECT COUNT(*) as cnt FROM steam_competitions')
                total_competitions = cursor.fetchone()['cnt']
                cursor.execute('SELECT COUNT(*) as cnt FROM print_jobs')
                total_prints = cursor.fetchone()['cnt']
                return {
                    'success': True,
                    'education_type': education_type,
                    'summary': {
                        'total_courses': total_courses,
                        'total_projects': total_projects,
                        'total_spaces': total_spaces,
                        'total_competitions': total_competitions,
                        'total_print_jobs': total_prints
                    },
                    'course_type_distribution': course_type_dist,
                    'discipline_distribution': discipline_dist,
                    'project_status_distribution': project_status_dist,
                    'equipment_usage': equipment_usage,
                    'low_stock_warning': low_stock,
                    'award_statistics': award_stats
                }
        except Exception as e:
            logger.error(f'获取统计信息失败: {e}')
            return {'success': False, 'error': str(e)}


if __name__ == '__main__':
    service = MakerSteamService()
    print('创客与STEAM教育服务初始化完成')
    stats = service.get_statistics()
    print(f'统计: {stats}')
