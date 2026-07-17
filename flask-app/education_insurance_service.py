#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育保险服务 (v15.30.0)
============================
提供学生保险、教师保险、学校保险、教育金保险、健康保险、意外保险、财产保险、责任保险等综合管理服务。

核心能力：
1. 学生保险 - 学平险、意外险、重疾险、医疗险、住院险、门诊险、住院津贴、意外医疗
2. 教师保险 - 意外险、重疾险、医疗险、职业险、养老保险、失业保险、工伤保险、生育保险
3. 学校保险 - 校责险、校园方责任险、公众责任险、财产险、雇主责任险、产品责任险、火灾险、自然灾害险
4. 教育金保险 - 少儿教育金、大学教育金、研究生教育金、留学教育金、终身教育金、分红型、万能型、投连型
5. 健康保险 - 重疾险、医疗险、住院险、门诊险、慢病险、牙科险、眼科险、体检险
6. 意外保险 - 个人意外险、团体意外险、交通意外险、旅行意外险、运动意外险、家庭意外险、校园意外险、综合意外险
7. 财产保险 - 房屋险、设备险、车辆险、货物险、电子产品险、办公用品险、图书资料险、无形资产险
8. 责任保险 - 校责险、教责险、产品责任险、公众责任险、雇主责任险、医疗责任险、职业责任险、环境责任险

差异化支持：
- 成人教育保险方案
- K12教育保险方案
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_insurance_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationInsurance')


# ========== 保险配置项 ==========

STUDENT_INSURANCE = {
    'student_health': {'name': '学平险', 'category': '综合', 'coverage': 50000, 'premium': 80},
    'student_accident': {'name': '意外险', 'category': '意外', 'coverage': 100000, 'premium': 50},
    'student_critical': {'name': '重疾险', 'category': '重疾', 'coverage': 200000, 'premium': 200},
    'student_medical': {'name': '医疗险', 'category': '医疗', 'coverage': 300000, 'premium': 150},
    'student_hospital': {'name': '住院险', 'category': '住院', 'coverage': 150000, 'premium': 100},
    'student_outpatient': {'name': '门诊险', 'category': '门诊', 'coverage': 10000, 'premium': 60},
    'student_hospital_allowance': {'name': '住院津贴', 'category': '津贴', 'coverage': 50, 'premium': 40},
    'student_accident_medical': {'name': '意外医疗', 'category': '意外医疗', 'coverage': 20000, 'premium': 30}
}

TEACHER_INSURANCE = {
    'teacher_accident': {'name': '意外险', 'category': '意外', 'coverage': 200000, 'premium': 100},
    'teacher_critical': {'name': '重疾险', 'category': '重疾', 'coverage': 300000, 'premium': 350},
    'teacher_medical': {'name': '医疗险', 'category': '医疗', 'coverage': 500000, 'premium': 250},
    'teacher_professional': {'name': '职业险', 'category': '职业', 'coverage': 1000000, 'premium': 120},
    'teacher_pension': {'name': '养老保险', 'category': '养老', 'coverage': 0, 'premium': 500},
    'teacher_unemployment': {'name': '失业保险', 'category': '失业', 'coverage': 50000, 'premium': 30},
    'teacher_work_injury': {'name': '工伤保险', 'category': '工伤', 'coverage': 400000, 'premium': 80},
    'teacher_maternity': {'name': '生育保险', 'category': '生育', 'coverage': 80000, 'premium': 40}
}

SCHOOL_INSURANCE = {
    'school_liability': {'name': '校责险', 'category': '责任', 'coverage': 5000000, 'premium': 5000},
    'school_party_liability': {'name': '校园方责任险', 'category': '责任', 'coverage': 3000000, 'premium': 3000},
    'school_public_liability': {'name': '公众责任险', 'category': '公众', 'coverage': 2000000, 'premium': 2000},
    'school_property': {'name': '财产险', 'category': '财产', 'coverage': 10000000, 'premium': 8000},
    'school_employer_liability': {'name': '雇主责任险', 'category': '雇主', 'coverage': 2000000, 'premium': 3500},
    'school_product_liability': {'name': '产品责任险', 'category': '产品', 'coverage': 1000000, 'premium': 1500},
    'school_fire': {'name': '火灾险', 'category': '灾害', 'coverage': 5000000, 'premium': 4000},
    'school_natural_disaster': {'name': '自然灾害险', 'category': '灾害', 'coverage': 8000000, 'premium': 6000}
}

EDUCATION_FUND = {
    'child_education': {'name': '少儿教育金', 'category': '少儿', 'min_amount': 10000, 'premium_mode': 'annual'},
    'college_education': {'name': '大学教育金', 'category': '大学', 'min_amount': 50000, 'premium_mode': 'annual'},
    'graduate_education': {'name': '研究生教育金', 'category': '研究生', 'min_amount': 80000, 'premium_mode': 'annual'},
    'study_abroad': {'name': '留学教育金', 'category': '留学', 'min_amount': 200000, 'premium_mode': 'lump_sum'},
    'lifelong_education': {'name': '终身教育金', 'category': '终身', 'min_amount': 30000, 'premium_mode': 'annual'},
    'dividend': {'name': '分红型', 'category': '投资', 'min_amount': 20000, 'premium_mode': 'annual'},
    'universal': {'name': '万能型', 'category': '投资', 'min_amount': 30000, 'premium_mode': 'flexible'},
    'unit_linked': {'name': '投连型', 'category': '投资', 'min_amount': 50000, 'premium_mode': 'flexible'}
}

HEALTH_INSURANCE = {
    'health_critical': {'name': '重疾险', 'category': '重疾', 'coverage': 500000, 'premium': 400},
    'health_medical': {'name': '医疗险', 'category': '医疗', 'coverage': 1000000, 'premium': 300},
    'health_hospital': {'name': '住院险', 'category': '住院', 'coverage': 200000, 'premium': 150},
    'health_outpatient': {'name': '门诊险', 'category': '门诊', 'coverage': 20000, 'premium': 100},
    'health_chronic': {'name': '慢病险', 'category': '慢病', 'coverage': 100000, 'premium': 120},
    'health_dental': {'name': '牙科险', 'category': '牙科', 'coverage': 15000, 'premium': 80},
    'health_eye': {'name': '眼科险', 'category': '眼科', 'coverage': 10000, 'premium': 60},
    'health_checkup': {'name': '体检险', 'category': '体检', 'coverage': 5000, 'premium': 200}
}

ACCIDENT_INSURANCE = {
    'accident_individual': {'name': '个人意外险', 'category': '个人', 'coverage': 100000, 'premium': 60},
    'accident_group': {'name': '团体意外险', 'category': '团体', 'coverage': 500000, 'premium': 200},
    'accident_traffic': {'name': '交通意外险', 'category': '交通', 'coverage': 500000, 'premium': 80},
    'accident_travel': {'name': '旅行意外险', 'category': '旅行', 'coverage': 300000, 'premium': 50},
    'accident_sports': {'name': '运动意外险', 'category': '运动', 'coverage': 150000, 'premium': 70},
    'accident_family': {'name': '家庭意外险', 'category': '家庭', 'coverage': 200000, 'premium': 150},
    'accident_campus': {'name': '校园意外险', 'category': '校园', 'coverage': 100000, 'premium': 40},
    'accident_comprehensive': {'name': '综合意外险', 'category': '综合', 'coverage': 200000, 'premium': 120}
}

PROPERTY_INSURANCE = {
    'property_building': {'name': '房屋险', 'category': '建筑', 'coverage': 2000000, 'premium': 2000},
    'property_equipment': {'name': '设备险', 'category': '设备', 'coverage': 500000, 'premium': 1000},
    'property_vehicle': {'name': '车辆险', 'category': '车辆', 'coverage': 300000, 'premium': 3000},
    'property_cargo': {'name': '货物险', 'category': '货物', 'coverage': 200000, 'premium': 800},
    'property_electronics': {'name': '电子产品险', 'category': '电子', 'coverage': 100000, 'premium': 500},
    'property_office': {'name': '办公用品险', 'category': '办公', 'coverage': 50000, 'premium': 300},
    'property_books': {'name': '图书资料险', 'category': '图书', 'coverage': 80000, 'premium': 400},
    'property_intangible': {'name': '无形资产险', 'category': '无形', 'coverage': 500000, 'premium': 600}
}

LIABILITY_INSURANCE = {
    'liability_school': {'name': '校责险', 'category': '教育', 'coverage': 5000000, 'premium': 5000},
    'liability_teacher': {'name': '教责险', 'category': '教育', 'coverage': 1000000, 'premium': 1500},
    'liability_product': {'name': '产品责任险', 'category': '产品', 'coverage': 2000000, 'premium': 2500},
    'liability_public': {'name': '公众责任险', 'category': '公众', 'coverage': 3000000, 'premium': 3000},
    'liability_employer': {'name': '雇主责任险', 'category': '雇主', 'coverage': 2000000, 'premium': 3500},
    'liability_medical': {'name': '医疗责任险', 'category': '医疗', 'coverage': 1500000, 'premium': 2000},
    'liability_professional': {'name': '职业责任险', 'category': '职业', 'coverage': 3000000, 'premium': 4000},
    'liability_environmental': {'name': '环境责任险', 'category': '环境', 'coverage': 2000000, 'premium': 3000}
}


class EducationInsuranceService:
    """教育保险服务"""

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
                    CREATE TABLE IF NOT EXISTS student_insurance (
                        policy_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        insurance_type TEXT NOT NULL,
                        education_type TEXT,
                        grade_level INTEGER,
                        coverage REAL,
                        premium REAL,
                        start_date TEXT,
                        end_date TEXT,
                        status TEXT DEFAULT 'active',
                        policy_no TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS student_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        policy_id TEXT NOT NULL,
                        student_id INTEGER,
                        claim_type TEXT,
                        claim_amount REAL,
                        claim_date TEXT,
                        status TEXT DEFAULT 'pending',
                        description TEXT,
                        processed_by TEXT,
                        processed_at TEXT,
                        FOREIGN KEY (policy_id) REFERENCES student_insurance(policy_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS teacher_insurance (
                        policy_id TEXT PRIMARY KEY,
                        teacher_id INTEGER NOT NULL,
                        teacher_name TEXT,
                        insurance_type TEXT NOT NULL,
                        education_type TEXT,
                        coverage REAL,
                        premium REAL,
                        start_date TEXT,
                        end_date TEXT,
                        status TEXT DEFAULT 'active',
                        policy_no TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS teacher_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        policy_id TEXT NOT NULL,
                        teacher_id INTEGER,
                        claim_type TEXT,
                        claim_amount REAL,
                        claim_date TEXT,
                        status TEXT DEFAULT 'pending',
                        description TEXT,
                        processed_by TEXT,
                        processed_at TEXT,
                        FOREIGN KEY (policy_id) REFERENCES teacher_insurance(policy_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS school_insurance (
                        policy_id TEXT PRIMARY KEY,
                        school_id INTEGER NOT NULL,
                        school_name TEXT,
                        insurance_type TEXT NOT NULL,
                        coverage REAL,
                        premium REAL,
                        start_date TEXT,
                        end_date TEXT,
                        status TEXT DEFAULT 'active',
                        policy_no TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS school_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        policy_id TEXT NOT NULL,
                        school_id INTEGER,
                        claim_type TEXT,
                        claim_amount REAL,
                        claim_date TEXT,
                        status TEXT DEFAULT 'pending',
                        description TEXT,
                        processed_by TEXT,
                        processed_at TEXT,
                        FOREIGN KEY (policy_id) REFERENCES school_insurance(policy_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS education_fund (
                        fund_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        student_name TEXT,
                        fund_type TEXT NOT NULL,
                        education_type TEXT,
                        grade_level INTEGER,
                        total_amount REAL,
                        paid_amount REAL,
                        annual_premium REAL,
                        start_date TEXT,
                        maturity_date TEXT,
                        expected_return REAL,
                        status TEXT DEFAULT 'active',
                        fund_no TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS fund_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fund_id TEXT NOT NULL,
                        student_id INTEGER,
                        transaction_type TEXT,
                        transaction_amount REAL,
                        transaction_date TEXT,
                        balance REAL,
                        description TEXT,
                        FOREIGN KEY (fund_id) REFERENCES education_fund(fund_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS health_insurance (
                        policy_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        insurance_type TEXT NOT NULL,
                        education_type TEXT,
                        coverage REAL,
                        premium REAL,
                        start_date TEXT,
                        end_date TEXT,
                        status TEXT DEFAULT 'active',
                        policy_no TEXT,
                        preexisting_conditions TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS health_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        policy_id TEXT NOT NULL,
                        user_id INTEGER,
                        claim_type TEXT,
                        claim_amount REAL,
                        claim_date TEXT,
                        status TEXT DEFAULT 'pending',
                        diagnosis TEXT,
                        hospital TEXT,
                        processed_by TEXT,
                        processed_at TEXT,
                        FOREIGN KEY (policy_id) REFERENCES health_insurance(policy_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS accident_insurance (
                        policy_id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        user_name TEXT,
                        insurance_type TEXT NOT NULL,
                        education_type TEXT,
                        coverage REAL,
                        premium REAL,
                        start_date TEXT,
                        end_date TEXT,
                        status TEXT DEFAULT 'active',
                        policy_no TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS accident_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        policy_id TEXT NOT NULL,
                        user_id INTEGER,
                        accident_type TEXT,
                        claim_amount REAL,
                        accident_date TEXT,
                        status TEXT DEFAULT 'pending',
                        description TEXT,
                        location TEXT,
                        processed_by TEXT,
                        processed_at TEXT,
                        FOREIGN KEY (policy_id) REFERENCES accident_insurance(policy_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS property_insurance (
                        policy_id TEXT PRIMARY KEY,
                        owner_id INTEGER NOT NULL,
                        owner_name TEXT,
                        insurance_type TEXT NOT NULL,
                        property_name TEXT,
                        property_value REAL,
                        coverage REAL,
                        premium REAL,
                        start_date TEXT,
                        end_date TEXT,
                        status TEXT DEFAULT 'active',
                        policy_no TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS property_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        policy_id TEXT NOT NULL,
                        owner_id INTEGER,
                        loss_type TEXT,
                        claim_amount REAL,
                        loss_date TEXT,
                        status TEXT DEFAULT 'pending',
                        description TEXT,
                        assessed_value REAL,
                        processed_by TEXT,
                        processed_at TEXT,
                        FOREIGN KEY (policy_id) REFERENCES property_insurance(policy_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS liability_insurance (
                        policy_id TEXT PRIMARY KEY,
                        entity_id INTEGER NOT NULL,
                        entity_name TEXT,
                        insurance_type TEXT NOT NULL,
                        coverage REAL,
                        premium REAL,
                        start_date TEXT,
                        end_date TEXT,
                        status TEXT DEFAULT 'active',
                        policy_no TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS liability_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        policy_id TEXT NOT NULL,
                        entity_id INTEGER,
                        claim_type TEXT,
                        claim_amount REAL,
                        claim_date TEXT,
                        status TEXT DEFAULT 'pending',
                        description TEXT,
                        third_party TEXT,
                        processed_by TEXT,
                        processed_at TEXT,
                        FOREIGN KEY (policy_id) REFERENCES liability_insurance(policy_id)
                    )
                ''')
                conn.commit()
                logger.info('教育保险服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 学生保险 ==========

    def enroll_student_insurance(self, student_id: int, student_name: str,
                                  insurance_type: str, education_type: str = 'k12',
                                  **kwargs) -> Dict[str, Any]:
        try:
            config = STUDENT_INSURANCE.get(insurance_type)
            if not config:
                return {'success': False, 'error': '保险类型不存在'}
            policy_id = f"si_{uuid.uuid4().hex[:12]}"
            policy_no = f"SIP{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
            now = datetime.now().isoformat()
            end_date = (datetime.now() + timedelta(days=365)).isoformat()[:10]
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO student_insurance (
                            policy_id, student_id, student_name, insurance_type,
                            education_type, grade_level, coverage, premium,
                            start_date, end_date, status, policy_no, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
                    ''', (policy_id, student_id, student_name, insurance_type,
                          education_type, kwargs.get('grade_level'),
                          kwargs.get('coverage', config['coverage']),
                          kwargs.get('premium', config['premium']),
                          now[:10], end_date, policy_no, now, now))
                    conn.commit()
                    logger.info(f'学生投保: {student_name} - {config["name"]}')
                    return {'success': True, 'policy_id': policy_id, 'policy_no': policy_no}
        except Exception as e:
            logger.error(f'学生投保失败: {e}')
            return {'success': False, 'error': str(e)}

    def renew_student_insurance(self, policy_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            new_end_date = (datetime.now() + timedelta(days=365)).isoformat()[:10]
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status, premium FROM student_insurance WHERE policy_id = ?', (policy_id,))
                    policy = cursor.fetchone()
                    if not policy:
                        return {'success': False, 'error': '保单不存在'}
                    if policy[0] != 'active':
                        return {'success': False, 'error': '保单状态不允许续费'}
                    cursor.execute('UPDATE student_insurance SET start_date = ?, end_date = ?, updated_at = ? WHERE policy_id = ?',
                                 (now[:10], new_end_date, now, policy_id))
                    conn.commit()
                    return {'success': True, 'renew_premium': policy[1]}
        except Exception as e:
            logger.error(f'学生保险续费失败: {e}')
            return {'success': False, 'error': str(e)}

    def file_student_claim(self, policy_id: str, claim_type: str,
                            claim_amount: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT student_id, student_name, coverage FROM student_insurance WHERE policy_id = ?', (policy_id,))
                    policy = cursor.fetchone()
                    if not policy:
                        return {'success': False, 'error': '保单不存在'}
                    if claim_amount > policy[2]:
                        return {'success': False, 'error': '理赔金额超过保额'}
                    cursor.execute('''
                        INSERT INTO student_records (policy_id, student_id, claim_type, claim_amount, claim_date, status, description)
                        VALUES (?, ?, ?, ?, ?, 'pending', ?)
                    ''', (policy_id, policy[0], claim_type, claim_amount, now[:10], kwargs.get('description')))
                    conn.commit()
                    return {'success': True, 'claim_id': cursor.lastrowid}
        except Exception as e:
            logger.error(f'学生理赔失败: {e}')
            return {'success': False, 'error': str(e)}

    def process_student_claim(self, claim_id: int, status: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE student_records SET status = ?, processed_by = ?, processed_at = ? WHERE id = ?',
                                 (status, kwargs.get('processed_by'), now, claim_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '理赔记录不存在'}
        except Exception as e:
            logger.error(f'处理学生理赔失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 教师保险 ==========

    def enroll_teacher_insurance(self, teacher_id: int, teacher_name: str,
                                  insurance_type: str, education_type: str = 'adult',
                                  **kwargs) -> Dict[str, Any]:
        try:
            config = TEACHER_INSURANCE.get(insurance_type)
            if not config:
                return {'success': False, 'error': '保险类型不存在'}
            policy_id = f"ti_{uuid.uuid4().hex[:12]}"
            policy_no = f"TIP{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
            now = datetime.now().isoformat()
            end_date = (datetime.now() + timedelta(days=365)).isoformat()[:10]
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO teacher_insurance (
                            policy_id, teacher_id, teacher_name, insurance_type,
                            education_type, coverage, premium, start_date, end_date,
                            status, policy_no, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
                    ''', (policy_id, teacher_id, teacher_name, insurance_type,
                          education_type, kwargs.get('coverage', config['coverage']),
                          kwargs.get('premium', config['premium']),
                          now[:10], end_date, policy_no, now, now))
                    conn.commit()
                    logger.info(f'教师投保: {teacher_name} - {config["name"]}')
                    return {'success': True, 'policy_id': policy_id, 'policy_no': policy_no}
        except Exception as e:
            logger.error(f'教师投保失败: {e}')
            return {'success': False, 'error': str(e)}

    def renew_teacher_insurance(self, policy_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            new_end_date = (datetime.now() + timedelta(days=365)).isoformat()[:10]
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status, premium FROM teacher_insurance WHERE policy_id = ?', (policy_id,))
                    policy = cursor.fetchone()
                    if not policy:
                        return {'success': False, 'error': '保单不存在'}
                    if policy[0] != 'active':
                        return {'success': False, 'error': '保单状态不允许续费'}
                    cursor.execute('UPDATE teacher_insurance SET start_date = ?, end_date = ?, updated_at = ? WHERE policy_id = ?',
                                 (now[:10], new_end_date, now, policy_id))
                    conn.commit()
                    return {'success': True, 'renew_premium': policy[1]}
        except Exception as e:
            logger.error(f'教师保险续费失败: {e}')
            return {'success': False, 'error': str(e)}

    def file_teacher_claim(self, policy_id: str, claim_type: str,
                            claim_amount: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT teacher_id, teacher_name, coverage FROM teacher_insurance WHERE policy_id = ?', (policy_id,))
                    policy = cursor.fetchone()
                    if not policy:
                        return {'success': False, 'error': '保单不存在'}
                    if claim_amount > policy[2]:
                        return {'success': False, 'error': '理赔金额超过保额'}
                    cursor.execute('''
                        INSERT INTO teacher_records (policy_id, teacher_id, claim_type, claim_amount, claim_date, status, description)
                        VALUES (?, ?, ?, ?, ?, 'pending', ?)
                    ''', (policy_id, policy[0], claim_type, claim_amount, now[:10], kwargs.get('description')))
                    conn.commit()
                    return {'success': True, 'claim_id': cursor.lastrowid}
        except Exception as e:
            logger.error(f'教师理赔失败: {e}')
            return {'success': False, 'error': str(e)}

    def process_teacher_claim(self, claim_id: int, status: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE teacher_records SET status = ?, processed_by = ?, processed_at = ? WHERE id = ?',
                                 (status, kwargs.get('processed_by'), now, claim_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '理赔记录不存在'}
        except Exception as e:
            logger.error(f'处理教师理赔失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 学校保险 ==========

    def enroll_school_insurance(self, school_id: int, school_name: str,
                                 insurance_type: str, **kwargs) -> Dict[str, Any]:
        try:
            config = SCHOOL_INSURANCE.get(insurance_type)
            if not config:
                return {'success': False, 'error': '保险类型不存在'}
            policy_id = f"sch_{uuid.uuid4().hex[:12]}"
            policy_no = f"SCH{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
            now = datetime.now().isoformat()
            end_date = (datetime.now() + timedelta(days=365)).isoformat()[:10]
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO school_insurance (
                            policy_id, school_id, school_name, insurance_type,
                            coverage, premium, start_date, end_date,
                            status, policy_no, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
                    ''', (policy_id, school_id, school_name, insurance_type,
                          kwargs.get('coverage', config['coverage']),
                          kwargs.get('premium', config['premium']),
                          now[:10], end_date, policy_no, now, now))
                    conn.commit()
                    logger.info(f'学校投保: {school_name} - {config["name"]}')
                    return {'success': True, 'policy_id': policy_id, 'policy_no': policy_no}
        except Exception as e:
            logger.error(f'学校投保失败: {e}')
            return {'success': False, 'error': str(e)}

    def renew_school_insurance(self, policy_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            new_end_date = (datetime.now() + timedelta(days=365)).isoformat()[:10]
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status, premium FROM school_insurance WHERE policy_id = ?', (policy_id,))
                    policy = cursor.fetchone()
                    if not policy:
                        return {'success': False, 'error': '保单不存在'}
                    if policy[0] != 'active':
                        return {'success': False, 'error': '保单状态不允许续费'}
                    cursor.execute('UPDATE school_insurance SET start_date = ?, end_date = ?, updated_at = ? WHERE policy_id = ?',
                                 (now[:10], new_end_date, now, policy_id))
                    conn.commit()
                    return {'success': True, 'renew_premium': policy[1]}
        except Exception as e:
            logger.error(f'学校保险续费失败: {e}')
            return {'success': False, 'error': str(e)}

    def file_school_claim(self, policy_id: str, claim_type: str,
                           claim_amount: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT school_id, school_name, coverage FROM school_insurance WHERE policy_id = ?', (policy_id,))
                    policy = cursor.fetchone()
                    if not policy:
                        return {'success': False, 'error': '保单不存在'}
                    if claim_amount > policy[2]:
                        return {'success': False, 'error': '理赔金额超过保额'}
                    cursor.execute('''
                        INSERT INTO school_records (policy_id, school_id, claim_type, claim_amount, claim_date, status, description)
                        VALUES (?, ?, ?, ?, ?, 'pending', ?)
                    ''', (policy_id, policy[0], claim_type, claim_amount, now[:10], kwargs.get('description')))
                    conn.commit()
                    return {'success': True, 'claim_id': cursor.lastrowid}
        except Exception as e:
            logger.error(f'学校理赔失败: {e}')
            return {'success': False, 'error': str(e)}

    def process_school_claim(self, claim_id: int, status: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE school_records SET status = ?, processed_by = ?, processed_at = ? WHERE id = ?',
                                 (status, kwargs.get('processed_by'), now, claim_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '理赔记录不存在'}
        except Exception as e:
            logger.error(f'处理学校理赔失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 教育金保险 ==========

    def create_education_fund(self, student_id: int, student_name: str,
                               fund_type: str, education_type: str = 'k12',
                               **kwargs) -> Dict[str, Any]:
        try:
            config = EDUCATION_FUND.get(fund_type)
            if not config:
                return {'success': False, 'error': '教育金类型不存在'}
            fund_id = f"ef_{uuid.uuid4().hex[:12]}"
            fund_no = f"EDF{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
            now = datetime.now().isoformat()
            total_amount = kwargs.get('total_amount', config['min_amount'])
            maturity_years = {'child_education': 15, 'college_education': 10, 'graduate_education': 7,
                             'study_abroad': 5, 'lifelong_education': 30, 'dividend': 10,
                             'universal': 15, 'unit_linked': 10}[fund_type]
            maturity_date = (datetime.now() + timedelta(days=maturity_years * 365)).isoformat()[:10]
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO education_fund (
                            fund_id, student_id, student_name, fund_type,
                            education_type, grade_level, total_amount, paid_amount,
                            annual_premium, start_date, maturity_date,
                            expected_return, status, fund_no, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, 'active', ?, ?, ?)
                    ''', (fund_id, student_id, student_name, fund_type,
                          education_type, kwargs.get('grade_level'),
                          total_amount, kwargs.get('annual_premium', total_amount / maturity_years),
                          now[:10], maturity_date, kwargs.get('expected_return', 0.03),
                          fund_no, now, now))
                    conn.commit()
                    logger.info(f'创建教育金: {student_name} - {config["name"]}')
                    return {'success': True, 'fund_id': fund_id, 'fund_no': fund_no}
        except Exception as e:
            logger.error(f'创建教育金失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_fund_payment(self, fund_id: str, amount: float) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT paid_amount, total_amount, student_id FROM education_fund WHERE fund_id = ?', (fund_id,))
                    fund = cursor.fetchone()
                    if not fund:
                        return {'success': False, 'error': '教育金不存在'}
                    new_paid = fund[0] + amount
                    if new_paid > fund[1]:
                        return {'success': False, 'error': '已超过应缴总额'}
                    cursor.execute('UPDATE education_fund SET paid_amount = ?, updated_at = ? WHERE fund_id = ?',
                                 (new_paid, now, fund_id))
                    cursor.execute('''
                        INSERT INTO fund_records (fund_id, student_id, transaction_type, transaction_amount, transaction_date, balance, description)
                        VALUES (?, ?, 'payment', ?, ?, ?, '缴纳保费')
                    ''', (fund_id, fund[2], amount, now[:10], new_paid))
                    conn.commit()
                    return {'success': True, 'current_balance': new_paid}
        except Exception as e:
            logger.error(f'教育金缴费失败: {e}')
            return {'success': False, 'error': str(e)}

    def withdraw_fund(self, fund_id: str, amount: float) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT paid_amount, maturity_date FROM education_fund WHERE fund_id = ?', (fund_id,))
                    fund = cursor.fetchone()
                    if not fund:
                        return {'success': False, 'error': '教育金不存在'}
                    if now[:10] < fund[1]:
                        return {'success': False, 'error': '未到期，无法支取'}
                    if amount > fund[0]:
                        return {'success': False, 'error': '支取金额超过余额'}
                    new_balance = fund[0] - amount
                    cursor.execute('UPDATE education_fund SET paid_amount = ?, updated_at = ? WHERE fund_id = ?',
                                 (new_balance, now, fund_id))
                    cursor.execute('''
                        INSERT INTO fund_records (fund_id, student_id, transaction_type, transaction_amount, transaction_date, balance, description)
                        VALUES (?, ?, 'withdrawal', ?, ?, ?, '支取教育金')
                    ''', (fund_id, 0, amount, now[:10], new_balance))
                    conn.commit()
                    return {'success': True, 'remaining_balance': new_balance}
        except Exception as e:
            logger.error(f'教育金支取失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_fund_balance(self, fund_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM education_fund WHERE fund_id = ?', (fund_id,))
                fund = cursor.fetchone()
                if not fund:
                    return {'success': False, 'error': '教育金不存在'}
                return {'success': True, 'fund': dict(fund)}
        except Exception as e:
            logger.error(f'查询教育金余额失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_fund_transactions(self, fund_id: str, page: int = 1,
                               page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) as cnt FROM fund_records WHERE fund_id = ?', (fund_id,))
                total = cursor.fetchone()['cnt']
                cursor.execute('SELECT * FROM fund_records WHERE fund_id = ? ORDER BY transaction_date DESC LIMIT ? OFFSET ?',
                             (fund_id, page_size, (page - 1) * page_size))
                records = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'transactions': records, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'查询教育金交易记录失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 健康保险 ==========

    def enroll_health_insurance(self, user_id: int, user_name: str,
                                 insurance_type: str, education_type: str = 'k12',
                                 **kwargs) -> Dict[str, Any]:
        try:
            config = HEALTH_INSURANCE.get(insurance_type)
            if not config:
                return {'success': False, 'error': '保险类型不存在'}
            policy_id = f"hi_{uuid.uuid4().hex[:12]}"
            policy_no = f"HIP{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
            now = datetime.now().isoformat()
            end_date = (datetime.now() + timedelta(days=365)).isoformat()[:10]
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO health_insurance (
                            policy_id, user_id, user_name, insurance_type,
                            education_type, coverage, premium, start_date, end_date,
                            status, policy_no, preexisting_conditions, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?)
                    ''', (policy_id, user_id, user_name, insurance_type,
                          education_type, kwargs.get('coverage', config['coverage']),
                          kwargs.get('premium', config['premium']),
                          now[:10], end_date, policy_no,
                          kwargs.get('preexisting_conditions'), now, now))
                    conn.commit()
                    logger.info(f'健康投保: {user_name} - {config["name"]}')
                    return {'success': True, 'policy_id': policy_id, 'policy_no': policy_no}
        except Exception as e:
            logger.error(f'健康投保失败: {e}')
            return {'success': False, 'error': str(e)}

    def renew_health_insurance(self, policy_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            new_end_date = (datetime.now() + timedelta(days=365)).isoformat()[:10]
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status, premium FROM health_insurance WHERE policy_id = ?', (policy_id,))
                    policy = cursor.fetchone()
                    if not policy:
                        return {'success': False, 'error': '保单不存在'}
                    if policy[0] != 'active':
                        return {'success': False, 'error': '保单状态不允许续费'}
                    cursor.execute('UPDATE health_insurance SET start_date = ?, end_date = ?, updated_at = ? WHERE policy_id = ?',
                                 (now[:10], new_end_date, now, policy_id))
                    conn.commit()
                    return {'success': True, 'renew_premium': policy[1]}
        except Exception as e:
            logger.error(f'健康保险续费失败: {e}')
            return {'success': False, 'error': str(e)}

    def file_health_claim(self, policy_id: str, claim_type: str,
                           claim_amount: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT user_id, user_name, coverage FROM health_insurance WHERE policy_id = ?', (policy_id,))
                    policy = cursor.fetchone()
                    if not policy:
                        return {'success': False, 'error': '保单不存在'}
                    if claim_amount > policy[2]:
                        return {'success': False, 'error': '理赔金额超过保额'}
                    cursor.execute('''
                        INSERT INTO health_records (policy_id, user_id, claim_type, claim_amount, claim_date, status, diagnosis, hospital)
                        VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
                    ''', (policy_id, policy[0], claim_type, claim_amount, now[:10],
                          kwargs.get('diagnosis'), kwargs.get('hospital')))
                    conn.commit()
                    return {'success': True, 'claim_id': cursor.lastrowid}
        except Exception as e:
            logger.error(f'健康理赔失败: {e}')
            return {'success': False, 'error': str(e)}

    def process_health_claim(self, claim_id: int, status: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE health_records SET status = ?, processed_by = ?, processed_at = ? WHERE id = ?',
                                 (status, kwargs.get('processed_by'), now, claim_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '理赔记录不存在'}
        except Exception as e:
            logger.error(f'处理健康理赔失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 意外保险 ==========

    def enroll_accident_insurance(self, user_id: int, user_name: str,
                                   insurance_type: str, education_type: str = 'k12',
                                   **kwargs) -> Dict[str, Any]:
        try:
            config = ACCIDENT_INSURANCE.get(insurance_type)
            if not config:
                return {'success': False, 'error': '保险类型不存在'}
            policy_id = f"aci_{uuid.uuid4().hex[:12]}"
            policy_no = f"ACP{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
            now = datetime.now().isoformat()
            end_date = (datetime.now() + timedelta(days=365)).isoformat()[:10]
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO accident_insurance (
                            policy_id, user_id, user_name, insurance_type,
                            education_type, coverage, premium, start_date, end_date,
                            status, policy_no, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
                    ''', (policy_id, user_id, user_name, insurance_type,
                          education_type, kwargs.get('coverage', config['coverage']),
                          kwargs.get('premium', config['premium']),
                          now[:10], end_date, policy_no, now, now))
                    conn.commit()
                    logger.info(f'意外投保: {user_name} - {config["name"]}')
                    return {'success': True, 'policy_id': policy_id, 'policy_no': policy_no}
        except Exception as e:
            logger.error(f'意外投保失败: {e}')
            return {'success': False, 'error': str(e)}

    def renew_accident_insurance(self, policy_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            new_end_date = (datetime.now() + timedelta(days=365)).isoformat()[:10]
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status, premium FROM accident_insurance WHERE policy_id = ?', (policy_id,))
                    policy = cursor.fetchone()
                    if not policy:
                        return {'success': False, 'error': '保单不存在'}
                    if policy[0] != 'active':
                        return {'success': False, 'error': '保单状态不允许续费'}
                    cursor.execute('UPDATE accident_insurance SET start_date = ?, end_date = ?, updated_at = ? WHERE policy_id = ?',
                                 (now[:10], new_end_date, now, policy_id))
                    conn.commit()
                    return {'success': True, 'renew_premium': policy[1]}
        except Exception as e:
            logger.error(f'意外保险续费失败: {e}')
            return {'success': False, 'error': str(e)}

    def file_accident_claim(self, policy_id: str, accident_type: str,
                             claim_amount: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT user_id, user_name, coverage FROM accident_insurance WHERE policy_id = ?', (policy_id,))
                    policy = cursor.fetchone()
                    if not policy:
                        return {'success': False, 'error': '保单不存在'}
                    if claim_amount > policy[2]:
                        return {'success': False, 'error': '理赔金额超过保额'}
                    cursor.execute('''
                        INSERT INTO accident_records (policy_id, user_id, accident_type, claim_amount, accident_date, status, description, location)
                        VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
                    ''', (policy_id, policy[0], accident_type, claim_amount, now[:10],
                          kwargs.get('description'), kwargs.get('location')))
                    conn.commit()
                    return {'success': True, 'claim_id': cursor.lastrowid}
        except Exception as e:
            logger.error(f'意外理赔失败: {e}')
            return {'success': False, 'error': str(e)}

    def process_accident_claim(self, claim_id: int, status: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE accident_records SET status = ?, processed_by = ?, processed_at = ? WHERE id = ?',
                                 (status, kwargs.get('processed_by'), now, claim_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '理赔记录不存在'}
        except Exception as e:
            logger.error(f'处理意外理赔失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 财产保险 ==========

    def enroll_property_insurance(self, owner_id: int, owner_name: str,
                                   insurance_type: str, property_name: str,
                                   property_value: float, **kwargs) -> Dict[str, Any]:
        try:
            config = PROPERTY_INSURANCE.get(insurance_type)
            if not config:
                return {'success': False, 'error': '保险类型不存在'}
            policy_id = f"pi_{uuid.uuid4().hex[:12]}"
            policy_no = f"PPP{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
            now = datetime.now().isoformat()
            end_date = (datetime.now() + timedelta(days=365)).isoformat()[:10]
            coverage = min(kwargs.get('coverage', config['coverage']), property_value)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO property_insurance (
                            policy_id, owner_id, owner_name, insurance_type,
                            property_name, property_value, coverage, premium,
                            start_date, end_date, status, policy_no, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
                    ''', (policy_id, owner_id, owner_name, insurance_type,
                          property_name, property_value, coverage,
                          kwargs.get('premium', config['premium']),
                          now[:10], end_date, policy_no, now, now))
                    conn.commit()
                    logger.info(f'财产投保: {property_name} - {config["name"]}')
                    return {'success': True, 'policy_id': policy_id, 'policy_no': policy_no}
        except Exception as e:
            logger.error(f'财产投保失败: {e}')
            return {'success': False, 'error': str(e)}

    def renew_property_insurance(self, policy_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            new_end_date = (datetime.now() + timedelta(days=365)).isoformat()[:10]
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status, premium FROM property_insurance WHERE policy_id = ?', (policy_id,))
                    policy = cursor.fetchone()
                    if not policy:
                        return {'success': False, 'error': '保单不存在'}
                    if policy[0] != 'active':
                        return {'success': False, 'error': '保单状态不允许续费'}
                    cursor.execute('UPDATE property_insurance SET start_date = ?, end_date = ?, updated_at = ? WHERE policy_id = ?',
                                 (now[:10], new_end_date, now, policy_id))
                    conn.commit()
                    return {'success': True, 'renew_premium': policy[1]}
        except Exception as e:
            logger.error(f'财产保险续费失败: {e}')
            return {'success': False, 'error': str(e)}

    def file_property_claim(self, policy_id: str, loss_type: str,
                             claim_amount: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT owner_id, owner_name, coverage FROM property_insurance WHERE policy_id = ?', (policy_id,))
                    policy = cursor.fetchone()
                    if not policy:
                        return {'success': False, 'error': '保单不存在'}
                    if claim_amount > policy[2]:
                        return {'success': False, 'error': '理赔金额超过保额'}
                    cursor.execute('''
                        INSERT INTO property_records (policy_id, owner_id, loss_type, claim_amount, loss_date, status, description, assessed_value)
                        VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
                    ''', (policy_id, policy[0], loss_type, claim_amount, now[:10],
                          kwargs.get('description'), kwargs.get('assessed_value', claim_amount)))
                    conn.commit()
                    return {'success': True, 'claim_id': cursor.lastrowid}
        except Exception as e:
            logger.error(f'财产理赔失败: {e}')
            return {'success': False, 'error': str(e)}

    def process_property_claim(self, claim_id: int, status: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE property_records SET status = ?, processed_by = ?, processed_at = ? WHERE id = ?',
                                 (status, kwargs.get('processed_by'), now, claim_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '理赔记录不存在'}
        except Exception as e:
            logger.error(f'处理财产理赔失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 责任保险 ==========

    def enroll_liability_insurance(self, entity_id: int, entity_name: str,
                                    insurance_type: str, **kwargs) -> Dict[str, Any]:
        try:
            config = LIABILITY_INSURANCE.get(insurance_type)
            if not config:
                return {'success': False, 'error': '保险类型不存在'}
            policy_id = f"li_{uuid.uuid4().hex[:12]}"
            policy_no = f"LIP{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
            now = datetime.now().isoformat()
            end_date = (datetime.now() + timedelta(days=365)).isoformat()[:10]
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO liability_insurance (
                            policy_id, entity_id, entity_name, insurance_type,
                            coverage, premium, start_date, end_date,
                            status, policy_no, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
                    ''', (policy_id, entity_id, entity_name, insurance_type,
                          kwargs.get('coverage', config['coverage']),
                          kwargs.get('premium', config['premium']),
                          now[:10], end_date, policy_no, now, now))
                    conn.commit()
                    logger.info(f'责任投保: {entity_name} - {config["name"]}')
                    return {'success': True, 'policy_id': policy_id, 'policy_no': policy_no}
        except Exception as e:
            logger.error(f'责任投保失败: {e}')
            return {'success': False, 'error': str(e)}

    def renew_liability_insurance(self, policy_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            new_end_date = (datetime.now() + timedelta(days=365)).isoformat()[:10]
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status, premium FROM liability_insurance WHERE policy_id = ?', (policy_id,))
                    policy = cursor.fetchone()
                    if not policy:
                        return {'success': False, 'error': '保单不存在'}
                    if policy[0] != 'active':
                        return {'success': False, 'error': '保单状态不允许续费'}
                    cursor.execute('UPDATE liability_insurance SET start_date = ?, end_date = ?, updated_at = ? WHERE policy_id = ?',
                                 (now[:10], new_end_date, now, policy_id))
                    conn.commit()
                    return {'success': True, 'renew_premium': policy[1]}
        except Exception as e:
            logger.error(f'责任保险续费失败: {e}')
            return {'success': False, 'error': str(e)}

    def file_liability_claim(self, policy_id: str, claim_type: str,
                              claim_amount: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT entity_id, entity_name, coverage FROM liability_insurance WHERE policy_id = ?', (policy_id,))
                    policy = cursor.fetchone()
                    if not policy:
                        return {'success': False, 'error': '保单不存在'}
                    if claim_amount > policy[2]:
                        return {'success': False, 'error': '理赔金额超过保额'}
                    cursor.execute('''
                        INSERT INTO liability_records (policy_id, entity_id, claim_type, claim_amount, claim_date, status, description, third_party)
                        VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
                    ''', (policy_id, policy[0], claim_type, claim_amount, now[:10],
                          kwargs.get('description'), kwargs.get('third_party')))
                    conn.commit()
                    return {'success': True, 'claim_id': cursor.lastrowid}
        except Exception as e:
            logger.error(f'责任理赔失败: {e}')
            return {'success': False, 'error': str(e)}

    def process_liability_claim(self, claim_id: int, status: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE liability_records SET status = ?, processed_by = ?, processed_at = ? WHERE id = ?',
                                 (status, kwargs.get('processed_by'), now, claim_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '理赔记录不存在'}
        except Exception as e:
            logger.error(f'处理责任理赔失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_insurance_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                where_clause = f" WHERE education_type = '{education_type}'" if education_type else ""
                stats = {}
                tables = [
                    ('student_insurance', 'student_records'),
                    ('teacher_insurance', 'teacher_records'),
                    ('school_insurance', 'school_records'),
                    ('health_insurance', 'health_records'),
                    ('accident_insurance', 'accident_records'),
                    ('property_insurance', 'property_records'),
                    ('liability_insurance', 'liability_records')
                ]
                for policy_table, record_table in tables:
                    cursor.execute(f'SELECT COUNT(*) FROM {policy_table}{where_clause}')
                    stats[f'{policy_table}_count'] = cursor.fetchone()[0]
                    cursor.execute(f'SELECT SUM(premium) FROM {policy_table}{where_clause}')
                    stats[f'{policy_table}_total_premium'] = cursor.fetchone()[0] or 0
                    cursor.execute(f'SELECT COUNT(*) FROM {record_table}')
                    stats[f'{record_table}_count'] = cursor.fetchone()[0]
                    cursor.execute(f'SELECT COUNT(*) FROM {record_table} WHERE status = "approved"')
                    stats[f'{record_table}_approved_count'] = cursor.fetchone()[0]
                    cursor.execute(f'SELECT SUM(claim_amount) FROM {record_table} WHERE status = "approved"')
                    stats[f'{record_table}_approved_amount'] = cursor.fetchone()[0] or 0
                cursor.execute(f'SELECT COUNT(*) FROM education_fund{" WHERE education_type = ?" if education_type else ""}',
                             (education_type,) if education_type else ())
                stats['education_fund_count'] = cursor.fetchone()[0]
                cursor.execute(f'SELECT SUM(paid_amount) FROM education_fund{" WHERE education_type = ?" if education_type else ""}',
                             (education_type,) if education_type else ())
                stats['education_fund_total_paid'] = cursor.fetchone()[0] or 0
                return {'success': True, 'statistics': stats}
        except Exception as e:
            logger.error(f'获取保险统计失败: {e}')
            return {'success': False, 'error': str(e)}