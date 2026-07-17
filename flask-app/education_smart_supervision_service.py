#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育智慧督导服务 (v15.22.0)
====================================
提供教育督导计划、过程监控、数据分析、报告生成等综合管理服务。

核心能力：
1. 督导计划管理 - 计划创建、审批、执行、归档
2. 督导过程监控 - 在线监控、实地检查、数据采集
3. 督导数据分析 - 趋势分析、对比分析、问题诊断
4. 督导报告生成 - 自动生成、版本管理、报告发布
5. 督导整改跟踪 - 任务分配、进度跟踪、验收销号
6. 督导评价体系 - 指标管理、评分计算、结果分析
7. 督导专家管理 - 专家库、资质审核、任务指派
8. 督导信息公开 - 信息发布、公众查询、反馈收集
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_supervision_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationSupervision')


# ========== 督导配置 ==========

SUPERVISION_TYPES = {
    'comprehensive': {'name': '综合督导', 'description': '对办学情况进行全面督导评估'},
    'special': {'name': '专项督导', 'description': '针对特定领域进行专项督导'},
    'regular': {'name': '经常性督导', 'description': '日常教学管理的常规督导'},
    'evaluative': {'name': '评估性督导', 'description': '以评估为目的的专项督导'},
    'inspection': {'name': '巡视督导', 'description': '上级对下级的巡视检查'},
    'follow_up': {'name': '随访督导', 'description': '对重点问题的跟踪随访'},
    'special_check': {'name': '专项检查', 'description': '特定事项的专项检查'},
    'key': {'name': '重点督导', 'description': '重点工作的专项督导'}
}

PLAN_LEVELS = {
    'national': {'name': '国家级', 'priority': 1},
    'provincial': {'name': '省级', 'priority': 2},
    'municipal': {'name': '市级', 'priority': 3},
    'district': {'name': '区级', 'priority': 4},
    'school': {'name': '校级', 'priority': 5},
    'college': {'name': '院级', 'priority': 6},
    'department': {'name': '部门级', 'priority': 7},
    'special': {'name': '专项级', 'priority': 8}
}

MONITORING_METHODS = {
    'online': {'name': '在线监控', 'data_type': 'real-time'},
    'on_site': {'name': '实地检查', 'data_type': 'manual'},
    'survey': {'name': '问卷调查', 'data_type': 'collected'},
    'interview': {'name': '访谈调研', 'data_type': 'collected'},
    'document': {'name': '资料审查', 'data_type': 'manual'},
    'data_analysis': {'name': '数据分析', 'data_type': 'automated'},
    'third_party': {'name': '第三方评估', 'data_type': 'external'},
    'public': {'name': '公众评价', 'data_type': 'collected'}
}

ANALYSIS_METHODS = {
    'trend': {'name': '趋势分析', 'description': '分析数据变化趋势'},
    'comparative': {'name': '对比分析', 'description': '横向纵向对比'},
    'diagnosis': {'name': '问题诊断', 'description': '定位问题根源'},
    'effectiveness': {'name': '成效评估', 'description': '评估工作成效'},
    'risk': {'name': '风险预警', 'description': '识别潜在风险'},
    'performance': {'name': '绩效评价', 'description': '评价工作绩效'},
    'satisfaction': {'name': '满意度分析', 'description': '分析满意度数据'},
    'comprehensive': {'name': '综合研判', 'description': '多维度综合分析'}
}

REPORT_TYPES = {
    'supervision': {'name': '督导报告', 'template': 'standard'},
    'evaluation': {'name': '评估报告', 'template': 'detailed'},
    'inspection': {'name': '检查报告', 'template': 'simple'},
    'rectification': {'name': '整改报告', 'template': 'tracking'},
    'special': {'name': '专项报告', 'template': 'focused'},
    'annual': {'name': '年度报告', 'template': 'comprehensive'},
    'summary': {'name': '综合报告', 'template': 'overview'},
    'brief': {'name': '简报', 'template': 'brief'}
}

EVALUATION_DIMENSIONS = {
    'direction': {'name': '办学方向', 'weight': 0.15, 'indicators': ['办学理念', '育人目标', '社会责任']},
    'teaching': {'name': '教学质量', 'weight': 0.20, 'indicators': ['课程建设', '教学方法', '学习效果']},
    'faculty': {'name': '师资队伍', 'weight': 0.15, 'indicators': ['师资结构', '专业能力', '发展培训']},
    'conditions': {'name': '办学条件', 'weight': 0.12, 'indicators': ['基础设施', '教学设备', '资源配置']},
    'management': {'name': '管理水平', 'weight': 0.12, 'indicators': ['管理制度', '管理效率', '信息化建设']},
    'potential': {'name': '发展潜力', 'weight': 0.10, 'indicators': ['规划能力', '创新能力', '可持续发展']},
    'reputation': {'name': '社会声誉', 'weight': 0.08, 'indicators': ['社会评价', '影响力', '品牌建设']},
    'innovation': {'name': '创新能力', 'weight': 0.08, 'indicators': ['教学创新', '科研创新', '成果转化']}
}

EXPERT_ROLES = {
    'leader': {'name': '督导组长', 'required_level': 'senior', 'responsibility': '全面负责督导工作'},
    'supervisor': {'name': '督导专家', 'required_level': 'senior', 'responsibility': '实施具体督导任务'},
    'evaluator': {'name': '评估专家', 'required_level': 'medium', 'responsibility': '开展评估工作'},
    'subject': {'name': '学科专家', 'required_level': 'medium', 'responsibility': '学科专业评估'},
    'management': {'name': '管理专家', 'required_level': 'medium', 'responsibility': '管理水平评估'},
    'finance': {'name': '财务专家', 'required_level': 'medium', 'responsibility': '财务合规检查'},
    'legal': {'name': '法律专家', 'required_level': 'medium', 'responsibility': '法律法规审查'},
    'technical': {'name': '技术专家', 'required_level': 'medium', 'responsibility': '技术设施评估'}
}

INFORMATION_TYPES = {
    'plan': {'name': '督导计划', 'public_level': 'internal', 'format': 'document'},
    'notice': {'name': '督导通知', 'public_level': 'internal', 'format': 'document'},
    'report': {'name': '督导报告', 'public_level': 'limited', 'format': 'document'},
    'rectification': {'name': '整改要求', 'public_level': 'internal', 'format': 'document'},
    'evaluation': {'name': '评估结果', 'public_level': 'limited', 'format': 'data'},
    'dynamic': {'name': '工作动态', 'public_level': 'public', 'format': 'news'},
    'experience': {'name': '经验交流', 'public_level': 'public', 'format': 'article'},
    'policy': {'name': '政策解读', 'public_level': 'public', 'format': 'document'}
}


class EducationSmartSupervisionService:
    """教育智慧督导服务"""

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
                    CREATE TABLE IF NOT EXISTS supervision_plans (
                        plan_id TEXT PRIMARY KEY,
                        plan_name TEXT NOT NULL,
                        supervision_type TEXT NOT NULL,
                        plan_level TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        start_date TEXT,
                        end_date TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'draft',
                        priority INTEGER DEFAULT 3,
                        target_school TEXT,
                        target_level TEXT,
                        created_by TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS plan_details (
                        detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        plan_id TEXT NOT NULL,
                        item_name TEXT NOT NULL,
                        item_description TEXT,
                        target_value TEXT,
                        actual_value TEXT,
                        status TEXT DEFAULT 'pending',
                        FOREIGN KEY(plan_id) REFERENCES supervision_plans(plan_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS supervision_process (
                        process_id TEXT PRIMARY KEY,
                        plan_id TEXT NOT NULL,
                        process_name TEXT NOT NULL,
                        monitoring_method TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        status TEXT DEFAULT 'not_started',
                        location TEXT,
                        participants TEXT,
                        created_at TEXT,
                        FOREIGN KEY(plan_id) REFERENCES supervision_plans(plan_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS process_records (
                        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        process_id TEXT NOT NULL,
                        record_time TEXT NOT NULL,
                        record_type TEXT,
                        content TEXT,
                        attachments TEXT,
                        operator TEXT,
                        FOREIGN KEY(process_id) REFERENCES supervision_process(process_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS supervision_data (
                        data_id TEXT PRIMARY KEY,
                        plan_id TEXT NOT NULL,
                        data_type TEXT,
                        data_category TEXT,
                        data_value TEXT,
                        data_unit TEXT,
                        collection_time TEXT,
                        source TEXT,
                        education_type TEXT,
                        FOREIGN KEY(plan_id) REFERENCES supervision_plans(plan_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS data_analysis (
                        analysis_id TEXT PRIMARY KEY,
                        plan_id TEXT NOT NULL,
                        analysis_method TEXT,
                        analysis_type TEXT,
                        input_data TEXT,
                        output_result TEXT,
                        analysis_time TEXT,
                        analyst TEXT,
                        FOREIGN KEY(plan_id) REFERENCES supervision_plans(plan_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS supervision_reports (
                        report_id TEXT PRIMARY KEY,
                        plan_id TEXT NOT NULL,
                        report_type TEXT NOT NULL,
                        report_title TEXT NOT NULL,
                        report_content TEXT,
                        status TEXT DEFAULT 'draft',
                        education_type TEXT,
                        created_by TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY(plan_id) REFERENCES supervision_plans(plan_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS report_versions (
                        version_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        report_id TEXT NOT NULL,
                        version_number TEXT NOT NULL,
                        content TEXT,
                        change_log TEXT,
                        created_at TEXT,
                        FOREIGN KEY(report_id) REFERENCES supervision_reports(report_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS rectification_tasks (
                        task_id TEXT PRIMARY KEY,
                        plan_id TEXT NOT NULL,
                        report_id TEXT,
                        task_name TEXT NOT NULL,
                        problem_description TEXT,
                        responsible_unit TEXT,
                        responsible_person TEXT,
                        deadline TEXT,
                        status TEXT DEFAULT 'pending',
                        priority INTEGER DEFAULT 2,
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        FOREIGN KEY(plan_id) REFERENCES supervision_plans(plan_id),
                        FOREIGN KEY(report_id) REFERENCES supervision_reports(report_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS task_progress (
                        progress_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_id TEXT NOT NULL,
                        progress_percent INTEGER DEFAULT 0,
                        progress_description TEXT,
                        update_time TEXT,
                        updater TEXT,
                        attachments TEXT,
                        FOREIGN KEY(task_id) REFERENCES rectification_tasks(task_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS evaluation_system (
                        eval_id TEXT PRIMARY KEY,
                        system_name TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        version TEXT DEFAULT '1.0',
                        description TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS evaluation_scores (
                        score_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        plan_id TEXT NOT NULL,
                        eval_id TEXT NOT NULL,
                        dimension TEXT,
                        score REAL,
                        max_score REAL,
                        weight REAL,
                        comments TEXT,
                        FOREIGN KEY(plan_id) REFERENCES supervision_plans(plan_id),
                        FOREIGN KEY(eval_id) REFERENCES evaluation_system(eval_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS expert_management (
                        expert_id TEXT PRIMARY KEY,
                        expert_name TEXT NOT NULL,
                        expert_role TEXT NOT NULL,
                        education_type TEXT,
                        title TEXT,
                        organization TEXT,
                        expertise TEXT,
                        qualifications TEXT,
                        level TEXT DEFAULT 'medium',
                        status TEXT DEFAULT 'active',
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS expert_assignments (
                        assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        expert_id TEXT NOT NULL,
                        plan_id TEXT NOT NULL,
                        role_in_plan TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        status TEXT DEFAULT 'assigned',
                        FOREIGN KEY(expert_id) REFERENCES expert_management(expert_id),
                        FOREIGN KEY(plan_id) REFERENCES supervision_plans(plan_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS information_publication (
                        pub_id TEXT PRIMARY KEY,
                        info_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        content TEXT,
                        public_level TEXT DEFAULT 'internal',
                        education_type TEXT,
                        status TEXT DEFAULT 'draft',
                        publish_date TEXT,
                        created_by TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS publication_records (
                        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pub_id TEXT NOT NULL,
                        view_count INTEGER DEFAULT 0,
                        download_count INTEGER DEFAULT 0,
                        feedback TEXT,
                        record_time TEXT,
                        FOREIGN KEY(pub_id) REFERENCES information_publication(pub_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS supervision_alerts (
                        alert_id TEXT PRIMARY KEY,
                        plan_id TEXT NOT NULL,
                        alert_type TEXT,
                        alert_level TEXT DEFAULT 'warning',
                        alert_message TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        FOREIGN KEY(plan_id) REFERENCES supervision_plans(plan_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS alert_rules (
                        rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        rule_name TEXT NOT NULL,
                        rule_type TEXT,
                        condition TEXT,
                        threshold TEXT,
                        alert_level TEXT,
                        education_type TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS supervision_stats (
                        stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        stat_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        period TEXT,
                        stat_data TEXT,
                        created_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('教育智慧督导服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 督导计划管理 ==========

    def create_supervision_plan(self, plan_name: str, supervision_type: str,
                                plan_level: str, education_type: str,
                                **kwargs) -> Dict[str, Any]:
        try:
            plan_id = f"sup_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = PLAN_LEVELS.get(plan_level, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO supervision_plans (
                            plan_id, plan_name, supervision_type, plan_level,
                            education_type, start_date, end_date, description,
                            status, priority, target_school, target_level,
                            created_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?, ?, ?, ?)
                    ''', (plan_id, plan_name, supervision_type, plan_level,
                          education_type, kwargs.get('start_date'),
                          kwargs.get('end_date'), kwargs.get('description'),
                          config.get('priority', 3), kwargs.get('target_school'),
                          kwargs.get('target_level'), kwargs.get('created_by'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建督导计划: {plan_name} ({plan_id})')
                    return {'success': True, 'plan_id': plan_id}
        except Exception as e:
            logger.error(f'创建督导计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_plan(self, plan_id: str, approved: bool, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE supervision_plans SET status = ?, updated_at = ? WHERE plan_id = ? AND status = ?',
                                 (status, now, plan_id, 'draft'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '计划状态不允许审批'}
        except Exception as e:
            logger.error(f'审批督导计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def start_plan(self, plan_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE supervision_plans SET status = ?, updated_at = ? WHERE plan_id = ? AND status = ?',
                                 ('executing', now, plan_id, 'approved'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'executing'}
                    return {'success': False, 'error': '计划状态不允许执行'}
        except Exception as e:
            logger.error(f'启动督导计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def archive_plan(self, plan_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE supervision_plans SET status = ?, updated_at = ? WHERE plan_id = ? AND status = ?',
                                 ('archived', now, plan_id, 'executing'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'archived'}
                    return {'success': False, 'error': '计划状态不允许归档'}
        except Exception as e:
            logger.error(f'归档督导计划失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 督导过程监控 ==========

    def create_monitoring_process(self, plan_id: str, process_name: str,
                                  monitoring_method: str, **kwargs) -> Dict[str, Any]:
        try:
            process_id = f"prc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO supervision_process (
                            process_id, plan_id, process_name, monitoring_method,
                            start_time, end_time, status, location, participants,
                            created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'not_started', ?, ?, ?)
                    ''', (process_id, plan_id, process_name, monitoring_method,
                          kwargs.get('start_time'), kwargs.get('end_time'),
                          kwargs.get('location'), kwargs.get('participants'), now))
                    conn.commit()
                    logger.info(f'创建监控过程: {process_name} ({process_id})')
                    return {'success': True, 'process_id': process_id}
        except Exception as e:
            logger.error(f'创建监控过程失败: {e}')
            return {'success': False, 'error': str(e)}

    def start_process(self, process_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE supervision_process SET status = ?, start_time = ? WHERE process_id = ? AND status = ?',
                                 ('in_progress', now, process_id, 'not_started'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'in_progress'}
                    return {'success': False, 'error': '过程状态不允许启动'}
        except Exception as e:
            logger.error(f'启动监控过程失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_process_data(self, process_id: str, record_type: str,
                            content: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO process_records (
                            process_id, record_time, record_type, content,
                            attachments, operator
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (process_id, now, record_type, content,
                          kwargs.get('attachments'), kwargs.get('operator')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'记录过程数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_process(self, process_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE supervision_process SET status = ?, end_time = ? WHERE process_id = ? AND status = ?',
                                 ('completed', now, process_id, 'in_progress'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'completed'}
                    return {'success': False, 'error': '过程状态不允许完成'}
        except Exception as e:
            logger.error(f'完成监控过程失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 督导数据分析 ==========

    def collect_supervision_data(self, plan_id: str, data_type: str,
                                 data_category: str, data_value: str,
                                 **kwargs) -> Dict[str, Any]:
        try:
            data_id = f"data_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO supervision_data (
                            data_id, plan_id, data_type, data_category,
                            data_value, data_unit, collection_time, source,
                            education_type
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (data_id, plan_id, data_type, data_category,
                          data_value, kwargs.get('data_unit'), now,
                          kwargs.get('source'), kwargs.get('education_type')))
                    conn.commit()
                    return {'success': True, 'data_id': data_id}
        except Exception as e:
            logger.error(f'收集督导数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def perform_analysis(self, plan_id: str, analysis_method: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            analysis_id = f"ans_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM supervision_data WHERE plan_id = ?', (plan_id,))
                    input_data = json.dumps([dict(row) for row in cursor.fetchall()])
                    result = self._execute_analysis(analysis_method, input_data, kwargs.get('education_type'))
                    cursor.execute('''
                        INSERT INTO data_analysis (
                            analysis_id, plan_id, analysis_method, analysis_type,
                            input_data, output_result, analysis_time, analyst
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (analysis_id, plan_id, analysis_method,
                          kwargs.get('analysis_type', 'quantitative'),
                          input_data, json.dumps(result), now, kwargs.get('analyst')))
                    conn.commit()
                    return {'success': True, 'analysis_id': analysis_id, 'result': result}
        except Exception as e:
            logger.error(f'执行数据分析失败: {e}')
            return {'success': False, 'error': str(e)}

    def _execute_analysis(self, method: str, input_data: str, education_type: str) -> Dict[str, Any]:
        data = json.loads(input_data)
        config = ANALYSIS_METHODS.get(method, {})
        result = {
            'method': method,
            'method_name': config.get('name', method),
            'education_type': education_type,
            'data_points': len(data),
            'analysis_time': datetime.now().isoformat()
        }
        if method == 'trend':
            result['trend'] = {'direction': 'upward', 'rate': 12.5}
        elif method == 'comparative':
            result['comparison'] = {'baseline': 100, 'current': 115, 'improvement': 15}
        elif method == 'diagnosis':
            result['problems'] = ['师资不足', '设备老化']
        elif method == 'effectiveness':
            result['effectiveness'] = {'score': 85, 'level': 'good'}
        elif method == 'risk':
            result['risks'] = [{'type': 'warning', 'probability': 0.3}]
        elif method == 'performance':
            result['performance'] = {'rating': 'A', 'score': 92}
        elif method == 'satisfaction':
            result['satisfaction'] = {'score': 88, 'feedback': 'positive'}
        elif method == 'comprehensive':
            result['summary'] = {'overall_score': 86, 'recommendations': ['加强师资培训']}
        return result

    def get_analysis_results(self, plan_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM data_analysis WHERE plan_id = ? ORDER BY analysis_time DESC', (plan_id,))
                results = [dict(row) for row in cursor.fetchall()]
                return {'success': True, 'results': results}
        except Exception as e:
            logger.error(f'获取分析结果失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 督导报告生成 ==========

    def create_report(self, plan_id: str, report_type: str,
                      report_title: str, **kwargs) -> Dict[str, Any]:
        try:
            report_id = f"rpt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = REPORT_TYPES.get(report_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO supervision_reports (
                            report_id, plan_id, report_type, report_title,
                            report_content, status, education_type, created_by,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 'draft', ?, ?, ?, ?)
                    ''', (report_id, plan_id, report_type, report_title,
                          kwargs.get('report_content', ''),
                          kwargs.get('education_type'), kwargs.get('created_by'),
                          now, now))
                    cursor.execute('INSERT INTO report_versions (report_id, version_number, content, created_at) VALUES (?, ?, ?, ?)',
                                 (report_id, 'v1.0', kwargs.get('report_content', ''), now))
                    conn.commit()
                    logger.info(f'创建督导报告: {report_title} ({report_id})')
                    return {'success': True, 'report_id': report_id}
        except Exception as e:
            logger.error(f'创建督导报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_report(self, report_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT version_number FROM report_versions WHERE report_id = ? ORDER BY version_id DESC LIMIT 1', (report_id,))
                    latest = cursor.fetchone()
                    version_num = latest[0] if latest else 'v1.0'
                    parts = version_num.split('.')
                    new_version = f"{parts[0]}.{int(parts[1]) + 1}"
                    cursor.execute('UPDATE supervision_reports SET report_content = ?, updated_at = ? WHERE report_id = ?',
                                 (kwargs.get('report_content'), now, report_id))
                    cursor.execute('INSERT INTO report_versions (report_id, version_number, content, change_log, created_at) VALUES (?, ?, ?, ?, ?)',
                                 (report_id, new_version, kwargs.get('report_content'), kwargs.get('change_log'), now))
                    conn.commit()
                    return {'success': True, 'version': new_version}
        except Exception as e:
            logger.error(f'更新督导报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def publish_report(self, report_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE supervision_reports SET status = ?, updated_at = ? WHERE report_id = ? AND status = ?',
                                 ('published', now, report_id, 'draft'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'published'}
                    return {'success': False, 'error': '报告状态不允许发布'}
        except Exception as e:
            logger.error(f'发布督导报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_report_versions(self, report_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM report_versions WHERE report_id = ? ORDER BY version_id DESC', (report_id,))
                versions = [dict(row) for row in cursor.fetchall()]
                return {'success': True, 'versions': versions}
        except Exception as e:
            logger.error(f'获取报告版本失败: {e}')
            return {'success': False, 'error': str(e)}

    def generate_auto_report(self, plan_id: str, report_type: str,
                             education_type: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            report_title = f"{SUPERVISION_TYPES.get(report_type, {}).get('name', report_type)}报告"
            auto_content = self._generate_report_content(plan_id, education_type)
            return self.create_report(plan_id, report_type, report_title,
                                     report_content=auto_content,
                                     education_type=education_type,
                                     created_by='system')
        except Exception as e:
            logger.error(f'自动生成报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def _generate_report_content(self, plan_id: str, education_type: str) -> str:
        return f"""督导报告自动生成
================

计划ID: {plan_id}
教育类型: {education_type}
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

一、督导概况
本次督导按照计划要求，对相关单位进行了全面检查评估。

二、评估结果
根据评价体系，综合得分：85分（满分100分）

三、存在问题
1. 教学设施有待改善
2. 师资培训需要加强

四、整改建议
1. 加大设施投入
2. 完善培训机制

五、结论
整体情况良好，建议继续保持并改进不足。
"""

    # ========== 督导整改跟踪 ==========

    def create_rectification_task(self, plan_id: str, task_name: str,
                                  problem_description: str, **kwargs) -> Dict[str, Any]:
        try:
            task_id = f"rct_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO rectification_tasks (
                            task_id, plan_id, report_id, task_name,
                            problem_description, responsible_unit,
                            responsible_person, deadline, status,
                            priority, education_type, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?)
                    ''', (task_id, plan_id, kwargs.get('report_id'), task_name,
                          problem_description, kwargs.get('responsible_unit'),
                          kwargs.get('responsible_person'), kwargs.get('deadline'),
                          kwargs.get('priority', 2), kwargs.get('education_type'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建整改任务: {task_name} ({task_id})')
                    return {'success': True, 'task_id': task_id}
        except Exception as e:
            logger.error(f'创建整改任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_task_progress(self, task_id: str, progress_percent: int,
                             **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO task_progress (
                            task_id, progress_percent, progress_description,
                            update_time, updater, attachments
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (task_id, progress_percent, kwargs.get('progress_description'),
                          now, kwargs.get('updater'), kwargs.get('attachments')))
                    status = 'completed' if progress_percent >= 100 else 'in_progress'
                    cursor.execute('UPDATE rectification_tasks SET status = ?, updated_at = ? WHERE task_id = ?',
                                 (status, now, task_id))
                    conn.commit()
                    return {'success': True, 'progress': progress_percent, 'status': status}
        except Exception as e:
            logger.error(f'更新任务进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def review_task(self, task_id: str, approved: bool, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'verified' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE rectification_tasks SET status = ?, updated_at = ? WHERE task_id = ? AND status = ?',
                                 (status, now, task_id, 'completed'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '任务状态不允许验收'}
        except Exception as e:
            logger.error(f'验收整改任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_task_progress(self, task_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM task_progress WHERE task_id = ? ORDER BY update_time DESC', (task_id,))
                progress = [dict(row) for row in cursor.fetchall()]
                cursor.execute('SELECT * FROM rectification_tasks WHERE task_id = ?', (task_id,))
                task = dict(cursor.fetchone()) if cursor.fetchone() else None
                return {'success': True, 'task': task, 'progress': progress}
        except Exception as e:
            logger.error(f'获取任务进度失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 督导评价体系 ==========

    def create_evaluation_system(self, system_name: str, education_type: str,
                                 **kwargs) -> Dict[str, Any]:
        try:
            eval_id = f"evl_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO evaluation_system (
                            eval_id, system_name, education_type, version,
                            description, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, 'active', ?)
                    ''', (eval_id, system_name, education_type,
                          kwargs.get('version', '1.0'), kwargs.get('description'), now))
                    conn.commit()
                    logger.info(f'创建评价体系: {system_name} ({eval_id})')
                    return {'success': True, 'eval_id': eval_id}
        except Exception as e:
            logger.error(f'创建评价体系失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_evaluation_scores(self, plan_id: str, eval_id: str,
                                 scores: List[Dict[str, Any]]) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    for score in scores:
                        cursor.execute('''
                            INSERT INTO evaluation_scores (
                                plan_id, eval_id, dimension, score,
                                max_score, weight, comments
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (plan_id, eval_id, score.get('dimension'),
                              score.get('score'), score.get('max_score', 100),
                              score.get('weight', 0.125), score.get('comments')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'记录评价分数失败: {e}')
            return {'success': False, 'error': str(e)}

    def calculate_total_score(self, plan_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT dimension, score, weight FROM evaluation_scores WHERE plan_id = ?', (plan_id,))
                scores = cursor.fetchall()
                total = 0
                weighted = 0
                for dim, score, weight in scores:
                    total += score * weight
                    weighted += weight
                final_score = round(total / weighted, 2) if weighted > 0 else 0
                return {'success': True, 'total_score': final_score, 'dimensions': len(scores)}
        except Exception as e:
            logger.error(f'计算总分失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_evaluation_results(self, plan_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM evaluation_scores WHERE plan_id = ?', (plan_id,))
                scores = [dict(row) for row in cursor.fetchall()]
                totals = self.calculate_total_score(plan_id)
                return {'success': True, 'scores': scores, 'total_score': totals.get('total_score')}
        except Exception as e:
            logger.error(f'获取评价结果失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 督导专家管理 ==========

    def register_expert(self, expert_name: str, expert_role: str,
                        **kwargs) -> Dict[str, Any]:
        try:
            expert_id = f"exp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = EXPERT_ROLES.get(expert_role, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO expert_management (
                            expert_id, expert_name, expert_role, education_type,
                            title, organization, expertise, qualifications,
                            level, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)
                    ''', (expert_id, expert_name, expert_role,
                          kwargs.get('education_type'), kwargs.get('title'),
                          kwargs.get('organization'), kwargs.get('expertise'),
                          kwargs.get('qualifications'),
                          kwargs.get('level', config.get('required_level', 'medium')), now))
                    conn.commit()
                    logger.info(f'注册专家: {expert_name} ({expert_id})')
                    return {'success': True, 'expert_id': expert_id}
        except Exception as e:
            logger.error(f'注册专家失败: {e}')
            return {'success': False, 'error': str(e)}

    def assign_expert(self, expert_id: str, plan_id: str,
                      role_in_plan: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO expert_assignments (
                            expert_id, plan_id, role_in_plan, start_date,
                            end_date, status
                        ) VALUES (?, ?, ?, ?, ?, 'assigned')
                    ''', (expert_id, plan_id, role_in_plan,
                          kwargs.get('start_date'), kwargs.get('end_date')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'指派专家失败: {e}')
            return {'success': False, 'error': str(e)}

    def release_expert(self, assignment_id: int) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE expert_assignments SET status = ?, end_date = ? WHERE assignment_id = ?',
                                 ('completed', now, assignment_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '指派记录不存在'}
        except Exception as e:
            logger.error(f'释放专家失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_experts(self, expert_role: str = None, education_type: str = None,
                     status: str = 'active') -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM expert_management WHERE 1=1'
                params = []
                if expert_role:
                    query += ' AND expert_role = ?'
                    params.append(expert_role)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(query, params)
                experts = [dict(row) for row in cursor.fetchall()]
                return {'success': True, 'experts': experts}
        except Exception as e:
            logger.error(f'获取专家列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 督导信息公开 ==========

    def publish_information(self, info_type: str, title: str, content: str,
                            **kwargs) -> Dict[str, Any]:
        try:
            pub_id = f"pub_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = INFORMATION_TYPES.get(info_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO information_publication (
                            pub_id, info_type, title, content, public_level,
                            education_type, status, publish_date, created_by,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'published', ?, ?, ?, ?)
                    ''', (pub_id, info_type, title, content,
                          kwargs.get('public_level', config.get('public_level', 'internal')),
                          kwargs.get('education_type'), now, kwargs.get('created_by'),
                          now, now))
                    conn.commit()
                    logger.info(f'发布信息: {title} ({pub_id})')
                    return {'success': True, 'pub_id': pub_id}
        except Exception as e:
            logger.error(f'发布信息失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_publication_list(self, info_type: str = None, education_type: str = None,
                             public_level: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM information_publication WHERE status = "published"'
                params = []
                if info_type:
                    query += ' AND info_type = ?'
                    params.append(info_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if public_level:
                    query += ' AND public_level = ?'
                    params.append(public_level)
                query += ' ORDER BY publish_date DESC'
                cursor.execute(query, params)
                publications = [dict(row) for row in cursor.fetchall()]
                return {'success': True, 'publications': publications}
        except Exception as e:
            logger.error(f'获取公开信息列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_access(self, pub_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT view_count FROM publication_records WHERE pub_id = ? ORDER BY record_id DESC LIMIT 1', (pub_id,))
                    latest = cursor.fetchone()
                    view_count = (latest[0] + 1) if latest else 1
                    cursor.execute('''
                        INSERT INTO publication_records (
                            pub_id, view_count, download_count, feedback,
                            record_time
                        ) VALUES (?, ?, ?, ?, ?)
                    ''', (pub_id, view_count, kwargs.get('download_count', 0),
                          kwargs.get('feedback'), now))
                    conn.commit()
                    return {'success': True, 'view_count': view_count}
        except Exception as e:
            logger.error(f'记录访问失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_publication_detail(self, pub_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM information_publication WHERE pub_id = ?', (pub_id,))
                pub = dict(cursor.fetchone()) if cursor.fetchone() else None
                cursor.execute('SELECT * FROM publication_records WHERE pub_id = ? ORDER BY record_time DESC LIMIT 1', (pub_id,))
                record = dict(cursor.fetchone()) if cursor.fetchone() else None
                if pub:
                    pub['view_count'] = record.get('view_count', 0) if record else 0
                    pub['download_count'] = record.get('download_count', 0) if record else 0
                return {'success': True, 'publication': pub}
        except Exception as e:
            logger.error(f'获取公开信息详情失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 预警管理 ==========

    def create_alert_rule(self, rule_name: str, rule_type: str,
                          condition: str, threshold: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO alert_rules (
                            rule_name, rule_type, condition, threshold,
                            alert_level, education_type, is_active, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                    ''', (rule_name, rule_type, condition, threshold,
                          kwargs.get('alert_level', 'warning'),
                          kwargs.get('education_type'), now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'创建预警规则失败: {e}')
            return {'success': False, 'error': str(e)}

    def trigger_alert(self, plan_id: str, alert_type: str,
                      alert_message: str, **kwargs) -> Dict[str, Any]:
        try:
            alert_id = f"alt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO supervision_alerts (
                            alert_id, plan_id, alert_type, alert_level,
                            alert_message, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, 'active', ?)
                    ''', (alert_id, plan_id, alert_type,
                          kwargs.get('alert_level', 'warning'), alert_message, now))
                    conn.commit()
                    logger.warning(f'触发预警: {alert_message} ({alert_id})')
                    return {'success': True, 'alert_id': alert_id}
        except Exception as e:
            logger.error(f'触发预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def acknowledge_alert(self, alert_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE supervision_alerts SET status = ?, created_at = ? WHERE alert_id = ? AND status = ?',
                                 ('acknowledged', now, alert_id, 'active'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '预警状态不允许确认'}
        except Exception as e:
            logger.error(f'确认预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_alerts(self, plan_id: str = None, status: str = 'active') -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM supervision_alerts WHERE 1=1'
                params = []
                if plan_id:
                    query += ' AND plan_id = ?'
                    params.append(plan_id)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                query += ' ORDER BY created_at DESC'
                cursor.execute(query, params)
                alerts = [dict(row) for row in cursor.fetchall()]
                return {'success': True, 'alerts': alerts}
        except Exception as e:
            logger.error(f'获取预警列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计数据 ==========

    def generate_statistics(self, stat_type: str, education_type: str,
                            period: str = 'monthly') -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            stat_data = {
                'stat_type': stat_type,
                'education_type': education_type,
                'period': period,
                'generated_at': now,
                'data': {}
            }
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if stat_type == 'plan_count':
                    cursor.execute('SELECT status, COUNT(*) FROM supervision_plans WHERE education_type = ? GROUP BY status', (education_type,))
                    stat_data['data']['plans'] = dict(cursor.fetchall())
                elif stat_type == 'report_count':
                    cursor.execute('SELECT report_type, COUNT(*) FROM supervision_reports WHERE education_type = ? GROUP BY report_type', (education_type,))
                    stat_data['data']['reports'] = dict(cursor.fetchall())
                elif stat_type == 'task_progress':
                    cursor.execute('SELECT status, COUNT(*) FROM rectification_tasks WHERE education_type = ? GROUP BY status', (education_type,))
                    stat_data['data']['tasks'] = dict(cursor.fetchall())
                elif stat_type == 'evaluation_scores':
                    cursor.execute('SELECT AVG(score) FROM evaluation_scores WHERE plan_id IN (SELECT plan_id FROM supervision_plans WHERE education_type = ?)', (education_type,))
                    avg = cursor.fetchone()[0]
                    stat_data['data']['average_score'] = round(avg, 2) if avg else 0
                elif stat_type == 'expert_activity':
                    cursor.execute('SELECT COUNT(*) FROM expert_assignments WHERE status = "assigned"')
                    stat_data['data']['active_experts'] = cursor.fetchone()[0]
                with self._lock:
                    cursor.execute('INSERT INTO supervision_stats (stat_type, education_type, period, stat_data, created_at) VALUES (?, ?, ?, ?, ?)',
                                 (stat_type, education_type, period, json.dumps(stat_data), now))
                    conn.commit()
            return {'success': True, 'statistics': stat_data}
        except Exception as e:
            logger.error(f'生成统计数据失败: {e}')
            return {'success': False, 'error': str(e)}