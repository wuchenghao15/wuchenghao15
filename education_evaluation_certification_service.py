#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育评价认证服务 (v15.26.0)
====================================
提供教育评价体系、认证标准管理、评价流程管理、认证审核管理、
评价结果分析、认证证书管理、评价数据统计、认证信息公开等综合管理服务。

核心能力：
1. 评价体系管理 - 评价类型、评价维度、评价指标体系
2. 认证标准管理 - 认证类型、标准级别、标准项管理
3. 评价流程管理 - 流程定义、流程记录、流程跟踪
4. 认证审核管理 - 审核方法、审核记录、审核结果
5. 评价结果分析 - 结果等级、结果详情、数据分析
6. 认证证书管理 - 证书类型、证书发放、证书验证
7. 评价数据统计 - 统计维度、统计数据、趋势分析
8. 认证信息公开 - 评价报告、认证结果、证书信息

支持教育类型：成人教育 / K12教育
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_evaluation_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationEvaluation')


# ========== 评价认证配置 ==========

EVALUATION_TYPES = {
    'school_running': {'name': '办学评价', 'description': '学校整体办学水平评价', 'education_types': ['adult', 'k12']},
    'teaching': {'name': '教学评价', 'description': '教学质量与效果评价', 'education_types': ['adult', 'k12']},
    'course': {'name': '课程评价', 'description': '课程建设与教学效果评价', 'education_types': ['adult', 'k12']},
    'teacher': {'name': '教师评价', 'description': '教师教学能力与素养评价', 'education_types': ['adult', 'k12']},
    'student': {'name': '学生评价', 'description': '学生学习成果与发展评价', 'education_types': ['adult', 'k12']},
    'management': {'name': '管理评价', 'description': '学校管理水平与效能评价', 'education_types': ['adult', 'k12']},
    'quality': {'name': '质量评价', 'description': '教育质量保障体系评价', 'education_types': ['adult', 'k12']},
    'development': {'name': '发展评价', 'description': '学校发展潜力与趋势评价', 'education_types': ['adult', 'k12']}
}

CERTIFICATION_TYPES = {
    'school': {'name': '学校认证', 'description': '学校办学资质认证', 'education_types': ['adult', 'k12']},
    'major': {'name': '专业认证', 'description': '专业建设水平认证', 'education_types': ['adult', 'k12']},
    'course': {'name': '课程认证', 'description': '课程质量标准认证', 'education_types': ['adult', 'k12']},
    'teacher': {'name': '教师认证', 'description': '教师专业资格认证', 'education_types': ['adult', 'k12']},
    'student': {'name': '学生认证', 'description': '学生学业成就认证', 'education_types': ['adult', 'k12']},
    'quality': {'name': '质量认证', 'description': '教育质量保障体系认证', 'education_types': ['adult', 'k12']},
    'qualification': {'name': '资格认证', 'description': '职业资格与能力认证', 'education_types': ['adult', 'k12']},
    'international': {'name': '国际认证', 'description': '国际教育标准认证', 'education_types': ['adult', 'k12']}
}

STANDARD_LEVELS = {
    'national': {'name': '国家标准', 'description': '国家统一制定的评价标准', 'priority': 1},
    'industry': {'name': '行业标准', 'description': '教育行业规范标准', 'priority': 2},
    'local': {'name': '地方标准', 'description': '地方教育主管部门制定标准', 'priority': 3},
    'school': {'name': '学校标准', 'description': '学校自主制定标准', 'priority': 4},
    'international': {'name': '国际标准', 'description': '国际教育认证标准', 'priority': 1},
    'regional': {'name': '区域标准', 'description': '特定区域教育标准', 'priority': 3},
    'discipline': {'name': '学科标准', 'description': '学科专业评价标准', 'priority': 2},
    'professional': {'name': '专业标准', 'description': '职业教育专业标准', 'priority': 2}
}

EVALUATION_DIMENSIONS = {
    'facilities': {'name': '办学条件', 'description': '学校硬件设施与资源条件', 'weight': 0.15},
    'faculty': {'name': '师资队伍', 'description': '教师队伍结构与水平', 'weight': 0.20},
    'teaching_quality': {'name': '教学质量', 'description': '教学过程与效果', 'weight': 0.25},
    'research': {'name': '科研水平', 'description': '科研能力与成果', 'weight': 0.10},
    'management': {'name': '管理水平', 'description': '学校管理效能', 'weight': 0.10},
    'reputation': {'name': '社会声誉', 'description': '社会认可度与影响力', 'weight': 0.10},
    'potential': {'name': '发展潜力', 'description': '未来发展能力', 'weight': 0.05},
    'innovation': {'name': '创新能力', 'description': '教育创新与改革', 'weight': 0.05}
}

AUDIT_METHODS = {
    'document': {'name': '材料审核', 'description': '审查提交的书面材料', 'required': True},
    'onsite': {'name': '实地考察', 'description': '现场实地检查评估', 'required': False},
    'survey': {'name': '问卷调查', 'description': '通过问卷收集数据', 'required': False},
    'expert': {'name': '专家评审', 'description': '专家委员会评审', 'required': True},
    'peer': {'name': '同行评议', 'description': '同行专家评价', 'required': False},
    'data': {'name': '数据分析', 'description': '定量数据分析评估', 'required': True},
    'third_party': {'name': '第三方评估', 'description': '独立第三方机构评估', 'required': False},
    'comprehensive': {'name': '综合评价', 'description': '多种方法综合评估', 'required': True}
}

RESULT_LEVELS = {
    'excellent': {'name': '优秀', 'description': '远超标准要求', 'score_range': [90, 100]},
    'good': {'name': '良好', 'description': '达到标准要求', 'score_range': [80, 89]},
    'qualified': {'name': '合格', 'description': '基本达到标准要求', 'score_range': [60, 79]},
    'basically_qualified': {'name': '基本合格', 'description': '接近标准要求', 'score_range': [50, 59]},
    'unqualified': {'name': '不合格', 'description': '未达到标准要求', 'score_range': [0, 49]},
    'pending_improvement': {'name': '待改进', 'description': '需要改进后重新评估', 'score_range': None},
    'deferred': {'name': '暂缓通过', 'description': '暂缓认证通过', 'score_range': None},
    'reassessment': {'name': '重新评估', 'description': '需重新进行评估', 'score_range': None}
}

CERTIFICATE_TYPES = {
    'certification': {'name': '认证证书', 'description': '教育认证合格证书', 'valid_years': 3},
    'qualification': {'name': '资格证书', 'description': '专业资格证书', 'valid_years': 5},
    'training': {'name': '培训证书', 'description': '培训结业证明', 'valid_years': None},
    'completion': {'name': '结业证书', 'description': '课程学习结业证明', 'valid_years': None},
    'graduation': {'name': '毕业证书', 'description': '学历教育毕业证明', 'valid_years': None},
    'degree': {'name': '学位证书', 'description': '学位授予证明', 'valid_years': None},
    'honor': {'name': '荣誉证书', 'description': '表彰荣誉证明', 'valid_years': None},
    'qualification_card': {'name': '资格证', 'description': '职业资格证明', 'valid_years': 3}
}

PUBLICATION_TYPES = {
    'report': {'name': '评价报告', 'description': '详细评价分析报告', 'public': True},
    'result': {'name': '认证结果', 'description': '认证结论与等级', 'public': True},
    'certificate': {'name': '证书信息', 'description': '证书发放信息', 'public': False},
    'standard': {'name': '评价标准', 'description': '评价指标与标准', 'public': True},
    'process': {'name': '审核流程', 'description': '认证审核流程说明', 'public': True},
    'expert': {'name': '专家信息', 'description': '评审专家信息', 'public': False},
    'fee': {'name': '评估费用', 'description': '认证评估费用标准', 'public': True},
    'contact': {'name': '联系方式', 'description': '认证机构联系方式', 'public': True}
}


class EducationEvaluationCertificationService:
    """教育评价认证服务"""

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
                    CREATE TABLE IF NOT EXISTS evaluation_system (
                        system_id TEXT PRIMARY KEY,
                        system_name TEXT NOT NULL,
                        evaluation_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_config (
                        config_id TEXT PRIMARY KEY,
                        system_id TEXT NOT NULL,
                        config_key TEXT NOT NULL,
                        config_value TEXT,
                        description TEXT,
                        created_at TEXT,
                        FOREIGN KEY(system_id) REFERENCES evaluation_system(system_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS certification_standards (
                        standard_id TEXT PRIMARY KEY,
                        standard_name TEXT NOT NULL,
                        certification_type TEXT NOT NULL,
                        standard_level TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        description TEXT,
                        version TEXT DEFAULT '1.0',
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS standard_items (
                        item_id TEXT PRIMARY KEY,
                        standard_id TEXT NOT NULL,
                        item_name TEXT NOT NULL,
                        item_code TEXT,
                        weight REAL DEFAULT 0.0,
                        criteria TEXT,
                        score_max INTEGER DEFAULT 100,
                        education_type TEXT NOT NULL,
                        created_at TEXT,
                        FOREIGN KEY(standard_id) REFERENCES certification_standards(standard_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS evaluation_process (
                        process_id TEXT PRIMARY KEY,
                        process_name TEXT NOT NULL,
                        evaluation_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        steps TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS process_records (
                        record_id TEXT PRIMARY KEY,
                        process_id TEXT NOT NULL,
                        entity_id TEXT NOT NULL,
                        entity_type TEXT,
                        current_step TEXT,
                        step_status TEXT DEFAULT 'pending',
                        education_type TEXT NOT NULL,
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY(process_id) REFERENCES evaluation_process(process_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS certification_audit (
                        audit_id TEXT PRIMARY KEY,
                        audit_name TEXT NOT NULL,
                        certification_type TEXT NOT NULL,
                        audit_method TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        description TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS audit_records (
                        record_id TEXT PRIMARY KEY,
                        audit_id TEXT NOT NULL,
                        auditor_id INTEGER,
                        auditor_name TEXT,
                        audit_date TEXT,
                        findings TEXT,
                        recommendation TEXT,
                        education_type TEXT NOT NULL,
                        created_at TEXT,
                        FOREIGN KEY(audit_id) REFERENCES certification_audit(audit_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS evaluation_results (
                        result_id TEXT PRIMARY KEY,
                        evaluation_id TEXT NOT NULL,
                        evaluation_type TEXT NOT NULL,
                        entity_id TEXT NOT NULL,
                        entity_name TEXT,
                        overall_score REAL,
                        result_level TEXT,
                        education_type TEXT NOT NULL,
                        status TEXT DEFAULT 'completed',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS result_details (
                        detail_id TEXT PRIMARY KEY,
                        result_id TEXT NOT NULL,
                        dimension TEXT NOT NULL,
                        score REAL,
                        weight REAL,
                        comments TEXT,
                        education_type TEXT NOT NULL,
                        created_at TEXT,
                        FOREIGN KEY(result_id) REFERENCES evaluation_results(result_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS certification_certificates (
                        certificate_id TEXT PRIMARY KEY,
                        certificate_no TEXT NOT NULL UNIQUE,
                        certificate_type TEXT NOT NULL,
                        certification_type TEXT NOT NULL,
                        entity_id TEXT NOT NULL,
                        entity_name TEXT,
                        education_type TEXT NOT NULL,
                        issue_date TEXT,
                        expire_date TEXT,
                        status TEXT DEFAULT 'valid',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS certificate_records (
                        record_id TEXT PRIMARY KEY,
                        certificate_id TEXT NOT NULL,
                        action_type TEXT NOT NULL,
                        action_date TEXT,
                        operator_id INTEGER,
                        operator_name TEXT,
                        notes TEXT,
                        created_at TEXT,
                        FOREIGN KEY(certificate_id) REFERENCES certification_certificates(certificate_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS evaluation_statistics (
                        stat_id TEXT PRIMARY KEY,
                        stat_name TEXT NOT NULL,
                        stat_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        time_range TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS stat_data (
                        data_id TEXT PRIMARY KEY,
                        stat_id TEXT NOT NULL,
                        data_key TEXT NOT NULL,
                        data_value REAL,
                        data_date TEXT,
                        education_type TEXT NOT NULL,
                        created_at TEXT,
                        FOREIGN KEY(stat_id) REFERENCES evaluation_statistics(stat_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS certification_publication (
                        pub_id TEXT PRIMARY KEY,
                        pub_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        content TEXT,
                        education_type TEXT NOT NULL,
                        is_public INTEGER DEFAULT 1,
                        publish_date TEXT,
                        status TEXT DEFAULT 'published',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS publication_records (
                        record_id TEXT PRIMARY KEY,
                        pub_id TEXT NOT NULL,
                        view_count INTEGER DEFAULT 0,
                        download_count INTEGER DEFAULT 0,
                        last_access_date TEXT,
                        created_at TEXT,
                        FOREIGN KEY(pub_id) REFERENCES certification_publication(pub_id)
                    )
                ''')
                conn.commit()
                logger.info('教育评价认证服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 评价体系管理 ==========

    def create_evaluation_system(self, system_name: str, evaluation_type: str,
                                  education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            system_id = f"evs_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO evaluation_system (
                            system_id, system_name, evaluation_type,
                            education_type, description, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (system_id, system_name, evaluation_type,
                          education_type, kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建评价体系: {system_name} ({system_id})')
                    return {'success': True, 'system_id': system_id}
        except Exception as e:
            logger.error(f'创建评价体系失败: {e}')
            return {'success': False, 'error': str(e)}

    def configure_system(self, system_id: str, config_key: str,
                          config_value: str, **kwargs) -> Dict[str, Any]:
        try:
            config_id = f"cfg_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO system_config (
                            config_id, system_id, config_key, config_value,
                            description, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (config_id, system_id, config_key, config_value,
                          kwargs.get('description'), now))
                    conn.commit()
                    return {'success': True, 'config_id': config_id}
        except Exception as e:
            logger.error(f'配置评价体系失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_evaluation_system(self, system_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM evaluation_system WHERE system_id = ?', (system_id,))
                system = cursor.fetchone()
                if not system:
                    return {'success': False, 'error': '评价体系不存在'}
                cursor.execute('SELECT * FROM system_config WHERE system_id = ?', (system_id,))
                configs = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'system': dict(system), 'configs': configs}
        except Exception as e:
            logger.error(f'获取评价体系失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_evaluation_systems(self, education_type: str = None,
                                 evaluation_type: str = None,
                                 page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM evaluation_system WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if evaluation_type:
                    query += ' AND evaluation_type = ?'
                    params.append(evaluation_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                systems = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'systems': systems, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取评价体系列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 认证标准管理 ==========

    def create_certification_standard(self, standard_name: str,
                                       certification_type: str,
                                       standard_level: str,
                                       education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            standard_id = f"std_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO certification_standards (
                            standard_id, standard_name, certification_type,
                            standard_level, education_type, description,
                            version, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, '1.0', 'active', ?, ?)
                    ''', (standard_id, standard_name, certification_type,
                          standard_level, education_type, kwargs.get('description'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建认证标准: {standard_name} ({standard_id})')
                    return {'success': True, 'standard_id': standard_id}
        except Exception as e:
            logger.error(f'创建认证标准失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_standard_item(self, standard_id: str, item_name: str,
                           education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            item_id = f"sit_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO standard_items (
                            item_id, standard_id, item_name, item_code,
                            weight, criteria, score_max, education_type, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (item_id, standard_id, item_name, kwargs.get('item_code'),
                          kwargs.get('weight', 0.0), kwargs.get('criteria'),
                          kwargs.get('score_max', 100), education_type, now))
                    conn.commit()
                    return {'success': True, 'item_id': item_id}
        except Exception as e:
            logger.error(f'添加标准项失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_certification_standard(self, standard_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM certification_standards WHERE standard_id = ?', (standard_id,))
                standard = cursor.fetchone()
                if not standard:
                    return {'success': False, 'error': '认证标准不存在'}
                cursor.execute('SELECT * FROM standard_items WHERE standard_id = ?', (standard_id,))
                items = [dict(i) for i in cursor.fetchall()]
                return {'success': True, 'standard': dict(standard), 'items': items}
        except Exception as e:
            logger.error(f'获取认证标准失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_certification_standards(self, education_type: str = None,
                                      certification_type: str = None,
                                      page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM certification_standards WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if certification_type:
                    query += ' AND certification_type = ?'
                    params.append(certification_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                standards = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'standards': standards, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取认证标准列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 评价流程管理 ==========

    def create_evaluation_process(self, process_name: str, evaluation_type: str,
                                   education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            process_id = f"prc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            steps = json.dumps(kwargs.get('steps', []))
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO evaluation_process (
                            process_id, process_name, evaluation_type,
                            education_type, steps, description, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (process_id, process_name, evaluation_type,
                          education_type, steps, kwargs.get('description'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建评价流程: {process_name} ({process_id})')
                    return {'success': True, 'process_id': process_id}
        except Exception as e:
            logger.error(f'创建评价流程失败: {e}')
            return {'success': False, 'error': str(e)}

    def start_process(self, process_id: str, entity_id: str,
                       education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"prr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT steps FROM evaluation_process WHERE process_id = ?', (process_id,))
                    process = cursor.fetchone()
                    if not process:
                        return {'success': False, 'error': '评价流程不存在'}
                    steps = json.loads(process[0]) if process[0] else []
                    current_step = steps[0]['name'] if steps else 'init'
                    cursor.execute('''
                        INSERT INTO process_records (
                            record_id, process_id, entity_id, entity_type,
                            current_step, step_status, education_type,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?)
                    ''', (record_id, process_id, entity_id, kwargs.get('entity_type'),
                          current_step, education_type, now, now))
                    conn.commit()
                    return {'success': True, 'record_id': record_id, 'current_step': current_step}
        except Exception as e:
            logger.error(f'启动评价流程失败: {e}')
            return {'success': False, 'error': str(e)}

    def advance_process(self, record_id: str, step_status: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT process_id, current_step FROM process_records WHERE record_id = ?', (record_id,))
                    record = cursor.fetchone()
                    if not record:
                        return {'success': False, 'error': '流程记录不存在'}
                    cursor.execute('SELECT steps FROM evaluation_process WHERE process_id = ?', (record[0],))
                    process = cursor.fetchone()
                    if not process:
                        return {'success': False, 'error': '评价流程不存在'}
                    steps = json.loads(process[0]) if process[0] else []
                    current_idx = next((i for i, s in enumerate(steps) if s.get('name') == record[1]), -1)
                    next_step = steps[current_idx + 1]['name'] if current_idx >= 0 and current_idx + 1 < len(steps) else 'completed'
                    cursor.execute('''
                        UPDATE process_records SET
                            step_status = ?, current_step = ?, updated_at = ?
                        WHERE record_id = ?
                    ''', (step_status, next_step, now, record_id))
                    conn.commit()
                    return {'success': True, 'current_step': next_step, 'step_status': step_status}
        except Exception as e:
            logger.error(f'推进评价流程失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_process_status(self, record_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM process_records WHERE record_id = ?', (record_id,))
                record = cursor.fetchone()
                if not record:
                    return {'success': False, 'error': '流程记录不存在'}
                cursor.execute('SELECT steps FROM evaluation_process WHERE process_id = ?', (record['process_id'],))
                process = cursor.fetchone()
                steps = json.loads(process['steps']) if process and process['steps'] else []
                return {'success': True, 'record': dict(record), 'steps': steps}
        except Exception as e:
            logger.error(f'获取流程状态失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 认证审核管理 ==========

    def create_certification_audit(self, audit_name: str, certification_type: str,
                                    audit_method: str, education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            audit_id = f"adt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO certification_audit (
                            audit_id, audit_name, certification_type,
                            audit_method, education_type, description,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                    ''', (audit_id, audit_name, certification_type,
                          audit_method, education_type, kwargs.get('description'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建认证审核: {audit_name} ({audit_id})')
                    return {'success': True, 'audit_id': audit_id}
        except Exception as e:
            logger.error(f'创建认证审核失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_audit_record(self, audit_id: str, auditor_id: int, auditor_name: str,
                         education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"adr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO audit_records (
                            record_id, audit_id, auditor_id, auditor_name,
                            audit_date, findings, recommendation,
                            education_type, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (record_id, audit_id, auditor_id, auditor_name,
                          kwargs.get('audit_date', now[:10]),
                          kwargs.get('findings'), kwargs.get('recommendation'),
                          education_type, now))
                    conn.commit()
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'添加审核记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_audit_status(self, audit_id: str, status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE certification_audit SET
                            status = ?, updated_at = ?
                        WHERE audit_id = ?
                    ''', (status, now, audit_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '审核不存在'}
        except Exception as e:
            logger.error(f'更新审核状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_audit_details(self, audit_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM certification_audit WHERE audit_id = ?', (audit_id,))
                audit = cursor.fetchone()
                if not audit:
                    return {'success': False, 'error': '审核不存在'}
                cursor.execute('SELECT * FROM audit_records WHERE audit_id = ?', (audit_id,))
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'audit': dict(audit), 'records': records}
        except Exception as e:
            logger.error(f'获取审核详情失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_audits(self, education_type: str = None, certification_type: str = None,
                     status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM certification_audit WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if certification_type:
                    query += ' AND certification_type = ?'
                    params.append(certification_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                audits = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'audits': audits, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取审核列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 结果分析管理 ==========

    def create_evaluation_result(self, evaluation_type: str, entity_id: str,
                                  education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            result_id = f"evr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            score = kwargs.get('overall_score', 0)
            if score >= 90:
                level = 'excellent'
            elif score >= 80:
                level = 'good'
            elif score >= 60:
                level = 'qualified'
            elif score >= 50:
                level = 'basically_qualified'
            else:
                level = 'unqualified'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO evaluation_results (
                            result_id, evaluation_id, evaluation_type,
                            entity_id, entity_name, overall_score,
                            result_level, education_type, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'completed', ?, ?)
                    ''', (result_id, kwargs.get('evaluation_id', ''),
                          evaluation_type, entity_id, kwargs.get('entity_name'),
                          score, level, education_type, now, now))
                    if kwargs.get('details'):
                        for detail in kwargs['details']:
                            detail_id = f"det_{uuid.uuid4().hex[:12]}"
                            cursor.execute('''
                                INSERT INTO result_details (
                                    detail_id, result_id, dimension, score,
                                    weight, comments, education_type, created_at
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (detail_id, result_id, detail.get('dimension'),
                                  detail.get('score'), detail.get('weight'),
                                  detail.get('comments'), education_type, now))
                    conn.commit()
                    logger.info(f'创建评价结果: {result_id}')
                    return {'success': True, 'result_id': result_id, 'result_level': level}
        except Exception as e:
            logger.error(f'创建评价结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def analyze_result(self, result_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM evaluation_results WHERE result_id = ?', (result_id,))
                result = cursor.fetchone()
                if not result:
                    return {'success': False, 'error': '评价结果不存在'}
                cursor.execute('SELECT * FROM result_details WHERE result_id = ?', (result_id,))
                details = [dict(d) for d in cursor.fetchall()]
                weak_dimensions = [d for d in details if d['score'] < 60]
                strong_dimensions = [d for d in details if d['score'] >= 85]
                return {
                    'success': True,
                    'result': dict(result),
                    'details': details,
                    'weak_dimensions': weak_dimensions,
                    'strong_dimensions': strong_dimensions,
                    'analysis_summary': f"总体评价等级为{RESULT_LEVELS.get(result['result_level'], {}).get('name', '')}，共发现{len(weak_dimensions)}个待改进维度，{len(strong_dimensions)}个优势维度"
                }
        except Exception as e:
            logger.error(f'分析评价结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_result_by_entity(self, entity_id: str, evaluation_type: str = None,
                             education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM evaluation_results WHERE entity_id = ?'
                params = [entity_id]
                if evaluation_type:
                    query += ' AND evaluation_type = ?'
                    params.append(evaluation_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                query += ' ORDER BY created_at DESC'
                cursor.execute(query, params)
                results = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'results': results}
        except Exception as e:
            logger.error(f'获取实体评价结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_results(self, education_type: str = None, result_level: str = None,
                      page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM evaluation_results WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if result_level:
                    query += ' AND result_level = ?'
                    params.append(result_level)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                results = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'results': results, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取评价结果列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 证书管理 ==========

    def issue_certificate(self, certificate_type: str, certification_type: str,
                           entity_id: str, entity_name: str, education_type: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            certificate_id = f"crt_{uuid.uuid4().hex[:12]}"
            certificate_no = f"CERT{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}"
            now = datetime.now().isoformat()
            valid_years = CERTIFICATE_TYPES.get(certificate_type, {}).get('valid_years')
            expire_date = (datetime.now() + timedelta(days=valid_years * 365)).isoformat()[:10] if valid_years else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO certification_certificates (
                            certificate_id, certificate_no, certificate_type,
                            certification_type, entity_id, entity_name,
                            education_type, issue_date, expire_date,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'valid', ?, ?)
                    ''', (certificate_id, certificate_no, certificate_type,
                          certification_type, entity_id, entity_name,
                          education_type, kwargs.get('issue_date', now[:10]),
                          expire_date, now, now))
                    record_id = f"crr_{uuid.uuid4().hex[:12]}"
                    cursor.execute('''
                        INSERT INTO certificate_records (
                            record_id, certificate_id, action_type,
                            action_date, operator_id, operator_name,
                            notes, created_at
                        ) VALUES (?, ?, 'issued', ?, ?, ?, ?, ?)
                    ''', (record_id, certificate_id, now[:10],
                          kwargs.get('operator_id'), kwargs.get('operator_name'),
                          '证书已发放', now))
                    conn.commit()
                    logger.info(f'发放证书: {certificate_no} ({certificate_id})')
                    return {'success': True, 'certificate_id': certificate_id, 'certificate_no': certificate_no}
        except Exception as e:
            logger.error(f'发放证书失败: {e}')
            return {'success': False, 'error': str(e)}

    def verify_certificate(self, certificate_no: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM certification_certificates WHERE certificate_no = ?', (certificate_no,))
                certificate = cursor.fetchone()
                if not certificate:
                    return {'success': False, 'error': '证书不存在'}
                cursor.execute('SELECT * FROM certificate_records WHERE certificate_id = ? ORDER BY action_date DESC', (certificate['certificate_id'],))
                records = [dict(r) for r in cursor.fetchall()]
                is_valid = certificate['status'] == 'valid' and (not certificate['expire_date'] or certificate['expire_date'] >= datetime.now().isoformat()[:10])
                return {
                    'success': True,
                    'certificate': dict(certificate),
                    'is_valid': is_valid,
                    'records': records
                }
        except Exception as e:
            logger.error(f'验证证书失败: {e}')
            return {'success': False, 'error': str(e)}

    def revoke_certificate(self, certificate_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE certification_certificates SET status = ?, updated_at = ? WHERE certificate_id = ?',
                                  ('revoked', now, certificate_id))
                    if cursor.rowcount > 0:
                        record_id = f"crr_{uuid.uuid4().hex[:12]}"
                        cursor.execute('''
                            INSERT INTO certificate_records (
                                record_id, certificate_id, action_type,
                                action_date, operator_id, operator_name,
                                notes, created_at
                            ) VALUES (?, ?, 'revoked', ?, ?, ?, ?, ?)
                        ''', (record_id, certificate_id, now[:10],
                              kwargs.get('operator_id'), kwargs.get('operator_name'),
                              kwargs.get('notes', '证书已撤销'), now))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '证书不存在'}
        except Exception as e:
            logger.error(f'撤销证书失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_certificates(self, education_type: str = None, certificate_type: str = None,
                           status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM certification_certificates WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if certificate_type:
                    query += ' AND certificate_type = ?'
                    params.append(certificate_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY issue_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                certificates = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'certificates': certificates, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取证书列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 数据统计 ==========

    def create_statistics(self, stat_name: str, stat_type: str, education_type: str,
                          **kwargs) -> Dict[str, Any]:
        try:
            stat_id = f"stt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO evaluation_statistics (
                            stat_id, stat_name, stat_type, education_type,
                            time_range, description, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (stat_id, stat_name, stat_type, education_type,
                          kwargs.get('time_range'), kwargs.get('description'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建统计任务: {stat_name} ({stat_id})')
                    return {'success': True, 'stat_id': stat_id}
        except Exception as e:
            logger.error(f'创建统计任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_stat_data(self, stat_id: str, data_key: str, data_value: float,
                       education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            data_id = f"std_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO stat_data (
                            data_id, stat_id, data_key, data_value,
                            data_date, education_type, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (data_id, stat_id, data_key, data_value,
                          kwargs.get('data_date', now[:10]), education_type, now))
                    conn.commit()
                    return {'success': True, 'data_id': data_id}
        except Exception as e:
            logger.error(f'添加统计数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_stat_data(self, stat_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM evaluation_statistics WHERE stat_id = ?', (stat_id,))
                stat = cursor.fetchone()
                if not stat:
                    return {'success': False, 'error': '统计任务不存在'}
                cursor.execute('SELECT * FROM stat_data WHERE stat_id = ? ORDER BY data_date', (stat_id,))
                data = [dict(d) for d in cursor.fetchall()]
                return {'success': True, 'stat': dict(stat), 'data': data}
        except Exception as e:
            logger.error(f'获取统计数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def calculate_trend(self, stat_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT data_date, data_value FROM stat_data WHERE stat_id = ? ORDER BY data_date', (stat_id,))
                rows = cursor.fetchall()
                if len(rows) < 2:
                    return {'success': False, 'error': '数据不足，无法计算趋势'}
                values = [r[1] for r in rows]
                dates = [r[0] for r in rows]
                trend = (values[-1] - values[0]) / len(values)
                direction = 'up' if trend > 0 else ('down' if trend < 0 else 'stable')
                return {
                    'success': True,
                    'trend': trend,
                    'direction': direction,
                    'data_points': len(values),
                    'start_value': values[0],
                    'end_value': values[-1],
                    'growth_rate': round((values[-1] - values[0]) / values[0] * 100, 2) if values[0] != 0 else 0
                }
        except Exception as e:
            logger.error(f'计算趋势失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 信息公开 ==========

    def create_publication(self, pub_type: str, title: str, content: str,
                            education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            pub_id = f"pub_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            is_public = PUBLICATION_TYPES.get(pub_type, {}).get('public', True)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO certification_publication (
                            pub_id, pub_type, title, content,
                            education_type, is_public, publish_date,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'published', ?, ?)
                    ''', (pub_id, pub_type, title, content, education_type,
                          1 if is_public else 0, kwargs.get('publish_date', now[:10]),
                          now, now))
                    record_id = f"pbr_{uuid.uuid4().hex[:12]}"
                    cursor.execute('''
                        INSERT INTO publication_records (
                            record_id, pub_id, view_count, download_count,
                            last_access_date, created_at
                        ) VALUES (?, ?, 0, 0, NULL, ?)
                    ''', (record_id, pub_id, now))
                    conn.commit()
                    logger.info(f'创建公开信息: {title} ({pub_id})')
                    return {'success': True, 'pub_id': pub_id}
        except Exception as e:
            logger.error(f'创建公开信息失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_publication(self, pub_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM certification_publication WHERE pub_id = ?', (pub_id,))
                pub = cursor.fetchone()
                if not pub:
                    return {'success': False, 'error': '公开信息不存在'}
                cursor.execute('SELECT * FROM publication_records WHERE pub_id = ?', (pub_id,))
                record = cursor.fetchone()
                return {'success': True, 'publication': dict(pub), 'record': dict(record) if record else None}
        except Exception as e:
            logger.error(f'获取公开信息失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_publications(self, education_type: str = None, pub_type: str = None,
                           is_public: bool = True, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM certification_publication WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if pub_type:
                    query += ' AND pub_type = ?'
                    params.append(pub_type)
                if is_public is not None:
                    query += ' AND is_public = ?'
                    params.append(1 if is_public else 0)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY publish_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                pubs = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'publications': pubs, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取公开信息列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_access_count(self, pub_id: str, access_type: str = 'view') -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    if access_type == 'view':
                        cursor.execute('''
                            UPDATE publication_records SET
                                view_count = view_count + 1,
                                last_access_date = ?
                            WHERE pub_id = ?
                        ''', (now[:10], pub_id))
                    else:
                        cursor.execute('''
                            UPDATE publication_records SET
                                download_count = download_count + 1,
                                last_access_date = ?
                            WHERE pub_id = ?
                        ''', (now[:10], pub_id))
                    conn.commit()
                    cursor.execute('SELECT view_count, download_count FROM publication_records WHERE pub_id = ?', (pub_id,))
                    record = cursor.fetchone()
                    return {'success': True, 'view_count': record[0], 'download_count': record[1]}
        except Exception as e:
            logger.error(f'更新访问计数失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 综合统计 ==========

    def get_comprehensive_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                results = {}
                query_filter = f" AND education_type = '{education_type}'" if education_type else ""
                cursor.execute(f"SELECT COUNT(*) FROM evaluation_system WHERE status = 'active'{query_filter}")
                results['evaluation_systems'] = cursor.fetchone()[0]
                cursor.execute(f"SELECT COUNT(*) FROM certification_standards WHERE status = 'active'{query_filter}")
                results['certification_standards'] = cursor.fetchone()[0]
                cursor.execute(f"SELECT COUNT(*) FROM evaluation_results WHERE status = 'completed'{query_filter}")
                results['completed_evaluations'] = cursor.fetchone()[0]
                cursor.execute(f"SELECT COUNT(*) FROM certification_certificates WHERE status = 'valid'{query_filter}")
                results['valid_certificates'] = cursor.fetchone()[0]
                cursor.execute(f"SELECT COUNT(*) FROM certification_audit WHERE status = 'completed'{query_filter}")
                results['completed_audits'] = cursor.fetchone()[0]
                cursor.execute(f"SELECT AVG(overall_score) FROM evaluation_results WHERE status = 'completed'{query_filter}")
                avg_score = cursor.fetchone()[0]
                results['average_score'] = round(avg_score, 2) if avg_score else 0
                cursor.execute(f"SELECT result_level, COUNT(*) FROM evaluation_results WHERE status = 'completed'{query_filter} GROUP BY result_level")
                level_counts = cursor.fetchall()
                results['level_distribution'] = {RESULT_LEVELS.get(l[0], {}).get('name', l[0]): l[1] for l in level_counts}
                return {'success': True, 'statistics': results}
        except Exception as e:
            logger.error(f'获取综合统计失败: {e}')
            return {'success': False, 'error': str(e)}