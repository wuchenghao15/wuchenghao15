#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 学费与财务服务 (v15.4.0)
====================================
提供学费管理、缴费记录、财务统计和退费管理等综合服务。

核心能力：
1. 学费标准 - 按年级/类型设置学费标准
2. 缴费管理 - 账单生成、在线缴费、缴费记录
3. 财务统计 - 收入统计、欠费统计、报表
4. 退费管理 - 退学退费、多余退费
5. 奖学金 - 奖学金管理、减免管理
6. 账单管理 - 账单生成、催缴、核销
7. 成人学费 - 成人教育学费管理
8. K12学费 - 九年制义务教育代收费
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tuition_financial_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('TuitionFinancial')


# ========== 财务配置 ==========

# 费用类型
FEE_TYPES = {
    'tuition': {'name': '学费', 'category': 'academic', 'is_mandatory': True},
    'accommodation': {'name': '住宿费', 'category': 'living', 'is_mandatory': False},
    'meal': {'name': '伙食费', 'category': 'living', 'is_mandatory': False},
    'textbook': {'name': '教材费', 'category': 'academic', 'is_mandatory': True},
    'uniform': {'name': '校服费', 'category': 'other', 'is_mandatory': False},
    'insurance': {'name': '保险费', 'category': 'other', 'is_mandatory': False},
    'exam': {'name': '考试费', 'category': 'academic', 'is_mandatory': True},
    'activity': {'name': '活动费', 'category': 'other', 'is_mandatory': False},
    'transport': {'name': '校车费', 'category': 'living', 'is_mandatory': False},
    'material': {'name': '材料费', 'category': 'academic', 'is_mandatory': True},
    'registration': {'name': '报名费', 'category': 'other', 'is_mandatory': True},
    'deposit': {'name': '押金', 'category': 'other', 'is_mandatory': False}
}

# 缴费状态
PAYMENT_STATUS = {
    'unpaid': {'name': '未缴费', 'color': '#f5222d'},
    'partial': {'name': '部分缴费', 'color': '#faad14'},
    'paid': {'name': '已缴费', 'color': '#52c41a'},
    'overdue': {'name': '已逾期', 'color': '#f5222d'},
    'refunding': {'name': '退费中', 'color': '#1890ff'},
    'refunded': {'name': '已退费', 'color': '#8c8c8c'},
    'waived': {'name': '已减免', 'color': '#722ed1'}
}

# 支付方式
PAYMENT_METHODS = {
    'wechat': {'name': '微信支付', 'fee_rate': 0.006},
    'alipay': {'name': '支付宝', 'fee_rate': 0.006},
    'bank_transfer': {'name': '银行转账', 'fee_rate': 0.0},
    'cash': {'name': '现金', 'fee_rate': 0.0},
    'pos': {'name': 'POS刷卡', 'fee_rate': 0.0038},
    'online_banking': {'name': '网银支付', 'fee_rate': 0.0}
}

# 账单状态
BILL_STATUS = {
    'draft': '草稿',
    'issued': '已发出',
    'partial_paid': '部分缴费',
    'fully_paid': '已缴清',
    'overdue': '已逾期',
    'cancelled': '已撤销'
}

# 奖学金类型
SCHOLARSHIP_TYPES = {
    'academic': {'name': '学业奖学金', 'max_amount': 5000, 'criteria': '成绩前10%'},
    'merit': {'name': '综合奖学金', 'max_amount': 3000, 'criteria': '综合素质评定优秀'},
    'need': {'name': '助学金', 'max_amount': 8000, 'criteria': '家庭经济困难'},
    'special': {'name': '专项奖学金', 'max_amount': 10000, 'criteria': '特定竞赛或项目获奖'},
    'work_study': {'name': '勤工助学', 'max_amount': 2000, 'criteria': '参加勤工助学岗位'}
}

# 退费规则
REFUND_RULES = {
    'before_start': {'name': '开学前退费', 'refund_rate': 1.0, 'description': '退还100%学费'},
    'first_week': {'name': '第一周内退费', 'refund_rate': 0.8, 'description': '退还80%学费'},
    'first_month': {'name': '第一月内退费', 'refund_rate': 0.5, 'description': '退还50%学费'},
    'after_first_month': {'name': '一月后退费', 'refund_rate': 0.0, 'description': '不退学费'},
    'course_drop': {'name': '退课退费', 'refund_rate': 0.7, 'description': '退还70%课程费'}
}


class TuitionFinancialService:
    """学费与财务服务"""

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
                    CREATE TABLE IF NOT EXISTS fee_standards (
                        standard_id TEXT PRIMARY KEY,
                        fee_type TEXT NOT NULL,
                        education_type TEXT NOT NULL,
                        grade_level INTEGER,
                        semester TEXT,
                        amount REAL NOT NULL,
                        description TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_by INTEGER,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS bills (
                        bill_id TEXT PRIMARY KEY,
                        bill_no TEXT UNIQUE,
                        student_id INTEGER NOT NULL,
                        semester TEXT NOT NULL,
                        education_type TEXT,
                        grade_level INTEGER,
                        class_id TEXT,
                        parent_id TEXT,
                        total_amount REAL DEFAULT 0,
                        paid_amount REAL DEFAULT 0,
                        due_date TEXT,
                        issue_date TEXT,
                        status TEXT DEFAULT 'draft',
                        remark TEXT,
                        created_by INTEGER,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS bill_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        bill_id TEXT NOT NULL,
                        fee_type TEXT NOT NULL,
                        fee_name TEXT,
                        standard_amount REAL,
                        actual_amount REAL,
                        discount_amount REAL DEFAULT 0,
                        paid_amount REAL DEFAULT 0,
                        is_mandatory INTEGER DEFAULT 1,
                        description TEXT,
                        UNIQUE(bill_id, fee_type)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS payment_records (
                        payment_id TEXT PRIMARY KEY,
                        bill_id TEXT NOT NULL,
                        student_id INTEGER NOT NULL,
                        amount REAL NOT NULL,
                        payment_method TEXT,
                        transaction_no TEXT,
                        payer_name TEXT,
                        payer_phone TEXT,
                        paid_at TEXT,
                        status TEXT DEFAULT 'success',
                        remark TEXT,
                        operator_id INTEGER,
                        operator_name TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS refund_records (
                        refund_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
        bill_id TEXT,
                        payment_id TEXT,
                        refund_type TEXT,
                        refund_amount REAL NOT NULL,
                        refund_reason TEXT,
                        refund_method TEXT,
                        status TEXT DEFAULT 'pending',
                        approved_by INTEGER,
                        approved_by_name TEXT,
                        approved_at TEXT,
                        completed_at TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS scholarships (
                        scholarship_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
                        scholarship_type TEXT NOT NULL,
                        semester TEXT,
                        amount REAL NOT NULL,
                        reason TEXT,
                        awarded_by INTEGER,
                        awarded_by_name TEXT,
                        awarded_at TEXT,
                        status TEXT DEFAULT 'awarded',
                        bill_id TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS fee_waivers (
                        waiver_id TEXT PRIMARY KEY,
                        student_id INTEGER NOT NULL,
        fee_type TEXT,
                        waiver_type TEXT,
                        waiver_amount REAL,
                        waiver_rate REAL,
                        reason TEXT,
                        approved_by INTEGER,
                        approved_by_name TEXT,
                        approved_at TEXT,
                        semester TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS financial_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        stat_date TEXT NOT NULL,
                        semester TEXT,
                        education_type TEXT,
                        total_billed REAL DEFAULT 0,
                        total_collected REAL DEFAULT 0,
                        total_outstanding REAL DEFAULT 0,
                        total_refunded REAL DEFAULT 0,
                        total_scholarship REAL DEFAULT 0,
                        total_waiver REAL DEFAULT 0,
                        student_count INTEGER DEFAULT 0,
                        paid_count INTEGER DEFAULT 0,
                        unpaid_count INTEGER DEFAULT 0,
                        updated_at TEXT,
                        UNIQUE(stat_date, semester, education_type)
                    )
                ''')
                conn.commit()
                logger.info('学费与财务服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    def set_fee_standard(self, fee_type: str, education_type: str, amount: float,
                          **kwargs) -> Dict[str, Any]:
        try:
            standard_id = f"std_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO fee_standards (
                            standard_id, fee_type, education_type, grade_level,
                            semester, amount, description, is_active, created_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
                    ''', (standard_id, fee_type, education_type,
                          kwargs.get('grade_level'), kwargs.get('semester'),
                          amount, kwargs.get('description'),
                          kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'设置学费标准: {fee_type}/{education_type} = {amount}')
                    return {'success': True, 'standard_id': standard_id}
        except Exception as e:
            logger.error(f'设置学费标准失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_fee_standards(self, education_type: str = None, fee_type: str = None,
                           semester: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM fee_standards WHERE is_active = 1'
                params = []
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                if fee_type:
                    query += ' AND fee_type = ?'
                    params.append(fee_type)
                if semester:
                    query += ' AND (semester = ? OR semester IS NULL)'
                    params.append(semester)
                cursor.execute(query, params)
                standards = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'standards': standards}
        except Exception as e:
            logger.error(f'获取学费标准失败: {e}')
            return {'success': False, 'error': str(e)}

    def generate_bill(self, student_id: int, semester: str,
                       education_type: str, **kwargs) -> Dict[str, Any]:
        try:
            bill_id = f"bill_{uuid.uuid4().hex[:12]}"
            bill_no = f"BL{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
            now = datetime.now().isoformat()
            standards = self.get_fee_standards(education_type=education_type, semester=semester)
            if not standards.get('standards'):
                return {'success': False, 'error': '未找到学费标准'}
            total_amount = 0
            bill_items = []
            for std in standards['standards']:
                if kwargs.get('grade_level') and std.get('grade_level') and std['grade_level'] != kwargs['grade_level']:
                    continue
                amount = std['amount']
                total_amount += amount
                bill_items.append({
                    'fee_type': std['fee_type'],
                    'fee_name': FEE_TYPES.get(std['fee_type'], {}).get('name', std['fee_type']),
                    'standard_amount': amount,
                    'actual_amount': amount,
                    'is_mandatory': FEE_TYPES.get(std['fee_type'], {}).get('is_mandatory', True)
                })
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO bills (
                            bill_id, bill_no, student_id, semester, education_type,
                            grade_level, class_id, parent_id, total_amount, paid_amount,
                            due_date, issue_date, status, created_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, 'issued', ?, ?, ?)
                    ''', (bill_id, bill_no, student_id, semester, education_type,
                          kwargs.get('grade_level'), kwargs.get('class_id'),
                          kwargs.get('parent_id'), total_amount,
                          kwargs.get('due_date'), now[:10],
                          kwargs.get('created_by'), now, now))
                    for item in bill_items:
                        cursor.execute('''
                            INSERT INTO bill_items (
                                bill_id, fee_type, fee_name, standard_amount,
                                actual_amount, paid_amount, is_mandatory, description
                            ) VALUES (?, ?, ?, ?, ?, 0, ?, ?)
                        ''', (bill_id, item['fee_type'], item['fee_name'],
                              item['standard_amount'], item['actual_amount'],
                              item['is_mandatory'], item.get('description')))
                    conn.commit()
                    logger.info(f'生成账单: {bill_no} ({bill_id}), 总额{total_amount}')
                    return {'success': True, 'bill_id': bill_id, 'bill_no': bill_no, 'total_amount': total_amount}
        except Exception as e:
            logger.error(f'生成账单失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_bill(self, bill_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM bills WHERE bill_id = ?', (bill_id,))
                row = cursor.fetchone()
                if row:
                    bill = dict(row)
                    cursor.execute('SELECT * FROM bill_items WHERE bill_id = ?', (bill_id,))
                    bill['items'] = [dict(i) for i in cursor.fetchall()]
                    cursor.execute('SELECT * FROM payment_records WHERE bill_id = ? ORDER BY paid_at DESC', (bill_id,))
                    bill['payments'] = [dict(p) for p in cursor.fetchall()]
                    return bill
                return None
        except Exception as e:
            logger.error(f'获取账单失败: {e}')
            return None

    def get_student_bills(self, student_id: int, semester: str = None,
                           status: str = None, page: int = 1,
                           page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM bills WHERE student_id = ?'
                params = [student_id]
                if semester:
                    query += ' AND semester = ?'
                    params.append(semester)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                bills = [dict(b) for b in cursor.fetchall()]
                return {'success': True, 'bills': bills, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取学生账单失败: {e}')
            return {'success': False, 'error': str(e)}

    def make_payment(self, bill_id: str, amount: float, payment_method: str,
                      **kwargs) -> Dict[str, Any]:
        try:
            payment_id = f"pay_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT total_amount, paid_amount, status FROM bills WHERE bill_id = ?', (bill_id,))
                    bill = cursor.fetchone()
                    if not bill:
                        return {'success': False, 'error': '账单不存在'}
                    total, paid, status = bill
                    if status in ('fully_paid', 'cancelled'):
                        return {'success': False, 'error': f'账单状态不允许缴费: {status}'}
                    if paid + amount > total:
                        return {'success': False, 'error': '缴费金额超过应缴金额'}
                    transaction_no = kwargs.get('transaction_no', f"TX{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4].upper()}")
                    cursor.execute('''
                        INSERT INTO payment_records (
                            payment_id, bill_id, student_id, amount, payment_method,
                            transaction_no, payer_name, payer_phone, paid_at, status,
                            remark, operator_id, operator_name, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'success', ?, ?, ?, ?)
                    ''', (payment_id, bill_id, kwargs.get('student_id'), amount,
                          payment_method, transaction_no,
                          kwargs.get('payer_name'), kwargs.get('payer_phone'),
                          now, kwargs.get('remark'),
                          kwargs.get('operator_id'), kwargs.get('operator_name'), now))
                    new_paid = paid + amount
                    new_status = 'fully_paid' if new_paid >= total else 'partial_paid'
                    cursor.execute('''
                        UPDATE bills SET paid_amount = ?, status = ?, updated_at = ? WHERE bill_id = ?
                    ''', (new_paid, new_status, now, bill_id))
                    conn.commit()
                    logger.info(f'缴费成功: {payment_id}, 金额{amount}')
                    return {
                        'success': True,
                        'payment_id': payment_id,
                        'transaction_no': transaction_no,
                        'paid_amount': new_paid,
                        'remaining': round(total - new_paid, 2),
                        'bill_status': new_status
                    }
        except Exception as e:
            logger.error(f'缴费失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_payment_records(self, student_id: int = None, bill_id: str = None,
                             payment_method: str = None, start_date: str = None,
                             end_date: str = None, page: int = 1,
                             page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM payment_records WHERE 1=1'
                params = []
                if student_id:
                    query += ' AND student_id = ?'
                    params.append(student_id)
                if bill_id:
                    query += ' AND bill_id = ?'
                    params.append(bill_id)
                if payment_method:
                    query += ' AND payment_method = ?'
                    params.append(payment_method)
                if start_date:
                    query += ' AND paid_at >= ?'
                    params.append(start_date)
                if end_date:
                    query += ' AND paid_at <= ?'
                    params.append(end_date)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY paid_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                payments = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'payments': payments, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取缴费记录失败: {e}')
            return {'success': False, 'error': str(e)}

    def apply_refund(self, student_id: int, refund_type: str, amount: float,
                      reason: str, **kwargs) -> Dict[str, Any]:
        try:
            refund_id = f"ref_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO refund_records (
                            refund_id, student_id, bill_id, payment_id, refund_type,
                            refund_amount, refund_reason, refund_method, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                    ''', (refund_id, student_id, kwargs.get('bill_id'),
                          kwargs.get('payment_id'), refund_type, amount, reason,
                          kwargs.get('refund_method', 'bank_transfer'), now))
                    conn.commit()
                    logger.info(f'申请退费: {refund_id}, 金额{amount}')
                    return {'success': True, 'refund_id': refund_id}
        except Exception as e:
            logger.error(f'申请退费失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_refund(self, refund_id: str, approved_by: int,
                        approved: bool, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE refund_records SET
                            status = ?, approved_by = ?, approved_by_name = ?,
                            approved_at = ?, completed_at = ?
                        WHERE refund_id = ? AND status = 'pending'
                    ''', (status, approved_by, kwargs.get('approved_by_name'),
                          now, now if approved else None, refund_id))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '退费申请不存在或已处理'}
        except Exception as e:
            logger.error(f'审批退费失败: {e}')
            return {'success': False, 'error': str(e)}

    def award_scholarship(self, student_id: int, scholarship_type: str,
                           amount: float, reason: str, **kwargs) -> Dict[str, Any]:
        try:
            scholarship_id = f"sch_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO scholarships (
                            scholarship_id, student_id, scholarship_type, semester,
                            amount, reason, awarded_by, awarded_by_name, awarded_at,
                            status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'awarded', ?)
                    ''', (scholarship_id, student_id, scholarship_type,
                          kwargs.get('semester'), amount, reason,
                          kwargs.get('awarded_by'), kwargs.get('awarded_by_name'),
                          now, now))
                    conn.commit()
                    logger.info(f'发放奖学金: {scholarship_id}, 金额{amount}')
                    return {'success': True, 'scholarship_id': scholarship_id}
        except Exception as e:
            logger.error(f'发放奖学金失败: {e}')
            return {'success': False, 'error': str(e)}

    def apply_waiver(self, student_id: int, fee_type: str,
                      waiver_type: str, **kwargs) -> Dict[str, Any]:
        try:
            waiver_id = f"wvr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            waiver_amount = kwargs.get('waiver_amount', 0)
            waiver_rate = kwargs.get('waiver_rate', 0)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO fee_waivers (
                            waiver_id, student_id, fee_type, waiver_type,
                            waiver_amount, waiver_rate, reason, approved_by,
                            approved_by_name, approved_at, semester, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (waiver_id, student_id, fee_type, waiver_type,
                          waiver_amount, waiver_rate, kwargs.get('reason'),
                          kwargs.get('approved_by'), kwargs.get('approved_by_name'),
                          now, kwargs.get('semester'), now))
                    conn.commit()
                    logger.info(f'申请减免: {waiver_id}')
                    return {'success': True, 'waiver_id': waiver_id}
        except Exception as e:
            logger.error(f'申请减免失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_financial_stats(self, semester: str, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = '''
                    SELECT
                        COUNT(DISTINCT student_id) as total_students,
                        SUM(total_amount) as total_billed,
                        SUM(paid_amount) as total_collected,
                        SUM(total_amount - paid_amount) as total_outstanding,
                        SUM(CASE WHEN status = 'fully_paid' THEN 1 ELSE 0 END) as paid_count,
                        SUM(CASE WHEN status IN ('issued', 'overdue', 'partial_paid') THEN 1 ELSE 0 END) as unpaid_count
                    FROM bills WHERE semester = ?
                '''
                params = [semester]
                if education_type:
                    query += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                row = cursor.fetchone()
                cursor.execute('SELECT COALESCE(SUM(refund_amount), 0) FROM refund_records WHERE status = ?', ('approved',))
                total_refunded = cursor.fetchone()[0]
                cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM scholarships WHERE status = ? AND semester = ?', ('awarded', semester))
                total_scholarship = cursor.fetchone()[0]
                return {
                    'success': True,
                    'stats': {
                        'total_students': row[0] or 0,
                        'total_billed': round(row[1] or 0, 2),
                        'total_collected': round(row[2] or 0, 2),
                        'total_outstanding': round(row[3] or 0, 2),
                        'total_refunded': round(total_refunded, 2),
                        'total_scholarship': round(total_scholarship, 2),
                        'paid_count': row[4] or 0,
                        'unpaid_count': row[5] or 0,
                        'collection_rate': round((row[2] or 0) / (row[1] or 1) * 100, 2)
                    }
                }
        except Exception as e:
            logger.error(f'获取财务统计失败: {e}')
            return {'success': False, 'error': str(e)}

    def mark_overdue_bills(self, semester: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()[:10]
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE bills SET status = 'overdue', updated_at = ?
                        WHERE semester = ? AND status IN ('issued', 'partial_paid')
                        AND due_date < ?
                    ''', (datetime.now().isoformat(), semester, now))
                    count = cursor.rowcount
                    conn.commit()
                    logger.info(f'标记逾期账单: {count}条')
                    return {'success': True, 'overdue_count': count}
        except Exception as e:
            logger.error(f'标记逾期账单失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_student_financial_summary(self, student_id: int, semester: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = '''
                    SELECT
                        COUNT(*) as bill_count,
                        SUM(total_amount) as total_billed,
                        SUM(paid_amount) as total_paid,
                        SUM(total_amount - paid_amount) as total_outstanding
                    FROM bills WHERE student_id = ?
                '''
                params = [student_id]
                if semester:
                    query += ' AND semester = ?'
                    params.append(semester)
                cursor.execute(query, params)
                row = cursor.fetchone()
                cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM scholarships WHERE student_id = ? AND status = ?', (student_id, 'awarded'))
                scholarship_total = cursor.fetchone()[0]
                return {
                    'success': True,
                    'summary': {
                        'bill_count': row[0] or 0,
                        'total_billed': round(row[1] or 0, 2),
                        'total_paid': round(row[2] or 0, 2),
                        'total_outstanding': round(row[3] or 0, 2),
                        'scholarship_total': round(scholarship_total, 2)
                    }
                }
        except Exception as e:
            logger.error(f'获取学生财务汇总失败: {e}')
            return {'success': False, 'error': str(e)}
