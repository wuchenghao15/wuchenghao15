from core.db_path import get_db_path as _mtscos_get_db_path
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS 校园安全保卫服务 (v15.7.0) ==================================== 提供门禁管理、巡逻检查、应急处理和安全教育等综合服务。  核心能力： 1. 门禁管理 - 出入控制、访客登记、权限管理 2. 巡逻检查 - 巡逻路线、检查记录、隐患排查 3. 应急处理 - 应急预案、事件报告、联动处置 4. 安全教育 - 安全培训、演练记录、知识考核 5. 监控管理 - 监控点位、报警记录、视频调阅 6. 消防安全 - 消防设施、检查记录、演练管理 7. 事故管理 - 事故记录、调查处理、统计分析 8. 成人与K12 - 差异化安全管理策略 """
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'campus_security_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('CampusSecurity')


# ========== 安全配置 ==========

# 门禁类型
ACCESS_POINT_TYPES = {
    'main_gate': {'name': '校门', 'level': 'high', '24h': True},
    'building': {'name': '教学楼入口', 'level': 'medium', '24h': False},
    'dormitory': {'name': '宿舍入口', 'level': 'high', '24h': True},
    'lab': {'name': '实验室入口', 'level': 'high', '24h': False},
    'library': {'name': '图书馆入口', 'level': 'low', '24h': False},
    'office': {'name': '办公区入口', 'level': 'medium', '24h': False},
    'parking': {'name': '停车场入口', 'level': 'low', '24h': True}
}

# 访客类型
VISITOR_TYPES = {
    'parent': {'name': '家长', 'pre_approved': False},
    'vendor': {'name': '供应商', 'pre_approved': True},
    'official': {'name': '公务来访', 'pre_approved': True},
    'interview': {'name': '面试人员', 'pre_approved': False},
    'delivery': {'name': '快递配送', 'pre_approved': False},
    'maintenance': {'name': '维修人员', 'pre_approved': True},
    'guest': {'name': '访客', 'pre_approved': False}
}

# 巡检类型
PATROL_TYPES = {
    'routine': {'name': '例行巡逻', 'frequency': 'daily'},
    'night': {'name': '夜间巡逻', 'frequency': 'daily'},
    'weekend': {'name': '周末巡逻', 'frequency': 'weekly'},
    'holiday': {'name': '节假日巡逻', 'frequency': 'holiday'},
    'special': {'name': '专项巡逻', 'frequency': 'as_needed'},
    'key_area': {'name': '重点区域巡逻', 'frequency': 'daily'}
}

# 应急事件类型
EMERGENCY_TYPES = {
    'fire': {'name': '火灾', 'level': 'critical', 'response_time': 3},
    'medical': {'name': '医疗急救', 'level': 'high', 'response_time': 5},
    'intrusion': {'name': '非法入侵', 'level': 'high', 'response_time': 5},
    'fight': {'name': '打架斗殴', 'level': 'medium', 'response_time': 10},
    'theft': {'name': '盗窃事件', 'level': 'medium', 'response_time': 15},
    'accident': {'name': '意外事故', 'level': 'high', 'response_time': 5},
    'natural_disaster': {'name': '自然灾害', 'level': 'critical', 'response_time': 3},
    'security_threat': {'name': '安全威胁', 'level': 'critical', 'response_time': 3},
    'lost_person': {'name': '人员走失', 'level': 'medium', 'response_time': 10},
    'equipment_failure': {'name': '设备故障', 'level': 'low', 'response_time': 30}
}

# 应急级别
EMERGENCY_LEVELS = {
    'low': {'name': '低级', 'color': '#52c41a', 'description': '一般事件'},
    'medium': {'name': '中级', 'color': '#faad14', 'description': '较大事件'},
    'high': {'name': '高级', 'color': '#f5222d', 'description': '重大事件'},
    'critical': {'name': '紧急', 'color': '#722ed1', 'description': '特大事件'}
}

# 安全培训类型
SAFETY_TRAINING_TYPES = {
    'fire_safety': {'name': '消防安全', 'frequency': 'quarterly', 'required': True},
    'earthquake': {'name': '地震安全', 'frequency': 'semiannual', 'required': True},
    'first_aid': {'name': '急救知识', 'frequency': 'annual', 'required': True},
    'traffic': {'name': '交通安全', 'frequency': 'semiannual', 'required': True},
    'food_safety': {'name': '食品安全', 'frequency': 'quarterly', 'required': True},
    'cyber_security': {'name': '网络安全', 'frequency': 'annual', 'required': False},
    'anti_bullying': {'name': '防欺凌', 'frequency': 'semiannual', 'required': True},
    'self_defense': {'name': '自我防护', 'frequency': 'annual', 'required': False}
}

# 消防设施类型
FIRE_EQUIPMENT_TYPES = {
    'extinguisher': {'name': '灭火器', 'check_interval': 30},
    'hydrant': {'name': '消火栓', 'check_interval': 90},
    'alarm': {'name': '火灾报警器', 'check_interval': 30},
    'sprinkler': {'name': '喷淋系统', 'check_interval': 90},
    'smoke_detector': {'name': '烟感探测器', 'check_interval': 30},
    'emergency_exit': {'name': '应急出口', 'check_interval': 7},
    'emergency_light': {'name': '应急照明', 'check_interval': 30},
    'fire_door': {'name': '防火门', 'check_interval': 30}
}

# 事故严重等级
INCIDENT_SEVERITY = {
    'minor': {'name': '轻微', 'color': '#52c41a', 'description': '无伤害'},
    'moderate': {'name': '一般', 'color': '#faad14', 'description': '轻微伤害'},
    'serious': {'name': '严重', 'color': '#f5222d', 'description': '需医疗处理'},
    'major': {'name': '重大', 'color': '#722ed1', 'description': '严重伤害'},
    'fatal': {'name': '特大', 'color': '#000000', 'description': '危及生命'}
}


class CampusSecurityService:
    """校园安全保卫服务"""

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
                cursor.execute(''' CREATE TABLE IF NOT EXISTS access_points ( point_id TEXT PRIMARY KEY, point_name TEXT NOT NULL, point_type TEXT NOT NULL, location TEXT, building TEXT, is_active INTEGER DEFAULT 1, open_time TEXT, close_time TEXT, is_24h INTEGER DEFAULT 0, require_card INTEGER DEFAULT 1, require_face INTEGER DEFAULT 0, description TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS access_logs ( log_id TEXT PRIMARY KEY, point_id TEXT NOT NULL, point_name TEXT, person_id INTEGER, person_name TEXT, person_type TEXT, access_type TEXT, access_time TEXT, card_no TEXT, direction TEXT, result TEXT, temperature REAL, photo_url TEXT, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS visitors ( visitor_id TEXT PRIMARY KEY, visitor_name TEXT NOT NULL, visitor_type TEXT, id_number TEXT, phone TEXT, company TEXT, purpose TEXT, host_id INTEGER, host_name TEXT, visit_date TEXT, check_in_time TEXT, check_out_time TEXT, status TEXT DEFAULT 'pending', approved_by INTEGER, approved_at TEXT, photo_url TEXT, vehicle_no TEXT, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS patrol_routes ( route_id TEXT PRIMARY KEY, route_name TEXT NOT NULL, patrol_type TEXT, description TEXT, checkpoints TEXT, estimated_duration INTEGER, is_active INTEGER DEFAULT 1, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS patrol_records ( record_id TEXT PRIMARY KEY, route_id TEXT NOT NULL, route_name TEXT, patrol_type TEXT, guard_id INTEGER, guard_name TEXT, start_time TEXT, end_time TEXT, checkpoints_visited TEXT, issues_found TEXT, status TEXT DEFAULT 'ongoing', notes TEXT, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS emergency_events ( event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL, emergency_level TEXT, title TEXT NOT NULL, description TEXT, location TEXT, occurred_at TEXT, reported_by TEXT, reported_at TEXT, response_team TEXT, response_time TEXT, resolved_at TEXT, resolution TEXT, casualties TEXT, property_loss REAL, status TEXT DEFAULT 'reported', created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS emergency_plans ( plan_id TEXT PRIMARY KEY, plan_name TEXT NOT NULL, emergency_type TEXT, description TEXT, procedures TEXT, responsible_person TEXT, contact_list TEXT, evacuation_route TEXT, assembly_point TEXT, is_active INTEGER DEFAULT 1, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS safety_trainings ( training_id TEXT PRIMARY KEY, training_type TEXT NOT NULL, title TEXT NOT NULL, trainer TEXT, training_date TEXT, location TEXT, duration_minutes INTEGER, target_audience TEXT, education_type TEXT, participant_count INTEGER DEFAULT 0, description TEXT, material_url TEXT, status TEXT DEFAULT 'scheduled', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS training_records ( id INTEGER PRIMARY KEY AUTOINCREMENT, training_id TEXT NOT NULL, student_id INTEGER, student_name TEXT, attendance INTEGER DEFAULT 0, score REAL, passed INTEGER, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS fire_equipment ( equipment_id TEXT PRIMARY KEY, equipment_type TEXT NOT NULL, location TEXT, building TEXT, floor TEXT, last_check_date TEXT, next_check_date TEXT, status TEXT DEFAULT 'normal', notes TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS fire_check_records ( check_id TEXT PRIMARY KEY, equipment_id TEXT NOT NULL, equipment_type TEXT, checker TEXT, check_date TEXT, result TEXT, status TEXT, action_taken TEXT, next_check_date TEXT, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS security_incidents ( incident_id TEXT PRIMARY KEY, incident_type TEXT, severity TEXT, title TEXT NOT NULL, description TEXT, location TEXT, occurred_at TEXT, reported_by TEXT, reported_at TEXT, involved_persons TEXT, cause TEXT, measures TEXT, follow_up TEXT, status TEXT DEFAULT 'open', resolved_at TEXT, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS surveillance_cameras ( camera_id TEXT PRIMARY KEY, camera_name TEXT NOT NULL, location TEXT, building TEXT, floor TEXT, coverage_area TEXT, is_online INTEGER DEFAULT 1, ip_address TEXT, stream_url TEXT, storage_days INTEGER DEFAULT 30, created_at TEXT, updated_at TEXT ) ''')
                conn.commit()
                logger.info('校园安全保卫服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 门禁管理 ==========

    def create_access_point(self, point_name: str, point_type: str,
                             **kwargs) -> Dict[str, Any]:
        try:
            point_id = f"acp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = ACCESS_POINT_TYPES.get(point_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO access_points ( point_id, point_name, point_type, location, building, is_active, open_time, close_time, is_24h, require_card, require_face, description, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?) ''', (point_id, point_name, point_type, kwargs.get('location'),
                          kwargs.get('building'), kwargs.get('open_time', '06:00'),
                          kwargs.get('close_time', '23:00'),
                          kwargs.get('is_24h', config.get('24h', False)),
                          kwargs.get('require_card', 1),
                          kwargs.get('require_face', 0),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建门禁点: {point_name} ({point_id})')
                    return {'success': True, 'point_id': point_id}
        except Exception as e:
            logger.error(f'创建门禁点失败: {e}')
            return {'success': False, 'error': str(e)}

    def log_access(self, point_id: str, person_id: int, person_name: str,
                    direction: str, **kwargs) -> Dict[str, Any]:
        try:
            log_id = f"alg_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT point_name FROM access_points WHERE point_id = ?', (point_id,))
                    pt = cursor.fetchone()
                    point_name = pt[0] if pt else ''
                    cursor.execute(''' INSERT INTO access_logs ( log_id, point_id, point_name, person_id, person_name, person_type, access_type, access_time, card_no, direction, result, temperature, photo_url, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (log_id, point_id, point_name, person_id, person_name,
                          kwargs.get('person_type', 'student'),
                          kwargs.get('access_type', 'card'),
                          now, kwargs.get('card_no'), direction,
                          kwargs.get('result', 'granted'),
                          kwargs.get('temperature'), kwargs.get('photo_url'), now))
                    conn.commit()
                    return {'success': True, 'log_id': log_id, 'access_time': now}
        except Exception as e:
            logger.error(f'记录门禁日志失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_access_logs(self, point_id: str = None, person_id: int = None,
                         start_date: str = None, end_date: str = None,
                         page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM access_logs WHERE 1=1'
                params = []
                if point_id:
                    query += ' AND point_id = ?'
                    params.append(point_id)
                if person_id:
                    query += ' AND person_id = ?'
                    params.append(person_id)
                if start_date:
                    query += ' AND date(access_time) >= ?'
                    params.append(start_date)
                if end_date:
                    query += ' AND date(access_time) <= ?'
                    params.append(end_date)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY access_time DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                logs = [dict(l) for l in cursor.fetchall()]
                return {'success': True, 'logs': logs, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取门禁日志失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 访客管理 ==========

    def register_visitor(self, visitor_name: str, visitor_type: str,
                          host_id: int, **kwargs) -> Dict[str, Any]:
        try:
            visitor_id = f"vst_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = VISITOR_TYPES.get(visitor_type, {})
            status = 'approved' if config.get('pre_approved') else 'pending'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO visitors ( visitor_id, visitor_name, visitor_type, id_number, phone, company, purpose, host_id, host_name, visit_date, status, photo_url, vehicle_no, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (visitor_id, visitor_name, visitor_type,
                          kwargs.get('id_number'), kwargs.get('phone'),
                          kwargs.get('company'), kwargs.get('purpose'),
                          host_id, kwargs.get('host_name'),
                          kwargs.get('visit_date', now[:10]),
                          status, kwargs.get('photo_url'),
                          kwargs.get('vehicle_no'), now))
                    conn.commit()
                    logger.info(f'访客登记: {visitor_name} ({visitor_id}), 状态: {status}')
                    return {'success': True, 'visitor_id': visitor_id, 'status': status}
        except Exception as e:
            logger.error(f'访客登记失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_visitor(self, visitor_id: str, approved: bool,
                         approved_by: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE visitors SET status = ?, approved_by = ?, approved_at = ? WHERE visitor_id = ? AND status = 'pending' ''', (status, approved_by, now, visitor_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '访客状态不允许审批'}
        except Exception as e:
            logger.error(f'审批访客失败: {e}')
            return {'success': False, 'error': str(e)}

    def check_in_visitor(self, visitor_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE visitors SET check_in_time = ?, status = 'checked_in' WHERE visitor_id = ? AND status = 'approved' ''', (now, visitor_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'check_in_time': now}
                    return {'success': False, 'error': '访客状态不允许签到'}
        except Exception as e:
            logger.error(f'访客签到失败: {e}')
            return {'success': False, 'error': str(e)}

    def check_out_visitor(self, visitor_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE visitors SET check_out_time = ?, status = 'checked_out' WHERE visitor_id = ? AND status = 'checked_in' ''', (now, visitor_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'check_out_time': now}
                    return {'success': False, 'error': '访客状态不允许签退'}
        except Exception as e:
            logger.error(f'访客签退失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 巡逻管理 ==========

    def create_patrol_route(self, route_name: str, patrol_type: str,
                             **kwargs) -> Dict[str, Any]:
        try:
            route_id = f"prt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            checkpoints = json.dumps(kwargs.get('checkpoints'),
            ensure_ascii=False) if kwargs.get('checkpoints') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO patrol_routes ( route_id, route_name, patrol_type, description, checkpoints, estimated_duration, is_active, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?) ''', (route_id, route_name, patrol_type,
                          kwargs.get('description'), checkpoints,
                          kwargs.get('estimated_duration', 60), now, now))
                    conn.commit()
                    return {'success': True, 'route_id': route_id}
        except Exception as e:
            logger.error(f'创建巡逻路线失败: {e}')
            return {'success': False, 'error': str(e)}

    def start_patrol(self, route_id: str, guard_id: int,
                      guard_name: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"plr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT route_name, patrol_type FROM patrol_routes WHERE route_id = ?', (route_id,))
                    route = cursor.fetchone()
                    if not route:
                        return {'success': False, 'error': '巡逻路线不存在'}
                    cursor.execute(''' INSERT INTO patrol_records ( record_id, route_id, route_name, patrol_type, guard_id, guard_name, start_time, status, notes, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, 'ongoing', ?, ?) ''', (record_id, route_id, route[0], route[1],
                          guard_id, guard_name, now,
                          kwargs.get('notes'), now))
                    conn.commit()
                    logger.info(f'开始巡逻: {record_id}, 路线: {route[0]}')
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'开始巡逻失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_patrol(self, record_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            checkpoints_visited = json.dumps(kwargs.get('checkpoints_visited'),
            ensure_ascii=False) if kwargs.get('checkpoints_visited') else None
            issues_found = json.dumps(kwargs.get('issues_found'),
            ensure_ascii=False) if kwargs.get('issues_found') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE patrol_records SET end_time = ?, checkpoints_visited = ?, issues_found = ?, status = 'completed', notes = ? WHERE record_id = ? AND status = 'ongoing' ''', (now, checkpoints_visited, issues_found,
                          kwargs.get('notes'), record_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '巡逻记录状态不允许完成'}
        except Exception as e:
            logger.error(f'完成巡逻失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 应急管理 ==========

    def report_emergency(self, event_type: str, title: str,
                          location: str, **kwargs) -> Dict[str, Any]:
        try:
            event_id = f"emg_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = EMERGENCY_TYPES.get(event_type, {})
            level = kwargs.get('emergency_level', 'medium')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO emergency_events ( event_id, event_type, emergency_level, title, description, location, occurred_at, reported_by, reported_at, status, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'reported', ?) ''', (event_id, level, title,
                          kwargs.get('description'), location,
                          kwargs.get('occurred_at', now),
                          kwargs.get('reported_by', ''),
                          now, now))
                    conn.commit()
                    logger.warning(f'应急事件报告: {event_id}, 类型: {event_type}, 级别: {level}')
                    return {'success': True, 'event_id': event_id,
                            'response_time_target': config.get('response_time', 15)}
        except Exception as e:
            logger.error(f'报告应急事件失败: {e}')
            return {'success': False, 'error': str(e)}

    def respond_emergency(self, event_id: str, response_team: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE emergency_events SET response_team = ?, response_time = ?, status = 'responding' WHERE event_id = ? AND status = 'reported' ''', (response_team, now, event_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'response_time': now}
                    return {'success': False, 'error': '事件状态不允许响应'}
        except Exception as e:
            logger.error(f'响应应急事件失败: {e}')
            return {'success': False, 'error': str(e)}

    def resolve_emergency(self, event_id: str, resolution: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE emergency_events SET resolution = ?, resolved_at = ?, casualties = ?, property_loss = ?, status = 'resolved' WHERE event_id = ? AND status IN ('reported', 'responding') ''', (resolution, now,
                          kwargs.get('casualties', '无'),
                          kwargs.get('property_loss', 0), event_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'应急事件已解决: {event_id}')
                        return {'success': True}
                    return {'success': False, 'error': '事件状态不允许结案'}
        except Exception as e:
            logger.error(f'结案应急事件失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_emergency_plan(self, plan_name: str, emergency_type: str,
                                **kwargs) -> Dict[str, Any]:
        try:
            plan_id = f"epl_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            contact_list = json.dumps(kwargs.get('contact_list'),
            ensure_ascii=False) if kwargs.get('contact_list') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO emergency_plans ( plan_id, plan_name, emergency_type, description, procedures, responsible_person, contact_list, evacuation_route, assembly_point, is_active, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?) ''', (plan_id, plan_name, emergency_type,
                          kwargs.get('description'), kwargs.get('procedures'),
                          kwargs.get('responsible_person'), contact_list,
                          kwargs.get('evacuation_route'),
                          kwargs.get('assembly_point'), now, now))
                    conn.commit()
                    return {'success': True, 'plan_id': plan_id}
        except Exception as e:
            logger.error(f'创建应急预案失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 安全培训 ==========

    def create_training(self, training_type: str, title: str,
                         training_date: str, **kwargs) -> Dict[str, Any]:
        try:
            training_id = f"str_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO safety_trainings ( training_id, training_type, title, trainer, training_date, location, duration_minutes, target_audience, education_type, participant_count, description, material_url, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, 'scheduled', ?, ?) ''', (training_id, training_type, title,
                          kwargs.get('trainer'), training_date,
                          kwargs.get('location'),
                          kwargs.get('duration_minutes', 60),
                          kwargs.get('target_audience', 'all'),
                          kwargs.get('education_type'),
                          kwargs.get('description'),
                          kwargs.get('material_url'), now, now))
                    conn.commit()
                    logger.info(f'创建安全培训: {title} ({training_id})')
                    return {'success': True, 'training_id': training_id}
        except Exception as e:
            logger.error(f'创建安全培训失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_training_attendance(self, training_id: str, student_id: int,
                                     student_name: str, attended: bool,
                                     **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT OR REPLACE INTO training_records ( training_id, student_id, student_name, attendance, score, passed, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?) ''', (training_id, student_id, student_name,
                          1 if attended else 0,
                          kwargs.get('score'),
                          kwargs.get('passed'), now))
                    if attended:
                        cursor.execute('UPDATE safety_trainings SET participant_count = participant_count + 1, updated_at = ? WHERE training_id = ?', (now, training_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'记录培训出勤失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 消防管理 ==========

    def add_fire_equipment(self, equipment_type: str, location: str,
                            **kwargs) -> Dict[str, Any]:
        try:
            equipment_id = f"feq_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = FIRE_EQUIPMENT_TYPES.get(equipment_type, {})
            next_check = (datetime.now() + timedelta(days=config.get('check_interval', 30))).strftime('%Y-%m-%d')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO fire_equipment ( equipment_id, equipment_type, location, building, floor, last_check_date, next_check_date, status, notes, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, 'normal', ?, ?, ?) ''', (equipment_id, equipment_type, location,
                          kwargs.get('building'), kwargs.get('floor'),
                          kwargs.get('last_check_date', now[:10]),
                          next_check, kwargs.get('notes'), now, now))
                    conn.commit()
                    return {'success': True, 'equipment_id': equipment_id, 'next_check_date': next_check}
        except Exception as e:
            logger.error(f'添加消防设施失败: {e}')
            return {'success': False, 'error': str(e)}

    def check_fire_equipment(self, equipment_id: str, checker: str,
                              result: str, **kwargs) -> Dict[str, Any]:
        try:
            check_id = f"fck_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT equipment_type FROM fire_equipment WHERE equipment_id = ?', (equipment_id,))
                    eq = cursor.fetchone()
                    if not eq:
                        return {'success': False, 'error': '设备不存在'}
                    config = FIRE_EQUIPMENT_TYPES.get(eq[0], {})
                    next_check = (datetime.now() + timedelta(days=config.get('check_interval',
                    30))).strftime('%Y-%m-%d')
                    status = 'normal' if '正常' in result else 'abnormal'
                    cursor.execute(''' INSERT INTO fire_check_records ( check_id, equipment_id, equipment_type, checker, check_date, result, status, action_taken, next_check_date, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (check_id, equipment_id, eq[0], checker,
                          now[:10], result, status,
                          kwargs.get('action_taken'), next_check, now))
                    cursor.execute('UPDATE fire_equipment SET last_check_date = ?, next_check_date = ?, status = ?, updated_at = ? WHERE equipment_id = ?',
                                 (now[:10], next_check, status, now, equipment_id))
                    conn.commit()
                    return {'success': True, 'next_check_date': next_check}
        except Exception as e:
            logger.error(f'消防检查失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_expired_fire_checks(self) -> Dict[str, Any]:
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM fire_equipment WHERE next_check_date < ? AND status != "scrapped"',
                (today,))
                items = [dict(i) for i in cursor.fetchall()]
                return {'success': True, 'expired_items': items, 'count': len(items)}
        except Exception as e:
            logger.error(f'获取过期消防检查失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 事故管理 ==========

    def report_incident(self, incident_type: str, title: str,
                         location: str, **kwargs) -> Dict[str, Any]:
        try:
            incident_id = f"sci_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO security_incidents ( incident_id, incident_type, severity, title, description, location, occurred_at, reported_by, reported_at, involved_persons, status, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?) ''', (incident_id, kwargs.get('severity', 'minor'),
                          title, kwargs.get('description'), location,
                          kwargs.get('occurred_at', now),
                          kwargs.get('reported_by', ''), now,
                          kwargs.get('involved_persons'), now))
                    conn.commit()
                    logger.info(f'事故报告: {incident_id}, 类型: {incident_type}')
                    return {'success': True, 'incident_id': incident_id}
        except Exception as e:
            logger.error(f'报告事故失败: {e}')
            return {'success': False, 'error': str(e)}

    def resolve_incident(self, incident_id: str, cause: str,
                          measures: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE security_incidents SET cause = ?, measures = ?, follow_up = ?, status = 'resolved', resolved_at = ? WHERE incident_id = ? AND status = 'open' ''', (cause, measures, kwargs.get('follow_up'),
                          now, incident_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '事故状态不允许处理'}
        except Exception as e:
            logger.error(f'处理事故失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_security_statistics(self, start_date: str = None,
                                  end_date: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = 'SELECT COUNT(*) FROM security_incidents WHERE 1=1'
                params = []
                if start_date:
                    query += ' AND date(occurred_at) >= ?'
                    params.append(start_date)
                if end_date:
                    query += ' AND date(occurred_at) <= ?'
                    params.append(end_date)
                cursor.execute(query, params)
                total = cursor.fetchone()[0]
                cursor.execute(f'SELECT incident_type, COUNT(*) FROM ({query}) GROUP BY incident_type', params)
                by_type = {r[0]: r[1] for r in cursor.fetchall()}
                cursor.execute(f'SELECT severity, COUNT(*) FROM ({query}) GROUP BY severity', params)
                by_severity = {r[0]: r[1] for r in cursor.fetchall()}
                cursor.execute(f'SELECT status, COUNT(*) FROM ({query}) GROUP BY status', params)
                by_status = {r[0]: r[1] for r in cursor.fetchall()}
                return {
                    'success': True,
                    'stats': {
                        'total_incidents': total,
                        'by_type': by_type,
                        'by_severity': by_severity,
                        'by_status': by_status
                    }
                }
        except Exception as e:
            logger.error(f'获取安全统计失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 监控管理 ==========

    def add_camera(self, camera_name: str, location: str,
                    **kwargs) -> Dict[str, Any]:
        try:
            camera_id = f"cam_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO surveillance_cameras ( camera_id, camera_name, location, building, floor, coverage_area, is_online, ip_address, stream_url, storage_days, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?) ''', (camera_id, camera_name, location,
                          kwargs.get('building'), kwargs.get('floor'),
                          kwargs.get('coverage_area'),
                          kwargs.get('ip_address'), kwargs.get('stream_url'),
                          kwargs.get('storage_days', 30), now, now))
                    conn.commit()
                    return {'success': True, 'camera_id': camera_id}
        except Exception as e:
            logger.error(f'添加监控摄像头失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_cameras(self, building: str = None,
                      is_online: bool = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM surveillance_cameras WHERE 1=1'
                params = []
                if building:
                    query += ' AND building = ?'
                    params.append(building)
                if is_online is not None:
                    query += ' AND is_online = ?'
                    params.append(1 if is_online else 0)
                cursor.execute(query, params)
                cameras = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'cameras': cameras, 'count': len(cameras)}
        except Exception as e:
            logger.error(f'获取摄像头列表失败: {e}')
            return {'success': False, 'error': str(e)}
