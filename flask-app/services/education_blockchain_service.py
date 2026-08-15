#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 教育区块链服务 (v15.15.0)
====================================
提供证书存证、学分认证、数据溯源、数字身份、智能合约、去中心化存储、区块链查询、跨链互操作等综合服务。

核心能力：
1. 证书存证 - 毕业证书、学位证书、资格证书等存证与查询
2. 学分认证 - 学习记录、成绩记录、学分认证与转换
3. 数据溯源 - 教育数据来源追踪、完整性验证
4. 数字身份 - 学生、教师、学校、机构身份管理
5. 智能合约 - 证书合约、学分合约、认证合约等
6. 去中心化存储 - 链上存储、链下存储、IPFS存储
7. 区块链查询 - 交易记录、区块信息、合约状态查询
8. 跨链互操作 - 跨链验证、跨链转移、跨链查询、跨链合约
9. 验证审计 - 验证日志、审计追踪、合规检查
10. 链上治理 - 节点管理、链配置、共识机制

支持教育类型：成人教育 / K12教育
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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'education_blockchain_service.log'),
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('EducationBlockchain')


# ========== 区块链配置 ==========

CHAIN_TYPES = {
    'consortium': {'name': '联盟链', 'description': '多机构联合运营的区块链网络', 'permissioned': True},
    'private': {'name': '私有链', 'description': '单一机构控制的区块链网络', 'permissioned': True},
    'public': {'name': '公有链', 'description': '开放参与的区块链网络', 'permissioned': False},
    'hybrid': {'name': '混合链', 'description': '结合公有链与联盟链特性的区块链网络', 'permissioned': True}
}

CERTIFICATE_TYPES = {
    'diploma': {'name': '毕业证书', 'requires_verification': True},
    'degree': {'name': '学位证书', 'requires_verification': True},
    'qualification': {'name': '资格证书', 'requires_verification': True},
    'training': {'name': '培训证书', 'requires_verification': False},
    'award': {'name': '获奖证书', 'requires_verification': True},
    'transcript': {'name': '成绩单', 'requires_verification': False}
}

RECORD_TYPES = {
    'learning': {'name': '学习记录', 'data_format': 'json'},
    'grade': {'name': '成绩记录', 'data_format': 'json'},
    'certificate': {'name': '证书记录', 'data_format': 'json'},
    'credit': {'name': '学分记录', 'data_format': 'json'},
    'verification': {'name': '认证记录', 'data_format': 'json'},
    'evaluation': {'name': '评价记录', 'data_format': 'json'}
}

IDENTITY_TYPES = {
    'student': {'name': '学生身份', 'required_fields': ['name', 'school', 'grade']},
    'teacher': {'name': '教师身份', 'required_fields': ['name', 'school', 'subject']},
    'school': {'name': '学校身份', 'required_fields': ['name', 'address', 'level']},
    'institution': {'name': '机构身份', 'required_fields': ['name', 'address', 'type']},
    'admin': {'name': '管理员身份', 'required_fields': ['name', 'role', 'scope']}
}

CONTRACT_TYPES = {
    'certificate': {'name': '证书合约', 'description': '证书存证与验证合约'},
    'credit': {'name': '学分合约', 'description': '学分管理与转换合约'},
    'verification': {'name': '认证合约', 'description': '身份认证与验证合约'},
    'payment': {'name': '支付合约', 'description': '教育费用支付合约'},
    'permission': {'name': '权限合约', 'description': '访问权限管理合约'},
    'data': {'name': '数据合约', 'description': '数据共享与访问合约'}
}

STORAGE_TYPES = {
    'onchain': {'name': '链上存储', 'description': '数据直接存储在区块链上', 'cost': 'high', 'speed': 'slow'},
    'offchain': {'name': '链下存储', 'description': '数据存储在链外，哈希值存链上', 'cost': 'low', 'speed': 'fast'},
    'distributed': {'name': '分布式存储', 'description': '数据分布式存储在多个节点', 'cost': 'medium', 'speed': 'medium'},
    'ipfs': {'name': 'IPFS存储', 'description': '基于IPFS的去中心化存储', 'cost': 'low', 'speed': 'medium'}
}

VERIFICATION_LEVELS = {
    'basic': {'name': '基础验证', 'description': '验证证书基本信息', 'required_fields': ['certificate_no', 'name']},
    'intermediate': {'name': '中级验证', 'description': '验证证书信息与身份匹配', 'required_fields': ['certificate_no', 'name', 'identity_id']},
    'advanced': {'name': '高级验证', 'description': '全面验证证书真实性与有效性', 'required_fields': ['certificate_no', 'name', 'identity_id', 'timestamp']},
    'authoritative': {'name': '权威验证', 'description': '由权威机构进行验证', 'required_fields': ['certificate_no', 'name', 'identity_id', 'timestamp', 'issuer_signature']}
}

INTEROP_TYPES = {
    'cross_chain_verify': {'name': '跨链验证', 'description': '验证其他链上的证书'},
    'cross_chain_transfer': {'name': '跨链转移', 'description': '将证书转移到其他链'},
    'cross_chain_query': {'name': '跨链查询', 'description': '查询其他链上的数据'},
    'cross_chain_contract': {'name': '跨链合约', 'description': '执行跨链合约调用'}
}


class EducationBlockchainService:
    """教育区块链服务"""

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
                    CREATE TABLE IF NOT EXISTS blockchain_nodes (
                        node_id TEXT PRIMARY KEY,
                        node_name TEXT NOT NULL,
                        node_type TEXT,
                        chain_type TEXT,
                        ip_address TEXT,
                        port INTEGER,
                        status TEXT DEFAULT 'active',
                        is_validator INTEGER DEFAULT 0,
                        stake_amount REAL DEFAULT 0,
                        last_sync_time TEXT,
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS chain_config (
                        config_id TEXT PRIMARY KEY,
                        chain_type TEXT NOT NULL,
                        consensus_algorithm TEXT DEFAULT 'PBFT',
                        block_size INTEGER DEFAULT 1000,
                        block_interval INTEGER DEFAULT 10,
                        gas_limit INTEGER DEFAULT 8000000,
                        validators_count INTEGER DEFAULT 4,
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS certificates (
                        certificate_id TEXT PRIMARY KEY,
                        certificate_no TEXT UNIQUE NOT NULL,
                        certificate_type TEXT NOT NULL,
                        holder_name TEXT NOT NULL,
                        holder_identity_id TEXT,
                        issuer_id TEXT NOT NULL,
                        issuer_name TEXT,
                        issue_date TEXT NOT NULL,
                        expiry_date TEXT,
                        content TEXT,
                        hash_value TEXT UNIQUE NOT NULL,
                        status TEXT DEFAULT 'issued',
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS certificate_records (
                        record_id TEXT PRIMARY KEY,
                        certificate_id TEXT NOT NULL,
                        transaction_hash TEXT,
                        block_number INTEGER,
                        operation_type TEXT,
                        previous_hash TEXT,
                        education_type TEXT,
                        created_at TEXT,
                        FOREIGN KEY (certificate_id) REFERENCES certificates(certificate_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS credential_verification (
                        verification_id TEXT PRIMARY KEY,
                        certificate_id TEXT NOT NULL,
                        verifier_id TEXT,
                        verifier_name TEXT,
                        verification_level TEXT,
                        result TEXT,
                        verification_time TEXT,
                        details TEXT,
                        education_type TEXT,
                        FOREIGN KEY (certificate_id) REFERENCES certificates(certificate_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS student_identity (
                        identity_id TEXT PRIMARY KEY,
                        student_id INTEGER,
                        student_name TEXT NOT NULL,
                        school_id TEXT,
                        school_name TEXT,
                        grade TEXT,
                        class_name TEXT,
                        education_type TEXT,
                        public_key TEXT,
                        private_key_hash TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS teacher_identity (
                        identity_id TEXT PRIMARY KEY,
                        teacher_id INTEGER,
                        teacher_name TEXT NOT NULL,
                        school_id TEXT,
                        school_name TEXT,
                        subject TEXT,
                        title TEXT,
                        education_type TEXT,
                        public_key TEXT,
                        private_key_hash TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS institution_identity (
                        identity_id TEXT PRIMARY KEY,
                        institution_name TEXT NOT NULL,
                        institution_type TEXT,
                        address TEXT,
                        license_number TEXT,
                        education_type TEXT,
                        public_key TEXT,
                        private_key_hash TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS smart_contracts (
                        contract_id TEXT PRIMARY KEY,
                        contract_type TEXT NOT NULL,
                        contract_name TEXT NOT NULL,
                        contract_code TEXT,
                        bytecode TEXT,
                        abi TEXT,
                        owner_id TEXT,
                        status TEXT DEFAULT 'deployed',
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS contract_executions (
                        execution_id TEXT PRIMARY KEY,
                        contract_id TEXT NOT NULL,
                        method_name TEXT,
                        parameters TEXT,
                        result TEXT,
                        transaction_hash TEXT,
                        gas_used INTEGER,
                        execution_time TEXT,
                        education_type TEXT,
                        FOREIGN KEY (contract_id) REFERENCES smart_contracts(contract_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS decentralized_storage (
                        storage_id TEXT PRIMARY KEY,
                        storage_type TEXT NOT NULL,
                        content_hash TEXT UNIQUE NOT NULL,
                        content_type TEXT,
                        size INTEGER,
                        node_ids TEXT,
                        status TEXT DEFAULT 'stored',
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS storage_records (
                        record_id TEXT PRIMARY KEY,
                        storage_id TEXT NOT NULL,
                        data_reference TEXT,
                        access_count INTEGER DEFAULT 0,
                        last_access_time TEXT,
                        education_type TEXT,
                        FOREIGN KEY (storage_id) REFERENCES decentralized_storage(storage_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS transaction_records (
                        tx_hash TEXT PRIMARY KEY,
                        tx_type TEXT,
                        from_address TEXT,
                        to_address TEXT,
                        value REAL,
                        gas_price INTEGER,
                        gas_used INTEGER,
                        block_number INTEGER,
                        tx_status TEXT DEFAULT 'pending',
                        timestamp TEXT,
                        education_type TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cross_chain_records (
                        record_id TEXT PRIMARY KEY,
                        interop_type TEXT NOT NULL,
                        source_chain TEXT,
                        target_chain TEXT,
                        data_hash TEXT,
                        status TEXT DEFAULT 'processing',
                        transaction_hash TEXT,
                        confirmation_count INTEGER DEFAULT 0,
                        education_type TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS verification_logs (
                        log_id TEXT PRIMARY KEY,
                        certificate_id TEXT,
                        identity_id TEXT,
                        operation TEXT,
                        operator_id TEXT,
                        operator_name TEXT,
                        result TEXT,
                        timestamp TEXT,
                        education_type TEXT,
                        details TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS audit_trails (
                        trail_id TEXT PRIMARY KEY,
                        action TEXT NOT NULL,
                        resource_type TEXT,
                        resource_id TEXT,
                        operator_id TEXT,
                        operator_name TEXT,
                        timestamp TEXT,
                        education_type TEXT,
                        details TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS block_headers (
                        block_number INTEGER PRIMARY KEY,
                        block_hash TEXT UNIQUE NOT NULL,
                        parent_hash TEXT,
                        merkle_root TEXT,
                        timestamp TEXT,
                        transactions_count INTEGER DEFAULT 0,
                        proposer TEXT,
                        education_type TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS merkle_trees (
                        tree_id TEXT PRIMARY KEY,
                        root_hash TEXT UNIQUE NOT NULL,
                        data_count INTEGER,
                        certificate_ids TEXT,
                        education_type TEXT,
                        created_at TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS chain_sync_status (
                        sync_id TEXT PRIMARY KEY,
                        chain_type TEXT,
                        sync_type TEXT,
                        last_block INTEGER DEFAULT 0,
                        target_block INTEGER DEFAULT 0,
                        progress REAL DEFAULT 0,
                        status TEXT DEFAULT 'idle',
                        education_type TEXT,
                        updated_at TEXT
                    )
                ''')
                conn.commit()
                logger.info('教育区块链服务数据库初始化完成')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')

    # ========== 证书存证 ==========

    def issue_certificate(self, certificate_type: str, holder_name: str,
                          issuer_id: str, issue_date: str, **kwargs) -> Dict[str, Any]:
        try:
            certificate_id = f"crt_{uuid.uuid4().hex[:12]}"
            certificate_no = f"CERT{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}"
            content = json.dumps({
                'type': certificate_type,
                'holder_name': holder_name,
                'issuer_id': issuer_id,
                'issue_date': issue_date,
                'expiry_date': kwargs.get('expiry_date'),
                'details': kwargs.get('details', {})
            }, ensure_ascii=False)
            hash_value = str(hash(content))
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO certificates (
                            certificate_id, certificate_no, certificate_type,
                            holder_name, holder_identity_id, issuer_id,
                            issuer_name, issue_date, expiry_date, content,
                            hash_value, status, education_type, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'issued', ?, ?, ?)
                    ''', (certificate_id, certificate_no, certificate_type, holder_name,
                          kwargs.get('holder_identity_id'), issuer_id,
                          kwargs.get('issuer_name'), issue_date,
                          kwargs.get('expiry_date'), content, hash_value,
                          kwargs.get('education_type', 'adult'), now, now))
                    conn.commit()
                    logger.info(f'颁发证书: {certificate_no} ({certificate_type})')
                    return {'success': True, 'certificate_id': certificate_id, 'certificate_no': certificate_no, 'hash_value': hash_value}
        except Exception as e:
            logger.error(f'颁发证书失败: {e}')
            return {'success': False, 'error': str(e)}

    def verify_certificate(self, certificate_no: str, **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM certificates WHERE certificate_no = ?', (certificate_no,))
                cert = cursor.fetchone()
                if not cert:
                    return {'success': False, 'error': '证书不存在'}
                content = json.loads(cert['content'])
                new_hash = str(hash(cert['content']))
                is_valid = new_hash == cert['hash_value']
                verification_id = f"vfy_{uuid.uuid4().hex[:12]}"
                now = datetime.now().isoformat()
                cursor.execute('''
                    INSERT INTO credential_verification (
                        verification_id, certificate_id, verifier_id, verifier_name,
                        verification_level, result, verification_time, details, education_type
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (verification_id, cert['certificate_id'], kwargs.get('verifier_id'),
                      kwargs.get('verifier_name'), kwargs.get('verification_level', 'basic'),
                      'success' if is_valid else 'failed', now,
                      json.dumps({'hash_verified': is_valid, 'status': cert['status']}),
                      cert['education_type']))
                conn.commit()
                return {'success': True, 'is_valid': is_valid, 'certificate': dict(cert), 'verification_id': verification_id}
        except Exception as e:
            logger.error(f'验证证书失败: {e}')
            return {'success': False, 'error': str(e)}

    def revoke_certificate(self, certificate_id: str, reason: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE certificates SET status = ?, updated_at = ? WHERE certificate_id = ? AND status = ?',
                                 ('revoked', now, certificate_id, 'issued'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'吊销证书: {certificate_id}')
                        return {'success': True, 'reason': reason}
                    return {'success': False, 'error': '证书状态不允许吊销'}
        except Exception as e:
            logger.error(f'吊销证书失败: {e}')
            return {'success': False, 'error': str(e)}

    def query_certificate(self, certificate_no: str = None, holder_name: str = None,
                          certificate_type: str = None, page: int = 1,
                          page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM certificates WHERE 1=1'
                params = []
                if certificate_no:
                    query += ' AND certificate_no LIKE ?'
                    params.append(f'%{certificate_no}%')
                if holder_name:
                    query += ' AND holder_name LIKE ?'
                    params.append(f'%{holder_name}%')
                if certificate_type:
                    query += ' AND certificate_type = ?'
                    params.append(certificate_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY issue_date DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                certificates = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'certificates': certificates, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'查询证书失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 学分认证 ==========

    def record_credits(self, student_id: int, student_name: str, credits: float,
                       course_name: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"crt_{uuid.uuid4().hex[:12]}"
            content = json.dumps({
                'student_id': student_id,
                'student_name': student_name,
                'credits': credits,
                'course_name': course_name,
                'school_id': kwargs.get('school_id'),
                'school_name': kwargs.get('school_name'),
                'semester': kwargs.get('semester'),
                'grade': kwargs.get('grade')
            }, ensure_ascii=False)
            hash_value = str(hash(content))
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO certificate_records (
                            record_id, certificate_id, transaction_hash,
                            operation_type, education_type, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (record_id, f"credit_{student_id}", hash_value, 'credit_record',
                          kwargs.get('education_type', 'adult'), now))
                    conn.commit()
                    logger.info(f'记录学分: {student_name} {credits}学分')
                    return {'success': True, 'record_id': record_id, 'hash_value': hash_value}
        except Exception as e:
            logger.error(f'记录学分失败: {e}')
            return {'success': False, 'error': str(e)}

    def verify_credits(self, student_id: int, **kwargs) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM certificate_records
                    WHERE certificate_id LIKE ? AND operation_type = ?
                    ORDER BY created_at DESC
                ''', (f"credit_{student_id}", 'credit_record'))
                records = [dict(r) for r in cursor.fetchall()]
                total_credits = sum(json.loads(r.get('parameters', '{}')).get('credits', 0) for r in records) if records else 0
                return {'success': True, 'student_id': student_id, 'total_credits': total_credits, 'records': records}
        except Exception as e:
            logger.error(f'验证学分失败: {e}')
            return {'success': False, 'error': str(e)}

    def transfer_credits(self, from_student_id: int, to_student_id: int,
                         credits: float, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT COUNT(*) FROM certificate_records
                        WHERE certificate_id LIKE ? AND operation_type = ?
                    ''', (f"credit_{from_student_id}", 'credit_record'))
                    count = cursor.fetchone()[0]
                    if count == 0:
                        return {'success': False, 'error': '转出学生无学分记录'}
                    transfer_id = f"trf_{uuid.uuid4().hex[:12]}"
                    content = json.dumps({
                        'from_student_id': from_student_id,
                        'to_student_id': to_student_id,
                        'credits': credits,
                        'reason': kwargs.get('reason', '学分转移')
                    }, ensure_ascii=False)
                    hash_value = str(hash(content))
                    cursor.execute('''
                        INSERT INTO certificate_records (
                            record_id, certificate_id, transaction_hash,
                            operation_type, education_type, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (transfer_id, f"transfer_{uuid.uuid4().hex[:8]}", hash_value,
                          'credit_transfer', kwargs.get('education_type', 'adult'), now))
                    conn.commit()
                    logger.info(f'学分转移: {from_student_id} -> {to_student_id} {credits}学分')
                    return {'success': True, 'transfer_id': transfer_id}
        except Exception as e:
            logger.error(f'学分转移失败: {e}')
            return {'success': False, 'error': str(e)}

    def convert_credits(self, student_id: int, from_system: str, to_system: str,
                        credits: float, **kwargs) -> Dict[str, Any]:
        try:
            conversion_rate = kwargs.get('conversion_rate', 1.0)
            converted_credits = credits * conversion_rate
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    convert_id = f"cnv_{uuid.uuid4().hex[:12]}"
                    content = json.dumps({
                        'student_id': student_id,
                        'from_system': from_system,
                        'to_system': to_system,
                        'original_credits': credits,
                        'converted_credits': converted_credits,
                        'conversion_rate': conversion_rate
                    }, ensure_ascii=False)
                    hash_value = str(hash(content))
                    cursor.execute('''
                        INSERT INTO certificate_records (
                            record_id, certificate_id, transaction_hash,
                            operation_type, education_type, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (convert_id, f"convert_{uuid.uuid4().hex[:8]}", hash_value,
                          'credit_conversion', kwargs.get('education_type', 'adult'), now))
                    conn.commit()
                    logger.info(f'学分转换: {student_id} {credits} {from_system} -> {converted_credits} {to_system}')
                    return {'success': True, 'convert_id': convert_id, 'converted_credits': converted_credits}
        except Exception as e:
            logger.error(f'学分转换失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 数字身份 ==========

    def create_student_identity(self, student_id: int, student_name: str, **kwargs) -> Dict[str, Any]:
        try:
            identity_id = f"sid_{uuid.uuid4().hex[:12]}"
            public_key = f"pub_{uuid.uuid4().hex[:32]}"
            private_key_hash = str(hash(f"priv_{uuid.uuid4().hex[:64]}"))
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO student_identity (
                            identity_id, student_id, student_name, school_id,
                            school_name, grade, class_name, education_type,
                            public_key, private_key_hash, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (identity_id, student_id, student_name, kwargs.get('school_id'),
                          kwargs.get('school_name'), kwargs.get('grade'),
                          kwargs.get('class_name'), kwargs.get('education_type', 'adult'),
                          public_key, private_key_hash, now, now))
                    conn.commit()
                    logger.info(f'创建学生身份: {student_name} ({identity_id})')
                    return {'success': True, 'identity_id': identity_id, 'public_key': public_key}
        except Exception as e:
            logger.error(f'创建学生身份失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_teacher_identity(self, teacher_id: int, teacher_name: str, **kwargs) -> Dict[str, Any]:
        try:
            identity_id = f"tid_{uuid.uuid4().hex[:12]}"
            public_key = f"pub_{uuid.uuid4().hex[:32]}"
            private_key_hash = str(hash(f"priv_{uuid.uuid4().hex[:64]}"))
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO teacher_identity (
                            identity_id, teacher_id, teacher_name, school_id,
                            school_name, subject, title, education_type,
                            public_key, private_key_hash, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (identity_id, teacher_id, teacher_name, kwargs.get('school_id'),
                          kwargs.get('school_name'), kwargs.get('subject'),
                          kwargs.get('title'), kwargs.get('education_type', 'adult'),
                          public_key, private_key_hash, now, now))
                    conn.commit()
                    logger.info(f'创建教师身份: {teacher_name} ({identity_id})')
                    return {'success': True, 'identity_id': identity_id, 'public_key': public_key}
        except Exception as e:
            logger.error(f'创建教师身份失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_institution_identity(self, institution_name: str, **kwargs) -> Dict[str, Any]:
        try:
            identity_id = f"iid_{uuid.uuid4().hex[:12]}"
            public_key = f"pub_{uuid.uuid4().hex[:32]}"
            private_key_hash = str(hash(f"priv_{uuid.uuid4().hex[:64]}"))
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO institution_identity (
                            identity_id, institution_name, institution_type,
                            address, license_number, education_type,
                            public_key, private_key_hash, status, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                    ''', (identity_id, institution_name, kwargs.get('institution_type'),
                          kwargs.get('address'), kwargs.get('license_number'),
                          kwargs.get('education_type', 'adult'), public_key,
                          private_key_hash, now, now))
                    conn.commit()
                    logger.info(f'创建机构身份: {institution_name} ({identity_id})')
                    return {'success': True, 'identity_id': identity_id, 'public_key': public_key}
        except Exception as e:
            logger.error(f'创建机构身份失败: {e}')
            return {'success': False, 'error': str(e)}

    def verify_identity(self, identity_id: str, identity_type: str) -> Dict[str, Any]:
        try:
            table_map = {
                'student': 'student_identity',
                'teacher': 'teacher_identity',
                'institution': 'institution_identity'
            }
            table = table_map.get(identity_type)
            if not table:
                return {'success': False, 'error': '不支持的身份类型'}
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(f'SELECT * FROM {table} WHERE identity_id = ?', (identity_id,))
                identity = cursor.fetchone()
                if not identity:
                    return {'success': False, 'error': '身份不存在'}
                is_valid = identity['status'] == 'active'
                now = datetime.now().isoformat()
                cursor.execute('''
                    INSERT INTO verification_logs (
                        log_id, identity_id, operation, operator_id,
                        operator_name, result, timestamp, details
                    ) VALUES (?, ?, 'identity_verify', ?, ?, ?, ?, ?)
                ''', (f"log_{uuid.uuid4().hex[:12]}", identity_id,
                      None, None, 'success' if is_valid else 'failed', now,
                      json.dumps({'status': identity['status']})))
                conn.commit()
                return {'success': True, 'is_valid': is_valid, 'identity': dict(identity)}
        except Exception as e:
            logger.error(f'验证身份失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 智能合约 ==========

    def deploy_contract(self, contract_type: str, contract_name: str, **kwargs) -> Dict[str, Any]:
        try:
            contract_id = f"cnt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO smart_contracts (
                            contract_id, contract_type, contract_name,
                            contract_code, bytecode, abi, owner_id,
                            status, education_type, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'deployed', ?, ?, ?)
                    ''', (contract_id, contract_type, contract_name,
                          kwargs.get('contract_code'), kwargs.get('bytecode'),
                          kwargs.get('abi'), kwargs.get('owner_id'),
                          kwargs.get('education_type', 'adult'), now, now))
                    conn.commit()
                    logger.info(f'部署合约: {contract_name} ({contract_id})')
                    return {'success': True, 'contract_id': contract_id}
        except Exception as e:
            logger.error(f'部署合约失败: {e}')
            return {'success': False, 'error': str(e)}

    def execute_contract(self, contract_id: str, method_name: str, **kwargs) -> Dict[str, Any]:
        try:
            execution_id = f"exe_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT status FROM smart_contracts WHERE contract_id = ?', (contract_id,))
                    contract = cursor.fetchone()
                    if not contract or contract[0] != 'deployed':
                        return {'success': False, 'error': '合约未部署或状态异常'}
                    cursor.execute('''
                        INSERT INTO contract_executions (
                            execution_id, contract_id, method_name,
                            parameters, result, gas_used,
                            execution_time, education_type
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (execution_id, contract_id, method_name,
                          json.dumps(kwargs.get('parameters', {})),
                          kwargs.get('result', 'success'),
                          kwargs.get('gas_used', 0), now,
                          kwargs.get('education_type', 'adult')))
                    conn.commit()
                    logger.info(f'执行合约: {contract_id}.{method_name}')
                    return {'success': True, 'execution_id': execution_id}
        except Exception as e:
            logger.error(f'执行合约失败: {e}')
            return {'success': False, 'error': str(e)}

    def query_contract(self, contract_id: str = None, contract_type: str = None,
                       page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM smart_contracts WHERE 1=1'
                params = []
                if contract_id:
                    query += ' AND contract_id = ?'
                    params.append(contract_id)
                if contract_type:
                    query += ' AND contract_type = ?'
                    params.append(contract_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                contracts = [dict(c) for c in cursor.fetchall()]
                return {'success': True, 'contracts': contracts, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'查询合约失败: {e}')
            return {'success': False, 'error': str(e)}

    def upgrade_contract(self, contract_id: str, **kwargs) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE smart_contracts SET
                            contract_code = COALESCE(?, contract_code),
                            bytecode = COALESCE(?, bytecode),
                            abi = COALESCE(?, abi),
                            updated_at = ?
                        WHERE contract_id = ? AND status = ?
                    ''', (kwargs.get('contract_code'), kwargs.get('bytecode'),
                          kwargs.get('abi'), now, contract_id, 'deployed'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'升级合约: {contract_id}')
                        return {'success': True}
                    return {'success': False, 'error': '合约状态不允许升级'}
        except Exception as e:
            logger.error(f'升级合约失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 去中心化存储 ==========

    def store_data(self, storage_type: str, content_hash: str, **kwargs) -> Dict[str, Any]:
        try:
            storage_id = f"str_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO decentralized_storage (
                            storage_id, storage_type, content_hash,
                            content_type, size, node_ids, status,
                            education_type, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'stored', ?, ?, ?)
                    ''', (storage_id, storage_type, content_hash,
                          kwargs.get('content_type'), kwargs.get('size'),
                          json.dumps(kwargs.get('node_ids', [])),
                          kwargs.get('education_type', 'adult'), now, now))
                    conn.commit()
                    logger.info(f'存储数据: {storage_id} ({storage_type})')
                    return {'success': True, 'storage_id': storage_id}
        except Exception as e:
            logger.error(f'存储数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def retrieve_data(self, storage_id: str) -> Dict[str, Any]:
        try:
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM decentralized_storage WHERE storage_id = ?', (storage_id,))
                    storage = cursor.fetchone()
                    if not storage:
                        return {'success': False, 'error': '存储记录不存在'}
                    cursor.execute('UPDATE decentralized_storage SET updated_at = ? WHERE storage_id = ?', (now, storage_id))
                    conn.commit()
                    return {'success': True, 'storage': dict(storage)}
        except Exception as e:
            logger.error(f'检索数据失败: {e}')
            return {'success': False, 'error': str(e)}

    def delete_storage(self, storage_id: str) -> Dict[str, Any]:
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('UPDATE decentralized_storage SET status = ? WHERE storage_id = ? AND status = ?',
                                 ('deleted', storage_id, 'stored'))
                    if cursor.rowcount > 0:
                        conn.commit()
                        logger.info(f'删除存储: {storage_id}')
                        return {'success': True}
                    return {'success': False, 'error': '存储记录不存在或已删除'}
        except Exception as e:
            logger.error(f'删除存储失败: {e}')
            return {'success': False, 'error': str(e)}

    def query_storage(self, storage_type: str = None, content_hash: str = None,
                      page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM decentralized_storage WHERE status != "deleted"'
                params = []
                if storage_type:
                    query += ' AND storage_type = ?'
                    params.append(storage_type)
                if content_hash:
                    query += ' AND content_hash LIKE ?'
                    params.append(f'%{content_hash}%')
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                storages = [dict(s) for s in cursor.fetchall()]
                return {'success': True, 'storages': storages, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'查询存储失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 区块链查询 ==========

    def query_transaction(self, tx_hash: str = None, from_address: str = None,
                          tx_type: str = None, page: int = 1,
                          page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM transaction_records WHERE 1=1'
                params = []
                if tx_hash:
                    query += ' AND tx_hash LIKE ?'
                    params.append(f'%{tx_hash}%')
                if from_address:
                    query += ' AND from_address = ?'
                    params.append(from_address)
                if tx_type:
                    query += ' AND tx_type = ?'
                    params.append(tx_type)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                transactions = [dict(t) for t in cursor.fetchall()]
                return {'success': True, 'transactions': transactions, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'查询交易失败: {e}')
            return {'success': False, 'error': str(e)}

    def query_block(self, block_number: int = None, block_hash: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                if block_number:
                    cursor.execute('SELECT * FROM block_headers WHERE block_number = ?', (block_number,))
                elif block_hash:
                    cursor.execute('SELECT * FROM block_headers WHERE block_hash LIKE ?', (f'%{block_hash}%',))
                else:
                    cursor.execute('SELECT * FROM block_headers ORDER BY block_number DESC LIMIT 1')
                block = cursor.fetchone()
                if not block:
                    return {'success': False, 'error': '区块不存在'}
                return {'success': True, 'block': dict(block)}
        except Exception as e:
            logger.error(f'查询区块失败: {e}')
            return {'success': False, 'error': str(e)}

    def get_latest_block(self) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM block_headers ORDER BY block_number DESC LIMIT 1')
                block = cursor.fetchone()
                if not block:
                    return {'success': False, 'error': '暂无区块数据'}
                return {'success': True, 'block': dict(block)}
        except Exception as e:
            logger.error(f'获取最新区块失败: {e}')
            return {'success': False, 'error': str(e)}

    def query_merkle_tree(self, tree_id: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                if tree_id:
                    cursor.execute('SELECT * FROM merkle_trees WHERE tree_id = ?', (tree_id,))
                else:
                    cursor.execute('SELECT * FROM merkle_trees ORDER BY created_at DESC LIMIT 1')
                tree = cursor.fetchone()
                if not tree:
                    return {'success': False, 'error': '默克尔树不存在'}
                return {'success': True, 'merkle_tree': dict(tree)}
        except Exception as e:
            logger.error(f'查询默克尔树失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 跨链互操作 ==========

    def cross_chain_verify(self, source_chain: str, certificate_no: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"ccv_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO cross_chain_records (
                            record_id, interop_type, source_chain,
                            target_chain, data_hash, status, education_type, created_at
                        ) VALUES (?, 'cross_chain_verify', ?, ?, ?, 'processing', ?, ?)
                    ''', (record_id, source_chain, kwargs.get('target_chain', 'local'),
                          str(hash(certificate_no)), kwargs.get('education_type', 'adult'), now))
                    cursor.execute('UPDATE cross_chain_records SET status = ?, confirmation_count = ? WHERE record_id = ?',
                                 ('completed', kwargs.get('confirmations', 1), record_id))
                    conn.commit()
                    logger.info(f'跨链验证: {source_chain} -> {certificate_no}')
                    return {'success': True, 'record_id': record_id, 'status': 'completed'}
        except Exception as e:
            logger.error(f'跨链验证失败: {e}')
            return {'success': False, 'error': str(e)}

    def cross_chain_transfer(self, source_chain: str, target_chain: str,
                             data_hash: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"cct_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO cross_chain_records (
                            record_id, interop_type, source_chain,
                            target_chain, data_hash, status, education_type, created_at
                        ) VALUES (?, 'cross_chain_transfer', ?, ?, ?, 'processing', ?, ?)
                    ''', (record_id, source_chain, target_chain, data_hash,
                          kwargs.get('education_type', 'adult'), now))
                    cursor.execute('UPDATE cross_chain_records SET status = ?, transaction_hash = ? WHERE record_id = ?',
                                 ('completed', f"tx_{uuid.uuid4().hex[:16]}", record_id))
                    conn.commit()
                    logger.info(f'跨链转移: {source_chain} -> {target_chain}')
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'跨链转移失败: {e}')
            return {'success': False, 'error': str(e)}

    def cross_chain_query(self, target_chain: str, query_type: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"ccq_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO cross_chain_records (
                            record_id, interop_type, source_chain,
                            target_chain, data_hash, status, education_type, created_at
                        ) VALUES (?, 'cross_chain_query', 'local', ?, ?, 'processing', ?, ?)
                    ''', (record_id, target_chain, str(hash(query_type)),
                          kwargs.get('education_type', 'adult'), now))
                    cursor.execute('UPDATE cross_chain_records SET status = ?, confirmation_count = ? WHERE record_id = ?',
                                 ('completed', kwargs.get('confirmations', 1), record_id))
                    conn.commit()
                    logger.info(f'跨链查询: local -> {target_chain}')
                    return {'success': True, 'record_id': record_id, 'data': kwargs.get('mock_data', {})}
        except Exception as e:
            logger.error(f'跨链查询失败: {e}')
            return {'success': False, 'error': str(e)}

    def cross_chain_contract(self, source_chain: str, target_chain: str,
                             contract_id: str, method_name: str, **kwargs) -> Dict[str, Any]:
        try:
            record_id = f"ccc_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO cross_chain_records (
                            record_id, interop_type, source_chain,
                            target_chain, data_hash, status, education_type, created_at
                        ) VALUES (?, 'cross_chain_contract', ?, ?, ?, 'processing', ?, ?)
                    ''', (record_id, source_chain, target_chain,
                          str(hash(f"{contract_id}.{method_name}")),
                          kwargs.get('education_type', 'adult'), now))
                    cursor.execute('UPDATE cross_chain_records SET status = ?, transaction_hash = ? WHERE record_id = ?',
                                 ('completed', f"tx_{uuid.uuid4().hex[:16]}", record_id))
                    conn.commit()
                    logger.info(f'跨链合约: {source_chain} -> {target_chain} {contract_id}.{method_name}')
                    return {'success': True, 'record_id': record_id}
        except Exception as e:
            logger.error(f'跨链合约失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 验证审计 ==========

    def log_verification(self, certificate_id: str, operation: str,
                         operator_id: str, operator_name: str, result: str, **kwargs) -> Dict[str, Any]:
        try:
            log_id = f"log_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO verification_logs (
                            log_id, certificate_id, identity_id, operation,
                            operator_id, operator_name, result, timestamp,
                            education_type, details
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (log_id, certificate_id, kwargs.get('identity_id'),
                          operation, operator_id, operator_name, result, now,
                          kwargs.get('education_type', 'adult'),
                          json.dumps(kwargs.get('details', {}))))
                    conn.commit()
                    return {'success': True, 'log_id': log_id}
        except Exception as e:
            logger.error(f'记录验证日志失败: {e}')
            return {'success': False, 'error': str(e)}

    def create_audit_trail(self, action: str, resource_type: str,
                           resource_id: str, operator_id: str, **kwargs) -> Dict[str, Any]:
        try:
            trail_id = f"aud_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO audit_trails (
                            trail_id, action, resource_type, resource_id,
                            operator_id, operator_name, timestamp,
                            education_type, details
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (trail_id, action, resource_type, resource_id,
                          operator_id, kwargs.get('operator_name'), now,
                          kwargs.get('education_type', 'adult'),
                          json.dumps(kwargs.get('details', {}))))
                    conn.commit()
                    return {'success': True, 'trail_id': trail_id}
        except Exception as e:
            logger.error(f'创建审计追踪失败: {e}')
            return {'success': False, 'error': str(e)}

    def query_verification_logs(self, certificate_id: str = None, operation: str = None,
                                page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM verification_logs WHERE 1=1'
                params = []
                if certificate_id:
                    query += ' AND certificate_id = ?'
                    params.append(certificate_id)
                if operation:
                    query += ' AND operation = ?'
                    params.append(operation)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                logs = [dict(l) for l in cursor.fetchall()]
                return {'success': True, 'logs': logs, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'查询验证日志失败: {e}')
            return {'success': False, 'error': str(e)}

    def query_audit_trails(self, action: str = None, resource_type: str = None,
                           resource_id: str = None, page: int = 1,
                           page_size: int = 20) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                query = 'SELECT * FROM audit_trails WHERE 1=1'
                params = []
                if action:
                    query += ' AND action = ?'
                    params.append(action)
                if resource_type:
                    query += ' AND resource_type = ?'
                    params.append(resource_type)
                if resource_id:
                    query += ' AND resource_id = ?'
                    params.append(resource_id)
                cursor.execute(f'SELECT COUNT(*) as cnt FROM ({query})', params)
                total = cursor.fetchone()['cnt']
                query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
                params.extend([page_size, (page - 1) * page_size])
                cursor.execute(query, params)
                trails = [dict(t) for t in cursor.fetchall()]
                return {'success': True, 'trails': trails, 'total': total, 'page': page, 'page_size': page_size}
        except Exception as e:
            logger.error(f'查询审计追踪失败: {e}')
            return {'success': False, 'error': str(e)}

    def generate_compliance_report(self, education_type: str = None, **kwargs) -> Dict[str, Any]:
        try:
            report_id = f"rpt_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = 'SELECT COUNT(*) FROM certificates'
                params = []
                if education_type:
                    query += ' WHERE education_type = ?'
                    params.append(education_type)
                cursor.execute(query, params)
                cert_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM student_identity WHERE status = "active"')
                student_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM teacher_identity WHERE status = "active"')
                teacher_count = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM verification_logs')
                verification_count = cursor.fetchone()[0]
                report = {
                    'report_id': report_id,
                    'generated_at': now,
                    'certificate_count': cert_count,
                    'active_student_count': student_count,
                    'active_teacher_count': teacher_count,
                    'verification_count': verification_count,
                    'education_type': education_type or 'all',
                    'compliance_status': 'compliant'
                }
                return {'success': True, 'report': report}
        except Exception as e:
            logger.error(f'生成合规报告失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 链上治理 ==========

    def register_node(self, node_name: str, node_type: str, **kwargs) -> Dict[str, Any]:
        try:
            node_id = f"nd_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO blockchain_nodes (
                            node_id, node_name, node_type, chain_type,
                            ip_address, port, status, is_validator,
                            stake_amount, last_sync_time, education_type,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?, ?)
                    ''', (node_id, node_name, node_type, kwargs.get('chain_type', 'consortium'),
                          kwargs.get('ip_address'), kwargs.get('port'),
                          kwargs.get('is_validator', 0), kwargs.get('stake_amount', 0),
                          now, kwargs.get('education_type', 'adult'), now, now))
                    conn.commit()
                    logger.info(f'注册节点: {node_name} ({node_id})')
                    return {'success': True, 'node_id': node_id}
        except Exception as e:
            logger.error(f'注册节点失败: {e}')
            return {'success': False, 'error': str(e)}

    def update_chain_config(self, chain_type: str, **kwargs) -> Dict[str, Any]:
        try:
            config_id = f"cfg_{chain_type}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT config_id FROM chain_config WHERE chain_type = ?', (chain_type,))
                    existing = cursor.fetchone()
                    if existing:
                        cursor.execute('''
                            UPDATE chain_config SET
                                consensus_algorithm = COALESCE(?, consensus_algorithm),
                                block_size = COALESCE(?, block_size),
                                block_interval = COALESCE(?, block_interval),
                                gas_limit = COALESCE(?, gas_limit),
                                validators_count = COALESCE(?, validators_count),
                                updated_at = ?
                            WHERE chain_type = ?
                        ''', (kwargs.get('consensus_algorithm'), kwargs.get('block_size'),
                              kwargs.get('block_interval'), kwargs.get('gas_limit'),
                              kwargs.get('validators_count'), now, chain_type))
                    else:
                        cursor.execute('''
                            INSERT INTO chain_config (
                                config_id, chain_type, consensus_algorithm,
                                block_size, block_interval, gas_limit,
                                validators_count, education_type, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (config_id, chain_type, kwargs.get('consensus_algorithm', 'PBFT'),
                              kwargs.get('block_size', 1000), kwargs.get('block_interval', 10),
                              kwargs.get('gas_limit', 8000000), kwargs.get('validators_count', 4),
                              kwargs.get('education_type', 'adult'), now, now))
                    conn.commit()
                    logger.info(f'更新链配置: {chain_type}')
                    return {'success': True, 'config_id': config_id}
        except Exception as e:
            logger.error(f'更新链配置失败: {e}')
            return {'success': False, 'error': str(e)}

    def sync_chain_data(self, chain_type: str, **kwargs) -> Dict[str, Any]:
        try:
            sync_id = f"sync_{uuid.uuid4().hex[:12]}"
            now = datetime.now().isoformat()
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO chain_sync_status (
                            sync_id, chain_type, sync_type, last_block,
                            target_block, progress, status, education_type, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (sync_id, chain_type, kwargs.get('sync_type', 'full'),
                          kwargs.get('last_block', 0), kwargs.get('target_block', 0),
                          0, 'syncing', kwargs.get('education_type', 'adult'), now))
                    cursor.execute('UPDATE chain_sync_status SET progress = ?, status = ? WHERE sync_id = ?',
                                 (kwargs.get('progress', 100), 'completed', sync_id))
                    conn.commit()
                    logger.info(f'同步链数据: {chain_type}')
                    return {'success': True, 'sync_id': sync_id}
        except Exception as e:
            logger.error(f'同步链数据失败: {e}')
            return {'success': False, 'error': str(e)}

    # ========== 统计 ==========

    def get_statistics(self, education_type: str = None) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                where_clause = f' WHERE education_type = "{education_type}"' if education_type else ''

                cursor.execute(f'SELECT COUNT(*) FROM certificates{where_clause}')
                cert_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM student_identity WHERE status = "active"{where_clause}')
                student_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM teacher_identity WHERE status = "active"{where_clause}')
                teacher_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM institution_identity WHERE status = "active"{where_clause}')
                institution_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM smart_contracts{where_clause}')
                contract_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM contract_executions{where_clause}')
                execution_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM transaction_records{where_clause}')
                tx_count = cursor.fetchone()[0]

                cursor.execute(f'SELECT COUNT(*) FROM cross_chain_records{where_clause}')
                cross_chain_count = cursor.fetchone()[0]

                cursor.execute('SELECT MAX(block_number) FROM block_headers')
                latest_block = cursor.fetchone()[0] or 0

                statistics = {
                    'certificate_count': cert_count,
                    'student_count': student_count,
                    'teacher_count': teacher_count,
                    'institution_count': institution_count,
                    'contract_count': contract_count,
                    'contract_execution_count': execution_count,
                    'transaction_count': tx_count,
                    'cross_chain_transaction_count': cross_chain_count,
                    'latest_block_number': latest_block,
                    'education_type': education_type or 'all',
                    'generated_at': datetime.now().isoformat()
                }
                return {'success': True, 'statistics': statistics}
        except Exception as e:
            logger.error(f'获取统计数据失败: {e}')
            return {'success': False, 'error': str(e)}