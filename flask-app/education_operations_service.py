#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育运营保障服务 (v15.18.0)
====================================
提供服务级别管理、故障管理、性能监控、容量管理、变更管理、配置管理、发布管理和服务连续性等综合运营保障服务。

核心能力：
1. 服务级别管理 - SLA定义、服务等级协议、服务水平监控
2. 故障管理 - 事件登记、故障处理、恢复跟踪
3. 性能监控 - 指标采集、告警管理、性能分析
4. 容量管理 - 资源预测、容量评估、扩展策略
5. 变更管理 - 变更请求、审批流程、变更实施
6. 配置管理 - 配置项管理、配置追踪、配置审计
7. 发布管理 - 版本发布、部署管理、回滚机制
8. 服务连续性 - 业务影响分析、灾难恢复、冗余设计
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_operations_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationOperations')


# ========== 服务配置 ==========

# 服务级别
SERVICE_LEVELS = {
    'basic': {'name': '基础服务', 'availability': '99.0%', 'response_time': '4小时', 'priority': 4},
    'standard': {'name': '标准服务', 'availability': '99.5%', 'response_time': '2小时', 'priority': 3},
    'advanced': {'name': '高级服务', 'availability': '99.9%', 'response_time': '1小时', 'priority': 2},
    'premium': {'name': '卓越服务', 'availability': '99.95%', 'response_time': '30分钟', 'priority': 1},
    'custom': {'name': '定制服务', 'availability': '定制', 'response_time': '定制', 'priority': 0}
}

# 服务类别
SERVICE_CATEGORIES = {
    'teaching': {'name': '教学服务', 'education_types': ['adult', 'k12']},
    'learning': {'name': '学习服务', 'education_types': ['adult', 'k12']},
    'management': {'name': '管理服务', 'education_types': ['adult', 'k12']},
    'technical': {'name': '技术服务', 'education_types': ['adult', 'k12']},
    'logistics': {'name': '后勤服务', 'education_types': ['adult', 'k12']},
    'security': {'name': '安全服务', 'education_types': ['adult', 'k12']},
    'finance': {'name': '财务服务', 'education_types': ['adult', 'k12']},
    'hr': {'name': '人事服务', 'education_types': ['adult', 'k12']}
}

# 故障类型
INCIDENT_TYPES = {
    'system': {'name': '系统故障', 'default_severity': 'high'},
    'network': {'name': '网络故障', 'default_severity': 'high'},
    'data': {'name': '数据故障', 'default_severity': 'critical'},
    'security': {'name': '安全事件', 'default_severity': 'critical'},
    'performance': {'name': '性能问题', 'default_severity': 'medium'},
    'function': {'name': '功能异常', 'default_severity': 'medium'},
    'configuration': {'name': '配置错误', 'default_severity': 'low'},
    'human': {'name': '人为失误', 'default_severity': 'medium'}
}

# 严重级别
SEVERITY_LEVELS = {
    'minor': {'name': '轻微', 'color': 'green', 'response_time': '24小时'},
    'medium': {'name': '一般', 'color': 'yellow', 'response_time': '8小时'},
    'high': {'name': '严重', 'color': 'orange', 'response_time': '4小时'},
    'critical': {'name': '紧急', 'color': 'red', 'response_time': '1小时'},
    'disaster': {'name': '灾难', 'color': 'purple', 'response_time': '立即'}
}

# 监控指标
MONITORING_METRICS = {
    'availability': {'name': '可用性', 'unit': '%', 'threshold': 99.0},
    'response_time': {'name': '响应时间', 'unit': 'ms', 'threshold': 500},
    'throughput': {'name': '吞吐量', 'unit': 'req/s', 'threshold': None},
    'concurrency': {'name': '并发数', 'unit': '', 'threshold': None},
    'error_rate': {'name': '错误率', 'unit': '%', 'threshold': 1.0},
    'resource_usage': {'name': '资源使用率', 'unit': '%', 'threshold': 80},
    'data_integrity': {'name': '数据完整性', 'unit': '%', 'threshold': 100},
    'user_satisfaction': {'name': '用户满意度', 'unit': '分', 'threshold': 80}
}

# 容量规划
CAPACITY_PLANNING = {
    'forecast': {'name': '资源预测', 'periods': ['week', 'month', 'quarter', 'year']},
    'evaluation': {'name': '容量评估', 'methods': ['trend', 'simulation', 'benchmark']},
    'scaling': {'name': '扩展策略', 'types': ['horizontal', 'vertical', 'hybrid']},
    'optimization': {'name': '资源优化', 'techniques': ['right-sizing', 'consolidation', 'automation']},
    'load_balancing': {'name': '负载均衡', 'algorithms': ['round-robin', 'least-connections', 'ip-hash']},
    'elasticity': {'name': '弹性伸缩', 'triggers': ['cpu', 'memory', 'queue', 'custom']},
    'cost_control': {'name': '成本控制', 'strategies': ['reserved', 'spot', 'on-demand']},
    'tuning': {'name': '性能调优', 'areas': ['database', 'cache', 'network', 'code']}
}

# 变更类型
CHANGE_TYPES = {
    'emergency': {'name': '紧急变更', 'approval_required': False, 'risk_level': 'high'},
    'standard': {'name': '标准变更', 'approval_required': True, 'risk_level': 'low'},
    'major': {'name': '重大变更', 'approval_required': True, 'risk_level': 'critical'},
    'routine': {'name': '日常变更', 'approval_required': False, 'risk_level': 'low'},
    'configuration': {'name': '配置变更', 'approval_required': True, 'risk_level': 'medium'},
    'data': {'name': '数据变更', 'approval_required': True, 'risk_level': 'high'},
    'architecture': {'name': '架构变更', 'approval_required': True, 'risk_level': 'critical'},
    'security': {'name': '安全变更', 'approval_required': True, 'risk_level': 'high'}
}

# 连续性规划
CONTINUITY_PLANNING = {
    'bia': {'name': '业务影响分析', 'factors': ['criticality', 'recovery_time', 'financial_impact']},
    'risk_assessment': {'name': '风险评估', 'methods': ['qualitative', 'quantitative']},
    'recovery_strategy': {'name': '恢复策略', 'approaches': ['hot', 'warm', 'cold']},
    'disaster_recovery': {'name': '灾难恢复', 'metrics': ['RTO', 'RPO', 'MTTR']},
    'redundancy': {'name': '冗余设计', 'levels': ['active-active', 'active-passive', 'n+1']},
    'failover': {'name': '故障转移', 'types': ['automatic', 'manual', 'scheduled']},
    'backup': {'name': '备份策略', 'methods': ['full', 'incremental', 'differential']},
    'drill': {'name': '演练计划', 'frequency': ['monthly', 'quarterly', 'biannually', 'annually']}
}


class EducationOperationsService:
    """教育运营保障服务"""

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
                    CREATE TABLE IF NOT EXISTS service_levels (
                        service_id TEXT PRIMARY KEY,
                        service_name TEXT NOT NULL,
                        service_category TEXT,
                        service_level TEXT,
                        education_type TEXT,
                        availability_target REAL,
                        response_time TEXT,
                        priority INTEGER,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sla_agreements (
                        sla_id TEXT PRIMARY KEY,
                        service_id TEXT NOT NULL,
                        education_type TEXT,
                        availability_guarantee REAL,
                        response_time_guarantee TEXT,
                        resolution_time_guarantee TEXT,
                        penalties TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY(service_id) REFERENCES service_levels(service_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS incident_management (
                        incident_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        incident_type TEXT,
                        severity TEXT,
                        education_type TEXT,
                        service_id TEXT,
                        description TEXT,
                        reporter_id INTEGER,
                        reporter_name TEXT,
                        assignee_id INTEGER,
                        assignee_name TEXT,
                        status TEXT DEFAULT 'open',
                        impact TEXT,
                        urgency TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        resolved_at TEXT,
                        FOREIGN KEY(service_id) REFERENCES service_levels(service_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS incident_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        incident_id TEXT NOT NULL,
                        action TEXT,
                        actor_id INTEGER,
                        actor_name TEXT,
                        status_before TEXT,
                        status_after TEXT,
                        comment TEXT,
                        created_at TEXT,
                        FOREIGN KEY(incident_id) REFERENCES incident_management(incident_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS performance_monitoring (
                        monitor_id TEXT PRIMARY KEY,
                        service_id TEXT,
                        education_type TEXT,
                        metric_type TEXT,
                        threshold REAL,
                        alert_enabled INTEGER DEFAULT 1,
                        alert_level TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY(service_id) REFERENCES service_levels(service_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS monitoring_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        monitor_id TEXT NOT NULL,
                        timestamp TEXT,
                        value REAL,
                        unit TEXT,
                        is_alert INTEGER DEFAULT 0,
                        FOREIGN KEY(monitor_id) REFERENCES performance_monitoring(monitor_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS capacity_management (
                        capacity_id TEXT PRIMARY KEY,
                        resource_type TEXT,
                        education_type TEXT,
                        current_capacity REAL,
                        used_capacity REAL,
                        peak_capacity REAL,
                        threshold REAL,
                        forecast_method TEXT,
                        status TEXT DEFAULT 'normal',
                        description TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS capacity_plans (
                        plan_id TEXT PRIMARY KEY,
                        capacity_id TEXT,
                        plan_name TEXT,
                        education_type TEXT,
                        scaling_strategy TEXT,
                        target_capacity REAL,
                        implementation_date TEXT,
                        estimated_cost REAL,
                        status TEXT DEFAULT 'planned',
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY(capacity_id) REFERENCES capacity_management(capacity_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS change_management (
                        change_id TEXT PRIMARY KEY,
                        change_type TEXT,
                        education_type TEXT,
                        service_id TEXT,
                        title TEXT NOT NULL,
                        description TEXT,
                        risk_level TEXT,
                        priority TEXT,
                        requester_id INTEGER,
                        requester_name TEXT,
                        status TEXT DEFAULT 'pending',
                        approval_status TEXT DEFAULT 'pending',
                        planned_start TEXT,
                        planned_end TEXT,
                        actual_start TEXT,
                        actual_end TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY(service_id) REFERENCES service_levels(service_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS change_requests (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        change_id TEXT NOT NULL,
                        approver_id INTEGER,
                        approver_name TEXT,
                        approval_action TEXT,
                        approval_comment TEXT,
                        approved_at TEXT,
                        FOREIGN KEY(change_id) REFERENCES change_management(change_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS configuration_items (
                        config_id TEXT PRIMARY KEY,
                        item_name TEXT NOT NULL,
                        item_type TEXT,
                        education_type TEXT,
                        service_id TEXT,
                        current_value TEXT,
                        previous_value TEXT,
                        owner_id INTEGER,
                        owner_name TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY(service_id) REFERENCES service_levels(service_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS config_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        config_id TEXT NOT NULL,
                        change_type TEXT,
                        old_value TEXT,
                        new_value TEXT,
                        changed_by_id INTEGER,
                        changed_by_name TEXT,
                        change_reason TEXT,
                        created_at TEXT,
                        FOREIGN KEY(config_id) REFERENCES configuration_items(config_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS release_management (
                        release_id TEXT PRIMARY KEY,
                        release_name TEXT NOT NULL,
                        education_type TEXT,
                        service_id TEXT,
                        version TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'planned',
                        release_date TEXT,
                        deployed_at TEXT,
                        rollback_plan TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY(service_id) REFERENCES service_levels(service_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS release_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        release_id TEXT NOT NULL,
                        environment TEXT,
                        status TEXT,
                        started_at TEXT,
                        completed_at TEXT,
                        result TEXT,
                        rollback_executed INTEGER DEFAULT 0,
                        FOREIGN KEY(release_id) REFERENCES release_management(release_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS service_continuity (
                        continuity_id TEXT PRIMARY KEY,
                        service_id TEXT,
                        education_type TEXT,
                        business_criticality TEXT,
                        impact_level TEXT,
                        recovery_time_objective TEXT,
                        recovery_point_objective TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY(service_id) REFERENCES service_levels(service_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS continuity_plans (
                        plan_id TEXT PRIMARY KEY,
                        continuity_id TEXT,
                        plan_name TEXT,
                        education_type TEXT,
                        recovery_strategy TEXT,
                        redundancy_level TEXT,
                        failover_type TEXT,
                        backup_method TEXT,
                        drill_frequency TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY(continuity_id) REFERENCES service_continuity(continuity_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS disaster_recovery (
                        dr_id TEXT PRIMARY KEY,
                        continuity_id TEXT,
                        education_type TEXT,
                        recovery_site TEXT,
                        recovery_type TEXT,
                        rto_target TEXT,
                        rpo_target TEXT,
                        mttr_target TEXT,
                        last_tested TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY(continuity_id) REFERENCES service_continuity(continuity_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS recovery_tests (
                        test_id TEXT PRIMARY KEY,
                        dr_id TEXT,
                        education_type TEXT,
                        test_type TEXT,
                        test_date TEXT,
                        test_results TEXT,
                        issues_found TEXT,
                        status TEXT DEFAULT 'completed',
                        created_at TEXT,
                        FOREIGN KEY(dr_id) REFERENCES disaster_recovery(dr_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS service_catalog (
                        catalog_id TEXT PRIMARY KEY,
                        catalog_name TEXT NOT NULL,
                        education_type TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS catalog_items (
                        item_id TEXT PRIMARY KEY,
                        catalog_id TEXT NOT NULL,
                        service_id TEXT,
                        education_type TEXT,
                        item_name TEXT NOT NULL,
                        item_description TEXT,
                        service_level TEXT,
                        price REAL DEFAULT 0,
                        status TEXT DEFAULT 'available',
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY(catalog_id) REFERENCES service_catalog(catalog_id),
                        FOREIGN KEY(service_id) REFERENCES service_levels(service_id)
                    )
                ''')
                conn.commit()
                logger.info('教育运营保障服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 服务级别管理 ==========

    def create_service_level(self, service_name: str, service_category: str,
                             service_level: str, education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            service_id = f"svc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = SERVICE_LEVELS.get(service_level, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO service_levels (
                            service_id, service_name, service_category,
                            service_level, education_type, availability_target,
                            response_time, priority, description, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (service_id, service_name, service_category,
                          service_level, education_type,
                          float(config.get('availability', '99.0').replace('%', '')),
                          config.get('response_time', '4小时'),
                          config.get('priority', 4), kwargs.get('description'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建服务级别: {service_name} ({service_id})')
                    return {'success': True, 'service_id': service_id}
        except Exception as e:
            logger.error(f'创建服务级别失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_sla_agreement(self, service_id: str, education_type: str,
                             **kwargs) -> Dict[str, Any]:
        try:
            sla_id = f"sla_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT service_level FROM service_levels WHERE service_id = ?', (service_id,))
                    service = cursor.fetchone()
                    if not service:
                        return {'success': False, 'error': '服务不存在'}
                    config = SERVICE_LEVELS.get(service[0], {})
                    cursor.execute('''
                        INSERT INTO sla_agreements (
                            sla_id, service_id, education_type,
                            availability_guarantee, response_time_guarantee,
                            resolution_time_guarantee, penalties, start_date,
                            end_date, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (sla_id, service_id, education_type,
                          kwargs.get('availability_guarantee', float(config.get('availability', '99.0').replace('%', ''))),
                          kwargs.get('response_time_guarantee', config.get('response_time', '4小时')),
                          kwargs.get('resolution_time_guarantee', '24小时'),
                          kwargs.get('penalties'), kwargs.get('start_date', now[:10]),
                          kwargs.get('end_date'), now, now))
                    conn.commit()
                    return {'success': True, 'sla_id': sla_id}
        except Exception as e:
            logger.error(f'创建SLA协议失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_service_levels(self, education_type: str = None, service_category: str = None,
                           page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM service_levels WHERE status = ?'
                params = ['active']
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if service_category:
                    query += ' AND service_category = ?'
                    params.append(service_category)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY priority ASC, created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                services = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'services': services, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取服务级别列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_sla_status(self, service_id: str, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM sla_agreements WHERE service_id = ? AND status = ?'
                params = [service_id, 'active']
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                sla = cursor.fetchone()
                if not sla:
                    return {'success': False, 'error': '未找到有效的SLA协议'}
                return {'success': True, 'sla': dict(sla)}
        except Exception as e:
            logger.error(f'获取SLA状态失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 故障管理 ==========

    def create_incident(self, title: str, incident_type: str, education_type: str,
                        reporter_id: int, **kwargs) -> Dict[str, Any]:
        try:
            incident_id = f"inc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = INCIDENT_TYPES.get(incident_type, {})
            severity = kwargs.get('severity', config.get('default_severity', 'medium'))
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO incident_management (
                            incident_id, title, incident_type, severity,
                            education_type, service_id, description,
                            reporter_id, reporter_name, assignee_id,
                            assignee_name, status, impact, urgency,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?, ?, ?, ?)
                    ''', (incident_id, title, incident_type, severity,
                          education_type, kwargs.get('service_id'),
                          kwargs.get('description'), reporter_id,
                          kwargs.get('reporter_name'), kwargs.get('assignee_id'),
                          kwargs.get('assignee_name'), kwargs.get('impact'),
                          kwargs.get('urgency'), now, now))
                    cursor.execute('''
                        INSERT INTO incident_history (incident_id, action, actor_id, actor_name,
                            status_before, status_after, comment, created_at)
                        VALUES (?, 'created', ?, ?, NULL, 'open', ?, ?)
                    ''', (incident_id, reporter_id, kwargs.get('reporter_name'),
                          kwargs.get('description'), now))
                    conn.commit()
                    logger.info(f'创建故障事件: {title} ({incident_id})')
                    return {'success': True, 'incident_id': incident_id}
        except Exception as e:
            logger.error(f'创建故障事件失败: {e}')
            return {'success': False, 'error': str(e)}

    def assign_incident(self, incident_id: str, assignee_id: int,
                        assignee_name: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM incident_management WHERE incident_id = ?', (incident_id,))
                    incident = cursor.fetchone()
                    if not incident:
                        return {'success': False, 'error': '故障事件不存在'}
                    cursor.execute('''
                        UPDATE incident_management SET assignee_id = ?, assignee_name = ?,
                            status = 'assigned', updated_at = ? WHERE incident_id = ?
                    ''', (assignee_id, assignee_name, now, incident_id))
                    cursor.execute('''
                        INSERT INTO incident_history (incident_id, action, actor_id, actor_name,
                            status_before, status_after, comment, created_at)
                        VALUES (?, 'assigned', ?, ?, ?, 'assigned', ?, ?)
                    ''', (incident_id, assignee_id, assignee_name, incident[0], now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'分配故障事件失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_incident_status(self, incident_id: str, status: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM incident_management WHERE incident_id = ?', (incident_id,))
                    incident = cursor.fetchone()
                    if not incident:
                        return {'success': False, 'error': '故障事件不存在'}
                    old_status = incident[0]
                    update_fields = {'status': status, 'updated_at': now}
                    if status == 'resolved':
                        update_fields['resolved_at'] = now
                    set_clause = ', '.join([f'{k} = ?' for k in update_fields.keys()])
                    params = list(update_fields.values()) + [incident_id]
                    cursor.execute(f'UPDATE incident_management SET {set_clause} WHERE incident_id = ?', params)
                    cursor.execute('''
                        INSERT INTO incident_history (incident_id, action, actor_id, actor_name,
                            status_before, status_after, comment, created_at)
                        VALUES (?, 'status_update', ?, ?, ?, ?, ?, ?)
                    ''', (incident_id, kwargs.get('actor_id'), kwargs.get('actor_name'),
                          old_status, status, kwargs.get('comment'), now))
                    conn.commit()
                    return {'success': True, 'status': status}
        except Exception as e:
            logger.error(f'更新故障状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_incident_comment(self, incident_id: str, comment: str,
                             actor_id: int, actor_name: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM incident_management WHERE incident_id = ?', (incident_id,))
                    incident = cursor.fetchone()
                    if not incident:
                        return {'success': False, 'error': '故障事件不存在'}
                    cursor.execute('''
                        INSERT INTO incident_history (incident_id, action, actor_id, actor_name,
                            status_before, status_after, comment, created_at)
                        VALUES (?, 'comment', ?, ?, ?, ?, ?, ?)
                    ''', (incident_id, actor_id, actor_name, incident[0], incident[0], comment, now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加故障评论失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_incidents(self, education_type: str = None, status: str = None,
                      severity: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM incident_management WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                if severity:
                    query += ' AND severity = ?'
                    params.append(severity)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY CASE severity WHEN "disaster" THEN 1 WHEN "critical" THEN 2 WHEN "high" THEN 3 WHEN "medium" THEN 4 ELSE 5 END, created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                incidents = [dict(i) for i in cursor.fetchall()]
                return {'success': True, 'incidents': incidents, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取故障列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 性能监控 ==========

    def create_monitor(self, service_id: str, metric_type: str, education_type: str,
                       **kwargs) -> Dict[str, Any]:
        try:
            monitor_id = f"mon_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = MONITORING_METRICS.get(metric_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO performance_monitoring (
                            monitor_id, service_id, education_type,
                            metric_type, threshold, alert_enabled,
                            alert_level, description, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (monitor_id, service_id, education_type, metric_type,
                          kwargs.get('threshold', config.get('threshold')),
                          kwargs.get('alert_enabled', 1),
                          kwargs.get('alert_level', 'warning'),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建监控项: {metric_type} ({monitor_id})')
                    return {'success': True, 'monitor_id': monitor_id}
        except Exception as e:
            logger.error(f'创建监控项失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_metric_data(self, monitor_id: str, value: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT threshold, alert_enabled FROM performance_monitoring WHERE monitor_id = ?', (monitor_id,))
                    monitor = cursor.fetchone()
                    if not monitor:
                        return {'success': False, 'error': '监控项不存在'}
                    is_alert = 0
                    if monitor[1] and monitor[0] is not None:
                        metric_config = MONITORING_METRICS.get(monitor[0], {})
                        if metric_type in ['availability', 'data_integrity', 'user_satisfaction']:
                            is_alert = 1 if value < monitor[0] else 0
                        else:
                            is_alert = 1 if value > monitor[0] else 0
                    cursor.execute('''
                        INSERT INTO monitoring_data (monitor_id, timestamp, value, unit, is_alert)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (monitor_id, now, value, kwargs.get('unit', ''), is_alert))
                    conn.commit()
                    return {'success': True, 'is_alert': is_alert}
        except Exception as e:
            logger.error(f'记录监控数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_metric_data(self, monitor_id: str, start_time: str = None,
                        end_time: str = None, limit: int = 100) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM monitoring_data WHERE monitor_id = ?'
                params = [monitor_id]
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
            logger.error(f'获取监控数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_monitor_alerts(self, education_type: str = None, limit: int = 50) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = '''
                    SELECT md.*, pm.metric_type, pm.service_id
                    FROM monitoring_data md
                    JOIN performance_monitoring pm ON md.monitor_id = pm.monitor_id
                    WHERE md.is_alert = 1
                '''
                params = []
                if education_type:
                    query += ' AND pm.education_type = ?'
                    params.append(education_type)
                query += ' ORDER BY md.timestamp DESC LIMIT ?'
                params.append(limit)
                cursor.execute(query, params)
                alerts = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'alerts': alerts}
        except Exception as e:
            logger.error(f'获取监控告警失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 容量管理 ==========

    def create_capacity_plan(self, resource_type: str, education_type: str,
                             **kwargs) -> Dict[str, Any]:
        try:
            capacity_id = f"cap_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO capacity_management (
                            capacity_id, resource_type, education_type,
                            current_capacity, used_capacity, peak_capacity,
                            threshold, forecast_method, status, description,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'normal', ?, ?, ?)
                    ''', (capacity_id, resource_type, education_type,
                          kwargs.get('current_capacity', 0),
                          kwargs.get('used_capacity', 0),
                          kwargs.get('peak_capacity', 0),
                          kwargs.get('threshold', 80),
                          kwargs.get('forecast_method', 'trend'),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建容量管理: {resource_type} ({capacity_id})')
                    return {'success': True, 'capacity_id': capacity_id}
        except Exception as e:
            logger.error(f'创建容量管理失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_capacity_usage(self, capacity_id: str, used_capacity: float,
                              **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT current_capacity, threshold FROM capacity_management WHERE capacity_id = ?', (capacity_id,))
                    capacity = cursor.fetchone()
                    if not capacity:
                        return {'success': False, 'error': '容量管理不存在'}
                    usage_percent = (used_capacity / capacity[0]) * 100 if capacity[0] > 0 else 0
                    status = 'normal' if usage_percent < capacity[1] else ('warning' if usage_percent < 90 else 'critical')
                    cursor.execute('''
                        UPDATE capacity_management SET used_capacity = ?, peak_capacity = ?,
                            status = ?, updated_at = ? WHERE capacity_id = ?
                    ''', (used_capacity, max(capacity[1], used_capacity) if kwargs.get('is_peak') else capacity[1],
                          status, now, capacity_id))
                    conn.commit()
                    return {'success': True, 'status': status, 'usage_percent': round(usage_percent, 2)}
        except Exception as e:
            logger.error(f'更新容量使用失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_scaling_plan(self, capacity_id: str, plan_name: str,
                            education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            plan_id = f"scp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO capacity_plans (
                            plan_id, capacity_id, plan_name, education_type,
                            scaling_strategy, target_capacity,
                            implementation_date, estimated_cost, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'planned', ?, ?)
                    ''', (plan_id, capacity_id, plan_name, education_type,
                          kwargs.get('scaling_strategy', 'horizontal'),
                          kwargs.get('target_capacity', 0),
                          kwargs.get('implementation_date'),
                          kwargs.get('estimated_cost', 0), now, now))
                    conn.commit()
                    return {'success': True, 'plan_id': plan_id}
        except Exception as e:
            logger.error(f'创建扩展计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_capacity_status(self, education_type: str = None,
                            resource_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM capacity_management WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if resource_type:
                    query += ' AND resource_type = ?'
                    params.append(resource_type)
                cursor.execute(query, params)
                capacities = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'capacities': capacities}
        except Exception as e:
            logger.error(f'获取容量状态失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 变更管理 ==========

    def create_change_request(self, change_type: str, title: str, education_type: str,
                              requester_id: int, **kwargs) -> Dict[str, Any]:
        try:
            change_id = f"chg_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = CHANGE_TYPES.get(change_type, {})
            approval_required = config.get('approval_required', True)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO change_management (
                            change_id, change_type, education_type,
                            service_id, title, description, risk_level,
                            priority, requester_id, requester_name, status,
                            approval_status, planned_start, planned_end,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (change_id, change_type, education_type,
                          kwargs.get('service_id'), title, kwargs.get('description'),
                          config.get('risk_level', 'medium'), kwargs.get('priority', 'medium'),
                          requester_id, kwargs.get('requester_name'),
                          'pending', 'approved' if not approval_required else 'pending',
                          kwargs.get('planned_start'), kwargs.get('planned_end'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建变更请求: {title} ({change_id})')
                    return {'success': True, 'change_id': change_id}
        except Exception as e:
            logger.error(f'创建变更请求失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_change(self, change_id: str, approver_id: int,
                       approver_name: str, approved: bool, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            approval_action = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT approval_status FROM change_management WHERE change_id = ?', (change_id,))
                    change = cursor.fetchone()
                    if not change:
                        return {'success': False, 'error': '变更请求不存在'}
                    if change[0] != 'pending':
                        return {'success': False, 'error': '变更请求已处理'}
                    cursor.execute('''
                        UPDATE change_management SET approval_status = ?,
                            status = ?, updated_at = ? WHERE change_id = ?
                    ''', (approval_action, 'approved' if approved else 'rejected', now, change_id))
                    cursor.execute('''
                        INSERT INTO change_requests (change_id, approver_id, approver_name,
                            approval_action, approval_comment, approved_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (change_id, approver_id, approver_name, approval_action,
                          kwargs.get('comment'), now))
                    conn.commit()
                    return {'success': True, 'approval_status': approval_action}
        except Exception as e:
            logger.error(f'审批变更请求失败: {e}')
            return {'success': False, 'error': str(e)}

    def implement_change(self, change_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT approval_status, status FROM change_management WHERE change_id = ?', (change_id,))
                    change = cursor.fetchone()
                    if not change:
                        return {'success': False, 'error': '变更请求不存在'}
                    if change[0] != 'approved':
                        return {'success': False, 'error': '变更请求未通过审批'}
                    cursor.execute('''
                        UPDATE change_management SET status = 'in_progress',
                            actual_start = ?, updated_at = ? WHERE change_id = ?
                    ''', (now, now, change_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'实施变更失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_change(self, change_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM change_management WHERE change_id = ?', (change_id,))
                    change = cursor.fetchone()
                    if not change:
                        return {'success': False, 'error': '变更请求不存在'}
                    if change[0] != 'in_progress':
                        return {'success': False, 'error': '变更未在实施中'}
                    cursor.execute('''
                        UPDATE change_management SET status = 'completed',
                            actual_end = ?, updated_at = ? WHERE change_id = ?
                    ''', (now, now, change_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'完成变更失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 配置管理 ==========

    def create_config_item(self, item_name: str, item_type: str, education_type: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            config_id = f"cfg_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO configuration_items (
                            config_id, item_name, item_type, education_type,
                            service_id, current_value, previous_value,
                            owner_id, owner_name, description, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, 'active', ?, ?)
                    ''', (config_id, item_name, item_type, education_type,
                          kwargs.get('service_id'), kwargs.get('current_value'),
                          kwargs.get('owner_id'), kwargs.get('owner_name'),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建配置项: {item_name} ({config_id})')
                    return {'success': True, 'config_id': config_id}
        except Exception as e:
            logger.error(f'创建配置项失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_config_item(self, config_id: str, current_value: str,
                           changed_by_id: int, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT current_value FROM configuration_items WHERE config_id = ?', (config_id,))
                    config = cursor.fetchone()
                    if not config:
                        return {'success': False, 'error': '配置项不存在'}
                    old_value = config[0]
                    cursor.execute('''
                        UPDATE configuration_items SET previous_value = ?,
                            current_value = ?, updated_at = ? WHERE config_id = ?
                    ''', (old_value, current_value, now, config_id))
                    cursor.execute('''
                        INSERT INTO config_history (config_id, change_type, old_value,
                            new_value, changed_by_id, changed_by_name,
                            change_reason, created_at)
                        VALUES (?, 'update', ?, ?, ?, ?, ?, ?)
                    ''', (config_id, old_value, current_value, changed_by_id,
                          kwargs.get('changed_by_name'), kwargs.get('change_reason'), now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'更新配置项失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_config_history(self, config_id: str, limit: int = 50) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM config_history WHERE config_id = ?
                    ORDER BY created_at DESC LIMIT ?
                ''', (config_id, limit))
                history = [dict(h) for h in cursor.fetchall()]
                return {'success': True, 'history': history}
        except Exception as e:
            logger.error(f'获取配置历史失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_config_items(self, education_type: str = None, item_type: str = None,
                         service_id: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM configuration_items WHERE status = ?'
                params = ['active']
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if item_type:
                    query += ' AND item_type = ?'
                    params.append(item_type)
                if service_id:
                    query += ' AND service_id = ?'
                    params.append(service_id)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(i) for i in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取配置项列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 发布管理 ==========

    def create_release(self, release_name: str, education_type: str,
                       version: str, **kwargs) -> Dict[str, Any]:
        try:
            release_id = f"rel_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO release_management (
                            release_id, release_name, education_type,
                            service_id, version, description, status,
                            release_date, rollback_plan, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'planned', ?, ?, ?, ?)
                    ''', (release_id, release_name, education_type,
                          kwargs.get('service_id'), version, kwargs.get('description'),
                          kwargs.get('release_date'), kwargs.get('rollback_plan'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建发布版本: {release_name} v{version} ({release_id})')
                    return {'success': True, 'release_id': release_id}
        except Exception as e:
            logger.error(f'创建发布版本失败: {e}')
            return {'success': False, 'error': str(e)}

    def deploy_release(self, release_id: str, environment: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM release_management WHERE release_id = ?', (release_id,))
                    release = cursor.fetchone()
                    if not release:
                        return {'success': False, 'error': '发布版本不存在'}
                    cursor.execute('''
                        INSERT INTO release_records (release_id, environment, status,
                            started_at) VALUES (?, ?, 'deploying', ?)
                    ''', (release_id, environment, now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'部署发布失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_deployment(self, release_id: str, environment: str,
                            result: str = 'success') -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE release_records SET status = ?, completed_at = ?, result = ?
                        WHERE release_id = ? AND environment = ? AND status = 'deploying'
                    ''', (result, now, result, release_id, environment))
                    if cursor.rowcount == 0:
                        return {'success': False, 'error': '未找到部署记录'}
                    if result == 'success':
                        cursor.execute('''
                            UPDATE release_management SET status = 'deployed',
                                deployed_at = ?, updated_at = ? WHERE release_id = ?
                        ''', (now, now, release_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'完成部署失败: {e}')
            return {'success': False, 'error': str(e)}

    def rollback_release(self, release_id: str, environment: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT rollback_plan FROM release_management WHERE release_id = ?', (release_id,))
                    release = cursor.fetchone()
                    if not release:
                        return {'success': False, 'error': '发布版本不存在'}
                    cursor.execute('''
                        UPDATE release_records SET status = 'rolled_back',
                            completed_at = ?, result = 'rollback',
                            rollback_executed = 1
                        WHERE release_id = ? AND environment = ?
                    ''', (now, release_id, environment))
                    cursor.execute('''
                        UPDATE release_management SET status = 'rolled_back',
                            updated_at = ? WHERE release_id = ?
                    ''', (now, release_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'回滚发布失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 服务连续性 ==========

    def create_continuity_plan(self, service_id: str, education_type: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            continuity_id = f"cty_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO service_continuity (
                            continuity_id, service_id, education_type,
                            business_criticality, impact_level,
                            recovery_time_objective, recovery_point_objective,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (continuity_id, service_id, education_type,
                          kwargs.get('business_criticality', 'high'),
                          kwargs.get('impact_level', 'high'),
                          kwargs.get('recovery_time_objective', '4小时'),
                          kwargs.get('recovery_point_objective', '15分钟'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建服务连续性计划: {service_id} ({continuity_id})')
                    return {'success': True, 'continuity_id': continuity_id}
        except Exception as e:
            logger.error(f'创建服务连续性计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_disaster_recovery(self, continuity_id: str, education_type: str,
                                 **kwargs) -> Dict[str, Any]:
        try:
            dr_id = f"dr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO disaster_recovery (
                            dr_id, continuity_id, education_type,
                            recovery_site, recovery_type, rto_target,
                            rpo_target, mttr_target, last_tested, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, 'active', ?, ?)
                    ''', (dr_id, continuity_id, education_type,
                          kwargs.get('recovery_site'),
                          kwargs.get('recovery_type', 'warm'),
                          kwargs.get('rto_target', '4小时'),
                          kwargs.get('rpo_target', '15分钟'),
                          kwargs.get('mttr_target', '1小时'), now, now))
                    conn.commit()
                    return {'success': True, 'dr_id': dr_id}
        except Exception as e:
            logger.error(f'创建灾难恢复计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def run_dr_test(self, dr_id: str, education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            test_id = f"tst_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO recovery_tests (
                            test_id, dr_id, education_type, test_type,
                            test_date, test_results, issues_found, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'completed', ?)
                    ''', (test_id, dr_id, education_type,
                          kwargs.get('test_type', 'simulation'),
                          kwargs.get('test_date', now[:10]),
                          kwargs.get('test_results'),
                          kwargs.get('issues_found'), now))
                    cursor.execute('UPDATE disaster_recovery SET last_tested = ? WHERE dr_id = ?', (now[:10], dr_id))
                    conn.commit()
                    return {'success': True, 'test_id': test_id}
        except Exception as e:
            logger.error(f'运行灾难恢复测试失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_continuity_status(self, education_type: str = None,
                              service_id: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM service_continuity WHERE status = ?'
                params = ['active']
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if service_id:
                    query += ' AND service_id = ?'
                    params.append(service_id)
                cursor.execute(query, params)
                continuities = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'continuities': continuities}
        except Exception as e:
            logger.error(f'获取服务连续性状态失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 服务目录 ==========

    def create_service_catalog(self, catalog_name: str, education_type: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            catalog_id = f"cat_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO service_catalog (
                            catalog_id, catalog_name, education_type,
                            description, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, 'active', ?, ?)
                    ''', (catalog_id, catalog_name, education_type,
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建服务目录: {catalog_name} ({catalog_id})')
                    return {'success': True, 'catalog_id': catalog_id}
        except Exception as e:
            logger.error(f'创建服务目录失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_catalog_item(self, catalog_id: str, item_name: str, education_type: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            item_id = f"cit_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO catalog_items (
                            item_id, catalog_id, service_id, education_type,
                            item_name, item_description, service_level,
                            price, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'available', ?, ?)
                    ''', (item_id, catalog_id, kwargs.get('service_id'), education_type,
                          item_name, kwargs.get('item_description'),
                          kwargs.get('service_level', 'standard'),
                          kwargs.get('price', 0), now, now))
                    conn.commit()
                    return {'success': True, 'item_id': item_id}
        except Exception as e:
            logger.error(f'添加目录项失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_service_catalog(self, education_type: str = None,
                            catalog_id: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM service_catalog WHERE status = ?'
                params = ['active']
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if catalog_id:
                    query += ' AND catalog_id = ?'
                    params.append(catalog_id)
                cursor.execute(query, params)
                catalogs = [dict(c) for c in cursor.fetchall()]
                if catalog_id and catalogs:
                    cursor.execute('SELECT * FROM catalog_items WHERE catalog_id = ? AND status = ?', (catalog_id, 'available'))
                    items = [dict(i) for i in cursor.fetchall()]
                    catalogs[0]['items'] = items
                return {'success': True, 'catalogs': catalogs}
        except Exception as e:
            logger.error(f'获取服务目录失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计与报告 ==========

    def get_operations_stats(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                filters = ''
                params = []
                if education_type:
                    filters = 'WHERE education_type = ?'
                    params.append(education_type)

                cursor.execute(f'SELECT COUNT(*) FROM service_levels {filters}', params)
                service_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM incident_management {filters}', params)
                incident_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM incident_management WHERE status = "resolved" {filters}', params)
                resolved_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM change_management {filters}', params)
                change_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM performance_monitoring WHERE status = "active" {filters}', params)
                monitor_count = cursor.fetchone()[0]

                avg_resolution = 0
                if resolved_count > 0:
                    cursor.execute(f'''
                        SELECT AVG(julianday(resolved_at) - julianday(created_at)) * 24
                        FROM incident_management WHERE status = "resolved" {filters}
                    ''', params)
                    avg_resolution = round(cursor.fetchone()[0], 2)

                return {
                    'success': True,
                    'stats': {
                        'total_services': service_count,
                        'total_incidents': incident_count,
                        'resolved_incidents': resolved_count,
                        'resolution_rate': round(resolved_count / incident_count * 100, 2) if incident_count > 0 else 0,
                        'avg_resolution_hours': avg_resolution,
                        'total_changes': change_count,
                        'active_monitors': monitor_count,
                        'education_type': education_type or 'all'
                    }
                }
        except Exception as e:
            logger.error(f'获取运营统计失败: {e}')
            return {'success': False, 'error': str(e)}