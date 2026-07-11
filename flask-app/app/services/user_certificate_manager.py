import logging
logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
用户数字证书管理器
为每个用户生成唯一的数字ID证书
"""

import os
import sqlite3
import hashlib
import uuid
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import json
from typing import Dict, Optional, Any

class UserCertificateManager:
    """用户数字证书管理器"""
    
    def __init__(self, db_path: str = "app.db"):
        self.db_path = db_path
        self._init_tables()
        self.fernet = self._init_fernet()
    
    def _connect(self):
        return sqlite3.connect(self.db_path)
    
    def _init_tables(self):
        """初始化证书相关的数据库表"""
        with self._connect() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_certificates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    user_name TEXT NOT NULL,
                    certificate_id TEXT UNIQUE NOT NULL,
                    certificate_number TEXT UNIQUE NOT NULL,
                    encrypted_certificate TEXT NOT NULL,
                    issue_date TEXT NOT NULL,
                    expire_date TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    certificate_type TEXT DEFAULT 'digital_id',
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS certificate_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type_name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    validity_days INTEGER DEFAULT 365,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS certificate_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    certificate_id TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 初始化证书类型
            self._init_certificate_types(cursor)
            
            conn.commit()
    
    def _init_certificate_types(self, cursor):
        """初始化证书类型"""
        certificate_types = [
            ('digital_id', '数字身份证书', 365),
            ('student', '学生证书', 365),
            ('teacher', '教师证书', 365),
            ('admin', '管理员证书', 365),
            ('exam', '考试证书', 90),
            ('achievement', '成就证书', 3650),
            ('certified', '认证证书', 730),
            ('temporary', '临时证书', 7)
        ]
        
        for type_name, description, validity_days in certificate_types:
            cursor.execute('''
                INSERT OR IGNORE INTO certificate_types 
                (type_name, description, validity_days) 
                VALUES (?, ?, ?)
            ''', (type_name, description, validity_days))
    
    def _init_fernet(self) -> Fernet:
        """初始化Fernet加密器"""
        password = b'MTSCOS_CERTIFICATE_KEY_2024'
        salt = b'MTSCOS_CERT_SALT'
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return Fernet(key)
    
    def generate_certificate_number(self, user_id: int) -> str:
        """生成唯一的证书编号"""
        timestamp = int(datetime.now().timestamp())
        random_suffix = hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:6].upper()
        return f"MC-{user_id:06d}-{timestamp}-{random_suffix}"
    
    def generate_certificate_id(self) -> str:
        """生成唯一的证书ID"""
        return str(uuid.uuid4())
    
    def create_certificate(self, user_id: int, user_name: str, 
                          certificate_type: str = 'digital_id') -> Optional[Dict]:
        """为用户创建数字证书"""
        try:
            # 检查用户是否已有证书
            if self.has_certificate(user_id):
                self.log_certificate(user_id, 'CREATE', 'FAILED', '用户已存在证书')
                return None
            
            # 获取证书类型配置
            validity_days = self._get_validity_days(certificate_type)
            
            # 生成证书信息
            certificate_id = self.generate_certificate_id()
            certificate_number = self.generate_certificate_number(user_id)
            issue_date = datetime.now()
            expire_date = issue_date + timedelta(days=validity_days)
            
            # 创建证书内容
            certificate_content = {
                'certificate_id': certificate_id,
                'certificate_number': certificate_number,
                'user_id': user_id,
                'user_name': user_name,
                'issue_date': issue_date.isoformat(),
                'expire_date': expire_date.isoformat(),
                'type': certificate_type,
                'validity_days': validity_days,
                'issued_by': 'MTSCOS AI Project',
                'signature': hashlib.sha256(f"{user_id}{certificate_id}{certificate_number}".encode()).hexdigest()
            }
            
            # 加密证书内容
            encrypted_certificate = self._encrypt_certificate(certificate_content)
            
            # 保存到数据库
            with self._connect() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO user_certificates 
                    (user_id, user_name, certificate_id, certificate_number, 
                     encrypted_certificate, issue_date, expire_date, status, 
                     certificate_type, metadata, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
                ''', (user_id, user_name, certificate_id, certificate_number,
                      encrypted_certificate, issue_date.isoformat(), 
                      expire_date.isoformat(), certificate_type,
                      json.dumps(certificate_content), datetime.now()))
                
                conn.commit()
            
            self.log_certificate(user_id, 'CREATE', 'SUCCESS', f'证书已创建: {certificate_number}')
            
            return {
                'certificate_id': certificate_id,
                'certificate_number': certificate_number,
                'issue_date': issue_date.isoformat(),
                'expire_date': expire_date.isoformat(),
                'status': 'active',
                'type': certificate_type
            }
        
        except Exception as e:
            self.log_certificate(user_id, 'CREATE', 'FAILED', str(e))
            return None
    
    def _get_validity_days(self, certificate_type: str) -> int:
        """获取证书有效期天数"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT validity_days FROM certificate_types WHERE type_name = ?', (certificate_type,))
            row = cursor.fetchone()
            return row[0] if row else 365
    
    def _encrypt_certificate(self, content: Dict) -> str:
        """加密证书内容"""
        return self.fernet.encrypt(json.dumps(content).encode()).decode()
    
    def _decrypt_certificate(self, encrypted_content: str) -> Dict:
        """解密证书内容"""
        try:
            decrypted = self.fernet.decrypt(encrypted_content.encode()).decode()
            return json.loads(decrypted)
        except Exception as e:
            print(f"解密证书失败: {e}")
            return {}
    
    def has_certificate(self, user_id: int) -> bool:
        """检查用户是否已有证书"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM user_certificates WHERE user_id = ? AND status = "active"', (user_id,))
            return cursor.fetchone() is not None
    
    def get_certificate(self, user_id: int) -> Optional[Dict]:
        """获取用户的证书"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT certificate_id, certificate_number, encrypted_certificate, 
                           issue_date, expire_date, status, certificate_type, metadata
                    FROM user_certificates WHERE user_id = ? AND status = "active"
                ''', (user_id,))
                
                row = cursor.fetchone()
                if row:
                    decrypted = self._decrypt_certificate(row[2])
                    return {
                        'certificate_id': row[0],
                        'certificate_number': row[1],
                        'content': decrypted,
                        'issue_date': row[3],
                        'expire_date': row[4],
                        'status': row[5],
                        'type': row[6],
                        'metadata': json.loads(row[7]) if row[7] else {}
                    }
                return None
        except Exception as e:
            print(f"获取证书失败: {e}")
            return None
    
    def get_certificate_by_number(self, certificate_number: str) -> Optional[Dict]:
        """通过证书编号获取证书"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT user_id, user_name, certificate_id, encrypted_certificate,
                           issue_date, expire_date, status, certificate_type, metadata
                    FROM user_certificates WHERE certificate_number = ?
                ''', (certificate_number,))
                
                row = cursor.fetchone()
                if row:
                    decrypted = self._decrypt_certificate(row[3])
                    return {
                        'user_id': row[0],
                        'user_name': row[1],
                        'certificate_id': row[2],
                        'content': decrypted,
                        'issue_date': row[4],
                        'expire_date': row[5],
                        'status': row[6],
                        'type': row[7],
                        'metadata': json.loads(row[8]) if row[8] else {}
                    }
                return None
        except Exception as e:
            print(f"通过证书编号获取证书失败: {e}")
            return None
    
    def verify_certificate(self, certificate_number: str) -> Dict:
        """验证证书有效性"""
        cert = self.get_certificate_by_number(certificate_number)
        
        if not cert:
            return {'valid': False, 'message': '证书不存在'}
        
        if cert['status'] != 'active':
            return {'valid': False, 'message': '证书已失效'}
        
        expire_date = datetime.fromisoformat(cert['expire_date'])
        if datetime.now() > expire_date:
            return {'valid': False, 'message': '证书已过期'}
        
        return {
            'valid': True,
            'message': '证书有效',
            'certificate_number': certificate_number,
            'user_id': cert['user_id'],
            'user_name': cert['user_name'],
            'expire_date': cert['expire_date'],
            'type': cert['type']
        }
    
    def renew_certificate(self, user_id: int) -> Optional[Dict]:
        """续期证书"""
        try:
            cert = self.get_certificate(user_id)
            if not cert:
                self.log_certificate(user_id, 'RENEW', 'FAILED', '证书不存在')
                return None
            
            validity_days = self._get_validity_days(cert['type'])
            new_expire_date = datetime.now() + timedelta(days=validity_days)
            
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE user_certificates 
                    SET expire_date = ?, status = 'active', updated_at = ?
                    WHERE user_id = ?
                ''', (new_expire_date.isoformat(), datetime.now(), user_id))
                
                conn.commit()
            
            self.log_certificate(user_id, 'RENEW', 'SUCCESS', f'证书已续期至 {new_expire_date.isoformat()}')
            
            return {
                'status': 'success',
                'expire_date': new_expire_date.isoformat()
            }
        
        except Exception as e:
            self.log_certificate(user_id, 'RENEW', 'FAILED', str(e))
            return None
    
    def revoke_certificate(self, user_id: int) -> bool:
        """吊销证书"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE user_certificates 
                    SET status = 'revoked', updated_at = ?
                    WHERE user_id = ? AND status = 'active'
                ''', (datetime.now(), user_id))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    self.log_certificate(user_id, 'REVOKE', 'SUCCESS', '证书已吊销')
                    return True
                
                self.log_certificate(user_id, 'REVOKE', 'FAILED', '证书不存在或已吊销')
                return False
        
        except Exception as e:
            self.log_certificate(user_id, 'REVOKE', 'FAILED', str(e))
            return False
    
    def log_certificate(self, user_id: int, action: str, status: str, message: str = ""):
        """记录证书操作日志"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT certificate_id FROM user_certificates WHERE user_id = ?', (user_id,))
                row = cursor.fetchone()
                cert_id = row[0] if row else ""
                
                cursor.execute('''
                    INSERT INTO certificate_logs (certificate_id, user_id, action, status, message)
                    VALUES (?, ?, ?, ?, ?)
                ''', (cert_id, user_id, action, status, message))
                
                conn.commit()
        except Exception as e:
            print(f"记录证书日志失败: {e}")
    
    def get_user_certificates(self, user_id: int) -> list:
        """获取用户所有证书"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT certificate_number, certificate_type, issue_date, expire_date, status
                    FROM user_certificates WHERE user_id = ? ORDER BY issue_date DESC
                ''', (user_id,))
                
                return [{
                    'certificate_number': row[0],
                    'type': row[1],
                    'issue_date': row[2],
                    'expire_date': row[3],
                    'status': row[4]
                } for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取用户证书列表失败: {e}")
            return []
    
    def get_all_certificates(self) -> list:
        """获取所有证书"""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT user_id, user_name, certificate_number, certificate_type, 
                           issue_date, expire_date, status
                    FROM user_certificates ORDER BY issue_date DESC
                ''')
                
                return [{
                    'user_id': row[0],
                    'user_name': row[1],
                    'certificate_number': row[2],
                    'type': row[3],
                    'issue_date': row[4],
                    'expire_date': row[5],
                    'status': row[6]
                } for row in cursor.fetchall()]
        except Exception as e:
            print(f"获取所有证书失败: {e}")
            return []

# 全局实例
user_certificate_manager = None

def get_user_certificate_manager():
    """获取用户证书管理器实例"""
    global user_certificate_manager
    if user_certificate_manager is None:
        user_certificate_manager = UserCertificateManager()
    return user_certificate_manager

if __name__ == "__main__":
    manager = UserCertificateManager()
    
    print("=== 用户数字证书测试 ===")
    
    # 创建证书
    result = manager.create_certificate(1001, "张三")
    if result:
        print(f"创建证书成功:")
        print(f"  证书ID: {result['certificate_id']}")
        print(f"  证书编号: {result['certificate_number']}")
        print(f"  颁发日期: {result['issue_date']}")
        print(f"  过期日期: {result['expire_date']}")
    
    # 获取证书
    cert = manager.get_certificate(1001)
    if cert:
        print(f"\n获取证书成功:")
        print(f"  用户ID: {cert['content']['user_id']}")
        print(f"  用户姓名: {cert['content']['user_name']}")
        print(f"  签名: {cert['content']['signature'][:20]}...")
    
    # 验证证书
    if result:
        verify_result = manager.verify_certificate(result['certificate_number'])
        print(f"\n证书验证结果: {verify_result}")
    
    # 获取所有证书
    all_certs = manager.get_all_certificates()
    print(f"\n系统中的证书数量: {len(all_certs)}")
    
    # 测试重复创建
    result2 = manager.create_certificate(1001, "张三")
    print(f"\n重复创建证书: {result2}")
    
    logger.info("\n == 测试完成 ===")
