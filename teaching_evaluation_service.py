#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教学评价服务 (v15.2.0)
====================================
提供教学质量评价、教师评价、课程评价和学生评价等综合服务。

核心能力：
1. 教学评价 - 多维度教学质量评价
2. 教师评价 - 学生对教师的评价反馈
3. 课程评价 - 课程满意度评价
4. 学生评价 - 学生学习表现评价
5. 评价分析 - 评价数据统计分析
6. 评价报告 - 自动生成评价报告
7. 成人评价 - 成人教育教学评价
8. K12评价 - 九年制义务教育教学评价
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'teaching_evaluation_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('TeachingEvaluation')


# ========== 评价配置 ==========

# 评价类型
EVALUATION_TYPES = {
    'teacher': {'name': '教师评价', 'target_type': 'teacher', 'evaluator_type': 'student'},
    'course': {'name': '课程评价', 'target_type': 'course', 'evaluator_type': 'student'},
    'teaching': {'name': '教学评价', 'target_type': 'class', 'evaluator_type': 'student'},
    'student': {'name': '学生评价', 'target_type': 'student', 'evaluator_type': 'teacher'},
    'self_evaluation': {'name': '自我评价', 'target_type': 'self', 'evaluator_type': 'self'},
    'peer_evaluation': {'name': '同伴评价', 'target_type': 'peer', 'evaluator_type': 'student'}
}

# 评价维度
EVALUATION_DIMENSIONS = {
    'teacher': {
        'teaching_attitude': {'name': '教学态度', 'weight': 0.15, 'description': '认真负责、耐心细致'},
        'professional_level': {'name': '专业水平', 'weight': 0.2, 'description': '知识渊博、讲解清晰'},
        'teaching_method': {'name': '教学方法', 'weight': 0.2, 'description': '方法多样、生动有趣'},
        'communication': {'name': '沟通互动', 'weight': 0.15, 'description': '善于交流、鼓励提问'},
        'classroom_management': {'name': '课堂管理', 'weight': 0.15, 'description': '秩序井然、节奏把控'},
        'teaching_effect': {'name': '教学效果', 'weight': 0.15, 'description': '学有所获、能力提升'}
    },
    'course': {
        'content_quality': {'name': '内容质量', 'weight': 0.25, 'description': '内容充实、实用性强'},
        'difficulty': {'name': '难易程度', 'weight': 0.15, 'description': '难度适中、循序渐进'},
        'practicality': {'name': '实用性', 'weight': 0.2, 'description': '学以致用、贴近实际'},
        'interest': {'name': '趣味性', 'weight': 0.15, 'description': '生动有趣、吸引学习'},
        'resource_quality': {'name': '资源质量', 'weight': 0.15, 'description': '资料丰富、质量优良'},
        'workload': {'name': '作业量', 'weight': 0.1, 'description': '作业适度、负担合理'}
    },
    'teaching': {
        'teaching_design': {'name': '教学设计', 'weight': 0.2, 'description': '目标明确、结构合理'},
        'teaching_content': {'name': '教学内容', 'weight': 0.2, 'description': '重点突出、内容充实'},
        'teaching_method': {'name': '教学方法', 'weight': 0.2, 'description': '方法得当、启发思维'},
        'teaching_effect': {'name': '教学效果', 'weight': 0.25, 'description': '知识掌握、能力提升'},
        'class_atmosphere': {'name': '课堂氛围', 'weight': 0.15, 'description': '积极活跃、师生互动'}
    },
    'student': {
        'learning_attitude': {'name': '学习态度', 'weight': 0.2, 'description': '认真刻苦、积极主动'},
        'class_participation': {'name': '课堂参与', 'weight': 0.15, 'description': '积极发言、勤于思考'},
        'homework_quality': {'name': '作业质量', 'weight': 0.2, 'description': '按时完成、质量优良'},
        'academic_performance': {'name': '学业成绩', 'weight': 0.25, 'description': '成绩优秀、稳步提升'},
        'collaboration': {'name': '合作交流', 'weight': 0.1, 'description': '乐于助人、善于合作'},
        'innovation': {'name': '创新思维', 'weight': 0.1, 'description': '勇于探索、敢于创新'}
    }
}

# 评价等级
RATING_LEVELS = {
    5: {'name': '优秀', 'score_range': [90, 100], 'description': '非常满意，表现卓越'},
    4: {'name': '良好', 'score_range': [80, 89], 'description': '比较满意，表现良好'},
    3: {'name': '中等', 'score_range': [70, 79], 'description': '基本满意，一般水平'},
    2: {'name': '及格', 'score_range': [60, 69], 'description': '不太满意，有待提升'},
    1: {'name': '待提升', 'score_range': [0, 59], 'description': '不满意，需要改进'}
}

# 评价状态
EVALUATION_STATUS = {
    'draft': '草稿',
    'published': '已发布',
    'ongoing': '进行中',
    'closed': '已结束',
    'archived': '已归档'
}

# 成人教育评价重点
ADULT_EVALUATION_FOCUS = {
    'practical_application': {'name': '实际应用', 'weight': 0.2},
    'career_help': {'name': '职业帮助', 'weight': 0.2},
    'time_arrangement': {'name': '时间安排', 'weight': 0.15},
    'teaching_quality': {'name': '教学质量', 'weight': 0.25},
    'service_quality': {'name': '服务质量', 'weight': 0.2}
}

# K12评价重点
K12_EVALUATION_FOCUS = {
    'knowledge_mastery': {'name': '知识掌握', 'weight': 0.3},
    'ability_development': {'name': '能力培养', 'weight': 0.25},
    'interest_cultivation': {'name': '兴趣培养', 'weight': 0.15},
    'learning_habits': {'name': '学习习惯', 'weight': 0.15},
    'character_development': {'name': '品德发展', 'weight': 0.15}
}


class TeachingEvaluationService:
    """教学评价服务"""

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
                    CREATE TABLE IF NOT EXISTS evaluation_templates (
                        template_id TEXT PRIMARY KEY,
                        template_name TEXT NOT NULL,
                        evaluation_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        description TEXT,
                        dimensions TEXT NOT NULL,
                        total_score REAL DEFAULT 100,
                        is_anonymous INTEGER DEFAULT 1,
                        allow_comment INTEGER DEFAULT 1,
                        status TEXT DEFAULT 'draft',
                        created_by INTEGER,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS evaluation_tasks (
                        task_id TEXT PRIMARY KEY,
                        task_name TEXT NOT NULL,
                        template_id TEXT,
                        evaluation_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        target_id TEXT,
                        target_type TEXT,
                        target_name TEXT,
                        evaluator_type TEXT,
                        class_id TEXT,
                        subject TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        status TEXT DEFAULT 'draft',
                        total_evaluators INTEGER DEFAULT 0,
                        completed_evaluators INTEGER DEFAULT 0,
                        average_score REAL DEFAULT 0,
                        created_by INTEGER,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS evaluation_records (
                        record_id TEXT PRIMARY KEY,
                        task_id TEXT NOT NULL,
                        evaluator_id INTEGER NOT NULL,
                        evaluator_name TEXT,
                        target_id TEXT NOT NULL,
                        target_type TEXT,
                        scores TEXT NOT NULL,
                        total_score REAL NOT NULL,
                        comment TEXT,
                        suggestions TEXT,
                        is_anonymous INTEGER DEFAULT 1,
                        is_valid INTEGER DEFAULT 1,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS evaluation_dimension_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_id TEXT NOT NULL,
                        dimension_code TEXT NOT NULL,
                        dimension_name TEXT,
                        average_score REAL DEFAULT 0,
                        max_score REAL DEFAULT 0,
                        min_score REAL DEFAULT 0,
                        std_dev REAL DEFAULT 0,
                        response_count INTEGER DEFAULT 0,
                        UNIQUE(task_id, dimension_code)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS evaluation_reports (
                        report_id TEXT PRIMARY KEY,
                        task_id TEXT NOT NULL,
                        report_type TEXT DEFAULT 'summary',
                        title TEXT,
                        content TEXT,
                        overall_score REAL,
                        strengths TEXT,
                        improvements TEXT,
                        suggestions TEXT,
                        generated_at TEXT,
                        generated_by INTEGER
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS teacher_evaluation_archive (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        teacher_id INTEGER NOT NULL,
                        evaluation_type TEXT,
                        period TEXT,
                        overall_score REAL,
                        dimension_scores TEXT,
                        total_evaluations INTEGER,
                        subject TEXT,
                        class_id TEXT,
                        created_at TEXT,
                        UNIQUE(teacher_id, evaluation_type, period)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS course_evaluation_archive (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        course_id TEXT NOT NULL,
                        evaluation_type TEXT,
                        period TEXT,
                        overall_score REAL,
                        dimension_scores TEXT,
                        total_evaluations INTEGER,
                        subject TEXT,
                        created_at TEXT,
                        UNIQUE(course_id, evaluation_type, period)
                    )
                ''')
                conn.commit()
                logger.info('教学评价服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    def create_template(self, template_name: str, evaluation_type: str,
                         education_type: str, dimensions: dict, **kwargs) -> Dict[str, Any]:
        try:
            template_id = f"tmpl_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO evaluation_templates (
                            template_id, template_name, evaluation_type, education_type,
                            description, dimensions, total_score, is_anonymous,
                            allow_comment, status, created_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        template_id, template_name, evaluation_type, education_type,
                        kwargs.get('description'), json.dumps(dimensions, ensure_ascii=False),
                        kwargs.get('total_score', 100), kwargs.get('is_anonymous', 1),
                        kwargs.get('allow_comment', 1), kwargs.get('status', 'draft'),
                        kwargs.get('created_by'), now, now
                    ))
                    conn.commit()
                    logger.info(f'创建评价模板: {template_name} ({template_id})')
                    return {'success': True, 'template_id': template_id, 'template_name': template_name}
        except Exception as e:
            logger.error(f'创建评价模板失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM evaluation_templates WHERE template_id = ?', (template_id,))
                row = cursor.fetchone()
                if row:
                    tmpl = dict(row)
                    if tmpl.get('dimensions'):
                        tmpl['dimensions'] = json.loads(tmpl['dimensions'])
                    return tmpl
                return None
        except Exception as e:
            logger.error(f'获取评价模板失败: {e}')
            return None

    def list_templates(self, evaluation_type: str = None, education_type: str = None,
                        status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM evaluation_templates WHERE 1=1'
                params = []
                if evaluation_type:
                    query += ' AND evaluation_type = ?'
                    params.append(evaluation_type)
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
                templates = [dict(t) for t in cursor.fetchall()]
                return {'success': True, 'templates': templates, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取评价模板列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_evaluation_task(self, task_name: str, evaluation_type: str,
                                education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            task_id = f"etask_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO evaluation_tasks (
                            task_id, task_name, template_id, evaluation_type, education_type,
                            target_id, target_type, target_name, evaluator_type, class_id,
                            subject, start_time, end_time, status, total_evaluators,
                            created_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        task_id, task_name, kwargs.get('template_id'), evaluation_type,
                        education_type, kwargs.get('target_id'), kwargs.get('target_type'),
                        kwargs.get('target_name'), kwargs.get('evaluator_type'),
                        kwargs.get('class_id'), kwargs.get('subject'),
                        kwargs.get('start_time'), kwargs.get('end_time'),
                        kwargs.get('status', 'draft'), kwargs.get('total_evaluators', 0),
                        kwargs.get('created_by'), now, now
                    ))
                    conn.commit()
                    logger.info(f'创建评价任务: {task_name} ({task_id})')
                    return {'success': True, 'task_id': task_id, 'task_name': task_name}
        except Exception as e:
            logger.error(f'创建评价任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def publish_evaluation_task(self, task_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE evaluation_tasks SET status = 'ongoing', updated_at = ?
                        WHERE task_id = ? AND status = 'draft'
                    ''', (now, task_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'发布评价任务: {task_id}')
                        return {'success': True}
                    return {'success': False, 'error': '任务状态不允许发布'}
        except Exception as e:
            logger.error(f'发布评价任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def submit_evaluation(self, task_id: str, evaluator_id: int, scores: dict,
                           comment: str = None, suggestions: str = None,
                           is_anonymous: int = 1, evaluator_name: str = None) -> Dict[str, Any]:
        try:
            record_id = f"erec_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            total_score = self._calculate_total_score(task_id, scores)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT target_id, target_type FROM evaluation_tasks WHERE task_id = ?', (task_id,))
                    task = cursor.fetchone()
                    if not task:
                        return {'success': False, 'error': '评价任务不存在'}
                    target_id, target_type = task
                    cursor.execute('''
                        INSERT INTO evaluation_records (
                            record_id, task_id, evaluator_id, evaluator_name, target_id,
                            target_type, scores, total_score, comment, suggestions,
                            is_anonymous, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        record_id, task_id, evaluator_id, evaluator_name, target_id,
                        target_type, json.dumps(scores, ensure_ascii=False), total_score,
                        comment, suggestions, is_anonymous, now
                    ))
                    cursor.execute('''
                        UPDATE evaluation_tasks SET
                            completed_evaluators = completed_evaluators + 1,
                            average_score = (
                                SELECT AVG(total_score) FROM evaluation_records
                                WHERE task_id = ? AND is_valid = 1
                            ),
                            updated_at = ?
                        WHERE task_id = ?
                    ''', (task_id, now, task_id))
                    self._update_dimension_stats(cursor, task_id, scores)
                    conn.commit()
                    logger.info(f'提交评价: {record_id}, 得分: {total_score}')
                    return {'success': True, 'record_id': record_id, 'total_score': total_score}
        except Exception as e:
            logger.error(f'提交评价失败: {e}')
            return {'success': False, 'error': str(e)}

    def _calculate_total_score(self, task_id: str, scores: dict) -> float:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT template_id, evaluation_type FROM evaluation_tasks WHERE task_id = ?', (task_id,))
                task = cursor.fetchone()
                if not task:
                    return sum(scores.values()) / len(scores) if scores else 0
                template_id, eval_type = task
                if template_id:
                    cursor.execute('SELECT dimensions FROM evaluation_templates WHERE template_id = ?', (template_id,))
                    row = cursor.fetchone()
                    if row and row[0]:
                        dimensions = json.loads(row[0])
                        total = 0
                        for dim_code, dim_info in dimensions.items():
                            if dim_code in scores:
                                weight = dim_info.get('weight', 1 / len(dimensions))
                                total += scores[dim_code] * weight
                        return round(total, 2)
                default_dims = EVALUATION_DIMENSIONS.get(eval_type, {})
                if default_dims:
                    total = 0
                    for dim_code, dim_info in default_dims.items():
                        if dim_code in scores:
                            weight = dim_info.get('weight', 1 / len(default_dims))
                            total += scores[dim_code] * weight
                    return round(total, 2)
                return sum(scores.values()) / len(scores) * 20 if scores else 0
        except Exception as e:
            logger.error(f'计算总分失败: {e}')
            return sum(scores.values()) / len(scores) if scores else 0

    def _update_dimension_stats(self, cursor, task_id: str, scores: dict):
        try:
            for dim_code, score in scores.items():
                cursor.execute('''
                    INSERT INTO evaluation_dimension_stats (task_id, dimension_code, dimension_name, average_score, max_score, min_score, response_count)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                    ON CONFLICT(task_id, dimension_code) DO UPDATE SET
                        average_score = (average_score * response_count + excluded.average_score) / (response_count + 1),
                        max_score = MAX(max_score, excluded.max_score),
                        min_score = MIN(min_score, excluded.min_score),
                        response_count = response_count + 1
                ''', (task_id, dim_code, dim_code, score, score, score))
        except Exception as e:
            logger.error(f'更新维度统计失败: {e}')

    def get_evaluation_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM evaluation_tasks WHERE task_id = ?', (task_id,))
                row = cursor.fetchone()
                if row:
                    task = dict(row)
                    return task
                return None
        except Exception as e:
            logger.error(f'获取评价任务失败: {e}')
            return None

    def list_evaluation_tasks(self, education_type: str = None, evaluation_type: str = None,
                               status: str = None, class_id: str = None,
                               page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM evaluation_tasks WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if evaluation_type:
                    query += ' AND evaluation_type = ?'
                    params.append(evaluation_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                if class_id:
                    query += ' AND class_id = ?'
                    params.append(class_id)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                tasks = [dict(t) for t in cursor.fetchall()]
                return {'success': True, 'tasks': tasks, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取评价任务列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_task_statistics(self, task_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM evaluation_tasks WHERE task_id = ?', (task_id,))
                task = cursor.fetchone()
                if not task:
                    return {'success': False, 'error': '评价任务不存在'}
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_responses,
                        AVG(total_score) as avg_score,
                        MAX(total_score) as max_score,
                        MIN(total_score) as min_score
                    FROM evaluation_records WHERE task_id = ? AND is_valid = 1
                ''', (task_id,))
                overall = cursor.fetchone()
                cursor.execute('SELECT * FROM evaluation_dimension_stats WHERE task_id = ?', (task_id,))
                dims = [dict(d) for d in cursor.fetchall()]
                cursor.execute('''
                    SELECT ROUND(total_score / 20) * 20 as score_range, COUNT(*) as cnt
                    FROM evaluation_records WHERE task_id = ? AND is_valid = 1
                    GROUP BY score_range ORDER BY score_range
                ''', (task_id,))
                distribution = {r[0]: r[1] for r in cursor.fetchall()}
                return {
                    'success': True,
                    'task': dict(task),
                    'overall': {
                        'total_responses': overall['total_responses'] or 0,
                        'average_score': round(overall['avg_score'] or 0, 2),
                        'max_score': overall['max_score'] or 0,
                        'min_score': overall['min_score'] or 0
                    },
                    'dimension_stats': dims,
                    'score_distribution': distribution
                }
        except Exception as e:
            logger.error(f'获取任务统计失败: {e}')
            return {'success': False, 'error': str(e)}

    def generate_evaluation_report(self, task_id: str, report_type: str = 'summary') -> Dict[str, Any]:
        try:
            report_id = f"rpt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            stats = self.get_task_statistics(task_id)
            if not stats.get('success'):
                return {'success': False, 'error': '获取统计数据失败'}
            task = stats.get('task', {})
            overall = stats.get('overall', {})
            dim_stats = stats.get('dimension_stats', [])
            avg_score = overall.get('average_score', 0)
            level = self._get_rating_level(avg_score)
            strengths = []
            improvements = []
            for dim in dim_stats:
                dim_score = dim.get('average_score', 0)
                if dim_score >= 85:
                    strengths.append(dim.get('dimension_name', dim.get('dimension_code', '')))
                elif dim_score < 70:
                    improvements.append(dim.get('dimension_name', dim.get('dimension_code', '')))
            suggestions = self._generate_suggestions(improvements, task.get('evaluation_type', ''))
            content = json.dumps({
                'overview': f'本次评价共收到{overall.get("total_responses", 0)}份有效评价，平均分为{avg_score}分，等级为{level.get("name", "")}。',
                'strengths': strengths,
                'improvements': improvements,
                'suggestions': suggestions
            }, ensure_ascii=False)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO evaluation_reports (
                            report_id, task_id, report_type, title, content, overall_score,
                            strengths, improvements, suggestions, generated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        report_id, task_id, report_type,
                        f'{task.get("task_name", "")}评价报告',
                        content, avg_score,
                        json.dumps(strengths, ensure_ascii=False),
                        json.dumps(improvements, ensure_ascii=False),
                        json.dumps(suggestions, ensure_ascii=False),
                        now
                    ))
                    conn.commit()
                    logger.info(f'生成评价报告: {report_id}')
                    return {
                        'success': True,
                        'report_id': report_id,
                        'overall_score': avg_score,
                        'level': level,
                        'strengths': strengths,
                        'improvements': improvements,
                        'suggestions': suggestions
                    }
        except Exception as e:
            logger.error(f'生成评价报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def _get_rating_level(self, score: float) -> dict:
        for level, info in sorted(RATING_LEVELS.items(), reverse=True):
            if score >= info['score_range'][0]:
                return {'level': level, **info}
        return {'level': 1, **RATING_LEVELS[1]}

    def _generate_suggestions(self, improvements: list, eval_type: str) -> list:
        suggestions = []
        for item in improvements:
            if '态度' in item:
                suggestions.append(f'建议在{item}方面加强，提升教学投入度和责任心')
            elif '方法' in item:
                suggestions.append(f'建议优化{item}，采用更多样化的教学方式')
            elif '效果' in item:
                suggestions.append(f'建议关注{item}，加强课后练习和反馈')
            elif '互动' in item or '沟通' in item:
                suggestions.append(f'建议增强课堂{item}，鼓励学生积极参与')
            else:
                suggestions.append(f'建议在{item}方面进行改进和提升')
        if not suggestions:
            suggestions.append('继续保持当前良好的教学状态，争取更好成绩')
        return suggestions

    def get_teacher_evaluation_summary(self, teacher_id: int, education_type: str = None,
                                        period: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = '''
                    SELECT er.target_id, 
                           AVG(er.total_score) as avg_score,
                           COUNT(*) as evaluation_count,
                           et.subject,
                           et.class_id,
                           strftime('%Y-%m', er.created_at) as month
                    FROM evaluation_records er
                    JOIN evaluation_tasks et ON er.task_id = et.task_id
                    WHERE er.target_id = ? AND et.evaluation_type = 'teacher' AND er.is_valid = 1
                '''
                params = [str(teacher_id)]
                if education_type:
                    query += ' AND et.education_type = ?'
                    params.append(education_type)
                query += ' GROUP BY er.target_id, et.subject, et.class_id, month ORDER BY month DESC'
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                cursor.execute('''
                    SELECT AVG(er.total_score) as overall_avg, COUNT(*) as total_count
                    FROM evaluation_records er
                    JOIN evaluation_tasks et ON er.task_id = et.task_id
                    WHERE er.target_id = ? AND et.evaluation_type = 'teacher' AND er.is_valid = 1
                ''', [str(teacher_id)])
                overall = cursor.fetchone()
                return {
                    'success': True,
                    'overall_average': round(overall['overall_avg'] or 0, 2),
                    'total_evaluations': overall['total_count'] or 0,
                    'by_subject_class': records
                }
        except Exception as e:
            logger.error(f'获取教师评价汇总失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_course_evaluation_summary(self, course_id: str, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT AVG(er.total_score) as avg_score,
                           COUNT(*) as evaluation_count
                    FROM evaluation_records er
                    JOIN evaluation_tasks et ON er.task_id = et.task_id
                    WHERE er.target_id = ? AND et.evaluation_type = 'course' AND er.is_valid = 1
                ''', (course_id,))
                row = cursor.fetchone()
                cursor.execute('''
                    SELECT eds.dimension_code, eds.dimension_name, AVG(eds.average_score) as avg_score
                    FROM evaluation_dimension_stats eds
                    JOIN evaluation_tasks et ON eds.task_id = et.task_id
                    WHERE et.target_id = ? AND et.evaluation_type = 'course'
                    GROUP BY eds.dimension_code
                ''', (course_id,))
                dims = [dict(d) for d in cursor.fetchall()]
                return {
                    'success': True,
                    'average_score': round(row['avg_score'] or 0, 2),
                    'evaluation_count': row['evaluation_count'] or 0,
                    'dimension_scores': dims
                }
        except Exception as e:
            logger.error(f'获取课程评价汇总失败: {e}')
            return {'success': False, 'error': str(e)}

    def has_user_evaluated(self, task_id: str, user_id: int) -> bool:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT record_id FROM evaluation_records WHERE task_id = ? AND evaluator_id = ?', (task_id, user_id))
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f'检查评价状态失败: {e}')
            return False

    def close_evaluation_task(self, task_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE evaluation_tasks SET status = 'closed', updated_at = ?
                        WHERE task_id = ? AND status = 'ongoing'
                    ''', (now, task_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'关闭评价任务: {task_id}')
                        return {'success': True}
                    return {'success': False, 'error': '任务状态不允许关闭'}
        except Exception as e:
            logger.error(f'关闭评价任务失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_user_evaluation_records(self, user_id: int, evaluator: bool = True,
                                     education_type: str = None,
                                     page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                if evaluator:
                    query = '''
                        SELECT er.*, et.task_name, et.evaluation_type, et.target_name
                        FROM evaluation_records er
                        JOIN evaluation_tasks et ON er.task_id = et.task_id
                        WHERE er.evaluator_id = ?
                    '''
                    params = [user_id]
                else:
                    query = '''
                        SELECT er.*, et.task_name, et.evaluation_type
                        FROM evaluation_records er
                        JOIN evaluation_tasks et ON er.task_id = et.task_id
                        WHERE er.target_id = ? AND er.is_valid = 1
                    '''
                    params = [str(user_id)]
                if education_type:
                    query += ' AND et.education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY er.created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取用户评价记录失败: {e}')
            return {'success': False, 'error': str(e)}
