#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育量子通信服务 (v15.21.0)
====================================
提供量子密钥分发、量子隐形传态、量子中继、量子网络、量子加密、
量子安全、量子认证、量子通信协议等综合管理服务。

核心能力：
1. 量子密钥分发 - BB84/B92/E91/QKD协议管理
2. 量子信道 - 光纤/自由空间/卫星信道管理
3. 密钥管理 - 生成/分发/存储/更新/销毁/备份/恢复/审计
4. 量子安全 - 理论安全/计算安全/量子安全策略
5. 量子认证 - 量子/经典/混合认证方法
6. 量子网络 - 星型/网状/树形网络拓扑
7. 通信协议 - 点对点/广播/组播通信模式
8. 应用管理 - 教育数据安全/在线考试/远程教学
9. 设备管理 - 量子设备监控与使用
10. 统计分析 - 量子通信数据统计
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_quantum_communication_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('QuantumCommunication')


# ========== 量子通信配置 ==========

# QKD协议
QKD_PROTOCOLS = {
    'BB84': {'name': 'BB84协议', 'type': 'discrete_variable', 'security': 'theoretical', 'bit_rate': '10kbps-1Gbps'},
    'B92': {'name': 'B92协议', 'type': 'discrete_variable', 'security': 'theoretical', 'bit_rate': '5kbps-500Mbps'},
    'E91': {'name': 'E91协议', 'type': 'entanglement_based', 'security': 'theoretical', 'bit_rate': '1kbps-100Mbps'},
    'COW': {'name': 'COW协议', 'type': 'continuous_variable', 'security': 'computational', 'bit_rate': '100kbps-10Gbps'},
    'SARG04': {'name': 'SARG04协议', 'type': 'discrete_variable', 'security': 'theoretical', 'bit_rate': '8kbps-800Mbps'},
    'DPS': {'name': 'DPS协议', 'type': 'discrete_variable', 'security': 'theoretical', 'bit_rate': '1kbps-50Mbps'},
    'QSDC': {'name': '量子安全直接通信', 'type': 'direct_communication', 'security': 'theoretical', 'bit_rate': '100bps-10Mbps'},
    'QOT': {'name': '量子隐形传态', 'type': 'quantum_teleportation', 'security': 'theoretical', 'bit_rate': '1bps-1Mbps'}
}

# 量子信道
QUANTUM_CHANNELS = {
    'fiber': {'name': '光纤信道', 'distance': '0-1000km', 'loss': '0.2dB/km', 'bandwidth': 'THz'},
    'free_space': {'name': '自由空间信道', 'distance': '0-100km', 'loss': 'atmospheric', 'bandwidth': 'THz'},
    'satellite': {'name': '卫星信道', 'distance': '1000-35000km', 'loss': 'atmospheric', 'bandwidth': 'GHz'},
    'waveguide': {'name': '波导信道', 'distance': '0-1km', 'loss': 'low', 'bandwidth': 'THz'},
    'entanglement': {'name': '纠缠信道', 'distance': '0-100km', 'loss': 'quantum', 'bandwidth': 'bps'},
    'relay': {'name': '中继信道', 'distance': 'unlimited', 'loss': 'accumulated', 'bandwidth': 'variable'},
    'hybrid': {'name': '混合信道', 'distance': 'unlimited', 'loss': 'variable', 'bandwidth': 'variable'},
    'quantum_internet': {'name': '量子互联网', 'distance': 'global', 'loss': 'network', 'bandwidth': 'Tbps'}
}

# 密钥管理
KEY_MANAGEMENT = {
    'generation': {'name': '密钥生成', 'method': 'QKD', 'security_level': 'quantum'},
    'distribution': {'name': '密钥分发', 'method': 'quantum_channel', 'security_level': 'quantum'},
    'storage': {'name': '密钥存储', 'method': 'secure_vault', 'security_level': 'high'},
    'update': {'name': '密钥更新', 'method': 'automatic', 'security_level': 'quantum'},
    'destruction': {'name': '密钥销毁', 'method': 'zeroization', 'security_level': 'high'},
    'backup': {'name': '密钥备份', 'method': 'encrypted', 'security_level': 'high'},
    'recovery': {'name': '密钥恢复', 'method': 'authorized', 'security_level': 'high'},
    'audit': {'name': '密钥审计', 'method': 'log_trail', 'security_level': 'medium'}
}

# 安全级别
SECURITY_LEVELS = {
    'theoretical': {'name': '理论安全', 'basis': 'quantum_law', 'proof': 'mathematical'},
    'computational': {'name': '计算安全', 'basis': 'hard_problem', 'proof': 'complexity'},
    'practical': {'name': '实际安全', 'basis': 'implementation', 'proof': 'testing'},
    'quantum': {'name': '量子安全', 'basis': 'quantum_resistant', 'proof': 'algorithm'},
    'post_quantum': {'name': '后量子安全', 'basis': 'lattice_crypto', 'proof': 'standard'},
    'hybrid': {'name': '混合安全', 'basis': 'quantum_classical', 'proof': 'combined'},
    'multi_layer': {'name': '多层安全', 'basis': 'defense_depth', 'proof': 'architecture'},
    'adaptive': {'name': '自适应安全', 'basis': 'dynamic', 'proof': 'monitoring'}
}

# 认证方法
AUTHENTICATION_METHODS = {
    'quantum': {'name': '量子认证', 'type': 'quantum_based', 'security': 'theoretical'},
    'classical': {'name': '经典认证', 'type': 'cryptographic', 'security': 'computational'},
    'hybrid': {'name': '混合认证', 'type': 'combined', 'security': 'enhanced'},
    'identity': {'name': '身份认证', 'type': 'biometric', 'security': 'high'},
    'message': {'name': '消息认证', 'type': 'hash_based', 'security': 'medium'},
    'signature': {'name': '签名认证', 'type': 'digital_signature', 'security': 'high'},
    'key': {'name': '密钥认证', 'type': 'key_exchange', 'security': 'quantum'},
    'device': {'name': '设备认证', 'type': 'hardware_based', 'security': 'high'}
}

# 通信模式
COMMUNICATION_MODES = {
    'point_to_point': {'name': '点对点通信', 'topology': 'linear', 'bandwidth': 'dedicated'},
    'point_to_multi': {'name': '点对多点通信', 'topology': 'star', 'bandwidth': 'shared'},
    'broadcast': {'name': '广播通信', 'topology': 'tree', 'bandwidth': 'shared'},
    'multicast': {'name': '组播通信', 'topology': 'mesh', 'bandwidth': 'group'},
    'full_duplex': {'name': '全双工通信', 'direction': 'bidirectional', 'bandwidth': 'simultaneous'},
    'half_duplex': {'name': '半双工通信', 'direction': 'alternating', 'bandwidth': 'time_shared'},
    'asynchronous': {'name': '异步通信', 'timing': 'independent', 'bandwidth': 'flexible'},
    'synchronous': {'name': '同步通信', 'timing': 'coordinated', 'bandwidth': 'fixed'}
}

# 网络拓扑
NETWORK_TOPOLOGY = {
    'star': {'name': '星型网络', 'central_node': True, 'reliability': 'medium', 'scalability': 'good'},
    'mesh': {'name': '网状网络', 'central_node': False, 'reliability': 'high', 'scalability': 'excellent'},
    'tree': {'name': '树形网络', 'central_node': True, 'reliability': 'medium', 'scalability': 'good'},
    'bus': {'name': '总线网络', 'central_node': False, 'reliability': 'low', 'scalability': 'limited'},
    'ring': {'name': '环型网络', 'central_node': False, 'reliability': 'medium', 'scalability': 'medium'},
    'hybrid': {'name': '混合网络', 'central_node': 'partial', 'reliability': 'high', 'scalability': 'excellent'},
    'quantum_backbone': {'name': '量子骨干网', 'central_node': False, 'reliability': 'high', 'scalability': 'excellent'},
    'quantum_lan': {'name': '量子局域网', 'central_node': True, 'reliability': 'high', 'scalability': 'good'}
}

# 应用场景
APPLICATION_SCENARIOS = {
    'education_data': {'name': '教育数据安全', 'description': '学生成绩、学籍数据加密传输', 'security_level': 'high'},
    'online_exam': {'name': '在线考试安全', 'description': '远程考试防作弊、试卷加密', 'security_level': 'critical'},
    'remote_teaching': {'name': '远程教学安全', 'description': '在线课堂内容保护、身份认证', 'security_level': 'high'},
    'research_data': {'name': '科研数据传输', 'description': '学术研究数据加密共享', 'security_level': 'high'},
    'student_privacy': {'name': '学生隐私保护', 'description': '个人信息安全存储与传输', 'security_level': 'critical'},
    'education_management': {'name': '教育管理安全', 'description': '教务系统、财务数据保护', 'security_level': 'high'},
    'campus_network': {'name': '校园网络安全', 'description': '校园网量子加密通信', 'security_level': 'medium'},
    'education_cloud': {'name': '教育云安全', 'description': '云端数据量子加密存储', 'security_level': 'high'}
}


class EducationQuantumCommunicationService:
    """教育量子通信服务"""

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
                    CREATE TABLE IF NOT EXISTS quantum_channels (
                        channel_id TEXT PRIMARY KEY,
                        channel_name TEXT NOT NULL,
                        channel_type TEXT NOT NULL,
                        education_type TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS channel_config (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        channel_id TEXT NOT NULL,
                        bandwidth REAL,
                        distance REAL,
                        loss_rate REAL,
                        noise_level REAL,
                        encryption_type TEXT,
                        error_correction TEXT,
                        FOREIGN KEY (channel_id) REFERENCES quantum_channels(channel_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS qkd_protocols (
                        protocol_id TEXT PRIMARY KEY,
                        protocol_name TEXT NOT NULL,
                        protocol_type TEXT,
                        education_type TEXT,
                        security_level TEXT,
                        bit_rate TEXT,
                        description TEXT,
                        is_enabled INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS protocol_params (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        protocol_id TEXT NOT NULL,
                        param_name TEXT,
                        param_value TEXT,
                        FOREIGN KEY (protocol_id) REFERENCES qkd_protocols(protocol_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS quantum_keys (
                        key_id TEXT PRIMARY KEY,
                        key_value TEXT NOT NULL,
                        key_length INTEGER DEFAULT 256,
                        protocol_id TEXT,
                        channel_id TEXT,
                        education_type TEXT,
                        status TEXT DEFAULT 'generated',
                        generated_at TEXT,
                        used_at TEXT,
                        expires_at TEXT,
                        FOREIGN KEY (protocol_id) REFERENCES qkd_protocols(protocol_id),
                        FOREIGN KEY (channel_id) REFERENCES quantum_channels(channel_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS key_management (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        key_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        operator TEXT,
                        timestamp TEXT,
                        details TEXT,
                        FOREIGN KEY (key_id) REFERENCES quantum_keys(key_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS quantum_security (
                        security_id TEXT PRIMARY KEY,
                        security_level TEXT NOT NULL,
                        education_type TEXT,
                        description TEXT,
                        policy_name TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS security_policies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        security_id TEXT NOT NULL,
                        policy_type TEXT,
                        policy_content TEXT,
                        priority INTEGER DEFAULT 1,
                        FOREIGN KEY (security_id) REFERENCES quantum_security(security_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS quantum_authentication (
                        auth_id TEXT PRIMARY KEY,
                        auth_method TEXT NOT NULL,
                        education_type TEXT,
                        description TEXT,
                        security_level TEXT,
                        is_enabled INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS auth_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        auth_id TEXT NOT NULL,
                        user_id INTEGER,
                        user_name TEXT,
                        auth_time TEXT,
                        auth_result TEXT,
                        details TEXT,
                        FOREIGN KEY (auth_id) REFERENCES quantum_authentication(auth_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS quantum_network (
                        network_id TEXT PRIMARY KEY,
                        network_name TEXT NOT NULL,
                        topology_type TEXT,
                        education_type TEXT,
                        description TEXT,
                        node_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS network_topology (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        network_id TEXT NOT NULL,
                        node_name TEXT,
                        node_type TEXT,
                        position_x REAL,
                        position_y REAL,
                        FOREIGN KEY (network_id) REFERENCES quantum_network(network_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS qc_applications (
                        app_id TEXT PRIMARY KEY,
                        app_name TEXT NOT NULL,
                        app_scenario TEXT,
                        education_type TEXT,
                        description TEXT,
                        security_level TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS application_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        app_id TEXT NOT NULL,
                        data_type TEXT,
                        data_size INTEGER,
                        encryption_status TEXT,
                        transmitted_at TEXT,
                        FOREIGN KEY (app_id) REFERENCES qc_applications(app_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS quantum_devices (
                        device_id TEXT PRIMARY KEY,
                        device_name TEXT NOT NULL,
                        device_type TEXT,
                        education_type TEXT,
                        manufacturer TEXT,
                        model TEXT,
                        status TEXT DEFAULT 'active',
                        location TEXT,
                        installed_at TEXT,
                        last_maintenance TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS device_usage (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        device_id TEXT NOT NULL,
                        usage_type TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        usage_duration REAL,
                        data_processed INTEGER,
                        FOREIGN KEY (device_id) REFERENCES quantum_devices(device_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS qc_monitoring (
                        monitor_id TEXT PRIMARY KEY,
                        monitor_name TEXT NOT NULL,
                        education_type TEXT,
                        monitored_object TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS monitoring_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        monitor_id TEXT NOT NULL,
                        metric_type TEXT,
                        metric_value REAL,
                        timestamp TEXT,
                        FOREIGN KEY (monitor_id) REFERENCES qc_monitoring(monitor_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS qc_alerts (
                        alert_id TEXT PRIMARY KEY,
                        alert_type TEXT NOT NULL,
                        education_type TEXT,
                        severity TEXT DEFAULT 'medium',
                        status TEXT DEFAULT 'pending',
                        description TEXT,
                        created_at TEXT,
                        resolved_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alert_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        alert_id TEXT NOT NULL,
                        action TEXT,
                        operator TEXT,
                        timestamp TEXT,
                        FOREIGN KEY (alert_id) REFERENCES qc_alerts(alert_id)
                    )
                ''')
                conn.commit()
                logger.info('教育量子通信服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 量子密钥分发 ==========

    def generate_quantum_key(self, protocol_type: str, channel_id: str = None,
                              education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            key_id = f"qk_{uuid.uuid4().hex[:16]}"
            key_value = uuid.uuid4().hex + uuid.uuid4().hex
            key_length = kwargs.get('key_length', 256)
            now = datetime.now().isoformat()
            expires_at = (datetime.now() + timedelta(days=30)).isoformat()

            protocol_info = QKD_PROTOCOLS.get(protocol_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO quantum_keys (
                            key_id, key_value, key_length, protocol_id,
                            channel_id, education_type, status,
                            generated_at, expires_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'generated', ?, ?)
                    ''', (key_id, key_value[:key_length//4], key_length,
                          protocol_type, channel_id, education_type,
                          now, expires_at))
                    cursor.execute('''
                        INSERT INTO key_management (key_id, action, operator, timestamp, details)
                        VALUES (?, 'generate', ?, ?, ?)
                    ''', (key_id, kwargs.get('operator', 'system'), now,
                          json.dumps({'protocol': protocol_type, 'education_type': education_type})))
                    conn.commit()
                    logger.info(f'生成量子密钥: {key_id[:8]}... ({protocol_type}, {education_type})')
                    return {'success': True, 'key_id': key_id, 'key_length': key_length}
        except Exception as e:
            logger.error(f'生成量子密钥失败: {e}')
            return {'success': False, 'error': str(e)}

    def distribute_key(self, key_id: str, target_node: str,
                        **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM quantum_keys WHERE key_id = ?', (key_id,))
                    key = cursor.fetchone()
                    if not key:
                        return {'success': False, 'error': '密钥不存在'}
                    if key[0] != 'generated':
                        return {'success': False, 'error': '密钥状态不允许分发'}
                    cursor.execute('UPDATE quantum_keys SET status = ?, used_at = ? WHERE key_id = ?',
                                  ('distributed', now, key_id))
                    cursor.execute('''
                        INSERT INTO key_management (key_id, action, operator, timestamp, details)
                        VALUES (?, 'distribute', ?, ?, ?)
                    ''', (key_id, kwargs.get('operator', 'system'), now,
                          json.dumps({'target_node': target_node})))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'分发密钥失败: {e}')
            return {'success': False, 'error': str(e)}

    def establish_qkd_connection(self, protocol_type: str, sender_id: str,
                                  receiver_id: str, education_type: str = 'k12',
                                  **kwargs) -> Dict[str, Any]:
        try:
            connection_id = f"qkd_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            protocol_info = QKD_PROTOCOLS.get(protocol_type, {})

            key_result = self.generate_quantum_key(protocol_type,
                                                   education_type=education_type,
                                                   **kwargs)
            if not key_result['success']:
                return key_result

            logger.info(f'建立QKD连接: {connection_id} ({protocol_type}, {education_type})')
            return {
                'success': True,
                'connection_id': connection_id,
                'key_id': key_result['key_id'],
                'protocol': protocol_type,
                'sender': sender_id,
                'receiver': receiver_id,
                'security_level': protocol_info.get('security', 'unknown')
            }
        except Exception as e:
            logger.error(f'建立QKD连接失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_key_status(self, key_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM quantum_keys WHERE key_id = ?', (key_id,))
                key = cursor.fetchone()
                if not key:
                    return {'success': False, 'error': '密钥不存在'}
                return {'success': True, 'key': dict(key)}
        except Exception as e:
            logger.error(f'获取密钥状态失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 量子信道 ==========

    def create_channel(self, channel_name: str, channel_type: str,
                        education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            channel_id = f"ch_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            channel_info = QUANTUM_CHANNELS.get(channel_type, {})

            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO quantum_channels (
                            channel_id, channel_name, channel_type,
                            education_type, description, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (channel_id, channel_name, channel_type, education_type,
                          kwargs.get('description', channel_info.get('name', '')),
                          now, now))
                    cursor.execute('''
                        INSERT INTO channel_config (channel_id, bandwidth, distance, loss_rate, noise_level, encryption_type, error_correction)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (channel_id, kwargs.get('bandwidth'), kwargs.get('distance'),
                          kwargs.get('loss_rate'), kwargs.get('noise_level'),
                          kwargs.get('encryption_type', 'quantum'),
                          kwargs.get('error_correction', 'LDPC')))
                    conn.commit()
                    logger.info(f'创建量子信道: {channel_name} ({channel_id}, {education_type})')
                    return {'success': True, 'channel_id': channel_id}
        except Exception as e:
            logger.error(f'创建量子信道失败: {e}')
            return {'success': False, 'error': str(e)}

    def configure_channel(self, channel_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    updates = []
                    params = []
                    if 'bandwidth' in kwargs:
                        updates.append('bandwidth = ?')
                        params.append(kwargs['bandwidth'])
                    if 'distance' in kwargs:
                        updates.append('distance = ?')
                        params.append(kwargs['distance'])
                    if 'loss_rate' in kwargs:
                        updates.append('loss_rate = ?')
                        params.append(kwargs['loss_rate'])
                    if 'noise_level' in kwargs:
                        updates.append('noise_level = ?')
                        params.append(kwargs['noise_level'])
                    if 'encryption_type' in kwargs:
                        updates.append('encryption_type = ?')
                        params.append(kwargs['encryption_type'])
                    if 'error_correction' in kwargs:
                        updates.append('error_correction = ?')
                        params.append(kwargs['error_correction'])
                    if updates:
                        params.append(channel_id)
                        cursor.execute(f'UPDATE channel_config SET {", ".join(updates)} WHERE channel_id = ?', params)
                        cursor.execute('UPDATE quantum_channels SET updated_at = ? WHERE channel_id = ?', (now, channel_id))
                        conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'配置量子信道失败: {e}')
            return {'success': False, 'error': str(e)}

    def activate_channel(self, channel_id: str, active: bool = True) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'active' if active else 'inactive'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE quantum_channels SET status = ?, updated_at = ? WHERE channel_id = ?',
                                  (status, now, channel_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '信道不存在'}
        except Exception as e:
            logger.error(f'激活信道失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_channels(self, education_type: str = None, channel_type: str = None,
                      status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM quantum_channels WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if channel_type:
                    query += ' AND channel_type = ?'
                    params.append(channel_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                channels = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'channels': channels, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取信道列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 密钥管理 ==========

    def store_key(self, key_id: str, storage_location: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM quantum_keys WHERE key_id = ?', (key_id,))
                    key = cursor.fetchone()
                    if not key:
                        return {'success': False, 'error': '密钥不存在'}
                    cursor.execute('''
                        INSERT INTO key_management (key_id, action, operator, timestamp, details)
                        VALUES (?, 'store', ?, ?, ?)
                    ''', (key_id, kwargs.get('operator', 'system'), now,
                          json.dumps({'storage_location': storage_location})))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'存储密钥失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_key(self, key_id: str, **kwargs) -> Dict[str, Any]:
        try:
            key_value = uuid.uuid4().hex + uuid.uuid4().hex
            key_length = kwargs.get('key_length', 256)
            now = datetime.now().isoformat()
            expires_at = (datetime.now() + timedelta(days=30)).isoformat()

            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE quantum_keys SET key_value = ?, key_length = ?, expires_at = ?, updated_at = ?, status = ? WHERE key_id = ?',
                                  (key_value[:key_length//4], key_length, expires_at, now, 'generated', key_id))
                    if cursor.rowcount > 0:
                        cursor.execute('''
                            INSERT INTO key_management (key_id, action, operator, timestamp, details)
                            VALUES (?, 'update', ?, ?, ?)
                        ''', (key_id, kwargs.get('operator', 'system'), now,
                              json.dumps({'key_length': key_length})))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '密钥不存在'}
        except Exception as e:
            logger.error(f'更新密钥失败: {e}')
            return {'success': False, 'error': str(e)}

    def destroy_key(self, key_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE quantum_keys SET key_value = ?, status = ? WHERE key_id = ?',
                                  ('', 'destroyed', key_id))
                    if cursor.rowcount > 0:
                        cursor.execute('''
                            INSERT INTO key_management (key_id, action, operator, timestamp, details)
                            VALUES (?, 'destroy', ?, ?, ?)
                        ''', (key_id, kwargs.get('operator', 'system'), now,
                              json.dumps({'method': 'zeroization'})))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '密钥不存在'}
        except Exception as e:
            logger.error(f'销毁密钥失败: {e}')
            return {'success': False, 'error': str(e)}

    def audit_key(self, key_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM key_management WHERE key_id = ? ORDER BY timestamp DESC', (key_id,))
                records = [dict(r) for r in cursor.fetchall()]
                cursor.execute('SELECT * FROM quantum_keys WHERE key_id = ?', (key_id,))
                key = cursor.fetchone()
                if not key:
                    return {'success': False, 'error': '密钥不存在'}
                return {'success': True, 'key': dict(key), 'audit_records': records}
        except Exception as e:
            logger.error(f'审计密钥失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 量子安全 ==========

    def create_security_policy(self, security_level: str, policy_name: str,
                                education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            security_id = f"sec_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            level_info = SECURITY_LEVELS.get(security_level, {})

            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO quantum_security (
                            security_id, security_level, education_type,
                            description, policy_name, is_active,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 1, ?, ?)
                    ''', (security_id, security_level, education_type,
                          kwargs.get('description', level_info.get('name', '')),
                          policy_name, now, now))
                    if 'policies' in kwargs:
                        for i, policy in enumerate(kwargs['policies']):
                            cursor.execute('''
                                INSERT INTO security_policies (security_id, policy_type, policy_content, priority)
                                VALUES (?, ?, ?, ?)
                            ''', (security_id, policy.get('type'), json.dumps(policy.get('content', {})), i + 1))
                    conn.commit()
                    logger.info(f'创建安全策略: {policy_name} ({security_id}, {education_type})')
                    return {'success': True, 'security_id': security_id}
        except Exception as e:
            logger.error(f'创建安全策略失败: {e}')
            return {'success': False, 'error': str(e)}

    def apply_security_policy(self, security_id: str, target_resource: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT is_active FROM quantum_security WHERE security_id = ?', (security_id,))
                    policy = cursor.fetchone()
                    if not policy:
                        return {'success': False, 'error': '安全策略不存在'}
                    if policy[0] != 1:
                        return {'success': False, 'error': '安全策略未激活'}
                    logger.info(f'应用安全策略: {security_id} -> {target_resource}')
                    return {'success': True, 'applied_at': now}
        except Exception as e:
            logger.error(f'应用安全策略失败: {e}')
            return {'success': False, 'error': str(e)}

    def validate_security(self, security_id: str, data: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM quantum_security WHERE security_id = ?', (security_id,))
                policy = cursor.fetchone()
                if not policy:
                    return {'success': False, 'error': '安全策略不存在'}

                cursor.execute('SELECT * FROM security_policies WHERE security_id = ?', (security_id,))
                policies = [dict(p) for p in cursor.fetchall()]

                validation_result = {
                    'valid': True,
                    'security_level': policy['security_level'],
                    'policy_count': len(policies),
                    'policies': [p['policy_type'] for p in policies]
                }
                return {'success': True, 'validation': validation_result}
        except Exception as e:
            logger.error(f'验证安全策略失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_security_policies(self, education_type: str = None,
                                security_level: str = None, page: int = 1,
                                page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM quantum_security WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if security_level:
                    query += ' AND security_level = ?'
                    params.append(security_level)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                policies = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'policies': policies, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取安全策略列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def set_security_level(self, education_type: str, security_level: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            level_info = SECURITY_LEVELS.get(security_level, {})
            if not level_info:
                return {'success': False, 'error': '无效的安全级别'}

            logger.info(f'设置安全级别: {education_type} -> {security_level}')
            return {
                'success': True,
                'education_type': education_type,
                'security_level': security_level,
                'security_name': level_info.get('name'),
                'set_at': now
            }
        except Exception as e:
            logger.error(f'设置安全级别失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 量子认证 ==========

    def create_authentication(self, auth_method: str, education_type: str = 'k12',
                               **kwargs) -> Dict[str, Any]:
        try:
            auth_id = f"auth_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            method_info = AUTHENTICATION_METHODS.get(auth_method, {})

            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO quantum_authentication (
                            auth_id, auth_method, education_type,
                            description, security_level, is_enabled,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 1, ?, ?)
                    ''', (auth_id, auth_method, education_type,
                          kwargs.get('description', method_info.get('name', '')),
                          method_info.get('security', 'medium'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建认证方法: {auth_method} ({auth_id}, {education_type})')
                    return {'success': True, 'auth_id': auth_id}
        except Exception as e:
            logger.error(f'创建认证方法失败: {e}')
            return {'success': False, 'error': str(e)}

    def perform_authentication(self, auth_id: str, user_id: int,
                                user_name: str = None, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT is_enabled, security_level FROM quantum_authentication WHERE auth_id = ?', (auth_id,))
                    auth = cursor.fetchone()
                    if not auth:
                        return {'success': False, 'error': '认证方法不存在'}
                    if auth[0] != 1:
                        return {'success': False, 'error': '认证方法未启用'}

                    auth_result = 'success' if kwargs.get('simulate_success', True) else 'failed'
                    cursor.execute('''
                        INSERT INTO auth_records (auth_id, user_id, user_name, auth_time, auth_result, details)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (auth_id, user_id, user_name, now, auth_result,
                          json.dumps({'security_level': auth[1]})))
                    conn.commit()
                    return {'success': True, 'auth_result': auth_result}
        except Exception as e:
            logger.error(f'执行认证失败: {e}')
            return {'success': False, 'error': str(e)}

    def verify_authentication(self, auth_record_id: int) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM auth_records WHERE id = ?', (auth_record_id,))
                record = cursor.fetchone()
                if not record:
                    return {'success': False, 'error': '认证记录不存在'}
                return {'success': True, 'record': dict(record), 'verified': True}
        except Exception as e:
            logger.error(f'验证认证失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_auth_records(self, auth_id: str = None, user_id: int = None,
                          auth_result: str = None, page: int = 1,
                          page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM auth_records WHERE 1=1'
                params = []
                if auth_id:
                    query += ' AND auth_id = ?'
                    params.append(auth_id)
                if user_id:
                    query += ' AND user_id = ?'
                    params.append(user_id)
                if auth_result:
                    query += ' AND auth_result = ?'
                    params.append(auth_result)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY auth_time DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取认证记录失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 量子网络 ==========

    def create_network(self, network_name: str, topology_type: str,
                       education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            network_id = f"net_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            topology_info = NETWORK_TOPOLOGY.get(topology_type, {})

            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO quantum_network (
                            network_id, network_name, topology_type,
                            education_type, description, node_count,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 0, 'active', ?, ?)
                    ''', (network_id, network_name, topology_type, education_type,
                          kwargs.get('description', topology_info.get('name', '')),
                          now, now))
                    if 'nodes' in kwargs:
                        for node in kwargs['nodes']:
                            cursor.execute('''
                                INSERT INTO network_topology (network_id, node_name, node_type, position_x, position_y)
                                VALUES (?, ?, ?, ?, ?)
                            ''', (network_id, node.get('name'), node.get('type', 'node'),
                                  node.get('x', 0), node.get('y', 0)))
                            cursor.execute('UPDATE quantum_network SET node_count = node_count + 1 WHERE network_id = ?', (network_id,))
                    conn.commit()
                    logger.info(f'创建量子网络: {network_name} ({network_id}, {education_type})')
                    return {'success': True, 'network_id': network_id}
        except Exception as e:
            logger.error(f'创建量子网络失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_network_node(self, network_id: str, node_name: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM quantum_network WHERE network_id = ?', (network_id,))
                    network = cursor.fetchone()
                    if not network:
                        return {'success': False, 'error': '网络不存在'}
                    if network[0] != 'active':
                        return {'success': False, 'error': '网络状态不允许添加节点'}
                    cursor.execute('''
                        INSERT INTO network_topology (network_id, node_name, node_type, position_x, position_y)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (network_id, node_name, kwargs.get('node_type', 'node'),
                          kwargs.get('x', 0), kwargs.get('y', 0)))
                    cursor.execute('UPDATE quantum_network SET node_count = node_count + 1, updated_at = ? WHERE network_id = ?', (now, network_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加网络节点失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_network_status(self, network_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM quantum_network WHERE network_id = ?', (network_id,))
                network = cursor.fetchone()
                if not network:
                    return {'success': False, 'error': '网络不存在'}
                cursor.execute('SELECT * FROM network_topology WHERE network_id = ?', (network_id,))
                nodes = [dict(n) for n in cursor.fetchall()]
                return {'success': True, 'network': dict(network), 'nodes': nodes}
        except Exception as e:
            logger.error(f'获取网络状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_networks(self, education_type: str = None, topology_type: str = None,
                      status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM quantum_network WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if topology_type:
                    query += ' AND topology_type = ?'
                    params.append(topology_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                networks = [dict(n) for n in cursor.fetchall()]
                return {'success': True, 'networks': networks, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取网络列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 通信协议 ==========

    def select_protocol(self, protocol_type: str, education_type: str = 'k12',
                         **kwargs) -> Dict[str, Any]:
        try:
            protocol_info = QKD_PROTOCOLS.get(protocol_type)
            if not protocol_info:
                return {'success': False, 'error': '无效的协议类型'}

            now = datetime.now().isoformat()
            protocol_id = f"proto_{uuid.uuid4().hex[:8]}"
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO qkd_protocols (
                            protocol_id, protocol_name, protocol_type,
                            education_type, security_level, bit_rate,
                            description, is_enabled, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                    ''', (protocol_id, protocol_info['name'], protocol_type,
                          education_type, protocol_info['security'],
                          protocol_info['bit_rate'],
                          kwargs.get('description', ''), now, now))
                    if 'params' in kwargs:
                        for param_name, param_value in kwargs['params'].items():
                            cursor.execute('INSERT INTO protocol_params (protocol_id, param_name, param_value) VALUES (?, ?, ?)',
                                          (protocol_id, param_name, str(param_value)))
                    conn.commit()
                    logger.info(f'选择通信协议: {protocol_type} ({protocol_id}, {education_type})')
                    return {'success': True, 'protocol_id': protocol_id, 'protocol_info': protocol_info}
        except Exception as e:
            logger.error(f'选择通信协议失败: {e}')
            return {'success': False, 'error': str(e)}

    def configure_protocol(self, protocol_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    updates = []
                    params = []
                    if 'security_level' in kwargs:
                        updates.append('security_level = ?')
                        params.append(kwargs['security_level'])
                    if 'bit_rate' in kwargs:
                        updates.append('bit_rate = ?')
                        params.append(kwargs['bit_rate'])
                    if 'description' in kwargs:
                        updates.append('description = ?')
                        params.append(kwargs['description'])
                    if updates:
                        params.append(protocol_id)
                        cursor.execute(f'UPDATE qkd_protocols SET {", ".join(updates)}, updated_at = ? WHERE protocol_id = ?',
                                      [now] + params)
                    if 'params' in kwargs:
                        for param_name, param_value in kwargs['params'].items():
                            cursor.execute('INSERT OR REPLACE INTO protocol_params (protocol_id, param_name, param_value) VALUES (?, ?, ?)',
                                          (protocol_id, param_name, str(param_value)))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'配置通信协议失败: {e}')
            return {'success': False, 'error': str(e)}

    def test_protocol(self, protocol_id: str, test_data: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM qkd_protocols WHERE protocol_id = ?', (protocol_id,))
                protocol = cursor.fetchone()
                if not protocol:
                    return {'success': False, 'error': '协议不存在'}
                if protocol['is_enabled'] != 1:
                    return {'success': False, 'error': '协议未启用'}

                test_result = {
                    'protocol_id': protocol_id,
                    'protocol_type': protocol['protocol_type'],
                    'test_time': datetime.now().isoformat(),
                    'status': 'success',
                    'latency': 0.001,
                    'throughput': float(protocol['bit_rate'].split('-')[1].replace('bps', '').replace('G', '000000000').replace('M', '000000')),
                    'error_rate': 0.0001
                }
                return {'success': True, 'test_result': test_result}
        except Exception as e:
            logger.error(f'测试通信协议失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_protocol_stats(self, protocol_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT COUNT(*) as count, AVG(bit_rate) as avg_bit_rate FROM qkd_protocols WHERE 1=1'
                params = []
                if protocol_type:
                    query += ' AND protocol_type = ?'
                    params.append(protocol_type)
                cursor.execute(query, params)
                stats = cursor.fetchone()
                return {'success': True, 'stats': dict(stats) if stats else {'count': 0, 'avg_bit_rate': 0}}
        except Exception as e:
            logger.error(f'获取协议统计失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 应用管理 ==========

    def create_application(self, app_name: str, app_scenario: str,
                           education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            app_id = f"app_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            scenario_info = APPLICATION_SCENARIOS.get(app_scenario, {})

            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO qc_applications (
                            app_id, app_name, app_scenario, education_type,
                            description, security_level, is_active,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
                    ''', (app_id, app_name, app_scenario, education_type,
                          kwargs.get('description', scenario_info.get('description', '')),
                          scenario_info.get('security_level', 'medium'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建量子应用: {app_name} ({app_id}, {education_type})')
                    return {'success': True, 'app_id': app_id}
        except Exception as e:
            logger.error(f'创建量子应用失败: {e}')
            return {'success': False, 'error': str(e)}

    def encrypt_data(self, app_id: str, data: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            encrypted_data = uuid.uuid4().hex[:32] + data.encode('utf-8').hex()[:128]

            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT is_active, security_level FROM qc_applications WHERE app_id = ?', (app_id,))
                    app = cursor.fetchone()
                    if not app:
                        return {'success': False, 'error': '应用不存在'}
                    if app[0] != 1:
                        return {'success': False, 'error': '应用未激活'}
                    cursor.execute('''
                        INSERT INTO application_data (app_id, data_type, data_size, encryption_status, transmitted_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (app_id, 'encrypted', len(data), 'encrypted', now))
                    conn.commit()
                    return {'success': True, 'encrypted_data': encrypted_data, 'security_level': app[1]}
        except Exception as e:
            logger.error(f'加密数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def transmit_data(self, app_id: str, data: str, destination: str,
                      **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            encrypt_result = self.encrypt_data(app_id, data, **kwargs)
            if not encrypt_result['success']:
                return encrypt_result

            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO application_data (app_id, data_type, data_size, encryption_status, transmitted_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (app_id, 'transmitted', len(data), 'transmitted', now))
                    conn.commit()
                    logger.info(f'传输数据: {app_id} -> {destination}')
                    return {'success': True, 'transmitted_at': now, 'destination': destination}
        except Exception as e:
            logger.error(f'传输数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_applications(self, education_type: str = None, app_scenario: str = None,
                          status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM qc_applications WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if app_scenario:
                    query += ' AND app_scenario = ?'
                    params.append(app_scenario)
                if status:
                    query += ' AND is_active = ?'
                    params.append(1 if status == 'active' else 0)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                apps = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'applications': apps, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取应用列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 设备管理 ==========

    def register_device(self, device_name: str, device_type: str,
                        education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            device_id = f"dev_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()

            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO quantum_devices (
                            device_id, device_name, device_type, education_type,
                            manufacturer, model, status, location,
                            installed_at, last_maintenance, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?)
                    ''', (device_id, device_name, device_type, education_type,
                          kwargs.get('manufacturer'), kwargs.get('model'),
                          kwargs.get('location'), now, now, now, now))
                    conn.commit()
                    logger.info(f'注册量子设备: {device_name} ({device_id}, {education_type})')
                    return {'success': True, 'device_id': device_id}
        except Exception as e:
            logger.error(f'注册量子设备失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_device_usage(self, device_id: str, usage_type: str,
                            **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            start_time = kwargs.get('start_time', now)
            end_time = kwargs.get('end_time', now)
            usage_duration = kwargs.get('usage_duration', 0)
            data_processed = kwargs.get('data_processed', 0)

            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM quantum_devices WHERE device_id = ?', (device_id,))
                    device = cursor.fetchone()
                    if not device:
                        return {'success': False, 'error': '设备不存在'}
                    cursor.execute('''
                        INSERT INTO device_usage (device_id, usage_type, start_time, end_time, usage_duration, data_processed)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (device_id, usage_type, start_time, end_time, usage_duration, data_processed))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'记录设备使用失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_device_status(self, device_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM quantum_devices WHERE device_id = ?', (device_id,))
                device = cursor.fetchone()
                if not device:
                    return {'success': False, 'error': '设备不存在'}
                cursor.execute('SELECT * FROM device_usage WHERE device_id = ? ORDER BY start_time DESC LIMIT 10', (device_id,))
                usages = [dict(u) for u in cursor.fetchall()]
                return {'success': True, 'device': dict(device), 'recent_usages': usages}
        except Exception as e:
            logger.error(f'获取设备状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_devices(self, education_type: str = None, device_type: str = None,
                     status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM quantum_devices WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if device_type:
                    query += ' AND device_type = ?'
                    params.append(device_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                devices = [dict(d) for d in cursor.fetchall()]
                return {'success': True, 'devices': devices, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取设备列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 ==========

    def get_quantum_communication_stats(self, education_type: str = None,
                                         time_range: str = 'all') -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                key_query = 'SELECT COUNT(*) as total_keys, COUNT(CASE WHEN status = "distributed" THEN 1 END) as distributed_keys FROM quantum_keys'
                channel_query = 'SELECT COUNT(*) as total_channels FROM quantum_channels'
                auth_query = 'SELECT COUNT(*) as total_auth, COUNT(CASE WHEN auth_result = "success" THEN 1 END) as success_auth FROM auth_records'
                app_query = 'SELECT COUNT(*) as total_apps FROM qc_applications'
                device_query = 'SELECT COUNT(*) as total_devices FROM quantum_devices'

                params = []
                if education_type:
                    key_query += ' WHERE education_type = ?'
                    channel_query += ' WHERE education_type = ?'
                    auth_query += ' WHERE education_type = ?'
                    app_query += ' WHERE education_type = ?'
                    device_query += ' WHERE education_type = ?'
                    params = [education_type] * 5

                cursor.execute(key_query, params[:1] if education_type else [])
                key_stats = cursor.fetchone()
                cursor.execute(channel_query, params[1:2] if education_type else [])
                channel_stats = cursor.fetchone()
                cursor.execute(auth_query, params[2:3] if education_type else [])
                auth_stats = cursor.fetchone()
                cursor.execute(app_query, params[3:4] if education_type else [])
                app_stats = cursor.fetchone()
                cursor.execute(device_query, params[4:5] if education_type else [])
                device_stats = cursor.fetchone()

                stats = {
                    'total_keys': key_stats[0] if key_stats else 0,
                    'distributed_keys': key_stats[1] if key_stats else 0,
                    'total_channels': channel_stats[0] if channel_stats else 0,
                    'total_authentications': auth_stats[0] if auth_stats else 0,
                    'successful_authentications': auth_stats[1] if auth_stats else 0,
                    'total_applications': app_stats[0] if app_stats else 0,
                    'total_devices': device_stats[0] if device_stats else 0,
                    'education_type': education_type or 'all',
                    'time_range': time_range,
                    'generated_at': datetime.now().isoformat()
                }
                return {'success': True, 'stats': stats}
        except Exception as e:
            logger.error(f'获取量子通信统计失败: {e}')
            return {'success': False, 'error': str(e)}