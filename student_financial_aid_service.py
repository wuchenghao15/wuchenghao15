#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 学生资助与奖学金服务 (v15.11.0)
====================================
提供学生资助、奖学金、困难认定、学费减免、勤工助学、贷款管理与资助发放等综合服务。
本模块同时支持成人教育和K12教育的差异化需求，覆盖学生从困难认定到资助发放的全流程。

核心能力：
1. 资助政策 - 资助项目、政策发布、申请条件管理
2. 助学金 - 国家助学金、学校助学金、社会助学金
3. 奖学金 - 国家奖学金、学校奖学金、专项奖学金、社会奖学金
4. 学费减免 - 减免申请、审批、执行
5. 困难认定 - 家庭经济困难认定、困难等级
6. 勤工助学 - 岗位发布、申请、安排（侧重资助角度的工费补助）
7. 贷款管理 - 生源地贷款、校园地贷款
8. 资助发放 - 发放记录、统计、报告
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'student_financial_aid_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('FinancialAid')


# ========== 资助配置 ==========

# 当地低保线基准（元/人/月），用于困难等级自动判定
LIVING_ALLOWANCE_LINE = 800

# 资助类型
AID_TYPES = {
    'national_grant': {'name': '国家助学金', 'funding_source': '中央财政'},
    'school_grant': {'name': '学校助学金', 'funding_source': '学校自筹'},
    'social_grant': {'name': '社会助学金', 'funding_source': '社会捐赠'},
    'tuition_waiver': {'name': '学费减免', 'funding_source': '学校减免'},
    'emergency_aid': {'name': '紧急救助', 'funding_source': '应急基金'},
    'living_allowance': {'name': '生活补助', 'funding_source': '财政补贴'}
}

# 奖学金类型
SCHOLARSHIP_TYPES = {
    'national_scholarship': {'name': '国家奖学金', 'amount': 8000, 'eligibility': 'GPA排名前1%，综合表现优异'},
    'national_inspirational': {'name': '国家励志奖学金', 'amount': 5000, 'eligibility': '家庭经济困难且成绩优秀'},
    'school_scholarship': {'name': '学校奖学金', 'amount': 2000, 'eligibility': 'GPA排名前10%'},
    'major_scholarship': {'name': '专业奖学金', 'amount': 1500, 'eligibility': '专业成绩突出'},
    'social_scholarship': {'name': '社会奖学金', 'amount': 3000, 'eligibility': '社会捐赠指定条件'},
    'enterprise_scholarship': {'name': '企业奖学金', 'amount': 5000, 'eligibility': '校企合作定向条件'}
}

# 奖学金等级
SCHOLARSHIP_LEVELS = {
    'special': {'name': '特等', 'amount': 8000},
    'first': {'name': '一等', 'amount': 5000},
    'second': {'name': '二等', 'amount': 3000},
    'third': {'name': '三等', 'amount': 1500},
    'excellence': {'name': '优秀', 'amount': 800}
}

# 困难等级
DIFFICULTY_LEVELS = {
    'special_difficulty': {'name': '特别困难', 'aid_amount': 4400},
    'difficulty': {'name': '困难', 'aid_amount': 3300},
    'general_difficulty': {'name': '一般困难', 'aid_amount': 2300},
    'not_difficulty': {'name': '非困难', 'aid_amount': 0}
}

# 资助状态
AID_STATUS = {
    'draft': '草稿',
    'pending': '待审核',
    'under_review': '审核中',
    'approved': '已批准',
    'rejected': '已驳回',
    'issued': '已发放',
    'cancelled': '已取消'
}

# 贷款类型
LOAN_TYPES = {
    'origin_loan': {'name': '生源地贷款', 'max_amount': 12000, 'interest_rate': 0.0, 'repayment_period': 20},
    'campus_loan': {'name': '校园地贷款', 'max_amount': 8000, 'interest_rate': 0.0, 'repayment_period': 15}
}

# 勤工助学类别
WORK_STUDY_CATEGORIES = {
    'administrative': {'name': '行政', 'hourly_wage': 15},
    'library': {'name': '图书馆', 'hourly_wage': 12},
    'lab': {'name': '实验室', 'hourly_wage': 18},
    'teaching_assistant': {'name': '助教', 'hourly_wage': 20},
    'research_assistant': {'name': '科研助理', 'hourly_wage': 25},
    'campus_maintenance': {'name': '校园维护', 'hourly_wage': 12}
}

# 减免类型
WAIVER_TYPES = {
    'full_waiver': {'name': '全额减免', 'waiver_percent': 100},
    'half_waiver': {'name': '半额减免', 'waiver_percent': 50},
    'partial_waiver': {'name': '部分减免', 'waiver_percent': 30},
    'military_waiver': {'name': '军属减免', 'waiver_percent': 50},
    'disability_waiver': {'name': '残障减免', 'waiver_percent': 70},
    'orphan_waiver': {'name': '孤儿减免', 'waiver_percent': 100}
}

# 发放方式
PAYMENT_METHODS = {
    'bank_transfer': {'name': '银行转账'},
    'cash': {'name': '现金'},
    'alipay': {'name': '支付宝'},
    'wechat_pay': {'name': '微信'},
    'campus_card': {'name': '校园卡'}
}


class StudentFinancialAidService:
    """学生资助与奖学金管理服务"""

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
                    CREATE TABLE IF NOT EXISTS aid_policies (
                        policy_id TEXT PRIMARY KEY,
                        policy_name TEXT NOT NULL,
                        aid_type TEXT,
                        target_group TEXT,
                        eligibility TEXT,
                        amount_range TEXT,
                        application_period_start TEXT,
                        application_period_end TEXT,
                        required_materials TEXT,
                        description TEXT,
                        education_type TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS aid_applications (
                        application_id TEXT PRIMARY KEY,
                        policy_id TEXT,
                        student_id INTEGER,
                        student_name TEXT,
                        education_type TEXT,
                        grade_level TEXT,
                        apply_type TEXT,
                        apply_amount REAL,
                        reason TEXT,
                        family_income REAL,
                        family_members INTEGER,
                        difficulty_level TEXT,
                        materials TEXT,
                        status TEXT DEFAULT 'pending',
                        submitted_at TEXT,
                        reviewed_by TEXT,
                        reviewed_at TEXT,
                        review_comment TEXT,
                        approved_amount REAL,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS scholarships (
                        scholarship_id TEXT PRIMARY KEY,
                        scholarship_name TEXT NOT NULL,
                        scholarship_type TEXT,
                        level TEXT,
                        amount REAL,
                        donor TEXT,
                        donor_type TEXT,
                        eligibility TEXT,
                        quota INTEGER DEFAULT 0,
                        applied_count INTEGER DEFAULT 0,
                        awarded_count INTEGER DEFAULT 0,
                        academic_year TEXT,
                        semester TEXT,
                        description TEXT,
                        education_type TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS scholarship_applications (
                        application_id TEXT PRIMARY KEY,
                        scholarship_id TEXT,
                        student_id INTEGER,
                        student_name TEXT,
                        grade_level TEXT,
                        gpa REAL,
                        rank_in_grade INTEGER,
                        achievements TEXT,
                        self_statement TEXT,
                        materials TEXT,
                        status TEXT DEFAULT 'pending',
                        score REAL,
                        ranked_position INTEGER,
                        reviewed_by TEXT,
                        reviewed_at TEXT,
                        review_comment TEXT,
                        awarded_amount REAL,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS difficulty_assessments (
                        assessment_id TEXT PRIMARY KEY,
                        student_id INTEGER,
                        student_name TEXT,
                        education_type TEXT,
                        grade_level TEXT,
                        family_income REAL,
                        family_members INTEGER,
                        per_capita_income REAL,
                        difficulty_level TEXT,
                        special_circumstances TEXT,
                        support_documents TEXT,
                        assessor_id TEXT,
                        assessor_name TEXT,
                        assessment_date TEXT,
                        valid_until TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tuition_waivers (
                        waiver_id TEXT PRIMARY KEY,
                        student_id INTEGER,
                        student_name TEXT,
                        education_type TEXT,
                        waiver_type TEXT,
                        original_fee REAL,
                        waiver_percent REAL,
                        waiver_amount REAL,
                        actual_fee REAL,
                        reason TEXT,
                        materials TEXT,
                        status TEXT DEFAULT 'pending',
                        approved_by TEXT,
                        approved_at TEXT,
                        academic_year TEXT,
                        semester TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS work_study_positions (
                        position_id TEXT PRIMARY KEY,
                        position_name TEXT NOT NULL,
                        category TEXT,
                        department TEXT,
                        supervisor_id TEXT,
                        supervisor_name TEXT,
                        weekly_hours INTEGER DEFAULT 10,
                        hourly_wage REAL DEFAULT 15,
                        total_positions INTEGER DEFAULT 1,
                        filled_positions INTEGER DEFAULT 0,
                        requirements TEXT,
                        semester TEXT,
                        education_type TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS work_study_records (
                        record_id TEXT PRIMARY KEY,
                        position_id TEXT,
                        student_id INTEGER,
                        student_name TEXT,
                        start_date TEXT,
                        end_date TEXT,
                        total_hours REAL DEFAULT 0,
                        total_earned REAL DEFAULT 0,
                        monthly_hours TEXT,
                        evaluation TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS student_loans (
                        loan_id TEXT PRIMARY KEY,
                        student_id INTEGER,
                        student_name TEXT,
                        education_type TEXT,
                        loan_type TEXT,
                        loan_amount REAL,
                        loan_date TEXT,
                        repayment_start_date TEXT,
                        repayment_end_date TEXT,
                        interest_rate REAL,
                        total_repay REAL,
                        repaid_amount REAL DEFAULT 0,
                        remaining_amount REAL,
                        status TEXT DEFAULT 'pending',
                        contract_number TEXT,
                        guarantor TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS aid_disbursements (
                        disbursement_id TEXT PRIMARY KEY,
                        application_id TEXT,
                        student_id INTEGER,
                        student_name TEXT,
                        aid_type TEXT,
                        amount REAL,
                        payment_method TEXT,
                        bank_account TEXT,
                        payment_date TEXT,
                        batch_number TEXT,
                        status TEXT DEFAULT 'pending',
                        operator_id TEXT,
                        operator_name TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS aid_statistics (
                        stat_id TEXT PRIMARY KEY,
                        academic_year TEXT,
                        semester TEXT,
                        education_type TEXT,
                        total_applications INTEGER DEFAULT 0,
                        approved_count INTEGER DEFAULT 0,
                        total_amount REAL DEFAULT 0,
                        by_type TEXT,
                        by_level TEXT,
                        generated_at TEXT,
                        created_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('学生资助与奖学金服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 资助政策管理 ==========

    def create_aid_policy(self, policy_name: str, aid_type: str,
                          **kwargs) -> Dict[str, Any]:
        """创建资助政策"""
        try:
            policy_id = f"pol_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = AID_TYPES.get(aid_type, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO aid_policies (
                            policy_id, policy_name, aid_type, target_group,
                            eligibility, amount_range, application_period_start,
                            application_period_end, required_materials, description,
                            education_type, is_active, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (policy_id, policy_name, aid_type,
                          kwargs.get('target_group'),
                          json.dumps(kwargs.get('eligibility', {}), ensure_ascii=False),
                          kwargs.get('amount_range'),
                          kwargs.get('application_period_start'),
                          kwargs.get('application_period_end'),
                          json.dumps(kwargs.get('required_materials', []), ensure_ascii=False),
                          kwargs.get('description'),
                          kwargs.get('education_type', 'common'),
                          1 if kwargs.get('is_active', True) else 0,
                          now, now))
                    conn.commit()
                    logger.info(f'创建资助政策: {policy_name} ({policy_id}) 类型={config.get("name", aid_type)}')
                    return {'success': True, 'policy_id': policy_id}
        except Exception as e:
            logger.error(f'创建资助政策失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_aid_policy(self, policy_id: str) -> Dict[str, Any]:
        """获取资助政策详情"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM aid_policies WHERE policy_id = ?', (policy_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '政策不存在'}
                policy = dict(row)
                policy['eligibility'] = json.loads(policy.get('eligibility') or '{}')
                policy['required_materials'] = json.loads(policy.get('required_materials') or '[]')
                return {'success': True, 'policy': policy}
        except Exception as e:
            logger.error(f'获取资助政策失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_aid_policies(self, page: int = 1, page_size: int = 20,
                          **filters) -> Dict[str, Any]:
        """资助政策列表（支持aid_type/education_type/is_active筛选）"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM aid_policies WHERE 1=1'
                params = []
                if filters.get('aid_type'):
                    query += ' AND aid_type = ?'
                    params.append(filters['aid_type'])
                if filters.get('education_type'):
                    query += ' AND education_type = ?'
                    params.append(filters['education_type'])
                if filters.get('is_active') is not None:
                    query += ' AND is_active = ?'
                    params.append(1 if filters['is_active'] else 0)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                policies = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'policies': policies, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取资助政策列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_aid_policy(self, policy_id: str, **kwargs) -> Dict[str, Any]:
        """更新资助政策"""
        try:
            now = datetime.now().isoformat()
            allowed = ['policy_name', 'aid_type', 'target_group', 'amount_range',
                       'application_period_start', 'application_period_end',
                       'description', 'education_type', 'is_active']
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT policy_id FROM aid_policies WHERE policy_id = ?', (policy_id,))
                    if not cursor.fetchone():
                        return {'success': False, 'error': '政策不存在'}
                    fields, params = [], []
                    for key in allowed:
                        if key in kwargs:
                            fields.append(f'{key} = ?')
                            params.append(kwargs[key])
                    if 'eligibility' in kwargs:
                        fields.append('eligibility = ?')
                        params.append(json.dumps(kwargs['eligibility'], ensure_ascii=False))
                    if 'required_materials' in kwargs:
                        fields.append('required_materials = ?')
                        params.append(json.dumps(kwargs['required_materials'], ensure_ascii=False))
                    if not fields:
                        return {'success': False, 'error': '无可更新字段'}
                    fields.append('updated_at = ?')
                    params.extend([now, policy_id])
                    cursor.execute(f'UPDATE aid_policies SET {", ".join(fields)} WHERE policy_id = ?', params)
                    conn.commit()
                    return {'success': True}
        except Exception as e:
            logger.error(f'更新资助政策失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 困难认定 ==========

    def apply_difficulty_assessment(self, student_id: int, **kwargs) -> Dict[str, Any]:
        """申请困难认定（自动计算人均收入、建议困难等级）"""
        try:
            assessment_id = f"das_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            family_income = float(kwargs.get('family_income', 0) or 0)
            family_members = int(kwargs.get('family_members', 1) or 1)
            per_capita = family_income / family_members if family_members > 0 else 0
            # 困难等级自动判定
            line = LIVING_ALLOWANCE_LINE
            if per_capita < line:
                level = 'special_difficulty'
            elif per_capita < line * 1.5:
                level = 'difficulty'
            elif per_capita < line * 2:
                level = 'general_difficulty'
            else:
                level = 'not_difficulty'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO difficulty_assessments (
                            assessment_id, student_id, student_name, education_type,
                            grade_level, family_income, family_members, per_capita_income,
                            difficulty_level, special_circumstances, support_documents,
                            assessor_id, assessor_name, assessment_date, valid_until,
                            status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                    ''', (assessment_id, student_id, kwargs.get('student_name'),
                          kwargs.get('education_type'), kwargs.get('grade_level'),
                          family_income, family_members, round(per_capita, 2), level,
                          json.dumps(kwargs.get('special_circumstances', []), ensure_ascii=False),
                          json.dumps(kwargs.get('support_documents', []), ensure_ascii=False),
                          kwargs.get('assessor_id'), kwargs.get('assessor_name'),
                          now[:10], kwargs.get('valid_until'),
                          now, now))
                    conn.commit()
                    logger.info(f'困难认定申请: student={student_id} 等级={level} 人均={per_capita}')
                    return {'success': True, 'assessment_id': assessment_id,
                            'per_capita_income': round(per_capita, 2),
                            'suggested_level': level}
        except Exception as e:
            logger.error(f'申请困难认定失败: {e}')
            return {'success': False, 'error': str(e)}

    def review_difficulty_assessment(self, assessment_id: str, difficulty_level: str,
                                     **kwargs) -> Dict[str, Any]:
        """审核困难认定"""
        try:
            now = datetime.now().isoformat()
            if difficulty_level not in DIFFICULTY_LEVELS:
                return {'success': False, 'error': '困难等级无效'}
            status = kwargs.get('status', 'approved')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE difficulty_assessments SET
                            difficulty_level = ?, status = ?, assessor_id = ?,
                            assessor_name = ?, assessment_date = ?, valid_until = ?,
                            updated_at = ?
                        WHERE assessment_id = ? AND status = 'pending'
                    ''', (difficulty_level, status,
                          kwargs.get('assessor_id'), kwargs.get('assessor_name'),
                          now[:10], kwargs.get('valid_until'), now, assessment_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'困难认定审核: {assessment_id} 等级={difficulty_level}')
                        return {'success': True, 'difficulty_level': difficulty_level}
                    return {'success': False, 'error': '认定记录不存在或已审核'}
        except Exception as e:
            logger.error(f'审核困难认定失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_difficulty_assessment(self, student_id: int) -> Dict[str, Any]:
        """获取学生最新困难认定"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM difficulty_assessments
                    WHERE student_id = ? AND status = 'approved'
                    ORDER BY created_at DESC LIMIT 1
                ''', (student_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '无有效困难认定记录'}
                assessment = dict(row)
                assessment['special_circumstances'] = json.loads(assessment.get('special_circumstances') or '[]')
                assessment['support_documents'] = json.loads(assessment.get('support_documents') or '[]')
                return {'success': True, 'assessment': assessment}
        except Exception as e:
            logger.error(f'获取困难认定失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_difficulty_assessments(self, page: int = 1, page_size: int = 20,
                                    **filters) -> Dict[str, Any]:
        """困难认定列表"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM difficulty_assessments WHERE 1=1'
                params = []
                if filters.get('difficulty_level'):
                    query += ' AND difficulty_level = ?'
                    params.append(filters['difficulty_level'])
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
                assessments = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'assessments': assessments, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取困难认定列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 资助申请 ==========

    def apply_aid(self, policy_id: str, student_id: int, **kwargs) -> Dict[str, Any]:
        """申请资助（检查申请条件、申请期）"""
        try:
            application_id = f"aap_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            today = now[:10]
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT aid_type, is_active, application_period_start, application_period_end FROM aid_policies WHERE policy_id = ?', (policy_id,))
                    policy = cursor.fetchone()
                    if not policy:
                        return {'success': False, 'error': '资助政策不存在'}
                    if not policy[1]:
                        return {'success': False, 'error': '政策未启用'}
                    if policy[2] and today < policy[2]:
                        return {'success': False, 'error': '未到申请开始时间'}
                    if policy[3] and today > policy[3]:
                        return {'success': False, 'error': '申请已截止'}
                    apply_amount = float(kwargs.get('apply_amount', 0) or 0)
                    cursor.execute('''
                        INSERT INTO aid_applications (
                            application_id, policy_id, student_id, student_name,
                            education_type, grade_level, apply_type, apply_amount,
                            reason, family_income, family_members, difficulty_level,
                            materials, status, submitted_at, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)
                    ''', (application_id, policy_id, student_id, kwargs.get('student_name'),
                          kwargs.get('education_type'), kwargs.get('grade_level'),
                          policy[0], apply_amount, kwargs.get('reason'),
                          kwargs.get('family_income'), kwargs.get('family_members'),
                          kwargs.get('difficulty_level'),
                          json.dumps(kwargs.get('materials', []), ensure_ascii=False),
                          now, now, now))
                    conn.commit()
                    logger.info(f'资助申请: student={student_id} 政策={policy_id} 金额={apply_amount}')
                    return {'success': True, 'application_id': application_id}
        except Exception as e:
            logger.error(f'申请资助失败: {e}')
            return {'success': False, 'error': str(e)}

    def review_aid_application(self, application_id: str, approved: bool,
                               **kwargs) -> Dict[str, Any]:
        """审核资助申请"""
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            approved_amount = float(kwargs.get('approved_amount', 0) or 0) if approved else 0
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE aid_applications SET
                            status = ?, reviewed_by = ?, reviewed_at = ?,
                            review_comment = ?, approved_amount = ?, updated_at = ?
                        WHERE application_id = ? AND status IN ('pending', 'under_review')
                    ''', (status, kwargs.get('reviewed_by'), now,
                          kwargs.get('review_comment'), approved_amount, now, application_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'资助申请审核: {application_id} 结果={status}')
                        return {'success': True, 'status': status, 'approved_amount': approved_amount}
                    return {'success': False, 'error': '申请不存在或已审核'}
        except Exception as e:
            logger.error(f'审核资助申请失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_aid_applications(self, page: int = 1, page_size: int = 20,
                              **filters) -> Dict[str, Any]:
        """资助申请列表"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM aid_applications WHERE 1=1'
                params = []
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                if filters.get('apply_type'):
                    query += ' AND apply_type = ?'
                    params.append(filters['apply_type'])
                if filters.get('education_type'):
                    query += ' AND education_type = ?'
                    params.append(filters['education_type'])
                if filters.get('student_id'):
                    query += ' AND student_id = ?'
                    params.append(filters['student_id'])
                if filters.get('policy_id'):
                    query += ' AND policy_id = ?'
                    params.append(filters['policy_id'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                applications = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'applications': applications, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取资助申请列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_aid_application(self, application_id: str) -> Dict[str, Any]:
        """获取资助申请详情"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM aid_applications WHERE application_id = ?', (application_id,))
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': '申请不存在'}
                application = dict(row)
                application['materials'] = json.loads(application.get('materials') or '[]')
                return {'success': True, 'application': application}
        except Exception as e:
            logger.error(f'获取资助申请详情失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 奖学金管理 ==========

    def create_scholarship(self, scholarship_name: str, scholarship_type: str,
                           **kwargs) -> Dict[str, Any]:
        """创建奖学金项目"""
        try:
            scholarship_id = f"sch_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = SCHOLARSHIP_TYPES.get(scholarship_type, {})
            level = kwargs.get('level')
            level_config = SCHOLARSHIP_LEVELS.get(level, {}) if level else {}
            amount = kwargs.get('amount', level_config.get('amount', config.get('amount', 0)))
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO scholarships (
                            scholarship_id, scholarship_name, scholarship_type, level,
                            amount, donor, donor_type, eligibility, quota, applied_count,
                            awarded_count, academic_year, semester, description,
                            education_type, is_active, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?, ?, ?, ?, ?, ?)
                    ''', (scholarship_id, scholarship_name, scholarship_type, level, amount,
                          kwargs.get('donor'), kwargs.get('donor_type'),
                          json.dumps(kwargs.get('eligibility', config.get('eligibility', '')), ensure_ascii=False),
                          kwargs.get('quota', 1), kwargs.get('academic_year'),
                          kwargs.get('semester'), kwargs.get('description'),
                          kwargs.get('education_type', 'common'),
                          1 if kwargs.get('is_active', True) else 0, now, now))
                    conn.commit()
                    logger.info(f'创建奖学金项目: {scholarship_name} ({scholarship_id}) 金额={amount}')
                    return {'success': True, 'scholarship_id': scholarship_id, 'amount': amount}
        except Exception as e:
            logger.error(f'创建奖学金项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def apply_scholarship(self, scholarship_id: str, student_id: int,
                          **kwargs) -> Dict[str, Any]:
        """申请奖学金（检查名额、资格）"""
        try:
            application_id = f"sap_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT quota, applied_count, is_active FROM scholarships WHERE scholarship_id = ?', (scholarship_id,))
                    scholarship = cursor.fetchone()
                    if not scholarship:
                        return {'success': False, 'error': '奖学金项目不存在'}
                    if not scholarship[2]:
                        return {'success': False, 'error': '项目未启用'}
                    if scholarship[1] >= scholarship[0]:
                        return {'success': False, 'error': '名额已满'}
                    cursor.execute('SELECT application_id FROM scholarship_applications WHERE scholarship_id = ? AND student_id = ?',
                                 (scholarship_id, student_id))
                    if cursor.fetchone():
                        return {'success': False, 'error': '已申请该奖学金'}
                    cursor.execute('''
                        INSERT INTO scholarship_applications (
                            application_id, scholarship_id, student_id, student_name,
                            grade_level, gpa, rank_in_grade, achievements, self_statement,
                            materials, status, score, ranked_position, awarded_amount,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', 0, 0, 0, ?, ?)
                    ''', (application_id, scholarship_id, student_id, kwargs.get('student_name'),
                          kwargs.get('grade_level'), kwargs.get('gpa'),
                          kwargs.get('rank_in_grade'),
                          json.dumps(kwargs.get('achievements', []), ensure_ascii=False),
                          kwargs.get('self_statement'),
                          json.dumps(kwargs.get('materials', []), ensure_ascii=False),
                          now, now))
                    cursor.execute('UPDATE scholarships SET applied_count = applied_count + 1, updated_at = ? WHERE scholarship_id = ?',
                                 (now, scholarship_id))
                    conn.commit()
                    logger.info(f'奖学金申请: student={student_id} 项目={scholarship_id}')
                    return {'success': True, 'application_id': application_id}
        except Exception as e:
            logger.error(f'申请奖学金失败: {e}')
            return {'success': False, 'error': str(e)}

    def review_scholarship_application(self, application_id: str, score: float,
                                       **kwargs) -> Dict[str, Any]:
        """评审奖学金（含排名）"""
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT scholarship_id FROM scholarship_applications WHERE application_id = ?', (application_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '申请不存在'}
                    scholarship_id = row[0]
                    cursor.execute('''
                        UPDATE scholarship_applications SET
                            score = ?, status = 'under_review', reviewed_by = ?,
                            reviewed_at = ?, review_comment = ?, updated_at = ?
                        WHERE application_id = ?
                    ''', (score, kwargs.get('reviewed_by'), now,
                          kwargs.get('review_comment'), now, application_id))
                    # 计算排名：按分数降序排名
                    cursor.execute('''
                        SELECT application_id FROM scholarship_applications
                        WHERE scholarship_id = ? AND score IS NOT NULL
                        ORDER BY score DESC
                    ''', (scholarship_id,))
                    ranked_ids = [r[0] for r in cursor.fetchall()]
                    for idx, aid in enumerate(ranked_ids, start=1):
                        cursor.execute('UPDATE scholarship_applications SET ranked_position = ? WHERE application_id = ?',
                                     (idx, aid))
                    conn.commit()
                    position = ranked_ids.index(application_id) + 1 if application_id in ranked_ids else 0
                    logger.info(f'奖学金评审: {application_id} 分数={score} 排名={position}')
                    return {'success': True, 'score': score, 'ranked_position': position}
        except Exception as e:
            logger.error(f'评审奖学金失败: {e}')
            return {'success': False, 'error': str(e)}

    def award_scholarship(self, application_id: str, **kwargs) -> Dict[str, Any]:
        """颁发奖学金"""
        try:
            now = datetime.now().isoformat()
            awarded_amount = float(kwargs.get('awarded_amount', 0) or 0)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT scholarship_id FROM scholarship_applications WHERE application_id = ? AND status = "under_review"',
                                 (application_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '申请不存在或未通过评审'}
                    scholarship_id = row[0]
                    cursor.execute('UPDATE scholarship_applications SET status = "awarded", awarded_amount = ?, updated_at = ? WHERE application_id = ?',
                                 (awarded_amount, now, application_id))
                    cursor.execute('UPDATE scholarships SET awarded_count = awarded_count + 1, updated_at = ? WHERE scholarship_id = ?',
                                 (now, scholarship_id))
                    conn.commit()
                    logger.info(f'颁发奖学金: {application_id} 金额={awarded_amount}')
                    return {'success': True, 'awarded_amount': awarded_amount}
        except Exception as e:
            logger.error(f'颁发奖学金失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_scholarships(self, page: int = 1, page_size: int = 20,
                          **filters) -> Dict[str, Any]:
        """奖学金项目列表"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM scholarships WHERE 1=1'
                params = []
                if filters.get('scholarship_type'):
                    query += ' AND scholarship_type = ?'
                    params.append(filters['scholarship_type'])
                if filters.get('education_type'):
                    query += ' AND education_type = ?'
                    params.append(filters['education_type'])
                if filters.get('academic_year'):
                    query += ' AND academic_year = ?'
                    params.append(filters['academic_year'])
                if filters.get('is_active') is not None:
                    query += ' AND is_active = ?'
                    params.append(1 if filters['is_active'] else 0)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                scholarships = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'scholarships': scholarships, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取奖学金列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_scholarship_applications(self, page: int = 1, page_size: int = 20,
                                      **filters) -> Dict[str, Any]:
        """奖学金申请列表"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM scholarship_applications WHERE 1=1'
                params = []
                if filters.get('scholarship_id'):
                    query += ' AND scholarship_id = ?'
                    params.append(filters['scholarship_id'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                if filters.get('student_id'):
                    query += ' AND student_id = ?'
                    params.append(filters['student_id'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY score DESC, created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                applications = [dict(a) for a in cursor.fetchall()]
                return {'success': True, 'applications': applications, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取奖学金申请列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 学费减免 ==========

    def apply_tuition_waiver(self, student_id: int, waiver_type: str,
                             **kwargs) -> Dict[str, Any]:
        """申请学费减免（自动计算减免金额）"""
        try:
            waiver_id = f"twv_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = WAIVER_TYPES.get(waiver_type, {})
            if not config:
                return {'success': False, 'error': '减免类型无效'}
            waiver_percent = config.get('waiver_percent', 0)
            original_fee = float(kwargs.get('original_fee', 0) or 0)
            # 减免金额 = 原费用 × 减免比例 / 100
            waiver_amount = round(original_fee * waiver_percent / 100, 2)
            actual_fee = round(original_fee - waiver_amount, 2)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO tuition_waivers (
                            waiver_id, student_id, student_name, education_type,
                            waiver_type, original_fee, waiver_percent, waiver_amount,
                            actual_fee, reason, materials, status, academic_year,
                            semester, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?)
                    ''', (waiver_id, student_id, kwargs.get('student_name'),
                          kwargs.get('education_type'), waiver_type, original_fee,
                          waiver_percent, waiver_amount, actual_fee,
                          kwargs.get('reason'),
                          json.dumps(kwargs.get('materials', []), ensure_ascii=False),
                          kwargs.get('academic_year'), kwargs.get('semester'),
                          now, now))
                    conn.commit()
                    logger.info(f'学费减免申请: student={student_id} 类型={waiver_type} 减免={waiver_amount}')
                    return {'success': True, 'waiver_id': waiver_id,
                            'waiver_amount': waiver_amount, 'actual_fee': actual_fee}
        except Exception as e:
            logger.error(f'申请学费减免失败: {e}')
            return {'success': False, 'error': str(e)}

    def review_tuition_waiver(self, waiver_id: str, approved: bool,
                              **kwargs) -> Dict[str, Any]:
        """审核学费减免"""
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE tuition_waivers SET
                            status = ?, approved_by = ?, approved_at = ?, updated_at = ?
                        WHERE waiver_id = ? AND status = 'pending'
                    ''', (status, kwargs.get('approved_by'), now, now, waiver_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'学费减免审核: {waiver_id} 结果={status}')
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '减免申请不存在或已审核'}
        except Exception as e:
            logger.error(f'审核学费减免失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_tuition_waivers(self, page: int = 1, page_size: int = 20,
                             **filters) -> Dict[str, Any]:
        """学费减免列表"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM tuition_waivers WHERE 1=1'
                params = []
                if filters.get('waiver_type'):
                    query += ' AND waiver_type = ?'
                    params.append(filters['waiver_type'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                if filters.get('education_type'):
                    query += ' AND education_type = ?'
                    params.append(filters['education_type'])
                if filters.get('student_id'):
                    query += ' AND student_id = ?'
                    params.append(filters['student_id'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                waivers = [dict(w) for w in cursor.fetchall()]
                return {'success': True, 'waivers': waivers, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取学费减免列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 勤工助学 ==========

    def create_work_study_position(self, position_name: str, category: str,
                                   **kwargs) -> Dict[str, Any]:
        """发布勤工助学岗位"""
        try:
            position_id = f"wsp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = WORK_STUDY_CATEGORIES.get(category, {})
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO work_study_positions (
                            position_id, position_name, category, department,
                            supervisor_id, supervisor_name, weekly_hours, hourly_wage,
                            total_positions, filled_positions, requirements, semester,
                            education_type, is_active, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?)
                    ''', (position_id, position_name, category,
                          kwargs.get('department'), kwargs.get('supervisor_id'),
                          kwargs.get('supervisor_name'),
                          kwargs.get('weekly_hours', 10),
                          kwargs.get('hourly_wage', config.get('hourly_wage', 15)),
                          kwargs.get('total_positions', 1),
                          kwargs.get('requirements'), kwargs.get('semester'),
                          kwargs.get('education_type', 'common'),
                          1 if kwargs.get('is_active', True) else 0, now, now))
                    conn.commit()
                    logger.info(f'发布勤工助学岗位: {position_name} ({position_id})')
                    return {'success': True, 'position_id': position_id}
        except Exception as e:
            logger.error(f'发布勤工助学岗位失败: {e}')
            return {'success': False, 'error': str(e)}

    def apply_work_study(self, position_id: str, student_id: int,
                         **kwargs) -> Dict[str, Any]:
        """申请勤工助学岗位"""
        try:
            record_id = f"wsr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT total_positions, filled_positions, is_active FROM work_study_positions WHERE position_id = ?', (position_id,))
                    position = cursor.fetchone()
                    if not position:
                        return {'success': False, 'error': '岗位不存在'}
                    if not position[2]:
                        return {'success': False, 'error': '岗位未启用'}
                    if position[1] >= position[0]:
                        return {'success': False, 'error': '岗位已满'}
                    cursor.execute('SELECT record_id FROM work_study_records WHERE position_id = ? AND student_id = ? AND status = "active"',
                                 (position_id, student_id))
                    if cursor.fetchone():
                        return {'success': False, 'error': '已申请该岗位'}
                    cursor.execute('''
                        INSERT INTO work_study_records (
                            record_id, position_id, student_id, student_name,
                            start_date, end_date, total_hours, total_earned,
                            monthly_hours, evaluation, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, NULL, 0, 0, ?, NULL, 'active', ?, ?)
                    ''', (record_id, position_id, student_id, kwargs.get('student_name'),
                          now[:10], json.dumps({}, ensure_ascii=False), now, now))
                    cursor.execute('UPDATE work_study_positions SET filled_positions = filled_positions + 1, updated_at = ? WHERE position_id = ?',
                                 (now, position_id))
                    conn.commit()
                    logger.info(f'勤工助学申请: student={student_id} 岗位={position_id}')
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'申请勤工助学失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_work_study(self, record_id: str, hours: float,
                          **kwargs) -> Dict[str, Any]:
        """记录工时（计算报酬）"""
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT r.position_id, p.hourly_wage
                        FROM work_study_records r
                        JOIN work_study_positions p ON r.position_id = p.position_id
                        WHERE r.record_id = ? AND r.status = 'active'
                    ''', (record_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '记录不存在或已结束'}
                    hourly_wage = row[1] or 0
                    earned = round(hours * hourly_wage, 2)
                    month_key = kwargs.get('month', now[:7])
                    cursor.execute('SELECT monthly_hours FROM work_study_records WHERE record_id = ?', (record_id,))
                    current = cursor.fetchone()
                    monthly = json.loads(current[0] or '{}')
                    monthly[month_key] = round(monthly.get(month_key, 0) + hours, 2)
                    cursor.execute('''
                        UPDATE work_study_records SET
                            total_hours = total_hours + ?, total_earned = total_earned + ?,
                            monthly_hours = ?, updated_at = ?
                        WHERE record_id = ?
                    ''', (hours, earned, json.dumps(monthly, ensure_ascii=False), now, record_id))
                    conn.commit()
                    logger.info(f'工时记录: {record_id} 工时={hours} 报酬={earned}')
                    return {'success': True, 'hours': hours, 'earned': earned}
        except Exception as e:
            logger.error(f'记录工时失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_work_study_positions(self, page: int = 1, page_size: int = 20,
                                  **filters) -> Dict[str, Any]:
        """勤工助学岗位列表"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM work_study_positions WHERE 1=1'
                params = []
                if filters.get('category'):
                    query += ' AND category = ?'
                    params.append(filters['category'])
                if filters.get('education_type'):
                    query += ' AND education_type = ?'
                    params.append(filters['education_type'])
                if filters.get('is_active') is not None:
                    query += ' AND is_active = ?'
                    params.append(1 if filters['is_active'] else 0)
                if filters.get('semester'):
                    query += ' AND semester = ?'
                    params.append(filters['semester'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                positions = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'positions': positions, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取勤工助学岗位列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 贷款管理 ==========

    def apply_loan(self, student_id: int, loan_type: str, loan_amount: float,
                   **kwargs) -> Dict[str, Any]:
        """申请贷款"""
        try:
            loan_id = f"loa_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            config = LOAN_TYPES.get(loan_type, {})
            if not config:
                return {'success': False, 'error': '贷款类型无效'}
            max_amount = config.get('max_amount', 0)
            if loan_amount > max_amount:
                return {'success': False, 'error': f'贷款金额超过上限{max_amount}'}
            interest_rate = config.get('interest_rate', 0.0)
            repayment_period = config.get('repayment_period', 15)
            loan_date = kwargs.get('loan_date', now[:10])
            repayment_start = (datetime.now() + timedelta(days=365 * 2)).strftime('%Y-%m-%d')
            repayment_end = (datetime.now() + timedelta(days=365 * (2 + repayment_period))).strftime('%Y-%m-%d')
            total_repay = round(loan_amount * (1 + interest_rate), 2)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO student_loans (
                            loan_id, student_id, student_name, education_type,
                            loan_type, loan_amount, loan_date, repayment_start_date,
                            repayment_end_date, interest_rate, total_repay,
                            repaid_amount, remaining_amount, status, contract_number,
                            guarantor, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 'pending', ?, ?, ?, ?)
                    ''', (loan_id, student_id, kwargs.get('student_name'),
                          kwargs.get('education_type'), loan_type, loan_amount,
                          loan_date, repayment_start, repayment_end,
                          interest_rate, total_repay, total_repay,
                          kwargs.get('contract_number'), kwargs.get('guarantor'),
                          now, now))
                    conn.commit()
                    logger.info(f'贷款申请: student={student_id} 类型={loan_type} 金额={loan_amount}')
                    return {'success': True, 'loan_id': loan_id, 'total_repay': total_repay}
        except Exception as e:
            logger.error(f'申请贷款失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_loan(self, loan_id: str, **kwargs) -> Dict[str, Any]:
        """审批贷款"""
        try:
            now = datetime.now().isoformat()
            contract_number = kwargs.get('contract_number') or f"LN{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE student_loans SET
                            status = 'approved', contract_number = ?, updated_at = ?
                        WHERE loan_id = ? AND status = 'pending'
                    ''', (contract_number, now, loan_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'贷款审批: {loan_id} 合同号={contract_number}')
                        return {'success': True, 'contract_number': contract_number}
                    return {'success': False, 'error': '贷款不存在或已审批'}
        except Exception as e:
            logger.error(f'审批贷款失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_repayment(self, loan_id: str, amount: float,
                         **kwargs) -> Dict[str, Any]:
        """记录还款"""
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT repaid_amount, remaining_amount, total_repay FROM student_loans WHERE loan_id = ?', (loan_id,))
                    loan = cursor.fetchone()
                    if not loan:
                        return {'success': False, 'error': '贷款不存在'}
                    new_repaid = round(loan[0] + amount, 2)
                    new_remaining = round(loan[1] - amount, 2)
                    status = 'repaid' if new_remaining <= 0 else 'repaying'
                    cursor.execute('''
                        UPDATE student_loans SET
                            repaid_amount = ?, remaining_amount = ?, status = ?, updated_at = ?
                        WHERE loan_id = ?
                    ''', (new_repaid, new_remaining, status, now, loan_id))
                    conn.commit()
                    logger.info(f'贷款还款: {loan_id} 本次={amount} 剩余={new_remaining}')
                    return {'success': True, 'repaid_amount': new_repaid,
                            'remaining_amount': new_remaining, 'status': status}
        except Exception as e:
            logger.error(f'记录还款失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_loans(self, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        """贷款列表"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM student_loans WHERE 1=1'
                params = []
                if filters.get('loan_type'):
                    query += ' AND loan_type = ?'
                    params.append(filters['loan_type'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                if filters.get('student_id'):
                    query += ' AND student_id = ?'
                    params.append(filters['student_id'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                loans = [dict(l) for l in cursor.fetchall()]
                return {'success': True, 'loans': loans, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取贷款列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 资助发放 ==========

    def disburse_aid(self, application_id: str, payment_method: str,
                     **kwargs) -> Dict[str, Any]:
        """发放资助"""
        try:
            disbursement_id = f"dis_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            if payment_method not in PAYMENT_METHODS:
                return {'success': False, 'error': '发放方式无效'}
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT student_id, student_name, apply_type, approved_amount, status FROM aid_applications WHERE application_id = ?', (application_id,))
                    app = cursor.fetchone()
                    if not app:
                        return {'success': False, 'error': '资助申请不存在'}
                    if app[4] != 'approved':
                        return {'success': False, 'error': '申请未批准，不可发放'}
                    amount = float(kwargs.get('amount', app[3] or 0))
                    batch_number = kwargs.get('batch_number') or f"BATCH{datetime.now().strftime('%Y%m%d')}"
                    cursor.execute('''
                        INSERT INTO aid_disbursements (
                            disbursement_id, application_id, student_id, student_name,
                            aid_type, amount, payment_method, bank_account, payment_date,
                            batch_number, status, operator_id, operator_name, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'issued', ?, ?, ?)
                    ''', (disbursement_id, application_id, app[0], app[1], app[2], amount,
                          payment_method, kwargs.get('bank_account'), now[:10],
                          batch_number, kwargs.get('operator_id'),
                          kwargs.get('operator_name'), now))
                    cursor.execute('UPDATE aid_applications SET status = "issued", updated_at = ? WHERE application_id = ?',
                                 (now, application_id))
                    conn.commit()
                    logger.info(f'资助发放: {application_id} 金额={amount} 方式={payment_method}')
                    return {'success': True, 'disbursement_id': disbursement_id,
                            'amount': amount, 'batch_number': batch_number}
        except Exception as e:
            logger.error(f'发放资助失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_disbursements(self, page: int = 1, page_size: int = 20,
                           **filters) -> Dict[str, Any]:
        """资助发放记录列表"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM aid_disbursements WHERE 1=1'
                params = []
                if filters.get('aid_type'):
                    query += ' AND aid_type = ?'
                    params.append(filters['aid_type'])
                if filters.get('payment_method'):
                    query += ' AND payment_method = ?'
                    params.append(filters['payment_method'])
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                if filters.get('batch_number'):
                    query += ' AND batch_number = ?'
                    params.append(filters['batch_number'])
                if filters.get('student_id'):
                    query += ' AND student_id = ?'
                    params.append(filters['student_id'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                disbursements = [dict(d) for d in cursor.fetchall()]
                return {'success': True, 'disbursements': disbursements, 'total': total,
                        'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取资助发放记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def generate_aid_statistics(self, academic_year: str, semester: str,
                                **kwargs) -> Dict[str, Any]:
        """生成资助统计"""
        try:
            stat_id = f"sta_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            education_type = kwargs.get('education_type', 'common')
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT COUNT(*) FROM aid_applications')
                    total_applications = cursor.fetchone()[0]
                    cursor.execute("SELECT COUNT(*) FROM aid_applications WHERE status IN ('approved', 'issued')")
                    approved_count = cursor.fetchone()[0]
                    cursor.execute("SELECT COALESCE(SUM(approved_amount), 0) FROM aid_applications WHERE status IN ('approved', 'issued')")
                    total_amount = cursor.fetchone()[0]
                    # 按类型统计
                    cursor.execute('SELECT apply_type, COUNT(*), COALESCE(SUM(approved_amount), 0) FROM aid_applications WHERE status IN ("approved","issued") GROUP BY apply_type')
                    by_type = {row[0]: {'count': row[1], 'amount': row[2]} for row in cursor.fetchall()}
                    # 按困难等级统计
                    cursor.execute('SELECT difficulty_level, COUNT(*) FROM aid_applications WHERE difficulty_level IS NOT NULL GROUP BY difficulty_level')
                    by_level = {row[0]: row[1] for row in cursor.fetchall()}
                    cursor.execute('''
                        INSERT INTO aid_statistics (
                            stat_id, academic_year, semester, education_type,
                            total_applications, approved_count, total_amount, by_type,
                            by_level, generated_at, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (stat_id, academic_year, semester, education_type,
                          total_applications, approved_count, total_amount,
                          json.dumps(by_type, ensure_ascii=False),
                          json.dumps(by_level, ensure_ascii=False),
                          now, now))
                    conn.commit()
                    logger.info(f'生成资助统计: {academic_year} {semester} 总额={total_amount}')
                    return {'success': True, 'stat_id': stat_id,
                            'total_applications': total_applications,
                            'approved_count': approved_count,
                            'total_amount': total_amount, 'by_type': by_type, 'by_level': by_level}
        except Exception as e:
            logger.error(f'生成资助统计失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 综合统计 ==========

    def get_statistics(self, education_type: str = None) -> Dict[str, Any]:
        """返回综合统计（资助类型分布/困难等级分布/奖学金发放统计/减免统计/勤工助学统计/贷款统计/发放总额）"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                et_cond = ' AND education_type = ?' if education_type else ''
                et_params = [education_type] if education_type else []
                result = {}
                # 资助类型分布
                cursor.execute(f'SELECT apply_type, COUNT(*), COALESCE(SUM(approved_amount), 0) FROM aid_applications WHERE 1=1{et_cond} GROUP BY apply_type', et_params)
                result['aid_type_distribution'] = {row[0]: {'count': row[1], 'amount': row[2]} for row in cursor.fetchall()}
                # 困难等级分布
                cursor.execute(f'SELECT difficulty_level, COUNT(*) FROM difficulty_assessments WHERE 1=1{et_cond} GROUP BY difficulty_level', et_params)
                result['difficulty_distribution'] = {row[0]: row[1] for row in cursor.fetchall()}
                # 奖学金发放统计
                cursor.execute('SELECT scholarship_type, COUNT(*), COALESCE(SUM(awarded_amount), 0) FROM scholarship_applications WHERE status = "awarded" GROUP BY scholarship_id')
                scholarship_rows = cursor.fetchall()
                result['scholarship_awarded'] = {'count': sum(r[1] for r in scholarship_rows),
                                                 'total_amount': sum(r[2] for r in scholarship_rows)}
                # 减免统计
                cursor.execute(f'SELECT COUNT(*), COALESCE(SUM(waiver_amount), 0) FROM tuition_waivers WHERE status = "approved"{et_cond}', et_params)
                waiver_row = cursor.fetchone()
                result['tuition_waiver'] = {'count': waiver_row[0], 'total_amount': waiver_row[1]}
                # 勤工助学统计
                cursor.execute('SELECT COUNT(*), COALESCE(SUM(total_hours), 0), COALESCE(SUM(total_earned), 0) FROM work_study_records WHERE status = "active"')
                ws_row = cursor.fetchone()
                result['work_study'] = {'count': ws_row[0], 'total_hours': ws_row[1], 'total_earned': ws_row[2]}
                # 贷款统计
                cursor.execute(f'SELECT COUNT(*), COALESCE(SUM(loan_amount), 0), COALESCE(SUM(remaining_amount), 0) FROM student_loans WHERE status IN ("approved","repaying"){et_cond}', et_params)
                loan_row = cursor.fetchone()
                result['loan'] = {'count': loan_row[0], 'total_amount': loan_row[1], 'remaining': loan_row[2]}
                # 发放总额
                cursor.execute('SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM aid_disbursements WHERE status = "issued"')
                dis_row = cursor.fetchone()
                result['disbursement'] = {'count': dis_row[0], 'total_amount': dis_row[1]}
                logger.info(f'获取资助综合统计: education_type={education_type}')
                return {'success': True, 'statistics': result}
        except Exception as e:
            logger.error(f'获取资助综合统计失败: {e}')
            return {'success': False, 'error': str(e)}


if __name__ == '__main__':
    service = StudentFinancialAidService()
    print('学生资助与奖学金服务初始化完成')
    stats = service.get_statistics()
    print(f'统计: {stats}')
