#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 校园后勤服务 (v15.4.0)
====================================
提供校园设施管理、报修维修、宿舍管理和物资管理等综合服务。

核心能力：
1. 设施管理 - 教室/实验室/运动场管理
2. 报修维修 - 在线报修、维修派工、进度追踪
3. 宿舍管理 - 宿舍分配、住宿管理
4. 物资管理 - 物资库存、领用、采购
5. 校车管理 - 校车路线、乘车登记
6. 食堂管理 - 菜单管理、用餐统计
7. 安保管理 - 来访登记、巡更记录
8. 成人后勤 - 成人教育后勤保障
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'campus_logistics_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('CampusLogistics')


# ========== 后勤配置 ==========

# 设施类型
FACILITY_TYPES = {
    'classroom': {'name': '教室', 'icon': 'classroom'},
    'lab': {'name': '实验室', 'icon': 'lab'},
    'library': {'name': '图书馆', 'icon': 'library'},
    'gym': {'name': '体育馆', 'icon': 'gym'},
    'playground': {'name': '运动场', 'icon': 'playground'},
    'auditorium': {'name': '报告厅', 'icon': 'auditorium'},
    'meeting_room': {'name': '会议室', 'icon': 'meeting'},
    'office': {'name': '办公室', 'icon': 'office'},
    'parking': {'name': '停车场', 'icon': 'parking'},
    'warehouse': {'name': '仓库', 'icon': 'warehouse'}
}

# 设施状态
FACILITY_STATUS = {
    'available': {'name': '可用', 'color': '#52c41a'},
    'in_use': {'name': '使用中', 'color': '#1890ff'},
    'reserved': {'name': '已预约', 'color': '#faad14'},
    'maintenance': {'name': '维修中', 'color': '#f5222d'},
    'closed': {'name': '已关闭', 'color': '#8c8c8c'}
}

# 报修类型
REPAIR_TYPES = {
    'electrical': {'name': '电气故障', 'priority': 3, 'response_hours': 4},
    'plumbing': {'name': '水管故障', 'priority': 3, 'response_hours': 4},
    'furniture': {'name': '家具损坏', 'priority': 2, 'response_hours': 24},
    'network': {'name': '网络故障', 'priority': 3, 'response_hours': 2},
    'ac': {'name': '空调故障', 'priority': 2, 'response_hours': 8},
    'door_window': {'name': '门窗损坏', 'priority': 2, 'response_hours': 24},
    'projector': {'name': '投影仪故障', 'priority': 3, 'response_hours': 2},
    'other': {'name': '其他', 'priority': 1, 'response_hours': 48}
}

# 报修状态
REPAIR_STATUS = {
    'pending': {'name': '待处理', 'color': '#f5222d'},
    'assigned': {'name': '已派工', 'color': '#faad14'},
    'in_progress': {'name': '维修中', 'color': '#1890ff'},
    'completed': {'name': '已完成', 'color': '#52c41a'},
    'verified': {'name': '已验收', 'color': '#52c41a'},
    'cancelled': {'name': '已取消', 'color': '#8c8c8c'}
}

# 宿舍类型
DORM_TYPES = {
    'single': {'name': '单人间', 'capacity': 1, 'monthly_fee': 800},
    'double': {'name': '双人间', 'capacity': 2, 'monthly_fee': 500},
    'quad': {'name': '四人间', 'capacity': 4, 'monthly_fee': 300},
    'six': {'name': '六人间', 'capacity': 6, 'monthly_fee': 200}
}

# 物资类型
MATERIAL_TYPES = {
    'stationery': {'name': '办公用品', 'unit': '件'},
    'cleaning': {'name': '清洁用品', 'unit': '瓶'},
    'maintenance': {'name': '维修材料', 'unit': '件'},
    'medical': {'name': '医疗用品', 'unit': '盒'},
    'sports': {'name': '体育用品', 'unit': '件'},
    'it': {'name': 'IT设备', 'unit': '台'},
    'furniture': {'name': '家具', 'unit': '件'},
    'book': {'name': '图书', 'unit': '本'}
}


class CampusLogisticsService:
    """校园后勤服务"""

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
                    CREATE TABLE IF NOT EXISTS facilities (
                        facility_id TEXT PRIMARY KEY,
        facility_name TEXT NOT NULL,
                        facility_type TEXT NOT NULL,
                        location TEXT,
                        floor INTEGER,
                        capacity INTEGER DEFAULT 0,
                        area REAL DEFAULT 0,
                        status TEXT DEFAULT 'available',
                        equipment TEXT,
                        responsible_person TEXT,
                        responsible_phone TEXT,
                        description TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS facility_reservations (
                        reservation_id TEXT PRIMARY KEY,
                        facility_id TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        purpose TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        attendees INTEGER DEFAULT 1,
                        status TEXT DEFAULT 'pending',
                        approved_by INTEGER,
                        approved_at TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS repair_requests (
                        repair_id TEXT PRIMARY KEY,
        repair_no TEXT UNIQUE,
                        facility_id TEXT,
                        location TEXT,
                        repair_type TEXT NOT NULL,
                        description TEXT NOT NULL,
                        urgency INTEGER DEFAULT 2,
                        reporter_id INTEGER,
                        reporter_name TEXT,
                        reporter_phone TEXT,
                        photos TEXT,
                        status TEXT DEFAULT 'pending',
                        assigned_to TEXT,
                        assigned_at TEXT,
                        completed_at TEXT,
                        verified_at TEXT,
                        verified_by INTEGER,
                        repair_cost REAL DEFAULT 0,
                        repair_notes TEXT,
                        feedback TEXT,
                        feedback_rating INTEGER,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS dormitories (
                        dorm_id TEXT PRIMARY KEY,
                        building TEXT NOT NULL,
                        floor INTEGER,
                        room_number TEXT NOT NULL,
                        dorm_type TEXT DEFAULT 'quad',
                        capacity INTEGER DEFAULT 4,
                        current_occupancy INTEGER DEFAULT 0,
                        gender_restriction TEXT,
                        monthly_fee REAL DEFAULT 300,
                        status TEXT DEFAULT 'available',
                        facilities TEXT,
                        responsible_person TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS dorm_assignments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        dorm_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        bed_number INTEGER,
                        check_in_date TEXT,
                        check_out_date TEXT,
                        status TEXT DEFAULT 'active',
                        deposit REAL DEFAULT 0,
                        remark TEXT,
                        created_at TEXT,
                        UNIQUE(dorm_id, bed_number)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS materials (
                        material_id TEXT PRIMARY KEY,
                        material_name TEXT NOT NULL,
                        material_type TEXT,
                        specification TEXT,
                        unit TEXT DEFAULT '件',
                        stock_quantity INTEGER DEFAULT 0,
                        min_stock INTEGER DEFAULT 10,
                        max_stock INTEGER DEFAULT 100,
                        unit_price REAL DEFAULT 0,
                        total_value REAL DEFAULT 0,
                        location TEXT,
                        supplier TEXT,
                        last_restocked TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS material_transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        material_id TEXT NOT NULL,
                        transaction_type TEXT NOT NULL,
                        quantity INTEGER NOT NULL,
                        unit_price REAL,
                        total_price REAL,
                        operator_id INTEGER,
                        operator_name TEXT,
                        department TEXT,
                        purpose TEXT,
                        transaction_date TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS bus_routes (
                        route_id TEXT PRIMARY KEY,
                        route_name TEXT NOT NULL,
                        driver_name TEXT,
                        driver_phone TEXT,
                        plate_number TEXT,
                        capacity INTEGER DEFAULT 30,
                        current_passengers INTEGER DEFAULT 0,
                        stops TEXT,
                        departure_time TEXT,
                        return_time TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS bus_registrations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        route_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        pickup_stop TEXT,
                        days_of_week TEXT,
                        semester TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        UNIQUE(route_id, student_id, semester)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS visitor_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        visitor_name TEXT NOT NULL,
                        visitor_phone TEXT,
        id_number TEXT,
                        visit_purpose TEXT,
                        host_name TEXT,
                        host_department TEXT,
                        check_in_time TEXT,
                        check_out_time TEXT,
                        vehicle_plate TEXT,
                        temperature REAL,
                        is_approved INTEGER DEFAULT 0,
                        approved_by INTEGER,
                        created_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('校园后勤服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 设施管理 ==========

    def add_facility(self, facility_name: str, facility_type: str, **kwargs) -> Dict[str, Any]:
        try:
            facility_id = f"fac_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            equipment = json.dumps(kwargs.get('equipment'), ensure_ascii=False) if kwargs.get('equipment') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO facilities (
                            facility_id, facility_name, facility_type, location, floor,
                            capacity, area, status, equipment, responsible_person,
                            responsible_phone, description, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (facility_id, facility_name, facility_type,
                          kwargs.get('location'), kwargs.get('floor'),
                          kwargs.get('capacity', 0), kwargs.get('area', 0),
                          kwargs.get('status', 'available'), equipment,
                          kwargs.get('responsible_person'), kwargs.get('responsible_phone'),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'添加设施: {facility_name} ({facility_id})')
                    return {'success': True, 'facility_id': facility_id}
        except Exception as e:
            logger.error(f'添加设施失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_facility(self, facility_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM facilities WHERE facility_id = ?', (facility_id,))
                row = cursor.fetchone()
                if row:
                    f = dict(row)
                    if f.get('equipment'):
                        f['equipment'] = json.loads(f['equipment'])
                    return f
                return None
        except Exception as e:
            logger.error(f'获取设施失败: {e}')
            return None

    def list_facilities(self, facility_type: str = None, status: str = None,
                         page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM facilities WHERE 1=1'
                params = []
                if facility_type:
                    query += ' AND facility_type = ?'
                    params.append(facility_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                facilities = [dict(f) for f in cursor.fetchall()]
                return {'success': True, 'facilities': facilities, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取设施列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def reserve_facility(self, facility_id: str, user_id: int,
                          start_time: str, end_time: str, **kwargs) -> Dict[str, Any]:
        try:
            reservation_id = f"res_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM facilities WHERE facility_id = ?', (facility_id,))
                    fac = cursor.fetchone()
                    if not fac:
                        return {'success': False, 'error': '设施不存在'}
                    if fac[0] not in ('available', 'reserved'):
                        return {'success': False, 'error': f'设施状态不允许预约: {fac[0]}'}
                    cursor.execute('''
                        SELECT reservation_id FROM facility_reservations
                        WHERE facility_id = ? AND status IN ('pending', 'approved')
                        AND (start_time < ? AND end_time > ?)
                    ''', (facility_id, end_time, start_time))
                    if cursor.fetchone():
                        return {'success': False, 'error': '该时段已被预约'}
                    cursor.execute('''
                        INSERT INTO facility_reservations (
                            reservation_id, facility_id, user_id, user_name,
                            purpose, start_time, end_time, attendees,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                    ''', (reservation_id, facility_id, user_id,
                          kwargs.get('user_name'), kwargs.get('purpose'),
                          start_time, end_time, kwargs.get('attendees', 1), now, now))
                    conn.commit()
                    logger.info(f'预约设施: {reservation_id}')
                    return {'success': True, 'reservation_id': reservation_id}
        except Exception as e:
            logger.error(f'预约设施失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_reservation(self, reservation_id: str, approved_by: int,
                             approved: bool) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE facility_reservations SET status = ?, approved_by = ?, approved_at = ?, updated_at = ?
                        WHERE reservation_id = ? AND status = 'pending'
                    ''', (status, approved_by, now, now, reservation_id))
                    conn.commit()
                    return {'success': True, 'status': status}
        except Exception as e:
            logger.error(f'审批预约失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 报修管理 ==========

    def submit_repair(self, repair_type: str, description: str,
                       **kwargs) -> Dict[str, Any]:
        try:
            repair_id = f"rep_{uuid.uuid4().hex[:12]}"
            repair_no = f"RP{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
            now = datetime.now().isoformat()
            photos = json.dumps(kwargs.get('photos'), ensure_ascii=False) if kwargs.get('photos') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO repair_requests (
                            repair_id, repair_no, facility_id, location, repair_type,
                            description, urgency, reporter_id, reporter_name, reporter_phone,
                            photos, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                    ''', (repair_id, repair_no, kwargs.get('facility_id'),
                          kwargs.get('location'), repair_type, description,
                          kwargs.get('urgancy', 2), kwargs.get('reporter_id'),
                          kwargs.get('reporter_name'), kwargs.get('reporter_phone'),
                          photos, now, now))
                    conn.commit()
                    logger.info(f'提交报修: {repair_no} ({repair_id})')
                    return {'success': True, 'repair_id': repair_id, 'repair_no': repair_no}
        except Exception as e:
            logger.error(f'提交报修失败: {e}')
            return {'success': False, 'error': str(e)}

    def assign_repair(self, repair_id: str, assigned_to: str,
                       **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE repair_requests SET status = 'assigned', assigned_to = ?,
                            assigned_at = ?, updated_at = ?
                        WHERE repair_id = ? AND status = 'pending'
                    ''', (assigned_to, now, now, repair_id))
                    conn.commit()
                    logger.info(f'派工报修: {repair_id} -> {assigned_to}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'派工报修失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_repair(self, repair_id: str, repair_notes: str,
                         repair_cost: float = 0, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE repair_requests SET status = 'completed', completed_at = ?,
                            repair_notes = ?, repair_cost = ?, updated_at = ?
                        WHERE repair_id = ? AND status IN ('assigned', 'in_progress')
                    ''', (now, repair_notes, repair_cost, now, repair_id))
                    conn.commit()
                    logger.info(f'完成报修: {repair_id}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'完成报修失败: {e}')
            return {'success': False, 'error': str(e)}

    def verify_repair(self, repair_id: str, verified_by: int,
                       feedback: str = None, rating: int = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE repair_requests SET status = 'verified', verified_at = ?,
                            verified_by = ?, feedback = ?, feedback_rating = ?, updated_at = ?
                        WHERE repair_id = ? AND status = 'completed'
                    ''', (now, verified_by, feedback, rating, now, repair_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'验收报修失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_repair_requests(self, status: str = None, repair_type: str = None,
                             reporter_id: int = None, page: int = 1,
                             page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM repair_requests WHERE 1=1'
                params = []
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                if repair_type:
                    query += ' AND repair_type = ?'
                    params.append(repair_type)
                if reporter_id:
                    query += ' AND reporter_id = ?'
                    params.append(reporter_id)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                repairs = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'repairs': repairs, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取报修列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 宿舍管理 ==========

    def add_dormitory(self, building: str, room_number: str, **kwargs) -> Dict[str, Any]:
        try:
            dorm_id = f"drm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            dorm_type = kwargs.get('dorm_type', 'quad')
            capacity = kwargs.get('capacity', DORM_TYPES.get(dorm_type, {}).get('capacity', 4))
            monthly_fee = kwargs.get('monthly_fee', DORM_TYPES.get(dorm_type, {}).get('monthly_fee', 300))
            facilities = json.dumps(kwargs.get('facilities'), ensure_ascii=False) if kwargs.get('facilities') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO dormitories (
                            dorm_id, building, floor, room_number, dorm_type,
                            capacity, current_occupancy, gender_restriction,
                            monthly_fee, status, facilities, responsible_person, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, 'available', ?, ?, ?, ?)
                    ''', (dorm_id, building, kwargs.get('floor'), room_number,
                          dorm_type, capacity, kwargs.get('gender_restriction'),
                          monthly_fee, facilities, kwargs.get('responsible_person'), now, now))
                    conn.commit()
                    logger.info(f'添加宿舍: {building}-{room_number} ({dorm_id})')
                    return {'success': True, 'dorm_id': dorm_id}
        except Exception as e:
            logger.error(f'添加宿舍失败: {e}')
            return {'success': False, 'error': str(e)}

    def assign_dormitory(self, dorm_id: str, student_id: int,
                          bed_number: int, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT capacity, current_occupancy, status FROM dormitories WHERE dorm_id = ?', (dorm_id,))
                    dorm = cursor.fetchone()
                    if not dorm:
                        return {'success': False, 'error': '宿舍不存在'}
                    if dorm[2] != 'available':
                        return {'success': False, 'error': f'宿舍状态不允许分配: {dorm[2]}'}
                    if dorm[1] <= dorm[0]:
                        return {'success': False, 'error': '宿舍已满'}
                    cursor.execute('SELECT id FROM dorm_assignments WHERE dorm_id = ? AND bed_number = ? AND status = ?', (dorm_id, bed_number, 'active'))
                    if cursor.fetchone():
                        return {'success': False, 'error': '该床位已被占用'}
                    cursor.execute('''
                        INSERT INTO dorm_assignments (dorm_id, student_id, bed_number, check_in_date, status, deposit, remark, created_at)
                        VALUES (?, ?, ?, ?, 'active', ?, ?, ?)
                    ''', (dorm_id, student_id, bed_number,
                          kwargs.get('check_in_date', now[:10]),
                          kwargs.get('deposit', 0), kwargs.get('remark'), now))
                    cursor.execute('UPDATE dormitories SET current_occupancy = current_occupancy + 1, status = CASE WHEN current_occupancy + 1 >= capacity THEN "full" ELSE status END, updated_at = ? WHERE dorm_id = ?', (now, dorm_id))
                    conn.commit()
                    logger.info(f'分配宿舍: {dorm_id} 床位{bed_number} -> 学生{student_id}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'分配宿舍失败: {e}')
            return {'success': False, 'error': str(e)}

    def check_out_dormitory(self, dorm_id: str, student_id: int,
                              check_out_date: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            check_out = check_out_date or now[:10]
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE dorm_assignments SET status = 'checked_out', check_out_date = ?
                        WHERE dorm_id = ? AND student_id = ? AND status = 'active'
                    ''', (check_out, dorm_id, student_id))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE dormitories SET current_occupancy = MAX(current_occupancy - 1, 0), status = "available", updated_at = ? WHERE dorm_id = ?', (now, dorm_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'退宿失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_available_dorms(self, dorm_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = "SELECT * FROM dormitories WHERE status = 'available' AND current_occupancy < capacity"
                params = []
                if dorm_type:
                    query += ' AND dorm_type = ?'
                    params.append(dorm_type)
                cursor.execute(query, params)
                dorms = [dict(d) for d in cursor.fetchall()]
                return {'success': True, 'dorms': dorms, 'count': len(dorms)}
        except Exception as e:
            logger.error(f'获取可用宿舍失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 物资管理 ==========

    def add_material(self, material_name: str, **kwargs) -> Dict[str, Any]:
        try:
            material_id = f"mat_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO materials (
                            material_id, material_name, material_type, specification,
                            unit, stock_quantity, min_stock, max_stock, unit_price,
                            total_value, location, supplier, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (material_id, material_name, kwargs.get('material_type'),
                          kwargs.get('specification'), kwargs.get('unit', '件'),
                          kwargs.get('stock_quantity', 0), kwargs.get('min_stock', 10),
                          kwargs.get('max_stock', 100), kwargs.get('unit_price', 0),
                          kwargs.get('stock_quantity', 0) * kwargs.get('unit_price', 0),
                          kwargs.get('location'), kwargs.get('supplier'), now, now))
                    conn.commit()
                    return {'success': True, 'material_id': material_id}
        except Exception as e:
            logger.error(f'添加物资失败: {e}')
            return {'success': False, 'error': str(e)}

    def stock_in(self, material_id: str, quantity: int, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT stock_quantity, unit_price FROM materials WHERE material_id = ?', (material_id,))
                    mat = cursor.fetchone()
                    if not mat:
                        return {'success': False, 'error': '物资不存在'}
                    new_qty = mat[0] + quantity
                    unit_price = kwargs.get('unit_price', mat[1])
                    total_value = new_qty * unit_price
                    cursor.execute('''
                        UPDATE materials SET stock_quantity = ?, unit_price = ?, total_value = ?, last_restocked = ?, updated_at = ?
                        WHERE material_id = ?
                    ''', (new_qty, unit_price, total_value, now, now, material_id))
                    cursor.execute('''
                        INSERT INTO material_transactions (material_id, transaction_type, quantity, unit_price, total_price, operator_id, operator_name, department, purpose, transaction_date, created_at)
                        VALUES (?, 'in', ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (material_id, quantity, unit_price, quantity * unit_price,
                          kwargs.get('operator_id'), kwargs.get('operator_name'),
                          kwargs.get('department'), kwargs.get('purpose', '入库'),
                          now[:10], now))
                    conn.commit()
                    return {'success': True, 'new_quantity': new_qty}
        except Exception as e:
            logger.error(f'物资入库失败: {e}')
            return {'success': False, 'error': str(e)}

    def stock_out(self, material_id: str, quantity: int, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT stock_quantity, unit_price FROM materials WHERE material_id = ?', (material_id,))
                    mat = cursor.fetchone()
                    if not mat:
                        return {'success': False, 'error': '物资不存在'}
                    if mat[0] < quantity:
                        return {'success': False, 'error': '库存不足'}
                    new_qty = mat[0] - quantity
                    total_value = new_qty * mat[1]
                    cursor.execute('UPDATE materials SET stock_quantity = ?, total_value = ?, updated_at = ? WHERE material_id = ?',
                                 (new_qty, total_value, now, material_id))
                    cursor.execute('''
                        INSERT INTO material_transactions (material_id, transaction_type, quantity, unit_price, total_price, operator_id, operator_name, department, purpose, transaction_date, created_at)
                        VALUES (?, 'out', ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (material_id, quantity, mat[1], quantity * mat[1],
                          kwargs.get('operator_id'), kwargs.get('operator_name'),
                          kwargs.get('department'), kwargs.get('purpose', '领用'),
                          now[:10], now))
                    conn.commit()
                    return {'success': True, 'new_quantity': new_qty}
        except Exception as e:
            logger.error(f'物资出库失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_low_stock_materials(self) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM materials WHERE stock_quantity <= min_stock')
                materials = [dict(m) for m in cursor.fetchall()]
                return {'success': True, 'materials': materials, 'count': len(materials)}
        except Exception as e:
            logger.error(f'获取低库存物资失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 来访管理 ==========

    def log_visitor(self, visitor_name: str, visit_purpose: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO visitor_logs (
                            visitor_name, visitor_phone, id_number, visit_purpose,
                            host_name, host_department, check_in_time, vehicle_plate,
                            temperature, is_approved, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (visitor_name, kwargs.get('visitor_phone'),
                          kwargs.get('id_number'), visit_purpose,
                          kwargs.get('host_name'), kwargs.get('host_department'),
                          now, kwargs.get('vehicle_plate'),
                          kwargs.get('temperature'), kwargs.get('is_approved', 1), now))
                    visitor_id = cursor.lastrowid
                    conn.commit()
                    return {'success': True, 'visitor_id': visitor_id}
        except Exception as e:
            logger.error(f'登记来访失败: {e}')
            return {'success': False, 'error': str(e)}

    def check_out_visitor(self, visitor_id: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE visitor_logs SET check_out_time = ? WHERE id = ? AND check_out_time IS NULL', (now, visitor_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'访客离开登记失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_visitor_logs(self, start_date: str = None, end_date: str = None,
                          page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM visitor_logs WHERE 1=1'
                params = []
                if start_date:
                    query += ' AND check_in_time >= ?'
                    params.append(start_date)
                if end_date:
                    query += ' AND check_in_time <= ?'
                    params.append(end_date)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY check_in_time DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                visitors = [dict(v) for v in cursor.fetchall()]
                return {'success': True, 'visitors': visitors, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取来访记录失败: {e}')
            return {'success': False, 'error': str(e)}
