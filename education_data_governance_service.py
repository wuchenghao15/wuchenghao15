#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育数据治理服务 (v15.20.0)
====================================
提供数据治理、数据标准、数据质量、数据安全、数据生命周期、元数据管理、数据目录和数据合规等综合管理服务。

核心能力：
1. 数据治理 - 治理框架、政策制定、流程管理、组织架构
2. 数据标准 - 分类标准、编码标准、命名规范、数据字典
3. 数据质量 - 质量规则、质量检查、质量报告、质量改进
4. 数据安全 - 安全等级、访问控制、数据脱敏、加密管理
5. 数据生命周期 - 数据采集、存储、处理、归档、销毁
6. 元数据管理 - 业务元数据、技术元数据、数据血缘、元数据目录
7. 数据目录 - 数据搜索、发现、预览、申请授权
8. 数据合规 - GDPR合规、数据安全法、个人信息保护、数据跨境
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_data_governance_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationDataGovernance')


# ========== 数据治理配置 ==========

DATA_GOVERNANCE_FRAMEWORKS = {
    'dama': {'name': 'DAMA-DMBOK', 'description': '数据管理知识体系', 'maturity_levels': 5},
    'cobit': {'name': 'COBIT', 'description': '信息及相关技术控制目标', 'maturity_levels': 5},
    'iso_8000': {'name': 'ISO 8000', 'description': '数据质量管理体系', 'maturity_levels': 5},
    'committee': {'name': '数据治理委员会', 'description': '组织级数据治理决策机构', 'maturity_levels': 3},
    'policy': {'name': '数据治理政策', 'description': '数据治理规章制度', 'maturity_levels': 3},
    'process': {'name': '数据治理流程', 'description': '数据治理工作流程', 'maturity_levels': 4},
    'organization': {'name': '数据治理组织', 'description': '数据治理职责体系', 'maturity_levels': 4},
    'maturity': {'name': '数据治理成熟度', 'description': '治理能力评估体系', 'maturity_levels': 5}
}

DATA_STANDARDS = {
    'classification': {'name': '数据分类标准', 'description': '数据资产分类分级规范'},
    'coding': {'name': '数据编码标准', 'description': '数据元素编码规则'},
    'naming': {'name': '数据命名标准', 'description': '数据对象命名规范'},
    'format': {'name': '数据格式标准', 'description': '数据存储与交换格式'},
    'metadata': {'name': '数据元标准', 'description': '数据元定义规范'},
    'dictionary': {'name': '数据字典', 'description': '数据元素定义集合'},
    'model': {'name': '数据模型', 'description': '数据结构与关系定义'},
    'specification': {'name': '数据规范', 'description': '数据使用与管理规范'}
}

DATA_QUALITY_DIMENSIONS = {
    'accuracy': {'name': '准确性', 'description': '数据值与真实情况的符合程度'},
    'completeness': {'name': '完整性', 'description': '数据信息的全面性和无缺失'},
    'consistency': {'name': '一致性', 'description': '同一数据在不同系统中的一致性'},
    'timeliness': {'name': '及时性', 'description': '数据产生和更新的时效性'},
    'validity': {'name': '有效性', 'description': '数据符合业务规则和格式要求'},
    'uniqueness': {'name': '唯一性', 'description': '数据无重复记录'},
    'reliability': {'name': '可靠性', 'description': '数据来源可信且可验证'},
    'accessibility': {'name': '可访问性', 'description': '数据能够被授权用户访问'}
}

DATA_SECURITY_LEVELS = {
    'public': {'name': '公开数据', 'description': '可对外公开的数据', 'encryption_required': False},
    'internal': {'name': '内部数据', 'description': '内部使用数据', 'encryption_required': False},
    'sensitive': {'name': '敏感数据', 'description': '需要保护的敏感信息', 'encryption_required': True},
    'confidential': {'name': '机密数据', 'description': '高度保密数据', 'encryption_required': True},
    'restricted': {'name': '受限数据', 'description': '严格控制访问的数据', 'encryption_required': True},
    'personal': {'name': '个人数据', 'description': '个人身份相关信息', 'encryption_required': True},
    'health': {'name': '健康数据', 'description': '医疗健康相关数据', 'encryption_required': True},
    'financial': {'name': '财务数据', 'description': '财务与交易数据', 'encryption_required': True}
}

DATA_LIFECYCLE = {
    'collection': {'name': '数据采集', 'description': '数据的获取和收集'},
    'storage': {'name': '数据存储', 'description': '数据的持久化存储'},
    'processing': {'name': '数据处理', 'description': '数据的转换和加工'},
    'usage': {'name': '数据使用', 'description': '数据的分析和应用'},
    'sharing': {'name': '数据共享', 'description': '数据的对外共享'},
    'archiving': {'name': '数据归档', 'description': '数据的长期保存'},
    'destruction': {'name': '数据销毁', 'description': '数据的安全删除'},
    'governance': {'name': '数据治理', 'description': '全生命周期治理'}
}

METADATA_TYPES = {
    'business': {'name': '业务元数据', 'description': '业务含义和业务规则'},
    'technical': {'name': '技术元数据', 'description': '数据存储和技术属性'},
    'operational': {'name': '操作元数据', 'description': '数据使用和操作记录'},
    'lineage': {'name': '数据血缘', 'description': '数据来源和流转关系'},
    'catalog': {'name': '数据目录', 'description': '数据资产的目录索引'},
    'dictionary': {'name': '数据字典', 'description': '数据元素详细定义'},
    'model': {'name': '数据模型', 'description': '数据结构和关系模型'},
    'standard': {'name': '数据标准', 'description': '数据标准规范定义'}
}

DATA_CATALOG_FUNCTIONS = {
    'search': {'name': '数据搜索', 'description': '按关键词搜索数据资产'},
    'discovery': {'name': '数据发现', 'description': '浏览和发现数据资产'},
    'preview': {'name': '数据预览', 'description': '查看数据样本和结构'},
    'request': {'name': '数据申请', 'description': '申请数据访问权限'},
    'authorization': {'name': '数据授权', 'description': '审批和授权数据访问'},
    'share': {'name': '数据共享', 'description': '共享数据资产给其他用户'},
    'rating': {'name': '数据评价', 'description': '对数据质量进行评价'},
    'statistics': {'name': '数据使用统计', 'description': '统计数据使用情况'}
}

DATA_COMPLIANCE = {
    'gdpr': {'name': 'GDPR', 'description': '欧盟通用数据保护条例'},
    'data_security_law': {'name': '数据安全法', 'description': '中华人民共和国数据安全法'},
    'personal_info_protection': {'name': '个人信息保护法', 'description': '中华人民共和国个人信息保护法'},
    'cross_border': {'name': '数据跨境', 'description': '数据跨境传输合规'},
    'anonymization': {'name': '数据脱敏', 'description': '敏感数据脱敏处理'},
    'encryption': {'name': '数据加密', 'description': '数据加密存储和传输'},
    'audit': {'name': '数据审计', 'description': '数据操作审计追踪'},
    'traceability': {'name': '数据留痕', 'description': '数据全生命周期留痕'}
}


class EducationDataGovernanceService:
    """教育数据治理服务"""

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
                    CREATE TABLE IF NOT EXISTS data_governance (
                        governance_id TEXT PRIMARY KEY,
                        framework TEXT NOT NULL,
                        name TEXT NOT NULL,
                        description TEXT,
                        education_type TEXT,
                        maturity_level INTEGER DEFAULT 1,
                        status TEXT DEFAULT 'active',
                        created_by TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS governance_policy (
                        policy_id TEXT PRIMARY KEY,
                        policy_name TEXT NOT NULL,
                        policy_type TEXT,
                        description TEXT,
                        education_type TEXT,
                        effective_date TEXT,
                        expiration_date TEXT,
                        status TEXT DEFAULT 'active',
                        created_by TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS data_standards (
                        standard_id TEXT PRIMARY KEY,
                        standard_name TEXT NOT NULL,
                        standard_type TEXT,
                        description TEXT,
                        education_type TEXT,
                        version TEXT DEFAULT '1.0',
                        status TEXT DEFAULT 'draft',
                        created_by TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS standard_definitions (
                        definition_id TEXT PRIMARY KEY,
                        standard_id TEXT NOT NULL,
                        field_name TEXT NOT NULL,
                        field_type TEXT,
                        length INTEGER,
                        precision INTEGER,
                        allowed_values TEXT,
                        description TEXT,
                        is_required INTEGER DEFAULT 1,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS data_quality (
                        quality_id TEXT PRIMARY KEY,
                        dataset_name TEXT NOT NULL,
                        education_type TEXT,
                        accuracy_score REAL DEFAULT 0,
                        completeness_score REAL DEFAULT 0,
                        consistency_score REAL DEFAULT 0,
                        timeliness_score REAL DEFAULT 0,
                        validity_score REAL DEFAULT 0,
                        overall_score REAL DEFAULT 0,
                        check_date TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS quality_rules (
                        rule_id TEXT PRIMARY KEY,
                        rule_name TEXT NOT NULL,
                        dimension TEXT,
                        education_type TEXT,
                        expression TEXT,
                        threshold REAL,
                        severity TEXT DEFAULT 'medium',
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_by TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS data_security (
                        security_id TEXT PRIMARY KEY,
                        dataset_name TEXT NOT NULL,
                        security_level TEXT,
                        education_type TEXT,
                        encryption_enabled INTEGER DEFAULT 0,
                        encryption_algorithm TEXT,
                        access_control_enabled INTEGER DEFAULT 1,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS security_policies (
                        policy_id TEXT PRIMARY KEY,
                        policy_name TEXT NOT NULL,
                        security_level TEXT,
                        education_type TEXT,
                        allowed_roles TEXT,
                        allowed_users TEXT,
                        access_duration TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_by TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS data_lifecycle (
                        lifecycle_id TEXT PRIMARY KEY,
                        dataset_name TEXT NOT NULL,
                        education_type TEXT,
                        current_stage TEXT,
                        collection_date TEXT,
                        storage_location TEXT,
                        processing_start TEXT,
                        processing_end TEXT,
                        archive_date TEXT,
                        retention_period INTEGER,
                        destruction_date TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS lifecycle_events (
                        event_id TEXT PRIMARY KEY,
                        lifecycle_id TEXT NOT NULL,
                        event_type TEXT,
                        event_date TEXT,
                        description TEXT,
                        operator TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS metadata_management (
                        metadata_id TEXT PRIMARY KEY,
                        metadata_type TEXT,
                        education_type TEXT,
                        name TEXT NOT NULL,
                        description TEXT,
                        source_system TEXT,
                        data_owner TEXT,
                        stewards TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS metadata_records (
                        record_id TEXT PRIMARY KEY,
                        metadata_id TEXT NOT NULL,
                        record_type TEXT,
                        record_content TEXT,
                        lineage_info TEXT,
                        quality_score REAL,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS data_catalog (
                        catalog_id TEXT PRIMARY KEY,
                        catalog_name TEXT NOT NULL,
                        education_type TEXT,
                        description TEXT,
                        data_owner TEXT,
                        data_asset_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_by TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS catalog_items (
                        item_id TEXT PRIMARY KEY,
                        catalog_id TEXT NOT NULL,
                        item_name TEXT NOT NULL,
                        item_type TEXT,
                        description TEXT,
                        data_location TEXT,
                        security_level TEXT,
                        access_status TEXT DEFAULT 'available',
                        usage_count INTEGER DEFAULT 0,
                        rating REAL DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS data_compliance (
                        compliance_id TEXT PRIMARY KEY,
                        dataset_name TEXT NOT NULL,
                        education_type TEXT,
                        gdpr_compliant INTEGER DEFAULT 0,
                        data_security_law_compliant INTEGER DEFAULT 0,
                        personal_info_compliant INTEGER DEFAULT 0,
                        cross_border_compliant INTEGER DEFAULT 0,
                        audit_status TEXT DEFAULT 'pending',
                        last_audit_date TEXT,
                        next_audit_date TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS compliance_checks (
                        check_id TEXT PRIMARY KEY,
                        compliance_id TEXT NOT NULL,
                        check_type TEXT,
                        check_result TEXT,
                        findings TEXT,
                        recommendations TEXT,
                        checked_by TEXT,
                        check_date TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS data_access (
                        access_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        dataset_name TEXT,
                        education_type TEXT,
                        access_type TEXT,
                        access_level TEXT,
                        granted_by TEXT,
                        grant_date TEXT,
                        expiration_date TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS access_logs (
                        log_id TEXT PRIMARY KEY,
                        access_id TEXT NOT NULL,
                        user_id INTEGER,
                        dataset_name TEXT,
                        education_type TEXT,
                        action TEXT,
                        access_time TEXT,
                        ip_address TEXT,
                        success INTEGER DEFAULT 1
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS data_sharing (
                        sharing_id TEXT PRIMARY KEY,
                        dataset_name TEXT NOT NULL,
                        education_type TEXT,
                        source_org TEXT,
                        target_org TEXT,
                        sharing_type TEXT,
                        security_level TEXT,
                        agreement_id TEXT,
                        status TEXT DEFAULT 'pending',
                        start_date TEXT,
                        end_date TEXT,
                        created_by TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sharing_agreements (
                        agreement_id TEXT PRIMARY KEY,
                        agreement_name TEXT NOT NULL,
                        education_type TEXT,
                        parties TEXT,
                        scope TEXT,
                        security_requirements TEXT,
                        compliance_requirements TEXT,
                        duration TEXT,
                        status TEXT DEFAULT 'draft',
                        signed_by TEXT,
                        signed_date TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('教育数据治理服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 数据治理 ==========

    def create_governance_framework(self, framework: str, name: str,
                                    **kwargs) -> Dict[str, Any]:
        try:
            governance_id = f"gov_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = DATA_GOVERNANCE_FRAMEWORKS.get(framework, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO data_governance (
                            governance_id, framework, name, description,
                            education_type, maturity_level, status, created_by,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
                    ''', (governance_id, framework, name,
                          kwargs.get('description', config.get('description')),
                          kwargs.get('education_type'),
                          kwargs.get('maturity_level', 1),
                          kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建数据治理框架: {name} ({governance_id})')
                    return {'success': True, 'governance_id': governance_id}
        except Exception as e:
            logger.error(f'创建数据治理框架失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_governance_policy(self, policy_name: str, **kwargs) -> Dict[str, Any]:
        try:
            policy_id = f"gpl_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO governance_policy (
                            policy_id, policy_name, policy_type, description,
                            education_type, effective_date, expiration_date,
                            status, created_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
                    ''', (policy_id, policy_name, kwargs.get('policy_type'),
                          kwargs.get('description'), kwargs.get('education_type'),
                          kwargs.get('effective_date'), kwargs.get('expiration_date'),
                          kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建数据治理政策: {policy_name} ({policy_id})')
                    return {'success': True, 'policy_id': policy_id}
        except Exception as e:
            logger.error(f'创建数据治理政策失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_governance_maturity(self, governance_id: str,
                                   maturity_level: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE data_governance SET maturity_level = ?, updated_at = ?
                        WHERE governance_id = ?
                    ''', (maturity_level, now, governance_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'maturity_level': maturity_level}
                    return {'success': False, 'error': '治理框架不存在'}
        except Exception as e:
            logger.error(f'更新治理成熟度失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_governance_frameworks(self, education_type: str = None,
                                   status: str = 'active') -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM data_governance WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                query += ' ORDER BY created_at DESC'
                cursor.execute(query, params)
                frameworks = [dict(f) for f in cursor.fetchall()]
                return {'success': True, 'frameworks': frameworks}
        except Exception as e:
            logger.error(f'获取治理框架列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 数据标准 ==========

    def create_data_standard(self, standard_name: str, standard_type: str,
                             **kwargs) -> Dict[str, Any]:
        try:
            standard_id = f"std_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = DATA_STANDARDS.get(standard_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO data_standards (
                            standard_id, standard_name, standard_type, description,
                            education_type, version, status, created_by,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, '1.0', 'draft', ?, ?, ?)
                    ''', (standard_id, standard_name, standard_type,
                          kwargs.get('description', config.get('description')),
                          kwargs.get('education_type'),
                          kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建数据标准: {standard_name} ({standard_id})')
                    return {'success': True, 'standard_id': standard_id}
        except Exception as e:
            logger.error(f'创建数据标准失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_standard_definition(self, standard_id: str, field_name: str,
                                **kwargs) -> Dict[str, Any]:
        try:
            definition_id = f"def_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT standard_id FROM data_standards WHERE standard_id = ?', (standard_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '数据标准不存在'}
                    cursor.execute('''
                        INSERT INTO standard_definitions (
                            definition_id, standard_id, field_name, field_type,
                            length, precision, allowed_values, description,
                            is_required, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (definition_id, standard_id, field_name,
                          kwargs.get('field_type'), kwargs.get('length'),
                          kwargs.get('precision'), kwargs.get('allowed_values'),
                          kwargs.get('description'), kwargs.get('is_required', 1), now))
                    conn.commit()
                    return {'success': True, 'definition_id': definition_id}
        except Exception as e:
            logger.error(f'添加标准定义失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_standard(self, standard_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE data_standards SET status = 'approved', updated_at = ?
                        WHERE standard_id = ? AND status = 'draft'
                    ''', (now, standard_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'approved'}
                    return {'success': False, 'error': '标准状态不允许审批'}
        except Exception as e:
            logger.error(f'审批数据标准失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_data_standards(self, education_type: str = None,
                            status: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM data_standards WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                query += ' ORDER BY created_at DESC'
                cursor.execute(query, params)
                standards = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'standards': standards}
        except Exception as e:
            logger.error(f'获取数据标准列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 数据质量 ==========

    def create_quality_rule(self, rule_name: str, dimension: str,
                            **kwargs) -> Dict[str, Any]:
        try:
            rule_id = f"qrl_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO quality_rules (
                            rule_id, rule_name, dimension, education_type,
                            expression, threshold, severity, description,
                            status, created_by, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (rule_id, rule_name, dimension, kwargs.get('education_type'),
                          kwargs.get('expression'), kwargs.get('threshold'),
                          kwargs.get('severity', 'medium'), kwargs.get('description'),
                          kwargs.get('created_by'), now))
                    conn.commit()
                    logger.info(f'创建质量规则: {rule_name} ({rule_id})')
                    return {'success': True, 'rule_id': rule_id}
        except Exception as e:
            logger.error(f'创建质量规则失败: {e}')
            return {'success': False, 'error': str(e)}

    def execute_quality_check(self, dataset_name: str, **kwargs) -> Dict[str, Any]:
        try:
            quality_id = f"qlt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            scores = {
                'accuracy_score': kwargs.get('accuracy_score', 0),
                'completeness_score': kwargs.get('completeness_score', 0),
                'consistency_score': kwargs.get('consistency_score', 0),
                'timeliness_score': kwargs.get('timeliness_score', 0),
                'validity_score': kwargs.get('validity_score', 0)
            }
            overall = sum(scores.values()) / len(scores) if scores else 0
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO data_quality (
                            quality_id, dataset_name, education_type,
                            accuracy_score, completeness_score, consistency_score,
                            timeliness_score, validity_score, overall_score,
                            check_date, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'completed', ?)
                    ''', (quality_id, dataset_name, kwargs.get('education_type'),
                          scores['accuracy_score'], scores['completeness_score'],
                          scores['consistency_score'], scores['timeliness_score'],
                          scores['validity_score'], round(overall, 2), now[:10], now))
                    conn.commit()
                    return {'success': True, 'quality_id': quality_id, 'overall_score': round(overall, 2)}
        except Exception as e:
            logger.error(f'执行质量检查失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_quality_report(self, dataset_name: str = None,
                           education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM data_quality WHERE 1=1'
                params = []
                if dataset_name:
                    query += ' AND dataset_name = ?'
                    params.append(dataset_name)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' ORDER BY check_date DESC'
                cursor.execute(query, params)
                reports = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'reports': reports}
        except Exception as e:
            logger.error(f'获取质量报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_quality_rules(self, education_type: str = None,
                           status: str = 'active') -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM quality_rules WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                query += ' ORDER BY created_at DESC'
                cursor.execute(query, params)
                rules = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'rules': rules}
        except Exception as e:
            logger.error(f'获取质量规则列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 数据安全 ==========

    def create_security_policy(self, policy_name: str, security_level: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            policy_id = f"spc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO security_policies (
                            policy_id, policy_name, security_level, education_type,
                            allowed_roles, allowed_users, access_duration,
                            description, status, created_by, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (policy_id, policy_name, security_level,
                          kwargs.get('education_type'), kwargs.get('allowed_roles'),
                          kwargs.get('allowed_users'), kwargs.get('access_duration'),
                          kwargs.get('description'), kwargs.get('created_by'), now))
                    conn.commit()
                    logger.info(f'创建安全策略: {policy_name} ({policy_id})')
                    return {'success': True, 'policy_id': policy_id}
        except Exception as e:
            logger.error(f'创建安全策略失败: {e}')
            return {'success': False, 'error': str(e)}

    def set_data_security(self, dataset_name: str, security_level: str,
                          **kwargs) -> Dict[str, Any]:
        try:
            security_id = f"ds_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = DATA_SECURITY_LEVELS.get(security_level, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO data_security (
                            security_id, dataset_name, security_level, education_type,
                            encryption_enabled, encryption_algorithm,
                            access_control_enabled, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 1, 'active', ?, ?)
                    ''', (security_id, dataset_name, security_level,
                          kwargs.get('education_type'),
                          1 if config.get('encryption_required') else 0,
                          kwargs.get('encryption_algorithm', 'AES-256'), now, now))
                    conn.commit()
                    return {'success': True, 'security_id': security_id}
        except Exception as e:
            logger.error(f'设置数据安全失败: {e}')
            return {'success': False, 'error': str(e)}

    def grant_data_access(self, user_id: int, dataset_name: str,
                          **kwargs) -> Dict[str, Any]:
        try:
            access_id = f"acc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO data_access (
                            access_id, user_id, user_name, dataset_name,
                            education_type, access_type, access_level,
                            granted_by, grant_date, expiration_date,
                            status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)
                    ''', (access_id, user_id, kwargs.get('user_name'), dataset_name,
                          kwargs.get('education_type'), kwargs.get('access_type', 'read'),
                          kwargs.get('access_level', 'normal'), kwargs.get('granted_by'),
                          now[:10], kwargs.get('expiration_date'), now))
                    conn.commit()
                    logger.info(f'授权数据访问: 用户{user_id} -> {dataset_name}')
                    return {'success': True, 'access_id': access_id}
        except Exception as e:
            logger.error(f'授权数据访问失败: {e}')
            return {'success': False, 'error': str(e)}

    def log_access(self, access_id: str, user_id: int, dataset_name: str,
                   action: str, **kwargs) -> Dict[str, Any]:
        try:
            log_id = f"log_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO access_logs (
                            log_id, access_id, user_id, dataset_name,
                            education_type, action, access_time, ip_address, success
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (log_id, access_id, user_id, dataset_name,
                          kwargs.get('education_type'), action, now,
                          kwargs.get('ip_address'), kwargs.get('success', 1)))
                    conn.commit()
                    return {'success': True, 'log_id': log_id}
        except Exception as e:
            logger.error(f'记录访问日志失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_access_logs(self, user_id: int = None, dataset_name: str = None,
                         education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM access_logs WHERE 1=1'
                params = []
                if user_id:
                    query += ' AND user_id = ?'
                    params.append(user_id)
                if dataset_name:
                    query += ' AND dataset_name = ?'
                    params.append(dataset_name)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' ORDER BY access_time DESC'
                cursor.execute(query, params)
                logs = [dict(l) for l in cursor.fetchall()]
                return {'success': True, 'logs': logs}
        except Exception as e:
            logger.error(f'获取访问日志失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 数据生命周期 ==========

    def create_lifecycle_record(self, dataset_name: str, **kwargs) -> Dict[str, Any]:
        try:
            lifecycle_id = f"lfc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO data_lifecycle (
                            lifecycle_id, dataset_name, education_type,
                            current_stage, collection_date, storage_location,
                            retention_period, status, created_at, updated_at
                        ) VALUES (?, ?, ?, 'collection', ?, ?, ?, 'active', ?, ?)
                    ''', (lifecycle_id, dataset_name, kwargs.get('education_type'),
                          now[:10], kwargs.get('storage_location'),
                          kwargs.get('retention_period', 365), now, now))
                    self._record_lifecycle_event(lifecycle_id, 'collection', '数据采集开始')
                    conn.commit()
                    logger.info(f'创建生命周期记录: {dataset_name} ({lifecycle_id})')
                    return {'success': True, 'lifecycle_id': lifecycle_id}
        except Exception as e:
            logger.error(f'创建生命周期记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def transition_lifecycle_stage(self, lifecycle_id: str, new_stage: str,
                                   **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT current_stage FROM data_lifecycle WHERE lifecycle_id = ?', (lifecycle_id,))
                    stage = cursor.fetchone()
                    if not stage:
                        return {'success': False, 'error': '生命周期记录不存在'}
                    cursor.execute('UPDATE data_lifecycle SET current_stage = ?, updated_at = ? WHERE lifecycle_id = ?',
                                  (new_stage, now, lifecycle_id))
                    if new_stage == 'processing':
                        cursor.execute('UPDATE data_lifecycle SET processing_start = ? WHERE lifecycle_id = ?', (now[:10], lifecycle_id))
                    elif new_stage == 'archiving':
                        cursor.execute('UPDATE data_lifecycle SET archive_date = ? WHERE lifecycle_id = ?', (now[:10], lifecycle_id))
                    elif new_stage == 'destruction':
                        cursor.execute('UPDATE data_lifecycle SET destruction_date = ?, status = ? WHERE lifecycle_id = ?', (now[:10], 'destroyed', lifecycle_id))
                    self._record_lifecycle_event(lifecycle_id, new_stage, kwargs.get('description', f'阶段变更为{new_stage}'))
                    conn.commit()
                    return {'success': True, 'current_stage': new_stage}
        except Exception as e:
            logger.error(f'变更生命周期阶段失败: {e}')
            return {'success': False, 'error': str(e)}

    def _record_lifecycle_event(self, lifecycle_id: str, event_type: str, description: str):
        event_id = f"lev_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO lifecycle_events (event_id, lifecycle_id, event_type, event_date, description, operator, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (event_id, lifecycle_id, event_type, now[:10], description, 'system', now))

    def archive_data(self, lifecycle_id: str, archive_location: str) -> Dict[str, Any]:
        try:
            return self.transition_lifecycle_stage(lifecycle_id, 'archiving',
                                                   description=f'数据归档至{archive_location}')
        except Exception as e:
            logger.error(f'数据归档失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_lifecycle_records(self, education_type: str = None,
                               status: str = 'active') -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM data_lifecycle WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                query += ' ORDER BY created_at DESC'
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records}
        except Exception as e:
            logger.error(f'获取生命周期记录失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 元数据管理 ==========

    def create_metadata(self, metadata_type: str, name: str, **kwargs) -> Dict[str, Any]:
        try:
            metadata_id = f"md_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = METADATA_TYPES.get(metadata_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO metadata_management (
                            metadata_id, metadata_type, education_type, name,
                            description, source_system, data_owner, stewards,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (metadata_id, metadata_type, kwargs.get('education_type'), name,
                          kwargs.get('description', config.get('description')),
                          kwargs.get('source_system'), kwargs.get('data_owner'),
                          kwargs.get('stewards'), now, now))
                    conn.commit()
                    logger.info(f'创建元数据: {name} ({metadata_id})')
                    return {'success': True, 'metadata_id': metadata_id}
        except Exception as e:
            logger.error(f'创建元数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_metadata_record(self, metadata_id: str, record_type: str,
                            record_content: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"mrc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT metadata_id FROM metadata_management WHERE metadata_id = ?', (metadata_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '元数据不存在'}
                    cursor.execute('''
                        INSERT INTO metadata_records (
                            record_id, metadata_id, record_type, record_content,
                            lineage_info, quality_score, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (record_id, metadata_id, record_type, record_content,
                          kwargs.get('lineage_info'), kwargs.get('quality_score', 0), now, now))
                    conn.commit()
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'添加元数据记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_data_lineage(self, metadata_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT r.record_id, r.record_type, r.lineage_info, r.created_at
                    FROM metadata_records r
                    WHERE r.metadata_id = ? AND r.lineage_info IS NOT NULL
                    ORDER BY r.created_at DESC
                ''', (metadata_id,))
                lineage = [dict(l) for l in cursor.fetchall()]
                return {'success': True, 'lineage': lineage}
        except Exception as e:
            logger.error(f'获取数据血缘失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_metadata(self, metadata_type: str = None,
                      education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM metadata_management WHERE 1=1'
                params = []
                if metadata_type:
                    query += ' AND metadata_type = ?'
                    params.append(metadata_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' ORDER BY created_at DESC'
                cursor.execute(query, params)
                metadata = [dict(m) for m in cursor.fetchall()]
                return {'success': True, 'metadata': metadata}
        except Exception as e:
            logger.error(f'获取元数据列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 数据目录 ==========

    def create_data_catalog(self, catalog_name: str, **kwargs) -> Dict[str, Any]:
        try:
            catalog_id = f"ctl_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO data_catalog (
                            catalog_id, catalog_name, education_type, description,
                            data_owner, data_asset_count, status, created_by,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 0, 'active', ?, ?, ?)
                    ''', (catalog_id, catalog_name, kwargs.get('education_type'),
                          kwargs.get('description'), kwargs.get('data_owner'),
                          kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建数据目录: {catalog_name} ({catalog_id})')
                    return {'success': True, 'catalog_id': catalog_id}
        except Exception as e:
            logger.error(f'创建数据目录失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_catalog_item(self, catalog_id: str, item_name: str, **kwargs) -> Dict[str, Any]:
        try:
            item_id = f"cit_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT catalog_id FROM data_catalog WHERE catalog_id = ?', (catalog_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '数据目录不存在'}
                    cursor.execute('''
                        INSERT INTO catalog_items (
                            item_id, catalog_id, item_name, item_type,
                            description, data_location, security_level,
                            access_status, usage_count, rating, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'available', 0, 0, ?, ?)
                    ''', (item_id, catalog_id, item_name, kwargs.get('item_type'),
                          kwargs.get('description'), kwargs.get('data_location'),
                          kwargs.get('security_level', 'internal'), now, now))
                    cursor.execute('UPDATE data_catalog SET data_asset_count = data_asset_count + 1, updated_at = ? WHERE catalog_id = ?', (now, catalog_id))
                    conn.commit()
                    return {'success': True, 'item_id': item_id}
        except Exception as e:
            logger.error(f'添加目录项失败: {e}')
            return {'success': False, 'error': str(e)}

    def search_catalog(self, keyword: str, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = '''
                    SELECT ci.* FROM catalog_items ci
                    JOIN data_catalog dc ON ci.catalog_id = dc.catalog_id
                    WHERE (ci.item_name LIKE ? OR ci.description LIKE ?)
                '''
                params = [f'%{keyword}%', f'%{keyword}%']
                if education_type:
                    query += ' AND dc.education_type = ?'
                    params.append(education_type)
                query += ' ORDER BY ci.created_at DESC'
                cursor.execute(query, params)
                items = [dict(i) for i in cursor.fetchall()]
                return {'success': True, 'items': items}
        except Exception as e:
            logger.error(f'搜索数据目录失败: {e}')
            return {'success': False, 'error': str(e)}

    def rate_catalog_item(self, item_id: str, rating: float) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT rating FROM catalog_items WHERE item_id = ?', (item_id,))
                    current = cursor.fetchone()
                    if not current:
                        return {'success': False, 'error': '目录项不存在'}
                    new_rating = (current[0] + rating) / 2
                    cursor.execute('UPDATE catalog_items SET rating = ?, updated_at = ? WHERE item_id = ?',
                                  (round(new_rating, 1), now, item_id))
                    conn.commit()
                    return {'success': True, 'rating': round(new_rating, 1)}
        except Exception as e:
            logger.error(f'评价目录项失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 数据合规 ==========

    def create_compliance_record(self, dataset_name: str, **kwargs) -> Dict[str, Any]:
        try:
            compliance_id = f"cpl_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            next_audit = (datetime.now() + timedelta(days=365)).isoformat()[:10]
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO data_compliance (
                            compliance_id, dataset_name, education_type,
                            gdpr_compliant, data_security_law_compliant,
                            personal_info_compliant, cross_border_compliant,
                            audit_status, last_audit_date, next_audit_date,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', NULL, ?, 'active', ?, ?)
                    ''', (compliance_id, dataset_name, kwargs.get('education_type'),
                          kwargs.get('gdpr_compliant', 0), kwargs.get('data_security_law_compliant', 0),
                          kwargs.get('personal_info_compliant', 0), kwargs.get('cross_border_compliant', 0),
                          next_audit, now, now))
                    conn.commit()
                    logger.info(f'创建合规记录: {dataset_name} ({compliance_id})')
                    return {'success': True, 'compliance_id': compliance_id}
        except Exception as e:
            logger.error(f'创建合规记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def execute_compliance_check(self, compliance_id: str, check_type: str,
                                 **kwargs) -> Dict[str, Any]:
        try:
            check_id = f"chk_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT compliance_id FROM data_compliance WHERE compliance_id = ?', (compliance_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '合规记录不存在'}
                    cursor.execute('''
                        INSERT INTO compliance_checks (
                            check_id, compliance_id, check_type, check_result,
                            findings, recommendations, checked_by, check_date,
                            created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (check_id, compliance_id, check_type, kwargs.get('check_result', 'pending'),
                          kwargs.get('findings'), kwargs.get('recommendations'),
                          kwargs.get('checked_by'), now[:10], now))
                    cursor.execute('UPDATE data_compliance SET audit_status = ?, last_audit_date = ? WHERE compliance_id = ?',
                                  (kwargs.get('check_result', 'pending'), now[:10], compliance_id))
                    conn.commit()
                    return {'success': True, 'check_id': check_id}
        except Exception as e:
            logger.error(f'执行合规检查失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_compliance_status(self, compliance_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    updates = []
                    params = []
                    if 'gdpr_compliant' in kwargs:
                        updates.append('gdpr_compliant = ?')
                        params.append(kwargs['gdpr_compliant'])
                    if 'data_security_law_compliant' in kwargs:
                        updates.append('data_security_law_compliant = ?')
                        params.append(kwargs['data_security_law_compliant'])
                    if 'personal_info_compliant' in kwargs:
                        updates.append('personal_info_compliant = ?')
                        params.append(kwargs['personal_info_compliant'])
                    if 'cross_border_compliant' in kwargs:
                        updates.append('cross_border_compliant = ?')
                        params.append(kwargs['cross_border_compliant'])
                    updates.append('updated_at = ?')
                    params.append(now)
                    params.append(compliance_id)
                    if updates:
                        cursor.execute(f'UPDATE data_compliance SET {", ".join(updates)} WHERE compliance_id = ?', params)
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '无更新字段'}
        except Exception as e:
            logger.error(f'更新合规状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_compliance_records(self, education_type: str = None,
                                audit_status: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM data_compliance WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if audit_status:
                    query += ' AND audit_status = ?'
                    params.append(audit_status)
                query += ' ORDER BY created_at DESC'
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records}
        except Exception as e:
            logger.error(f'获取合规记录列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 数据共享 ==========

    def create_sharing_agreement(self, agreement_name: str, **kwargs) -> Dict[str, Any]:
        try:
            agreement_id = f"sag_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO sharing_agreements (
                            agreement_id, agreement_name, education_type,
                            parties, scope, security_requirements,
                            compliance_requirements, duration, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?)
                    ''', (agreement_id, agreement_name, kwargs.get('education_type'),
                          kwargs.get('parties'), kwargs.get('scope'),
                          kwargs.get('security_requirements'),
                          kwargs.get('compliance_requirements'),
                          kwargs.get('duration'), now, now))
                    conn.commit()
                    logger.info(f'创建共享协议: {agreement_name} ({agreement_id})')
                    return {'success': True, 'agreement_id': agreement_id}
        except Exception as e:
            logger.error(f'创建共享协议失败: {e}')
            return {'success': False, 'error': str(e)}

    def sign_sharing_agreement(self, agreement_id: str, signed_by: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE sharing_agreements SET status = ?, signed_by = ?, signed_date = ?, updated_at = ? WHERE agreement_id = ? AND status = ?',
                                  ('active', signed_by, now[:10], now, agreement_id, 'draft'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'active'}
                    return {'success': False, 'error': '协议状态不允许签署'}
        except Exception as e:
            logger.error(f'签署共享协议失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_data_sharing(self, dataset_name: str, source_org: str,
                            target_org: str, **kwargs) -> Dict[str, Any]:
        try:
            sharing_id = f"shr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO data_sharing (
                            sharing_id, dataset_name, education_type,
                            source_org, target_org, sharing_type,
                            security_level, agreement_id, status,
                            start_date, end_date, created_by,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?, ?)
                    ''', (sharing_id, dataset_name, kwargs.get('education_type'),
                          source_org, target_org, kwargs.get('sharing_type', 'read'),
                          kwargs.get('security_level', 'internal'),
                          kwargs.get('agreement_id'), now[:10],
                          kwargs.get('end_date'), kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建数据共享: {dataset_name} ({sharing_id})')
                    return {'success': True, 'sharing_id': sharing_id}
        except Exception as e:
            logger.error(f'创建数据共享失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_data_sharing(self, sharing_id: str, approved: bool,
                             **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE data_sharing SET status = ?, updated_at = ? WHERE sharing_id = ? AND status = ?',
                                  (status, now, sharing_id, 'pending'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '共享请求状态不允许审批'}
        except Exception as e:
            logger.error(f'审批数据共享失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_governance_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                filters = f" AND education_type = '{education_type}'" if education_type else ""

                cursor.execute(f'SELECT COUNT(*) FROM data_governance WHERE status = "active"{filters}')
                governance_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM data_standards WHERE status = "approved"{filters}')
                standards_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM data_quality{filters}')
                quality_checks = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM data_security WHERE status = "active"{filters}')
                security_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM data_lifecycle WHERE status = "active"{filters}')
                lifecycle_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM metadata_management WHERE status = "active"{filters}')
                metadata_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM data_catalog WHERE status = "active"{filters}')
                catalog_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM data_compliance WHERE status = "active"{filters}')
                compliance_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT AVG(overall_score) FROM data_quality{filters}')
                avg_quality = round(cursor.fetchone()[0], 2) if cursor.fetchone()[0] else 0

                return {
                    'success': True,
                    'statistics': {
                        'governance_frameworks': governance_count,
                        'approved_standards': standards_count,
                        'quality_checks': quality_checks,
                        'security_policies': security_count,
                        'lifecycle_records': lifecycle_count,
                        'metadata_records': metadata_count,
                        'data_catalogs': catalog_count,
                        'compliance_records': compliance_count,
                        'average_quality_score': avg_quality
                    },
                    'education_type': education_type
                }
        except Exception as e:
            logger.error(f'获取治理统计失败: {e}')
            return {'success': False, 'error': str(e)}