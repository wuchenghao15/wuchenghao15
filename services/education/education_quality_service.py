from core.db_path import get_db_path as _mtscos_get_db_path
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS 教育质量督导评估服务 (v15.10.0) ====================================== 提供教育质量督导、办学水平评估、质量监测和整改追踪等综合管理服务， 支持成人教育和K12教育的差异化评估需求。  核心能力： 1. 教学督导 - 督导计划、听课评课、督导报告 2. 办学水平评估 - 评估指标体系、自评、专家组评估 3. 质量监测 - 教学质量监测、数据采集、质量报告 4. 整改追踪 - 问题发现、整改通知、整改落实 5. 督导队伍 - 督导员管理、培训、考核 6. 评估指标 - 指标体系管理、权重配置 7. 质量报告 - 定期报告、专项报告 8. 成人教育质量与K12教育质量差异化评估 """
import os
import json
import uuid
import sqlite3
import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

DATABASE_PATH = _mtscos_get_db_path('app.db')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_quality_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationQuality')


# ========== 督导评估配置 ==========

# 督导类型
SUPERVISION_TYPES = {
    'routine': {'name': '常规督导', 'frequency': '每月'},
    'special': {'name': '专项督导', 'frequency': '按需'},
    'follow_up': {'name': '随访督导', 'frequency': '不定期'},
    'comprehensive': {'name': '综合督导', 'frequency': '每学期'},
    'emergency': {'name': '紧急督导', 'frequency': '紧急触发'}
}

# 督导状态
SUPERVISION_STATUS = {
    'planned': {'name': '计划中'},
    'in_progress': {'name': '进行中'},
    'completed': {'name': '已完成'},
    'cancelled': {'name': '已取消'}
}

# 评估维度
EVALUATION_DIMENSIONS = {
    'teaching_quality': {'name': '教学质量', 'default_weight': 0.30},
    'management_level': {'name': '管理水平', 'default_weight': 0.20},
    'student_development': {'name': '学生发展', 'default_weight': 0.20},
    'teacher_growth': {'name': '教师发展', 'default_weight': 0.10},
    'condition_support': {'name': '条件保障', 'default_weight': 0.10},
    'social_recognition': {'name': '社会认可', 'default_weight': 0.10}
}

# 指标级别
INDICATOR_LEVELS = {
    'level1': {'name': '一级指标', 'level': 1},
    'level2': {'name': '二级指标', 'level': 2},
    'level3': {'name': '三级指标', 'level': 3}
}

# 评估等级
EVALUATION_GRADES = {
    'excellent': {'name': '优秀', 'grade': 'A', 'score_range': '90-100'},
    'good': {'name': '良好', 'grade': 'B', 'score_range': '80-89'},
    'qualified': {'name': '合格', 'grade': 'C', 'score_range': '60-79'},
    'unqualified': {'name': '不合格', 'grade': 'D', 'score_range': '0-59'}
}

# 问题严重程度
ISSUE_SEVERITY = {
    'minor': {'name': '轻微', 'response_time': 72},
    'moderate': {'name': '中等', 'response_time': 48},
    'major': {'name': '严重', 'response_time': 24},
    'critical': {'name': '严重', 'response_time': 12}
}

# 整改状态
RECTIFICATION_STATUS = {
    'issued': {'name': '已下发'},
    'in_progress': {'name': '整改中'},
    'completed': {'name': '已完成'},
    'verified': {'name': '已验证'},
    'overdue': {'name': '逾期未改'}
}

# 报告类型
REPORT_TYPES = {
    'monthly': {'name': '月报', 'required_review': True},
    'quarterly': {'name': '季报', 'required_review': True},
    'annual': {'name': '年报', 'required_review': True},
    'special': {'name': '专项报告', 'required_review': True},
    'supervision': {'name': '督导报告', 'required_review': False},
    'evaluation': {'name': '评估报告', 'required_review': True}
}


class EducationQualityService:
    """教育质量督导评估服务"""

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
                cursor.execute(''' CREATE TABLE IF NOT EXISTS supervisors ( supervisor_id TEXT PRIMARY KEY, user_id TEXT, name TEXT NOT NULL, title TEXT, department TEXT, specialties TEXT, level TEXT, max_assignments INTEGER DEFAULT 5, current_assignments INTEGER DEFAULT 0, training_hours REAL DEFAULT 0, evaluation_score REAL DEFAULT 0, is_active INTEGER DEFAULT 1, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS supervision_plans ( plan_id TEXT PRIMARY KEY, plan_name TEXT NOT NULL, supervision_type TEXT, target_scope TEXT, target_department TEXT, supervisor_id TEXT, supervisor_name TEXT, start_date TEXT, end_date TEXT, objectives TEXT, status TEXT DEFAULT 'planned', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS classroom_observations ( observation_id TEXT PRIMARY KEY, plan_id TEXT, supervisor_id TEXT, supervisor_name TEXT, teacher_id TEXT, teacher_name TEXT, course_name TEXT, class_name TEXT, observation_date TEXT, observation_type TEXT, lesson_content TEXT, dimensions TEXT, total_score REAL, grade TEXT, strengths TEXT, weaknesses TEXT, suggestions TEXT, status TEXT DEFAULT 'completed', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS supervision_reports ( report_id TEXT PRIMARY KEY, plan_id TEXT, supervisor_id TEXT, supervisor_name TEXT, report_type TEXT DEFAULT 'supervision', title TEXT, content TEXT, findings TEXT, recommendations TEXT, issues_found TEXT, status TEXT DEFAULT 'draft', reviewed_by TEXT, reviewed_at TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS evaluation_systems ( system_id TEXT PRIMARY KEY, system_name TEXT NOT NULL, evaluation_type TEXT, description TEXT, dimensions TEXT, total_weight REAL DEFAULT 0, status TEXT DEFAULT 'active', version TEXT DEFAULT '1.0', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS evaluation_indicators ( indicator_id TEXT PRIMARY KEY, system_id TEXT, parent_id TEXT, indicator_name TEXT NOT NULL, indicator_level TEXT, description TEXT, weight REAL DEFAULT 0, measurement TEXT, data_source TEXT, is_leaf INTEGER DEFAULT 1, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS self_evaluations ( self_eval_id TEXT PRIMARY KEY, system_id TEXT, evaluator_id TEXT, evaluator_name TEXT, target_scope TEXT, indicator_scores TEXT, total_score REAL, grade TEXT, evidence TEXT, self_summary TEXT, status TEXT DEFAULT 'submitted', submitted_at TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS expert_evaluations ( expert_eval_id TEXT PRIMARY KEY, system_id TEXT, self_eval_id TEXT, expert_id TEXT, expert_name TEXT, indicator_scores TEXT, total_score REAL, grade TEXT, comments TEXT, recommendations TEXT, eval_date TEXT, status TEXT DEFAULT 'completed', created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS quality_monitors ( monitor_id TEXT PRIMARY KEY, monitor_name TEXT, indicator_id TEXT, indicator_name TEXT, target_scope TEXT, data_value REAL, target_value REAL, achievement_rate REAL, data_period TEXT, data_source TEXT, collected_by TEXT, collected_at TEXT, status TEXT DEFAULT 'collected', created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS quality_issues ( issue_id TEXT PRIMARY KEY, source_type TEXT, source_id TEXT, description TEXT, severity TEXT, affected_scope TEXT, identified_by TEXT, identified_at TEXT, assigned_to TEXT, assigned_at TEXT, status TEXT DEFAULT 'open', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS rectification_notices ( notice_id TEXT PRIMARY KEY, issue_id TEXT, title TEXT, content TEXT, deadline TEXT, responsible_person TEXT, responsible_department TEXT, requirements TEXT, status TEXT DEFAULT 'issued', issued_by TEXT, issued_at TEXT, completed_at TEXT, verified_by TEXT, verified_at TEXT, verification_result TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS quality_reports ( report_id TEXT PRIMARY KEY, report_type TEXT, title TEXT NOT NULL, period TEXT, target_scope TEXT, content TEXT, data_summary TEXT, conclusions TEXT, recommendations TEXT, status TEXT DEFAULT 'draft', author_id TEXT, author_name TEXT, reviewed_by TEXT, reviewed_at TEXT, published_at TEXT, created_at TEXT, updated_at TEXT ) ''')
                conn.commit()
                logger.info('教育质量督导评估服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 内部辅助方法 ==========

    def _calculate_grade(self, score: float) -> str:
        """根据分数判定评估等级"""
        if score >= 90:
            return 'excellent'
        elif score >= 80:
            return 'good'
        elif score >= 60:
            return 'qualified'
        else:
            return 'unqualified'

    def _calculate_observation_score(self, dimensions: Dict[str, Any]) -> float:
        """根据各维度评分加权计算听课总分"""
        if not dimensions:
            return 0.0
        total_weight = 0.0
        weighted_sum = 0.0
        for dim_key, score in dimensions.items():
            weight = EVALUATION_DIMENSIONS.get(dim_key, {}).get('default_weight', 0)
            if weight > 0:
                weighted_sum += float(score) * weight
                total_weight += weight
        if total_weight == 0:
            values = list(dimensions.values())
            return round(sum(float(v) for v in values) / len(values), 2)
        return round(weighted_sum / total_weight, 2)

    def _calculate_eval_score(self, conn, system_id: str, indicator_scores: Dict[str, Any]) -> float:
        """根据指标权重加权计算评估总分"""
        if not indicator_scores:
            return 0.0
        cursor = conn.cursor()
        total_weight = 0.0
        weighted_sum = 0.0
        for ind_id, score in indicator_scores.items():
            cursor.execute('SELECT weight, is_leaf FROM evaluation_indicators WHERE indicator_id = ?', (ind_id,))
            row = cursor.fetchone()
            if row and row[1]:
                weighted_sum += float(score) * float(row[0])
                total_weight += float(row[0])
        if total_weight == 0:
            values = list(indicator_scores.values())
            return round(sum(float(v) for v in values) / len(values), 2)
        return round(weighted_sum / total_weight, 2)

    def _parse_json(self, text: str, default=None):
        """安全解析JSON字段"""
        if not text:
            return default if default is not None else {}
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return default if default is not None else {}

    # ========== 督导员管理 ==========

    def register_supervisor(self, name: str, **kwargs) -> Dict[str, Any]:
        try:
            supervisor_id = f"sup_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            specialties = kwargs.get('specialties', [])
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO supervisors ( supervisor_id, user_id, name, title, department, specialties, level, max_assignments, current_assignments, training_hours, evaluation_score, is_active, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, 1, ?, ?) ''', (supervisor_id, kwargs.get('user_id'), name,
                          kwargs.get('title'), kwargs.get('department'),
                          json.dumps(specialties, ensure_ascii=False),
                          kwargs.get('level'), kwargs.get('max_assignments', 5),
                          kwargs.get('training_hours', 0),
                          kwargs.get('evaluation_score', 0), now, now))
                    conn.commit()
                    logger.info(f'注册督导员: {name} ({supervisor_id})')
                    return {'success': True, 'supervisor_id': supervisor_id}
        except Exception as e:
            logger.error(f'注册督导员失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_supervisor(self, supervisor_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM supervisors WHERE supervisor_id = ?', (supervisor_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '督导员不存在'}
                data = dict(row)
                data['specialties'] = self._parse_json(data.get('specialties'), [])
                return {'success': True, 'supervisor': data}
        except Exception as e:
            logger.error(f'获取督导员失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_supervisors(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM supervisors WHERE 1=1'
                params = []
                if filters.get('department'):
                    query += ' AND department = ?'
                    params.append(filters['department'])
                if filters.get('level'):
                    query += ' AND level = ?'
                    params.append(filters['level'])
                if 'is_active' in filters:
                    query += ' AND is_active = ?'
                    params.append(1 if filters['is_active'] else 0)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(r) for r in cursor.fetchall()]
                for it in items:
                    it['specialties'] = self._parse_json(it.get('specialties'), [])
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取督导员列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_supervisor(self, supervisor_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM supervisors WHERE supervisor_id = ?', (supervisor_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '督导员不存在'}
                    allowed = ['user_id', 'name', 'title', 'department', 'level',
                               'max_assignments', 'current_assignments', 'training_hours',
                               'evaluation_score', 'is_active']
                    sets = []
                    params = []
                    for k, v in kwargs.items():
                        if k in allowed:
                            sets.append(f'{k} = ?')
                            params.append(v)
                        elif k == 'specialties':
                            sets.append('specialties = ?')
                            params.append(json.dumps(v, ensure_ascii=False))
                    if not sets:
                        return {'success': False, 'error': '无可更新字段'}
                    sets.append('updated_at = ?')
                    params.append(now)
                    params.append(supervisor_id)
                    cursor.execute(f'UPDATE supervisors SET {", ".join(sets)} WHERE supervisor_id = ?', params)
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'更新督导员失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 督导计划与听课 ==========

    def create_supervision_plan(self, plan_name: str, supervision_type: str, **kwargs) -> Dict[str, Any]:
        try:
            plan_id = f"spl_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            objectives = kwargs.get('objectives', [])
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO supervision_plans ( plan_id, plan_name, supervision_type, target_scope, target_department, supervisor_id, supervisor_name, start_date, end_date, objectives, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (plan_id, plan_name, supervision_type,
                          kwargs.get('target_scope'), kwargs.get('target_department'),
                          kwargs.get('supervisor_id'), kwargs.get('supervisor_name'),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          json.dumps(objectives, ensure_ascii=False),
                          kwargs.get('status', 'planned'), now, now))
                    if kwargs.get('supervisor_id'):
                        cursor.execute(
                        'UPDATE supervisors SET current_assignments = current_assignments + 1 WHERE supervisor_id = ?',
                                     (kwargs['supervisor_id'],))
                    conn.commit()
                    logger.info(f'创建督导计划: {plan_name} ({plan_id})')
                    return {'success': True, 'plan_id': plan_id}
        except Exception as e:
            logger.error(f'创建督导计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_supervision_plan(self, plan_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM supervision_plans WHERE plan_id = ?', (plan_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '督导计划不存在'}
                data = dict(row)
                data['objectives'] = self._parse_json(data.get('objectives'), [])
                cursor.execute('SELECT COUNT(*) as cnt FROM classroom_observations WHERE plan_id = ?', (plan_id,))
                data['observation_count'] = cursor.fetchone()['cnt']
                return {'success': True, 'plan': data}
        except Exception as e:
            logger.error(f'获取督导计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_supervision_plans(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM supervision_plans WHERE 1=1'
                params = []
                if filters.get('supervision_type'):
                    query += ' AND supervision_type = ?'
                    params.append(filters['supervision_type'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                if filters.get('supervisor_id'):
                    query += ' AND supervisor_id = ?'
                    params.append(filters['supervisor_id'])
                if filters.get('target_department'):
                    query += ' AND target_department = ?'
                    params.append(filters['target_department'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(r) for r in cursor.fetchall()]
                for it in items:
                    it['objectives'] = self._parse_json(it.get('objectives'), [])
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取督导计划列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_classroom_observation(self, plan_id: str, supervisor_id: str,
                                      teacher_id: str, **kwargs) -> Dict[str, Any]:
        try:
            observation_id = f"obs_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            dimensions = kwargs.get('dimensions', {})
            total_score = self._calculate_observation_score(dimensions)
            grade = self._calculate_grade(total_score)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT supervisor_name FROM supervision_plans WHERE plan_id = ?', (plan_id,))
                    plan_row = cursor.fetchone()
                    supervisor_name = kwargs.get('supervisor_name')
                    if not supervisor_name and plan_row:
                        supervisor_name = plan_row[0]
                    cursor.execute(''' INSERT INTO classroom_observations ( observation_id, plan_id, supervisor_id, supervisor_name, teacher_id, teacher_name, course_name, class_name, observation_date, observation_type, lesson_content, dimensions, total_score, grade, strengths, weaknesses, suggestions, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (observation_id, plan_id, supervisor_id, supervisor_name,
                          teacher_id, kwargs.get('teacher_name'),
                          kwargs.get('course_name'), kwargs.get('class_name'),
                          kwargs.get('observation_date', now[:10]),
                          kwargs.get('observation_type', 'routine'),
                          kwargs.get('lesson_content'),
                          json.dumps(dimensions, ensure_ascii=False),
                          total_score, grade, kwargs.get('strengths'),
                          kwargs.get('weaknesses'), kwargs.get('suggestions'),
                          kwargs.get('status', 'completed'), now, now))
                    conn.commit()
                    logger.info(f'创建听课记录: {observation_id}, 总分={total_score}, 等级={grade}')
                    return {'success': True, 'observation_id': observation_id,
                            'total_score': total_score, 'grade': grade}
        except Exception as e:
            logger.error(f'创建听课记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_observation(self, observation_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM classroom_observations WHERE observation_id = ?', (observation_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '听课记录不存在'}
                data = dict(row)
                data['dimensions'] = self._parse_json(data.get('dimensions'), {})
                return {'success': True, 'observation': data}
        except Exception as e:
            logger.error(f'获取听课记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_observations(self, plan_id: str = None, page: int = 1,
                           page_size: int = 20, **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM classroom_observations WHERE 1=1'
                params = []
                if plan_id:
                    query += ' AND plan_id = ?'
                    params.append(plan_id)
                if filters.get('supervisor_id'):
                    query += ' AND supervisor_id = ?'
                    params.append(filters['supervisor_id'])
                if filters.get('teacher_id'):
                    query += ' AND teacher_id = ?'
                    params.append(filters['teacher_id'])
                if filters.get('grade'):
                    query += ' AND grade = ?'
                    params.append(filters['grade'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(r) for r in cursor.fetchall()]
                for it in items:
                    it['dimensions'] = self._parse_json(it.get('dimensions'), {})
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取听课列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def generate_supervision_report(self, plan_id: str, **kwargs) -> Dict[str, Any]:
        try:
            report_id = f"sre_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM supervision_plans WHERE plan_id = ?', (plan_id,))
                    plan = cursor.fetchone()
                    if not plan:
                        return {'success': False, 'error': '督导计划不存在'}
                    plan = dict(plan)
                    cursor.execute('SELECT * FROM classroom_observations WHERE plan_id = ?', (plan_id,))
                    observations = [dict(o) for o in cursor.fetchall()]
                    findings = []
                    grade_dist = {'excellent': 0, 'good': 0, 'qualified': 0, 'unqualified': 0}
                    for obs in observations:
                        grade_dist[obs.get('grade')] = grade_dist.get(obs.get('grade'), 0) + 1
                        if obs.get('total_score') is not None and obs['total_score'] < 60:
                            findings.append({'observation_id': obs['observation_id'],
                                             'teacher': obs.get('teacher_name'),
                                             'score': obs.get('total_score'),
                                             'issue': '评分不合格'})
                    avg_score = 0
                    if observations:
                        scores = [o['total_score'] for o in observations if o.get('total_score') is not None]
                        avg_score = round(sum(scores) / len(scores), 2) if scores else 0
                    title = kwargs.get('title', f"{plan['plan_name']}督导报告")
                    content = kwargs.get('content') or f"本次督导共听课{len(observations)}节，平均分{avg_score}。"
                    cursor.execute(''' INSERT INTO supervision_reports ( report_id, plan_id, supervisor_id, supervisor_name, report_type, title, content, findings, recommendations, issues_found, status, reviewed_by, reviewed_at, created_at, updated_at ) VALUES (?, ?, ?, ?, 'supervision', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (report_id, plan_id, plan.get('supervisor_id'),
                          plan.get('supervisor_name'), title, content,
                          json.dumps(findings, ensure_ascii=False),
                          kwargs.get('recommendations', ''),
                          kwargs.get('issues_found', ''),
                          kwargs.get('status', 'draft'),
                          kwargs.get('reviewed_by'), kwargs.get('reviewed_at'),
                          now, now))
                    cursor.execute("UPDATE supervision_plans SET status = 'completed', updated_at = ? WHERE plan_id = ?",
                                 (now, plan_id))
                    conn.commit()
                    logger.info(f'生成督导报告: {report_id}')
                    return {'success': True, 'report_id': report_id,
                            'observation_count': len(observations),
                            'average_score': avg_score,
                            'grade_distribution': grade_dist}
        except Exception as e:
            logger.error(f'生成督导报告失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 评估指标体系 ==========

    def create_evaluation_system(self, system_name: str, evaluation_type: str, **kwargs) -> Dict[str, Any]:
        try:
            system_id = f"esys_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            dimensions = kwargs.get('dimensions')
            if dimensions is None:
                dimensions = {k: {'name': v['name'], 'weight': v['default_weight']}
                              for k, v in EVALUATION_DIMENSIONS.items()}
            total_weight = round(sum(d.get('weight', 0) for d in dimensions.values()), 4)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO evaluation_systems ( system_id, system_name, evaluation_type, description, dimensions, total_weight, status, version, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (system_id, system_name, evaluation_type,
                          kwargs.get('description', ''),
                          json.dumps(dimensions, ensure_ascii=False),
                          total_weight, kwargs.get('status', 'active'),
                          kwargs.get('version', '1.0'), now, now))
                    conn.commit()
                    logger.info(f'创建评估指标体系: {system_name} ({system_id})')
                    return {'success': True, 'system_id': system_id, 'total_weight': total_weight}
        except Exception as e:
            logger.error(f'创建评估指标体系失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_indicator(self, system_id: str, indicator_name: str,
                       indicator_level: str, **kwargs) -> Dict[str, Any]:
        try:
            indicator_id = f"ind_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT system_id FROM evaluation_systems WHERE system_id = ?', (system_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '评估体系不存在'}
                    cursor.execute(''' INSERT INTO evaluation_indicators ( indicator_id, system_id, parent_id, indicator_name, indicator_level, description, weight, measurement, data_source, is_leaf, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (indicator_id, system_id, kwargs.get('parent_id'),
                          indicator_name, indicator_level,
                          kwargs.get('description', ''),
                          kwargs.get('weight', 0),
                          kwargs.get('measurement', ''),
                          kwargs.get('data_source', ''),
                          kwargs.get('is_leaf', 1), now, now))
                    conn.commit()
                    logger.info(f'添加评估指标: {indicator_name} ({indicator_id})')
                    return {'success': True, 'indicator_id': indicator_id}
        except Exception as e:
            logger.error(f'添加评估指标失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_evaluation_system(self, system_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM evaluation_systems WHERE system_id = ?', (system_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '评估体系不存在'}
                data = dict(row)
                data['dimensions'] = self._parse_json(data.get('dimensions'), {})
                cursor.execute('SELECT * FROM evaluation_indicators WHERE system_id = ? ORDER BY indicator_level, created_at',
                             (system_id,))
                indicators = [dict(r) for r in cursor.fetchall()]
                indicator_map = {ind['indicator_id']: ind for ind in indicators}
                tree = []
                for ind in indicators:
                    ind['children'] = []
                    if ind.get('parent_id') and ind['parent_id'] in indicator_map:
                        indicator_map[ind['parent_id']]['children'].append(ind)
                    elif not ind.get('parent_id'):
                        tree.append(ind)
                data['indicators'] = tree
                return {'success': True, 'system': data}
        except Exception as e:
            logger.error(f'获取评估体系失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_evaluation_systems(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM evaluation_systems WHERE 1=1'
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', [])
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                cursor.execute(query, [page_size, (page - 1) * page_size])
                items = [dict(r) for r in cursor.fetchall()]
                for it in items:
                    it['dimensions'] = self._parse_json(it.get('dimensions'), {})
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取评估体系列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 自评与专家评估 ==========

    def submit_self_evaluation(self, system_id: str, evaluator_id: str, **kwargs) -> Dict[str, Any]:
        try:
            self_eval_id = f"sev_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            indicator_scores = kwargs.get('indicator_scores', {})
            evidence = kwargs.get('evidence', [])
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    total_score = self._calculate_eval_score(conn, system_id, indicator_scores)
                    grade = self._calculate_grade(total_score)
                    cursor.execute(''' INSERT INTO self_evaluations ( self_eval_id, system_id, evaluator_id, evaluator_name, target_scope, indicator_scores, total_score, grade, evidence, self_summary, status, submitted_at, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (self_eval_id, system_id, evaluator_id,
                          kwargs.get('evaluator_name'), kwargs.get('target_scope'),
                          json.dumps(indicator_scores, ensure_ascii=False),
                          total_score, grade,
                          json.dumps(evidence, ensure_ascii=False),
                          kwargs.get('self_summary', ''),
                          kwargs.get('status', 'submitted'), now, now, now))
                    conn.commit()
                    logger.info(f'提交自评: {self_eval_id}, 总分={total_score}, 等级={grade}')
                    return {'success': True, 'self_eval_id': self_eval_id,
                            'total_score': total_score, 'grade': grade}
        except Exception as e:
            logger.error(f'提交自评失败: {e}')
            return {'success': False, 'error': str(e)}

    def submit_expert_evaluation(self, system_id: str, self_eval_id: str,
                                  expert_id: str, **kwargs) -> Dict[str, Any]:
        try:
            expert_eval_id = f"eev_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            indicator_scores = kwargs.get('indicator_scores', {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    total_score = self._calculate_eval_score(conn, system_id, indicator_scores)
                    grade = self._calculate_grade(total_score)
                    cursor.execute(''' INSERT INTO expert_evaluations ( expert_eval_id, system_id, self_eval_id, expert_id, expert_name, indicator_scores, total_score, grade, comments, recommendations, eval_date, status, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (expert_eval_id, system_id, self_eval_id, expert_id,
                          kwargs.get('expert_name'),
                          json.dumps(indicator_scores, ensure_ascii=False),
                          total_score, grade, kwargs.get('comments', ''),
                          kwargs.get('recommendations', ''),
                          kwargs.get('eval_date', now[:10]),
                          kwargs.get('status', 'completed'), now))
                    conn.commit()
                    logger.info(f'提交专家评估: {expert_eval_id}, 总分={total_score}, 等级={grade}')
                    return {'success': True, 'expert_eval_id': expert_eval_id,
                            'total_score': total_score, 'grade': grade}
        except Exception as e:
            logger.error(f'提交专家评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_evaluation_result(self, eval_id: str, eval_type: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                if eval_type == 'self':
                    cursor.execute('SELECT * FROM self_evaluations WHERE self_eval_id = ?', (eval_id,))
                elif eval_type == 'expert':
                    cursor.execute('SELECT * FROM expert_evaluations WHERE expert_eval_id = ?', (eval_id,))
                else:
                    return {'success': False, 'error': '无效的评估类型'}
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '评估记录不存在'}
                data = dict(row)
                data['indicator_scores'] = self._parse_json(data.get('indicator_scores'), {})
                if 'evidence' in data:
                    data['evidence'] = self._parse_json(data.get('evidence'), [])
                return {'success': True, 'result': data}
        except Exception as e:
            logger.error(f'获取评估结果失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 质量监测 ==========

    def record_monitor_data(self, indicator_id: str, data_value: float, **kwargs) -> Dict[str, Any]:
        try:
            monitor_id = f"qmd_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            target_value = kwargs.get('target_value', 0)
            achievement_rate = round(data_value / target_value * 100, 2) if target_value else 0
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT indicator_name FROM evaluation_indicators WHERE indicator_id = ?',
                    (indicator_id,))
                    ind_row = cursor.fetchone()
                    indicator_name = kwargs.get('indicator_name')
                    if not indicator_name and ind_row:
                        indicator_name = ind_row[0]
                    cursor.execute(''' INSERT INTO quality_monitors ( monitor_id, monitor_name, indicator_id, indicator_name, target_scope, data_value, target_value, achievement_rate, data_period, data_source, collected_by, collected_at, status, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (monitor_id, kwargs.get('monitor_name', ''),
                          indicator_id, indicator_name,
                          kwargs.get('target_scope', ''),
                          data_value, target_value, achievement_rate,
                          kwargs.get('data_period', now[:7]),
                          kwargs.get('data_source', ''),
                          kwargs.get('collected_by'), now,
                          kwargs.get('status', 'collected'), now))
                    conn.commit()
                    logger.info(f'记录监测数据: {monitor_id}, 达成率={achievement_rate}%')
                    return {'success': True, 'monitor_id': monitor_id,
                            'achievement_rate': achievement_rate}
        except Exception as e:
            logger.error(f'记录监测数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_monitor_data(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM quality_monitors WHERE 1=1'
                params = []
                if filters.get('indicator_id'):
                    query += ' AND indicator_id = ?'
                    params.append(filters['indicator_id'])
                if filters.get('target_scope'):
                    query += ' AND target_scope = ?'
                    params.append(filters['target_scope'])
                if filters.get('data_period'):
                    query += ' AND data_period = ?'
                    params.append(filters['data_period'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取监测数据列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_monitor_statistics(self, target_scope: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM quality_monitors WHERE 1=1'
                params = []
                if target_scope:
                    query += ' AND target_scope = ?'
                    params.append(target_scope)
                cursor.execute(query, params)
                rows = [dict(r) for r in cursor.fetchall()]
                total = len(rows)
                achieved = sum(1 for r in rows if r.get(
                'achievement_rate') is not None and r['achievement_rate'] >= 100)
                avg_rate = round(sum(r['achievement_rate'] for r in rows if r.get(
                'achievement_rate') is not None) / total, 2) if total else 0
                by_period = {}
                for r in rows:
                    period = r.get('data_period', 'unknown')
                    by_period.setdefault(period, []).append(r.get('achievement_rate', 0))
                period_stats = {p: round(sum(v) / len(v), 2) for p, v in by_period.items()}
                return {'success': True, 'total_records': total,
                        'achieved_count': achieved,
                        'achievement_rate': avg_rate,
                        'period_statistics': period_stats}
        except Exception as e:
            logger.error(f'获取监测统计失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 问题与整改 ==========

    def report_issue(self, source_type: str, source_id: str,
                      description: str, **kwargs) -> Dict[str, Any]:
        try:
            issue_id = f"qis_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO quality_issues ( issue_id, source_type, source_id, description, severity, affected_scope, identified_by, identified_at, assigned_to, assigned_at, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (issue_id, source_type, source_id, description,
                          kwargs.get('severity', 'moderate'),
                          kwargs.get('affected_scope', ''),
                          kwargs.get('identified_by', ''),
                          kwargs.get('identified_at', now),
                          kwargs.get('assigned_to', ''),
                          kwargs.get('assigned_at'), kwargs.get('status', 'open'),
                          now, now))
                    conn.commit()
                    logger.info(f'报告质量问题: {issue_id}, 严重程度={kwargs.get("severity", "moderate")}')
                    return {'success': True, 'issue_id': issue_id}
        except Exception as e:
            logger.error(f'报告质量问题失败: {e}')
            return {'success': False, 'error': str(e)}

    def issue_rectification_notice(self, issue_id: str, deadline: str,
                                    responsible_person: str, **kwargs) -> Dict[str, Any]:
        try:
            notice_id = f"rct_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT issue_id, description FROM quality_issues WHERE issue_id = ?', (issue_id,))
                    issue = cursor.fetchone()
                    if not issue:
                        return {'success': False, 'error': '质量问题不存在'}
                    title = kwargs.get('title', f'整改通知-{issue_id}')
                    content = kwargs.get('content') or issue[1]
                    cursor.execute(''' INSERT INTO rectification_notices ( notice_id, issue_id, title, content, deadline, responsible_person, responsible_department, requirements, status, issued_by, issued_at, completed_at, verified_by, verified_at, verification_result, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'issued', ?, ?, ?, ?, ?, ?, ?, ?) ''', (notice_id, issue_id, title, content, deadline,
                          responsible_person, kwargs.get('responsible_department', ''),
                          kwargs.get('requirements', ''),
                          kwargs.get('issued_by', ''), now,
                          None, None, None, None, now, now))
                    cursor.execute("UPDATE quality_issues SET status = 'assigned', assigned_to = ?, assigned_at = ?, updated_at = ? WHERE issue_id = ?",
                                 (responsible_person, now, now, issue_id))
                    conn.commit()
                    logger.info(f'下发整改通知: {notice_id}, 截止={deadline}')
                    return {'success': True, 'notice_id': notice_id}
        except Exception as e:
            logger.error(f'下发整改通知失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_rectification(self, notice_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT status, deadline FROM rectification_notices WHERE notice_id = ?", (notice_id,
                    ))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '整改通知不存在'}
                    new_status = 'completed'
                    cursor.execute(''' UPDATE rectification_notices SET status = ?, completed_at = ?, verification_result = ?, updated_at = ? WHERE notice_id = ? ''', (new_status, now, kwargs.get('verification_result', ''), now, notice_id))
                    cursor.execute("UPDATE quality_issues SET status = 'rectified', updated_at = ? WHERE issue_id = (SELECT issue_id FROM rectification_notices WHERE notice_id = ?)",
                                 (now, notice_id))
                    conn.commit()
                    logger.info(f'完成整改: {notice_id}')
                    return {'success': True, 'status': new_status}
        except Exception as e:
            logger.error(f'完成整改失败: {e}')
            return {'success': False, 'error': str(e)}

    def verify_rectification(self, notice_id: str, verified_by: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT status FROM rectification_notices WHERE notice_id = ?", (notice_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '整改通知不存在'}
                    if row[0] != 'completed':
                        return {'success': False, 'error': '整改未完成，无法验证'}
                    passed = kwargs.get('passed', True)
                    new_status = 'verified' if passed else 'in_progress'
                    cursor.execute(''' UPDATE rectification_notices SET status = ?, verified_by = ?, verified_at = ?, verification_result = ?, updated_at = ? WHERE notice_id = ? ''', (new_status, verified_by, now,
                          kwargs.get('verification_result', ''), now, notice_id))
                    if passed:
                        cursor.execute("UPDATE quality_issues SET status = 'resolved', updated_at = ? WHERE issue_id = ( SELECT issue_id FROM rectification_notices WHERE notice_id = ?)",
                                     (now, notice_id))
                    conn.commit()
                    logger.info(f'验证整改: {notice_id}, 通过={passed}')
                    return {'success': True, 'status': new_status}
        except Exception as e:
            logger.error(f'验证整改失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_issues(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM quality_issues WHERE 1=1'
                params = []
                if filters.get('severity'):
                    query += ' AND severity = ?'
                    params.append(filters['severity'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                if filters.get('source_type'):
                    query += ' AND source_type = ?'
                    params.append(filters['source_type'])
                if filters.get('assigned_to'):
                    query += ' AND assigned_to = ?'
                    params.append(filters['assigned_to'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取问题列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_rectification_notices(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE rectification_notices SET status = 'overdue' WHERE deadline < ? AND status NOT IN ('completed', 'verified') ''', (now,))
                    conn.commit()
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM rectification_notices WHERE 1=1'
                params = []
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                if filters.get('issue_id'):
                    query += ' AND issue_id = ?'
                    params.append(filters['issue_id'])
                if filters.get('responsible_person'):
                    query += ' AND responsible_person = ?'
                    params.append(filters['responsible_person'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取整改通知列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 质量报告 ==========

    def create_quality_report(self, report_type: str, title: str, **kwargs) -> Dict[str, Any]:
        try:
            report_id = f"qre_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            data_summary = kwargs.get('data_summary', {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO quality_reports ( report_id, report_type, title, period, target_scope, content, data_summary, conclusions, recommendations, status, author_id, author_name, reviewed_by, reviewed_at, published_at, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (report_id, report_type, title,
                          kwargs.get('period', ''),
                          kwargs.get('target_scope', ''),
                          kwargs.get('content', ''),
                          json.dumps(data_summary, ensure_ascii=False),
                          kwargs.get('conclusions', ''),
                          kwargs.get('recommendations', ''),
                          kwargs.get('status', 'draft'),
                          kwargs.get('author_id', ''),
                          kwargs.get('author_name', ''),
                          kwargs.get('reviewed_by'), kwargs.get('reviewed_at'),
                          kwargs.get('published_at'), now, now))
                    conn.commit()
                    logger.info(f'创建质量报告: {title} ({report_id})')
                    return {'success': True, 'report_id': report_id}
        except Exception as e:
            logger.error(f'创建质量报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def review_quality_report(self, report_id: str, reviewed_by: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM quality_reports WHERE report_id = ?', (report_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '质量报告不存在'}
                    if row[0] != 'draft':
                        return {'success': False, 'error': '报告状态不允许审核'}
                    approved = kwargs.get('approved', True)
                    new_status = 'reviewed' if approved else 'rejected'
                    cursor.execute(''' UPDATE quality_reports SET status = ?, reviewed_by = ?, reviewed_at = ?, updated_at = ? WHERE report_id = ? ''', (new_status, reviewed_by, now, now, report_id))
                    conn.commit()
                    logger.info(f'审核质量报告: {report_id}, 结果={new_status}')
                    return {'success': True, 'status': new_status}
        except Exception as e:
            logger.error(f'审核质量报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def publish_quality_report(self, report_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status, report_type FROM quality_reports WHERE report_id = ?', (report_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '质量报告不存在'}
                    status, report_type = row[0], row[1]
                    config = REPORT_TYPES.get(report_type, {})
                    if config.get('required_review') and status != 'reviewed':
                        return {'success': False, 'error': '需审核的报告未通过审核'}
                    if status == 'published':
                        return {'success': False, 'error': '报告已发布'}
                    cursor.execute(''' UPDATE quality_reports SET status = 'published', published_at = ?, updated_at = ? WHERE report_id = ? ''', (now, now, report_id))
                    conn.commit()
                    logger.info(f'发布质量报告: {report_id}')
                    return {'success': True, 'published_at': now}
        except Exception as e:
            logger.error(f'发布质量报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_quality_reports(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM quality_reports WHERE 1=1'
                params = []
                if filters.get('report_type'):
                    query += ' AND report_type = ?'
                    params.append(filters['report_type'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                if filters.get('period'):
                    query += ' AND period = ?'
                    params.append(filters['period'])
                if filters.get('author_id'):
                    query += ' AND author_id = ?'
                    params.append(filters['author_id'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(r) for r in cursor.fetchall()]
                for it in items:
                    it['data_summary'] = self._parse_json(it.get('data_summary'), {})
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取质量报告列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    stats = {}
                    # 督导计划状态分布
                    cursor.execute('SELECT status, COUNT(*) as cnt FROM supervision_plans GROUP BY status')
                    stats['plan_status_distribution'] = {r['status']: r['cnt'] for r in cursor.fetchall()}
                    # 听课评分分布
                    cursor.execute('SELECT grade, COUNT(*) as cnt FROM classroom_observations GROUP BY grade')
                    stats['observation_grade_distribution'] = {r['grade']: r['cnt'] for r in cursor.fetchall()}
                    cursor.execute('SELECT AVG(total_score) as avg_score, MAX(total_score) as max_score, MIN(total_score) as min_score, COUNT(*) as cnt FROM classroom_observations')
                    obs_stats = cursor.fetchone()
                    stats['observation_score_summary'] = {
                        'average': round(obs_stats['avg_score'], 2) if obs_stats['avg_score'] else 0,
                        'max': obs_stats['max_score'] or 0,
                        'min': obs_stats['min_score'] or 0,
                        'count': obs_stats['cnt'] or 0
                    }
                    # 评估等级分布（自评+专家评估）
                    cursor.execute('SELECT grade, COUNT(*) as cnt FROM self_evaluations GROUP BY grade')
                    self_grades = {r['grade']: r['cnt'] for r in cursor.fetchall()}
                    cursor.execute('SELECT grade, COUNT(*) as cnt FROM expert_evaluations GROUP BY grade')
                    expert_grades = {r['grade']: r['cnt'] for r in cursor.fetchall()}
                    eval_dist = {}
                    for g in set(list(self_grades.keys()) + list(expert_grades.keys())):
                        eval_dist[g] = self_grades.get(g, 0) + expert_grades.get(g, 0)
                    stats['evaluation_grade_distribution'] = eval_dist
                    # 问题严重程度分布
                    cursor.execute('SELECT severity, COUNT(*) as cnt FROM quality_issues GROUP BY severity')
                    stats['issue_severity_distribution'] = {r['severity']: r['cnt'] for r in cursor.fetchall()}
                    # 整改完成率
                    cursor.execute('SELECT COUNT(*) as total FROM rectification_notices')
                    total_notices = cursor.fetchone()['total']
                    cursor.execute("SELECT COUNT(*) as done FROM rectification_notices WHERE status IN ('completed', 'verified')")
                    done_notices = cursor.fetchone()['done']
                    stats['rectification_completion_rate'] = round(done_notices / total_notices * 100,
                    2) if total_notices else 0
                    stats['rectification_total'] = total_notices
                    stats['rectification_completed'] = done_notices
                    # 报告数量
                    cursor.execute('SELECT status, COUNT(*) as cnt FROM quality_reports GROUP BY status')
                    stats['report_status_distribution'] = {r['status']: r['cnt'] for r in cursor.fetchall()}
                    cursor.execute('SELECT COUNT(*) as cnt FROM quality_reports')
                    stats['report_count'] = cursor.fetchone()['cnt']
                    # 督导员统计
                    cursor.execute('SELECT COUNT(*) as cnt FROM supervisors WHERE is_active = 1')
                    stats['active_supervisor_count'] = cursor.fetchone()['cnt']
                    # 监测数据统计
                    cursor.execute('SELECT COUNT(*) as cnt FROM quality_monitors')
                    stats['monitor_record_count'] = cursor.fetchone()['cnt']
                    stats['education_type'] = education_type
                    return {'success': True, **stats}
        except Exception as e:
            logger.error(f'获取统计失败: {e}')
            return {'success': False, 'error': str(e)}


if __name__ == '__main__':
    service = EducationQualityService()
    print('教育质量督导评估服务初始化完成')
    stats = service.get_statistics()
    print(f'统计: {stats}')
