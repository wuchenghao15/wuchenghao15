#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育智能硬件服务 (v15.16.0)
====================================
提供智能设备管理、物联网连接、智慧教室硬件、智能终端、传感器网络、
设备运维、数据采集、硬件集成等综合管理服务。

核心能力：
1. 设备管理 - 设备注册、状态监控、设备配置、设备分组
2. 物联网连接 - 连接管理、协议支持、网络配置、连接日志
3. 传感器网络 - 传感器管理、数据采集、网络拓扑、节点监控
4. 智慧教室 - 教室管理、设备绑定、环境监测、智能控制
5. 设备运维 - 维护计划、故障修复、设备校准、安全检查、性能优化
6. 数据采集 - 采集规则、实时采集、批量处理、数据存储
7. 硬件集成 - 集成配置、接口对接、数据同步、生态整合
8. 设备预警 - 预警规则、异常检测、告警通知、告警处理
9. 更新管理 - 固件更新、版本管理、更新记录
10. 统计分析 - 设备统计、使用分析、运维报告
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_smart_hardware_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationSmartHardware')


# ========== 智能硬件配置 ==========

DEVICE_CATEGORIES = {
    'terminal': {'name': '智能终端', 'description': '学生/教师使用的智能设备'},
    'sensor': {'name': '传感器', 'description': '环境监测与数据采集设备'},
    'controller': {'name': '控制器', 'description': '智能控制与执行设备'},
    'display': {'name': '显示设备', 'description': '大屏显示与交互终端'},
    'interaction': {'name': '交互设备', 'description': '教学互动与反馈设备'},
    'network': {'name': '网络设备', 'description': '网络连接与通信设备'},
    'security': {'name': '安全设备', 'description': '安防监控与门禁设备'},
    'storage': {'name': '存储设备', 'description': '数据存储与备份设备'}
}

SMART_DEVICES = {
    'smart_board': {'name': '智能黑板', 'category': 'display', 'education_type': ['k12', 'adult']},
    'smart_desk': {'name': '智能课桌', 'category': 'interaction', 'education_type': ['k12']},
    'smart_lamp': {'name': '智能台灯', 'category': 'controller', 'education_type': ['k12']},
    'smart_pen': {'name': '智能笔', 'category': 'terminal', 'education_type': ['k12', 'adult']},
    'smart_bracelet': {'name': '智能手环', 'category': 'terminal', 'education_type': ['k12']},
    'smart_camera': {'name': '智能摄像头', 'category': 'security', 'education_type': ['k12', 'adult']},
    'smart_speaker': {'name': '智能音箱', 'category': 'interaction', 'education_type': ['k12', 'adult']},
    'smart_gateway': {'name': '智能网关', 'category': 'network', 'education_type': ['k12', 'adult']}
}

SENSOR_TYPES = {
    'temperature': {'name': '温湿度传感器', 'unit': '°C/%RH', 'precision': '0.1'},
    'illumination': {'name': '光照传感器', 'unit': 'lux', 'precision': '1'},
    'air_quality': {'name': '空气质量传感器', 'unit': 'AQI', 'precision': '1'},
    'human_detection': {'name': '人体感应传感器', 'unit': 'bool', 'precision': '-'},
    'sound': {'name': '声音传感器', 'unit': 'dB', 'precision': '1'},
    'motion': {'name': '运动传感器', 'unit': 'm/s²', 'precision': '0.01'},
    'pressure': {'name': '压力传感器', 'unit': 'kPa', 'precision': '0.1'},
    'biometric': {'name': '生物识别传感器', 'unit': '-', 'precision': '-'}
}

IOT_PROTOCOLS = {
    'wifi': {'name': 'WiFi', 'bandwidth': '2.4G/5G', 'range': '100m', 'power_consumption': 'medium'},
    'ble': {'name': 'BLE蓝牙', 'bandwidth': '1Mbps', 'range': '50m', 'power_consumption': 'low'},
    'zigbee': {'name': 'Zigbee', 'bandwidth': '250kbps', 'range': '100m', 'power_consumption': 'low'},
    'zwave': {'name': 'ZWave', 'bandwidth': '100kbps', 'range': '100m', 'power_consumption': 'low'},
    'mqtt': {'name': 'MQTT', 'bandwidth': 'variable', 'range': 'network', 'power_consumption': 'low'},
    'coap': {'name': 'CoAP', 'bandwidth': 'variable', 'range': 'network', 'power_consumption': 'low'},
    'http': {'name': 'HTTP', 'bandwidth': 'high', 'range': 'network', 'power_consumption': 'high'},
    'websocket': {'name': 'WebSocket', 'bandwidth': 'high', 'range': 'network', 'power_consumption': 'medium'}
}

NETWORK_TOPOLOGY = {
    'star': {'name': '星型拓扑', 'description': '中心化网络结构', 'scalability': 'medium'},
    'mesh': {'name': '网状拓扑', 'description': '去中心化自组织网络', 'scalability': 'high'},
    'tree': {'name': '树形拓扑', 'description': '层级化网络结构', 'scalability': 'medium'},
    'bus': {'name': '总线拓扑', 'description': '共享总线结构', 'scalability': 'low'},
    'hybrid': {'name': '混合拓扑', 'description': '多种拓扑组合', 'scalability': 'high'}
}

MAINTENANCE_TYPES = {
    'preventive': {'name': '预防性维护', 'frequency': 'monthly', 'description': '定期检查与保养'},
    'repair': {'name': '故障修复', 'frequency': 'on-demand', 'description': '设备故障维修'},
    'upgrade': {'name': '升级更新', 'frequency': 'quarterly', 'description': '固件与软件升级'},
    'calibration': {'name': '设备校准', 'frequency': 'semiannually', 'description': '传感器精度校准'},
    'security': {'name': '安全检查', 'frequency': 'monthly', 'description': '安全漏洞检测与修复'},
    'optimization': {'name': '性能优化', 'frequency': 'quarterly', 'description': '设备性能调优'}
}

DATA_COLLECTION = {
    'realtime': {'name': '实时采集', 'interval': 'continuous', 'description': '持续实时数据采集'},
    'periodic': {'name': '定时采集', 'interval': 'configurable', 'description': '按设定时间间隔采集'},
    'event_triggered': {'name': '事件触发', 'interval': 'event-based', 'description': '特定事件触发采集'},
    'batch': {'name': '批量采集', 'interval': 'scheduled', 'description': '定时批量数据收集'},
    'continuous': {'name': '连续采集', 'interval': '24/7', 'description': '全天候不间断采集'},
    'on_demand': {'name': '按需采集', 'interval': 'request-based', 'description': '根据请求触发采集'}
}

INTEGRATION_LEVELS = {
    'basic': {'name': '基础集成', 'features': ['数据同步', '状态监控'], 'complexity': 'low'},
    'deep': {'name': '深度集成', 'features': ['双向控制', '智能联动'], 'complexity': 'medium'},
    'smart': {'name': '智能集成', 'features': ['AI分析', '自动决策'], 'complexity': 'high'},
    'ecosystem': {'name': '生态集成', 'features': ['多平台协同', '开放接口'], 'complexity': 'very_high'}
}


class EducationSmartHardwareService:
    """教育智能硬件服务"""

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
                    CREATE TABLE IF NOT EXISTS smart_devices (
                        device_id TEXT PRIMARY KEY,
                        device_name TEXT NOT NULL,
                        device_type TEXT NOT NULL,
                        category TEXT,
                        education_type TEXT,
                        manufacturer TEXT,
                        model TEXT,
                        serial_number TEXT UNIQUE,
                        firmware_version TEXT,
                        ip_address TEXT,
                        mac_address TEXT UNIQUE,
                        location TEXT,
                        status TEXT DEFAULT 'offline',
                        last_online TEXT,
                        metadata TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS device_registry (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        device_id TEXT NOT NULL,
                        registered_by INTEGER,
                        registered_name TEXT,
                        registration_date TEXT,
                        classroom_id TEXT,
                        assigned_user_id INTEGER,
                        assigned_user_name TEXT,
                        status TEXT DEFAULT 'registered',
                        FOREIGN KEY(device_id) REFERENCES smart_devices(device_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS device_status (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        device_id TEXT NOT NULL,
                        status TEXT NOT NULL,
                        battery_level INTEGER,
                        signal_strength INTEGER,
                        temperature REAL,
                        cpu_usage REAL,
                        memory_usage REAL,
                        disk_usage REAL,
                        uptime INTEGER,
                        timestamp TEXT,
                        FOREIGN KEY(device_id) REFERENCES smart_devices(device_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS iot_connections (
                        connection_id TEXT PRIMARY KEY,
                        device_id TEXT NOT NULL,
                        protocol TEXT NOT NULL,
                        gateway_id TEXT,
                        connection_status TEXT DEFAULT 'disconnected',
                        connected_at TEXT,
                        disconnected_at TEXT,
                        signal_strength INTEGER,
                        latency INTEGER,
                        data_rate INTEGER,
                        FOREIGN KEY(device_id) REFERENCES smart_devices(device_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS connection_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        connection_id TEXT NOT NULL,
                        device_id TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        event_description TEXT,
                        timestamp TEXT,
                        FOREIGN KEY(device_id) REFERENCES smart_devices(device_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sensor_network (
                        network_id TEXT PRIMARY KEY,
                        network_name TEXT NOT NULL,
                        topology TEXT DEFAULT 'star',
                        education_type TEXT,
                        gateway_id TEXT,
                        node_count INTEGER DEFAULT 0,
                        coverage_area TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sensor_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        network_id TEXT NOT NULL,
                        sensor_id TEXT NOT NULL,
                        sensor_type TEXT NOT NULL,
                        value REAL NOT NULL,
                        unit TEXT,
                        timestamp TEXT,
                        location TEXT,
                        FOREIGN KEY(network_id) REFERENCES sensor_network(network_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS smart_classrooms (
                        classroom_id TEXT PRIMARY KEY,
                        classroom_name TEXT NOT NULL,
                        education_type TEXT,
                        school_id INTEGER,
                        school_name TEXT,
                        grade_level TEXT,
                        capacity INTEGER DEFAULT 50,
                        floor TEXT,
                        building TEXT,
                        has_ac INTEGER DEFAULT 0,
                        has_air_purifier INTEGER DEFAULT 0,
                        has_smart_board INTEGER DEFAULT 0,
                        has_sensor_network INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS classroom_devices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        classroom_id TEXT NOT NULL,
                        device_id TEXT NOT NULL,
                        device_role TEXT,
                        installed_at TEXT,
                        FOREIGN KEY(classroom_id) REFERENCES smart_classrooms(classroom_id),
                        FOREIGN KEY(device_id) REFERENCES smart_devices(device_id),
                        UNIQUE(classroom_id, device_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS device_maintenance (
                        maintenance_id TEXT PRIMARY KEY,
                        device_id TEXT NOT NULL,
                        maintenance_type TEXT NOT NULL,
                        scheduled_date TEXT,
                        priority TEXT DEFAULT 'medium',
                        assignee_id INTEGER,
                        assignee_name TEXT,
                        status TEXT DEFAULT 'pending',
                        description TEXT,
                        FOREIGN KEY(device_id) REFERENCES smart_devices(device_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS maintenance_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        maintenance_id TEXT NOT NULL,
                        device_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        result TEXT,
                        technician_id INTEGER,
                        technician_name TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        notes TEXT,
                        FOREIGN KEY(device_id) REFERENCES smart_devices(device_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS device_updates (
                        update_id TEXT PRIMARY KEY,
                        device_type TEXT NOT NULL,
                        firmware_version TEXT NOT NULL,
                        previous_version TEXT,
                        release_date TEXT,
                        update_size INTEGER,
                        changelog TEXT,
                        is_mandatory INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'available',
                        education_type TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS update_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        update_id TEXT NOT NULL,
                        device_id TEXT NOT NULL,
                        start_time TEXT,
                        end_time TEXT,
                        result TEXT,
                        error_message TEXT,
                        FOREIGN KEY(device_id) REFERENCES smart_devices(device_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS data_collectors (
                        collector_id TEXT PRIMARY KEY,
                        collector_name TEXT NOT NULL,
                        data_source TEXT NOT NULL,
                        collection_type TEXT DEFAULT 'periodic',
                        interval INTEGER DEFAULT 60,
                        education_type TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS collection_rules (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        collector_id TEXT NOT NULL,
                        rule_name TEXT NOT NULL,
                        filter_condition TEXT,
                        aggregation_type TEXT,
                        retention_days INTEGER DEFAULT 30,
                        enabled INTEGER DEFAULT 1,
                        FOREIGN KEY(collector_id) REFERENCES data_collectors(collector_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS hardware_integrations (
                        integration_id TEXT PRIMARY KEY,
                        integration_name TEXT NOT NULL,
                        integration_level TEXT DEFAULT 'basic',
                        provider TEXT,
                        api_endpoint TEXT,
                        education_type TEXT,
                        status TEXT DEFAULT 'configured',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS integration_config (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        integration_id TEXT NOT NULL,
                        config_key TEXT NOT NULL,
                        config_value TEXT,
                        FOREIGN KEY(integration_id) REFERENCES hardware_integrations(integration_id),
                        UNIQUE(integration_id, config_key)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS device_alerts (
                        alert_id TEXT PRIMARY KEY,
                        device_id TEXT NOT NULL,
                        alert_type TEXT NOT NULL,
                        severity TEXT DEFAULT 'warning',
                        message TEXT,
                        status TEXT DEFAULT 'active',
                        triggered_at TEXT,
                        resolved_at TEXT,
                        FOREIGN KEY(device_id) REFERENCES smart_devices(device_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alert_rules (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        rule_name TEXT NOT NULL,
                        device_type TEXT,
                        alert_type TEXT NOT NULL,
                        condition TEXT NOT NULL,
                        severity TEXT DEFAULT 'warning',
                        notification_enabled INTEGER DEFAULT 1,
                        auto_resolve INTEGER DEFAULT 0,
                        education_type TEXT,
                        enabled INTEGER DEFAULT 1,
                        created_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('教育智能硬件服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 设备管理 ==========

    def register_device(self, device_name: str, device_type: str,
                        serial_number: str, mac_address: str,
                        **kwargs) -> Dict[str, Any]:
        try:
            device_id = f"dev_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = SMART_DEVICES.get(device_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO smart_devices (
                            device_id, device_name, device_type, category,
                            education_type, manufacturer, model,
                            serial_number, firmware_version, ip_address,
                            mac_address, location, status, last_online,
                            metadata, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'offline', NULL, ?, ?, ?)
                    ''', (device_id, device_name, device_type,
                          kwargs.get('category', config.get('category')),
                          kwargs.get('education_type'),
                          kwargs.get('manufacturer'), kwargs.get('model'),
                          serial_number, kwargs.get('firmware_version', '1.0.0'),
                          kwargs.get('ip_address'), mac_address,
                          kwargs.get('location'),
                          json.dumps(kwargs.get('metadata', {})), now, now))
                    conn.commit()
                    logger.info(f'注册智能设备: {device_name} ({device_id})')
                    return {'success': True, 'device_id': device_id}
        except sqlite3.IntegrityError as e:
            if 'serial_number' in str(e):
                return {'success': False, 'error': '序列号已存在'}
            if 'mac_address' in str(e):
                return {'success': False, 'error': 'MAC地址已存在'}
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f'注册设备失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_device_status(self, device_id: str, status: str,
                             **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE smart_devices SET status = ?, last_online = ?, updated_at = ? WHERE device_id = ?',
                                 (status, now if status == 'online' else None, now, device_id))
                    if cursor.rowcount > 0:
                        cursor.execute('''
                            INSERT INTO device_status (device_id, status, battery_level,
                            signal_strength, temperature, cpu_usage, memory_usage,
                            disk_usage, uptime, timestamp)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (device_id, status, kwargs.get('battery_level'),
                              kwargs.get('signal_strength'), kwargs.get('temperature'),
                              kwargs.get('cpu_usage'), kwargs.get('memory_usage'),
                              kwargs.get('disk_usage'), kwargs.get('uptime'), now))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '设备不存在'}
        except Exception as e:
            logger.error(f'更新设备状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def configure_device(self, device_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    update_fields = []
                    update_params = []
                    if 'ip_address' in kwargs:
                        update_fields.append('ip_address = ?')
                        update_params.append(kwargs['ip_address'])
                    if 'location' in kwargs:
                        update_fields.append('location = ?')
                        update_params.append(kwargs['location'])
                    if 'firmware_version' in kwargs:
                        update_fields.append('firmware_version = ?')
                        update_params.append(kwargs['firmware_version'])
                    if 'metadata' in kwargs:
                        update_fields.append('metadata = ?')
                        update_params.append(json.dumps(kwargs['metadata']))
                    if update_fields:
                        update_params.append(device_id)
                        update_params.append(now)
                        cursor.execute(f'UPDATE smart_devices SET {", ".join(update_fields)}, updated_at = ? WHERE device_id = ?',
                                     update_params)
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '未提供更新字段'}
        except Exception as e:
            logger.error(f'配置设备失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_device_info(self, device_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM smart_devices WHERE device_id = ?', (device_id,))
                device = cursor.fetchone()
                if device:
                    device_dict = dict(device)
                    if device_dict.get('metadata'):
                        device_dict['metadata'] = json.loads(device_dict['metadata'])
                    return {'success': True, 'device': device_dict}
                return {'success': False, 'error': '设备不存在'}
        except Exception as e:
            logger.error(f'获取设备信息失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 物联网连接 ==========

    def establish_connection(self, device_id: str, protocol: str,
                             **kwargs) -> Dict[str, Any]:
        try:
            connection_id = f"conn_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO iot_connections (
                            connection_id, device_id, protocol, gateway_id,
                            connection_status, connected_at, signal_strength,
                            latency, data_rate
                        ) VALUES (?, ?, ?, ?, 'connected', ?, ?, ?, ?)
                    ''', (connection_id, device_id, protocol,
                          kwargs.get('gateway_id'), now,
                          kwargs.get('signal_strength'),
                          kwargs.get('latency'), kwargs.get('data_rate')))
                    cursor.execute('INSERT INTO connection_logs (connection_id, device_id, event_type, event_description, timestamp) VALUES (?, ?, ?, ?, ?)',
                                 (connection_id, device_id, 'connected', f'使用{protocol}协议连接', now))
                    conn.commit()
                    return {'success': True, 'connection_id': connection_id}
        except Exception as e:
            logger.error(f'建立连接失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_connection_status(self, device_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM iot_connections WHERE device_id = ? ORDER BY connected_at DESC LIMIT 1', (device_id,))
                connection = cursor.fetchone()
                if connection:
                    return {'success': True, 'connection': dict(connection)}
                return {'success': False, 'error': '无连接记录'}
        except Exception as e:
            logger.error(f'获取连接状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def disconnect_device(self, device_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT connection_id FROM iot_connections WHERE device_id = ? AND connection_status = ?', (device_id, 'connected'))
                    row = cursor.fetchone()
                    if row:
                        connection_id = row[0]
                        cursor.execute('UPDATE iot_connections SET connection_status = ?, disconnected_at = ? WHERE connection_id = ?',
                                     ('disconnected', now, connection_id))
                        cursor.execute('INSERT INTO connection_logs (connection_id, device_id, event_type, event_description, timestamp) VALUES (?, ?, ?, ?, ?)',
                                     (connection_id, device_id, 'disconnected', '设备断开连接', now))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '设备未连接'}
        except Exception as e:
            logger.error(f'断开连接失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_connection_logs(self, device_id: str, limit: int = 50) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM connection_logs WHERE device_id = ? ORDER BY timestamp DESC LIMIT ?', (device_id, limit))
                logs = [dict(log) for log in cursor.fetchall()]
                return {'success': True, 'logs': logs}
        except Exception as e:
            logger.error(f'获取连接日志失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 传感器网络 ==========

    def create_sensor_network(self, network_name: str, **kwargs) -> Dict[str, Any]:
        try:
            network_id = f"net_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO sensor_network (
                            network_id, network_name, topology, education_type,
                            gateway_id, node_count, coverage_area, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 0, ?, 'active', ?, ?)
                    ''', (network_id, network_name,
                          kwargs.get('topology', 'star'),
                          kwargs.get('education_type'),
                          kwargs.get('gateway_id'),
                          kwargs.get('coverage_area'), now, now))
                    conn.commit()
                    logger.info(f'创建传感器网络: {network_name} ({network_id})')
                    return {'success': True, 'network_id': network_id}
        except Exception as e:
            logger.error(f'创建传感器网络失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_sensor_node(self, network_id: str, sensor_id: str,
                        sensor_type: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            config = SENSOR_TYPES.get(sensor_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE sensor_network SET node_count = node_count + 1, updated_at = ? WHERE network_id = ?', (now, network_id))
                    cursor.execute('''
                        INSERT INTO sensor_data (network_id, sensor_id, sensor_type,
                        value, unit, timestamp, location)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (network_id, sensor_id, sensor_type,
                          kwargs.get('initial_value', 0),
                          config.get('unit', ''), now, kwargs.get('location')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加传感器节点失败: {e}')
            return {'success': False, 'error': str(e)}

    def collect_sensor_data(self, network_id: str, sensor_id: str = None,
                            **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    if sensor_id:
                        cursor.execute('SELECT sensor_type FROM sensor_data WHERE network_id = ? AND sensor_id = ? ORDER BY timestamp DESC LIMIT 1', (network_id, sensor_id))
                        row = cursor.fetchone()
                        if not row:
                            return {'success': False, 'error': '传感器不存在'}
                        sensor_type = row[0]
                        config = SENSOR_TYPES.get(sensor_type, {})
                        cursor.execute('''
                            INSERT INTO sensor_data (network_id, sensor_id, sensor_type,
                            value, unit, timestamp, location)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (network_id, sensor_id, sensor_type,
                              kwargs.get('value', 0),
                              config.get('unit', ''), now, kwargs.get('location')))
                    else:
                        cursor.execute('SELECT DISTINCT sensor_id, sensor_type FROM sensor_data WHERE network_id = ?', (network_id,))
                        sensors = cursor.fetchall()
                        for sensor in sensors:
                            sid, stype = sensor
                            config = SENSOR_TYPES.get(stype, {})
                            cursor.execute('''
                                INSERT INTO sensor_data (network_id, sensor_id, sensor_type,
                                value, unit, timestamp, location)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            ''', (network_id, sid, stype, kwargs.get('value', 0),
                                  config.get('unit', ''), now, kwargs.get('location')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'采集传感器数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_sensor_data(self, network_id: str, sensor_id: str = None,
                        start_time: str = None, end_time: str = None,
                        limit: int = 100) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM sensor_data WHERE network_id = ?'
                params = [network_id]
                if sensor_id:
                    query += ' AND sensor_id = ?'
                    params.append(sensor_id)
                if start_time:
                    query += ' AND timestamp >= ?'
                    params.append(start_time)
                if end_time:
                    query += ' AND timestamp <= ?'
                    params.append(end_time)
                query += ' ORDER BY timestamp DESC LIMIT ?'
                params.append(limit)
                cursor.execute(query, params)
                data = [dict(d) for d in cursor.fetchall()]
                return {'success': True, 'data': data}
        except Exception as e:
            logger.error(f'获取传感器数据失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 智慧教室 ==========

    def create_smart_classroom(self, classroom_name: str, **kwargs) -> Dict[str, Any]:
        try:
            classroom_id = f"cls_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO smart_classrooms (
                            classroom_id, classroom_name, education_type,
                            school_id, school_name, grade_level, capacity,
                            floor, building, has_ac, has_air_purifier,
                            has_smart_board, has_sensor_network, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (classroom_id, classroom_name,
                          kwargs.get('education_type'),
                          kwargs.get('school_id'), kwargs.get('school_name'),
                          kwargs.get('grade_level'), kwargs.get('capacity', 50),
                          kwargs.get('floor'), kwargs.get('building'),
                          kwargs.get('has_ac', 0), kwargs.get('has_air_purifier', 0),
                          kwargs.get('has_smart_board', 0), kwargs.get('has_sensor_network', 0),
                          now, now))
                    conn.commit()
                    logger.info(f'创建智慧教室: {classroom_name} ({classroom_id})')
                    return {'success': True, 'classroom_id': classroom_id}
        except Exception as e:
            logger.error(f'创建智慧教室失败: {e}')
            return {'success': False, 'error': str(e)}

    def bind_device_to_classroom(self, classroom_id: str, device_id: str,
                                  device_role: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT OR IGNORE INTO classroom_devices (classroom_id, device_id, device_role, installed_at) VALUES (?, ?, ?, ?)',
                                 (classroom_id, device_id, device_role, now))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '设备已绑定该教室'}
        except Exception as e:
            logger.error(f'绑定设备到教室失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_classroom_devices(self, classroom_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT sd.*, cd.device_role, cd.installed_at
                    FROM smart_devices sd
                    JOIN classroom_devices cd ON sd.device_id = cd.device_id
                    WHERE cd.classroom_id = ?
                ''', (classroom_id,))
                devices = [dict(d) for d in cursor.fetchall()]
                return {'success': True, 'devices': devices}
        except Exception as e:
            logger.error(f'获取教室设备失败: {e}')
            return {'success': False, 'error': str(e)}

    def control_classroom_device(self, classroom_id: str, device_id: str,
                                  action: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM classroom_devices WHERE classroom_id = ? AND device_id = ?', (classroom_id, device_id))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '设备未绑定该教室'}
                    cursor.execute('SELECT status FROM smart_devices WHERE device_id = ?', (device_id,))
                    device = cursor.fetchone()
                    if not device:
                        return {'success': False, 'error': '设备不存在'}
                    new_status = 'online' if action in ['turn_on', 'activate'] else ('offline' if action in ['turn_off', 'deactivate'] else device[0])
                    cursor.execute('UPDATE smart_devices SET status = ?, updated_at = ? WHERE device_id = ?', (new_status, now, device_id))
                    cursor.execute('INSERT INTO device_status (device_id, status, timestamp) VALUES (?, ?, ?)', (device_id, new_status, now))
                    conn.commit()
                    return {'success': True, 'action': action, 'status': new_status}
        except Exception as e:
            logger.error(f'控制教室设备失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 设备运维 ==========

    def create_maintenance_task(self, device_id: str, maintenance_type: str,
                                **kwargs) -> Dict[str, Any]:
        try:
            maintenance_id = f"mnt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = MAINTENANCE_TYPES.get(maintenance_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO device_maintenance (
                            maintenance_id, device_id, maintenance_type,
                            scheduled_date, priority, assignee_id,
                            assignee_name, status, description
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                    ''', (maintenance_id, device_id, maintenance_type,
                          kwargs.get('scheduled_date', now[:10]),
                          kwargs.get('priority', 'medium'),
                          kwargs.get('assignee_id'), kwargs.get('assignee_name'),
                          kwargs.get('description', config.get('description', ''))))
                    conn.commit()
                    logger.info(f'创建维护任务: {maintenance_type} ({maintenance_id})')
                    return {'success': True, 'maintenance_id': maintenance_id}
        except Exception as e:
            logger.error(f'创建维护任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def execute_maintenance(self, maintenance_id: str, technician_id: int,
                            technician_name: str, action: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT device_id, maintenance_type FROM device_maintenance WHERE maintenance_id = ?', (maintenance_id,))
                    task = cursor.fetchone()
                    if not task:
                        return {'success': False, 'error': '维护任务不存在'}
                    device_id, mtype = task
                    cursor.execute('UPDATE device_maintenance SET status = ? WHERE maintenance_id = ?', ('in_progress', maintenance_id))
                    cursor.execute('''
                        INSERT INTO maintenance_records (
                            maintenance_id, device_id, action, result,
                            technician_id, technician_name, start_time,
                            end_time, notes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (maintenance_id, device_id, action,
                          kwargs.get('result', 'in_progress'),
                          technician_id, technician_name, now,
                          kwargs.get('end_time'), kwargs.get('notes')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'执行维护任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_maintenance(self, maintenance_id: str, result: str,
                             **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE device_maintenance SET status = ?, updated_at = ? WHERE maintenance_id = ?',
                                 ('completed', now, maintenance_id))
                    cursor.execute('UPDATE maintenance_records SET result = ?, end_time = ?, notes = ? WHERE maintenance_id = ?',
                                 (result, now, kwargs.get('notes'), maintenance_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'完成维护任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_maintenance_history(self, device_id: str = None, limit: int = 50) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM maintenance_records WHERE 1=1'
                params = []
                if device_id:
                    query += ' AND device_id = ?'
                    params.append(device_id)
                query += ' ORDER BY start_time DESC LIMIT ?'
                params.append(limit)
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records}
        except Exception as e:
            logger.error(f'获取维护历史失败: {e}')
            return {'success': False, 'error': str(e)}

    def schedule_preventive_maintenance(self, device_type: str = None,
                                       education_type: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            scheduled_date = (datetime.now() + timedelta(days=30)).isoformat()[:10]
            count = 0
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    query = 'SELECT device_id FROM smart_devices WHERE 1=1'
                    params = []
                    if device_type:
                        query += ' AND device_type = ?'
                        params.append(device_type)
                    if education_type:
                        query += ' AND education_type = ?'
                        params.append(education_type)
                    cursor.execute(query, params)
                    devices = cursor.fetchall()
                    for device in devices:
                        device_id = device[0]
                        maintenance_id = f"mnt_{uuid.uuid4().hex[:12]}"
                        cursor.execute('''
                            INSERT INTO device_maintenance (
                                maintenance_id, device_id, maintenance_type,
                                scheduled_date, priority, status, description
                            ) VALUES (?, ?, 'preventive', ?, 'low', 'pending', '定期预防性维护')
                        ''', (maintenance_id, device_id, scheduled_date))
                        count += 1
                    conn.commit()
            logger.info(f'已计划 {count} 个预防性维护任务')
            return {'success': True, 'scheduled_count': count}
        except Exception as e:
            logger.error(f'计划预防性维护失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 数据采集 ==========

    def create_data_collector(self, collector_name: str, data_source: str,
                              **kwargs) -> Dict[str, Any]:
        try:
            collector_id = f"col_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO data_collectors (
                            collector_id, collector_name, data_source,
                            collection_type, interval, education_type,
                            is_active, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
                    ''', (collector_id, collector_name, data_source,
                          kwargs.get('collection_type', 'periodic'),
                          kwargs.get('interval', 60),
                          kwargs.get('education_type'), now, now))
                    conn.commit()
                    logger.info(f'创建数据采集器: {collector_name} ({collector_id})')
                    return {'success': True, 'collector_id': collector_id}
        except Exception as e:
            logger.error(f'创建数据采集器失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_collection_rule(self, collector_id: str, rule_name: str,
                            condition: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO collection_rules (
                            collector_id, rule_name, filter_condition,
                            aggregation_type, retention_days, enabled
                        ) VALUES (?, ?, ?, ?, ?, 1)
                    ''', (collector_id, rule_name, condition,
                          kwargs.get('aggregation_type'),
                          kwargs.get('retention_days', 30)))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加采集规则失败: {e}')
            return {'success': False, 'error': str(e)}

    def execute_data_collection(self, collector_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT data_source, collection_type, interval, education_type FROM data_collectors WHERE collector_id = ? AND is_active = 1', (collector_id,))
                    collector = cursor.fetchone()
                    if not collector:
                        return {'success': False, 'error': '采集器不存在或未激活'}
                    data_source, coll_type, interval, edu_type = collector
                    cursor.execute('SELECT rule_name, filter_condition FROM collection_rules WHERE collector_id = ? AND enabled = 1', (collector_id,))
                    rules = cursor.fetchall()
                    collected_count = len(rules) if rules else 1
                    logger.info(f'执行数据采集: {collector_id}, 来源: {data_source}, 规则数: {collected_count}')
            return {'success': True, 'collected_count': collected_count}
        except Exception as e:
            logger.error(f'执行数据采集失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_collection_rules(self, collector_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM collection_rules WHERE collector_id = ?', (collector_id,))
                rules = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'rules': rules}
        except Exception as e:
            logger.error(f'获取采集规则失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 硬件集成 ==========

    def create_integration(self, integration_name: str, **kwargs) -> Dict[str, Any]:
        try:
            integration_id = f"int_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO hardware_integrations (
                            integration_id, integration_name, integration_level,
                            provider, api_endpoint, education_type, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'configured', ?, ?)
                    ''', (integration_id, integration_name,
                          kwargs.get('integration_level', 'basic'),
                          kwargs.get('provider'), kwargs.get('api_endpoint'),
                          kwargs.get('education_type'), now, now))
                    if kwargs.get('config'):
                        for key, value in kwargs['config'].items():
                            cursor.execute('INSERT INTO integration_config (integration_id, config_key, config_value) VALUES (?, ?, ?)',
                                         (integration_id, key, str(value)))
                    conn.commit()
                    logger.info(f'创建硬件集成: {integration_name} ({integration_id})')
                    return {'success': True, 'integration_id': integration_id}
        except Exception as e:
            logger.error(f'创建硬件集成失败: {e}')
            return {'success': False, 'error': str(e)}

    def configure_integration(self, integration_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    for key, value in config.items():
                        cursor.execute('INSERT OR REPLACE INTO integration_config (integration_id, config_key, config_value) VALUES (?, ?, ?)',
                                     (integration_id, key, str(value)))
                    cursor.execute('UPDATE hardware_integrations SET updated_at = ? WHERE integration_id = ?', (now, integration_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'配置硬件集成失败: {e}')
            return {'success': False, 'error': str(e)}

    def sync_integration_data(self, integration_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT integration_level, education_type FROM hardware_integrations WHERE integration_id = ?', (integration_id,))
                    integration = cursor.fetchone()
                    if not integration:
                        return {'success': False, 'error': '集成不存在'}
                    level, edu_type = integration
                    logger.info(f'同步集成数据: {integration_id}, 级别: {level}, 教育类型: {edu_type}')
            return {'success': True, 'synced_at': now}
        except Exception as e:
            logger.error(f'同步集成数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_integration_status(self, integration_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM hardware_integrations WHERE integration_id = ?', (integration_id,))
                integration = cursor.fetchone()
                if not integration:
                    return {'success': False, 'error': '集成不存在'}
                result = dict(integration)
                cursor.execute('SELECT config_key, config_value FROM integration_config WHERE integration_id = ?', (integration_id,))
                configs = cursor.fetchall()
                result['config'] = {c['config_key']: c['config_value'] for c in configs}
                return {'success': True, 'integration': result}
        except Exception as e:
            logger.error(f'获取集成状态失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 设备预警 ==========

    def create_alert_rule(self, rule_name: str, alert_type: str,
                          condition: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO alert_rules (
                            rule_name, device_type, alert_type, condition,
                            severity, notification_enabled, auto_resolve,
                            education_type, enabled, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    ''', (rule_name, kwargs.get('device_type'), alert_type, condition,
                          kwargs.get('severity', 'warning'),
                          kwargs.get('notification_enabled', 1),
                          kwargs.get('auto_resolve', 0),
                          kwargs.get('education_type'), now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'创建预警规则失败: {e}')
            return {'success': False, 'error': str(e)}

    def trigger_alert(self, device_id: str, alert_type: str, message: str,
                      **kwargs) -> Dict[str, Any]:
        try:
            alert_id = f"alt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO device_alerts (
                            alert_id, device_id, alert_type, severity,
                            message, status, triggered_at
                        ) VALUES (?, ?, ?, ?, ?, 'active', ?)
                    ''', (alert_id, device_id, alert_type,
                          kwargs.get('severity', 'warning'), message, now))
                    conn.commit()
                    logger.warning(f'触发设备预警: {alert_type} - {message}')
                    return {'success': True, 'alert_id': alert_id}
        except Exception as e:
            logger.error(f'触发预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def resolve_alert(self, alert_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE device_alerts SET status = ?, resolved_at = ? WHERE alert_id = ? AND status = ?',
                                 ('resolved', now, alert_id, 'active'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '预警不存在或已处理'}
        except Exception as e:
            logger.error(f'处理预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_device_alerts(self, device_id: str = None, status: str = 'active',
                          limit: int = 50) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM device_alerts WHERE 1=1'
                params = []
                if device_id:
                    query += ' AND device_id = ?'
                    params.append(device_id)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                query += ' ORDER BY triggered_at DESC LIMIT ?'
                params.append(limit)
                cursor.execute(query, params)
                alerts = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'alerts': alerts}
        except Exception as e:
            logger.error(f'获取设备预警失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 更新管理 ==========

    def create_device_update(self, device_type: str, firmware_version: str,
                             **kwargs) -> Dict[str, Any]:
        try:
            update_id = f"upd_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO device_updates (
                            update_id, device_type, firmware_version,
                            previous_version, release_date, update_size,
                            changelog, is_mandatory, status, education_type
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'available', ?)
                    ''', (update_id, device_type, firmware_version,
                          kwargs.get('previous_version'), now[:10],
                          kwargs.get('update_size'), kwargs.get('changelog'),
                          kwargs.get('is_mandatory', 0),
                          kwargs.get('education_type')))
                    conn.commit()
                    logger.info(f'创建设备更新: {device_type} v{firmware_version} ({update_id})')
                    return {'success': True, 'update_id': update_id}
        except Exception as e:
            logger.error(f'创建设备更新失败: {e}')
            return {'success': False, 'error': str(e)}

    def apply_update(self, update_id: str, device_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT firmware_version FROM device_updates WHERE update_id = ?', (update_id,))
                    update = cursor.fetchone()
                    if not update:
                        return {'success': False, 'error': '更新不存在'}
                    firmware_version = update[0]
                    cursor.execute('INSERT INTO update_history (update_id, device_id, start_time, result) VALUES (?, ?, ?, ?)',
                                 (update_id, device_id, now, 'in_progress'))
                    cursor.execute('UPDATE smart_devices SET firmware_version = ?, updated_at = ? WHERE device_id = ?',
                                 (firmware_version, now, device_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'应用更新失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_update(self, update_id: str, device_id: str, result: str,
                        **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE update_history SET result = ?, end_time = ?, error_message = ? WHERE update_id = ? AND device_id = ?',
                                 (result, now, kwargs.get('error_message'), update_id, device_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '更新记录不存在'}
        except Exception as e:
            logger.error(f'完成更新失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 ==========

    def get_device_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = 'SELECT status, COUNT(*) as cnt FROM smart_devices WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' GROUP BY status'
                cursor.execute(query, params)
                status_stats = {row[0]: row[1] for row in cursor.fetchall()}
                query = 'SELECT device_type, COUNT(*) as cnt FROM smart_devices WHERE 1=1'
                if education_type:
                    query += ' AND education_type = ?'
                query += ' GROUP BY device_type'
                cursor.execute(query, params)
                type_stats = {row[0]: row[1] for row in cursor.fetchall()}
                query = 'SELECT COUNT(*) FROM smart_devices WHERE 1=1'
                if education_type:
                    query += ' AND education_type = ?'
                cursor.execute(query, params)
                total = cursor.fetchone()[0]
                query = 'SELECT COUNT(*) FROM device_alerts WHERE status = ?'
                if education_type:
                    query += ' AND device_id IN (SELECT device_id FROM smart_devices WHERE education_type = ?)'
                    params_alert = ['active', education_type]
                else:
                    params_alert = ['active']
                cursor.execute(query, params_alert)
                active_alerts = cursor.fetchone()[0]
                return {
                    'success': True,
                    'total_devices': total,
                    'status_distribution': status_stats,
                    'type_distribution': type_stats,
                    'active_alerts': active_alerts,
                    'education_type': education_type
                }
        except Exception as e:
            logger.error(f'获取设备统计失败: {e}')
            return {'success': False, 'error': str(e)}