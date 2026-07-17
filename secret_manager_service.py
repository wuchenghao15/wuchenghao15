#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS密钥管理服务
提供敏感信息加密存储和访问控制
"""

import os
import sys
import json
import time
import base64
import hashlib
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

logger = print


class Secret:
    """密钥"""

    def __init__(self, secret_id: str, name: str, encrypted_value: str,
                 description: str = '', secret_type: str = 'generic',
                 version: int = 1, expires_at: str = None,
                 created_at: str = None):
        self.secret_id = secret_id
        self.name = name
        self.encrypted_value = encrypted_value
        self.description = description
        self.secret_type = secret_type  # generic, password, api_key, certificate, token
        self.version = version
        self.expires_at = expires_at
        self.created_at = created_at or datetime.now().isoformat()
        self.last_accessed = None
        self.access_count = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'secret_id': self.secret_id,
            'name': self.name,
            'description': self.description,
            'secret_type': self.secret_type,
            'version': self.version,
            'expires_at': self.expires_at,
            'created_at': self.created_at,
            'last_accessed': self.last_accessed,
            'access_count': self.access_count,
            'is_expired': self._is_expired()
        }

    def _is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.now().isoformat() > self.expires_at


class SecretManagerService:
    """密钥管理服务"""

    def __init__(self, master_key: str = None):
        self.secrets: Dict[str, Secret] = {}
        self.is_running = False
        self.lock = threading.Lock()

        self.master_key = master_key or self._get_or_create_master_key()
        self._init_database()
        self._register_default_secrets()

    def _get_or_create_master_key(self) -> str:
        """获取或创建主密钥"""
        key_path = os.path.join(os.path.dirname(__file__), '.master_key')
        if os.path.exists(key_path):
            with open(key_path, 'r') as f:
                return f.read().strip()

        master_key = base64.b64encode(os.urandom(32)).decode('utf-8')

        with open(key_path, 'w') as f:
            f.write(master_key)

        os.chmod(key_path, 0o600)

        return master_key

    def _encrypt(self, plaintext: str) -> str:
        """加密"""
        try:
            from cryptography.fernet import Fernet
            key = hashlib.sha256(self.master_key.encode()).digest()
            fernet_key = base64.urlsafe_b64encode(key)
            f = Fernet(fernet_key)
            return f.encrypt(plaintext.encode('utf-8')).decode('utf-8')
        except ImportError:
            return base64.b64encode(
                plaintext.encode('utf-8') + self.master_key.encode('utf-8')
            ).decode('utf-8')

    def _decrypt(self, ciphertext: str) -> str:
        """解密"""
        try:
            from cryptography.fernet import Fernet
            key = hashlib.sha256(self.master_key.encode()).digest()
            fernet_key = base64.urlsafe_b64encode(key)
            f = Fernet(fernet_key)
            return f.decrypt(ciphertext.encode('utf-8')).decode('utf-8')
        except ImportError:
            decoded = base64.b64decode(ciphertext).decode('utf-8')
            return decoded.replace(self.master_key, '')

    def _init_database(self):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS secrets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    secret_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    encrypted_value TEXT NOT NULL,
                    description TEXT,
                    secret_type TEXT DEFAULT 'generic',
                    version INTEGER DEFAULT 1,
                    expires_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TEXT,
                    access_count INTEGER DEFAULT 0
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS secret_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    secret_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    encrypted_value TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS secret_access_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    secret_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    action TEXT NOT NULL,
                    accessor TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_secrets_id ON secrets(secret_id)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_secrets_name ON secrets(name)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_secret_versions_secret ON secret_versions(secret_id)
            ''')

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[密钥] 初始化数据库失败: {e}")

    def _register_default_secrets(self):
        """注册默认密钥占位符"""
        defaults = [
            ('db_password', '数据库密码', 'password', '应用数据库连接密码'),
            ('redis_password', 'Redis密码', 'password', 'Redis缓存密码'),
            ('jwt_secret', 'JWT密钥', 'token', 'JWT签名密钥'),
            ('api_key_external', '外部API密钥', 'api_key', '外部服务API密钥'),
            ('smtp_password', 'SMTP密码', 'password', '邮件服务SMTP密码'),
            ('sms_api_key', '短信API密钥', 'api_key', '短信服务API密钥'),
            ('encryption_key', '加密密钥', 'generic', '数据加密密钥'),
            ('oauth_client_secret', 'OAuth客户端密钥', 'token', 'OAuth2.0客户端密钥')
        ]

        for name, description, secret_type, desc in defaults:
            secret_id = f"sec_{name}"
            if secret_id not in self.secrets:
                encrypted = self._encrypt(f"placeholder_{name}")
                secret = Secret(
                    secret_id=secret_id,
                    name=name,
                    encrypted_value=encrypted,
                    description=desc,
                    secret_type=secret_type
                )
                self.secrets[secret_id] = secret
                self._save_secret_to_db(secret)

    def _generate_secret_id(self) -> str:
        import uuid
        return f"sec_{uuid.uuid4().hex[:12]}"

    def store_secret(self, name: str, value: str, description: str = '',
                     secret_type: str = 'generic', expires_at: str = None) -> str:
        """存储密钥"""
        secret_id = f"sec_{name}"
        encrypted_value = self._encrypt(value)

        with self.lock:
            if secret_id in self.secrets:
                old_secret = self.secrets[secret_id]
                new_version = old_secret.version + 1

                self._save_version_to_db(secret_id, old_secret.version, old_secret.encrypted_value)

                old_secret.encrypted_value = encrypted_value
                old_secret.version = new_version
                old_secret.description = description or old_secret.description
                old_secret.expires_at = expires_at

                self._update_secret_in_db(old_secret)
                self._log_access(secret_id, name, 'update')

                logger(f"[密钥] 更新密钥: {name} (v{new_version})")
                return secret_id

            secret = Secret(
                secret_id=secret_id,
                name=name,
                encrypted_value=encrypted_value,
                description=description,
                secret_type=secret_type,
                expires_at=expires_at
            )

            self.secrets[secret_id] = secret
            self._save_secret_to_db(secret)
            self._log_access(secret_id, name, 'create')

            logger(f"[密钥] 存储密钥: {name}")
            return secret_id

    def _save_secret_to_db(self, secret: Secret):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO secrets
                (secret_id, name, encrypted_value, description, secret_type,
                 version, expires_at, created_at, last_accessed, access_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                secret.secret_id, secret.name, secret.encrypted_value,
                secret.description, secret.secret_type,
                secret.version, secret.expires_at,
                secret.created_at, secret.last_accessed, secret.access_count
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[密钥] 保存密钥失败: {e}")

    def _update_secret_in_db(self, secret: Secret):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE secrets
                SET encrypted_value = ?, description = ?, version = ?,
                    expires_at = ?, last_accessed = ?, access_count = ?
                WHERE secret_id = ?
            ''', (
                secret.encrypted_value, secret.description,
                secret.version, secret.expires_at,
                secret.last_accessed, secret.access_count,
                secret.secret_id
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[密钥] 更新密钥失败: {e}")

    def _save_version_to_db(self, secret_id: str, version: int, encrypted_value: str):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO secret_versions (secret_id, version, encrypted_value)
                VALUES (?, ?, ?)
            ''', (secret_id, version, encrypted_value))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[密钥] 保存版本失败: {e}")

    def _log_access(self, secret_id: str, name: str, action: str,
                    accessor: str = ''):
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO secret_access_logs (secret_id, name, action, accessor)
                VALUES (?, ?, ?, ?)
            ''', (secret_id, name, action, accessor))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[密钥] 记录访问失败: {e}")

    def get_secret(self, name: str, accessor: str = '') -> Optional[str]:
        """获取密钥值"""
        secret_id = f"sec_{name}"

        with self.lock:
            secret = self.secrets.get(secret_id)
            if not secret:
                logger(f"[密钥] 密钥不存在: {name}")
                return None

            if secret._is_expired():
                logger(f"[密钥] 密钥已过期: {name}")
                return None

            secret.last_accessed = datetime.now().isoformat()
            secret.access_count += 1

        self._update_secret_in_db(secret)
        self._log_access(secret_id, name, 'read', accessor)

        return self._decrypt(secret.encrypted_value)

    def delete_secret(self, name: str) -> bool:
        """删除密钥"""
        secret_id = f"sec_{name}"

        with self.lock:
            if secret_id not in self.secrets:
                return False

            secret = self.secrets[secret_id]
            del self.secrets[secret_id]

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('DELETE FROM secrets WHERE secret_id = ?', (secret_id,))
            cursor.execute('DELETE FROM secret_versions WHERE secret_id = ?', (secret_id,))

            conn.commit()
            conn.close()
        except Exception as e:
            logger(f"[密钥] 删除密钥失败: {e}")

        self._log_access(secret_id, name, 'delete')
        logger(f"[密钥] 删除密钥: {name}")
        return True

    def rotate_secret(self, name: str, new_value: str) -> bool:
        """轮换密钥"""
        return self.store_secret(name, new_value) is not None

    def get_secret_info(self, name: str) -> Optional[Dict[str, Any]]:
        """获取密钥信息（不含值）"""
        secret_id = f"sec_{name}"
        secret = self.secrets.get(secret_id)
        if not secret:
            return None
        return secret.to_dict()

    def list_secrets(self, secret_type: str = None) -> List[Dict[str, Any]]:
        """列出密钥"""
        with self.lock:
            secrets = list(self.secrets.values())

            if secret_type:
                secrets = [s for s in secrets if s.secret_type == secret_type]

            return [s.to_dict() for s in secrets]

    def get_secret_versions(self, name: str) -> List[Dict[str, Any]]:
        """获取密钥版本历史"""
        secret_id = f"sec_{name}"

        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM secret_versions
                WHERE secret_id = ?
                ORDER BY version DESC
            ''', (secret_id,))

            columns = [desc[0] for desc in cursor.description]
            versions = [dict(zip(columns, row)) for row in cursor.fetchall()]

            conn.close()
            return versions
        except Exception as e:
            logger(f"[密钥] 获取版本失败: {e}")
            return []

    def get_access_logs(self, name: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取访问日志"""
        try:
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            query = 'SELECT * FROM secret_access_logs WHERE 1=1'
            params = []

            if name:
                query += ' AND name = ?'
                params.append(name)

            query += ' ORDER BY created_at DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)

            columns = [desc[0] for desc in cursor.description]
            logs = [dict(zip(columns, row)) for row in cursor.fetchall()]

            conn.close()
            return logs
        except Exception as e:
            logger(f"[密钥] 获取访问日志失败: {e}")
            return []

    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            expired = sum(1 for s in self.secrets.values() if s._is_expired())

            return {
                'status': 'running' if self.is_running else 'stopped',
                'total_secrets': len(self.secrets),
                'expired_secrets': expired,
                'total_accesses': sum(s.access_count for s in self.secrets.values())
            }

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        logger(f"[密钥] 密钥管理服务已启动")

    def stop(self):
        self.is_running = False
        logger(f"[密钥] 密钥管理服务已停止")


secret_manager_service = SecretManagerService()
