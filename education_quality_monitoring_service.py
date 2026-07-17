#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育质量监测服务 (v15.13.0)
====================================
提供教育质量监测、标准制定、数据采集、质量分析、预警机制、
质量报告、趋势监测、质量改进等综合管理服务。

核心能力：
1. 标准管理 - 监测标准制定、标准版本管理、标准发布
2. 指标管理 - 质量指标定义、指标权重配置、指标阈值设置
3. 数据采集 - 多源数据采集、数据校验、数据整合
4. 质量分析 - 综合分析、专项分析、对比分析、趋势分析
5. 预警机制 - 阈值预警、趋势预警、智能预警、预警处置
6. 趋势监测 - 趋势追踪、变化分析、预测预警
7. 报告管理 - 报告生成、报告发布、报告归档
8. 改进计划 - 问题诊断、改进方案、实施跟踪、效果评估
9. 对标分析 - 校际对标、区域对标、行业对标
10. 统计服务 - 数据统计、报表生成

差异化支持：
- 成人教育：职业技能、继续教育、学历提升
- K12教育：义务教育、高中教育、综合素质评价
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_quality_monitoring_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationQuality')


# ========== 监测配置 ==========

MONITORING_DIMENSIONS = {
    'teaching_quality': {'name': '教学质量', 'weight': 0.25, 'description': '课堂教学效果与质量'},
    'course_quality': {'name': '课程质量', 'weight': 0.15, 'description': '课程设计与实施质量'},
    'teacher_quality': {'name': '师资质量', 'weight': 0.20, 'description': '教师专业能力与素养'},
    'management_quality': {'name': '管理质量', 'weight': 0.10, 'description': '教学管理与服务质量'},
    'facility_quality': {'name': '设施质量', 'weight': 0.10, 'description': '教学设施与环境质量'},
    'student_development': {'name': '学生发展', 'weight': 0.15, 'description': '学生综合素质发展'},
    'satisfaction': {'name': '满意度', 'weight': 0.03, 'description': '师生满意度评价'},
    'safety_quality': {'name': '安全质量', 'weight': 0.02, 'description': '校园安全与健康'}
}

STANDARD_LEVELS = {
    'national': {'name': '国家标准', 'authority': '教育部', 'priority': 1},
    'industry': {'name': '行业标准', 'authority': '教育行业协会', 'priority': 2},
    'local': {'name': '地方标准', 'authority': '地方教育部门', 'priority': 3},
    'school': {'name': '学校标准', 'authority': '学校', 'priority': 4}
}

INDICATOR_TYPES = {
    'quantitative': {'name': '定量指标', 'measurement': '数值', 'unit_required': True},
    'qualitative': {'name': '定性指标', 'measurement': '评级', 'unit_required': False},
    'process': {'name': '过程指标', 'measurement': '状态', 'unit_required': False},
    'outcome': {'name': '结果指标', 'measurement': '成果', 'unit_required': True}
}

DATA_SOURCES = {
    'exam_scores': {'name': '考试成绩', 'frequency': '定期', 'data_type': 'numeric'},
    'teaching_evaluation': {'name': '教学评估', 'frequency': '定期', 'data_type': 'rating'},
    'student_feedback': {'name': '学生反馈', 'frequency': '不定期', 'data_type': 'text'},
    'teacher_evaluation': {'name': '教师评价', 'frequency': '定期', 'data_type': 'rating'},
    'third_party': {'name': '第三方评估', 'frequency': '年度', 'data_type': 'composite'},
    'observation': {'name': '观测数据', 'frequency': '实时', 'data_type': 'mixed'}
}

ALERT_THRESHOLDS = {
    'normal': {'name': '正常', 'color': 'green', 'range': '达标', 'action': '无'},
    'attention': {'name': '关注', 'color': 'yellow', 'range': '接近临界', 'action': '监控'},
    'warning': {'name': '预警', 'color': 'orange', 'range': '低于标准', 'action': '干预'},
    'severe': {'name': '严重', 'color': 'red', 'range': '严重超标', 'action': '紧急处置'}
}

REPORT_TYPES = {
    'monitoring': {'name': '监测报告', 'frequency': '月度', 'scope': '全面'},
    'analysis': {'name': '分析报告', 'frequency': '季度', 'scope': '专项'},
    'alert': {'name': '预警报告', 'frequency': '实时', 'scope': '异常'},
    'improvement': {'name': '改进报告', 'frequency': '按需', 'scope': '问题'},
    'annual': {'name': '年度报告', 'frequency': '年度', 'scope': '综合'}
}

TREND_PERIODS = {
    'monthly': {'name': '月度', 'duration': 30, 'color': '#3B82F6'},
    'quarterly': {'name': '季度', 'duration': 90, 'color': '#10B981'},
    'yearly': {'name': '年度', 'duration': 365, 'color': '#F59E0B'},
    'three_year': {'name': '三年', 'duration': 1095, 'color': '#8B5CF6'},
    'five_year': {'name': '五年', 'duration': 1825, 'color': '#EC4899'}
}

IMPROVEMENT_STAGES = {
    'diagnosis': {'name': '诊断', 'description': '问题识别与分析', 'duration_days': 15},
    'planning': {'name': '计划', 'description': '制定改进方案', 'duration_days': 10},
    'implementation': {'name': '实施', 'description': '执行改进措施', 'duration_days': 60},
    'evaluation': {'name': '评估', 'description': '效果评估与反馈', 'duration_days': 15},
    'consolidation': {'name': '巩固', 'description': '固化成果与标准化', 'duration_days': 30}
}


class EducationQualityMonitoringService:
    """教育质量监测服务"""

    def __init__(self):
        self.db_path = DATABASE_PATH
        self._lock = threading.RLock()
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS monitoring_standards (
                            standard_id TEXT PRIMARY KEY,
                            standard_name TEXT NOT NULL,
                            standard_level TEXT NOT NULL,
                            education_type TEXT NOT NULL,
                            monitoring_dimension TEXT,
                            description TEXT,
                            version TEXT DEFAULT '1.0',
                            effective_date TEXT,
                            status TEXT DEFAULT 'draft',
                            creator TEXT,
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS quality_indicators (
                            indicator_id TEXT PRIMARY KEY,
                            indicator_name TEXT NOT NULL,
                            indicator_type TEXT NOT NULL,
                            monitoring_dimension TEXT NOT NULL,
                            education_type TEXT NOT NULL,
                            weight REAL DEFAULT 0.0,
                            unit TEXT,
                            calculation_method TEXT,
                            description TEXT,
                            status TEXT DEFAULT 'active',
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS indicator_thresholds (
                            threshold_id TEXT PRIMARY KEY,
                            indicator_id TEXT NOT NULL,
                            education_type TEXT NOT NULL,
                            normal_min REAL,
                            normal_max REAL,
                            attention_min REAL,
                            attention_max REAL,
                            warning_min REAL,
                            warning_max REAL,
                            severe_min REAL,
                            severe_max REAL,
                            created_at TEXT,
                            updated_at TEXT,
                            FOREIGN KEY (indicator_id) REFERENCES quality_indicators(indicator_id)
                        )
                    ''')

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS monitoring_data (
                            data_id TEXT PRIMARY KEY,
                            indicator_id TEXT NOT NULL,
                            education_type TEXT NOT NULL,
                            monitoring_session TEXT,
                            value REAL,
                            raw_value TEXT,
                            data_source TEXT,
                            collection_time TEXT,
                            verified INTEGER DEFAULT 0,
                            verified_by TEXT,
                            verified_at TEXT,
                            status TEXT DEFAULT 'pending',
                            created_at TEXT
                        )
                    ''')

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS data_collections (
                            collection_id TEXT PRIMARY KEY,
                            collection_name TEXT NOT NULL,
                            education_type TEXT NOT NULL,
                            data_source TEXT NOT NULL,
                            start_time TEXT,
                            end_time TEXT,
                            total_records INTEGER DEFAULT 0,
                            success_count INTEGER DEFAULT 0,
                            failed_count INTEGER DEFAULT 0,
                            status TEXT DEFAULT 'collecting',
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS quality_analysis (
                            analysis_id TEXT PRIMARY KEY,
                            analysis_name TEXT NOT NULL,
                            education_type TEXT NOT NULL,
                            monitoring_dimension TEXT,
                            analysis_type TEXT,
                            scope TEXT,
                            start_date TEXT,
                            end_date TEXT,
                            status TEXT DEFAULT 'running',
                            result_summary TEXT,
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS analysis_results (
                            result_id TEXT PRIMARY KEY,
                            analysis_id TEXT NOT NULL,
                            indicator_id TEXT,
                            indicator_name TEXT,
                            actual_value REAL,
                            target_value REAL,
                            deviation REAL,
                            rating TEXT,
                            education_type TEXT NOT NULL,
                            created_at TEXT,
                            FOREIGN KEY (analysis_id) REFERENCES quality_analysis(analysis_id)
                        )
                    ''')

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS quality_alerts (
                            alert_id TEXT PRIMARY KEY,
                            alert_type TEXT NOT NULL,
                            indicator_id TEXT,
                            education_type TEXT NOT NULL,
                            alert_level TEXT NOT NULL,
                            title TEXT NOT NULL,
                            description TEXT,
                            triggered_value REAL,
                            threshold_value REAL,
                            status TEXT DEFAULT 'active',
                            assigned_to TEXT,
                            resolved_at TEXT,
                            resolution_note TEXT,
                            created_at TEXT
                        )
                    ''')

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS alert_rules (
                            rule_id TEXT PRIMARY KEY,
                            rule_name TEXT NOT NULL,
                            indicator_id TEXT,
                            education_type TEXT NOT NULL,
                            condition_type TEXT,
                            condition_expression TEXT,
                            alert_level TEXT,
                            enabled INTEGER DEFAULT 1,
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS trend_data (
                            trend_id TEXT PRIMARY KEY,
                            indicator_id TEXT NOT NULL,
                            education_type TEXT NOT NULL,
                            period TEXT NOT NULL,
                            period_start TEXT,
                            period_end TEXT,
                            average_value REAL,
                            min_value REAL,
                            max_value REAL,
                            trend_direction TEXT,
                            change_rate REAL,
                            created_at TEXT
                        )
                    ''')

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS quality_reports (
                            report_id TEXT PRIMARY KEY,
                            report_name TEXT NOT NULL,
                            report_type TEXT NOT NULL,
                            education_type TEXT NOT NULL,
                            period TEXT,
                            content TEXT,
                            summary TEXT,
                            status TEXT DEFAULT 'draft',
                            published_at TEXT,
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS report_schedules (
                            schedule_id TEXT PRIMARY KEY,
                            report_type TEXT NOT NULL,
                            education_type TEXT NOT NULL,
                            frequency TEXT,
                            next_run TEXT,
                            last_run TEXT,
                            enabled INTEGER DEFAULT 1,
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS improvement_plans (
                            plan_id TEXT PRIMARY KEY,
                            plan_name TEXT NOT NULL,
                            education_type TEXT NOT NULL,
                            problem_description TEXT,
                            target_indicator TEXT,
                            target_value REAL,
                            current_value REAL,
                            stage TEXT DEFAULT 'diagnosis',
                            status TEXT DEFAULT 'active',
                            deadline TEXT,
                            responsible TEXT,
                            created_at TEXT,
                            updated_at TEXT
                        )
                    ''')

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS improvement_tasks (
                            task_id TEXT PRIMARY KEY,
                            plan_id TEXT NOT NULL,
                            task_name TEXT NOT NULL,
                            description TEXT,
                            stage TEXT,
                            assignee TEXT,
                            status TEXT DEFAULT 'pending',
                            due_date TEXT,
                            completed_at TEXT,
                            created_at TEXT,
                            updated_at TEXT,
                            FOREIGN KEY (plan_id) REFERENCES improvement_plans(plan_id)
                        )
                    ''')

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS monitoring_sessions (
                            session_id TEXT PRIMARY KEY,
                            session_name TEXT NOT NULL,
                            education_type TEXT NOT NULL,
                            start_date TEXT,
                            end_date TEXT,
                            status TEXT DEFAULT 'active',
                            created_at TEXT
                        )
                    ''')

                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS benchmark_data (
                            benchmark_id TEXT PRIMARY KEY,
                            education_type TEXT NOT NULL,
                            indicator_id TEXT NOT NULL,
                            benchmark_type TEXT,
                            reference_value REAL,
                            reference_source TEXT,
                            period TEXT,
                            created_at TEXT
                        )
                    ''')

                    conn.commit()
                    logger.info('教育质量监测服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 标准管理 ==========

    def create_monitoring_standard(self, standard_name: str, standard_level: str,
                                   education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            standard_id = f"std_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO monitoring_standards (
                            standard_id, standard_name, standard_level,
                            education_type, monitoring_dimension, description,
                            version, effective_date, status, creator,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (standard_id, standard_name, standard_level, education_type,
                          kwargs.get('monitoring_dimension'), kwargs.get('description'),
                          kwargs.get('version', '1.0'), kwargs.get('effective_date'),
                          kwargs.get('status', 'draft'), kwargs.get('creator'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建监测标准: {standard_name} ({standard_id})')
                    return {'success': True, 'standard_id': standard_id}
        except Exception as e:
            logger.error(f'创建监测标准失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_monitoring_standard(self, standard_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    updates = []
                    params = []
                    if 'standard_name' in kwargs:
                        updates.append('standard_name = ?')
                        params.append(kwargs['standard_name'])
                    if 'description' in kwargs:
                        updates.append('description = ?')
                        params.append(kwargs['description'])
                    if 'version' in kwargs:
                        updates.append('version = ?')
                        params.append(kwargs['version'])
                    if 'effective_date' in kwargs:
                        updates.append('effective_date = ?')
                        params.append(kwargs['effective_date'])
                    if 'status' in kwargs:
                        updates.append('status = ?')
                        params.append(kwargs['status'])
                    if not updates:
                        return {'success': False, 'error': '没有需要更新的字段'}
                    updates.append('updated_at = ?')
                    params.append(now)
                    params.append(standard_id)
                    cursor.execute(f'UPDATE monitoring_standards SET {", ".join(updates)} WHERE standard_id = ?', params)
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '标准不存在'}
        except Exception as e:
            logger.error(f'更新监测标准失败: {e}')
            return {'success': False, 'error': str(e)}

    def publish_standard(self, standard_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE monitoring_standards SET status = ?, effective_date = ?, updated_at = ? WHERE standard_id = ? AND status = ?',
                                 ('published', now[:10], now, standard_id, 'draft'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'effective_date': now[:10]}
                    return {'success': False, 'error': '标准状态不允许发布'}
        except Exception as e:
            logger.error(f'发布监测标准失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_standards(self, education_type: str = None, standard_level: str = None,
                      status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM monitoring_standards WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if standard_level:
                    query += ' AND standard_level = ?'
                    params.append(standard_level)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                standards = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'standards': standards, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取监测标准失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 指标管理 ==========

    def create_quality_indicator(self, indicator_name: str, indicator_type: str,
                                 monitoring_dimension: str, education_type: str,
                                 **kwargs) -> Dict[str, Any]:
        try:
            indicator_id = f"ind_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO quality_indicators (
                            indicator_id, indicator_name, indicator_type,
                            monitoring_dimension, education_type, weight,
                            unit, calculation_method, description, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (indicator_id, indicator_name, indicator_type,
                          monitoring_dimension, education_type,
                          kwargs.get('weight', 0.0), kwargs.get('unit'),
                          kwargs.get('calculation_method'), kwargs.get('description'),
                          kwargs.get('status', 'active'), now, now))
                    conn.commit()
                    logger.info(f'创建质量指标: {indicator_name} ({indicator_id})')
                    return {'success': True, 'indicator_id': indicator_id}
        except Exception as e:
            logger.error(f'创建质量指标失败: {e}')
            return {'success': False, 'error': str(e)}

    def set_indicator_thresholds(self, indicator_id: str, education_type: str,
                                 **kwargs) -> Dict[str, Any]:
        try:
            threshold_id = f"thr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO indicator_thresholds (
                            threshold_id, indicator_id, education_type,
                            normal_min, normal_max, attention_min, attention_max,
                            warning_min, warning_max, severe_min, severe_max,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (threshold_id, indicator_id, education_type,
                          kwargs.get('normal_min'), kwargs.get('normal_max'),
                          kwargs.get('attention_min'), kwargs.get('attention_max'),
                          kwargs.get('warning_min'), kwargs.get('warning_max'),
                          kwargs.get('severe_min'), kwargs.get('severe_max'),
                          now, now))
                    conn.commit()
                    return {'success': True, 'threshold_id': threshold_id}
        except Exception as e:
            logger.error(f'设置指标阈值失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_indicator_weight(self, indicator_id: str, weight: float) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE quality_indicators SET weight = ?, updated_at = ? WHERE indicator_id = ?',
                                 (weight, now, indicator_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '指标不存在'}
        except Exception as e:
            logger.error(f'更新指标权重失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_indicators(self, education_type: str = None, monitoring_dimension: str = None,
                       indicator_type: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM quality_indicators WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if monitoring_dimension:
                    query += ' AND monitoring_dimension = ?'
                    params.append(monitoring_dimension)
                if indicator_type:
                    query += ' AND indicator_type = ?'
                    params.append(indicator_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                indicators = [dict(i) for i in cursor.fetchall()]
                return {'success': True, 'indicators': indicators, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取质量指标失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 数据采集 ==========

    def start_data_collection(self, collection_name: str, education_type: str,
                              data_source: str, **kwargs) -> Dict[str, Any]:
        try:
            collection_id = f"col_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO data_collections (
                            collection_id, collection_name, education_type,
                            data_source, start_time, end_time, total_records,
                            success_count, failed_count, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, NULL, 0, 0, 0, 'collecting', ?, ?)
                    ''', (collection_id, collection_name, education_type,
                          data_source, now, now, now))
                    conn.commit()
                    logger.info(f'开始数据采集: {collection_name} ({collection_id})')
                    return {'success': True, 'collection_id': collection_id}
        except Exception as e:
            logger.error(f'开始数据采集失败: {e}')
            return {'success': False, 'error': str(e)}

    def submit_monitoring_data(self, indicator_id: str, education_type: str,
                               value: float, **kwargs) -> Dict[str, Any]:
        try:
            data_id = f"dat_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO monitoring_data (
                            data_id, indicator_id, education_type,
                            monitoring_session, value, raw_value,
                            data_source, collection_time, verified,
                            verified_by, verified_at, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, NULL, NULL, 'pending', ?)
                    ''', (data_id, indicator_id, education_type,
                          kwargs.get('monitoring_session'), value,
                          kwargs.get('raw_value'), kwargs.get('data_source'),
                          kwargs.get('collection_time', now), now))
                    conn.commit()
                    return {'success': True, 'data_id': data_id}
        except Exception as e:
            logger.error(f'提交监测数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def verify_data(self, data_id: str, verified_by: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE monitoring_data SET verified = 1, verified_by = ?, verified_at = ?, status = ? WHERE data_id = ? AND status = ?',
                                 (verified_by, now, 'verified', data_id, 'pending'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '数据状态不允许验证'}
        except Exception as e:
            logger.error(f'验证监测数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_data_collection(self, collection_id: str, success_count: int,
                                 failed_count: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE data_collections SET
                            end_time = ?, total_records = ?,
                            success_count = ?, failed_count = ?,
                            status = ?, updated_at = ?
                        WHERE collection_id = ?
                    ''', (now, success_count + failed_count, success_count,
                          failed_count, 'completed', now, collection_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '采集任务不存在'}
        except Exception as e:
            logger.error(f'完成数据采集失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 质量分析 ==========

    def create_quality_analysis(self, analysis_name: str, education_type: str,
                                analysis_type: str, **kwargs) -> Dict[str, Any]:
        try:
            analysis_id = f"ana_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO quality_analysis (
                            analysis_id, analysis_name, education_type,
                            monitoring_dimension, analysis_type, scope,
                            start_date, end_date, status, result_summary,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'running', NULL, ?, ?)
                    ''', (analysis_id, analysis_name, education_type,
                          kwargs.get('monitoring_dimension'), analysis_type,
                          kwargs.get('scope', 'all'), kwargs.get('start_date'),
                          kwargs.get('end_date'), now, now))
                    conn.commit()
                    logger.info(f'创建质量分析: {analysis_name} ({analysis_id})')
                    return {'success': True, 'analysis_id': analysis_id}
        except Exception as e:
            logger.error(f'创建质量分析失败: {e}')
            return {'success': False, 'error': str(e)}

    def run_comprehensive_analysis(self, analysis_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type, monitoring_dimension FROM quality_analysis WHERE analysis_id = ?', (analysis_id,))
                    analysis = cursor.fetchone()
                    if not analysis:
                        return {'success': False, 'error': '分析任务不存在'}

                    education_type = analysis[0]
                    dimension = analysis[1]

                    query = 'SELECT i.indicator_id, i.indicator_name, i.weight, AVG(m.value) as avg_value, t.normal_min, t.normal_max FROM quality_indicators i LEFT JOIN monitoring_data m ON i.indicator_id = m.indicator_id AND m.status = ? LEFT JOIN indicator_thresholds t ON i.indicator_id = t.indicator_id AND t.education_type = ? WHERE i.education_type = ?'
                    params = ['verified', education_type, education_type]
                    if dimension:
                        query += ' AND i.monitoring_dimension = ?'
                        params.append(dimension)
                    cursor.execute(query, params)
                    indicators = cursor.fetchall()

                    results = []
                    total_score = 0.0
                    total_weight = 0.0

                    for indicator in indicators:
                        indicator_id, indicator_name, weight, avg_value, normal_min, normal_max = indicator
                        if avg_value is None:
                            avg_value = 0.0
                        target_value = (normal_min + normal_max) / 2 if normal_min and normal_max else avg_value
                        deviation = avg_value - target_value if target_value != 0 else 0

                        if normal_min is not None and normal_max is not None:
                            if avg_value >= normal_min and avg_value <= normal_max:
                                rating = 'normal'
                            elif avg_value < normal_min * 0.9:
                                rating = 'severe'
                            elif avg_value < normal_min:
                                rating = 'warning'
                            else:
                                rating = 'attention'
                        else:
                            rating = 'normal'

                        result_id = f"res_{uuid.uuid4().hex[:12]}"
                        cursor.execute('''
                            INSERT INTO analysis_results (
                                result_id, analysis_id, indicator_id,
                                indicator_name, actual_value, target_value,
                                deviation, rating, education_type, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (result_id, analysis_id, indicator_id, indicator_name,
                              avg_value, target_value, deviation, rating, education_type, now))
                        results.append({'indicator_id': indicator_id, 'indicator_name': indicator_name, 'rating': rating})

                        if weight:
                            total_score += avg_value * weight
                            total_weight += weight

                    overall_score = total_score / total_weight if total_weight > 0 else 0
                    summary = f"综合分析完成，共分析{len(results)}个指标，综合得分{round(overall_score, 2)}"
                    cursor.execute('UPDATE quality_analysis SET status = ?, result_summary = ?, updated_at = ? WHERE analysis_id = ?',
                                 ('completed', summary, now, analysis_id))
                    conn.commit()
                    return {'success': True, 'overall_score': round(overall_score, 2), 'indicators_analyzed': len(results)}
        except Exception as e:
            logger.error(f'执行综合分析失败: {e}')
            return {'success': False, 'error': str(e)}

    def run_trend_analysis(self, indicator_id: str, education_type: str,
                           period: str = 'yearly') -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT strftime('%Y', collection_time) as year,
                           AVG(value) as avg_value,
                           MIN(value) as min_value,
                           MAX(value) as max_value
                    FROM monitoring_data
                    WHERE indicator_id = ? AND education_type = ? AND status = ?
                    GROUP BY year
                    ORDER BY year DESC
                    LIMIT 5
                ''', (indicator_id, education_type, 'verified'))
                rows = cursor.fetchall()

                trend_data_list = []
                for row in rows:
                    trend_id = f"trd_{uuid.uuid4().hex[:12]}"
                    cursor.execute('''
                        INSERT INTO trend_data (
                            trend_id, indicator_id, education_type,
                            period, period_start, period_end,
                            average_value, min_value, max_value,
                            trend_direction, change_rate, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (trend_id, indicator_id, education_type, period,
                          f"{row['year']}-01-01", f"{row['year']}-12-31",
                          row['avg_value'], row['min_value'], row['max_value'],
                          None, None, now))
                    trend_data_list.append(dict(row))

                conn.commit()
                return {'success': True, 'trend_data': trend_data_list}
        except Exception as e:
            logger.error(f'执行趋势分析失败: {e}')
            return {'success': False, 'error': str(e)}

    def run_comparative_analysis(self, analysis_id: str, compare_with: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT education_type FROM quality_analysis WHERE analysis_id = ?', (analysis_id,))
                analysis = cursor.fetchone()
                if not analysis:
                    return {'success': False, 'error': '分析任务不存在'}

                education_type = analysis[0]
                cursor.execute('''
                    SELECT ar.indicator_id, ar.indicator_name, ar.actual_value,
                           bm.reference_value
                    FROM analysis_results ar
                    LEFT JOIN benchmark_data bm ON ar.indicator_id = bm.indicator_id AND bm.education_type = ? AND bm.benchmark_type = ?
                    WHERE ar.analysis_id = ?
                ''', (education_type, compare_with, analysis_id))
                comparisons = cursor.fetchall()

                diffs = []
                for comp in comparisons:
                    indicator_id, indicator_name, actual_value, reference_value = comp
                    diff = actual_value - reference_value if reference_value is not None else None
                    diffs.append({
                        'indicator_id': indicator_id,
                        'indicator_name': indicator_name,
                        'actual_value': actual_value,
                        'reference_value': reference_value,
                        'difference': diff
                    })

                summary = f"对比分析完成，共对比{len(diffs)}个指标"
                cursor.execute('UPDATE quality_analysis SET result_summary = ?, updated_at = ? WHERE analysis_id = ?',
                             (summary, now, analysis_id))
                conn.commit()
                return {'success': True, 'comparisons': diffs}
        except Exception as e:
            logger.error(f'执行对比分析失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_analysis_results(self, analysis_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM analysis_results WHERE analysis_id = ?', (analysis_id,))
                results = [dict(r) for r in cursor.fetchall()]
                cursor.execute('SELECT analysis_name, status, result_summary FROM quality_analysis WHERE analysis_id = ?', (analysis_id,))
                analysis = cursor.fetchone()
                if not analysis:
                    return {'success': False, 'error': '分析任务不存在'}
                return {'success': True, 'analysis': dict(analysis), 'results': results}
        except Exception as e:
            logger.error(f'获取分析结果失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 预警机制 ==========

    def create_alert_rule(self, rule_name: str, education_type: str,
                          condition_type: str, condition_expression: str,
                          alert_level: str, **kwargs) -> Dict[str, Any]:
        try:
            rule_id = f"rul_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO alert_rules (
                            rule_id, rule_name, indicator_id, education_type,
                            condition_type, condition_expression, alert_level,
                            enabled, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (rule_id, rule_name, kwargs.get('indicator_id'), education_type,
                          condition_type, condition_expression, alert_level,
                          kwargs.get('enabled', 1), now, now))
                    conn.commit()
                    logger.info(f'创建预警规则: {rule_name} ({rule_id})')
                    return {'success': True, 'rule_id': rule_id}
        except Exception as e:
            logger.error(f'创建预警规则失败: {e}')
            return {'success': False, 'error': str(e)}

    def trigger_alert(self, alert_type: str, education_type: str, alert_level: str,
                      title: str, **kwargs) -> Dict[str, Any]:
        try:
            alert_id = f"alt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO quality_alerts (
                            alert_id, alert_type, indicator_id, education_type,
                            alert_level, title, description, triggered_value,
                            threshold_value, status, assigned_to, resolved_at,
                            resolution_note, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?)
                    ''', (alert_id, alert_type, kwargs.get('indicator_id'), education_type,
                          alert_level, title, kwargs.get('description'),
                          kwargs.get('triggered_value'), kwargs.get('threshold_value'),
                          'active', kwargs.get('assigned_to'), now))
                    conn.commit()
                    logger.warning(f'触发预警: {title} ({alert_id})')
                    return {'success': True, 'alert_id': alert_id}
        except Exception as e:
            logger.error(f'触发预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def resolve_alert(self, alert_id: str, resolution_note: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE quality_alerts SET status = ?, resolved_at = ?, resolution_note = ? WHERE alert_id = ? AND status = ?',
                                 ('resolved', now, resolution_note, alert_id, 'active'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '预警状态不允许处理'}
        except Exception as e:
            logger.error(f'处理预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_alerts(self, education_type: str = None, alert_level: str = None,
                   status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM quality_alerts WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if alert_level:
                    query += ' AND alert_level = ?'
                    params.append(alert_level)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                alerts = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'alerts': alerts, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取预警列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 趋势监测 ==========

    def get_trend_data(self, indicator_id: str, education_type: str,
                       period: str = 'yearly') -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM trend_data
                    WHERE indicator_id = ? AND education_type = ? AND period = ?
                    ORDER BY period_start DESC
                ''', (indicator_id, education_type, period))
                trends = [dict(t) for t in cursor.fetchall()]
                return {'success': True, 'trends': trends}
        except Exception as e:
            logger.error(f'获取趋势数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def analyze_trend_change(self, indicator_id: str, education_type: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT average_value, period_start FROM trend_data
                    WHERE indicator_id = ? AND education_type = ?
                    ORDER BY period_start ASC
                    LIMIT 10
                ''', (indicator_id, education_type))
                rows = cursor.fetchall()

                if len(rows) < 2:
                    return {'success': False, 'error': '数据不足，无法分析趋势变化'}

                changes = []
                for i in range(1, len(rows)):
                    prev = rows[i-1]
                    curr = rows[i]
                    change = curr['average_value'] - prev['average_value']
                    change_rate = (change / prev['average_value']) * 100 if prev['average_value'] != 0 else 0
                    changes.append({
                        'period': curr['period_start'],
                        'change': round(change, 2),
                        'change_rate': round(change_rate, 2),
                        'direction': 'up' if change > 0 else 'down' if change < 0 else 'stable'
                    })

                overall_direction = 'up' if sum(c['change'] for c in changes) > 0 else 'down'
                return {'success': True, 'changes': changes, 'overall_direction': overall_direction}
        except Exception as e:
            logger.error(f'分析趋势变化失败: {e}')
            return {'success': False, 'error': str(e)}

    def predict_future_trend(self, indicator_id: str, education_type: str,
                             periods_ahead: int = 3) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT average_value, period_start FROM trend_data
                    WHERE indicator_id = ? AND education_type = ?
                    ORDER BY period_start ASC
                ''', (indicator_id, education_type))
                rows = cursor.fetchall()

                if len(rows) < 3:
                    return {'success': False, 'error': '历史数据不足，无法预测'}

                values = [r['average_value'] for r in rows]
                recent_changes = [values[i] - values[i-1] for i in range(1, len(values))]
                avg_change = sum(recent_changes) / len(recent_changes)

                predictions = []
                last_value = values[-1]
                for i in range(1, periods_ahead + 1):
                    predicted_value = last_value + avg_change * i
                    predictions.append({
                        'period_offset': i,
                        'predicted_value': round(predicted_value, 2),
                        'confidence': min(100 - (i * 15), 50)
                    })

                return {'success': True, 'predictions': predictions, 'method': 'linear_extrapolation'}
        except Exception as e:
            logger.error(f'预测未来趋势失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 报告管理 ==========

    def create_quality_report(self, report_name: str, report_type: str,
                              education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            report_id = f"rpt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO quality_reports (
                            report_id, report_name, report_type, education_type,
                            period, content, summary, status, published_at,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)
                    ''', (report_id, report_name, report_type, education_type,
                          kwargs.get('period'), kwargs.get('content'),
                          kwargs.get('summary'), kwargs.get('status', 'draft'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建质量报告: {report_name} ({report_id})')
                    return {'success': True, 'report_id': report_id}
        except Exception as e:
            logger.error(f'创建质量报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def generate_report_content(self, report_id: str, analysis_id: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT report_type, education_type FROM quality_reports WHERE report_id = ?', (report_id,))
                report = cursor.fetchone()
                if not report:
                    return {'success': False, 'error': '报告不存在'}

                content = {
                    'generated_at': now,
                    'education_type': report['education_type'],
                    'report_type': report['report_type'],
                    'sections': []
                }

                if analysis_id:
                    cursor.execute('SELECT * FROM analysis_results WHERE analysis_id = ?', (analysis_id,))
                    results = cursor.fetchall()
                    content['sections'].append({
                        'title': '分析结果',
                        'content': [dict(r) for r in results]
                    })

                content_str = json.dumps(content, ensure_ascii=False, indent=2)
                summary = f"报告内容已生成，包含{len(content['sections'])}个章节"

                cursor.execute('UPDATE quality_reports SET content = ?, summary = ?, updated_at = ? WHERE report_id = ?',
                             (content_str, summary, now, report_id))
                conn.commit()
                return {'success': True, 'content': content}
        except Exception as e:
            logger.error(f'生成报告内容失败: {e}')
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
            logger.error(f'发布质量报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_reports(self, education_type: str = None, report_type: str = None,
                    status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM quality_reports WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if report_type:
                    query += ' AND report_type = ?'
                    params.append(report_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                reports = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'reports': reports, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取质量报告失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 改进计划 ==========

    def create_improvement_plan(self, plan_name: str, education_type: str,
                                **kwargs) -> Dict[str, Any]:
        try:
            plan_id = f"pln_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO improvement_plans (
                            plan_id, plan_name, education_type,
                            problem_description, target_indicator,
                            target_value, current_value, stage, status,
                            deadline, responsible, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (plan_id, plan_name, education_type,
                          kwargs.get('problem_description'), kwargs.get('target_indicator'),
                          kwargs.get('target_value'), kwargs.get('current_value'),
                          kwargs.get('stage', 'diagnosis'), kwargs.get('status', 'active'),
                          kwargs.get('deadline'), kwargs.get('responsible'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建改进计划: {plan_name} ({plan_id})')
                    return {'success': True, 'plan_id': plan_id}
        except Exception as e:
            logger.error(f'创建改进计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_improvement_task(self, plan_id: str, task_name: str, **kwargs) -> Dict[str, Any]:
        try:
            task_id = f"tsk_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT stage FROM improvement_plans WHERE plan_id = ?', (plan_id,))
                    plan = cursor.fetchone()
                    if not plan:
                        return {'success': False, 'error': '改进计划不存在'}
                    cursor.execute('''
                        INSERT INTO improvement_tasks (
                            task_id, plan_id, task_name, description,
                            stage, assignee, status, due_date,
                            completed_at, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)
                    ''', (task_id, plan_id, task_name, kwargs.get('description'),
                          kwargs.get('stage', plan[0]), kwargs.get('assignee'),
                          kwargs.get('status', 'pending'), kwargs.get('due_date'),
                          now, now))
                    conn.commit()
                    return {'success': True, 'task_id': task_id}
        except Exception as e:
            logger.error(f'添加改进任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_plan_stage(self, plan_id: str, stage: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE improvement_plans SET stage = ?, updated_at = ? WHERE plan_id = ?',
                                 (stage, now, plan_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '改进计划不存在'}
        except Exception as e:
            logger.error(f'更新改进计划阶段失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_task(self, task_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE improvement_tasks SET status = ?, completed_at = ?, updated_at = ? WHERE task_id = ? AND status = ?',
                                 ('completed', now, now, task_id, 'pending'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '任务状态不允许完成'}
        except Exception as e:
            logger.error(f'完成改进任务失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 对标分析 ==========

    def add_benchmark_data(self, education_type: str, indicator_id: str,
                           benchmark_type: str, reference_value: float, **kwargs) -> Dict[str, Any]:
        try:
            benchmark_id = f"bmk_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO benchmark_data (
                            benchmark_id, education_type, indicator_id,
                            benchmark_type, reference_value, reference_source,
                            period, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (benchmark_id, education_type, indicator_id,
                          benchmark_type, reference_value, kwargs.get('reference_source'),
                          kwargs.get('period'), now))
                    conn.commit()
                    return {'success': True, 'benchmark_id': benchmark_id}
        except Exception as e:
            logger.error(f'添加对标数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def run_benchmark_analysis(self, education_type: str, benchmark_type: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT i.indicator_name, i.indicator_id,
                           AVG(m.value) as actual_value,
                           bm.reference_value
                    FROM quality_indicators i
                    LEFT JOIN monitoring_data m ON i.indicator_id = m.indicator_id AND m.status = ? AND m.education_type = ?
                    LEFT JOIN benchmark_data bm ON i.indicator_id = bm.indicator_id AND bm.education_type = ? AND bm.benchmark_type = ?
                    WHERE i.education_type = ?
                    GROUP BY i.indicator_id
                ''', ('verified', education_type, education_type, benchmark_type, education_type))
                results = cursor.fetchall()

                analysis = []
                for row in results:
                    actual = row['actual_value'] or 0
                    reference = row['reference_value'] or 0
                    gap = reference - actual if reference != 0 else 0
                    gap_percent = (gap / reference) * 100 if reference != 0 else 0
                    analysis.append({
                        'indicator_id': row['indicator_id'],
                        'indicator_name': row['indicator_name'],
                        'actual_value': round(actual, 2),
                        'reference_value': round(reference, 2),
                        'gap': round(gap, 2),
                        'gap_percent': round(gap_percent, 2),
                        'status': 'exceeding' if actual > reference else 'meeting' if abs(gap) < reference * 0.05 else 'needing_improvement'
                    })

                return {'success': True, 'benchmark_type': benchmark_type, 'analysis': analysis}
        except Exception as e:
            logger.error(f'执行对标分析失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_benchmark_comparison(self, indicator_id: str, education_type: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT benchmark_type, reference_value, reference_source, period
                    FROM benchmark_data
                    WHERE indicator_id = ? AND education_type = ?
                ''', (indicator_id, education_type))
                benchmarks = [dict(b) for b in cursor.fetchall()]

                cursor.execute('SELECT AVG(value) as avg_value FROM monitoring_data WHERE indicator_id = ? AND education_type = ? AND status = ?',
                             (indicator_id, education_type, 'verified'))
                actual = cursor.fetchone()['avg_value'] or 0

                return {'success': True, 'actual_value': round(actual, 2), 'benchmarks': benchmarks}
        except Exception as e:
            logger.error(f'获取对标对比失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计服务 ==========

    def get_quality_statistics(self, education_type: str, period: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                stats = {}

                cursor.execute('SELECT COUNT(*) FROM monitoring_standards WHERE education_type = ?', (education_type,))
                stats['standards_count'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM quality_indicators WHERE education_type = ?', (education_type,))
                stats['indicators_count'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM monitoring_data WHERE education_type = ? AND status = ?', (education_type, 'verified'))
                stats['verified_data_count'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM quality_alerts WHERE education_type = ? AND status = ?', (education_type, 'active'))
                stats['active_alerts'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM quality_reports WHERE education_type = ? AND status = ?', (education_type, 'published'))
                stats['published_reports'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM improvement_plans WHERE education_type = ? AND status = ?', (education_type, 'active'))
                stats['active_plans'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM improvement_tasks WHERE status = ?', ('pending',))
                stats['pending_tasks'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM improvement_tasks WHERE status = ?', ('completed',))
                stats['completed_tasks'] = cursor.fetchone()[0]

                return {'success': True, 'statistics': stats, 'education_type': education_type}
        except Exception as e:
            logger.error(f'获取质量统计失败: {e}')
            return {'success': False, 'error': str(e)}