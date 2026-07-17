#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育边缘计算服务 (v15.21.0)
====================================
提供边缘节点管理、边缘计算任务、边缘数据处理、边缘AI推理、
边缘网络、边缘安全、边缘存储和边缘协同等综合服务。

核心能力：
1. 边缘节点管理 - 节点注册、配置管理、状态监控、节点调度
2. 边缘计算任务 - 任务创建、任务分配、任务执行、任务监控
3. 边缘数据处理 - 数据采集、数据预处理、数据存储、数据同步
4. 边缘AI推理 - 推理任务、模型管理、推理执行、结果分析
5. 边缘网络管理 - 网络配置、连接管理、带宽控制、网络优化
6. 边缘安全管理 - 安全策略、访问控制、安全审计、入侵检测
7. 边缘存储管理 - 存储配置、数据存储、缓存管理、数据备份
8. 边缘协同管理 - 协同任务、资源共享、分布式处理、智能调度

教育类型支持：成人教育(adult)、K12教育(k12)
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_edge_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationEdge')


# ========== 边缘配置 ==========

EDGE_NODE_TYPES = {
    'campus': {'name': '校园边缘节点', 'capacity': 'high', 'location': 'campus'},
    'classroom': {'name': '教室边缘节点', 'capacity': 'medium', 'location': 'classroom'},
    'lab': {'name': '实验室边缘节点', 'capacity': 'high', 'location': 'lab'},
    'device': {'name': '设备边缘节点', 'capacity': 'low', 'location': 'device'},
    'gateway': {'name': '网关边缘节点', 'capacity': 'medium', 'location': 'gateway'},
    'mobile': {'name': '移动边缘节点', 'capacity': 'medium', 'location': 'mobile'},
    'vehicle': {'name': '车载边缘节点', 'capacity': 'medium', 'location': 'vehicle'},
    'home': {'name': '家庭边缘节点', 'capacity': 'low', 'location': 'home'}
}

COMPUTING_TASKS = {
    'data_collection': {'name': '数据采集', 'resource_requirement': 'low'},
    'data_preprocessing': {'name': '数据预处理', 'resource_requirement': 'medium'},
    'ai_inference': {'name': 'AI推理', 'resource_requirement': 'high'},
    'model_training': {'name': '模型训练', 'resource_requirement': 'high'},
    'real_time_analysis': {'name': '实时分析', 'resource_requirement': 'medium'},
    'event_processing': {'name': '事件处理', 'resource_requirement': 'medium'},
    'decision_control': {'name': '决策控制', 'resource_requirement': 'medium'},
    'data_synchronization': {'name': '数据同步', 'resource_requirement': 'low'}
}

DATA_PROCESSING = {
    'real_time': {'name': '实时处理', 'latency': 'low', 'throughput': 'medium'},
    'batch': {'name': '离线处理', 'latency': 'high', 'throughput': 'high'},
    'stream': {'name': '流处理', 'latency': 'low', 'throughput': 'high'},
    'batch_processing': {'name': '批处理', 'latency': 'medium', 'throughput': 'high'},
    'incremental': {'name': '增量处理', 'latency': 'low', 'throughput': 'medium'},
    'full': {'name': '全量处理', 'latency': 'high', 'throughput': 'high'},
    'compression': {'name': '压缩处理', 'latency': 'low', 'throughput': 'medium'},
    'encryption': {'name': '加密处理', 'latency': 'medium', 'throughput': 'low'}
}

AI_INFERENCE = {
    'image_recognition': {'name': '图像识别', 'model_type': 'cnn', 'latency': 'low'},
    'speech_recognition': {'name': '语音识别', 'model_type': 'rnn', 'latency': 'medium'},
    'nlp': {'name': '自然语言处理', 'model_type': 'transformer', 'latency': 'medium'},
    'behavior_analysis': {'name': '行为分析', 'model_type': 'lstm', 'latency': 'medium'},
    'anomaly_detection': {'name': '异常检测', 'model_type': 'autoencoder', 'latency': 'low'},
    'predictive_analysis': {'name': '预测分析', 'model_type': 'mlp', 'latency': 'medium'},
    'recommendation': {'name': '推荐系统', 'model_type': 'collaborative', 'latency': 'low'},
    'qa_system': {'name': '智能问答', 'model_type': 'transformer', 'latency': 'medium'}
}

NETWORK_TYPES = {
    'lan': {'name': '局域网', 'bandwidth': 'high', 'latency': 'low', 'range': 'short'},
    'iot': {'name': '物联网', 'bandwidth': 'low', 'latency': 'medium', 'range': 'medium'},
    '5g': {'name': '5G网络', 'bandwidth': 'high', 'latency': 'low', 'range': 'medium'},
    'wifi': {'name': 'Wi-Fi网络', 'bandwidth': 'high', 'latency': 'low', 'range': 'short'},
    'bluetooth': {'name': '蓝牙网络', 'bandwidth': 'low', 'latency': 'low', 'range': 'very_short'},
    'zigbee': {'name': 'Zigbee网络', 'bandwidth': 'low', 'latency': 'medium', 'range': 'short'},
    'lora': {'name': 'LoRa网络', 'bandwidth': 'low', 'latency': 'high', 'range': 'long'},
    'satellite': {'name': '卫星网络', 'bandwidth': 'medium', 'latency': 'high', 'range': 'very_long'}
}

SECURITY_MEASURES = {
    'data_encryption': {'name': '数据加密', 'level': 'high', 'type': 'protection'},
    'identity_auth': {'name': '身份认证', 'level': 'high', 'type': 'access'},
    'access_control': {'name': '访问控制', 'level': 'medium', 'type': 'access'},
    'security_audit': {'name': '安全审计', 'level': 'medium', 'type': 'monitor'},
    'intrusion_detection': {'name': '入侵检测', 'level': 'high', 'type': 'monitor'},
    'firewall': {'name': '防火墙', 'level': 'medium', 'type': 'protection'},
    'data_masking': {'name': '数据脱敏', 'level': 'medium', 'type': 'protection'},
    'security_isolation': {'name': '安全隔离', 'level': 'high', 'type': 'protection'}
}

STORAGE_TYPES = {
    'local': {'name': '本地存储', 'capacity': 'medium', 'speed': 'high', 'persistence': 'high'},
    'distributed': {'name': '分布式存储', 'capacity': 'high', 'speed': 'medium', 'persistence': 'high'},
    'cache': {'name': '缓存存储', 'capacity': 'low', 'speed': 'very_high', 'persistence': 'low'},
    'persistent': {'name': '持久化存储', 'capacity': 'high', 'speed': 'medium', 'persistence': 'very_high'},
    'temporary': {'name': '临时存储', 'capacity': 'low', 'speed': 'high', 'persistence': 'none'},
    'backup': {'name': '备份存储', 'capacity': 'high', 'speed': 'low', 'persistence': 'very_high'},
    'cloud': {'name': '云存储', 'capacity': 'very_high', 'speed': 'medium', 'persistence': 'high'},
    'edge_cloud': {'name': '边缘云存储', 'capacity': 'high', 'speed': 'high', 'persistence': 'high'}
}

COOPERATION_MODELS = {
    'edge_cloud': {'name': '边缘-云端协同', 'architecture': 'hierarchical'},
    'edge_edge': {'name': '边缘-边缘协同', 'architecture': 'distributed'},
    'distributed': {'name': '分布式协同', 'architecture': 'peer_to_peer'},
    'centralized': {'name': '集中式协同', 'architecture': 'centralized'},
    'hybrid': {'name': '混合协同', 'architecture': 'hybrid'},
    'dynamic': {'name': '动态协同', 'architecture': 'adaptive'},
    'adaptive': {'name': '自适应协同', 'architecture': 'self_organizing'},
    'intelligent': {'name': '智能协同', 'architecture': 'ai_driven'}
}


class EducationEdgeComputingService:
    """教育边缘计算服务"""

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
                    CREATE TABLE IF NOT EXISTS edge_nodes (
                        node_id TEXT PRIMARY KEY,
                        node_name TEXT NOT NULL,
                        node_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        location TEXT,
                        ip_address TEXT,
                        status TEXT DEFAULT 'online',
                        cpu_usage REAL DEFAULT 0,
                        memory_usage REAL DEFAULT 0,
                        storage_usage REAL DEFAULT 0,
                        network_bandwidth REAL DEFAULT 0,
                        last_heartbeat TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS node_config (
                        config_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        node_id TEXT NOT NULL,
                        config_key TEXT NOT NULL,
                        config_value TEXT,
                        education_type TEXT,
                        created_at TEXT,
                        UNIQUE(node_id, config_key)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS edge_tasks (
                        task_id TEXT PRIMARY KEY,
                        task_name TEXT NOT NULL,
                        task_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        priority INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'pending',
                        progress REAL DEFAULT 0,
                        description TEXT,
                        input_params TEXT,
                        output_result TEXT,
                        scheduled_time TEXT,
                        started_at TEXT,
                        completed_at TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS task_assignments (
                        assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_id TEXT NOT NULL,
                        node_id TEXT NOT NULL,
                        status TEXT DEFAULT 'assigned',
                        started_at TEXT,
                        completed_at TEXT,
                        error_message TEXT,
                        created_at TEXT,
                        UNIQUE(task_id, node_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS edge_data (
                        data_id TEXT PRIMARY KEY,
                        data_name TEXT NOT NULL,
                        data_type TEXT,
                        education_type TEXT NOT NULL,
                        source_node_id TEXT,
                        data_size INTEGER DEFAULT 0,
                        data_format TEXT,
                        data_content TEXT,
                        is_processed INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS data_processing (
                        processing_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        data_id TEXT NOT NULL,
                        processing_type TEXT NOT NULL,
                        education_type TEXT,
                        status TEXT DEFAULT 'pending',
                        processed_data TEXT,
                        processing_time REAL DEFAULT 0,
                        created_at TEXT,
                        completed_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_inference (
                        inference_id TEXT PRIMARY KEY,
                        inference_name TEXT NOT NULL,
                        model_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        model_version TEXT,
                        input_data TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS inference_results (
                        result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        inference_id TEXT NOT NULL,
                        node_id TEXT,
                        result_data TEXT,
                        confidence REAL DEFAULT 0,
                        inference_time REAL DEFAULT 0,
                        status TEXT DEFAULT 'completed',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS edge_network (
                        network_id TEXT PRIMARY KEY,
                        network_name TEXT NOT NULL,
                        network_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        bandwidth REAL DEFAULT 0,
                        latency REAL DEFAULT 0,
                        signal_strength REAL DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS network_config (
                        config_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        network_id TEXT NOT NULL,
                        config_key TEXT NOT NULL,
                        config_value TEXT,
                        education_type TEXT,
                        created_at TEXT,
                        UNIQUE(network_id, config_key)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS edge_security (
                        security_id TEXT PRIMARY KEY,
                        security_name TEXT NOT NULL,
                        security_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        status TEXT DEFAULT 'active',
                        severity_level TEXT DEFAULT 'medium',
                        configuration TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS security_policies (
                        policy_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        security_id TEXT NOT NULL,
                        policy_name TEXT NOT NULL,
                        policy_rule TEXT,
                        education_type TEXT,
                        is_enabled INTEGER DEFAULT 1,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS edge_storage (
                        storage_id TEXT PRIMARY KEY,
                        storage_name TEXT NOT NULL,
                        storage_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        capacity INTEGER DEFAULT 0,
                        used_space INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        location TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS storage_config (
                        config_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        storage_id TEXT NOT NULL,
                        config_key TEXT NOT NULL,
                        config_value TEXT,
                        education_type TEXT,
                        created_at TEXT,
                        UNIQUE(storage_id, config_key)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS edge_cooperation (
                        cooperation_id TEXT PRIMARY KEY,
                        cooperation_name TEXT NOT NULL,
                        cooperation_model TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        status TEXT DEFAULT 'active',
                        participating_nodes TEXT,
                        description TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cooperation_tasks (
                        task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cooperation_id TEXT NOT NULL,
                        task_name TEXT NOT NULL,
                        task_type TEXT,
                        education_type TEXT,
                        status TEXT DEFAULT 'pending',
                        progress REAL DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS edge_monitoring (
                        monitor_id TEXT PRIMARY KEY,
                        monitor_name TEXT NOT NULL,
                        monitor_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        target_node_id TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS monitoring_data (
                        data_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        monitor_id TEXT NOT NULL,
                        metric_type TEXT NOT NULL,
                        metric_value REAL,
                        metric_unit TEXT,
                        education_type TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS edge_alerts (
                        alert_id TEXT PRIMARY KEY,
                        alert_name TEXT NOT NULL,
                        alert_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        severity TEXT DEFAULT 'warning',
                        status TEXT DEFAULT 'active',
                        node_id TEXT,
                        message TEXT,
                        created_at TEXT,
                        resolved_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alert_rules (
                        rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        rule_name TEXT NOT NULL,
                        rule_condition TEXT,
                        education_type TEXT,
                        severity TEXT DEFAULT 'warning',
                        is_enabled INTEGER DEFAULT 1,
                        created_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('教育边缘计算服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 边缘节点管理 ==========

    def register_node(self, node_name: str, node_type: str, education_type: str,
                       **kwargs) -> Dict[str, Any]:
        try:
            node_id = f"edn_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO edge_nodes (
                            node_id, node_name, node_type, education_type,
                            location, ip_address, status, cpu_usage,
                            memory_usage, storage_usage, network_bandwidth,
                            last_heartbeat, is_active, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'online', 0, 0, 0, 0, ?, 1, ?, ?)
                    ''', (node_id, node_name, node_type, education_type,
                          kwargs.get('location'), kwargs.get('ip_address'),
                          now, now, now))
                    conn.commit()
                    logger.info(f'注册边缘节点: {node_name} ({node_id}, {education_type})')
                    return {'success': True, 'node_id': node_id}
        except Exception as e:
            logger.error(f'注册边缘节点失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_node_status(self, node_id: str, status: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE edge_nodes SET
                            status = ?, cpu_usage = ?, memory_usage = ?,
                            storage_usage = ?, network_bandwidth = ?,
                            last_heartbeat = ?, updated_at = ?
                        WHERE node_id = ?
                    ''', (status, kwargs.get('cpu_usage', 0), kwargs.get('memory_usage', 0),
                          kwargs.get('storage_usage', 0), kwargs.get('network_bandwidth', 0),
                          now, now, node_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '节点不存在'}
        except Exception as e:
            logger.error(f'更新节点状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_node_info(self, node_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM edge_nodes WHERE node_id = ?', (node_id,))
                node = cursor.fetchone()
                if node:
                    return {'success': True, 'node': dict(node)}
                return {'success': False, 'error': '节点不存在'}
        except Exception as e:
            logger.error(f'获取节点信息失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_nodes(self, education_type: str = None, node_type: str = None,
                   status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM edge_nodes WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if node_type:
                    query += ' AND node_type = ?'
                    params.append(node_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                nodes = [dict(n) for n in cursor.fetchall()]
                return {'success': True, 'nodes': nodes, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取节点列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 边缘计算任务 ==========

    def create_computing_task(self, task_name: str, task_type: str, education_type: str,
                              **kwargs) -> Dict[str, Any]:
        try:
            task_id = f"edt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO edge_tasks (
                            task_id, task_name, task_type, education_type,
                            priority, status, progress, description,
                            input_params, output_result, scheduled_time,
                            started_at, completed_at, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 'pending', 0, ?, ?, NULL, ?, NULL, NULL, ?, ?)
                    ''', (task_id, task_name, task_type, education_type,
                          kwargs.get('priority', 0), kwargs.get('description'),
                          json.dumps(kwargs.get('input_params', {})),
                          kwargs.get('scheduled_time'), now, now))
                    conn.commit()
                    logger.info(f'创建边缘计算任务: {task_name} ({task_id}, {education_type})')
                    return {'success': True, 'task_id': task_id}
        except Exception as e:
            logger.error(f'创建边缘计算任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def assign_task(self, task_id: str, node_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM edge_tasks WHERE task_id = ?', (task_id,))
                    task = cursor.fetchone()
                    if not task:
                        return {'success': False, 'error': '任务不存在'}
                    if task[0] != 'pending':
                        return {'success': False, 'error': '任务状态不允许分配'}
                    cursor.execute('SELECT status FROM edge_nodes WHERE node_id = ?', (node_id,))
                    node = cursor.fetchone()
                    if not node or node[0] != 'online':
                        return {'success': False, 'error': '节点不可用'}
                    cursor.execute('''
                        INSERT OR IGNORE INTO task_assignments (task_id, node_id, status, created_at)
                        VALUES (?, ?, 'assigned', ?)
                    ''', (task_id, node_id, now))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE edge_tasks SET status = ?, updated_at = ? WHERE task_id = ?',
                                     ('assigned', now, task_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '任务已分配'}
        except Exception as e:
            logger.error(f'分配任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_task_progress(self, task_id: str, progress: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'completed' if progress >= 100 else ('running' if progress > 0 else 'pending')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    update_fields = ['progress = ?', 'status = ?', 'updated_at = ?']
                    update_values = [progress, status, now]
                    if kwargs.get('output_result'):
                        update_fields.append('output_result = ?')
                        update_values.append(json.dumps(kwargs['output_result']))
                    if progress >= 100:
                        update_fields.append('completed_at = ?')
                        update_values.append(now)
                    if not kwargs.get('started_at') and progress > 0:
                        update_fields.append('started_at = ?')
                        update_values.append(now)
                    update_values.append(task_id)
                    cursor.execute(f'UPDATE edge_tasks SET {", ".join(update_fields)} WHERE task_id = ?', update_values)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '任务不存在'}
        except Exception as e:
            logger.error(f'更新任务进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_tasks(self, education_type: str = None, task_type: str = None,
                   status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM edge_tasks WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if task_type:
                    query += ' AND task_type = ?'
                    params.append(task_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                tasks = [dict(t) for t in cursor.fetchall()]
                return {'success': True, 'tasks': tasks, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取任务列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 边缘数据处理 ==========

    def collect_data(self, data_name: str, education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            data_id = f"edd_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO edge_data (
                            data_id, data_name, data_type, education_type,
                            source_node_id, data_size, data_format,
                            data_content, is_processed, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                    ''', (data_id, data_name, kwargs.get('data_type'), education_type,
                          kwargs.get('source_node_id'), kwargs.get('data_size', 0),
                          kwargs.get('data_format'), kwargs.get('data_content'),
                          now, now))
                    conn.commit()
                    logger.info(f'采集边缘数据: {data_name} ({data_id}, {education_type})')
                    return {'success': True, 'data_id': data_id}
        except Exception as e:
            logger.error(f'采集边缘数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def process_data(self, data_id: str, processing_type: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM edge_data WHERE data_id = ?', (data_id,))
                    data = cursor.fetchone()
                    if not data:
                        return {'success': False, 'error': '数据不存在'}
                    cursor.execute('''
                        INSERT INTO data_processing (
                            data_id, processing_type, education_type,
                            status, processed_data, processing_time,
                            created_at, completed_at
                        ) VALUES (?, ?, ?, 'processing', NULL, 0, ?, NULL)
                    ''', (data_id, processing_type, data[0], now))
                    processing_id = cursor.lastrowid
                    processed_data = kwargs.get('processed_data')
                    processing_time = kwargs.get('processing_time', 0)
                    cursor.execute('''
                        UPDATE data_processing SET
                            status = ?, processed_data = ?,
                            processing_time = ?, completed_at = ?
                        WHERE processing_id = ?
                    ''', ('completed', processed_data, processing_time, now, processing_id))
                    cursor.execute('UPDATE edge_data SET is_processed = 1, updated_at = ? WHERE data_id = ?',
                                 (now, data_id))
                    conn.commit()
                    return {'success': True, 'processing_id': processing_id}
        except Exception as e:
            logger.error(f'处理边缘数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def store_data(self, data_id: str, storage_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT data_size FROM edge_data WHERE data_id = ?', (data_id,))
                    data = cursor.fetchone()
                    if not data:
                        return {'success': False, 'error': '数据不存在'}
                    cursor.execute('SELECT capacity, used_space FROM edge_storage WHERE storage_id = ?', (storage_id,))
                    storage = cursor.fetchone()
                    if not storage:
                        return {'success': False, 'error': '存储不存在'}
                    if storage[0] and storage[1] + data[0] > storage[0]:
                        return {'success': False, 'error': '存储空间不足'}
                    cursor.execute('UPDATE edge_storage SET used_space = used_space + ?, updated_at = ? WHERE storage_id = ?',
                                 (data[0], now, storage_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'存储数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def sync_data(self, source_node_id: str, target_node_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM edge_nodes WHERE node_id IN (?, ?)', (source_node_id, target_node_id))
                    nodes = cursor.fetchall()
                    if len(nodes) < 2:
                        return {'success': False, 'error': '节点不存在'}
                    if any(n[0] != 'online' for n in nodes):
                        return {'success': False, 'error': '节点不可用'}
                    sync_task_id = f"eds_{uuid.uuid4().hex[:12]}"
                    cursor.execute('''
                        INSERT INTO edge_tasks (
                            task_id, task_name, task_type, education_type,
                            priority, status, progress, description,
                            input_params, created_at, updated_at
                        ) VALUES (?, ?, 'data_synchronization', ?, 1, 'running', 50, ?, ?, ?, ?)
                    ''', (sync_task_id, '数据同步任务', kwargs.get('education_type', 'k12'),
                          '数据同步', json.dumps({'source': source_node_id, 'target': target_node_id}),
                          now, now))
                    cursor.execute('UPDATE edge_tasks SET status = ?, progress = ?, updated_at = ? WHERE task_id = ?',
                                 ('completed', 100, now, sync_task_id))
                    conn.commit()
                    return {'success': True, 'sync_task_id': sync_task_id}
        except Exception as e:
            logger.error(f'数据同步失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 边缘AI推理 ==========

    def create_inference_task(self, inference_name: str, model_type: str, education_type: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            inference_id = f"ein_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO ai_inference (
                            inference_id, inference_name, model_type,
                            education_type, model_version, input_data,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                    ''', (inference_id, inference_name, model_type, education_type,
                          kwargs.get('model_version'), json.dumps(kwargs.get('input_data', {})),
                          now, now))
                    conn.commit()
                    logger.info(f'创建AI推理任务: {inference_name} ({inference_id}, {education_type})')
                    return {'success': True, 'inference_id': inference_id}
        except Exception as e:
            logger.error(f'创建AI推理任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def execute_inference(self, inference_id: str, node_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM ai_inference WHERE inference_id = ?', (inference_id,))
                    inference = cursor.fetchone()
                    if not inference:
                        return {'success': False, 'error': '推理任务不存在'}
                    cursor.execute('UPDATE ai_inference SET status = ?, updated_at = ? WHERE inference_id = ?',
                                 ('running', now, inference_id))
                    cursor.execute('''
                        INSERT INTO inference_results (
                            inference_id, node_id, result_data,
                            confidence, inference_time, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, 'completed', ?)
                    ''', (inference_id, node_id, json.dumps(kwargs.get('result_data', {})),
                          kwargs.get('confidence', 0), kwargs.get('inference_time', 0), now))
                    result_id = cursor.lastrowid
                    cursor.execute('UPDATE ai_inference SET status = ?, updated_at = ? WHERE inference_id = ?',
                                 ('completed', now, inference_id))
                    conn.commit()
                    return {'success': True, 'result_id': result_id}
        except Exception as e:
            logger.error(f'执行AI推理失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_inference_result(self, inference_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM ai_inference WHERE inference_id = ?', (inference_id,))
                inference = cursor.fetchone()
                if not inference:
                    return {'success': False, 'error': '推理任务不存在'}
                cursor.execute('SELECT * FROM inference_results WHERE inference_id = ? ORDER BY created_at DESC', (inference_id,))
                results = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'inference': dict(inference), 'results': results}
        except Exception as e:
            logger.error(f'获取推理结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_inference_tasks(self, education_type: str = None, model_type: str = None,
                              status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM ai_inference WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if model_type:
                    query += ' AND model_type = ?'
                    params.append(model_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                tasks = [dict(t) for t in cursor.fetchall()]
                return {'success': True, 'tasks': tasks, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取推理任务列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def analyze_inference_results(self, education_type: str = None, days: int = 7) -> Dict[str, Any]:
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = '''
                    SELECT ir.status, COUNT(*) as count, AVG(ir.confidence) as avg_confidence
                    FROM inference_results ir
                    JOIN ai_inference ai ON ir.inference_id = ai.inference_id
                    WHERE ir.created_at >= ? AND ir.created_at <= ?
                '''
                params = [start_date.isoformat(), end_date.isoformat()]
                if education_type:
                    query += ' AND ai.education_type = ?'
                    params.append(education_type)
                query += ' GROUP BY ir.status'
                cursor.execute(query, params)
                stats = cursor.fetchall()
                result = {'success': True, 'statistics': [], 'period': {'start': start_date.isoformat()[:10], 'end': end_date.isoformat()[:10]}}
                for stat in stats:
                    result['statistics'].append({
                        'status': stat[0],
                        'count': stat[1],
                        'avg_confidence': round(stat[2], 2) if stat[2] else 0
                    })
                return result
        except Exception as e:
            logger.error(f'分析推理结果失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 边缘网络管理 ==========

    def create_network(self, network_name: str, network_type: str, education_type: str,
                       **kwargs) -> Dict[str, Any]:
        try:
            network_id = f"edn_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO edge_network (
                            network_id, network_name, network_type,
                            education_type, bandwidth, latency,
                            signal_strength, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (network_id, network_name, network_type, education_type,
                          kwargs.get('bandwidth', 0), kwargs.get('latency', 0),
                          kwargs.get('signal_strength', 0), now, now))
                    conn.commit()
                    logger.info(f'创建边缘网络: {network_name} ({network_id}, {education_type})')
                    return {'success': True, 'network_id': network_id}
        except Exception as e:
            logger.error(f'创建边缘网络失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_network_status(self, network_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    update_fields = ['updated_at = ?']
                    update_values = [now]
                    if 'bandwidth' in kwargs:
                        update_fields.append('bandwidth = ?')
                        update_values.append(kwargs['bandwidth'])
                    if 'latency' in kwargs:
                        update_fields.append('latency = ?')
                        update_values.append(kwargs['latency'])
                    if 'signal_strength' in kwargs:
                        update_fields.append('signal_strength = ?')
                        update_values.append(kwargs['signal_strength'])
                    if 'status' in kwargs:
                        update_fields.append('status = ?')
                        update_values.append(kwargs['status'])
                    update_values.append(network_id)
                    cursor.execute(f'UPDATE edge_network SET {", ".join(update_fields)} WHERE network_id = ?', update_values)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '网络不存在'}
        except Exception as e:
            logger.error(f'更新网络状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_network_info(self, network_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM edge_network WHERE network_id = ?', (network_id,))
                network = cursor.fetchone()
                if network:
                    return {'success': True, 'network': dict(network)}
                return {'success': False, 'error': '网络不存在'}
        except Exception as e:
            logger.error(f'获取网络信息失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_networks(self, education_type: str = None, network_type: str = None,
                      status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM edge_network WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if network_type:
                    query += ' AND network_type = ?'
                    params.append(network_type)
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

    # ========== 边缘安全管理 ==========

    def create_security_policy(self, security_name: str, security_type: str, education_type: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            security_id = f"eds_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO edge_security (
                            security_id, security_name, security_type,
                            education_type, status, severity_level,
                            configuration, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, 'active', ?, ?, ?, ?)
                    ''', (security_id, security_name, security_type, education_type,
                          kwargs.get('severity_level', 'medium'),
                          json.dumps(kwargs.get('configuration', {})), now, now))
                    conn.commit()
                    logger.info(f'创建安全策略: {security_name} ({security_id}, {education_type})')
                    return {'success': True, 'security_id': security_id}
        except Exception as e:
            logger.error(f'创建安全策略失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_security_rule(self, security_id: str, policy_name: str, policy_rule: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM edge_security WHERE security_id = ?', (security_id,))
                    security = cursor.fetchone()
                    if not security:
                        return {'success': False, 'error': '安全策略不存在'}
                    cursor.execute('''
                        INSERT INTO security_policies (
                            security_id, policy_name, policy_rule,
                            education_type, is_enabled, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (security_id, policy_name, policy_rule,
                          kwargs.get('education_type', security[0]),
                          kwargs.get('is_enabled', 1), now))
                    policy_id = cursor.lastrowid
                    conn.commit()
                    return {'success': True, 'policy_id': policy_id}
        except Exception as e:
            logger.error(f'添加安全规则失败: {e}')
            return {'success': False, 'error': str(e)}

    def enforce_security(self, security_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM edge_security WHERE security_id = ?', (security_id,))
                    security = cursor.fetchone()
                    if not security:
                        return {'success': False, 'error': '安全策略不存在'}
                    cursor.execute('UPDATE edge_security SET status = ?, updated_at = ? WHERE security_id = ?',
                                 ('enforced', now, security_id))
                    cursor.execute('UPDATE security_policies SET is_enabled = 1 WHERE security_id = ?', (security_id,))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'执行安全策略失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_security_policies(self, education_type: str = None, security_type: str = None,
                                status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM edge_security WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if security_type:
                    query += ' AND security_type = ?'
                    params.append(security_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
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

    # ========== 边缘存储管理 ==========

    def create_storage(self, storage_name: str, storage_type: str, education_type: str,
                       **kwargs) -> Dict[str, Any]:
        try:
            storage_id = f"eds_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO edge_storage (
                            storage_id, storage_name, storage_type,
                            education_type, capacity, used_space,
                            status, location, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 0, 'active', ?, ?, ?)
                    ''', (storage_id, storage_name, storage_type, education_type,
                          kwargs.get('capacity', 0), kwargs.get('location'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建边缘存储: {storage_name} ({storage_id}, {education_type})')
                    return {'success': True, 'storage_id': storage_id}
        except Exception as e:
            logger.error(f'创建边缘存储失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_storage_status(self, storage_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    update_fields = ['updated_at = ?']
                    update_values = [now]
                    if 'used_space' in kwargs:
                        update_fields.append('used_space = ?')
                        update_values.append(kwargs['used_space'])
                    if 'capacity' in kwargs:
                        update_fields.append('capacity = ?')
                        update_values.append(kwargs['capacity'])
                    if 'status' in kwargs:
                        update_fields.append('status = ?')
                        update_values.append(kwargs['status'])
                    update_values.append(storage_id)
                    cursor.execute(f'UPDATE edge_storage SET {", ".join(update_fields)} WHERE storage_id = ?', update_values)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '存储不存在'}
        except Exception as e:
            logger.error(f'更新存储状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_storage_info(self, storage_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM edge_storage WHERE storage_id = ?', (storage_id,))
                storage = cursor.fetchone()
                if storage:
                    storage_dict = dict(storage)
                    if storage_dict['capacity'] > 0:
                        storage_dict['usage_percentage'] = round(storage_dict['used_space'] / storage_dict['capacity'] * 100, 2)
                    else:
                        storage_dict['usage_percentage'] = 0
                    return {'success': True, 'storage': storage_dict}
                return {'success': False, 'error': '存储不存在'}
        except Exception as e:
            logger.error(f'获取存储信息失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_storages(self, education_type: str = None, storage_type: str = None,
                      status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM edge_storage WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if storage_type:
                    query += ' AND storage_type = ?'
                    params.append(storage_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                storages = []
                for s in cursor.fetchall():
                    s_dict = dict(s)
                    if s_dict['capacity'] > 0:
                        s_dict['usage_percentage'] = round(s_dict['used_space'] / s_dict['capacity'] * 100, 2)
                    else:
                        s_dict['usage_percentage'] = 0
                    storages.append(s_dict)
                return {'success': True, 'storages': storages, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取存储列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 边缘协同管理 ==========

    def create_cooperation(self, cooperation_name: str, cooperation_model: str, education_type: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            cooperation_id = f"edc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO edge_cooperation (
                            cooperation_id, cooperation_name, cooperation_model,
                            education_type, status, participating_nodes,
                            description, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, 'active', ?, ?, ?, ?)
                    ''', (cooperation_id, cooperation_name, cooperation_model, education_type,
                          json.dumps(kwargs.get('participating_nodes', [])),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建边缘协同: {cooperation_name} ({cooperation_id}, {education_type})')
                    return {'success': True, 'cooperation_id': cooperation_id}
        except Exception as e:
            logger.error(f'创建边缘协同失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_cooperation_task(self, cooperation_id: str, task_name: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM edge_cooperation WHERE cooperation_id = ?', (cooperation_id,))
                    cooperation = cursor.fetchone()
                    if not cooperation:
                        return {'success': False, 'error': '协同不存在'}
                    cursor.execute('''
                        INSERT INTO cooperation_tasks (
                            cooperation_id, task_name, task_type,
                            education_type, status, progress,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, 'pending', 0, ?, ?)
                    ''', (cooperation_id, task_name, kwargs.get('task_type'),
                          kwargs.get('education_type', cooperation[0]),
                          now, now))
                    task_id = cursor.lastrowid
                    conn.commit()
                    return {'success': True, 'task_id': task_id}
        except Exception as e:
            logger.error(f'添加协同任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_cooperation_task(self, task_id: int, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    update_fields = ['updated_at = ?']
                    update_values = [now]
                    if 'status' in kwargs:
                        update_fields.append('status = ?')
                        update_values.append(kwargs['status'])
                    if 'progress' in kwargs:
                        update_fields.append('progress = ?')
                        update_values.append(kwargs['progress'])
                    update_values.append(task_id)
                    cursor.execute(f'UPDATE cooperation_tasks SET {", ".join(update_fields)} WHERE task_id = ?', update_values)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '协同任务不存在'}
        except Exception as e:
            logger.error(f'更新协同任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_cooperations(self, education_type: str = None, cooperation_model: str = None,
                          status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM edge_cooperation WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if cooperation_model:
                    query += ' AND cooperation_model = ?'
                    params.append(cooperation_model)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                cooperations = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'cooperations': cooperations, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取协同列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 监控管理 ==========

    def create_monitor(self, monitor_name: str, monitor_type: str, education_type: str,
                       **kwargs) -> Dict[str, Any]:
        try:
            monitor_id = f"edm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO edge_monitoring (
                            monitor_id, monitor_name, monitor_type,
                            education_type, target_node_id, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (monitor_id, monitor_name, monitor_type, education_type,
                          kwargs.get('target_node_id'), now, now))
                    conn.commit()
                    logger.info(f'创建监控: {monitor_name} ({monitor_id}, {education_type})')
                    return {'success': True, 'monitor_id': monitor_id}
        except Exception as e:
            logger.error(f'创建监控失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_monitor_data(self, monitor_id: str, metric_type: str, metric_value: float,
                             **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM edge_monitoring WHERE monitor_id = ?', (monitor_id,))
                    monitor = cursor.fetchone()
                    if not monitor:
                        return {'success': False, 'error': '监控不存在'}
                    cursor.execute('''
                        INSERT INTO monitoring_data (
                            monitor_id, metric_type, metric_value,
                            metric_unit, education_type, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (monitor_id, metric_type, metric_value,
                          kwargs.get('metric_unit'),
                          kwargs.get('education_type', monitor[0]), now))
                    data_id = cursor.lastrowid
                    conn.commit()
                    return {'success': True, 'data_id': data_id}
        except Exception as e:
            logger.error(f'记录监控数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_alert(self, alert_name: str, alert_type: str, education_type: str,
                     **kwargs) -> Dict[str, Any]:
        try:
            alert_id = f"eda_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO edge_alerts (
                            alert_id, alert_name, alert_type,
                            education_type, severity, status,
                            node_id, message, created_at, resolved_at
                        ) VALUES (?, ?, ?, ?, ?, 'active', ?, ?, ?, NULL)
                    ''', (alert_id, alert_name, alert_type, education_type,
                          kwargs.get('severity', 'warning'),
                          kwargs.get('node_id'), kwargs.get('message'), now))
                    conn.commit()
                    logger.info(f'创建告警: {alert_name} ({alert_id}, {education_type})')
                    return {'success': True, 'alert_id': alert_id}
        except Exception as e:
            logger.error(f'创建告警失败: {e}')
            return {'success': False, 'error': str(e)}

    def resolve_alert(self, alert_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE edge_alerts SET status = ?, resolved_at = ? WHERE alert_id = ? AND status = ?',
                                 ('resolved', now, alert_id, 'active'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '告警不存在或已处理'}
        except Exception as e:
            logger.error(f'处理告警失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_service_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                results = {'success': True, 'education_type': education_type}
                for table, label in [('edge_nodes', 'nodes'), ('edge_tasks', 'tasks'),
                                     ('edge_data', 'data'), ('ai_inference', 'inferences'),
                                     ('edge_network', 'networks'), ('edge_security', 'security_policies'),
                                     ('edge_storage', 'storages'), ('edge_cooperation', 'cooperations')]:
                    query = f'SELECT COUNT(*) FROM {table}'
                    params = []
                    if education_type:
                        query += ' WHERE education_type = ?'
                        params.append(education_type)
                    cursor.execute(query, params)
                    results[label] = cursor.fetchone()[0]
                query = 'SELECT severity, COUNT(*) FROM edge_alerts WHERE status = ?'
                params = ['active']
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' GROUP BY severity'
                cursor.execute(query, params)
                alerts = {}
                for row in cursor.fetchall():
                    alerts[row[0]] = row[1]
                results['active_alerts'] = alerts
                return results
        except Exception as e:
            logger.error(f'获取统计信息失败: {e}')
            return {'success': False, 'error': str(e)}