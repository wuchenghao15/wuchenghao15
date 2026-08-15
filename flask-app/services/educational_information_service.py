#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育信息化服务 (v15.12.0)
================================
提供智慧校园、数字化转型、信息化基础设施等综合管理服务。

核心能力：
1. 智慧校园 - 教务/学工/财务/后勤/人事/科研/图书馆/校园卡/门禁/监控/能源/停车/班车/迎新/离校
2. 数字化转型 - 数字化规划、流程再造、数据治理
3. 信息化基础设施 - 服务器/存储/网络/数据库/中间件/安全设备
4. 教育软件系统 - 各类教育管理系统集成
5. 数据中心 - 机房/机柜/供电/空调/消防/监控
6. 网络安全 - 安全等级L1-L5，安全设备管理
7. 移动校园 - 课表/成绩/考勤/通知/缴费/请假/活动
8. 物联网 - 温湿度/门禁/监控/能源/照明/空调/传感器
9. 智慧教室 - 互动白板/录播/直播/点名/分组/答题器
"""
import os
import uuid
import sqlite3
import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'educational_information_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationalInformation')


# ========== 教育信息化配置 ==========

CAMPUS_SYSTEMS = {
    'academic': {'name': '教务系统', 'modules': ['选课', '排课', '成绩', '学籍', '毕业']},
    'student': {'name': '学工系统', 'modules': ['评奖评优', '资助', '心理健康', '社会实践']},
    'finance': {'name': '财务系统', 'modules': ['收费', '报销', '预算', '工资']},
    'logistics': {'name': '后勤系统', 'modules': ['维修', '宿舍', '餐饮', '物业']},
    'hr': {'name': '人事系统', 'modules': ['招聘', '考勤', '绩效', '培训']},
    'research': {'name': '科研系统', 'modules': ['项目', '成果', '专利', '论文']},
    'library': {'name': '图书馆系统', 'modules': ['借阅', '预约', '检索', '座位']},
    'card': {'name': '校园卡系统', 'modules': ['消费', '充值', '挂失', '权限']},
    'access': {'name': '门禁系统', 'modules': ['刷卡', '人脸识别', '访客', '权限']},
    'monitor': {'name': '监控系统', 'modules': ['视频', '报警', '存储', '回放']},
    'energy': {'name': '能源系统', 'modules': ['水电', '能耗', '节能', '监控']},
    'parking': {'name': '停车系统', 'modules': ['车位', '计费', '预约', '管理']},
    'shuttle': {'name': '班车系统', 'modules': ['线路', '班次', '预约', '考勤']},
    'welcome': {'name': '迎新系统', 'modules': ['报到', '缴费', '住宿', '军训']},
    'graduation': {'name': '离校系统', 'modules': ['手续', '清欠', '档案', '证书']}
}

INFRASTRUCTURE = {
    'server': {'name': '服务器', 'types': ['物理服务器', '虚拟机', '云服务器', '容器']},
    'storage': {'name': '存储设备', 'types': ['SAN', 'NAS', 'DAS', '云存储']},
    'network': {'name': '网络设备', 'types': ['交换机', '路由器', '防火墙', '无线AP']},
    'database': {'name': '数据库', 'types': ['MySQL', 'PostgreSQL', 'SQLite', 'MongoDB', 'Redis']},
    'middleware': {'name': '中间件', 'types': ['Web服务器', '应用服务器', '消息队列', '缓存']},
    'security': {'name': '安全设备', 'types': ['防火墙', '入侵检测', '防病毒', 'VPN']}
}

DATA_CENTER = {
    'room': {'name': '机房', 'features': ['面积', '承重', '防静电', '温湿度']},
    'cabinet': {'name': '机柜', 'features': ['U位', 'PDU', '冷却', '监控']},
    'power': {'name': '供电系统', 'features': ['UPS', '配电柜', '发电机', '冗余']},
    'aircon': {'name': '空调系统', 'features': ['精密空调', '新风', '加湿', '节能']},
    'fire': {'name': '消防系统', 'features': ['烟感', '喷淋', '气体灭火', '报警']},
    'dc_monitor': {'name': '环境监控', 'features': ['温湿度', '漏水', '视频', '门禁']}
}

SECURITY_LEVELS = {
    'L1': {'name': '基础级', 'description': '基础安全防护', 'requirements': ['防火墙', '防病毒']},
    'L2': {'name': '标准级', 'description': '标准安全防护', 'requirements': ['入侵检测', '日志审计']},
    'L3': {'name': '增强级', 'description': '增强安全防护', 'requirements': ['数据加密', '访问控制']},
    'L4': {'name': '高级', 'description': '高级安全防护', 'requirements': ['漏洞扫描', '安全评估']},
    'L5': {'name': '最高级', 'description': '最高安全防护', 'requirements': ['等保三级', '渗透测试']}
}

IOT_DEVICES = {
    'temp_humidity': {'name': '温湿度传感器', 'category': '环境'},
    'access_control': {'name': '门禁设备', 'category': '安防'},
    'camera': {'name': '监控摄像头', 'category': '安防'},
    'energy': {'name': '能源计量设备', 'category': '能源'},
    'lighting': {'name': '智能照明', 'category': '设备'},
    'aircon': {'name': '智能空调', 'category': '设备'},
    'sensor': {'name': '通用传感器', 'category': '传感器'}
}

SMART_CLASSROOM = {
    'whiteboard': {'name': '互动白板', 'features': ['触控', '投屏', '书写', '录制']},
    'recording': {'name': '录播系统', 'features': ['自动追踪', '多机位', '实时录制']},
    'live': {'name': '直播系统', 'features': ['实时推流', '互动', '回放']},
    'attendance': {'name': '点名系统', 'features': ['人脸识别', '签到', '统计']},
    'grouping': {'name': '分组讨论', 'features': ['分组', '互动', '展示']},
    'clicker': {'name': '答题器', 'features': ['实时答题', '统计', '反馈']}
}

MOBILE_FEATURES = {
    'schedule': {'name': '课表查询', 'available': ['adult', 'k12']},
    'grades': {'name': '成绩查询', 'available': ['adult', 'k12']},
    'attendance': {'name': '考勤管理', 'available': ['adult', 'k12']},
    'notifications': {'name': '消息通知', 'available': ['adult', 'k12']},
    'payment': {'name': '在线缴费', 'available': ['adult', 'k12']},
    'leave': {'name': '请假申请', 'available': ['adult', 'k12']},
    'activities': {'name': '活动报名', 'available': ['adult', 'k12']}
}


class EducationalInformationService:
    """教育信息化服务"""

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
                    CREATE TABLE IF NOT EXISTS campus_systems (
                        system_id TEXT PRIMARY KEY,
                        system_name TEXT NOT NULL,
                        system_type TEXT NOT NULL,
                        education_type TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        version TEXT,
                        installed_date TEXT,
                        last_updated TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_modules (
                        module_id TEXT PRIMARY KEY,
                        system_id TEXT NOT NULL,
                        module_name TEXT NOT NULL,
                        description TEXT,
                        status TEXT DEFAULT 'enabled',
                        access_level TEXT DEFAULT 'normal',
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY (system_id) REFERENCES campus_systems(system_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS infrastructure (
                        infra_id TEXT PRIMARY KEY,
                        infra_type TEXT NOT NULL,
                        infra_name TEXT NOT NULL,
                        model TEXT,
                        manufacturer TEXT,
                        location TEXT,
                        ip_address TEXT,
                        status TEXT DEFAULT 'running',
                        purchase_date TEXT,
                        warranty_date TEXT,
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS data_center (
                        dc_id TEXT PRIMARY KEY,
                        dc_name TEXT NOT NULL,
                        dc_type TEXT NOT NULL,
                        location TEXT,
                        capacity INTEGER,
                        used_capacity INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'normal',
                        temperature REAL,
                        humidity REAL,
                        power_status TEXT DEFAULT 'normal',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS network_devices (
                        device_id TEXT PRIMARY KEY,
                        device_name TEXT NOT NULL,
                        device_type TEXT NOT NULL,
                        ip_address TEXT,
                        subnet TEXT,
                        gateway TEXT,
                        status TEXT DEFAULT 'running',
                        bandwidth INTEGER,
                        location TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS security_devices (
                        device_id TEXT PRIMARY KEY,
                        device_name TEXT NOT NULL,
                        device_type TEXT NOT NULL,
                        security_level TEXT,
                        ip_address TEXT,
                        status TEXT DEFAULT 'active',
                        last_scan TEXT,
                        threat_count INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS iot_devices (
                        device_id TEXT PRIMARY KEY,
                        device_name TEXT NOT NULL,
                        device_type TEXT NOT NULL,
                        category TEXT,
                        location TEXT,
                        ip_address TEXT,
                        status TEXT DEFAULT 'online',
                        last_data TEXT,
                        data_value TEXT,
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS smart_classrooms (
                        classroom_id TEXT PRIMARY KEY,
                        classroom_name TEXT NOT NULL,
                        location TEXT,
                        capacity INTEGER,
                        equipment TEXT,
                        status TEXT DEFAULT 'available',
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS classroom_bookings (
                        booking_id TEXT PRIMARY KEY,
                        classroom_id TEXT NOT NULL,
                        user_id INTEGER,
                        user_name TEXT,
                        booking_date TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        purpose TEXT,
                        status TEXT DEFAULT 'confirmed',
                        education_type TEXT,
                        created_at TEXT,
                        FOREIGN KEY (classroom_id) REFERENCES smart_classrooms(classroom_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS mobile_users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT NOT NULL,
                        password TEXT NOT NULL,
                        real_name TEXT,
                        role TEXT DEFAULT 'student',
                        education_type TEXT,
                        phone TEXT,
                        email TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS mobile_sessions (
                        session_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        token TEXT,
                        device_info TEXT,
                        login_time TEXT,
                        expire_time TEXT,
                        status TEXT DEFAULT 'active',
                        FOREIGN KEY (user_id) REFERENCES mobile_users(user_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS digital_transformation (
                        project_id TEXT PRIMARY KEY,
                        project_name TEXT NOT NULL,
                        description TEXT,
                        phase TEXT DEFAULT 'planning',
                        budget REAL,
                        start_date TEXT,
                        end_date TEXT,
                        progress INTEGER DEFAULT 0,
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS it_projects (
                        project_id TEXT PRIMARY KEY,
                        project_name TEXT NOT NULL,
                        project_type TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'pending',
                        priority TEXT DEFAULT 'medium',
                        budget REAL,
                        start_date TEXT,
                        end_date TEXT,
                        responsible TEXT,
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_maintenance (
                        maintenance_id TEXT PRIMARY KEY,
                        system_id TEXT,
                        maintenance_type TEXT,
                        description TEXT,
                        scheduled_date TEXT,
                        completed_date TEXT,
                        status TEXT DEFAULT 'scheduled',
                        operator TEXT,
                        created_at TEXT,
                        FOREIGN KEY (system_id) REFERENCES campus_systems(system_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS security_incidents (
                        incident_id TEXT PRIMARY KEY,
                        incident_type TEXT NOT NULL,
                        severity TEXT DEFAULT 'medium',
                        description TEXT,
                        affected_system TEXT,
                        status TEXT DEFAULT 'open',
                        reported_at TEXT,
                        resolved_at TEXT,
                        resolver TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS data_backups (
                        backup_id TEXT PRIMARY KEY,
                        backup_name TEXT NOT NULL,
                        backup_type TEXT,
                        target_system TEXT,
                        backup_date TEXT,
                        size TEXT,
                        status TEXT DEFAULT 'completed',
                        storage_location TEXT,
                        retention_days INTEGER DEFAULT 30,
                        created_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('教育信息化服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 系统管理 ==========

    def add_campus_system(self, system_name: str, system_type: str,
                          education_type: str = 'adult', **kwargs) -> Dict[str, Any]:
        try:
            system_id = f"sys_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO campus_systems (
                            system_id, system_name, system_type, education_type,
                            description, status, version, installed_date,
                            last_updated, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?)
                    ''', (system_id, system_name, system_type, education_type,
                          kwargs.get('description'), kwargs.get('version', '1.0.0'),
                          kwargs.get('installed_date', now[:10]), now, now, now))
                    conn.commit()
                    logger.info(f'创建校园系统: {system_name} ({system_id})')
                    return {'success': True, 'system_id': system_id}
        except Exception as e:
            logger.error(f'创建校园系统失败: {e}')
            return {'success': False, 'error': str(e)}

    def enable_system_module(self, system_id: str, module_name: str,
                             **kwargs) -> Dict[str, Any]:
        try:
            module_id = f"mod_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT system_id FROM campus_systems WHERE system_id = ?', (system_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '系统不存在'}
                    cursor.execute('INSERT OR IGNORE INTO system_modules '
                                 '(module_id, system_id, module_name, description, status, access_level, created_at, updated_at) '
                                 'VALUES (?, ?, ?, ?, \'enabled\', ?, ?, ?)',
                                 (module_id, system_id, module_name, kwargs.get('description'),
                                  kwargs.get('access_level', 'normal'), now, now))
                    conn.commit()
                    return {'success': True, 'module_id': module_id}
        except Exception as e:
            logger.error(f'启用系统模块失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_system_status(self, system_id: str = None, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM campus_systems WHERE 1=1'
                params = []
                if system_id:
                    query += ' AND system_id = ?'
                    params.append(system_id)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' ORDER BY created_at DESC'
                cursor.execute(query, params)
                systems = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'systems': systems}
        except Exception as e:
            logger.error(f'获取系统状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_system_config(self, system_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    set_clause = ', '.join([f'{k} = ?' for k in kwargs.keys()])
                    params = list(kwargs.values()) + [now, system_id]
                    cursor.execute(f'UPDATE campus_systems SET {set_clause}, updated_at = ? WHERE system_id = ?', params)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '系统不存在'}
        except Exception as e:
            logger.error(f'更新系统配置失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 基础设施管理 ==========

    def add_infrastructure(self, infra_type: str, infra_name: str,
                           education_type: str = 'adult', **kwargs) -> Dict[str, Any]:
        try:
            infra_id = f"inf_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO infrastructure (
                            infra_id, infra_type, infra_name, model, manufacturer,
                            location, ip_address, status, purchase_date,
                            warranty_date, education_type, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'running', ?, ?, ?, ?, ?)
                    ''', (infra_id, infra_type, infra_name, kwargs.get('model'),
                          kwargs.get('manufacturer'), kwargs.get('location'),
                          kwargs.get('ip_address'), kwargs.get('purchase_date', now[:10]),
                          kwargs.get('warranty_date'), education_type, now, now))
                    conn.commit()
                    logger.info(f'添加基础设施: {infra_name} ({infra_id})')
                    return {'success': True, 'infra_id': infra_id}
        except Exception as e:
            logger.error(f'添加基础设施失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_network_device(self, device_name: str, device_type: str, **kwargs) -> Dict[str, Any]:
        try:
            device_id = f"net_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO network_devices (
                            device_id, device_name, device_type, ip_address,
                            subnet, gateway, status, bandwidth, location,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'running', ?, ?, ?, ?)
                    ''', (device_id, device_name, device_type, kwargs.get('ip_address'),
                          kwargs.get('subnet'), kwargs.get('gateway'),
                          kwargs.get('bandwidth', 1000), kwargs.get('location'),
                          now, now))
                    conn.commit()
                    return {'success': True, 'device_id': device_id}
        except Exception as e:
            logger.error(f'添加网络设备失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_infrastructure_status(self, infra_type: str = None, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM infrastructure WHERE 1=1'
                params = []
                if infra_type:
                    query += ' AND infra_type = ?'
                    params.append(infra_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' ORDER BY created_at DESC'
                cursor.execute(query, params)
                infra_list = [dict(i) for i in cursor.fetchall()]
                return {'success': True, 'infrastructure': infra_list}
        except Exception as e:
            logger.error(f'获取基础设施状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_infrastructure(self, infra_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    set_clause = ', '.join([f'{k} = ?' for k in kwargs.keys()])
                    params = list(kwargs.values()) + [now, infra_id]
                    cursor.execute(f'UPDATE infrastructure SET {set_clause}, updated_at = ? WHERE infra_id = ?', params)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '基础设施不存在'}
        except Exception as e:
            logger.error(f'更新基础设施失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 数据中心管理 ==========

    def add_data_center(self, dc_name: str, dc_type: str, **kwargs) -> Dict[str, Any]:
        try:
            dc_id = f"dc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO data_center (
                            dc_id, dc_name, dc_type, location, capacity,
                            used_capacity, status, temperature, humidity,
                            power_status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 0, 'normal', ?, ?, 'normal', ?, ?)
                    ''', (dc_id, dc_name, dc_type, kwargs.get('location'),
                          kwargs.get('capacity', 100), kwargs.get('temperature', 22),
                          kwargs.get('humidity', 50), now, now))
                    conn.commit()
                    logger.info(f'添加数据中心: {dc_name} ({dc_id})')
                    return {'success': True, 'dc_id': dc_id}
        except Exception as e:
            logger.error(f'添加数据中心失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_data_center_status(self, dc_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    set_clause = ', '.join([f'{k} = ?' for k in kwargs.keys()])
                    params = list(kwargs.values()) + [now, dc_id]
                    cursor.execute(f'UPDATE data_center SET {set_clause}, updated_at = ? WHERE dc_id = ?', params)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '数据中心不存在'}
        except Exception as e:
            logger.error(f'更新数据中心状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_data_center_status(self) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM data_center ORDER BY created_at DESC')
                dc_list = [dict(d) for d in cursor.fetchall()]
                return {'success': True, 'data_centers': dc_list}
        except Exception as e:
            logger.error(f'获取数据中心状态失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 物联网管理 ==========

    def add_iot_device(self, device_name: str, device_type: str,
                       education_type: str = 'adult', **kwargs) -> Dict[str, Any]:
        try:
            device_id = f"iot_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = IOT_DEVICES.get(device_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO iot_devices (
                            device_id, device_name, device_type, category,
                            location, ip_address, status, last_data,
                            data_value, education_type, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'online', ?, ?, ?, ?, ?)
                    ''', (device_id, device_name, device_type,
                          kwargs.get('category', config.get('category')),
                          kwargs.get('location'), kwargs.get('ip_address'),
                          now, kwargs.get('data_value'), education_type, now, now))
                    conn.commit()
                    logger.info(f'添加物联网设备: {device_name} ({device_id})')
                    return {'success': True, 'device_id': device_id}
        except Exception as e:
            logger.error(f'添加物联网设备失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_iot_device_data(self, device_id: str, data_value: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE iot_devices SET last_data = ?, data_value = ?, updated_at = ? WHERE device_id = ?',
                                 (now, data_value, now, device_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '设备不存在'}
        except Exception as e:
            logger.error(f'更新物联网设备数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_iot_device_status(self, device_type: str = None, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM iot_devices WHERE 1=1'
                params = []
                if device_type:
                    query += ' AND device_type = ?'
                    params.append(device_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' ORDER BY created_at DESC'
                devices = [dict(d) for d in cursor.fetchall()]
                return {'success': True, 'devices': devices}
        except Exception as e:
            logger.error(f'获取物联网设备状态失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 智慧教室 ==========

    def add_smart_classroom(self, classroom_name: str, location: str,
                            education_type: str = 'adult', **kwargs) -> Dict[str, Any]:
        try:
            classroom_id = f"sc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO smart_classrooms (
                            classroom_id, classroom_name, location, capacity,
                            equipment, status, education_type, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 'available', ?, ?, ?)
                    ''', (classroom_id, classroom_name, location,
                          kwargs.get('capacity', 45), kwargs.get('equipment'),
                          education_type, now, now))
                    conn.commit()
                    logger.info(f'添加智慧教室: {classroom_name} ({classroom_id})')
                    return {'success': True, 'classroom_id': classroom_id}
        except Exception as e:
            logger.error(f'添加智慧教室失败: {e}')
            return {'success': False, 'error': str(e)}

    def book_classroom(self, classroom_id: str, user_id: int, user_name: str,
                       booking_date: str, start_time: str, end_time: str,
                       education_type: str = 'adult', **kwargs) -> Dict[str, Any]:
        try:
            booking_id = f"bk_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM smart_classrooms WHERE classroom_id = ?', (classroom_id,))
                    classroom = cursor.fetchone()
                    if not classroom:
                        return {'success': False, 'error': '教室不存在'}
                    if classroom[0] != 'available':
                        return {'success': False, 'error': '教室不可用'}
                    cursor.execute('''
                        INSERT INTO classroom_bookings (
                            booking_id, classroom_id, user_id, user_name,
                            booking_date, start_time, end_time, purpose,
                            status, education_type, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'confirmed', ?, ?)
                    ''', (booking_id, classroom_id, user_id, user_name,
                          booking_date, start_time, end_time, kwargs.get('purpose'),
                          education_type, now))
                    conn.commit()
                    return {'success': True, 'booking_id': booking_id}
        except Exception as e:
            logger.error(f'预约教室失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_classroom_status(self, classroom_id: str = None, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM smart_classrooms WHERE 1=1'
                params = []
                if classroom_id:
                    query += ' AND classroom_id = ?'
                    params.append(classroom_id)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' ORDER BY created_at DESC'
                classrooms = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'classrooms': classrooms}
        except Exception as e:
            logger.error(f'获取教室状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def cancel_classroom_booking(self, booking_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE classroom_bookings SET status = ? WHERE booking_id = ?', ('cancelled', booking_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '预约不存在'}
        except Exception as e:
            logger.error(f'取消教室预约失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 移动校园 ==========

    def add_mobile_user(self, username: str, password: str,
                        education_type: str = 'adult', **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT user_id FROM mobile_users WHERE username = ?', (username,))
                    if cursor.fetchone():
                        return {'success': False, 'error': '用户名已存在'}
                    cursor.execute('''
                        INSERT INTO mobile_users (
                            username, password, real_name, role, education_type,
                            phone, email, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (username, password, kwargs.get('real_name'),
                          kwargs.get('role', 'student'), education_type,
                          kwargs.get('phone'), kwargs.get('email'), now, now))
                    user_id = cursor.lastrowid
                    conn.commit()
                    logger.info(f'添加移动用户: {username} ({user_id})')
                    return {'success': True, 'user_id': user_id}
        except Exception as e:
            logger.error(f'添加移动用户失败: {e}')
            return {'success': False, 'error': str(e)}

    def mobile_login(self, username: str, password: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            expire_time = (datetime.now() + timedelta(hours=24)).isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT user_id, status FROM mobile_users WHERE username = ? AND password = ?', (username, password))
                    user = cursor.fetchone()
                    if not user:
                        return {'success': False, 'error': '用户名或密码错误'}
                    if user[1] != 'active':
                        return {'success': False, 'error': '用户已禁用'}
                    session_id = f"ses_{uuid.uuid4().hex[:16]}"
                    token = uuid.uuid4().hex
                    cursor.execute('''
                        INSERT INTO mobile_sessions (
                            session_id, user_id, token, device_info,
                            login_time, expire_time, status
                        ) VALUES (?, ?, ?, ?, ?, ?, 'active')
                    ''', (session_id, user[0], token, kwargs.get('device_info'), now, expire_time))
                    conn.commit()
                    return {'success': True, 'token': token, 'session_id': session_id}
        except Exception as e:
            logger.error(f'移动登录失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_mobile_features(self, education_type: str = 'adult') -> Dict[str, Any]:
        try:
            features = {}
            for key, value in MOBILE_FEATURES.items():
                if education_type in value.get('available', []):
                    features[key] = value
            return {'success': True, 'features': features}
        except Exception as e:
            logger.error(f'获取移动功能失败: {e}')
            return {'success': False, 'error': str(e)}

    def mobile_logout(self, session_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE mobile_sessions SET status = ? WHERE session_id = ?', ('expired', session_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '会话不存在'}
        except Exception as e:
            logger.error(f'移动登出失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 数字化转型 ==========

    def add_transformation_project(self, project_name: str, education_type: str = 'adult', **kwargs) -> Dict[str, Any]:
        try:
            project_id = f"dtp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO digital_transformation (
                            project_id, project_name, description, phase,
                            budget, start_date, end_date, progress,
                            education_type, created_at, updated_at
                        ) VALUES (?, ?, ?, 'planning', ?, ?, ?, 0, ?, ?, ?)
                    ''', (project_id, project_name, kwargs.get('description'),
                          kwargs.get('budget', 0), kwargs.get('start_date', now[:10]),
                          kwargs.get('end_date'), education_type, now, now))
                    conn.commit()
                    logger.info(f'添加数字化转型项目: {project_name} ({project_id})')
                    return {'success': True, 'project_id': project_id}
        except Exception as e:
            logger.error(f'添加数字化转型项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_transformation_progress(self, project_id: str, progress: int, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    phase = 'completed' if progress >= 100 else ('in_progress' if progress > 0 else 'planning')
                    cursor.execute('UPDATE digital_transformation SET progress = ?, phase = ?, updated_at = ? WHERE project_id = ?',
                                 (progress, phase, now, project_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'phase': phase}
                    return {'success': False, 'error': '项目不存在'}
        except Exception as e:
            logger.error(f'更新转型进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_transformation_status(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM digital_transformation WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' ORDER BY created_at DESC'
                projects = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'projects': projects}
        except Exception as e:
            logger.error(f'获取转型状态失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== IT项目管理 ==========

    def add_it_project(self, project_name: str, project_type: str,
                       education_type: str = 'adult', **kwargs) -> Dict[str, Any]:
        try:
            project_id = f"itp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO it_projects (
                            project_id, project_name, project_type, description,
                            status, priority, budget, start_date, end_date,
                            responsible, education_type, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (project_id, project_name, project_type, kwargs.get('description'),
                          kwargs.get('priority', 'medium'), kwargs.get('budget', 0),
                          kwargs.get('start_date', now[:10]), kwargs.get('end_date'),
                          kwargs.get('responsible'), education_type, now, now))
                    conn.commit()
                    logger.info(f'添加IT项目: {project_name} ({project_id})')
                    return {'success': True, 'project_id': project_id}
        except Exception as e:
            logger.error(f'添加IT项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_it_project_status(self, project_id: str, status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE it_projects SET status = ?, updated_at = ? WHERE project_id = ?', (status, now, project_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '项目不存在'}
        except Exception as e:
            logger.error(f'更新IT项目状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_it_projects(self, project_type: str = None, status: str = None,
                        education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM it_projects WHERE 1=1'
                params = []
                if project_type:
                    query += ' AND project_type = ?'
                    params.append(project_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' ORDER BY created_at DESC'
                projects = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'projects': projects}
        except Exception as e:
            logger.error(f'获取IT项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def delete_it_project(self, project_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM it_projects WHERE project_id = ?', (project_id,))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '项目不存在'}
        except Exception as e:
            logger.error(f'删除IT项目失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 系统维护 ==========

    def schedule_maintenance(self, system_id: str, maintenance_type: str,
                             scheduled_date: str, **kwargs) -> Dict[str, Any]:
        try:
            maintenance_id = f"mtn_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT system_id FROM campus_systems WHERE system_id = ?', (system_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '系统不存在'}
                    cursor.execute('''
                        INSERT INTO system_maintenance (
                            maintenance_id, system_id, maintenance_type, description,
                            scheduled_date, completed_date, status, operator, created_at
                        ) VALUES (?, ?, ?, ?, ?, NULL, 'scheduled', ?, ?)
                    ''', (maintenance_id, system_id, maintenance_type, kwargs.get('description'),
                          scheduled_date, kwargs.get('operator'), now))
                    conn.commit()
                    return {'success': True, 'maintenance_id': maintenance_id}
        except Exception as e:
            logger.error(f'计划维护失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_maintenance(self, maintenance_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE system_maintenance SET status = ?, completed_date = ? WHERE maintenance_id = ?',
                                 ('completed', now, maintenance_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '维护记录不存在'}
        except Exception as e:
            logger.error(f'完成维护失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_maintenance_history(self, system_id: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM system_maintenance WHERE 1=1'
                params = []
                if system_id:
                    query += ' AND system_id = ?'
                    params.append(system_id)
                query += ' ORDER BY scheduled_date DESC'
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'maintenance_records': records}
        except Exception as e:
            logger.error(f'获取维护历史失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 安全管理 ==========

    def add_security_device(self, device_name: str, device_type: str,
                            security_level: str = 'L2', **kwargs) -> Dict[str, Any]:
        try:
            device_id = f"sec_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO security_devices (
                            device_id, device_name, device_type, security_level,
                            ip_address, status, last_scan, threat_count,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 'active', ?, 0, ?, ?)
                    ''', (device_id, device_name, device_type, security_level,
                          kwargs.get('ip_address'), now, now, now))
                    conn.commit()
                    return {'success': True, 'device_id': device_id}
        except Exception as e:
            logger.error(f'添加安全设备失败: {e}')
            return {'success': False, 'error': str(e)}

    def report_security_incident(self, incident_type: str, **kwargs) -> Dict[str, Any]:
        try:
            incident_id = f"inc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO security_incidents (
                            incident_id, incident_type, severity, description,
                            affected_system, status, reported_at, resolved_at,
                            resolver, created_at
                        ) VALUES (?, ?, ?, ?, ?, 'open', ?, NULL, ?, ?)
                    ''', (incident_id, incident_type, kwargs.get('severity', 'medium'),
                          kwargs.get('description'), kwargs.get('affected_system'),
                          now, kwargs.get('resolver'), now))
                    conn.commit()
                    logger.warning(f'安全事件报告: {incident_type} ({incident_id})')
                    return {'success': True, 'incident_id': incident_id}
        except Exception as e:
            logger.error(f'报告安全事件失败: {e}')
            return {'success': False, 'error': str(e)}

    def resolve_security_incident(self, incident_id: str, resolver: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE security_incidents SET status = ?, resolved_at = ?, resolver = ? WHERE incident_id = ?',
                                 ('resolved', now, resolver, incident_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '事件不存在'}
        except Exception as e:
            logger.error(f'解决安全事件失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_security_status(self) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM security_devices ORDER BY created_at DESC')
                devices = [dict(d) for d in cursor.fetchall()]
                cursor.execute('SELECT * FROM security_incidents WHERE status = ? ORDER BY reported_at DESC', ('open',))
                open_incidents = [dict(i) for i in cursor.fetchall()]
                return {'success': True, 'devices': devices, 'open_incidents': open_incidents}
        except Exception as e:
            logger.error(f'获取安全状态失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 数据备份 ==========

    def create_backup(self, backup_name: str, backup_type: str,
                      target_system: str, **kwargs) -> Dict[str, Any]:
        try:
            backup_id = f"bck_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO data_backups (
                            backup_id, backup_name, backup_type, target_system,
                            backup_date, size, status, storage_location,
                            retention_days, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'completed', ?, ?, ?)
                    ''', (backup_id, backup_name, backup_type, target_system,
                          now[:19], kwargs.get('size', '0KB'),
                          kwargs.get('storage_location'),
                          kwargs.get('retention_days', 30), now))
                    conn.commit()
                    logger.info(f'创建备份: {backup_name} ({backup_id})')
                    return {'success': True, 'backup_id': backup_id}
        except Exception as e:
            logger.error(f'创建备份失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_backup_history(self, target_system: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM data_backups WHERE 1=1'
                params = []
                if target_system:
                    query += ' AND target_system = ?'
                    params.append(target_system)
                query += ' ORDER BY backup_date DESC'
                backups = [dict(b) for b in cursor.fetchall()]
                return {'success': True, 'backups': backups}
        except Exception as e:
            logger.error(f'获取备份历史失败: {e}')
            return {'success': False, 'error': str(e)}

    def delete_backup(self, backup_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM data_backups WHERE backup_id = ?', (backup_id,))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '备份不存在'}
        except Exception as e:
            logger.error(f'删除备份失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_service_summary(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                params = []
                where_clause = ''
                if education_type:
                    where_clause = 'WHERE education_type = ?'
                    params.append(education_type)

                cursor.execute(f'SELECT COUNT(*) FROM campus_systems {where_clause}', params)
                system_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM infrastructure {where_clause}', params)
                infra_count = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM data_center')
                dc_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM iot_devices {where_clause}', params)
                iot_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM smart_classrooms {where_clause}', params)
                classroom_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM mobile_users {where_clause}', params)
                mobile_user_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM digital_transformation {where_clause}', params)
                dt_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM it_projects {where_clause}', params)
                it_count = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM security_incidents WHERE status = ?', ('open',))
                open_incidents = cursor.fetchone()[0]

                return {
                    'success': True,
                    'summary': {
                        'campus_systems': system_count,
                        'infrastructure': infra_count,
                        'data_centers': dc_count,
                        'iot_devices': iot_count,
                        'smart_classrooms': classroom_count,
                        'mobile_users': mobile_user_count,
                        'digital_transformation': dt_count,
                        'it_projects': it_count,
                        'open_security_incidents': open_incidents
                    }
                }
        except Exception as e:
            logger.error(f'获取服务统计失败: {e}')
            return {'success': False, 'error': str(e)}