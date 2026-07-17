#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育质量保障服务 (v15.20.0)
====================================
提供质量标准、质量监控、质量评估、质量改进、认证认可、
质量文化、质量审计、质量报告等综合管理服务。

核心能力：
1. 质量标准 - 标准管理、标准项配置、标准版本控制
2. 质量监控 - 监控计划、监控记录、预警管理
3. 质量评估 - 评估方案、评分管理、结果分析
4. 质量改进 - 改进计划、改进措施、效果验证
5. 认证认可 - 认证申请、认证记录、证书管理
6. 质量文化 - 文化建设、培训管理、激励机制
7. 质量审计 - 审计计划、审计发现、整改跟踪
8. 质量报告 - 报告生成、报告发布、报告归档
9. 标杆管理 - 数据采集、对比分析、差距评估
10. 统计分析 - 综合统计、趋势分析
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'quality_assurance_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('QualityAssurance')


# ========== 质量配置 ==========

QUALITY_STANDARDS = {
    'national': {'name': '国家标准', 'description': '国家教育质量标准'},
    'industry': {'name': '行业标准', 'description': '教育行业质量标准'},
    'local': {'name': '地方标准', 'description': '地方教育质量标准'},
    'school': {'name': '学校标准', 'description': '学校内部质量标准'},
    'international': {'name': '国际标准', 'description': '国际教育质量标准'},
    'certification': {'name': '认证标准', 'description': '认证机构质量标准'},
    'assessment': {'name': '评估标准', 'description': '教育评估质量标准'},
    'specification': {'name': '质量规范', 'description': '质量保障工作规范'}
}

MONITORING_METHODS = {
    'regular': {'name': '定期检查', 'frequency': 'monthly', 'scope': 'comprehensive'},
    'random': {'name': '随机抽查', 'frequency': 'weekly', 'scope': 'sample'},
    'special': {'name': '专项检查', 'frequency': 'on_demand', 'scope': 'specific'},
    'third_party': {'name': '第三方评估', 'frequency': 'yearly', 'scope': 'comprehensive'},
    'peer': {'name': '同行评估', 'frequency': 'semiannually', 'scope': 'comprehensive'},
    'student_feedback': {'name': '学生反馈', 'frequency': 'quarterly', 'scope': 'comprehensive'},
    'social': {'name': '社会评价', 'frequency': 'yearly', 'scope': 'comprehensive'},
    'data_analysis': {'name': '数据分析', 'frequency': 'weekly', 'scope': 'comprehensive'}
}

ASSESSMENT_CRITERIA = {
    'facilities': {'name': '办学条件', 'weight': 0.15, 'threshold': 60},
    'faculty': {'name': '师资队伍', 'weight': 0.20, 'threshold': 60},
    'teaching': {'name': '教学质量', 'weight': 0.25, 'threshold': 60},
    'research': {'name': '科研水平', 'weight': 0.15, 'threshold': 60},
    'management': {'name': '管理水平', 'weight': 0.10, 'threshold': 60},
    'reputation': {'name': '社会声誉', 'weight': 0.08, 'threshold': 60},
    'potential': {'name': '发展潜力', 'weight': 0.04, 'threshold': 60},
    'innovation': {'name': '创新能力', 'weight': 0.03, 'threshold': 60}
}

IMPROVEMENT_MODELS = {
    'pdca': {'name': 'PDCA循环', 'phases': ['计划', '执行', '检查', '改进']},
    'iso9000': {'name': 'ISO9000', 'focus': '质量管理体系'},
    'tqm': {'name': '全面质量管理', 'focus': '全员参与'},
    'six_sigma': {'name': '六西格玛', 'focus': '质量改进'},
    'lean': {'name': '精益管理', 'focus': '消除浪费'},
    'bpr': {'name': '业务流程再造', 'focus': '流程优化'},
    'continuous': {'name': '持续改进', 'focus': '渐进提升'},
    'benchmarking': {'name': '标杆管理', 'focus': '对标先进'}
}

CERTIFICATION_TYPES = {
    'iso': {'name': 'ISO认证', 'body': '国际标准化组织', 'validity': 3},
    'program': {'name': '专业认证', 'body': '专业认证机构', 'validity': 5},
    'school': {'name': '学校认证', 'body': '教育认证机构', 'validity': 5},
    'course': {'name': '课程认证', 'body': '课程认证机构', 'validity': 3},
    'quality': {'name': '质量认证', 'body': '质量管理机构', 'validity': 3},
    'international': {'name': '国际认证', 'body': '国际认证机构', 'validity': 5},
    'regional': {'name': '区域认证', 'body': '区域认证机构', 'validity': 5},
    'industry': {'name': '行业认证', 'body': '行业协会', 'validity': 3}
}

QUALITY_CULTURE = {
    'awareness': {'name': '质量意识', 'description': '全员质量意识培养'},
    'values': {'name': '质量价值观', 'description': '质量第一的价值观'},
    'behavior': {'name': '质量行为', 'description': '质量导向的行为规范'},
    'system': {'name': '质量制度', 'description': '完善的质量管理制度'},
    'training': {'name': '质量培训', 'description': '定期质量培训'},
    'incentive': {'name': '质量激励', 'description': '质量激励机制'},
    'responsibility': {'name': '质量责任', 'description': '明确的质量责任体系'},
    'commitment': {'name': '质量承诺', 'description': '组织质量承诺'}
}

AUDIT_FUNCTIONS = {
    'quality': {'name': '质量审计', 'scope': '质量体系'},
    'compliance': {'name': '合规审计', 'scope': '法规合规'},
    'performance': {'name': '绩效审计', 'scope': '绩效目标'},
    'special': {'name': '专项审计', 'scope': '特定领域'},
    'internal': {'name': '内部审计', 'type': 'internal'},
    'external': {'name': '外部审计', 'type': 'external'},
    'periodic': {'name': '定期审计', 'frequency': 'yearly'},
    'random': {'name': '随机审计', 'frequency': 'on_demand'}
}

REPORT_TYPES = {
    'quality': {'name': '质量报告', 'period': 'quarterly'},
    'assessment': {'name': '评估报告', 'period': 'yearly'},
    'certification': {'name': '认证报告', 'period': 'on_demand'},
    'audit': {'name': '审计报告', 'period': 'yearly'},
    'improvement': {'name': '改进报告', 'period': 'quarterly'},
    'annual': {'name': '年度报告', 'period': 'yearly'},
    'special': {'name': '专项报告', 'period': 'on_demand'},
    'comprehensive': {'name': '综合报告', 'period': 'yearly'}
}


class EducationQualityAssuranceService:
    """教育质量保障服务"""

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
                    CREATE TABLE IF NOT EXISTS quality_standards (
                        standard_id TEXT PRIMARY KEY,
                        standard_name TEXT NOT NULL,
                        standard_type TEXT,
                        education_type TEXT,
                        version TEXT DEFAULT '1.0',
                        status TEXT DEFAULT 'active',
                        effective_date TEXT,
                        expiration_date TEXT,
                        description TEXT,
                        created_by TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS standard_items (
                        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        standard_id TEXT NOT NULL,
                        item_name TEXT NOT NULL,
                        item_code TEXT,
                        weight REAL DEFAULT 0,
                        description TEXT,
                        requirement TEXT,
                        status TEXT DEFAULT 'active',
                        FOREIGN KEY (standard_id) REFERENCES quality_standards(standard_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS quality_monitoring (
                        monitor_id TEXT PRIMARY KEY,
                        monitor_name TEXT NOT NULL,
                        monitor_method TEXT,
                        education_type TEXT,
                        frequency TEXT,
                        scope TEXT,
                        status TEXT DEFAULT 'active',
                        description TEXT,
                        created_by TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS monitoring_records (
                        record_id TEXT PRIMARY KEY,
                        monitor_id TEXT NOT NULL,
                        education_type TEXT,
                        check_date TEXT,
                        checker TEXT,
                        findings TEXT,
                        status TEXT DEFAULT 'pending',
                        risk_level TEXT,
                        follow_up_required INTEGER DEFAULT 0,
                        created_at TEXT,
                        FOREIGN KEY (monitor_id) REFERENCES quality_monitoring(monitor_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS quality_assessment (
                        assessment_id TEXT PRIMARY KEY,
                        assessment_name TEXT NOT NULL,
                        assessment_type TEXT,
                        education_type TEXT,
                        criteria_config TEXT,
                        status TEXT DEFAULT 'draft',
                        start_date TEXT,
                        end_date TEXT,
                        description TEXT,
                        created_by TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS assessment_scores (
                        score_id TEXT PRIMARY KEY,
                        assessment_id TEXT NOT NULL,
                        entity_id TEXT NOT NULL,
                        entity_name TEXT,
                        education_type TEXT,
                        criteria_code TEXT,
                        score REAL,
                        max_score REAL DEFAULT 100,
                        comments TEXT,
                        scored_by TEXT,
                        scored_at TEXT,
                        FOREIGN KEY (assessment_id) REFERENCES quality_assessment(assessment_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS quality_improvement (
                        improvement_id TEXT PRIMARY KEY,
                        improvement_name TEXT NOT NULL,
                        education_type TEXT,
                        improvement_model TEXT,
                        status TEXT DEFAULT 'planned',
                        target TEXT,
                        deadline TEXT,
                        responsible TEXT,
                        description TEXT,
                        created_by TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS improvement_actions (
                        action_id TEXT PRIMARY KEY,
                        improvement_id TEXT NOT NULL,
                        action_name TEXT NOT NULL,
                        phase TEXT,
                        status TEXT DEFAULT 'pending',
                        deadline TEXT,
                        responsible TEXT,
                        resources TEXT,
                        progress REAL DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY (improvement_id) REFERENCES quality_improvement(improvement_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS certifications (
                        cert_id TEXT PRIMARY KEY,
                        cert_name TEXT NOT NULL,
                        cert_type TEXT,
                        education_type TEXT,
                        issuing_body TEXT,
                        validity_period INTEGER DEFAULT 3,
                        status TEXT DEFAULT 'active',
                        description TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS certification_records (
                        record_id TEXT PRIMARY KEY,
                        cert_id TEXT NOT NULL,
                        entity_id TEXT NOT NULL,
                        entity_name TEXT,
                        education_type TEXT,
                        application_date TEXT,
                        certification_date TEXT,
                        expiration_date TEXT,
                        status TEXT DEFAULT 'applied',
                        certificate_no TEXT,
                        issued_by TEXT,
                        created_at TEXT,
                        FOREIGN KEY (cert_id) REFERENCES certifications(cert_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS quality_culture (
                        culture_id TEXT PRIMARY KEY,
                        culture_name TEXT NOT NULL,
                        culture_type TEXT,
                        education_type TEXT,
                        status TEXT DEFAULT 'active',
                        description TEXT,
                        objectives TEXT,
                        created_by TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS culture_initiatives (
                        initiative_id TEXT PRIMARY KEY,
                        culture_id TEXT NOT NULL,
                        initiative_name TEXT NOT NULL,
                        education_type TEXT,
                        status TEXT DEFAULT 'planned',
                        start_date TEXT,
                        end_date TEXT,
                        responsible TEXT,
                        budget REAL DEFAULT 0,
                        description TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY (culture_id) REFERENCES quality_culture(culture_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS quality_audit (
                        audit_id TEXT PRIMARY KEY,
                        audit_name TEXT NOT NULL,
                        audit_type TEXT,
                        education_type TEXT,
                        audit_scope TEXT,
                        status TEXT DEFAULT 'planned',
                        start_date TEXT,
                        end_date TEXT,
                        auditor TEXT,
                        description TEXT,
                        created_by TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS audit_findings (
                        finding_id TEXT PRIMARY KEY,
                        audit_id TEXT NOT NULL,
                        finding_title TEXT NOT NULL,
                        education_type TEXT,
                        severity TEXT DEFAULT 'medium',
                        description TEXT,
                        recommendation TEXT,
                        status TEXT DEFAULT 'open',
                        deadline TEXT,
                        responsible TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY (audit_id) REFERENCES quality_audit(audit_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS quality_reports (
                        report_id TEXT PRIMARY KEY,
                        report_name TEXT NOT NULL,
                        report_type TEXT,
                        education_type TEXT,
                        period TEXT,
                        status TEXT DEFAULT 'draft',
                        content TEXT,
                        generated_by TEXT,
                        generated_at TEXT,
                        published_at TEXT,
                        archived INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS report_schedules (
                        schedule_id TEXT PRIMARY KEY,
                        report_type TEXT NOT NULL,
                        education_type TEXT,
                        frequency TEXT,
                        next_generation_date TEXT,
                        enabled INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS benchmarking_data (
                        data_id TEXT PRIMARY KEY,
                        education_type TEXT,
                        metric_code TEXT,
                        metric_name TEXT,
                        source TEXT,
                        period TEXT,
                        value REAL,
                        unit TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS benchmark_comparison (
                        comparison_id TEXT PRIMARY KEY,
                        education_type TEXT,
                        entity_id TEXT,
                        entity_name TEXT,
                        benchmark_data_id TEXT,
                        actual_value REAL,
                        gap REAL,
                        analysis TEXT,
                        created_at TEXT,
                        FOREIGN KEY (benchmark_data_id) REFERENCES benchmarking_data(data_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS quality_metrics (
                        metric_id TEXT PRIMARY KEY,
                        metric_name TEXT NOT NULL,
                        education_type TEXT,
                        metric_code TEXT,
                        calculation_method TEXT,
                        target_value REAL,
                        warning_threshold REAL,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS metric_data (
                        data_id TEXT PRIMARY KEY,
                        metric_id TEXT NOT NULL,
                        education_type TEXT,
                        period TEXT,
                        value REAL,
                        collected_at TEXT,
                        FOREIGN KEY (metric_id) REFERENCES quality_metrics(metric_id)
                    )
                ''')
                conn.commit()
                logger.info('教育质量保障服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 质量标准 ==========

    def create_standard(self, standard_name: str, standard_type: str,
                        education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            standard_id = f"std_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO quality_standards (
                            standard_id, standard_name, standard_type,
                            education_type, version, status, effective_date,
                            expiration_date, description, created_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?, ?)
                    ''', (standard_id, standard_name, standard_type, education_type,
                          kwargs.get('version', '1.0'),
                          kwargs.get('effective_date'), kwargs.get('expiration_date'),
                          kwargs.get('description'), kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建质量标准: {standard_name} ({standard_id})')
                    return {'success': True, 'standard_id': standard_id}
        except Exception as e:
            logger.error(f'创建质量标准失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_standard_item(self, standard_id: str, item_name: str,
                          **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT standard_id FROM quality_standards WHERE standard_id = ?', (standard_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '标准不存在'}
                    cursor.execute('''
                        INSERT INTO standard_items (standard_id, item_name, item_code, weight, description, requirement, status)
                        VALUES (?, ?, ?, ?, ?, ?, 'active')
                    ''', (standard_id, item_name, kwargs.get('item_code'),
                          kwargs.get('weight', 0), kwargs.get('description'),
                          kwargs.get('requirement')))
                    conn.commit()
                    return {'success': True, 'item_id': cursor.lastrowid}
        except Exception as e:
            logger.error(f'添加标准项失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_standard_version(self, standard_id: str, new_version: str,
                                **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE quality_standards SET version = ?, effective_date = ?, updated_at = ? WHERE standard_id = ?',
                                 (new_version, kwargs.get('effective_date'), now, standard_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'version': new_version}
                    return {'success': False, 'error': '标准不存在'}
        except Exception as e:
            logger.error(f'更新标准版本失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_standards(self, education_type: str = None, standard_type: str = None,
                       page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM quality_standards WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if standard_type:
                    query += ' AND standard_type = ?'
                    params.append(standard_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                standards = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'standards': standards, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取标准列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 质量监控 ==========

    def create_monitor_plan(self, monitor_name: str, monitor_method: str,
                            education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            monitor_id = f"mon_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = MONITORING_METHODS.get(monitor_method, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO quality_monitoring (
                            monitor_id, monitor_name, monitor_method, education_type,
                            frequency, scope, status, description, created_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?)
                    ''', (monitor_id, monitor_name, monitor_method, education_type,
                          kwargs.get('frequency', config.get('frequency', 'monthly')),
                          kwargs.get('scope', config.get('scope', 'comprehensive')),
                          kwargs.get('description'), kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建监控计划: {monitor_name} ({monitor_id})')
                    return {'success': True, 'monitor_id': monitor_id}
        except Exception as e:
            logger.error(f'创建监控计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_monitoring(self, monitor_id: str, check_date: str,
                          checker: str, education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"rec_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT monitor_id FROM quality_monitoring WHERE monitor_id = ?', (monitor_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '监控计划不存在'}
                    cursor.execute('''
                        INSERT INTO monitoring_records (
                            record_id, monitor_id, education_type, check_date, checker,
                            findings, status, risk_level, follow_up_required, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)
                    ''', (record_id, monitor_id, education_type, check_date, checker,
                          kwargs.get('findings'), kwargs.get('risk_level', 'medium'),
                          1 if kwargs.get('follow_up_required') else 0, now))
                    conn.commit()
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'记录监控结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_monitor_status(self, record_id: str, status: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE monitoring_records SET status = ?, updated_at = ? WHERE record_id = ?',
                                 (status, now, record_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '监控记录不存在'}
        except Exception as e:
            logger.error(f'更新监控状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_monitor_records(self, monitor_id: str = None, education_type: str = None,
                            page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM monitoring_records WHERE 1=1'
                params = []
                if monitor_id:
                    query += ' AND monitor_id = ?'
                    params.append(monitor_id)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY check_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取监控记录失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 质量评估 ==========

    def create_assessment(self, assessment_name: str, assessment_type: str,
                          education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            assessment_id = f"ast_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            criteria_config = json.dumps(kwargs.get('criteria_config', {}))
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO quality_assessment (
                            assessment_id, assessment_name, assessment_type,
                            education_type, criteria_config, status, start_date,
                            end_date, description, created_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 'draft', ?, ?, ?, ?, ?, ?)
                    ''', (assessment_id, assessment_name, assessment_type, education_type,
                          criteria_config, kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('description'), kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建评估方案: {assessment_name} ({assessment_id})')
                    return {'success': True, 'assessment_id': assessment_id}
        except Exception as e:
            logger.error(f'创建评估方案失败: {e}')
            return {'success': False, 'error': str(e)}

    def submit_assessment_score(self, assessment_id: str, entity_id: str,
                                entity_name: str, education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            score_id = f"sco_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT assessment_id FROM quality_assessment WHERE assessment_id = ?', (assessment_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '评估方案不存在'}
                    cursor.execute('''
                        INSERT INTO assessment_scores (
                            score_id, assessment_id, entity_id, entity_name,
                            education_type, criteria_code, score, max_score,
                            comments, scored_by, scored_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (score_id, assessment_id, entity_id, entity_name, education_type,
                          kwargs.get('criteria_code'), kwargs.get('score'),
                          kwargs.get('max_score', 100), kwargs.get('comments'),
                          kwargs.get('scored_by'), now))
                    conn.commit()
                    return {'success': True, 'score_id': score_id}
        except Exception as e:
            logger.error(f'提交评估分数失败: {e}')
            return {'success': False, 'error': str(e)}

    def calculate_assessment_result(self, assessment_id: str, entity_id: str,
                                    education_type: str = 'k12') -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT criteria_config FROM quality_assessment WHERE assessment_id = ?', (assessment_id,))
                config = cursor.fetchone()
                if not config:
                    return {'success': False, 'error': '评估方案不存在'}
                criteria_config = json.loads(config['criteria_config']) if config['criteria_config'] else {}
                cursor.execute('SELECT criteria_code, score, max_score FROM assessment_scores WHERE assessment_id = ? AND entity_id = ? AND education_type = ?',
                             (assessment_id, entity_id, education_type))
                scores = cursor.fetchall()
                if not scores:
                    return {'success': False, 'error': '没有评估分数记录'}
                total_weighted = 0
                total_weight = 0
                details = []
                for score in scores:
                    weight = criteria_config.get(score['criteria_code'], {}).get('weight', 0.125)
                    normalized = (score['score'] / score['max_score']) * 100 if score['max_score'] > 0 else 0
                    total_weighted += normalized * weight
                    total_weight += weight
                    details.append({
                        'criteria': score['criteria_code'],
                        'score': score['score'],
                        'max_score': score['max_score'],
                        'weight': weight,
                        'weighted_score': normalized * weight
                    })
                final_score = round(total_weighted / total_weight, 2) if total_weight > 0 else 0
                level = 'excellent' if final_score >= 90 else ('good' if final_score >= 80 else ('pass' if final_score >= 60 else 'fail'))
                return {'success': True, 'final_score': final_score, 'level': level, 'details': details}
        except Exception as e:
            logger.error(f'计算评估结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_assessment_results(self, assessment_id: str = None, education_type: str = None,
                               page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT DISTINCT entity_id, entity_name, education_type, MIN(scored_at) as first_scored FROM assessment_scores WHERE 1=1'
                params = []
                if assessment_id:
                    query += ' AND assessment_id = ?'
                    params.append(assessment_id)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' GROUP BY entity_id, entity_name, education_type'
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY first_scored DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                results = []
                for row in cursor.fetchall():
                    result = self.calculate_assessment_result(assessment_id, row['entity_id'], row['education_type']) if assessment_id else {}
                    results.append({
                        'entity_id': row['entity_id'],
                        'entity_name': row['entity_name'],
                        'education_type': row['education_type'],
                        'final_score': result.get('final_score'),
                        'level': result.get('level')
                    })
                return {'success': True, 'results': results, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取评估结果失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 质量改进 ==========

    def create_improvement_plan(self, improvement_name: str, improvement_model: str,
                                education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            improvement_id = f"imp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO quality_improvement (
                            improvement_id, improvement_name, education_type,
                            improvement_model, status, target, deadline,
                            responsible, description, created_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, 'planned', ?, ?, ?, ?, ?, ?, ?)
                    ''', (improvement_id, improvement_name, education_type, improvement_model,
                          kwargs.get('target'), kwargs.get('deadline'),
                          kwargs.get('responsible'), kwargs.get('description'),
                          kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建改进计划: {improvement_name} ({improvement_id})')
                    return {'success': True, 'improvement_id': improvement_id}
        except Exception as e:
            logger.error(f'创建改进计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_improvement_action(self, improvement_id: str, action_name: str,
                               **kwargs) -> Dict[str, Any]:
        try:
            action_id = f"act_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT improvement_id FROM quality_improvement WHERE improvement_id = ?', (improvement_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '改进计划不存在'}
                    cursor.execute('''
                        INSERT INTO improvement_actions (
                            action_id, improvement_id, action_name, phase,
                            status, deadline, responsible, resources, progress,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, 0, ?, ?)
                    ''', (action_id, improvement_id, action_name, kwargs.get('phase'),
                          kwargs.get('deadline'), kwargs.get('responsible'),
                          kwargs.get('resources'), now, now))
                    conn.commit()
                    return {'success': True, 'action_id': action_id}
        except Exception as e:
            logger.error(f'添加改进措施失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_action_progress(self, action_id: str, progress: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'completed' if progress >= 100 else ('in_progress' if progress > 0 else 'pending')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE improvement_actions SET progress = ?, status = ?, updated_at = ? WHERE action_id = ?',
                                 (progress, status, now, action_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'progress': progress, 'status': status}
                    return {'success': False, 'error': '改进措施不存在'}
        except Exception as e:
            logger.error(f'更新措施进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_improvement_status(self, improvement_id: str, status: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE quality_improvement SET status = ?, updated_at = ? WHERE improvement_id = ?',
                                 (status, now, improvement_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '改进计划不存在'}
        except Exception as e:
            logger.error(f'更新改进状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_improvement_summary(self, improvement_id: str, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM quality_improvement WHERE improvement_id = ?', (improvement_id,))
                plan = cursor.fetchone()
                if not plan:
                    return {'success': False, 'error': '改进计划不存在'}
                cursor.execute('SELECT action_id, action_name, phase, status, progress, deadline FROM improvement_actions WHERE improvement_id = ?', (improvement_id,))
                actions = [dict(a) for a in cursor.fetchall()]
                total_actions = len(actions)
                completed_actions = sum(1 for a in actions if a['status'] == 'completed')
                avg_progress = sum(a['progress'] for a in actions) / total_actions if total_actions > 0 else 0
                return {
                    'success': True,
                    'plan': dict(plan),
                    'actions': actions,
                    'total_actions': total_actions,
                    'completed_actions': completed_actions,
                    'overall_progress': round(avg_progress, 2)
                }
        except Exception as e:
            logger.error(f'获取改进汇总失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 认证认可 ==========

    def create_certification(self, cert_name: str, cert_type: str,
                             education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            cert_id = f"crt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = CERTIFICATION_TYPES.get(cert_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO certifications (
                            cert_id, cert_name, cert_type, education_type,
                            issuing_body, validity_period, status, description,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
                    ''', (cert_id, cert_name, cert_type, education_type,
                          kwargs.get('issuing_body', config.get('body', '')),
                          kwargs.get('validity_period', config.get('validity', 3)),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建认证类型: {cert_name} ({cert_id})')
                    return {'success': True, 'cert_id': cert_id}
        except Exception as e:
            logger.error(f'创建认证类型失败: {e}')
            return {'success': False, 'error': str(e)}

    def apply_certification(self, cert_id: str, entity_id: str,
                            entity_name: str, education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"cre_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT cert_id, validity_period FROM certifications WHERE cert_id = ?', (cert_id,))
                    cert = cursor.fetchone()
                    if not cert:
                        return {'success': False, 'error': '认证类型不存在'}
                    validity = cert[1]
                    exp_date = (datetime.now() + timedelta(days=validity * 365)).isoformat()[:10] if kwargs.get('certification_date') else None
                    cursor.execute('''
                        INSERT INTO certification_records (
                            record_id, cert_id, entity_id, entity_name,
                            education_type, application_date, certification_date,
                            expiration_date, status, certificate_no, issued_by, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'applied', ?, ?, ?)
                    ''', (record_id, cert_id, entity_id, entity_name, education_type,
                          now[:10], kwargs.get('certification_date'), exp_date,
                          kwargs.get('certificate_no'), kwargs.get('issued_by'), now))
                    conn.commit()
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'申请认证失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_certification_status(self, record_id: str, status: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    update_fields = ['status = ?']
                    update_params = [status]
                    if status == 'certified':
                        update_fields.append('certification_date = ?')
                        update_params.append(kwargs.get('certification_date', now[:10]))
                        update_fields.append('certificate_no = ?')
                        update_params.append(kwargs.get('certificate_no', f"CERT{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"))
                        update_fields.append('issued_by = ?')
                        update_params.append(kwargs.get('issued_by'))
                        update_fields.append('expiration_date = ?')
                        update_params.append(kwargs.get('expiration_date'))
                    update_params.append(record_id)
                    cursor.execute(f'UPDATE certification_records SET {", ".join(update_fields)} WHERE record_id = ?',
                                 update_params)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '认证记录不存在'}
        except Exception as e:
            logger.error(f'更新认证状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_certification_records(self, cert_id: str = None, education_type: str = None,
                                  status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM certification_records WHERE 1=1'
                params = []
                if cert_id:
                    query += ' AND cert_id = ?'
                    params.append(cert_id)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY application_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取认证记录失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 质量文化 ==========

    def create_culture_program(self, culture_name: str, culture_type: str,
                               education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            culture_id = f"cul_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO quality_culture (
                            culture_id, culture_name, culture_type, education_type,
                            status, description, objectives, created_by,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, 'active', ?, ?, ?, ?, ?)
                    ''', (culture_id, culture_name, culture_type, education_type,
                          kwargs.get('description'), kwargs.get('objectives'),
                          kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建质量文化项目: {culture_name} ({culture_id})')
                    return {'success': True, 'culture_id': culture_id}
        except Exception as e:
            logger.error(f'创建质量文化项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_culture_initiative(self, culture_id: str, initiative_name: str,
                               education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            initiative_id = f"ini_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT culture_id FROM quality_culture WHERE culture_id = ?', (culture_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '质量文化项目不存在'}
                    cursor.execute('''
                        INSERT INTO culture_initiatives (
                            initiative_id, culture_id, initiative_name, education_type,
                            status, start_date, end_date, responsible,
                            budget, description, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, 'planned', ?, ?, ?, ?, ?, ?, ?)
                    ''', (initiative_id, culture_id, initiative_name, education_type,
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('responsible'), kwargs.get('budget', 0),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    return {'success': True, 'initiative_id': initiative_id}
        except Exception as e:
            logger.error(f'添加文化举措失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_initiative_status(self, initiative_id: str, status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE culture_initiatives SET status = ?, updated_at = ? WHERE initiative_id = ?',
                                 (status, now, initiative_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '文化举措不存在'}
        except Exception as e:
            logger.error(f'更新举措状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_culture_summary(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM quality_culture WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                programs = [dict(p) for p in cursor.fetchall()]
                query = 'SELECT * FROM culture_initiatives WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                initiatives = [dict(i) for i in cursor.fetchall()]
                active_initiatives = sum(1 for i in initiatives if i['status'] == 'active')
                total_budget = sum(i['budget'] for i in initiatives)
                return {
                    'success': True,
                    'programs': programs,
                    'initiatives': initiatives,
                    'active_initiatives': active_initiatives,
                    'total_budget': round(total_budget, 2)
                }
        except Exception as e:
            logger.error(f'获取文化汇总失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 质量审计 ==========

    def create_audit_plan(self, audit_name: str, audit_type: str,
                          education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            audit_id = f"aud_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = AUDIT_FUNCTIONS.get(audit_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO quality_audit (
                            audit_id, audit_name, audit_type, education_type,
                            audit_scope, status, start_date, end_date,
                            auditor, description, created_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 'planned', ?, ?, ?, ?, ?, ?, ?)
                    ''', (audit_id, audit_name, audit_type, education_type,
                          kwargs.get('audit_scope', config.get('scope', '')),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('auditor'), kwargs.get('description'),
                          kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建审计计划: {audit_name} ({audit_id})')
                    return {'success': True, 'audit_id': audit_id}
        except Exception as e:
            logger.error(f'创建审计计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_audit_finding(self, audit_id: str, finding_title: str,
                          education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            finding_id = f"fin_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT audit_id FROM quality_audit WHERE audit_id = ?', (audit_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '审计计划不存在'}
                    cursor.execute('''
                        INSERT INTO audit_findings (
                            finding_id, audit_id, finding_title, education_type,
                            severity, description, recommendation, status,
                            deadline, responsible, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'open', ?, ?, ?, ?)
                    ''', (finding_id, audit_id, finding_title, education_type,
                          kwargs.get('severity', 'medium'), kwargs.get('description'),
                          kwargs.get('recommendation'), kwargs.get('deadline'),
                          kwargs.get('responsible'), now, now))
                    conn.commit()
                    return {'success': True, 'finding_id': finding_id}
        except Exception as e:
            logger.error(f'添加审计发现失败: {e}')
            return {'success': False, 'error': str(e)}

    def resolve_finding(self, finding_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE audit_findings SET status = ?, updated_at = ? WHERE finding_id = ?',
                                 ('resolved', now, finding_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'resolved'}
                    return {'success': False, 'error': '审计发现不存在'}
        except Exception as e:
            logger.error(f'解决审计发现失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_audit_results(self, audit_id: str = None, education_type: str = None,
                          page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM quality_audit WHERE 1=1'
                params = []
                if audit_id:
                    query += ' AND audit_id = ?'
                    params.append(audit_id)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY start_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                audits = []
                for audit in cursor.fetchall():
                    cursor.execute('SELECT COUNT(*) as cnt, SUM(CASE WHEN severity = ? THEN 1 ELSE 0 END) as critical FROM audit_findings WHERE audit_id = ?', ('critical', audit['audit_id']))
                    stats = cursor.fetchone()
                    cursor.execute('SELECT COUNT(*) as resolved FROM audit_findings WHERE audit_id = ? AND status = ?', (audit['audit_id'], 'resolved'))
                    resolved = cursor.fetchone()
                    audits.append({
                        'audit': dict(audit),
                        'total_findings': stats['cnt'] or 0,
                        'critical_findings': stats['critical'] or 0,
                        'resolved_findings': resolved['resolved'] or 0
                    })
                return {'success': True, 'audits': audits, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取审计结果失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 质量报告 ==========

    def generate_report(self, report_name: str, report_type: str,
                        education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            report_id = f"rpt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO quality_reports (
                            report_id, report_name, report_type, education_type,
                            period, status, content, generated_by, generated_at,
                            archived, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 'draft', ?, ?, ?, 0, ?, ?)
                    ''', (report_id, report_name, report_type, education_type,
                          kwargs.get('period'), kwargs.get('content', ''),
                          kwargs.get('generated_by'), now, now, now))
                    conn.commit()
                    logger.info(f'生成质量报告: {report_name} ({report_id})')
                    return {'success': True, 'report_id': report_id}
        except Exception as e:
            logger.error(f'生成报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def publish_report(self, report_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE quality_reports SET status = ?, published_at = ?, updated_at = ? WHERE report_id = ? AND status = ?',
                                 ('published', now, now, report_id, 'draft'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'published_at': now}
                    return {'success': False, 'error': '报告状态不允许发布'}
        except Exception as e:
            logger.error(f'发布报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def archive_report(self, report_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE quality_reports SET archived = 1, updated_at = ? WHERE report_id = ?',
                                 (now, report_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '报告不存在'}
        except Exception as e:
            logger.error(f'归档报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_reports(self, report_type: str = None, education_type: str = None,
                     status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM quality_reports WHERE archived = 0'
                params = []
                if report_type:
                    query += ' AND report_type = ?'
                    params.append(report_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY generated_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                reports = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'reports': reports, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取报告列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 标杆管理 ==========

    def add_benchmark_data(self, metric_code: str, metric_name: str,
                           education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            data_id = f"bmd_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO benchmarking_data (
                            data_id, education_type, metric_code, metric_name,
                            source, period, value, unit, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (data_id, education_type, metric_code, metric_name,
                          kwargs.get('source'), kwargs.get('period'),
                          kwargs.get('value'), kwargs.get('unit'), now))
                    conn.commit()
                    return {'success': True, 'data_id': data_id}
        except Exception as e:
            logger.error(f'添加标杆数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_benchmark_comparison(self, entity_id: str, entity_name: str,
                                 benchmark_data_id: str, education_type: str = 'k12', **kwargs) -> Dict[str, Any]:
        try:
            comparison_id = f"bmc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT value FROM benchmarking_data WHERE data_id = ?', (benchmark_data_id,))
                    benchmark = cursor.fetchone()
                    if not benchmark:
                        return {'success': False, 'error': '标杆数据不存在'}
                    benchmark_value = benchmark[0]
                    actual_value = kwargs.get('actual_value', 0)
                    gap = actual_value - benchmark_value
                    cursor.execute('''
                        INSERT INTO benchmark_comparison (
                            comparison_id, education_type, entity_id, entity_name,
                            benchmark_data_id, actual_value, gap, analysis, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (comparison_id, education_type, entity_id, entity_name,
                          benchmark_data_id, actual_value, gap,
                          kwargs.get('analysis'), now))
                    conn.commit()
                    return {'success': True, 'comparison_id': comparison_id, 'gap': gap}
        except Exception as e:
            logger.error(f'添加标杆对比失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_benchmark_summary(self, entity_id: str = None, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM benchmark_comparison WHERE 1=1'
                params = []
                if entity_id:
                    query += ' AND entity_id = ?'
                    params.append(entity_id)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                comparisons = [dict(c) for c in cursor.fetchall()]
                avg_gap = sum(c['gap'] for c in comparisons) / len(comparisons) if comparisons else 0
                positive_gap = sum(1 for c in comparisons if c['gap'] >= 0)
                return {
                    'success': True,
                    'comparisons': comparisons,
                    'total_metrics': len(comparisons),
                    'average_gap': round(avg_gap, 2),
                    'positive_gap_count': positive_gap,
                    'negative_gap_count': len(comparisons) - positive_gap
                }
        except Exception as e:
            logger.error(f'获取标杆汇总失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_benchmark_data(self, education_type: str = None,
                            page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM benchmarking_data WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY period DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                data = [dict(d) for d in cursor.fetchall()]
                return {'success': True, 'data': data, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取标杆数据失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 ==========

    def get_quality_statistics(self, education_type: str = None, period: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                stats = {}
                query_params = []
                edu_filter = ' AND education_type = ?' if education_type else ''
                if education_type:
                    query_params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM quality_standards WHERE status = ?{edu_filter}', ['active'] + query_params)
                stats['total_standards'] = cursor.fetchone()['cnt']
                cursor.execute(f'SELECT COUNT(*) as cnt FROM quality_monitoring WHERE status = ?{edu_filter}', ['active'] + query_params)
                stats['total_monitors'] = cursor.fetchone()['cnt']
                cursor.execute(f'SELECT COUNT(*) as cnt FROM monitoring_records WHERE status = ?{edu_filter}', ['completed'] + query_params)
                stats['completed_monitors'] = cursor.fetchone()['cnt']
                cursor.execute(f'SELECT COUNT(*) as cnt FROM quality_assessment WHERE status = ?{edu_filter}', ['completed'] + query_params)
                stats['completed_assessments'] = cursor.fetchone()['cnt']
                cursor.execute(f'SELECT AVG(score) as avg_score FROM assessment_scores WHERE education_type = ?', [education_type]) if education_type else cursor.execute('SELECT AVG(score) as avg_score FROM assessment_scores')
                avg = cursor.fetchone()['avg_score']
                stats['average_score'] = round(avg, 2) if avg else 0
                cursor.execute(f'SELECT COUNT(*) as cnt FROM quality_improvement WHERE status = ?{edu_filter}', ['completed'] + query_params)
                stats['completed_improvements'] = cursor.fetchone()['cnt']
                cursor.execute(f'SELECT COUNT(*) as cnt FROM certification_records WHERE status = ?{edu_filter}', ['certified'] + query_params)
                stats['certified_count'] = cursor.fetchone()['cnt']
                cursor.execute(f'SELECT COUNT(*) as cnt FROM quality_audit WHERE status = ?{edu_filter}', ['completed'] + query_params)
                stats['completed_audits'] = cursor.fetchone()['cnt']
                cursor.execute(f'SELECT COUNT(*) as cnt FROM audit_findings WHERE status = ?{edu_filter}', ['resolved'] + query_params)
                stats['resolved_findings'] = cursor.fetchone()['cnt']
                cursor.execute(f'SELECT COUNT(*) as cnt FROM quality_reports WHERE status = ?{edu_filter}', ['published'] + query_params)
                stats['published_reports'] = cursor.fetchone()['cnt']
                return {'success': True, 'statistics': stats}
        except Exception as e:
            logger.error(f'获取质量统计失败: {e}')
            return {'success': False, 'error': str(e)}