#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 考试与成绩管理服务 (v15.3.0)
====================================
提供考试安排、成绩录入、成绩分析和报告生成等综合服务。

核心能力：
1. 考试管理 - 考试创建、安排、状态管理
2. 成绩录入 - 单个/批量成绩录入
3. 成绩分析 - 排名、分布、对比分析
4. 报告生成 - 成绩单、班级报告、学期报告
5. 成绩预警 - 不及格预警、退步预警
6. 考试类型 - 月考/期中/期末/模拟/等级考试
7. 成人考试 - 成人教育考试管理
8. K12考试 - 九年制义务教育考试管理
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exam_management_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ExamManagement')


# ========== 考试配置 ==========

# 考试类型
EXAM_TYPES = {
    'monthly': {'name': '月考', 'weight': 0.1, 'full_score': 100},
    'midterm': {'name': '期中考试', 'weight': 0.3, 'full_score': 100},
    'final': {'name': '期末考试', 'weight': 0.4, 'full_score': 100},
    'mock': {'name': '模拟考试', 'weight': 0.15, 'full_score': 100},
    'quiz': {'name': '随堂测验', 'weight': 0.05, 'full_score': 50},
    'level_test': {'name': '等级考试', 'weight': 0.0, 'full_score': 180},
    'placement': {'name': '分班考试', 'weight': 0.0, 'full_score': 100},
    'graduation': {'name': '毕业考试', 'weight': 0.5, 'full_score': 100}
}

# 考试状态
EXAM_STATUS = {
    'draft': '草稿',
    'scheduled': '已安排',
    'ongoing': '进行中',
    'grading': '批改中',
    'completed': '已完成',
    'published': '成绩已发布',
    'archived': '已归档'
}

# 成绩等级
GRADE_LEVELS = {
    'A+': {'score_range': [95, 100], 'gpa': 4.0, 'description': '卓越'},
    'A': {'score_range': [90, 94], 'gpa': 3.8, 'description': '优秀'},
    'B+': {'score_range': [85, 89], 'gpa': 3.5, 'description': '良好+'},
    'B': {'score_range': [80, 84], 'gpa': 3.2, 'description': '良好'},
    'C+': {'score_range': [75, 79], 'gpa': 2.8, 'description': '中等+'},
    'C': {'score_range': [70, 74], 'gpa': 2.5, 'description': '中等'},
    'D+': {'score_range': [65, 69], 'gpa': 2.0, 'description': '及格+'},
    'D': {'score_range': [60, 64], 'gpa': 1.5, 'description': '及格'},
    'F': {'score_range': [0, 59], 'gpa': 0.0, 'description': '不及格'}
}

# 成人考试类型
ADULT_EXAM_TYPES = {
    'jplt': {'name': 'JLPT日本语能力测试', 'levels': ['N5', 'N4', 'N3', 'N2', 'N1'], 'full_score': 180},
    'jtest': {'name': 'J.TEST实用日本语鉴定', 'levels': ['A-D', 'E-F'], 'full_score': 1000},
    'toeic': {'name': 'TOEIC托业考试', 'levels': ['Listening', 'Reading'], 'full_score': 990},
    'toefl': {'name': 'TOEFL托福', 'levels': ['ibt'], 'full_score': 120},
    'adult_gaokao': {'name': '成人高考', 'levels': ['高起专', '高起本', '专升本'], 'full_score': 450},
    'self_study': {'name': '自学考试', 'levels': ['专科', '本科'], 'full_score': 100},
    'internal': {'name': '校内考试', 'levels': ['月考', '期中', '期末'], 'full_score': 100}
}

# K12考试类型
K12_EXAM_TYPES = {
    'unit_test': {'name': '单元测试', 'full_score': 100},
    'monthly': {'name': '月考', 'full_score': 100},
    'midterm': {'name': '期中考试', 'full_score': 100},
    'final': {'name': '期末考试', 'full_score': 100},
    'entrance_exam': {'name': '入学考试', 'full_score': 100},
    'zhongkao': {'name': '中考模拟', 'full_score': 750},
    'gaokao': {'name': '高考模拟', 'full_score': 750}
}

# 预警类型
WARNING_TYPES = {
    'fail_risk': {'name': '不及格预警', 'threshold': 60, 'color': '#f5222d'},
    'decline_risk': {'name': '退步预警', 'threshold': -10, 'color': '#faad14'},
    'attendance_risk': {'name': '考勤预警', 'threshold': 0.7, 'color': '#fa8c16'},
    'gpa_risk': {'name': 'GPA预警', 'threshold': 2.0, 'color': '#f5222d'}
}


class ExamManagementService:
    """考试与成绩管理服务"""

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
                    CREATE TABLE IF NOT EXISTS exams (
                        exam_id TEXT PRIMARY KEY,
                        exam_name TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        exam_type TEXT NOT NULL,
                        subject TEXT,
                        grade_level INTEGER,
                        class_id TEXT,
                        full_score REAL DEFAULT 100,
                        pass_score REAL DEFAULT 60,
                        exam_date TEXT,
                        duration_minutes INTEGER DEFAULT 90,
                        location TEXT,
                        supervisor TEXT,
                        status TEXT DEFAULT 'draft',
                        description TEXT,
                        created_by INTEGER,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS exam_subjects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        exam_id TEXT NOT NULL,
                        subject TEXT NOT NULL,
                        full_score REAL DEFAULT 100,
                        pass_score REAL DEFAULT 60,
                        duration_minutes INTEGER DEFAULT 90,
                        exam_date TEXT,
                        UNIQUE(exam_id, subject)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS exam_scores (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        exam_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        subject TEXT NOT NULL,
                        score REAL,
                        grade TEXT,
                        gpa REAL,
                        rank INTEGER,
                        class_rank INTEGER,
                        is_absent INTEGER DEFAULT 0,
                        is_exempt INTEGER DEFAULT 0,
                        remark TEXT,
                        graded_by INTEGER,
                        graded_at TEXT,
                        created_at TEXT,
                        UNIQUE(exam_id, student_id, subject)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS exam_statistics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        exam_id TEXT NOT NULL,
                        subject TEXT,
                        total_students INTEGER DEFAULT 0,
                        actual_count INTEGER DEFAULT 0,
                        average_score REAL DEFAULT 0,
                        max_score REAL DEFAULT 0,
                        min_score REAL DEFAULT 0,
                        pass_count INTEGER DEFAULT 0,
                        pass_rate REAL DEFAULT 0,
                        excellent_count INTEGER DEFAULT 0,
                        excellent_rate REAL DEFAULT 0,
                        std_deviation REAL DEFAULT 0,
                        median_score REAL DEFAULT 0,
                        updated_at TEXT,
                        UNIQUE(exam_id, subject)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS score_warnings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id INTEGER NOT NULL,
                        exam_id TEXT NOT NULL,
                        subject TEXT,
                        warning_type TEXT NOT NULL,
                        warning_value REAL,
                        threshold REAL,
                        description TEXT,
                        is_resolved INTEGER DEFAULT 0,
                        resolved_at TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS report_cards (
                        report_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        semester TEXT NOT NULL,
                        education_type TEXT,
                        grade_level INTEGER,
                        class_id TEXT,
                        subjects_data TEXT,
                        total_score REAL,
                        average_score REAL,
                        total_gpa REAL,
                        class_rank INTEGER,
                        grade_rank INTEGER,
                        teacher_comment TEXT,
                        head_teacher_comment TEXT,
                        generated_at TEXT,
                        is_published INTEGER DEFAULT 0
                    )
                ''')
                conn.commit()
                logger.info('考试与成绩管理服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    def create_exam(self, exam_name: str, education_type: str, exam_type: str, **kwargs) -> Dict[str, Any]:
        try:
            exam_id = f"exam_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            exam_type_config = EXAM_TYPES.get(exam_type, {})
            full_score = kwargs.get('full_score', exam_type_config.get('full_score', 100))
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO exams (
                            exam_id, exam_name, education_type, exam_type, subject,
                            grade_level, class_id, full_score, pass_score,
                            exam_date, duration_minutes, location, supervisor,
                            status, description, created_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        exam_id, exam_name, education_type, exam_type,
                        kwargs.get('subject'), kwargs.get('grade_level'),
                        kwargs.get('class_id'), full_score,
                        kwargs.get('pass_score', 60),
                        kwargs.get('exam_date'), kwargs.get('duration_minutes', 90),
                        kwargs.get('location'), kwargs.get('supervisor'),
                        kwargs.get('status', 'draft'), kwargs.get('description'),
                        kwargs.get('created_by'), now, now
                    ))
                    if kwargs.get('subjects'):
                        for subj in kwargs['subjects']:
                            cursor.execute('''
                                INSERT OR IGNORE INTO exam_subjects (
                                    exam_id, subject, full_score, pass_score, duration_minutes, exam_date
                                ) VALUES (?, ?, ?, ?, ?, ?)
                            ''', (exam_id, subj.get('name'),
                                  subj.get('full_score', full_score),
                                  subj.get('pass_score', 60),
                                  subj.get('duration_minutes', 90),
                                  subj.get('exam_date')))
                    conn.commit()
                    logger.info(f'创建考试: {exam_name} ({exam_id})')
                    return {'success': True, 'exam_id': exam_id, 'exam_name': exam_name}
        except Exception as e:
            logger.error(f'创建考试失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_exam(self, exam_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM exams WHERE exam_id = ?', (exam_id,))
                row = cursor.fetchone()
                if row:
                    exam = dict(row)
                    cursor.execute('SELECT * FROM exam_subjects WHERE exam_id = ?', (exam_id,))
                    exam['subjects'] = [dict(s) for s in cursor.fetchall()]
                    return exam
                return None
        except Exception as e:
            logger.error(f'获取考试失败: {e}')
            return None

    def list_exams(self, education_type: str = None, exam_type: str = None,
                   status: str = None, class_id: str = None,
                   page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM exams WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if exam_type:
                    query += ' AND exam_type = ?'
                    params.append(exam_type)
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
                exams = [dict(e) for e in cursor.fetchall()]
                return {'success': True, 'exams': exams, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取考试列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_exam_status(self, exam_id: str, status: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE exams SET status = ?, updated_at = ? WHERE exam_id = ?', (status, now, exam_id))
                    conn.commit()
                    logger.info(f'更新考试状态: {exam_id} -> {status}')
                    return {'success': True}
        except Exception as e:
            logger.error(f'更新考试状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def input_score(self, exam_id: str, student_id: int, subject: str,
                     score: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            grade = self._calculate_grade(score, kwargs.get('full_score', 100))
            gpa = GRADE_LEVELS.get(grade, {}).get('gpa', 0.0)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO exam_scores (
                            exam_id, student_id, subject, score, grade, gpa,
                            is_absent, is_exempt, remark, graded_by, graded_at, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(exam_id, student_id, subject) DO UPDATE SET
                            score = excluded.score,
                            grade = excluded.grade,
                            gpa = excluded.gpa,
                            is_absent = excluded.is_absent,
                            is_exempt = excluded.is_exempt,
                            remark = excluded.remark,
                            graded_by = excluded.graded_by,
                            graded_at = excluded.graded_at
                    ''', (exam_id, student_id, subject, score, grade, gpa,
                          kwargs.get('is_absent', 0), kwargs.get('is_exempt', 0),
                          kwargs.get('remark'), kwargs.get('graded_by'), now, now))
                    conn.commit()
                    return {'success': True, 'grade': grade, 'gpa': gpa}
        except Exception as e:
            logger.error(f'录入成绩失败: {e}')
            return {'success': False, 'error': str(e)}

    def batch_input_scores(self, exam_id: str, subject: str,
                            scores: List[Dict[str, Any]]) -> Dict[str, Any]:
        try:
            success_count = 0
            fail_count = 0
            for item in scores:
                result = self.input_score(
                    exam_id, item['student_id'], subject,
                    item['score'], **{k: v for k, v in item.items() if k != 'student_id'}
                )
                if result.get('success'):
                    success_count += 1
                else:
                    fail_count += 1
            logger.info(f'批量录入成绩: {exam_id}/{subject}, 成功{success_count}条, 失败{fail_count}条')
            return {'success': True, 'success_count': success_count, 'fail_count': fail_count}
        except Exception as e:
            logger.error(f'批量录入成绩失败: {e}')
            return {'success': False, 'error': str(e)}

    def _calculate_grade(self, score: float, full_score: float = 100) -> str:
        percentage = score / full_score * 100 if full_score > 0 else 0
        for grade, info in GRADE_LEVELS.items():
            low, high = info['score_range']
            if low <= percentage <= high:
                return grade
        return 'F'

    def get_student_scores(self, student_id: int, exam_id: str = None,
                            semester: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = '''
                    SELECT es.*, e.exam_name, e.exam_type, e.education_type, e.exam_date
                    FROM exam_scores es
                    JOIN exams e ON es.exam_id = e.exam_id
                    WHERE es.student_id = ?
                '''
                params = [student_id]
                if exam_id:
                    query += ' AND es.exam_id = ?'
                    params.append(exam_id)
                if semester:
                    query += ' AND e.exam_date LIKE ?'
                    params.append(f'{semester}%')
                query += ' ORDER BY e.exam_date DESC'
                cursor.execute(query, params)
                scores = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'scores': scores, 'count': len(scores)}
        except Exception as e:
            logger.error(f'获取学生成绩失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_exam_scores(self, exam_id: str, subject: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM exam_scores WHERE exam_id = ?'
                params = [exam_id]
                if subject:
                    query += ' AND subject = ?'
                    params.append(subject)
                query += ' ORDER BY score DESC'
                cursor.execute(query, params)
                scores = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'scores': scores, 'count': len(scores)}
        except Exception as e:
            logger.error(f'获取考试成绩失败: {e}')
            return {'success': False, 'error': str(e)}

    def calculate_statistics(self, exam_id: str, subject: str = None) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    subjects_to_calc = []
                    if subject:
                        subjects_to_calc = [subject]
                    else:
                        cursor.execute('SELECT DISTINCT subject FROM exam_scores WHERE exam_id = ?', (exam_id,))
                        subjects_to_calc = [r[0] for r in cursor.fetchall()]
                    results = []
                    for subj in subjects_to_calc:
                        cursor.execute('''
                            SELECT score FROM exam_scores
                            WHERE exam_id = ? AND subject = ? AND is_absent = 0 AND is_exempt = 0
                        ''', (exam_id, subj))
                        scores = [r[0] for r in cursor.fetchall() if r[0] is not None]
                        if not scores:
                            continue
                        scores_sorted = sorted(scores, reverse=True)
                        total = len(scores)
                        avg = sum(scores) / total
                        max_score = max(scores)
                        min_score = min(scores)
                        pass_count = sum(1 for s in scores if s >= 60)
                        excellent_count = sum(1 for s in scores if s >= 90)
                        median = scores_sorted[total // 2] if total % 2 == 1 else (scores_sorted[total // 2 - 1] + scores_sorted[total // 2]) / 2
                        variance = sum((s - avg) ** 2 for s in scores) / total
                        std_dev = variance ** 0.5
                        now = datetime.now().isoformat()
                        cursor.execute('''
                            INSERT INTO exam_statistics (
                                exam_id, subject, total_students, actual_count,
                                average_score, max_score, min_score,
                                pass_count, pass_rate, excellent_count, excellent_rate,
                                std_deviation, median_score, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(exam_id, subject) DO UPDATE SET
                                total_students = excluded.total_students,
                                actual_count = excluded.actual_count,
                                average_score = excluded.average_score,
                                max_score = excluded.max_score,
                                min_score = excluded.min_score,
                                pass_count = excluded.pass_count,
                                pass_rate = excluded.pass_rate,
                                excellent_count = excluded.excellent_count,
                                excellent_rate = excluded.excellent_rate,
                                std_deviation = excluded.std_deviation,
                                median_score = excluded.median_score,
                                updated_at = excluded.updated_at
                        ''', (exam_id, subj, total, total, round(avg, 2), max_score, min_score,
                              pass_count, round(pass_count / total * 100, 2),
                              excellent_count, round(excellent_count / total * 100, 2),
                              round(std_dev, 2), round(median, 2), now))
                        results.append({
                            'subject': subj,
                            'average': round(avg, 2),
                            'max': max_score,
                            'min': min_score,
                            'pass_rate': round(pass_count / total * 100, 2),
                            'excellent_rate': round(excellent_count / total * 100, 2),
                            'std_dev': round(std_dev, 2),
                            'median': round(median, 2)
                        })
                    self._calculate_ranks(cursor, exam_id, subjects_to_calc)
                    conn.commit()
                    logger.info(f'计算考试统计: {exam_id}, {len(results)}个科目')
                    return {'success': True, 'statistics': results}
        except Exception as e:
            logger.error(f'计算考试统计失败: {e}')
            return {'success': False, 'error': str(e)}

    def _calculate_ranks(self, cursor, exam_id: str, subjects: list):
        for subj in subjects:
            cursor.execute('''
                SELECT id, student_id, score FROM exam_scores
                WHERE exam_id = ? AND subject = ? AND is_absent = 0 AND is_exempt = 0
                ORDER BY score DESC
            ''', (exam_id, subj))
            rows = cursor.fetchall()
            for rank, (row_id, student_id, score) in enumerate(rows, 1):
                cursor.execute('UPDATE exam_scores SET rank = ? WHERE id = ?', (rank, row_id))

    def get_statistics(self, exam_id: str, subject: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM exam_statistics WHERE exam_id = ?'
                params = [exam_id]
                if subject:
                    query += ' AND subject = ?'
                    params.append(subject)
                cursor.execute(query, params)
                stats = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'statistics': stats}
        except Exception as e:
            logger.error(f'获取考试统计失败: {e}')
            return {'success': False, 'error': str(e)}

    def generate_warnings(self, exam_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            warnings_created = 0
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT student_id, subject, score FROM exam_scores WHERE exam_id = ? AND is_absent = 0', (exam_id,))
                    scores = cursor.fetchall()
                    for student_id, subject, score in scores:
                        if score is not None and score < 60:
                            cursor.execute('''
                                INSERT INTO score_warnings (
                                    student_id, exam_id, subject, warning_type,
                                    warning_value, threshold, description, created_at
                                ) VALUES (?, ?, ?, 'fail_risk', ?, 60, ?, ?)
                            ''', (student_id, exam_id, subject, score,
                                  f'{subject}成绩{score}分，低于及格线60分', now))
                            warnings_created += 1
                    cursor.execute('''
                        SELECT es.student_id, es.subject, es.score
                        FROM exam_scores es
                        JOIN exams e ON es.exam_id = e.exam_id
                        WHERE es.exam_id = ? AND es.is_absent = 0
                    ''', (exam_id,))
                    conn.commit()
                    logger.info(f'生成成绩预警: {exam_id}, {warnings_created}条')
                    return {'success': True, 'warnings_created': warnings_created}
        except Exception as e:
            logger.error(f'生成成绩预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_student_warnings(self, student_id: int, resolved: int = 0) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT sw.*, e.exam_name
                    FROM score_warnings sw
                    LEFT JOIN exams e ON sw.exam_id = e.exam_id
                    WHERE sw.student_id = ? AND sw.is_resolved = ?
                    ORDER BY sw.created_at DESC
                ''', (student_id, resolved))
                warnings = [dict(w) for w in cursor.fetchall()]
                return {'success': True, 'warnings': warnings, 'count': len(warnings)}
        except Exception as e:
            logger.error(f'获取学生预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def generate_report_card(self, student_id: int, semester: str,
                              education_type: str = None, **kwargs) -> Dict[str, Any]:
        try:
            report_id = f"rpt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    query = '''
                        SELECT es.subject, es.score, es.grade, es.gpa, es.rank, e.exam_name, e.exam_type
                        FROM exam_scores es
                        JOIN exams e ON es.exam_id = e.exam_id
                        WHERE es.student_id = ? AND e.exam_date LIKE ?
                    '''
                    params = [student_id, f'{semester}%']
                    if education_type:
                        query += ' AND e.education_type = ?'
                        params.append(education_type)
                    cursor.execute(query, params)
                    all_scores = [dict(s) for s in cursor.fetchall()]
                    subjects_data = {}
                    for s in all_scores:
                        subj = s['subject']
                        if subj not in subjects_data:
                            subjects_data[subj] = {'scores': [], 'best_score': 0, 'best_grade': ''}
                        subjects_data[subj]['scores'].append({
                            'exam_name': s['exam_name'],
                            'exam_type': s['exam_type'],
                            'score': s['score'],
                            'grade': s['grade'],
                            'gpa': s['gpa'],
                            'rank': s['rank']
                        })
                        if s['score'] and s['score'] > subjects_data[subj]['best_score']:
                            subjects_data[subj]['best_score'] = s['score']
                            subjects_data[subj]['best_grade'] = s['grade']
                    total_score = sum(v['best_score'] for v in subjects_data.values())
                    avg_score = total_score / len(subjects_data) if subjects_data else 0
                    total_gpa = sum(GRADE_LEVELS.get(v['best_grade'], {}).get('gpa', 0) for v in subjects_data.values())
                    cursor.execute('''
                        INSERT INTO report_cards (
                            report_id, student_id, semester, education_type,
                            grade_level, class_id, subjects_data, total_score,
                            average_score, total_gpa, teacher_comment,
                            head_teacher_comment, generated_at, is_published
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                    ''', (report_id, student_id, semester, education_type,
                          kwargs.get('grade_level'), kwargs.get('class_id'),
                          json.dumps(subjects_data, ensure_ascii=False),
                          round(total_score, 2), round(avg_score, 2), round(total_gpa, 2),
                          kwargs.get('teacher_comment'), kwargs.get('head_teacher_comment'), now))
                    conn.commit()
                    logger.info(f'生成成绩单: {report_id}')
                    return {
                        'success': True,
                        'report_id': report_id,
                        'total_score': round(total_score, 2),
                        'average_score': round(avg_score, 2),
                        'total_gpa': round(total_gpa, 2),
                        'subject_count': len(subjects_data)
                    }
        except Exception as e:
            logger.error(f'生成成绩单失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_report_card(self, report_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM report_cards WHERE report_id = ?', (report_id,))
                row = cursor.fetchone()
                if row:
                    report = dict(row)
                    if report.get('subjects_data'):
                        report['subjects_data'] = json.loads(report['subjects_data'])
                    return report
                return None
        except Exception as e:
            logger.error(f'获取成绩单失败: {e}')
            return None

    def publish_report_card(self, report_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE report_cards SET is_published = 1 WHERE report_id = ?', (report_id,))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'发布成绩单失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_class_ranking(self, exam_id: str, subject: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = '''
                    SELECT es.student_id, es.subject, es.score, es.grade, es.rank
                    FROM exam_scores es
                    WHERE es.exam_id = ? AND es.is_absent = 0 AND es.is_exempt = 0
                '''
                params = [exam_id]
                if subject:
                    query += ' AND es.subject = ?'
                    params.append(subject)
                query += ' ORDER BY es.rank ASC'
                cursor.execute(query, params)
                rankings = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'rankings': rankings, 'count': len(rankings)}
        except Exception as e:
            logger.error(f'获取班级排名失败: {e}')
            return {'success': False, 'error': str(e)}
