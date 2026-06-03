#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据安全法则 - Data Security Framework
MTSCOS AI Project v3.1
数据分类、加密、访问控制和审计追踪
"""

import os
import sys
import json
import sqlite3
import logging
import hashlib
import hmac
import time
import base64
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_security.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('data_security')

class DataClassification(Enum):
    """数据分类"""
    PUBLIC = "public"              # 公开数据
    INTERNAL = "internal"          # 内部数据
    CONFIDENTIAL = "confidential"  # 机密数据
    SECRET = "secret"             # 绝密数据
    RESTRICTED = "restricted"     # 受限数据

class DataType(Enum):
    """数据类型"""
    PERSONAL_INFO = "personal_info"          # 个人信息
    FINANCIAL_DATA = "financial_data"        # 财务数据
    HEALTH_DATA = "health_data"            # 健康数据
    BUSINESS_DATA = "business_data"        # 业务数据
    TECHNICAL_DATA = "technical_data"      # 技术数据
    COMMUNICATION = "communication"        # 通讯数据
    AUTHENTICATION = "authentication"      # 认证数据
    CUSTOMER_DATA = "customer_data"        # 客户数据
    EMPLOYEE_DATA = "employee_data"        # 员工数据
    INTELLECTUAL_PROPERTY = "intellectual_property"  # 知识产权

class EncryptionLevel(Enum):
    """加密级别"""
    NONE = 0           # 无需加密
    BASIC = 1         # 基本加密
    STANDARD = 2       # 标准加密
    STRONG = 3        # 强加密
    MILITARY = 4      # 军事级加密

class AccessLevel(Enum):
    """访问级别"""
    NONE = 0       # 无权限
    READ = 1       # 只读
    WRITE = 2      # 读写
    DELETE = 3     # 删除权限
    ADMIN = 4      # 管理权限
    OWNER = 5      # 所有者权限

@dataclass
class DataAsset:
    """数据资产"""
    asset_id: str
    name: str
    description: str
    data_type: DataType
    classification: DataClassification
    owner_id: str
    encryption_level: EncryptionLevel
    created_at: str
    updated_at: str
    last_accessed: str = None
    access_count: int = 0
    size_bytes: int = 0
    checksum: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    encrypted: int = 0

@dataclass
class AccessPolicy:
    """访问策略"""
    policy_id: str
    name: str
    description: str
    classification: DataClassification
    required_clearance: int
    allowed_roles: List[str]
    allowed_users: List[str]
    denied_users: List[str]
    conditions: Dict[str, Any] = field(default_factory=dict)
    audit_required: bool = True
    encryption_required: bool = True
    time_restrictions: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DataAccess:
    """数据访问记录"""
    access_id: str
    user_id: str
    asset_id: str
    access_type: str
    timestamp: str
    ip_address: str
    success: bool
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DataIntegrityCheck:
    """数据完整性检查"""
    check_id: str
    asset_id: str
    timestamp: str
    expected_checksum: str
    actual_checksum: str
    status: str
    details: str = ""

class EncryptionManager:
    """加密管理器"""
    
    def __init__(self, master_key: str = None):
        self.master_key = master_key or base64.b64encode(secrets.token_bytes(32)).decode()
    
    def encrypt(self, data: str) -> str:
        """加密数据"""
        try:
            key = hashlib.sha256(self.master_key.encode()).digest()
            encrypted = []
            for i, char in enumerate(data.encode()):
                encrypted.append(char ^ key[i % len(key)])
            return base64.b64encode(bytes(encrypted)).decode()
        except Exception as e:
            logger.error(f"加密失败: {e}")
            return None
    
    def decrypt(self, encrypted_data: str) -> str:
        """解密数据"""
        try:
            key = hashlib.sha256(self.master_key.encode()).digest()
            decoded = base64.b64decode(encrypted_data.encode())
            decrypted = []
            for i, byte in enumerate(decoded):
                decrypted.append(byte ^ key[i % len(key)])
            return bytes(decrypted).decode()
        except Exception as e:
            logger.error(f"解密失败: {e}")
            return None
    
    def generate_checksum(self, data: str) -> str:
        """生成校验和"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def verify_checksum(self, data: str, expected_checksum: str) -> bool:
        """验证校验和"""
        return self.generate_checksum(data) == expected_checksum
    
    def generate_hash(self, data: str, salt: str = "") -> str:
        """生成哈希"""
        return hashlib.pbkdf2_hmac(
            'sha256',
            data.encode(),
            salt.encode(),
            100000
        ).hex()
    
    def verify_hash(self, data: str, expected_hash: str, salt: str = "") -> bool:
        """验证哈希"""
        return self.generate_hash(data, salt) == expected_hash

class DataSecurityManager:
    """数据安全管理器"""
    
    def __init__(self, db_path: str = "data_security.db"):
        self.db_path = db_path
        self.encryption = EncryptionManager()
        self._init_database()
        self._init_default_policies()
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_assets (
                asset_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                data_type TEXT NOT NULL,
                classification TEXT NOT NULL,
                owner_id TEXT,
                encryption_level INTEGER,
                created_at TEXT,
                updated_at TEXT,
                last_accessed TEXT,
                access_count INTEGER DEFAULT 0,
                size_bytes INTEGER DEFAULT 0,
                checksum TEXT,
                metadata TEXT,
                encrypted INTEGER DEFAULT 0
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS access_policies (
                policy_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                classification TEXT NOT NULL,
                required_clearance INTEGER,
                allowed_roles TEXT,
                allowed_users TEXT,
                denied_users TEXT,
                conditions TEXT,
                audit_required INTEGER DEFAULT 1,
                encryption_required INTEGER DEFAULT 1,
                time_restrictions TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_access (
                access_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                asset_id TEXT NOT NULL,
                access_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                ip_address TEXT,
                success INTEGER,
                reason TEXT,
                metadata TEXT,
                FOREIGN KEY (asset_id) REFERENCES data_assets(asset_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_integrity (
                check_id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                expected_checksum TEXT,
                actual_checksum TEXT,
                status TEXT,
                details TEXT,
                FOREIGN KEY (asset_id) REFERENCES data_assets(asset_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS encryption_keys (
                key_id TEXT PRIMARY KEY,
                asset_id TEXT,
                key_type TEXT,
                encrypted_key TEXT,
                created_at TEXT,
                expires_at TEXT,
                status TEXT,
                FOREIGN KEY (asset_id) REFERENCES data_assets(asset_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                severity TEXT,
                user_id TEXT,
                asset_id TEXT,
                description TEXT,
                timestamp TEXT,
                resolved INTEGER DEFAULT 0
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_audit (
                audit_id TEXT PRIMARY KEY,
                action TEXT NOT NULL,
                user_id TEXT,
                asset_id TEXT,
                old_value TEXT,
                new_value TEXT,
                timestamp TEXT,
                ip_address TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"数据安全数据库初始化完成: {self.db_path}")
    
    def _init_default_policies(self):
        """初始化默认策略"""
        default_policies = [
            {
                'policy_id': 'DP-001',
                'name': '公开数据访问策略',
                'description': '公开数据的访问控制策略',
                'classification': DataClassification.PUBLIC,
                'required_clearance': 0,
                'allowed_roles': ['*'],
                'audit_required': False,
                'encryption_required': False
            },
            {
                'policy_id': 'DP-002',
                'name': '内部数据访问策略',
                'description': '内部数据的访问控制策略',
                'classification': DataClassification.INTERNAL,
                'required_clearance': 1,
                'allowed_roles': ['employee', 'manager', 'admin'],
                'audit_required': True,
                'encryption_required': False
            },
            {
                'policy_id': 'DP-003',
                'name': '机密数据访问策略',
                'description': '机密数据的访问控制策略',
                'classification': DataClassification.CONFIDENTIAL,
                'required_clearance': 2,
                'allowed_roles': ['manager', 'admin'],
                'allowed_users': [],
                'audit_required': True,
                'encryption_required': True
            },
            {
                'policy_id': 'DP-004',
                'name': '绝密数据访问策略',
                'description': '绝密数据的访问控制策略',
                'classification': DataClassification.SECRET,
                'required_clearance': 3,
                'allowed_roles': ['admin'],
                'allowed_users': [],
                'audit_required': True,
                'encryption_required': True,
                'time_restrictions': {'start': '09:00', 'end': '18:00'}
            },
            {
                'policy_id': 'DP-005',
                'name': '受限数据访问策略',
                'description': '受限数据的访问控制策略',
                'classification': DataClassification.RESTRICTED,
                'required_clearance': 4,
                'allowed_roles': ['admin', 'owner'],
                'allowed_users': ['owner'],
                'audit_required': True,
                'encryption_required': True
            }
        ]
        
        for policy_data in default_policies:
            policy = AccessPolicy(
                policy_id=policy_data['policy_id'],
                name=policy_data['name'],
                description=policy_data['description'],
                classification=policy_data['classification'],
                required_clearance=policy_data['required_clearance'],
                allowed_roles=policy_data['allowed_roles'],
                allowed_users=policy_data.get('allowed_users', []),
                denied_users=policy_data.get('denied_users', []),
                audit_required=policy_data['audit_required'],
                encryption_required=policy_data['encryption_required'],
                time_restrictions=policy_data.get('time_restrictions', {})
            )
            self._save_policy(policy)
    
    def register_data_asset(self, name: str, description: str, data_type: DataType,
                          classification: DataClassification, owner_id: str,
                          size_bytes: int = 0, metadata: Dict = None) -> str:
        """注册数据资产"""
        asset_id = f"DA-{hashlib.md5(f'{name}{time.time()}'.encode()).hexdigest()[:12]}"
        
        encryption_level = self._determine_encryption_level(classification)
        checksum = self.encryption.generate_checksum(f"{name}{description}")
        
        asset = DataAsset(
            asset_id=asset_id,
            name=name,
            description=description,
            data_type=data_type,
            classification=classification,
            owner_id=owner_id,
            encryption_level=encryption_level,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            size_bytes=size_bytes,
            checksum=checksum,
            metadata=metadata or {},
            encrypted=1 if encryption_level != EncryptionLevel.NONE else 0
        )
        
        self._save_asset(asset)
        
        self._log_security_event(
            "data_registered",
            "info",
            owner_id,
            asset_id,
            f"数据资产已注册: {name}"
        )
        
        logger.info(f"数据资产已注册: {asset_id}")
        return asset_id
    
    def _determine_encryption_level(self, classification: DataClassification) -> EncryptionLevel:
        """确定加密级别"""
        levels = {
            DataClassification.PUBLIC: EncryptionLevel.NONE,
            DataClassification.INTERNAL: EncryptionLevel.BASIC,
            DataClassification.CONFIDENTIAL: EncryptionLevel.STANDARD,
            DataClassification.SECRET: EncryptionLevel.STRONG,
            DataClassification.RESTRICTED: EncryptionLevel.MILITARY
        }
        return levels.get(classification, EncryptionLevel.STANDARD)
    
    def _save_asset(self, asset: DataAsset):
        """保存数据资产"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO data_assets 
            (asset_id, name, description, data_type, classification, owner_id,
             encryption_level, created_at, updated_at, last_accessed, access_count,
             size_bytes, checksum, metadata, encrypted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            asset.asset_id, asset.name, asset.description, asset.data_type.value,
            asset.classification.value, asset.owner_id, asset.encryption_level.value,
            asset.created_at, asset.updated_at, asset.last_accessed, asset.access_count,
            asset.size_bytes, asset.checksum, json.dumps(asset.metadata), asset.encrypted
        ))
        conn.commit()
        conn.close()
    
    def _save_policy(self, policy: AccessPolicy):
        """保存访问策略"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO access_policies 
            (policy_id, name, description, classification, required_clearance,
             allowed_roles, allowed_users, denied_users, conditions, audit_required,
             encryption_required, time_restrictions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            policy.policy_id, policy.name, policy.description, policy.classification.value,
            policy.required_clearance, json.dumps(policy.allowed_roles),
            json.dumps(policy.allowed_users), json.dumps(policy.denied_users),
            json.dumps(policy.conditions), int(policy.audit_required),
            int(policy.encryption_required), json.dumps(policy.time_restrictions)
        ))
        conn.commit()
        conn.close()
    
    def check_access_permission(self, user_id: str, asset_id: str, 
                              access_level: AccessLevel, user_role: str = "user") -> Tuple[bool, str]:
        """检查访问权限"""
        asset = self._get_asset(asset_id)
        if not asset:
            return False, "数据资产不存在"
        
        policy = self._get_policy(asset.classification)
        if not policy:
            return False, "未找到访问策略"
        
        if user_id in policy.denied_users:
            return False, "用户被拒绝访问"
        
        if policy.allowed_users and user_id not in policy.allowed_users:
            if user_role not in policy.allowed_roles and '*' not in policy.allowed_roles:
                return False, "用户角色无权访问"
        
        if policy.time_restrictions:
            current_hour = datetime.now().hour
            start_hour = int(policy.time_restrictions.get('start', '00:00').split(':')[0])
            end_hour = int(policy.time_restrictions.get('end', '23:59').split(':')[0])
            if not (start_hour <= current_hour < end_hour):
                return False, f"访问时间限制: {start_hour}:00-{end_hour}:00"
        
        return True, "允许访问"
    
    def request_access(self, user_id: str, asset_id: str, 
                     access_level: AccessLevel, ip_address: str = "",
                     user_role: str = "user") -> Tuple[bool, str]:
        """请求数据访问"""
        allowed, reason = self.check_access_permission(user_id, asset_id, access_level, user_role)
        
        access_type = "read" if access_level == AccessLevel.READ else "write" if access_level == AccessLevel.WRITE else "delete"
        
        access_record = DataAccess(
            access_id=f"DA-{int(time.time())}-{hashlib.md5(f'{user_id}{asset_id}'.encode()).hexdigest()[:8]}",
            user_id=user_id,
            asset_id=asset_id,
            access_type=access_type,
            timestamp=datetime.now().isoformat(),
            ip_address=ip_address,
            success=allowed,
            reason=reason
        )
        
        self._save_access(access_record)
        
        if allowed:
            self._update_asset_access(asset_id)
            self._log_audit("access_granted", user_id, asset_id)
            logger.info(f"访问已授权: {user_id} -> {asset_id}")
        else:
            self._log_security_event(
                "access_denied",
                "warning",
                user_id,
                asset_id,
                f"访问被拒绝: {reason}"
            )
            logger.warning(f"访问被拒绝: {user_id} -> {asset_id}: {reason}")
        
        return allowed, reason
    
    def _get_asset(self, asset_id: str) -> Optional[DataAsset]:
        """获取数据资产"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM data_assets WHERE asset_id = ?", (asset_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        columns = ['asset_id', 'name', 'description', 'data_type', 'classification',
                  'owner_id', 'encryption_level', 'created_at', 'updated_at',
                  'last_accessed', 'access_count', 'size_bytes', 'checksum', 'metadata', 'encrypted']
        
        data = dict(zip(columns, row))
        data['data_type'] = DataType(data['data_type'])
        data['classification'] = DataClassification(data['classification'])
        data['encryption_level'] = EncryptionLevel(data['encryption_level'])
        data['metadata'] = json.loads(data['metadata']) if data['metadata'] else {}
        
        return DataAsset(**data)
    
    def _get_policy(self, classification: DataClassification) -> Optional[AccessPolicy]:
        """获取访问策略"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM access_policies WHERE classification = ?
        """, (classification.value,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        columns = ['policy_id', 'name', 'description', 'classification', 'required_clearance',
                  'allowed_roles', 'allowed_users', 'denied_users', 'conditions',
                  'audit_required', 'encryption_required', 'time_restrictions']
        
        data = dict(zip(columns, row))
        data['classification'] = DataClassification(data['classification'])
        data['allowed_roles'] = json.loads(data['allowed_roles'])
        data['allowed_users'] = json.loads(data['allowed_users'])
        data['denied_users'] = json.loads(data['denied_users'])
        data['conditions'] = json.loads(data['conditions'])
        data['audit_required'] = bool(data['audit_required'])
        data['encryption_required'] = bool(data['encryption_required'])
        data['time_restrictions'] = json.loads(data['time_restrictions'])
        
        return AccessPolicy(**data)
    
    def _save_access(self, access: DataAccess):
        """保存访问记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO data_access 
            (access_id, user_id, asset_id, access_type, timestamp, ip_address, success, reason, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            access.access_id, access.user_id, access.asset_id, access.access_type,
            access.timestamp, access.ip_address, int(access.success), access.reason,
            json.dumps(access.metadata)
        ))
        conn.commit()
        conn.close()
    
    def _update_asset_access(self, asset_id: str):
        """更新资产访问信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE data_assets 
            SET last_accessed = ?, access_count = access_count + 1
            WHERE asset_id = ?
        """, (datetime.now().isoformat(), asset_id))
        conn.commit()
        conn.close()
    
    def check_data_integrity(self, asset_id: str, data: str = None) -> DataIntegrityCheck:
        """检查数据完整性"""
        asset = self._get_asset(asset_id)
        if not asset:
            return None
        
        if data is None:
            data = f"{asset.name}{asset.description}"
        
        actual_checksum = self.encryption.generate_checksum(data)
        
        integrity_check = DataIntegrityCheck(
            check_id=f"IC-{int(time.time())}-{secrets.token_hex(4)}",
            asset_id=asset_id,
            timestamp=datetime.now().isoformat(),
            expected_checksum=asset.checksum,
            actual_checksum=actual_checksum,
            status="pass" if actual_checksum == asset.checksum else "fail",
            details="校验通过" if actual_checksum == asset.checksum else "数据被篡改"
        )
        
        self._save_integrity_check(integrity_check)
        
        if actual_checksum != asset.checksum:
            self._log_security_event(
                "integrity_violation",
                "critical",
                asset_id=asset_id,
                description=f"数据完整性检查失败: {asset_id}"
            )
            logger.critical(f"🚨 数据完整性违规: {asset_id}")
        
        return integrity_check
    
    def _save_integrity_check(self, check: DataIntegrityCheck):
        """保存完整性检查结果"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO data_integrity 
            (check_id, asset_id, timestamp, expected_checksum, actual_checksum, status, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            check.check_id, check.asset_id, check.timestamp, check.expected_checksum,
            check.actual_checksum, check.status, check.details
        ))
        conn.commit()
        conn.close()
    
    def encrypt_data(self, data: str, asset_id: str = None) -> str:
        """加密数据"""
        encrypted = self.encryption.encrypt(data)
        if encrypted and asset_id:
            self._log_audit("data_encrypted", asset_id=asset_id)
        return encrypted
    
    def decrypt_data(self, encrypted_data: str, asset_id: str = None) -> str:
        """解密数据"""
        decrypted = self.encryption.decrypt(encrypted_data)
        if decrypted and asset_id:
            self._log_audit("data_decrypted", asset_id=asset_id)
        return decrypted
    
    def _log_security_event(self, event_type: str, severity: str, 
                          user_id: str = None, asset_id: str = None, description: str = ""):
        """记录安全事件"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO security_events 
            (event_id, event_type, severity, user_id, asset_id, description, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            f"SE-{int(time.time())}-{secrets.token_hex(4)}",
            event_type, severity, user_id, asset_id, description,
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
    
    def _log_audit(self, action: str, user_id: str = None, asset_id: str = None,
                  old_value: str = None, new_value: str = None, ip_address: str = ""):
        """记录审计日志"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO data_audit 
            (audit_id, action, user_id, asset_id, old_value, new_value, timestamp, ip_address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"AU-{int(time.time())}-{secrets.token_hex(4)}",
            action, user_id, asset_id, old_value, new_value,
            datetime.now().isoformat(), ip_address
        ))
        conn.commit()
        conn.close()
    
    def get_data_assets(self, classification: DataClassification = None) -> List[DataAsset]:
        """获取数据资产列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if classification:
            cursor.execute("""
                SELECT * FROM data_assets WHERE classification = ?
            """, (classification.value,))
        else:
            cursor.execute("SELECT * FROM data_assets")
        
        rows = cursor.fetchall()
        conn.close()
        
        assets = []
        columns = ['asset_id', 'name', 'description', 'data_type', 'classification',
                  'owner_id', 'encryption_level', 'created_at', 'updated_at',
                  'last_accessed', 'access_count', 'size_bytes', 'checksum', 'metadata', 'encrypted']
        
        for row in rows:
            data = dict(zip(columns, row))
            data['data_type'] = DataType(data['data_type'])
            data['classification'] = DataClassification(data['classification'])
            data['encryption_level'] = EncryptionLevel(data['encryption_level'])
            data['metadata'] = json.loads(data['metadata']) if data['metadata'] else {}
            assets.append(DataAsset(**data))
        
        return assets
    
    def get_access_history(self, asset_id: str = None, user_id: str = None, 
                          limit: int = 100) -> List[Dict]:
        """获取访问历史"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM data_access WHERE 1=1"
        params = []
        
        if asset_id:
            query += " AND asset_id = ?"
            params.append(asset_id)
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        columns = ['access_id', 'user_id', 'asset_id', 'access_type', 'timestamp',
                  'ip_address', 'success', 'reason', 'metadata']
        
        return [dict(zip(columns, row)) for row in rows]
    
    def get_security_events(self, severity: str = None, limit: int = 50) -> List[Dict]:
        """获取安全事件"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if severity:
            cursor.execute("""
                SELECT * FROM security_events 
                WHERE severity = ? AND resolved = 0
                ORDER BY timestamp DESC LIMIT ?
            """, (severity, limit))
        else:
            cursor.execute("""
                SELECT * FROM security_events 
                WHERE resolved = 0
                ORDER BY timestamp DESC LIMIT ?
            """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        columns = ['event_id', 'event_type', 'severity', 'user_id', 'asset_id',
                  'description', 'timestamp', 'resolved']
        
        return [dict(zip(columns, row)) for row in rows]
    
    def get_security_statistics(self) -> Dict[str, Any]:
        """获取安全统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM data_assets")
        total_assets = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM data_access")
        total_access = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM data_access WHERE success = 1")
        successful_access = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM data_access WHERE success = 0")
        failed_access = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM security_events WHERE resolved = 0")
        active_events = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT classification, COUNT(*) 
            FROM data_assets 
            GROUP BY classification
        """)
        classification_dist = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_assets': total_assets,
            'total_access': total_access,
            'successful_access': successful_access,
            'failed_access': failed_access,
            'success_rate': f"{(successful_access/total_access*100):.2f}%" if total_access > 0 else "0%",
            'active_security_events': active_events,
            'classification_distribution': classification_dist
        }

def main():
    """测试主函数"""
    print("\n🔐 数据安全法则测试")
    print("=" * 60)
    
    manager = DataSecurityManager()
    
    print("\n📊 安全统计:")
    stats = manager.get_security_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n🧪 测试注册数据资产:")
    asset_id = manager.register_data_asset(
        name="客户数据库",
        description="包含客户个人信息和交易记录",
        data_type=DataType.CUSTOMER_DATA,
        classification=DataClassification.CONFIDENTIAL,
        owner_id="admin001",
        size_bytes=1024000
    )
    print(f"  资产ID: {asset_id}")
    
    print("\n🧪 测试访问权限检查:")
    allowed, reason = manager.request_access(
        user_id="user001",
        asset_id=asset_id,
        access_level=AccessLevel.READ,
        user_role="employee",
        ip_address="192.168.1.100"
    )
    print(f"  允许访问: {allowed}")
    print(f"  原因: {reason}")
    
    print("\n🧪 测试数据加密:")
    test_data = "这是一个测试数据，包含敏感信息！"
    encrypted = manager.encrypt_data(test_data, asset_id)
    print(f"  原始数据: {test_data[:20]}...")
    print(f"  加密后: {encrypted[:30]}...")
    
    decrypted = manager.decrypt_data(encrypted, asset_id)
    print(f"  解密后: {decrypted}")
    
    print("\n🧪 测试数据完整性检查:")
    integrity = manager.check_data_integrity(asset_id)
    print(f"  检查ID: {integrity.check_id}")
    print(f"  状态: {integrity.status}")
    print(f"  详情: {integrity.details}")
    
    print("\n🔍 获取安全事件:")
    events = manager.get_security_events()
    print(f"  活跃事件数: {len(events)}")
    for event in events[:3]:
        print(f"  - [{event['severity']}] {event['description']}")
    
    print("\n📋 访问历史:")
    history = manager.get_access_history(asset_id)
    print(f"  访问记录数: {len(history)}")
    
    print("\n📈 最终安全统计:")
    stats = manager.get_security_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("✅ 数据安全法则测试完成")

if __name__ == '__main__':
    main()
