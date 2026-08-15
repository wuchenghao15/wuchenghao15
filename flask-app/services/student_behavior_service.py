#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 学生行为与品德管理服务 (v15.3.0)
====================================
提供学生行为记录、品德评定、奖惩管理和行为分析等综合服务。

核心能力：
1. 行为记录 - 日常行为记录、分类管理
2. 品德评定 - 多维度品德评分与评定
3. 奖惩管理 - 奖励与处分记录
4. 行为分析 - 行为趋势分析、异常预警
5. 品德档案 - 学生品德成长档案
6. 行为积分 - 行为积分制管理
7. 成人品德 - 成人教育职业素养管理
8. K12品德 - 九年制义务教育品德发展
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'student_behavior_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('StudentBehavior')


# ========== 行为配置 ==========

# 行为类型
BEHAVIOR_TYPES = {
    'positive': {'name': '正面行为', 'color': '#52c41a', 'score_effect': 1},
    'negative': {'name': '负面行为', 'color': '#f5222d', 'score_effect': -1},
    'neutral': {'name': '中性记录', 'color': '#1890ff', 'score_effect': 0}
}

# 行为分类
BEHAVIOR_CATEGORIES = {
    'discipline': {'name': '纪律', 'description': '课堂纪律、校规遵守'},
    'learning': {'name': '学习', 'description': '学习态度、课堂参与'},
    'social': {'name': '社交', 'description': '同学关系、团队合作'},
    'labor': {'name': '劳动', 'description': '值日、劳动表现'},
    'hygiene': {'name': '卫生', 'description': '个人卫生、环境卫生'},
    'safety': {'name': '安全', 'description': '安全意识、安全行为'},
    'integrity': {'name': '诚信', 'description': '诚实守信、考试诚信'},
    'respect': {'name': '礼貌', 'description': '尊师重道、文明礼貌'},
    'activity': {'name': '活动', 'description': '课外活动、社团参与'},
    'attendance': {'name': '考勤', 'description': '出勤、迟到、早退'}
}

# 正面行为明细
POSITIVE_BEHAVIORS = {
    'help_others': {'name': '乐于助人', 'category': 'social', 'score': 5, 'description': '主动帮助同学'},
    'active_answer': {'name': '积极发言', 'category': 'learning', 'score': 3, 'description': '课堂积极回答问题'},
    'homework_excellent': {'name': '作业优秀', 'category': 'learning', 'score': 3, 'description': '作业完成质量高'},
    'leadership': {'name': '领导表现', 'category': 'social', 'score': 5, 'description': '在团队中发挥领导作用'},
    'volunteer': {'name': '志愿服务', 'category': 'activity', 'score': 5, 'description': '参加志愿服务活动'},
    'competition_award': {'name': '竞赛获奖', 'category': 'activity', 'score': 10, 'description': '在竞赛中获得奖项'},
    'honesty': {'name': '诚实守信', 'category': 'integrity', 'score': 5, 'description': '拾金不昧、信守承诺'},
    'class_duty': {'name': '值日认真', 'category': 'labor', 'score': 2, 'description': '认真完成值日工作'},
    'improvement': {'name': '进步明显', 'category': 'learning', 'score': 5, 'description': '学习成绩或行为明显进步'},
    'creativity': {'name': '创新表现', 'category': 'learning', 'score': 5, 'description': '有创新思维或创意表现'}
}

# 负面行为明细
NEGATIVE_BEHAVIORS = {
    'late': {'name': '迟到', 'category': 'attendance', 'score': -2, 'description': '上课迟到'},
    'early_leave': {'name': '早退', 'category': 'attendance', 'score': -3, 'description': '未经批准提前离开'},
    'absent': {'name': '旷课', 'category': 'attendance', 'score': -5, 'description': '无故缺席课程'},
    'classroom_disruption': {'name': '课堂违纪', 'category': 'discipline', 'score': -3, 'description': '扰乱课堂秩序'},
    'homework_miss': {'name': '未交作业', 'category': 'learning', 'score': -2, 'description': '未按时提交作业'},
    'cheating': {'name': '考试作弊', 'category': 'integrity', 'score': -10, 'description': '考试中作弊行为'},
    'fighting': {'name': '打架斗殴', 'category': 'discipline', 'score': -10, 'description': '与同学发生肢体冲突'},
    'bullying': {'name': '欺凌行为', 'category': 'social', 'score': -10, 'description': '欺凌或排挤同学'},
    'disrespect': {'name': '不尊重师长', 'category': 'respect', 'score': -5, 'description': '对老师不礼貌'},
    'property_damage': {'name': '损坏公物', 'category': 'discipline', 'score': -5, 'description': '故意损坏学校财物'},
    'littering': {'name': '乱扔垃圾', 'category': 'hygiene', 'score': -1, 'description': '随地吐痰或乱扔垃圾'},
    'safety_violation': {'name': '安全违规', 'category': 'safety', 'score': -5, 'description': '违反安全规定'}
}

# 奖励类型
REWARD_TYPES = {
    'oral_praise': {'name': '口头表扬', 'level': 1, 'score': 5},
    'written_praise': {'name': '书面表扬', 'level': 2, 'score': 10},
    'class_award': {'name': '班级奖励', 'level': 2, 'score': 10},
    'grade_award': {'name': '年级奖励', 'level': 3, 'score': 20},
    'school_award': {'name': '校级奖励', 'level': 4, 'score': 30},
    'honor_title': {'name': '荣誉称号', 'level': 4, 'score': 30},
    'scholarship': {'name': '奖学金', 'level': 5, 'score': 50}
}

# 处分类型
PUNISHMENT_TYPES = {
    'oral_warning': {'name': '口头警告', 'level': 1, 'score': -5},
    'written_warning': {'name': '书面警告', 'level': 2, 'score': -10},
    'class_criticism': {'name': '班级批评', 'level': 2, 'score': -10},
    'grade_criticism': {'name': '年级批评', 'level': 3, 'score': -20},
    'school_criticism': {'name': '校级通报批评', 'level': 3, 'score': -30},
    'disciplinary_warning': {'name': '记过处分', 'level': 4, 'score': -40},
    'major_demerit': {'name': '记大过处分', 'level': 5, 'score': -50},
    'probation': {'name': '留校察看', 'level': 5, 'score': -50}
}

# 品德评定维度
MORAL_DIMENSIONS = {
    'ideological': {'name': '思想品德', 'weight': 0.2, 'description': '政治思想、价值观念'},
    'academic_ethics': {'name': '学习品德', 'weight': 0.2, 'description': '学习态度、学术诚信'},
    'social_ethics': {'name': '社会公德', 'weight': 0.2, 'description': '文明礼貌、公共意识'},
    'teamwork': {'name': '团队协作', 'weight': 0.15, 'description': '合作精神、集体荣誉'},
    'labor_attitude': {'name': '劳动态度', 'weight': 0.1, 'description': '劳动观念、实践能力'},
    'innovation': {'name': '创新精神', 'weight': 0.15, 'description': '创新思维、探索精神'}
}

# 品德等级
MORAL_GRADES = {
    'excellent': {'name': '优秀', 'score_range': [90, 100], 'color': '#52c41a'},
    'good': {'name': '良好', 'score_range': [80, 89], 'color': '#1890ff'},
    'fair': {'name': '合格', 'score_range': [60, 79], 'color': '#faad14'},
    'poor': {'name': '待改进', 'score_range': [0, 59], 'color': '#f5222d'}
}


class StudentBehaviorService:
    """学生行为与品德管理服务"""

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
                    CREATE TABLE IF NOT EXISTS behavior_records (
                        record_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
        behavior_type TEXT NOT NULL,
                        category TEXT,
                        behavior_code TEXT,
                        description TEXT,
                        score_change REAL DEFAULT 0,
                        record_date TEXT,
                        recorded_by INTEGER,
                        recorded_by_name TEXT,
                        class_id TEXT,
                        education_type TEXT,
                        location TEXT,
                        witnesses TEXT,
                        attachments TEXT,
                        remark TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS behavior_scores (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id INTEGER NOT NULL,
                        semester TEXT NOT NULL,
                        total_score REAL DEFAULT 100,
                        positive_count INTEGER DEFAULT 0,
                        negative_count INTEGER DEFAULT 0,
                        positive_score REAL DEFAULT 0,
                        negative_score REAL DEFAULT 0,
                        reward_count INTEGER DEFAULT 0,
                        punishment_count INTEGER DEFAULT 0,
                        moral_grade TEXT,
                        updated_at TEXT,
                        UNIQUE(student_id, semester)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS reward_records (
                        reward_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        reward_type TEXT NOT NULL,
                        reward_name TEXT,
                        description TEXT,
                        score_change REAL DEFAULT 0,
                        reward_date TEXT,
                        awarded_by INTEGER,
                        awarded_by_name TEXT,
                        semester TEXT,
                        is_revoked INTEGER DEFAULT 0,
                        revoked_at TEXT,
                        revoke_reason TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS punishment_records (
                        punishment_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        punishment_type TEXT NOT NULL,
                        punishment_name TEXT,
                        description TEXT,
                        score_change REAL DEFAULT 0,
                        punishment_date TEXT,
                        issued_by INTEGER,
                        issued_by_name TEXT,
                        semester TEXT,
                        duration_days INTEGER,
                        is_active INTEGER DEFAULT 1,
                        is_revoked INTEGER DEFAULT 0,
                        revoked_at TEXT,
                        revoke_reason TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS moral_evaluations (
                        evaluation_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        semester TEXT NOT NULL,
                        dimensions TEXT NOT NULL,
                        total_score REAL,
                        grade TEXT,
                        evaluator_id INTEGER,
                        evaluator_name TEXT,
                        teacher_comment TEXT,
                        student_self_eval TEXT,
                        parent_feedback TEXT,
                        class_id TEXT,
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS moral_archive (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id INTEGER NOT NULL,
                        semester TEXT NOT NULL,
                        academic_year TEXT,
                        behavior_score REAL,
                        moral_grade TEXT,
                        reward_count INTEGER DEFAULT 0,
                        punishment_count INTEGER DEFAULT 0,
                        summary TEXT,
                        created_at TEXT,
                        UNIQUE(student_id, semester)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS behavior_warnings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id INTEGER NOT NULL,
                        warning_type TEXT NOT NULL,
                        description TEXT,
                        threshold REAL,
                        current_value REAL,
                        is_resolved INTEGER DEFAULT 0,
                        resolved_at TEXT,
                        created_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('学生行为与品德管理服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    def record_behavior(self, student_id: int, behavior_type: str,
                         description: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"bhv_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            score_change = 0
            behavior_code = kwargs.get('behavior_code')
            if behavior_code:
                if behavior_type == 'positive' and behavior_code in POSITIVE_BEHAVIORS:
                    score_change = POSITIVE_BEHAVIORS[behavior_code]['score']
                elif behavior_type == 'negative' and behavior_code in NEGATIVE_BEHAVIORS:
                    score_change = NEGATIVE_BEHAVIORS[behavior_code]['score']
            witnesses = json.dumps(kwargs.get('witnesses'), ensure_ascii=False) if kwargs.get('witnesses') else None
            attachments = json.dumps(kwargs.get('attachments'), ensure_ascii=False) if kwargs.get('attachments') else None
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO behavior_records (
                            record_id, student_id, behavior_type, category, behavior_code,
                            description, score_change, record_date, recorded_by,
                            recorded_by_name, class_id, education_type, location,
                            witnesses, attachments, remark, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (record_id, student_id, behavior_type,
                          kwargs.get('category'), behavior_code, description,
                          score_change, kwargs.get('record_date', now[:10]),
                          kwargs.get('recorded_by'), kwargs.get('recorded_by_name'),
                          kwargs.get('class_id'), kwargs.get('education_type'),
                          kwargs.get('location'), witnesses, attachments,
                          kwargs.get('remark'), now))
                    self._update_behavior_score(cursor, student_id, behavior_type, score_change)
                    conn.commit()
                    logger.info(f'记录行为: {record_id}, 学生{student_id}')
                    return {'success': True, 'record_id': record_id, 'score_change': score_change}
        except Exception as e:
            logger.error(f'记录行为失败: {e}')
            return {'success': False, 'error': str(e)}

    def _update_behavior_score(self, cursor, student_id: int, behavior_type: str, score_change: float):
        semester = self._get_current_semester()
        now = datetime.now().isoformat()
        cursor.execute('SELECT id, total_score, positive_count, negative_count, positive_score, negative_score FROM behavior_scores WHERE student_id = ? AND semester = ?', (student_id, semester))
        row = cursor.fetchone()
        if row:
            score_id, total, pos_cnt, neg_cnt, pos_score, neg_score = row
            total += score_change
            if behavior_type == 'positive':
                pos_cnt += 1
                pos_score += score_change
            elif behavior_type == 'negative':
                neg_cnt += 1
                neg_score += abs(score_change)
            cursor.execute('''
                UPDATE behavior_scores SET total_score = ?, positive_count = ?, negative_count = ?,
                    positive_score = ?, negative_score = ?, updated_at = ?
                WHERE id = ?
            ''', (round(total, 2), pos_cnt, neg_cnt, round(pos_score, 2),
                  round(neg_score, 2), now, score_id))
        else:
            total = 100 + score_change
            pos_cnt = 1 if behavior_type == 'positive' else 0
            neg_cnt = 1 if behavior_type == 'negative' else 0
            pos_score = score_change if behavior_type == 'positive' else 0
            neg_score = abs(score_change) if behavior_type == 'negative' else 0
            cursor.execute('''
                INSERT INTO behavior_scores (student_id, semester, total_score, positive_count,
                    negative_count, positive_score, negative_score, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (student_id, semester, round(total, 2), pos_cnt, neg_cnt,
                  round(pos_score, 2), round(neg_score, 2), now))

    def _get_current_semester(self) -> str:
        now = datetime.now()
        year = now.year
        month = now.month
        if month >= 9 or month <= 1:
            return f"{year}-{year+1}-1" if month <= 1 else f"{year}-{year+1}-1"
        else:
            return f"{year-1}-{year}-2"

    def record_reward(self, student_id: int, reward_type: str,
                       description: str, **kwargs) -> Dict[str, Any]:
        try:
            reward_id = f"rwd_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            reward_config = REWARD_TYPES.get(reward_type, {})
            score_change = reward_config.get('score', 0)
            semester = kwargs.get('semester', self._get_current_semester())
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO reward_records (
                            reward_id, student_id, reward_type, reward_name, description,
                            score_change, reward_date, awarded_by, awarded_by_name,
                            semester, is_revoked, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                    ''', (reward_id, student_id, reward_type,
                          reward_config.get('name', ''), description, score_change,
                          kwargs.get('reward_date', now[:10]),
                          kwargs.get('awarded_by'), kwargs.get('awarded_by_name'),
                          semester, now))
                    cursor.execute('''
                        UPDATE behavior_scores SET reward_count = reward_count + 1,
                            total_score = total_score + ?, updated_at = ?
                        WHERE student_id = ? AND semester = ?
                    ''', (score_change, now, student_id, semester))
                    if cursor.rowcount == 0:
                        cursor.execute('''
                            INSERT INTO behavior_scores (student_id, semester, total_score, reward_count, updated_at)
                            VALUES (?, ?, ?, 1, ?)
                        ''', (student_id, semester, 100 + score_change, now))
                    conn.commit()
                    logger.info(f'记录奖励: {reward_id}')
                    return {'success': True, 'reward_id': reward_id, 'score_change': score_change}
        except Exception as e:
            logger.error(f'记录奖励失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_punishment(self, student_id: int, punishment_type: str,
                           description: str, **kwargs) -> Dict[str, Any]:
        try:
            punishment_id = f"psh_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            punishment_config = PUNISHMENT_TYPES.get(punishment_type, {})
            score_change = punishment_config.get('score', 0)
            semester = kwargs.get('semester', self._get_current_semester())
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO punishment_records (
                            punishment_id, student_id, punishment_type, punishment_name,
                            description, score_change, punishment_date, issued_by,
                            issued_by_name, semester, duration_days, is_active, is_revoked, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0, ?)
                    ''', (punishment_id, student_id, punishment_type,
                          punishment_config.get('name', ''), description, score_change,
                          kwargs.get('punishment_date', now[:10]),
                          kwargs.get('issued_by'), kwargs.get('issued_by_name'),
                          semester, kwargs.get('duration_days'), now))
                    cursor.execute('''
                        UPDATE behavior_scores SET punishment_count = punishment_count + 1,
                            total_score = total_score + ?, updated_at = ?
                        WHERE student_id = ? AND semester = ?
                    ''', (score_change, now, student_id, semester))
                    if cursor.rowcount == 0:
                        cursor.execute('''
                            INSERT INTO behavior_scores (student_id, semester, total_score, punishment_count, updated_at)
                            VALUES (?, ?, ?, 1, ?)
                        ''', (student_id, semester, 100 + score_change, now))
                    conn.commit()
                    logger.info(f'记录处分: {punishment_id}')
                    return {'success': True, 'punishment_id': punishment_id, 'score_change': score_change}
        except Exception as e:
            logger.error(f'记录处分失败: {e}')
            return {'success': False, 'error': str(e)}

    def revoke_punishment(self, punishment_id: str, reason: str = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE punishment_records SET is_revoked = 1, is_active = 0,
                            revoked_at = ?, revoke_reason = ?
                        WHERE punishment_id = ? AND is_revoked = 0
                    ''', (now, reason, punishment_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'撤销处分失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_behavior_records(self, student_id: int, behavior_type: str = None,
                              category: str = None, start_date: str = None,
                              end_date: str = None, page: int = 1,
                              page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM behavior_records WHERE student_id = ?'
                params = [student_id]
                if behavior_type:
                    query += ' AND behavior_type = ?'
                    params.append(behavior_type)
                if category:
                    query += ' AND category = ?'
                    params.append(category)
                if start_date:
                    query += ' AND record_date >= ?'
                    params.append(start_date)
                if end_date:
                    query += ' AND record_date <= ?'
                    params.append(end_date)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取行为记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_behavior_score(self, student_id: int, semester: str = None) -> Dict[str, Any]:
        try:
            semester = semester or self._get_current_semester()
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM behavior_scores WHERE student_id = ? AND semester = ?', (student_id, semester))
                row = cursor.fetchone()
                if row:
                    score = dict(row)
                    grade = self._get_moral_grade(score['total_score'])
                    return {'success': True, 'score': score, 'grade': grade}
                return {'success': True, 'score': None, 'grade': None, 'default_score': 100}
        except Exception as e:
            logger.error(f'获取行为分数失败: {e}')
            return {'success': False, 'error': str(e)}

    def _get_moral_grade(self, score: float) -> dict:
        for grade, info in MORAL_GRADES.items():
            low, high = info['score_range']
            if low <= score <= high:
                return {'grade': grade, **info}
        return {'grade': 'poor', **MORAL_GRADES['poor']}

    def evaluate_moral(self, student_id: int, semester: str, dimensions: dict,
                        **kwargs) -> Dict[str, Any]:
        try:
            evaluation_id = f"mev_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            total_score = self._calculate_moral_score(dimensions)
            grade = self._get_moral_grade(total_score)
            dims_json = json.dumps(dimensions, ensure_ascii=False)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO moral_evaluations (
                            evaluation_id, student_id, semester, dimensions,
                            total_score, grade, evaluator_id, evaluator_name,
                            teacher_comment, student_self_eval, parent_feedback,
                            class_id, education_type, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (evaluation_id, student_id, semester, dims_json,
                          round(total_score, 2), grade['grade'],
                          kwargs.get('evaluator_id'), kwargs.get('evaluator_name'),
                          kwargs.get('teacher_comment'), kwargs.get('student_self_eval'),
                          kwargs.get('parent_feedback'), kwargs.get('class_id'),
                          kwargs.get('education_type'), now, now))
                    cursor.execute('''
                        UPDATE behavior_scores SET moral_grade = ?, updated_at = ?
                        WHERE student_id = ? AND semester = ?
                    ''', (grade['grade'], now, student_id, semester))
                    conn.commit()
                    logger.info(f'品德评定: {evaluation_id}, 得分{total_score}')
                    return {'success': True, 'evaluation_id': evaluation_id,
                            'total_score': round(total_score, 2), 'grade': grade}
        except Exception as e:
            logger.error(f'品德评定失败: {e}')
            return {'success': False, 'error': str(e)}

    def _calculate_moral_score(self, dimensions: dict) -> float:
        total = 0
        for dim_code, score in dimensions.items():
            weight = MORAL_DIMENSIONS.get(dim_code, {}).get('weight', 0)
            total += score * weight
        return total

    def get_moral_evaluation(self, student_id: int, semester: str = None) -> Dict[str, Any]:
        try:
            semester = semester or self._get_current_semester()
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM moral_evaluations WHERE student_id = ? AND semester = ?', (student_id, semester))
                row = cursor.fetchone()
                if row:
                    eval_data = dict(row)
                    if eval_data.get('dimensions'):
                        eval_data['dimensions'] = json.loads(eval_data['dimensions'])
                    return {'success': True, 'evaluation': eval_data}
                return {'success': True, 'evaluation': None}
        except Exception as e:
            logger.error(f'获取品德评定失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_reward_records(self, student_id: int, semester: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM reward_records WHERE student_id = ? AND is_revoked = 0'
                params = [student_id]
                if semester:
                    query += ' AND semester = ?'
                    params.append(semester)
                query += ' ORDER BY reward_date DESC'
                cursor.execute(query, params)
                rewards = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'rewards': rewards, 'count': len(rewards)}
        except Exception as e:
            logger.error(f'获取奖励记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_punishment_records(self, student_id: int, active_only: bool = False) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM punishment_records WHERE student_id = ?'
                params = [student_id]
                if active_only:
                    query += ' AND is_active = 1 AND is_revoked = 0'
                query += ' ORDER BY punishment_date DESC'
                cursor.execute(query, params)
                punishments = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'punishments': punishments, 'count': len(punishments)}
        except Exception as e:
            logger.error(f'获取处分记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_behavior_summary(self, student_id: int, semester: str = None) -> Dict[str, Any]:
        try:
            semester = semester or self._get_current_semester()
            score_data = self.get_behavior_score(student_id, semester)
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT behavior_type, COUNT(*) as cnt, SUM(score_change) as total_score
                    FROM behavior_records WHERE student_id = ?
                    AND created_at >= ?
                    GROUP BY behavior_type
                ''', (student_id, f'{semester.split("-")[0]}-09-01' if '-' in semester else '2026-01-01'))
                type_stats = {r[0]: {'count': r[1], 'score': r[2]} for r in cursor.fetchall()}
                cursor.execute('''
                    SELECT category, COUNT(*) as cnt FROM behavior_records
                    WHERE student_id = ? GROUP BY category
                ''', (student_id,))
                cat_stats = {r[0]: r[1] for r in cursor.fetchall()}
                cursor.execute('SELECT COUNT(*) FROM reward_records WHERE student_id = ? AND semester = ? AND is_revoked = 0', (student_id, semester))
                reward_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM punishment_records WHERE student_id = ? AND is_active = 1 AND is_revoked = 0', (student_id,))
                active_punishments = cursor.fetchone()[0]
                return {
                    'success': True,
                    'score': score_data.get('score'),
                    'grade': score_data.get('grade'),
                    'by_type': type_stats,
                    'by_category': cat_stats,
                    'reward_count': reward_count,
                    'active_punishments': active_punishments
                }
        except Exception as e:
            logger.error(f'获取行为汇总失败: {e}')
            return {'success': False, 'error': str(e)}

    def generate_behavior_warnings(self) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            warnings_created = 0
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT student_id, total_score FROM behavior_scores WHERE semester = ?', (self._get_current_semester(),))
                    students = cursor.fetchall()
                    for student_id, score in students:
                        if score < 60:
                            cursor.execute('''
                                INSERT INTO behavior_warnings (
                                    student_id, warning_type, description,
                                    threshold, current_value, created_at
                                ) VALUES (?, 'low_score', ?, 60, ?, ?)
                            ''', (student_id, f'行为分数{score}分，低于及格线60分', score, now))
                            warnings_created += 1
                        if score < 80:
                            cursor.execute('''
                                INSERT INTO behavior_warnings (
                                    student_id, warning_type, description,
                                    threshold, current_value, created_at
                                ) VALUES (?, 'decline_risk', ?, 80, ?, ?)
                            ''', (student_id, f'行为分数{score}分，接近警戒线', score, now))
                            warnings_created += 1
                    conn.commit()
                    logger.info(f'生成行为预警: {warnings_created}条')
                    return {'success': True, 'warnings_created': warnings_created}
        except Exception as e:
            logger.error(f'生成行为预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_student_warnings(self, student_id: int, resolved: int = 0) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM behavior_warnings
                    WHERE student_id = ? AND is_resolved = ?
                    ORDER BY created_at DESC
                ''', (student_id, resolved))
                warnings = [dict(w) for w in cursor.fetchall()]
                return {'success': True, 'warnings': warnings, 'count': len(warnings)}
        except Exception as e:
            logger.error(f'获取学生行为预警失败: {e}')
            return {'success': False, 'error': str(e)}

    def archive_moral_record(self, student_id: int, semester: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            score_data = self.get_behavior_score(student_id, semester)
            score = score_data.get('score', {})
            total_score = score.get('total_score', 100) if score else 100
            moral_grade = score.get('moral_grade', '') if score else ''
            reward_count = score.get('reward_count', 0) if score else 0
            punishment_count = score.get('punishment_count', 0) if score else 0
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO moral_archive (
                            student_id, semester, academic_year, behavior_score,
                            moral_grade, reward_count, punishment_count, summary, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(student_id, semester) DO UPDATE SET
                            behavior_score = excluded.behavior_score,
                            moral_grade = excluded.moral_grade,
                            reward_count = excluded.reward_count,
                            punishment_count = excluded.punishment_count,
                            summary = excluded.summary
                    ''', (student_id, semester, kwargs.get('academic_year'),
                          round(total_score, 2), moral_grade,
                          reward_count, punishment_count,
                          kwargs.get('summary'), now))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'归档品德记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_moral_archive(self, student_id: int) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM moral_archive WHERE student_id = ? ORDER BY semester DESC', (student_id,))
                archives = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'archives': archives}
        except Exception as e:
            logger.error(f'获取品德档案失败: {e}')
            return {'success': False, 'error': str(e)}
