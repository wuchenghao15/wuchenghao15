#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育智慧校园服务 (v15.30.0)
====================================
提供智慧校园建设、智能设备管理、物联网应用、智能安防、智能能源、智慧图书馆、智慧教室、智慧后勤等综合管理服务。

核心能力：
1. 智慧校园 - 校园配置、模块管理、数据统计、系统集成
2. 智能设备 - 设备管理、设备监控、设备维护、设备调度
3. 物联网 - 感知控制、智能分析、预警联动、决策支持
4. 智能安防 - 视频监控、门禁控制、消防报警、入侵检测、访客管理
5. 智能能源 - 能耗监测、节能控制、能源分析、绿色校园
6. 智慧图书馆 - 智能书架、自助借还、座位预约、图书检索
7. 智慧教室 - 智能黑板、录播系统、环境监测、课堂分析
8. 智慧后勤 - 智能食堂、宿舍管理、维修服务、采购配送
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_smart_campus_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SmartCampus')


# ========== 智慧校园配置 ==========

SMART_CAMPUS_MODULES = {
    'access_control': {'name': '智能门禁', 'description': '人脸/刷卡门禁系统', 'k12_features': ['家长接送', '出入记录'], 'adult_features': ['访客管理', '时段控制']},
    'attendance': {'name': '智能考勤', 'description': '自动考勤统计', 'k12_features': ['家校通知', '请假管理'], 'adult_features': ['弹性考勤', '工时统计']},
    'surveillance': {'name': '智能监控', 'description': '高清视频监控', 'k12_features': ['区域告警', '行为分析'], 'adult_features': ['隐私保护', 'AI识别']},
    'broadcast': {'name': '智能广播', 'description': '校园广播系统', 'k12_features': ['上下课铃', '安全播报'], 'adult_features': ['会议广播', '紧急通知']},
    'lighting': {'name': '智能照明', 'description': '节能照明控制', 'k12_features': ['教室调光', '定时开关'], 'adult_features': ['场景模式', '远程控制']},
    'aircon': {'name': '智能空调', 'description': '恒温控制管理', 'k12_features': ['定时启停', '温度限制'], 'adult_features': ['个性化设置', '能耗统计']},
    'water': {'name': '智能饮水', 'description': '直饮水管理', 'k12_features': ['水质监测', '用量统计'], 'adult_features': ['健康饮水', '智能提醒']},
    'elevator': {'name': '智能电梯', 'description': '电梯智能调度', 'k12_features': ['楼层限制', '安全监控'], 'adult_features': ['预约服务', '效率优化']}
}

DEVICE_TYPES = {
    'sensor': {'name': '传感器', 'sub_types': ['温湿度', '光照', '空气质量', '烟雾', '红外', '水位', '能耗']},
    'controller': {'name': '控制器', 'sub_types': ['继电器', '调光器', '变频器', 'PLC']},
    'camera': {'name': '摄像头', 'sub_types': ['高清', '红外', '全景', 'AI识别']},
    'card_reader': {'name': '读卡器', 'sub_types': ['IC卡', 'NFC', '二维码', '蓝牙']},
    'access_machine': {'name': '门禁机', 'sub_types': ['人脸识别', '指纹', '刷卡', '组合验证']},
    'attendance_machine': {'name': '考勤机', 'sub_types': ['人脸', '指纹', '刷卡', 'APP签到']},
    'smart_terminal': {'name': '智能终端', 'sub_types': ['电子班牌', '查询机', '自助终端', '智能手表']},
    'iot_gateway': {'name': '物联网网关', 'sub_types': ['LoRa', 'NB-IoT', 'WiFi', '4G/5G']}
}

IOT_APPLICATIONS = {
    'perception': {'name': '智能感知', 'description': '环境数据采集与感知'},
    'control': {'name': '智能控制', 'description': '设备自动化控制'},
    'analysis': {'name': '智能分析', 'description': '数据挖掘与趋势分析'},
    'warning': {'name': '智能预警', 'description': '异常检测与预警'},
    'linkage': {'name': '智能联动', 'description': '多系统协同联动'},
    'decision': {'name': '智能决策', 'description': '数据驱动决策支持'},
    'operation': {'name': '智能运维', 'description': '设备远程运维管理'},
    'service': {'name': '智能服务', 'description': '个性化服务推送'}
}

SECURITY_SYSTEMS = {
    'video_monitor': {'name': '视频监控', 'features': ['实时查看', '录像回放', 'AI识别', '移动侦测']},
    'intrusion_detection': {'name': '入侵检测', 'features': ['红外报警', '周界防护', '异常行为']},
    'access_control': {'name': '门禁控制', 'features': ['身份验证', '权限管理', '出入记录']},
    'fire_alarm': {'name': '消防报警', 'features': ['烟雾探测', '温度监测', '联动控制']},
    'emergency_call': {'name': '紧急呼叫', 'features': ['一键报警', '位置定位', '语音对讲']},
    'patrol_system': {'name': '巡更系统', 'features': ['路线规划', '打卡记录', '异常反馈']},
    'visitor_management': {'name': '访客管理', 'features': ['预约登记', '证件识别', '临时授权']},
    'safety_warning': {'name': '安全预警', 'features': ['风险评估', '预警推送', '应急响应']}
}

ENERGY_MANAGEMENT = {
    'smart_meter': {'name': '智能电表', 'description': '电力消耗实时监测'},
    'smart_water': {'name': '智能水表', 'description': '用水量统计分析'},
    'smart_gas': {'name': '智能气表', 'description': '燃气使用监测'},
    'energy_monitor': {'name': '能耗监测', 'description': '多维度能耗数据分析'},
    'energy_saving': {'name': '节能控制', 'description': '智能节能策略执行'},
    'energy_analysis': {'name': '能源分析', 'description': '能耗趋势与优化建议'},
    'green_campus': {'name': '绿色校园', 'description': '环保指标管理'},
    'carbon_neutral': {'name': '碳中和', 'description': '碳排放统计与减排'}
}

LIBRARY_SERVICES = {
    'smart_shelf': {'name': '智能书架', 'description': '图书定位与盘点'},
    'self_service': {'name': '自助借还', 'description': '无人化借还书'},
    'seat_reservation': {'name': '座位预约', 'description': '自习座位管理'},
    'book_search': {'name': '图书检索', 'description': '智能图书查找'},
    'reading_recommend': {'name': '阅读推荐', 'description': '个性化书单'},
    'digital_resource': {'name': '电子资源', 'description': '数字图书馆访问'},
    'data_statistics': {'name': '数据统计', 'description': '借阅数据分析'},
    'reader_service': {'name': '读者服务', 'description': '读者信息管理'}
}

CLASSROOM_TECHNOLOGY = {
    'smart_board': {'name': '智慧黑板', 'description': '交互式教学设备'},
    'smart_projector': {'name': '智能投影', 'description': '高清投影系统'},
    'interactive_whiteboard': {'name': '互动白板', 'description': '多人协作教学'},
    'recording_system': {'name': '录播系统', 'description': '课程录制直播'},
    'remote_teaching': {'name': '远程教学', 'description': '在线课堂互动'},
    'smart_attendance': {'name': '智能点名', 'description': '自动考勤统计'},
    'environment_monitor': {'name': '环境监测', 'description': '教室环境管理'},
    'class_analysis': {'name': '课堂分析', 'description': '教学效果评估'}
}

LOGISTICS_SERVICES = {
    'smart_canteen': {'name': '智能食堂', 'description': '餐饮服务管理'},
    'smart_dormitory': {'name': '智能宿舍', 'description': '住宿管理服务'},
    'smart_maintenance': {'name': '智能维修', 'description': '报修与维修管理'},
    'smart_purchase': {'name': '智能采购', 'description': '物资采购管理'},
    'smart_storage': {'name': '智能仓储', 'description': '仓库库存管理'},
    'smart_delivery': {'name': '智能配送', 'description': '物资配送服务'},
    'smart_cleaning': {'name': '智能保洁', 'description': '清洁服务管理'},
    'smart_greening': {'name': '智能绿化', 'description': '校园绿化养护'}
}


class EducationSmartCampusService:
    """教育智慧校园服务"""

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
                    CREATE TABLE IF NOT EXISTS smart_campus (
                        campus_id TEXT PRIMARY KEY,
                        campus_name TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        address TEXT,
                        total_area REAL,
                        building_count INTEGER DEFAULT 0,
                        device_count INTEGER DEFAULT 0,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS campus_config (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        campus_id TEXT NOT NULL,
                        module_key TEXT NOT NULL,
                        module_name TEXT,
                        enabled INTEGER DEFAULT 1,
                        config_json TEXT,
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        UNIQUE(campus_id, module_key)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS smart_devices (
                        device_id TEXT PRIMARY KEY,
                        device_name TEXT NOT NULL,
                        device_type TEXT NOT NULL,
                        sub_type TEXT,
                        campus_id TEXT,
                        location TEXT,
                        ip_address TEXT,
                        mac_address TEXT,
                        status TEXT DEFAULT 'online',
                        last_heartbeat TEXT,
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS device_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        device_id TEXT NOT NULL,
                        record_type TEXT,
                        value REAL,
                        unit TEXT,
                        record_time TEXT,
                        education_type TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS iot_applications (
                        app_id TEXT PRIMARY KEY,
                        app_name TEXT NOT NULL,
                        app_type TEXT,
                        campus_id TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        config_json TEXT,
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS iot_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        app_id TEXT NOT NULL,
                        record_type TEXT,
                        data_json TEXT,
                        record_time TEXT,
                        education_type TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS smart_security (
                        security_id TEXT PRIMARY KEY,
                        system_type TEXT NOT NULL,
                        system_name TEXT,
                        campus_id TEXT,
                        location TEXT,
                        status TEXT DEFAULT 'normal',
                        config_json TEXT,
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS security_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        security_id TEXT NOT NULL,
                        event_type TEXT,
                        event_level TEXT,
                        event_desc TEXT,
                        event_time TEXT,
                        handled INTEGER DEFAULT 0,
                        education_type TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS smart_energy (
                        energy_id TEXT PRIMARY KEY,
                        meter_type TEXT NOT NULL,
                        meter_name TEXT,
                        campus_id TEXT,
                        location TEXT,
                        last_reading REAL,
                        unit TEXT,
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS energy_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        energy_id TEXT NOT NULL,
                        reading REAL,
                        consumption REAL,
                        unit TEXT,
                        record_date TEXT,
                        education_type TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS smart_library (
                        library_id TEXT PRIMARY KEY,
                        service_type TEXT NOT NULL,
                        service_name TEXT,
                        campus_id TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        config_json TEXT,
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS library_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        library_id TEXT NOT NULL,
                        record_type TEXT,
                        data_json TEXT,
                        record_time TEXT,
                        education_type TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS smart_classroom (
                        classroom_id TEXT PRIMARY KEY,
                        classroom_name TEXT NOT NULL,
                        campus_id TEXT,
                        floor TEXT,
                        capacity INTEGER DEFAULT 0,
                        tech_config TEXT,
                        status TEXT DEFAULT 'available',
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS classroom_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        classroom_id TEXT NOT NULL,
                        record_type TEXT,
                        data_json TEXT,
                        record_time TEXT,
                        education_type TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS smart_logistics (
                        logistics_id TEXT PRIMARY KEY,
                        service_type TEXT NOT NULL,
                        service_name TEXT,
                        campus_id TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        config_json TEXT,
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS logistics_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        logistics_id TEXT NOT NULL,
                        record_type TEXT,
                        data_json TEXT,
                        record_time TEXT,
                        education_type TEXT
                    )
                ''')
                conn.commit()
                logger.info('教育智慧校园服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 智慧校园 ==========

    def create_campus(self, campus_name: str, education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            campus_id = f"cmp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO smart_campus (
                            campus_id, campus_name, education_type, address,
                            total_area, building_count, device_count, description,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, 'active', ?, ?)
                    ''', (campus_id, campus_name, education_type,
                          kwargs.get('address'), kwargs.get('total_area'),
                          kwargs.get('building_count', 0),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建智慧校园: {campus_name} ({campus_id})')
                    return {'success': True, 'campus_id': campus_id}
        except Exception as e:
            logger.error(f'创建智慧校园失败: {e}')
            return {'success': False, 'error': str(e)}

    def configure_campus_module(self, campus_id: str, module_key: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            module_info = SMART_CAMPUS_MODULES.get(module_key, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM smart_campus WHERE campus_id = ?', (campus_id,))
                    campus = cursor.fetchone()
                    if not campus:
                        return {'success': False, 'error': '校园不存在'}
                    education_type = campus[0]
                    features = module_info.get('k12_features', []) if education_type == 'k12' else module_info.get('adult_features', [])
                    config = {'features': features, 'settings': kwargs.get('settings', {})}
                    cursor.execute('''
                        INSERT OR REPLACE INTO campus_config (
                            campus_id, module_key, module_name, enabled,
                            config_json, education_type, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (campus_id, module_key, module_info.get('name'),
                          kwargs.get('enabled', 1), json.dumps(config, ensure_ascii=False),
                          education_type, now, now))
                    conn.commit()
                    return {'success': True, 'module_key': module_key}
        except Exception as e:
            logger.error(f'配置校园模块失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_campus_info(self, campus_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM smart_campus WHERE campus_id = ?', (campus_id,))
                campus = cursor.fetchone()
                if not campus:
                    return {'success': False, 'error': '校园不存在'}
                cursor.execute('SELECT * FROM campus_config WHERE campus_id = ?', (campus_id,))
                configs = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'campus': dict(campus), 'configs': configs}
        except Exception as e:
            logger.error(f'获取校园信息失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_campuses(self, education_type: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM smart_campus WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                campuses = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'campuses': campuses, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取校园列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 智能设备 ==========

    def register_device(self, device_name: str, device_type: str, campus_id: str, **kwargs) -> Dict[str, Any]:
        try:
            device_id = f"dev_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM smart_campus WHERE campus_id = ?', (campus_id,))
                    campus = cursor.fetchone()
                    if not campus:
                        return {'success': False, 'error': '校园不存在'}
                    cursor.execute('''
                        INSERT INTO smart_devices (
                            device_id, device_name, device_type, sub_type,
                            campus_id, location, ip_address, mac_address,
                            status, last_heartbeat, education_type,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'online', ?, ?, ?, ?)
                    ''', (device_id, device_name, device_type, kwargs.get('sub_type'),
                          campus_id, kwargs.get('location'), kwargs.get('ip_address'),
                          kwargs.get('mac_address'), now, campus[0], now, now))
                    cursor.execute('UPDATE smart_campus SET device_count = device_count + 1 WHERE campus_id = ?', (campus_id,))
                    conn.commit()
                    logger.info(f'注册智能设备: {device_name} ({device_id})')
                    return {'success': True, 'device_id': device_id}
        except Exception as e:
            logger.error(f'注册智能设备失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_device_status(self, device_id: str, status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE smart_devices SET status = ?, last_heartbeat = ?, updated_at = ?
                        WHERE device_id = ?
                    ''', (status, now, now, device_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '设备不存在'}
        except Exception as e:
            logger.error(f'更新设备状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_device_data(self, device_id: str, record_type: str, value: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM smart_devices WHERE device_id = ?', (device_id,))
                    device = cursor.fetchone()
                    if not device:
                        return {'success': False, 'error': '设备不存在'}
                    cursor.execute('''
                        INSERT INTO device_records (device_id, record_type, value, unit, record_time, education_type)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (device_id, record_type, value, kwargs.get('unit', ''), now, device[0]))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'记录设备数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_device_records(self, device_id: str, record_type: str = None, start_time: str = None, end_time: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM device_records WHERE device_id = ?'
                params = [device_id]
                if record_type:
                    query += ' AND record_type = ?'
                    params.append(record_type)
                if start_time:
                    query += ' AND record_time >= ?'
                    params.append(start_time)
                if end_time:
                    query += ' AND record_time <= ?'
                    params.append(end_time)
                query += ' ORDER BY record_time DESC'
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records}
        except Exception as e:
            logger.error(f'获取设备记录失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 物联网应用 ==========

    def create_iot_application(self, app_name: str, app_type: str, campus_id: str, **kwargs) -> Dict[str, Any]:
        try:
            app_id = f"iot_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM smart_campus WHERE campus_id = ?', (campus_id,))
                    campus = cursor.fetchone()
                    if not campus:
                        return {'success': False, 'error': '校园不存在'}
                    cursor.execute('''
                        INSERT INTO iot_applications (
                            app_id, app_name, app_type, campus_id,
                            description, status, config_json, education_type,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 'active', ?, ?, ?, ?)
                    ''', (app_id, app_name, app_type, campus_id,
                          kwargs.get('description'),
                          json.dumps(kwargs.get('config', {}), ensure_ascii=False),
                          campus[0], now, now))
                    conn.commit()
                    logger.info(f'创建物联网应用: {app_name} ({app_id})')
                    return {'success': True, 'app_id': app_id}
        except Exception as e:
            logger.error(f'创建物联网应用失败: {e}')
            return {'success': False, 'error': str(e)}

    def run_iot_analysis(self, app_id: str, analysis_type: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM iot_applications WHERE app_id = ?', (app_id,))
                    app = cursor.fetchone()
                    if not app:
                        return {'success': False, 'error': '应用不存在'}
                    analysis_result = {'analysis_type': analysis_type, 'params': kwargs, 'executed_at': now}
                    cursor.execute('''
                        INSERT INTO iot_records (app_id, record_type, data_json, record_time, education_type)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (app_id, 'analysis', json.dumps(analysis_result, ensure_ascii=False), now, app[0]))
                    conn.commit()
                    return {'success': True, 'analysis_result': analysis_result}
        except Exception as e:
            logger.error(f'执行物联网分析失败: {e}')
            return {'success': False, 'error': str(e)}

    def trigger_iot_warning(self, app_id: str, warning_level: str, warning_desc: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM iot_applications WHERE app_id = ?', (app_id,))
                    app = cursor.fetchone()
                    if not app:
                        return {'success': False, 'error': '应用不存在'}
                    warning_data = {'warning_level': warning_level, 'warning_desc': warning_desc, 'triggered_at': now}
                    cursor.execute('''
                        INSERT INTO iot_records (app_id, record_type, data_json, record_time, education_type)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (app_id, 'warning', json.dumps(warning_data, ensure_ascii=False), now, app[0]))
                    conn.commit()
                    logger.warning(f'物联网预警触发: {warning_level} - {warning_desc}')
                    return {'success': True, 'warning_data': warning_data}
        except Exception as e:
            logger.error(f'触发物联网预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def link_iot_devices(self, app_id: str, device_ids: List[str], **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM iot_applications WHERE app_id = ?', (app_id,))
                    app = cursor.fetchone()
                    if not app:
                        return {'success': False, 'error': '应用不存在'}
                    linkage_data = {'device_ids': device_ids, 'linkage_type': kwargs.get('linkage_type', 'auto'), 'created_at': now}
                    cursor.execute('''
                        INSERT INTO iot_records (app_id, record_type, data_json, record_time, education_type)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (app_id, 'linkage', json.dumps(linkage_data, ensure_ascii=False), now, app[0]))
                    conn.commit()
                    return {'success': True, 'linked_count': len(device_ids)}
        except Exception as e:
            logger.error(f'物联网设备联动失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 智能安防 ==========

    def deploy_security_system(self, system_type: str, campus_id: str, **kwargs) -> Dict[str, Any]:
        try:
            security_id = f"sec_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            system_info = SECURITY_SYSTEMS.get(system_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM smart_campus WHERE campus_id = ?', (campus_id,))
                    campus = cursor.fetchone()
                    if not campus:
                        return {'success': False, 'error': '校园不存在'}
                    cursor.execute('''
                        INSERT INTO smart_security (
                            security_id, system_type, system_name, campus_id,
                            location, status, config_json, education_type,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 'normal', ?, ?, ?, ?)
                    ''', (security_id, system_type, system_info.get('name'),
                          campus_id, kwargs.get('location'),
                          json.dumps({'features': system_info.get('features', []), 'settings': kwargs.get('settings', {})}, ensure_ascii=False),
                          campus[0], now, now))
                    conn.commit()
                    logger.info(f'部署安防系统: {system_info.get("name")} ({security_id})')
                    return {'success': True, 'security_id': security_id}
        except Exception as e:
            logger.error(f'部署安防系统失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_security_event(self, security_id: str, event_type: str, event_level: str, event_desc: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM smart_security WHERE security_id = ?', (security_id,))
                    security = cursor.fetchone()
                    if not security:
                        return {'success': False, 'error': '安防系统不存在'}
                    cursor.execute('''
                        INSERT INTO security_records (security_id, event_type, event_level, event_desc, event_time, handled, education_type)
                        VALUES (?, ?, ?, ?, ?, 0, ?)
                    ''', (security_id, event_type, event_level, event_desc, now, security[0]))
                    cursor.execute('UPDATE smart_security SET status = ? WHERE security_id = ?', ('warning' if event_level == 'high' else 'normal', security_id))
                    conn.commit()
                    logger.warning(f'安防事件记录: {event_level} - {event_desc}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'记录安防事件失败: {e}')
            return {'success': False, 'error': str(e)}

    def handle_security_event(self, record_id: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE security_records SET handled = 1 WHERE id = ?', (record_id,))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '事件记录不存在'}
        except Exception as e:
            logger.error(f'处理安防事件失败: {e}')
            return {'success': False, 'error': str(e)}

    def register_visitor(self, campus_id: str, visitor_name: str, **kwargs) -> Dict[str, Any]:
        try:
            visitor_id = f"vis_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM smart_campus WHERE campus_id = ?', (campus_id,))
                    campus = cursor.fetchone()
                    if not campus:
                        return {'success': False, 'error': '校园不存在'}
                    cursor.execute('''
                        INSERT INTO security_records (security_id, event_type, event_level, event_desc, event_time, handled, education_type)
                        VALUES (?, ?, ?, ?, ?, 1, ?)
                    ''', ('visitor', 'visitor_register', 'info',
                          f"访客登记: {visitor_name}, 证件: {kwargs.get('id_card', '')}, 来访事由: {kwargs.get('purpose', '')}",
                          now, campus[0]))
                    conn.commit()
                    return {'success': True, 'visitor_id': visitor_id}
        except Exception as e:
            logger.error(f'访客登记失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_security_status(self, campus_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM smart_security WHERE campus_id = ?', (campus_id,))
                systems = [dict(s) for s in cursor.fetchall()]
                cursor.execute('SELECT * FROM security_records WHERE security_id IN (SELECT security_id FROM smart_security WHERE campus_id = ?) AND handled = 0 ORDER BY event_time DESC LIMIT 10', (campus_id,))
                pending_events = [dict(e) for e in cursor.fetchall()]
                return {'success': True, 'systems': systems, 'pending_events': pending_events}
        except Exception as e:
            logger.error(f'获取安防状态失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 智能能源 ==========

    def install_energy_meter(self, meter_type: str, campus_id: str, **kwargs) -> Dict[str, Any]:
        try:
            energy_id = f"ene_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            meter_info = ENERGY_MANAGEMENT.get(meter_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM smart_campus WHERE campus_id = ?', (campus_id,))
                    campus = cursor.fetchone()
                    if not campus:
                        return {'success': False, 'error': '校园不存在'}
                    cursor.execute('''
                        INSERT INTO smart_energy (
                            energy_id, meter_type, meter_name, campus_id,
                            location, last_reading, unit, education_type,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
                    ''', (energy_id, meter_type, meter_info.get('name'),
                          campus_id, kwargs.get('location'),
                          kwargs.get('unit', 'kWh'), campus[0], now, now))
                    conn.commit()
                    logger.info(f'安装能源仪表: {meter_info.get("name")} ({energy_id})')
                    return {'success': True, 'energy_id': energy_id}
        except Exception as e:
            logger.error(f'安装能源仪表失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_energy_reading(self, energy_id: str, reading: float) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            today = now[:10]
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT last_reading, unit, education_type FROM smart_energy WHERE energy_id = ?', (energy_id,))
                    meter = cursor.fetchone()
                    if not meter:
                        return {'success': False, 'error': '仪表不存在'}
                    consumption = reading - meter[0] if meter[0] > 0 else 0
                    cursor.execute('UPDATE smart_energy SET last_reading = ?, updated_at = ? WHERE energy_id = ?', (reading, now, energy_id))
                    cursor.execute('''
                        INSERT INTO energy_records (energy_id, reading, consumption, unit, record_date, education_type)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (energy_id, reading, consumption, meter[1], today, meter[2]))
                    conn.commit()
                    return {'success': True, 'consumption': consumption}
        except Exception as e:
            logger.error(f'记录能源读数失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_energy_statistics(self, campus_id: str, period: str = 'month') -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                now = datetime.now()
                if period == 'day':
                    start_date = now.strftime('%Y-%m-%d')
                elif period == 'week':
                    start_date = (now - timedelta(days=7)).strftime('%Y-%m-%d')
                else:
                    start_date = (now - timedelta(days=30)).strftime('%Y-%m-%d')
                cursor.execute('''
                    SELECT er.unit, SUM(er.consumption) as total_consumption
                    FROM energy_records er
                    JOIN smart_energy se ON er.energy_id = se.energy_id
                    WHERE se.campus_id = ? AND er.record_date >= ?
                    GROUP BY er.unit
                ''', (campus_id, start_date))
                stats = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'statistics': stats, 'period': period, 'start_date': start_date}
        except Exception as e:
            logger.error(f'获取能源统计失败: {e}')
            return {'success': False, 'error': str(e)}

    def apply_energy_saving(self, campus_id: str, strategy: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM smart_campus WHERE campus_id = ?', (campus_id,))
                    campus = cursor.fetchone()
                    if not campus:
                        return {'success': False, 'error': '校园不存在'}
                    strategy_data = {'strategy': strategy, 'params': kwargs, 'applied_at': now}
                    cursor.execute('INSERT INTO energy_records (energy_id, reading, consumption, unit, record_date, education_type) VALUES (?, 0, 0, ?, ?, ?)', ('strategy', 'strategy', now[:10], campus[0]))
                    conn.commit()
                    logger.info(f'应用节能策略: {strategy}')
                    return {'success': True, 'strategy': strategy_data}
        except Exception as e:
            logger.error(f'应用节能策略失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 智慧图书馆 ==========

    def setup_library_service(self, service_type: str, campus_id: str, **kwargs) -> Dict[str, Any]:
        try:
            library_id = f"lib_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            service_info = LIBRARY_SERVICES.get(service_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM smart_campus WHERE campus_id = ?', (campus_id,))
                    campus = cursor.fetchone()
                    if not campus:
                        return {'success': False, 'error': '校园不存在'}
                    cursor.execute('''
                        INSERT INTO smart_library (
                            library_id, service_type, service_name, campus_id,
                            description, status, config_json, education_type,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 'active', ?, ?, ?, ?)
                    ''', (library_id, service_type, service_info.get('name'),
                          campus_id, service_info.get('description'),
                          json.dumps(kwargs.get('config', {}), ensure_ascii=False),
                          campus[0], now, now))
                    conn.commit()
                    logger.info(f'设置图书馆服务: {service_info.get("name")} ({library_id})')
                    return {'success': True, 'library_id': library_id}
        except Exception as e:
            logger.error(f'设置图书馆服务失败: {e}')
            return {'success': False, 'error': str(e)}

    def borrow_book(self, library_id: str, book_id: str, user_id: int, user_name: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM smart_library WHERE library_id = ?', (library_id,))
                    library = cursor.fetchone()
                    if not library:
                        return {'success': False, 'error': '图书馆服务不存在'}
                    borrow_data = {'book_id': book_id, 'user_id': user_id, 'user_name': user_name, 'borrow_time': now, 'status': 'borrowed'}
                    cursor.execute('''
                        INSERT INTO library_records (library_id, record_type, data_json, record_time, education_type)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (library_id, 'borrow', json.dumps(borrow_data, ensure_ascii=False), now, library[0]))
                    conn.commit()
                    return {'success': True, 'borrow_data': borrow_data}
        except Exception as e:
            logger.error(f'借书失败: {e}')
            return {'success': False, 'error': str(e)}

    def reserve_seat(self, library_id: str, seat_id: str, user_id: int, user_name: str, duration: int = 4) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            end_time = (datetime.now() + timedelta(hours=duration)).isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM smart_library WHERE library_id = ?', (library_id,))
                    library = cursor.fetchone()
                    if not library:
                        return {'success': False, 'error': '图书馆服务不存在'}
                    cursor.execute('SELECT * FROM library_records WHERE library_id = ? AND record_type = ? AND data_json LIKE ? AND record_time >= ?',
                                   (library_id, 'reservation', f'%{seat_id}%', (datetime.now() - timedelta(hours=duration)).isoformat()))
                    if cursor.fetchone():
                        return {'success': False, 'error': '座位已被预约'}
                    reserve_data = {'seat_id': seat_id, 'user_id': user_id, 'user_name': user_name, 'start_time': now, 'end_time': end_time, 'status': 'reserved'}
                    cursor.execute('''
                        INSERT INTO library_records (library_id, record_type, data_json, record_time, education_type)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (library_id, 'reservation', json.dumps(reserve_data, ensure_ascii=False), now, library[0]))
                    conn.commit()
                    return {'success': True, 'reserve_data': reserve_data}
        except Exception as e:
            logger.error(f'预约座位失败: {e}')
            return {'success': False, 'error': str(e)}

    def search_book(self, library_id: str, keyword: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM smart_library WHERE library_id = ?', (library_id,))
                    library = cursor.fetchone()
                    if not library:
                        return {'success': False, 'error': '图书馆服务不存在'}
                    search_data = {'keyword': keyword, 'filters': kwargs, 'search_time': now}
                    cursor.execute('''
                        INSERT INTO library_records (library_id, record_type, data_json, record_time, education_type)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (library_id, 'search', json.dumps(search_data, ensure_ascii=False), now, library[0]))
                    conn.commit()
                    mock_results = [{'book_id': f"bk_{uuid.uuid4().hex[:8]}", 'title': f"《{keyword}相关书籍》", 'author': '佚名', 'location': 'A区1排'}]
                    return {'success': True, 'results': mock_results}
        except Exception as e:
            logger.error(f'搜索图书失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 智慧教室 ==========

    def create_classroom(self, classroom_name: str, campus_id: str, **kwargs) -> Dict[str, Any]:
        try:
            classroom_id = f"cls_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM smart_campus WHERE campus_id = ?', (campus_id,))
                    campus = cursor.fetchone()
                    if not campus:
                        return {'success': False, 'error': '校园不存在'}
                    tech_config = {
                        'smart_board': kwargs.get('smart_board', False),
                        'projector': kwargs.get('projector', False),
                        'recording': kwargs.get('recording', False),
                        'environment_monitor': kwargs.get('environment_monitor', False)
                    }
                    cursor.execute('''
                        INSERT INTO smart_classroom (
                            classroom_id, classroom_name, campus_id, floor,
                            capacity, tech_config, status, education_type,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'available', ?, ?, ?)
                    ''', (classroom_id, classroom_name, campus_id,
                          kwargs.get('floor', '1'), kwargs.get('capacity', 40),
                          json.dumps(tech_config, ensure_ascii=False), campus[0], now, now))
                    conn.commit()
                    logger.info(f'创建智慧教室: {classroom_name} ({classroom_id})')
                    return {'success': True, 'classroom_id': classroom_id}
        except Exception as e:
            logger.error(f'创建智慧教室失败: {e}')
            return {'success': False, 'error': str(e)}

    def reserve_classroom(self, classroom_id: str, user_id: int, user_name: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type, status FROM smart_classroom WHERE classroom_id = ?', (classroom_id,))
                    classroom = cursor.fetchone()
                    if not classroom:
                        return {'success': False, 'error': '教室不存在'}
                    if classroom[1] != 'available':
                        return {'success': False, 'error': '教室不可用'}
                    cursor.execute('UPDATE smart_classroom SET status = ? WHERE classroom_id = ?', ('reserved', classroom_id))
                    reserve_data = {'user_id': user_id, 'user_name': user_name, 'start_time': kwargs.get('start_time'), 'end_time': kwargs.get('end_time'), 'purpose': kwargs.get('purpose')}
                    cursor.execute('''
                        INSERT INTO classroom_records (classroom_id, record_type, data_json, record_time, education_type)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (classroom_id, 'reservation', json.dumps(reserve_data, ensure_ascii=False), now, classroom[0]))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'预约教室失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_classroom_environment(self, classroom_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM smart_classroom WHERE classroom_id = ?', (classroom_id,))
                    classroom = cursor.fetchone()
                    if not classroom:
                        return {'success': False, 'error': '教室不存在'}
                    env_data = {
                        'temperature': kwargs.get('temperature'),
                        'humidity': kwargs.get('humidity'),
                        'light_level': kwargs.get('light_level'),
                        'air_quality': kwargs.get('air_quality'),
                        'record_time': now
                    }
                    cursor.execute('''
                        INSERT INTO classroom_records (classroom_id, record_type, data_json, record_time, education_type)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (classroom_id, 'environment', json.dumps(env_data, ensure_ascii=False), now, classroom[0]))
                    conn.commit()
                    return {'success': True, 'environment_data': env_data}
        except Exception as e:
            logger.error(f'记录教室环境失败: {e}')
            return {'success': False, 'error': str(e)}

    def start_class_recording(self, classroom_id: str, course_name: str, teacher_name: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM smart_classroom WHERE classroom_id = ?', (classroom_id,))
                    classroom = cursor.fetchone()
                    if not classroom:
                        return {'success': False, 'error': '教室不存在'}
                    recording_data = {'course_name': course_name, 'teacher_name': teacher_name, 'start_time': now, 'status': 'recording'}
                    cursor.execute('''
                        INSERT INTO classroom_records (classroom_id, record_type, data_json, record_time, education_type)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (classroom_id, 'recording', json.dumps(recording_data, ensure_ascii=False), now, classroom[0]))
                    conn.commit()
                    logger.info(f'开始课堂录制: {course_name}')
                    return {'success': True, 'recording_data': recording_data}
        except Exception as e:
            logger.error(f'开始课堂录制失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 智慧后勤 ==========

    def setup_logistics_service(self, service_type: str, campus_id: str, **kwargs) -> Dict[str, Any]:
        try:
            logistics_id = f"log_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            service_info = LOGISTICS_SERVICES.get(service_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM smart_campus WHERE campus_id = ?', (campus_id,))
                    campus = cursor.fetchone()
                    if not campus:
                        return {'success': False, 'error': '校园不存在'}
                    cursor.execute('''
                        INSERT INTO smart_logistics (
                            logistics_id, service_type, service_name, campus_id,
                            description, status, config_json, education_type,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 'active', ?, ?, ?, ?)
                    ''', (logistics_id, service_type, service_info.get('name'),
                          campus_id, service_info.get('description'),
                          json.dumps(kwargs.get('config', {}), ensure_ascii=False),
                          campus[0], now, now))
                    conn.commit()
                    logger.info(f'设置后勤服务: {service_info.get("name")} ({logistics_id})')
                    return {'success': True, 'logistics_id': logistics_id}
        except Exception as e:
            logger.error(f'设置后勤服务失败: {e}')
            return {'success': False, 'error': str(e)}

    def submit_maintenance_request(self, logistics_id: str, user_id: int, user_name: str, issue_desc: str, **kwargs) -> Dict[str, Any]:
        try:
            request_id = f"mtn_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM smart_logistics WHERE logistics_id = ?', (logistics_id,))
                    logistics = cursor.fetchone()
                    if not logistics:
                        return {'success': False, 'error': '后勤服务不存在'}
                    request_data = {'request_id': request_id, 'user_id': user_id, 'user_name': user_name, 'issue_desc': issue_desc, 'location': kwargs.get('location'), 'priority': kwargs.get('priority', 'normal'), 'status': 'pending', 'created_at': now}
                    cursor.execute('''
                        INSERT INTO logistics_records (logistics_id, record_type, data_json, record_time, education_type)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (logistics_id, 'maintenance_request', json.dumps(request_data, ensure_ascii=False), now, logistics[0]))
                    conn.commit()
                    return {'success': True, 'request_id': request_id}
        except Exception as e:
            logger.error(f'提交维修请求失败: {e}')
            return {'success': False, 'error': str(e)}

    def order_canteen(self, logistics_id: str, user_id: int, user_name: str, items: List[Dict], **kwargs) -> Dict[str, Any]:
        try:
            order_id = f"ctn_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM smart_logistics WHERE logistics_id = ?', (logistics_id,))
                    logistics = cursor.fetchone()
                    if not logistics:
                        return {'success': False, 'error': '后勤服务不存在'}
                    total_amount = sum(item.get('price', 0) * item.get('quantity', 1) for item in items)
                    order_data = {'order_id': order_id, 'user_id': user_id, 'user_name': user_name, 'items': items, 'total_amount': total_amount, 'status': 'ordered', 'order_time': now}
                    cursor.execute('''
                        INSERT INTO logistics_records (logistics_id, record_type, data_json, record_time, education_type)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (logistics_id, 'canteen_order', json.dumps(order_data, ensure_ascii=False), now, logistics[0]))
                    conn.commit()
                    return {'success': True, 'order_id': order_id, 'total_amount': total_amount}
        except Exception as e:
            logger.error(f'食堂订餐失败: {e}')
            return {'success': False, 'error': str(e)}

    def manage_dormitory(self, logistics_id: str, student_id: int, student_name: str, room_no: str, action: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM smart_logistics WHERE logistics_id = ?', (logistics_id,))
                    logistics = cursor.fetchone()
                    if not logistics:
                        return {'success': False, 'error': '后勤服务不存在'}
                    dorm_data = {'student_id': student_id, 'student_name': student_name, 'room_no': room_no, 'action': action, 'time': now}
                    cursor.execute('''
                        INSERT INTO logistics_records (logistics_id, record_type, data_json, record_time, education_type)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (logistics_id, 'dormitory', json.dumps(dorm_data, ensure_ascii=False), now, logistics[0]))
                    conn.commit()
                    return {'success': True, 'action': action}
        except Exception as e:
            logger.error(f'宿舍管理失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_campus_overview(self, campus_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM smart_campus WHERE campus_id = ?', (campus_id,))
                campus = cursor.fetchone()
                if not campus:
                    return {'success': False, 'error': '校园不存在'}
                cursor.execute('SELECT COUNT(*) as cnt FROM smart_devices WHERE campus_id = ?', (campus_id,))
                device_count = cursor.fetchone()['cnt']
                cursor.execute('SELECT COUNT(*) as cnt FROM smart_security WHERE campus_id = ?', (campus_id,))
                security_count = cursor.fetchone()['cnt']
                cursor.execute('SELECT COUNT(*) as cnt FROM smart_energy WHERE campus_id = ?', (campus_id,))
                energy_count = cursor.fetchone()['cnt']
                cursor.execute('SELECT COUNT(*) as cnt FROM smart_classroom WHERE campus_id = ?', (campus_id,))
                classroom_count = cursor.fetchone()['cnt']
                cursor.execute('SELECT COUNT(*) as cnt FROM security_records WHERE security_id IN (SELECT security_id FROM smart_security WHERE campus_id = ?) AND handled = 0', (campus_id,))
                pending_events = cursor.fetchone()['cnt']
                cursor.execute('SELECT SUM(consumption) as total FROM energy_records WHERE energy_id IN (SELECT energy_id FROM smart_energy WHERE campus_id = ?) AND record_date >= ?', (campus_id, (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')))
                monthly_energy = cursor.fetchone()['total'] or 0
                overview = {
                    'campus_name': campus['campus_name'],
                    'education_type': campus['education_type'],
                    'device_count': device_count,
                    'security_count': security_count,
                    'energy_count': energy_count,
                    'classroom_count': classroom_count,
                    'pending_events': pending_events,
                    'monthly_energy': round(monthly_energy, 2)
                }
                return {'success': True, 'overview': overview}
        except Exception as e:
            logger.error(f'获取校园概览失败: {e}')
            return {'success': False, 'error': str(e)}