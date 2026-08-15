#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育信息化建设服务 (v15.29.0)
====================================
提供教育信息化规划、基础设施建设、网络建设、数据中心建设、系统集成、云服务、安全建设、运维服务等综合管理服务。

核心能力：
1. 信息化规划 - 规划编制、方案设计、预算编制、评估验收
2. 基础设施 - 设施建设、设备采购、部署安装、运维管理
3. 网络建设 - 网络规划、布线施工、设备配置、性能优化
4. 数据中心 - 机房建设、服务器部署、存储配置、灾备方案、运维监控
5. 系统集成 - 应用集成、数据集成、流程集成、门户集成
6. 云服务 - IaaS/PaaS/SaaS/DaaS/FaaS/BaaS/MaaS/XaaS
7. 安全建设 - 安全评估、防护部署、合规检查、应急响应
8. 运维服务 - IT运维、网络运维、系统运维、数据运维
9. 统计分析 - 建设进度、资源使用、成本统计
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_infrastructure_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationInfrastructure')


# ========== 基础设施配置 ==========

INFRASTRUCTURE_TYPES = {
    'network': {'name': '网络基础设施', 'description': '校园网、城域网、广域网等网络设备与线路'},
    'data': {'name': '数据基础设施', 'description': '数据存储、数据库、数据仓库等设施'},
    'application': {'name': '应用基础设施', 'description': '各类教育应用系统、平台软件'},
    'security': {'name': '安全基础设施', 'description': '防火墙、入侵检测、加密设备等安全设施'},
    'storage': {'name': '存储基础设施', 'description': '磁盘阵列、NAS、SAN等存储设备'},
    'computing': {'name': '计算基础设施', 'description': '服务器、虚拟机、容器等计算资源'},
    'terminal': {'name': '终端基础设施', 'description': '计算机、平板、智能终端等设备'},
    'operation': {'name': '运维基础设施', 'description': '监控系统、运维工具、管理平台'}
}

NETWORK_TYPES = {
    'campus': {'name': '校园网', 'scope': '校内', 'bandwidth': '10G/100G'},
    'metropolitan': {'name': '城域网', 'scope': '城区', 'bandwidth': '100G/1T'},
    'wide_area': {'name': '广域网', 'scope': '跨区域', 'bandwidth': '10G/100G'},
    'internet': {'name': '互联网', 'scope': '全球', 'bandwidth': '1G/10G'},
    'iot': {'name': '物联网', 'scope': '智能设备', 'bandwidth': '100M/1G'},
    'wifi': {'name': '无线局域网', 'scope': '覆盖区域', 'bandwidth': '1G/10G'},
    '5g': {'name': '5G网络', 'scope': '移动覆盖', 'bandwidth': '10G/100G'},
    'satellite': {'name': '卫星网络', 'scope': '偏远地区', 'bandwidth': '100M/1G'}
}

DATA_CENTER_TYPES = {
    'local': {'name': '本地数据中心', 'location': '校内自建', 'scale': '中小型'},
    'colocation': {'name': '托管数据中心', 'location': '第三方机房', 'scale': '中型'},
    'cloud': {'name': '云数据中心', 'location': '公有云/私有云', 'scale': '弹性'},
    'edge': {'name': '边缘数据中心', 'location': '网络边缘', 'scale': '小型'},
    'hybrid': {'name': '混合数据中心', 'location': '本地+云端', 'scale': '中大型'},
    'distributed': {'name': '分布式数据中心', 'location': '多地域', 'scale': '大型'},
    'green': {'name': '绿色数据中心', 'location': '节能环境', 'scale': '中小型'},
    'smart': {'name': '智能数据中心', 'location': '智能化管理', 'scale': '中大型'}
}

SYSTEM_INTEGRATION = {
    'application': {'name': '应用集成', 'description': '多个应用系统互联互通'},
    'data': {'name': '数据集成', 'description': '数据抽取、转换、加载'},
    'process': {'name': '流程集成', 'description': '业务流程自动化整合'},
    'portal': {'name': '门户集成', 'description': '统一身份认证与单点登录'},
    'api': {'name': 'API集成', 'description': '应用程序接口对接'},
    'identity': {'name': '身份集成', 'description': '统一身份管理与权限控制'},
    'security': {'name': '安全集成', 'description': '安全策略统一管理'},
    'cloud': {'name': '云集成', 'description': '多云环境统一管理'}
}

CLOUD_SERVICES = {
    'iaas': {'name': 'IaaS', 'description': '基础设施即服务', 'category': '基础设施'},
    'paas': {'name': 'PaaS', 'description': '平台即服务', 'category': '平台'},
    'saas': {'name': 'SaaS', 'description': '软件即服务', 'category': '软件'},
    'daas': {'name': 'DaaS', 'description': '数据即服务', 'category': '数据'},
    'faas': {'name': 'FaaS', 'description': '函数即服务', 'category': '计算'},
    'baas': {'name': 'BaaS', 'description': '后端即服务', 'category': '后端'},
    'maas': {'name': 'MaaS', 'description': '机器学习即服务', 'category': 'AI'},
    'xaas': {'name': 'XaaS', 'description': '一切即服务', 'category': '综合'}
}

SECURITY_LEVELS = {
    'basic': {'name': '基础安全', 'requirements': '基础防火墙、防病毒'},
    'standard': {'name': '标准安全', 'requirements': '入侵检测、访问控制'},
    'advanced': {'name': '高级安全', 'requirements': '安全审计、加密传输'},
    'enterprise': {'name': '企业安全', 'requirements': '数据防泄漏、安全运维'},
    'financial': {'name': '金融安全', 'requirements': '等保三级、交易安全'},
    'medical': {'name': '医疗安全', 'requirements': 'HIPAA合规、隐私保护'},
    'education': {'name': '教育安全', 'requirements': '等保二级、学生隐私'},
    'government': {'name': '政府安全', 'requirements': '等保三级、涉密保护'}
}

OPERATION_TYPES = {
    'it': {'name': 'IT运维', 'scope': '硬件设备、办公系统'},
    'network': {'name': '网络运维', 'scope': '网络设备、线路监控'},
    'system': {'name': '系统运维', 'scope': '操作系统、数据库'},
    'data': {'name': '数据运维', 'scope': '数据备份、数据治理'},
    'security': {'name': '安全运维', 'scope': '安全设备、漏洞管理'},
    'cloud': {'name': '云运维', 'scope': '云资源、弹性伸缩'},
    'devops': {'name': 'DevOps', 'scope': '开发运维一体化'},
    'aiops': {'name': 'AIOps', 'scope': '智能运维、自动化'}
}

CONSTRUCTION_PHASES = {
    'planning': {'name': '规划设计', 'order': 1},
    'implementation': {'name': '项目实施', 'order': 2},
    'testing': {'name': '系统测试', 'order': 3},
    'deployment': {'name': '上线部署', 'order': 4},
    'operation': {'name': '运维保障', 'order': 5},
    'optimization': {'name': '优化升级', 'order': 6},
    'migration': {'name': '数据迁移', 'order': 7},
    'support': {'name': '技术支持', 'order': 8}
}


class EducationInfrastructureService:
    """教育信息化建设服务"""

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
                    CREATE TABLE IF NOT EXISTS infrastructure_planning (
                        plan_id TEXT PRIMARY KEY,
                        plan_name TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        school_name TEXT,
                        plan_type TEXT,
                        description TEXT,
                        budget REAL DEFAULT 0,
                        start_date TEXT,
                        end_date TEXT,
                        status TEXT DEFAULT 'draft',
                        created_by TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS planning_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        plan_id TEXT NOT NULL,
                        phase TEXT,
                        activity TEXT,
                        responsible TEXT,
                        deadline TEXT,
                        status TEXT DEFAULT 'pending',
                        progress INTEGER DEFAULT 0,
                        remarks TEXT,
                        created_at TEXT,
                        FOREIGN KEY(plan_id) REFERENCES infrastructure_planning(plan_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS infrastructure_construction (
                        construction_id TEXT PRIMARY KEY,
                        construction_name TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        infrastructure_type TEXT,
                        school_name TEXT,
                        location TEXT,
                        budget REAL DEFAULT 0,
                        actual_cost REAL DEFAULT 0,
                        start_date TEXT,
                        end_date TEXT,
                        phase TEXT DEFAULT 'planning',
                        status TEXT DEFAULT 'active',
                        created_by TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS construction_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        construction_id TEXT NOT NULL,
                        activity TEXT,
                        equipment_name TEXT,
                        quantity INTEGER DEFAULT 1,
                        cost REAL DEFAULT 0,
                        completed_at TEXT,
                        remarks TEXT,
                        created_at TEXT,
                        FOREIGN KEY(construction_id) REFERENCES infrastructure_construction(construction_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS network_construction (
                        network_id TEXT PRIMARY KEY,
                        network_name TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        network_type TEXT,
                        school_name TEXT,
                        coverage_area TEXT,
                        bandwidth TEXT,
                        device_count INTEGER DEFAULT 0,
                        ip_range TEXT,
                        vlan_config TEXT,
                        status TEXT DEFAULT 'planning',
                        created_by TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS network_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        network_id TEXT NOT NULL,
                        device_type TEXT,
                        device_name TEXT,
                        ip_address TEXT,
                        location TEXT,
                        installed_at TEXT,
                        remarks TEXT,
                        FOREIGN KEY(network_id) REFERENCES network_construction(network_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS data_center (
                        center_id TEXT PRIMARY KEY,
                        center_name TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        center_type TEXT,
                        school_name TEXT,
                        location TEXT,
                        rack_count INTEGER DEFAULT 0,
                        server_count INTEGER DEFAULT 0,
                        storage_capacity TEXT,
                        power_capacity TEXT,
                        cooling_system TEXT,
                        status TEXT DEFAULT 'planning',
                        created_by TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS center_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        center_id TEXT NOT NULL,
                        asset_type TEXT,
                        asset_name TEXT,
                        serial_number TEXT,
                        purchase_date TEXT,
                        warranty_expire TEXT,
                        status TEXT DEFAULT 'active',
                        remarks TEXT,
                        FOREIGN KEY(center_id) REFERENCES data_center(center_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_integration (
                        integration_id TEXT PRIMARY KEY,
                        integration_name TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        integration_type TEXT,
                        school_name TEXT,
                        source_system TEXT,
                        target_system TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'planning',
                        created_by TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS integration_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        integration_id TEXT NOT NULL,
                        step TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'pending',
                        completed_at TEXT,
                        FOREIGN KEY(integration_id) REFERENCES system_integration(integration_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cloud_services (
                        service_id TEXT PRIMARY KEY,
                        service_name TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        service_type TEXT,
                        school_name TEXT,
                        provider TEXT,
                        subscription_type TEXT,
                        resource_spec TEXT,
                        monthly_cost REAL DEFAULT 0,
                        start_date TEXT,
                        end_date TEXT,
                        status TEXT DEFAULT 'active',
                        created_by TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS service_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        service_id TEXT NOT NULL,
                        record_type TEXT,
                        usage_data TEXT,
                        cost REAL DEFAULT 0,
                        recorded_at TEXT,
                        FOREIGN KEY(service_id) REFERENCES cloud_services(service_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS security_construction (
                        security_id TEXT PRIMARY KEY,
                        security_name TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        security_level TEXT,
                        school_name TEXT,
                        description TEXT,
                        compliance_requirement TEXT,
                        budget REAL DEFAULT 0,
                        status TEXT DEFAULT 'planning',
                        created_by TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS security_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        security_id TEXT NOT NULL,
                        record_type TEXT,
                        event_type TEXT,
                        severity TEXT,
                        description TEXT,
                        resolved INTEGER DEFAULT 0,
                        resolved_at TEXT,
                        FOREIGN KEY(security_id) REFERENCES security_construction(security_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS operation_services (
                        operation_id TEXT PRIMARY KEY,
                        operation_name TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        operation_type TEXT,
                        school_name TEXT,
                        description TEXT,
                        service_level TEXT,
                        status TEXT DEFAULT 'active',
                        created_by TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS operation_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        operation_id TEXT NOT NULL,
                        incident_type TEXT,
                        title TEXT,
                        description TEXT,
                        priority TEXT DEFAULT 'medium',
                        status TEXT DEFAULT 'open',
                        assigned_to TEXT,
                        resolved_at TEXT,
                        FOREIGN KEY(operation_id) REFERENCES operation_services(operation_id)
                    )
                ''')
                conn.commit()
                logger.info('教育信息化建设服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 信息化规划 ==========

    def create_planning(self, plan_name: str, education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            plan_id = f"pln_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO infrastructure_planning (
                            plan_id, plan_name, education_type, school_name,
                            plan_type, description, budget, start_date, end_date,
                            status, created_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?)
                    ''', (plan_id, plan_name, education_type,
                          kwargs.get('school_name'), kwargs.get('plan_type'),
                          kwargs.get('description'), kwargs.get('budget', 0),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建信息化规划: {plan_name} ({plan_id})')
                    return {'success': True, 'plan_id': plan_id}
        except Exception as e:
            logger.error(f'创建信息化规划失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_planning(self, plan_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    updates = []
                    params = []
                    for key, value in kwargs.items():
                        if key in ['plan_name', 'education_type', 'school_name',
                                   'plan_type', 'description', 'budget',
                                   'start_date', 'end_date', 'status', 'created_by']:
                            updates.append(f'{key} = ?')
                            params.append(value)
                    if updates:
                        updates.append('updated_at = ?')
                        params.append(now)
                        params.append(plan_id)
                        cursor.execute(f'UPDATE infrastructure_planning SET {", ".join(updates)} WHERE plan_id = ?', params)
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '没有可更新的字段'}
        except Exception as e:
            logger.error(f'更新信息化规划失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_planning_record(self, plan_id: str, phase: str, activity: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT plan_id FROM infrastructure_planning WHERE plan_id = ?', (plan_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '规划不存在'}
                    cursor.execute('''
                        INSERT INTO planning_records (plan_id, phase, activity, responsible, deadline, status, progress, remarks, created_at)
                        VALUES (?, ?, ?, ?, ?, 'pending', 0, ?, ?)
                    ''', (plan_id, phase, activity, kwargs.get('responsible'),
                          kwargs.get('deadline'), kwargs.get('remarks'), now))
                    conn.commit()
                    return {'success': True, 'record_id': cursor.lastrowid}
        except Exception as e:
            logger.error(f'添加规划记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_planning_progress(self, plan_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT plan_name, status FROM infrastructure_planning WHERE plan_id = ?', (plan_id,))
                plan = cursor.fetchone()
                if not plan:
                    return {'success': False, 'error': '规划不存在'}
                cursor.execute('SELECT COUNT(*) FROM planning_records WHERE plan_id = ?', (plan_id,))
                total = cursor.fetchone()[0] or 0
                cursor.execute('SELECT COUNT(*) FROM planning_records WHERE plan_id = ? AND status = ?', (plan_id, 'completed'))
                completed = cursor.fetchone()[0] or 0
                progress = round((completed / total) * 100) if total > 0 else 0
                return {'success': True, 'plan_name': plan[0], 'status': plan[1], 'total_records': total, 'completed_records': completed, 'progress': progress}
        except Exception as e:
            logger.error(f'获取规划进度失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 基础设施建设 ==========

    def create_construction(self, construction_name: str, education_type: str, infrastructure_type: str, **kwargs) -> Dict[str, Any]:
        try:
            construction_id = f"con_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO infrastructure_construction (
                            construction_id, construction_name, education_type,
                            infrastructure_type, school_name, location,
                            budget, actual_cost, start_date, end_date,
                            phase, status, created_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, 'planning', 'active', ?, ?, ?)
                    ''', (construction_id, construction_name, education_type,
                          infrastructure_type, kwargs.get('school_name'),
                          kwargs.get('location'), kwargs.get('budget', 0),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建基础设施建设项目: {construction_name} ({construction_id})')
                    return {'success': True, 'construction_id': construction_id}
        except Exception as e:
            logger.error(f'创建基础设施建设项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_construction_phase(self, construction_id: str, phase: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE infrastructure_construction SET phase = ?, updated_at = ? WHERE construction_id = ?',
                                 (phase, now, construction_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'phase': phase}
                    return {'success': False, 'error': '建设项目不存在'}
        except Exception as e:
            logger.error(f'更新建设阶段失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_construction_record(self, construction_id: str, activity: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT construction_id FROM infrastructure_construction WHERE construction_id = ?', (construction_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '建设项目不存在'}
                    cursor.execute('''
                        INSERT INTO construction_records (construction_id, activity, equipment_name, quantity, cost, completed_at, remarks, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (construction_id, activity, kwargs.get('equipment_name'),
                          kwargs.get('quantity', 1), kwargs.get('cost', 0),
                          kwargs.get('completed_at'), kwargs.get('remarks'), now))
                    if kwargs.get('cost', 0) > 0:
                        cursor.execute('UPDATE infrastructure_construction SET actual_cost = actual_cost + ? WHERE construction_id = ?',
                                     (kwargs.get('cost', 0), construction_id))
                    conn.commit()
                    return {'success': True, 'record_id': cursor.lastrowid}
        except Exception as e:
            logger.error(f'添加建设记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_construction_cost(self, construction_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT construction_name, budget, actual_cost FROM infrastructure_construction WHERE construction_id = ?', (construction_id,))
                construction = cursor.fetchone()
                if not construction:
                    return {'success': False, 'error': '建设项目不存在'}
                return {'success': True, 'construction_name': construction[0], 'budget': construction[1], 'actual_cost': construction[2], 'remaining': max(0, construction[1] - construction[2])}
        except Exception as e:
            logger.error(f'获取建设成本失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 网络建设 ==========

    def create_network(self, network_name: str, education_type: str, network_type: str, **kwargs) -> Dict[str, Any]:
        try:
            network_id = f"net_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO network_construction (
                            network_id, network_name, education_type, network_type,
                            school_name, coverage_area, bandwidth, device_count,
                            ip_range, vlan_config, status, created_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, 'planning', ?, ?, ?)
                    ''', (network_id, network_name, education_type, network_type,
                          kwargs.get('school_name'), kwargs.get('coverage_area'),
                          kwargs.get('bandwidth'), kwargs.get('ip_range'),
                          kwargs.get('vlan_config'), kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建网络建设项目: {network_name} ({network_id})')
                    return {'success': True, 'network_id': network_id}
        except Exception as e:
            logger.error(f'创建网络建设项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_network_device(self, network_id: str, device_type: str, device_name: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT network_id FROM network_construction WHERE network_id = ?', (network_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '网络项目不存在'}
                    cursor.execute('''
                        INSERT INTO network_records (network_id, device_type, device_name, ip_address, location, installed_at, remarks)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (network_id, device_type, device_name, kwargs.get('ip_address'),
                          kwargs.get('location'), kwargs.get('installed_at', now[:10]), kwargs.get('remarks')))
                    cursor.execute('UPDATE network_construction SET device_count = device_count + 1, updated_at = ? WHERE network_id = ?',
                                 (now, network_id))
                    conn.commit()
                    return {'success': True, 'record_id': cursor.lastrowid}
        except Exception as e:
            logger.error(f'添加网络设备失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_network_status(self, network_id: str, status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE network_construction SET status = ?, updated_at = ? WHERE network_id = ?',
                                 (status, now, network_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '网络项目不存在'}
        except Exception as e:
            logger.error(f'更新网络状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_network_devices(self, network_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM network_records WHERE network_id = ?', (network_id,))
                devices = [dict(d) for d in cursor.fetchall()]
                cursor.execute('SELECT network_name, device_count FROM network_construction WHERE network_id = ?', (network_id,))
                network = cursor.fetchone()
                if not network:
                    return {'success': False, 'error': '网络项目不存在'}
                return {'success': True, 'network_name': network[0], 'device_count': network[1], 'devices': devices}
        except Exception as e:
            logger.error(f'获取网络设备列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 数据中心 ==========

    def create_data_center(self, center_name: str, education_type: str, center_type: str, **kwargs) -> Dict[str, Any]:
        try:
            center_id = f"dc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO data_center (
                            center_id, center_name, education_type, center_type,
                            school_name, location, rack_count, server_count,
                            storage_capacity, power_capacity, cooling_system,
                            status, created_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, 'planning', ?, ?, ?)
                    ''', (center_id, center_name, education_type, center_type,
                          kwargs.get('school_name'), kwargs.get('location'),
                          kwargs.get('rack_count', 0), kwargs.get('storage_capacity'),
                          kwargs.get('power_capacity'), kwargs.get('cooling_system'),
                          kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建数据中心: {center_name} ({center_id})')
                    return {'success': True, 'center_id': center_id}
        except Exception as e:
            logger.error(f'创建数据中心失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_center_asset(self, center_id: str, asset_type: str, asset_name: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT center_id FROM data_center WHERE center_id = ?', (center_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '数据中心不存在'}
                    cursor.execute('''
                        INSERT INTO center_records (center_id, asset_type, asset_name, serial_number, purchase_date, warranty_expire, status, remarks)
                        VALUES (?, ?, ?, ?, ?, ?, 'active', ?)
                    ''', (center_id, asset_type, asset_name, kwargs.get('serial_number'),
                          kwargs.get('purchase_date', now[:10]), kwargs.get('warranty_expire'), kwargs.get('remarks')))
                    if asset_type == 'server':
                        cursor.execute('UPDATE data_center SET server_count = server_count + 1, updated_at = ? WHERE center_id = ?',
                                     (now, center_id))
                    conn.commit()
                    return {'success': True, 'record_id': cursor.lastrowid}
        except Exception as e:
            logger.error(f'添加数据中心资产失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_center_status(self, center_id: str, status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE data_center SET status = ?, updated_at = ? WHERE center_id = ?',
                                 (status, now, center_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '数据中心不存在'}
        except Exception as e:
            logger.error(f'更新数据中心状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def configure_disaster_recovery(self, center_id: str, strategy: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT center_id FROM data_center WHERE center_id = ?', (center_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '数据中心不存在'}
                    cursor.execute('''
                        INSERT INTO center_records (center_id, asset_type, asset_name, serial_number, purchase_date, warranty_expire, status, remarks)
                        VALUES (?, 'disaster_recovery', ?, ?, ?, ?, 'active', ?)
                    ''', (center_id, strategy, kwargs.get('serial_number'), now[:10],
                          kwargs.get('warranty_expire'), json.dumps({'strategy': strategy, 'details': kwargs})))
                    conn.commit()
                    return {'success': True, 'strategy': strategy}
        except Exception as e:
            logger.error(f'配置灾备方案失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_center_assets(self, center_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM data_center WHERE center_id = ?', (center_id,))
                center = cursor.fetchone()
                if not center:
                    return {'success': False, 'error': '数据中心不存在'}
                cursor.execute('SELECT * FROM center_records WHERE center_id = ?', (center_id,))
                assets = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'center': dict(center), 'assets': assets}
        except Exception as e:
            logger.error(f'获取数据中心资产失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 系统集成 ==========

    def create_integration(self, integration_name: str, education_type: str, integration_type: str, **kwargs) -> Dict[str, Any]:
        try:
            integration_id = f"int_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO system_integration (
                            integration_id, integration_name, education_type,
                            integration_type, school_name, source_system,
                            target_system, description, status, created_by,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'planning', ?, ?, ?)
                    ''', (integration_id, integration_name, education_type, integration_type,
                          kwargs.get('school_name'), kwargs.get('source_system'),
                          kwargs.get('target_system'), kwargs.get('description'),
                          kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建系统集成项目: {integration_name} ({integration_id})')
                    return {'success': True, 'integration_id': integration_id}
        except Exception as e:
            logger.error(f'创建系统集成项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_integration_step(self, integration_id: str, step: str, description: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT integration_id FROM system_integration WHERE integration_id = ?', (integration_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '集成项目不存在'}
                    cursor.execute('''
                        INSERT INTO integration_records (integration_id, step, description, status, completed_at)
                        VALUES (?, ?, ?, 'pending', NULL)
                    ''', (integration_id, step, description))
                    conn.commit()
                    return {'success': True, 'record_id': cursor.lastrowid}
        except Exception as e:
            logger.error(f'添加集成步骤失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_integration_step(self, record_id: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE integration_records SET status = ?, completed_at = ? WHERE id = ?',
                                 ('completed', now[:10], record_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '步骤记录不存在'}
        except Exception as e:
            logger.error(f'完成集成步骤失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_integration_progress(self, integration_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT integration_name, status FROM system_integration WHERE integration_id = ?', (integration_id,))
                integration = cursor.fetchone()
                if not integration:
                    return {'success': False, 'error': '集成项目不存在'}
                cursor.execute('SELECT COUNT(*) FROM integration_records WHERE integration_id = ?', (integration_id,))
                total = cursor.fetchone()[0] or 0
                cursor.execute('SELECT COUNT(*) FROM integration_records WHERE integration_id = ? AND status = ?', (integration_id, 'completed'))
                completed = cursor.fetchone()[0] or 0
                progress = round((completed / total) * 100) if total > 0 else 0
                return {'success': True, 'integration_name': integration[0], 'status': integration[1], 'total_steps': total, 'completed_steps': completed, 'progress': progress}
        except Exception as e:
            logger.error(f'获取集成进度失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 云服务 ==========

    def create_cloud_service(self, service_name: str, education_type: str, service_type: str, **kwargs) -> Dict[str, Any]:
        try:
            service_id = f"cls_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO cloud_services (
                            service_id, service_name, education_type, service_type,
                            school_name, provider, subscription_type,
                            resource_spec, monthly_cost, start_date, end_date,
                            status, created_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
                    ''', (service_id, service_name, education_type, service_type,
                          kwargs.get('school_name'), kwargs.get('provider'),
                          kwargs.get('subscription_type'), kwargs.get('resource_spec'),
                          kwargs.get('monthly_cost', 0), kwargs.get('start_date'),
                          kwargs.get('end_date'), kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建云服务: {service_name} ({service_id})')
                    return {'success': True, 'service_id': service_id}
        except Exception as e:
            logger.error(f'创建云服务失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_service_usage(self, service_id: str, record_type: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT service_id FROM cloud_services WHERE service_id = ?', (service_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '云服务不存在'}
                    cursor.execute('''
                        INSERT INTO service_records (service_id, record_type, usage_data, cost, recorded_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (service_id, record_type, json.dumps(kwargs.get('usage_data', {})),
                          kwargs.get('cost', 0), now[:10]))
                    conn.commit()
                    return {'success': True, 'record_id': cursor.lastrowid}
        except Exception as e:
            logger.error(f'记录云服务使用失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_service_status(self, service_id: str, status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE cloud_services SET status = ?, updated_at = ? WHERE service_id = ?',
                                 (status, now, service_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '云服务不存在'}
        except Exception as e:
            logger.error(f'更新云服务状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_service_usage(self, service_id: str, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT service_name, service_type, provider, monthly_cost FROM cloud_services WHERE service_id = ?', (service_id,))
                service = cursor.fetchone()
                if not service:
                    return {'success': False, 'error': '云服务不存在'}
                query = 'SELECT * FROM service_records WHERE service_id = ?'
                params = [service_id]
                if start_date:
                    query += ' AND recorded_at >= ?'
                    params.append(start_date)
                if end_date:
                    query += ' AND recorded_at <= ?'
                    params.append(end_date)
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                total_cost = sum(r.get('cost', 0) for r in records)
                return {'success': True, 'service': dict(service), 'records': records, 'total_cost': total_cost}
        except Exception as e:
            logger.error(f'获取云服务使用情况失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 安全建设 ==========

    def create_security_project(self, security_name: str, education_type: str, security_level: str, **kwargs) -> Dict[str, Any]:
        try:
            security_id = f"sec_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO security_construction (
                            security_id, security_name, education_type,
                            security_level, school_name, description,
                            compliance_requirement, budget, status, created_by,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'planning', ?, ?, ?)
                    ''', (security_id, security_name, education_type, security_level,
                          kwargs.get('school_name'), kwargs.get('description'),
                          kwargs.get('compliance_requirement'), kwargs.get('budget', 0),
                          kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建安全建设项目: {security_name} ({security_id})')
                    return {'success': True, 'security_id': security_id}
        except Exception as e:
            logger.error(f'创建安全建设项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_security_event(self, security_id: str, event_type: str, severity: str, description: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT security_id FROM security_construction WHERE security_id = ?', (security_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '安全项目不存在'}
                    cursor.execute('''
                        INSERT INTO security_records (security_id, record_type, event_type, severity, description, resolved)
                        VALUES (?, 'event', ?, ?, ?, 0)
                    ''', (security_id, event_type, severity, description))
                    conn.commit()
                    return {'success': True, 'record_id': cursor.lastrowid}
        except Exception as e:
            logger.error(f'添加安全事件失败: {e}')
            return {'success': False, 'error': str(e)}

    def resolve_security_event(self, record_id: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE security_records SET resolved = ?, resolved_at = ? WHERE id = ?',
                                 (1, now[:10], record_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '安全事件不存在'}
        except Exception as e:
            logger.error(f'处理安全事件失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_security_status(self, security_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT security_name, security_level, status FROM security_construction WHERE security_id = ?', (security_id,))
                security = cursor.fetchone()
                if not security:
                    return {'success': False, 'error': '安全项目不存在'}
                cursor.execute('SELECT COUNT(*) FROM security_records WHERE security_id = ? AND resolved = 0', (security_id,))
                unresolved = cursor.fetchone()[0] or 0
                cursor.execute('SELECT COUNT(*) FROM security_records WHERE security_id = ?', (security_id,))
                total = cursor.fetchone()[0] or 0
                return {'success': True, 'security_name': security[0], 'security_level': security[1], 'status': security[2], 'total_events': total, 'unresolved_events': unresolved}
        except Exception as e:
            logger.error(f'获取安全状态失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 运维服务 ==========

    def create_operation_service(self, operation_name: str, education_type: str, operation_type: str, **kwargs) -> Dict[str, Any]:
        try:
            operation_id = f"ops_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO operation_services (
                            operation_id, operation_name, education_type,
                            operation_type, school_name, description,
                            service_level, status, created_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
                    ''', (operation_id, operation_name, education_type, operation_type,
                          kwargs.get('school_name'), kwargs.get('description'),
                          kwargs.get('service_level', 'standard'), kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建运维服务: {operation_name} ({operation_id})')
                    return {'success': True, 'operation_id': operation_id}
        except Exception as e:
            logger.error(f'创建运维服务失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_operation_incident(self, operation_id: str, incident_type: str, title: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT operation_id FROM operation_services WHERE operation_id = ?', (operation_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '运维服务不存在'}
                    cursor.execute('''
                        INSERT INTO operation_records (operation_id, incident_type, title, description, priority, status, assigned_to)
                        VALUES (?, ?, ?, ?, ?, 'open', ?)
                    ''', (operation_id, incident_type, title, kwargs.get('description'),
                          kwargs.get('priority', 'medium'), kwargs.get('assigned_to')))
                    conn.commit()
                    return {'success': True, 'record_id': cursor.lastrowid}
        except Exception as e:
            logger.error(f'创建运维事件失败: {e}')
            return {'success': False, 'error': str(e)}

    def resolve_operation_incident(self, record_id: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE operation_records SET status = ?, resolved_at = ? WHERE id = ?',
                                 ('resolved', now[:10], record_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '运维事件不存在'}
        except Exception as e:
            logger.error(f'处理运维事件失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_operation_stats(self, operation_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT operation_name, operation_type, service_level, status FROM operation_services WHERE operation_id = ?', (operation_id,))
                operation = cursor.fetchone()
                if not operation:
                    return {'success': False, 'error': '运维服务不存在'}
                cursor.execute('SELECT COUNT(*) FROM operation_records WHERE operation_id = ?', (operation_id,))
                total = cursor.fetchone()[0] or 0
                cursor.execute('SELECT COUNT(*) FROM operation_records WHERE operation_id = ? AND status = ?', (operation_id, 'resolved'))
                resolved = cursor.fetchone()[0] or 0
                cursor.execute('SELECT COUNT(*) FROM operation_records WHERE operation_id = ? AND status = ?', (operation_id, 'open'))
                open_count = cursor.fetchone()[0] or 0
                return {'success': True, 'operation_name': operation[0], 'operation_type': operation[1], 'service_level': operation[2], 'status': operation[3], 'total_incidents': total, 'resolved_incidents': resolved, 'open_incidents': open_count}
        except Exception as e:
            logger.error(f'获取运维统计失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 ==========

    def get_overall_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                filters = []
                params = []
                if education_type:
                    filters.append('education_type = ?')
                    params.append(education_type)
                where_clause = 'WHERE ' + ' AND '.join(filters) if filters else ''

                stats = {}

                cursor.execute(f'SELECT COUNT(*) FROM infrastructure_planning {where_clause}', params)
                stats['planning_count'] = cursor.fetchone()[0] or 0

                cursor.execute(f'SELECT COUNT(*) FROM infrastructure_construction {where_clause}', params)
                stats['construction_count'] = cursor.fetchone()[0] or 0

                cursor.execute(f'SELECT COUNT(*) FROM network_construction {where_clause}', params)
                stats['network_count'] = cursor.fetchone()[0] or 0

                cursor.execute(f'SELECT COUNT(*) FROM data_center {where_clause}', params)
                stats['data_center_count'] = cursor.fetchone()[0] or 0

                cursor.execute(f'SELECT COUNT(*) FROM system_integration {where_clause}', params)
                stats['integration_count'] = cursor.fetchone()[0] or 0

                cursor.execute(f'SELECT COUNT(*) FROM cloud_services {where_clause}', params)
                stats['cloud_service_count'] = cursor.fetchone()[0] or 0

                cursor.execute(f'SELECT COUNT(*) FROM security_construction {where_clause}', params)
                stats['security_count'] = cursor.fetchone()[0] or 0

                cursor.execute(f'SELECT COUNT(*) FROM operation_services {where_clause}', params)
                stats['operation_count'] = cursor.fetchone()[0] or 0

                cursor.execute(f'SELECT COALESCE(SUM(budget), 0) FROM infrastructure_planning {where_clause}', params)
                stats['total_planning_budget'] = cursor.fetchone()[0] or 0

                cursor.execute(f'SELECT COALESCE(SUM(budget), 0) FROM infrastructure_construction {where_clause}', params)
                stats['total_construction_budget'] = cursor.fetchone()[0] or 0

                cursor.execute(f'SELECT COALESCE(SUM(budget), 0) FROM security_construction {where_clause}', params)
                stats['total_security_budget'] = cursor.fetchone()[0] or 0

                cursor.execute(f'SELECT COALESCE(SUM(monthly_cost), 0) FROM cloud_services {where_clause}', params)
                stats['total_cloud_monthly_cost'] = cursor.fetchone()[0] or 0

                stats['education_type'] = education_type or 'all'
                stats['generated_at'] = datetime.now().isoformat()

                return {'success': True, 'statistics': stats}
        except Exception as e:
            logger.error(f'获取统计信息失败: {e}')
            return {'success': False, 'error': str(e)}