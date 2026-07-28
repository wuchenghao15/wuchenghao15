#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS 学生综合素质评价服务 (v15.11.0) ========================================== 提供面向成人教育和 K12 教育的学生综合素质评价全流程管理服务， 围绕“德智体美劳”五育并举构建多维度、可追溯、可申诉的综合评价体系。  核心能力： 1. 评价体系 - 五育并举评价维度、指标管理、权重配置 2. 德育评价 - 思想品德、社会责任、文明素养 3. 智育评价 - 学业表现、学习能力、创新思维 4. 体育评价 - 体质健康、运动技能、健康习惯 5. 美育评价 - 艺术素养、审美能力、文化理解 6. 劳动评价 - 劳动观念、劳动技能、劳动习惯 7. 成长档案 - 综合素质档案、成长轨迹、学期报告 8. 成人素质评价与 K12 综合素质评价差异化 """
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'comprehensive_evaluation_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ComprehensiveEval')


# ========== 综合素质评价配置 ==========

# 五育维度
FIVE_DIMENSIONS = {
    'moral': {'name': '德育', 'color': '#E74C3C', 'default_weight': 25},
    'intellectual': {'name': '智育', 'color': '#3498DB', 'default_weight': 30},
    'physical': {'name': '体育', 'color': '#2ECC71', 'default_weight': 15},
    'aesthetic': {'name': '美育', 'color': '#9B59B6', 'default_weight': 15},
    'labor': {'name': '劳动', 'color': '#F39C12', 'default_weight': 15}
}

# 德育指标
MORAL_INDICATORS = {
    'ideology': {'name': '理想信念', 'max_score': 100},
    'morality': {'name': '道德品质', 'max_score': 100},
    'social_responsibility': {'name': '社会责任', 'max_score': 100},
    'civility': {'name': '文明素养', 'max_score': 100},
    'discipline': {'name': '纪律遵守', 'max_score': 100},
    'volunteer_service': {'name': '志愿服务', 'max_score': 100}
}

# 智育指标
INTELLECTUAL_INDICATORS = {
    'academic_performance': {'name': '学业成绩', 'max_score': 100},
    'learning_ability': {'name': '学习能力', 'max_score': 100},
    'innovation_thinking': {'name': '创新思维', 'max_score': 100},
    'knowledge_application': {'name': '知识应用', 'max_score': 100},
    'academic_competition': {'name': '学科竞赛', 'max_score': 100}
}

# 体育指标
PHYSICAL_INDICATORS = {
    'physical_fitness': {'name': '体质健康', 'max_score': 100},
    'sports_skills': {'name': '运动技能', 'max_score': 100},
    'health_habits': {'name': '健康习惯', 'max_score': 100},
    'sports_competition': {'name': '体育竞赛', 'max_score': 100},
    'mental_health': {'name': '心理健康', 'max_score': 100}
}

# 美育指标
AESTHETIC_INDICATORS = {
    'art_literacy': {'name': '艺术素养', 'max_score': 100},
    'aesthetic_ability': {'name': '审美能力', 'max_score': 100},
    'cultural_understanding': {'name': '文化理解', 'max_score': 100},
    'art_creation': {'name': '艺术创作', 'max_score': 100},
    'art_activities': {'name': '艺术活动', 'max_score': 100}
}

# 劳动指标
LABOR_INDICATORS = {
    'labor_concept': {'name': '劳动观念', 'max_score': 100},
    'labor_skills': {'name': '劳动技能', 'max_score': 100},
    'labor_habits': {'name': '劳动习惯', 'max_score': 100},
    'social_practice': {'name': '社会实践', 'max_score': 100},
    'vocational_experience': {'name': '职业体验', 'max_score': 100}
}

# 评价等级
EVALUATION_LEVELS = {
    'excellent': {'name': '优秀', 'grade': 'A', 'score_range': '>=90'},
    'good': {'name': '良好', 'grade': 'B', 'score_range': '75-89'},
    'qualified': {'name': '合格', 'grade': 'C', 'score_range': '60-74'},
    'to_be_improved': {'name': '待改进', 'grade': 'D', 'score_range': '<60'}
}

# 证据类型
EVIDENCE_TYPES = {
    'certificate': {'name': '证书'},
    'award': {'name': '获奖'},
    'work': {'name': '作品'},
    'activity': {'name': '活动'},
    'testimonial': {'name': '证明'},
    'report': {'name': '报告'},
    'photo': {'name': '照片'},
    'video': {'name': '视频'}
}

# 学期类型
TERM_TYPES = {
    'first_semester': {'name': '第一学期'},
    'second_semester': {'name': '第二学期'},
    'whole_year': {'name': '全学年'}
}


class ComprehensiveEvaluationService:
    """学生综合素质评价服务"""

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
                cursor.execute(''' CREATE TABLE IF NOT EXISTS eval_systems ( system_id TEXT PRIMARY KEY, system_name TEXT NOT NULL, education_type TEXT, description TEXT, dimensions TEXT, total_weight REAL DEFAULT 100, version TEXT DEFAULT '1.0', status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS eval_indicators ( indicator_id TEXT PRIMARY KEY, system_id TEXT NOT NULL, dimension TEXT NOT NULL, indicator_name TEXT NOT NULL, indicator_code TEXT, description TEXT, weight REAL DEFAULT 0, max_score REAL DEFAULT 100, measurement_method TEXT, data_source TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS student_evaluations ( eval_id TEXT PRIMARY KEY, student_id TEXT NOT NULL, student_name TEXT, education_type TEXT, grade_level TEXT, academic_year TEXT, term TEXT, system_id TEXT, dimension_scores TEXT, indicator_evidence TEXT, total_score REAL DEFAULT 0, level TEXT, rank INTEGER, evaluator_id TEXT, evaluator_name TEXT, eval_date TEXT, status TEXT DEFAULT 'draft', comments TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS dimension_scores ( id INTEGER PRIMARY KEY AUTOINCREMENT, eval_id TEXT NOT NULL, student_id TEXT, dimension TEXT NOT NULL, total_score REAL DEFAULT 0, indicators TEXT, evidence_count INTEGER DEFAULT 0, graded_by TEXT, graded_at TEXT, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS evidence_records ( evidence_id TEXT PRIMARY KEY, student_id TEXT NOT NULL, student_name TEXT, dimension TEXT, indicator TEXT, evidence_type TEXT, title TEXT NOT NULL, description TEXT, file_url TEXT, event_name TEXT, event_date TEXT, award_level TEXT, verified_by TEXT, verified_at TEXT, status TEXT DEFAULT 'pending', created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS growth_portfolios ( portfolio_id TEXT PRIMARY KEY, student_id TEXT NOT NULL, student_name TEXT, education_type TEXT, grade_level TEXT, enroll_year TEXT, graduate_year TEXT, total_score_avg REAL DEFAULT 0, best_dimension TEXT, weak_dimension TEXT, level_history TEXT, achievement_count INTEGER DEFAULT 0, award_count INTEGER DEFAULT 0, activity_count INTEGER DEFAULT 0, summary TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS growth_records ( record_id TEXT PRIMARY KEY, portfolio_id TEXT NOT NULL, student_id TEXT, record_type TEXT, title TEXT NOT NULL, description TEXT, record_date TEXT, dimension TEXT, score REAL, level TEXT, file_url TEXT, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS term_reports ( report_id TEXT PRIMARY KEY, student_id TEXT NOT NULL, student_name TEXT, education_type TEXT, grade_level TEXT, academic_year TEXT, term TEXT, eval_id TEXT, dimension_analysis TEXT, strengths TEXT, weaknesses TEXT, improvement_plan TEXT, teacher_comment TEXT, parent_comment TEXT, self_reflection TEXT, overall_level TEXT, generated_at TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS peer_evaluations ( peer_eval_id TEXT PRIMARY KEY, eval_id TEXT NOT NULL, evaluator_id TEXT, evaluator_name TEXT, student_id TEXT, student_name TEXT, dimension TEXT, scores TEXT, comment TEXT, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS self_evaluations ( self_eval_id TEXT PRIMARY KEY, eval_id TEXT NOT NULL, student_id TEXT, student_name TEXT, dimension_scores TEXT, self_summary TEXT, improvement_goals TEXT, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS eval_appeals ( appeal_id TEXT PRIMARY KEY, eval_id TEXT NOT NULL, student_id TEXT, student_name TEXT, dimension TEXT, original_score REAL, appealed_score REAL, reason TEXT, evidence TEXT, status TEXT DEFAULT 'pending', reviewed_by TEXT, review_result TEXT, reviewed_at TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS class_evaluations ( class_eval_id TEXT PRIMARY KEY, class_name TEXT NOT NULL, grade_level TEXT, academic_year TEXT, term TEXT, system_id TEXT, student_count INTEGER DEFAULT 0, avg_score REAL DEFAULT 0, max_score REAL DEFAULT 0, min_score REAL DEFAULT 0, level_distribution TEXT, dimension_avg TEXT, generated_at TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS eval_standards ( standard_id TEXT PRIMARY KEY, system_id TEXT NOT NULL, dimension TEXT, indicator TEXT, level TEXT, min_score REAL, max_score REAL, description TEXT, examples TEXT, created_at TEXT, updated_at TEXT ) ''')
                conn.commit()
                logger.info('学生综合素质评价服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 评价体系管理 ==========

    def create_eval_system(self, system_name: str, education_type: str,
                            **kwargs) -> Dict[str, Any]:
        try:
            system_id = f"es_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            weights = kwargs.get('weights')
            if not weights:
                weights = {dim: cfg['default_weight'] for dim, cfg in FIVE_DIMENSIONS.items()}
            dimensions_data = {dim: {'name': FIVE_DIMENSIONS[dim]['name'],
                                     'weight': weights.get(dim, FIVE_DIMENSIONS[dim]['default_weight'])}
                               for dim in FIVE_DIMENSIONS}
            total_weight = sum(d['weight'] for d in dimensions_data.values())
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO eval_systems ( system_id, system_name, education_type, description, dimensions, total_weight, version, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (system_id, system_name, education_type,
                          kwargs.get('description'),
                          json.dumps(dimensions_data, ensure_ascii=False),
                          total_weight, kwargs.get('version', '1.0'),
                          kwargs.get('status', 'active'), now, now))
                    conn.commit()
                    logger.info(f'创建评价体系: {system_name} ({system_id})')
                    return {'success': True, 'system_id': system_id, 'total_weight': total_weight}
        except Exception as e:
            logger.error(f'创建评价体系失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_indicator(self, system_id: str, dimension: str,
                       indicator_name: str, **kwargs) -> Dict[str, Any]:
        try:
            indicator_id = f"ind_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO eval_indicators ( indicator_id, system_id, dimension, indicator_name, indicator_code, description, weight, max_score, measurement_method, data_source, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (indicator_id, system_id, dimension, indicator_name,
                          kwargs.get('indicator_code'),
                          kwargs.get('description'),
                          kwargs.get('weight', 0),
                          kwargs.get('max_score', 100),
                          kwargs.get('measurement_method'),
                          kwargs.get('data_source'), now, now))
                    conn.commit()
                    logger.info(f'添加指标: {indicator_name} ({indicator_id})')
                    return {'success': True, 'indicator_id': indicator_id}
        except Exception as e:
            logger.error(f'添加指标失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_eval_system(self, system_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM eval_systems WHERE system_id = ?', (system_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '评价体系不存在'}
                system = dict(row)
                if system.get('dimensions'):
                    system['dimensions'] = json.loads(system['dimensions'])
                cursor.execute('SELECT * FROM eval_indicators WHERE system_id = ? ORDER BY dimension', (system_id,))
                system['indicators'] = [dict(r) for r in cursor.fetchall()]
                cursor.execute('SELECT * FROM eval_standards WHERE system_id = ?', (system_id,))
                system['standards'] = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'system': system}
        except Exception as e:
            logger.error(f'获取评价体系详情失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_eval_systems(self, page: int = 1, page_size: int = 20,
                           **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM eval_systems WHERE 1=1'
                params = []
                if filters.get('education_type'):
                    query += ' AND education_type = ?'
                    params.append(filters['education_type'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取评价体系列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def set_eval_standards(self, system_id: str, dimension: str,
                            indicator: str, **kwargs) -> Dict[str, Any]:
        try:
            standard_id = f"std_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO eval_standards ( standard_id, system_id, dimension, indicator, level, min_score, max_score, description, examples, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (standard_id, system_id, dimension, indicator,
                          kwargs.get('level'),
                          kwargs.get('min_score'),
                          kwargs.get('max_score'),
                          kwargs.get('description'),
                          kwargs.get('examples'), now, now))
                    conn.commit()
                    logger.info(f'设置评价标准: {dimension}/{indicator} ({standard_id})')
                    return {'success': True, 'standard_id': standard_id}
        except Exception as e:
            logger.error(f'设置评价标准失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 证据管理 ==========

    def add_evidence(self, student_id: str, dimension: str, indicator: str,
                      evidence_type: str, title: str, **kwargs) -> Dict[str, Any]:
        try:
            evidence_id = f"ev_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO evidence_records ( evidence_id, student_id, student_name, dimension, indicator, evidence_type, title, description, file_url, event_name, event_date, award_level, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?) ''', (evidence_id, student_id, kwargs.get('student_name'),
                          dimension, indicator, evidence_type, title,
                          kwargs.get('description'), kwargs.get('file_url'),
                          kwargs.get('event_name'), kwargs.get('event_date'),
                          kwargs.get('award_level'), now, now))
                    conn.commit()
                    logger.info(f'添加证据: {title} ({evidence_id})')
                    return {'success': True, 'evidence_id': evidence_id}
        except Exception as e:
            logger.error(f'添加证据失败: {e}')
            return {'success': False, 'error': str(e)}

    def verify_evidence(self, evidence_id: str, verified_by: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = kwargs.get('status', 'verified')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE evidence_records SET status = ?, verified_by = ?, verified_at = ?, updated_at = ? WHERE evidence_id = ? AND status = 'pending' ''', (status, verified_by, now, now, evidence_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '证据不存在或状态不允许审核'}
        except Exception as e:
            logger.error(f'审核证据失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_evidence(self, student_id: str = None, page: int = 1,
                       page_size: int = 20, **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM evidence_records WHERE 1=1'
                params = []
                if student_id:
                    query += ' AND student_id = ?'
                    params.append(student_id)
                if filters.get('dimension'):
                    query += ' AND dimension = ?'
                    params.append(filters['dimension'])
                if filters.get('evidence_type'):
                    query += ' AND evidence_type = ?'
                    params.append(filters['evidence_type'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取证据列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 综合素质评价 ==========

    def create_evaluation(self, student_id: str, system_id: str,
                           academic_year: str, term: str, **kwargs) -> Dict[str, Any]:
        try:
            eval_id = f"ce_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT dimensions FROM eval_systems WHERE system_id = ?', (system_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '评价体系不存在'}
                weights = {dim: cfg['weight'] for dim, cfg in json.loads(row['dimensions']).items()}
            dim_scores = kwargs.get('dimension_scores', {})
            total_score, level = self._calc_total_and_level(dim_scores, weights)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO student_evaluations ( eval_id, student_id, student_name, education_type, grade_level, academic_year, term, system_id, dimension_scores, indicator_evidence, total_score, level, evaluator_id, evaluator_name, eval_date, status, comments, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?) ''', (eval_id, student_id, kwargs.get('student_name'),
                          kwargs.get('education_type'), kwargs.get('grade_level'),
                          academic_year, term, system_id,
                          json.dumps(dim_scores, ensure_ascii=False),
                          json.dumps(kwargs.get('indicator_evidence', {}), ensure_ascii=False),
                          total_score, level,
                          kwargs.get('evaluator_id'), kwargs.get('evaluator_name'),
                          kwargs.get('eval_date', now[:10]),
                          kwargs.get('comments'), now, now))
                    conn.commit()
                    logger.info(f'创建评价: student={student_id} ({eval_id})')
                    return {'success': True, 'eval_id': eval_id, 'total_score': total_score, 'level': level}
        except Exception as e:
            logger.error(f'创建评价失败: {e}')
            return {'success': False, 'error': str(e)}

    def _calc_total_and_level(self, dim_scores: Dict[str, Any],
                               weights: Dict[str, float]) -> Tuple[float, str]:
        total = 0.0
        weight_sum = sum(weights.values()) or 1
        for dim, weight in weights.items():
            score = dim_scores.get(dim, 0)
            if isinstance(score, dict):
                score = score.get('total_score', 0)
            total += (score * weight / weight_sum)
        total = round(total, 2)
        if total >= 90:
            level = 'excellent'
        elif total >= 75:
            level = 'good'
        elif total >= 60:
            level = 'qualified'
        else:
            level = 'to_be_improved'
        return total, level

    def record_dimension_score(self, eval_id: str, dimension: str,
                                **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            indicators = kwargs.get('indicators', {})
            total_score = kwargs.get('total_score')
            if total_score is None and indicators:
                total_score = round(sum(indicators.values()) / len(indicators), 2)
            elif total_score is None:
                total_score = 0
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT student_id, system_id, dimension_scores, status FROM student_evaluations WHERE eval_id = ?', (eval_id,))
                    eval_row = cursor.fetchone()
                    if not eval_row:
                        return {'success': False, 'error': '评价不存在'}
                    if eval_row['status'] != 'draft':
                        return {'success': False, 'error': '评价已锁定，无法修改'}
                    cursor.execute('SELECT id FROM dimension_scores WHERE eval_id = ? AND dimension = ?', (eval_id,
                    dimension))
                    existing = cursor.fetchone()
                    if existing:
                        cursor.execute(''' UPDATE dimension_scores SET total_score = ?, indicators = ?, evidence_count = ?, graded_by = ?, graded_at = ? WHERE id = ? ''', (total_score, json.dumps(indicators, ensure_ascii=False),
                              kwargs.get('evidence_count', 0),
                              kwargs.get('graded_by'), now, existing['id']))
                    else:
                        cursor.execute(''' INSERT INTO dimension_scores (eval_id, student_id, dimension, total_score, indicators, evidence_count, graded_by, graded_at, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (eval_id, eval_row['student_id'], dimension, total_score,
                              json.dumps(indicators, ensure_ascii=False),
                              kwargs.get('evidence_count', 0),
                              kwargs.get('graded_by'), now, now))
                    dim_scores = json.loads(eval_row['dimension_scores'] or '{}')
                    dim_scores[dimension] = total_score
                    cursor.execute('SELECT dimensions FROM eval_systems WHERE system_id = ?', (eval_row['system_id'],))
                    sys_row = cursor.fetchone()
                    weights = {dim: cfg['weight'] for dim,
                    cfg in json.loads(sys_row['dimensions']).items()} if sys_row else {}
                    total, level = self._calc_total_and_level(dim_scores, weights)
                    cursor.execute(''' UPDATE student_evaluations SET dimension_scores = ?, total_score = ?, level = ?, updated_at = ? WHERE eval_id = ? ''', (json.dumps(dim_scores, ensure_ascii=False), total, level, now, eval_id))
                    conn.commit()
                    logger.info(f'记录维度评分: eval={eval_id} dim={dimension} score={total_score}')
                    return {'success': True, 'dimension': dimension, 'dimension_score': total_score,
                            'total_score': total, 'level': level}
        except Exception as e:
            logger.error(f'记录维度评分失败: {e}')
            return {'success': False, 'error': str(e)}

    def submit_evaluation(self, eval_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM student_evaluations WHERE eval_id = ?', (eval_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '评价不存在'}
                    if row[0] != 'draft':
                        return {'success': False, 'error': '评价状态不允许提交'}
                    cursor.execute(''' UPDATE student_evaluations SET status = 'submitted', evaluator_id = ?, evaluator_name = ?, eval_date = ?, updated_at = ? WHERE eval_id = ? ''', (kwargs.get('evaluator_id'), kwargs.get('evaluator_name'),
                          kwargs.get('eval_date', now[:10]), now, eval_id))
                    conn.commit()
                    logger.info(f'提交评价: {eval_id}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'提交评价失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_evaluation(self, eval_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM student_evaluations WHERE eval_id = ?', (eval_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '评价不存在'}
                evaluation = dict(row)
                for field in ('dimension_scores', 'indicator_evidence'):
                    if evaluation.get(field):
                        evaluation[field] = json.loads(evaluation[field])
                cursor.execute('SELECT * FROM dimension_scores WHERE eval_id = ? ORDER BY dimension', (eval_id,))
                dimensions = [dict(r) for r in cursor.fetchall()]
                for d in dimensions:
                    if d.get('indicators'):
                        d['indicators'] = json.loads(d['indicators'])
                evaluation['dimension_details'] = dimensions
                return {'success': True, 'evaluation': evaluation}
        except Exception as e:
            logger.error(f'获取评价详情失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_evaluations(self, page: int = 1, page_size: int = 20,
                          **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM student_evaluations WHERE 1=1'
                params = []
                if filters.get('student_id'):
                    query += ' AND student_id = ?'
                    params.append(filters['student_id'])
                if filters.get('grade_level'):
                    query += ' AND grade_level = ?'
                    params.append(filters['grade_level'])
                if filters.get('term'):
                    query += ' AND term = ?'
                    params.append(filters['term'])
                if filters.get('academic_year'):
                    query += ' AND academic_year = ?'
                    params.append(filters['academic_year'])
                if filters.get('education_type'):
                    query += ' AND education_type = ?'
                    params.append(filters['education_type'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取评价列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 自评与互评 ==========

    def create_self_evaluation(self, eval_id: str, student_id: str,
                                **kwargs) -> Dict[str, Any]:
        try:
            self_eval_id = f"se_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO self_evaluations ( self_eval_id, eval_id, student_id, student_name, dimension_scores, self_summary, improvement_goals, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ''', (self_eval_id, eval_id, student_id, kwargs.get('student_name'),
                          json.dumps(kwargs.get('dimension_scores', {}), ensure_ascii=False),
                          kwargs.get('self_summary'),
                          kwargs.get('improvement_goals'), now))
                    conn.commit()
                    logger.info(f'创建自我评价: {self_eval_id}')
                    return {'success': True, 'self_eval_id': self_eval_id}
        except Exception as e:
            logger.error(f'创建自我评价失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_peer_evaluation(self, eval_id: str, evaluator_id: str,
                                student_id: str, **kwargs) -> Dict[str, Any]:
        try:
            peer_eval_id = f"pe_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO peer_evaluations ( peer_eval_id, eval_id, evaluator_id, evaluator_name, student_id, student_name, dimension, scores, comment, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (peer_eval_id, eval_id, evaluator_id, kwargs.get('evaluator_name'),
                          student_id, kwargs.get('student_name'), kwargs.get('dimension'),
                          json.dumps(kwargs.get('scores', {}), ensure_ascii=False),
                          kwargs.get('comment'), now))
                    conn.commit()
                    logger.info(f'创建同伴互评: {peer_eval_id}')
                    return {'success': True, 'peer_eval_id': peer_eval_id}
        except Exception as e:
            logger.error(f'创建同伴互评失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_peer_evaluations(self, eval_id: str, page: int = 1,
                                page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM peer_evaluations WHERE eval_id = ?'
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', (eval_id,))
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                cursor.execute(query, (eval_id, page_size, (page - 1) * page_size))
                items = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取互评列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 成长档案 ==========

    def create_growth_portfolio(self, student_id: str, **kwargs) -> Dict[str, Any]:
        try:
            portfolio_id = f"gp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT portfolio_id FROM growth_portfolios WHERE student_id = ?', (student_id,))
                    if cursor.fetchone():
                        return {'success': False, 'error': '该学生档案已存在'}
                    cursor.execute(''' INSERT INTO growth_portfolios ( portfolio_id, student_id, student_name, education_type, grade_level, enroll_year, graduate_year, total_score_avg, best_dimension, weak_dimension, level_history, achievement_count, award_count, activity_count, summary, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, 0, 0, 0, ?, ?, ?) ''', (portfolio_id, student_id, kwargs.get('student_name'),
                          kwargs.get('education_type'), kwargs.get('grade_level'),
                          kwargs.get('enroll_year'), kwargs.get('graduate_year'),
                          kwargs.get('best_dimension'), kwargs.get('weak_dimension'),
                          json.dumps(kwargs.get('level_history', []), ensure_ascii=False),
                          kwargs.get('summary'), now, now))
                    conn.commit()
                    logger.info(f'创建成长档案: student={student_id} ({portfolio_id})')
                    return {'success': True, 'portfolio_id': portfolio_id}
        except Exception as e:
            logger.error(f'创建成长档案失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_growth_record(self, portfolio_id: str, student_id: str,
                           **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"gr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            record_type = kwargs.get('record_type', 'milestone')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO growth_records ( record_id, portfolio_id, student_id, record_type, title, description, record_date, dimension, score, level, file_url, created_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (record_id, portfolio_id, student_id, record_type,
                          kwargs.get('title', ''), kwargs.get('description'),
                          kwargs.get('record_date', now[:10]), kwargs.get('dimension'),
                          kwargs.get('score'), kwargs.get('level'),
                          kwargs.get('file_url'), now))
                    field_map = {'achievement': 'achievement_count', 'award': 'award_count',
                                 'activity': 'activity_count'}
                    if record_type in field_map:
                        cursor.execute(
                        f'UPDATE growth_portfolios SET {field_map[record_type]} = {field_map[record_type]} + 1, updated_at = ? WHERE portfolio_id = ?', (now, portfolio_id))
                    conn.commit()
                    logger.info(f'添加成长记录: {record_id}')
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'添加成长记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_growth_portfolio(self, student_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM growth_portfolios WHERE student_id = ?', (student_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '成长档案不存在'}
                portfolio = dict(row)
                if portfolio.get('level_history'):
                    portfolio['level_history'] = json.loads(portfolio['level_history'])
                cursor.execute('SELECT * FROM growth_records WHERE portfolio_id = ? ORDER BY record_date DESC',
                (portfolio['portfolio_id'],))
                portfolio['records'] = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'portfolio': portfolio}
        except Exception as e:
            logger.error(f'获取成长档案失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_growth_portfolio(self, student_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT portfolio_id, level_history FROM growth_portfolios WHERE student_id = ?',
                    (student_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '成长档案不存在'}
                    level_history = json.loads(row['level_history'] or '[]')
                    if kwargs.get('level'):
                        level_history.append({'level': kwargs['level'], 'academic_year': kwargs.get('academic_year'),
                        'term': kwargs.get('term'), 'score': kwargs.get('score')})
                    cursor.execute(''' UPDATE growth_portfolios SET summary = ?, best_dimension = ?, weak_dimension = ?, total_score_avg = ?, level_history = ?, updated_at = ? WHERE student_id = ? ''', (kwargs.get('summary', ''), kwargs.get('best_dimension'),
                          kwargs.get('weak_dimension'), kwargs.get('total_score_avg', 0),
                          json.dumps(level_history, ensure_ascii=False), now, student_id))
                    conn.commit()
                    logger.info(f'更新成长档案: student={student_id}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'更新成长档案失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 学期报告 ==========

    def generate_term_report(self, student_id: str, academic_year: str,
                              term: str, **kwargs) -> Dict[str, Any]:
        try:
            report_id = f"tr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                'SELECT * FROM student_evaluations WHERE student_id = ? AND academic_year = ? AND term = ? ORDER BY  updated_at DESC LIMIT 1', (student_id, academic_year, term))
                eval_row = cursor.fetchone()
                dimension_analysis = {}
                overall_level = kwargs.get('overall_level')
                if eval_row:
                    evaluation = dict(eval_row)
                    dim_scores = json.loads(evaluation.get('dimension_scores') or '{}')
                    cursor.execute('SELECT * FROM dimension_scores WHERE eval_id = ?', (evaluation['eval_id'],))
                    for d in cursor.fetchall():
                        d = dict(d)
                        indicators = json.loads(d.get('indicators') or '{}')
                        dimension_analysis[d['dimension']] = {'total_score': d['total_score'], 'indicators': indicators}
                    if not overall_level:
                        overall_level = evaluation.get('level')
                    if not kwargs.get('eval_id'):
                        kwargs['eval_id'] = evaluation['eval_id']
                    for k in ('student_name', 'education_type', 'grade_level'):
                        if not kwargs.get(k):
                            kwargs[k] = evaluation.get(k)
                with self._lock:
                    cursor.execute(''' INSERT INTO term_reports ( report_id, student_id, student_name, education_type, grade_level, academic_year, term, eval_id, dimension_analysis, strengths, weaknesses, improvement_plan, teacher_comment, parent_comment, self_reflection, overall_level, generated_at, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (report_id, student_id, kwargs.get('student_name'),
                          kwargs.get('education_type'), kwargs.get('grade_level'),
                          academic_year, term, kwargs.get('eval_id'),
                          json.dumps(dimension_analysis, ensure_ascii=False),
                          kwargs.get('strengths'), kwargs.get('weaknesses'),
                          kwargs.get('improvement_plan'), kwargs.get('teacher_comment'),
                          kwargs.get('parent_comment'), kwargs.get('self_reflection'),
                          overall_level, now, now, now))
                    conn.commit()
                    logger.info(f'生成学期报告: {report_id}')
                    return {'success': True, 'report_id': report_id, 'overall_level': overall_level}
        except Exception as e:
            logger.error(f'生成学期报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_term_report(self, report_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM term_reports WHERE report_id = ?', (report_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '报告不存在'}
                report = dict(row)
                if report.get('dimension_analysis'):
                    report['dimension_analysis'] = json.loads(report['dimension_analysis'])
                return {'success': True, 'report': report}
        except Exception as e:
            logger.error(f'获取学期报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_term_reports(self, student_id: str = None, page: int = 1,
                           page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM term_reports WHERE 1=1'
                params = []
                if student_id:
                    query += ' AND student_id = ?'
                    params.append(student_id)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取报告列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 评价申诉 ==========

    def create_appeal(self, eval_id: str, student_id: str, dimension: str,
                       **kwargs) -> Dict[str, Any]:
        try:
            appeal_id = f"ap_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO eval_appeals ( appeal_id, eval_id, student_id, student_name, dimension, original_score, appealed_score, reason, evidence, status, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?) ''', (appeal_id, eval_id, student_id, kwargs.get('student_name'),
                          dimension, kwargs.get('original_score'),
                          kwargs.get('appealed_score'), kwargs.get('reason'),
                          json.dumps(kwargs.get('evidence', []), ensure_ascii=False),
                          now, now))
                    conn.commit()
                    logger.info(f'创建申诉: {appeal_id}')
                    return {'success': True, 'appeal_id': appeal_id}
        except Exception as e:
            logger.error(f'创建申诉失败: {e}')
            return {'success': False, 'error': str(e)}

    def review_appeal(self, appeal_id: str, reviewed_by: str,
                       **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = kwargs.get('status', 'approved')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' UPDATE eval_appeals SET status = ?, reviewed_by = ?, review_result = ?, reviewed_at = ?, updated_at = ? WHERE appeal_id = ? AND status = 'pending' ''', (status, reviewed_by, kwargs.get('review_result'), now, now, appeal_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'审核申诉: {appeal_id} -> {status}')
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '申诉不存在或已处理'}
        except Exception as e:
            logger.error(f'审核申诉失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_appeals(self, page: int = 1, page_size: int = 20,
                      **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM eval_appeals WHERE 1=1'
                params = []
                if filters.get('student_id'):
                    query += ' AND student_id = ?'
                    params.append(filters['student_id'])
                if filters.get('eval_id'):
                    query += ' AND eval_id = ?'
                    params.append(filters['eval_id'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取申诉列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 班级汇总 ==========

    def generate_class_evaluation(self, class_name: str, grade_level: str,
                                   academic_year: str, term: str,
                                   **kwargs) -> Dict[str, Any]:
        try:
            class_eval_id = f"cle_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    query = 'SELECT * FROM student_evaluations WHERE grade_level = ? AND academic_year = ? AND term = ?  AND status = ?'
                    params = [grade_level, academic_year, term, 'submitted']
                    if kwargs.get('education_type'):
                        query += ' AND education_type = ?'
                        params.append(kwargs['education_type'])
                    cursor.execute(query, params)
                    evals = [dict(r) for r in cursor.fetchall()]
                    student_count = len(evals)
                    scores = []
                    level_dist = {lvl: 0 for lvl in EVALUATION_LEVELS}
                    dim_total = {dim: [] for dim in FIVE_DIMENSIONS}
                    for ev in evals:
                        if ev.get('total_score') is not None:
                            scores.append(ev['total_score'])
                        if ev.get('level') in level_dist:
                            level_dist[ev['level']] += 1
                        dim_scores = json.loads(ev.get('dimension_scores') or '{}')
                        for dim, sc in dim_scores.items():
                            if dim in dim_total:
                                dim_total[dim].append(sc)
                    avg_score = round(sum(scores) / len(scores), 2) if scores else 0
                    max_score = max(scores) if scores else 0
                    min_score = min(scores) if scores else 0
                    dimension_avg = {dim: round(sum(v) / len(v), 2) if v else 0 for dim, v in dim_total.items()}
                    cursor.execute(''' INSERT INTO class_evaluations ( class_eval_id, class_name, grade_level, academic_year, term, system_id, student_count, avg_score, max_score, min_score, level_distribution, dimension_avg, generated_at, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (class_eval_id, class_name, grade_level, academic_year, term,
                          kwargs.get('system_id'), student_count, avg_score, max_score, min_score,
                          json.dumps(level_dist, ensure_ascii=False),
                          json.dumps(dimension_avg, ensure_ascii=False), now, now, now))
                    conn.commit()
                    logger.info(f'生成班级评价汇总: {class_name} ({class_eval_id})')
                    return {'success': True, 'class_eval_id': class_eval_id,
                            'student_count': student_count, 'avg_score': avg_score}
        except Exception as e:
            logger.error(f'生成班级评价汇总失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_class_evaluations(self, page: int = 1, page_size: int = 20,
                                **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM class_evaluations WHERE 1=1'
                params = []
                if filters.get('class_name'):
                    query += ' AND class_name = ?'
                    params.append(filters['class_name'])
                if filters.get('grade_level'):
                    query += ' AND grade_level = ?'
                    params.append(filters['grade_level'])
                if filters.get('academic_year'):
                    query += ' AND academic_year = ?'
                    params.append(filters['academic_year'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取班级汇总列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                sys_query = 'SELECT COUNT(*) as cnt FROM eval_systems'
                sys_params = []
                if education_type:
                    sys_query += ' WHERE education_type = ? OR education_type = ?'
                    sys_params.extend([education_type, 'common'])
                cursor.execute(sys_query, sys_params)
                system_count = cursor.fetchone()['cnt']
                eval_query = 'SELECT level, dimension_scores FROM student_evaluations WHERE status = ?'
                eval_params = ['submitted']
                if education_type:
                    eval_query += ' AND education_type = ?'
                    eval_params.append(education_type)
                cursor.execute(eval_query, eval_params)
                eval_rows = cursor.fetchall()
                level_dist = {lvl: 0 for lvl in EVALUATION_LEVELS}
                dim_sum = {dim: 0.0 for dim in FIVE_DIMENSIONS}
                dim_count = {dim: 0 for dim in FIVE_DIMENSIONS}
                for r in eval_rows:
                    if r['level'] in level_dist:
                        level_dist[r['level']] += 1
                    dim_scores = json.loads(r['dimension_scores'] or '{}')
                    for dim, sc in dim_scores.items():
                        if dim in dim_sum:
                            dim_sum[dim] += float(sc)
                            dim_count[dim] += 1
                dimension_avg = {dim: round(dim_sum[dim] / dim_count[dim],
                2) if dim_count[dim] else 0 for dim in FIVE_DIMENSIONS}
                ev_query = 'SELECT evidence_type, COUNT(*) as cnt FROM evidence_records GROUP BY evidence_type'
                cursor.execute(ev_query)
                evidence_dist = {row['evidence_type']: row['cnt'] for row in cursor.fetchall()}
                cursor.execute('SELECT COUNT(*) as cnt FROM growth_portfolios')
                portfolio_count = cursor.fetchone()['cnt']
                cursor.execute('SELECT COUNT(*) as cnt FROM eval_appeals')
                total_appeals = cursor.fetchone()['cnt']
                cursor.execute('SELECT COUNT(*) as cnt FROM eval_appeals WHERE status != ?', ('pending',))
                processed_appeals = cursor.fetchone()['cnt']
                appeal_rate = round(processed_appeals / total_appeals * 100, 2) if total_appeals else 0
                return {'success': True, 'system_count': system_count,
                        'level_distribution': level_dist,
                        'dimension_avg': dimension_avg,
                        'evidence_type_distribution': evidence_dist,
                        'portfolio_count': portfolio_count,
                        'appeal_total': total_appeals,
                        'appeal_processed': processed_appeals,
                        'appeal_processing_rate': appeal_rate}
        except Exception as e:
            logger.error(f'获取统计失败: {e}')
            return {'success': False, 'error': str(e)}


if __name__ == '__main__':
    service = ComprehensiveEvaluationService()
    print('学生综合素质评价服务初始化完成')
    stats = service.get_statistics()
    print(f'统计: {stats}')
