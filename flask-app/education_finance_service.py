#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育金融服务 (v15.30.0)
==============================
提供教育贷款、教育理财、教育保险、教育支付、教育结算、教育融资、教育投资、资金管理等综合金融服务。

核心能力：
1. 教育贷款 - 贷款申请、审批、还款管理、逾期处理
2. 教育理财 - 理财产品、购买管理、收益计算、赎回管理
3. 教育保险 - 保险产品、投保管理、理赔处理、保单管理
4. 教育支付 - 支付下单、支付处理、退款管理、账单查询
5. 教育结算 - 结算处理、对账管理、清算管理、分账管理
6. 教育融资 - 融资申请、融资审批、融资放款、还款管理
7. 教育投资 - 投资组合、投资策略、风险评估、收益分析
8. 资金管理 - 预算管理、现金流管理、成本控制、财务报告
9. 统计分析 - 综合统计报表

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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_finance_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationFinance')


# ========== 教育金融配置 ==========

LOAN_TYPES = {
    'student_loan': {'name': '助学贷款', 'rate': 0.03, 'max_amount': 12000, 'duration': 240, 'education_types': ['adult', 'k12']},
    'tuition_loan': {'name': '学费贷款', 'rate': 0.045, 'max_amount': 50000, 'duration': 120, 'education_types': ['adult', 'k12']},
    'training_loan': {'name': '培训贷款', 'rate': 0.06, 'max_amount': 30000, 'duration': 60, 'education_types': ['adult']},
    'startup_loan': {'name': '创业贷款', 'rate': 0.05, 'max_amount': 100000, 'duration': 180, 'education_types': ['adult']},
    'study_abroad_loan': {'name': '留学贷款', 'rate': 0.055, 'max_amount': 200000, 'duration': 240, 'education_types': ['adult', 'k12']},
    'consumption_loan': {'name': '消费贷款', 'rate': 0.07, 'max_amount': 50000, 'duration': 36, 'education_types': ['adult']},
    'installment_loan': {'name': '分期贷款', 'rate': 0.035, 'max_amount': 20000, 'duration': 24, 'education_types': ['adult', 'k12']},
    'credit_loan': {'name': '信用贷款', 'rate': 0.08, 'max_amount': 100000, 'duration': 60, 'education_types': ['adult']}
}

INVESTMENT_TYPES = {
    'education_savings': {'name': '教育储蓄', 'risk': 'low', 'min_amount': 500, 'expected_return': 0.025, 'lock_period': 365},
    'education_fund': {'name': '教育基金', 'risk': 'medium', 'min_amount': 1000, 'expected_return': 0.05, 'lock_period': 730},
    'education_bond': {'name': '教育债券', 'risk': 'low', 'min_amount': 100, 'expected_return': 0.03, 'lock_period': 365},
    'education_trust': {'name': '教育信托', 'risk': 'medium', 'min_amount': 100000, 'expected_return': 0.06, 'lock_period': 1095},
    'education_insurance': {'name': '教育保险', 'risk': 'low', 'min_amount': 5000, 'expected_return': 0.035, 'lock_period': 3650},
    'education_finance': {'name': '教育理财', 'risk': 'medium', 'min_amount': 1000, 'expected_return': 0.045, 'lock_period': 180},
    'education_fixed_investment': {'name': '教育定投', 'risk': 'medium', 'min_amount': 100, 'expected_return': 0.055, 'lock_period': 730},
    'education_crowdfunding': {'name': '教育众筹', 'risk': 'high', 'min_amount': 100, 'expected_return': 0.1, 'lock_period': 365}
}

INSURANCE_TYPES = {
    'student_insurance': {'name': '学平险', 'premium': 100, 'coverage': 50000, 'education_types': ['k12']},
    'accident_insurance': {'name': '意外险', 'premium': 200, 'coverage': 100000, 'education_types': ['adult', 'k12']},
    'critical_illness': {'name': '重疾险', 'premium': 1000, 'coverage': 500000, 'education_types': ['adult', 'k12']},
    'medical_insurance': {'name': '医疗险', 'premium': 500, 'coverage': 200000, 'education_types': ['adult', 'k12']},
    'education_insurance': {'name': '教育金保险', 'premium': 5000, 'coverage': 1000000, 'education_types': ['k12']},
    'study_abroad_insurance': {'name': '留学保险', 'premium': 800, 'coverage': 300000, 'education_types': ['adult', 'k12']},
    'travel_insurance': {'name': '旅行保险', 'premium': 100, 'coverage': 50000, 'education_types': ['adult', 'k12']},
    'property_insurance': {'name': '财产保险', 'premium': 300, 'coverage': 200000, 'education_types': ['adult', 'k12']}
}

PAYMENT_METHODS = {
    'online_payment': {'name': '在线支付', 'support_types': ['adult', 'k12'], 'fee_rate': 0.006},
    'mobile_payment': {'name': '移动支付', 'support_types': ['adult', 'k12'], 'fee_rate': 0.0038},
    'bank_card': {'name': '银行卡支付', 'support_types': ['adult', 'k12'], 'fee_rate': 0.006},
    'campus_card': {'name': '校园卡支付', 'support_types': ['k12'], 'fee_rate': 0},
    'third_party': {'name': '第三方支付', 'support_types': ['adult', 'k12'], 'fee_rate': 0.005},
    'cross_border': {'name': '跨境支付', 'support_types': ['adult'], 'fee_rate': 0.01},
    'installment_payment': {'name': '分期支付', 'support_types': ['adult'], 'fee_rate': 0.008},
    'points_payment': {'name': '积分支付', 'support_types': ['adult', 'k12'], 'fee_rate': 0}
}

SETTLEMENT_TYPES = {
    'real_time': {'name': '实时结算', 'cycle': 'T+0', 'fee_rate': 0.001},
    'batch': {'name': '批量结算', 'cycle': 'T+1', 'fee_rate': 0.0005},
    'installment': {'name': '分期结算', 'cycle': 'T+N', 'fee_rate': 0.0015},
    'cross_period': {'name': '跨期结算', 'cycle': 'T+7', 'fee_rate': 0.002},
    'cross_border': {'name': '跨境结算', 'cycle': 'T+3', 'fee_rate': 0.015},
    'cross_bank': {'name': '跨行结算', 'cycle': 'T+1', 'fee_rate': 0.001},
    'pre_settlement': {'name': '预结算', 'cycle': 'T+0', 'fee_rate': 0.002},
    'post_settlement': {'name': '后结算', 'cycle': 'T+30', 'fee_rate': 0.003}
}

FINANCING_METHODS = {
    'equity_financing': {'name': '股权融资', 'max_ratio': 0.49, 'min_amount': 500000, 'education_types': ['adult']},
    'debt_financing': {'name': '债权融资', 'max_ratio': 0.6, 'min_amount': 100000, 'education_types': ['adult']},
    'government_grant': {'name': '政府资助', 'max_ratio': 0.3, 'min_amount': 0, 'education_types': ['adult', 'k12']},
    'social_donation': {'name': '社会捐赠', 'max_ratio': 1.0, 'min_amount': 0, 'education_types': ['adult', 'k12']},
    'cooperative_financing': {'name': '合作融资', 'max_ratio': 0.5, 'min_amount': 200000, 'education_types': ['adult']},
    'crowdfunding': {'name': '众筹融资', 'max_ratio': 0.3, 'min_amount': 10000, 'education_types': ['adult']},
    'policy_financing': {'name': '政策性融资', 'max_ratio': 0.5, 'min_amount': 50000, 'education_types': ['adult', 'k12']},
    'commercial_financing': {'name': '商业性融资', 'max_ratio': 0.7, 'min_amount': 100000, 'education_types': ['adult']}
}

INVESTMENT_STRATEGIES = {
    'conservative': {'name': '稳健型', 'risk_level': 1, 'max_stock_ratio': 0.3, 'description': '低风险，追求本金安全'},
    'balanced': {'name': '平衡型', 'risk_level': 2, 'max_stock_ratio': 0.5, 'description': '中等风险，兼顾收益与安全'},
    'growth': {'name': '成长型', 'risk_level': 3, 'max_stock_ratio': 0.7, 'description': '中高风险，追求较高收益'},
    'aggressive': {'name': '进取型', 'risk_level': 4, 'max_stock_ratio': 0.9, 'description': '高风险，追求最大收益'},
    'value_investing': {'name': '价值投资', 'risk_level': 2, 'max_stock_ratio': 0.6, 'description': '基于价值分析的投资策略'},
    'growth_investing': {'name': '成长投资', 'risk_level': 3, 'max_stock_ratio': 0.8, 'description': '投资成长型标的'},
    'index_investing': {'name': '指数投资', 'risk_level': 2, 'max_stock_ratio': 0.7, 'description': '跟踪指数的被动投资'},
    'portfolio': {'name': '组合投资', 'risk_level': 2, 'max_stock_ratio': 0.6, 'description': '多元化资产配置'}
}

CASH_MANAGEMENT = {
    'budget_management': {'name': '预算管理', 'description': '教育经费预算编制与执行监控'},
    'cash_flow': {'name': '现金流管理', 'description': '资金流入流出的动态管理'},
    'cost_control': {'name': '成本控制', 'description': '教育成本核算与优化'},
    'revenue_management': {'name': '收益管理', 'description': '教育收入的规划与管理'},
    'risk_control': {'name': '风险控制', 'description': '财务风险识别与防范'},
    'fund_dispatching': {'name': '资金调度', 'description': '跨部门资金调配'},
    'financial_analysis': {'name': '财务分析', 'description': '财务数据的深度分析'},
    'financial_report': {'name': '财务报告', 'description': '定期财务报表生成'}
}


class EducationFinanceService:
    """教育金融服务"""

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
                    CREATE TABLE IF NOT EXISTS education_loans (
                        loan_id TEXT PRIMARY KEY,
                        loan_type TEXT NOT NULL,
                        education_type TEXT,
                        applicant_id INTEGER NOT NULL,
                        applicant_name TEXT,
                        amount REAL NOT NULL,
                        rate REAL NOT NULL,
                        duration INTEGER NOT NULL,
                        monthly_payment REAL,
                        total_payment REAL,
                        status TEXT DEFAULT 'applied',
                        reason TEXT,
                        collateral TEXT,
                        credit_score INTEGER,
                        approved_at TEXT,
                        disbursed_at TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS loan_records (
                        record_id TEXT PRIMARY KEY,
                        loan_id TEXT NOT NULL,
                        record_type TEXT,
                        amount REAL,
                        remaining_amount REAL,
                        due_date TEXT,
                        paid_date TEXT,
                        status TEXT DEFAULT 'pending',
                        penalty REAL DEFAULT 0,
                        created_at TEXT
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS education_investment (
                        investment_id TEXT PRIMARY KEY,
                        investment_type TEXT NOT NULL,
                        education_type TEXT,
                        investor_id INTEGER NOT NULL,
                        investor_name TEXT,
                        amount REAL NOT NULL,
                        expected_return REAL,
                        actual_return REAL DEFAULT 0,
                        risk_level TEXT,
                        lock_period INTEGER,
                        maturity_date TEXT,
                        status TEXT DEFAULT 'active',
                        purchased_at TEXT,
                        redeemed_at TEXT,
                        created_at TEXT
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS investment_records (
                        record_id TEXT PRIMARY KEY,
                        investment_id TEXT NOT NULL,
                        record_type TEXT,
                        amount REAL,
                        return_amount REAL,
                        record_date TEXT,
                        description TEXT,
                        created_at TEXT
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS education_insurance (
                        policy_id TEXT PRIMARY KEY,
                        insurance_type TEXT NOT NULL,
                        education_type TEXT,
                        insured_id INTEGER NOT NULL,
                        insured_name TEXT,
                        premium REAL NOT NULL,
                        coverage REAL NOT NULL,
                        start_date TEXT,
                        end_date TEXT,
                        status TEXT DEFAULT 'active',
                        beneficiary TEXT,
                        claim_amount REAL DEFAULT 0,
                        claimed_at TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS insurance_records (
                        record_id TEXT PRIMARY KEY,
                        policy_id TEXT NOT NULL,
                        record_type TEXT,
                        amount REAL,
                        description TEXT,
                        record_date TEXT,
                        status TEXT,
                        created_at TEXT
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS education_payment (
                        payment_id TEXT PRIMARY KEY,
                        order_id TEXT NOT NULL,
                        payment_method TEXT NOT NULL,
                        education_type TEXT,
                        payer_id INTEGER,
                        payer_name TEXT,
                        amount REAL NOT NULL,
                        fee REAL DEFAULT 0,
                        status TEXT DEFAULT 'pending',
                        transaction_no TEXT,
                        paid_at TEXT,
                        refunded_at TEXT,
                        refund_amount REAL DEFAULT 0,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS payment_records (
                        record_id TEXT PRIMARY KEY,
                        payment_id TEXT NOT NULL,
                        record_type TEXT,
                        amount REAL,
                        description TEXT,
                        record_date TEXT,
                        created_at TEXT
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS education_settlement (
                        settlement_id TEXT PRIMARY KEY,
                        settlement_type TEXT NOT NULL,
                        education_type TEXT,
                        amount REAL NOT NULL,
                        fee REAL DEFAULT 0,
                        status TEXT DEFAULT 'pending',
                        settlement_date TEXT,
                        completed_at TEXT,
                        source_account TEXT,
                        target_account TEXT,
                        description TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS settlement_records (
                        record_id TEXT PRIMARY KEY,
                        settlement_id TEXT NOT NULL,
                        record_type TEXT,
                        amount REAL,
                        description TEXT,
                        record_date TEXT,
                        created_at TEXT
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS education_financing (
                        financing_id TEXT PRIMARY KEY,
                        financing_method TEXT NOT NULL,
                        education_type TEXT,
                        applicant_id INTEGER NOT NULL,
                        applicant_name TEXT,
                        project_name TEXT,
                        amount REAL NOT NULL,
                        ratio REAL,
                        status TEXT DEFAULT 'applied',
                        business_plan TEXT,
                        approved_at TEXT,
                        funded_at TEXT,
                        repayment_schedule TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS financing_records (
                        record_id TEXT PRIMARY KEY,
                        financing_id TEXT NOT NULL,
                        record_type TEXT,
                        amount REAL,
                        description TEXT,
                        record_date TEXT,
                        status TEXT,
                        created_at TEXT
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS education_investment_analysis (
                        analysis_id TEXT PRIMARY KEY,
                        investment_id TEXT,
                        strategy_type TEXT NOT NULL,
                        risk_score INTEGER,
                        expected_return REAL,
                        actual_return REAL DEFAULT 0,
                        portfolio TEXT,
                        performance_benchmark TEXT,
                        analysis_date TEXT,
                        created_at TEXT
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS analysis_records (
                        record_id TEXT PRIMARY KEY,
                        analysis_id TEXT NOT NULL,
                        metric_name TEXT,
                        metric_value REAL,
                        metric_date TEXT,
                        created_at TEXT
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS education_cash_management (
                        cash_id TEXT PRIMARY KEY,
                        management_type TEXT NOT NULL,
                        education_type TEXT,
                        organization_id INTEGER,
                        organization_name TEXT,
                        budget_amount REAL DEFAULT 0,
                        actual_amount REAL DEFAULT 0,
                        balance REAL DEFAULT 0,
                        period TEXT,
                        status TEXT DEFAULT 'active',
                        description TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cash_records (
                        record_id TEXT PRIMARY KEY,
                        cash_id TEXT NOT NULL,
                        record_type TEXT,
                        amount REAL,
                        description TEXT,
                        record_date TEXT,
                        balance_after REAL,
                        created_at TEXT
                    )
                ''')

                conn.commit()
                logger.info('教育金融服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 教育贷款 ==========

    def apply_loan(self, loan_type: str, applicant_id: int,
                    amount: float, duration: int, **kwargs) -> Dict[str, Any]:
        try:
            config = LOAN_TYPES.get(loan_type)
            if not config:
                return {'success': False, 'error': '贷款类型不存在'}

            education_type = kwargs.get('education_type', 'adult')
            if education_type not in config.get('education_types', ['adult']):
                return {'success': False, 'error': f'{config["name"]}不支持{education_type}教育'}

            if amount > config['max_amount']:
                return {'success': False, 'error': f'贷款金额超过上限{config["max_amount"]}'}

            rate = config['rate']
            monthly_rate = rate / 12
            if monthly_rate > 0:
                monthly_payment = amount * monthly_rate * (1 + monthly_rate) ** duration / ((1 + monthly_rate) ** duration - 1)
            else:
                monthly_payment = amount / duration
            total_payment = monthly_payment * duration

            loan_id = f"eln_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()

            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO education_loans (
                            loan_id, loan_type, education_type, applicant_id,
                            applicant_name, amount, rate, duration,
                            monthly_payment, total_payment, status, reason,
                            collateral, credit_score, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'applied', ?, ?, ?, ?, ?)
                    ''', (loan_id, loan_type, education_type, applicant_id,
                          kwargs.get('applicant_name'), amount, rate, duration,
                          round(monthly_payment, 2), round(total_payment, 2),
                          kwargs.get('reason'), kwargs.get('collateral'),
                          kwargs.get('credit_score', 600), now, now))
                    conn.commit()
                    logger.info(f'申请贷款: {config["name"]} {amount}元 ({loan_id})')
                    return {'success': True, 'loan_id': loan_id, 'monthly_payment': round(monthly_payment, 2), 'total_payment': round(total_payment, 2)}
        except Exception as e:
            logger.error(f'申请贷款失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_loan(self, loan_id: str, approved: bool, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE education_loans SET status = ?, approved_at = ?, updated_at = ? WHERE loan_id = ? AND status = ?',
                                 (status, now, now, loan_id, 'applied'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '贷款状态不允许审核'}
        except Exception as e:
            logger.error(f'审核贷款失败: {e}')
            return {'success': False, 'error': str(e)}

    def disburse_loan(self, loan_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT amount, duration, monthly_payment FROM education_loans WHERE loan_id = ? AND status = ?',
                                 (loan_id, 'approved'))
                    loan = cursor.fetchone()
                    if not loan:
                        return {'success': False, 'error': '贷款未通过审核或已放款'}

                    cursor.execute('UPDATE education_loans SET status = ?, disbursed_at = ?, updated_at = ? WHERE loan_id = ?',
                                 ('disbursed', now, now, loan_id))

                    amount, duration, monthly_payment = loan
                    remaining_amount = amount
                    for i in range(duration):
                        due_date = (datetime.now() + timedelta(days=30 * (i + 1))).strftime('%Y-%m-%d')
                        record_id = f"lrc_{uuid.uuid4().hex[:8]}"
                        cursor.execute('''
                            INSERT INTO loan_records (record_id, loan_id, record_type, amount, remaining_amount, due_date, status, created_at)
                            VALUES (?, ?, 'installment', ?, ?, ?, 'pending', ?)
                        ''', (record_id, loan_id, round(monthly_payment, 2), round(remaining_amount, 2), due_date, now))
                        remaining_amount -= monthly_payment

                    conn.commit()
                    logger.info(f'放款成功: {amount}元 ({loan_id})')
                    return {'success': True}
        except Exception as e:
            logger.error(f'放款失败: {e}')
            return {'success': False, 'error': str(e)}

    def repay_loan(self, loan_id: str, amount: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM education_loans WHERE loan_id = ?', (loan_id,))
                    loan = cursor.fetchone()
                    if not loan or loan[0] != 'disbursed':
                        return {'success': False, 'error': '贷款未放款或已结清'}

                    cursor.execute('SELECT record_id, amount, remaining_amount FROM loan_records WHERE loan_id = ? AND status = ? ORDER BY due_date ASC LIMIT 1',
                                 (loan_id, 'pending'))
                    record = cursor.fetchone()
                    if not record:
                        return {'success': False, 'error': '无待还款记录'}

                    record_id, installment_amount, remaining = record
                    actual_pay = min(amount, installment_amount)

                    cursor.execute('UPDATE loan_records SET status = ?, paid_date = ?, amount = ? WHERE record_id = ?',
                                 ('paid', now, actual_pay, record_id))

                    if actual_pay < installment_amount:
                        penalty = (installment_amount - actual_pay) * 0.0005
                        cursor.execute('UPDATE loan_records SET penalty = ? WHERE record_id = ?', (penalty, record_id))

                    remaining_after = remaining - actual_pay
                    cursor.execute('UPDATE loan_records SET remaining_amount = ? WHERE record_id = ?', (round(remaining_after, 2), record_id))

                    repay_record_id = f"lrp_{uuid.uuid4().hex[:8]}"
                    cursor.execute('''
                        INSERT INTO loan_records (record_id, loan_id, record_type, amount, paid_date, status, created_at)
                        VALUES (?, ?, 'repayment', ?, ?, 'completed', ?)
                    ''', (repay_record_id, loan_id, actual_pay, now, now))

                    cursor.execute('SELECT COUNT(*) FROM loan_records WHERE loan_id = ? AND status = ?', (loan_id, 'pending'))
                    pending_count = cursor.fetchone()[0]
                    if pending_count == 0:
                        cursor.execute('UPDATE education_loans SET status = ?, updated_at = ? WHERE loan_id = ?', ('settled', now, loan_id))

                    conn.commit()
                    return {'success': True, 'paid_amount': actual_pay, 'remaining_amount': round(remaining_after, 2)}
        except Exception as e:
            logger.error(f'还款失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 教育理财 ==========

    def purchase_investment(self, investment_type: str, investor_id: int,
                             amount: float, **kwargs) -> Dict[str, Any]:
        try:
            config = INVESTMENT_TYPES.get(investment_type)
            if not config:
                return {'success': False, 'error': '理财产品不存在'}

            if amount < config['min_amount']:
                return {'success': False, 'error': f'最低购买金额{config["min_amount"]}元'}

            maturity_date = (datetime.now() + timedelta(days=config['lock_period'])).strftime('%Y-%m-%d')
            investment_id = f"ein_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()

            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO education_investment (
                            investment_id, investment_type, education_type,
                            investor_id, investor_name, amount,
                            expected_return, risk_level, lock_period,
                            maturity_date, status, purchased_at, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (investment_id, investment_type, kwargs.get('education_type', 'adult'),
                          investor_id, kwargs.get('investor_name'), amount,
                          config['expected_return'], config['risk'], config['lock_period'],
                          maturity_date, now, now))
                    conn.commit()
                    logger.info(f'购买理财: {config["name"]} {amount}元 ({investment_id})')
                    return {'success': True, 'investment_id': investment_id, 'maturity_date': maturity_date}
        except Exception as e:
            logger.error(f'购买理财失败: {e}')
            return {'success': False, 'error': str(e)}

    def calculate_return(self, investment_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM education_investment WHERE investment_id = ?', (investment_id,))
                investment = cursor.fetchone()
                if not investment:
                    return {'success': False, 'error': '投资记录不存在'}

                config = INVESTMENT_TYPES.get(investment['investment_type'], {})
                days_held = (datetime.now() - datetime.fromisoformat(investment['purchased_at'])).days
                lock_period = investment['lock_period']
                if days_held < 0:
                    days_held = 0

                expected_return_amount = investment['amount'] * config.get('expected_return', 0) * (days_held / 365)
                remaining_days = max(0, lock_period - days_held)

                return {
                    'success': True,
                    'investment_id': investment_id,
                    'amount': investment['amount'],
                    'days_held': days_held,
                    'remaining_days': remaining_days,
                    'expected_return': round(expected_return_amount, 2),
                    'total_expected': round(investment['amount'] + expected_return_amount, 2)
                }
        except Exception as e:
            logger.error(f'计算收益失败: {e}')
            return {'success': False, 'error': str(e)}

    def redeem_investment(self, investment_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM education_investment WHERE investment_id = ?', (investment_id,))
                    investment = cursor.fetchone()
                    if not investment:
                        return {'success': False, 'error': '投资记录不存在'}

                    if investment['status'] != 'active':
                        return {'success': False, 'error': '投资已赎回或已到期'}

                    days_held = (datetime.now() - datetime.fromisoformat(investment['purchased_at'])).days
                    lock_period = investment['lock_period']

                    config = INVESTMENT_TYPES.get(investment['investment_type'], {})
                    actual_return = investment['amount'] * config.get('expected_return', 0) * (days_held / 365)

                    if days_held < lock_period:
                        penalty = actual_return * 0.1
                        actual_return -= penalty
                    else:
                        penalty = 0

                    cursor.execute('UPDATE education_investment SET status = ?, redeemed_at = ?, actual_return = ? WHERE investment_id = ?',
                                 ('redeemed', now, round(actual_return, 2), investment_id))

                    record_id = f"inv_{uuid.uuid4().hex[:8]}"
                    cursor.execute('''
                        INSERT INTO investment_records (record_id, investment_id, record_type, amount, return_amount, record_date, description, created_at)
                        VALUES (?, ?, 'redemption', ?, ?, ?, ?, ?)
                    ''', (record_id, investment_id, investment['amount'], round(actual_return, 2), now,
                          f'提前赎回扣罚{round(penalty, 2)}元' if penalty > 0 else '正常赎回', now))

                    conn.commit()
                    return {'success': True, 'redeemed_amount': round(investment['amount'] + actual_return, 2), 'penalty': round(penalty, 2)}
        except Exception as e:
            logger.error(f'赎回理财失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_investments(self, investor_id: int = None, status: str = None,
                          page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM education_investment WHERE 1=1'
                params = []
                if investor_id:
                    query += ' AND investor_id = ?'
                    params.append(investor_id)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                investments = [dict(i) for i in cursor.fetchall()]
                return {'success': True, 'investments': investments, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取投资列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 教育保险 ==========

    def purchase_insurance(self, insurance_type: str, insured_id: int,
                            **kwargs) -> Dict[str, Any]:
        try:
            config = INSURANCE_TYPES.get(insurance_type)
            if not config:
                return {'success': False, 'error': '保险类型不存在'}

            education_type = kwargs.get('education_type', 'adult')
            if education_type not in config.get('education_types', ['adult']):
                return {'success': False, 'error': f'{config["name"]}不支持{education_type}教育'}

            start_date = datetime.now().strftime('%Y-%m-%d')
            end_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
            policy_id = f"eis_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()

            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO education_insurance (
                            policy_id, insurance_type, education_type,
                            insured_id, insured_name, premium, coverage,
                            start_date, end_date, status, beneficiary,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
                    ''', (policy_id, insurance_type, education_type,
                          insured_id, kwargs.get('insured_name'), config['premium'],
                          config['coverage'], start_date, end_date,
                          kwargs.get('beneficiary'), now, now))
                    conn.commit()
                    logger.info(f'购买保险: {config["name"]} ({policy_id})')
                    return {'success': True, 'policy_id': policy_id, 'premium': config['premium'], 'coverage': config['coverage']}
        except Exception as e:
            logger.error(f'购买保险失败: {e}')
            return {'success': False, 'error': str(e)}

    def apply_claim(self, policy_id: str, amount: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM education_insurance WHERE policy_id = ?', (policy_id,))
                    policy = cursor.fetchone()
                    if not policy:
                        return {'success': False, 'error': '保单不存在'}

                    if policy['status'] != 'active':
                        return {'success': False, 'error': '保单状态异常'}

                    if amount > policy['coverage']:
                        return {'success': False, 'error': f'理赔金额超过保额{policy["coverage"]}'}

                    cursor.execute('UPDATE education_insurance SET status = ?, claim_amount = ?, claimed_at = ?, updated_at = ? WHERE policy_id = ?',
                                 ('claiming', amount, now, now, policy_id))

                    record_id = f"icm_{uuid.uuid4().hex[:8]}"
                    cursor.execute('''
                        INSERT INTO insurance_records (record_id, policy_id, record_type, amount, description, record_date, status, created_at)
                        VALUES (?, ?, 'claim', ?, ?, ?, 'pending', ?)
                    ''', (record_id, policy_id, amount, kwargs.get('description'), now, now))

                    conn.commit()
                    return {'success': True, 'claim_id': record_id}
        except Exception as e:
            logger.error(f'申请理赔失败: {e}')
            return {'success': False, 'error': str(e)}

    def settle_claim(self, claim_id: str, approved: bool, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT policy_id, amount FROM insurance_records WHERE record_id = ? AND status = ?',
                                 (claim_id, 'pending'))
                    record = cursor.fetchone()
                    if not record:
                        return {'success': False, 'error': '理赔申请不存在'}

                    policy_id, amount = record
                    status = 'approved' if approved else 'rejected'

                    cursor.execute('UPDATE insurance_records SET status = ?, description = ? WHERE record_id = ?',
                                 (status, kwargs.get('reason'), claim_id))

                    if approved:
                        cursor.execute('UPDATE education_insurance SET status = ?, updated_at = ? WHERE policy_id = ?',
                                     ('settled', now, policy_id))

                    conn.commit()
                    return {'success': True, 'status': status, 'amount': amount if approved else 0}
        except Exception as e:
            logger.error(f'理赔处理失败: {e}')
            return {'success': False, 'error': str(e)}

    def renew_insurance(self, policy_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM education_insurance WHERE policy_id = ?', (policy_id,))
                    policy = cursor.fetchone()
                    if not policy:
                        return {'success': False, 'error': '保单不存在'}

                    config = INSURANCE_TYPES.get(policy['insurance_type'], {})
                    new_start_date = datetime.now().strftime('%Y-%m-%d')
                    new_end_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')

                    cursor.execute('''
                        UPDATE education_insurance SET
                            status = 'active', premium = ?, coverage = ?,
                            start_date = ?, end_date = ?, claim_amount = 0,
                            claimed_at = NULL, updated_at = ?
                        WHERE policy_id = ?
                    ''', (config.get('premium', policy['premium']), config.get('coverage', policy['coverage']),
                          new_start_date, new_end_date, now, policy_id))

                    record_id = f"irn_{uuid.uuid4().hex[:8]}"
                    cursor.execute('''
                        INSERT INTO insurance_records (record_id, policy_id, record_type, amount, description, record_date, status, created_at)
                        VALUES (?, ?, 'renewal', ?, ?, ?, 'completed', ?)
                    ''', (record_id, policy_id, config.get('premium', policy['premium']), '保单续费', now, now))

                    conn.commit()
                    return {'success': True, 'new_end_date': new_end_date}
        except Exception as e:
            logger.error(f'续期保险失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 教育支付 ==========

    def create_payment(self, order_id: str, payment_method: str, amount: float,
                        **kwargs) -> Dict[str, Any]:
        try:
            config = PAYMENT_METHODS.get(payment_method)
            if not config:
                return {'success': False, 'error': '支付方式不存在'}

            education_type = kwargs.get('education_type', 'adult')
            if education_type not in config.get('support_types', ['adult']):
                return {'success': False, 'error': f'{config["name"]}不支持{education_type}教育'}

            fee = amount * config['fee_rate']
            payment_id = f"epy_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()

            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO education_payment (
                            payment_id, order_id, payment_method, education_type,
                            payer_id, payer_name, amount, fee, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                    ''', (payment_id, order_id, payment_method, education_type,
                          kwargs.get('payer_id'), kwargs.get('payer_name'),
                          amount, round(fee, 2), now, now))
                    conn.commit()
                    logger.info(f'创建支付: {amount}元 ({payment_id})')
                    return {'success': True, 'payment_id': payment_id, 'fee': round(fee, 2)}
        except Exception as e:
            logger.error(f'创建支付失败: {e}')
            return {'success': False, 'error': str(e)}

    def process_payment(self, payment_id: str, transaction_no: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE education_payment SET status = ?, transaction_no = ?, paid_at = ?, updated_at = ? WHERE payment_id = ? AND status = ?',
                                 ('paid', transaction_no, now, now, payment_id, 'pending'))
                    if cursor.rowcount > 0:
                        record_id = f"prc_{uuid.uuid4().hex[:8]}"
                        cursor.execute('''
                            INSERT INTO payment_records (record_id, payment_id, record_type, amount, description, record_date, created_at)
                            VALUES (?, ?, 'payment', ?, '支付成功', ?, ?)
                        ''', (record_id, payment_id, transaction_no, now, now))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '支付状态异常'}
        except Exception as e:
            logger.error(f'处理支付失败: {e}')
            return {'success': False, 'error': str(e)}

    def refund_payment(self, payment_id: str, amount: float = None) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM education_payment WHERE payment_id = ?', (payment_id,))
                    payment = cursor.fetchone()
                    if not payment:
                        return {'success': False, 'error': '支付记录不存在'}

                    if payment['status'] != 'paid':
                        return {'success': False, 'error': '支付未成功，无法退款'}

                    refund_amount = amount if amount else payment['amount']
                    if refund_amount > payment['amount'] - payment['refund_amount']:
                        return {'success': False, 'error': '退款金额超过可退款余额'}

                    cursor.execute('UPDATE education_payment SET status = ?, refunded_at = ?, refund_amount = ?, updated_at = ? WHERE payment_id = ?',
                                 ('refunded', now, round(refund_amount, 2), now, payment_id))

                    record_id = f"rfd_{uuid.uuid4().hex[:8]}"
                    cursor.execute('''
                        INSERT INTO payment_records (record_id, payment_id, record_type, amount, description, record_date, created_at)
                        VALUES (?, ?, 'refund', ?, '退款', ?, ?)
                    ''', (record_id, payment_id, refund_amount, now, now))

                    conn.commit()
                    return {'success': True, 'refund_amount': refund_amount}
        except Exception as e:
            logger.error(f'退款失败: {e}')
            return {'success': False, 'error': str(e)}

    def query_bill(self, payer_id: int = None, order_id: str = None,
                    status: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM education_payment WHERE 1=1'
                params = []
                if payer_id:
                    query += ' AND payer_id = ?'
                    params.append(payer_id)
                if order_id:
                    query += ' AND order_id = ?'
                    params.append(order_id)
                if status:
                    query += ' AND status = ?'
                    params.append(status)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                payments = [dict(p) for p in cursor.fetchall()]
                return {'success': True, 'payments': payments, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'查询账单失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM education_payment WHERE payment_id = ?', (payment_id,))
                payment = cursor.fetchone()
                if not payment:
                    return {'success': False, 'error': '支付记录不存在'}
                return {'success': True, 'payment': dict(payment)}
        except Exception as e:
            logger.error(f'查询支付状态失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 教育结算 ==========

    def create_settlement(self, settlement_type: str, amount: float,
                          **kwargs) -> Dict[str, Any]:
        try:
            config = SETTLEMENT_TYPES.get(settlement_type)
            if not config:
                return {'success': False, 'error': '结算类型不存在'}

            fee = amount * config['fee_rate']
            settlement_id = f"est_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()

            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO education_settlement (
                            settlement_id, settlement_type, education_type,
                            amount, fee, status, source_account,
                            target_account, description, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?, ?)
                    ''', (settlement_id, settlement_type, kwargs.get('education_type', 'adult'),
                          amount, round(fee, 2), kwargs.get('source_account'),
                          kwargs.get('target_account'), kwargs.get('description'), now, now))
                    conn.commit()
                    logger.info(f'创建结算: {amount}元 ({settlement_id})')
                    return {'success': True, 'settlement_id': settlement_id, 'fee': round(fee, 2)}
        except Exception as e:
            logger.error(f'创建结算失败: {e}')
            return {'success': False, 'error': str(e)}

    def process_settlement(self, settlement_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE education_settlement SET status = ?, completed_at = ?, updated_at = ? WHERE settlement_id = ? AND status = ?',
                                 ('completed', now, now, settlement_id, 'pending'))
                    if cursor.rowcount > 0:
                        record_id = f"stc_{uuid.uuid4().hex[:8]}"
                        cursor.execute('''
                            INSERT INTO settlement_records (record_id, settlement_id, record_type, amount, description, record_date, created_at)
                            VALUES (?, ?, 'settlement', ?, '结算完成', ?, ?)
                        ''', (record_id, settlement_id, now, now, now))
                        conn.commit()
                        return {'success': True}
                    return {'success': False, 'error': '结算状态异常'}
        except Exception as e:
            logger.error(f'处理结算失败: {e}')
            return {'success': False, 'error': str(e)}

    def reconcile_settlement(self, settlement_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM education_settlement WHERE settlement_id = ?', (settlement_id,))
                settlement = cursor.fetchone()
                if not settlement:
                    return {'success': False, 'error': '结算记录不存在'}

                cursor.execute('SELECT SUM(amount) FROM settlement_records WHERE settlement_id = ?', (settlement_id,))
                recorded_amount = cursor.fetchone()[0] or 0

                discrepancy = settlement['amount'] - recorded_amount
                is_reconciled = abs(discrepancy) < 0.01

                record_id = f"rcn_{uuid.uuid4().hex[:8]}"
                cursor.execute('''
                    INSERT INTO settlement_records (record_id, settlement_id, record_type, amount, description, record_date, created_at)
                    VALUES (?, ?, 'reconciliation', ?, ?, ?, ?)
                ''', (record_id, settlement_id, discrepancy, f'对账差异: {discrepancy:.2f}', datetime.now().strftime('%Y-%m-%d'), datetime.now().isoformat()))

                conn.commit()
                return {'success': True, 'is_reconciled': is_reconciled, 'discrepancy': round(discrepancy, 2)}
        except Exception as e:
            logger.error(f'对账失败: {e}')
            return {'success': False, 'error': str(e)}

    def split_settlement(self, settlement_id: str, splits: List[Dict[str, Any]]) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT amount FROM education_settlement WHERE settlement_id = ?', (settlement_id,))
                    settlement = cursor.fetchone()
                    if not settlement:
                        return {'success': False, 'error': '结算记录不存在'}

                    total_split = sum(s['amount'] for s in splits)
                    if abs(total_split - settlement['amount']) > 0.01:
                        return {'success': False, 'error': '分账金额总和与结算金额不一致'}

                    for split in splits:
                        record_id = f"spt_{uuid.uuid4().hex[:8]}"
                        cursor.execute('''
                            INSERT INTO settlement_records (record_id, settlement_id, record_type, amount, description, record_date, created_at)
                            VALUES (?, ?, 'split', ?, ?, ?, ?)
                        ''', (record_id, settlement_id, split['amount'], split.get('description', f'分账至{split.get("target", "")}'), now, now))

                    conn.commit()
                    return {'success': True, 'split_count': len(splits)}
        except Exception as e:
            logger.error(f'分账失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 教育融资 ==========

    def apply_financing(self, financing_method: str, applicant_id: int,
                        project_name: str, amount: float, **kwargs) -> Dict[str, Any]:
        try:
            config = FINANCING_METHODS.get(financing_method)
            if not config:
                return {'success': False, 'error': '融资方式不存在'}

            education_type = kwargs.get('education_type', 'adult')
            if education_type not in config.get('education_types', ['adult']):
                return {'success': False, 'error': f'{config["name"]}不支持{education_type}教育'}

            if amount < config['min_amount']:
                return {'success': False, 'error': f'最低融资金额{config["min_amount"]}元'}

            financing_id = f"efn_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()

            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO education_financing (
                            financing_id, financing_method, education_type,
                            applicant_id, applicant_name, project_name,
                            amount, ratio, status, business_plan,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'applied', ?, ?, ?)
                    ''', (financing_id, financing_method, education_type,
                          applicant_id, kwargs.get('applicant_name'), project_name,
                          amount, config['max_ratio'], kwargs.get('business_plan'),
                          now, now))
                    conn.commit()
                    logger.info(f'申请融资: {config["name"]} {amount}元 ({financing_id})')
                    return {'success': True, 'financing_id': financing_id}
        except Exception as e:
            logger.error(f'申请融资失败: {e}')
            return {'success': False, 'error': str(e)}

    def approve_financing(self, financing_id: str, approved: bool, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE education_financing SET status = ?, approved_at = ?, updated_at = ? WHERE financing_id = ? AND status = ?',
                                 (status, now, now, financing_id, 'applied'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        return {'success': True, 'status': status}
                    return {'success': False, 'error': '融资状态不允许审核'}
        except Exception as e:
            logger.error(f'审核融资失败: {e}')
            return {'success': False, 'error': str(e)}

    def fund_financing(self, financing_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT amount FROM education_financing WHERE financing_id = ? AND status = ?',
                                 (financing_id, 'approved'))
                    financing = cursor.fetchone()
                    if not financing:
                        return {'success': False, 'error': '融资未通过审核或已放款'}

                    cursor.execute('UPDATE education_financing SET status = ?, funded_at = ?, updated_at = ? WHERE financing_id = ?',
                                 ('funded', now, now, financing_id))

                    record_id = f"fnd_{uuid.uuid4().hex[:8]}"
                    cursor.execute('''
                        INSERT INTO financing_records (record_id, financing_id, record_type, amount, description, record_date, status, created_at)
                        VALUES (?, ?, 'funding', ?, '融资放款', ?, 'completed', ?)
                    ''', (record_id, financing_id, financing[0], now, now))

                    conn.commit()
                    logger.info(f'融资放款: {financing[0]}元 ({financing_id})')
                    return {'success': True}
        except Exception as e:
            logger.error(f'融资放款失败: {e}')
            return {'success': False, 'error': str(e)}

    def repay_financing(self, financing_id: str, amount: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM education_financing WHERE financing_id = ?', (financing_id,))
                    financing = cursor.fetchone()
                    if not financing or financing[0] != 'funded':
                        return {'success': False, 'error': '融资未放款或已结清'}

                    record_id = f"rpf_{uuid.uuid4().hex[:8]}"
                    cursor.execute('''
                        INSERT INTO financing_records (record_id, financing_id, record_type, amount, description, record_date, status, created_at)
                        VALUES (?, ?, 'repayment', ?, ?, ?, 'completed', ?)
                    ''', (record_id, financing_id, amount, kwargs.get('description', '还款'), now, now))

                    cursor.execute('SELECT SUM(amount) FROM financing_records WHERE financing_id = ? AND record_type = ?',
                                 (financing_id, 'repayment'))
                    total_repaid = cursor.fetchone()[0] or 0

                    cursor.execute('SELECT amount FROM education_financing WHERE financing_id = ?', (financing_id,))
                    total_amount = cursor.fetchone()[0]

                    if total_repaid >= total_amount:
                        cursor.execute('UPDATE education_financing SET status = ?, updated_at = ? WHERE financing_id = ?',
                                     ('settled', now, financing_id))

                    conn.commit()
                    return {'success': True, 'total_repaid': round(total_repaid, 2)}
        except Exception as e:
            logger.error(f'融资还款失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 教育投资 ==========

    def create_investment_portfolio(self, strategy_type: str, investor_id: int,
                                     **kwargs) -> Dict[str, Any]:
        try:
            config = INVESTMENT_STRATEGIES.get(strategy_type)
            if not config:
                return {'success': False, 'error': '投资策略不存在'}

            analysis_id = f"eia_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()

            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO education_investment_analysis (
                            analysis_id, strategy_type, risk_score,
                            expected_return, portfolio, analysis_date,
                            created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (analysis_id, strategy_type, config['risk_level'],
                          kwargs.get('expected_return', 0.05),
                          json.dumps(kwargs.get('portfolio', {})),
                          now[:10], now))
                    conn.commit()
                    logger.info(f'创建投资组合: {config["name"]} ({analysis_id})')
                    return {'success': True, 'analysis_id': analysis_id}
        except Exception as e:
            logger.error(f'创建投资组合失败: {e}')
            return {'success': False, 'error': str(e)}

    def evaluate_risk(self, analysis_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM education_investment_analysis WHERE analysis_id = ?', (analysis_id,))
                analysis = cursor.fetchone()
                if not analysis:
                    return {'success': False, 'error': '投资分析记录不存在'}

                config = INVESTMENT_STRATEGIES.get(analysis['strategy_type'], {})
                portfolio = json.loads(analysis['portfolio']) if analysis['portfolio'] else {}

                risk_factors = []
                total_weight = sum(portfolio.values(), 0)
                if total_weight > 0:
                    for asset, weight in portfolio.items():
                        if 'stock' in asset.lower() or 'equity' in asset.lower():
                            risk_factors.append(weight / total_weight * config.get('risk_level', 2) * 0.5)
                        elif 'bond' in asset.lower() or 'fixed' in asset.lower():
                            risk_factors.append(weight / total_weight * 1)
                        else:
                            risk_factors.append(weight / total_weight * 2)

                risk_score = sum(risk_factors) if risk_factors else config.get('risk_level', 2)

                return {
                    'success': True,
                    'analysis_id': analysis_id,
                    'risk_score': round(risk_score, 2),
                    'risk_level': config.get('name'),
                    'risk_description': config.get('description')
                }
        except Exception as e:
            logger.error(f'风险评估失败: {e}')
            return {'success': False, 'error': str(e)}

    def analyze_performance(self, analysis_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM education_investment_analysis WHERE analysis_id = ?', (analysis_id,))
                analysis = cursor.fetchone()
                if not analysis:
                    return {'success': False, 'error': '投资分析记录不存在'}

                cursor.execute('SELECT SUM(metric_value) FROM analysis_records WHERE analysis_id = ? AND metric_name = ?',
                             (analysis_id, 'return'))
                total_return = cursor.fetchone()[0] or 0

                cursor.execute('SELECT SUM(metric_value) FROM analysis_records WHERE analysis_id = ? AND metric_name = ?',
                             (analysis_id, 'risk'))
                total_risk = cursor.fetchone()[0] or 0

                sharpe_ratio = total_return / (total_risk + 0.0001)

                return {
                    'success': True,
                    'analysis_id': analysis_id,
                    'total_return': round(total_return, 4),
                    'total_risk': round(total_risk, 4),
                    'sharpe_ratio': round(sharpe_ratio, 4),
                    'expected_return': analysis['expected_return'],
                    'actual_return': analysis['actual_return']
                }
        except Exception as e:
            logger.error(f'绩效分析失败: {e}')
            return {'success': False, 'error': str(e)}

    def add_metric_record(self, analysis_id: str, metric_name: str,
                           metric_value: float) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            record_id = f"amr_{uuid.uuid4().hex[:8]}"
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO analysis_records (record_id, analysis_id, metric_name, metric_value, metric_date, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (record_id, analysis_id, metric_name, metric_value, now[:10], now))
                    conn.commit()
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'添加指标记录失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 资金管理 ==========

    def create_budget(self, organization_id: int, management_type: str,
                       budget_amount: float, **kwargs) -> Dict[str, Any]:
        try:
            config = CASH_MANAGEMENT.get(management_type)
            if not config:
                return {'success': False, 'error': '资金管理类型不存在'}

            cash_id = f"ecm_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()

            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO education_cash_management (
                            cash_id, management_type, education_type,
                            organization_id, organization_name, budget_amount,
                            actual_amount, balance, period, status,
                            description, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, 'active', ?, ?, ?)
                    ''', (cash_id, management_type, kwargs.get('education_type', 'adult'),
                          organization_id, kwargs.get('organization_name'),
                          budget_amount, budget_amount,
                          kwargs.get('period', datetime.now().strftime('%Y%m')),
                          kwargs.get('description', config['description']), now, now))
                    conn.commit()
                    logger.info(f'创建资金管理: {config["name"]} {budget_amount}元 ({cash_id})')
                    return {'success': True, 'cash_id': cash_id}
        except Exception as e:
            logger.error(f'创建资金管理失败: {e}')
            return {'success': False, 'error': str(e)}

    def record_cash_flow(self, cash_id: str, record_type: str, amount: float,
                          **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT balance, actual_amount FROM education_cash_management WHERE cash_id = ?', (cash_id,))
                    cash = cursor.fetchone()
                    if not cash:
                        return {'success': False, 'error': '资金管理记录不存在'}

                    balance, actual_amount = cash
                    if record_type == 'income':
                        new_balance = balance + amount
                        new_actual = actual_amount + amount
                    elif record_type == 'expense':
                        if amount > balance:
                            return {'success': False, 'error': '余额不足'}
                        new_balance = balance - amount
                        new_actual = actual_amount + amount
                    else:
                        return {'success': False, 'error': '记录类型无效'}

                    cursor.execute('UPDATE education_cash_management SET balance = ?, actual_amount = ?, updated_at = ? WHERE cash_id = ?',
                                 (round(new_balance, 2), round(new_actual, 2), now, cash_id))

                    record_id = f"cfl_{uuid.uuid4().hex[:8]}"
                    cursor.execute('''
                        INSERT INTO cash_records (record_id, cash_id, record_type, amount, description, record_date, balance_after, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (record_id, cash_id, record_type, amount, kwargs.get('description'), now[:10], round(new_balance, 2), now))

                    conn.commit()
                    return {'success': True, 'balance': round(new_balance, 2)}
        except Exception as e:
            logger.error(f'记录现金流失败: {e}')
            return {'success': False, 'error': str(e)}

    def generate_financial_report(self, cash_id: str = None, organization_id: int = None,
                                   period: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM education_cash_management WHERE 1=1'
                params = []
                if cash_id:
                    query += ' AND cash_id = ?'
                    params.append(cash_id)
                if organization_id:
                    query += ' AND organization_id = ?'
                    params.append(organization_id)
                if period:
                    query += ' AND period = ?'
                    params.append(period)
                cursor.execute(query, params)
                cash_management = [dict(c) for c in cursor.fetchall()]

                reports = []
                for cm in cash_management:
                    cursor.execute('SELECT SUM(amount) FROM cash_records WHERE cash_id = ? AND record_type = ?',
                                 (cm['cash_id'], 'income'))
                    total_income = cursor.fetchone()[0] or 0
                    cursor.execute('SELECT SUM(amount) FROM cash_records WHERE cash_id = ? AND record_type = ?',
                                 (cm['cash_id'], 'expense'))
                    total_expense = cursor.fetchone()[0] or 0

                    reports.append({
                        'cash_id': cm['cash_id'],
                        'management_type': cm['management_type'],
                        'organization_name': cm['organization_name'],
                        'period': cm['period'],
                        'budget_amount': cm['budget_amount'],
                        'actual_amount': cm['actual_amount'],
                        'balance': cm['balance'],
                        'total_income': round(total_income, 2),
                        'total_expense': round(total_expense, 2),
                        'utilization_rate': round(cm['actual_amount'] / cm['budget_amount'] * 100, 2) if cm['budget_amount'] > 0 else 0
                    })

                return {'success': True, 'reports': reports}
        except Exception as e:
            logger.error(f'生成财务报告失败: {e}')
            return {'success': False, 'error': str(e)}

    def analyze_cash_flow(self, organization_id: int, period: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                query = '''
                    SELECT cr.record_type, SUM(cr.amount) as total, cr.record_date
                    FROM cash_records cr
                    JOIN education_cash_management cm ON cr.cash_id = cm.cash_id
                    WHERE cm.organization_id = ?
                '''
                params = [organization_id]
                if period:
                    query += ' AND cm.period = ?'
                    params.append(period)

                query += ' GROUP BY cr.record_type, cr.record_date ORDER BY cr.record_date'
                cursor.execute(query, params)
                records = [dict(r) for r in cursor.fetchall()]

                income_trend = []
                expense_trend = []
                for r in records:
                    if r['record_type'] == 'income':
                        income_trend.append({'date': r['record_date'], 'amount': round(r['total'], 2)})
                    else:
                        expense_trend.append({'date': r['record_date'], 'amount': round(r['total'], 2)})

                cursor.execute('SELECT SUM(balance) FROM education_cash_management WHERE organization_id = ?', (organization_id,))
                total_balance = cursor.fetchone()[0] or 0

                return {
                    'success': True,
                    'organization_id': organization_id,
                    'total_balance': round(total_balance, 2),
                    'income_trend': income_trend,
                    'expense_trend': expense_trend
                }
        except Exception as e:
            logger.error(f'现金流分析失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_cash_balance(self, organization_id: int = None, cash_id: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM education_cash_management WHERE 1=1'
                params = []
                if organization_id:
                    query += ' AND organization_id = ?'
                    params.append(organization_id)
                if cash_id:
                    query += ' AND cash_id = ?'
                    params.append(cash_id)
                cursor.execute(query, params)
                cash_management = [dict(c) for c in cursor.fetchall()]

                total_balance = sum(cm['balance'] for cm in cash_management)

                return {
                    'success': True,
                    'cash_management': cash_management,
                    'total_balance': round(total_balance, 2)
                }
        except Exception as e:
            logger.error(f'获取资金余额失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计分析 ==========

    def get_finance_statistics(self, education_type: str = None, period: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                statistics = {}

                cursor.execute('SELECT COUNT(*), SUM(amount) FROM education_loans WHERE status = ?', ('disbursed',))
                loan_stats = cursor.fetchone()
                statistics['loans'] = {
                    'count': loan_stats[0] or 0,
                    'total_amount': round(loan_stats[1] or 0, 2)
                }

                cursor.execute('SELECT COUNT(*), SUM(amount) FROM education_investment WHERE status = ?', ('active',))
                investment_stats = cursor.fetchone()
                statistics['investments'] = {
                    'count': investment_stats[0] or 0,
                    'total_amount': round(investment_stats[1] or 0, 2)
                }

                cursor.execute('SELECT COUNT(*), SUM(premium) FROM education_insurance WHERE status = ?', ('active',))
                insurance_stats = cursor.fetchone()
                statistics['insurance'] = {
                    'count': insurance_stats[0] or 0,
                    'total_premium': round(insurance_stats[1] or 0, 2)
                }

                cursor.execute('SELECT COUNT(*), SUM(amount) FROM education_payment WHERE status = ?', ('paid',))
                payment_stats = cursor.fetchone()
                statistics['payments'] = {
                    'count': payment_stats[0] or 0,
                    'total_amount': round(payment_stats[1] or 0, 2)
                }

                cursor.execute('SELECT COUNT(*), SUM(amount) FROM education_settlement WHERE status = ?', ('completed',))
                settlement_stats = cursor.fetchone()
                statistics['settlements'] = {
                    'count': settlement_stats[0] or 0,
                    'total_amount': round(settlement_stats[1] or 0, 2)
                }

                cursor.execute('SELECT COUNT(*), SUM(amount) FROM education_financing WHERE status = ?', ('funded',))
                financing_stats = cursor.fetchone()
                statistics['financing'] = {
                    'count': financing_stats[0] or 0,
                    'total_amount': round(financing_stats[1] or 0, 2)
                }

                cursor.execute('SELECT SUM(budget_amount), SUM(balance) FROM education_cash_management')
                cash_stats = cursor.fetchone()
                statistics['cash_management'] = {
                    'total_budget': round(cash_stats[0] or 0, 2),
                    'total_balance': round(cash_stats[1] or 0, 2)
                }

                if education_type:
                    cursor.execute('SELECT COUNT(*), SUM(amount) FROM education_loans WHERE status = ? AND education_type = ?',
                                 ('disbursed', education_type))
                    loan_type_stats = cursor.fetchone()
                    statistics['loans'][education_type] = {
                        'count': loan_type_stats[0] or 0,
                        'total_amount': round(loan_type_stats[1] or 0, 2)
                    }

                return {'success': True, 'statistics': statistics}
        except Exception as e:
            logger.error(f'获取财务统计失败: {e}')
            return {'success': False, 'error': str(e)}