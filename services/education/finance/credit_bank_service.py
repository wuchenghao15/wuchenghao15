from core.db_path import get_db_path as _mtscos_get_db_path
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" MTSCOS 学分银行服务 (v15.8.0) ==================================== 提供学分账户、学分存储、学分转换、学分兑换、学分认证、跨机构互认等 综合管理服务，支持成人教育与K12教育的差异化需求。  核心能力： 1. 学分账户 - 开户、账户管理、信用评级 2. 学分存储 - 学习成果转换学分、存入记录 3. 学分转换规则 - 成果类型与学分换算 4. 学分累积与等级 - 等级体系、权益解锁 5. 学分兑换 - 证书、课程、奖励兑换 6. 学分认证 - 学习成果认证申请与审核 7. 跨机构互认 - 学分互认协议、转换 8. 成人终身学习档案与K12综合素质学分 """
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credit_bank_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('CreditBank')


# ========== 学分银行配置 ==========

# 学分来源
CREDIT_SOURCES = {
    'course_completion': {'name': '课程完成', 'default_credits': 10},
    'certification': {'name': '证书获得', 'default_credits': 30},
    'competition': {'name': '获奖', 'default_credits': 20},
    'work_experience': {'name': '工作经历', 'default_credits': 15},
    'training': {'name': '培训', 'default_credits': 8},
    'volunteer': {'name': '志愿服务', 'default_credits': 5},
    'research': {'name': '科研', 'default_credits': 25},
    'project': {'name': '项目', 'default_credits': 18},
    'exam_pass': {'name': '考试通过', 'default_credits': 12},
    'self_learning': {'name': '自主学习', 'default_credits': 6}
}

# 学习成果类型
ACHIEVEMENT_TYPES = {
    'formal_edu': {'name': '正规教育', 'conversion_factor': 1.0},
    'non_formal': {'name': '非正规教育', 'conversion_factor': 0.8},
    'informal': {'name': '非正式学习', 'conversion_factor': 0.6},
    'work_experience': {'name': '工作经验', 'conversion_factor': 0.7},
    'competition': {'name': '竞赛获奖', 'conversion_factor': 0.9},
    'certificate': {'name': '证书', 'conversion_factor': 1.0}
}

# 学分等级
CREDIT_LEVELS = {
    'bronze': {'name': '铜牌', 'min_credits': 100, 'badge': '🥉',
               'benefits': ['基础学习资源访问', '普通课程兑换']},
    'silver': {'name': '银牌', 'min_credits': 500, 'badge': '🥈',
               'benefits': ['进阶课程兑换', '学习资料折扣', '优先报名']},
    'gold': {'name': '金牌', 'min_credits': 1500, 'badge': '🥇',
             'benefits': ['高级课程兑换', '证书兑换', '专属导师咨询']},
    'platinum': {'name': '白金', 'min_credits': 3000, 'badge': '💎',
                 'benefits': ['全部课程兑换', '学费优惠', '跨机构互认优先', '活动资格']},
    'diamond': {'name': '钻石', 'min_credits': 6000, 'badge': '👑',
                'benefits': ['最高权益', '终身学习档案认证', '学术资源全开放', '荣誉证书']}
}

# 兑换项目
EXCHANGE_ITEMS = {
    'certificate': {'name': '证书', 'required_credits': 200},
    'course': {'name': '课程', 'required_credits': 80},
    'discount': {'name': '学费优惠', 'required_credits': 150},
    'award': {'name': '奖励', 'required_credits': 300},
    'material': {'name': '学习资料', 'required_credits': 50},
    'event': {'name': '活动资格', 'required_credits': 100}
}

# 认证状态
CERTIFICATION_STATUS = {
    'pending': {'name': '待审核'},
    'under_review': {'name': '审核中'},
    'approved': {'name': '已通过'},
    'rejected': {'name': '已驳回'},
    'additional_info': {'name': '需补充'}
}

# 学分状态
CREDIT_STATUS = {
    'pending': {'name': '待审核'},
    'credited': {'name': '已入账'},
    'frozen': {'name': '冻结'},
    'consumed': {'name': '已消耗'},
    'expired': {'name': '已过期'}
}

# 互认类型
MUTUAL_RECOGNITION_TYPES = {
    'bilateral': {'name': '双边'},
    'multilateral': {'name': '多边'},
    'alliance': {'name': '联盟'},
    'platform': {'name': '平台'}
}


class CreditBankService:
    """学分银行服务"""

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
                cursor.execute(''' CREATE TABLE IF NOT EXISTS credit_accounts ( account_id TEXT PRIMARY KEY, user_id TEXT UNIQUE NOT NULL, user_name TEXT, education_type TEXT, total_credits REAL DEFAULT 0, available_credits REAL DEFAULT 0, frozen_credits REAL DEFAULT 0, consumed_credits REAL DEFAULT 0, level TEXT DEFAULT 'bronze', status TEXT DEFAULT 'active', opened_at TEXT, last_activity TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS credit_transactions ( txn_id TEXT PRIMARY KEY, account_id TEXT NOT NULL, user_id TEXT, txn_type TEXT, source_type TEXT, source_id TEXT, credits REAL, balance_after REAL, description TEXT, status TEXT, operator_id TEXT, created_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS achievement_applications ( application_id TEXT PRIMARY KEY, account_id TEXT NOT NULL, user_id TEXT, achievement_type TEXT, achievement_name TEXT, achievement_desc TEXT, evidence_files TEXT, achieved_date TEXT, requesting_credits REAL, status TEXT DEFAULT 'pending', review_score REAL, review_comment TEXT, reviewed_by TEXT, reviewed_at TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS credit_conversion_rules ( rule_id TEXT PRIMARY KEY, achievement_type TEXT, achievement_name TEXT, conversion_base REAL, conversion_factor REAL, max_credits REAL, education_type TEXT, description TEXT, is_active INTEGER DEFAULT 1, created_by TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS credit_exchanges ( exchange_id TEXT PRIMARY KEY, account_id TEXT NOT NULL, user_id TEXT, item_type TEXT, item_id TEXT, item_name TEXT, credits_cost REAL, quantity INTEGER DEFAULT 1, status TEXT DEFAULT 'pending', fulfill_by TEXT, fulfilled_at TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS exchange_items_catalog ( item_id TEXT PRIMARY KEY, item_name TEXT NOT NULL, item_type TEXT, credits_required REAL, stock INTEGER DEFAULT -1, description TEXT, education_type TEXT, is_active INTEGER DEFAULT 1, valid_from TEXT, valid_to TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS mutual_recognition_agreements ( agreement_id TEXT PRIMARY KEY, agreement_name TEXT NOT NULL, agreement_type TEXT, partner_institution TEXT, partner_type TEXT, valid_from TEXT, valid_to TEXT, conversion_ratio REAL DEFAULT 1.0, covered_categories TEXT, status TEXT DEFAULT 'active', signed_by TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS cross_institution_transfers ( transfer_id TEXT PRIMARY KEY, account_id TEXT NOT NULL, user_id TEXT, source_institution TEXT, source_credits REAL, converted_credits REAL, agreement_id TEXT, evidence TEXT, status TEXT DEFAULT 'pending', processed_by TEXT, processed_at TEXT, created_at TEXT, updated_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS credit_level_history ( id INTEGER PRIMARY KEY AUTOINCREMENT, account_id TEXT NOT NULL, user_id TEXT, old_level TEXT, new_level TEXT, credits_at_change REAL, change_reason TEXT, changed_at TEXT ) ''')
                cursor.execute(''' CREATE TABLE IF NOT EXISTS learning_portfolios ( portfolio_id TEXT PRIMARY KEY, account_id TEXT NOT NULL, user_id TEXT, education_type TEXT, total_learning_hours REAL DEFAULT 0, total_achievements INTEGER DEFAULT 0, total_certificates INTEGER DEFAULT 0, skill_tags TEXT, learning_summary TEXT, last_updated TEXT, created_at TEXT ) ''')
                conn.commit()
                logger.info('学分银行服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 账户管理 ==========

    def open_account(self, user_id: str, user_name: str,
                     education_type: str = 'adult') -> Dict[str, Any]:
        try:
            account_id = f"cb_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT account_id FROM credit_accounts WHERE user_id = ?', (user_id,))
                    if cursor.fetchone():
                        return {'success': False, 'error': '该用户已开通过学分账户'}
                    cursor.execute(''' INSERT INTO credit_accounts ( account_id, user_id, user_name, education_type, total_credits, available_credits, frozen_credits, consumed_credits, level, status, opened_at, last_activity, created_at, updated_at ) VALUES (?, ?, ?, ?, 0, 0, 0, 0, 'bronze', 'active', ?, ?, ?, ?) ''', (account_id, user_id, user_name, education_type,
                          now, now, now, now))
                    conn.commit()
                    logger.info(f'开通学分账户: {user_name} ({account_id})')
                    return {'success': True, 'account_id': account_id}
        except Exception as e:
            logger.error(f'开通学分账户失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_account(self, account_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM credit_accounts WHERE account_id = ?', (account_id,))
                row = cursor.fetchone()
                if row:
                    return {'success': True, 'account': dict(row)}
                return {'success': False, 'error': '账户不存在'}
        except Exception as e:
            logger.error(f'获取账户失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_account_by_user(self, user_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM credit_accounts WHERE user_id = ?', (user_id,))
                row = cursor.fetchone()
                if row:
                    return {'success': True, 'account': dict(row)}
                return {'success': False, 'error': '账户不存在'}
        except Exception as e:
            logger.error(f'按用户获取账户失败: {e}')
            return {'success': False, 'error': str(e)}

    def _update_account_level(self, cursor, account_id: str, total_credits: float):
        """根据总学分自动更新等级，并记录等级变更历史"""
        new_level = 'bronze'
        for level_key, level_cfg in CREDIT_LEVELS.items():
            if total_credits >= level_cfg['min_credits']:
                new_level = level_key
        cursor.execute('SELECT user_id, level FROM credit_accounts WHERE account_id = ?', (account_id,))
        row = cursor.fetchone()
        if not row:
            return
        user_id, old_level = row[0], row[1]
        if old_level != new_level:
            now = datetime.now().isoformat()
            old_min = CREDIT_LEVELS.get(old_level, {}).get('min_credits', 0)
            new_min = CREDIT_LEVELS.get(new_level, {}).get('min_credits', 0)
            reason = '等级自动升级' if new_min > old_min else '等级调整'
            cursor.execute('UPDATE credit_accounts SET level = ?, updated_at = ? WHERE account_id = ?',
                           (new_level, now, account_id))
            cursor.execute(''' INSERT INTO credit_level_history (account_id, user_id, old_level, new_level, credits_at_change, change_reason, changed_at) VALUES (?, ?, ?, ?, ?, ?, ?) ''', (account_id, user_id, old_level, new_level, total_credits, reason, now))
            logger.info(f'账户 {account_id} 等级变更: {old_level} -> {new_level}')

    # ========== 学分存入 ==========

    def deposit_credits(self, account_id: str, source_type: str,
                        credits: float, **kwargs) -> Dict[str, Any]:
        try:
            txn_id = f"ctx_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT user_id, total_credits, available_credits, status FROM credit_accounts WHERE account_id = ?', (account_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '账户不存在'}
                    if row[3] != 'active':
                        return {'success': False, 'error': '账户状态异常'}
                    user_id, total_credits, available_credits = row[0], row[1], row[2]
                    new_total = total_credits + credits
                    new_available = available_credits + credits
                    cursor.execute(''' UPDATE credit_accounts SET total_credits = ?, available_credits = ?, last_activity = ?, updated_at = ? WHERE account_id = ? ''', (new_total, new_available, now, now, account_id))
                    self._update_account_level(cursor, account_id, new_total)
                    cursor.execute(''' INSERT INTO credit_transactions (txn_id, account_id, user_id, txn_type, source_type, source_id, credits, balance_after, description, status, operator_id, created_at) VALUES (?, ?, ?, 'deposit', ?, ?, ?, ?, ?, 'credited', ?, ?) ''', (txn_id, account_id, user_id, source_type,
                          kwargs.get('source_id'), credits, new_available,
                          kwargs.get('description', f'学分存入-{source_type}'),
                          kwargs.get('operator_id'), now))
                    conn.commit()
                    logger.info(f'学分存入: 账户{account_id} 存入{credits}学分')
                    return {'success': True, 'txn_id': txn_id, 'balance': new_available, 'total_credits': new_total}
        except Exception as e:
            logger.error(f'学分存入失败: {e}')
            return {'success': False, 'error': str(e)}

    def apply_achievement(self, user_id: str, achievement_type: str,
                          achievement_name: str, requesting_credits: float,
                          **kwargs) -> Dict[str, Any]:
        try:
            application_id = f"cap_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT account_id FROM credit_accounts WHERE user_id = ?', (user_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '账户不存在，请先开户'}
                    account_id = row[0]
                    evidence_files = kwargs.get('evidence_files', [])
                    cursor.execute(''' INSERT INTO achievement_applications ( application_id, account_id, user_id, achievement_type, achievement_name, achievement_desc, evidence_files, achieved_date, requesting_credits, status, review_score, review_comment, reviewed_by, reviewed_at, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', NULL, NULL, NULL, NULL, ?, ?) ''', (application_id, account_id, user_id, achievement_type,
                          achievement_name, kwargs.get('achievement_desc'),
                          json.dumps(evidence_files, ensure_ascii=False),
                          kwargs.get('achieved_date', now[:10]),
                          requesting_credits, now, now))
                    conn.commit()
                    logger.info(f'学习成果认证申请: {achievement_name} ({application_id})')
                    return {'success': True, 'application_id': application_id}
        except Exception as e:
            logger.error(f'学习成果认证申请失败: {e}')
            return {'success': False, 'error': str(e)}

    def review_achievement(self, application_id: str, approved: bool,
                           **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            status = 'approved' if approved else 'rejected'
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT account_id, user_id, achievement_type, achievement_name, requesting_credits, status FROM achievement_applications WHERE application_id = ?', (application_id,))
                    row = cursor.fetchone()
                    if not row:
                        return {'success': False, 'error': '认证申请不存在'}
                    if row[5] not in ('pending', 'under_review', 'additional_info'):
                        return {'success': False, 'error': '申请状态不允许审核'}
                    account_id, user_id, achievement_type, achievement_name, requesting_credits = row[0], row[1],
                    row[2], row[3], row[4]
                    cursor.execute(''' UPDATE achievement_applications SET status = ?, review_score = ?, review_comment = ?, reviewed_by = ?, reviewed_at = ?, updated_at = ? WHERE application_id = ? ''', (status, kwargs.get('review_score'), kwargs.get('review_comment'),
                          kwargs.get('reviewed_by'), now, now, application_id))
                    if approved:
                        txn_id = f"ctx_{uuid.uuid4().hex[:12]}"
                        cursor.execute('SELECT total_credits, available_credits FROM credit_accounts WHERE account_id = ?', (account_id,))
                        acc = cursor.fetchone()
                        new_total = acc[0] + requesting_credits
                        new_available = acc[1] + requesting_credits
                        cursor.execute(''' UPDATE credit_accounts SET total_credits = ?, available_credits = ?, last_activity = ?, updated_at = ? WHERE account_id = ? ''', (new_total, new_available, now, now, account_id))
                        self._update_account_level(cursor, account_id, new_total)
                        cursor.execute(''' INSERT INTO credit_transactions (txn_id, account_id, user_id, txn_type, source_type, source_id, credits, balance_after, description, status, operator_id, created_at) VALUES (?, ?, ?, 'deposit', 'certification', ?, ?, ?, ?, 'credited', ?, ?) ''', (txn_id, account_id, user_id, application_id, requesting_credits,
                              new_available, f'认证通过-{achievement_name}',
                              kwargs.get('reviewed_by'), now))
                    conn.commit()
                    logger.info(f'认证审核: {application_id} -> {status}')
                    return {'success': True, 'status': status, 'credited': approved}
        except Exception as e:
            logger.error(f'认证审核失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_achievements(self, user_id: str = None, page: int = 1,
                          page_size: int = 20, **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM achievement_applications WHERE 1=1'
                params = []
                if user_id:
                    query += ' AND user_id = ?'
                    params.append(user_id)
                if filters.get('status'):
                    query += ' AND status = ?'
                    params.append(filters['status'])
                if filters.get('achievement_type'):
                    query += ' AND achievement_type = ?'
                    params.append(filters['achievement_type'])
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取认证申请列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 转换规则 ==========

    def create_conversion_rule(self, achievement_type: str, achievement_name: str,
                               conversion_base: float, **kwargs) -> Dict[str, Any]:
        try:
            rule_id = f"cr_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            default_factor = ACHIEVEMENT_TYPES.get(achievement_type, {}).get('conversion_factor', 1.0)
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO credit_conversion_rules ( rule_id, achievement_type, achievement_name, conversion_base, conversion_factor, max_credits, education_type, description, is_active, created_by, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?) ''', (rule_id, achievement_type, achievement_name, conversion_base,
                          kwargs.get('conversion_factor', default_factor),
                          kwargs.get('max_credits', 9999),
                          kwargs.get('education_type'),
                          kwargs.get('description'),
                          kwargs.get('created_by'), now, now))
                    conn.commit()
                    logger.info(f'创建转换规则: {achievement_name} ({rule_id})')
                    return {'success': True, 'rule_id': rule_id}
        except Exception as e:
            logger.error(f'创建转换规则失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_conversion_rules(self, page: int = 1, page_size: int = 20,
                              **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM credit_conversion_rules WHERE 1=1'
                params = []
                if filters.get('achievement_type'):
                    query += ' AND achievement_type = ?'
                    params.append(filters['achievement_type'])
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
                items = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取转换规则列表失败: {e}')
            return {'success': False, 'error': str(e)}

    def calculate_credits(self, achievement_type: str, achievement_name: str,
                          base_value: float) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(''' SELECT conversion_factor, max_credits FROM credit_conversion_rules WHERE achievement_type = ? AND achievement_name = ? AND is_active = 1 ORDER BY created_at DESC LIMIT 1 ''', (achievement_type, achievement_name))
                row = cursor.fetchone()
                if row:
                    factor = row['conversion_factor']
                    max_credits = row['max_credits']
                    source = 'rule'
                else:
                    factor = ACHIEVEMENT_TYPES.get(achievement_type, {}).get('conversion_factor', 1.0)
                    max_credits = 9999
                    source = 'default'
                credits = base_value * factor
                capped = False
                if credits > max_credits:
                    credits = max_credits
                    capped = True
                return {'success': True, 'credits': credits, 'factor': factor,
                        'max_credits': max_credits, 'capped': capped, 'source': source}
        except Exception as e:
            logger.error(f'计算学分失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 学分兑换 ==========

    def add_exchange_item(self, item_name: str, item_type: str,
                          credits_required: float, **kwargs) -> Dict[str, Any]:
        try:
            item_id = f"cei_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(''' INSERT INTO exchange_items_catalog ( item_id, item_name, item_type, credits_required, stock, description, education_type, is_active, valid_from, valid_to, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?) ''', (item_id, item_name, item_type,
                          credits_required, kwargs.get('stock', -1),
                          kwargs.get('description'),
                          kwargs.get('education_type'),
                          kwargs.get('valid_from'), kwargs.get('valid_to'),
                          now, now))
                    conn.commit()
                    logger.info(f'添加兑换项目: {item_name} ({item_id})')
                    return {'success': True, 'item_id': item_id}
        except Exception as e:
            logger.error(f'添加兑换项目失败: {e}')
            return {'success': False, 'error': str(e)}

    def exchange_credits(self, account_id: str, item_id: str,
                         quantity: int = 1) -> Dict[str, Any]:
        try:
            exchange_id = f"cex_{uuid.uuid4().hex[:12]}"
            txn_id = f"ctx_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT item_name, item_type, credits_required, stock, is_active FROM exchange_items_catalog WHERE item_id = ?', (item_id,))
                    item = cursor.fetchone()
                    if not item:
                        return {'success': False, 'error': '兑换项目不存在'}
                    if not item[4]:
                        return {'success': False, 'error': '兑换项目已下架'}
                    if item[3] >= 0 and item[3] < quantity:
                        return {'success': False, 'error': '库存不足'}
                    credits_cost = item[2] * quantity
                    cursor.execute('SELECT user_id, available_credits, status FROM credit_accounts WHERE account_id = ?', (account_id,))
                    acc = cursor.fetchone()
                    if not acc:
                        return {'success': False, 'error': '账户不存在'}
                    if acc[2] != 'active':
                        return {'success': False, 'error': '账户状态异常'}
                    if acc[1] < credits_cost:
                        return {'success': False, 'error': '可用学分不足'}
                    user_id, available_credits = acc[0], acc[1]
                    new_available = available_credits - credits_cost
                    cursor.execute(''' UPDATE credit_accounts SET available_credits = ?, consumed_credits = consumed_credits + ?, last_activity = ?, updated_at = ? WHERE account_id = ? ''', (new_available, credits_cost, now, now, account_id))
                    if item[3] >= 0:
                        cursor.execute('UPDATE exchange_items_catalog SET stock = stock - ?, updated_at = ? WHERE item_id = ?',
                                       (quantity, now, item_id))
                    cursor.execute(''' INSERT INTO credit_exchanges (exchange_id, account_id, user_id, item_type, item_id, item_name, credits_cost, quantity, status, fulfill_by, fulfilled_at, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'fulfilled', NULL, NULL, ?, ?) ''', (exchange_id, account_id, user_id, item[1], item_id, item[0],
                          credits_cost, quantity, now, now))
                    cursor.execute(''' INSERT INTO credit_transactions (txn_id, account_id, user_id, txn_type, source_type, source_id, credits, balance_after, description, status, operator_id, created_at) VALUES (?, ?, ?, 'withdraw', 'exchange', ?, ?, ?, ?, 'consumed', NULL, ?) ''', (txn_id, account_id, user_id, exchange_id, credits_cost,
                          new_available, f'兑换-{item[0]}x{quantity}', now))
                    conn.commit()
                    logger.info(f'学分兑换: 账户{account_id} 兑换{item[0]}x{quantity} 消耗{credits_cost}学分')
                    return {'success': True, 'exchange_id': exchange_id, 'credits_cost': credits_cost,
                    'balance': new_available}
        except Exception as e:
            logger.error(f'学分兑换失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_exchange_items(self, page: int = 1, page_size: int = 20,
                            **filters) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM exchange_items_catalog WHERE 1=1'
                params = []
                if filters.get('item_type'):
                    query += ' AND item_type = ?'
                    params.append(filters['item_type'])
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
                items = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取兑换目录失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_exchange_records(self, user_id: str = None, page: int = 1,
                              page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM credit_exchanges WHERE 1=1'
                params = []
                if user_id:
                    query += ' AND user_id = ?'
                    params.append(user_id)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                items = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取兑换记录失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 跨机构互认 ==========

    def create_mutual_agreement(self, agreement_name: str, partner_institution: str,
                                **kwargs) -> Dict[str, Any]:
        try:
            agreement_id = f"cma_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    covered = kwargs.get('covered_categories', [])
                    cursor.execute(''' INSERT INTO mutual_recognition_agreements ( agreement_id, agreement_name, agreement_type, partner_institution, partner_type, valid_from, valid_to, conversion_ratio, covered_categories, status, signed_by, created_at, updated_at ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?) ''', (agreement_id, agreement_name,
                          kwargs.get('agreement_type', 'bilateral'),
                          partner_institution, kwargs.get('partner_type'),
                          kwargs.get('valid_from'), kwargs.get('valid_to'),
                          kwargs.get('conversion_ratio', 1.0),
                          json.dumps(covered, ensure_ascii=False),
                          kwargs.get('signed_by'), now, now))
                    conn.commit()
                    logger.info(f'创建互认协议: {agreement_name} ({agreement_id})')
                    return {'success': True, 'agreement_id': agreement_id}
        except Exception as e:
            logger.error(f'创建互认协议失败: {e}')
            return {'success': False, 'error': str(e)}

    def transfer_credits(self, account_id: str, source_institution: str,
                         source_credits: float, **kwargs) -> Dict[str, Any]:
        try:
            transfer_id = f"ctf_{uuid.uuid4().hex[:12]}"
            txn_id = f"ctx_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT user_id, total_credits, available_credits FROM credit_accounts WHERE account_id = ?', (account_id,))
                    acc = cursor.fetchone()
                    if not acc:
                        return {'success': False, 'error': '账户不存在'}
                    user_id, total_credits, available_credits = acc[0], acc[1], acc[2]
                    cursor.execute(''' SELECT agreement_id, conversion_ratio FROM mutual_recognition_agreements WHERE partner_institution = ? AND status = 'active' ORDER BY created_at DESC LIMIT 1 ''', (source_institution,))
                    agr = cursor.fetchone()
                    if not agr:
                        return {'success': False, 'error': '未找到与该机构的互认协议'}
                    agreement_id, ratio = agr[0], agr[1]
                    converted_credits = round(source_credits * ratio, 2)
                    new_total = total_credits + converted_credits
                    new_available = available_credits + converted_credits
                    cursor.execute(''' UPDATE credit_accounts SET total_credits = ?, available_credits = ?, last_activity = ?, updated_at = ? WHERE account_id = ? ''', (new_total, new_available, now, now, account_id))
                    self._update_account_level(cursor, account_id, new_total)
                    cursor.execute(''' INSERT INTO cross_institution_transfers (transfer_id, account_id, user_id, source_institution, source_credits, converted_credits, agreement_id, evidence, status, processed_by, processed_at, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'completed', ?, ?, ?, ?) ''', (transfer_id, account_id, user_id, source_institution,
                          source_credits, converted_credits, agreement_id,
                          kwargs.get('evidence'),
                          kwargs.get('processed_by'), now, now, now))
                    cursor.execute(''' INSERT INTO credit_transactions (txn_id, account_id, user_id, txn_type, source_type, source_id, credits, balance_after, description, status, operator_id, created_at) VALUES (?, ?, ?, 'transfer', 'cross_institution', ?, ?, ?, ?, 'credited', ?, ?) ''', (txn_id, account_id, user_id, transfer_id, converted_credits,
                          new_available, f'跨机构转入-{source_institution}',
                          kwargs.get('processed_by'), now))
                    conn.commit()
                    logger.info(f'跨机构转入: 账户{account_id} 从{source_institution}转入{converted_credits}学分')
                    return {'success': True, 'transfer_id': transfer_id,
                            'converted_credits': converted_credits, 'balance': new_available}
        except Exception as e:
            logger.error(f'跨机构学分转入失败: {e}')
            return {'success': False, 'error': str(e)}

    def list_mutual_agreements(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM mutual_recognition_agreements WHERE 1=1'
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', [])
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                cursor.execute(query, [page_size, (page - 1) * page_size])
                items = [dict(r) for r in cursor.fetchall()]
                return {'success': True, 'items': items, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'获取互认协议列表失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 学习档案 ==========

    def update_portfolio(self, user_id: str, **kwargs) -> Dict[str, Any]:
        try:
            portfolio_id = f"clp_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT account_id, education_type FROM credit_accounts WHERE user_id = ?', (user_id,
                    ))
                    acc = cursor.fetchone()
                    if not acc:
                        return {'success': False, 'error': '账户不存在'}
                    account_id, education_type = acc[0], acc[1]
                    cursor.execute('SELECT portfolio_id FROM learning_portfolios WHERE user_id = ?', (user_id,))
                    existing = cursor.fetchone()
                    skill_tags = json.dumps(kwargs.get('skill_tags', []), ensure_ascii=False)
                    if existing:
                        cursor.execute(''' UPDATE learning_portfolios SET total_learning_hours = ?, total_achievements = ?, total_certificates = ?, skill_tags = ?, learning_summary = ?, last_updated = ? WHERE user_id = ? ''', (kwargs.get('total_learning_hours', 0),
                              kwargs.get('total_achievements', 0),
                              kwargs.get('total_certificates', 0),
                              skill_tags, kwargs.get('learning_summary'), now, user_id))
                        conn.commit()
                        return {'success': True, 'portfolio_id': existing[0], 'updated': True}
                    cursor.execute(''' INSERT INTO learning_portfolios (portfolio_id, account_id, user_id, education_type, total_learning_hours, total_achievements, total_certificates, skill_tags, learning_summary, last_updated, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''', (portfolio_id, account_id, user_id, education_type,
                          kwargs.get('total_learning_hours', 0),
                          kwargs.get('total_achievements', 0),
                          kwargs.get('total_certificates', 0),
                          skill_tags, kwargs.get('learning_summary'), now, now))
                    conn.commit()
                    logger.info(f'更新学习档案: 用户{user_id}')
                    return {'success': True, 'portfolio_id': portfolio_id, 'updated': False}
        except Exception as e:
            logger.error(f'更新学习档案失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_portfolio(self, user_id: str) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM learning_portfolios WHERE user_id = ?', (user_id,))
                row = cursor.fetchone()
                if row:
                    portfolio = dict(row)
                    try:
                        portfolio['skill_tags'] = json.loads(portfolio.get('skill_tags') or '[]')
                    except (ValueError, TypeError):
                        portfolio['skill_tags'] = []
                    return {'success': True, 'portfolio': portfolio}
                return {'success': False, 'error': '学习档案不存在'}
        except Exception as e:
            logger.error(f'获取学习档案失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                base_where = 'WHERE 1=1'
                params = []
                if education_type:
                    base_where += ' AND education_type = ?'
                    params.append(education_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM credit_accounts {base_where}', params)
                account_count = cursor.fetchone()['cnt']
                cursor.execute(f'SELECT COALESCE(SUM(total_credits), 0) as s FROM credit_accounts {base_where}', params)
                total_credits = cursor.fetchone()['s']
                cursor.execute(f'SELECT level, COUNT(*) as cnt FROM credit_accounts {base_where} GROUP BY level',
                params)
                level_distribution = {r['level']: r['cnt'] for r in cursor.fetchall()}
                cursor.execute(''' SELECT source_type, COALESCE(SUM(credits), 0) as s, COUNT(*) as cnt FROM credit_transactions WHERE txn_type = 'deposit' AND status = 'credited' GROUP BY source_type ''')
                source_distribution = {r['source_type']: {'credits': r['s'],
                'count': r['cnt']} for r in cursor.fetchall()}
                cursor.execute('SELECT COUNT(*) as cnt, COALESCE(SUM(credits_cost), 0) as s FROM credit_exchanges')
                exchange_row = cursor.fetchone()
                exchange_stats = {'total_count': exchange_row['cnt'], 'total_credits': exchange_row['s']}
                cursor.execute('SELECT COUNT(*) as total FROM achievement_applications')
                total_apps = cursor.fetchone()['total']
                cursor.execute("SELECT COUNT(*) as approved FROM achievement_applications WHERE status = 'approved'")
                approved_apps = cursor.fetchone()['approved']
                pass_rate = round(approved_apps / total_apps, 4) if total_apps else 0
                return {'success': True, 'statistics': {
                    'account_count': account_count,
                    'total_credits': total_credits,
                    'level_distribution': level_distribution,
                    'source_distribution': source_distribution,
                    'exchange_stats': exchange_stats,
                    'certification_pass_rate': pass_rate,
                    'certification_total': total_apps,
                    'certification_approved': approved_apps
                }}
        except Exception as e:
            logger.error(f'获取统计失败: {e}')
            return {'success': False, 'error': str(e)}


if __name__ == '__main__':
    service = CreditBankService()
    print('学分银行服务初始化完成')
    stats = service.get_statistics()
    print(f'统计: {stats}')










































































