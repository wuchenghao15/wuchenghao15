#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育人才服务 (v15.29.0)
====================================
提供人才招聘、人才培养、人才评价、人才流动、人才激励、人才储备、人才服务和人才发展等综合管理服务。

核心能力：
1. 人才招聘 - 招聘管理、报名审核、录用流程、招聘统计
2. 人才培养 - 培训计划、培训实施、培训评估、培养跟踪
3. 人才评价 - 绩效评估、能力测评、360度评价、评价结果
4. 人才流动 - 内部流动、外部流动、岗位轮换、晋升管理、人才引进
5. 人才激励 - 薪酬激励、绩效激励、股权期权、荣誉表彰
6. 人才储备 - 后备干部、名师工作室、专家库、人才梯队
7. 人才服务 - 职业规划、心理咨询、法律援助、生活服务
8. 人才发展 - 发展路径、职业指导、继续教育、导师计划

支持成人教育和K12教育差异化管理。
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_talent_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationTalent')


# ========== 人才配置 ==========

RECRUITMENT_TYPES = {
    'campus': {'name': '校园招聘', 'target': '应届毕业生', 'education_types': ['adult', 'k12']},
    'social': {'name': '社会招聘', 'target': '有工作经验者', 'education_types': ['adult', 'k12']},
    'overseas': {'name': '海外招聘', 'target': '海外人才', 'education_types': ['adult']},
    'internal': {'name': '内部竞聘', 'target': '在职员工', 'education_types': ['adult', 'k12']},
    'headhunter': {'name': '猎头招聘', 'target': '高端人才', 'education_types': ['adult']},
    'online': {'name': '网络招聘', 'target': '广泛人才', 'education_types': ['adult', 'k12']},
    'on_site': {'name': '现场招聘', 'target': '本地人才', 'education_types': ['adult', 'k12']},
    'special': {'name': '专项招聘', 'target': '特定领域', 'education_types': ['adult', 'k12']}
}

TRAINING_TYPES = {
    'pre_job': {'name': '岗前培训', 'duration': '1-2周', 'education_types': ['adult', 'k12']},
    'on_job': {'name': '在职培训', 'duration': '持续进行', 'education_types': ['adult', 'k12']},
    'professional': {'name': '专业培训', 'duration': '2-4周', 'education_types': ['adult', 'k12']},
    'management': {'name': '管理培训', 'duration': '4-8周', 'education_types': ['adult']},
    'skill': {'name': '技能培训', 'duration': '1-3周', 'education_types': ['adult', 'k12']},
    'quality': {'name': '素质培训', 'duration': '1-2周', 'education_types': ['adult', 'k12']},
    'overseas': {'name': '海外培训', 'duration': '1-3个月', 'education_types': ['adult']},
    'custom': {'name': '定制培训', 'duration': '按需定制', 'education_types': ['adult', 'k12']}
}

EVALUATION_METHODS = {
    'performance': {'name': '绩效考核', 'frequency': '季度/年度', 'education_types': ['adult', 'k12']},
    'ability': {'name': '能力评估', 'frequency': '年度', 'education_types': ['adult', 'k12']},
    'three_sixty': {'name': '360度评估', 'frequency': '年度', 'education_types': ['adult']},
    'objective': {'name': '目标管理', 'frequency': '季度', 'education_types': ['adult', 'k12']},
    'behavior': {'name': '行为锚定', 'frequency': '半年度', 'education_types': ['adult', 'k12']},
    'kpi': {'name': '关键绩效', 'frequency': '月度/季度', 'education_types': ['adult', 'k12']},
    'balanced': {'name': '平衡计分', 'frequency': '年度', 'education_types': ['adult']},
    'comprehensive': {'name': '综合评价', 'frequency': '年度', 'education_types': ['adult', 'k12']}
}

FLOW_TYPES = {
    'internal': {'name': '内部流动', 'direction': '部门间', 'education_types': ['adult', 'k12']},
    'external': {'name': '外部流动', 'direction': '进出', 'education_types': ['adult', 'k12']},
    'cross_region': {'name': '跨区域流动', 'direction': '地区间', 'education_types': ['adult']},
    'international': {'name': '国际流动', 'direction': '国家间', 'education_types': ['adult']},
    'rotation': {'name': '岗位轮换', 'direction': '岗位间', 'education_types': ['adult', 'k12']},
    'promotion': {'name': '晋升调动', 'direction': '向上', 'education_types': ['adult', 'k12']},
    'resignation': {'name': '离职管理', 'direction': '流出', 'education_types': ['adult', 'k12']},
    'introduction': {'name': '人才引进', 'direction': '流入', 'education_types': ['adult', 'k12']}
}

INCENTIVE_TYPES = {
    'salary': {'name': '薪酬激励', 'form': '现金', 'education_types': ['adult', 'k12']},
    'performance': {'name': '绩效激励', 'form': '奖金', 'education_types': ['adult', 'k12']},
    'equity': {'name': '股权激励', 'form': '股权', 'education_types': ['adult']},
    'promotion': {'name': '晋升激励', 'form': '职位', 'education_types': ['adult', 'k12']},
    'honor': {'name': '荣誉激励', 'form': '荣誉', 'education_types': ['adult', 'k12']},
    'training': {'name': '培训激励', 'form': '学习', 'education_types': ['adult', 'k12']},
    'welfare': {'name': '福利激励', 'form': '福利', 'education_types': ['adult', 'k12']},
    'long_term': {'name': '长期激励', 'form': '期权', 'education_types': ['adult']}
}

RESERVE_TYPES = {
    'cadre': {'name': '后备干部', 'level': '管理', 'education_types': ['adult']},
    'young': {'name': '青年教师', 'level': '专业', 'education_types': ['adult', 'k12']},
    'backbone': {'name': '骨干教师', 'level': '专业', 'education_types': ['adult', 'k12']},
    'academic': {'name': '学科带头人', 'level': '学科', 'education_types': ['adult', 'k12']},
    'master': {'name': '名师工作室', 'level': '名师', 'education_types': ['adult', 'k12']},
    'expert': {'name': '专家库', 'level': '专家', 'education_types': ['adult']},
    'echelon': {'name': '人才梯队', 'level': '综合', 'education_types': ['adult', 'k12']},
    'international': {'name': '国际化人才', 'level': '高端', 'education_types': ['adult']}
}

SERVICE_TYPES = {
    'consulting': {'name': '人才咨询', 'provider': 'HR', 'education_types': ['adult', 'k12']},
    'career': {'name': '职业规划', 'provider': '导师', 'education_types': ['adult', 'k12']},
    'psychological': {'name': '心理咨询', 'provider': '咨询师', 'education_types': ['adult', 'k12']},
    'legal': {'name': '法律援助', 'provider': '律师', 'education_types': ['adult', 'k12']},
    'life': {'name': '生活服务', 'provider': '行政', 'education_types': ['adult', 'k12']},
    'health': {'name': '健康管理', 'provider': '医生', 'education_types': ['adult', 'k12']},
    'education': {'name': '子女教育', 'provider': '教育', 'education_types': ['adult']},
    'retirement': {'name': '退休服务', 'provider': 'HR', 'education_types': ['adult']}
}

DEVELOPMENT_PATHS = {
    'teaching': {'name': '教学型', 'focus': '教学能力', 'education_types': ['adult', 'k12']},
    'research': {'name': '科研型', 'focus': '科研能力', 'education_types': ['adult']},
    'management': {'name': '管理型', 'focus': '管理能力', 'education_types': ['adult']},
    'composite': {'name': '复合型', 'focus': '综合能力', 'education_types': ['adult', 'k12']},
    'expert': {'name': '专家型', 'focus': '专业深度', 'education_types': ['adult', 'k12']},
    'entrepreneur': {'name': '创业型', 'focus': '创新能力', 'education_types': ['adult']},
    'international': {'name': '国际化', 'focus': '全球视野', 'education_types': ['adult']},
    'diversified': {'name': '多元化', 'focus': '多领域', 'education_types': ['adult', 'k12']}
}


class EducationTalentService:
    """教育人才服务"""

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
                    CREATE TABLE IF NOT EXISTS talent_recruitment (
                        recruitment_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        recruitment_type TEXT,
                        education_type TEXT,
                        department TEXT,
                        position TEXT,
                        requirement TEXT,
                        salary_range TEXT,
                        location TEXT,
                        quota INTEGER DEFAULT 1,
                        status TEXT DEFAULT 'open',
                        start_date TEXT,
                        end_date TEXT,
                        contact TEXT,
                        description TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS recruitment_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        recruitment_id TEXT NOT NULL,
                        applicant_id INTEGER NOT NULL,
                        applicant_name TEXT,
                        resume_url TEXT,
                        status TEXT DEFAULT 'applied',
                        apply_date TEXT,
                        interview_date TEXT,
                        interview_result TEXT,
                        offer_date TEXT,
                        accept_status TEXT,
                        UNIQUE(recruitment_id, applicant_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS talent_training (
                        training_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        training_type TEXT,
                        education_type TEXT,
                        department TEXT,
                        duration TEXT,
                        location TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        max_participants INTEGER DEFAULT 30,
                        enrolled_count INTEGER DEFAULT 0,
                        instructor TEXT,
                        content TEXT,
                        cost REAL DEFAULT 0,
                        status TEXT DEFAULT 'planned',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS training_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        training_id TEXT NOT NULL,
                        trainee_id INTEGER NOT NULL,
                        trainee_name TEXT,
                        enroll_date TEXT,
                        attendance_rate REAL DEFAULT 0,
                        final_score REAL,
                        evaluation TEXT,
                        completion_status TEXT DEFAULT 'in_progress',
                        UNIQUE(training_id, trainee_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS talent_evaluation (
                        evaluation_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        evaluation_method TEXT,
                        education_type TEXT,
                        department TEXT,
                        period TEXT,
                        criteria TEXT,
                        weight TEXT,
                        status TEXT DEFAULT 'draft',
                        start_date TEXT,
                        end_date TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS evaluation_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        evaluation_id TEXT NOT NULL,
                        employee_id INTEGER NOT NULL,
                        employee_name TEXT,
                        self_score REAL,
                        manager_score REAL,
                        peer_score REAL,
                        total_score REAL,
                        grade TEXT,
                        comment TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT,
                        UNIQUE(evaluation_id, employee_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS talent_flow (
                        flow_id TEXT PRIMARY KEY,
                        flow_type TEXT,
                        education_type TEXT,
                        employee_id INTEGER NOT NULL,
                        employee_name TEXT,
                        current_department TEXT,
                        target_department TEXT,
                        current_position TEXT,
                        target_position TEXT,
                        reason TEXT,
                        status TEXT DEFAULT 'pending',
                        apply_date TEXT,
                        approve_date TEXT,
                        effective_date TEXT,
                        approver_id INTEGER,
                        approver_name TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS flow_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        flow_id TEXT NOT NULL,
                        step TEXT,
                        action TEXT,
                        operator_id INTEGER,
                        operator_name TEXT,
                        operation_date TEXT,
                        remark TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS talent_incentive (
                        incentive_id TEXT PRIMARY KEY,
                        incentive_type TEXT,
                        education_type TEXT,
                        title TEXT NOT NULL,
                        description TEXT,
                        criteria TEXT,
                        budget REAL DEFAULT 0,
                        period TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS incentive_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        incentive_id TEXT NOT NULL,
                        employee_id INTEGER NOT NULL,
                        employee_name TEXT,
                        amount REAL DEFAULT 0,
                        reason TEXT,
                        grant_date TEXT,
                        status TEXT DEFAULT 'approved',
                        UNIQUE(incentive_id, employee_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS talent_reserve (
                        reserve_id TEXT PRIMARY KEY,
                        reserve_type TEXT,
                        education_type TEXT,
                        employee_id INTEGER NOT NULL,
                        employee_name TEXT,
                        department TEXT,
                        position TEXT,
                        level TEXT,
                        target_position TEXT,
                        evaluation_result TEXT,
                        development_plan TEXT,
                        status TEXT DEFAULT 'active',
                        join_date TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS reserve_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        reserve_id TEXT NOT NULL,
                        activity_type TEXT,
                        activity_name TEXT,
                        activity_date TEXT,
                        result TEXT,
                        evaluator TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS talent_service (
                        service_id TEXT PRIMARY KEY,
                        service_type TEXT,
                        education_type TEXT,
                        title TEXT NOT NULL,
                        provider TEXT,
                        description TEXT,
                        schedule TEXT,
                        capacity INTEGER DEFAULT 20,
                        used_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS service_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        service_id TEXT NOT NULL,
                        employee_id INTEGER NOT NULL,
                        employee_name TEXT,
                        request_date TEXT,
                        service_date TEXT,
                        content TEXT,
                        feedback TEXT,
                        rating INTEGER,
                        status TEXT DEFAULT 'completed',
                        UNIQUE(service_id, employee_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS talent_development (
                        development_id TEXT PRIMARY KEY,
                        development_path TEXT,
                        education_type TEXT,
                        employee_id INTEGER NOT NULL,
                        employee_name TEXT,
                        department TEXT,
                        current_position TEXT,
                        target_position TEXT,
                        plan TEXT,
                        milestones TEXT,
                        start_date TEXT,
                        expected_end_date TEXT,
                        status TEXT DEFAULT 'in_progress',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS development_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        development_id TEXT NOT NULL,
                        milestone TEXT,
                        target_date TEXT,
                        actual_date TEXT,
                        status TEXT DEFAULT 'pending',
                        comment TEXT,
                        evaluator_id INTEGER,
                        evaluator_name TEXT
                    )
                ''')
                conn.commit()
                logger.info('教育人才服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 人才招聘 ==========

    def create_recruitment(self, title: str, recruitment_type: str,
                           education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            recruitment_id = f"rec_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO talent_recruitment (
                            recruitment_id, title, recruitment_type, education_type,
                            department, position, requirement, salary_range,
                            location, quota, status, start_date, end_date,
                            contact, description, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?, ?, ?, ?, ?, ?)
                    ''', (recruitment_id, title, recruitment_type, education_type,
                          kwargs.get('department'), kwargs.get('position'),
                          kwargs.get('requirement'), kwargs.get('salary_range'),
                          kwargs.get('location'), kwargs.get('quota', 1),
                          kwargs.get('start_date', now[:10]),
                          kwargs.get('end_date'),
                          kwargs.get('contact'), kwargs.get('description'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建招聘: {title} ({recruitment_id})')
                    return {'success': True, 'recruitment_id': recruitment_id}
        except Exception as e:
            logger.error(f'创建招聘失败: {e}')
            return {'success': False, 'error': str(e)}

    def apply_recruitment(self, recruitment_id: str, applicant_id: int,
                          applicant_name: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status, end_date FROM talent_recruitment WHERE recruitment_id = ?', (recruitment_id,))
                    recruitment = cursor.fetchone()
                    if not recruitment:
                        return {'success': False, 'error': '招聘不存在'}
                    if recruitment[0] != 'open':
                        return {'success': False, 'error': '招聘已关闭'}
                    if recruitment[1] and now[:10] > recruitment[1]:
                        return {'success': False, 'error': '招聘已过期'}
                    cursor.execute('INSERT OR IGNORE INTO recruitment_records (recruitment_id, applicant_id, applicant_name, resume_url, status, apply_date) VALUES (?, ?, ?, ?, \'applied\', ?)',
                                 (recruitment_id, applicant_id, applicant_name,
                                  kwargs.get('resume_url'), now[:10]))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已投递该职位'}
        except Exception as e:
            logger.error(f'投递简历失败: {e}')
            return {'success': False, 'error': str(e)}

    def process_interview(self, recruitment_id: str, applicant_id: int,
                          **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE recruitment_records SET
                            interview_date = ?, interview_result = ?, status = ?
                        WHERE recruitment_id = ? AND applicant_id = ?
                    ''', (kwargs.get('interview_date', now[:10]),
                          kwargs.get('interview_result'),
                          kwargs.get('status', 'interviewed'),
                          recruitment_id, applicant_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '记录不存在'}
        except Exception as e:
            logger.error(f'处理面试失败: {e}')
            return {'success': False, 'error': str(e)}

    def issue_offer(self, recruitment_id: str, applicant_id: int,
                    **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE recruitment_records SET offer_date = ?, accept_status = ?, status = \'offered\' WHERE recruitment_id = ? AND applicant_id = ?',
                                 (now[:10], kwargs.get('accept_status', 'pending'),
                                  recruitment_id, applicant_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '记录不存在'}
        except Exception as e:
            logger.error(f'发放offer失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 人才培养 ==========

    def create_training(self, title: str, training_type: str,
                        education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            training_id = f"tra_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = TRAINING_TYPES.get(training_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO talent_training (
                            training_id, title, training_type, education_type,
                            department, duration, location, start_date,
                            end_date, max_participants, enrolled_count,
                            instructor, content, cost, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, 'planned', ?, ?)
                    ''', (training_id, title, training_type, education_type,
                          kwargs.get('department'),
                          kwargs.get('duration', config.get('duration', '1-2周')),
                          kwargs.get('location'), kwargs.get('start_date'),
                          kwargs.get('end_date'), kwargs.get('max_participants', 30),
                          kwargs.get('instructor'), kwargs.get('content'),
                          kwargs.get('cost', 0), now, now))
                    conn.commit()
                    logger.info(f'创建培训: {title} ({training_id})')
                    return {'success': True, 'training_id': training_id}
        except Exception as e:
            logger.error(f'创建培训失败: {e}')
            return {'success': False, 'error': str(e)}

    def enroll_training(self, training_id: str, trainee_id: int,
                        trainee_name: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT max_participants, enrolled_count, status FROM talent_training WHERE training_id = ?', (training_id,))
                    training = cursor.fetchone()
                    if not training:
                        return {'success': False, 'error': '培训不存在'}
                    if training[2] != 'planned':
                        return {'success': False, 'error': '培训状态不允许报名'}
                    if training[0] and training[1] >= training[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('INSERT OR IGNORE INTO training_records (training_id, trainee_id, trainee_name, enroll_date) VALUES (?, ?, ?, ?)',
                                 (training_id, trainee_id, trainee_name, now[:10]))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE talent_training SET enrolled_count = enrolled_count + 1, updated_at = ? WHERE training_id = ?', (now, training_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已报名该培训'}
        except Exception as e:
            logger.error(f'报名培训失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_training_result(self, training_id: str, trainee_id: int,
                               **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    score = kwargs.get('final_score', 0)
                    status = 'completed' if score >= 60 else 'failed'
                    cursor.execute('''
                        UPDATE training_records SET
                            attendance_rate = ?, final_score = ?,
                            evaluation = ?, completion_status = ?
                        WHERE training_id = ? AND trainee_id = ?
                    ''', (kwargs.get('attendance_rate', 0), score,
                          kwargs.get('evaluation'), status,
                          training_id, trainee_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'completion_status': status}
                    return {'success': False, 'error': '记录不存在'}
        except Exception as e:
            logger.error(f'记录培训结果失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_trainings(self, education_type: str = None, training_type: str = None,
                       status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM talent_training WHERE 1=1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if training_type:
                    query += ' AND training_type = ?'
                    params.append(training_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                trainings = [dict(t) for t in cursor.fetchall()]
                return {'success': True, 'trainings': trainings, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取培训列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 人才评价 ==========

    def create_evaluation(self, title: str, evaluation_method: str,
                          education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            evaluation_id = f"eva_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = EVALUATION_METHODS.get(evaluation_method, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO talent_evaluation (
                            evaluation_id, title, evaluation_method, education_type,
                            department, period, criteria, weight, status,
                            start_date, end_date, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?, ?)
                    ''', (evaluation_id, title, evaluation_method, education_type,
                          kwargs.get('department'),
                          kwargs.get('period', config.get('frequency', '年度')),
                          kwargs.get('criteria'), kwargs.get('weight'),
                          kwargs.get('start_date'), kwargs.get('end_date'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建评价: {title} ({evaluation_id})')
                    return {'success': True, 'evaluation_id': evaluation_id}
        except Exception as e:
            logger.error(f'创建评价失败: {e}')
            return {'success': False, 'error': str(e)}

    def submit_self_evaluation(self, evaluation_id: str, employee_id: int,
                               employee_name: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT OR IGNORE INTO evaluation_records (evaluation_id, employee_id, employee_name, self_score, comment, status) VALUES (?, ?, ?, ?, ?, \'pending\')',
                                 (evaluation_id, employee_id, employee_name,
                                  kwargs.get('self_score'), kwargs.get('comment')))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    cursor.execute('UPDATE evaluation_records SET self_score = ?, comment = ? WHERE evaluation_id = ? AND employee_id = ?',
                                 (kwargs.get('self_score'), kwargs.get('comment'),
                                  evaluation_id, employee_id))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'提交自评失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_manager_score(self, evaluation_id: str, employee_id: int,
                             manager_score: float, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT self_score, peer_score FROM evaluation_records WHERE evaluation_id = ? AND employee_id = ?', (evaluation_id, employee_id))
                    record = cursor.fetchone()
                    if not record:
                        return {'success': False, 'error': '评价记录不存在'}
                    peer_score = record[1] or 0
                    total_score = (record[0] or 0) * 0.3 + manager_score * 0.5 + peer_score * 0.2
                    grade = 'A' if total_score >= 90 else ('B' if total_score >= 80 else ('C' if total_score >= 60 else 'D'))
                    cursor.execute('UPDATE evaluation_records SET manager_score = ?, total_score = ?, grade = ?, status = ? WHERE evaluation_id = ? AND employee_id = ?',
                                 (manager_score, round(total_score, 1), grade,
                                  kwargs.get('status', 'completed'),
                                  evaluation_id, employee_id))
                    conn.commit()
                    return {'success': True, 'total_score': round(total_score, 1), 'grade': grade}
        except Exception as e:
            logger.error(f'记录主管评分失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_evaluation_result(self, evaluation_id: str, employee_id: int) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM evaluation_records WHERE evaluation_id = ? AND employee_id = ?', (evaluation_id, employee_id))
                record = cursor.fetchone()
                if record:
                    return {'success': True, 'result': dict(record)}
                return {'success': False, 'error': '评价记录不存在'}
        except Exception as e:
            logger.error(f'获取评价结果失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 人才流动 ==========

    def apply_flow(self, flow_type: str, education_type: str,
                   employee_id: int, employee_name: str, **kwargs) -> Dict[str, Any]:
        try:
            flow_id = f"flo_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO talent_flow (
                            flow_id, flow_type, education_type, employee_id,
                            employee_name, current_department, target_department,
                            current_position, target_position, reason, status,
                            apply_date, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)
                    ''', (flow_id, flow_type, education_type, employee_id,
                          employee_name, kwargs.get('current_department'),
                          kwargs.get('target_department'),
                          kwargs.get('current_position'),
                          kwargs.get('target_position'),
                          kwargs.get('reason'), now[:10], now, now))
                    conn.commit()
                    logger.info(f'创建流动申请: {flow_id}')
                    return {'success': True, 'flow_id': flow_id}
        except Exception as e:
            logger.error(f'创建流动申请失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_flow(self, flow_id: str, approved: bool,
                     **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE talent_flow SET status = ?, approve_date = ?, effective_date = ?, approver_id = ?, approver_name = ?, updated_at = ? WHERE flow_id = ?',
                                 (status, now[:10], kwargs.get('effective_date', now[:10]),
                                  kwargs.get('approver_id'), kwargs.get('approver_name'),
                                  now, flow_id))
                    if cursor.rowcount > 0:
                        cursor.execute('INSERT INTO flow_records (flow_id, step, action, operator_id, operator_name, operation_date, remark) VALUES (?, \'approval\', ?, ?, ?, ?, ?)',
                                     (flow_id, status, kwargs.get('approver_id'),
                                      kwargs.get('approver_name'), now[:10],
                                      kwargs.get('remark')))
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '申请不存在'}
        except Exception as e:
            logger.error(f'审批流动申请失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_flow_step(self, flow_id: str, step: str, action: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO flow_records (flow_id, step, action, operator_id, operator_name, operation_date, remark) VALUES (?, ?, ?, ?, ?, ?, ?)',
                                 (flow_id, step, action, kwargs.get('operator_id'),
                                  kwargs.get('operator_name'), now[:10],
                                  kwargs.get('remark')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'记录流动步骤失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_flow_details(self, flow_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM talent_flow WHERE flow_id = ?', (flow_id,))
                flow = cursor.fetchone()
                if not flow:
                    return {'success': False, 'error': '流动记录不存在'}
                cursor.execute('SELECT * FROM flow_records WHERE flow_id = ? ORDER BY operation_date', (flow_id,))
                steps = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'flow': dict(flow), 'steps': steps}
        except Exception as e:
            logger.error(f'获取流动详情失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_flows(self, flow_type: str = None, education_type: str = None,
                   status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM talent_flow WHERE 1=1'
                params = []
                if flow_type:
                    query += ' AND flow_type = ?'
                    params.append(flow_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY apply_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                flows = [dict(f) for f in cursor.fetchall()]
                return {'success': True, 'flows': flows, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取流动列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 人才激励 ==========

    def create_incentive(self, incentive_type: str, education_type: str,
                         title: str, **kwargs) -> Dict[str, Any]:
        try:
            incentive_id = f"inc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO talent_incentive (
                            incentive_id, incentive_type, education_type, title,
                            description, criteria, budget, period, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (incentive_id, incentive_type, education_type, title,
                          kwargs.get('description'), kwargs.get('criteria'),
                          kwargs.get('budget', 0), kwargs.get('period'),
                          now, now))
                    conn.commit()
                    logger.info(f'创建激励: {title} ({incentive_id})')
                    return {'success': True, 'incentive_id': incentive_id}
        except Exception as e:
            logger.error(f'创建激励失败: {e}')
            return {'success': False, 'error': str(e)}

    def grant_incentive(self, incentive_id: str, employee_id: int,
                        employee_name: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT OR IGNORE INTO incentive_records (incentive_id, employee_id, employee_name, amount, reason, grant_date, status) VALUES (?, ?, ?, ?, ?, ?, \'approved\')',
                                 (incentive_id, employee_id, employee_name,
                                  kwargs.get('amount', 0), kwargs.get('reason'),
                                  now[:10]))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已获得该激励'}
        except Exception as e:
            logger.error(f'发放激励失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_incentive_records(self, employee_id: int = None,
                              incentive_type: str = None, page: int = 1,
                              page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM incentive_records WHERE 1=1'
                params = []
                if employee_id:
                    query += ' AND employee_id = ?'
                    params.append(employee_id)
                if incentive_type:
                    query += ' AND incentive_type = ?'
                    params.append(incentive_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY grant_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取激励记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def calculate_incentive_budget(self, incentive_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT budget FROM talent_incentive WHERE incentive_id = ?', (incentive_id,))
                incentive = cursor.fetchone()
                if not incentive:
                    return {'success': False, 'error': '激励不存在'}
                cursor.execute('SELECT SUM(amount) as total FROM incentive_records WHERE incentive_id = ?', (incentive_id,))
                used = cursor.fetchone()['total'] or 0
                remaining = incentive['budget'] - used
                return {'success': True, 'total_budget': incentive['budget'], 'used_amount': used, 'remaining_amount': remaining}
        except Exception as e:
            logger.error(f'计算激励预算失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 人才储备 ==========

    def add_to_reserve(self, reserve_type: str, education_type: str,
                       employee_id: int, employee_name: str, **kwargs) -> Dict[str, Any]:
        try:
            reserve_id = f"res_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = RESERVE_TYPES.get(reserve_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO talent_reserve (
                            reserve_id, reserve_type, education_type, employee_id,
                            employee_name, department, position, level,
                            target_position, evaluation_result, development_plan,
                            status, join_date, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
                    ''', (reserve_id, reserve_type, education_type, employee_id,
                          employee_name, kwargs.get('department'),
                          kwargs.get('position'),
                          kwargs.get('level', config.get('level', '专业')),
                          kwargs.get('target_position'),
                          kwargs.get('evaluation_result'),
                          kwargs.get('development_plan'),
                          now[:10], now, now))
                    conn.commit()
                    logger.info(f'加入储备: {employee_name} ({reserve_id})')
                    return {'success': True, 'reserve_id': reserve_id}
        except Exception as e:
            logger.error(f'加入储备失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_reserve_status(self, reserve_id: str, status: str,
                              **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE talent_reserve SET status = ?, evaluation_result = ?, development_plan = ?, updated_at = ? WHERE reserve_id = ?',
                                 (status, kwargs.get('evaluation_result'),
                                  kwargs.get('development_plan'), now, reserve_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '储备记录不存在'}
        except Exception as e:
            logger.error(f'更新储备状态失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_reserve_activity(self, reserve_id: str, activity_type: str,
                             activity_name: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO reserve_records (reserve_id, activity_type, activity_name, activity_date, result, evaluator) VALUES (?, ?, ?, ?, ?, ?)',
                                 (reserve_id, activity_type, activity_name,
                                  kwargs.get('activity_date', now[:10]),
                                  kwargs.get('result'), kwargs.get('evaluator')))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加储备活动失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_reserves(self, reserve_type: str = None, education_type: str = None,
                      status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM talent_reserve WHERE 1=1'
                params = []
                if reserve_type:
                    query += ' AND reserve_type = ?'
                    params.append(reserve_type)
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY join_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                reserves = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'reserves': reserves, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取储备列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 人才服务 ==========

    def create_service(self, service_type: str, education_type: str,
                       title: str, **kwargs) -> Dict[str, Any]:
        try:
            service_id = f"ser_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = SERVICE_TYPES.get(service_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO talent_service (
                            service_id, service_type, education_type, title,
                            provider, description, schedule, capacity,
                            used_count, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 'active', ?, ?)
                    ''', (service_id, service_type, education_type, title,
                          kwargs.get('provider', config.get('provider', 'HR')),
                          kwargs.get('description'), kwargs.get('schedule'),
                          kwargs.get('capacity', 20), now, now))
                    conn.commit()
                    logger.info(f'创建服务: {title} ({service_id})')
                    return {'success': True, 'service_id': service_id}
        except Exception as e:
            logger.error(f'创建服务失败: {e}')
            return {'success': False, 'error': str(e)}

    def request_service(self, service_id: str, employee_id: int,
                        employee_name: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT capacity, used_count, status FROM talent_service WHERE service_id = ?', (service_id,))
                    service = cursor.fetchone()
                    if not service:
                        return {'success': False, 'error': '服务不存在'}
                    if service[2] != 'active':
                        return {'success': False, 'error': '服务不可用'}
                    if service[0] and service[1] >= service[0]:
                        return {'success': False, 'error': '服务已满'}
                    cursor.execute('INSERT OR IGNORE INTO service_records (service_id, employee_id, employee_name, request_date, service_date, content) VALUES (?, ?, ?, ?, ?, ?)',
                                 (service_id, employee_id, employee_name,
                                  now[:10], kwargs.get('service_date'),
                                  kwargs.get('content')))
                    if cursor.rowcount > 0:
                        cursor.execute('UPDATE talent_service SET used_count = used_count + 1, updated_at = ? WHERE service_id = ?', (now, service_id))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '已申请该服务'}
        except Exception as e:
            logger.error(f'申请服务失败: {e}')
            return {'success': False, 'error': str(e)}

    def complete_service(self, service_id: str, employee_id: int,
                         **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE service_records SET feedback = ?, rating = ?, status = \'completed\' WHERE service_id = ? AND employee_id = ?',
                                 (kwargs.get('feedback'), kwargs.get('rating'),
                                  service_id, employee_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '服务记录不存在'}
        except Exception as e:
            logger.error(f'完成服务失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_services(self, service_type: str = None, education_type: str = None,
                      status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM talent_service WHERE 1=1'
                params = []
                if service_type:
                    query += ' AND service_type = ?'
                    params.append(service_type)
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
                services = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'services': services, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取服务列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 人才发展 ==========

    def create_development_plan(self, development_path: str, education_type: str,
                                employee_id: int, employee_name: str, **kwargs) -> Dict[str, Any]:
        try:
            development_id = f"dev_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO talent_development (
                            development_id, development_path, education_type,
                            employee_id, employee_name, department,
                            current_position, target_position, plan,
                            milestones, start_date, expected_end_date,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'in_progress', ?, ?)
                    ''', (development_id, development_path, education_type,
                          employee_id, employee_name, kwargs.get('department'),
                          kwargs.get('current_position'),
                          kwargs.get('target_position'),
                          kwargs.get('plan'), kwargs.get('milestones'),
                          kwargs.get('start_date', now[:10]),
                          kwargs.get('expected_end_date'), now, now))
                    conn.commit()
                    logger.info(f'创建发展计划: {employee_name} ({development_id})')
                    return {'success': True, 'development_id': development_id}
        except Exception as e:
            logger.error(f'创建发展计划失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_milestone(self, development_id: str, milestone: str,
                      target_date: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT INTO development_records (development_id, milestone, target_date, status) VALUES (?, ?, ?, \'pending\')',
                                 (development_id, milestone, target_date))
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'添加里程碑失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_milestone(self, development_id: str, milestone: str,
                         **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE development_records SET actual_date = ?, status = ?, comment = ?, evaluator_id = ?, evaluator_name = ? WHERE development_id = ? AND milestone = ?',
                                 (kwargs.get('actual_date', now[:10]),
                                  kwargs.get('status', 'completed'),
                                  kwargs.get('comment'),
                                  kwargs.get('evaluator_id'),
                                  kwargs.get('evaluator_name'),
                                  development_id, milestone))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '里程碑不存在'}
        except Exception as e:
            logger.error(f'更新里程碑失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_development_progress(self, development_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM talent_development WHERE development_id = ?', (development_id,))
                plan = cursor.fetchone()
                if not plan:
                    return {'success': False, 'error': '发展计划不存在'}
                cursor.execute('SELECT * FROM development_records WHERE development_id = ? ORDER BY target_date', (development_id,))
                milestones = [dict(m) for m in cursor.fetchall()]
                total = len(milestones)
                completed = sum(1 for m in milestones if m['status'] == 'completed')
                progress = round((completed / total) * 100, 1) if total > 0 else 0
                return {'success': True, 'plan': dict(plan), 'milestones': milestones, 'progress': progress}
        except Exception as e:
            logger.error(f'获取发展进度失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_talent_statistics(self, education_type: str = None,
                              period: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                stats = {}
                filters = []
                params = []
                if education_type:
                    filters.append('education_type = ?')
                    params.append(education_type)
                filter_str = ' AND '.join(filters) if filters else '1=1'
                cursor.execute(f'SELECT COUNT(*) as cnt FROM talent_recruitment WHERE {filter_str}', params)
                stats['total_recruitments'] = cursor.fetchone()['cnt']
                cursor.execute(f'SELECT COUNT(*) as cnt FROM recruitment_records WHERE {filter_str}', params)
                stats['total_applications'] = cursor.fetchone()['cnt']
                cursor.execute(f'SELECT COUNT(*) as cnt FROM talent_training WHERE {filter_str}', params)
                stats['total_trainings'] = cursor.fetchone()['cnt']
                cursor.execute(f'SELECT COUNT(*) as cnt FROM training_records WHERE {filter_str}', params)
                stats['total_training_participants'] = cursor.fetchone()['cnt']
                cursor.execute(f'SELECT COUNT(*) as cnt FROM talent_evaluation WHERE {filter_str}', params)
                stats['total_evaluations'] = cursor.fetchone()['cnt']
                cursor.execute(f'SELECT COUNT(*) as cnt FROM evaluation_records WHERE {filter_str}', params)
                stats['total_evaluation_records'] = cursor.fetchone()['cnt']
                cursor.execute(f'SELECT COUNT(*) as cnt FROM talent_flow WHERE {filter_str}', params)
                stats['total_flows'] = cursor.fetchone()['cnt']
                cursor.execute(f'SELECT COUNT(*) as cnt FROM talent_incentive WHERE {filter_str}', params)
                stats['total_incentives'] = cursor.fetchone()['cnt']
                cursor.execute(f'SELECT SUM(amount) as total FROM incentive_records', params)
                stats['total_incentive_amount'] = cursor.fetchone()['total'] or 0
                cursor.execute(f'SELECT COUNT(*) as cnt FROM talent_reserve WHERE {filter_str}', params)
                stats['total_reserves'] = cursor.fetchone()['cnt']
                cursor.execute(f'SELECT COUNT(*) as cnt FROM talent_service WHERE {filter_str}', params)
                stats['total_services'] = cursor.fetchone()['cnt']
                cursor.execute(f'SELECT COUNT(*) as cnt FROM talent_development WHERE {filter_str}', params)
                stats['total_developments'] = cursor.fetchone()['cnt']
                return {'success': True, 'statistics': stats}
        except Exception as e:
            logger.error(f'获取人才统计失败: {e}')
            return {'success': False, 'error': str(e)}