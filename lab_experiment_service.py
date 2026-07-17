#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 实验室与实验管理服务 (v15.6.0)
====================================
提供实验室管理、实验课程、设备管理和安全监管等综合服务。

核心能力：
1. 实验室管理 - 实验室信息、开放预约、使用统计
2. 实验课程 - 实验项目管理、实验预约、成绩记录
3. 设备管理 - 设备台账、借用归还、维护保养
4. 耗材管理 - 实验耗材、入库出库、库存预警
5. 安全管理 - 安全培训、事故记录、检查整改
6. 实验报告 - 报告提交、批改评分、模板管理
7. 成人实验 - 成人教育实验实践管理
8. K12实验 - 中小学科学实验管理
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lab_experiment_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('LabExperiment')


# ========== 实验室配置 ==========

# 实验室类型
LAB_TYPES = {
    'physics': {'name': '物理实验室', 'subjects': ['物理'], 'safety_level': 2},
    'chemistry': {'name': '化学实验室', 'subjects': ['化学'], 'safety_level': 3},
    'biology': {'name': '生物实验室', 'subjects': ['生物'], 'safety_level': 2},
    'computer': {'name': '计算机实验室', 'subjects': ['信息技术', '编程'], 'safety_level': 1},
    'language': {'name': '语言实验室', 'subjects': ['外语'], 'safety_level': 1},
    'multimedia': {'name': '多媒体实验室', 'subjects': ['艺术', '设计'], 'safety_level': 1},
    'comprehensive': {'name': '综合实验室', 'subjects': ['多学科'], 'safety_level': 2},
    'science': {'name': '科学实验室', 'subjects': ['科学'], 'safety_level': 2},
    'engineering': {'name': '工程实验室', 'subjects': ['工程', '制造'], 'safety_level': 3},
    'medical': {'name': '医学实验室', 'subjects': ['医学', '护理'], 'safety_level': 3}
}

# 实验类型
EXPERIMENT_TYPES = {
    'demonstration': {'name': '演示实验', 'duration': 45, 'group_size': 1},
    'group': {'name': '分组实验', 'duration': 90, 'group_size': 4},
    'individual': {'name': '个人实验', 'duration': 90, 'group_size': 1},
    'virtual': {'name': '虚拟实验', 'duration': 60, 'group_size': 1},
    'design': {'name': '设计性实验', 'duration': 180, 'group_size': 3},
    'research': {'name': '研究性实验', 'duration': 240, 'group_size': 2},
    'verification': {'name': '验证性实验', 'duration': 90, 'group_size': 2},
    'comprehensive': {'name': '综合性实验', 'duration': 180, 'group_size': 4}
}

# 设备状态
EQUIPMENT_STATUS = {
    'normal': {'name': '正常', 'color': '#52c41a'},
    'in_use': {'name': '使用中', 'color': '#1890ff'},
    'borrowed': {'name': '已借出', 'color': '#faad14'},
    'maintenance': {'name': '维护中', 'color': '#fa8c16'},
    'repair': {'name': '维修中', 'color': '#f5222d'},
    'scrapped': {'name': '已报废', 'color': '#8c8c8c'},
    'reserved': {'name': '已预约', 'color': '#722ed1'}
}

# 耗材分类
CONSUMABLE_CATEGORIES = {
    'chemical': {'name': '化学试剂', 'unit': '瓶', 'warning_days': 30},
    'glassware': {'name': '玻璃器皿', 'unit': '个', 'warning_days': 90},
    'biology': {'name': '生物耗材', 'unit': '份', 'warning_days': 15},
    'electronic': {'name': '电子耗材', 'unit': '个', 'warning_days': 60},
    'tool': {'name': '工具量具', 'unit': '件', 'warning_days': 90},
    'material': {'name': '实验材料', 'unit': '份', 'warning_days': 30},
    'safety': {'name': '安全防护', 'unit': '件', 'warning_days': 60}
}

# 安全等级
SAFETY_LEVELS = {
    1: {'name': '一级（低风险）', 'description': '基本安全要求', 'color': '#52c41a'},
    2: {'name': '二级（中风险）', 'description': '需要防护设备', 'color': '#faad14'},
    3: {'name': '三级（高风险）', 'description': '严格安全规程', 'color': '#f5222d'},
    4: {'name': '四级（极高风险）', 'description': '特殊许可操作', 'color': '#722ed1'}
}

# 安全检查类型
SAFETY_CHECK_TYPES = {
    'daily': {'name': '日常检查', 'frequency': '每日'},
    'weekly': {'name': '周检查', 'frequency': '每周'},
    'monthly': {'name': '月度检查', 'frequency': '每月'},
    'quarterly': {'name': '季度检查', 'frequency': '每季度'},
    'special': {'name': '专项检查', 'frequency': '不定期'},
    'pre_experiment': {'name': '实验前检查', 'frequency': '每次实验前'}
}

# 实验报告状态
REPORT_STATUS = {
    'draft': {'name': '草稿', 'color': '#d9d9d9'},
    'submitted': {'name': '已提交', 'color': '#1890ff'},
    'reviewing': {'name': '批改中', 'color': '#faad14'},
    'graded': {'name': '已评分', 'color': '#52c41a'},
    'returned': {'name': '已退回', 'color': '#f5222d'}
}


class LabExperimentService:
    """实验室与实验管理服务"""

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
                    CREATE TABLE IF NOT EXISTS laboratories (
                        lab_id TEXT PRIMARY KEY,
                        lab_name TEXT NOT NULL,
                        lab_type TEXT NOT NULL,
                        location TEXT,
                        building TEXT,
                        floor INTEGER,
                        room_number TEXT,
                        area REAL,
                        capacity INTEGER DEFAULT 30,
                        manager_id INTEGER,
                        manager_name TEXT,
                        safety_level INTEGER DEFAULT 1,
        safety_rules TEXT,
                        open_time TEXT,
                        close_time TEXT,
                        is_available INTEGER DEFAULT 1,
                        description TEXT,
                        photo_url TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS lab_reservations (
                        reservation_id TEXT PRIMARY KEY,
                        lab_id TEXT NOT NULL,
                        lab_name TEXT,
                        reserved_by INTEGER,
                        reserved_by_name TEXT,
                        course_name TEXT,
                        experiment_name TEXT,
                        reserve_date TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        student_count INTEGER DEFAULT 0,
                        purpose TEXT,
                        status TEXT DEFAULT 'pending',
                        approved_by INTEGER,
                        approved_at TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS experiments (
                        experiment_id TEXT PRIMARY KEY,
                        experiment_name TEXT NOT NULL,
                        experiment_type TEXT,
                        subject TEXT,
                        lab_type TEXT,
                        education_type TEXT,
                        grade_level INTEGER,
                        description TEXT,
                        objectives TEXT,
                        materials TEXT,
                        procedure TEXT,
                        safety_notes TEXT,
                        duration_minutes INTEGER DEFAULT 90,
                        group_size INTEGER DEFAULT 2,
                        difficulty TEXT DEFAULT 'medium',
                        is_virtual INTEGER DEFAULT 0,
                        virtual_url TEXT,
                        created_by INTEGER,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS experiment_sessions (
                        session_id TEXT PRIMARY KEY,
                        experiment_id TEXT NOT NULL,
                        experiment_name TEXT,
                        lab_id TEXT,
                        lab_name TEXT,
                        teacher_id INTEGER,
                        teacher_name TEXT,
                        class_id TEXT,
                        class_name TEXT,
                        session_date TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        student_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'scheduled',
                        notes TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS lab_equipment (
                        equipment_id TEXT PRIMARY KEY,
                        equipment_name TEXT NOT NULL,
                        equipment_code TEXT UNIQUE,
                        category TEXT,
                        lab_id TEXT,
                        lab_name TEXT,
                        model TEXT,
                        manufacturer TEXT,
                        purchase_date TEXT,
                        purchase_price REAL,
                        status TEXT DEFAULT 'normal',
                        location TEXT,
                        last_maintenance TEXT,
                        next_maintenance TEXT,
                        description TEXT,
                        photo_url TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS equipment_borrows (
                        borrow_id TEXT PRIMARY KEY,
                        equipment_id TEXT NOT NULL,
                        equipment_name TEXT,
                        borrower_id INTEGER,
                        borrower_name TEXT,
                        borrow_date TEXT,
                        expected_return TEXT,
                        actual_return TEXT,
                        purpose TEXT,
                        status TEXT DEFAULT 'borrowed',
                        condition_on_borrow TEXT,
                        condition_on_return TEXT,
                        approved_by INTEGER,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS consumables (
                        consumable_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        category TEXT,
                        lab_id TEXT,
                        lab_name TEXT,
                        unit TEXT,
                        total_quantity INTEGER DEFAULT 0,
                        available_quantity INTEGER DEFAULT 0,
                        warning_threshold INTEGER DEFAULT 10,
                        unit_price REAL,
                        expiry_date TEXT,
                        storage_location TEXT,
                        supplier TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS consumable_transactions (
                        transaction_id TEXT PRIMARY KEY,
                        consumable_id TEXT NOT NULL,
                        consumable_name TEXT,
                        transaction_type TEXT,
                        quantity INTEGER,
                        operator_id INTEGER,
                        operator_name TEXT,
                        transaction_date TEXT,
                        purpose TEXT,
        related_session TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS safety_inspections (
                        inspection_id TEXT PRIMARY KEY,
                        lab_id TEXT NOT NULL,
                        lab_name TEXT,
                        inspection_type TEXT,
                        inspector TEXT,
                        inspection_date TEXT,
                        items_checked TEXT,
                        issues_found TEXT,
                        severity TEXT,
                        status TEXT DEFAULT 'open',
                        rectification TEXT,
                        rectified_at TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS safety_incidents (
                        incident_id TEXT PRIMARY KEY,
                        lab_id TEXT,
                        lab_name TEXT,
                        incident_type TEXT,
                        severity TEXT,
                        description TEXT,
                        occurred_at TEXT,
                        reported_by TEXT,
                        reported_at TEXT,
                        affected_persons TEXT,
                        cause_analysis TEXT,
                        measures TEXT,
                        status TEXT DEFAULT 'reported',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS experiment_reports (
                        report_id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        experiment_id TEXT NOT NULL,
                        experiment_name TEXT,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        group_members TEXT,
                        hypothesis TEXT,
                        procedure_detail TEXT,
                        data_record TEXT,
                        analysis TEXT,
                        conclusion TEXT,
                        reflection TEXT,
                        file_url TEXT,
                        status TEXT DEFAULT 'draft',
                        submitted_at TEXT,
                        graded_by INTEGER,
                        graded_at TEXT,
                        score REAL,
                        feedback TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('实验室与实验管理服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 实验室管理 ==========

    def create_lab(self, lab_name: str, lab_type: str,
                    **kwargs) -> Dict[str, Any]:
        try:
            lab_id = f"lab_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = LAB_TYPES.get(lab_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO laboratories (
                            lab_id, lab_name, lab_type, location, building,
                            floor, room_number, area, capacity, manager_id,
                            manager_name, safety_level, safety_rules,
                            open_time, close_time, is_available, description,
                            photo_url, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
                    ''', (lab_id, lab_name, lab_type, kwargs.get('location'),
                          kwargs.get('building'), kwargs.get('floor'),
                          kwargs.get('room_number'), kwargs.get('area'),
                          kwargs.get('capacity', 30), kwargs.get('manager_id'),
                          kwargs.get('manager_name'),
                          kwargs.get('safety_level', config.get('safety_level', 1)),
                          kwargs.get('safety_rules'),
                          kwargs.get('open_time', '08:00'),
                          kwargs.get('close_time', '22:00'),
                          kwargs.get('description'), kwargs.get('photo_url'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建实验室: {lab_name} ({lab_id})')
                    return {'success': True, 'lab_id': lab_id}
        except Exception as e:
            logger.error(f'创建实验室失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_lab(self, lab_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM laboratories WHERE lab_id = ?', (lab_id,))
                row = cursor.fetchone()
                if row:
                    lab = dict(row)
                    if lab.get('safety_rules'):
                        lab['safety_rules'] = json.loads(lab['safety_rules'])
                    return lab
                return None
        except Exception as e:
            logger.error(f'获取实验室失败: {e}')
            return None

    def list_labs(self, lab_type: str = None, is_available: bool = None,
                   page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM laboratories WHERE 1=1'
                params = []
                if lab_type:
                    query += ' AND lab_type = ?'
                    params.append(lab_type)
                if is_available is not None:
                    query += ' AND is_available = ?'
                    params.append(1 if is_available else 0)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                labs = [dict(l) for l in cursor.fetchall()]
                return {'success': True, 'labs': labs, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取实验室列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def reserve_lab(self, lab_id: str, reserved_by: int,
                     reserve_date: str, start_time: str,
                     end_time: str, **kwargs) -> Dict[str, Any]:
        try:
            reservation_id = f"lrs_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT lab_name, is_available, safety_level FROM laboratories WHERE lab_id = ?', (lab_id,))
                    lab = cursor.fetchone()
                    if not lab:
                        return {'success': False, 'error': '实验室不存在'}
                    if not lab[1]:
                        return {'success': False, 'error': '实验室不可用'}
                    cursor.execute('''
                        SELECT COUNT(*) FROM lab_reservations
                        WHERE lab_id = ? AND reserve_date = ?
                        AND ((start_time < ? AND end_time > ?) OR (start_time < ? AND end_time > ?))
                        AND status IN ('pending', 'approved')
                    ''', (lab_id, reserve_date, end_time, start_time, end_time, start_time))
                    if cursor.fetchone()[0] > 0:
                        return {'success': False, 'error': '该时段已被预约'}
                    status = 'approved' if lab[2] <= 1 else 'pending'
                    cursor.execute('''
                        INSERT INTO lab_reservations (
                            reservation_id, lab_id, lab_name, reserved_by,
                            reserved_by_name, course_name, experiment_name,
                            reserve_date, start_time, end_time, student_count,
                            purpose, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (reservation_id, lab_id, lab[0], reserved_by,
                          kwargs.get('reserved_by_name'),
                          kwargs.get('course_name'),
                          kwargs.get('experiment_name'),
                          reserve_date, start_time, end_time,
                          kwargs.get('student_count', 0),
                          kwargs.get('purpose'), status, now))
                    conn.commit()
                    logger.info(f'实验室预约: {reservation_id}, 状态: {status}')
                    return {'success': True, 'reservation_id': reservation_id, 'status': status}
        except Exception as e:
            logger.error(f'实验室预约失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_reservation(self, reservation_id: str, approved: bool,
                             approved_by: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE lab_reservations SET status = ?, approved_by = ?, approved_at = ?
                        WHERE reservation_id = ? AND status = 'pending'
                    ''', (status, approved_by, now, reservation_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '预约状态不允许审核'}
        except Exception as e:
            logger.error(f'审核预约失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 实验管理 ==========

    def create_experiment(self, experiment_name: str, experiment_type: str,
                           subject: str, **kwargs) -> Dict[str, Any]:
        try:
            experiment_id = f"exp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = EXPERIMENT_TYPES.get(experiment_type, {})
            materials = json.dumps(kwargs.get('materials'), ensure_ascii=False) if kwargs.get('materials') else None
            procedure = json.dumps(kwargs.get('procedure'), ensure_ascii=False) if kwargs.get('procedure') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO experiments (
                            experiment_id, experiment_name, experiment_type,
                            subject, lab_type, education_type, grade_level,
                            description, objectives, materials, procedure,
                            safety_notes, duration_minutes, group_size,
                            difficulty, is_virtual, virtual_url,
                            created_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (experiment_id, experiment_name, experiment_type,
                          subject, kwargs.get('lab_type'),
                          kwargs.get('education_type'), kwargs.get('grade_level'),
                          kwargs.get('description'), kwargs.get('objectives'),
                          materials, procedure, kwargs.get('safety_notes'),
                          kwargs.get('duration_minutes', config.get('duration', 90)),
                          kwargs.get('group_size', config.get('group_size', 2)),
                          kwargs.get('difficulty', 'medium'),
                          kwargs.get('is_virtual', 0), kwargs.get('virtual_url'),
                          kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建实验项目: {experiment_name} ({experiment_id})')
                    return {'success': True, 'experiment_id': experiment_id}
        except Exception as e:
            logger.error(f'创建实验项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM experiments WHERE experiment_id = ?', (experiment_id,))
                row = cursor.fetchone()
                if row:
                    exp = dict(row)
                    if exp.get('materials'):
                        exp['materials'] = json.loads(exp['materials'])
                    if exp.get('procedure'):
                        exp['procedure'] = json.loads(exp['procedure'])
                    return exp
                return None
        except Exception as e:
            logger.error(f'获取实验项目失败: {e}')
            return None

    def list_experiments(self, subject: str = None, experiment_type: str = None,
                          education_type: str = None, page: int = 1,
                          page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM experiments WHERE 1=1'
                params = []
                if subject:
                    query += ' AND subject = ?'
                    params.append(subject)
                if experiment_type:
                    query += ' AND experiment_type = ?'
                    params.append(experiment_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                experiments = [dict(e) for e in cursor.fetchall()]
                return {'success': True, 'experiments': experiments, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取实验列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def schedule_experiment(self, experiment_id: str, lab_id: str,
                             session_date: str, start_time: str,
                             end_time: str, **kwargs) -> Dict[str, Any]:
        try:
            session_id = f"ses_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT experiment_name FROM experiments WHERE experiment_id = ?', (experiment_id,))
                    exp = cursor.fetchone()
                    if not exp:
                        return {'success': False, 'error': '实验项目不存在'}
                    cursor.execute('SELECT lab_name FROM laboratories WHERE lab_id = ?', (lab_id,))
                    lab = cursor.fetchone()
                    if not lab:
                        return {'success': False, 'error': '实验室不存在'}
                    cursor.execute('''
                        INSERT INTO experiment_sessions (
                            session_id, experiment_id, experiment_name,
                            lab_id, lab_name, teacher_id, teacher_name,
                            class_id, class_name, session_date, start_time,
                            end_time, student_count, status, notes, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'scheduled', ?, ?, ?)
                    ''', (session_id, experiment_id, exp[0],
                          lab_id, lab[0], kwargs.get('teacher_id'),
                          kwargs.get('teacher_name'), kwargs.get('class_id'),
                          kwargs.get('class_name'), session_date, start_time,
                          end_time, kwargs.get('student_count', 0),
                          kwargs.get('notes'), now, now))
                    conn.commit()
                    logger.info(f'安排实验: {session_id}')
                    return {'success': True, 'session_id': session_id}
        except Exception as e:
            logger.error(f'安排实验失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 设备管理 ==========

    def add_equipment(self, equipment_name: str, category: str,
                       **kwargs) -> Dict[str, Any]:
        try:
            equipment_id = f"eqp_{uuid.uuid4().hex[:12]}"
            equipment_code = kwargs.get('equipment_code', f"EQ{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:4].upper()}")
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT lab_name FROM laboratories WHERE lab_id = ?', (kwargs.get('lab_id'),))
                    lab = cursor.fetchone()
                    cursor.execute('''
                        INSERT INTO lab_equipment (
                            equipment_id, equipment_name, equipment_code, category,
                            lab_id, lab_name, model, manufacturer, purchase_date,
                            purchase_price, status, location, last_maintenance,
                            next_maintenance, description, photo_url, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'normal', ?, ?, ?, ?, ?, ?, ?)
                    ''', (equipment_id, equipment_name, equipment_code, category,
                          kwargs.get('lab_id'), lab[0] if lab else None,
                          kwargs.get('model'), kwargs.get('manufacturer'),
                          kwargs.get('purchase_date'), kwargs.get('purchase_price'),
                          kwargs.get('location'), kwargs.get('last_maintenance'),
                          kwargs.get('next_maintenance'),
                          kwargs.get('description'), kwargs.get('photo_url'),
                          now, now))
                    conn.commit()
                    logger.info(f'添加设备: {equipment_name} ({equipment_id})')
                    return {'success': True, 'equipment_id': equipment_id, 'equipment_code': equipment_code}
        except Exception as e:
            logger.error(f'添加设备失败: {e}')
            return {'success': False, 'error': str(e)}

    def borrow_equipment(self, equipment_id: str, borrower_id: int,
                          **kwargs) -> Dict[str, Any]:
        try:
            borrow_id = f"brw_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT equipment_name, status FROM lab_equipment WHERE equipment_id = ?', (equipment_id,))
                    eq = cursor.fetchone()
                    if not eq:
                        return {'success': False, 'error': '设备不存在'}
                    if eq[1] != 'normal':
                        return {'success': False, 'error': f'设备状态不允许借出: {eq[1]}'}
                    cursor.execute('UPDATE lab_equipment SET status = ?, updated_at = ? WHERE equipment_id = ?', ('borrowed', now, equipment_id))
                    cursor.execute('''
                        INSERT INTO equipment_borrows (
                            borrow_id, equipment_id, equipment_name,
                            borrower_id, borrower_name, borrow_date,
                            expected_return, purpose, status,
                            condition_on_borrow, approved_by, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'borrowed', ?, ?, ?)
                    ''', (borrow_id, equipment_id, eq[0], borrower_id,
                          kwargs.get('borrower_name'), now[:10],
                          kwargs.get('expected_return'),
                          kwargs.get('purpose'),
                          kwargs.get('condition_on_borrow', '正常'),
                          kwargs.get('approved_by'), now))
                    conn.commit()
                    return {'success': True, 'borrow_id': borrow_id}
        except Exception as e:
            logger.error(f'借出设备失败: {e}')
            return {'success': False, 'error': str(e)}

    def return_equipment(self, borrow_id: str, condition: str = '正常',
                          **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT equipment_id FROM equipment_borrows WHERE borrow_id = ? AND status = ?', (borrow_id, 'borrowed'))
                    borrow = cursor.fetchone()
                    if not borrow:
                        return {'success': False, 'error': '借出记录不存在或已归还'}
                    cursor.execute('UPDATE equipment_borrows SET actual_return = ?, condition_on_return = ?, status = ? WHERE borrow_id = ?',
                                 (now[:10], condition, 'returned', borrow_id))
                    new_status = 'normal' if condition == '正常' else 'repair'
                    cursor.execute('UPDATE lab_equipment SET status = ?, updated_at = ? WHERE equipment_id = ?', (new_status, now, borrow[0]))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'归还设备失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_equipment(self, lab_id: str = None, category: str = None,
                        status: str = None, page: int = 1,
                        page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM lab_equipment WHERE 1=1'
                params = []
                if lab_id:
                    query += ' AND lab_id = ?'
                    params.append(lab_id)
                if category:
                    query += ' AND category = ?'
                    params.append(category)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                equipment = [dict(e) for e in cursor.fetchall()]
                return {'success': True, 'equipment': equipment, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取设备列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 耗材管理 ==========

    def add_consumable(self, name: str, category: str, **kwargs) -> Dict[str, Any]:
        try:
            consumable_id = f"cnm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = CONSUMABLE_CATEGORIES.get(category, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT lab_name FROM laboratories WHERE lab_id = ?', (kwargs.get('lab_id'),))
                    lab = cursor.fetchone()
                    cursor.execute('''
                        INSERT INTO consumables (
                            consumable_id, name, category, lab_id, lab_name,
                            unit, total_quantity, available_quantity,
                            warning_threshold, unit_price, expiry_date,
                            storage_location, supplier, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (consumable_id, name, category, kwargs.get('lab_id'),
                          lab[0] if lab else None, kwargs.get('unit', config.get('unit', '个')),
                          kwargs.get('total_quantity', 0),
                          kwargs.get('available_quantity', kwargs.get('total_quantity', 0)),
                          kwargs.get('warning_threshold', 10),
                          kwargs.get('unit_price', 0), kwargs.get('expiry_date'),
                          kwargs.get('storage_location'), kwargs.get('supplier'),
                          now, now))
                    conn.commit()
                    return {'success': True, 'consumable_id': consumable_id}
        except Exception as e:
            logger.error(f'添加耗材失败: {e}')
            return {'success': False, 'error': str(e)}

    def stock_in(self, consumable_id: str, quantity: int,
                  **kwargs) -> Dict[str, Any]:
        return self._consumable_transaction(consumable_id, quantity, 'in', **kwargs)

    def stock_out(self, consumable_id: str, quantity: int,
                   **kwargs) -> Dict[str, Any]:
        return self._consumable_transaction(consumable_id, quantity, 'out', **kwargs)

    def _consumable_transaction(self, consumable_id: str, quantity: int,
                                 txn_type: str, **kwargs) -> Dict[str, Any]:
        try:
            transaction_id = f"cnt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT name, available_quantity FROM consumables WHERE consumable_id = ?', (consumable_id,))
                    c = cursor.fetchone()
                    if not c:
                        return {'success': False, 'error': '耗材不存在'}
                    if txn_type == 'out' and c[1] < quantity:
                        return {'success': False, 'error': '库存不足'}
                    new_qty = c[1] + quantity if txn_type == 'in' else c[1] - quantity
                    cursor.execute('UPDATE consumables SET available_quantity = ?, updated_at = ? WHERE consumable_id = ?', (new_qty, now, consumable_id))
                    cursor.execute('''
                        INSERT INTO consumable_transactions (
                            transaction_id, consumable_id, consumable_name,
                            transaction_type, quantity, operator_id, operator_name,
                            transaction_date, purpose, related_session, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (transaction_id, consumable_id, c[0], txn_type, quantity,
                          kwargs.get('operator_id'), kwargs.get('operator_name'),
                          now[:10], kwargs.get('purpose'),
                          kwargs.get('related_session'), now))
                    conn.commit()
                    return {'success': True, 'new_quantity': new_qty}
        except Exception as e:
            logger.error(f'耗材出入库失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_low_stock_consumables(self, lab_id: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM consumables WHERE available_quantity <= warning_threshold'
                params = []
                if lab_id:
                    query += ' AND lab_id = ?'
                    params.append(lab_id)
                cursor.execute(query, params)
                items = [dict(i) for i in cursor.fetchall()]
                return {'success': True, 'low_stock_items': items, 'count': len(items)}
        except Exception as e:
            logger.error(f'获取低库存耗材失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 安全管理 ==========

    def create_safety_inspection(self, lab_id: str, inspection_type: str,
                                   inspector: str, **kwargs) -> Dict[str, Any]:
        try:
            inspection_id = f"sin_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT lab_name FROM laboratories WHERE lab_id = ?', (lab_id,))
                    lab = cursor.fetchone()
                    if not lab:
                        return {'success': False, 'error': '实验室不存在'}
                    items_checked = json.dumps(kwargs.get('items_checked'), ensure_ascii=False) if kwargs.get('items_checked') else None
                    issues_found = json.dumps(kwargs.get('issues_found'), ensure_ascii=False) if kwargs.get('issues_found') else None
                    cursor.execute('''
                        INSERT INTO safety_inspections (
                            inspection_id, lab_id, lab_name, inspection_type,
                            inspector, inspection_date, items_checked, issues_found,
                            severity, status, rectification, rectified_at, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?, ?, ?)
                    ''', (inspection_id, lab_id, lab[0], inspection_type,
                          inspector, kwargs.get('inspection_date', now[:10]),
                          items_checked, issues_found,
                          kwargs.get('severity', 'low'),
                          kwargs.get('rectification'),
                          kwargs.get('rectified_at'), now))
                    conn.commit()
                    logger.info(f'安全检查: {inspection_id}')
                    return {'success': True, 'inspection_id': inspection_id}
        except Exception as e:
            logger.error(f'创建安全检查失败: {e}')
            return {'success': False, 'error': str(e)}

    def report_incident(self, lab_id: str, incident_type: str,
                         description: str, **kwargs) -> Dict[str, Any]:
        try:
            incident_id = f"sid_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT lab_name FROM laboratories WHERE lab_id = ?', (lab_id,))
                    lab = cursor.fetchone()
                    lab_name = lab[0] if lab else None
                    cursor.execute('''
                        INSERT INTO safety_incidents (
                            incident_id, lab_id, lab_name, incident_type,
                            severity, description, occurred_at, reported_by,
                            reported_at, affected_persons, cause_analysis,
                            measures, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'reported', ?)
                    ''', (incident_id, lab_id, lab_name, incident_type,
                          kwargs.get('severity', 'minor'),
                          description, kwargs.get('occurred_at', now),
                          kwargs.get('reported_by', ''), now,
                          kwargs.get('affected_persons'),
                          kwargs.get('cause_analysis'),
                          kwargs.get('measures'), now))
                    conn.commit()
                    logger.warning(f'安全事故报告: {incident_id}, 类型: {incident_type}')
                    return {'success': True, 'incident_id': incident_id}
        except Exception as e:
            logger.error(f'报告安全事故失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 实验报告 ==========

    def submit_report(self, session_id: str, experiment_id: str,
                       student_id: int, **kwargs) -> Dict[str, Any]:
        try:
            report_id = f"rpt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            cursor_data = None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT experiment_name FROM experiments WHERE experiment_id = ?', (experiment_id,))
                    exp = cursor.fetchone()
                    group_members = json.dumps(kwargs.get('group_members'), ensure_ascii=False) if kwargs.get('group_members') else None
                    cursor.execute('''
                        INSERT INTO experiment_reports (
                            report_id, session_id, experiment_id, experiment_name,
                            student_id, student_name, group_members, hypothesis,
                            procedure_detail, data_record, analysis, conclusion,
                            reflection, file_url, status, submitted_at, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'submitted', ?, ?, ?)
                    ''', (report_id, session_id, experiment_id,
                          exp[0] if exp else None, student_id,
                          kwargs.get('student_name'), group_members,
                          kwargs.get('hypothesis'), kwargs.get('procedure_detail'),
                          kwargs.get('data_record'), kwargs.get('analysis'),
                          kwargs.get('conclusion'), kwargs.get('reflection'),
                          kwargs.get('file_url'), now, now, now))
                    conn.commit()
                    logger.info(f'提交实验报告: {report_id}')
                    return {'success': True, 'report_id': report_id}
        except Exception as e:
            logger.error(f'提交实验报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def grade_report(self, report_id: str, graded_by: int,
                      score: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE experiment_reports SET
                            status = 'graded', graded_by = ?, graded_at = ?,
                            score = ?, feedback = ?, updated_at = ?
                        WHERE report_id = ? AND status IN ('submitted', 'reviewing')
                    ''', (graded_by, now, score,
                          kwargs.get('feedback'), now, report_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'score': score}
                    return {'success': False, 'error': '报告状态不允许评分'}
        except Exception as e:
            logger.error(f'评分实验报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_student_reports(self, student_id: int,
                              status: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM experiment_reports WHERE student_id = ?'
                params = [student_id]
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                query += ' ORDER BY submitted_at DESC'
                cursor.execute(query, params)
                reports = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'reports': reports}
        except Exception as e:
            logger.error(f'获取学生实验报告失败: {e}')
            return {'success': False, 'error': str(e)}
