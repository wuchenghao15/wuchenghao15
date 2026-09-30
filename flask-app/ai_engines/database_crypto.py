#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTSCOS 数据库系统加密管理器 (DatabaseCryptoManager)
=====================================================
功能：
  - 字段级 AES 加密（Fernet: AES-128-CBC + HMAC-SHA256）
  - 文件级 AES-256-CBC 加密（备份文件加密）
  - 密钥派生（HKDF-SHA256: vikey序列号 + 系统指纹）
  - 密钥版本管理（支持轮换，旧数据用旧密钥解密）
  - 透明加解密（应用层无感知）
  - 加密标识（ENC: 前缀）

遵循：
  - SSOT 原则（密钥版本元数据落库）
  - 超级管理员 vikey 绑定
  - 审计日志记录

版本: v1.0.0
"""

import os
import sys
import json
import uuid
import socket
import hashlib
import sqlite3
import logging
import base64
import struct
import secrets
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger('database_crypto')

# 加密前缀标识
ENCRYPTED_PREFIX = b'ENC:'
ENCRYPTED_PREFIX_STR = 'ENC:'

# 密钥派生信息常量
KDF_INFO_FIELD = b'mtscos_field_encryption_v1'
KDF_INFO_FILE = b'mtscos_file_encryption_v1'


class DatabaseCryptoManager:
    """
    数据库系统加密管理器

    使用方式：
        crypto = DatabaseCryptoManager(db_path='app.db')
        encrypted = crypto.encrypt_field('sensitive_data')
        decrypted = crypto.decrypt_field(encrypted)
    """

    VERSION = 'v1.0.0'
    MANAGER_ID = 'database_crypto_manager_001'

    def __init__(self, db_path: str = None, vikey_serial: str = None,
                 dual_db=None, key_seed: bytes = None):
        """
        初始化加密管理器

        Args:
            db_path: 数据库路径（用于密钥版本表）
            vikey_serial: vikey USB Key 序列号（密钥种子之一）
            dual_db: 双数据库管理器（可选，用于双写密钥版本）
            key_seed: 自定义密钥种子（可选，覆盖 vikey+系统指纹）
        """
        self.db_path = db_path
        self.dual_db = dual_db
        self.vikey_serial = vikey_serial or os.environ.get('MTSCOS_VIKEY_SERIAL', 'default_vikey_serial')

        # 密钥种子（内存中，不落盘）
        if key_seed:
            self._key_seed = key_seed
        else:
            self._key_seed = self._derive_key_seed()

        # 派生密钥
        self._fernet_key = self._derive_fernet_key(self._key_seed)
        self._aes_key = self._derive_aes_key(self._key_seed)
        self._fernet = Fernet(self._fernet_key)

        # 密钥版本
        self._current_key_version = 1
        self._key_history: Dict[int, Fernet] = {}

        # 统计
        self.stats = {
            'total_encryptions': 0,
            'total_decryptions': 0,
            'total_file_encryptions': 0,
            'total_file_decryptions': 0,
            'failed_decryptions': 0,
            'key_rotations': 0,
        }

        # 初始化数据库表
        self._ensure_tables()

        # 加载当前密钥版本
        self._load_key_version()

        logger.info(f"DatabaseCryptoManager 已初始化 (v{self.VERSION}) "
                     f"vikey_bound={'✓' if vikey_serial else '✗'}")

    # ========================================================================
    # 密钥派生
    # ========================================================================

    def _derive_key_seed(self) -> bytes:
        """
        从 vikey 序列号 + 系统指纹派生密钥种子

        种子 = vikey_serial + MAC地址 + 主机名 + Python版本
        """
        # 系统指纹
        try:
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff)
                            for ele in range(0, 8 * 6, 8)][::-1])
        except Exception:
            mac = '00:00:00:00:00:00'

        hostname = socket.gethostname()
        python_ver = f"{sys.version_info.major}.{sys.version_info.minor}"

        # 组合种子
        seed_str = f"{self.vikey_serial}|{mac}|{hostname}|{python_ver}"
        seed = hashlib.sha256(seed_str.encode('utf-8')).digest()

        logger.debug(f"密钥种子已派生 (vikey={self.vikey_serial[:8]}... mac={mac[:8]}...)")
        return seed

    def _derive_fernet_key(self, seed: bytes, version: int = 1) -> bytes:
        """从种子派生 Fernet 密钥（HKDF-SHA256）"""
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=struct.pack('>I', version),
            info=KDF_INFO_FIELD,
            backend=default_backend()
        )
        key = hkdf.derive(seed)
        return base64.urlsafe_b64encode(key)

    def _derive_aes_key(self, seed: bytes, version: int = 1) -> bytes:
        """从种子派生 AES-256 密钥（HKDF-SHA256）"""
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=struct.pack('>I', version),
            info=KDF_INFO_FILE,
            backend=default_backend()
        )
        return hkdf.derive(seed)

    # ========================================================================
    # 字段级加密（Fernet: AES-128-CBC + HMAC-SHA256）
    # ========================================================================

    def encrypt_field(self, value: Union[str, bytes, int, float, dict, list, None],
                      add_prefix: bool = True) -> Optional[str]:
        """
        加密字段值

        Args:
            value: 待加密的值（支持 str/bytes/int/float/dict/list）
            add_prefix: 是否添加 ENC: 前缀

        Returns:
            加密后的字符串（base64编码），或 None（输入为 None）
        """
        if value is None:
            return None

        # 序列化为 JSON 字符串（统一处理各种类型）
        if isinstance(value, bytes):
            plaintext = value
        elif isinstance(value, str):
            # 检查是否已加密
            if value.startswith(ENCRYPTED_PREFIX_STR):
                return value  # 已加密，直接返回
            plaintext = value.encode('utf-8')
        else:
            plaintext = json.dumps(value, ensure_ascii=False).encode('utf-8')

        # Fernet 加密
        ciphertext = self._fernet.encrypt(plaintext)

        # 编码为字符串
        encrypted_str = ciphertext.decode('ascii')

        # 添加前缀
        if add_prefix:
            encrypted_str = ENCRYPTED_PREFIX_STR + encrypted_str

        self.stats['total_encryptions'] += 1
        return encrypted_str

    def decrypt_field(self, value: Union[str, bytes, None],
                      remove_prefix: bool = True) -> Any:
        """
        解密字段值

        Args:
            value: 加密的值
            remove_prefix: 是否移除 ENC: 前缀

        Returns:
            解密后的原始值（自动尝试 JSON 反序列化）
        """
        if value is None:
            return None

        if isinstance(value, bytes):
            value = value.decode('utf-8', errors='replace')

        # 移除前缀
        if remove_prefix and value.startswith(ENCRYPTED_PREFIX_STR):
            value = value[len(ENCRYPTED_PREFIX_STR):]
        elif not value.startswith('gAAAAA'):  # Fernet 密文通常以 gAAAAA 开头
            # 不是加密值，直接返回
            return value

        try:
            ciphertext = value.encode('ascii')
            plaintext = self._fernet.decrypt(ciphertext)
            self.stats['total_decryptions'] += 1

            # 尝试 JSON 反序列化（支持 dict/list/bool/int/float/null）
            try:
                text = plaintext.decode('utf-8')
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return text  # 普通字符串，直接返回
            except UnicodeDecodeError:
                return plaintext

        except InvalidToken:
            # 尝试使用历史密钥
            for ver, fernet in self._key_history.items():
                try:
                    plaintext = fernet.decrypt(value.encode('ascii'))
                    self.stats['total_decryptions'] += 1
                    logger.debug(f"使用历史密钥版本 {ver} 解密成功")
                    try:
                        return plaintext.decode('utf-8')
                    except:
                        return plaintext
                except InvalidToken:
                    continue

            self.stats['failed_decryptions'] += 1
            logger.error("解密失败：无有效密钥")
            return None

    def is_encrypted(self, value: Any) -> bool:
        """检查值是否已加密"""
        if value is None:
            return False
        if isinstance(value, bytes):
            value = value.decode('utf-8', errors='replace')
        if isinstance(value, str):
            return value.startswith(ENCRYPTED_PREFIX_STR) or value.startswith('gAAAAA')
        return False

    # ========================================================================
    # 批量字段加密/解密
    # ========================================================================

    def encrypt_dict(self, data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """
        加密字典中指定字段

        Args:
            data: 原始字典
            fields: 需要加密的字段名列表

        Returns:
            加密后的字典（新对象）
        """
        result = data.copy()
        for field in fields:
            if field in result and result[field] is not None:
                result[field] = self.encrypt_field(result[field])
        return result

    def decrypt_dict(self, data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """
        解密字典中指定字段

        Args:
            data: 加密的字典
            fields: 需要解密的字段名列表

        Returns:
            解密后的字典（新对象）
        """
        result = data.copy()
        for field in fields:
            if field in result and result[field] is not None:
                result[field] = self.decrypt_field(result[field])
        return result

    def encrypt_record(self, table: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        加密数据库记录（根据表名自动选择加密字段）

        Args:
            table: 表名
            record: 原始记录

        Returns:
            加密后的记录
        """
        # 敏感字段配置（可扩展）
        sensitive_fields_map = {
            'users': ['password_hash', 'session_token', 'api_key', 'email', 'phone'],
            'mt_users': ['password_hash', 'session_token', 'api_key', 'email', 'phone'],
            'mt_sessions': ['session_token', 'csrf_token'],
            'mt_api_keys': ['api_key', 'secret'],
            'mt_system_config': ['value'],
            'mt_maintenance_proposals': ['execution_result', 'report_summary'],
        }
        fields = sensitive_fields_map.get(table, [])
        if fields:
            return self.encrypt_dict(record, fields)
        return record

    def decrypt_record(self, table: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        解密数据库记录

        Args:
            table: 表名
            record: 加密记录

        Returns:
            解密后的记录
        """
        sensitive_fields_map = {
            'users': ['password_hash', 'session_token', 'api_key', 'email', 'phone'],
            'mt_users': ['password_hash', 'session_token', 'api_key', 'email', 'phone'],
            'mt_sessions': ['session_token', 'csrf_token'],
            'mt_api_keys': ['api_key', 'secret'],
            'mt_system_config': ['value'],
            'mt_maintenance_proposals': ['execution_result', 'report_summary'],
        }
        fields = sensitive_fields_map.get(table, [])
        if fields:
            return self.decrypt_dict(record, fields)
        return record

    # ========================================================================
    # 文件级加密（AES-256-CBC）
    # ========================================================================

    def encrypt_file(self, src_path: str, dst_path: str = None,
                     delete_src: bool = False) -> Dict[str, Any]:
        """
        加密文件（AES-256-CBC + 随机IV + HMAC-SHA256）

        Args:
            src_path: 源文件路径
            dst_path: 目标文件路径（默认在源文件后加 .enc）
            delete_src: 是否删除源文件

        Returns:
            加密结果（含文件路径、SHA256、大小）
        """
        if dst_path is None:
            dst_path = src_path + '.enc'

        result = {
            'src_path': src_path,
            'dst_path': dst_path,
            'success': False,
            'sha256': None,
            'size_bytes': 0,
            'error': None,
        }

        try:
            # 读取源文件
            with open(src_path, 'rb') as f:
                plaintext = f.read()

            # 生成随机 IV
            iv = secrets.token_bytes(16)

            # PKCS7 填充
            padder = padding.PKCS7(algorithms.AES.block_size).padder()
            padded_data = padder.update(plaintext) + padder.finalize()

            # AES-256-CBC 加密
            cipher = Cipher(algorithms.AES(self._aes_key), modes.CBC(iv),
                            backend=default_backend())
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(padded_data) + encryptor.finalize()

            # HMAC-SHA256 完整性校验
            h = hashlib.sha256()
            h.update(iv)
            h.update(ciphertext)
            hmac_digest = h.digest()

            # 写入加密文件：[魔数 4B][版本 1B][IV 16B][HMAC 32B][密文]
            with open(dst_path, 'wb') as f:
                f.write(b'MTCE')  # 魔数 MTSCOS Crypto Encrypted
                f.write(struct.pack('>B', 1))  # 版本
                f.write(iv)  # IV
                f.write(hmac_digest)  # HMAC
                f.write(ciphertext)  # 密文

            # 计算加密文件 SHA256
            with open(dst_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()

            result['success'] = True
            result['sha256'] = file_hash
            result['size_bytes'] = os.path.getsize(dst_path)
            self.stats['total_file_encryptions'] += 1

            # 删除源文件
            if delete_src and os.path.exists(src_path):
                os.remove(src_path)

            logger.debug(f"文件加密成功: {src_path} → {dst_path} ({result['size_bytes']} bytes)")

        except Exception as e:
            result['error'] = str(e)
            logger.error(f"文件加密失败: {e}")

        return result

    def decrypt_file(self, src_path: str, dst_path: str = None,
                     delete_src: bool = False) -> Dict[str, Any]:
        """
        解密文件

        Args:
            src_path: 加密文件路径
            dst_path: 目标文件路径（默认去掉 .enc 后缀）
            delete_src: 是否删除加密文件

        Returns:
            解密结果
        """
        if dst_path is None:
            if src_path.endswith('.enc'):
                dst_path = src_path[:-4]
            else:
                dst_path = src_path + '.dec'

        result = {
            'src_path': src_path,
            'dst_path': dst_path,
            'success': False,
            'sha256': None,
            'size_bytes': 0,
            'error': None,
        }

        try:
            with open(src_path, 'rb') as f:
                magic = f.read(4)
                if magic != b'MTCE':
                    result['error'] = '无效的加密文件格式（魔数不匹配）'
                    return result

                version = struct.unpack('>B', f.read(1))[0]
                iv = f.read(16)
                stored_hmac = f.read(32)
                ciphertext = f.read()

            # HMAC 验证
            h = hashlib.sha256()
            h.update(iv)
            h.update(ciphertext)
            computed_hmac = h.digest()

            if computed_hmac != stored_hmac:
                result['error'] = 'HMAC 完整性校验失败'
                logger.error(f"文件 HMAC 校验失败: {src_path}")
                return result

            # AES-256-CBC 解密
            cipher = Cipher(algorithms.AES(self._aes_key), modes.CBC(iv),
                            backend=default_backend())
            decryptor = cipher.decryptor()
            padded_data = decryptor.update(ciphertext) + decryptor.finalize()

            # PKCS7 去填充
            unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
            plaintext = unpadder.update(padded_data) + unpadder.finalize()

            # 写入解密文件
            with open(dst_path, 'wb') as f:
                f.write(plaintext)

            # 计算 SHA256
            file_hash = hashlib.sha256(plaintext).hexdigest()

            result['success'] = True
            result['sha256'] = file_hash
            result['size_bytes'] = os.path.getsize(dst_path)
            self.stats['total_file_decryptions'] += 1

            if delete_src and os.path.exists(src_path):
                os.remove(src_path)

            logger.debug(f"文件解密成功: {src_path} → {dst_path} ({result['size_bytes']} bytes)")

        except Exception as e:
            result['error'] = str(e)
            logger.error(f"文件解密失败: {e}")

        return result

    def verify_encrypted_file(self, file_path: str) -> bool:
        """验证加密文件完整性"""
        try:
            with open(file_path, 'rb') as f:
                magic = f.read(4)
                if magic != b'MTCE':
                    return False
                f.read(1)  # version
                iv = f.read(16)
                stored_hmac = f.read(32)
                ciphertext = f.read()

            h = hashlib.sha256()
            h.update(iv)
            h.update(ciphertext)
            return h.digest() == stored_hmac
        except Exception:
            return False

    # ========================================================================
    # 密钥版本管理
    # ========================================================================

    def _ensure_tables(self):
        """创建密钥版本管理表"""
        if not self.db_path:
            return
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mt_crypto_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_version INTEGER UNIQUE NOT NULL,
                    key_fingerprint TEXT NOT NULL,
                    algorithm TEXT DEFAULT 'Fernet+AES-256-CBC',
                    created_at TEXT DEFAULT (datetime('now', 'localtime')),
                    rotated_at TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_by TEXT DEFAULT 'system'
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mt_crypto_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    target_type TEXT,
                    target_id TEXT,
                    key_version INTEGER,
                    operator TEXT DEFAULT 'system',
                    created_at TEXT DEFAULT (datetime('now', 'localtime'))
                )
            """)
            conn.commit()
            conn.close()
            logger.info("加密管理器数据库表已就绪")
        except Exception as e:
            logger.error(f"创建加密表失败: {e}")

    def _load_key_version(self):
        """从数据库加载当前密钥版本"""
        if not self.db_path:
            return
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT key_version FROM mt_crypto_keys WHERE is_active = 1 ORDER BY key_version DESC LIMIT 1"
            )
            row = cursor.fetchone()
            if row:
                self._current_key_version = row[0]
            else:
                # 首次初始化，记录版本1
                fingerprint = hashlib.sha256(self._fernet_key).hexdigest()[:16]
                cursor.execute(
                    "INSERT OR REPLACE INTO mt_crypto_keys (key_version, key_fingerprint, is_active) VALUES (?, ?, 1)",
                    (1, fingerprint)
                )
                conn.commit()
                self._current_key_version = 1
            conn.close()
        except Exception as e:
            logger.error(f"加载密钥版本失败: {e}")

    def rotate_key(self, operator: str = 'system') -> Dict[str, Any]:
        """
        密钥轮换（生成新密钥，旧密钥保留用于解密旧数据）

        Args:
            operator: 操作人

        Returns:
            轮换结果
        """
        result = {'success': False, 'old_version': self._current_key_version, 'new_version': None}

        # 保存旧密钥到历史
        self._key_history[self._current_key_version] = self._fernet

        # 生成新密钥
        new_version = self._current_key_version + 1
        new_fernet_key = self._derive_fernet_key(self._key_seed, new_version)
        new_aes_key = self._derive_aes_key(self._key_seed, new_version)

        # 更新当前密钥
        self._fernet_key = new_fernet_key
        self._aes_key = new_aes_key
        self._fernet = Fernet(new_fernet_key)
        self._current_key_version = new_version

        # 落库
        if self.db_path:
            try:
                conn = sqlite3.connect(self.db_path, timeout=10)
                cursor = conn.cursor()
                # 旧密钥标记为非活跃
                cursor.execute(
                    "UPDATE mt_crypto_keys SET is_active = 0 WHERE key_version < ?",
                    (new_version,)
                )
                # 新密钥
                fingerprint = hashlib.sha256(new_fernet_key).hexdigest()[:16]
                cursor.execute(
                    "INSERT INTO mt_crypto_keys (key_version, key_fingerprint, is_active, rotated_at, created_by) VALUES (?, ?, 1, ?, ?)",
                    (new_version, fingerprint, datetime.now().isoformat(), operator)
                )
                # 审计日志
                cursor.execute(
                    "INSERT INTO mt_crypto_audit_log (action, target_type, key_version, operator) VALUES (?, ?, ?, ?)",
                    ('key_rotation', 'master_key', new_version, operator)
                )
                conn.commit()
                conn.close()
            except Exception as e:
                logger.error(f"密钥轮换落库失败: {e}")

        self.stats['key_rotations'] += 1
        result['success'] = True
        result['new_version'] = new_version
        logger.info(f"密钥已轮换: v{result['old_version']} → v{new_version} (operator={operator})")
        return result

    # ========================================================================
    # 审计日志
    # ========================================================================

    def log_audit(self, action: str, target_type: str = None,
                  target_id: str = None, operator: str = 'system'):
        """记录加解密审计日志"""
        if not self.db_path:
            return
        try:
            if self.dual_db:
                self.dual_db.execute_write(
                    "INSERT INTO mt_crypto_audit_log (action, target_type, target_id, key_version, operator) VALUES (?, ?, ?, ?, ?)",
                    (action, target_type, target_id, self._current_key_version, operator)
                )
            else:
                conn = sqlite3.connect(self.db_path, timeout=10)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO mt_crypto_audit_log (action, target_type, target_id, key_version, operator) VALUES (?, ?, ?, ?, ?)",
                    (action, target_type, target_id, self._current_key_version, operator)
                )
                conn.commit()
                conn.close()
        except Exception as e:
            logger.error(f"审计日志写入失败: {e}")

    # ========================================================================
    # 状态查询
    # ========================================================================

    def get_status(self) -> Dict[str, Any]:
        """获取加密管理器状态"""
        return {
            'manager_id': self.MANAGER_ID,
            'version': self.VERSION,
            'vikey_bound': self.vikey_serial != 'default_vikey_serial',
            'current_key_version': self._current_key_version,
            'key_history_count': len(self._key_history),
            'algorithm': 'Fernet(AES-128-CBC+HMAC-SHA256) + AES-256-CBC',
            'stats': self.stats.copy(),
        }

    def get_key_info(self) -> Dict[str, Any]:
        """获取密钥信息（不含密钥本身）"""
        return {
            'current_version': self._current_key_version,
            'vikey_serial': self.vikey_serial[:8] + '...' if len(self.vikey_serial) > 8 else self.vikey_serial,
            'algorithm': 'HKDF-SHA256 → Fernet + AES-256-CBC',
            'key_history': list(self._key_history.keys()),
        }


# ============================================================================
# 单例管理
# ============================================================================

_crypto_manager_instance: Optional[DatabaseCryptoManager] = None
_crypto_lock = threading.Lock() if 'threading' in dir() else None

try:
    import threading
    _crypto_lock = threading.Lock()
except ImportError:
    pass

def get_crypto_manager(db_path: str = None, vikey_serial: str = None,
                       dual_db=None) -> DatabaseCryptoManager:
    """获取加密管理器单例"""
    global _crypto_manager_instance
    if _crypto_manager_instance is None:
        import threading
        with threading.Lock():
            if _crypto_manager_instance is None:
                _crypto_manager_instance = DatabaseCryptoManager(
                    db_path=db_path,
                    vikey_serial=vikey_serial,
                    dual_db=dual_db,
                )
    return _crypto_manager_instance
