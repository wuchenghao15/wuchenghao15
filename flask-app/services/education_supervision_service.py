#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育督导管理服务 (v15.12.0)
====================================
提供教育督导、教育监察、办学行为规范、督导评估、整改追踪等综合管理服务。

核心能力：
1. 督导计划 - 计划制定、审核、发布、查询
2. 督导任务 - 任务分配、执行、反馈、归档
3. 督导队伍 - 成员管理、资质审核、培训记录
4. 督导执行 - 现场检查、记录录入、评分评估、问题反馈
5. 教育监察 - 监察立项、调查取证、结果认定、通报处理
6. 违规处理 - 违规登记、等级评定、处罚决定、申诉处理
7. 整改追踪 - 整改任务、进度跟踪、复核验收、销号管理
8. 师德师风 - 考核评价、问题查处、培训提升、档案管理
9. 合规检查 - 办学资质、课程设置、财务规范、安全制度
10. 投诉处理 - 投诉受理、调查核实、处理回复、满意度评价
11. 报告管理 - 报告生成、审核发布、归档保存、统计分析
12. 统计分析 - 数据汇总、趋势分析、报表生成

差异化支持：成人教育 / K12教育
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
    'comprehensive': {'name': '综合督导', 'description': '对学校整体办学情况进行全面督导'},
    'special': {'name': '专项督导', 'description': '针对特定领域或问题进行专项督导'},
    'follow_up': {'name': '随访督导', 'description': '不定期对学校进行随访检查'},
    'special_inspection': {'name': '专项检查', 'description': '针对特定事项的专项检查'},
    'assessment': {'name': '评估督导', 'description': '以评估为目的的督导活动'},
    'emergency': {'name': '应急督导', 'description': '突发事件后的应急督导'}
}

INSPECTION_CATEGORIES = {
    'school_norm': {'name': '办学规范', 'items': ['办学许可', '办学范围', '办学条件']},
    'fee_management': {'name': '收费管理', 'items': ['收费标准', '收费公示', '退费管理']},
    'enrollment': {'name': '招生行为', 'items': ['招生宣传', '录取程序', '学籍管理']},
    'teacher_qualification': {'name': '教师资质', 'items': ['教师资格证', '学历达标', '专业匹配']},
    'teaching_quality': {'name': '教学质量', 'items': ['课程实施', '教学效果', '学业评价']},
    'safety_management': {'name': '安全管理', 'items': ['安全制度', '设施安全', '应急预案']},
    'financial_management': {'name': '财务管理', 'items': ['财务制度', '收支规范', '资产登记']},
    'teacher_ethics': {'name': '师德师风', 'items': ['政治思想', '职业道德', '为人师表']}
}

VIOLATION_LEVELS = {
    'minor': {'name': '轻微', 'color': 'green', 'penalty': '警告提醒'},
    'general': {'name': '一般', 'color': 'yellow', 'penalty': '通报批评'},
    'serious': {'name': '较重', 'color': 'orange', 'penalty': '限期整改'},
    'severe': {'name': '严重', 'color': 'red', 'penalty': '行政处罚'},
    'critical': {'name': '特别严重', 'color': 'purple', 'penalty': '吊销许可'}
}

SUPERVISION_STATUS = {
    'planned': {'name': '计划中', 'order': 1},
    'in_progress': {'name': '进行中', 'order': 2},
    'completed': {'name': '已完成', 'order': 3},
    'rectifying': {'name': '整改中', 'order': 4},
    'reviewed': {'name': '已复核', 'order': 5},
    'archived': {'name': '已归档', 'order': 6}
}

DEDICATION_ASPECTS = {
    'political': {'name': '政治思想', 'weight': 0.2, 'description': '政治立场、意识形态'},
    'professional': {'name': '职业道德', 'weight': 0.25, 'description': '敬业精神、职业操守'},
    'role_model': {'name': '为人师表', 'weight': 0.2, 'description': '言行举止、示范作用'},
    'teaching_attitude': {'name': '教学态度', 'weight': 0.15, 'description': '教学责任心、工作热情'},
    'academic_integrity': {'name': '学术诚信', 'weight': 0.1, 'description': '学术规范、科研诚信'},
    'care_students': {'name': '关爱学生', 'weight': 0.1, 'description': '学生关怀、心理健康'}
}

COMPLIANCE_ITEMS = {
    'school_license': {'name': '办学许可证', 'required': True, 'description': '办学许可资质'},
    'teacher_cert': {'name': '教师资格', 'required': True, 'description': '教师从业资格'},
    'curriculum': {'name': '课程设置', 'required': True, 'description': '课程计划与实施'},
    'textbook': {'name': '教材使用', 'required': True, 'description': '教材选用与管理'},
    'safety_system': {'name': '安全制度', 'required': True, 'description': '安全管理体系'},
    'financial_norm': {'name': '财务规范', 'required': True, 'description': '财务管理制度'}
}

REPORT_TYPES = {
    'supervision': {'name': '督导报告', 'template': 'standard'},
    'inspection': {'name': '监察报告', 'template': 'investigation'},
    'special': {'name': '专项报告', 'template': 'special'},
    'rectification': {'name': '整改报告', 'template': 'rectification'},
    'review': {'name': '复核报告', 'template': 'review'},
    'annual': {'name': '年度报告', 'template': 'annual'}
}


class EducationSupervisionService:
    """教育督导管理服务"""

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
                        supervision_type TEXT,
                        education_type TEXT,
                        target_school TEXT,
                        target_level TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        scope TEXT,
                        objectives TEXT,
                        budget REAL DEFAULT 0,
                        status TEXT DEFAULT 'draft',
                        approved_by INTEGER,
                        approved_at TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS supervision_tasks (
                        task_id TEXT PRIMARY KEY,
                        plan_id TEXT,
                        task_name TEXT NOT NULL,
                        task_type TEXT,
                        assignee_id INTEGER,
                        assignee_name TEXT,
                        target_school TEXT,
                        scheduled_date TEXT,
                        status TEXT DEFAULT 'pending',
                        priority TEXT DEFAULT 'normal',
                        description TEXT,
                        completed_at TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS supervision_teams (
                        team_id TEXT PRIMARY KEY,
                        team_name TEXT NOT NULL,
                        leader_id INTEGER,
                        leader_name TEXT,
                        education_type TEXT,
                        specialty TEXT,
                        description TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS supervision_members (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        team_id TEXT NOT NULL,
                        member_id INTEGER NOT NULL,
                        member_name TEXT,
                        role TEXT DEFAULT 'member',
                        qualification TEXT,
                        joined_at TEXT,
                        UNIQUE(team_id, member_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS supervision_records (
                        record_id TEXT PRIMARY KEY,
                        task_id TEXT,
                        plan_id TEXT,
                        school_id INTEGER,
                        school_name TEXT,
                        education_type TEXT,
                        supervisor_id INTEGER,
                        supervisor_name TEXT,
                        record_date TEXT,
                        findings TEXT,
                        score REAL,
                        rating TEXT,
                        issues_found INTEGER DEFAULT 0,
                        photos TEXT,
                        status TEXT DEFAULT 'draft',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS inspection_items (
                        item_id TEXT PRIMARY KEY,
                        inspection_category TEXT,
                        item_name TEXT NOT NULL,
                        education_type TEXT,
                        standard TEXT,
                        weight REAL DEFAULT 1,
                        pass_score REAL DEFAULT 60,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS violation_records (
                        violation_id TEXT PRIMARY KEY,
                        record_id TEXT,
                        school_id INTEGER,
                        school_name TEXT,
                        education_type TEXT,
                        violation_type TEXT,
                        violation_level TEXT,
                        description TEXT,
                        evidence TEXT,
                        responsible_person TEXT,
                        status TEXT DEFAULT 'pending',
                        penalty_decision TEXT,
                        penalty_date TEXT,
                        appealed INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS rectification_tasks (
                        rect_id TEXT PRIMARY KEY,
                        violation_id TEXT,
                        record_id TEXT,
                        school_id INTEGER,
                        school_name TEXT,
                        education_type TEXT,
                        problem_description TEXT,
                        rectification_measures TEXT,
                        deadline TEXT,
                        responsible_person TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS rectification_progress (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        rect_id TEXT NOT NULL,
                        progress REAL DEFAULT 0,
                        status TEXT DEFAULT 'in_progress',
                        update_date TEXT,
                        description TEXT,
                        evidence TEXT,
                        updated_by TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS supervision_reports (
                        report_id TEXT PRIMARY KEY,
                        report_type TEXT,
                        plan_id TEXT,
                        record_id TEXT,
                        school_id INTEGER,
                        school_name TEXT,
                        education_type TEXT,
                        title TEXT NOT NULL,
                        content TEXT,
                        summary TEXT,
                        recommendations TEXT,
                        author_id INTEGER,
                        author_name TEXT,
                        status TEXT DEFAULT 'draft',
                        published_at TEXT,
                        archived INTEGER DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS dedication_evaluations (
                        eval_id TEXT PRIMARY KEY,
                        teacher_id INTEGER NOT NULL,
                        teacher_name TEXT,
                        education_type TEXT,
                        evaluation_period TEXT,
                        political_score REAL DEFAULT 0,
                        professional_score REAL DEFAULT 0,
                        role_model_score REAL DEFAULT 0,
                        teaching_attitude_score REAL DEFAULT 0,
                        academic_integrity_score REAL DEFAULT 0,
                        care_students_score REAL DEFAULT 0,
                        overall_score REAL DEFAULT 0,
                        overall_rating TEXT,
                        evaluator_id INTEGER,
                        evaluator_name TEXT,
                        comments TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS compliance_checks (
                        check_id TEXT PRIMARY KEY,
                        school_id INTEGER,
                        school_name TEXT,
                        education_type TEXT,
                        check_date TEXT,
                        check_items TEXT,
                        status TEXT DEFAULT 'in_progress',
                        completed_at TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS compliance_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        check_id TEXT NOT NULL,
                        item_code TEXT,
                        item_name TEXT,
                        result TEXT DEFAULT 'pending',
                        score REAL,
                        evidence TEXT,
                        comments TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS supervision_comments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        record_id TEXT NOT NULL,
                        commenter_id INTEGER,
                        commenter_name TEXT,
                        comment TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS complaint_handling (
                        complaint_id TEXT PRIMARY KEY,
                        complaint_type TEXT,
                        school_id INTEGER,
                        school_name TEXT,
                        education_type TEXT,
                        complainant_name TEXT,
                        contact_info TEXT,
                        content TEXT,
                        evidence TEXT,
                        status TEXT DEFAULT 'pending',
                        handler_id INTEGER,
                        handler_name TEXT,
                        investigation_result TEXT,
                        handling_measures TEXT,
                        reply_content TEXT,
                        satisfaction_rating INTEGER,
                        closed_at TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS supervision_archive (
                        archive_id TEXT PRIMARY KEY,
                        related_type TEXT,
                        related_id TEXT,
                        title TEXT,
                        education_type TEXT,
                        archive_date TEXT,
                        archived_by INTEGER,
                        file_path TEXT,
                        metadata TEXT,
                        created_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('教育督导管理服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 督导计划 ==========

    def create_supervision_plan(self, plan_name: str, supervision_type: str,
                                education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            plan_id = f"sup_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO supervision_plans (
                            plan_id, plan_name, supervision_type, education_type,
                            target_school, target_level, start_date, end_date,
                            scope, objectives, budget, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?)
                    ''', (plan_id, plan_name, supervision_type, education_type,
                          kwargs.get('target_school'), kwargs.get('target_level'),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          kwargs.get('scope'), kwargs.get('objectives'),
                          kwargs.get('budget', 0), now, now))
                    conn.commit()
                    logger.info(f'创建督导计划: {plan_name} ({plan_id})')
                    return {'success': True, 'plan_id': plan_id}
        except Exception as e:
            logger.error(f'创建督导计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_supervision_plan(self, plan_id: str, approved_by: int,
                                  approved: bool = True) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE supervision_plans SET status = ?, approved_by = ?, approved_at = ?, updated_at = ?
                        WHERE plan_id = ? AND status = 'draft'
                    ''', (status, approved_by, now, now, plan_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '计划状态不允许审核'}
        except Exception as e:
            logger.error(f'审核督导计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def publish_supervision_plan(self, plan_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE supervision_plans SET status = ?, updated_at = ? WHERE plan_id = ? AND status = ?',
                                 ('published', now, plan_id, 'approved'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'published'}
                    return {'success': False, 'error': '计划状态不允许发布'}
        except Exception as e:
            logger.error(f'发布督导计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_supervision_plans(self, education_type: str = None,
                               status: str = None, page: int = 1,
                               page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM supervision_plans WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                plans = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'plans': plans, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取督导计划列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 督导任务 ==========

    def create_supervision_task(self, plan_id: str, task_name: str,
                                 assignee_id: int, assignee_name: str,
                                 **kwargs) -> Dict[str, Any]:
        try:
            task_id = f"task_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT education_type FROM supervision_plans WHERE plan_id = ?', (plan_id,))
                    plan = cursor.fetchone()
                    if not plan:
                        return {'success': False, 'error': '督导计划不存在'}
                    cursor.execute('''
                        INSERT INTO supervision_tasks (
                            task_id, plan_id, task_name, task_type,
                            assignee_id, assignee_name, target_school,
                            scheduled_date, status, priority, description,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?)
                    ''', (task_id, plan_id, task_name, kwargs.get('task_type'),
                          assignee_id, assignee_name, kwargs.get('target_school'),
                          kwargs.get('scheduled_date'), kwargs.get('priority', 'normal'),
                          kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建督导任务: {task_name} ({task_id})')
                    return {'success': True, 'task_id': task_id}
        except Exception as e:
            logger.error(f'创建督导任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def assign_supervision_task(self, task_id: str, assignee_id: int,
                                 assignee_name: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE supervision_tasks SET assignee_id = ?, assignee_name = ?, status = ?, updated_at = ? WHERE task_id = ? AND status = ?',
                                 (assignee_id, assignee_name, 'assigned', now, task_id, 'pending'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'assigned'}
                    return {'success': False, 'error': '任务状态不允许分配'}
        except Exception as e:
            logger.error(f'分配督导任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_supervision_task(self, task_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE supervision_tasks SET status = ?, completed_at = ?, updated_at = ? WHERE task_id = ? AND status IN (?, ?)',
                                 ('completed', now, now, task_id, 'assigned', 'in_progress'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'completed'}
                    return {'success': False, 'error': '任务状态不允许完成'}
        except Exception as e:
            logger.error(f'完成督导任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def archive_supervision_task(self, task_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE supervision_tasks SET status = ?, updated_at = ? WHERE task_id = ? AND status = ?',
                                 ('archived', now, task_id, 'completed'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'archived'}
                    return {'success': False, 'error': '任务状态不允许归档'}
        except Exception as e:
            logger.error(f'归档督导任务失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 督导队伍 ==========

    def create_supervision_team(self, team_name: str, leader_id: int,
                                 leader_name: str, **kwargs) -> Dict[str, Any]:
        try:
            team_id = f"team_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO supervision_teams (
                            team_id, team_name, leader_id, leader_name,
                            education_type, specialty, description, is_active,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                    ''', (team_id, team_name, leader_id, leader_name,
                          kwargs.get('education_type'), kwargs.get('specialty'),
                          kwargs.get('description'), now, now))
                    cursor.execute('INSERT INTO supervision_members (team_id, member_id, member_name, role, joined_at) VALUES (?, ?, ?, ?, ?)',
                                 (team_id, leader_id, leader_name, 'leader', now))
                    conn.commit()
                    logger.info(f'创建督导队伍: {team_name} ({team_id})')
                    return {'success': True, 'team_id': team_id}
        except Exception as e:
            logger.error(f'创建督导队伍失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_team_member(self, team_id: str, member_id: int, member_name: str,
                        **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT OR IGNORE INTO supervision_members (team_id, member_id, member_name, role, qualification, joined_at) VALUES (?, ?, ?, ?, ?, ?)',
                                 (team_id, member_id, member_name, kwargs.get('role', 'member'), kwargs.get('qualification'), now))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '成员已加入该队伍'}
        except Exception as e:
            logger.error(f'添加队伍成员失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_team_members(self, team_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM supervision_members WHERE team_id = ? ORDER BY joined_at ASC', (team_id,))
                members = [dict(m) for m in cursor.fetchall()]
                return {'success': True, 'members': members}
        except Exception as e:
            logger.error(f'获取队伍成员失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 督导执行 ==========

    def create_supervision_record(self, task_id: str, school_id: int,
                                   school_name: str, education_type: str,
                                   supervisor_id: int, supervisor_name: str,
                                   **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"rec_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT plan_id FROM supervision_tasks WHERE task_id = ?', (task_id,))
                    task = cursor.fetchone()
                    plan_id = task[0] if task else None
                    cursor.execute('''
                        INSERT INTO supervision_records (
                            record_id, task_id, plan_id, school_id, school_name,
                            education_type, supervisor_id, supervisor_name,
                            record_date, findings, score, rating, issues_found,
                            photos, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 'draft', ?, ?)
                    ''', (record_id, task_id, plan_id, school_id, school_name,
                          education_type, supervisor_id, supervisor_name,
                          kwargs.get('record_date', now[:10]), kwargs.get('findings'),
                          kwargs.get('score'), kwargs.get('rating'), kwargs.get('photos'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建督导记录: {record_id}')
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'创建督导记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_supervision_record(self, record_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    updates = []
                    params = []
                    if 'findings' in kwargs:
                        updates.append('findings = ?')
                        params.append(kwargs['findings'])
                    if 'score' in kwargs:
                        updates.append('score = ?')
                        params.append(kwargs['score'])
                        score = kwargs['score']
                        rating = 'excellent' if score >= 90 else ('good' if score >= 80 else ('pass' if score >= 60 else 'fail'))
                        updates.append('rating = ?')
                        params.append(rating)
                    if 'issues_found' in kwargs:
                        updates.append('issues_found = ?')
                        params.append(kwargs['issues_found'])
                    if 'photos' in kwargs:
                        updates.append('photos = ?')
                        params.append(kwargs['photos'])
                    if updates:
                        updates.append('updated_at = ?')
                        params.append(now)
                        params.append(record_id)
                        query = f'UPDATE supervision_records SET {", ".join(updates)} WHERE record_id = ?'
                        cursor.execute(query, params)
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '未提供更新字段'}
        except Exception as e:
            logger.error(f'更新督导记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def submit_supervision_record(self, record_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE supervision_records SET status = ?, updated_at = ? WHERE record_id = ? AND status = ?',
                                 ('submitted', now, record_id, 'draft'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'submitted'}
                    return {'success': False, 'error': '记录状态不允许提交'}
        except Exception as e:
            logger.error(f'提交督导记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_supervision_record(self, record_id: str, approved: bool = True) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE supervision_records SET status = ?, updated_at = ? WHERE record_id = ? AND status = ?',
                                 (status, now, record_id, 'submitted'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '记录状态不允许审核'}
        except Exception as e:
            logger.error(f'审核督导记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_supervision_comment(self, record_id: str, commenter_id: int,
                                 commenter_name: str, comment: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO supervision_comments (record_id, commenter_id, commenter_name, comment, created_at) VALUES (?, ?, ?, ?, ?)',
                                 (record_id, commenter_id, commenter_name, comment, now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加督导评论失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 教育监察 ==========

    def create_inspection_item(self, inspection_category: str, item_name: str,
                                **kwargs) -> Dict[str, Any]:
        try:
            item_id = f"ins_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO inspection_items (
                            item_id, inspection_category, item_name,
                            education_type, standard, weight, pass_score,
                            created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (item_id, inspection_category, item_name,
                          kwargs.get('education_type'), kwargs.get('standard'),
                          kwargs.get('weight', 1), kwargs.get('pass_score', 60),
                          now))
                    conn.commit()
                    logger.info(f'创建监察项: {item_name} ({item_id})')
                    return {'success': True, 'item_id': item_id}
        except Exception as e:
            logger.error(f'创建监察项失败: {e}')
            return {'success': False, 'error': str(e)}

    def conduct_inspection(self, school_id: int, school_name: str,
                            education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            check_id = f"chk_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO compliance_checks (
                            check_id, school_id, school_name, education_type,
                            check_date, check_items, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'in_progress', ?, ?)
                    ''', (check_id, school_id, school_name, education_type,
                          kwargs.get('check_date', now[:10]),
                          kwargs.get('check_items', '{}'), now, now))
                    conn.commit()
                    logger.info(f'启动合规检查: {school_name} ({check_id})')
                    return {'success': True, 'check_id': check_id}
        except Exception as e:
            logger.error(f'启动合规检查失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_compliance_result(self, check_id: str, item_code: str,
                                  item_name: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO compliance_results (check_id, item_code, item_name, result, score, evidence, comments)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (check_id, item_code, item_name,
                          kwargs.get('result', 'pending'), kwargs.get('score'),
                          kwargs.get('evidence'), kwargs.get('comments')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'记录合规结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_compliance_check(self, check_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE compliance_checks SET status = ?, completed_at = ?, updated_at = ? WHERE check_id = ? AND status = ?',
                                 ('completed', now, now, check_id, 'in_progress'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'completed'}
                    return {'success': False, 'error': '检查状态不允许完成'}
        except Exception as e:
            logger.error(f'完成合规检查失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 违规处理 ==========

    def create_violation_record(self, record_id: str, school_id: int,
                                 school_name: str, education_type: str,
                                 violation_type: str, description: str,
                                 **kwargs) -> Dict[str, Any]:
        try:
            violation_id = f"vio_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO violation_records (
                            violation_id, record_id, school_id, school_name,
                            education_type, violation_type, violation_level,
                            description, evidence, responsible_person,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                    ''', (violation_id, record_id, school_id, school_name,
                          education_type, violation_type, kwargs.get('violation_level', 'general'),
                          description, kwargs.get('evidence'), kwargs.get('responsible_person'),
                          now, now))
                    conn.commit()
                    logger.info(f'登记违规记录: {violation_id}')
                    return {'success': True, 'violation_id': violation_id}
        except Exception as e:
            logger.error(f'登记违规记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def assess_violation_level(self, violation_id: str, violation_level: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE violation_records SET violation_level = ?, updated_at = ? WHERE violation_id = ?',
                                 (violation_level, now, violation_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'violation_level': violation_level}
                    return {'success': False, 'error': '违规记录不存在'}
        except Exception as e:
            logger.error(f'评定违规等级失败: {e}')
            return {'success': False, 'error': str(e)}

    def issue_penalty(self, violation_id: str, penalty_decision: str,
                       **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE violation_records SET penalty_decision = ?, penalty_date = ?, status = ?, updated_at = ? WHERE violation_id = ? AND status = ?',
                                 (penalty_decision, now, 'penalized', now, violation_id, 'pending'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'penalized'}
                    return {'success': False, 'error': '违规记录状态不允许处罚'}
        except Exception as e:
            logger.error(f'作出处罚决定失败: {e}')
            return {'success': False, 'error': str(e)}

    def handle_appeal(self, violation_id: str, appeal_result: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE violation_records SET appealed = 1, status = ?, updated_at = ? WHERE violation_id = ?',
                                 (appeal_result, now, violation_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'appeal_result': appeal_result}
                    return {'success': False, 'error': '违规记录不存在'}
        except Exception as e:
            logger.error(f'处理申诉失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 整改追踪 ==========

    def create_rectification_task(self, violation_id: str, school_id: int,
                                   school_name: str, education_type: str,
                                   problem_description: str,
                                   rectification_measures: str, **kwargs) -> Dict[str, Any]:
        try:
            rect_id = f"rect_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT record_id FROM violation_records WHERE violation_id = ?', (violation_id,))
                    violation = cursor.fetchone()
                    record_id = violation[0] if violation else None
                    cursor.execute('''
                        INSERT INTO rectification_tasks (
                            rect_id, violation_id, record_id, school_id, school_name,
                            education_type, problem_description, rectification_measures,
                            deadline, responsible_person, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                    ''', (rect_id, violation_id, record_id, school_id, school_name,
                          education_type, problem_description, rectification_measures,
                          kwargs.get('deadline'), kwargs.get('responsible_person'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建整改任务: {rect_id}')
                    return {'success': True, 'rect_id': rect_id}
        except Exception as e:
            logger.error(f'创建整改任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_rectification_progress(self, rect_id: str, progress: float,
                                       **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'completed' if progress >= 100 else ('in_progress' if progress > 0 else 'pending')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO rectification_progress (rect_id, progress, status, update_date, description, evidence, updated_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (rect_id, progress, status, now[:10], kwargs.get('description'), kwargs.get('evidence'), kwargs.get('updated_by')))
                    cursor.execute('UPDATE rectification_tasks SET status = ?, updated_at = ? WHERE rect_id = ?',
                                 (status, now, rect_id))
                    conn.commit()
                    return {'success': True, 'progress': progress, 'status': status}
        except Exception as e:
            logger.error(f'更新整改进度失败: {e}')
            return {'success': False, 'error': str(e)}

    def review_rectification(self, rect_id: str, reviewed_by: str,
                             approved: bool = True) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE rectification_tasks SET status = ?, updated_at = ? WHERE rect_id = ? AND status = ?',
                                 (status, now, rect_id, 'completed'))
                    if cursor.rowcount > 0:
                        cursor.execute('INSERT INTO rectification_progress (rect_id, progress, status, update_date, description, updated_by) VALUES (?, ?, ?, ?, ?, ?)',
                                     (rect_id, 100 if approved else 0, status, now[:10], '复核完成', reviewed_by))
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '整改任务状态不允许复核'}
        except Exception as e:
            logger.error(f'复核整改任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def close_rectification(self, rect_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE rectification_tasks SET status = ?, updated_at = ? WHERE rect_id = ? AND status = ?',
                                 ('closed', now, rect_id, 'approved'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'closed'}
                    return {'success': False, 'error': '整改任务状态不允许销号'}
        except Exception as e:
            logger.error(f'销号整改任务失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 师德师风 ==========

    def create_dedication_evaluation(self, teacher_id: int, teacher_name: str,
                                      education_type: str, evaluation_period: str,
                                      **kwargs) -> Dict[str, Any]:
        try:
            eval_id = f"ded_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            scores = {k: kwargs.get(k, 0) for k in ['political_score', 'professional_score', 'role_model_score', 'teaching_attitude_score', 'academic_integrity_score', 'care_students_score']}
            weights = {'political_score': 0.2, 'professional_score': 0.25, 'role_model_score': 0.2, 'teaching_attitude_score': 0.15, 'academic_integrity_score': 0.1, 'care_students_score': 0.1}
            overall_score = sum(scores[k] * weights[k] for k in scores)
            overall_rating = 'excellent' if overall_score >= 90 else ('good' if overall_score >= 80 else ('pass' if overall_score >= 60 else 'fail'))
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO dedication_evaluations (
                            eval_id, teacher_id, teacher_name, education_type,
                            evaluation_period, political_score, professional_score,
                            role_model_score, teaching_attitude_score,
                            academic_integrity_score, care_students_score,
                            overall_score, overall_rating, evaluator_id,
                            evaluator_name, comments, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                    ''', (eval_id, teacher_id, teacher_name, education_type,
                          evaluation_period, scores['political_score'], scores['professional_score'],
                          scores['role_model_score'], scores['teaching_attitude_score'],
                          scores['academic_integrity_score'], scores['care_students_score'],
                          round(overall_score, 1), overall_rating, kwargs.get('evaluator_id'),
                          kwargs.get('evaluator_name'), kwargs.get('comments'), now, now))
                    conn.commit()
                    logger.info(f'创建师德师风评价: {teacher_name} ({eval_id})')
                    return {'success': True, 'eval_id': eval_id, 'overall_score': round(overall_score, 1), 'overall_rating': overall_rating}
        except Exception as e:
            logger.error(f'创建师德师风评价失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_dedication_scores(self, eval_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT political_score, professional_score, role_model_score, teaching_attitude_score, academic_integrity_score, care_students_score FROM dedication_evaluations WHERE eval_id = ?', (eval_id,))
                    current = cursor.fetchone()
                    if not current:
                        return {'success': False, 'error': '评价记录不存在'}
                    scores = dict(zip(['political_score', 'professional_score', 'role_model_score', 'teaching_attitude_score', 'academic_integrity_score', 'care_students_score'], current))
                    scores.update({k: v for k, v in kwargs.items() if k in scores})
                    weights = {'political_score': 0.2, 'professional_score': 0.25, 'role_model_score': 0.2, 'teaching_attitude_score': 0.15, 'academic_integrity_score': 0.1, 'care_students_score': 0.1}
                    overall_score = sum(scores[k] * weights[k] for k in scores)
                    overall_rating = 'excellent' if overall_score >= 90 else ('good' if overall_score >= 80 else ('pass' if overall_score >= 60 else 'fail'))
                    cursor.execute('''
                        UPDATE dedication_evaluations SET
                            political_score = ?, professional_score = ?,
                            role_model_score = ?, teaching_attitude_score = ?,
                            academic_integrity_score = ?, care_students_score = ?,
                            overall_score = ?, overall_rating = ?, updated_at = ?
                        WHERE eval_id = ?
                    ''', (scores['political_score'], scores['professional_score'],
                          scores['role_model_score'], scores['teaching_attitude_score'],
                          scores['academic_integrity_score'], scores['care_students_score'],
                          round(overall_score, 1), overall_rating, now, eval_id))
                    conn.commit()
                    return {'success': True, 'overall_score': round(overall_score, 1), 'overall_rating': overall_rating}
        except Exception as e:
            logger.error(f'更新师德师风评分失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_dedication_evaluation(self, eval_id: str, approved: bool = True) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE dedication_evaluations SET status = ?, updated_at = ? WHERE eval_id = ? AND status = ?',
                                 (status, now, eval_id, 'pending'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '评价状态不允许审核'}
        except Exception as e:
            logger.error(f'审核师德师风评价失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_dedication_evaluations(self, teacher_id: int = None,
                                     education_type: str = None, page: int = 1,
                                     page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM dedication_evaluations WHERE 1=1'
                params = []
                if teacher_id:
                    query += ' AND teacher_id = ?'
                    params.append(teacher_id)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY evaluation_period DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                evals = [dict(e) for e in cursor.fetchall()]
                return {'success': True, 'evaluations': evals, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取师德师风评价列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 合规检查 ==========

    def create_compliance_check(self, school_id: int, school_name: str,
                                 education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            check_id = f"cck_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO compliance_checks (
                            check_id, school_id, school_name, education_type,
                            check_date, check_items, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'in_progress', ?, ?)
                    ''', (check_id, school_id, school_name, education_type,
                          kwargs.get('check_date', now[:10]),
                          json.dumps(kwargs.get('check_items', [])), now, now))
                    conn.commit()
                    logger.info(f'创建合规检查: {school_name} ({check_id})')
                    return {'success': True, 'check_id': check_id}
        except Exception as e:
            logger.error(f'创建合规检查失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_compliance_result(self, check_id: str, item_code: str,
                               item_name: str, result: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO compliance_results (check_id, item_code, item_name, result, score, evidence, comments)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (check_id, item_code, item_name, result,
                          kwargs.get('score'), kwargs.get('evidence'), kwargs.get('comments')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加合规检查结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_compliance_summary(self, check_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM compliance_checks WHERE check_id = ?', (check_id,))
                check = cursor.fetchone()
                if not check:
                    return {'success': False, 'error': '检查记录不存在'}
                cursor.execute('SELECT * FROM compliance_results WHERE check_id = ?', (check_id,))
                results = [dict(r) for r in cursor.fetchall()]
                passed = sum(1 for r in results if r['result'] == 'pass')
                failed = sum(1 for r in results if r['result'] == 'fail')
                pending = sum(1 for r in results if r['result'] == 'pending')
                avg_score = round(sum(r['score'] for r in results if r['score']) / len(results), 1) if results else 0
                return {
                    'success': True,
                    'check': dict(check),
                    'results': results,
                    'summary': {'total': len(results), 'passed': passed, 'failed': failed, 'pending': pending, 'avg_score': avg_score}
                }
        except Exception as e:
            logger.error(f'获取合规检查汇总失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_compliance_checks(self, school_id: int = None,
                                education_type: str = None, page: int = 1,
                                page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM compliance_checks WHERE 1=1'
                params = []
                if school_id:
                    query += ' AND school_id = ?'
                    params.append(school_id)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY check_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                checks = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'checks': checks, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取合规检查列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 投诉处理 ==========

    def create_complaint(self, complaint_type: str, school_id: int,
                          school_name: str, education_type: str,
                          complainant_name: str, content: str, **kwargs) -> Dict[str, Any]:
        try:
            complaint_id = f"cmp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO complaint_handling (
                            complaint_id, complaint_type, school_id, school_name,
                            education_type, complainant_name, contact_info,
                            content, evidence, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                    ''', (complaint_id, complaint_type, school_id, school_name,
                          education_type, complainant_name, kwargs.get('contact_info'),
                          content, kwargs.get('evidence'), now, now))
                    conn.commit()
                    logger.info(f'受理投诉: {complaint_id}')
                    return {'success': True, 'complaint_id': complaint_id}
        except Exception as e:
            logger.error(f'受理投诉失败: {e}')
            return {'success': False, 'error': str(e)}

    def assign_complaint(self, complaint_id: str, handler_id: int,
                          handler_name: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE complaint_handling SET handler_id = ?, handler_name = ?, status = ?, updated_at = ? WHERE complaint_id = ? AND status = ?',
                                 (handler_id, handler_name, 'processing', now, complaint_id, 'pending'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'processing'}
                    return {'success': False, 'error': '投诉状态不允许分配'}
        except Exception as e:
            logger.error(f'分配投诉处理失败: {e}')
            return {'success': False, 'error': str(e)}

    def resolve_complaint(self, complaint_id: str, investigation_result: str,
                           handling_measures: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE complaint_handling SET investigation_result = ?, handling_measures = ?, reply_content = ?, status = ?, updated_at = ? WHERE complaint_id = ? AND status = ?',
                                 (investigation_result, handling_measures, kwargs.get('reply_content'), 'resolved', now, complaint_id, 'processing'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'resolved'}
                    return {'success': False, 'error': '投诉状态不允许处理'}
        except Exception as e:
            logger.error(f'处理投诉失败: {e}')
            return {'success': False, 'error': str(e)}

    def close_complaint(self, complaint_id: str, satisfaction_rating: int = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    if satisfaction_rating:
                        cursor.execute('UPDATE complaint_handling SET satisfaction_rating = ?, status = ?, closed_at = ?, updated_at = ? WHERE complaint_id = ? AND status = ?',
                                     (satisfaction_rating, 'closed', now, now, complaint_id, 'resolved'))
                    else:
                        cursor.execute('UPDATE complaint_handling SET status = ?, closed_at = ?, updated_at = ? WHERE complaint_id = ? AND status = ?',
                                     ('closed', now, now, complaint_id, 'resolved'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'closed'}
                    return {'success': False, 'error': '投诉状态不允许关闭'}
        except Exception as e:
            logger.error(f'关闭投诉失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 报告管理 ==========

    def create_supervision_report(self, report_type: str, title: str,
                                   author_id: int, author_name: str, **kwargs) -> Dict[str, Any]:
        try:
            report_id = f"rpt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO supervision_reports (
                            report_id, report_type, plan_id, record_id,
                            school_id, school_name, education_type, title,
                            content, summary, recommendations, author_id,
                            author_name, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?)
                    ''', (report_id, report_type, kwargs.get('plan_id'), kwargs.get('record_id'),
                          kwargs.get('school_id'), kwargs.get('school_name'),
                          kwargs.get('education_type'), title, kwargs.get('content'),
                          kwargs.get('summary'), kwargs.get('recommendations'),
                          author_id, author_name, now, now))
                    conn.commit()
                    logger.info(f'创建督导报告: {title} ({report_id})')
                    return {'success': True, 'report_id': report_id}
        except Exception as e:
            logger.error(f'创建督导报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_supervision_report(self, report_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    updates = []
                    params = []
                    for field in ['content', 'summary', 'recommendations']:
                        if field in kwargs:
                            updates.append(f'{field} = ?')
                            params.append(kwargs[field])
                    if updates:
                        updates.append('updated_at = ?')
                        params.append(now)
                        params.append(report_id)
                        query = f'UPDATE supervision_reports SET {", ".join(updates)} WHERE report_id = ?'
                        cursor.execute(query, params)
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '未提供更新字段'}
        except Exception as e:
            logger.error(f'更新督导报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def publish_supervision_report(self, report_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE supervision_reports SET status = ?, published_at = ?, updated_at = ? WHERE report_id = ? AND status = ?',
                                 ('published', now, now, report_id, 'approved'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': 'published'}
                    return {'success': False, 'error': '报告状态不允许发布'}
        except Exception as e:
            logger.error(f'发布督导报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def archive_supervision_report(self, report_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE supervision_reports SET archived = 1, updated_at = ? WHERE report_id = ?',
                                 (now, report_id))
                    if cursor.rowcount > 0:
                        cursor.execute('INSERT INTO supervision_archive (archive_id, related_type, related_id, title, education_type, archive_date, archived_by, metadata, created_at) SELECT ?, ?, ?, title, education_type, ?, ?, ?, ? FROM supervision_reports WHERE report_id = ?',
                                     (f"arc_{uuid.uuid4().hex[:12]}", 'report', report_id, now[:10], None, '{}', now, report_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '报告不存在'}
        except Exception as e:
            logger.error(f'归档督导报告失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 ==========

    def get_supervision_statistics(self, education_type: str = None,
                                    start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                where_clause = ' WHERE 1=1'
                params = []
                if education_type:
                    where_clause += ' AND education_type = ?'
                    params.append(education_type)
                if start_date:
                    where_clause += ' AND record_date >= ?'
                    params.append(start_date)
                if end_date:
                    where_clause += ' AND record_date <= ?'
                    params.append(end_date)
                cursor.execute(f'SELECT COUNT(*) FROM supervision_records{where_clause}', params)
                total_records = cursor.fetchone()[0]
                cursor.execute(f'SELECT COUNT(*) FROM supervision_plans{where_clause}', params)
                total_plans = cursor.fetchone()[0]
                cursor.execute(f'SELECT COUNT(*) FROM violation_records{where_clause}', params)
                total_violations = cursor.fetchone()[0]
                cursor.execute(f'SELECT COUNT(*) FROM rectification_tasks{where_clause}', params)
                total_rectifications = cursor.fetchone()[0]
                cursor.execute(f'SELECT COUNT(*) FROM complaint_handling{where_clause}', params)
                total_complaints = cursor.fetchone()[0]
                cursor.execute(f'SELECT AVG(score) FROM supervision_records{where_clause} AND score IS NOT NULL', params)
                avg_score_result = cursor.fetchone()
                avg_score = round(avg_score_result[0], 1) if avg_score_result and avg_score_result[0] else 0
                cursor.execute(f'SELECT violation_level, COUNT(*) FROM violation_records{where_clause} GROUP BY violation_level', params)
                violation_distribution = {r[0]: r[1] for r in cursor.fetchall()}
                cursor.execute(f'SELECT status, COUNT(*) FROM supervision_records{where_clause} GROUP BY status', params)
                record_status_distribution = {r[0]: r[1] for r in cursor.fetchall()}
                cursor.execute(f'SELECT status, COUNT(*) FROM rectification_tasks{where_clause} GROUP BY status', params)
                rectification_status_distribution = {r[0]: r[1] for r in cursor.fetchall()}
                cursor.execute(f'SELECT status, COUNT(*) FROM complaint_handling{where_clause} GROUP BY status', params)
                complaint_status_distribution = {r[0]: r[1] for r in cursor.fetchall()}
                return {
                    'success': True,
                    'summary': {
                        'total_records': total_records,
                        'total_plans': total_plans,
                        'total_violations': total_violations,
                        'total_rectifications': total_rectifications,
                        'total_complaints': total_complaints,
                        'avg_score': avg_score
                    },
                    'distributions': {
                        'violation_level': violation_distribution,
                        'record_status': record_status_distribution,
                        'rectification_status': rectification_status_distribution,
                        'complaint_status': complaint_status_distribution
                    }
                }
        except Exception as e:
            logger.error(f'获取督导统计数据失败: {e}')
            return {'success': False, 'error': str(e)}